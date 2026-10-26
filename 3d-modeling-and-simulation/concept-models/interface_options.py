"""Screwless plank interfaces: a test bench. Each option is one column in the OCP viewer,
its three test models behind each other:
    chair C1               front seat plank lifted 150 mm, option number engraved in it
    chair with back C2     S2 tube back post; front seat plank lifted
    planter P1             top front wall plank pulled 150 mm out, number engraved in it
so every interface is seen on the seat, the tilted back post, and the planter's floor (bottom
rail), front/rear walls (posts' outer faces) and end walls (frames' outer faces).
The planks lie on furniture.py's plank rows (seat_rows, back_rows, planter_rows), the same ones
the products use; an interface only says what it adds/cuts at ONE plank end (see below).

Rules (2026-10-14):
    no screws or bolts: the plank is pressed (or tapped with a rubber mallet) on.
    no small loose parts: every steel feature is welded to, or cut from, the frame.
    a new plank must go on easily; the old one may be sawn or split off.
    hidden: Bjørge prefers interfaces you can't see (in a groove/slot in the plank, under it).
    demonstrator: planks laser cut (outline + through-holes) or 3D printed, frames 3D printed,
        assembled by a cobot -> one straight move per plank is best.

Only the hidden ones are kept (numbers unchanged; removed 2026-10-15 because they show:
4 edge tabs, 6 skewer, 9 edge clip, 10 drawer, 11 snap fork, 12 cap rail, 13 hook + swing).
Press fit (hold by friction / bite):
    1  pin        ribbed Ø10 pin welded on the rail;  Ø9 blind hole in the plank
    2  fin        4 mm fin with 2 holes;  3.5 mm saw kerf across the plank underside
    3  tab        barbed tab cut from the rail wall and bent up;  slot in the plank
Form lock (the wood has to break first):
    5  keyhole    mushroom stud;  keyhole + T-slot in the plank, tap 25 mm along its length
    7  snap hook  hooked tabs snap into a stopped groove (pocket) in both plank edges (15 mm tabs,
                  staggered); the pocket locates the plank along its length
    8  fir tree   pin with 4 cone barbs
    14 wide snap hook  7 with 40 mm wide clips (both edges at the same spot), 3 mm hook:
                       about 2.5x the hook length of 7. Invisible from above.
Designed for manufacture (2026-10-15): bent-up tabs (3, 7, 14) can't be made in a closed
tube, so one identical base frame + the interface welded on (SW, bright steel) or cast in:
    15 stud keyhole + detent  stud-welded headed stud; 5's slot with a wood detent that locks
    16 welded hairpin clip    14's hook as bent spring-steel clips welded in the gaps, one
                              clip holds two planks (n + 1 per row)
    17 tongue in laser slot   slot cut by the tube laser, split tongue with barbs on the plank
    18 cast frame + lug       S1 as a ductile-iron casting (SK), 15's lug cast in

Run:  python interface_options.py   (imports the parts from furniture.py, exports nothing)
"""

# %% Setup
from build123d import *
import furniture as f
from furniture import (DEPTH, FRAME_TOP, HOLE_E, L_SHORT, MIN3, P, T, TUBE, TUBE_WALL, W, WALL_ZB,
                       back_post, back_rows, hole_x, paint, planter_rows, plank, seat_rows,
                       side_frame)

f.COLORS["SW"] = Color(0.75, 0.75, 0.78)  # welded-on interface parts (studs, clips): bright steel
f.COLORS["SK"] = Color(0.30, 0.30, 0.33)  # cast side frame: iron grey

LIFT = 150                   # shown plank lifted / pulled out to show the interface
ENGRAVE, FONT = 3, 60
w = TUBE_WALL
L = L_SHORT
X = HOLE_E                   # interface centre, 25 mm from the plank end


def at(x, y, z):
    return Pos(x, y, z)


def union(parts):
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out


