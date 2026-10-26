"""RoboDK cell: Omron TM5-900 assembles the 1:7.5 demonstrator (sequence from old six-product cell/cell_sequence.py).

    python robot_cell/robot_cell.py build B2   new station: table, robot, gripper, nests, parts
    python robot_cell/robot_cell.py play B2    run the assembly, check reach + collisions per step

Inside RoboDK the station has this script as "Assemble" (double-click = play).
Needs only the robodk package (no numpy), so RoboDK's own Python can run it.

One session drives the main RoboDK (port 20500, licensed: saves stations, exports to TMflow).
Other sessions build and test in their own RoboDK on a free port, which saves nothing:
    $env:ROBODK_API_PORT=20601; python robot_cell/robot_cell.py build B2
"""
import json
import os
import sys
import time
from pathlib import Path

from robodk import robolink, robomath

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
ROBOT_FILE = HERE / "Omron-TM5-900.robot"
OLD = HERE / "old six-product cell"         # sequences, stations and reports of the six products
STATION = "DAM cell"
ROBOT = "Omron TM5-900"
READY = [29.3, -39.9, 110.0, 19.9, 90.0, 119.3]   # flange at (250, 0, 500) pointing down: over free table
GRIPPER_SPEED = 100                      # mm/s linear in the simulation
TEST_PORT = os.environ.get("ROBODK_API_PORT", "20500") != "20500"   # own test RoboDK, see connect()


def connect():
    """The main RoboDK, or with ROBODK_API_PORT set this session's own RoboDK on that port
    (started if needed). A 2nd RoboDK runs without the licence (Free): build and test only."""
    return robolink.Robolink(args=["-NEWINSTANCE"]) if TEST_PORT else robolink.Robolink()


def close_stations(RDK, match):
    """Close every open station whose name matches (ItemList only sees the active station)."""
    for st in RDK.getOpenStations():
        if match(st.Name()):
            RDK.CloseStation() if st == RDK.ActiveStation() else st.Delete()


def Mat(m):
    return robomath.Mat([list(map(float, r)) for r in m])


