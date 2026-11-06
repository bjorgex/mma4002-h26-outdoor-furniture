"""Jig V5: the JigV3 bases + guide and the plank rack bolted to the 300 x 300 T-slot robot base (robot_base.py).

Plate coordinates (as robot_base.py): x away from the robot 0..300, y to the left 0..300, top of the plate z = 0.
T-slot lines along y at x = 45, 75, ... 255 (robot_base.FIRST + i * PITCH).

    layout        plank rack nearest the robot, bases + guide farther out (Bjørge, 2026-11-06); 5 planks per bench
    bases A + B   JigV3 base (jig_v3.py), both turned +90 deg (legs along -x, towards the rack), side by side across
                  the slots, centred: A at (210, 60), B at (210, 240) -> each overhangs the plate by 30 mm in y.
                  NEW screw holes: M8 through + counterbore from the top, on T-slot lines, only where the base is
                  solid from bottom to top and (base A) clear of the guide. A and B are the same part: same holes.
    guide         JigV3's two halves, on base A (start/end of the cycle), as in jig_v3.py.
    plank rack    PlankRack_V2's body, turned 90 deg (its 60 mm width along x) in the near strip x 30..90, centred
                  in y; flanges widened for M8 and the holes moved onto the slot lines x = 45 and 75.
Bolts: M8 into M8 T-nuts in the slots (robot_base.py: 9 mm opening, 15 x 6 head).

    python robot_cell/jig_v5.py
Out: jig-cad/Jig V5/JigAssembly_V5.STEP (+ .stl), JigBaseV3_holes_V5.STEP/.stl (one base, local coords),
     PlankRack_V5.STEP/.stl; sim STLs in robot_cell/jig_parts/*_v5.stl and the layout jig_v5_layout.json.
"""
import json
import math
from pathlib import Path

import build123d as bd
from build123d import Align

import jig_v3
import robot_base as rbase
import jig_v2

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = HERE.parent / "jig-cad" / "Jig V5"
SIM = HERE / "jig_parts"

SLOTS = [rbase.FIRST + i * rbase.PITCH for i in range(rbase.N_SLOTS)]       # 45 .. 255
BASE_TURN = 90                                                                # legs towards -x: the rack / robot
BASES = {"A": (210.0, 60.0), "B": (210.0, 240.0)}                            # base centres on the plate (far side)
BOLT_D, CB_D, CB_H = 9.0, 14.5, 9.0                                           # M8 clearance, counterbore for the head
EDGE_MIN = 10.0                                                               # hole edge to base edge, at least
SLAB, MIN_SOLID = 20.0, 18.0                                                  # JigV3 base floor thickness; min under a hole
RACK_TURN = -90                                                               # rack-local y -> plate +x
RACK_AT = (30.0, 195.0)                                                       # rack-local origin on the plate (near the robot)
RACK_HOLES_Y = (15.0, 45.0)                                                   # rack-local y of the flange holes -> x 45, 75
RACK_FLANGE = 22.0                                                            # flange length (was 16: room for M8)


def base_hole_positions(base, guide):
    """Plate-coordinate hole centres for base A: per slot line under the base, the two y positions farthest apart
    where a counterbore-sized column is solid base from bottom to top and clear of the guide."""
    # JigV3's base is mostly a 20 mm slab (walls up to 40); the guide covers much of it and the frame's leg
    # pockets run along x. A hole goes where a counterbore-wide column is solid slab from z 0 to its top
    # (one level, >= MIN_SOLID), clear of the guide, over the plate, and not in a pocket.
    cx, cy = BASES["A"]
    placed = jig_v3.place_at(base, (cx, cy), BASE_TURN)
    guides = [jig_v3.place_at(g, (cx, cy), BASE_TURN) for g in guide]
    area = math.pi * (CB_D / 2) ** 2
    lines = {}
    for x in SLOTS:
        if not (cx - 90 + EDGE_MIN + CB_D / 2 <= x <= cx + 90 - EDGE_MIN - CB_D / 2):
            continue
        ok = []
        y = max(cy - 90, 0) + EDGE_MIN + CB_D / 2
        while y <= min(cy + 90, rbase.SIZE) - EDGE_MIN - CB_D / 2:
            col = bd.Cylinder(CB_D / 2, 80, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, 0))
            solid = placed & col
            v = sum(s.volume for s in solid.solids()) if solid else 0
            if v > 1:
                h = solid.bounding_box().max.Z
                clear = all(not (g & col) or sum(s.volume for s in (g & col).solids()) < 1e-3 for g in guides)
                if h >= MIN_SOLID and v > 0.99 * area * h and abs(h - SLAB) < 0.5 and clear:
                    ok.append(y)
            y += 2.0
        if len(ok) >= 2 and ok[-1] - ok[0] >= 25:
            lines[x] = (ok[0], ok[-1])
    # the two slot lines farthest apart, two holes on each (widest spread)
    xs = sorted(lines)
    use = [xs[0], xs[-1]] if len(xs) >= 2 else xs
    return [(x, y) for x in use for y in lines[x]]


def to_base_local(px, py, which="A"):
    """Plate point -> base-local (JigV3 base, right side up, before the turn)."""
    cx, cy = BASES[which]
    dx, dy = px - cx, py - cy
    a = math.radians(-BASE_TURN)
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)


def base_with_holes(base, local_holes):
    for x, y in local_holes:                                  # all holes are in the 20 mm slab: counterbore from z 20
        base -= bd.Cylinder(BOLT_D / 2, SLAB + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, -1))
        base -= bd.Cylinder(CB_D / 2, CB_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, SLAB - CB_H))
    return base


