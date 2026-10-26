"""Listen-node pick-and-place test: the laptop drives the real TM5-900 over the network (no USB).
The Hand-E gripper only works through its TMflow components (Robotiq HANDE_V002 SET/GRIP/RELEASE),
so the TMflow project alternates Listen nodes and gripper nodes. The script leaves a Listen node
with ScriptExit(), the flow runs the gripper node, and the script reconnects to the next Listen node.

TMflow project "TestProject" (Manual mode), SET with Initialize_or_Not = true:
    Start -> SET -> RELEASE -> Listen -> GRIP -> Listen -> RELEASE -> Listen
Positions are taught by hand-guiding (no RoboDK model involved), as flange poses in the robot base.

    python robot_cell/tests/listen_pick_place_test.py teach pick       fingers open around the box
    python robot_cell/tests/listen_pick_place_test.py teach place      the drop spot (leave the robot here)
    python robot_cell/tests/listen_pick_place_test.py run --above 50   dry run 50 mm above both spots
    python robot_cell/tests/listen_pick_place_test.py run              the real pick and place
    python robot_cell/tests/listen_pick_place_test.py status           which Listen node the flow waits in
    python robot_cell/tests/listen_pick_place_test.py pass             leave that Listen node (Pass exit)
    python robot_cell/tests/listen_pick_place_test.py up 50            straight up 50 mm (-50 = down), stays in the node
"""
import argparse
import json
import re
import socket
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
POINTS = HERE / "listen_test_points.json"
IP = "10.0.12.101"                                      # lab robot controller
LISTEN, SLAVE = 5890, 5891                              # Listen node, Ethernet Slave (state stream)
LIFT = 100                                              # approach/retract height [mm]
SPEED = 50                                              # Line speed [mm/s]
ACC = 500                                               # time to reach that speed [ms]


def packet(header, data):
    """$HEADER,<bytes in data>,data,*CS   CS = XOR of every byte between $ and *."""
    body = f"{header},{len(data.encode())},{data},"
    cs = 0
    for b in body.encode():
        cs ^= b
    return f"${body}*{cs:02X}\r\n".encode()


def read_state():
    """Joint angles and flange pose (robot base) from the Ethernet Slave stream. Read-only."""
    with socket.create_connection((IP, SLAVE), timeout=3) as s:
        buf = b""
        while buf.count(b"$TMSVR") < 3:
            buf += s.recv(4096)
    pkt = buf.split(b"$TMSVR")[-2].decode()            # last complete packet
    get = lambda key: [float(v) for v in re.search(key + r"=\{([^}]*)\}", pkt).group(1).split(",")]
    return {"joints": get("Joint_Angle"), "flange": get("Coord_Robot_Flange")}


def line(pose, dz=0):
    """Straight-line move of the flange to pose, dz mm higher. CAP = Cartesian, mm/s, % blend."""
    x, y, z, rx, ry, rz = pose
    xyz = ",".join(f"{v:.3f}" for v in (x, y, z + dz, rx, ry, rz))
    return f'Line("CAP",{xyz},{SPEED},{ACC},0,false)'


class Listen:
    """One Listen node session: connect when the flow reaches it, leave with exit()."""

    def __init__(self, timeout=60):
        t0 = time.time()
        while True:                                     # 5890 opens when the flow enters the node
            try:
                self.s = socket.create_connection((IP, LISTEN), timeout=2)
                break
            except OSError:
                if time.time() - t0 > timeout:
                    raise TimeoutError("no Listen node on 5890: is TestProject running?")
                time.sleep(0.5)
        self.s.settimeout(30)
        self.buf, self.n = b"", 0
        if "true" not in self.status("00"):
            raise RuntimeError("connected, but the robot is not in Listen mode")
        self.script('ChangeBase("RobotBase")\r\nChangeTCP(0,0,0,0,0,0)')   # flange, as taught

    def reply(self, header):
        while True:
            while b"\r\n" not in self.buf:
                chunk = self.s.recv(4096)
                if not chunk:
                    raise ConnectionError("Listen node closed the connection (project stopped?)")
                self.buf += chunk
            msg, self.buf = self.buf.split(b"\r\n", 1)
            msg = msg.decode(errors="replace")
            if msg.startswith("$CPERR"):
                raise RuntimeError(f"packet error: {msg}")
            if msg.startswith("$" + header):
                return msg

    def status(self, data):
        self.s.sendall(packet("TMSTA", data))
        return self.reply("TMSTA")

    def script(self, code):
        self.n += 1
        self.s.sendall(packet("TMSCT", f"{self.n},{code}"))
        r = self.reply("TMSCT")
        if ",OK," not in r:
            raise RuntimeError(f"robot rejected {code!r}: {r}")

    def move(self, *cmds):
        """Queue the moves plus a tag, then wait until the robot has reached the tag."""
        tag = self.n % 15 + 1
        self.script("\r\n".join(cmds + (f"QueueTag({tag},0)",)))
        while True:
            f = self.status(f"01,{tag}").split(",")     # $TMSTA,len,01,tag,true|false|none,*CS
            if int(f[3]) == tag and f[4] == "true":
                return
            time.sleep(0.2)

    def exit(self):
        """Leave the Listen node: the flow runs the next HANDE node, then the next Listen node."""
        self.script("ScriptExit()")
        self.s.close()
        time.sleep(1)                                   # let this node close before reconnecting


