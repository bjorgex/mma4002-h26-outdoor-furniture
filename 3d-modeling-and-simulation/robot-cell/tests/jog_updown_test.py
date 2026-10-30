"""Minimal real-robot motion test: straight down then back up, no gripper/IO at all.

Confirms RoboDK's own driver can move the robot without hitting the Modbus I/O hang that
"AssembleBench" ran into on its first gripper DO command (see bench_cell_v3.py). Uses whatever
robot is in RoboDK's currently open/active station - connect to the real robot and set
"Run on Robot" first, same as for AssembleBench.

    python robot_cell/tests/jog_updown_test.py [dz_mm]   (default 50 mm)
"""
import sys

from robodk import robolink, robomath

DOWN_MM = float(sys.argv[1]) if len(sys.argv) > 1 else 50
SPEED, ACC = 20, 60    # mm/s, deg/s: slow for a first real move

RDK = robolink.Robolink()
robot = RDK.Item("", robolink.ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit("no robot found in the active RoboDK station")
print("robot:", robot.Name())
robot.setSpeed(SPEED, ACC)

start = robot.Pose()
down = start * robomath.transl(0, 0, -DOWN_MM)       # along the tool's own z axis
print(f"current joints: {[round(v, 1) for v in robot.Joints().list()]}")
input(f"Manual mode, low project speed, hand on the E-stop. Enter to move {DOWN_MM:.0f} mm down ")
robot.MoveL(down)
input("Enter to move back up ")
robot.MoveL(start)
print("done")
