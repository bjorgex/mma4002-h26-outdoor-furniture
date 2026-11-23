"""Bench V1 cell v11, ONE plank (v11-1plank): a cut-down test program for the real TM5-900 cell.

    python bench_cell_v11_1plank.py                                    no moves file: every jig where it was taught
    python bench_cell_v11_1plank.py <moves.json>                       measured jig moves, v11 names (below)
    python bench_cell_v11_1plank.py <moves.json> --sim-names           the same in v9/v10 names (jig_vision.py's model)
    add --check: reach (IK + Line followability), collisions (fixtures + parts), cycle time in the own sim tools
-> tests/v11_1plank_moves.json      the program (tests/v10_moves.json's format, cell "v11-1plank", v11 names)
   tests/v11_1plank_segments.json   the program split at every gripper action, for the Listen-node driver

NAMES (v11 = the real cell; the v9 CAD, cell_v9.glb, jig_boxes_v9.json, v9/v10_moves.json and jig_vision.py's
model have A and B the other way round):
    v11 "Base A" = START base: frame 1 + its interface pieces + the guide (red/black halves); the plank goes in here
                 = v9/v10 "Base B" (robot base y < 0)
    v11 "Base B" = END base: frame 2 + its interface pieces, nothing else
                 = v9/v10 "Base A" (robot base y > 0)
    "Plank rack" is the same in both. Part names (frame1, frame2, plank2, piece A2/B2, Guide small/big) are v9's:
    frame1 / piece A2 sit in v11 Base A, frame2 / piece B2 in v11 Base B.
Bases: straight on the T-slot plate, no risers (as in v9's CAD already - the risers were the v3/v4 cells).

Program: v9's (tests/v9_moves.json) with stage 1 cut to its FIRST plank (plank2 - v9 places plank2 first, rack ->
through the guide into frame 1), then v9's stages 2-7 unchanged: small, then big guide half A -> B, frame 1 + plank
picked up and turned over onto frame 2 in B ("flip frame"), big, then small half back B -> A, the finished bench
stood up and set down on the AMR, home. Planks 1, 3, 5, 6 and their interface pieces are not in the cell.
That source goes through bench_cell_v10.build() (imported, not copied; its output redirected so tests/v10_moves.json
is untouched): every move follows the jig of its grab/release and is shifted by that jig's measured move
(new flange = T_move @ taught flange), IK solved again seeded with v9's joints, an up/over at z 596 added where a low
transfer joins two jigs that moved differently; an unreachable target stops the build.

Moves file: jig_vision.py --save format {"moves": {"<jig>": {"x", "y" (mm, the pivot's move), "rz" (deg), "T_move"
(4x4, optional)}}}. T_move is used when present, else x/y/rz about the jig's pivot (jig_boxes_v9.json). Jigs not in
the file stay where taught.

Segments file: [moves, GRIP|RELEASE, moves, ...]. Move: "type" PTP|Line, "flange" = TM pose [X, Y, Z mm, Rx, Ry,
Rz deg] of the FLANGE (tool 0, no TCP) in the ROBOT BASE - what tests/step_run.py sends with Line("CAP", ...) -,
"joints" (deg; send PTP as PTP("JPP", joints) to keep v9's arm configuration), "tcp_xyz" (closed fingertips,
information only), speed: Line "speed_mm_s" (the program's), PTP "speed_pct" (step_run.py's default 50 %).
Gripper: GRIP = close, RELEASE = open. The gripper must be open at the start (SET + RELEASE before the first Listen).
"""
import argparse
import contextlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests" / "robot_sim"))
import bench_cell_v10 as V10                            # noqa: E402
import teach_overrides                                  # noqa: E402  grip points taught on the robot
import tm5_kin                                          # noqa: E402
from bench_cell_v9 import PLATE                         # noqa: E402  plate frame in robot base (tests/robot_sim/teach.py)

VERSION = "v11_1plank"                                  # teach_v11_1plank.json, tests/v11_1plank_moves.json
TESTS = HERE / "tests"
TIP = V10.TIP                                           # flange -> closed fingertips (mm along tool z)

