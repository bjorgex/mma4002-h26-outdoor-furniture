"""Build the cell model: every object (table, plate, jigs, bench parts at their start) as one mesh in the robot
base frame -> design/cell.glb + design/cell_layout.json (what the judge loads).

    ./py design/build_cell.py

This is the v3 cell. Change the constants below (or the jig meshes in design/meshes/jig/, made by
design/cad/jig_parts.py) to change the layout or the jigs. The bench parts' meshes (design/meshes/bench/) and how the
bench goes together (ASM, from design/meshes/bench/assembly.json) are the product: they must not change.

Frames: everything is placed on the "ground base" frame G = WORK_FRAME * GROUND_IN_WORK (x away from the robot
along the plate, y to the left, z up, the plate's top face at z = 0); WORK_FRAME is the plate as measured on the
real robot (fixed). Robot base frame: the robot stands at the origin, the plate lies at x < 0 (x -206 .. -796 mm).
Object kinds (cell_layout.json "kind"): table, plate, jig (fixtures), marker (ignored by the checks), amr, and the
parts frame, piece, plank, guide (they can be gripped and moved; the guide is a jig part the robot moves).
"""
import json
import math
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
JIG, BENCH = HERE / "meshes" / "jig", HERE / "meshes" / "bench"


def transl(x, y, z):
    T = np.eye(4)
    T[:3, 3] = (x, y, z)
    return T


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])


pi = math.pi

# ------------------------------------------------------------------ fixed (not up to the design)
WORK_FRAME = np.array([[-1.0, 0.00042, 0.00116, -206.43707], [-0.00042, -1.0, -0.00047, 152.98623],
                       [0.00116, -0.00047, 1.0, -4.46049], [0.0, 0.0, 0.0, 1.0]])
GROUND_IN_WORK = transl(0, -67, 15)
GROUND_SIZE = (590, 440, 15)                 # ground base plate x (away from the robot) x y x thickness
TABLE_H = 750                                # floor below the table top
TIP = 160.0                                  # flange -> closed fingertips (the tcp)
EGP = [((-47, -45, 0), (47, 45, 123)), ((-9, -4, 123), (-6, 4, TIP)), ((6, -4, 123), (9, 4, TIP))]   # gripper boxes
AMR_GAP, AMR_PLATE = 150, (300, 320)         # the AMR stands past the far edge of the plate
# the bench (STEP coordinates -> base-local of a frame pocket) and the flip that puts frame 1 + planks onto frame 2
T_IN = transl(-2.715, -21.877, 134.5) @ rotx(pi / 2)
FLIP = transl(0, 0, 269) @ rotx(pi)

# ------------------------------------------------------------------ the layout (v3)
RISER_A, RISER_B = 10, 80                    # base B raised 70 mm (iter 02): the wrist camera clears the plate
                                             # when the guide is gripped from above at base B
BASE_A, BASE_B = transl(480, 120, RISER_A), transl(230, 320, RISER_B)    # frame 1 pocket, frame 2 pocket
                                             # (B2 iter 11: base B x 480 -> 280, release on the J5 < 0 branch)
PLANK_JIG, PITCH = transl(295, 130, 0), 30   # plank jig: 2 rows of 3 slots, 30 mm apart (iter 03: y 190 -> 130,
                                             # out from under the forearm reaching to base B; iter 26: x 150 -> 250,
                                             # closer to base A; B2 iter 03: x 250 -> 295, ~5 mm from base A)
PLANK_ROW_YAW = (0, 80)                      # iter 27: row-1 slots (planks 4-6) turned 80 deg as they sit in frame 1
PLANK_FLOOR = 0                            # plank bottoms stand on the plate (through slots)
PLANK_SLOT = {1: 2, 2: 1, 3: 3, 4: 4, 5: 5, 6: 6}    # plank k starts in jig slot n (iter 05: plank1 <-> plank2, so
                                             # picks go outer-first while places in the guide go robot-side-last)
GUIDE_START = BASE_B @ transl(0, 0, 80) @ rotx(pi)   # the double-sided guide starts flipped onto base B

# grips the v3 program uses (TCP pose in the part's / jig's own coordinates) - for your own program generator
PLANK_GRIP = np.array([[0, -1, 0, 0], [0, 0, -1, 110], [1, 0, 0, 2.5], [0, 0, 0, 1.0]])     # plank coordinates
PLANK_PUSH = np.array([[0, -1, 0, 0], [0, 0, -1, 125], [1, 0, 0, 2.5], [0, 0, 0, 1.0]])     # pushed home
GUIDE_GRIP = np.array([[0, 0, 1, -72], [0, -1, 0, -70], [1, 0, 0, 40], [0, 0, 0, 1.0]])    # guide (= base A) coords
_C, _S = math.cos(math.atan2(1.75, 10)), math.sin(math.atan2(1.75, 10))
FOOT_GRIP = np.array([[_C, _S, 0, 60.8], [_S, -_C, 0, -96.7], [0, 0, -1, 12], [0, 0, 0, 1.0]]) @ rotx(pi / 3)  # base A


