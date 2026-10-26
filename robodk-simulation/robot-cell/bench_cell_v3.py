"""RoboDK cell for Bench V1, version 3 (v3): the co-student's jig (JigAssemDraft1) on a ground base, one
double-sided guide moved base B -> A -> B. (v1/v2: older jigs, in the git history of bench_cell.py; v4:
bench_cell_v4.py, the guide cut in two + the hand-over to the AMR.)

    python robot_cell/bench_cell_v3.py   (RoboDK's own Python is enough; the main RoboDK, it needs the licence)
Station "Bench V1 cell v3", TMflow export bench_tmflow/v3/, cycle time logged in cycle_times.csv.

Needs jig_parts.py (bases, double-sided guide, plank jig, ground base), bench_parts.py (frame,
plank body, interface piece) and bench_layout.json (work frame logged on the real robot).
Start: base A holds frame 1 + 6 interface pieces, base B frame 2 + 6 interface pieces with the
guide on top, the planks stand in the plank jig. Robot program "AssembleBench":
    1  guide: base B -> flipped in the air -> base A
    2  planks 1-6: plank jig -> straight down through the guide into frame 1, pushed home
    3  guide: lifted off over the plank tops -> flipped -> base B
    4  frame 1 with the planks: gripped at a leg foot, flipped (planks down) in the middle, lowered
       through the guide into frame 2
The wrist changes branch (J5 through 0) only in a J5-only joint move, with the fingertips nearly
still: the fingertips never leave the ground base.
Everything happens on the ground base; all targets are relative to the frame "Ground base", so the
TMflow export carries that base (re-teach it on the robot, e.g. with the 4 red vision squares).
Gripper (Schunk EGP): DO 0 = close; the guide is held from inside its grip pocket (fingers go in
closed and open to grip). Not yet: the hand-over of the bench to the AMR (the guide sits between
the frames at the end).
"""
import json
import math
import re
import shutil
from pathlib import Path

from robodk import robolink, robomath
from robodk.robomath import Mat, pi, rotx, rotz, transl

import cycle_times
import robot_cell as rc                                  # ROBOT_FILE, ROBOT, ik(), shape(), close_stations()

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
PARTS, JIG, OUT = HERE / "benchV1_parts", HERE / "jig_parts", HERE / "bench_tmflow" / "v3"
LAYOUT = json.loads((HERE / "bench_layout.json").read_text(encoding="utf-8"))
VERSION, STATION, PROGRAM = "v3", "Bench V1 cell v3", "AssembleBench"
AMR_FILE = "C:/RoboDK/Library/Add-in - Sensor2D safety sensor with AGV/Parts/Omron-LD-250.robot"
POST, POSTS_DIR = "Omron_DAM", Path("C:/RoboDK/Posts")       # Omron post without the Explorer pop-up
TIP = LAYOUT["tip_mm"]                                   # flange -> closed fingertips (estimate)
TABLE_H = 750                                            # floor below the table top (assumed)

# ground base (jig_parts.py): 590 x 440 x 15, x away from the robot, y to the left, top at z = 0
GROUND_SIZE = (590, 440, 15)
GROUND_IN_WORK = transl(0, -67, 15)                      # near edge on the logged plate's, centred on the robot, on the table
RISER_A = RISER_B = 10                                   # both bases on 10 mm risers (horizontal gripper body clears)
# far row, not turned: legs point sideways (base A right, base B left), the guide's grip pocket (side face of
# its short arm) faces the robot, so the robot reaches it straight out from its base and turns the guide
# over with J6; both flips are about x. (A straight move down to the horizontal guide grip only works from
# ~550 mm out: guide grip ~630 mm.) Frame 1's foot ends at base B's outer side, where the wrist has room.
BASE_A, BASE_B = transl(480, 120, RISER_A), transl(480, 320, RISER_B)
PLANK_JIG, PITCH = transl(150, 190, 0), 30                # near row, middle: the reach-in lanes are at the edges
PLANK_ORDER = (3, 6, 2, 5, 1, 4)                          # far column first, front row first: never over a standing plank
FLIP_AT = (430, 220, 450)                                 # frame 1 + planks turned over here, in the middle
AMR_GAP, AMR_PLATE = 150, (300, 320)

