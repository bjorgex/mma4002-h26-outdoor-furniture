"""The finished Bench V1 cell assembly (RoboDK program "AssembleBench": bench_cell_v4.py, or with --cell v5
bench_cell_v5.py) replayed through the Hand-E bridge (hande_bridge.py, TMflow HandE_Bridge_v1): Python does
every move, TMflow the gripper.

    python tests/v4_replay.py cache          once, RoboDK with 'Bench V1 cell v4' open: read-only, -> v4_moves.json
    python tests/v4_replay.py cache --cell v5          'Bench V1 cell v5' open -> v5_moves.json
    python tests/v4_replay.py derive                   no RoboDK: v5_moves.json from v4_moves.json (see derive())
    python tests/v4_replay.py --list [--cell v5]       the stages and their moves, connect to nothing
Against the mock (no robot, no RoboDK needed), with "python tests/tmflow_mock.py serve" (hande flow) running:
    python tests/tmflow_mock.py run tests/v4_replay.py
    python tests/tmflow_mock.py run tests/v4_replay.py --speed 2      programmed speeds x2 (Manual caps 250 mm/s)
    python tests/tmflow_mock.py run tests/v4_replay.py --cell v5      v5: the guide starts on base A

Stages, as bench_cell_v4.py's / bench_cell_v5.py's docstrings number them (one step function each):
    v4: 1 guide B -> A   2 planks 1-6 into frame 1   3 guide A -> B   4 frame 1 + planks into frame 2
        5 inner half -> pad   6 outer half -> pad   7 bench -> AMR, back home
    v5: v4 without its stage 1 (the guide starts on base A), the others numbered 1-6
The 3D pane's start state must match the cell: scenarios.json's "cell" (cell.glb for v4, cell_v5.glb for v5,
robot_sim/cell_layout.py).
Moves: MoveJ -> PTP("JPP") to the target's joints (the station's wrist/elbow choice exactly), MoveL -> Line("CAP")
to the flange pose of the target's joints (FK), at the program's Set speed. The station's tool (EGP, TCP 160 mm
out) is taken out: poses here are flange in robot base, as the bridge sends them.
Gripper: the station's EGP has DO 0 (1 = close); the bridge has a Hand-E. A DO 0 change that is followed by a
"Simulation: attach" is a grip (b.grip(), var_cmd 1), one followed by a "Simulation: release" is a release
(b.release(), var_cmd 2). Under "tmflow_mock.py run" each GRIP / RELEASE is preceded by a "carry" step event
with those station names (cell.glb node names), so the mock's 3D pane carries exactly what RoboDK attaches - not
the TM protocol, the robot never sees it. The DO changes that only pre-set the fingers (closed before going into the guide's
pocket, closed to push a plank home, open before the bench re-grip) have no Hand-E step and are skipped
(printed). Note the guide is held from inside (the EGP opens to grip it): with a Hand-E that is a different grip.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE))
import hande_bridge as hb                               # noqa: E402  Bridge: grip, release
import listen_pick_place_test as lt                     # noqa: E402  ACC

PROGRAM, ROBOT = "AssembleBench", "Omron TM5-900"
JOINT_SPEED = 50                                        # bench_cell_v4/5.py JOINT [deg/s]; the mock: 180 deg/s = 100 %
# step -> move name prefixes, in program order (stage numbers per cell: their place in its list)
STEPS = {"guide_to_base_a": ("guide B-A",), "planks_into_frame1": ("plank",), "guide_back_to_base_b": ("guide A-B",),
         "frame1_into_frame2": ("sub",), "inner_half_to_pad": ("inner",), "outer_half_to_pad": ("outer",),
         "bench_to_amr": ("bench", "back to middle")}    # "Home" stays in the stage it's in
CELLS = {"v4": ("Bench V1 cell v4", list(STEPS)),
         "v5": ("Bench V1 cell v5", [k for k in STEPS if k != "guide_to_base_a"])}   # v5: guide starts on base A
CELL = MOVES = STATION = None                           # set by use(): --cell
STAGE = []                                              # (stage, move name prefix)


def use(cell):
    """Pick the cell: its station, moves file (<cell>_moves.json) and stage numbers."""
    global CELL, MOVES, STATION, STAGE
    CELL, MOVES, STATION = cell, HERE / f"{cell}_moves.json", CELLS[cell][0]
    STAGE = [(n, pre) for n, step in enumerate(CELLS[cell][1], 1) for pre in STEPS[step]]


def stage_of(step):
    return CELLS[CELL][1].index(step) + 1


use("v4")

b = None                                                # the Bridge session
scale = 1                                               # --speed


def cache():
    """AssembleBench's moves and gripper events from the open station (read-only) -> v4_moves.json."""
    from robodk import robolink, robomath
    RDK = robolink.Robolink()
    st = [s for s in RDK.getOpenStations() if s.Name() == STATION]
    if not st:
        raise SystemExit(f"open '{STATION}.rdk' in RoboDK first")
    RDK.setActiveStation(st[0])
    robot, prog = RDK.Item(ROBOT, robolink.ITEM_TYPE_ROBOT), RDK.Item(PROGRAM, robolink.ITEM_TYPE_PROGRAM)
    ins = [prog.Instruction(i) for i in range(prog.InstructionCount())]
    out, stage, speed = [], 1, 100.0
    for i, (name, kind, movetype, _, _, joints) in enumerate(ins):
        if kind == robolink.INS_TYPE_CHANGESPEED:
            speed = float(re.search(r"\(([\d.]+) mm/s\)", name).group(1))
        elif kind == robolink.INS_TYPE_MOVE:
            label = re.match(r"Move[JL] \((.*)\)", name).group(1)
            stage = next((k for k, pre in STAGE if label.startswith(pre)), stage)
            q = [round(v, 4) for v in joints.list()[:6]]
            f = [round(v, 4) for v in robomath.Pose_2_Techman(robot.SolveFK(q))]
            out.append({"stage": stage, "name": label, "move": "ptp" if movetype == 1 else "line",
                        "joints": q, "flange": f, "speed": speed})
        elif name.startswith("Set IO_0="):
            what, parts = None, []
            for later in ins[i + 1:]:                   # the attach/release events right after it, if any
                if later[1] == robolink.INS_TYPE_MOVE or later[0].startswith("Set IO"):
                    break
                m = re.match(r"Simulation: (attach|release) (.*)", later[0])
                if m:
                    what = what or ("grip" if m.group(1) == "attach" else "release")
                    parts.append(m.group(2))
            out.append({"stage": stage, "name": name, "do0": int(name.endswith("=1")), "gripper": what, "parts": parts})
    MOVES.write_text(json.dumps({"station": STATION, "cell": CELL, "program": PROGRAM, "steps": out}, indent=1))
    print(f"{MOVES.name}: {sum('move' in s for s in out)} moves, {sum(bool(s.get('gripper')) for s in out)} gripper"
          f" actions, {sum('do0' in s and not s['gripper'] for s in out)} finger pre-sets (skipped on the Hand-E)")


