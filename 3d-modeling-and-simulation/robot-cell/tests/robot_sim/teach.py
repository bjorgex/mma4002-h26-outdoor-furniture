"""Teach the grip points on the real robot: jog the TM5 to where a grip (or its approach) really is, press Enter on
the laptop, and the correction goes into robot-cell/teach_<version>.json; the program builder applies it on the
next build (teach_overrides.apply in bench_cell_<version>.py's Program.move). Read-only towards the robot: it only
listens to the Ethernet Slave stream (port 5891, Coord_Robot_Flange + Joint_Angle), it never moves the arm.

    python tests/robot_sim/teach.py v8 --list                         grip events: approach + grip move names
    python tests/robot_sim/teach.py v8 "plank2 pick" --real           live offset to the plan; Enter = take it
    python tests/robot_sim/teach.py v8 "plank2 pick approach" --real  teach an approach on its own
    python tests/robot_sim/teach.py v8 "plank2 pick" --with-rotation  also keep the orientation you jogged to
    python tests/robot_sim/teach.py v8 --show                         what is taught
    python tests/robot_sim/teach.py v8 --clear "plank2 pick"          forget one
    python tests/robot_sim/teach.py v8 --rebuild                      program + TMflow zip with the corrections

Default robot = the mock (127.0.0.1:5891, tests/tmflow_mock.py serve); --real = the lab TM5 (10.0.12.101:5891).
Run from robot-cell/.
"""
import argparse
import importlib
import json
import math
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CELL = HERE.parents[1]
sys.path.insert(0, str(CELL))
import teach_overrides as TO                              # noqa: E402

REAL_IP, SLAVE = "10.0.12.101", 5891
STILL_MM = 0.05                                           # max spread of the flange position while taking a point


# --- the Ethernet Slave stream ($TMSVR, STRING or JSON mode)
def _items(pkt):
    """Joint_Angle / Coord_Robot_Flange from one $TMSVR packet's text."""
    out = {}
    for k in ("Joint_Angle", "Coord_Robot_Flange"):
        m = re.search(k + r"\s*=\s*\{([^}]*)\}", pkt) or \
            re.search(r'"Item"\s*:\s*"' + k + r'"\s*,\s*"Value"\s*:\s*\[([^\]]*)\]', pkt)
        if m:
            out[k] = [float(v) for v in m.group(1).split(",")]
    return out


class Stream:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=5)
        self.s.settimeout(3)
        self.buf = b""

    def read(self, seconds=0.0):
        """Every complete packet's (joints, flange) for `seconds` (0: until at least one)."""
        out, t0 = [], time.time()
        while True:
            try:
                self.buf += self.s.recv(65536)
            except socket.timeout:
                raise SystemExit("no data on the Ethernet Slave port (TMflow: Ethernet Slave enabled? cable / IP?)")
            parts = self.buf.split(b"$TMSVR")
            self.buf = b"$TMSVR" + parts[-1] if len(parts) > 1 else parts[-1]   # last one may be cut off
            for p in parts[1:-1]:
                it = _items(p.decode("utf-8", "replace"))
                if len(it) == 2:
                    out.append((it["Joint_Angle"], it["Coord_Robot_Flange"]))
            if out and time.time() - t0 >= seconds:
                return out

    def still_pose(self, seconds=0.3):
        """Mean joints + flange over `seconds`, and the position spread (mm)."""
        pk = self.read(seconds)
        fl = np.array([f for _, f in pk])
        spread = float(max(fl[:, i].max() - fl[:, i].min() for i in range(3)))
        joints = np.mean([j for j, _ in pk], axis=0).tolist()
        # angles: average as unit vectors (rx near +-180 deg would average to 0)
        ang = [math.degrees(math.atan2(np.sin(np.radians(fl[:, i])).mean(), np.cos(np.radians(fl[:, i])).mean()))
               for i in range(3, 6)]
        return joints, fl[:, :3].mean(axis=0).tolist() + ang, spread, len(pk)

    def close(self):
        self.s.close()


# --- the program
def builder(version):
    return importlib.import_module(f"bench_cell_{version}")