TRAVEL_Z = 380                                           # TCP for planks plank jig -> base A: clears the guide, not standing planks
LIFT_Z = 450                                             # guide carried and flipped at this height (sweeps ~157 mm)
WRIST_SWAP = 15                                          # J5 (deg) where the wrist changes branch
SUB_LIFT = 40                                            # frame 1 + planks lifted this much out of the pocket
BACK_OFF = 25                                            # out of the guide's grip pocket (fingers 15 mm in)
APPROACH, FAST, SLOW, JOINT = 40, 100, 20, 50
EVENT = robolink.INS_TYPE_EVENT
ATTACH, DETACH, SET_POSITION = 0, 1, 5

EGP = [((-47, -45, 0), (47, 45, 123)), ((-9, -4, 123), (-6, 4, TIP)), ((6, -4, 123), (9, 4, TIP))]

# STEP (bench) -> base-local; flip about x that puts frame 1 + planks onto frame 2 in base B
T_IN = transl(-2.715, -21.877, 134.5) * rotx(pi / 2)
FLIP = transl(0, 0, 269) * rotx(pi)
GUIDE_ON_B = transl(0, 0, 80) * rotx(pi)                 # the guide flipped onto base B (its slots mirror)
# grips (TCP poses): plank in plank coordinates, guide in its own (= base A) coordinates, foot in base A
PLANK_GRIP = Mat([[0, -1, 0, 0], [0, 0, -1, 110], [1, 0, 0, 2.5], [0, 0, 0, 1]])
PLANK_PUSH = Mat([[0, -1, 0, 0], [0, 0, -1, 125], [1, 0, 0, 2.5], [0, 0, 0, 1]])
GUIDE_GRIP = Mat([[0, 0, 1, -72], [0, -1, 0, -70], [1, 0, 0, 40], [0, 0, 0, 1]])  # tool +x, 15 mm into the pocket,
                                                         # fingers open vertically: wrist camera sideways
C, S = math.cos(math.atan2(1.75, 10)), math.sin(math.atan2(1.75, 10))              # rear leg tilt 9.9 deg
# rear foot, fingers 2.7 mm past the base edge, tilted 60 deg about the closing direction: the gripper leans
# out (up-and-out at base A, down-and-out after the flip at base B, where the wrist would otherwise hit it)
FOOT_GRIP = Mat([[C, S, 0, 60.8], [S, -C, 0, -96.7], [0, 0, -1, 12], [0, 0, 0, 1]]) * rotx(pi / 3)