OUT = HERE / "tests" / "v11_1plank_moves.json"
SEG = HERE / "tests" / "v11_1plank_segments.json"
CELL_GLB = HERE / "tests" / "robot_sim" / "cell_v9.glb"
TO_SIM = {"Base A": "Base B", "Base B": "Base A", "Plank rack": "Plank rack"}     # v11 name -> v9/v10 name
TO_V11 = {s: v for v, s in TO_SIM.items()}
KEEP = 2                                                # plank2: the first plank v9 places
DROPPED = {f"{p}{k}" for k in (1, 3, 5, 6) for p in ("plank", "piece A", "piece B")}
ON_JIG = {"Base B": ("frame1", "piece A2", "Guide small", "Guide big"),           # sim names: what sits on a jig at
          "Base A": ("frame2", "piece B2")}                                        # the start and moves with it
PTP_PCT = 50                                            # step_run.py's default joint speed


# v9 move names -> v11 names (by v9 stage), so the teach list reads as the one-plank test with A = start, B = end
RENAME = {1: ("plank2 ", "plank "), 2: ("guide small ", "small half to B "), 3: ("guide big ", "big half to B "),
          4: ("sub ", "frame flip "), 5: ("big half ", "big half back to A "),
          6: ("small half ", "small half back to A "), 7: ("bench ", "bench to AMR ")}


def v11_name(name, stage):
    old, new = RENAME.get(stage, ("", ""))
    if not old or not name.startswith(old):
        return name                                     # Home, "back up", the gripper steps
    return (new + name[len(old):]).replace(" to start base", " across")


def one_plank_source():
    """v9's steps with stage 1 cut to plank2's pick and place; dropped planks/pieces out of every part list."""
    src = json.loads(V10.SRC.read_text())
    steps = []
    for s in src["steps"]:
        if s.get("stage") == 1 and s.get("name") != "Home":
            if "move" in s and not s["name"].startswith(f"plank{KEEP} "):
                continue
            if "move" not in s and s.get("parts") != [f"plank{KEEP}"]:
                continue
        s = dict(s)
        if "parts" in s:
            s["parts"] = [p for p in s["parts"] if p not in DROPPED]
        if "move" in s:
            s["name"] = v11_name(s["name"], s.get("stage"))
        steps.append(s)
    return {**src, "steps": steps}


def sim_moves(path, sim_names=False):
    """The moves file in v9/v10 jig names, with T_move for every jig (x, y, rz about its pivot where missing)."""
    d = json.loads(Path(path).read_text())
    boxes = json.loads(V10.BOXES.read_text())["jigs"]
    out = {}
    for n, m in d["moves"].items():
        s = n if sim_names else TO_SIM.get(n, n)        # guides etc. keep their names
        m = dict(m)
        if not m.get("T_move"):
            r = np.radians(m.get("rz", 0.0))
            R = np.array([[np.cos(r), -np.sin(r), 0], [np.sin(r), np.cos(r), 0], [0, 0, 1]])
            p = np.array(boxes[s]["pivot"], float)
            T = np.eye(4)
            T[:3, :3], T[:3, 3] = R, p + [m.get("x", 0.0), m.get("y", 0.0), 0.0] - R @ p
            m["T_move"] = T.tolist()
        out[s] = m
    return out


