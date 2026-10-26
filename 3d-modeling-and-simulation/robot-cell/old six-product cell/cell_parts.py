"""Parts and poses for the robot cell (demonstrator scale, insert_draft.py with DEMO = True).

Every product is a list of instances: (name, unique part, pose in product coordinates).
The unique parts are exported once to parts/ as STEP (for Fusion) and STL (for RoboDK);
a pose is a 4x4 matrix (mm) that puts the part's own coordinates into the product.

    python "robot_cell/old six-product cell/cell_parts.py"   -> writes parts/<code>.step / .stl next to it
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE.parent.parent / "Furniture concepts"))   # insert_draft, furniture

import insert_draft as d  # noqa: E402
from build123d import Location, Plane, Pos, Rot, export_step, export_stl, mirror  # noqa: E402

PARTS_DIR = HERE / "parts"


def mat(loc):
    """build123d Location -> 4x4 numpy matrix."""
    t = loc.wrapped.Transformation()
    m = np.eye(4)
    for r in range(3):
        for c in range(4):
            m[r, c] = t.Value(r + 1, c + 1)
    return m


def detached(part):
    """The part's solid on its own (a child of an assembly won't export to STEP by itself)."""
    s = part.solids()[0]
    s.label, s.color = part.label, part.color
    return s


# %% Unique parts (own coordinates = the left / assembled product coordinates)
def unique_parts():
    return {
        "S1L": d.S1B,                                  # side frame, left
        "S1R": mirror(d.S1B, Plane.YZ),                # side frame, right (mirror image)
        "S5L": d.S5,                                   # back post, left
        "S5R": mirror(d.S5, Plane.YZ),
        "S6L": d.S6,                                   # ornament
        "S6R": mirror(d.S6, Plane.YZ),
        "W2": d.plank(d.LP),                           # chair plank
        "W1": d.plank(d.BENCH_LP),                     # bench plank
        "S3": d.rod(d.BENCH - 2 * d.TUBE),             # bench stretcher rod (locked position)
        "S4": detached(d.planter("P1").children[0]),   # planter corner post (the one at the origin)
    }


# %% Products: instance name -> (unique part, pose in product coordinates)
ROD_Y, ROD_Z = d.ROD_C
ROD_BEFORE_TURN = mat(Pos(0, ROD_Y, ROD_Z) * Rot(90, 0, 0) * Pos(0, -ROD_Y, -ROD_Z))


SIDES = ("front", "right", "rear", "left")


def planter_xf(code):
    """P1 / P2: the four sides as transforms of the front wall (insert_draft.planter), and the
    outer size X x Y. Post k = side k's transform applied to the post at the origin (pinwheel)."""
    span_x = d.DEPTH if code == "P1" else d.LONG_SPAN
    X, Y = span_x + 2 * d.POST, d.DEPTH + 2 * d.POST
    xf = [Location(), Pos(X, 0, 0) * Rot(0, 0, 90), Pos(X, Y, 0) * Rot(0, 0, 180), Pos(0, Y, 0) * Rot(0, 0, 270)]
    return X, Y, [span_x, d.DEPTH, span_x, d.DEPTH], xf


def product(code):
    """Instances of C1 / C2 (chair, ornaments / back), B1 / B2 (bench), P1 / P2 (planter).
    Returns (outer width along x, {instance: (unique part, 4x4 pose)})."""
    if code.startswith("P"):
        X, Y, spans, xf = planter_xf(code)
        p = {f"S4_{k}": ("S4", mat(xf[k])) for k in range(4)}
        for k, side in enumerate(SIDES):
            w = "W2" if spans[k] == d.DEPTH else "W1"
            for i, loc in enumerate(d.wall_locs()):
                p[f"{side}{i + 1}"] = (w, mat(xf[k] * loc))
        return X, p
    width, w = (d.WIDTH, "W2") if code[0] == "C" else (d.BENCH, "W1")
    p = {"S1L": ("S1L", np.eye(4)), "S1R": ("S1R", mat(Pos(width, 0, 0)))}
    if code[0] == "B" and d.ROD:                      # no stretcher rod on the prototype
        p["S3"] = ("S3", np.eye(4))
    for i, loc in enumerate(d.seat_locs()):
        p[f"seat{i + 1}"] = (w, mat(loc))
    if code[1] == "2":                                  # back
        p["S5L"] = ("S5L", np.eye(4))
        p["S5R"] = ("S5R", mat(Pos(width, 0, 0)))
        for i, loc in enumerate(d.back_locs()):
            p[f"back{i + 1}"] = (w, mat(loc))
    else:                                               # ornaments in the sockets
        p["S6L"] = ("S6L", np.eye(4))
        p["S6R"] = ("S6R", mat(Pos(width, 0, 0)))
    return width, p


# Numbers the cell needs (product coordinates, mm)
DIMS = dict(TUBE=d.TUBE, IN=d.IN, T=d.T, W=d.W, TOP=d.TOP, Z0=d.Z0, DEPTH=d.DEPTH, P=d.P,
            PEG_L=d.PEG_L, PEG_C=d.PEG_C, ROD_C=d.ROD_C, BACK_LEN=d.BACK_LEN,
            BACK_XF=mat(d.BACK_XF), W1_EXTRA=d.W1_H - d.T, POST=d.POST, POST_H=d.POST_H,
            ORN_H=d.ORN_H, ORN_T=d.ORN_T)


if __name__ == "__main__":
    PARTS_DIR.mkdir(exist_ok=True)
    for code, part in unique_parts().items():
        export_step(part, str(PARTS_DIR / f"{code}.step"))
        export_stl(part, str(PARTS_DIR / f"{code}.stl"), tolerance=0.02, angular_tolerance=0.2)
        bb = part.bounding_box()
        print(f"{code:4s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm  -> parts/{code}.step/.stl",
              flush=True)