def teach(name):
    if name not in ("pick", "place"):
        raise SystemExit("teach pick | teach place")
    pts = json.loads(POINTS.read_text()) if POINTS.exists() else {}
    pts[name] = read_state()
    POINTS.write_text(json.dumps(pts, indent=2))
    print(f"{name}: flange {pts[name]['flange']}\n{' ' * len(name)}  joints {pts[name]['joints']}")


def run(above):
    pts = json.loads(POINTS.read_text())
    pick, place = pts["pick"]["flange"], pts["place"]["flange"]
    start = read_state()["flange"]
    print(f"start z {start[2]:.0f} -> up {LIFT} mm")
    print(f"pick  ({pick[0]:.0f}, {pick[1]:.0f})  z {pick[2] + above:.0f}  (approach z {pick[2] + above + LIFT:.0f})")
    print(f"place ({place[0]:.0f}, {place[1]:.0f})  z {place[2] + above:.0f}  (approach z {place[2] + above + LIFT:.0f})")
    input("Manual mode, low project speed, hand on the E-stop, TestProject running. Enter to start ")

    r = Listen()                                        # Listen 1, gripper opened by the flow
    r.move(line(start, LIFT), line(pick, above + LIFT), line(pick, above))
    r.exit()                                            # -> GRIP
    r = Listen()                                        # Listen 2
    r.move(line(pick, above + LIFT), line(place, above + LIFT), line(place, above))
    r.exit()                                            # -> RELEASE
    r = Listen()                                        # Listen 3
    r.move(line(place, above + LIFT))
    r.exit()                                            # -> end of the flow
    print("done")


def status():
    """Status query only: true/false + the Listen node's name, or closed if the flow isn't in one."""
    try:
        with socket.create_connection((IP, LISTEN), timeout=3) as s:
            s.settimeout(3)
            s.sendall(packet("TMSTA", "00"))
            print(s.recv(4096).decode().strip())     # $TMSTA,15,00,true,Listen1,*79
    except OSError:
        print("5890 closed: the flow is not in a Listen node")


def leave():
    """The Pass exit: ScriptExit() on the Listen node the flow is waiting in."""
    status()
    Listen(timeout=3).exit()
    print("ScriptExit() OK: flow continues from Pass")


def up(dz):
    """Straight up dz mm (negative = down) from where the flange is now; stays in the Listen node."""
    p = read_state()["flange"]
    cmd = line(p, dz)
    print("sending:", packet("TMSCT", f"1,{cmd}").decode().strip())
    r = Listen(timeout=3)
    r.move(cmd)
    r.s.close()                                         # no ScriptExit: the flow keeps waiting here
    print(f"z {p[2]:.1f} -> {read_state()['flange'][2]:.1f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["teach", "run", "status", "pass", "up"])
    ap.add_argument("arg", nargs="?", help="teach: pick | place,  up: mm (negative = down)")
    ap.add_argument("--above", type=float, default=0, help="extra height on pick/place [mm] (dry run)")
    a = ap.parse_args()
    {"teach": lambda: teach(a.arg), "run": lambda: run(a.above), "status": status, "pass": leave,
     "up": lambda: up(float(a.arg))}[a.cmd]()