def build(moves_file=None, sim_names=False):
    tmp = Path(tempfile.mkdtemp(prefix="v11_1plank_"))
    (tmp / "v9_1plank_moves.json").write_text(json.dumps(one_plank_source()))
    mf = None
    if moves_file:
        mf = tmp / "moves_sim_names.json"
        mf.write_text(json.dumps({"moves": sim_moves(moves_file, sim_names)}))
    src_save, out_save = V10.SRC, V10.OUT
    V10.SRC, V10.OUT = tmp / "v9_1plank_moves.json", tmp / "built.json"    # never tests/v10_moves.json
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):           # its report speaks v9/v10 names: swap them for v11's
            out = V10.build(str(mf) if mf else None)
    finally:
        V10.SRC, V10.OUT = src_save, out_save
    print(re.sub(r"'?Base [AB]'?", lambda m: m[0].replace(m[0].strip("'"), TO_V11[m[0].strip("'")]), log.getvalue())
          .replace("built.json", OUT.name), end="")
    for s in out["steps"]:
        if s.get("jig"):
            s["jig"] = TO_V11.get(s["jig"], s["jig"])
        if "move" in s:
            s["name"] = s["name"].replace(" (v10)", " (high travel)")
    taught = apply_teach(out["steps"])
    above_interface(out["steps"])
    drop_deleted(out["steps"])
    hand_points(out["steps"])
    joint_flip(out["steps"])
    # simple_flip(out["steps"])   # 2026-11-20: off - step 2/6 unreachable; the 13 turns stay (fix later)
    out.update(cell="v11-1plank", station="Bench V1 cell v11 (1 plank)",
               names="v11: Base A = START base (frame1, guide; v9/v10 'Base B'), Base B = END base (frame2; "
                     "v9/v10 'Base A')",
               jig_moves={TO_V11[k]: v for k, v in out["jig_moves"].items()}, parts_removed=sorted(DROPPED),
               taught=f"{taught} moves corrected from {teach_overrides.path_for(VERSION).name}",
               source=f"bench_cell_v11_1plank.py: v9_moves.json cut to plank{KEEP} via bench_cell_v10.build() + "
                      f"{Path(moves_file).name if moves_file else 'no jig moves'}")
    OUT.write_text(json.dumps(out, indent=1))
    print(f"{OUT.name}: jig moves (v11 names) {out['jig_moves']}")
    import kin_check as KC                              # a Line the arm can't follow (a joint limit on the way,
    from tmflow_export import load_program              # another IK branch at the end) - say so right away
    stats, problems, _ = KC.check(load_program(str(OUT)), report=lambda *a, **k: None)
    bad = stats["limit"] + stats["line_fail"] + stats["line_posture"] + stats["limit_path"] + stats["j5_flip_line"]
    if bad:
        print(f"WARNING: {bad} move(s) can't be driven as programmed (kin_check.py): " + "; ".join(map(str, problems)))
    segments(out)
    return out


DELETED = HERE / "tests" / "v11_1plank_deleted.json"   # move names deleted on the robot (step_run 'delete')


def drop_deleted(steps):
    """Remove the moves named in tests/v11_1plank_deleted.json (Bjørge deletes them in the step tool)."""
    if not DELETED.exists():
        return
    gone = set(json.loads(DELETED.read_text(encoding="utf-8")).get("deleted", []))
    before = len(steps)
    steps[:] = [s for s in steps if not ("move" in s and s.get("name") in gone)]
    if before != len(steps):
        print(f"deleted on request: {before - len(steps)} move(s) {sorted(gone)}")


HAND = HERE / "tests" / "v11_1plank_hand_points.json"     # poses set by hand on the robot (FreeBot)


def hand_points(steps):
    """2026-11-20 (Bjørge): the end base was turned 90 deg and the bench is grabbed lower. Two poses set by hand
    replace the program's: 'frame flip pick' and 'frame flip above guide'. Their neighbours follow:
      over pick = pick + 100 mm up; pick approach / pick out / up = pick + their old offsets to the old pick
      (new pick's orientation); 'frame flip turn 15' is dropped (the flip starts at 'frame flip up');
      place = above guide - 75 mm (straight down, as before); place out / back up go STRAIGHT UP (+40 mm,
      then the old height) - the old sideways slide-out may point into the turned jig."""
    rec = HERE / "tests" / "v11_1plank_flip_waypoints.json"   # a whole recorded flip (record_flip.py) wins:
    wps = json.loads(rec.read_text(encoding="utf-8")).get("waypoints", []) if rec.exists() else []
    if len(wps) >= 2:                                          # first = the grab, last = above the guide
        pts = {"frame flip pick": wps[0], "frame flip above guide": wps[-1]}
    elif HAND.exists():
        pts = json.loads(HAND.read_text(encoding="utf-8")).get("points", {})
    else:
        return
    by = {s.get("name"): s for s in steps if "move" in s}

    def put(name, pose, seed):
        s = by.get(name)
        if s is None:
            return None
        q = tm5_kin.ik(list(pose), list(seed))
        if q is None:
            print(f"WARNING: hand_points: '{name}' can't be reached - left as it was")
            return None
        s["flange"], s["joints"] = [round(v, 4) for v in pose], [round(v, 4) for v in q]
        s.pop("planned_flange", None)
        return q

    if "frame flip pick" in pts and "frame flip pick" in by:
        P = pts["frame flip pick"]
        old = by["frame flip pick"]["flange"]
        put("frame flip pick", P["pose"], P["joints"])
        for n in ("frame flip pick approach", "frame flip pick out", "frame flip up"):
            if n in by:
                d = [by[n]["flange"][k] - old[k] for k in range(3)]
                put(n, [P["pose"][k] + d[k] for k in range(3)] + list(P["pose"][3:]), P["joints"])
        put("frame flip over pick", [P["pose"][0], P["pose"][1], P["pose"][2] + 100] + list(P["pose"][3:]),
            P["joints"])
        if len(wps) >= 3:                               # recorded point 2 = only its HEIGHT: straight up there
            put("frame flip up", list(P["pose"][:2]) + [wps[1]["pose"][2]] + list(P["pose"][3:]), P["joints"])
        steps[:] = [s for s in steps if s.get("name") != "frame flip turn 15"]
    if "frame flip above guide" in pts and "frame flip above guide" in by:
        A = pts["frame flip above guide"]
        old_place = by.get("frame flip place", {}).get("flange")
        put("frame flip above guide", A["pose"], A["joints"])
        place = [A["pose"][0], A["pose"][1], A["pose"][2] - 75] + list(A["pose"][3:])
        put("frame flip place", place, A["joints"])
        if old_place:
            hi = by.get("frame flip back up", {}).get("flange", [0, 0, place[2] + 193])[2]
            put("frame flip place out", place[:2] + [place[2] + 40] + place[3:], A["joints"])
            put("frame flip back up", place[:2] + [max(hi, place[2] + 193)] + place[3:], A["joints"])
    print(f"hand points: {sorted(pts)} set from {HAND.name}")


