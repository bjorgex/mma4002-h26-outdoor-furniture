"""Plank interface candidates (round 6, 2026-10-15). Same test bench as interface_options.py:
one column per interface, chair -> chair with back -> planter behind each other, the shown
plank lifted / pulled out with the number engraved.

Kept from interface_options.py (welded on / laser cut, frame = S1 tube):
    16 welded hairpin clip   bent spring-steel clip in each gap holds both neighbouring planks
    17 tongue in laser slot  split tongue on the plank snaps under the tube wall, no steel added

Cast frame (SK, ductile iron, C-section, 8 mm walls). Every feature is rigid and cast in; any
spring is in the WOOD (cast iron cracks if it has to flex). All plank cuts are blind pockets
from below, so no opening shows at the plank end:
    19 barbed boss         boss with 3 cast barbs, pressed into a blind hole
    20 T-lug, side slide   T-head lug; plank set down 9 mm sideways (into the 10 mm gap), slid
                           across, a wood detent clicks. Entry pockets on both sides: every
                           plank is the same, either direction works
    21 cast pocket+tongue  17 in iron: the slot is cast, the plank's split tongue snaps under
                           the 8 mm flange
    22 barbed rib          cast rib with 3 barbs in a stopped kerf (kerf stops 20 mm short of
                           both plank edges: invisible)
    23 T-lug, end slide    T-head across the plank; plank set down 10 mm off, slid along its
                           length, detent clicks. Both ends closed (18's open end fixed)
Plank-end interfaces (frame = S1 tube, parts welded on, SW). A 3 mm steel cap covers each plank
end (stops 4 mm above the frame: a drain gap so the end grain dries). The planter floor has no
cap - its ends are already hidden behind the end-wall planks:
    24 end fin             barbed fin in a stopped vertical kerf in the end grain, press down
    25 end T-key           T-key in a T-slot in the end grain (open below), press down, the
                           mouth of the slot is 0.3 mm tight
    26 spring end cap      2 mm spring-steel cap with a bead that snaps into a groove across
                           the end face; a plain fin locates
    27 end pin, tilt in    pin into a hole in end a, tilt the plank down onto the pin at end b
                           (slot open below, detent). The plank has a "this end first" end
    28 end shoe            cap + two cheeks in the gaps with dimples into stopped edge grooves

Run:  python interface_candidates.py   (exports nothing)
"""

# %% Setup
from build123d import *
import interface_options as io
from furniture import T, W
from interface_options import X, at, cast_frame, hairpin, lower_ok, tongue, union

CAST = io.CAST_WALL          # cast flange thickness (8)


def bar(x0, x1, y, z0, z1, wy):
    """Box x0..x1, centred on y (width wy), z0..z1 - in plank coordinates."""
    return at((x0 + x1) / 2, y, (z0 + z1) / 2) * Box(x1 - x0, wy, z1 - z0)


# %% Cast frame interfaces (19-23): "steel" = cast into the SK frame
def cast_boss(i, n, end, lo):
    """19: Ø11 boss with 3 cast barbs (Ø13), blind Ø11.5 hole 20 deep: the barbs bite 0.75 mm."""
    steel = at(X, W / 2, 9) * Cylinder(5.5, 18)
    for z in (3, 8, 13):
        steel += at(X, W / 2, z) * Cone(6.5, 5.5, 4)
    return dict(steel=steel, wood=at(X, W / 2, 9.5) * Cylinder(5.75, 21))


SIDE = 9                     # 20: sideways slide (the gap is 10)


def cast_tlug_side(i, n, end, lo):
    """20: neck 10 x 4, head 30 (along the plank) x 8 x 4. Plank set down 9 mm off to either
    side, slid across; the 12 mm neck channel narrows to 9 mm just before the end position."""
    lug = at(X, W / 2, 4) * Box(10, 4, 8) + at(X, W / 2, 10) * Box(30, 8, 4)
    wood = (at(X, W / 2, 3.5) * Box(12, 2 * SIDE + 5, 9)          # neck channel, both ways
            + at(X, W / 2, 10.5) * Box(32, 2 * SIDE + 10, 5))      # undercut for the head
    for s in (-1, 1):
        wood += at(X, W / 2 + s * SIDE, 6) * Box(32, 10, 14)        # entry pocket
        for sx in (-1, 1):
            wood -= at(X + sx * 5.25, W / 2 + s * 4, 3.5) * Box(1.5, 2, 9)  # detent ridge
    return dict(steel=lug, wood=wood)