def build():
    asm = {p["name"]: rc.Mat(p["pose"]) for p in json.loads((PARTS / "assembly.json").read_text())["parts"]}
    RDK = robolink.Robolink()
    RDK.COM.settimeout(300)                                   # RoboDK can be busy for a while after a reopen
    RDK.setCollisionActive(robolink.COLLISION_OFF)            # MoveL_Test (link()) then answers 0 / -1 only
    rc.close_stations(RDK, lambda name: name == STATION)
    RDK.AddStation(STATION)
    RDK.Render(False)
    cell = RDK.AddFrame("Cell")
    work = RDK.AddFrame("Work plate", cell)
    work.setPose(rc.Mat(LAYOUT["work_frame"]))
    gb = RDK.AddFrame("Ground base", work)
    gb.setPose(GROUND_IN_WORK)
    grey, wood, frame_c, red = [0.6, 0.6, 0.62, 1], [0.75, 0.55, 0.3, 1], [0.55, 0.62, 0.75, 1], [0.85, 0.1, 0.1, 1]
    jig_c, guide_c = [0.35, 0.55, 0.85, 1], [0.95, 0.75, 0.2, 1]

    def obj(name, stl, parent, pose, colour):
        o = RDK.AddFile(str(stl), parent)
        o.setName(name)
        o.setColor(colour)
        o.setPose(pose)
        return o

    sx, sy, st = GROUND_SIZE
    fixtures = [rc.shape(RDK, [((-350, -60, -TABLE_H), (sx + 10, sy + 60, -st))], gb, [0.78, 0.74, 0.68, 1], "Table"),
                obj("Ground base plate", JIG / "ground_base.stl", gb, robomath.eye(4), [0.82, 0.8, 0.74, 1])]
    for i, (qx, qy) in enumerate(((3, 3), (sx - 28, 3), (3, sy - 28), (sx - 28, sy - 28)), 1):
        obj(f"Vision square {i}", JIG / "vision_square.stl", gb, transl(qx, qy, 0), red)
    for name, base, stl, riser in (("Base A", BASE_A, "base_a", RISER_A), ("Base B", BASE_B, "base_b", RISER_B)):
        fixtures.append(rc.shape(RDK, [((-90, -90, -riser), (90, 90, 0))], gb, grey, f"{name} riser"))
        fixtures[-1].setPose(base)
        fixtures.append(obj(name, JIG / f"{stl}.stl", gb, base, jig_c))
    fixtures.append(obj("Plank jig", JIG / "plank_jig.stl", gb, PLANK_JIG, jig_c))

    robot = RDK.AddFile(str(rc.ROBOT_FILE))
    robot.setName(rc.ROBOT)
    robot.Parent().setParent(cell)
    robot.Parent().setPose(robomath.eye(4))
    real = json.loads((HERE / "real_points.json").read_text(encoding="utf-8"))
    robot.setJoints(real[0]["joints"])
    tool = robot.AddTool(transl(0, 0, TIP), "EGP")
    rc.shape(RDK, EGP, tool, [0.25, 0.25, 0.28, 1])
    robot.setPoseFrame(gb)
    robot.setPoseTool(tool)

    # AMR past the far edge (for the hand-over later) and its 2 m drive script
    amr = RDK.AddFrame("AMR", gb)
    amr.setPose(transl(sx + AMR_GAP, sy / 2 - AMR_PLATE[1] / 2, 0))
    fixtures.append(rc.shape(RDK, [((0, 0, -10), (AMR_PLATE[0], AMR_PLATE[1], 0))], amr, [0.4, 0.75, 0.45, 1], "AMR plate"))
    fixtures.append(rc.shape(RDK, [((40, 40, 383 - TABLE_H - st), (AMR_PLATE[0] - 40, AMR_PLATE[1] - 40, -10))], amr,
                             [0.85, 0.85, 0.88, 1], "AMR top module"))
    if Path(AMR_FILE).exists():
        ld = RDK.AddFile(AMR_FILE, amr)
        ld.setName("AMR LD-250")
        ld.setJoints([0, 0, 0, 0])
        ld.Parent().setPose(transl(380, AMR_PLATE[1] / 2, -TABLE_H - st))
        ld.Parent().setVisible(False)

    # parts at their start (ground base coordinates)
    f1 = obj("frame1", PARTS / "frame.stl", gb, BASE_A * T_IN * asm["frame1"], frame_c)
    f2 = obj("frame2", PARTS / "frame.stl", gb, BASE_B * FLIP * T_IN * asm["frame2"], frame_c)
    pieces_a, pieces_b, planks, final = [], [], [], {}
    for k in range(1, 7):
        P = T_IN * asm[f"plank{k}"]
        pieces_a.append(obj(f"piece A{k}", PARTS / "interface_piece.stl", gb, BASE_A * P, red))
        pieces_b.append(obj(f"piece B{k}", PARTS / "interface_piece.stl", gb, BASE_B * FLIP * P * rotz(pi), red))
        row, col = divmod(k - 1, 3)
        start = PLANK_JIG * transl(PITCH * (col + 0.5), PITCH * (row + 0.5) + 2.5, 125) * rotx(pi / 2)
        planks.append(obj(f"plank{k}", PARTS / "plank_body.stl", gb, start, wood))
        final[k] = (start, BASE_A * P)
    guide = obj("Guide", JIG / "guide.stl", gb, BASE_B * GUIDE_ON_B, guide_c)
    parts = [f1, f2, guide] + planks + pieces_a + pieces_b

    # targets and program
    j, bad = robomath.Mat([[v] for v in real[0]["joints"]]), []

    def elbow_up(pose):
        """Joints with the elbow as high as possible (low, horizontal grips: elbow-down hits the table);
        of the two wrists the elbow allows, the one closer to the previous target (no wrist flip on the way)."""
        sols = robot.SolveIK_All(gb.PoseAbs() * pose, tool.PoseTool())
        lo, hi = (v.list() for v in robot.JointLimits()[:2])
        best, a = None, j.list()[:6]
        for c in range(sols.size(1)):
            q = [sols[i, c] for i in range(6)]
            if abs(q[0]) > 100 or any(not lo[i] <= q[i] <= hi[i] for i in range(5)):
                continue
            q[5] = min((q[5] + k for k in (-360, 0, 360) if lo[5] <= q[5] + k <= hi[5]), key=lambda v: abs(v - a[5]))
            z = round(robot.JointPoses(q)[3].Pos()[2])             # elbow (joint 3) height
            d = sum(w * (x - y) ** 2 for w, x, y in zip((3, 3, 2, 1, 1, 0.5), q, a))
            if best is None or (z, -d) > (best[0], -best[1]):
                best = (z, d, q)
        return robomath.Mat([[v] for v in best[2]]) if best else None

    def target(name, pose, seed=None, up=False, joints=None, fixed=False):
        """Target with the joints closest to the previous target, or to `seed` (then the chain is kept),
        or (up=True) with the elbow highest, or with the given `joints`. fixed: a joint target (a joint
        move then ends in exactly these joints, not in another solution of the pose)."""
        nonlocal j
        if joints is not None:
            q = joints
        else:
            q = elbow_up(pose) if up else rc.ik(robot, gb.PoseAbs() * pose, seed if seed is not None else j, tool.PoseTool())
        if q is None:
            bad.append(name)
        elif seed is None:
            j = q
        q = q if q is not None else j
        t = RDK.AddTarget(name, gb, robot)
        t.setPose(pose)
        t.setJoints(q)
        if fixed:
            t.setAsJointTarget()
        t.setVisible(False)
        return t

    def at_z(pose, z):
        p = Mat(pose)
        p[2, 3] = z
        return p

    def attach(objs, name):
        for o in objs:
            prog.setParam("Add", {"Type": EVENT, "Behavior": ATTACH, "Name": f"Simulation: attach {o.Name()}",
                                  "ToolPtr": str(tool.item), "AttachStrategy": 4, "AttachDistance": 3000,
                                  "ObjectList": str(o.item)})

    def release(name):
        prog.setParam("Add", {"Type": EVENT, "Behavior": DETACH, "Name": f"Simulation: release {name}",
                              "ToolPtr": str(tool.item), "FramePtr": str(gb.item)})

    def gripper(close, wait=500):
        prog.setDO(0, 1 if close else 0)
        prog.Pause(wait)

    home = target("Home", transl(sx / 2, sy / 2, TRAVEL_Z) * rotx(pi))
    robot.setJoints(home.Joints())
    prog = RDK.AddProgram(PROGRAM, robot)
    prog.setParam("Add", {"Type": EVENT, "Behavior": SET_POSITION, "Name": "Simulation: parts to start",
                          "ObjectList": ",".join(str(p.item) for p in parts),
                          "ParentList": ",".join(str(gb.item) for _ in parts)})
    prog.setPoseFrame(gb)
    prog.setPoseTool(tool)
    prog.setRounding(0)
    prog.setSpeed(FAST, JOINT)
    prog.MoveJ(home)

    def link(prev, t):
        """Straight move if the robot can make it from the joints `prev`, else a joint move."""
        prog.MoveL(t) if robot.MoveL_Test(prev, t.Pose()) == 0 else prog.MoveJ(t)

    def follow(q, pose, n=36):
        """Joints the robot ends with after a straight move from the joints q to pose (the move keeps its
        posture, the closest solution can be another one). None if a step is unreachable."""
        p0 = gb.PoseAbs().inv() * robot.SolveFK(q) * tool.PoseTool()
        R = p0.inv() * pose
        a = math.acos(max(-1.0, min(1.0, (R[0, 0] + R[1, 1] + R[2, 2] - 1) / 2)))
        k = (R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1])
        s = math.sqrt(sum(v * v for v in k))
        for i in range(1, n + 1):
            f = i / n
            P = p0 * axis_rot([v / s for v in k], f * a) if s > 1e-9 else Mat(p0)
            for r, (u, v) in enumerate(zip(p0.Pos(), pose.Pos())):
                P[r, 3] = u + (v - u) * f
            q = rc.ik(robot, gb.PoseAbs() * P, q, tool.PoseTool())
            if q is None:
                return None
        return q

    def fk(q):
        return gb.PoseAbs().inv() * robot.SolveFK(q) * tool.PoseTool()

    def swap_wrist(label, q):
        """Change the wrist branch (J5 sign) with the fingertips nearly still: turn about the tip, tool axis
        towards J4's axis, until |J5| < WRIST_SWAP, then a J5-only joint move through 0 (a straight move
        cannot pass this singularity). Returns the joints after the swap."""
        qa, pa = Mat(q), fk(q)
        x, y, z = pa.Pos()
        for _ in range(180):
            if abs(qa[4, 0]) < WRIST_SWAP:
                break
            zt, a4 = pa.VZ(), (gb.PoseAbs().inv() * robot.JointPoses(qa.list())[4]).VZ()   # J5 = 0: zt = a4
            k = (zt[1] * a4[2] - zt[2] * a4[1], zt[2] * a4[0] - zt[0] * a4[2], zt[0] * a4[1] - zt[1] * a4[0])
            n = math.sqrt(sum(v * v for v in k))
            pa = transl(x, y, z) * axis_rot([v / n for v in k], math.radians(1)) * transl(-x, -y, -z) * pa
            qa = rc.ik(robot, gb.PoseAbs() * pa, qa, tool.PoseTool())
        ready = target(f"{label} wrist ready", pa, joints=follow(q, pa))
        if max(abs(u - v) for u, v in zip(ready.Joints().list(), qa.list())) > 1:
            bad.append(f"{label} wrist ready (posture)")
        prog.MoveL(ready)
        qb = Mat(qa)
        qb[4, 0] = -qb[4, 0]
        prog.MoveJ(target(f"{label} wrist swapped", fk(qb), joints=qb, fixed=True))
        return qb

    def straight(name, q, pose, like):
        """Straight move from the joints q to pose; must end in the posture of the joints `like` (the
        solution of pose closest to them)."""
        t = target(name, pose, joints=follow(q, pose))
        want = rc.ik(robot, gb.PoseAbs() * pose, like, tool.PoseTool())
        if want is None or max(abs(u - v) for u, v in zip(t.Joints().list()[:5], want.list()[:5])) > 1:
            bad.append(f"{name} (posture)")
        prog.MoveL(t)
        return t

    def move_guide(label, pick, place):
        """Guide held from inside its grip pocket (horizontal tool), carried at LIFT_Z, flipped on the way."""
        prev = Mat(j)                                              # joints of the move before
        out = pick * transl(0, 0, -BACK_OFF)                      # backed out of the pocket
        low = target(f"{label} pick out low", out, up=True)      # solved first: the point above takes its posture
        hi = target(f"{label} pick out", at_z(out, LIFT_Z), seed=low.Joints())
        via = Mat(out)                                             # turn the tool over the middle, then straight on
        via[0, 3], via[1, 3], via[2, 3] = GROUND_SIZE[0] / 2, GROUND_SIZE[1] / 2, LIFT_Z
        to_via = target(f"{label} via", via, seed=hi.Joints())
        if prev[4, 0] * to_via.Joints()[4, 0] < 0:                 # other wrist: swapped first, then straight on
            straight(f"{label} via", swap_wrist(label, prev), via, to_via.Joints())
        else:
            link(prev, to_via)
        prog.MoveL(hi)
        prog.MoveL(low)
        prog.setSpeed(SLOW, JOINT)
        gripper(True, 300)                                        # fingers closed to go in
        prog.MoveL(target(f"{label} pick", pick))
        gripper(False)                                            # open: grips the pocket walls
        attach([guide], "guide")
        prog.MoveL(target(f"{label} lift", at_z(pick, pick[2, 3] + 20)))
        prog.setSpeed(FAST, JOINT)
        prog.MoveL(target(f"{label} up", at_z(pick, LIFT_Z)))
        across = Mat(pick)                                         # straight across first, still unflipped
        across[0, 3], across[1, 3], across[2, 3] = place[0, 3], place[1, 3], LIFT_Z
        prog.MoveL(target(f"{label} across", across))
        down = target(f"{label} place", place, up=True)           # solved first (posture for the way down)
        prog.MoveJ(target(f"{label} over place", at_z(place, LIFT_Z), seed=down.Joints()))   # flipped: J6 turns 180
        prog.MoveL(target(f"{label} place approach", at_z(place, place[2, 3] + APPROACH), seed=down.Joints()))
        prog.setSpeed(SLOW, JOINT)
        prog.MoveL(down)
        gripper(True)                                             # closed: lets go
        release("guide")
        prog.MoveL(target(f"{label} place out", place * transl(0, 0, -BACK_OFF)))
        prog.setSpeed(FAST, JOINT)
        prog.MoveL(target(f"{label} place out up", at_z(place * transl(0, 0, -BACK_OFF), LIFT_Z)))

    # 1  guide: base B -> base A
    move_guide("guide B-A", BASE_B * GUIDE_ON_B * GUIDE_GRIP, BASE_A * GUIDE_GRIP)
    # 2  planks into frame 1 through the guide
    for k in PLANK_ORDER:
        plank = planks[k - 1]
        start, end = final[k]
        pick, place, push = start * PLANK_GRIP, end * PLANK_GRIP, end * PLANK_PUSH
        prog.MoveJ(target(f"plank{k} pick travel", at_z(pick, TRAVEL_Z)))
        prog.MoveL(target(f"plank{k} pick approach", at_z(pick, pick[2, 3] + APPROACH)))
        prog.setSpeed(SLOW, JOINT)
        prog.MoveL(target(f"plank{k} pick", pick))
        gripper(True)
        attach([plank], f"plank{k}")
        prog.MoveL(target(f"plank{k} pick out", at_z(pick, pick[2, 3] + 60)))
        prog.setSpeed(FAST, JOINT)
        prog.MoveL(target(f"plank{k} pick up", at_z(pick, TRAVEL_Z)))
        prog.MoveJ(target(f"plank{k} place travel", at_z(place, TRAVEL_Z)))
        prog.MoveL(target(f"plank{k} above guide", at_z(place, place[2, 3] + 75)))   # bottom 15 mm over the guide
        prog.setSpeed(SLOW, JOINT)
        prog.MoveL(target(f"plank{k} place", place))
        gripper(False)
        release(f"plank{k}")
        prog.MoveL(target(f"plank{k} push approach", at_z(push, push[2, 3] + 20)))
        gripper(True, 300)                                        # closed fingers push the plank home
        prog.MoveL(target(f"plank{k} push", push))
        prog.MoveL(target(f"plank{k} push out", at_z(push, push[2, 3] + 20)))
        gripper(False, 300)
        prog.setSpeed(FAST, JOINT)
        prog.MoveL(target(f"plank{k} place up", at_z(place, TRAVEL_Z)))
    # 3  guide: base A -> base B (lifted straight off over the plank tops first)
    move_guide("guide A-B", BASE_A * GUIDE_GRIP, BASE_B * GUIDE_ON_B * GUIDE_GRIP)
    # 4  frame 1 + planks: foot grip from above, flipped, lowered through the guide into frame 2
    pick, place = BASE_A * FOOT_GRIP, BASE_B * FLIP * FOOT_GRIP
    prev = Mat(j)
    grab = target("sub pick", pick, up=True)
    near = target("sub pick approach", at_z(pick, pick[2, 3] + SUB_LIFT), seed=grab.Joints())
    via = Mat(pick)                                                 # tilted grip taken over the middle first
    via[0, 3], via[1, 3], via[2, 3] = GROUND_SIZE[0] / 2, GROUND_SIZE[1] / 2, FLIP_AT[2]
    to_via = target("sub via", via, joints=follow(near.Joints(), via))   # the way down keeps the pick posture
    if prev[4, 0] * to_via.Joints()[4, 0] < 0:                     # other wrist: swapped over the middle first
        centre = fk(prev)
        centre[0, 3], centre[1, 3], centre[2, 3] = GROUND_SIZE[0] / 2, GROUND_SIZE[1] / 2, LIFT_Z
        prog.MoveL(target("sub centre", centre, joints=follow(prev, centre)))
        prev = swap_wrist("sub start", Mat(j))
    link(prev, to_via)
    prog.MoveL(near)
    prog.setSpeed(SLOW, JOINT)
    prog.MoveL(grab)
    gripper(True)
    attach([f1] + planks + pieces_a, "frame 1 with the planks")
    prog.MoveL(near)                                                # lifted out of the pocket
    prog.setSpeed(FAST, JOINT)
    # Turned over in the middle: the pick posture has the wrist one way (J5 < 0), base B needs it the other
    # way, so the wrist is swapped at the singularity, then one straight move turns and carries it over B.
    mid = Mat(pick)
    mid[0, 3], mid[1, 3], mid[2, 3] = FLIP_AT
    prog.MoveJ(target("sub to middle", mid, fixed=True))           # elbow back up on the way to the middle
    qb = swap_wrist("sub", Mat(j))
    put = target("sub place", place, up=True)
    above = target("sub above guide", at_z(place, place[2, 3] + 75), seed=put.Joints())
    straight("sub flipped", qb, at_z(place, place[2, 3] + 120), above.Joints())   # planks clear the guide
    prog.MoveL(above)
    prog.setSpeed(SLOW, JOINT)
    prog.MoveL(put)
    gripper(False)
    release("frame 1 with the planks")
    out = place * transl(0, 0, -25)                                 # fingers off the foot, along the gripper
    q = put.Joints()                                                # straight moves: joints followed along
    for name, pose in (("sub place out", out), ("sub clear", transl(-150, 0, 0) * out)):  # back towards the robot
        t = target(name, pose, joints=follow(q, pose))                  # along base B's outer side
        prog.MoveL(t)
        q = t.Joints()
    back = Mat(out)                                                 # back over the middle, then home
    back[0, 3], back[1, 3], back[2, 3] = GROUND_SIZE[0] / 2, GROUND_SIZE[1] / 2, FLIP_AT[2]
    b0 = target("sub back to middle", back, joints=follow(q, back))
    prog.MoveL(b0)
    prog.setSpeed(FAST, JOINT)
    if b0.Joints()[4, 0] * home.Joints()[4, 0] < 0:
        straight("back home", swap_wrist("back", b0.Joints()), home.Pose(), home.Joints())
    else:
        link(b0.Joints(), home)

    RDK.AddFile(str(HERE / "amr_drive.py"), RDK.ActiveStation()).setName("Deliver (AMR)")
    style(RDK, robot, prog, (cell, work, gb, amr, robot.Parent()))
    cell.setParam("Tree", "Collapse")
    RDK.Render(True)
    OUT.mkdir(parents=True, exist_ok=True)
    RDK.Save(str(HERE / f"{STATION}.rdk"))
    return RDK, robot, tool, gb, prog, parts, fixtures, bad