def ground():
    """The ground base frame in robot base coordinates."""
    return WORK_FRAME @ GROUND_IN_WORK


def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)])
    b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)])
    return b


def objects():
    """[(name, kind, mesh in its own coordinates, pose in ground base coordinates, colour)]"""
    asm = {p["name"]: np.array(p["pose"], float) for p in json.loads((BENCH / "assembly.json").read_text())["parts"]}
    stl = trimesh.load_mesh
    sx, sy, st = GROUND_SIZE
    grey, wood, frame_c, red = [0.6, 0.6, 0.62, 1], [0.75, 0.55, 0.3, 1], [0.55, 0.62, 0.75, 1], [0.85, 0.1, 0.1, 1]
    jig_c, guide_c = [0.35, 0.55, 0.85, 1], [0.95, 0.75, 0.2, 1]
    I = np.eye(4)
    out = [("Table", "table", box((-350, -60, -TABLE_H), (sx + 10, sy + 60, -st)), I, [0.78, 0.74, 0.68, 1]),
           ("Ground base plate", "plate", stl(JIG / "ground_base.stl"), I, [0.82, 0.8, 0.74, 1])]
    for i, (qx, qy) in enumerate(((3, 3), (sx - 28, 3), (3, sy - 28), (sx - 28, sy - 28)), 1):
        out.append((f"Vision square {i}", "marker", stl(JIG / "vision_square.stl"), transl(qx, qy, 0), red))
    for name, base, f, riser in (("Base A", BASE_A, "base_a", RISER_A), ("Base B", BASE_B, "base_b", RISER_B)):
        out.append((f"{name} riser", "jig", box((-90, -90, -riser), (90, 90, 0)), base, grey))
        out.append((name, "jig", stl(JIG / f"{f}.stl"), base, jig_c))
    out.append(("Plank jig", "jig", stl(JIG / "plank_jig.stl"), PLANK_JIG, jig_c))
    amr = transl(sx + AMR_GAP, sy / 2 - AMR_PLATE[1] / 2, 0)
    out.append(("AMR plate", "amr", box((0, 0, -10), (AMR_PLATE[0], AMR_PLATE[1], 0)), amr, [0.4, 0.75, 0.45, 1]))
    out.append(("AMR top module", "amr", box((40, 40, 383 - TABLE_H - st), (AMR_PLATE[0] - 40, AMR_PLATE[1] - 40, -10)),
                amr, [0.85, 0.85, 0.88, 1]))
    frame, piece, plank = stl(BENCH / "frame.stl"), stl(BENCH / "interface_piece.stl"), stl(BENCH / "plank_body.stl")
    out.append(("frame1", "frame", frame, BASE_A @ T_IN @ asm["frame1"], frame_c))
    out.append(("frame2", "frame", frame, BASE_B @ FLIP @ T_IN @ asm["frame2"], frame_c))
    for k in range(1, 7):
        P = T_IN @ asm[f"plank{k}"]
        out.append((f"piece A{k}", "piece", piece, BASE_A @ P, red))
        out.append((f"piece B{k}", "piece", piece, BASE_B @ FLIP @ P @ rotz(pi), red))
        row, col = divmod(PLANK_SLOT[k] - 1, 3)
        start = (PLANK_JIG @ transl(PITCH * (col + 0.5), PITCH * (row + 0.5), 0) @ rotz(math.radians(PLANK_ROW_YAW[row]))
                 @ transl(0, 2.5, 125 + PLANK_FLOOR) @ rotx(pi / 2))
        out.append((f"plank{k}", "plank", plank, start, wood))
    out.append(("Guide", "guide", stl(JIG / "guide.stl"), GUIDE_START, guide_c))
    return out


def main():
    G = ground()
    scene, info = trimesh.Scene(), []
    for name, kind, mesh, pose, colour in objects():
        m = G @ pose
        mesh = mesh.copy()
        mesh.apply_transform(m)
        mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=colour, metallicFactor=0.0, roughnessFactor=0.8))
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        info.append({"name": name, "kind": kind, "colour": colour, "pose": np.round(m, 4).tolist()})
    (HERE / "cell.glb").write_bytes(scene.export(file_type="glb"))
    (HERE / "cell_layout.json").write_text(json.dumps(
        {"source": "design/build_cell.py", "units": "mm, robot base frame (z up)", "tip_mm": TIP, "egp": EGP,
         "table_h": TABLE_H, "ground_base_in_robot_base": np.round(G, 5).tolist(), "objects": info}, indent=1))
    print(f"{len(info)} objects -> design/cell.glb ({(HERE / 'cell.glb').stat().st_size / 1e3:.0f} kB), cell_layout.json")


if __name__ == "__main__":
    main()