JFLIP_STEPS, JFLIP_LIFT_MM = 8, 300   # 2026-11-20 (Bjørge): flip in JOINT space, small even steps, high in the middle


def joint_flip(steps):
    """The frame flip as JFLIP_STEPS-1 joint moves ('frame flip j1..'), from the last flip move before
    'frame flip above guide' (turn 15, or 'frame flip up') to 'frame flip above guide': every joint turns evenly one
    way (J1 +17 -> -85 deg), at most ~19 deg per step, and each step is lifted JFLIP_LIFT_MM * sin(pi t) (IK, seeded
    from the previous step, so the arm keeps its setup) - no straight line through the wrist singularity, the frame
    kept high over the jigs. Only where the original 'frame flip turn 30..180' lines are not in the program."""
    names = [s.get("name") for s in steps]
    if "frame flip above guide" not in names or any(n and n.startswith("frame flip turn 3") for n in names):
        return
    b = names.index("frame flip above guide")
    a = max(i for i in range(b) if names[i] in ("frame flip up", "frame flip turn 15"))
    wfile = HERE / "tests" / "v11_1plank_flip_waypoints.json"       # recorded by hand (tests/record_flip.py)
    hand = json.loads(wfile.read_text(encoding="utf-8")).get("waypoints", []) if wfile.exists() else []
    if len(hand) >= 2:                                         # first = grab, 2nd = height of the lift (straight
        mid = hand[2:-1] if len(hand) >= 3 else []             # up, hand_points), last = above guide; between:
        new = [{**steps[a], "name": f"frame flip hand {k}", "move": "ptp", "flange": list(w["pose"]),
                "joints": list(w["joints"])} for k, w in enumerate(mid, 1)]
        steps[b]["move"] = "ptp"                               # the turn into 'above guide' = a JOINT move (J6
                                                               # turns ~180 deg; a line would hit the singularity)
        for n in new:
            n.pop("planned_flange", None)
        steps[b:b] = new
        print(f"hand flip: {len(new)} recorded joint moves between '{names[a]}' and 'frame flip above guide'")
        return
    A, B = np.array(steps[a]["joints"], float), np.array(steps[b]["joints"], float)
    new, prev = [], A
    for k in range(1, JFLIP_STEPS):
        t = k / JFLIP_STEPS
        p = list(tm5_kin.fk(list(A + (B - A) * t)))
        p[2] += JFLIP_LIFT_MM * np.sin(np.pi * t)
        q = tm5_kin.ik(p, list(prev))
        if q is None or not tm5_kin.within_limits(q):
            print(f"WARNING: joint flip step {k} unreachable - flip left as it is")
            return
        new.append({**steps[a], "name": f"frame flip j{k}", "move": "ptp",
                    "flange": [round(v, 4) for v in p], "joints": [round(v, 4) for v in q]})
        new[-1].pop("planned_flange", None)
        prev = np.array(q)
    steps[b:b] = new
    print(f"joint flip: {len(new)} joint moves between '{names[a]}' and 'frame flip above guide' "
          f"(lift {JFLIP_LIFT_MM} mm, max {np.abs(np.diff(np.array([A] + [n['joints'] for n in new] + [B], float), axis=0)).max():.0f} "
          "deg per step)")