def axis_rot(k, a):
    """Rotation by a about the unit axis k (Rodrigues)."""
    x, y, z = k
    c, s, v = math.cos(a), math.sin(a), 1 - math.cos(a)
    return Mat([[x * x * v + c, x * y * v - z * s, x * z * v + y * s, 0],
                [y * x * v + z * s, y * y * v + c, y * z * v - x * s, 0],
                [z * x * v - y * s, z * y * v + x * s, z * z * v + c, 0], [0, 0, 0, 1]])


def style(RDK, robot, prog, frames):
    """No axis arrows, no path, no trace (call again after the station is reopened)."""
    for f in frames:
        f.setVisible(False)
    robot.setVisible(True, 0x2AAAAAAA)
    prog.setVisible(False)
    RDK.Command("Trace", "Off")


def check(RDK, robot, tool, prog, parts, fixtures):
    """Robot and gripper against the fixtures (parts are left out: they touch on purpose)."""
    RDK.COM.settimeout(1200)
    RDK.setCollisionActive(robolink.COLLISION_ON)
    every = parts + fixtures
    for i, a in enumerate(every):
        for b in every[i + 1:]:
            RDK.setCollisionActivePair(robolink.COLLISION_OFF, a, b)
    for p in parts:
        RDK.setCollisionActivePair(robolink.COLLISION_OFF, tool, p)
        for link in range(7):
            RDK.setCollisionActivePair(robolink.COLLISION_OFF, robot, p, link, 0)
    for link in range(7):
        RDK.setCollisionActivePair(robolink.COLLISION_OFF, robot, tool, link, 0)
    ld = RDK.Item("AMR LD-250", robolink.ITEM_TYPE_ROBOT)
    if ld.Valid():
        for other in every:
            for link in range(5):
                RDK.setCollisionActivePair(robolink.COLLISION_OFF, ld, other, link, 0)
    res = prog.Update(robolink.COLLISION_ON)
    RDK.setCollisionActive(robolink.COLLISION_OFF)
    return res


