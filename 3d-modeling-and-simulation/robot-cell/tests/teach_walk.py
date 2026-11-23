"""Walk through the grip points of a program and teach each one by hand (FreeBot / jog), no Listen node needed.

    python tests/teach_walk.py v11_1plank [--from 3]

Shows the robot's live pose (Modbus 7001, read-only) and the next grip point. Move the arm there by hand (TMflow
FreeBot, lock the axes you don't want), then:
    Enter  save it: teach.py <version> <point> --real --now --with-rotation (as step_run's 'save'), next point
    s      skip this point          b   back one point          q   quit
Every saved pose is also kept raw in tests/<version>_real_points.json. Afterwards: teach.py <version> --rebuild.
"""
import json
import msvcrt
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RC = HERE.parent
IP = "10.0.12.101"


def pose():
    s = socket.create_connection((IP, 502), timeout=2)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 4, 7001, 12))
    r = s.recv(64)
    s.close()
    return struct.unpack(">6f", r[9:33])


def points(version):
    out = subprocess.run([sys.executable, str(HERE / "robot_sim" / "teach.py"), version, "--list"], cwd=RC,
                         capture_output=True, text=True).stdout.splitlines()[1:]
    names = []
    for line in out:
        parts = line.split()
        if len(parts) < 3 or not parts[0].isdigit():
            continue
        rest = line.split(None, 2)[2]
        names.append((parts[1], rest.split("->")[-1].split("[")[0].split("(")[0].replace("*", "").strip().lower()))
    return names


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v11_1plank"
    i = int(sys.argv[sys.argv.index("--from") + 1]) - 1 if "--from" in sys.argv else 0
    pts = points(version)
    raw_file = HERE / f"{version}_real_points.json"
    print(f"{len(pts)} grip points. Move the arm by hand, Enter = save, s = skip, b = back, q = quit.\n")
    while 0 <= i < len(pts):
        kind, name = pts[i]
        print(f"\n[{i + 1}/{len(pts)}] {kind.upper()}: {name}")
        while True:
            try:
                p = pose()
                sys.stdout.write(f"\r  now  X {p[0]:8.2f}  Y {p[1]:8.2f}  Z {p[2]:8.2f}   Rx {p[3]:7.2f}  Ry {p[4]:6.2f}  "
                                 f"Rz {p[5]:7.2f}   ")
                sys.stdout.flush()
            except OSError:
                sys.stdout.write("\r  (no answer from the robot)                                            ")
            if msvcrt.kbhit():
                k = msvcrt.getwch().lower()
                if k == "q":
                    print("\nquit. Next: python tests/robot_sim/teach.py", version, "--rebuild")
                    return
                if k == "s":
                    print("\n  skipped")
                    i += 1
                    break
                if k == "b":
                    i = max(0, i - 1)
                    print("\n  back")
                    break
                if k in "\r\n":
                    r = subprocess.run([sys.executable, str(HERE / "robot_sim" / "teach.py"), version, name, "--real",
                                        "--now", "--with-rotation", "--max-mm", "300"], cwd=RC, capture_output=True,
                                       text=True)
                    msg = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
                    print("\n  " + "\n  ".join(msg[-3:]))
                    if r.returncode == 0:
                        d = json.loads(raw_file.read_text()) if raw_file.exists() else {"points": {}}
                        d.setdefault("points", {})[name] = {"flange": [round(v, 2) for v in p],
                                                            "how": "taught by hand (teach_walk.py)",
                                                            "time": time.strftime("%Y-%m-%d %H:%M")}
                        raw_file.write_text(json.dumps(d, indent=1), encoding="utf-8")
                        i += 1
                    else:
                        print("  NOT saved - move closer or check the point, then Enter again")
                    break
            time.sleep(0.25)
    print("\nall points done. Next: python tests/robot_sim/teach.py", version, "--rebuild")


if __name__ == "__main__":
    main()