def box_tris(lo, hi):
    """12 triangles of an axis-aligned box, as a flat list of points."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return [list(v[i]) for f in faces for i in f]


def shape(RDK, boxes, parent, colour, name=None):
    pts = [p for b in boxes for p in box_tris(*b)]
    if parent.Type() == robolink.ITEM_TYPE_TOOL:              # geometry of the tool itself
        item = RDK.AddShape(robomath.Mat(pts).tr(), parent)
    else:                                                     # a new object in that frame
        item = RDK.AddShape(robomath.Mat(pts).tr())
        item.setParent(parent)
    item.setColor(colour)
    if name:
        item.setName(name)
    return item


# Gripper (flange coordinates, z out of the flange): body, two fingers (TCP "Fingers"),
# an arm along the finger axis with a suction cup on a stroke cylinder: extended 22 mm past the
# fingers for vacuum picks (TCP "Vacuum"), retracted 50 mm while the fingers work.
GRIPPER = [((-25, -15, 0), (25, 15, 40)),
           ((-10, -4, 40), (-7, 4, 114)), ((7, -4, 40), (10, 4, 114)),    # long fingers, 14 mm open
           ((15, -6, 25), (50, 6, 40))]                                   # vacuum arm, along the finger axis
CUP = [((42, -3, 40), (48, 3, 130)), ((40, -5, 130), (50, 5, 135))]      # stem + cup (extended)
CUP_STROKE = 50
TCP = {"F": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 113], [0, 0, 0, 1]],
       "V": [[1, 0, 0, 45], [0, 1, 0, 0], [0, 0, 1, 135], [0, 0, 0, 1]]}


def ik(robot, pose, j0, tool):
    """Joint solution for a TCP pose: the one closest to j0, shoulder facing the cell
    (|J1| < 100 deg), J6 shifted by 360 deg when that is closer. None if unreachable."""
    sols = robot.SolveIK_All(pose, tool)
    lo, hi = (v.list() for v in robot.JointLimits()[:2])
    a, best = j0.list()[:6], None
    for c in range(sols.size(1)):
        q = [sols[i, c] for i in range(6)]
        if abs(q[0]) > 100:
            continue
        for k in (-360, 0, 360):
            q6 = q[:5] + [q[5] + k]
            if not lo[5] <= q6[5] <= hi[5]:
                continue
            d = sum(w * (x - y) ** 2 for w, x, y in zip((3, 3, 2, 1, 1, 0.5), q6, a))
            if best is None or d < best[0]:
                best = (d, q6)
    return robomath.Mat([[v] for v in best[1]]) if best else None


def set_cup(RDK, robot, cup, extended):
    """Put the suction cup on the flange, extended or retracted by CUP_STROKE along the tool axis."""
    tool = RDK.Item("Fingers", robolink.ITEM_TYPE_TOOL)
    cell = RDK.Item("Cell", robolink.ITEM_TYPE_FRAME)
    flange = robot.Parent().PoseAbs() * robot.SolveFK(robot.Joints())
    cup.setParentStatic(cell)                       # place it in cell coordinates, then re-attach
    cup.setPoseAbs(flange * robomath.transl(0, 0, 0 if extended else -CUP_STROKE))
    cup.setParentStatic(tool)


def load(code):
    return json.loads((OLD / f"sequence_{code}.json").read_text(encoding="utf-8"))


def build(code):
    seq = load(code)
    RDK = connect()
    close_stations(RDK, lambda name: name.startswith(STATION))
    station = RDK.AddStation(f"{STATION} {code}")
    RDK.Render(False)
    cell = RDK.AddFrame("Cell")
    cell.setPose(robomath.eye(4))
    shape(RDK, [((-250, -520, -20), (700, 390, -1))], cell, [0.85, 0.85, 0.82, 1], "Table")
    robot = RDK.AddFile(str(ROBOT_FILE))
    robot.setName(ROBOT)
    robot.Parent().setParent(cell)
    robot.Parent().setPose(robomath.eye(4))                       # robot base at the cell origin
    robot.setJoints(READY)
    toolF = robot.AddTool(Mat(TCP["F"]), "Fingers")
    shape(RDK, GRIPPER, toolF, [0.3, 0.45, 0.8, 1])
    robot.AddTool(Mat(TCP["V"]), "Vacuum")
    cup = shape(RDK, CUP, cell, [0.9, 0.5, 0.1, 1], "Vacuum cup")   # its own object: it moves
    set_cup(RDK, robot, cup, True)
    amr_frame = RDK.AddFrame("AMR", cell)                          # the mobile robot, docked
    amr_frame.setPose(Mat(seq["amr"]["pose"]))
    if Path(seq["amr"]["robot"]).exists():
        RDK.AddFile(seq["amr"]["robot"], amr_frame).setName("AMR LD-250")
    else:
        print("AMR model not found (RoboDK library):", seq["amr"]["robot"])
    for f in seq["fixtures"]:                                      # jigs (STL) and risers (boxes)
        parent = amr_frame if f.get("parent") == "AMR" else cell
        if "stl" in f:
            item = RDK.AddFile(f["stl"], cell)
            item.setPoseAbs(Mat(f["pose"]))
        else:
            item = shape(RDK, [f["box"]], cell, f["colour"])
        item.setName(f["name"])
        item.setColor(f["colour"])
        if parent != cell:
            item.setParentStatic(parent)
    parts = RDK.AddFrame("Parts", cell)
    parts.setPose(robomath.eye(4))
    for name, p in seq["parts"].items():
        obj = RDK.AddFile(p["stl"], parts)
        obj.setName(name)
        obj.setColor(p["colour"])
        obj.setPose(Mat(p["start"]))
    RDK.setParam("DAM_PRODUCT", code)               # station parameters, saved in the .rdk
    RDK.setParam("DAM_DIR", str(HERE))              # RoboDK runs a copy of this script from Temp
    RDK.AddFile(str(Path(__file__).resolve()), station).setName("Assemble")
    RDK.Render(True)
    if TEST_PORT:                                   # Free licence: a station with a robot can't be saved
        print("built in the test RoboDK on port", os.environ["ROBODK_API_PORT"], "- not saved")
        return
    out = OLD / f"DAM cell {code}.rdk"
    RDK.Save(str(out))
    print("saved", out)


def play(code, check=True, upto=None):
    seq = load(code)
    RDK = connect()
    robot = RDK.Item(ROBOT, robolink.ITEM_TYPE_ROBOT)
    amr_frame = RDK.Item("AMR", robolink.ITEM_TYPE_FRAME)
    amr_frame.setPose(Mat(seq["amr"]["pose"]))                     # docked
    tools = {"F": RDK.Item("Fingers", robolink.ITEM_TYPE_TOOL), "V": RDK.Item("Vacuum", robolink.ITEM_TYPE_TOOL)}
    parts = RDK.Item("Parts", robolink.ITEM_TYPE_FRAME)
    objs = {n: RDK.Item(n, robolink.ITEM_TYPE_OBJECT) for n in seq["parts"]}
    fixed = [RDK.Item(f["name"], robolink.ITEM_TYPE_OBJECT) for f in seq["fixtures"]] + \
        [RDK.Item("Table", robolink.ITEM_TYPE_OBJECT)]
    cup = RDK.Item("Vacuum cup", robolink.ITEM_TYPE_OBJECT)
    for n, p in seq["parts"].items():                              # reset
        objs[n].setParentStatic(parts)
        objs[n].setPose(Mat(p["start"]))
    robot.setPoseFrame(RDK.Item("Cell", robolink.ITEM_TYPE_FRAME))   # all poses in cell coordinates
    robot.setJoints(READY)
    RDK.setSimulationSpeed(4)
    robot.setSpeed(GRIPPER_SPEED, 60)                                # mm/s, deg/s
    t0 = RDK.SimulationTime()

    def pairs(state, names):
        for n in names:
            RDK.setCollisionActivePair(state, tools["F"], objs[n])
            RDK.setCollisionActivePair(state, cup, objs[n])
            for link in range(7):
                RDK.setCollisionActivePair(state, robot, objs[n], link, 0)

    def who(j0, j1, n=12):
        """Names of what collides somewhere between joints j0 and j1 (sampled)."""
        a, b, hit = j0.list(), j1.list(), set()
        for i in range(n + 1):
            robot.setJoints([x + (y - x) * i / n for x, y in zip(a, b)])
            if RDK.Collisions():
                hit |= {it.Name() for it in RDK.CollisionItems()}
        return "+".join(sorted(hit)) or "?"

    if check:                    # only the robot and gripper against the cell, not part vs part
        RDK.setCollisionActive(robolink.COLLISION_ON)
        every = list(objs.values()) + fixed
        for i, a in enumerate(every):
            for b in every[i + 1:]:
                RDK.setCollisionActivePair(robolink.COLLISION_OFF, a, b)
        RDK.setCollisionActivePair(robolink.COLLISION_OFF, robot, fixed[-1], 0, 0)   # base on table
        for link in range(7):                                    # gripper sits on the flange
            RDK.setCollisionActivePair(robolink.COLLISION_OFF, robot, tools["F"], link, 0)
            RDK.setCollisionActivePair(robolink.COLLISION_OFF, robot, cup, link, 0)
        RDK.setCollisionActivePair(robolink.COLLISION_OFF, tools["F"], cup)
    report, err = [], None

    def position_error():
        return max(max(abs(a - b) for a, b in zip(objs[n].PoseAbs().Pos(), Mat(p["final"]).Pos()))
                   for n, p in seq["parts"].items())

    for k, st in enumerate(seq["steps"], 1):
        if upto and k > upto:
            return report
        robot.setPoseTool(tools[st["tool"]])
        set_cup(RDK, robot, cup, st["tool"] == "V")             # cup out for vacuum, in for fingers
        if check:
            pairs(robolink.COLLISION_OFF, st["attach"])
        bad = []
        for kind, m in [["R", None]] + st["moves"]:          # R: via the ready pose between stations
            if kind == "amr":                                # the product rides away on the AMR
                err = position_error()
                for n in objs:
                    objs[n].setParentStatic(amr_frame)
                home = Mat(seq["amr"]["pose"])
                dx, dy, dz = (m * v for v in seq["amr"]["drive"])
                for i in range(1, 61):
                    amr_frame.setPose(robomath.transl(dx * i / 60, dy * i / 60, dz * i / 60) * home)
                    if not check:
                        RDK.Render(True)
                        time.sleep(0.03)
                continue
            if kind == "attach":
                for n in st["attach"]:
                    objs[n].setParentStatic(tools[st["tool"]])
                continue
            if kind == "detach":
                for n in st["detach"]:
                    objs[n].setParentStatic(parts)
                continue
            j0 = robot.Joints()
            if kind == "R":
                kind, j1 = "J", robomath.Mat([[v] for v in READY])
                pose = robot.SolveFK(j1) * tools[st["tool"]].PoseTool()
            else:
                pose = Mat(m)
                j1 = ik(robot, pose, j0, tools[st["tool"]].PoseTool())
            if j1 is None:
                bad.append("unreachable")
                continue
            if check:
                RDK.setCollisionActive(robolink.COLLISION_ON)
                c = robot.MoveJ_Test(j0, j1) if kind == "J" else robot.MoveL_Test(j0, pose)
                if c > 0:
                    bad.append(f"{kind} hits {who(j0, j1)}")
                elif c < 0:
                    bad.append(f"{kind}: no linear path")
                RDK.setCollisionActive(robolink.COLLISION_OFF)
                robot.setJoints(j0)
            try:
                robot.MoveJ(j1) if kind == "J" else robot.MoveL(pose)
            except Exception as e:                                   # keep going, report it
                bad.append(f"{kind}: {e}")
                robot.setJoints(j1)
        if check:
            pairs(robolink.COLLISION_ON, st["attach"])
        line = f"{k:2d} {st['label']:55s} {'OK' if not bad else '; '.join(sorted(set(bad)))}"
        report.append(line)
        print(line, flush=True)
    robot.MoveJ(READY)
    RDK.setCollisionActive(robolink.COLLISION_OFF)
    err = position_error() if err is None else err
    if not check:                                   # the collision tests use simulated time too
        report.append(f"cycle time (simulated, {GRIPPER_SPEED} mm/s, 60 deg/s): {RDK.SimulationTime() - t0:.0f} s")
    report.append(f"largest part position error vs the designed assembly: {err:.3f} mm")
    print("\n".join(report[-2:]))
    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:                                    # run from inside the RoboDK station
        RDK = robolink.Robolink()
        HERE = Path(RDK.getParam("DAM_DIR") or HERE)
        play(RDK.getParam("DAM_PRODUCT") or "B2", check=False)
    elif args[0] == "build":
        build(args[1] if len(args) > 1 else "B2")
    else:                                           # check pass, then a clean pass for the cycle time
        code = args[1] if len(args) > 1 else "B2"
        rep = play(code)[:-1] + play(code, check=False)[-2:]
        (OLD / f"report_{code}.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")
