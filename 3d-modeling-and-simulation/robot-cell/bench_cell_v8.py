"""Bench V1 cell, version 8 (v8): v7's program (bench_cell_v7.py) on the Jig V5 hardware (jig_v5.py), built
WITHOUT RoboDK for the group's own simulator (tests/tmflow_mock.py --sim, tests/robot_sim/tm5_kin.py).

    python robot_cell/bench_cell_v8.py          program -> tests/v8_moves.json (+ a reach/line report)
    python robot_cell/tests/robot_sim/cell_layout.py --cell v8      the 3D cell -> cell_v8.glb, cell_layout_v8.json
    then in the mock page: scenario "v8-full" (speed it up with the page's Robot speed)

Hardware (jig_v5_layout.json, plate coordinates: x away from the robot, y to the left, plate top z = 0):
    plate        300 x 300 x 20 T-slot plate (tslot_plate_v5.stl)
    plank rack   PlankRack_V5, turned -90 deg, nearest the robot (plate x 30..90)
    bases A + B  JigV3 base (base_v5.stl), both turned +90 deg (frame legs towards the rack / robot), A at (210, 60),
                 B at (210, 240); frame 1 lies in A's H pocket, frame 2 in B's
    guide        JigV3's two halves: "Guide small" (guide_1_v5, 206 cm3: the inner U) and "Guide big" (guide_2_v5,
                 435 cm3: the outer ring with the long arms), on base A at the start
Program "AssembleBench" (v7's stages, adapted; base roles START_BASE = B, FINISH_BASE = A):
    1  planks (5) rack -> through the guide into frame 1 on the start base
    2  small half, 3 big half: start -> finish base, NOT flipped (JigV3 is mirror symmetric about base-local x, so the
       guide works on the finish base as it is; frame 1 + planks are turned over about base-local y). Both lifted
       straight up off the planks; the big half turned 45 deg about z once clear of the plank tops
    4  frame 1 + planks: outer foot grip, lifted, turned over about an axis along plate x (the bench rolls over
       away from the arm, foot over the top), lowered through the guide into frame 2
    5  small half: lifted off the base's bosses, slid out from between the frames (base-local +y), up, onto the
       start base; 6  big half: lifted, turned 45 deg, slid out, up, straight onto the start base (never the AMR)
    7  finished bench: gripped at frame 1's backrest from above (STAND_GRIP), lifted out of the finish base, turned up
       onto its feet on the way and set down STANDING on the AMR plate (BENCH_ON_AMR); home
    (2026-11-06, Bjørge: the guide must come out BEFORE the bench is lifted - frame 2 cannot pass the guide)
Checks: tests/robot_sim/kin_check.py, collision.py (fixtures + --parts, per-move Hand-E finger gap "egp_gap"),
manipulability.py targets; all with the "techman" link lengths (tm5_kin.py's default, the mock's IK).
ASSUMPTION marks every guessed value.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE / "tests" / "robot_sim"))
import tm5_kin as kin                                      # noqa: E402
import teach_overrides                                     # noqa: E402  grip points taught on the robot (teach_v8.json)

PARTS, JIG, TESTS = HERE / "benchV1_parts", HERE / "jig_parts", HERE / "tests"
LAYOUT = json.loads((HERE / "bench_layout.json").read_text(encoding="utf-8"))
JL = json.loads((HERE / "jig_v5_layout.json").read_text(encoding="utf-8"))
VERSION, STATION, PROGRAM = "v8", "Bench V1 cell v8", "AssembleBench"
TIP = LAYOUT["tip_mm"]                                     # flange -> closed fingertips
TABLE_H = 750
N_PLANKS = 5


# --- 4x4 helpers (numpy)
def transl(x, y, z):
    t = np.eye(4)
    t[:3, 3] = (x, y, z)
    return t


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])


def at_z(p, z):
    p = p.copy()
    p[2, 3] = z
    return p


pi, deg = math.pi, math.radians

# --- where things are
WORK = np.array(LAYOUT["work_frame"], float)                 # logged work plate frame in robot base coordinates
ROBOT_Y = float((np.linalg.inv(WORK) @ [0, 0, 0, 1])[1])     # robot base's y in the work frame (152.99)
# ASSUMPTION: the T-slot plate IS the robot's logged work plate area: its near edge (x = 0) on the logged plate's
# near edge, centred on the robot's y, its top at the logged plate surface (work frame z = 0).
PLATE_IN_WORK = transl(0, ROBOT_Y - JL["plate"]["size"][1] / 2, 0)
PLATE = WORK @ PLATE_IN_WORK                                 # plate frame in robot base coordinates


def placed(entry):
    (x, y), t = JL[entry]["at"], JL[entry]["turn"]
    return transl(x, y, 0) @ rotz(deg(t))


BASE_A, BASE_B, RACK = placed("base_A"), placed("base_B"), placed("plank_rack")
# AS BUILT (measured on the real robot, 2026-11-06/07): where the jig parts really sit on the plate, from the taught
# grips (teach_v8.json). The program is planned from these, the 3D cell and the collision check show them; the jig
# DESIGN (jig_v5.py, JigAssembly_V5.STEP, jig_v5_layout.json: holes on the T-slot lines) is unchanged.
#   rack: all plank picks were taught at the same plate shift (plank 2) -> the rack sits there
#   base B (+ frame 1, its pieces, the guide on it): SHIFTED by the mean of the taught plank places 2, 5, 6 (they
#   scatter 1.4-6 mm around it; the taught corrections keep each one exact). Not turned: the flip (stage 4) needs base
#   B parallel to base A. A turn of ~1.5 deg fits the places better (gripper turned +1-1.5 deg at planks 5/6) - OPEN:
#   check on the real cell whether B is turned; then the flip must handle it.
#   base A: moved like base B (below); AMR: not measured yet (CAD)
AS_BUILT_RACK = transl(-2.06, -14.81, 0)                     # plate frame, mm
# the rack as built: PlankRack_V3 (jig-cad/Jig V3, made 2026-11-05: flanges on all 4 sides, one counterbored M5 hole
# each, flat bottom; code on branch backup/local-v8-draft-2026-11-06, jig_v3.py). Same slot grid and rack coordinates
# as PlankRack_V5 (jig_v5_layout.json), so only the 3D shape changes, not where the planks stand.
RACK_STL = "plank_rack_v8.stl"                              # = PlankRack_V3.stl (jig_parts/)
AS_BUILT_B = transl(8.5, -7.6, 0)                            # plate frame, mm
# base A: not measured; moved like base B (2026-11-07, Bjørge: the two bases are in line on the real cell, both on
# the same T-slot lines) - keeps the flip (stage 4) between them right
# 2026-11-07: moving the rack along its T-slot (plate x, - = towards the robot) gives the big half's side grip
# (BIG_GRIP_BACK "side") room: the rack stands 15 mm beside the tab's end. PROPOSAL, not on the real cell yet.
RACK_MOVE = 0.0
RACK, BASE_B, BASE_A = transl(RACK_MOVE, 0, 0) @ AS_BUILT_RACK @ RACK, AS_BUILT_B @ BASE_B, AS_BUILT_B @ BASE_A
# Base roles (Bjørge 2026-11-06: the guide starts on B, so the finished bench ends on A, beside the AMR).
# START: guide + frame 1 at the start, planks go in here; FINISH: frame 2, the finished bench. Swap to "A"/"B" to undo.
START_BASE, FINISH_BASE = "B", "A"
START, FINISH = (BASE_A if START_BASE == "A" else BASE_B), (BASE_A if FINISH_BASE == "A" else BASE_B)
MID = (150.0, 150.0)                                         # ASSUMPTION: middle of the plate (home, turns)

asm = {p["name"]: np.array(p["pose"], float) for p in json.loads((PARTS / "assembly.json").read_text())["parts"]}
# STEP (bench) -> base-local. v7's T_IN (Jig V2) puts frame 1 at z 9.5..19.5 = JigV3's pocket floor (9.5) too;
# JigV3's pocket is v7's pocket made mirror symmetric about local x. Fitted offsets (scratch fit of frame.stl into
# the pocket section at z 15, planks into the guide slots at z 50): x +0.5 mm. ASSUMPTION (fit, 0.5 mm grid)
T_IN = transl(0.5, 0, 0) @ transl(-2.715, -21.877, 134.5) @ rotx(pi / 2)
# turned over about base-local y (x mirrored, as JigV3's symmetric pocket takes it): frame 2 into base B's pocket
FLIP = transl(0, 0, 269) @ roty(pi)
GUIDE_ON_A = GUIDE_ON_B = np.eye(4)                          # the guide moves A -> B unturned (it is symmetric)
# 5 planks: JigV3's guide has 3 seat slots + 2 back slots; the back slots take assembly.json's plank5 and plank6
# (plank4, the lowest back plank, is fully blocked by the guide: checked in its z 50 section).
PLANKS = (1, 2, 3, 5, 6)                                     # ASSUMPTION: no plank4 in the 5-plank bench
assert len(PLANKS) == N_PLANKS
# rack slots: PlankRack_V2's 3 x 2 grid (rack-local x: column, y: row); plank k in v7's slot k, slot 4 empty
PITCH, PLANK_FLOOR = 30, 3
# order: near row (nearest the robot) first, so the robot never reaches over a standing plank in the rack; in base
# A the seat planks first (farthest from the rack), farthest-in-y first, the back planks last. ASSUMPTION
PLANK_ORDER = (2, 1, 3, 5, 6)


def rack_start(k):
    row, col = divmod(k - 1, 3)
    return RACK @ transl(PITCH * (col + 0.5), PITCH * (row + 0.5) + 2.5, 125 + PLANK_FLOOR) @ rotx(pi / 2)


# grips (TCP poses, tool z = approach, fingers close along tool x)
PLANK_GRIP = np.array([[0, -1, 0, 0], [0, 0, -1, 110], [1, 0, 0, 2.5], [0, 0, 0, 1.0]])   # v7 (plank coords)
PLANK_PUSH = np.array([[0, -1, 0, 0], [0, 0, -1, 125], [1, 0, 0, 2.5], [0, 0, 0, 1.0]])
# 2026-11-06, bases turned: plank 2's place needed J6 = 270 (the limit); the Hand-E is symmetric, so both plank
# grips are spun 180 deg about the tool axis (J6 ~180 deg lower)
PLANK_GRIP, PLANK_PUSH = PLANK_GRIP @ rotz(pi), PLANK_PUSH @ rotz(pi)
DOWN = rotx(pi)                                              # tool z down, tool x = local x
ARM_Z = 48                                                   # fingertips 12 mm below the guide top (z 60)
# DECISION 2026-11-06 (Claude, Bjørge asleep): the gripper is a Robotiq Hand-E (stroke 0-50 mm). Its fingers are
# modelled at the gap they have in each move (moves file "egp_gap": open = part width + 7, closed = part width;
# tests/robot_sim/collision.py rebuilds the fingers per move). Widths across the gripped feature:
GAP = {"plank": (5, 12), "arm": (10, 17), "foot": (7.5, 16)}    # (closed on the part, open), mm; arm = the 10 mm grip tab
ARM_Y = 63          # ASSUMPTION: guide grips 25-27 mm in from the arm tips (at y 78-80 the body hit the plank rack)
# Guide halves gripped only on their arms (base-local, across the arm, fingers along local x), at y 63 where both
# arms are 17 mm wide (small x 42.5..59.5, big 66.7..83.7) with the 7 mm back-plank slot between them: on the side
# without back planks that slot is empty and takes the inner finger (24 mm open). (Measured in the z 50 section.)
# Side: the arm away from the back planks (start base: -x, finish base: +x, the bench being turned over).
ARM_X = {"small": 51.0, "big": 75.2}                     # the side legs (gripped there until 2026-11-07)
# 2026-11-07 (Bjørge): grip the halves by the GRIP TAB in the middle - 10 mm wide (x -5..5), on top (z 45..60);
# small half (inner U) y -13..35, big half (outer) y -84..-36 (measured in jig_parts/guide_*_v5.stl). Middle of the
# free part of each tab; fingers close across it (local x).
GUIDE_TAB = {"small": (0.0, 22.0), "big": (0.0, -60.0)}   # base-local (x, y) of the grip, mm
GUIDE_LIFT, GUIDE_OUT = 25, 130   # off the base's bosses (z 40), then out along base-local +y past frame 1
# Grip orientation: tool down, spun 180 deg about the tool axis (fingers symmetric): upright and unspun the wrist
# (link 6) hit seat plank 2 when picking the halves off the start base (collision search). ASSUMPTION
SPIN = pi
# per half (2026-11-07): the TM5's wrist housing sits on one side of the tool axis; turning the grip 180 deg about the
# tool axis puts it on the other side (the Hand-E is symmetric: the fingers still close across the tab)
GUIDE_SPIN = {"small": SPIN, "big": 0.0}          # big: turned 180 deg - its wrist housing away from planks 1-3


# 2026-11-07: tilt about the CLOSING direction (tool x) so the gripper's top leans away from the standing planks
# (planks 1-3 stand 33 mm from the big half's tab; the body is +-45 mm): straight down it cannot reach the tab
GRIP_ROLL = {"small": 10, "big": 20}             # deg; big: top leans 20 deg away from planks 1-3; small 10: its wrist cleared frame 1 (searched 2026-11-07:
                                                 # roll -30..30 x tab y -55..-79 x spin 0/180 x wrist flip, collision.py)


def grips(side=-1, tilt=None, roll=None):
    """Guide grips in base-local coordinates on the arm on base-local x = side * ARM_X: -1 on the start base (away
    from its back planks), +1 on the finish base after the flip (its back planks are on -x)."""
    tilt = GRIP_TILT if tilt is None else tilt
    roll = GRIP_ROLL if roll is None else roll
    return {who: transl(side * GUIDE_TAB[who][0], GUIDE_TAB[who][1], ARM_Z) @ DOWN @ rotz(GUIDE_SPIN[who]) @ rotx(deg(roll[who]))
                 @ roty(side * deg(tilt[who])) for who in ("small", "big")}


# The big half's arm faces the other base where it is set down: upright, the Hand-E body (+-45 mm) hit the planks
# standing on the other base (collision.py). Tilted 15 deg about the arm, the body leans in over its own guide.
GRIP_TILT = {"small": 0, "big": 0}             # 2026-11-07: was -15 (for the old side-leg grip); with the tab grip 0         # start -> finish (stage 3)
# finish -> start (stage 6), straight onto the start base: -10 deg leans the body away from the bench still on the
# finish base (2026-11-06 scan, collision.py --parts: 0/+-8/+-15/+-25 and -11..-13 worse; from -11 link 4 hits frame 1
# at the pick). Left: the EGP box model (94 x 90) grazes plank 6 at the place; an 82 x 78 body clears it - check the
# Hand-E's real body on the robot.
GRIP_TILT_BACK = {"small": 0, "big": 0}       # 2026-11-07: was -10 (side-leg grip)
GRIP_ROLL_BACK = None                            # the roll on the finish base (stages 5/6); None = GRIP_ROLL
APPROACH_VERTICAL = ("big half", "guide big")   # these pick approaches come straight down (see pick_from_above)


# DECISION 2026-11-06 (Claude, Bjørge asleep): the big half is lifted straight up until its bottom is >= 15 mm over
# the plank tops, THEN turned 45 deg about z (through the grip point), then carried; never turned among the planks
# (turned at the seat it hits a plank's worth of cross-section at any pivot, either way: 2D check).
BIG_TURN = deg(-45)
PLANK_TOP = 260            # planks stand in frame 1 up to z 259.5 (base-local)
TURN_CLEAR = 15
# DECISION 2026-11-06 (Claude, Bjørge asleep): the guide is NOT taken out from under the turned-over bench (v7's
# stages 4/5). With JigV3's split the big half is trapped there: its back-plank slots (closed at both ends by its own
# teeth) only let it go -x, its seat notches only -y, and frame 1 sits on the planks above it (no vertical way out);
# turning it about any pivot hits a plank too (2D check). Instead the finished bench is lifted straight up out of the
# finish base (planks slide up out of the guide's slots: vertical, free; frame 2 then 49 mm over the guide) and set
# on the AMR first; then both halves are lifted off the empty finish base and set back on the start base.
# frame 1's rear foot (v7's FOOT_GRIP, + the 0.5 mm fit), tilted about the closing direction: v7's 60 deg left the
# elbow stretched at the finish base's far corner (J3 -9..-27, mu1 up to 22); 30 deg keeps J3 near -50
# 2026-11-06: bases turned (feet towards the robot); the OUTER foot (base-local x -60.8: plate y 300 on B, 0 on A),
# the inner one is beside the plank rack. Tilted about the closing direction so the gripper leans towards the robot.
FOOT_LEAN = deg(45)
C, S = math.cos(math.atan2(1.75, 10)), math.sin(math.atan2(1.75, 10))
FOOT_GRIP = transl(0.5, 0, 0) @ np.array([[C, -S, 0, -60.8], [-S, -C, 0, -96.7], [0, 0, -1, 12], [0, 0, 0, 1.0]]) @ rotx(FOOT_LEAN)
FLIP_SIGN = 1
FLIP_H, FLIP_STEP = 160, 15        # the turn-over axis lifted 160 mm (bench clears base A + guide), 15 deg per line
HAND_GRIP = transl(0, 0, 5) @ FOOT_GRIP @ rotx(-FOOT_LEAN) @ rotx(pi)
# AMR beside the plate on base A's side (-y), plate top level with the jig plate. ASSUMPTION
AMR_AT, AMR_PLATE = transl(100, -370, 0), (300, 320)
AMR_SHIFT, BENCH_LIFT = ((0, -400, -19) if FINISH_BASE == "B" else (0, -355, -19)), 100   # finish base -> AMR plate (frame 2 0.5 mm above it)
# AMR_SHIFT: the old stage 7 (bench set down lying on frame 2); no longer used by build(), kept for reference.
# 2026-11-07: the bench goes onto the AMR STANDING ON ITS FEET (both frames' legs down, seat up). In assembly.json
# coordinates (asm) the bench's up is -z: feet (soles) at asm z 77.5, backrest top at z -97.2; depth asm x -69.1..72.8
# (front legs at -x, backrest at +x), length asm y -125..125 (frame 1 at -125..-115, frame 2 at 115..125).
# Lying in the finish base, bench up = plate +x (feet towards the robot), frame 1 on top. Standing = turned so that
# bench up -> plate +z: about plate y by -90 deg, then BENCH_YAW about plate z (one turn about one axis, done in
# STAND_STEP lines while the bench is carried from the finish base to over the AMR).
# BENCH_ON_AMR: plate pose of the asm frame of a bench standing on the AMR plate (part pose = BENCH_ON_AMR @ asm[part];
# a 2nd bench stacked on this one: transl(0, 0, h) @ BENCH_ON_AMR). AMR_MARGIN = (x, y) mm from the AMR plate's edges
# nearest the robot (plate x 100, y -50) to the bench's footprint; soles BENCH_SET_DZ above the plate top (let go).
# BENCH_YAW -90: length along plate y, frame 1 at the near end (y -60), frame 2 at y -310, backrest at +x (away from the
# robot), front legs at plate x 110. Search 2026-11-07 (stage 7 only: yaw 0..-90, margins 10..150, grip h 45..140,
# STAND_LEAN 0..50): with a level grip (lean 0) yaw 0..-60 fold the elbow to J3's limit (flange too close to the
# robot) or hit J1_MAX, and yaw -90 swings the forearm into the guide halves on base B; with STAND_LEAN 35 yaw -60..-90
# are all lines, J5 103..145, J1 -14..-20. Yaw -90 keeps the footprint square to the plate (nearest corner, 10 mm).
BENCH_SOLE_Z, BENCH_X_MAX, BENCH_Y_HALF = 77.5, 72.8, 125.0      # asm: sole z, backrest's +x, half length
AMR_MARGIN, BENCH_SET_DZ = (10.0, 10.0), 0.5
BENCH_YAW = -90.0        # deg about plate z


def bench_on_amr(yaw=None, margin=None):
    """Plate pose of the asm frame of a bench standing on the AMR plate, turned yaw deg about plate z, its footprint
    (asm x -69.1..BENCH_X_MAX, y +-BENCH_Y_HALF) margin = (x, y) mm inside the plate's edges nearest the robot."""
    yaw = BENCH_YAW if yaw is None else yaw
    mx, my = AMR_MARGIN if margin is None else margin
    R = rotz(deg(yaw)) @ np.array([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1.0]])   # asm up (-z) -> +z
    c = R[:3, :3] @ np.array([[x, y, 0] for x in (-69.1, BENCH_X_MAX) for y in (-BENCH_Y_HALF, BENCH_Y_HALF)]).T
    return AMR_AT @ transl(mx - c[0].min(), AMR_PLATE[1] - my - c[1].max(), BENCH_SOLE_Z) @ R