def program(version):
    B = builder(version)
    moves_file = B.TESTS / f"{version}_moves.json"
    steps = json.loads(moves_file.read_text(encoding="utf-8"))["steps"]
    PLATE_inv = np.linalg.inv(B.PLATE)
    tip = np.eye(4)
    tip[2, 3] = B.TIP

    def flange_to_plate(f):
        return PLATE_inv @ TO.pose_to_T(f) @ tip

    def plate_T(s):                                        # planned (uncorrected) pose when the moves file has it
        return flange_to_plate(s.get("planned_flange", s["flange"]))

    return B, steps, flange_to_plate, plate_T, moves_file


def fmt(v, n=1):
    return " ".join(f"{x:+8.{n}f}" for x in v)


def do_list(version, data):
    B, steps, _, plate_T, mf = program(version)
    ev = TO.events_from_steps(steps, plate_T)
    taught = {n: t for e in data.get("events", {}).values() for n, t in e.get("taught", {}).items()}
    print(f"{mf.name}: {len(ev)} grip events (approach -> GRIP; * = taught, plate-frame shift in mm)")
    for k, (name, e) in enumerate(ev.items(), 1):
        def tag(n):
            return f"*{n} ({fmt(taught[n]['plate_delta_mm'])})" if n in taught else n
        appr = e["approach"]
        print(f"{k:2d} {e['kind']:7s} " + "  ->  ".join([tag(n) for n in appr[-2:]] + [tag(name).upper() if name not in taught else tag(name)])
              + (f"   (+{len(appr) - 2} higher)" if len(appr) > 2 else "") + f"   [{len(e['follow'])} follow]")


def do_teach(a, data):
    B, steps, flange_to_plate, plate_T, _ = program(a.version)
    events = TO.events_from_steps(steps, plate_T)
    step = next((s for s in steps if s.get("name") == a.name and "move" in s), None)
    if step is None:
        raise SystemExit(f"no move '{a.name}' in the program (see --list)")
    if not any(a.name == e["grip"] or a.name in e["approach"] for e in events.values()):
        raise SystemExit(f"'{a.name}' is not a grip or an approach move (see --list)")
    T_plan = plate_T(step)
    planned_flange = step.get("planned_flange", step["flange"])
    print(f"'{a.name}' planned:\n  flange (robot base, TM X Y Z RX RY RZ): {fmt(planned_flange, 2)}\n"
          f"  TCP on the plate (x y z mm):           {fmt(T_plan[:3, 3], 1)}")
    st = Stream(a.host, a.port)
    print(f"connected to {a.host}:{a.port}. Jog the robot to the right spot, then Enter (q + Enter = cancel).")

    def offset(flange):
        T = flange_to_plate(flange)
        d = T[:3, 3] - T_plan[:3, 3]
        return T, d, T_plan[:3, :3].T @ d, TO.rot_deg(T_plan[:3, :3].T @ T[:3, :3])

    if not a.now:
        try:
            import msvcrt
        except ImportError:
            msvcrt = None
        while True:
            _, f = st.read()[-1]
            _, d, dt, r = offset(f)
            print(f"\r  now: plate dx dy dz {fmt(d)} mm | tool {fmt(dt)} mm | turned {r:5.2f} deg   ", end="", flush=True)
            if msvcrt is None:                             # no live display without msvcrt: one line, then wait
                if input().strip().lower() == "q":
                    raise SystemExit("cancelled")
                break
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch.lower() == "q":
                    raise SystemExit("\ncancelled")
                if ch in "\r\n":
                    print()
                    break
            time.sleep(0.1)
    joints, flange, spread, n = st.still_pose()
    st.close()
    if spread > STILL_MM:
        raise SystemExit(f"the arm is moving ({spread:.2f} mm in 0.3 s): nothing stored, try again")
    T_taught, d, dt, r = offset(flange)
    if np.linalg.norm(d) > a.max_mm:
        raise SystemExit(f"{np.linalg.norm(d):.1f} mm from the plan (> --max-mm {a.max_mm:g}): wrong move name or "
                         f"wrong spot? Nothing stored.")
    ev, C, dp = TO.record(data, events, a.name, T_plan, T_taught, flange, joints, a.with_rotation)
    TO.save(data, a.version)
    print(f"stored '{a.name}' (event '{ev}'): plate shift {fmt(dp)} mm, tool-frame correction {fmt(C['xyz'])} mm"
          + (f", rotation {fmt(C['rpy'], 2)} deg" if a.with_rotation else f" (orientation kept; you were {r:.2f} deg off)")
          + f"  [{n} packets, spread {spread:.3f} mm] -> {TO.path_for(a.version).name}")
    e = events[ev]
    if a.name == e["grip"]:
        own = [x for x in e["approach"] if x in data["events"][ev]["taught"]]
        print(f"  moves with it: approach {e['approach']}{' (except taught ' + str(own) + ')' if own else ''}, "
              f"follow {e['follow']}")
    print("  next: python tests/robot_sim/teach.py", a.version, "--rebuild")


