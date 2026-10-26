"""Modular outdoor furniture: black steel frames + wooden planks (build123d).

MODULAR SYSTEM: as few unique parts as possible, every product built from the same parts.

PRODUCTS                          PARTS (count per product)
    B1  bench                         W1 x4  S1 x2  S3 x1
    B2  bench with back               W1 x7  S2 x2  S3 x1
    C1  chair                         W2 x4  S1 x2
    C2  chair with back               W2 x7  S2 x2
    P1  planter square                W2 x20 S1 x2
    P2  planter long (trough)         W1 x12 W2 x8 S1 x2

PARTS
    W1  plank long  1500 mm           S1  side frame (welded 50x50 square tube)
    W2  plank short  510 mm           S2  side frame with back
        (510 = S1's outer depth, so one W2 is the chair seat, the planter floor and every
         planter wall)
                                      S3  bench stretcher
    (S4 planter frame: retired, the planters now use S1)

THE INTERFACE (shared by every plank and every metal part):
    plank section  W x T = 95 x 28 mm, gap between planks 10 mm -> pitch P = 105 mm
    each plank end rests on a 50 mm wide steel bearing zone (= the tube width)
    one fixing per plank end, 25 mm from the end, centred on the width, at that 105 mm pitch
    (marked here as a Ø8 hole; the screwless options are in interface_options.py)
-> any plank fits any frame; only the plank length differs: W1 1500 mm, W2 510 mm.

S1 is a welded rectangle of 50x50x3 square tube (mitred corners): top rail, bottom rail and two
posts. The posts stand OUTSIDE the plank zone (y -50..0 and 410..460), so the window between
them is exactly the seat depth. Benches/chairs: seat planks on the top rail. Planters use the
same two S1s: 4 floor planks on the bottom rails, and every wall plank on the OUTSIDE of the
frames, 4 rows high (z 6..416): front/rear walls on the posts' outer faces, end walls on the
frames' outer faces. Each wall covers exactly its own face, corners open (28 x 28), so the top
view is mirror-symmetric across both diagonals. A plastic/metal insert holds the soil.
The bench adds a stretcher tube.

Units: mm everywhere. Run:  python furniture.py   (or Run Cell)
Outputs: parts/*.stl (one per unique part), assemblies/*.stl and *.3mf (3MF keeps colours).
"""

# %% Parameters
from pathlib import Path
from build123d import *

try:
    OUT = Path(__file__).parent
except NameError:  # Run Cell / Jupyter kernel
    OUT = Path.cwd()

MIN3 = (Align.MIN, Align.MIN, Align.MIN)
# one colour per part code, so the parts are easy to tell apart in the viewer
COLORS = {
    "W1": Color(0.86, 0.66, 0.40),  # plank long: light oak
    "W2": Color(0.52, 0.32, 0.16),  # plank short: dark walnut
    "S1": Color(0.08, 0.08, 0.08),  # side frame: black
    "S2": Color(0.20, 0.32, 0.55),  # side frame with back: steel blue
    "S3": Color(0.70, 0.18, 0.12),  # bench stretcher: red
}
PLANTER_WOOD = COLORS["W1"]  # both planters: all planks one colour, W1 and W2 alike

# interface
W, T, GAP = 95, 28, 10       # plank width, thickness, gap
P = W + GAP                  # hole pitch on all metal parts
BEAR = 50                    # bearing zone under each plank end
HOLE_D = 8
HOLE_E = BEAR / 2            # hole distance from plank end

# plank lengths
L_LONG = 1500
L_SHORT = 510                # = DEPTH + 2 * TUBE: the frame's outer depth

# seat side frame (bench + chair)
SEAT_H = 450                 # top of seat planks
N_SEAT = 4                   # seat planks -> depth 410
DEPTH = N_SEAT * P - GAP
TUBE = BEAR                  # square tube 50 x 50: the bearing zone is the tube top
TUBE_WALL = 3
FRAME_TOP = SEAT_H - T       # top of the top rail = underside of the seat planks (422)
# the old flat-plate frame; back_options.py still builds on these
PLATE_T = 10                 # frame plate thickness (x)
BAR = 40                     # frame bar width in the side view
FL_T = 6                     # flange thickness
FRAME_H = SEAT_H - T - FL_T  # top of frame plate = underside of flange

