"""Step through the v8 program on the REAL robot, one move at a time, from your own terminal.

Before every step it prints what comes next and waits for you:
    Enter / n      do it
    q / stop       stop (the robot stays where it is; TMflow stays in the Listen node)
    x 2 / y -1 / z -0.5     nudge the flange by that many mm in the robot base frame (orientation kept)
    j1 10 .. j6 -5          turn ONE joint that many degrees (joint move, max 60)
    j                       show the joint bars (o = now, x = next step, ! = near a limit)
    jgoto X Y Z RX RY RZ    JOINT move to that pose (no singularity; shows J1..J6 now -> target, y to move, 20 %)
    delete                  delete the NEXT step for good (asks y to confirm; not GRIP/RELEASE)
    set X Y Z RX RY RZ      change the NEXT step's target before it moves (Enter goes there, save keeps it)
    goto X Y Z RX RY RZ     straight line (10 mm/s) to exactly that flange pose (robot base; max 150 mm / 60 deg away)
    rz 1 / rx -0.5 / ry 1   turn that many degrees about the base axis through the fingertips
                   (nudges and turns stay in effect for the next straight moves, also through GRIP/RELEASE, until a joint move or save)
    save           store where the robot is now as the LAST move's taught pose (teach.py --with-rotation),
                   rebuild tests/v8_moves.json and carry on with the new numbers
    s / skip       skip the next step
    open / close   open or close the gripper now (the next step stays the same; closing on air is allowed)
    (open width: TMflow Variables ...SET1_var_release_pos, read by HANDE SET at program start; 10 = good for planks)
    step 74        jump to step 74 (see --list); the robot only moves when you press Enter, and it says how far
    b              back: undo the last move (straight line back to where it started, slow); not across a GRIP/RELEASE
    f              estimate the push force now (lifts 2 mm and back: pressing vs free joint torques)
Directions (standing across the plate, facing the robot): +Y = left, -X = towards you, -Z = down.

TMflow: HandE_Bridge_v1 running and waiting in the Bridge Listen node, Manual mode, low project speed.
    python tests/step_run.py                       from the start (Home, RELEASE, stage 1 ...)
    python tests/step_run.py --from "plank1 pick travel"     (or the step number: --from 8, see --list)
    python tests/step_run.py --from "plank1 pick travel" --to "plank1 place up"
    python tests/step_run.py --list                the step names
    python tests/step_run.py --cell v8x2 --from "reload the jig for bench 2"     the 2-bench program (v8x2_moves.json);
                   its reload step is a prompt: reload the jig, then Enter (never a gripper action)
Speeds: joint moves --ptp % (default 50), lines --line mm/s (default 100, capped by the program's own speed), lines ending lower than 15 mm above
a place or pick --slow mm/s (default 10); nudges 20 mm/s (z down 5), back 30 mm/s.
"""
import argparse
import json
import re
import socket
import subprocess
import sys
import time
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
    """Moves + GRIP/RELEASE; the EGP finger pre-sets (gripper None) have no Hand-E step, as in v4_replay.py; waits (wait_ms)
    and reload holds (v8x2) stay."""
    return [s for s in json.loads(MOVES.read_text(encoding="utf-8"))["steps"]
            if "move" in s or s.get("gripper") in ("grip", "release") or "wait_ms" in s or "reload" in s]


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


def joint_bars(now, nxt=None, width=36):
    """Each joint on a bar from its lower to its upper limit: o = now, x = the next step, | = 0, ! = < 20 deg from a
    limit (2026-11-20, Bjørge: to see how close the joints are to the target and to the limits)."""
    rows = []
    for j, (lo, hi) in enumerate(K.LIMITS):
        bar = ["·"] * width
        pos = lambda v: min(width - 1, max(0, round((v - lo) / (hi - lo) * (width - 1))))   # noqa: E731
        bar[pos(0)] = "|"
        if nxt is not None:
            bar[pos(nxt[j])] = "x"
        bar[pos(now[j])] = "o" if nxt is None or pos(now[j]) != pos(nxt[j]) else "@"
        near = min(now[j] - lo, hi - now[j]) < 20 or (nxt is not None and min(nxt[j] - lo, hi - nxt[j]) < 20)
        tail = f"{now[j]:8.1f}" + (f" → {nxt[j]:8.1f}  ({nxt[j] - now[j]:+7.1f})" if nxt is not None else "")
        rows.append(f"      J{j + 1} [{lo:+5d} {''.join(bar)} {hi:+5d}] {tail}{'  !' if near else ''}")
    return "\n".join(rows)


