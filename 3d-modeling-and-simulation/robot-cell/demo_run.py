"""Demonstrator run on the real TM5-900: home -> grab plank -> move it to the jig -> place -> release -> home,
for N planks. Moves and gripper go through the Hand-E bridge (tests/hande_bridge.py), nothing new on the wire.

How to run (from robot-cell/, shared venv). TMflow: HandE_Bridge_v1 running in Manual mode, waiting in
Listen1 (Bridge), low project speed, hand on the E-stop.
    python demo_run.py --list                 print the steps, connect to nothing
    python demo_run.py --air --step           dry run: 50 mm higher, no gripping, Enter before each step
    python demo_run.py --step                 the real thing, Enter before each step
    python demo_run.py --planks 3 --speed 40  the first three planks of the order, 40 mm/s (default 30)
    python demo_run.py --points tests/real_cell_points.json teach plank2
                                              store the flange pose here as plank 2's pick (jig2 = its place)
Against the mock (no robot), with "python tests/tmflow_mock.py serve" (default hande flow) running:
    python tests/tmflow_mock.py run demo_run.py --air

Poses (flange, robot base) come from --points, default tests/demo_points_v4_cad.json: the v4 cell's own
targets (station "Bench V1 cell v4": 'plank<i> pick', 'plank<i> place', 'Home'), each slot with its own
orientation (jig 4-6 are turned 80 deg against jig 1-3). Planks go in the cell's order 3, 6, 2, 5, 1, 4 (far
column first, front row first: never over a standing plank). On the real cell, teach into a file of its own
(--points ... teach plank<i> / jig<i>) instead of changing the CAD file. In a points file:
    plank<i>, jig<i>   pick and place of plank i
    pick, place        the spots listen_pick_place_test.py taught; plank 1 and jig 1 when those are missing
A plank with no pose in the file gets plank 1's / jig 1's moved by the v4 cell layout (plank rack pitch from
bench_cell_v4.py, slot positions from benchV1_parts/assembly.json, turned into robot base with
bench_layout.json's work frame), and runs in the air only: AIR above it, no gripping.
--air is 50 mm (not 100): with the lift on top, 100 mm puts jig 3-6 (~720 mm out) out of the arm's reach.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE / "tests"))
import hande_bridge as hb                               # noqa: E402  Bridge: move, lift, grip, release, home
import listen_pick_place_test as lt                     # noqa: E402  line(), read_state(), POINTS, SPEED, LIFT

AIR = 50                                                # --air and untaught spots: this much higher [mm]
ORDER = (3, 6, 2, 5, 1, 4)                              # bench_cell_v4.py PLANK_ORDER
CAD_POINTS = HERE / "tests" / "demo_points_v4_cad.json"  # the v4 station's targets (default --points)
SPEED = 30                                              # default straight-line speed [mm/s] (the bridge's: 50)
RACK_PITCH = 30                                         # bench_cell_v4.py PITCH: 3 planks per row, 2 rows
PLANK_GRIP = (0, 110, 2.5)                              # bench_cell_v4.py PLANK_GRIP: grip point in the plank

b = None                                                # the Bridge session
air = False                                             # --air: nothing is gripped
spots = {}                                              # plank i -> (pick, place, taught)
holding = False                                         # a plank is between the fingers


def mat_vec(m, v):
    return [sum(m[r][c] * v[c] for c in range(3)) for r in range(3)]


def cell_offsets(i):
    """TODO poses: where plank i and its jig slot are relative to plank 1's, in robot base [mm]."""
    work = json.loads((HERE / "bench_layout.json").read_text())["work_frame"]   # ground base axes = work frame's
    row, col = divmod(i - 1, 3)                                                  # bench_cell_v4.py rack layout
    parts = {p["name"]: p["pose"] for p in json.loads((HERE / "benchV1_parts" / "assembly.json").read_text())["parts"]}

    def grip(k):                                        # grip point on base A; T_IN = rotx(90): (x, y, z) -> (x, -z, y)
        p = parts[f"plank{k}"]
        x, y, z = (v + p[r][3] for r, v in enumerate(mat_vec(p, PLANK_GRIP)))
        return [x, -z, y]
    slot = [a - a1 for a, a1 in zip(grip(i), grip(1))]
    return mat_vec(work, [RACK_PITCH * col, RACK_PITCH * row, 0]), mat_vec(work, slot)


def load_spots():
    flange = {k: v["flange"] for k, v in json.loads(lt.POINTS.read_text()).items()}
    for i in range(1, 7):                               # all six: an untaught plank is placed from plank 1's spot
        pick = flange.get(f"plank{i}", flange.get("pick") if i == 1 else None)
        place = flange.get(f"jig{i}", flange.get("place") if i == 1 else None)
        if pick and place:
            spots[i] = (pick, place, True)
            continue
        d_pick, d_place = cell_offsets(i)
        p1, j1 = spots[1][0], spots[1][1]
        pick = pick or [a + d for a, d in zip(p1, d_pick)] + p1[3:]
        place = place or [a + d for a, d in zip(j1, d_place)] + j1[3:]
        spots[i] = (pick, place, False)