# backrest
N_BACK = 3
BACK_TILT = 15               # deg from vertical
BACK_BAR = 50                # back post: one bar from the floor, diagonally through the
BACK_Y0 = 305                #   side frame (braced triangle), up behind the seat
BACK_U0 = 480                # first back plank, measured along the back post
BACK_LEN = BACK_U0 + N_BACK * P - GAP + 15

# bench stretcher (side to side, in the frames' top rail, under the seat)
STR = 40                     # square tube
END_T = 6                    # end plate
STR_Y = DEPTH / 2
STR_Z = FRAME_TOP - TUBE / 2  # centred in the top rail
STR_DY = 30                  # two bolts per end at +-30 mm

# planter: floor in the frame window on the bottom rails, walls on the outside of the frames
N_WALL = 4
WALL_ZB = [6 + i * P for i in range(N_WALL)]     # wall planks (bottom edges): 6..321, top 416
N_FLOOR = N_SEAT             # the window is the seat depth: 4 planks, same pattern as the seat
FLOOR_Y0 = 0
END_Y0 = -TUBE               # end walls cover the frame's outer face: y -50..460
END_HOLES_Y = (END_Y0 + HOLE_E, END_Y0 + L_SHORT - HOLE_E)  # = -25 and 435, the post centres


def hole_z(depth):  # Ø8 hole, axis along Z, centred
    return Cylinder(HOLE_D / 2, depth)


def hole_y(depth):  # Ø8 hole, axis along Y
    return Rot(90, 0, 0) * Cylinder(HOLE_D / 2, depth)


def hole_x(depth):  # Ø8 hole, axis along X
    return Rot(0, 90, 0) * Cylinder(HOLE_D / 2, depth)


def paint(part, label):
    """Label starts with the part code; the colour follows from it."""
    part.color, part.label = COLORS[label[:2]], label
    return part


# %% Parts
def plank(length, holes=True):
    """Local: X = length, Y = width, Z = thickness. Holes at both ends."""
    p = Box(length, W, T, align=MIN3)
    for x in (HOLE_E, length - HOLE_E) if holes else ():
        p -= Pos(x, W / 2, T / 2) * hole_z(T + 2)
    return paint(p, {L_LONG: "W1 plank long", L_SHORT: "W2 plank short"}[length])


BACK_XFORM = Pos(0, BACK_Y0, 0) * Rot(-BACK_TILT, 0, 0)
ABOVE_FLOOR = Pos(-5000, -5000, 0) * Box(10000, 10000, 5000, align=MIN3)


def back_post():
    """50x50 tube post, built upright (front face y=0 facing -Y), tilted, cut at the floor.
    The back planks sit on its front face."""
    post = Pos(TUBE / 2, BACK_BAR / 2, 0) * tube(TUBE, BACK_BAR, BACK_LEN)
    for i in range(N_BACK):
        post -= Pos(HOLE_E, TUBE_WALL / 2, BACK_U0 + i * P + W / 2) * hole_y(TUBE_WALL + 2)
    return (BACK_XFORM * post) & ABOVE_FLOOR


