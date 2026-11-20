"""Score one robot program in one cell model: one row of the assembly experiment's metrics (README.md).

    python score_run.py --version v9                 one known version (VERSIONS below)
    python score_run.py --all --jobs 10              every known version, in parallel
    python score_run.py <program> <cell> --label my-try [--geometry techman] [--shift "Base A:dx,dy,dz,rz"]
    options: --step 2 (path sampling, mm / deg), --out results/versions.csv, --no-csv (print only)

No RoboDK: the own tools in ../robot-cell/tests/robot_sim (collision.py, cycle_time.py, kin_check.py,
manipulability.py, tm5_kin.py). A program is a TMflow zip, a program json or a moves json; a cell is a cell .glb (+ its
cell_layout json), or "v6" / "v7" (collision.py builds those from bench_cell_v6/7.py's constants).
Out: one row per run appended to results/versions.csv, and results/runs/<label>.json with the details (every hit,
the clearance per move, the manipulability per target).

Metric definitions (what each column really measures):
    cycle_s / cycle_ramps_s   cycle_time.estimate: programmed speeds, + trapezoid ramps (no blending)
    phases_s                  the same split by phase (json, programmed s)
    tcp_path_m                TCP (flange + tcp pose) path over every move, PTP included, from the sampled joint path
    line_path_m               only the Line moves (cycle_time.estimate's path length)
    j1..j6_travel_deg         sum of |dq| along the sampled path per joint; joint_travel_deg = their sum
    wrist_flips               J5 sign changes (kin_check: in PTP + along Lines)
    collisions_fixtures/parts moves with a hit (collision.check_program, parts on)
    min_clearance_mm          smallest forearm/wrist/gripper - fixture distance on collision-free samples (every 5th)
    ptp_near_parts            PTP moves that start or end within NEAR_MM of a grip / release TCP point
    low_traverses             moves with > TRAVERSE_MM horizontal TCP travel whose highest TCP point stays below
                              (tallest object in the cell at the start + LOW_MARGIN)
    ik_failures               move targets our IK (seeded with the joints before) can't reach at all
    line_failures             Lines not followable + Lines ending in another posture (kin_check)
    limit_hits                joint limit at a target or along a line (kin_check)
    max_mu1_vfix / min_mu3_vfix / near_singular   manipulability at each move's end joints (MR 5.4; vfix =
                              orientation held), near_singular = targets with mu1_vfix > manipulability.MU1_THR
    grips                     gripper "grip" events; regrasps = grips of a part that was gripped before
    part_flips                grip -> release with the held part turned > 90 deg
    jig_parts / jig_volume_l  fixture objects that are jigs (not table, plates, AMR, markers) + the guides (the robot
                              moves them, but they are jig parts); volume from the meshes (convex hull if not closed)
"""
import argparse
import csv
import datetime
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
CELL = HERE.parent / "robot-cell"
SIM = CELL / "tests" / "robot_sim"
OUT_CSV = HERE / "results" / "versions.csv"
RUNS = HERE / "results" / "runs"

NEAR_MM = 100.0          # ptp_near_parts: TCP this close to a grip / release point
TRAVERSE_MM = 100.0      # low_traverses: horizontal TCP travel of the move
LOW_MARGIN = 50.0        # low_traverses: margin over the tallest object at the start