FLIP_STEPS = 6              # 2026-11-20 (Bjørge): the 13 'frame flip turn' lines fought the robot after teaching
FLIP_LIFT_MM = 80            # extra height in the middle of the flip, for clearance


def simple_flip(steps):
    """Replace 'frame flip turn 15 .. 165' by FLIP_STEPS even steps from 'frame flip up' (taught pick side) to
    'frame flip turn 180' (taught place side): position straight between them + FLIP_LIFT_MM * sin(pi t) up, the
    rotation turned evenly the SAME way round as the original flip (checked against the original 'turn 90'),
    IK seeded from the previous step so the arm keeps one joint setup. Lines; a step whose joints jump > 40 deg
    is reported."""
    from scipy.spatial.transform import Rotation as Rot, Slerp
    names = [s.get("name") for s in steps]
    if "frame flip up" not in names or "frame flip turn 180" not in names:
        return
    a, b = names.index("frame flip up"), names.index("frame flip turn 180")
    old = steps[a + 1:b]
    ref90 = next((s for s in old if s.get("name") == "frame flip turn 90"), None)
    A, B = steps[a], steps[b]
    TA, TB = teach_overrides.pose_to_T(A["flange"]), teach_overrides.pose_to_T(B["flange"])
    rA, rB = Rot.from_matrix(TA[:3, :3]), Rot.from_matrix(TB[:3, :3])
    d = rB * rA.inv()                                   # base-frame rotation A -> B
    rv = d.as_rotvec()
    ang = np.linalg.norm(rv)
    paths = [rv]
    if ang > 1e-6:                                      # the other way round, same axis line
        paths.append(-rv / ang * (2 * np.pi - ang))
    def mid_err(v):
        if ref90 is None:
            return 0
        Rm = (Rot.from_rotvec(v * 0.5) * rA).as_matrix()
        R90 = teach_overrides.pose_to_T(ref90["flange"])[:3, :3]
        return Rot.from_matrix(Rm.T @ R90).magnitude()
    v = min(paths, key=mid_err)
    new, seed = [], A["joints"]
    for k in range(1, FLIP_STEPS):
        t = k / FLIP_STEPS
        R = (Rot.from_rotvec(v * t) * rA).as_matrix()
        p = (1 - t) * TA[:3, 3] + t * TB[:3, 3]
        p[2] += FLIP_LIFT_MM * np.sin(np.pi * t)
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = R, p
        pose = teach_overrides.T_to_pose(T)
        q = tm5_kin.ik(pose, seed)
        if q is None:
            raise SystemExit(f"simple flip: step {k}/{FLIP_STEPS} can't be reached")
        jump = max(abs(q[j] - seed[j]) for j in range(6))
        if jump > 40:
            print(f"WARNING: simple flip step {k}: a joint turns {jump:.0f} deg")
        tmpl = old[min(len(old) - 1, round(t * (len(old) - 1)))] if old else A
        new.append({**tmpl, "name": f"frame flip turn {round(180 * t)}", "move": "line",
                    "flange": [round(x, 4) for x in pose], "joints": [round(x, 4) for x in q]})
        new[-1].pop("planned_flange", None)
        seed = q
    jump = max(abs(B["joints"][j] - seed[j]) for j in range(6))
    if jump > 40:
        print(f"WARNING: simple flip into 'frame flip turn 180': a joint turns {jump:.0f} deg")
    steps[a + 1:b] = new
    print(f"simple flip: {len(old)} turn moves -> {len(new)} even steps "
          f"({np.degrees(np.linalg.norm(v)):.0f} deg in all, lift {FLIP_LIFT_MM} mm)")


ABOVE_INTERFACE_MM = 15      # 2026-11-20 (Bjørge, real robot): stop right above the interface, then the last push