def derive():
    """v5_moves.json without RoboDK: bench_cell_v5.py's program is v4's stages 2-7 with the same targets (same
    poses, same IK configurations); only the start differs - Home, then straight to plank 3 - so the IK chain is
    seeded from Home instead of v4's guide place. rc.ik keeps the configuration and takes J6 +-360 when that is
    closer to the move before (limits +-270): the same choice here. Lines go out as flange poses anyway; PTPs use
    these joints. "cache --cell v5" from the station replaces it with the station's own joints."""
    use("v4")
    src = load()
    use("v5")
    out, prev, home = [], None, True
    for st in src:
        if st["stage"] == 1 and not (home and st.get("name") == "Home"):
            continue                                    # v4's stage 1 (guide B -> A) is gone; its Home stays
        st = {**st, "stage": max(1, st["stage"] - 1)}
        if "move" in st:
            home = False
            q = list(st["joints"])
            if prev is not None:
                q[5] = min((q[5] + k for k in (-360, 0, 360) if -270 <= q[5] + k <= 270), key=lambda v: abs(v - prev[5]))
            st["joints"], prev = [round(v, 4) for v in q], q
        out.append(st)
    MOVES.write_text(json.dumps({"station": STATION, "cell": CELL, "program": PROGRAM, "derived_from": "v4_moves.json",
                                 "note": derive.__doc__.split("\n")[0], "steps": out}, indent=1))
    shifted = sum("move" in a and a["joints"][5] != b["joints"][5]
                  for a, b in zip(out, [x for x in src if not (x["stage"] == 1 and x.get("name") != "Home")]))
    print(f"{MOVES.name}: {sum('move' in x for x in out)} moves, {sum(bool(x.get('gripper')) for x in out)} gripper"
          f" actions (from v4_moves.json; J6 shifted by 360 in {shifted} moves)")


def load():
    return json.loads(MOVES.read_text())["steps"]


def cmd(s):
    if s["move"] == "ptp":
        pct = min(100, JOINT_SPEED / 180 * 100 * scale)
        return f'PTP("JPP",{",".join(f"{v:.4f}" for v in s["joints"])},{pct:.0f},{lt.ACC},0,false)'
    v = min(250, s["speed"] * scale)                    # Manual mode caps the tool at 250 mm/s
    return f'Line("CAP",{",".join(f"{x:.3f}" for x in s["flange"])},{v:.0f},{lt.ACC},0,false)'