# version: (program, cell, geometry, note). Paths relative to robot-cell/. Geometry = the link lengths the program's
# joints were made with: v3-v7 RoboDK's station ("robodk"), v8+ our tm5_kin IK ("techman").
VERSIONS = {
    "v3": ("tests/robot_sim/ref/v3_program.json", "tests/robot_sim/cell_v3.glb", "robodk",
           "one double-sided guide B->A->B; RoboDK's TMflow export as program json; cell from bench_cell_v3 constants"),
    "v4": ("tests/v4_moves.json", "tests/robot_sim/cell.glb", "robodk", "guide cut in two halves, parking pad, AMR hand-over"),
    "v5": ("tests/v5_moves.json", "tests/robot_sim/cell_v5.glb", "robodk", "v4 starting with the guide on base A"),
    "v6": ("tests/robot_sim/ref/v6_program.json", "v6", "robodk", "v5 without the parking pad"),
    "v7": ("tests/robot_sim/ref/v7_program.json", "v7", "robodk", "Jig V2 on the work plate, rack outside, guide arms"),
    "v8": ("tests/v8_moves.json", "tests/robot_sim/cell_v8.glb", "techman", "Jig V3/V5 on T-slot profiles"),
    "v8x2": ("tests/v8x2_moves.json", "tests/robot_sim/cell_v8x2.glb", "techman", "v8, two benches"),
    "v9": ("tests/v9_moves.json", "tests/robot_sim/cell_v9.glb", "techman", "guide split V6"),
    "v9x2": ("tests/v9x2_moves.json", "tests/robot_sim/cell_v9x2.glb", "techman", "v9, two benches"),
    "v10": ("tests/v10_moves.json", "tests/robot_sim/cell_v9.glb", "techman",
            "v9's program moved to one camera-found jig layout (v10_moves.json jig_moves); cell = v9 shifted the same"),
}
# v10: which cell objects ride on which carrier in the v9 cell (bench_cell_v10.CARRIERS; frame 1 + its pieces and the
# guides sit in Base B, frame 2 + its pieces in Base A; checked against vision_lab collision_for_run's shifts)
CARRIED = {"Base A": ("frame2", "piece B"), "Base B": ("frame1", "piece A", "Guide small", "Guide big"),
           "Plank rack": ("plank",)}
NOT_JIG = ("table", "plate", "amr", "vision", "marker")

COLUMNS = ["label", "version", "scored_at", "program", "cell", "geometry", "note",
           "cycle_s", "cycle_ramps_s", "phases_s",
           "tcp_path_m", "line_path_m", "joint_travel_deg", "j1_travel_deg", "j2_travel_deg", "j3_travel_deg",
           "j4_travel_deg", "j5_travel_deg", "j6_travel_deg", "n_moves", "n_ptp", "n_line", "wrist_flips",
           "collisions_fixtures", "collisions_parts", "min_clearance_mm", "ptp_near_parts", "low_traverses",
           "ik_failures", "line_failures", "limit_hits", "max_mu1_vfix", "min_mu3_vfix", "near_singular",
           "grips", "regrasps", "part_flips", "jig_parts", "jig_volume_l",
           "iteration", "wall_time_s", "kept", "tool_changes", "score_seconds"]


def _tools(geometry):
    sys.path.insert(0, str(SIM))
    import tm5_kin as K
    K.use(geometry)
    import collision
    import cycle_time
    import kin_check
    import manipulability
    from tmflow_export import load_program
    return K, collision, cycle_time, kin_check, manipulability, load_program


def v10_shift(program):
    """{cell object: (dx, dy, dz, rz)} for v10: each carrier's jig_moves applied to it and to what rides on it."""
    out = {}
    for jig, m in program.get("jig_moves", {}).items():
        if abs(m["x"]) + abs(m["y"]) + abs(m["rz_deg"]) < 1e-6:
            continue
        d = (m["x"], m["y"], 0.0, m["rz_deg"])
        out[jig] = d
        out.update({f"__prefix__{p}": d for p in CARRIED.get(jig, ())})
    return out


def expand_shift(shift, cell):
    out = {}
    for k, d in shift.items():
        if k.startswith("__prefix__"):
            p = k[len("__prefix__"):]
            out.update({n: d for n in cell if n.startswith(p)})
        else:
            out[k] = d
    return out


