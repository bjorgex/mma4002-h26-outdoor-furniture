"""Step through the v8 program on the REAL robot, one move at a time, from your own terminal.

Before every step it prints what comes next and waits for you:
    Enter / n      do it
    s / q          stop (the robot stays where it is; TMflow stays in the Listen node)
    x 2 / y -1 / z -0.5     nudge the flange by that many mm in the robot base frame (orientation kept)
    rz 1 / rx -0.5 / ry 1   turn that many degrees about the base axis through the fingertips
                   (nudges and turns stay in effect for the next straight moves, also through GRIP/RELEASE, until a joint move or save)
    save           store where the robot is now as the LAST move's taught pose (teach.py --with-rotation),
                   rebuild tests/v8_moves.json and carry on with the new numbers
    skip           skip the next step
    open / close   open or close the gripper now (the next step stays the same; closing on air is allowed)
    step 74        jump to step 74 (see --list); the robot only moves when you press Enter, and it says how far
    b              back: undo the last move (straight line back to where it started, slow); not across a GRIP/RELEASE
    f              estimate the push force now (lifts 2 mm and back: pressing vs free joint torques)
Directions (standing across the plate, facing the robot): +Y = left, -X = towards you, -Z = down.

TMflow: HandE_Bridge_v1 running and waiting in the Bridge Listen node, Manual mode, low project speed.
    python tests/step_run.py                       from the start (Home, RELEASE, stage 1 ...)
    python tests/step_run.py --from "plank1 pick travel"
    python tests/step_run.py --from "plank1 pick travel" --to "plank1 place up"
    python tests/step_run.py --list                the step names
Speeds: joint moves --ptp % (default 50), lines --line mm/s (default 100, capped by the program's own speed), lines ending lower than 15 mm above
a place or pick --slow mm/s (default 10); nudges 20 mm/s (z down 5), back 30 mm/s.
"""
import argparse
import json
import re
import socket
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RC = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(RC)); sys.path.insert(0, str(HERE / "robot_sim"))
import listen_pick_place_test as lt                    # noqa: E402
import hande_bridge as hb                              # noqa: E402
import tm5_kin as K                                    # noqa: E402
import teach_overrides as TO                           # noqa: E402

TIP = 160.0                                            # flange -> fingertips along tool z [mm]


def tcp_point(F):
    T = TO.pose_to_T(list(F))
    return T[:3, 3] + TIP * T[:3, 2]