def plank_rack_v5():
    """PlankRack_V2's body with longer flanges and M8 holes at rack-local y 15 / 45 (-> the slot lines)."""
    import jig_platform_v4 as v4
    body = jig_v2.plank_rack_v2()
    (x0, x1), (y0, y1) = v4.RACK_X, v4.RACK_Y
    # cut the old flanges off (everything outside the body's x range), add longer ones
    keep = bd.Box(x1 - x0, 1000, 1000, align=(Align.MIN, Align.CENTER, Align.CENTER)).translate((x0, (y0 + y1) / 2, 0))
    body = body & keep
    body = bd.Compound(list(body.solids())) if not isinstance(body, bd.Solid) else body
    holes = []
    for side, xf in (("lo", x0 - RACK_FLANGE), ("hi", x1)):
        fl = bd.Box(RACK_FLANGE, y1 - y0, jig_v2.FLANGE_T, align=(Align.MIN, Align.MIN, Align.MIN)).translate((xf, y0, 0))
        body = body + fl
        hx = xf + RACK_FLANGE / 2
        for hy in RACK_HOLES_Y:
            body -= bd.Cylinder(BOLT_D / 2, 50, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((hx, hy, -1))
            holes.append((hx, hy))
    return body, holes


def rack_place(shape):
    return shape.rotate(bd.Axis.Z, RACK_TURN).translate((*RACK_AT, 0))


def rack_to_plate(x, y):
    a = math.radians(RACK_TURN)
    return (RACK_AT[0] + x * math.cos(a) - y * math.sin(a), RACK_AT[1] + x * math.sin(a) + y * math.cos(a))


def main():
    base, guide = jig_v3.jig_v3_parts()
    plate_holes = base_hole_positions(base, guide)
    local = [to_base_local(x, y) for x, y in plate_holes]
    base_h = base_with_holes(base, local)
    rack, rack_holes = plank_rack_v5()
    plate, _ = rbase.robot_base()

    parts = [("RobotBase_Tslot", plate, (0.70, 0.72, 0.75)),
             ("JigV3 base A (V5 holes)", jig_v3.place_at(base_h, BASES["A"], BASE_TURN), (0.35, 0.55, 0.85)),
             ("JigV3 guide half 1 (on A)", jig_v3.place_at(guide[0], BASES["A"], BASE_TURN), (0.95, 0.65, 0.15)),
             ("JigV3 guide half 2 (on A)", jig_v3.place_at(guide[1], BASES["A"], BASE_TURN), (0.95, 0.65, 0.15)),
             ("JigV3 base B (V5 holes)", jig_v3.place_at(base_h, BASES["B"], BASE_TURN), (0.35, 0.55, 0.85)),
             ("PlankRack_V5", rack_place(rack), (0.45, 0.47, 0.50))]
    for name, s, c in parts:
        s.label, s.color = name, bd.Color(*c)
    OUT.mkdir(exist_ok=True)
    asm = bd.Compound(children=[s for _, s, _ in parts], label="JigAssembly_V5")
    bd.export_step(asm, str(OUT / "JigAssembly_V5.STEP"))
    bd.export_stl(asm, str(OUT / "JigAssembly_V5.stl"))
    bd.export_step(base_h, str(OUT / "JigBaseV3_holes_V5.STEP"))
    bd.export_stl(base_h, str(OUT / "JigBaseV3_holes_V5.stl"))
    bd.export_step(rack, str(OUT / "PlankRack_V5.STEP"))
    bd.export_stl(rack, str(OUT / "PlankRack_V5.stl"))

    # sim parts (robot_cell/jig_parts) in their own local frames + where they go (for bench_cell_v8.py)
    for name, s in (("tslot_plate_v5", plate), ("base_v5", base_h), ("guide_1_v5", guide[0]),
                    ("guide_2_v5", guide[1]), ("plank_rack_v5", rack)):
        bd.export_stl(s, str(SIM / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2)
    layout = {"_doc": "jig_v5.py: plate coords (x away from robot, y left, plate top z=0); turn = deg about z",
              "plate": {"stl": "tslot_plate_v5.stl", "size": [rbase.SIZE, rbase.SIZE, rbase.THICK]},
              "base_A": {"stl": "base_v5.stl", "at": BASES["A"], "turn": BASE_TURN},
              "base_B": {"stl": "base_v5.stl", "at": BASES["B"], "turn": BASE_TURN},
              "guide": {"stl": ["guide_1_v5.stl", "guide_2_v5.stl"], "on": "base_A", "note": "base-local, z 20..60"},
              "plank_rack": {"stl": "plank_rack_v5.stl", "at": RACK_AT, "turn": RACK_TURN,
                             "note": "rack-local = PlankRack_V2 coords (slot-grid corner at origin)"},
              "tslots_x": SLOTS, "base_holes_plate_A": plate_holes,
              "rack_holes_plate": [rack_to_plate(x, y) for x, y in rack_holes]}
    (HERE / "jig_v5_layout.json").write_text(json.dumps(layout, indent=1), encoding="utf-8")

    print("base A holes (plate x, y):", [(round(x), round(y)) for x, y in plate_holes])
    print("base-local holes:", [(round(x, 1), round(y, 1)) for x, y in local])
    print("rack holes (plate):", [tuple(round(v, 1) for v in rack_to_plate(x, y)) for x, y in rack_holes])
    for name, s, _ in parts:
        b = s.bounding_box()
        print(f"{name:28s} x {b.min.X:6.1f}..{b.max.X:6.1f}  y {b.min.Y:6.1f}..{b.max.Y:6.1f}  z {b.min.Z:5.1f}..{b.max.Z:5.1f}")
    print(OUT / "JigAssembly_V5.STEP")


if __name__ == "__main__":
    main()