def above(i):
    """Extra height over plank i's spots: AIR when nothing is gripped (--air, or no taught pose)."""
    return AIR if air or not spots[i][2] else 0


def raised(pose, dz):
    return pose[:2] + [pose[2] + dz] + pose[3:]


# ---- the steps, in the order they run ----

def home():
    """Lift out of the parts if down there, then TMflow's Home2 (var_cmd = 3)."""
    work_z = max(p[2] + above(i) for i, s in spots.items() for p in s[:2])
    if lt.read_state()["flange"][2] < work_z + 10:
        b.lift()
    b.home()


def open_gripper():
    if air:
        return print("    skipped (--air)")
    b.release()


def grab_plank(i):
    """Up, across, straight down onto the plank, grip."""
    global holding
    b.move(raised(spots[i][0], above(i)))
    if above(i):
        return print(f"    no grip ({'--air' if air else 'TODO: plank %d not taught' % i})")
    b.grip()                                            # GripLost if the fingers close on nothing
    holding = True


def move_to_jig(i):
    """Straight up, across to above the jig slot."""
    b.lift()
    b.r.move(lt.line(spots[i][1], above(i) + lt.LIFT))


def place_in_jig(i):
    """Straight down into the slot."""
    b.r.move(lt.line(spots[i][1], above(i)))


def release():
    global holding
    if not holding:
        return print("    no release (nothing gripped)")
    b.release()
    holding = False


def steps(n):
    seq = [(home, ()), (open_gripper, ())]
    for i in ORDER[:n]:
        seq += [(grab_plank, (i,)), (move_to_jig, (i,)), (place_in_jig, (i,)), (release, ()), (home, ())]
    return seq


def label(do, args):
    return f"{do.__name__}({', '.join(map(str, args))})"


def run(n, step):
    global b
    load_spots()
    print(f"points: {lt.POINTS.name}")
    for i in ORDER[:n]:
        pick, place, taught = spots[i]
        h = above(i)
        print(f"plank {i}: pick ({pick[0]:.0f}, {pick[1]:.0f}) z {pick[2] + h:.0f}   "
              f"jig ({place[0]:.0f}, {place[1]:.0f}) z {place[2] + h:.0f}"
              + ("" if taught else f"   TODO not taught: cell-layout spot, air only"))
    print(f"speed {lt.SPEED} mm/s" + (f", --air: +{AIR} mm, no gripping" if air else ""))
    input("Manual mode, low project speed, hand on the E-stop, HandE_Bridge_v1 in Listen1. Enter to start ")
    b = hb.Bridge()
    seq = steps(n)
    try:
        for k, (do, args) in enumerate(seq, 1):
            if step:
                input(f"{k}/{len(seq)} Enter: {label(do, args)} ")
            else:
                print(f"{k}/{len(seq)} {label(do, args)}")
            do(*args)
    except hb.GripLost:
        print("GRIP found no plank: opening, lifting and going Home")
        b.release()
        b.finish()
        raise SystemExit("stopped (--air runs without planks)")
    b.r.s.close()
    print("done: arm at Home, flow waiting in Listen1, run again any time")


def teach(name):
    if not re.fullmatch(r"(plank|jig)[1-6]", name):
        raise SystemExit("teach plank<i> | jig<i>, i = 1-6")
    pts = json.loads(lt.POINTS.read_text())
    pts[name] = lt.read_state()
    lt.POINTS.write_text(json.dumps(pts, indent=2))
    print(f"{name}: flange {pts[name]['flange']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("teach", nargs="*", metavar="teach NAME", help="store the flange pose here as plank<i> or jig<i>")
    ap.add_argument("--planks", type=int, default=1, help=f"number of planks, 1-6, in the order {ORDER} (default 1)")
    ap.add_argument("--points", help=f"points file (default {CAD_POINTS.relative_to(HERE)})")
    ap.add_argument("--air", action="store_true", help=f"everything {AIR} mm higher, no gripping")
    ap.add_argument("--step", action="store_true", help="wait for Enter before each step")
    ap.add_argument("--speed", type=int, default=SPEED, help=f"straight-line speed [mm/s], default {SPEED}")
    ap.add_argument("--list", action="store_true", help="print the steps and exit")
    a = ap.parse_args()
    if a.points:
        lt.POINTS = Path(a.points).resolve()
    elif lt.POINTS.name == "listen_test_points.json":   # not set by tmflow_mock.py run --points
        lt.POINTS = CAD_POINTS
    if a.teach:
        if len(a.teach) != 2 or a.teach[0] != "teach":
            raise SystemExit("teach plank<i> | jig<i>")
        raise SystemExit(teach(a.teach[1]))
    if not 1 <= a.planks <= 6:
        raise SystemExit("--planks 1-6 (the bench has six)")
    if a.list:
        for k, (do, args) in enumerate(steps(a.planks), 1):
            print(f"{k} {label(do, args)}")
        raise SystemExit
    air = a.air
    lt.SPEED = min(a.speed, 250)                        # Manual mode caps the tool at 250 mm/s anyway
    run(a.planks, a.step)