def rot_about(axis, deg, p):
    """4x4: turn `deg` about base axis x|y|z through point p."""
    R = np.eye(4)
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    R[:3, :3] = {"x": [[1, 0, 0], [0, c, -s], [0, s, c]], "y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
                 "z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]
    A, B = np.eye(4), np.eye(4)
    A[:3, 3], B[:3, 3] = p, -np.asarray(p)
    return A @ R @ B

MOVES = HERE / "v8_moves.json"
SLOW_NEAR = ("pick", "place")                          # last approach into a grip/place pose goes slow


def load():
    """Moves + GRIP/RELEASE; the EGP finger pre-sets (gripper None) have no Hand-E step, as in v4_replay.py."""
    return [s for s in json.loads(MOVES.read_text(encoding="utf-8"))["steps"] if "move" in s or s.get("gripper")]


def state(n=5):
    with socket.create_connection((lt.IP, lt.SLAVE), timeout=3) as s:
        buf = b""
        while buf.count(b"$TMSVR") < n + 2:
            buf += s.recv(65536)
    pk = [p.decode(errors="replace") for p in buf.split(b"$TMSVR")[2:2 + n]]
    def g(k):                                           # a key the stream lacks (the mock: no torques) -> zeros
        rows = [re.search(k + r"=\{([^}]*)\}", p) for p in pk]
        rows = [[float(v) for v in m.group(1).split(",")] for m in rows if m]
        return np.mean(rows, axis=0) if rows else np.zeros(6)
    return g("Coord_Robot_Flange"), g("Joint_Torque"), g("Joint_Angle")


def line(f, v):
    return f'Line("CAP",{",".join(f"{x:.3f}" for x in f)},{v:g},{lt.ACC},0,false)'


def ptp(q, pct):
    return f'PTP("JPP",{",".join(f"{v:.4f}" for v in q)},{pct:g},{lt.ACC},0,false)'


VIEW = 8092                                            # the 3D page (demo_viewer.py view ... --port 8092); 0 = off


def view(**ev):
    """Tell the 3D page what the gripper does (POST /step, as v4_replay.py under the mock): a 'carry' names the parts
    the next GRIP takes along, 'grip' ok attaches them, 'node' release puts everything down. Never blocks a move."""
    if not VIEW:
        return
    try:
        import urllib.request
        req = urllib.request.Request(f"http://127.0.0.1:{VIEW}/step", data=json.dumps(ev).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=1).read()
    except Exception:
        pass                                           # no page running: fine


def view_grip(parts, ok=True):
    view(t="carry", action="grip", parts=list(parts))
    view(t="node", kind="grip")
    view(t="grip", result="ok" if ok else "loss")


def view_release(parts=()):
    view(t="carry", action="release", parts=list(parts))
    view(t="node", kind="release")


def describe(s):
    if "move" in s:
        f = s["flange"]
        return f'{s["name"]:28s} {s["move"]:4s} to x {f[0]:7.1f}  y {f[1]:7.1f}  z {f[2]:6.1f}  (J6 {s["joints"][5]:6.1f})'
    return f'{s["gripper"].upper():28s} ({", ".join(s.get("parts", [])[:3])})'


def force(b, lift=2.0):
    """Push force from the joint torques: pressing now vs 2 mm up, through the Jacobian (6D wrench at the flange)."""
    F0, tq0, q0 = state(10)
    up = list(F0); up[2] += lift
    b.r.move(line(up, 2))
    _, tq1, _ = state(10)
    b.r.move(line(F0, 2))
    J = np.array(K._jacobian(K.frames(list(q0))), float)
    W = np.linalg.solve(J.T, tq0 - tq1)                # Joint_Torque mNm, J linear mm -> N
    print(f"    push force ~ {W[2]:+.0f} N down/up (z), {W[0]:+.0f} N x, {W[1]:+.0f} N y  (negative z = pressing down)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--to", dest="stop", default=None)
    ap.add_argument("--ptp", type=float, default=50)
    ap.add_argument("--line", type=float, default=100)
    ap.add_argument("--slow", type=float, default=10)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--view", type=int, default=8092, help="3D page port for the gripper events (0 = off)")
    a = ap.parse_args()
    global VIEW
    VIEW = a.view

    steps = load()
    names = [s.get("name") or f'{s["gripper"]} {i}' for i, s in enumerate(steps)]
    if a.list:
        for i, s in enumerate(steps):
            print(f"{i:3d} st{s['stage']} {describe(s)}")
        return
    i = names.index(a.start) if a.start else 0
    last = names.index(a.stop) if a.stop else len(steps) - 1

    print(f"robot {lt.IP}: connecting to the Bridge Listen node ...")
    b = hb.Bridge()
    print(f"connected ({b.node}). Enter = next, s = stop, x|y|z <mm>, rx|ry|rz <deg>, b = back, step <n>, open, close, save, skip, f = force\n")
    done = names[i - 1] if i > 0 and "move" in steps[i - 1] else None   # what 'save' teaches (the last move)
    adj = np.eye(4)                                     # your nudges since the last GRIP/RELEASE/joint move:
    hist = []                                           # (step index, pose/joints before it) of each move done, for 'b'
    while i <= last:                                    # applied to the following straight-line targets too
        s = steps[i]
        print(f"[{i}] next: {describe(s)}")
        cmd = input("> ").strip().lower()
        if cmd in ("s", "q", "stop"):
            break
        if cmd == "skip":
            i += 1
            continue
        m = re.fullmatch(r"(?:step|goto|g)\s+(\d+)", cmd)
        if m:                                           # jump: the robot does not move until you press Enter
            k = int(m.group(1))
            if not 0 <= k < len(steps):
                print(f"    no step {k} (0..{len(steps) - 1}, see --list)")
                continue
            i, adj = k, np.eye(4)
            done = names[k - 1] if k > 0 and "move" in steps[k - 1] else None
            t = steps[k]
            if "move" in t:
                F, _, _ = state(2)
                dist = np.linalg.norm(np.array(t["flange"][:3]) - F[:3])
                kind = "joint move" if t["move"] == "ptp" else "STRAIGHT LINE"
                print(f"    jumped to [{k}]. Enter = {kind} from here, {dist:.0f} mm away"
                      + ("  !! check the path is clear" if dist > 50 else ""))
            else:
                print(f"    jumped to [{k}] ({t['gripper'].upper()}): Enter does the gripper action where the arm is now")
            continue
        if cmd in ("open", "o"):                       # gripper only, the step pointer stays where it is
            b.release()
            view_release()
            print("    gripper OPEN")
            continue
        if cmd in ("close", "c"):
            b.dry = True                                # closing on air is fine here: no GripLost
            try:
                b.grip()
            finally:
                b.dry = False
            nxt = s.get("parts", []) if s.get("gripper") == "grip" else []   # at a GRIP step: its parts
            view_grip(nxt, ok=not b.lost)
            print("    gripper CLOSED" + (" - no object between the fingers" if b.lost else " - object held"))
            continue
        if cmd in ("b", "back"):
            if not hist:
                print("    nothing to go back to (no move done in this run)")
                continue
            if any("move" not in steps[k] for k in range(hist[-1][0] + 1, i)):
                print("    a GRIP/RELEASE came after that move: not undone automatically (fix the gripper first)")
                continue
            k, F_before, q_before = hist.pop()
            print(f"    back: undoing [{k}] {names[k]} -> to where it started (straight line, slow)")
            b.r.move(line(F_before, 30))
            i, adj = k, np.eye(4)
            done = names[k - 1] if k > 0 and "move" in steps[k - 1] else None
            continue
        if cmd == "f":
            force(b)
            continue
        m = re.fullmatch(r"(r?)([xyz])\s*([-+]?\d*\.?\d+)", cmd)
        if m:
            F, tq0, _ = state()
            rot, ax, d = m.group(1) == "r", m.group(2), float(m.group(3))
            if (rot and abs(d) > 10) or (not rot and abs(d) > 30):
                print("    at most 30 mm / 10 deg per nudge")
                continue
            if rot:                                     # about the base axis through the fingertips
                D = rot_about(ax, d, tcp_point(F))
            else:
                D = np.eye(4); D["xyz".index(ax), 3] = d
            adj = D @ adj
            T = TO.T_to_pose(D @ TO.pose_to_T(list(F)))
            b.r.move(line(T, 5 if (ax == "z" and d < 0 and not rot) else 20))
            G, tq1, _ = state()
            dt = tq1 - tq0
            print(f"    now x {G[0]:.1f} y {G[1]:.1f} z {G[2]:.2f}  rx {G[3]:.2f} ry {G[4]:.2f} rz {G[5]:.2f}"
                  f"   torque change J2 {dt[1]:+.0f} J3 {dt[2]:+.0f}   (kept for the next straight moves, through GRIP/RELEASE, until a joint move or save)")
            continue
        if cmd == "save":
            if not done:
                print("    nothing done yet to save")
                continue
            r = subprocess.run([sys.executable, str(HERE / "robot_sim" / "teach.py"), "v8", done, "--real",
                                "--with-rotation", "--now"], cwd=RC, capture_output=True, text=True)
            print("    " + "\n    ".join(l for l in (r.stdout + r.stderr).splitlines() if "stored" in l or "rror" in l
                                          or "refuse" in l) or "    (no output)")
            r = subprocess.run([sys.executable, str(HERE / "robot_sim" / "teach.py"), "v8", "--rebuild"], cwd=RC,
                               capture_output=True, text=True)
            steps = load()
            adj = np.eye(4)                             # the saved pose is in the program now
            print("    program rebuilt" + ("" if r.returncode == 0 else f" - FAILED:\n{r.stdout[-600:]}{r.stderr[-600:]}"))
            continue
        if cmd not in ("", "n", "next"):
            print("    ? Enter / n, s, x|y|z <mm>, rx|ry|rz <deg>, b, step <n>, open, close, save, skip, f")
            continue
        # do the step
        try:
            if "move" in s:
                F0, _, q0 = state(2)
                hist.append((i, list(F0), list(q0)))
                if s["move"] == "ptp":
                    adj = np.eye(4)
                    b.r.move(ptp(s["joints"], a.ptp))
                else:
                    slow = s["name"].endswith(SLOW_NEAR)
                    target = TO.T_to_pose(adj @ TO.pose_to_T(list(s["flange"])))
                    b.r.move(line(target, a.slow if slow else min(a.line, s.get("speed", a.line))))
                done = s["name"]
            elif s["gripper"] == "grip":
                b.grip()                                # nudges kept: the lift goes straight up from here
                view_grip(s.get("parts", []))           # the 3D page carries the program's parts from here
                print("    GRIP OK")
            else:
                b.release()                             # nudges kept: out/up go straight from here
                view_release(s.get("parts", []))
                print("    RELEASE done")
        except hb.GripLost as e:
            view_grip([], ok=False)
            print(f"    !! {e}. Fix it (TMflow: clear the message, restart the project) and run again with --from")
            break
        i += 1
    b.r.s.close()
    print("stopped. The robot stays where it is; TMflow waits in the Listen node.")


if __name__ == "__main__":
    main()
