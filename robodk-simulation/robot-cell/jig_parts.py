"""Jig parts for Bench V1 (co-student's JigAssemDraft1, fitted to BenchInterfaceV1) and the ground base.

    python robot_cell/jig_parts.py           (shared venv: build123d)

Base-local coordinates ("up"): base bottom at z = 0, open face of the pocket up at z = 20, frame 1
lying in the pocket at z 9.5..19.5, planks pointing up (z 9.5..259.5). The bench sits in the base
like in JigAssemDraft1 (x - 2.715, y = -(STEP z) - 21.877).
    base A    180 x 180 x 20, pocket = V1 frame outline + 0.25 mm, 10.5 deep (JigAssemDraft1 was drawn
              for the older frame V0, whose backrest the V1 frame overhangs by ~2 mm)
    base B    base A mirrored in y: frame 2 after the flip about x (FLIP in bench_cell_v3.py / _v4.py)
    guide     JigGuide_DoubleSided.STEP + a 20 x 10 mm (wide x tall) grip pocket, 18 deep, in the side
              face of its short arm (x = -87) at mid-height: the robot reaches it straight out from its base
              and flips the guide by turning J6 (EGP opens 12 mm: fingers go in closed and open vertically)
    plank jig 90 x 60 x 40 block, 6 slots (2 rows of 3, 30 mm apart)
    ground base, with 4 red 25 x 25 mm vision squares in the corners
Out: robot_cell/jig_parts/*.stl (RoboDK) and CAD/Jig V1/*.STEP (for cutting/printing).
"""
from pathlib import Path

import build123d as bd

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = HERE / "jig_parts"
CAD = HERE.parent / "CAD" / "Jig V1"
BENCH = HERE.parent / "CAD" / "BenchInterfaceV1.STEP"
GUIDE = HERE.parent / "CAD" / "JigGuide_DoubleSided.STEP"
BASE = (180, 180, 20)
POCKET_DEPTH, CLEAR = 10.5, 0.25
IN_BASE = (-2.715, -21.877, 134.5)       # STEP -> base-local: rotate x +90, then move (frame 1 outer face at z 9.5)
GRIP_POCKET = ((-90, -80, 35), (-69, -60, 45))   # guide, base-local box (x, y, z) min/max: short arm side face
GROUND = (590, 440, 15)                  # ground base x (away from the robot) x y x thickness
SQUARE, SQUARE_IN = 25, 3                # vision squares and their inset from the edges
RACK = (90, 60, 40, 30)                  # plank jig size x, y, height, pitch


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


def guide():
    g = bd.import_step(str(GUIDE))
    g = g.rotate(bd.Axis.X, 180)                               # JigAssemDraft1 -> base-local: z 20..60
    (x0, y0, z0), (x1, y1, z1) = GRIP_POCKET
    return g - bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN,) * 3).translate((x0, y0, z0))


def plank_jig():
    x, y, h, p = RACK
    block = bd.Box(x, y, h, align=(bd.Align.MIN,) * 3)
    for r in range(2):
        for c in range(3):
            block -= bd.Box(25.6, 5.6, h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).translate(
                (p * (c + 0.5), p * (r + 0.5), 0))
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
    a = base_a()
    b = a.mirror(bd.Plane.XZ)
    g = guide()
    parts = {"base_a": a, "base_b": b, "guide": g, "plank_jig": plank_jig()}
    plate, squares = ground_base()
    parts["ground_base"] = plate
    parts["vision_square"] = squares[0].translate((-SQUARE_IN, -SQUARE_IN, 0))
    for name, s in parts.items():
        bd.export_stl(s, str(OUT / f"{name}.stl"), tolerance=0.05)
    cad = {"JigBaseA_V1": a, "JigBaseB_V1": b, "JigGuide_DoubleSided_grip": g, "PlankJig_V1": parts["plank_jig"],
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