def do_show(version, data):
    for ev, e in data.get("events", {}).items():
        for n, t in e.get("taught", {}).items():
            print(f"{n:28s} {t['time']}  plate {fmt(t['plate_delta_mm'])} mm  tool {fmt(t['correction']['xyz'])} mm"
                  + (f"  rpy {fmt(t['correction']['rpy'], 2)}" if t["correction"].get("rpy") else ""))
    if not any(e.get("taught") for e in data.get("events", {}).values()):
        print("nothing taught yet")


def do_rebuild(a):
    py = sys.executable
    r = subprocess.run([py, str(CELL / f"bench_cell_{a.version}.py")], cwd=CELL)
    if r.returncode:
        raise SystemExit(r.returncode)
    out = a.out or str(CELL / "bench_tmflow" / a.version / "AssembleBench.zip")
    Path(out).parent.mkdir(parents=True, exist_ok=True)            # e.g. bench_tmflow/v8x2/ the first time
    subprocess.run([py, str(HERE / "tmflow_export.py"), "export", str(CELL / "tests" / f"{a.version}_moves.json"),
                    "--base-from", str(CELL / "bench_tmflow" / "v7" / "AssembleBench.zip"), "-o", out], cwd=CELL, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version", help="cell version, e.g. v8 (bench_cell_v8.py, tests/v8_moves.json)")
    ap.add_argument("name", nargs="?", help="the move to teach: a grip or an approach (see --list)")
    ap.add_argument("--list", action="store_true", help="grip events of the program")
    ap.add_argument("--show", action="store_true", help="what is taught")
    ap.add_argument("--clear", metavar="NAME", help="forget a taught move ('all' = everything)")
    ap.add_argument("--rebuild", action="store_true", help="bench_cell_<v>.py + TMflow export with the corrections")
    ap.add_argument("--out", help="with --rebuild: the zip (default bench_tmflow/<v>/AssembleBench.zip)")
    ap.add_argument("--real", action="store_true", help=f"the lab robot ({REAL_IP})")
    ap.add_argument("--host", default="127.0.0.1", help="Ethernet Slave host (default: the mock)")
    ap.add_argument("--port", type=int, default=SLAVE, help=f"Ethernet Slave port (default {SLAVE})")
    ap.add_argument("--with-rotation", action="store_true", help="store the jogged orientation too (default: position)")
    ap.add_argument("--max-mm", type=float, default=30, help="refuse corrections larger than this (default 30)")
    ap.add_argument("--now", action="store_true", help="take the pose straight away (no Enter; scripts/tests)")
    a = ap.parse_args()
    if a.real:
        a.host = REAL_IP
    sys.path.insert(0, str(CELL))
    data = TO.load(a.version)
    if a.list:
        do_list(a.version, data)
    elif a.show:
        do_show(a.version, data)
    elif a.clear:
        for e in data.get("events", {}).values():
            for n in list(e.get("taught", {})):
                if a.clear in ("all", n):
                    del e["taught"][n]
                    print(f"forgot '{n}'")
        TO.save(data, a.version)
    elif a.rebuild:
        do_rebuild(a)
    elif a.name:
        do_teach(a, data)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
