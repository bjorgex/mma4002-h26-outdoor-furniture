"""The judge: score one robot program in one cell model -> one row of metrics + the hard-rule checks.

    python judge/score.py design/program.json design/cell.glb --out log/try [--step 2] [--no-shots]
    python judge/score.py ... --step 10 --no-shots        a quick screen (coarse sampling: not valid for keeping)

Out (--out DIR): DIR/score.json (the row, every hit, every rule violation, per-move data, the sampled TCP path),
DIR/shots/*.png (3D renders after every release + start + end, iso and top view; shots.py) and DIR/topview.png.
Prints a short summary; exit code 0 = every hard rule passed, 1 = at least one violation.

Metric columns (one row per run; the same as the human versions' table):
    cycle_s / cycle_ramps_s   cycle_time.estimate: programmed speeds, + trapezoid ramps (no blending)
    phases_s                  the same split by phase (json, programmed s)
    tcp_path_m                TCP path over every move, PTP included, from the sampled joint path
    line_path_m               only the Line moves
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
    max_mu1_vfix / min_mu3_vfix / near_singular   manipulability at each move's end joints (vfix = orientation
                              held), near_singular = targets with mu1_vfix > manip.MU1_THR
    grips                     gripper "grip" events; regrasps = grips of a part that was gripped before
    part_flips                grip -> release with the held part turned > 90 deg
    jig_parts / jig_volume_l  fixture objects that are jigs (not table, plates, AMR, markers) + the guides (the robot
                              moves them, but they are jig parts); volume from the meshes (convex hull if not closed)
Hard-rule columns (AGENT.md "Hard constraints"; rule_violations = their sum, 0 = the design is legal):
    r1_collisions             collisions_fixtures + collisions_parts
    r2_kinematics             ik_failures + line_failures + limit_hits
    r3_approach               grip / release events whose last APPROACH_MM in or first APPROACH_MM out is not a
                              vertical Line (TCP within VERT_TOL_MM of the event point in x/y, above it) at
                              <= SLOW mm/s; + low_traverses (free moves below the safe height)
    r4_ptp_near               PTP moves with ptp_near_parts, or with a TCP sample less than PTP_ABOVE_MM above a jig
                              or a part that is not held (inside its x/y box)
    r5_clearance              free moves (PTP, or Line faster than SLOW) with clearance < MIN_CLEAR_MM
    r6_floating               releases where the released parts float (collision.py rest check), + objects that
                              float at the start (parts and jigs; table, AMR and markers left out)
    r7_jigs                   jigs off the work plate (x/y) or larger than MAX_PRINT_MM (oriented box, longest side)
    r8_bench                  bench parts missing / changed (volume, size), or not assembled at the end (every part
                              within BENCH_TOL_MM of where it belongs relative to frame2)
    r_fixed                   fixed parameters changed: tcp, gripper (egp_gap), Line speed > FAST, PTP joint speed >
                              JOINT, gripper waits shorter than WAIT_GRIP / WAIT_DO, table or plate changed
    min_clearance_free_mm     the smallest clearance in free moves
    min_z_free_mm             the lowest TCP z in free moves (robot base frame)
    jig_max_print_mm          the longest side (oriented box) of any jig
"""
import argparse
import datetime
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tm5_kin as K                                         # noqa: E402

NEAR_MM = 100.0          # ptp_near_parts: TCP this close to a grip / release point
TRAVERSE_MM = 100.0      # low_traverses: horizontal TCP travel of the move
LOW_MARGIN = 50.0        # low_traverses: margin over the tallest object at the start
APPROACH_MM = 50.0       # r3: last / first mm into / out of a part
VERT_TOL_MM = 1.0        # r3: x/y deviation from the event point that still counts as vertical
PTP_ABOVE_MM = 100.0     # r4
MIN_CLEAR_MM = 10.0      # r5
MAX_PRINT_MM = 250.0     # r7
BENCH_TOL_MM = 2.0       # r8
FAST, SLOW, JOINT = 100.0, 20.0, 50.0                       # mm/s, mm/s, deg/s (fixed)
WAIT_GRIP, WAIT_DO = 500, 300                               # ms (fixed)
TCP = [0.0, 0.0, 160.0, 0.0, 0.0, 0.0]                      # fixed
NOT_JIG = ("table", "plate", "amr", "vision", "marker")
BENCH = ["frame1", "frame2"] + [f"plank{k}" for k in range(1, 7)] + \
        [f"piece {s}{k}" for s in "AB" for k in range(1, 7)]
