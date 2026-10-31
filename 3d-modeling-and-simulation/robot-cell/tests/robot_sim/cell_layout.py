"""The version-4 bench cell ("Bench V1 cell v4") as web meshes in the robot base frame, for sim_view.html.

    python robot_cell/tests/robot_sim/cell_layout.py              (shared venv: robodk's robomath + trimesh)
    python robot_cell/tests/robot_sim/cell_layout.py --cell v5    v5 start: the guide on base A (bench_cell_v5.py)

No RoboDK and no .rdk needed: this repeats bench_cell_v4.py's build() - the script the station is built
from - with the same meshes and poses: the STLs in jig_parts/ (jig_parts.py, jig_parts_v4.py) and
benchV1_parts/ (bench_parts.py, from BenchInterfaceV1.STEP), BASE_A/B, PLANK_JIG, PAD, GUIDE_ON_B, T_IN,
FLIP, AMR_AT, the table/riser/AMR boxes, all under the frame "Ground base" = bench_layout.json's work
frame (plate corners logged on our robot) * GROUND_IN_WORK. Imports bench_cell_v4 for its constants only
(build(), which talks to RoboDK, is not called). Parts are at their start positions: planks in the plank
jig, frame 1 + pieces in base A, frame 2 + pieces and the guide on base B.
Out: cell.glb (one node per object, named as in the station, mm, robot base frame) and cell_layout.json
(the same objects: name, colour, pose, STL bounds); --cell v5: cell_v5.glb and cell_layout_v5.json, the same
cell with the guide's halves starting on base A (bench_cell_v5.GUIDE_ON_A: v4 after its stage 1).
The mock's 3D pane loads the one named by the scenario's "cell" (tests/scenarios.json).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
CELL = HERE.parents[1]
sys.path.insert(0, str(CELL))
import bench_cell_v4 as v4                                # noqa: E402
import bench_cell_v5 as v5                                # noqa: E402  (same constants, the guide starts on A)
from robodk.robomath import Mat, eye, pi, rotx, rotz, transl   # noqa: E402


def to_np(m):
    return np.array([[m[i, j] for j in range(4)] for i in range(4)])


def main(cell="v4"):
    v = v5 if cell == "v5" else v4
    guide = v4.BASE_A * v5.GUIDE_ON_A if cell == "v5" else v4.BASE_B * v4.GUIDE_ON_B
    glb, layout = ("cell_v5.glb", "cell_layout_v5.json") if cell == "v5" else ("cell.glb", "cell_layout.json")
    asm = {p["name"]: Mat(p["pose"]) for p in json.loads((v4.PARTS / "assembly.json").read_text())["parts"]}
    gb = Mat(v4.LAYOUT["work_frame"]) * v4.GROUND_IN_WORK          # ground base in robot base coordinates
    sx, sy, st = v4.GROUND_SIZE
    scene, info = trimesh.Scene(), []

    def add(name, kind, mesh, pose, colour):
        mesh = mesh.copy()
        mesh.apply_transform(to_np(gb * pose))
        mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=colour, metallicFactor=0.0, roughnessFactor=0.8))
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        m = gb * pose
        info.append({"name": name, "kind": kind, "colour": colour,
                     "pose": [[round(m[i, j], 4) for j in range(4)] for i in range(4)]})

    def stl(path):
        return trimesh.load_mesh(path)

    def box(lo, hi):
        b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)])
        b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)])
        return b

    # colours as in bench_cell_v4.build()
    grey, wood, frame_c, red = [0.6, 0.6, 0.62, 1], [0.75, 0.55, 0.3, 1], [0.55, 0.62, 0.75, 1], [0.85, 0.1, 0.1, 1]
    jig_c, guide_c = [0.35, 0.55, 0.85, 1], [0.95, 0.75, 0.2, 1]
    add("Table", "table", box((-350, -10, -v4.TABLE_H), (sx + 10, sy + 60, -st)), eye(4), [0.78, 0.74, 0.68, 1])
    add("Ground base plate", "plate", stl(v4.JIG / "ground_base_split.stl"), eye(4), [0.82, 0.8, 0.74, 1])
    for i, (qx, qy) in enumerate(((3, 3), (sx - 28, 3), (3, sy - 28), (sx - 28, sy - 28)), 1):
        add(f"Vision square {i}", "marker", stl(v4.JIG / "vision_square.stl"), transl(qx, qy, 0), red)
    for name, base, f, riser in (("Base A", v4.BASE_A, "base_a", v4.RISER_A), ("Base B", v4.BASE_B, "base_b", v4.RISER_B)):
        add(f"{name} riser", "jig", box((-90, -90, -riser), (90, 90, 0)), base, grey)
        add(name, "jig", stl(v4.JIG / f"{f}.stl"), base, jig_c)
    add("Plank jig", "jig", stl(v4.JIG / "plank_jig.stl"), v4.PLANK_JIG, jig_c)
    add("Parking pad", "jig", stl(v4.JIG / "parking_pad.stl"), v4.PAD, grey)
    add("AMR plate", "amr", box((0, 0, -10), (v4.AMR_PLATE[0], v4.AMR_PLATE[1], 0)), v4.AMR_AT, [0.4, 0.75, 0.45, 1])
    add("AMR top module", "amr", box((40, 40, 383 - v4.TABLE_H - st), (v4.AMR_PLATE[0] - 40, v4.AMR_PLATE[1] - 40, -10)),
        v4.AMR_AT, [0.85, 0.85, 0.88, 1])

    frame, piece, plank = stl(v4.PARTS / "frame.stl"), stl(v4.PARTS / "interface_piece.stl"), stl(v4.PARTS / "plank_body.stl")
    add("frame1", "frame", frame, v4.BASE_A * v4.T_IN * asm["frame1"], frame_c)
    add("frame2", "frame", frame, v4.BASE_B * v4.FLIP * v4.T_IN * asm["frame2"], frame_c)
    for k in range(1, 7):
        P = v4.T_IN * asm[f"plank{k}"]
        add(f"piece A{k}", "piece", piece, v4.BASE_A * P, red)
        add(f"piece B{k}", "piece", piece, v4.BASE_B * v4.FLIP * P * rotz(pi), red)
        row, col = divmod(k - 1, 3)
        start = v4.PLANK_JIG * transl(v4.PITCH * (col + 0.5), v4.PITCH * (row + 0.5) + 2.5, 125) * rotx(pi / 2)
        add(f"plank{k}", "plank", plank, start, wood)
    add("Guide inner", "guide", stl(v4.JIG / "guide_inner.stl"), guide, [0.95, 0.6, 0.15, 1])
    add("Guide outer", "guide", stl(v4.JIG / "guide_outer.stl"), guide, guide_c)

    (HERE / glb).write_bytes(scene.export(file_type="glb"))
    (HERE / layout).write_text(json.dumps(
        {"source": f"{v.__name__}.py build() poses + bench_layout.json work frame; meshes jig_parts/, benchV1_parts/",
         "station": v.STATION,
         "units": "mm, robot base frame (z up)", "tip_mm": v4.TIP, "egp": v4.EGP, "table_h": v4.TABLE_H,
         "objects": info}, indent=1))
    print(f"{len(info)} objects -> {glb} ({(HERE / glb).stat().st_size / 1e3:.0f} kB), {layout}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cell", choices=["v4", "v5"], default="v4", help="v4 (default): guide on base B; v5: on base A")
    main(ap.parse_args().cell)
