"""Planter with every wall plank on the OUTSIDE of the tube frame (chosen layout B, now in
furniture.py; A pinwheel was dropped 2026-10-15).

    B  open corners  each wall covers exactly its own frame face, corners left open (28 x 28,
                     the steel corner shows). Mirror-symmetric across both diagonals.
                     W2 = 510 = frame span, W1 = 1500 (unchanged): the floor fits exactly between
                     the frames, walls run full height (4 rows, z 6..416), fixing 25 mm from both
                     plank ends as before.
A plastic/metal insert holds the soil.

Top view: P1 is 566 x 566. Run:  python planter_options.py
"""

# %% Setup
from build123d import *
from furniture import DEPTH, MIN3, N_SEAT, P, T, TUBE, W, paint, show_row, side_frame

Y0, Y1 = -TUBE, DEPTH + TUBE  # frame core in y: -50..460 (510)
SPAN = Y1 - Y0               # 510


def board(code, x, y, z, sx, sy, sz):
    """Axis-aligned plank, min corner (x, y, z), size (sx, sy, sz)."""
    names = {"W1": "W1 plank long", "W2": "W2 plank short"}
    return paint(Pos(x, y, z) * Box(sx, sy, sz, align=MIN3), names[code])


def frames(lf):
    left = side_frame(False, holes=False)
    return [left, paint(Pos(lf, 0, 0) * mirror(side_frame(False, holes=False), Plane.YZ), left.label)]


def floor(lf, code):
    return [board(code, 0, i * P, TUBE, lf, W, T) for i in range(N_SEAT)]


def open_corners(lf, code_x, name):
    """Frames' outer faces at x = 0 and lf; every wall exactly covers its own frame face."""
    parts = frames(lf) + floor(lf, code_x)
    for i in range(4):
        z = 6 + i * P                                                      # 4 rows, z 6..416
        parts += [board(code_x, 0, Y0 - T, z, lf, T, W),                   # front
                  board(code_x, 0, Y1, z, lf, T, W),                       # rear
                  board("W2", -T, Y0, z, T, SPAN, W),                      # left
                  board("W2", lf, Y0, z, T, SPAN, W)]                      # right
    return Compound(children=parts, label=name)


options = {
    "B P1 open corners (W2 510)": open_corners(SPAN, "W2", "B P1 open corners (W2 510)"),
    "B P2 open corners (W1 1500)": open_corners(1500, "W1", "B P2 open corners (W1 1500)"),
}

# %% Check + show
if __name__ == "__main__":
    from itertools import combinations
    for name, a in options.items():
        s = a.bounding_box().size
        bad = [round((p & q).volume) for p, q in combinations(a.children, 2) if (p & q).volume > 0.5]
        lengths = sorted({round(max(c.bounding_box().size.X, c.bounding_box().size.Y))
                          for c in a.children if c.label.startswith("W")})
        print(f"{name:30s} {s.X:5.0f} x {s.Y:5.0f} x {s.Z:4.0f} mm  plank lengths {lengths}  "
              f"overlaps: {bad or 'none'}")
    show_row(options, gap=400)