BENCH_ON_AMR = bench_on_amr()
# Stage 7 grip (2026-11-07): frame 1's BACKREST from outside (asm -y), STAND_GRIP_H mm above the sole (asm z -62.5:
# between the slots of back planks 5 and 6, the planks fill them), fingers across the 10 mm backrest bar (leaning
# 10 deg like it), centred on it, tips 2.5 mm short of frame 1's inner face (as HAND_GRIP). Lying: tool straight down
# (bar at plate x ~258); standing: tool pointing plate -y, tilted STAND_LEAN down, gripper body well above the AMR.
# Not HAND_GRIP (the foot): there the fingers reach past the sole, so the bench cannot stand while held. A front-leg
# grip (STAND_GRIP_H <= 60, also handled below) is reachable too but puts the elbow near J3's limit (-144..-148).
STAND_GRIP_H = 140.0
_t = math.atan2(1.75, 10)                                        # the bars' lean (as FOOT_GRIP's C, S)
_zg = BENCH_SOLE_Z - STAND_GRIP_H
_xc = -63.6 + math.tan(_t) * (75 - _zg) if _zg > 5 else 53.0 - math.tan(_t) * (_zg + 10)   # front leg / backrest centre
# STAND_LEAN: tilted about the closing direction (as FOOT_LEAN), so that standing the tool points down at the bar and
# the wrist is lifted away from the bases (level, 0 deg: the forearm hit the guide halves on the start base and J5
# reached -177); lying, the Hand-E body leans away from the robot.
STAND_LEAN = 35.0
STAND_GRIP = transl(_xc, -117.5, _zg) @ np.array(
    [[math.cos(_t), math.sin(_t), 0, 0], [0, 0, 1, 0], [math.sin(_t), -math.cos(_t), 0, 0], [0, 0, 0, 1.0]]) @ \
    rotx(deg(STAND_LEAN))