def above_interface(steps):
    """Insert 'plank above interface' just before 'plank place': planned = the place pose ABOVE_INTERFACE_MM higher
    (robot base z), then its own taught correction if it has one (teach.py / step_run 'save' on that step).
    While 'plank place' itself is not taught, the place starts AT that (taught) above-interface pose - same position
    and rotation - so it is adjusted down from there and saved (Bjørge, 2026-11-20). The last push = place."""
    ev = (teach_overrides.load(VERSION) or {}).get("events", {}).get("plank place", {})
    place_taught = "plank place" in (ev.get("taught") or {})
    tip = np.eye(4)
    tip[2, 3] = TIP
    for i, s in enumerate(steps):
        if s.get("name") == "plank place" and "move" in s:
            planned = list(s["flange"])
            planned[2] += ABOVE_INTERFACE_MM
            T = np.linalg.inv(PLATE) @ teach_overrides.pose_to_T(planned) @ tip
            T2 = teach_overrides.apply("plank above interface", T, VERSION)
            pose = teach_overrides.T_to_pose(PLATE @ T2 @ np.linalg.inv(tip))
            q = tm5_kin.ik(pose, s["joints"])
            if q is None:
                raise SystemExit("'plank above interface' can't be reached")
            new = {**s, "name": "plank above interface", "flange": [round(v, 4) for v in pose],
                   "joints": [round(v, 4) for v in q], "speed": min(float(s.get("speed", 20)), 20.0),
                   "planned_flange": [round(v, 4) for v in planned]}
            steps.insert(i, new)
            if not place_taught:
                s["flange"], s["joints"] = list(new["flange"]), list(new["joints"])
            return
    print("WARNING: no 'plank place' move - 'plank above interface' not added")


def apply_teach(steps):
    """teach_v11_1plank.json (tests/robot_sim/teach.py v11_1plank ...) on the built moves, as v9's Program.move does:
    the TCP pose on the plate through teach_overrides.apply(name, T, VERSION), IK again seeded with the move's own
    joints. "planned_flange" = the pose before the teaching (after any jig move): teach.py shows offsets to it."""
    tip = np.eye(4)
    tip[2, 3] = TIP
    P_inv, n = np.linalg.inv(PLATE), 0
    for s in steps:
        if "move" not in s:
            continue
        s["planned_flange"] = list(s["flange"])
        T = P_inv @ teach_overrides.pose_to_T(s["flange"]) @ tip
        T2 = teach_overrides.apply(s["name"], T, VERSION)
        if T2 is T or np.allclose(T2, T, atol=1e-9):
            continue
        pose = teach_overrides.T_to_pose(PLATE @ T2 @ np.linalg.inv(tip))
        q = tm5_kin.ik(pose, s["joints"])
        if q is None:
            raise SystemExit(f"taught move '{s['name']}' can't be reached")
        s["flange"], s["joints"] = [round(v, 4) for v in pose], [round(v, 4) for v in q]
        n += 1
    return n


def segments(out):
    prog, cur = [], []
    for s in out["steps"]:
        if "move" in s:
            F = np.array(tm5_kin.pose_to_mat(s["flange"]))
            m = {"name": s["name"], "type": "PTP" if s["move"] == "ptp" else "Line",
                 "flange": [round(v, 3) for v in s["flange"]], "joints": [round(v, 4) for v in s["joints"]],
                 "tcp_xyz": [round(float(v), 3) for v in (F @ [0, 0, V10.TIP, 1])[:3]], "jig": s.get("jig")}
            m.update({"speed_pct": PTP_PCT} if m["type"] == "PTP" else {"speed_mm_s": s["speed"]})
            cur.append(m)
        elif s.get("gripper") in ("grip", "release"):
            prog.append({"segment": sum("segment" in p for p in prog) + 1, "moves": cur})
            g = s["gripper"] == "grip"
            prog.append({"gripper": "GRIP" if g else "RELEASE", "action": "close" if g else "open",
                         "parts": s.get("parts", [])})
            cur = []
    if cur:
        prog.append({"segment": sum("segment" in p for p in prog) + 1, "moves": cur})
    seg = {"cell": out["cell"], "names": out["names"], "source": out["source"], "jig_moves": out["jig_moves"],
           "pose_format": "flange = TM pose [X, Y, Z mm, Rx, Ry, Rz deg] of the FLANGE (tool 0, no TCP) in the robot "
                          f"base; tcp_xyz = closed fingertips (flange + {V10.TIP:.0f} mm along tool z), info only",
           "send_as": {"Line": 'Line("CAP", flange..., speed_mm_s, acc_ms, 0, false)',
                       "PTP": 'PTP("JPP", joints..., speed_pct, acc_ms, 0, false)'},
           "gripper_at_start": "open (RELEASE before the first segment)",
           "counts": {"moves": sum(len(p["moves"]) for p in prog if "segment" in p),
                      "segments": sum("segment" in p for p in prog),
                      "gripper_actions": sum("gripper" in p for p in prog)},
           "program": prog}
    SEG.write_text(json.dumps(seg, indent=1))
    c = seg["counts"]
    print(f"{SEG.name}: {c['moves']} moves in {c['segments']} segments, {c['gripper_actions']} gripper actions")