def side_frame(back=False, holes=True):
    """Left side frame. Local: X = 0..50 inward, Y = depth (front y=0), Z up.
    Welded rectangle of 50x50x3 tube: posts at y -50..0 and 410..460, rails z 0..50 and 372..422.
    Every interface hole goes through ONE wall: the one the plank lies against.
    holes=False leaves the plank interface out (for interface_options.py)."""
    w = TUBE_WALL
    outer = Pos(0, -TUBE, 0) * Box(TUBE, DEPTH + 2 * TUBE, FRAME_TOP, align=MIN3)
    window = Pos(-1, 0, TUBE) * Box(TUBE + 2, DEPTH, FRAME_TOP - 2 * TUBE, align=MIN3)
    cavity = Pos(w, -TUBE + w, w) * Box(TUBE - 2 * w, DEPTH + 2 * TUBE - 2 * w, FRAME_TOP - 2 * w,
                                        align=MIN3)
    cavity -= Pos(0, -w, TUBE - w) * Box(TUBE, DEPTH + 2 * w, FRAME_TOP - 2 * TUBE + 2 * w, align=MIN3)
    f = outer - window - cavity
    if back:
        f += back_post()
    if holes:
        for i in range(N_SEAT):  # seat planks: top wall of the top rail
            f -= Pos(HOLE_E, i * P + W / 2, FRAME_TOP - w / 2) * hole_z(w + 2)
        for i in range(N_FLOOR):  # planter floor: top wall of the bottom rail
            f -= Pos(HOLE_E, FLOOR_Y0 + i * P + W / 2, TUBE - w / 2) * hole_z(w + 2)
        for zb in WALL_ZB:
            for y in (-TUBE + w / 2, DEPTH + TUBE - w / 2):  # front/rear walls: outer wall of each post
                f -= Pos(HOLE_E, y, zb + W / 2) * hole_y(w + 2)
            for y in END_HOLES_Y:  # end walls: the frame's outer wall, at the post centres
                f -= Pos(w / 2, y, zb + W / 2) * hole_x(w + 2)
    for dy in (-STR_DY, STR_DY):  # stretcher bolts: inner wall of the top rail
        f -= Pos(TUBE - w / 2, STR_Y + dy, STR_Z) * hole_x(w + 2)
    return paint(f, "S2 side frame with back" if back else "S1 side frame")

def tube(w, d, h):
    """Closed rectangular tube, centred in XY, z = 0..h."""
    return Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN)) - Pos(
        0, 0, TUBE_WALL
    ) * Box(w - 2 * TUBE_WALL, d - 2 * TUBE_WALL, h - 2 * TUBE_WALL,
            align=(Align.CENTER, Align.CENTER, Align.MIN))


def stretcher(length):
    """40x40 tube + end plates, x = 0..length; placed between the frames' inner faces (x = 50)."""
    s = Pos(END_T, STR_Y, STR_Z) * Rot(0, 90, 0) * tube(STR, STR, length - 2 * END_T)
    for x in (0, length - END_T):
        plate = Pos(x, STR_Y, STR_Z) * Box(END_T, 2 * BAR, BAR, align=(Align.MIN, Align.CENTER, Align.CENTER))
        for dy in (-STR_DY, STR_DY):
            plate -= Pos(x + END_T / 2, STR_Y + dy, STR_Z) * hole_x(END_T + 2)
        s += plate
    return paint(s, "S3 bench stretcher")


