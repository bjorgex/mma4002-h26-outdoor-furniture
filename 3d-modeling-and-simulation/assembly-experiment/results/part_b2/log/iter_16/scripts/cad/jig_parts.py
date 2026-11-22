"""Jig parts of the v3 cell (fitted to the bench) and the ground base, build123d.

    ./py design/cad/jig_parts.py          then ./py design/build_cell.py

Base-local coordinates ("up"): base bottom at z = 0, open face of the pocket up at z = 20, frame 1
lying in the pocket at z 9.5..19.5, planks pointing up (z 9.5..259.5). The bench sits in the base
at x - 2.715, y = -(STEP z) - 21.877 (build_cell.T_IN).
    base A    180 x 180 x 20, pocket = the frame outline + 0.25 mm, 10.5 deep
    base B    base A mirrored in y: frame 2 after the flip about x (build_cell.FLIP)
    guide     the double-sided guide (step/JigGuide_DoubleSided.STEP, made by jig_guide.py) + a 24 mm wide grip
              notch, 18 deep, through the full thickness, in the side face of its short arm (x = -87): the
              fingers (tool horizontal, pointing away from the robot) drop into it from above, open across it
              (in y), and the robot turns the guide over by turning J6. Walls left: 8 mm to the outer edge.
    plank jig 90 x 60 x 40 block, 6 slots (2 rows of 3, 30 mm apart)
    ground base, with 4 red 25 x 25 mm vision squares in the corners (fixed: the work plate)
Out: design/meshes/jig/*.stl (the cell) and design/cad/out/*.STEP.
"""
import math
from pathlib import Path

import build123d as bd

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = HERE.parent / "meshes" / "jig"
CAD = HERE / "out"
BENCH = HERE / "step" / "BenchInterfaceV1.STEP"
GUIDE = HERE / "step" / "JigGuide_DoubleSided.STEP"
BASE = (180, 180, 20)
POCKET_DEPTH, CLEAR = 10.5, 0.25
IN_BASE = (-2.715, -21.877, 134.5)       # STEP -> base-local: rotate x +90, then move (frame 1 outer face at z 9.5)
GRIP_POCKET = ((-90, -82, 19), (-69, -58, 61))   # guide, base-local box (x, y, z) min/max: short arm side face,
                                                 # cut through the full thickness (z 20..60): a vertical notch the
                                                 # fingers enter from above in either guide orientation (iter 02)
GROUND = (590, 440, 15)                  # ground base x (away from the robot) x y x thickness
SQUARE, SQUARE_IN = 25, 3                # vision squares and their inset from the edges
PLANK_JIG_SIZE = (90, 66, 40, 30)        # plank jig size x, y, height, pitch (iter 27: y 60 -> 66, the turned
                                         # row-1 slots reach y 58.1: outer wall 7.9 mm)
PLANK_ROW_YAW = (0, 80)                  # slot yaw per row, deg (iter 27: row 1 = planks 4-6 turned as in frame 1)
# B2 iter 12: one column along base A (40 x 168 mm), slot n -> (x, y, yaw) in jig coordinates; slots 1-3 = row 0
# (yaw 0), 4-6 = row 1 (yaw 80), each at the robot y of its plank's place in frame 1. Same as build_cell.PLANK_SLOTS.
PLANK_JIG_SIZE = (40, 168, 40, 30)
PLANK_SLOTS = {1: (24, 8, 0), 2: (24, 38, 0), 3: (24, 68, 0), 4: (32, 90, 80), 5: (32, 120, 80), 6: (32, 150, 80)}
# B2 iter 14: the column keeps slots 1-3 only (40 x 86); slots 4-6 move to plank jig 2 (25 x 100) at the plate's far
# edge, beside frame 1's far place column. Same as build_cell.PLANK_SLOTS / PLANK_SLOTS2.
PLANK_JIG_SIZE = (40, 86, 40, 30)
PLANK_SLOTS = {1: (24, 8, 0), 2: (24, 38, 0), 3: (24, 68, 0)}
PLANK_JIG2_SIZE = (25, 100, 40)
PLANK_SLOTS2 = {4: (12.5, 20, 80), 5: (12.5, 50, 80), 6: (12.5, 80, 80)}
# B2 iter 15: slots 1-3 move into base A's free corner (base-local x, y, yaw), through the 20 mm block: the planks
# stand on the riser, each right in front of its place in frame 1's y-124 arm. Same as build_cell.PLANK_SLOTS_A.
PLANK_SLOTS_A = {1: (-33.0, -2.0, 0), 2: (-3.0, -2.0, 0), 3: (27.0, -2.0, 0)}


def to_base(shape):
    return shape.rotate(bd.Axis.X, 90).translate(IN_BASE)