REF = json.loads((HERE / "reference.json").read_text(encoding="utf-8")) if (HERE / "reference.json").exists() else {}

COLUMNS = ["label", "version", "scored_at", "program", "cell", "geometry", "note",
           "cycle_s", "cycle_ramps_s", "phases_s",
           "tcp_path_m", "line_path_m", "joint_travel_deg", "j1_travel_deg", "j2_travel_deg", "j3_travel_deg",
           "j4_travel_deg", "j5_travel_deg", "j6_travel_deg", "n_moves", "n_ptp", "n_line", "wrist_flips",
           "collisions_fixtures", "collisions_parts", "min_clearance_mm", "ptp_near_parts", "low_traverses",
           "ik_failures", "line_failures", "limit_hits", "max_mu1_vfix", "min_mu3_vfix", "near_singular",
           "grips", "regrasps", "part_flips", "jig_parts", "jig_volume_l",
           "iteration", "wall_time_s", "kept", "tool_changes", "score_seconds"]
RULE_COLUMNS = ["rule_violations", "r1_collisions", "r2_kinematics", "r3_approach", "r4_ptp_near", "r5_clearance",
                "r6_floating", "r7_jigs", "r8_bench", "r_fixed", "min_clearance_free_mm", "min_z_free_mm",
                "jig_max_print_mm", "step_mm"]


def _tools(geometry):
    K.use(geometry)
    import collision
    import cycle_time
    import kin_check
    import manip
    from program_io import load_program
    return collision, cycle_time, kin_check, manip, load_program


def _rz(d):
    c, s_ = math.cos(math.radians(d[3])), math.sin(math.radians(d[3]))
    return np.array([[c, -s_, 0, d[0]], [s_, c, 0, d[1]], [0, 0, 1, d[2]], [0, 0, 0, 1]])