def score(program_path, cell_arg, geometry="techman", label=None, version="", note="", step=2.0, shift=None):
    t0 = time.time()
    K, collision, cycle_time, kin_check, manip, load_program = _tools(geometry)
    prog_path = Path(program_path)
    if not prog_path.is_absolute():
        prog_path = CELL / prog_path
    cell_s = str(cell_arg)
    if cell_s.endswith((".glb", ".json")) and not Path(cell_s).is_absolute():
        cell_s = str(CELL / cell_s)
    program = load_program(prog_path)
    cell = dict(collision.load_cell(cell_s))
    shift = expand_shift(shift if shift is not None else (v10_shift(program) if version == "v10" else {}), cell)
    T_tcp = np.array(K.pose_to_mat(program.get("tcp", {}).get("pose", [0, 0, 160, 0, 0, 0])))
    steps = program["steps"]
    moves = [s for s in steps if "move" in s]
    row = {c: "" for c in COLUMNS}
    row.update(label=label or version or prog_path.stem, version=version, note=note, geometry=geometry,
               scored_at=datetime.datetime.now().isoformat(timespec="seconds"),
               program=str(prog_path.relative_to(CELL.parent)) if CELL.parent in prog_path.parents else str(prog_path),
               cell=Path(cell_s).name + (f" + shift {sorted(shift)}" if shift else ""))

    # time
    phases, line_m = cycle_time.estimate(program)
    row["cycle_s"] = round(sum(a for a, _ in phases.values()), 1)
    row["cycle_ramps_s"] = round(sum(b for _, b in phases.values()), 1)
    row["phases_s"] = json.dumps({k: round(a, 1) for k, (a, _) in phases.items()})
    row["line_path_m"] = round(line_m, 2)

    # motion along the sampled path
    per, events = collision.program_samples(program, step)
    travel, tcp_pts, tcp_m = np.zeros(6), [], 0.0
    prev_q = None
    for path in per:
        pts = []
        for q in path:
            if prev_q is not None:
                travel += np.abs(np.subtract(q, prev_q))
            prev_q = q
            pts.append((np.array(K.fk_mat(q)) @ T_tcp)[:3, 3])
        tcp_pts.append(np.array(pts))
    allp = np.vstack(tcp_pts)
    tcp_m = float(np.linalg.norm(np.diff(allp, axis=0), axis=1).sum()) / 1000
    row["tcp_path_m"] = round(tcp_m, 2)
    for j in range(6):
        row[f"j{j + 1}_travel_deg"] = round(float(travel[j]), 0)
    row["joint_travel_deg"] = round(float(travel.sum()), 0)
    row["n_moves"] = len(moves)
    row["n_ptp"] = sum(s["move"] == "ptp" for s in moves)
    row["n_line"] = sum(s["move"] == "line" for s in moves)

    # kinematics
    stats, problems, actual = kin_check.check(program, report=lambda *_: None)
    row["wrist_flips"] = stats["j5_flip_ptp"] + stats["j5_flip_line"]
    row["line_failures"] = stats["line_fail"] + stats["line_posture"]
    row["limit_hits"] = stats["limit"] + stats["limit_path"]
    ik_fail = 0
    for a, s in zip(actual, moves[1:]):
        if K.ik(s["flange"], a) is None:
            ik_fail += 1
    row["ik_failures"] = ik_fail

    # manipulability at the targets (the joints the arm really has after each move)
    mu1, mu3 = [], []
    for q in actual:
        r = manip.analyse(q)
        mu1.append(r["vfix"][0])
        mu3.append(r["vfix"][2])
    row["max_mu1_vfix"] = round(float(np.max(mu1)), 2)
    row["min_mu3_vfix"] = round(float(np.min(mu3)), 4)
    row["near_singular"] = int(sum(m > manip.MU1_THR for m in mu1))

    # gripper events: grips, regrasps, flips, near-part points
    grip_pts, seen, regrasp, flips, grips = [], set(), 0, 0, 0
    R_grip, mi = None, -1
    for s in steps:
        if "move" in s:
            mi += 1
            continue
        g = s.get("gripper")
        if g not in ("grip", "release") or mi < 0:
            continue
        p = tcp_pts[mi][-1]
        grip_pts.append(p)
        R = np.array(K.fk_mat(per[mi][-1]))[:3, :3]
        if g == "grip":
            grips += 1
            if set(s.get("parts", [])) & seen:
                regrasp += 1
            seen |= set(s.get("parts", []))
            R_grip = R
        elif R_grip is not None:
            ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R @ R_grip.T) - 1) / 2))))
            flips += ang > 90
            R_grip = None
    row["grips"], row["regrasps"], row["part_flips"] = grips, regrasp, flips
    gp = np.array(grip_pts) if grip_pts else np.zeros((0, 3))
    near = 0
    for k, s in enumerate(moves):
        if s["move"] != "ptp" or k == 0 or not len(gp):
            continue
        ends = (tcp_pts[k - 1][-1], tcp_pts[k][-1])
        near += any(np.min(np.linalg.norm(gp - e, axis=1)) < NEAR_MM for e in ends)
    row["ptp_near_parts"] = near

    # low traverses: against the tallest object at the start (shifted cell)
    shifted = dict(cell)
    for n, d in shift.items():
        kind, mesh = cell[n]
        mesh = mesh.copy()
        c, s_ = math.cos(math.radians(d[3])), math.sin(math.radians(d[3]))
        mesh.apply_transform([[c, -s_, 0, d[0]], [s_, c, 0, d[1]], [0, 0, 1, d[2]], [0, 0, 0, 1]])
        shifted[n] = (kind, mesh)
    top = max(m.bounds[1][2] for n, (k, m) in shifted.items() if not n.lower().startswith(("amr",)))
    low = 0
    for k in range(1, len(tcp_pts)):
        pts = np.vstack([tcp_pts[k - 1][-1:], tcp_pts[k]])
        if np.linalg.norm(pts[-1, :2] - pts[0, :2]) > TRAVERSE_MM and pts[:, 2].max() < top + LOW_MARGIN:
            low += 1
    row["low_traverses"] = low

    # jig parts
    jigs = {n: m for n, (k, m) in shifted.items()
            if (k == "fixture" and not any(w in n.lower() for w in NOT_JIG)) or "guide" in n.lower()}
    row["jig_parts"] = len(jigs)
    row["jig_volume_l"] = round(sum(abs(m.volume) if m.is_watertight else m.convex_hull.volume
                                    for m in jigs.values()) / 1e6, 2)

    # collisions (the slow part)
    clear = {}
    sh = {n: list(d) for n, d in shift.items()}
    hits = collision.check_program(program, cell_s, step, parts=True, shift=sh, clearance=clear)
    row["collisions_fixtures"] = sum(h["check"] == "fixtures" for h in hits)
    row["collisions_parts"] = sum(h["check"] == "parts" for h in hits)
    row["min_clearance_mm"] = round(min(clear.values()), 1) if clear else ""
    row["score_seconds"] = round(time.time() - t0, 1)

    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / f"{row['label']}.json").write_text(json.dumps(
        {"row": row, "shift": sh, "hits": [{**h, "pairs": [list(p) for p in h["pairs"]]} for h in hits],
         "clearance_mm": {str(k): round(v, 1) for k, v in sorted(clear.items())},
         "mu1_vfix": [round(float(v), 2) for v in mu1], "kin_problems": problems,
         "definitions": {"NEAR_MM": NEAR_MM, "TRAVERSE_MM": TRAVERSE_MM, "LOW_MARGIN": LOW_MARGIN,
                         "tallest_object_z": round(float(top), 1), "step": step}}, indent=1, default=str))
    return row


