"""Log the real robot's position from its Ethernet Slave stream (read-only, port 5891).

    python robot_cell/log_points.py "right down"     log one point under that label
    python robot_cell/log_points.py --show           print the current position, log nothing

Averages 0.3 s of the stream and refuses to log if the arm is still moving.
Appends to robot_cell/real_points.json: label, time, joints (deg), flange X Y Z RX RY RZ
(mm, deg, robot base). Only the Python standard library.
"""
import json
import re
import socket
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
LOG = HERE / "real_points.json"
ROBOT = ("10.0.12.101", 5891)
STILL_MM = 0.05                     # max spread of the flange position while logging


def packets(seconds=0.3):
    """Joint_Angle and Coord_Robot_Flange of every packet received in `seconds`."""
    s = socket.create_connection(ROBOT, timeout=5)
    s.settimeout(3)
    buf, t0 = b"", time.time()
    while time.time() - t0 < seconds:
        buf += s.recv(65536)
    s.close()
    out = []
    for p in buf.split(b"$TMSVR")[1:-1]:                  # the last one may be cut off
        items = dict(re.findall(r"(\w+)=([^\r\n]+)", p.decode("utf-8", "replace")))
        if "Joint_Angle" in items and "Coord_Robot_Flange" in items:
            num = lambda k: [float(x) for x in items[k].strip("{}").split(",")]
            out.append((num("Joint_Angle"), num("Coord_Robot_Flange")))
    return out


def reading():
    pk = packets()
    if not pk:
        sys.exit("no data from the robot (Ethernet Slave on? cable?)")
    mean = lambda rows: [sum(c) / len(c) for c in zip(*rows)]
    flanges = [f for _, f in pk]
    spread = max(max(c) - min(c) for c in list(zip(*flanges))[:3])
    return mean([j for j, _ in pk]), mean(flanges), spread, len(pk)


def main():
    joints, flange, spread, n = reading()
    print(f"flange X Y Z RX RY RZ: {', '.join(f'{v:.2f}' for v in flange)}   ({n} packets, spread {spread:.3f} mm)")
    if len(sys.argv) < 2 or sys.argv[1] == "--show":
        return
    if spread > STILL_MM:
        sys.exit(f"arm is moving ({spread:.2f} mm in 0.3 s), not logged")
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    log.append({"label": sys.argv[1], "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "joints": [round(v, 4) for v in joints], "flange": [round(v, 4) for v in flange]})
    LOG.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"logged '{sys.argv[1]}' ({len(log)} points in {LOG.name})")


if __name__ == "__main__":
    main()