GAP["leg"] = (10, 17)                                            # Hand-E across the 10 mm bar: closed, open
STAND_TURN_Z = 300        # the turn (from 'bench lift' to over the AMR) ends with the TCP this high, then straight down
STAND_ABOVE = 40          # fast down to the soles this far above the AMR plate, then slow
STAND_STEP = 15           # deg per line in the turn

# --- 2 benches (v8x2, bench_cell_v8x2.py): bench 2 stacked on bench 1 for transport. STACK = bench 2's pose in bench
# 1's STANDING frame (x along the bench = asm y, frame 1 at -x; y = depth = asm x, backrest at +y; z up = asm -z, seat
# top z 0, soles -77.5): turned yaw deg about z, pitched about x, shifted dx, dy, dz.
# Search 2026-11-07 (scratch stack_search*.py: height maps, bench 2 lowered straight down onto bench 1 + the AMR plate
# until it touches; stable = its centre of mass (uniform density, ASSUMPTION) inside the contacts, margin > 3 mm; exact
# contact height then with fcl): chosen - bench 2 TURNED 180 deg, frames over bench 1's frames (dx 0), its BACK LEGS
# standing on bench 1's seat (rear seat plank, in front of bench 1's backrest), its seat lying on the top of bench 1's
# backrest, tilted 20.5 deg (its backrest leans over bench 1's seat); top of the stack 168 mm over bench 1's seat
# (246 mm over the AMR plate; bench 1 alone 175), COM 12 mm inside the contacts. tests/robot_sim/v8x2_stack.png.
# Rejected: same facing (yaw 0) - the back legs cannot go down between bench 1's seat and back planks: they lean
# backwards, so their upper ends sit over the rear seat plank (plank 3) and stop on it while the feet still hang in the
# gap; with nothing under the front legs (they stand in front of bench 1) bench 2 tips forward. Its only stable yaw-0
# poses have the front legs on bench 1's seat and the seat on bench 1's backrest, the back legs hanging behind it: top
# 206 mm (284 over the AMR). Frames beside each other (dx +-11.5, so the 10 mm frames miss): no stable pose at all (the
# outer frame stands on nothing, all contacts at one end). Less tilt (yaw 180, dy 26, pitch 15: top 172) is more stable
# (margin 22 mm) but higher; more (dy 56, pitch 24.5: top 163) leaves only 4.7 mm margin.
STACK = {"dx": 0.0, "dy": 50.0, "dz": 99.7, "pitch": 20.5, "yaw": 180.0}
R_STAND = np.array([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1.0]])   # asm -> standing frame (own inverse)