# %% Interfaces
# Every interface is drawn in PLANK coordinates for one plank end:
#   the plank end is at x = 0, the plank runs to +x, its width is y = 0..W, its thickness z = 0..T
#   the frame face it lies on is z = 0; the frame wall is z = -3..0; the next plank is at y + P.
# f(i, n, end, lo) -> dict, i = plank in its row (0..n-1), end "a" (x = 0) or "b" (other end:
# the same drawing is mirrored onto it), lo = False when plank 0's lower edge sits on a rail
# (planter walls), so nothing may stick out below it; lo = None: something else sits just below
# plank 0 (the seat under the back planks), so row-level parts go to the top end instead.
#   steel     welded to the frame        cut       cut from the frame
#   wood      cut from the plank         wood_add  added to the plank outline
#   extra     loose steel parts
def lower_ok(i, lo):
    return i > 0 or lo is not False


def pin(i, n, end, lo):
    steel = at(X, W / 2, 9) * Cylinder(5, 18)
    for dz in (5, 10, 15):  # ribs bite into the hole wall
        steel += at(X, W / 2, dz) * Cylinder(5.6, 1.2)
    return dict(steel=steel, wood=at(X, W / 2, 10) * Cylinder(4.5, 20))


def fin(i, n, end, lo):
    steel = at(X, W / 2, 8) * Box(4, 40, 16)
    for dy in (-10, 10):
        steel -= at(X, W / 2 + dy, 9) * hole_x(6)
    return dict(steel=steel, wood=at(X, W / 2, 9) * Box(3.5, W + 2, 18))


def tab(i, n, end, lo):
    steel = at(X, W / 2, 7.5) * Box(3, 16, 15) + at(X - 2.25, W / 2, 12) * Box(1.5, 16, 3)
    return dict(steel=steel, cut=at(X + 9, W / 2, -w / 2) * Box(15, 16, w + 2),
                wood=at(X, W / 2, 8.5) * Box(4, 18, 17))


def keyhole(i, n, end, lo):
    steel = at(X, W / 2, 4.5) * Cylinder(4, 9) + at(X, W / 2, 11) * Cylinder(8, 4)

    def slot(x0, x1):  # neck channel 9 wide + head undercut 18 wide x 6 high
        return (at((x0 + x1) / 2, W / 2, 3.5) * Box(x1 - x0, 9, 9)
                + at((x0 + x1) / 2, W / 2, 11) * Box(x1 - x0 + 8, 18, 6))
    if end == "a":   # closed keyhole: entry hole 25 mm further in
        wood = slot(X - 4.5, X + 25) + at(X + 25, W / 2, 7) * Cylinder(9, 14)
    else:            # open at the plank end
        wood = slot(-5, X + 4.5)
    return dict(steel=steel, wood=wood)


def snap_hook(i, n, end, lo, wide=False):
    """Hooked tabs into a stopped groove (pocket) 10 mm above the plank underside on both edges.
    7: 15 mm tabs staggered (8..23 and 27..42), 3.5 mm hook.  14: 40 mm tabs (5..45), 3 mm hook.
    The pocket is only 1 mm longer than the tab at each side, so it locates the plank along its
    length and stops it sliding (a groove through the whole plank would not)."""
    tl, hook, gd = (40, 3, 4) if wide else (15, 3.5, 4.5)  # tab length, hook depth, groove depth
    xl, xr = (X, X) if wide else (X - 9.5, X + 9.5)
    steel, cut = [], []
    if lower_ok(i, lo):
        steel += [at(xl, -1.5, 10) * Box(tl, 3, 20), at(xl, hook / 2, 12) * Box(tl, hook, 4)]
        cut.append(at(xl, 7.5, -w / 2) * Box(tl, 15, w + 2))
    steel += [at(xr, W + 1.5, 10) * Box(tl, 3, 20), at(xr, W - hook / 2, 12) * Box(tl, hook, 4)]
    cut.append(at(xr, W - 7.5, -w / 2) * Box(tl, 15, w + 2))
    pockets = [at(x, y, 12) * Box(tl + 2, 2 * gd, 4.5) for x, y in ((xl, 0), (xr, W))]
    return dict(steel=union(steel), cut=union(cut), wood=union(pockets))