def cast_tongue(i, n, end, lo):
    """21: 17's split tongue, 24 long, 11 deep, barbs under the 8 mm cast flange; the slot is
    cast. (24, not 30: at a planter corner the front-wall and end-wall tongues meet in the post.)"""
    tl, tw, depth = 24, 12, CAST + 3
    add = at(X, W / 2, -depth / 2) * Box(tl, tw, depth)
    for s in (-1, 1):
        add += at(X, W / 2 + s * (tw / 2 + 0.75), -CAST - 1.5) * Box(tl, 1.5, 2)
    kerf = at(X, W / 2, (8 - depth - 1) / 2) * Box(tl + 2, 2, 8 + depth + 1)
    return dict(wood_add=add, wood=kerf, cut=at(X, W / 2, -CAST / 2) * Box(tl, tw, CAST + 2))


def cast_rib(i, n, end, lo):
    """22: rib 4 x 50 x 14 across the plank, 3 barbs (5 mm); kerf 4.5 x 56, 16 deep."""
    rib = at(X, W / 2, 7) * Box(4, 50, 14)
    for z in (4, 8, 12):
        rib += at(X, W / 2, z) * Box(5, 50, 1)
    return dict(steel=rib, wood=at(X, W / 2, 7.5) * Box(4.5, 56, 17))


SLIDE = 10                   # 23: slide along the plank


def cast_tlug_end(i, n, end, lo):
    """23: neck 4 x 5, head 8 x 26 (across the plank). Plank slides +x by 10: end a's entry is
    10 mm further in, end b's 10 mm nearer the end (still 10 mm of wood to the end face)."""
    s = 1 if end == "a" else -1
    lug = at(X, W / 2, 4) * Box(4, 5, 8) + at(X, W / 2, 10) * Box(8, 26, 4)
    mid = X + s * SLIDE / 2
    wood = (at(mid, W / 2, 3.5) * Box(SLIDE + 6, 6.5, 9)                # neck channel
            + at(mid, W / 2, 10.5) * Box(SLIDE + 10, 28, 5)              # undercut
            + at(X + s * SLIDE, W / 2, 6) * Box(10, 28, 14))             # entry pocket
    for sy in (-1, 1):
        wood -= at(X + s * 3.5, W / 2 + sy * 2.75, 3.5) * Box(2, 1, 9)  # detent ridge
    return dict(steel=lug, wood=wood)


# %% Plank-end interfaces (24-28): "weld" = welded onto the S1 tube (SW)
def cap(lo, t=3):
    """End cap x -t..0 over the plank's end face, from t + 1 mm above the frame face to the top
    (drain gap; it also keeps two caps at a planter corner from touching).
    None on the planter floor (boxed): the end-wall planks cover those ends."""
    return None if lo == "boxed" else bar(-t, 0, W / 2, t + 1, T, W)


def x0(lo, t=3):
    """Welded parts start at the cap (x = -t), or at the frame edge when there is no cap."""
    return 0 if lo == "boxed" else -t


def end_fin(i, n, end, lo):
    """24: 3 mm fin, 16 into the end, 20 high, barbs 0.2 mm; kerf 3.2 open below and at the end
    (behind the cap), stopped 8 mm below the top face."""
    fin = bar(x0(lo), 16, W / 2, 0, 20, 3)
    for z in (5, 10, 15):
        fin += bar(1, 16, W / 2, z - 0.5, z + 0.5, 3.6)
    return dict(weld=union([fin, cap(lo)]), wood=bar(-1, 16.5, W / 2, -1, 20.5, 3.2))


def end_tkey(i, n, end, lo):
    """25: T-key (neck 5 x 5, head 8 x 14, 22 high); T-slot open below, 0.3 mm tight at its
    mouth so the key is pressed in the last 3 mm."""
    key = bar(x0(lo), 5, W / 2, 0, 22, 5) + bar(5, 13, W / 2, 0, 22, 14)
    slot = bar(-1, 5.5, W / 2, -1, 23, 6) + bar(5, 13.5, W / 2, -1, 23, 15)
    for s in (-1, 1):
        slot -= bar(5, 13.5, W / 2 + s * 7.1, -1, 3, 0.8)
    return dict(weld=union([key, cap(lo)]), wood=slot)


