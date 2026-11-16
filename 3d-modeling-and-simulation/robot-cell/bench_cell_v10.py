"""Bench V1 cell, version 10 (v10): v9's program (tests/v9_moves.json) moved to where the camera found the jigs.

    python bench_cell_v10.py tests/vision_lab/moves.json     jig_vision.py --save output -> tests/v10_moves.json
    python bench_cell_v10.py                                 no moves file: v10 = v9 (all jigs where they were taught)
    then in the mock page: scenario "v10-full"

Each grab and release belongs to the jig under the tool tip there (flange + 160 mm along tool z, in the jigs' CAD
footprints tests/vision_lab/jig_boxes_v9.json + MARGIN): the jig the part is taken from or put into. Every move follows
the jig of its NEAREST grab/release in the program: the first half of the moves after an event go with that event's
jig, the second half with the next event's (approach, insert, slide-out and lift all stay with the part's jig, even
where the tool leaves the footprint). new flange = T_move @ flange. The guide halves sit in Base B at the start and
are moved with it; the planks and frames sit in the rack and the bases. Home and the turn point never move. Joints
are solved again (tm5_kin.ik, seeded with v9's joints). A target that can't be reached stops the build: no program
with a gap in it.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE / "tests" / "robot_sim"))
import tm5_kin  # noqa: E402

SRC, OUT = HERE / "tests" / "v9_moves.json", HERE / "tests" / "v10_moves.json"
BOXES = HERE / "tests" / "vision_lab" / "jig_boxes_v9.json"
TIP = json.loads((HERE / "bench_layout.json").read_text(encoding="utf-8"))["tip_mm"]
CARRIERS = ("Plank rack", "Base A", "Base B")          # what parts sit in; the guides ride on Base B
FREE = ("Home", "back to middle")                     # never moved: the start/end pose and the turn point
MARGIN = 15.0                                          # mm around a footprint that still counts as on it


def jig_of(tip, boxes):
    """The carrier whose footprint (xy, + MARGIN) holds the tool tip; the nearest centre if two do."""
    hits = [n for n in CARRIERS if all(boxes[n]["box_min"][i] - MARGIN <= tip[i] <= boxes[n]["box_max"][i] + MARGIN
                                       for i in (0, 1))]
    c = lambda n: (np.add(boxes[n]["box_min"], boxes[n]["box_max"]) / 2)[:2]        # noqa: E731
    return min(hits, key=lambda n: np.linalg.norm(c(n) - tip[:2])) if hits else None


def build(moves_file=None):
    src = json.loads(SRC.read_text())
    boxes = json.loads(BOXES.read_text())["jigs"]
    found = json.loads(Path(moves_file).read_text())["moves"] if moves_file else {}
    T = {n: np.array(found[n]["T_move"]) if n in found else np.eye(4) for n in CARRIERS}
    missing = [n for n in CARRIERS if n not in found]
    for g in ("Guide small", "Guide big"):              # check the guides really sit where Base B says
        if g in found and "Base B" in found:
            p = [*boxes[g]["pivot"], 1]
            d = np.linalg.norm((np.array(found[g]["T_move"]) @ p)[:3] - (T["Base B"] @ p)[:3])
            if d > 2:
                print(f"WARNING: {g} is {d:.1f} mm from where Base B's move puts it - is it seated in the base?")
    seq = src["steps"]
    tips = [(np.array(tm5_kin.pose_to_mat(x["flange"])) @ [0, 0, TIP, 1])[:3] if "move" in x else None for x in seq]
    anchors = []                                        # (step index, jig) of every grab / release
    for i, x in enumerate(seq):
        if x.get("gripper") in ("grip", "release"):
            last = next((k for k in range(i - 1, -1, -1) if tips[k] is not None), None)
            anchors.append((i, jig_of(tips[last], boxes) if last is not None else None))

    def jig_for(i):
        before = [a for a in anchors if a[0] < i]
        after = [a for a in anchors if a[0] > i]
        if not before or not after:
            return (after or before)[0 if after else -1][1]
        a, b = before[-1], after[0]
        moves = [k for k in range(a[0] + 1, b[0]) if tips[k] is not None]
        return a[1] if moves.index(i) < len(moves) / 2 else b[1]

    steps, prev, used, worst = [], None, {}, 0.0
    for i, st in enumerate(seq):
        st = dict(st)
        if "move" in st:
            F = np.array(tm5_kin.pose_to_mat(st["flange"]))
            j = None if st["name"].startswith(FREE) else (jig_for(i) or jig_of(tips[i], boxes))
            if j is not None and not np.allclose(T[j], np.eye(4)):
                F2 = T[j] @ F
                pose = [float(v) for v in tm5_kin.mat_to_pose(F2.tolist())]
                q = tm5_kin.ik(pose, st["joints"])        # v9's own joints: same configuration, same J6 turn
                if q is None:
                    raise SystemExit(f"move '{st['name']}' (on {j}) can't be reached after the jig move")
                worst = max(worst, max(abs(a - b) for a, b in zip(q, st["joints"])))
                st["flange"], st["joints"] = [round(v, 4) for v in pose], [round(v, 4) for v in q]
            st["jig"] = j
            used[j] = used.get(j, 0) + 1
            prev = st["joints"]
        steps.append(st)
    out = {**{k: v for k, v in src.items() if k != "steps"}, "cell": "v10",
           "source": f"bench_cell_v10.py: v9_moves.json + {Path(moves_file).name if moves_file else 'no jig moves'}",
           "jig_moves": {n: {"x": round(float(T[n][0, 3]), 3), "y": round(float(T[n][1, 3]), 3),
                             "rz_deg": round(float(np.degrees(np.arctan2(T[n][1, 0], T[n][0, 0]))), 3)} for n in CARRIERS},
           "steps": steps}
    OUT.write_text(json.dumps(out, indent=1))
    print(f"{OUT.name}: {sum('move' in s for s in steps)} moves; per jig {used}; largest joint change {worst:.2f} deg")
    if missing and moves_file:
        print(f"not in the moves file (left where taught): {', '.join(missing)}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("moves", nargs="?", help="jig_vision.py --save output (moves.json)")
    build(ap.parse_args().moves)
