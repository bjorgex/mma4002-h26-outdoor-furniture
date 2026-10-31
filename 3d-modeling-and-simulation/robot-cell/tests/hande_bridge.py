"""Python does every move, TMflow does the gripper. The script asks for GRIP, RELEASE or Home by
setting var_cmd before it leaves the Listen node, so any sequence runs on one fixed TMflow flow.

TMflow project "HandE_Bridge_v1" (Manual mode). Project variable: integer cmd (TMflow shows var_cmd), start 0.
    Start -> Home -> SET1 -> (OK|FAIL) -> Bridge
    Bridge Pass -> Gateway   var_cmd == 1 -> GRIP1      OK -> Bridge     FAIL|LOSS -> Lost
                             var_cmd == 2 -> RELEASE1   OK|FAIL -> Bridge
                             var_cmd == 3 -> Home2      -> Bridge        (same pose as Home)
                             else         -> Stop
    Lost Pass -> Bridge.     Bridge Fail, Lost Fail -> Stop.

    python robot_cell/tests/hande_bridge.py check             gripper and Home2 only, no Python moves
    python robot_cell/tests/hande_bridge.py demo --above 50   box A -> B -> A, 50 mm above both (dry run)
    python robot_cell/tests/hande_bridge.py demo              the real thing
    python robot_cell/tests/hande_bridge.py pickplace --air   from Home: open, down, grip, up, left, down, release
Spots A and B are the ones listen_pick_place_test.py teaches ("teach pick", "teach place").
"""
import argparse
import json
import time

import listen_pick_place_test as lt

BRIDGE, LOST = "Listen1", "Listen2"                     # TMflow names Listen nodes itself: Bridge, Lost
GRIP, RELEASE, HOME = 1, 2, 3                           # var_cmd values the Gateway branches on


class GripLost(RuntimeError):
    pass


class Bridge:
    """Session with the Bridge flow. dry: an empty grip (Lost) is expected and the sequence goes on."""

    def __init__(self, above=0, dry=False):
        self.above, self.dry, self.lost = above, dry, False
        self._connect()

    def _connect(self, timeout=60):
        t0 = time.time()
        while True:                                     # 5890 can answer "not listening" while a gripper node runs
            try:
                self.r = lt.Listen(timeout=timeout)
                break
            except RuntimeError:
                if time.time() - t0 > timeout:
                    raise
                time.sleep(0.5)
        self.r.script("var_cmd = 0")                    # a bare ScriptExit() goes to Stop, never repeats a grip
        self.node = self.r.status("00").split(",")[4]
        if self.node not in (BRIDGE, LOST):
            raise RuntimeError(f"in Listen node {self.node!r}: is HandE_Bridge_v1 running?")

    def _handover(self, cmd):
        """Set var_cmd, leave the node, reconnect when the flow is back in a Listen node."""
        self.r.script(f"var_cmd = {cmd}")
        self.r.exit()
        self._connect()

    def move(self, spot):
        """Up LIFT mm from here, across at that height, then straight down onto spot (+ above)."""
        here = lt.read_state()["flange"]
        self.r.move(lt.line(here, lt.LIFT), lt.line(spot, self.above + lt.LIFT), lt.line(spot, self.above))

    def lift(self):
        self.r.move(lt.line(lt.read_state()["flange"], lt.LIFT))

    def grip(self):
        self._handover(GRIP)
        self.lost = self.node == LOST
        if self.lost:
            self.r.exit()                               # Lost Pass -> Bridge
            self._connect()
            if not self.dry:
                raise GripLost("GRIP found no object between the fingers")

    def release(self):
        self._handover(RELEASE)

    def home(self):
        self._handover(HOME)

    def finish(self):
        """Lift, drive to Home2, and leave the flow waiting in Bridge for the next run."""
        self.lift()
        self.home()
        self.r.s.close()