def describe(s):
    if "move" in s:
        f = s["flange"]
        # one line: the pose as 'set X Y Z RX RY RZ' (copy it, change a number, paste) + J6
        return (f'{s["name"]:28s} {s["move"]:4s}  set {" ".join(f"{v:.2f}" for v in f)}'
                f'   (J6 {s["joints"][5]:.1f})')
    if "wait_ms" in s:
        return f'WAIT {s["wait_ms"] / 1000:.0f} s{"":21s} ({s.get("name", "")})'
    if "reload" in s:
        return f'RELOAD {s["reload"]:22s} ({s.get("name", "")}: put the parts in, then Enter)'
    return f'{(s.get("gripper") or "open").upper():28s} ({", ".join(s.get("parts", [])[:3])})'


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
    ap.add_argument("--cell", default="v8", help="moves file tests/<cell>_moves.json: v8 (default), v8x2 (2 benches), v9 or v9x2 (Guide split V6)")
    a = ap.parse_args()
    global VIEW, MOVES
    VIEW = a.view
    MOVES = HERE / f"{a.cell}_moves.json"
    # 'save' teaches into the cell's own teach file (v8x2 -> v8, v9x2 -> v9: they share their base program's points)
    teach_v = {"v8x2": "v8", "v9x2": "v9"}.get(a.cell, a.cell)

    steps = load()
    names = [s.get("name") or f'{s.get("gripper")} {i}' for i, s in enumerate(steps)]
    if a.list:
        for i, s in enumerate(steps):
            print(f"{i:3d} st{s['stage']} {describe(s)}")
        return
    pick = lambda v: int(v) if v.isdigit() else names.index(v)   # --from 8 or --from "plank above interface"
    i = pick(a.start) if a.start else 0
    last = pick(a.stop) if a.stop else len(steps) - 1

    print(f"robot {lt.IP}: connecting to the Bridge Listen node ...")
    b = hb.Bridge()
    print(f"connected ({b.node}). Enter = next, s = skip, q = stop, x|y|z <mm>, rx|ry|rz <deg>, set|goto|jgoto X Y Z RX RY RZ, j1..j6 <deg>, j, delete, b = back, step <n>, open, close, save, f = force\n")
    done = names[i - 1] if i > 0 and "move" in steps[i - 1] else None   # what 'save' teaches (the last move)
    adj = np.eye(4)                                     # your nudges since the last GRIP/RELEASE/joint move:
    hist = []                                           # (step index, pose/joints before it) of each move done, for 'b'
    while i <= last:                                    # applied to the following straight-line targets too
        s = steps[i]
        print(f"[{i}] next: {describe(s)}")
        if "move" in s:                                 # now / next / diff under each other (Bjørge, 2026-11-20)
            try:
                F, _, qn = state(2)
                nx = s["flange"]
                fmt = lambda v: " ".join(f"{x:8.2f}" for x in v)   # noqa: E731
                d = [nx[k] - F[k] for k in range(3)] + [((nx[k] - F[k] + 180) % 360) - 180 for k in range(3, 6)]
                print(f"      now   set {fmt(F)}\n      next  set {fmt(nx)}\n      diff      {fmt(d)}"
                      f"   ({np.linalg.norm(d[:3]):.1f} mm)")
                print(joint_bars(qn, s["joints"]))
            except OSError:
                pass
        cmd = input("> ").strip().lower()
        if cmd == "j":                                  # joint bars now (2026-11-20, Bjørge)
            _, _, qn = state(2)
            print(joint_bars(qn, s["joints"] if "move" in s else None))
            continue
        m = re.fullmatch(r"j([1-6])\s*([-+]?\d*\.?\d+)", cmd)
        if m:                                           # turn ONE joint (joint move, max 60 deg)
            jn, dj = int(m.group(1)) - 1, float(m.group(2))
            if abs(dj) > 60:
                print("    at most 60 deg per joint turn")
                continue
            F, _, qn = state(2)
            q = list(qn)
            q[jn] += dj
            lo, hi = K.LIMITS[jn]
            if not lo + 2 <= q[jn] <= hi - 2:
                print(f"    J{jn + 1} would go to {q[jn]:.1f} - outside its limits {lo}..{hi}; not moved")
                continue
            hist.append((i, list(F), list(qn)))
            b.r.move(ptp(q, 20))
            adj = np.eye(4)
            _, _, qn = state(2)
            print(joint_bars(qn, s["joints"] if "move" in s else None))
            continue
        if cmd in ("q", "stop"):                    # 2026-11-20: s = skip now (Bjørge), q = stop
            break
        if cmd in ("s", "skip"):
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
                print(f"    jumped to [{k}] ({describe(t).split('  ')[0].strip()}): Enter does it where the arm is now")
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
        m = re.fullmatch(r"goto((?:\s+[-+]?\d*\.?\d+){6})", cmd)
        if m:                                           # 2026-11-20 (Bjørge): straight to an exact pose, slowly
            target = [float(v) for v in m.group(1).split()]
            F, _, _ = state()
            dist = float(np.linalg.norm(np.array(target[:3]) - F[:3]))
            dang = max(abs(((target[k] - F[k] + 180) % 360) - 180) for k in range(3, 6))
            if dist > 150 or dang > 60:
                print(f"    goto: {dist:.0f} mm / {dang:.0f} deg away - too far for one straight move "
                      "(max 150 mm / 60 deg); go closer first")
                continue
            print(f"    goto: straight line {dist:.1f} mm, {dang:.1f} deg, 10 mm/s ...")
            b.r.move(line(target, 10))
            G, _, _ = state()
            adj = np.eye(4)                             # an exact pose: no nudges carried on
            print(f"    now x {G[0]:.2f} y {G[1]:.2f} z {G[2]:.2f}  rx {G[3]:.2f} ry {G[4]:.2f} rz {G[5]:.2f}"
                  "   ('save' stores it as the last move)")
            continue
        m = re.fullmatch(r"jgoto((?:\s+[-+]?\d*\.?\d+){6})", cmd)
        if m:                                           # 2026-11-20: a straight 'set' line ran into a wrist singularity;
            target = [float(v) for v in m.group(1).split()]   # a JOINT move to the same pose has no singularity problem
            F, _, q_now = state(2)
            seed = s["joints"] if "move" in s else list(q_now)    # the program's joint setup for the next step
            q = K.ik(target, seed)
            if q is None or not K.within_limits(q):
                print("    jgoto: no reachable joint solution for that pose - not moved")
                continue
            names6 = ("J1", "J2", "J3", "J4", "J5", "J6")
            print("    jgoto = JOINT move (a curve, not a straight line - the part swings; look around first), 20 %:")
            for j in range(6):
                print(f"      {names6[j]} {q_now[j]:8.1f} -> {q[j]:8.1f}   ({q[j] - q_now[j]:+.1f})")
            if input("    move? y = yes, anything else = no: ").strip().lower() != "y":
                print("    not moved")
                continue
            hist.append((i, list(F), list(q_now)))
            b.r.move(ptp(q, 20))
            G, _, _ = state(2)
            adj = np.eye(4)
            print(f"    now x {G[0]:.2f} y {G[1]:.2f} z {G[2]:.2f}  rx {G[3]:.2f} ry {G[4]:.2f} rz {G[5]:.2f}")
            continue
        if cmd == "delete":                           # 2026-11-20 (Bjørge): drop the NEXT step for good, after a y
            if "move" not in s:
                print("    delete: only moves can be deleted (not GRIP/RELEASE)")
                continue
            if input(f"    delete step [{i}] '{s['name']}' for good? y = yes, anything else = no: ").strip().lower() != "y":
                print("    not deleted")
                continue
            dfile = HERE / f"{a.cell}_deleted.json"
            d = json.loads(dfile.read_text(encoding="utf-8")) if dfile.exists() else {"deleted": []}
            if s["name"] not in d["deleted"]:
                d["deleted"].append(s["name"])
            dfile.write_text(json.dumps(d, indent=1), encoding="utf-8")
            print(f"    deleted '{s['name']}' (listed in {dfile.name}; the build skips it). Undo: remove it from that file.")
            del steps[i]
            names = [x.get("name") or f'{x.get("gripper")} {k}' for k, x in enumerate(steps)]
            last -= 1
            continue
        m = re.fullmatch(r"set((?:\s+[-+]?\d*\.?\d+){6})", cmd)
        if m:                                           # 2026-11-20 (Bjørge): change the NEXT step's target first
            if "move" not in s:
                print("    set: the next step is not a move")
                continue
            target = [float(v) for v in m.group(1).split()]
            # 2026-11-20: a 'set' with a wrong angle swung the tool ~90 deg and faulted the robot. Checked against
            # the STEP'S OWN target (not the current pose), so planned turns (frame flip, tilted approaches) are fine
            # and only a change of > 150 mm / > 60 deg from the step's target, or a different joint setup, is refused.
            plan = s.get("planned_set", s["flange"])
            dist0 = float(np.linalg.norm(np.array(target[:3]) - np.array(plan[:3])))
            dang0 = max(abs(((target[k] - plan[k] + 180) % 360) - 180) for k in range(3, 6))
            if dist0 > 150 or dang0 > 60:
                print(f"    set REFUSED: {dist0:.0f} mm / {dang0:.0f} deg from this step's own target "
                      f"(max 150 mm / 60 deg). You typed: x {target[0]} y {target[1]} z {target[2]} "
                      f"rx {target[3]} ry {target[4]} rz {target[5]} - check the order and signs")
                continue
            q = K.ik(target, s["joints"])
            if q is None:
                print("    set: the robot can't reach that pose - not changed")
                continue
            if max(abs(q[j] - s["joints"][j]) for j in range(6)) > 30:
                print(f"    set REFUSED: the arm would need a different joint setup than this step (a joint turns "
                      f"{max(abs(q[j] - s['joints'][j]) for j in range(6)):.0f} deg more) - not changed")
                continue
            s.setdefault("planned_set", list(s["flange"]))     # several sets in a row: still measured from the plan
            s["flange"], s["joints"] = target, [float(v) for v in q]
            adj = np.eye(4)                             # the new target is exact: no nudges added on top
            F, _, _ = state()
            dist = float(np.linalg.norm(np.array(target[:3]) - F[:3]))
            print(f"    [{i}] {s['name']} now goes to x {target[0]:.2f} y {target[1]:.2f} z {target[2]:.2f}  "
                  f"rx {target[3]:.2f} ry {target[4]:.2f} rz {target[5]:.2f}  (J6 {q[5]:.1f}), {dist:.0f} mm from here. "
                  "Enter = go there; 'save' after it keeps it. (This run only until saved.)")
            continue
        m = re.fullmatch(r"(r?)([xyz])\s*([-+]?\d*\.?\d+)", cmd)
        if m:
            F, tq0, _ = state()
            rot, ax, d = m.group(1) == "r", m.group(2), float(m.group(3))
            if (rot and abs(d) > 60) or (not rot and abs(d) > 30):
                print("    at most 30 mm / 60 deg per nudge")
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
            r = subprocess.run([sys.executable, str(HERE / "robot_sim" / "teach.py"), teach_v, done, "--real",
                                "--with-rotation", "--now", "--max-mm", "300"], cwd=RC, capture_output=True, text=True)
            print("    " + "\n    ".join(l for l in (r.stdout + r.stderr).splitlines() if "stored" in l or "rror" in l
                                          or "refuse" in l) or "    (no output)")
            r = subprocess.run([sys.executable, str(HERE / "robot_sim" / "teach.py"), teach_v, "--rebuild"], cwd=RC,
                               capture_output=True, text=True)
            steps = load()
            adj = np.eye(4)                             # the saved pose is in the program now
            G, _, _ = state(2)
            print(f"    saved '{done}' at   set {' '.join(f'{x:.2f}' for x in G)}")
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
            elif "wait_ms" in s:                    # Program.wait: the arm stands still (the full run's help pause)
                print(f"    waiting {s['wait_ms'] / 1000:.0f} s ...")
                time.sleep(s["wait_ms"] / 1000)
            elif "reload" in s:                     # bench_cell_v8 Program.reload (v8x2): people reload, the robot waits
                view(t="spawn", parts=list(s.get("spawn", {})), stage=s.get("stage"))   # the 3D page shows the new parts
                input(f"    reload the jig ({s['reload']}: frames, interface pieces, planks), then Enter ")
                b.r.status("00")                        # still in the Listen node (raises if the session dropped)
            elif s.get("gripper") == "grip":
                b.grip()                                # nudges kept: the lift goes straight up from here
                view_grip(s.get("parts", []))           # the 3D page carries the program's parts from here
                print("    GRIP OK")
            elif s.get("gripper") == "release":         # release (load() keeps no other gripper steps)
                b.release()                             # nudges kept: out/up go straight from here
                view_release(s.get("parts", []))
                print("    RELEASE done")
            else:                                       # a step type this tool doesn't know: never a gripper action
                print(f"    skipped: unknown step {s.get('name', '')!r} (no robot or gripper action)")
        except hb.GripLost as e:
            view_grip([], ok=False)
            print(f"    !! {e}. Fix it (TMflow: clear the message, restart the project) and run again with --from")
            break
        i += 1
    b.r.s.close()
    print("stopped. The robot stays where it is; TMflow waits in the Listen node.")


if __name__ == "__main__":
    main()
