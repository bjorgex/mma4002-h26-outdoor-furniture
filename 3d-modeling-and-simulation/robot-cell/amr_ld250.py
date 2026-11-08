"""A simplified Omron LD-250 AMR for the 3D cell (our sim; RoboDK's library model can't be exported).

    python robot_cell/amr_ld250.py      -> jig_parts/ld250_{body,cover,band,light,wheels}.stl

Outer size from Omron's LD-250 data: 963 (long, the drive direction) x 718 x 383 mm. Shape simplified: a rounded
body, a lighter top cover, the black safety-scanner band front and back, a blue light strip round the sides, two drive
wheels in the middle and four casters. AMR-local frame: x = forward (length), y = left (width), z up, origin on the
floor at the centre.
"""
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
OUT = HERE / "jig_parts"
L, W, H = 963.0, 718.0, 383.0
R = 140.0                                             # corner radius (plan view)
CLEAR = 30.0                                          # body bottom above the floor


def rounded_box(l, w, h, r, z0):
    """A box l x w x h with rounded vertical edges (radius r), bottom at z0, centred in x/y: two boxes + 4 corner
    cylinders (overlapping - fine for the view and the collision check)."""
    T = trimesh.transformations.translation_matrix
    pieces = [trimesh.creation.box([l - 2 * r, w, h], T([0, 0, z0 + h / 2])),
              trimesh.creation.box([l, w - 2 * r, h], T([0, 0, z0 + h / 2]))]
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = trimesh.creation.cylinder(radius=r, height=h, sections=24)
            c.apply_translation([sx * (l / 2 - r), sy * (w / 2 - r), z0 + h / 2])
            pieces.append(c)
    return trimesh.util.concatenate(pieces)


def parts():
    body = rounded_box(L, W, H - CLEAR - 18, R, CLEAR)                       # dark grey body
    cover = rounded_box(L - 30, W - 30, 18, R - 15, H - 18)                   # lighter top cover
    # safety scanner bands: front and back, black, ~ 175 mm above the floor
    band = trimesh.util.concatenate([
        trimesh.creation.box([12, W - 2 * R + 60, 60], trimesh.transformations.translation_matrix([sx * (L / 2 + 1), 0, 175]))
        for sx in (-1, 1)])
    # light strip: a thin ring just under the cover (slightly bigger than the body so it shows)
    light = rounded_box(L + 6, W + 6, 14, R + 3, H - 60)                     # sticks out 3 mm all round
    # wheels: 2 drive wheels (dia 200, width 50) in the middle, 4 casters (dia 80) near the corners
    wheels = []
    for sy in (-1, 1):
        c = trimesh.creation.cylinder(radius=100, height=50, sections=32)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        c.apply_translation([0, sy * (W / 2 - 60), 100])
        wheels.append(c)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = trimesh.creation.cylinder(radius=40, height=30, sections=20)
            c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            c.apply_translation([sx * (L / 2 - 120), sy * (W / 2 - 110), 40])
            wheels.append(c)
    return {"body": body, "cover": cover, "band": band, "light": light, "wheels": trimesh.util.concatenate(wheels)}


COLORS = {"body": [0.22, 0.23, 0.25, 1], "cover": [0.62, 0.64, 0.67, 1], "band": [0.05, 0.05, 0.05, 1],
          "light": [0.15, 0.55, 0.95, 1], "wheels": [0.08, 0.08, 0.08, 1]}


if __name__ == "__main__":
    for name, m in parts().items():
        f = OUT / f"ld250_{name}.stl"
        m.export(str(f))
        print(f"{f.name}: {len(m.faces)} faces, bounds {np.round(m.bounds, 0).tolist()}")