def wide_snap_hook(i, n, end, lo):
    return snap_hook(i, n, end, lo, wide=True)


def fir_tree(i, n, end, lo):
    steel = at(X, W / 2, 10) * Cylinder(4, 20)
    for k in range(4):
        steel += at(X, W / 2, 3 + 4 * k) * Cone(6, 4, 4)
    return dict(steel=steel, wood=at(X, W / 2, 11) * Cylinder(4.25, 22))


# %% Round 5 - designed for how the frame is made (2026-10-15)
# One identical base frame; the interface is welded on afterwards (or cast in), never bent out
# of the closed tube. "weld" = a separate welded-on part, shown in its own colour (SW).
def headed_stud():
    """Stud-welded headed stud: Ø8 shank 9 mm, Ø16 x 4 mm head (like a shear-connector stud)."""
    return at(X, W / 2, 4.5) * Cylinder(4, 9) + at(X, W / 2, 11) * Cylinder(8, 4)


def locking_slot(end):
    """5's keyhole slot + a wood detent: at end a the 9 mm neck narrows to 7 mm for 3 mm just
    before the stud's seat, so the Ø8 shank squeezes past (0.5 mm wood each side) and clicks in.
    Sliding back out needs the same push again, not just a tap."""
    def slot(x0, x1):  # neck channel 9 wide + head undercut 18 wide x 6 high
        return (at((x0 + x1) / 2, W / 2, 3.5) * Box(x1 - x0, 9, 9)
                + at((x0 + x1) / 2, W / 2, 11) * Box(x1 - x0 + 8, 18, 6))
    if end == "b":
        return slot(-5, X + 4.5)
    ridges = [at(X + 6.5, W / 2 + s * 4, 3.5) * Box(3, 1, 9) for s in (-1, 1)]
    return slot(X - 4.5, X + 25) + at(X + 25, W / 2, 7) * Cylinder(9, 14) - union(ridges)


def stud_keyhole(i, n, end, lo):
    """15: headed stud welded on (stud welding), plank goes down over it and slides 25 mm,
    the detent locks it."""
    return dict(weld=headed_stud(), wood=locking_slot(end))


def hairpin(i, n, end, lo):
    """16: 14's hook, but as laser-cut + press-brake bent 2 mm spring-steel clips welded on in
    the 10 mm gaps. One hairpin per gap holds BOTH neighbouring planks (two arms), an L clip at
    each end of the row: a row of n planks has n + 1 clips. Same stopped pockets as 14."""
    tl, t, hook = 40, 2, 3

    def arm(y0, s):  # arm on the frame face at y0..y0+s*t, hook pointing -s into the pocket
        return (at(X, y0 + s * t / 2, 10) * Box(tl, t, 20)
                + at(X, y0 - s * hook / 2, 12) * Box(tl, hook, 4))

    def foot(y0, y1):
        return at(X, (y0 + y1) / 2, 1) * Box(tl, y1 - y0, 2)
    boxed = lo == "boxed"  # planter floor: the posts hold the row's outer edges, no end clips
    parts = []
    if i < n - 1:                                         # hairpin in the gap above this plank
        parts += [arm(W, 1), arm(P, -1), foot(W, P)]
    elif not boxed:                                       # row end: L clip at the upper edge
        parts += [arm(W, 1), foot(W, W + 6)]
    if i == 0 and lower_ok(i, lo) and not boxed:          # row start: L clip at the lower edge
        parts += [arm(0, -1), foot(-6, 0)]
    pockets = [at(X, y, 12) * Box(tl + 2, 8, 4.5) for y in (0, W)]
    return dict(weld=union(parts), wood=union(pockets))