def bench_on_stack(stack=None, under=None):
    """Plate pose of bench 2's asm frame stacked on the bench at `under` (default BENCH_ON_AMR)."""
    s = STACK if stack is None else stack
    under = BENCH_ON_AMR if under is None else under
    Q = transl(s["dx"], s["dy"], s["dz"]) @ rotx(deg(s.get("pitch", 0.0))) @ rotz(deg(s["yaw"]))
    return under @ R_STAND @ Q @ R_STAND


BENCH2_ON_STACK = bench_on_stack()
STACK_TURN_Z = STAND_TURN_Z + 120   # bench 2's turn ends this high (TCP), then straight down onto bench 1
STACK_LIFT_Z = 500                  # bench 2 lifted straight up to this (TCP) before the turn (bench 1 is beside it)
STACK_BACK_DZ = 60                  # straight up this far from the stack after the release (far end: higher is out of reach)
# (Bjørge 2026-11-06: nothing but the finished bench goes on the AMR; the big half is NOT parked there - it goes
# straight from the finish base onto the start base, see GRIP_TILT_BACK.)
BIG_LIFT = 90                     # the big half turns above the plank rack (100) and the small half on B (60)
BACK_TURN = deg(45)               # the big half's turn on the way out (away from base B, where the small half is)
# 2026-11-07 (Bjørge): stage 6, big half out of the finished bench on the finish base. After the flip frame 1 lies
# right above the grip tab, so the gripper can't come straight down: it comes in at a slant, past frame 1's edge, from
# BIG_SIDE_IN (plate mm from the grip). Then the guide is lifted BIG_LIFT to the middle of the bench
# (bottom over the plank rack's height), turned BIG_SNAP about z through the grip, away from the AMR - on the real
# jig that snaps the guide off the bench - and the robot waits BIG_HELP_MS so people can help. Then out and onto
# the start base (the guide still passes planks in the model there: accepted, it is loose after the snap).
BIG_SIDE_IN = (-31, 0, 116)       # 120 mm, 75 deg up, towards -x: the one free line (scratch probe stage6_dirs.py)
BIG_SNAP = deg(30)
BIG_HELP_MS = 5000
BIG_EXIT = "back"                 # after the pause: "back" (the way the gripper came in; fewest hits), "out" (base-local +y), "up"
# 2026-11-07 (Bjørge): stage 6 grip "side": the tab's END, from the robot side (tool along base-local +y, tilted
# BIG_SIDE_PITCH down from horizontal, fingers closing across the 10 mm tab), so the gripper stays outside the bench
# for the lift and the turn. Placed on the start base with the same grip. "top": the tab from above (BIG_SIDE_IN).
BIG_GRIP_BACK = "end"   # 2026-11-07: "end" (BIG_END, let go END_DROP over the seat on B): no gripper/arm hit. "leg" (BIG_LEG):
                        # also clean. "top": the tab
                        # from above (BIG_SIDE_IN): the 30 deg turn hits frame 1 + planks 1-2. "side": the tab's end from the
                        # robot side: clean of the rack only at pitch 65, then the turn hits like "top". "end": the free back
                        # end (BIG_END): on B the small half sits flush inside that corner (0 mm gap): solved by letting go
                        # END_DROP mm above the seat (fingers stay over the small half).
TAB_END_Y, TAB_Z = -85.5, 52.5    # big half's tab (base-local): end at y -85.5 (tab y -85.5..-40.5), z 45..60
BIG_SIDE_PITCH, BIG_SIDE_DEPTH, BIG_SIDE_BACK = 65, 28, 80   # deg down, fingers this far onto the tab, approach mm

# 2026-11-07 (Bjørge, screenshot): "leg" = the big half's U-leg at its robot end, from above, fingers closing across
# the leg (41 mm thick there: Hand-E nearly fully open), the gripper leaning OUT of the bench by roll deg so frame 1
# (it overhangs the leg's inner part) stays clear. x = plate x of the grip on base A. side -1 = the leg on base B's
# side (+1 = the AMR side, as marked: same at A, but at B its lean points back at the bench on A and the wrist hits
# frame 1). Search (collision.py per candidate): side -1, x 140, roll 45 -> no gripper / arm hit in stage 6.
BIG_LEG = {"side": -1, "x": 140.0, "roll": 45.0, "spin": 0.0}
LEG_MID_X, LEG_GAP = 59.5, (41, 50)             # base-local |x| of the leg's middle at its robot end; Hand-E gap


def leg_grip(side=None, x=None, roll=None, spin=None):
    L = BIG_LEG
    s = L["side"] if side is None else side
    r = math.radians(L["roll"] if roll is None else roll)
    z = np.array([-s * math.sin(r), 0, -math.cos(r)]); xa = np.array([math.cos(r), 0, -s * math.sin(r)])
    T = np.eye(4); T[:3, :3] = np.column_stack([xa, np.cross(z, xa), z])
    T[:3, 3] = (s * LEG_MID_X, (L["x"] if x is None else x) - 218.5, ARM_Z)
    return T @ rotz(L["spin"] if spin is None else spin)

# 2026-11-07 (Bjørge, 2nd screenshot): "end" = the big half's free BACK end: the AMR-side leg's far corner (plate x
# 296-304 on base A, a ~10 mm wall, y about -30..-20, z 20-60), outside frame 1 in x (to 293.9) and y (from -18.9).
# From above, fingers across the wall (closing along plate y, turned yaw deg), the gripper leaning tilt deg towards
# azimuth az (plate deg: 0 = +x, away from the robot; -90 = towards the AMR) so it clears frame 1's corner.
# Search 2026-11-07 (collision.py per candidate): the B-side leg's back end (y 129.5: wall y 124.6..134.6 at x 298),
# leaning 55 deg away from the robot (+x), fingers across the wall.
BIG_END = {"x": 298.0, "y": 129.5, "az": 0.0, "tilt": 55.0, "yaw": 0.0}
END_GAP = (10, 18)
END_HIGH = 290                    # travel height at the far end (LIFT_Z 450 is out of reach that far out)
# Bjørge 2026-11-07: the halves locate on their own (bosses), so on the start base the big half is let go END_DROP mm
# above its seat: the fingertips (z 48 at the grip) then stay over the small half's top (z 60), which sits flush
# inside this corner.
END_DROP = 18.0                   # 17 is the least with no hit; 15 grazes the small half