def stays_inside(robot, gb, prog):
    """Largest distance (x/y) the fingertips get outside the ground base."""
    msg, path, status = prog.InstructionListJoints(5, 2)
    inv, worst = gb.PoseAbs().inv(), 0.0
    cell = robot.Parent().PoseAbs()
    for col in range(path.size(1)):
        x, y, _ = (inv * cell * robot.SolveFK([path[i, col] for i in range(6)]) * transl(0, 0, TIP)).Pos()
        worst = max(worst, -x, x - GROUND_SIZE[0], -y, y - GROUND_SIZE[1])
    return worst


def main():
    RDK, robot, tool, gb, prog, parts, fixtures, bad = build()
    n, t, d, ok, msg = prog.Update()
    print(f"{PROGRAM}: {n:.0f} instructions, {t:.0f} s, {d / 1000:.1f} m, {'OK' if ok == 1 else 'NOT OK: ' + msg}")
    print("unreachable targets:", bad or "none")
    if ok != 1:
        return
    msg = check(RDK, robot, tool, prog, parts, fixtures)[-1]
    collisions = "none" if not msg or "No collisions" in msg else re.sub(r"<[^>]+>", " ", msg).strip()
    print("collision check:", collisions)
    out = stays_inside(robot, gb, prog)
    print(f"fingertips outside the ground base: {out:.1f} mm")
    post = HERE / f"{POST}.py"
    if POSTS_DIR.exists() and (not (POSTS_DIR / post.name).exists()
                               or (POSTS_DIR / post.name).read_bytes() != post.read_bytes()):
        shutil.copy(post, POSTS_DIR / post.name)
    robot.setParam("PostProcessor", POST)
    print("TMflow export:", prog.MakeProgram(str(OUT))[0])
    RDK.CloseStation()                       # reopen the saved file: only then the window title shows its name
    st = RDK.AddFile(str(HERE / f"{STATION}.rdk"))
    RDK.setActiveStation(st)
    r = RDK.Item(rc.ROBOT, robolink.ITEM_TYPE_ROBOT)
    prog = RDK.Item(PROGRAM, robolink.ITEM_TYPE_PROGRAM)
    row = cycle_times.log(VERSION, prog, "build", collisions=collisions, fingertips=f"{out:.1f}")
    print(f"cycle time {row['cycle_s']:.0f} s per bench at the programmed speeds, logged in {cycle_times.LOG.name}")
    style(RDK, r, prog,
          [RDK.Item(n, robolink.ITEM_TYPE_FRAME) for n in ("Cell", "Work plate", "Ground base", "AMR")] + [r.Parent()])


if __name__ == "__main__":
    main()