def tongue(i, n, end, lo):
    """17: slot cut in the tube by the tube laser (no weld, no bend) + a split tongue on the
    plank underside with two 1.5 mm barbs that snap under the tube wall. The 2 mm kerf lets
    the two halves spring together. Locates the plank in x and y; no steel added at all.
    Wood plank: tongue glued/dowelled on, or the plank 3D printed (demonstrator)."""
    tl, tw, depth = 30, 12, 6
    add = at(X, W / 2, -depth / 2) * Box(tl, tw, depth)
    for s in (-1, 1):  # barb: 1.5 mm past the slot, just below the 3 mm wall
        add += at(X, W / 2 + s * (tw / 2 + 0.75), -4.5) * Box(tl, 1.5, 2)
    kerf = at(X, W / 2, (8 - depth - 1) / 2) * Box(tl + 2, 2, 8 + depth + 1)
    return dict(wood_add=add, wood=kerf, cut=at(X, W / 2, -w / 2) * Box(tl, tw, w + 2))


CAST_WALL = 8


def cast_frame(back, holes=False):
    """18: S1's outline as one casting (ductile iron): a C-section open on the inner side,
    8 mm walls, every plank face kept. The interface lugs are cast in (not welded)."""
    c = CAST_WALL
    outer = Pos(0, -TUBE, 0) * Box(TUBE, DEPTH + 2 * TUBE, FRAME_TOP, align=MIN3)
    window = Pos(-1, 0, TUBE) * Box(TUBE + 2, DEPTH, FRAME_TOP - 2 * TUBE, align=MIN3)
    pocket = Pos(c, -TUBE + c, c) * Box(TUBE, DEPTH + 2 * TUBE - 2 * c, FRAME_TOP - 2 * c, align=MIN3)
    pocket -= Pos(0, -c, TUBE - c) * Box(TUBE + 1, DEPTH + 2 * c, FRAME_TOP - 2 * TUBE + 2 * c, align=MIN3)
    fr = outer - window - pocket
    if back:
        fr += back_post()
    return paint(fr, "SK cast side frame with back" if back else "SK cast side frame")


def cast_lug(i, n, end, lo):
    """18: 15's stud and plank, but the mushroom lug is cast into the frame. Rigid features
    only - the flex is in the wood detent, never in the cast iron (it would crack)."""
    return dict(steel=headed_stud(), wood=locking_slot(end))


INTERFACES = [(1, "pin", pin), (2, "fin", fin), (3, "tab", tab), (5, "keyhole", keyhole),
              (7, "snap hook", snap_hook), (8, "fir tree", fir_tree), (14, "wide snap hook", wide_snap_hook),
              (15, "stud keyhole + detent", stud_keyhole), (16, "welded hairpin clip", hairpin),
              (17, "tongue in laser slot", tongue), (18, "cast frame + lug", cast_lug)]
FRAMES = {18: cast_frame}    # interfaces that need their own frame (default: the S1 tube frame)


# %% Build
def mirror_end(s, length):
    return Pos(length, 0, 0) * mirror(s, Plane.YZ)


def engrave(p, n, normal):
    """Engrave n into the plank's largest face pointing along `normal` (world)."""
    face = max((fc for fc in p.faces() if fc.normal_at().dot(Vector(*normal)) > 0.9),
               key=lambda fc: fc.area)
    nrm = face.normal_at()
    x_dir = (1, 0, 0) if abs(nrm.X) < 0.9 else (0, 1, 0)
    s = face.bounding_box().size
    font = min(FONT, 0.7 * sorted((s.X, s.Y, s.Z))[1])  # fits the face's short side
    pl = Plane(origin=face.center() - nrm * ENGRAVE, x_dir=x_dir, z_dir=nrm)
    return p - extrude(pl * Text(str(n), font), amount=ENGRAVE + 1)