def end_grip(x=None, az=None, tilt=None, yaw=None):
    """Base-local TCP pose (finish/start base) of the "end" grip, defined on base A in plate terms."""
    E = BIG_END
    t, a = math.radians(E["tilt"] if tilt is None else tilt), math.radians(E["az"] if az is None else az)
    z = -np.array([math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t)])
    yw = math.radians(E["yaw"] if yaw is None else yaw)
    c = np.array([-math.sin(yw), math.cos(yw), 0.0])          # closing direction: plate y, turned by yaw
    xa = c - z * (c @ z); xa /= np.linalg.norm(xa)
    T = np.eye(4); T[:3, :3] = np.column_stack([xa, np.cross(z, xa), z])
    T[:3, 3] = (E["x"] if x is None else x, E["y"], ARM_Z)
    return np.linalg.inv(FINISH @ GUIDE_ON_B) @ T


def side_grip(pitch=None, depth=None):
    a = math.radians(BIG_SIDE_PITCH if pitch is None else pitch)
    z = np.array([0, math.cos(a), -math.sin(a)]); x = np.array([1.0, 0, 0]); y = np.cross(z, x)
    T = np.eye(4); T[:3, :3] = np.column_stack([x, y, z])
    T[:3, 3] = (0, TAB_END_Y + (BIG_SIDE_DEPTH if depth is None else depth), TAB_Z)
    return T

PICK_Z = 420       # over the rack, empty: gripper body (TCP + 37) over the plank tops (253)
PLANK_PICK_DZ = -10  # 2026-11-06, real robot: GRIP at the plank rack closed on air -> pick 10 mm lower (world z, rack only)
TRAVEL_Z = 520     # planks carried with their lower end (235 mm under the TCP) over standing planks (top 260)
LIFT_Z = 450       # guide halves / frame 1 carried at this height
FLIP_Z = 340       # foot grip on base B at z 380+ is out of reach (far corner); flipped planks still clear the guide
SUB_LIFT = 40
BACK_Z = 330       # up from the AMR (450 there: elbow nearly stretched, mu1 5)
SUB_AWAY = 30      # after the release: fingers slid off the foot's end (plate -x), then straight up
APPROACH, FAST, SLOW = 40, 100, 20
PLANK_APPROACH, PLANK_LIFT = 15, 50   # plank picks: last stop 15 mm above the grab; lift out of the rack at 50 mm/s

STAGES = ["planks_into_frame1", "small_half_to_finish", "big_half_to_finish", "frame1_into_frame2",
          "small_half_back", "big_half_back", "bench_to_amr"]


# --- kinematics
def tcp_to_flange_tm(T):
    """Plate-frame TCP pose -> TM flange pose [x, y, z, rx, ry, rz] in robot base coordinates."""
    m = PLATE @ T @ transl(0, 0, -TIP)
    return kin.mat_to_pose(m.tolist())


def interp(T0, T1, f):
    """Pose between T0 and T1 (straight line, rotation about one axis)."""
    R = T0[:3, :3].T @ T1[:3, :3]
    a = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))
    out = np.eye(4)
    if a < 1e-9:
        out[:3, :3] = T0[:3, :3]
    else:
        k = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
        if np.linalg.norm(k) < 1e-9:                         # 180 deg
            k = np.sqrt(np.maximum(0, (np.diag(R) + 1) / 2))
        k = k / np.linalg.norm(k)
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        t = f * a
        out[:3, :3] = T0[:3, :3] @ (np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K)
    out[:3, 3] = T0[:3, 3] + f * (T1[:3, 3] - T0[:3, 3])
    return out


# v5's Home joints (RoboDK station): shoulder facing the cell (the cell is at robot -x, J1 near 0)
HOME_SEED = [-14.09, 2.92, -80.10, -12.75, -90.01, 75.89]
J1_MAX = 100                                                 # as robot_cell.ik: |J1| < 100 deg (shoulder facing the cell)


# 2026-11-07: the wrist housing (J5/J6, ~110 mm beside the tool axis) hit the planks standing in frame 1 when the big
# guide half is gripped by its tab: with the wrist flipped (J5 the other sign) it sits on the robot's side instead.
# Moves whose name starts with one of these use the flipped wrist (J5 > 0); None = the program's usual choice.
WRIST_FLIP = ()                                   # e.g. ("guide big", "big half"): set by the check below


def solve(flange, near, wrist=None):
    """IK nearest `near`, shoulder facing the cell (|J1| < J1_MAX, robot_cell.ik's rule) and elbow up (J3 < 0, as
    Home: elbow-down solutions put links 2/3 into the table and the bases this close to the robot); falls back to
    any |J1| < J1_MAX solution."""
    cands = []
    for seed in (near, [near[0], near[1], near[2], near[3], -near[4], near[5]], HOME_SEED,
                 [near[0], 20, -90, -20, -90, near[5]], [near[0], 0, -120, 30, -90, near[5]],
                 [near[0], 40, -140, 10, -90, near[5]], [near[0], 20, -90, -20, 90, near[5]],
                 [0, 0, 90, 0, 90, 0], [0, 30, -120, 0, -90, 0], [-40, 10, -100, 0, -90, 0], [40, 10, -100, 0, -90, 0]):
        q = kin.ik(flange, seed, seeds=False)
        if q is not None and abs(q[0]) <= J1_MAX:
            q = kin._wrap_near(q, near)
            if q[5] > 180 and q[5] - 360 >= -265:       # 2026-11-06: J6 on the low turn. The taught plank grips
                q[5] -= 360                             # (wrist side kept, Hand-E tilted on the flange) put the place
            if kin.within_limits(q):                    # at J6 270.2 (past the limit) - at -89.8 it is 32 deg from the pick
                cands.append(q)
    if wrist == "flip":
        cands = [q for q in cands if q[4] > 0]
    elif wrist == "normal":
        cands = [q for q in cands if q[4] < 0]
    if not cands:
        return None
    up = [q for q in cands if q[2] < 0] or cands
    return min(up, key=lambda q: sum(w * (a - b) ** 2 for w, a, b in zip((3, 3, 2, 1, 1, 0.5), q, near)))