def spring_cap(i, n, end, lo):
    """26: plain 3 mm fin locates; the 2 mm spring-steel cap's bead snaps into a groove across
    the end face (the cap bends out as the plank goes down)."""
    fin = bar(x0(lo, 2), 12, W / 2, 0, 18, 3)
    c = cap(lo, 2)
    parts = [fin] if c is None else [fin, c, bar(0, 1.5, W / 2, 17, 19, W - 10)]
    wood = bar(-1, 12.5, W / 2, -1, 18.5, 3.2) + bar(-1, 2, W / 2, 16.5, 19.5, W - 8)
    return dict(weld=union(parts), wood=wood)


def end_pin(i, n, end, lo):
    """27: Ø10 pin 16 long at mid height on a web. End a: blind hole (plank pushed onto it
    lengthwise); end b: slot open below (plank tilted down onto it), 9.6 mm detent under the pin."""
    pin = at(8, W / 2, 14) * Rot(0, 90, 0) * Cylinder(5, 16)
    web = bar(x0(lo), 12, W / 2, 0, 14, 3)
    wood = bar(-1, 12.5, W / 2, -1, 14, 3.2)                               # web kerf
    if end == "a":
        wood += at(8, W / 2, 14) * Rot(0, 90, 0) * Cylinder(5.2, 18)
    else:
        wood += bar(-1, 16.5, W / 2, -1, 14, 10.4) + at(7.75, W / 2, 14) * Rot(0, 90, 0) * Cylinder(5.2, 17.5)
        for s in (-1, 1):
            wood -= bar(-1, 16.5, W / 2 + s * 5.0, 6, 9, 0.4)
    return dict(weld=union([pin, web, cap(lo)]), wood=wood)


def end_shoe(i, n, end, lo):
    """28: cap + a 2 mm cheek on each plank edge (in the gap) with a 1.5 mm dimple that snaps
    into a stopped groove (3 deep) in the edge. Planter floor: no cheeks against the posts."""
    boxed = lo == "boxed"
    parts = [cap(lo)]
    for y0, s in ((0, -1), (W, 1)):  # s: the cheek's side of the edge
        if y0 == 0 and (not lower_ok(i, lo) or (boxed and i == 0)):
            continue
        if y0 == W and boxed and i == n - 1:
            continue
        parts += [bar(x0(lo), 40, y0 + s, 0, 18, 2), bar(5, 35, y0 - s * 0.75, 10.5, 13.5, 1.5)]
    grooves = union([bar(4, 36, y, 10, 14, 6) for y in (0, W)])
    return dict(weld=union(parts), wood=grooves)


# %% Candidates
INTERFACES = [(16, "welded hairpin clip", hairpin), (17, "tongue in laser slot", tongue),
              (19, "cast barbed boss", cast_boss), (20, "cast T-lug side slide", cast_tlug_side),
              (21, "cast pocket + tongue", cast_tongue), (22, "cast barbed rib", cast_rib),
              (23, "cast T-lug end slide", cast_tlug_end),
              (24, "end fin", end_fin), (25, "end T-key", end_tkey), (26, "spring end cap", spring_cap),
              (27, "end pin tilt-in", end_pin), (28, "end shoe", end_shoe)]
FRAMES = {n: cast_frame for n in range(19, 24)}

models = {}  # built on first use


def build_all():
    if not models:
        models.update({f"{n} {nm}": io.test_models(n, nm, fn, FRAMES) for n, nm, fn in INTERFACES})
    return models


def grid(y0=0, gap=400):
    return io.grid(y0, gap, build_all())


# %% Show: one column per interface
if __name__ == "__main__":
    from ocp_vscode import Camera, get_port, show

    for col in build_all().values():
        print("   ".join(f"{a.label} ({len(a.children)} parts)" for a in col))
    if get_port() is None:
        print("OCP viewer not open (Ctrl+Shift+P -> 'OCP CAD Viewer: Open viewer'), skipping show")
    else:
        layout = grid()
        show(*layout.values(), names=list(layout), reset_camera=Camera.RESET)