def base_a():
    bench = bd.import_step(str(BENCH))
    frame1 = min((c for c in bench.children if c.label.startswith("Part2")), key=lambda c: c.bounding_box().min.Y)
    f = to_base(frame1)
    bottom = min(f.faces().filter_by(bd.Axis.Z), key=lambda face: face.center().Z)          # outer face, z 9.5
    outline = bd.offset(bd.Face(bottom.outer_wire()), CLEAR)
    pocket = bd.extrude(outline.translate((0, 0, BASE[2] - POCKET_DEPTH - bottom.center().Z)),
                        amount=POCKET_DEPTH + 1, dir=(0, 0, 1))      # up from the pocket floor (face normal is down)
    block = bd.Box(*BASE, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return block - pocket


def base_a_slotted():
    """B2 iter 15: base A + three plank through-slots (planks 1-3 start here). Base B stays the unslotted mirror."""
    a = base_a()
    for sx, sy, yaw in PLANK_SLOTS_A.values():
        a -= bd.Box(25.6, 5.6, BASE[2] + 2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).rotate(
            bd.Axis.Z, yaw).translate((sx, sy, -1))
    return a


RELIEF_DEPTH, RELIEF_CLEAR, TAB = 2.0, 0.75, 2.0   # base B: recess under each plank end tab (iter 08)


def base_b():
    """Base A mirrored in y, plus a 2 mm recess under each plank end tab. After the flip the plank ends of frame 1
    land flush on the pocket floor (z 9.5): a zero-depth contact the checker flags at random (L09). A plank end is
    two 2 mm tabs with the interface piece between them; only the tabs (+0.75 mm) are relieved, so pieces B keep
    their floor (L10: a whole-plank recess made them float)."""
    bench = bd.import_step(str(BENCH))
    a = base_a()
    z0 = BASE[2] - POCKET_DEPTH                                 # pocket floor, z 9.5
    for c in bench.children:
        if not c.label.lower().startswith("plank"):
            continue
        p = to_base(c)
        if p.bounding_box().min.Z > z0 + 0.5:
            continue
        # the STEP plank is a plain box; the mesh (plank_body.stl) end has a 2 mm tab at each end of its 25 mm width
        bottom = min(p.faces().filter_by(bd.Axis.Z), key=lambda f: f.center().Z)
        ctr = bottom.center()
        edges = sorted(bottom.edges(), key=lambda e: e.length)
        u = (edges[-1] @ 1) - (edges[-1] @ 0)
        u = u.normalized()                                      # the STEP end face is stepped (21.4 mm): take the
        half = max(abs((bd.Vector(v) - ctr).dot(u)) for v in p.vertices())  # plank's full extent along its width (25 mm)
        ang = math.degrees(math.atan2(u.Y, u.X))
        w = edges[0].length
        for s in (-1, 1):
            tc = ctr + u * (s * (half - TAB / 2))
            a -= (bd.Box(TAB + 2 * RELIEF_CLEAR, w + 2 * RELIEF_CLEAR, RELIEF_DEPTH + 0.5,
                         align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
                  .rotate(bd.Axis.Z, ang).translate((tc.X, tc.Y, z0 - RELIEF_DEPTH)))
    return a.mirror(bd.Plane.XZ)


def guide():
    g = bd.import_step(str(GUIDE))
    g = g.rotate(bd.Axis.X, 180)                               # draft jig coordinates -> base-local: z 20..60
    (x0, y0, z0), (x1, y1, z1) = GRIP_POCKET
    return g - bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN,) * 3).translate((x0, y0, z0))


def plank_jig(size=None, slots=None):
    x, y, h = (size or PLANK_JIG_SIZE)[:3]
    block = bd.Box(x, y, h, align=(bd.Align.MIN,) * 3)
    for sx, sy, yaw in (slots or PLANK_SLOTS).values():
        block -= bd.Box(25.6, 5.6, h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).rotate(
            bd.Axis.Z, yaw).translate((sx, sy, 0))
    return block


def ground_base():
    x, y, t = GROUND
    plate = bd.Box(x, y, t, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MAX))           # top face at z = 0
    squares = [bd.Box(SQUARE, SQUARE, 0.5, align=(bd.Align.MIN,) * 3).translate((sx, sy, 0))
               for sx in (SQUARE_IN, x - SQUARE_IN - SQUARE) for sy in (SQUARE_IN, y - SQUARE_IN - SQUARE)]
    return plate, squares


def main():
    OUT.mkdir(exist_ok=True)
    CAD.mkdir(exist_ok=True)
    a = base_a_slotted()
    b = base_b()
    g = guide()
    parts = {"base_a": a, "base_b": b, "guide": g, "plank_jig": plank_jig(),
             "plank_jig2": plank_jig(PLANK_JIG2_SIZE, PLANK_SLOTS2)}
    plate, squares = ground_base()
    parts["ground_base"] = plate
    parts["vision_square"] = squares[0].translate((-SQUARE_IN, -SQUARE_IN, 0))
    for name, s in parts.items():
        bd.export_stl(s, str(OUT / f"{name}.stl"), tolerance=0.05)
    cad = {"JigBaseA_V1": a, "JigBaseB_V1": b, "JigGuide_DoubleSided_grip": g, "PlankJig_V1": parts["plank_jig"],
           "PlankJig2_V1": parts["plank_jig2"],
           "GroundBase_V1": bd.Compound([plate] + squares)}
    for name, s in cad.items():
        s.label = name
        bd.export_step(s, str(CAD / f"{name}.STEP"))
    for name, s in parts.items():
        bb = s.bounding_box()
        print(f"{name:13s} {s.volume / 1000:7.1f} cm3  x {bb.min.X:6.1f}..{bb.max.X:6.1f}  y {bb.min.Y:6.1f}..{bb.max.Y:6.1f}"
              f"  z {bb.min.Z:6.1f}..{bb.max.Z:6.1f}")


if __name__ == "__main__":
    main()