class Program:
    def __init__(self, stages=None):
        self.stages = list(stages or STAGES)                 # stage names (stage k = stages[k - 1])
        self.q = list(HOME_SEED)
        self.T = None
        self.steps, self.stage, self.speed = [], 1, FAST
        self.bad, self.lines_to_ptp = [], []
        self.gap = GAP["plank"][1]                           # Hand-E finger gap (mm) in force

    def move(self, name, T, kind="line"):
        T_plan, T = T, teach_overrides.apply(name, T, VERSION)   # grip points taught on the robot (tests/robot_sim/teach.py)
        flange = tcp_to_flange_tm(T)
        q = solve(flange, self.q, "flip" if name.startswith(WRIST_FLIP) and WRIST_FLIP else None)
        if q is None:
            self.bad.append(f"{self.stages[self.stage - 1]}: {name}")
            q = self.q
        if kind == "line" and self.T is not None and not self.followable(T):
            kind = "ptp"                                     # as v7's link(): a joint move if no straight one
            self.lines_to_ptp.append(name)
        self.steps.append({"stage": self.stage, "name": name, "move": "ptp" if kind == "ptp" else "line",
                           "joints": [round(v, 4) for v in q], "flange": [round(v, 4) for v in flange],
                           "speed": float(self.speed), "egp_gap": float(self.gap),
                           **({"planned_flange": [round(v, 4) for v in tcp_to_flange_tm(T_plan)]} if T is not T_plan else {})})
        self.q, self.T = list(q), T.copy()

    def followable(self, T1, n=24):
        q = self.q
        for i in range(1, n + 1):
            q2 = kin.ik(tcp_to_flange_tm(interp(self.T, T1, i / n)), q, seeds=False)
            if q2 is None or max(abs(a - b) for a, b in zip(q2, q)) > 25:
                return False
            q = q2
        return True

    def ptp(self, name, T):
        self.move(name, T, "ptp")

    def line(self, name, T):
        self.move(name, T, "line")

    def set_speed(self, v):
        self.speed = v

    def gripper(self, close, action=None, parts=(), gap=None):
        if gap is not None:
            self.gap = gap
        self.steps.append({"stage": self.stage, "name": f"Set IO_0={1 if close else 0}", "do0": int(close),
                           "gripper": action, "parts": list(parts)})

    def wait(self, ms, name):
        """The robot stands still ms milliseconds (TMflow WaitFor; v4_replay / step_run sleep)."""
        self.steps.append({"stage": self.stage, "name": name, "wait_ms": int(ms)})

    def reload(self, name, tag, spawn):
        """The robot stands still at Home until people have reloaded the jig and pressed Resume (v4_replay: a hold on
        the 3D page; step_run: an Enter prompt; TMflow export: a message + a long WaitFor). Never a gripper action.
        spawn: {part name: plate pose} - the next bench's parts, which appear (3D view, collision check) here."""
        self.steps.append({"stage": self.stage, "name": name, "reload": tag,
                           "spawn": {k: np.round(v, 4).tolist() for k, v in spawn.items()}})


def stages_for(n_benches=1):
    """Stage names: bench 1 = STAGES (1-7); each further bench b: a reload stage (8 for bench 2), then its 7 stages
    (9-15), the last one setting it on the bench before (stacked)."""
    out = list(STAGES)
    for b in range(2, n_benches + 1):
        out += [f"reload_jig_for_bench_{b}"] + [f"bench_{b}_{s}" for s in STAGES[:-1]] + [f"bench_{b}_onto_bench_{b - 1}"]
    return out


def tag_of(b):
    """Part-name suffix of bench b: "" for bench 1, " #2" for bench 2 ("frame1 #2", "plank3 #2", "piece A1 #2")."""
    return "" if b == 1 else f" #{b}"


def build(n_benches=1):
    """The program: bench 1's stages 1-7 (n_benches = 1: exactly v8's AssembleBench); with n_benches = 2 (v8x2,
    bench_cell_v8x2.py) then a reload hold (stage 8: people put new frames, pieces and planks in, the robot waits at
    Home) and bench 2's stages 9-15, the same moves with the #2 parts, set on top of bench 1 (BENCH2_ON_STACK)."""
    assert n_benches in (1, 2), "the stacked place is worked out for 2 benches (BENCH2_ON_STACK)"
    p = Program(stages_for(n_benches))
    home = transl(MID[0], MID[1], LIFT_Z) @ DOWN
    p.ptp("Home", home)
    for b in range(1, n_benches + 1):
        if b > 1:
            p.stage = 8 * (b - 1)
            tag = tag_of(b)
            p.reload(f"reload the jig for bench {b}", tag.strip(),
                     {n + tag: P for n, kind, _, P, _ in cell_objects() if kind in ("frame", "piece", "plank")})
        _bench(p, home, b)
    return p