def score_version(v, step=2.0):
    prog, cell, geo, note = VERSIONS[v]
    return score(prog, cell, geo, label=v, version=v, note=note, step=step)


def write_rows(rows, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    new = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program", nargs="?")
    ap.add_argument("cell", nargs="?")
    ap.add_argument("--label")
    ap.add_argument("--version", choices=list(VERSIONS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--geometry", default="techman", choices=["techman", "robodk"])
    ap.add_argument("--shift", action="append", default=[], help='"<object>:dx,dy,dz[,rz]" (robot base, mm / deg)')
    ap.add_argument("--step", type=float, default=2.0)
    ap.add_argument("--out", default=str(OUT_CSV))
    ap.add_argument("--no-csv", action="store_true")
    a = ap.parse_args()
    rows = []
    if a.all or a.version:
        vs = list(VERSIONS) if a.all else [a.version]
        if a.jobs > 1 and len(vs) > 1:
            with ProcessPoolExecutor(a.jobs) as ex:
                futs = {v: ex.submit(score_version, v, a.step) for v in vs}
                for v, f in futs.items():
                    try:
                        rows.append(f.result())
                    except Exception as e:                       # one broken version doesn't lose the others
                        print(f"{v}: FAILED {type(e).__name__}: {e}", flush=True)
        else:
            for v in vs:
                rows.append(score_version(v, a.step))
    else:
        if not (a.program and a.cell):
            ap.error("give a program and a cell, or --version / --all")
        shift = {s.split(":")[0]: [float(x) for x in s.split(":")[1].split(",")] for s in a.shift}
        shift = {k: (v + [0.0] * (4 - len(v))) for k, v in shift.items()}
        rows.append(score(a.program, a.cell, a.geometry, label=a.label, step=a.step, shift=shift))
    for r in rows:
        print(f"{r['label']:6s} cycle {r['cycle_s']} s, path {r['tcp_path_m']} m, joints {r['joint_travel_deg']} deg, "
              f"collisions fx {r['collisions_fixtures']} / parts {r['collisions_parts']}, clearance {r['min_clearance_mm']} mm, "
              f"({r['score_seconds']} s)", flush=True)
    if not a.no_csv:
        write_rows(rows, Path(a.out))


if __name__ == "__main__":
    main()
