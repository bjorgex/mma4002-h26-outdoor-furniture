"""Jig parts of version 4 (bench_cell_v4.py): the double-sided guide cut in two halves, so it is not
trapped between frame 1 and frame 2 at the end, a parking pad for the halves and a longer ground base.

    python robot_cell/jig_parts_v4.py        (shared venv: build123d; needs jig_parts.py's guide)

Base-local coordinates (bench up = +y, the backrest leans to +x; w along the back planks, t across
them, pointing back):
    inner  above the seat and in front of the backrest: the wall on top of each seat plank, the front
           wall and both ends of each back plank; plus the front end below the seat line (x < -60,
           y > -70). Slides out forward (-t), then up (+y).
    outer  under the seat and behind the backrest: the wall under and both ends of each seat plank,
           the wall behind each back plank. Slides out down (-y), then back (+x).
Together the halves close every slot (the same funnels). The cut runs through the middle of the
guide's grip pocket (y -80..-60, split at y -70): fingers in the middle clamp both halves (the guide is
carried as one, as before); fingers 5 mm to one side (8 mm wide fingers in 10 mm) hold one half.
Checked here in 3D: no overlap with the planks or the other half along the slide-outs (inner first).
Parking pad (behind both bases, for the halves): 180 x 380 x 80, top at z = 0 in its own coordinates.
Ground base 770 x 440 (version 3's 590 x 440 plus the pad) with the 4 red vision squares.
Out: robot_cell/jig_parts/{guide_inner,guide_outer,parking_pad,ground_base_split}.stl and
     CAD/Jig V1/v4 split guide/*.STEP
"""
import build123d as bd

import jig_guide
import jig_parts as jp

CAD = jp.CAD / "v4 split guide"
GROUND = (770, 440, 15)
PAD = (180, 380, 80)
FRONT_END = (-60, -70)                   # inner's front end below the seat line: x < -60, y > -70 (pocket middle)
SLIDE, LIFT = 8, 50                      # mm off the planks (5.65 mm slots + walls); then lifted over the bases


def rows():
    """Seat line y, back row centre, w (along the back planks) and t (across, pointing back), base-local."""
    slots = [((c[0], -c[1]), (u[0], -u[1])) for c, u in jig_guide.plank_slots()]   # guide turned over x
    half = jig_guide.STRAIGHT[1] / 2
    seat_y = [c[1] for c, u in slots if abs(u[1]) < 0.1][0]
    back = [(c, u) for c, u in slots if abs(u[1]) > 0.1]
    w = back[0][1] if back[0][1][1] > 0 else (-back[0][1][0], -back[0][1][1])
    t = (w[1], -w[0])
    return seat_y + half, back[0][0], w, t, half, slots


def split(guide):
    y_line, cb, w, t, half, _ = rows()
    big = 1000
    box = lambda: bd.Box(big, big, big, align=(bd.Align.MAX, bd.Align.MIN, bd.Align.CENTER))   # x < 0, y > 0
    above = bd.Box(big, big, big, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.CENTER)).translate((0, y_line, 0))
    front = (bd.Plane(origin=(cb[0] + t[0] * half, cb[1] + t[1] * half, 0), x_dir=(t[0], t[1], 0))
             * bd.Box(big, big, big, align=(bd.Align.MAX, bd.Align.CENTER, bd.Align.CENTER)))
    region = (above & front) + box().translate((*FRONT_END, 0))
    return guide & region, guide - region


def planks():
    """The six planks as straight 25 x 5 bars through the guide (base-local, z 0..300)."""
    *_, slots = rows()
    return [bd.Plane(origin=(c[0], c[1], 0), x_dir=(u[0], u[1], 0)) * bd.Box(25, 5, 300, align=(
        bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)) for c, u in slots]


def slide_check(inner, outer):
    """Largest overlap (mm3) of each half with the planks (and the other half) along its way out."""
    _, _, w, t, _, _ = rows()
    bars = planks()

    def overlap(shape, others):
        return sum(getattr(shape & o, "volume", 0.0) for o in others)

    worst = {"inner": 0.0, "outer": 0.0}
    for s in (0.5, 1, 2, 3, 5, SLIDE):                           # inner first: forward ...
        worst["inner"] = max(worst["inner"], overlap(inner.translate((-t[0] * s, -t[1] * s, 0)), bars + [outer]))
    fwd = (-t[0] * SLIDE, -t[1] * SLIDE, 0)
    for s in (1, 5, 20, 60, 200):                                # ... then up
        worst["inner"] = max(worst["inner"], overlap(inner.translate((fwd[0], fwd[1] + s, 0)), bars + [outer]))
    for s in (0.5, 1, 2, 3, 5, SLIDE):                           # outer: down ...
        worst["outer"] = max(worst["outer"], overlap(outer.translate((0, -s, 0)), bars))
    for s in (1, 5, 20, 60, 185):                                # ... lifted, then back
        worst["outer"] = max(worst["outer"], overlap(outer.translate((s, -SLIDE, LIFT)), bars))
    return worst


def ground(size):
    x, y, t = size
    plate = bd.Box(x, y, t, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MAX))           # top face at z = 0
    s, i = jp.SQUARE, jp.SQUARE_IN
    squares = [bd.Box(s, s, 0.5, align=(bd.Align.MIN,) * 3).translate((sx, sy, 0))
               for sx in (i, x - i - s) for sy in (i, y - i - s)]
    return plate, squares


def main():
    CAD.mkdir(exist_ok=True)
    inner, outer = split(jp.guide())
    pad = bd.Box(*PAD, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX))
    plate, squares = ground(GROUND)
    parts = {"guide_inner": inner, "guide_outer": outer, "parking_pad": pad, "ground_base_split": plate}
    for name, s in parts.items():
        bd.export_stl(s, str(jp.OUT / f"{name}.stl"), tolerance=0.05)
    cad = {"JigGuide_inner_V1": inner, "JigGuide_outer_V1": outer, "ParkingPad_V1": pad,
           "GroundBase_split_V1": bd.Compound([plate] + squares)}
    for name, s in cad.items():
        s.label = name
        bd.export_step(s, str(CAD / f"{name}.STEP"))
    for name, s in parts.items():
        bb = s.bounding_box()
        print(f"{name:18s} {s.volume / 1000:7.1f} cm3  {len(s.solids())} solid(s)  x {bb.min.X:6.1f}..{bb.max.X:6.1f}"
              f"  y {bb.min.Y:6.1f}..{bb.max.Y:6.1f}  z {bb.min.Z:6.1f}..{bb.max.Z:6.1f}")
    print("way-out overlap with planks / other half (mm3):", slide_check(inner, outer))


if __name__ == "__main__":
    main()