def _bench(p, home, b=1):
    """Stages 1-7 of bench b into Program p (stage numbers 8 * (b - 1) + 1..7, part names + tag_of(b)); the guide
    halves are the same for every bench. Bench 1 goes onto the AMR (BENCH_ON_AMR), bench 2 onto bench 1."""
    s0, tag = 8 * (b - 1), tag_of(b)
    T_ = lambda n: n + tag                                   # noqa: E731  this bench's part name
    p.stage = s0 + 1
    GRIP_ = grips()
    final = {k: START @ T_IN @ asm[f"plank{k}"] for k in PLANKS}
    sub_parts = [T_("frame1")] + [T_(f"plank{k}") for k in PLANKS] + [T_(f"piece A{k}") for k in PLANKS]

    # 1  planks
    for k in PLANK_ORDER:
        pick, place, push = rack_start(k) @ PLANK_GRIP, final[k] @ PLANK_GRIP, final[k] @ PLANK_PUSH
        pick = transl(0, 0, PLANK_PICK_DZ) @ pick
        p.set_speed(FAST)
        p.ptp(f"plank{k} pick travel", at_z(pick, PICK_Z))   # empty gripper: lower (z 520 that close to J1: mu1 3.1)
        # 2026-11-07 (Bjørge): fewer stops at the rack - fast down to just above the grab, slow the last bit, grab,
        # one straight lift to travel height ('pick out' at +60 removed)
        p.line(f"plank{k} pick approach", at_z(pick, pick[2, 3] + PLANK_APPROACH))
        p.set_speed(SLOW)
        p.line(f"plank{k} pick", pick)
        p.gripper(True, "grip", [T_(f"plank{k}")], gap=GAP["plank"][0])
        p.set_speed(PLANK_LIFT)
        p.line(f"plank{k} pick up", at_z(pick, TRAVEL_Z))
        p.set_speed(FAST)
        p.ptp(f"plank{k} place travel", at_z(place, TRAVEL_Z))
        p.line(f"plank{k} above guide", at_z(place, place[2, 3] + 55))   # 2026-11-06: 55 (was 75), closer to watch
        p.set_speed(SLOW)
        p.line(f"plank{k} place", place)
        p.gripper(False, "release", [T_(f"plank{k}")], gap=GAP["plank"][1])
        # 2026-11-06: the push (push approach / push / push out, closed fingers on the plank) is gone - on the real
        # robot the place itself presses the plank into the interface; after the release the push only moved in air
        p.set_speed(FAST)
        p.line(f"plank{k} place up", at_z(place, TRAVEL_Z))

    def pick_from_above(label, grip, parts, high=LIFT_Z, gap=GAP["arm"]):
        p.gripper(False, gap=gap[1])                         # Hand-E opened to the part + 7 mm
        p.set_speed(FAST)
        p.ptp(f"{label} over pick", at_z(grip, high))
        # tilted grips (GRIP_ROLL): straight down onto the grip, not back along the tilted tool axis - that point lies
        # to the side, and on the way to it the big half's gripper clipped frame 1 (stage 6, 2026-11-07)
        appr = at_z(grip, grip[2, 3] + APPROACH) if label.startswith(APPROACH_VERTICAL) else grip @ transl(0, 0, -APPROACH)
        p.line(f"{label} pick approach", appr)
        p.set_speed(SLOW)
        p.line(f"{label} pick", grip)
        p.gripper(True, "grip", parts, gap=gap[0])

    def put_down(label, place, parts, back=APPROACH, gap=GAP["arm"], high=LIFT_Z, drop=0.0):
        """drop: let go this many mm above the seat; the part falls onto its own locating features (bosses)."""
        place = at_z(place, place[2, 3] + drop)
        p.set_speed(FAST)
        p.ptp(f"{label} over place", at_z(place, high))
        p.line(f"{label} place approach", at_z(place, place[2, 3] + APPROACH))
        p.set_speed(SLOW)
        p.line(f"{label} place", place)
        p.gripper(False, "release", parts, gap=gap[1])
        p.line(f"{label} place out", at_z(place, place[2, 3] + back))      # straight up (the grip may be tilted)
        p.set_speed(FAST)
        p.line(f"{label} place out up", at_z(place, high))

    # 2  guide halves A -> B, small first (straight up along the planks), then the big one (lifted clear, turned 45)
    p.stage = s0 + 2
    g = START @ GUIDE_ON_A @ GRIP_["small"]
    pick_from_above("guide small", g, ["Guide small"])
    p.line("guide small lift off", at_z(g, g[2, 3] + PLANK_TOP))
    p.set_speed(FAST)
    p.line("guide small up", at_z(g, LIFT_Z))
    put_down("guide small", FINISH @ GUIDE_ON_B @ GRIP_["small"], ["Guide small"])
    p.stage = s0 + 3
    g = START @ GUIDE_ON_A @ GRIP_["big"]
    pick_from_above("guide big", g, ["Guide big"])
    high = at_z(g, g[2, 3] + PLANK_TOP + TURN_CLEAR)          # bottom (z 20) >= 15 mm over the plank tops
    p.line("guide big lift off", high)
    turned = high.copy()
    turned[:3, :3] = rotz(BIG_TURN)[:3, :3] @ high[:3, :3]   # about z through the grip point, clear of the planks
    p.line("guide big turn 45", turned)
    p.set_speed(FAST)
    p.line("guide big up", at_z(turned, LIFT_Z))
    put_down("guide big", FINISH @ GUIDE_ON_B @ GRIP_["big"], ["Guide big"])

    # 4  frame 1 + planks turned over into frame 2: FINISH @ FLIP = a 180 deg turn about an axis along plate x
    #    (checked below); done about that axis lifted FLIP_H, foot over the top (away from the arm), in lines
    p.stage = s0 + 4
    pick, place = START @ FOOT_GRIP, FINISH @ FLIP @ FOOT_GRIP
    M = FINISH @ FLIP @ np.linalg.inv(START)
    assert np.allclose(M[:3, :3], rotx(pi)[:3, :3], atol=1e-6), "flip is not a turn about plate x"
    yc, zc = M[1, 3] / 2, M[2, 3] / 2                         # rotx(pi) about (yc, zc): y -> 2yc - y, z -> 2zc - z
    about = lambda a: transl(0, yc, zc + FLIP_H) @ rotx(a) @ transl(0, -yc, -zc - FLIP_H)
    p.set_speed(FAST)
    p.gripper(False, gap=GAP["foot"][1])
    p.ptp("sub over pick", at_z(pick, pick[2, 3] + 120))
    p.line("sub pick approach", at_z(pick, pick[2, 3] + SUB_LIFT))
    p.set_speed(SLOW)
    p.line("sub pick", pick)
    p.gripper(True, "grip", sub_parts, gap=GAP["foot"][0])
    p.line("sub pick out", at_z(pick, pick[2, 3] + SUB_LIFT))
    p.set_speed(FAST)
    p.line("sub up", transl(0, 0, FLIP_H) @ pick)
    for a in range(FLIP_STEP, 181, FLIP_STEP):
        p.line(f"sub turn {a}", about(FLIP_SIGN * deg(a)) @ transl(0, 0, FLIP_H) @ pick)
    p.line("sub above guide", at_z(place, place[2, 3] + 75))
    p.set_speed(SLOW)
    p.line("sub place", place)
    p.gripper(False, "release", sub_parts, gap=GAP["foot"][1])
    out = transl(-SUB_AWAY, 0, 0) @ place                    # fingers slid off the end of the foot (towards the robot)
    p.line("sub place out", out)
    p.set_speed(FAST)
    p.line("sub back up", at_z(out, LIFT_Z))                 # fingers clear of the foot: straight up

    # 5, 6  guide halves out from between the frames (Bjørge: before the bench can be lifted), back to the start base
    # DECISION 2026-11-06 (Bjørge: "the 45 degrees is meant for that, don't worry about that detail now"): the big
    # half is lifted, turned 45 deg about its grip and slid out; in the model it still rubs planks in the turn
    # (collision.py lists it as the one known hit) - to be checked on the real jig.
    GF = grips(+1, GRIP_TILT_BACK, GRIP_ROLL_BACK)
    out_dir = FINISH[:3, :3] @ np.array([0, 1.0, 0])         # base-local +y in plate coordinates
    for stage, who in ((5, "small"), (6, "big")):
        p.stage = s0 + stage
        label = f"{who} half"
        g = FINISH @ GUIDE_ON_B @ GF[who]
        if who == "small":
            pick_from_above(label, g, [f"Guide {who}"])
            up = transl(0, 0, GUIDE_LIFT) @ g
            p.line(f"{label} lift off bosses", up)
            slid = transl(*(out_dir * GUIDE_OUT)) @ up
            p.line(f"{label} slide out", slid)
        else:                                                # see BIG_GRIP_BACK / BIG_SIDE_IN / BIG_SNAP
            if BIG_GRIP_BACK in ("side", "leg", "end"):
                g = FINISH @ GUIDE_ON_B @ {"side": side_grip, "leg": leg_grip, "end": end_grip}[BIG_GRIP_BACK]()
                side = g @ transl(0, 0, -BIG_SIDE_BACK)      # back along the gripper, out of the bench
            else:
                side = transl(*BIG_SIDE_IN) @ g
            gap = {"leg": LEG_GAP, "end": END_GAP}.get(BIG_GRIP_BACK, GAP["arm"])
            p.gripper(False, gap=gap[1])
            p.set_speed(FAST)
            high = END_HIGH if BIG_GRIP_BACK == "end" else LIFT_Z
            p.ptp(f"{label} over pick", at_z(side, high))
            p.line(f"{label} pick side", side)               # straight down to the start of the way in
            p.set_speed(SLOW)
            p.line(f"{label} pick", g)                       # in along the gripper onto the tab
            p.gripper(True, "grip", [f"Guide {who}"], gap=gap[0])
            up = transl(0, 0, BIG_LIFT) @ g
            p.line(f"{label} lift to mid bench", up)
            # the turn's sign: the one that moves the guide away from the AMR (plate +y) about this grip point
            c = (FINISH @ GUIDE_ON_B @ np.array([0, -1.5, 40, 1.0]))[:2] - up[:2, 3]
            snap = max((BIG_SNAP, -BIG_SNAP), key=lambda a: math.sin(a) * c[0] + math.cos(a) * c[1])
            t = up.copy()
            t[:3, :3] = rotz(snap)[:3, :3] @ up[:3, :3]
            p.line(f"{label} snap turn {round(math.degrees(BIG_SNAP))}", t)
            p.wait(BIG_HELP_MS, f"{label} wait {BIG_HELP_MS // 1000} s (people can help)")
            back = side[:3, 3] - g[:3, 3]                    # the way the gripper came in
            slid = {"out": transl(*(out_dir * GUIDE_OUT)) @ t, "back": transl(*back) @ t, "up": t}[BIG_EXIT]
            if BIG_EXIT != "up":
                p.line(f"{label} slide out", slid)
        high = END_HIGH if who == "big" and BIG_GRIP_BACK == "end" else LIFT_Z
        p.set_speed(FAST)
        p.line(f"{label} up", at_z(slid, high))
        # Bjørge 2026-11-06: both halves go from the finish base straight onto the start base - never onto the AMR
        back_grip = {"side": side_grip, "leg": leg_grip, "end": end_grip}.get(BIG_GRIP_BACK) if who == "big" else None
        put_down(label, START @ GUIDE_ON_A @ (back_grip() if back_grip else GF[who]), [f"Guide {who}"],
                 gap={leg_grip: LEG_GAP, end_grip: END_GAP}.get(back_grip, GAP["arm"]), high=high,
                 drop=END_DROP if back_grip is end_grip else 0.0)

    # 7  finished bench: gripped at frame 1's backrest from above (STAND_GRIP), lifted out of the finish base, turned
    #    up onto its feet on the way to the AMR (one turn about one axis, STAND_STEP deg per line, ending STAND_TURN_Z
    #    over the place), straight down and let go standing (BENCH_ON_AMR)
    p.stage = s0 + 7
    lying = FINISH @ FLIP @ T_IN                              # asm -> plate, bench in the finish base
    grip = lying @ STAND_GRIP
    # the same grip, bench standing on the AMR (bench 1) or on top of bench 1 (bench 2: BENCH2_ON_STACK)
    stand = (BENCH_ON_AMR if b == 1 else BENCH2_ON_STACK) @ STAND_GRIP
    pre, turn_z = ("bench", STAND_TURN_Z) if b == 1 else ("bench stack", STACK_TURN_Z)   # place-side move names
    bench_parts = [T_(n) for n in ["frame1", "frame2"] + [f"plank{k}" for k in PLANKS] +
                   [f"piece A{k}" for k in PLANKS] + [f"piece B{k}" for k in PLANKS]]
    p.set_speed(FAST)
    p.gripper(False, gap=GAP["leg"][1])
    p.ptp("bench over pick", at_z(grip, grip[2, 3] + 60))
    p.set_speed(SLOW)
    p.line("bench pick", grip)
    p.gripper(True, "grip", bench_parts, gap=GAP["leg"][0])
    lifted = transl(0, 0, BENCH_LIFT) @ grip
    p.line("bench lift", lifted)
    p.set_speed(FAST)
    if b > 1:                                                # bench 1 stands on the AMR beside the finish base: turn
        lifted = at_z(lifted, STACK_LIFT_Z)                  # bench 2 above it, not through it
        p.line("bench stack lift", lifted)
    turned = at_z(stand, turn_z)
    for a in range(STAND_STEP, 91, STAND_STEP):
        p.line(f"{pre} stand turn {a}", interp(lifted, turned, a / 90))
    p.line(f"{pre} lower", transl(0, 0, STAND_ABOVE) @ stand)
    p.set_speed(SLOW)
    p.line(f"{pre} down", transl(0, 0, BENCH_SET_DZ) @ stand)
    p.gripper(False, "release", bench_parts, gap=GAP["leg"][1])
    out = transl(0, 0, BENCH_SET_DZ) @ stand @ transl(0, 0, -40)   # back along the tool, off the bar
    p.line(f"{pre} place out", out)
    p.set_speed(FAST)
    p.line("back up" if b == 1 else "stack back up", at_z(out, BACK_Z if b == 1 else out[2, 3] + STACK_BACK_DZ))
    p.ptp("Home", home)