# %% Plank rows: where every plank lies (the one place; products and interface tests use it)
# A row = (plank locations, plank length, lo). Each location puts the plank's z = 0 face on the
# frame face it rests on, so an interface drawn in plank coordinates fits every row
# (interface_options.py). lo: what is below plank 0: True = nothing, None = the seat (back rows),
# "boxed" = the row runs exactly post to post, nothing fits before plank 0 or after the last.
# New product type = a new rows function.
def on_face(origin, x_dir, z_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location


def seat_rows(length):
    return [([Pos(0, i * P, FRAME_TOP) for i in range(N_SEAT)], length, True)]


def back_rows(length):
    return [([BACK_XFORM * Pos(0, 0, BACK_U0 + i * P) * Rot(90, 0, 0) for i in range(N_BACK)],
             length, None)]


def planter_rows(length):
    """Floor on the bottom rails; every wall on the outside of the frames, corners open."""
    return [
        ([Pos(0, FLOOR_Y0 + i * P, TUBE) for i in range(N_FLOOR)], length, "boxed"),             # floor
        ([on_face((0, -TUBE, zb), (1, 0, 0), (0, -1, 0)) for zb in WALL_ZB], length, True),       # front
        ([on_face((length, DEPTH + TUBE, zb), (-1, 0, 0), (0, 1, 0)) for zb in WALL_ZB], length, True),  # rear
        ([on_face((0, END_Y0 + L_SHORT, zb), (0, -1, 0), (-1, 0, 0)) for zb in WALL_ZB], L_SHORT, True),  # left end
        ([on_face((length, END_Y0, zb), (0, 1, 0), (1, 0, 0)) for zb in WALL_ZB], L_SHORT, True),  # right end
    ]


def lay(rows):
    """Plain planks (Ø8 holes) on every location of every row."""
    # a fresh plank per location: moved copies of one plank share their geometry, and the
    # 3MF mesher in all_models.py hangs on that after the STL export has meshed it once
    return [paint(loc * plank(length), plank(length).label)
            for locs, length, _ in rows for loc in locs]


# %% Assemblies
def frames(back, length):
    left = side_frame(back)
    return [left, paint(Pos(length, 0, 0) * mirror(side_frame(back), Plane.YZ), left.label)]


def seat(length, back, name, stretch=False):
    parts = frames(back, length)
    if stretch:
        parts.append(paint(Pos(TUBE, 0, 0) * stretcher(length - 2 * TUBE), "S3 bench stretcher"))
    parts += lay(seat_rows(length) + (back_rows(length) if back else []))
    return Compound(children=parts, label=name)


def planter(length, name):
    """Two S1 frames + the planter rows."""
    parts = frames(False, length) + lay(planter_rows(length))
    for p in parts[2:]:  # one wood colour for every planter (labels keep the part codes)
        p.color = PLANTER_WOOD
    return Compound(children=parts, label=name)

products = {
    "B1 bench": seat(L_LONG, False, "B1 bench", stretch=True),
    "B2 bench with back": seat(L_LONG, True, "B2 bench with back", stretch=True),
    "C1 chair": seat(L_SHORT, False, "C1 chair"),
    "C2 chair with back": seat(L_SHORT, True, "C2 chair with back"),
    "P1 planter": planter(L_SHORT, "P1 planter"),
    "P2 planter long": planter(L_LONG, "P2 planter long"),
}
unique_parts = {p.label: p for p in (
    plank(L_LONG), plank(L_SHORT), side_frame(False), side_frame(True),
    stretcher(L_LONG - 2 * TUBE),
)}

# %% Check: interface + sizes
RUN = __name__ == "__main__"  # False when imported (e.g. by back_options.py)
for name, a in products.items() if RUN else []:
    s = a.bounding_box().size
    print(f"{name:20s} {s.X:7.0f} x {s.Y:5.0f} x {s.Z:5.0f} mm")
if RUN:
    print(f"plank pitch {P} mm, hole Ø{HOLE_D} at {HOLE_E} mm from end")

# %% Export
if RUN:
    (OUT / "parts").mkdir(exist_ok=True)
    (OUT / "assemblies").mkdir(exist_ok=True)
    for name, p in unique_parts.items():
        export_stl(p, str(OUT / "parts" / f"{name}.stl"))
    for name, a in products.items():
        export_stl(a, str(OUT / "assemblies" / f"{name}.stl"))
        m = Mesher()
        for child in a.children:
            m.add_shape(child)
        m.write(str(OUT / "assemblies" / f"{name}.3mf"))
    print("exported to", OUT)


# %% Show in OCP CAD Viewer (VS Code panel), side by side
def show_row(items, gap=300):
    """Send {name: Compound} to the OCP viewer, laid out side by side along x."""
    from ocp_vscode import Camera, get_port, show

    if get_port() is None:
        print("OCP viewer not open (Ctrl+Shift+P -> 'OCP CAD Viewer: Open viewer'), skipping show")
        return
    x, layout = 0, []
    for name, a in items.items():
        bb = a.bounding_box()
        dx = x - bb.min.X
        layout.append(Compound(children=[paint(Pos(dx, 0, 0) * c, c.label)
                                         for c in a.children], label=name))
        x += bb.size.X + gap
    show(*layout, names=list(items), reset_camera=Camera.RESET)


if RUN:
    show_row(products)