def score(program_path, cell_path, geometry="station", label=None, version="", note="", step=2.0, shift=None,
          out_dir=None, shots=True, layout_path=None):
    """(row, details). `shift` {object: (dx, dy, dz, rz)} moves cell objects first (robot base axes)."""
    t0 = time.time()
    collision, cycle_time, kin_check, manip, load_program = _tools(geometry)
    prog_path = Path(program_path)
    program = load_program(prog_path)
    cell_s = str(cell_path)
    cell = dict(collision.load_cell(cell_s))
    shift = shift or {}
    T_tcp = np.array(K.pose_to_mat(program.get("tcp", {}).get("pose", [0, 0, 160, 0, 0, 0])))
    steps = program["steps"]
    moves = [s for s in steps if "move" in s]
    row = {c: "" for c in COLUMNS + RULE_COLUMNS}
    row.update(label=label or version or prog_path.stem, version=version, note=note, geometry=geometry,
               scored_at=datetime.datetime.now().isoformat(timespec="seconds"), program=str(prog_path),
               cell=Path(cell_s).name + (f" + shift {sorted(shift)}" if shift else ""), step_mm=step)

    # time
    phases, line_m = cycle_time.estimate(program)
    row["cycle_s"] = round(sum(a for a, _ in phases.values()), 1)
    row["cycle_ramps_s"] = round(sum(b for _, b in phases.values()), 1)
    row["phases_s"] = json.dumps({k: round(a, 1) for k, (a, _) in phases.items()})
    row["line_path_m"] = round(line_m, 2)

    # motion along the sampled path
    per, events = collision.program_samples(program, step)
    travel, tcp_pts = np.zeros(6), []
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
    grip_pts, ev_list, seen, regrasp, flips, grips = [], [], set(), 0, 0, 0
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
        ev_list.append((mi, g, s.get("parts", []), p))
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
    near, near_moves = 0, set()
    for k, s in enumerate(moves):
        if s["move"] != "ptp" or k == 0 or not len(gp):
            continue
        ends = (tcp_pts[k - 1][-1], tcp_pts[k][-1])
        if any(np.min(np.linalg.norm(gp - e, axis=1)) < NEAR_MM for e in ends):
            near += 1
            near_moves.add(k)
    row["ptp_near_parts"] = near

    # low traverses: against the tallest object at the start (shifted cell)
    shifted = dict(cell)
    for n, d in shift.items():
        kind, mesh = cell[n]
        mesh = mesh.copy()
        mesh.apply_transform(_rz(d))
        shifted[n] = (kind, mesh)
    top = max(m.bounds[1][2] for n, (k, m) in shifted.items() if not n.lower().startswith(("amr",)))
    low, low_moves = 0, []
    for k in range(1, len(tcp_pts)):
        pts = np.vstack([tcp_pts[k - 1][-1:], tcp_pts[k]])
        if np.linalg.norm(pts[-1, :2] - pts[0, :2]) > TRAVERSE_MM and pts[:, 2].max() < top + LOW_MARGIN:
            low += 1
            low_moves.append(k + 1)
    row["low_traverses"] = low

    # jig parts
    jigs = {n: m for n, (k, m) in shifted.items()
            if (k == "fixture" and not any(w in n.lower() for w in NOT_JIG)) or "guide" in n.lower()}
    row["jig_parts"] = len(jigs)
    row["jig_volume_l"] = round(sum(abs(m.volume) if m.is_watertight else m.convex_hull.volume
                                    for m in jigs.values()) / 1e6, 2)

    # collisions (the slow part) + the rest check + snapshots
    clear, rest, snaps = {}, [], []
    sh = {n: list(d) for n, d in shift.items()}
    hits = collision.check_program(program, cell_s, step, parts=True, shift=sh, clearance=clear, rest=rest,
                                   snaps=snaps)
    row["collisions_fixtures"] = sum(h["check"] == "fixtures" for h in hits)
    row["collisions_parts"] = sum(h["check"] == "parts" for h in hits)
    row["min_clearance_mm"] = round(min(clear.values()), 1) if clear else ""

    # ------------------------------------------------------------------ hard rules
    viol = {}                                                # rule -> list of findings (strings)
    free = [k for k, s in enumerate(moves) if s["move"] == "ptp" or s.get("speed", FAST) > SLOW]

    # r3: vertical slow approach / retreat at every grip / release
    r3 = []
    for (mi, g, parts, p) in ev_list:
        for direction in ("in", "out"):
            ks = range(mi, -1, -1) if direction == "in" else range(mi + 1, len(per))
            dist, bad = 0.0, None
            for k in ks:
                pts = np.vstack([tcp_pts[k - 1][-1:] if k else tcp_pts[k][:1], tcp_pts[k]])
                if direction == "in":
                    pts = pts[::-1]
                d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
                if d[-1] < 1e-6:
                    continue
                inside = pts[d + dist <= APPROACH_MM + 1e-6]
                s = moves[k]
                if s["move"] != "line" or s.get("speed", FAST) > SLOW:
                    bad = f"move #{k + 1} ({s['move']}, {s.get('speed', '')} mm/s) inside the last/first {APPROACH_MM:.0f} mm"
                elif len(inside) and (np.linalg.norm(inside[:, :2] - p[:2], axis=1).max() > VERT_TOL_MM
                                      or inside[:, 2].min() < p[2] - VERT_TOL_MM):
                    bad = f"move #{k + 1} not vertical above the event point"
                dist += d[-1]
                if bad or dist >= APPROACH_MM:
                    break
            if bad:
                r3.append(f"{g} {', '.join(parts[:3])} after move #{mi + 1}, {direction}: {bad}")
    r3 += [f"low traverse: move #{k} below the safe height ({top + LOW_MARGIN:.0f} mm)" for k in low_moves]
    viol["r3_approach"] = r3

    # r4: PTP near parts / above jigs and parts that are not held
    jig_boxes = {n: m.bounds for n, m in jigs.items() if n in cell and cell[n][0] == "fixture"}
    part_mesh = {n: m for n, (k, m) in shifted.items() if k == "part"}
    r4 = []
    snap_at = sorted(snaps, key=lambda x: x["move"])
    for k, s in enumerate(moves):
        if s["move"] != "ptp" or k == 0:
            continue
        why = []
        if k in near_moves:
            why.append(f"starts/ends within {NEAR_MM:.0f} mm of a grip/release point")
        before = [x for x in snap_at if x["move"] <= k]       # snapshots after move k (1-based) = before this move
        state = before[-1] if before else None
        held = set()
        for x in snap_at:
            if x["move"] > k:
                break
            if x["event"] == "grip":
                held |= set(x["parts"])
            elif x["event"] == "release":
                held = set()
        boxes = dict(jig_boxes)
        if state:
            for n, P in state["poses"].items():
                if n in held or n not in part_mesh:
                    continue
                v = part_mesh[n].vertices @ P[:3, :3].T + P[:3, 3]
                boxes[n] = np.array([v.min(0), v.max(0)])
        pts = tcp_pts[k]
        for n, (lo, hi) in boxes.items():
            inside = (pts[:, 0] >= lo[0]) & (pts[:, 0] <= hi[0]) & (pts[:, 1] >= lo[1]) & (pts[:, 1] <= hi[1])
            if np.any(inside & (pts[:, 2] < hi[2] + PTP_ABOVE_MM)):
                why.append(f"TCP < {PTP_ABOVE_MM:.0f} mm above {n}")
                break
        if why:
            r4.append(f"PTP move #{k + 1} ({s.get('name', '')}): " + "; ".join(why))
    viol["r4_ptp_near"] = r4

    # r5: clearance in free moves
    fc = {k + 1: clear[k + 1] for k in free if k + 1 in clear}
    row["min_clearance_free_mm"] = round(min(fc.values()), 1) if fc else ""
    viol["r5_clearance"] = [f"free move #{m} ({moves[m - 1].get('name', '')}): clearance {c:.1f} mm < {MIN_CLEAR_MM:.0f}"
                            for m, c in sorted(fc.items()) if c < MIN_CLEAR_MM]
    zf = [tcp_pts[k][:, 2].min() for k in free if k > 0]
    row["min_z_free_mm"] = round(float(min(zf)), 1) if zf else ""

    # r6: released parts float / objects float at the start
    r6 = [f"release after move #{r['move']}: {', '.join(r['parts'])} floats (nothing {collision.DROP_MM:.0f} mm below)"
          for r in rest if not r["rests"]]
    r6 += [f"start: {n} floats" for n in start_floating(collision, shifted)]
    viol["r6_floating"] = r6

    # r7: jigs on the plate, printable size
    plate = next((m for n, (k, m) in shifted.items() if "plate" in n.lower() and "amr" not in n.lower()), None)
    r7, longest = [], 0.0
    for n, m in jigs.items():
        ext = float(max(m.bounding_box_oriented.extents))
        longest = max(longest, ext)
        if ext > MAX_PRINT_MM + 0.5:
            r7.append(f"{n}: {ext:.0f} mm long > {MAX_PRINT_MM:.0f} mm (split it into printable parts)")
        if plate is not None:
            (x0, y0, _), (x1, y1, _) = plate.bounds
            (a0, b0, _), (a1, b1, _) = m.bounds
            if a0 < x0 - 1 or b0 < y0 - 1 or a1 > x1 + 1 or b1 > y1 + 1:
                r7.append(f"{n}: not on the work plate (x/y outside it)")
    row["jig_max_print_mm"] = round(longest, 1)
    viol["r7_jigs"] = r7

    # r8: the bench product
    viol["r8_bench"] = bench_check(cell, snaps, layout_path or _layout_of(cell_s), shift)

    # fixed parameters
    viol["r_fixed"] = fixed_check(program, shifted)

    row["r1_collisions"] = row["collisions_fixtures"] + row["collisions_parts"]
    row["r2_kinematics"] = row["ik_failures"] + row["line_failures"] + row["limit_hits"]
    for r, v in viol.items():
        row[r] = len(v)
    row["rule_violations"] = sum(row[c] for c in RULE_COLUMNS[1:10])
    row["score_seconds"] = round(time.time() - t0, 1)

    # ------------------------------------------------------------------ details
    names = [s.get("name", "") for s in moves]
    per_move = []
    for k, s in enumerate(moves):
        p = tcp_pts[k]
        per_move.append({"move": k + 1, "name": names[k], "type": s["move"], "speed": s.get("speed"),
                         "free": k in free, "clearance_mm": round(clear[k + 1], 1) if k + 1 in clear else None,
                         "mu1_vfix": round(float(mu1[k - 1]), 2) if k else None,
                         "tcp_z_min": round(float(p[:, 2].min()), 1), "tcp_z_max": round(float(p[:, 2].max()), 1),
                         "tcp_end": [round(float(v), 1) for v in p[-1]]})
    path = [{"move": k + 1, "xyz": np.round(tcp_pts[k][::max(1, len(tcp_pts[k]) // 25)], 1).tolist()}
            for k in range(len(tcp_pts))]
    details = {"row": row, "shift": sh,
               "hits": [{**h, "pairs": [list(p) for p in h["pairs"]]} for h in hits],
               "violations": viol, "rest": rest,
               "kin_problems": problems, "per_move": per_move, "tcp_path": path,
               "events": [{"after_move": mi + 1, "gripper": g, "parts": parts, "tcp": np.round(p, 1).tolist()}
                          for mi, g, parts, p in ev_list],
               "definitions": {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float))}
               | {"tallest_object_z": round(float(top), 1), "step": step, "DROP_MM": collision.DROP_MM}}
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "score.json").write_text(json.dumps(details, indent=1, default=_js), encoding="utf-8")
        if shots:
            import shots as S
            S.render(shifted, snaps, tcp_pts, moves, out, label=row["label"])
    return row, details


def _js(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return str(o)


def _layout_of(cell_s):
    p = Path(cell_s)
    if p.suffix == ".json":
        return p
    cand = p.with_name(p.name.replace("cell", "cell_layout", 1).replace(".glb", ".json"))
    return cand if cand.exists() else None


def start_floating(collision, cell):
    """Parts and jigs that float at the start (moved DROP_MM down they touch nothing)."""
    import trimesh
    out = []
    skip = ("table", "amr", "vision", "marker")
    objs = {n: m for n, (k, m) in cell.items()}
    mgr = trimesh.collision.CollisionManager()
    for n, m in objs.items():
        mgr.add_object(n, m)
    down = np.eye(4)
    down[2, 3] = -collision.DROP_MM
    for n, m in objs.items():
        if any(w in n.lower() for w in skip):
            continue
        one = trimesh.collision.CollisionManager()
        one.add_object(n, m, transform=down)
        hit, pairs = one.in_collision_other(mgr, return_names=True)
        if not (hit and any(b != n for a, b in pairs)):
            out.append(n)
    return out


def bench_check(cell, snaps, layout_path, shift):
    """The bench parts are all there, unchanged, and assembled at the end (relative to frame2)."""
    out = []
    if not REF:
        return ["judge/reference.json missing"]
    lay = {}
    if layout_path and Path(layout_path).exists():
        lay = {o["name"]: np.array(o["pose"]) for o in json.loads(Path(layout_path).read_text())["objects"]}
    end = next((x for x in reversed(snaps) if x["event"] == "end"), None)
    final = {}
    for n in BENCH:
        if n not in cell or cell[n][0] != "part":
            out.append(f"{n}: missing in the cell")
            continue
        if n not in lay:
            out.append(f"{n}: no pose in the cell layout json")
            continue
        ref = REF["parts"][n]
        L = lay[n].copy()
        local = cell[n][1].copy()
        local.apply_transform(np.linalg.inv(L))
        if n in shift:                                       # the start mesh the program's poses apply to
            L = _rz(shift[n]) @ L
        if abs(abs(local.volume) - ref["volume"]) > 0.01 * ref["volume"] or \
                np.abs(local.bounds - np.array(ref["bounds"])).max() > 0.5:
            out.append(f"{n}: mesh changed (volume {abs(local.volume):.0f} vs {ref['volume']:.0f} mm3, or size)")
            continue
        P = end["poses"].get(n) if end else None
        if P is None:
            out.append(f"{n}: not in the program's end state")
            continue
        final[n] = (P @ L, np.array(ref["bounds"]))
    if "frame2" in final and not out:
        A = {n: np.array(REF["parts"][n]["asm"]) for n in BENCH}
        M = final["frame2"][0] @ np.linalg.inv(A["frame2"])
        worst = []
        for n, (T, b) in final.items():
            corners = np.array([[x, y, z, 1] for x in b[:, 0] for y in b[:, 1] for z in b[:, 2]])
            err = np.linalg.norm((corners @ T.T - corners @ (M @ A[n]).T)[:, :3], axis=1).max()
            if err > BENCH_TOL_MM:
                worst.append((err, n))
        for err, n in sorted(worst, reverse=True):
            out.append(f"{n}: {err:.1f} mm from its place in the bench at the end (relative to frame2)")
    return out


def fixed_check(program, cell):
    out = []
    tcp = program.get("tcp", {}).get("pose", TCP)
    if max(abs(a - b) for a, b in zip(tcp, TCP)) > 1e-6:
        out.append(f"tcp changed: {tcp}")
    if program.get("joint_speed", JOINT) > JOINT + 1e-6:
        out.append(f"program joint_speed {program['joint_speed']} > {JOINT}")
    parts = {n for n, (k, m) in cell.items() if k == "part"}
    for s in program["steps"]:
        nm = s.get("name", "")
        if "egp_gap" in s:
            out.append(f"{nm}: egp_gap (the gripper is fixed)")
        if "move" in s:
            if s["move"] == "line" and not 0 < s.get("speed", 0) <= FAST + 1e-6:
                out.append(f"{nm}: Line speed {s.get('speed')} (allowed 0 < v <= {FAST:.0f})")
            if s["move"] == "ptp" and s.get("joint_speed", program.get("joint_speed", JOINT)) > JOINT + 1e-6:
                out.append(f"{nm}: PTP joint_speed {s.get('joint_speed')} > {JOINT:.0f}")
        elif "do0" in s or s.get("gripper"):
            need = WAIT_GRIP if s.get("gripper") in ("grip", "release") else WAIT_DO
            if s.get("wait_ms", need) < need:
                out.append(f"{nm}: wait {s.get('wait_ms')} ms < {need} ms")
            unknown = [p for p in s.get("parts", []) if p not in parts and p.lower() not in {q.lower() for q in parts}]
            if s.get("gripper") == "grip" and unknown:
                out.append(f"{nm}: grips unknown parts {unknown}")
    for n in ("Table", "Ground base plate"):
        if n in REF.get("fixed", {}):
            if n not in cell:
                out.append(f"{n}: missing in the cell")
            elif np.abs(cell[n][1].bounds - np.array(REF["fixed"][n])).max() > 0.5:
                out.append(f"{n}: moved or changed")
    return out


def summary(row, details):
    lines = [f"{row['label']}: cycle {row['cycle_s']} s (ramps {row['cycle_ramps_s']} s), joints "
             f"{row['joint_travel_deg']} deg, TCP path {row['tcp_path_m']} m, {row['n_moves']} moves "
             f"({row['n_ptp']} PTP), phases {row['phases_s']}",
             f"  rule violations {row['rule_violations']}: " + ", ".join(f"{c} {row[c]}" for c in RULE_COLUMNS[1:10]),
             f"  clearance min {row['min_clearance_mm']} mm (free moves {row['min_clearance_free_mm']} mm), "
             f"max mu1 {row['max_mu1_vfix']}, near-singular {row['near_singular']}, jig parts {row['jig_parts']} "
             f"({row['jig_volume_l']} l, longest {row['jig_max_print_mm']} mm), step {row['step_mm']} mm, "
             f"{row['score_seconds']} s"]
    for h in details["hits"][:12]:
        pairs = sorted({f"{p}/{q}" for p, q in h["pairs"]})
        lines.append(f"  HIT {h['check']} move #{h['move']} ({h['name']}, {h['context']}): {', '.join(pairs[:5])}")
    for r, v in details["violations"].items():
        for x in v[:8]:
            lines.append(f"  {r}: {x}")
        if len(v) > 8:
            lines.append(f"  {r}: ... {len(v) - 8} more (score.json)")
    for tag, notes in details["kin_problems"][:8]:
        lines.append(f"  KIN {tag}: {'; '.join(notes)}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program")
    ap.add_argument("cell", help="cell .glb (its cell_layout json next to it)")
    ap.add_argument("--label")
    ap.add_argument("--out", help="folder for score.json + shots")
    ap.add_argument("--step", type=float, default=2.0)
    ap.add_argument("--geometry", default="station", choices=list(K.GEOMETRY))
    ap.add_argument("--no-shots", action="store_true")
    a = ap.parse_args()
    row, details = score(a.program, a.cell, a.geometry, label=a.label, step=a.step, out_dir=a.out,
                         shots=not a.no_shots)
    print(summary(row, details))
    raise SystemExit(0 if row["rule_violations"] == 0 else 1)


if __name__ == "__main__":
    main()