def cell_objects(n_benches=1):
    """(name, kind, mesh file or box (lo, hi), pose in the plate frame, colour) of every object at the start
    (rack and base B as built: AS_BUILT_RACK / AS_BUILT_B above). n_benches = 2 (v8x2): also bench 2's frames, pieces
    and planks ("frame1 #2", ...) at the same start poses - they are spawned at the reload (hidden until then)."""
    grey, wood, frame_c, red = [0.7, 0.72, 0.75, 1], [0.75, 0.55, 0.3, 1], [0.55, 0.62, 0.75, 1], [0.85, 0.1, 0.1, 1]
    jig_c, guide_c = [0.35, 0.55, 0.85, 1], [0.95, 0.75, 0.2, 1]
    ps, th = JL["plate"]["size"][0], JL["plate"]["size"][2]
    objs = [("Table", "table", ((-350, -40, -TABLE_H), (ps + 10, ps + 40, -th)), np.eye(4), [0.78, 0.74, 0.68, 1]),
            ("T-slot plate", "plate", JIG / JL["plate"]["stl"], np.eye(4), grey),
            ("Base A", "jig", JIG / JL["base_A"]["stl"], BASE_A, jig_c),
            ("Base B", "jig", JIG / JL["base_B"]["stl"], BASE_B, jig_c),
            ("Plank rack", "jig", JIG / RACK_STL, RACK, [0.45, 0.47, 0.5, 1]),
            ("AMR plate", "amr", ((0, 0, -10), (AMR_PLATE[0], AMR_PLATE[1], 0)), AMR_AT, [0.4, 0.75, 0.45, 1]),
            ("AMR top module", "amr", ((40, 40, 383 - TABLE_H - th), (AMR_PLATE[0] - 40, AMR_PLATE[1] - 40, -10)), AMR_AT,
             [0.85, 0.85, 0.88, 1]),
            # the Omron LD-250 under it (amr_ld250.py: simplified, 963 x 718 x 383, x = drive direction), on the floor,
            # where RoboDK's v4 station had its library model (AMR frame x 150, y -40): beside the table, not under it
            *[(f"AMR LD-250 {part}", "amr", JIG / f"ld250_{part}.stl",
               AMR_AT @ transl(AMR_PLATE[0] / 2, -40, -TABLE_H - th), c)
              for part, c in (("body", [0.22, 0.23, 0.25, 1]), ("cover", [0.62, 0.64, 0.67, 1]),
                              ("band", [0.05, 0.05, 0.05, 1]), ("light", [0.15, 0.55, 0.95, 1]),
                              ("wheels", [0.08, 0.08, 0.08, 1]))],
            ("frame1", "frame", PARTS / "frame.stl", START @ T_IN @ asm["frame1"], frame_c),
            ("frame2", "frame", PARTS / "frame.stl", FINISH @ FLIP @ T_IN @ asm["frame2"], frame_c)]
    for k in PLANKS:
        P = T_IN @ asm[f"plank{k}"]
        objs.append((f"piece A{k}", "piece", PARTS / "interface_piece.stl", START @ P, red))
        objs.append((f"piece B{k}", "piece", PARTS / "interface_piece.stl", FINISH @ FLIP @ P @ rotz(pi), red))
        objs.append((f"plank{k}", "plank", PARTS / "plank_body.stl", rack_start(k), wood))
    objs.append(("Guide small", "guide", JIG / "guide_1_v5.stl", START @ GUIDE_ON_A, [0.95, 0.6, 0.15, 1]))
    objs.append(("Guide big", "guide", JIG / "guide_2_v5.stl", START @ GUIDE_ON_A, guide_c))
    for b in range(2, n_benches + 1):
        objs += [(n + tag_of(b), kind, src, P, c) for n, kind, src, P, c in list(objs)
                 if kind in ("frame", "piece", "plank") and "#" not in n]
    return objs


def main(n_benches=1, version=VERSION, station=STATION, source="bench_cell_v8.py"):
    p = build(n_benches)
    moves = [s for s in p.steps if "move" in s]
    out = TESTS / f"{version}_moves.json"
    out.write_text(json.dumps({"station": station, "cell": version, "program": PROGRAM,
                               "source": f"{source} (tm5_kin IK, no RoboDK)", "steps": p.steps}, indent=1))
    print(f"{out.name}: {len(moves)} moves, {sum(bool(s.get('gripper')) for s in p.steps)} gripper actions")
    for k, name in enumerate(p.stages, 1):
        st = [s for s in moves if s["stage"] == k]
        bad = [b for b in p.bad if b.startswith(name + ":")]
        lp = [s["name"] for s in st if s["name"] in p.lines_to_ptp]
        print(f"{k} {name}: {len(st)} moves, unreachable {len(bad)}{' ' + str([b.split(': ')[1] for b in bad]) if bad else ''}"
              f"{', lines made joint moves: ' + str(lp) if lp else ''}")
    # time at the programmed speeds (joint moves at 50 deg/s on the largest joint, no acceleration)
    t, prev = 0.0, None
    for s in moves:
        if prev is not None:
            if s["move"] == "ptp":
                t += max(abs(a - b) for a, b in zip(s["joints"], prev["joints"])) / 50
            else:
                t += math.dist(s["flange"][:3], prev["flange"][:3]) / s["speed"]
        prev = s
    t += sum(0.5 for s in p.steps if "do0" in s) + sum(s["wait_ms"] / 1000 for s in p.steps if "wait_ms" in s)
    print(f"cycle estimate {t:.0f} s (programmed speeds, no accelerations)")
    return p


if __name__ == "__main__":
    main()