def build(n, name, interface, rows, back, show_row_i, show_plank, show_move, show_normal, length_x,
          frame=side_frame):
    """rows of planks on two side frames; the interface is added at both ends of every plank.
    Steel goes to whichever frame (left/right) it lands on; welded-on parts become one SW part
    per frame."""
    frames = {"L": frame(back, holes=False)}
    frame_label = frames["L"].label
    frames["R"] = Pos(length_x, 0, 0) * mirror(frames["L"], Plane.YZ)
    cuts, steel, weld, extra = {"L": [], "R": []}, {"L": [], "R": []}, {"L": [], "R": []}, []
    planks = []
    for r, (locs, length, lo) in enumerate(rows):
        for i, loc in enumerate(locs):
            p = plank(length, holes=False)
            for end in ("a", "b"):
                d = interface(i, len(locs), end, lo)
                tr = (lambda s: s) if end == "a" else (lambda s, ln=length: mirror_end(s, ln))
                if d.get("wood_add") is not None:
                    p += tr(d["wood_add"])
                if d.get("wood") is not None:
                    p -= tr(d["wood"])
                for key, bucket in (("steel", steel), ("cut", cuts), ("weld", weld)):
                    if d.get(key) is not None:
                        s = loc * tr(d[key])
                        bucket["L" if s.center().X < length_x / 2 else "R"].append(s)
                for e in d.get("extra", []):
                    s = loc * tr(e)
                    extra.append(("L" if s.center().X < length_x / 2 else "R", s, e.label))
            p = loc * p
            label = plank(length).label
            if (r, i) == (show_row_i, show_plank):
                p, label = show_move * engrave(p, n, show_normal), label + ", shown"
            planks.append(paint(p, label))
    parts = []
    for side in ("L", "R"):
        fr = frames[side]
        for c in cuts[side]:
            fr -= c
        for s in steel[side]:
            fr += s
        frames[side] = paint(fr, frame_label)
        parts.append(frames[side])
        if weld[side]:
            parts.append(paint(union(weld[side]), "SW welded-on interface"))
    for side, s, label in extra:  # loose parts: never inside the frame
        parts.append(paint(s - frames[side], label))
    return Compound(children=parts + planks, label=f"{n} {name}")


# %% Test models: every interface on every product type, using furniture.py's plank rows.
# New product type to test (e.g. another back) = one more line here + its rows function in
# furniture.py. Long bench / long planter left out until an interface is chosen.
TESTS = [  # (name suffix, rows, frame has back, shown plank (row, index), pull-out move)
    ("", seat_rows(L), False, (0, 0), Pos(0, 0, LIFT)),
    (" + back", seat_rows(L) + back_rows(L), True, (0, 0), Pos(0, 0, LIFT)),
    (" planter", planter_rows(L), False, (1, len(WALL_ZB) - 1), Pos(0, -LIFT, 0)),
]


def test_models(n, name, interface, frames=None):
    """The interface on every TESTS product. frames: {n: frame function} (default this file's)."""
    return [build(n, name + sfx, interface, rows, back, *shown, move, (0, -1, 0), L,
                  (FRAMES if frames is None else frames).get(n, side_frame))
            for sfx, rows, back, shown, move in TESTS]


models = {}  # built on first use (build_all), so a quick check can build just one interface


def build_all():
    if not models:
        models.update({f"{n} {nm}": test_models(n, nm, fn) for n, nm, fn in INTERFACES})
    return models


def grid(y0=0, gap=400, cols=None):
    """One column per interface, its test models behind each other (chair, + back, planter).
    cols: {name: [models]} (default this file's). Returns {name: placed copy}."""
    placed, x = {}, 0
    for col in (build_all() if cols is None else cols).values():
        width, y = max(a.bounding_box().size.X for a in col), y0
        for a in col:
            bb = a.bounding_box()
            d = Pos(x + (width - bb.size.X) / 2 - bb.min.X, y - bb.min.Y, 0)
            placed[a.label] = Compound(children=[paint(d * c, c.label) for c in a.children], label=a.label)
            y += bb.size.Y + gap
        x += width + gap
    return placed


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