def check():
    print("HandE_Bridge_v1 running in Manual mode, nothing near the fingers.")
    print("TMflow will open and close the gripper and go to Home2. Python moves nothing.")
    input("Enter to connect ")
    try:
        b = Bridge(dry=True)
    except RuntimeError as e:
        raise SystemExit(f"{e}\nIf var_cmd = 0 was rejected: is there an integer project variable 'cmd'?")
    print(f"1/4 in {b.node}, and the Listen node accepted var_cmd = 0")
    input("Enter: var_cmd = 2, RELEASE1 opens the fingers ")
    b.release()
    print(f"2/4 back in {b.node}")
    input("Enter: var_cmd = 1, GRIP1 closes on air ")
    b.grip()
    print(f"3/4 GRIP1 took {'FAIL or LOSS, through Lost' if b.lost else 'OK'}, back in {b.node}")
    input("Enter: var_cmd = 3, TMflow goes to Home2 ")
    b.home()
    b.r.s.close()
    print(f"4/4 back in {b.node}. All three branches work; the flow waits in Bridge.")


def demo(above):
    pts = json.loads(lt.POINTS.read_text())
    A, B = pts["pick"]["flange"], pts["place"]["flange"]
    print(f"A ({A[0]:.0f}, {A[1]:.0f}) z {A[2] + above:.0f}   B ({B[0]:.0f}, {B[1]:.0f}) z {B[2] + above:.0f}")
    input("Manual mode, low project speed, hand on the E-stop, HandE_Bridge_v1 running. Enter to start ")
    b = Bridge(above, dry=above > 0)
    try:
        b.move(A)
        b.grip()
        b.move(B)
        b.release()
        b.move(B)
        b.grip()
        b.move(A)
        b.release()
    except GripLost:
        b.release()
        b.finish()
        raise SystemExit("Stopped: GRIP found no object. Fingers open, arm at Home, flow waiting in Bridge.")
    b.finish()
    print("Done. Arm at Home, flow waiting in Bridge: run again any time.")


DOWN, UP, LEFT = 100, 50, 100                           # pickplace distances [mm]; left = +Y of the robot base


def offset(pose, dx=0, dy=0, dz=0):
    x, y, z, rx, ry, rz = pose
    return lt.line([x + dx, y + dy, z + dz, rx, ry, rz])


def pickplace(air):
    """From Home: open, down, grip, up, left, down, release, home. Enter before every step."""
    input("HandE_Bridge_v1 running and waiting in Listen1 (arm at Home). Enter to connect ")
    b = Bridge(dry=air)
    s = lt.read_state()["flange"]
    print(f"start x {s[0]:.0f}  y {s[1]:.0f}  z {s[2]:.0f}")
    steps = [
        ("open the gripper", b.release),
        (f"down {DOWN} mm to z {s[2] - DOWN:.0f}", lambda: b.r.move(offset(s, dz=-DOWN))),
        ("grip", b.grip),
        (f"up {UP} mm to z {s[2] - DOWN + UP:.0f}", lambda: b.r.move(offset(s, dz=-DOWN + UP))),
        (f"left {LEFT} mm to y {s[1] + LEFT:.0f}", lambda: b.r.move(offset(s, dy=LEFT, dz=-DOWN + UP))),
        (f"down {UP} mm to z {s[2] - DOWN:.0f}", lambda: b.r.move(offset(s, dy=LEFT, dz=-DOWN))),
        ("release", b.release),
        ("lift 100 mm and go Home", b.finish),
    ]
    try:
        for i, (what, do) in enumerate(steps, 1):
            input(f"{i}/{len(steps)} Enter: {what} ")
            do()
    except GripLost:
        print("GRIP found no object: opening and going Home")
        b.release()
        b.finish()
        raise SystemExit("stopped (run with --air to grip on air without stopping)")
    print("done, flow waiting in Listen1")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "demo", "pickplace"])
    ap.add_argument("--above", type=float, default=0, help="demo: extra height on both spots [mm]; > 0 = dry run")
    ap.add_argument("--air", action="store_true", help="pickplace: no object, an empty grip is expected")
    ap.add_argument("--speed", type=int, default=lt.SPEED, help=f"straight-line speed [mm/s], default {lt.SPEED}")
    a = ap.parse_args()
    lt.SPEED = min(a.speed, 250)                        # Manual mode limits the tool to 250 mm/s anyway
    print(f"speed {lt.SPEED} mm/s (TMflow's project speed % scales this down further)")
    {"check": check, "demo": lambda: demo(a.above), "pickplace": lambda: pickplace(a.air)}[a.cmd]()
