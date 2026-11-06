"""Bench V1 cell, version 8 (v8): v7's program (bench_cell_v7.py) on the Jig V5 hardware (jig_v5.py), built
WITHOUT RoboDK for the group's own simulator (tests/tmflow_mock.py --sim, tests/robot_sim/tm5_kin.py).

    python robot_cell/bench_cell_v8.py          program -> tests/v8_moves.json (+ a reach/line report)
    python robot_cell/tests/robot_sim/cell_layout.py --cell v8      the 3D cell -> cell_v8.glb, cell_layout_v8.json
    then in the mock page: scenario "v8-full" (or "v8-full-fast")

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
       start base; 6  big half: lifted, turned 45 deg, slid out, up, onto the start base
    7  finished bench: re-gripped at frame 1's foot from above, lifted out of the finish base, onto the AMR; home
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
GAP = {"plank": (5, 12), "arm": (17, 22), "foot": (7.5, 16)}    # (closed on the part, open), mm
ARM_Y = 63          # ASSUMPTION: guide grips 25-27 mm in from the arm tips (at y 78-80 the body hit the plank rack)
# Guide halves gripped only on their arms (base-local, across the arm, fingers along local x), at y 63 where both
# arms are 17 mm wide (small x 42.5..59.5, big 66.7..83.7) with the 7 mm back-plank slot between them: on the side
# without back planks that slot is empty and takes the inner finger (24 mm open). (Measured in the z 50 section.)
# Side: the arm away from the back planks (start base: -x, finish base: +x, the bench being turned over).
ARM_X = {"small": 51.0, "big": 75.2}
GUIDE_LIFT, GUIDE_OUT = 25, 130   # off the base's bosses (z 40), then out along base-local +y past frame 1
# Grip orientation: tool down, spun 180 deg about the tool axis (fingers symmetric): upright and unspun the wrist
# (link 6) hit seat plank 2 when picking the halves off the start base (collision search). ASSUMPTION
SPIN = pi


def grips(side=-1, tilt=None):
    """Guide grips in base-local coordinates on the arm on base-local x = side * ARM_X: -1 on the start base (away
    from its back planks), +1 on the finish base after the flip (its back planks are on -x)."""
    tilt = GRIP_TILT if tilt is None else tilt
    return {who: transl(side * ARM_X[who], ARM_Y, ARM_Z) @ DOWN @ rotz(SPIN) @ roty(side * deg(tilt[who]))
            for who in ("small", "big")}


# The big half's arm faces the other base where it is set down: upright, the Hand-E body (+-45 mm) hit the planks
# standing on the other base (collision.py). Tilted 15 deg about the arm, the body leans in over its own guide.
GRIP_TILT = {"small": 0, "big": -15}         # start -> finish (stage 3)
GRIP_TILT_BACK = {"small": 0, "big": 0}      # finish -> start (stage 6): tilted, the arm hit frame 1 at the pick


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
AMR_SHIFT, BENCH_LIFT = ((0, -400, -19) if FINISH_BASE == "B" else (0, -270, -19)), 100   # finish base -> AMR plate (frame 2 0.5 mm above it)

PICK_Z = 420       # over the rack, empty: gripper body (TCP + 37) over the plank tops (253)
TRAVEL_Z = 520     # planks carried with their lower end (235 mm under the TCP) over standing planks (top 260)
LIFT_Z = 450       # guide halves / frame 1 carried at this height
FLIP_Z = 340       # foot grip on base B at z 380+ is out of reach (far corner); flipped planks still clear the guide
SUB_LIFT = 40
BACK_Z = 330       # up from the AMR (450 there: elbow nearly stretched, mu1 5)
SUB_AWAY = 30      # after the release: fingers slid off the foot's end (plate -x), then straight up
APPROACH, FAST, SLOW = 40, 100, 20

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


def solve(flange, near):
    """IK nearest `near`, shoulder facing the cell (|J1| < J1_MAX, robot_cell.ik's rule) and elbow up (J3 < 0, as
    Home: elbow-down solutions put links 2/3 into the table and the bases this close to the robot); falls back to
    any |J1| < J1_MAX solution."""
    cands = []
    for seed in (near, HOME_SEED, [near[0], 20, -90, -20, -90, near[5]], [near[0], 0, -120, 30, -90, near[5]],
                 [near[0], 40, -140, 10, -90, near[5]], [near[0], 20, -90, -20, 90, near[5]],
                 [0, 0, 90, 0, 90, 0], [0, 30, -120, 0, -90, 0], [-40, 10, -100, 0, -90, 0], [40, 10, -100, 0, -90, 0]):
        q = kin.ik(flange, seed, seeds=False)
        if q is not None and abs(q[0]) <= J1_MAX:
            q = kin._wrap_near(q, near)
            if kin.within_limits(q):
                cands.append(q)
    if not cands:
        return None
    up = [q for q in cands if q[2] < 0] or cands
    return min(up, key=lambda q: sum(w * (a - b) ** 2 for w, a, b in zip((3, 3, 2, 1, 1, 0.5), q, near)))


class Program:
    def __init__(self):
        self.q = list(HOME_SEED)
        self.T = None
        self.steps, self.stage, self.speed = [], 1, FAST
        self.bad, self.lines_to_ptp = [], []
        self.gap = GAP["plank"][1]                           # Hand-E finger gap (mm) in force

    def move(self, name, T, kind="line"):
        T_plan, T = T, teach_overrides.apply(name, T, VERSION)   # grip points taught on the robot (tests/robot_sim/teach.py)
        flange = tcp_to_flange_tm(T)
        q = solve(flange, self.q)
        if q is None:
            self.bad.append(f"{STAGES[self.stage - 1]}: {name}")
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


def build():
    GRIP_ = grips()
    p = Program()
    home = transl(MID[0], MID[1], LIFT_Z) @ DOWN
    p.ptp("Home", home)
    final = {k: START @ T_IN @ asm[f"plank{k}"] for k in PLANKS}
    sub_parts = ["frame1"] + [f"plank{k}" for k in PLANKS] + [f"piece A{k}" for k in PLANKS]

    # 1  planks
    for k in PLANK_ORDER:
        pick, place, push = rack_start(k) @ PLANK_GRIP, final[k] @ PLANK_GRIP, final[k] @ PLANK_PUSH
        p.set_speed(FAST)
        p.ptp(f"plank{k} pick travel", at_z(pick, PICK_Z))   # empty gripper: lower (z 520 that close to J1: mu1 3.1)
        p.line(f"plank{k} pick approach", at_z(pick, pick[2, 3] + APPROACH))
        p.set_speed(SLOW)
        p.line(f"plank{k} pick", pick)
        p.gripper(True, "grip", [f"plank{k}"], gap=GAP["plank"][0])
        p.line(f"plank{k} pick out", at_z(pick, pick[2, 3] + 60))
        p.set_speed(FAST)
        p.line(f"plank{k} pick up", at_z(pick, TRAVEL_Z))
        p.ptp(f"plank{k} place travel", at_z(place, TRAVEL_Z))
        p.line(f"plank{k} above guide", at_z(place, place[2, 3] + 75))
        p.set_speed(SLOW)
        p.line(f"plank{k} place", place)
        p.gripper(False, "release", [f"plank{k}"], gap=GAP["plank"][1])
        p.line(f"plank{k} push approach", at_z(push, push[2, 3] + 20))
        p.gripper(True, gap=0)                               # closed fingers push the plank home
        p.line(f"plank{k} push", push)
        p.line(f"plank{k} push out", at_z(push, push[2, 3] + 20))
        p.gripper(False, gap=GAP["plank"][1])
        p.set_speed(FAST)
        p.line(f"plank{k} place up", at_z(place, TRAVEL_Z))

    def pick_from_above(label, grip, parts, high=LIFT_Z, gap=GAP["arm"]):
        p.gripper(False, gap=gap[1])                         # Hand-E opened to the part + 7 mm
        p.set_speed(FAST)
        p.ptp(f"{label} over pick", at_z(grip, high))
        p.line(f"{label} pick approach", grip @ transl(0, 0, -APPROACH))
        p.set_speed(SLOW)
        p.line(f"{label} pick", grip)
        p.gripper(True, "grip", parts, gap=gap[0])

    def put_down(label, place, parts, back=APPROACH, gap=GAP["arm"]):
        p.set_speed(FAST)
        p.ptp(f"{label} over place", at_z(place, LIFT_Z))
        p.line(f"{label} place approach", at_z(place, place[2, 3] + APPROACH))
        p.set_speed(SLOW)
        p.line(f"{label} place", place)
        p.gripper(False, "release", parts, gap=gap[1])
        p.line(f"{label} place out", at_z(place, place[2, 3] + back))      # straight up (the grip may be tilted)
        p.set_speed(FAST)
        p.line(f"{label} place out up", at_z(place, LIFT_Z))

    # 2  guide halves A -> B, small first (straight up along the planks), then the big one (lifted clear, turned 45)
    p.stage = 2
    g = START @ GUIDE_ON_A @ GRIP_["small"]
    pick_from_above("guide small", g, ["Guide small"])
    p.line("guide small lift off", at_z(g, g[2, 3] + PLANK_TOP))
    p.set_speed(FAST)
    p.line("guide small up", at_z(g, LIFT_Z))
    put_down("guide small", FINISH @ GUIDE_ON_B @ GRIP_["small"], ["Guide small"])
    p.stage = 3
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
    p.stage = 4
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
    GF = grips(+1, GRIP_TILT_BACK)
    out_dir = FINISH[:3, :3] @ np.array([0, 1.0, 0])         # base-local +y in plate coordinates
    for stage, who in ((5, "small"), (6, "big")):
        p.stage = stage
        label = f"{who} half"
        g = FINISH @ GUIDE_ON_B @ GF[who]
        pick_from_above(label, g, [f"Guide {who}"])
        up = transl(0, 0, GUIDE_LIFT) @ g
        p.line(f"{label} lift off bosses", up)
        if who == "big":
            t = up.copy()
            t[:3, :3] = rotz(BIG_TURN)[:3, :3] @ up[:3, :3]
            p.line(f"{label} turn 45", t)
            up = t
        slid = transl(*(out_dir * GUIDE_OUT)) @ up
        p.line(f"{label} slide out", slid)
        p.set_speed(FAST)
        p.line(f"{label} up", at_z(slid, LIFT_Z))
        put_down(label, START @ GUIDE_ON_A @ GF[who], [f"Guide {who}"])

    # 7  finished bench: re-gripped at frame 1's foot from above, lifted out of the finish base -> AMR
    p.stage = 7
    grip = FINISH @ FLIP @ HAND_GRIP
    bench_parts = ["frame1", "frame2"] + [f"plank{k}" for k in PLANKS] + [f"piece A{k}" for k in PLANKS] + \
        [f"piece B{k}" for k in PLANKS]
    p.set_speed(FAST)
    p.gripper(False, gap=GAP["foot"][1])
    p.ptp("bench over pick", at_z(grip, grip[2, 3] + 60))
    p.set_speed(SLOW)
    p.line("bench pick", grip)
    p.gripper(True, "grip", bench_parts, gap=GAP["foot"][0])
    p.line("bench lift", transl(0, 0, BENCH_LIFT) @ grip)
    dx, dy, dz = AMR_SHIFT
    p.set_speed(FAST)
    p.line("bench over AMR", transl(dx, dy, BENCH_LIFT) @ grip)
    p.set_speed(SLOW)
    p.line("bench down", transl(dx, dy, dz) @ grip)
    p.gripper(False, "release", bench_parts, gap=GAP["foot"][1])
    p.line("bench place out", transl(dx, dy, dz) @ grip @ transl(0, 0, -40))
    p.set_speed(FAST)
    p.line("back up", at_z(transl(dx, dy, dz) @ grip @ transl(0, 0, -40), BACK_Z))
    p.ptp("Home", home)
    return p


def cell_objects():
    """(name, kind, mesh file or box (lo, hi), pose in the plate frame, colour) of every object at the start."""
    grey, wood, frame_c, red = [0.7, 0.72, 0.75, 1], [0.75, 0.55, 0.3, 1], [0.55, 0.62, 0.75, 1], [0.85, 0.1, 0.1, 1]
    jig_c, guide_c = [0.35, 0.55, 0.85, 1], [0.95, 0.75, 0.2, 1]
    ps, th = JL["plate"]["size"][0], JL["plate"]["size"][2]
    objs = [("Table", "table", ((-350, -40, -TABLE_H), (ps + 10, ps + 40, -th)), np.eye(4), [0.78, 0.74, 0.68, 1]),
            ("T-slot plate", "plate", JIG / JL["plate"]["stl"], np.eye(4), grey),
            ("Base A", "jig", JIG / JL["base_A"]["stl"], BASE_A, jig_c),
            ("Base B", "jig", JIG / JL["base_B"]["stl"], BASE_B, jig_c),
            ("Plank rack", "jig", JIG / JL["plank_rack"]["stl"], RACK, [0.45, 0.47, 0.5, 1]),
            ("AMR plate", "amr", ((0, 0, -10), (AMR_PLATE[0], AMR_PLATE[1], 0)), AMR_AT, [0.4, 0.75, 0.45, 1]),
            ("AMR top module", "amr", ((40, 40, 383 - TABLE_H - th), (AMR_PLATE[0] - 40, AMR_PLATE[1] - 40, -10)), AMR_AT,
             [0.85, 0.85, 0.88, 1]),
            ("frame1", "frame", PARTS / "frame.stl", START @ T_IN @ asm["frame1"], frame_c),
            ("frame2", "frame", PARTS / "frame.stl", FINISH @ FLIP @ T_IN @ asm["frame2"], frame_c)]
    for k in PLANKS:
        P = T_IN @ asm[f"plank{k}"]
        objs.append((f"piece A{k}", "piece", PARTS / "interface_piece.stl", START @ P, red))
        objs.append((f"piece B{k}", "piece", PARTS / "interface_piece.stl", FINISH @ FLIP @ P @ rotz(pi), red))
        objs.append((f"plank{k}", "plank", PARTS / "plank_body.stl", rack_start(k), wood))
    objs.append(("Guide small", "guide", JIG / "guide_1_v5.stl", START @ GUIDE_ON_A, [0.95, 0.6, 0.15, 1]))
    objs.append(("Guide big", "guide", JIG / "guide_2_v5.stl", START @ GUIDE_ON_A, guide_c))
    return objs


def main():
    p = build()
    moves = [s for s in p.steps if "move" in s]
    out = TESTS / "v8_moves.json"
    out.write_text(json.dumps({"station": STATION, "cell": VERSION, "program": PROGRAM,
                               "source": "bench_cell_v8.py (tm5_kin IK, no RoboDK)", "steps": p.steps}, indent=1))
    print(f"{out.name}: {len(moves)} moves, {sum(bool(s.get('gripper')) for s in p.steps)} gripper actions")
    for k, name in enumerate(STAGES, 1):
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
    t += sum(0.5 for s in p.steps if "do0" in s)
    print(f"cycle estimate {t:.0f} s (programmed speeds, no accelerations)")
    return p


if __name__ == "__main__":
    main()