def check(moves_file=None, sim_names=False):
    """Own sim tools on tests/v11_1plank_moves.json: kin_check (reach, joint limits, Line followability), collision.py
    (fixtures + parts; each moved jig shifted in the cell together with what sits on it), cycle_time.py.
    techman link lengths (tm5_kin's default, the real robot) for reach and collisions."""
    import collision as C
    import cycle_time as CT
    import kin_check as KC
    from tmflow_export import load_program
    tm5_kin.use("techman")
    prog = load_program(str(OUT))
    stats, problems, _ = KC.check(prog, report=lambda *a, **k: None)
    KC.summary(stats)
    for p in problems:
        print("   ", p)
    cell = {n: v for n, v in C.load_cell(str(CELL_GLB)).items() if n not in DROPPED}
    shift = {}
    if moves_file:
        moves = sim_moves(moves_file, sim_names)
        for n, m in moves.items():
            T = np.array(m["T_move"])
            if not np.allclose(T, np.eye(4)):
                d = [*T[:3, 3], float(np.degrees(np.arctan2(T[1, 0], T[0, 0])))]
                for o in (n, *ON_JIG.get(n, ())):
                    if o in cell and (o == n or o not in moves):
                        shift[o] = d
        print("cell shifted (v9 object names):", {k: [round(float(v), 2) for v in d] for k, d in shift.items()})
    hits = C.check_program(prog, cell, 2.0, True, shift)
    for c in ("fixtures", "parts"):
        h = [x for x in hits if x["check"] == c]
        print(f"collisions {c}: {'free' if not h else f'{len(h)} moves collide'}")
        for x in h:
            print(f"    move #{x['move']} ({x['name']}, {x['context']}): "
                  f"{', '.join(sorted({f'{p}/{q}' for p, q in x['pairs']}))}")
    tm5_kin.use("robodk")                               # cycle_time.py's own setting
    tot = lambda ph: [sum(v[i] for v in ph.values()) for i in (0, 1)]      # noqa: E731
    ph, dist = CT.estimate(prog)
    stage, prev = {}, [0.0, 0.0]                        # per v9 stage: totals of growing prefixes, differenced
    for st in sorted({x.get("stage") for x in prog["steps"] if x.get("stage")}):
        n = max(i for i, x in enumerate(prog["steps"]) if x.get("stage") == st) + 1
        t = tot(CT.estimate({**prog, "steps": prog["steps"][:n]})[0])
        stage[st], prev = [t[0] - prev[0], t[1] - prev[1]], t
    print(f"cycle time: {tot(ph)[0]:.1f} s programmed, {tot(ph)[1]:.1f} s with TMflow ramps (Line path {dist:.2f} m); "
          "per stage (1 plank, 2 small half A->B, 3 big half A->B, 4 flip frame, 5 big half back, 6 small half back, "
          "7 bench to AMR + home): " + ", ".join(f"{k} {v[0]:.1f}/{v[1]:.1f}" for k, v in stage.items()))
    bad = stats["limit"] + stats["line_fail"] + stats["line_posture"] + stats["limit_path"] + stats["j5_flip_line"]
    return bad, hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("moves", nargs="?", help="jig_vision.py --save output (moves.json), v11 jig names")
    ap.add_argument("--sim-names", action="store_true", help="the moves file uses v9/v10 names (A/B swapped)")
    ap.add_argument("--check", action="store_true", help="also run reach, collision and cycle-time checks")
    a = ap.parse_args()
    build(a.moves, a.sim_names)
    if a.check:
        bad, hits = check(a.moves, a.sim_names)
        raise SystemExit(1 if bad or hits else 0)