def carry(action, parts):
    """Tell the mock's 3D pane what the next GRIP takes along / RELEASE puts down: a "carry" event through the same
    /step queue "tmflow_mock.py run" posts this script's step calls with (its profile hook). A no-op otherwise.
    Waits until it is posted: the queue posts in the background, and on a busy PC the names could otherwise reach the
    mock after the GRIP they are for (that grip then carries nothing, in RoboDK and in the 3D pane)."""
    steps = getattr(sys.getprofile(), "__self__", None)
    if hasattr(steps, "send"):
        steps.send("carry", action=action, parts=parts)
        steps.q.join()


def play(stage):
    """One stage: the moves between two gripper actions go out as one queue, then GRIP or RELEASE."""
    batch = []
    for s in [s for s in load() if s["stage"] == stage]:
        if "move" in s:
            batch.append(cmd(s))
            continue
        if batch:
            b.r.move(*batch)
            batch = []
        if s["gripper"] == "grip":
            print(f"    grip: {', '.join(s['parts'][:3])}{' ...' if len(s['parts']) > 3 else ''}  (EGP DO 0 = {s['do0']})")
            carry("grip", s["parts"])
            b.grip()
        elif s["gripper"] == "release":
            print(f"    release: {', '.join(s['parts'])}  (EGP DO 0 = {s['do0']})")
            carry("release", s["parts"])
            b.release()
        else:
            print(f"    skipped: EGP fingers {'closed' if s['do0'] else 'opened'} beforehand (no Hand-E step)")
    if batch:
        b.r.move(*batch)


# ---- the stages, in the order they run (numbers: bench_cell_v4.py's / bench_cell_v5.py's, via stage_of) ----

def guide_to_base_a():
    """guide: base B -> flipped in the air -> base A  (v4 only)"""
    play(stage_of("guide_to_base_a"))


def planks_into_frame1():
    """planks 3, 6, 2, 5, 1, 4: plank jig -> through the guide into frame 1"""
    play(stage_of("planks_into_frame1"))


def guide_back_to_base_b():
    """guide: lifted off over the plank tops -> flipped -> base B"""
    play(stage_of("guide_back_to_base_b"))


def frame1_into_frame2():
    """frame 1 with the planks: flipped, lowered through the guide into frame 2"""
    play(stage_of("frame1_into_frame2"))


def inner_half_to_pad():
    """inner guide half: slid off the planks, lifted, over base A, pushed back onto the pad"""
    play(stage_of("inner_half_to_pad"))


def outer_half_to_pad():
    """outer guide half: slid down the bench, lifted over base B, pushed back onto the pad"""
    play(stage_of("outer_half_to_pad"))


def bench_to_amr():
    """finished bench: re-gripped at frame 1's foot, lifted out of base B onto the AMR plate, back home"""
    play(stage_of("bench_to_amr"))


def steps():
    return [(globals()[name], ()) for name in CELLS[CELL][1]]


def run():
    global b
    seq = steps()
    input(f"{STATION}: {PROGRAM} ({len(load())} steps from {MOVES.name}), HandE_Bridge_v1 in Listen1."
          " Enter to start ")
    b = hb.Bridge()
    for k, (do, args) in enumerate(seq, 1):
        print(f"{k}/{len(seq)} {do.__name__}: {do.__doc__}")
        do(*args)
    b.r.s.close()
    print("done: bench on the AMR plate, arm back in the middle, flow waiting in Listen1")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cache", nargs="?", choices=["cache", "derive"],
                    help=f"cache: read {PROGRAM} from RoboDK into <cell>_moves.json; derive: v5 from v4, no RoboDK")
    ap.add_argument("--cell", choices=list(CELLS), default="v4", help="v4 (default) or v5 (guide starts on base A)")
    ap.add_argument("--speed", type=float, default=1, help="programmed speeds times this (default 1)")
    ap.add_argument("--list", action="store_true", help="print the stages and exit")
    a = ap.parse_args()
    use(a.cell)
    if a.cache == "derive":
        raise SystemExit(derive())
    if a.cache:
        raise SystemExit(cache())
    if json.loads(MOVES.read_text()).get("station", STATION) != STATION:
        raise SystemExit(f"{MOVES.name} is not from '{STATION}': run cache --cell {CELL}")
    if a.list:
        for k, (do, _) in enumerate(steps(), 1):
            st = [s for s in load() if s["stage"] == k]
            print(f"{k} {do.__name__}: {sum('move' in s for s in st)} moves, "
                  f"{sum(bool(s.get('gripper')) for s in st)} gripper actions  - {do.__doc__}")
        raise SystemExit
    scale = a.speed
    run()
