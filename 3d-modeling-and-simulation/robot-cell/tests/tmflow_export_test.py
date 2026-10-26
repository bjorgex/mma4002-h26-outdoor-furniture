"""RoboDK -> TMflow export test: the TM5-900 picks a bench plank (suction cup) and places it
300 mm away. Post-processed with every Omron/Techman post RoboDK ships, so the outputs can be
compared and loaded into TMflow.

    python robot_cell/tests/tmflow_export_test.py      (RoboDK's own Python is enough)

Adds a new station tab to the open RoboDK (needs the licence: the trial covers one instance only).
Double-click PickPlaceTest to run it: simulation events put the plank back, pick and place it.
Events don't move the real robot; the exports only carry their names as comments (TMflow: Display nodes).
Output: robot_cell/tests/tmflow_test/<post>/...
"""
import os
import shutil
import sys
from pathlib import Path

from robodk import robolink, robomath

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import robot_cell as rc                                 # table, gripper and TCPs of the cell

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = HERE / "tmflow_test"
PLANK = HERE.parent / "benchV1_parts" / "plank.stl"            # from bench_parts.py: 250 x 25 x 5 mm, z 0..5
STATION = "TMflow export test"
POSTS = ["Omron", "Techman_TMscript", "Omron_Remote"]   # .flow zip (USB import), .scpt, listen-node script
DOWN = robomath.rotx(robomath.pi)                       # tool z pointing down at the table
TABLE_Z = -1                                            # table top, as in robot_cell.py
PICK, PLACE = (400, -150, TABLE_Z + 5), (400, 150, TABLE_Z + 5)   # plank top centre, cell frame (robot base = origin)
LIFT = 100                                              # approach/retract height above pick/place
EVENT = robolink.INS_TYPE_EVENT
ATTACH, DETACH, SET_POSITION = 0, 1, 5                  # simulation event behaviours (RoboDK GUI order)


def build_program(RDK):
    cell = RDK.AddFrame("Cell")
    rc.shape(RDK, [((-250, -520, -20), (700, 390, TABLE_Z))], cell, [0.85, 0.85, 0.82, 1], "Table")
    robot = RDK.AddFile(str(rc.ROBOT_FILE))
    robot.setName(rc.ROBOT)
    robot.Parent().setParent(cell)
    robot.Parent().setPose(robomath.eye(4))                         # robot base at the cell origin
    robot.setJoints(rc.READY)
    tool = robot.AddTool(rc.Mat(rc.TCP["V"]), "Vacuum")            # suction cup TCP of robot_cell.py
    rc.shape(RDK, rc.GRIPPER + rc.CUP, tool, [0.3, 0.45, 0.8, 1])  # fingers + extended cup
    plank = RDK.AddFile(str(PLANK), cell)
    plank.setName("Plank")
    plank.setColor([0.75, 0.55, 0.3, 1])
    plank.setPose(robomath.transl(PICK[0], PICK[1], TABLE_Z) * robomath.rotz(robomath.pi / 2))   # long axis along x
    robot.setPoseFrame(cell)
    robot.setPoseTool(tool)

    def target(name, xyz):
        t = RDK.AddTarget(name, cell, robot)
        pose = robomath.transl(*xyz) * DOWN
        t.setPose(pose)
        t.setJoints(robot.SolveIK(pose * tool.PoseTool().inv(), rc.READY))   # posts that write joints use these
        return t

    home = RDK.AddTarget("Home", cell, robot)
    home.setAsJointTarget()
    home.setJoints(rc.READY)
    pick_up, pick = target("PickApproach", (PICK[0], PICK[1], PICK[2] + LIFT)), target("Pick", PICK)
    place_up, place = target("PlaceApproach", (PLACE[0], PLACE[1], PLACE[2] + LIFT)), target("Place", PLACE)

    prog = RDK.AddProgram("PickPlaceTest", robot)
    prog.setParam("Add", {"Type": EVENT, "Behavior": SET_POSITION, "Name": "Simulation: plank to start",
                          "ObjectList": str(plank.item), "ParentList": str(cell.item)})   # start pose recorded now
    prog.setPoseFrame(cell)
    prog.setPoseTool(tool)
    prog.setSpeed(100, 60)                               # mm/s, deg/s
    prog.setRounding(0)
    prog.MoveJ(home)
    prog.MoveJ(pick_up)
    prog.MoveL(pick)
    prog.setDO(0, 1)                                     # vacuum on (DO 0)
    prog.setParam("Add", {"Type": EVENT, "Behavior": ATTACH, "Name": "Simulation: attach plank", "ToolPtr": str(tool.item),
                          "AttachStrategy": 4, "ObjectList": str(plank.item)})
    prog.Pause(500)                                      # ms
    prog.MoveL(pick_up)
    prog.MoveJ(place_up)
    prog.MoveL(place)
    prog.setDO(0, 0)                                     # vacuum off
    prog.setParam("Add", {"Type": EVENT, "Behavior": DETACH, "Name": "Simulation: release plank", "ToolPtr": str(tool.item),
                          "FramePtr": str(cell.item)})
    prog.Pause(500)
    prog.MoveL(place_up)
    prog.MoveJ(home)
    return robot, prog, plank


def main():
    if os.environ.get("ROBODK_API_PORT", "20500") != "20500":
        sys.exit("TMflow export needs the licence, i.e. the main RoboDK: unset ROBODK_API_PORT")
    OUT.mkdir(exist_ok=True)
    for old in OUT.iterdir():                # empty it; the folder itself may be open in Explorer
        shutil.rmtree(old) if old.is_dir() else old.unlink()
    RDK = robolink.Robolink()               # the open RoboDK: a 2nd instance runs without the licence
    rc.close_stations(RDK, lambda name: name == STATION)          # replace an earlier test tab
    RDK.AddStation(STATION)                 # new station tab, other open stations are left alone
    print("RoboDK", RDK.Version(), "license:", RDK.License()[0])
    robot, prog, plank = build_program(RDK)
    RDK.Save(str(OUT / f"{STATION}.rdk"))
    n, t, d, ok, msg = prog.Update()
    print(f"program check: {n:.0f} instructions, {t:.1f} s, {d:.0f} mm, {'OK' if ok == 1 else 'NOT OK: ' + msg}")
    for i in range(prog.InstructionCount()):
        print(f"  {i:2d} {prog.Instruction(i)[0]}")
    for post in POSTS:
        folder = OUT / post
        folder.mkdir()
        robot.setParam("PostProcessor", post)
        res = prog.MakeProgram(str(folder))
        print(f"{post:18s} MakeProgram -> {res}")
        for f in sorted(folder.rglob("*")):
            print("    ", f.relative_to(OUT), f.stat().st_size if f.is_file() else "")


if __name__ == "__main__":
    main()
