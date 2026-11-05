"""Offline check of what the mock's 3D pane carries: replays <cell>_moves.json's grips and releases on the
cell's .glb (the start state the pane loads) and, at every grip, measures how far the fingertips are from the
parts the station attaches (their boxes, as sim_scene.js measures) - so a wrong start state (e.g. v4's cell.glb under v5's moves) shows up as grips
in empty air.

    python robot_cell/tests/robot_sim/carry_check.py --cell v5      (shared venv: trimesh + robodk's robomath)

Parts follow the flange between a grip and its release (as sim_scene.js does: attached to the flange where
they are). Fingertips: flange * (0, 0, TIP - 10), as sim_scene.js's tipWorld(). A grip passes when the
nearest of the parts it names is within LIMIT mm of the tip (sim_scene.js's GRAB_MM) and all are in the .glb.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import trimesh
from robodk.robomath import Techman_2_Pose

HERE = Path(__file__).resolve().parent
TIP, LIMIT = 160, 40                                     # sim_scene.js TIP, GRAB_MM


def to_np(m):
    return np.array([[m[i, j] for j in range(4)] for i in range(4)])


def box_dist(mesh, p):
    """Distance from p to the mesh's axis-aligned box (0 inside), as three.js Box3.distanceToPoint in sim_scene.js."""
    lo, hi = mesh.vertices.min(axis=0), mesh.vertices.max(axis=0)
    return float(np.linalg.norm(np.maximum(0, np.maximum(lo - p, p - hi))))


def main(cell, glb=None):
    glb = Path(glb) if glb else HERE / ("cell_v5.glb" if cell == "v5" else "cell.glb")
    moves = json.loads((HERE.parent / f"{cell}_moves.json").read_text())["steps"]
    scene = trimesh.load(glb)
    meshes = {}                                          # node name (as in the station) -> world mesh now
    for node in scene.graph.nodes_geometry:
        T, g = scene.graph[node]
        m = scene.geometry[g].copy()
        m.apply_transform(T)
        meshes[node] = m
    flange, held, bad, n = None, [], 0, 0
    for s in moves:
        if "move" in s:
            flange = to_np(Techman_2_Pose(s["flange"]))
            continue
        if s["gripper"] == "grip":
            n += 1
            tip = (flange @ [0, 0, TIP - 10, 1])[:3]
            d = {p: box_dist(meshes[p], tip) if p in meshes else None for p in s["parts"]}
            missing = [p for p, v in d.items() if v is None]
            near = min((v for v in d.values() if v is not None), default=None)
            ok = not missing and near is not None and near <= LIMIT
            bad += not ok
            first = ", ".join(s["parts"][:3]) + (f" + {len(s['parts']) - 3}" if len(s["parts"]) > 3 else "")
            print(f"stage {s['stage']} grip {first}: tip {np.round(tip).astype(int).tolist()}, nearest named part "
                  f"{'-' if near is None else f'{near:.1f} mm'}{'  MISSING ' + str(missing) if missing else ''}"
                  f"  {'ok' if ok else 'FAR'}")
            held = [(p, np.linalg.inv(flange)) for p in s["parts"] if p in meshes]
        elif s["gripper"] == "release":
            for p, inv in held:
                meshes[p].apply_transform(flange @ inv)
            held = []
    print(f"{cell} moves on {glb.name}: {n} grips, {bad} not at the parts")
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cell", choices=["v4", "v5"], default="v5")
    ap.add_argument("--glb", help="another start state (default: the cell's own .glb)")
    a = ap.parse_args()
    raise SystemExit(1 if main(a.cell, a.glb) else 0)
