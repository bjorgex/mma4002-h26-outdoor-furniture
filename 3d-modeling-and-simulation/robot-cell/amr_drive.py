"""The AMR drives the finished bench 2 m away along the table and comes back (RoboDK station script
"Deliver (AMR)").

    python robot_cell/amr_drive.py           also works from outside RoboDK

Needs only the robodk package. Everything under the station's "AMR" frame rides along: its plate,
top module and LD-250, and the bench once the robot program has set it down there (the program's
release puts the bench under the AMR frame).
"""
import time

from robodk import robolink, robomath

DISTANCE = 2000          # mm, along the ground base's x (away from the robot)
STEPS = 120              # per direction
PAUSE = 1.0              # s at the far end
OWN = ("AMR plate", "AMR top module")


def main():
    RDK = robolink.Robolink()
    amr = RDK.Item("AMR", robolink.ITEM_TYPE_FRAME)
    if not amr.Valid():
        raise SystemExit("no AMR in the open station")
    riding = [c for c in amr.Childs() if c.Type() == robolink.ITEM_TYPE_OBJECT and c.Name() not in OWN]
    home = amr.Pose()
    for out in (True, False):
        for i in range(1, STEPS + 1):
            s = i / STEPS if out else 1 - i / STEPS
            s = 0.5 - 0.5 * robomath.cos(robomath.pi * s)        # smooth start and stop
            amr.setPose(robomath.transl(DISTANCE * s, 0, 0) * home)
            RDK.Render(True)
            time.sleep(0.02)
        if out:
            time.sleep(PAUSE)
    amr.setPose(home)
    print(f"AMR drove {DISTANCE / 1000:.0f} m and back with {len(riding)} parts on its plate")


if __name__ == "__main__":
    main()
