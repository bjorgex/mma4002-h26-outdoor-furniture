"""DRAFT v6 (2026-10-15): the plank END goes INTO the frame, and the WOOD is the spring.
Chair: 2 x S1 + 4 W2.   Chair with back: + 2 back posts S5 + 3 W2.
Planter: 4 corner posts S4 + 16 W2.   Same plank, same interface.

BACK (S5): a 50 x 50 post leaning back 15 deg from the top of S1's rear post, two interfaces:
    planks  channels on its inner face, the plank interface (3 back planks between the posts)
    frame   a split 30 x 30 peg under the post drops 60 mm into a socket in S1's rear-post top;
            its two prongs' barbs spring out under the underside of S1's solid top rail (the
            catch). One straight move down, can't be pulled up. S1 gets only the socket.
ORNAMENT (S6): on a chair without back the same socket takes a customer ornament (crest, logo)
    on the standard peg: max 45 mm above the frame, rounded, solid. Bronze in the viewer.
STRETCHER (S3 rod, quarter-turn bayonet - replaces the knobs below, 2026-10-16): the rod's end
    lugs pass a keyhole in each bottom rail's inner wall; one 90 deg turn makes them climb
    ramps (mirrored on the right frame = turnbuckle) and pulls the frames together. Nothing
    outside, no tools; one push + one wrist turn for a robot.
(old) STRETCHER (S3 rod + 2 S7 hand knobs): the only screwed joint, by hand, no tools. Ø30 rod
    between the bottom rails at mid length; S1 has a Ø31 hole in the bottom rail's inner wall
    (holds the rod end sideways) and a Ø11 hole in its outer wall for the knob's M10 stud. The
    knobs stand 15 mm out of the frames' outer faces. Benches: same S1, longer rod.

THE INTERFACE (defined once at one plank end, in plank coordinates: end_features)
    channel       1 mm bigger than the plank (97 x 29). The plank end sits 23.5 mm in when
                  fitted. A DEEP channel (47) lets a plank be pushed in to fit the other end; a
                  SHALLOW one (24.5) only takes the fitted end.
    lead-in       the channel mouth flares (cut into the member, nothing sticks out) + 3 mm
                  chamfer on the plank ends
    catch         a 2 mm recess in each channel side wall - no moving metal
    plank spring  TOP HALF only (his idea): a 75 x 50 cut from mid height up, plus a 2 mm
                  horizontal saw cut at mid height (full width, 50 deep, Ø4 stop hole), frees two
                  10 x 13 mm prongs that bend sideways; a 1 mm barb on each long edge, top half.
                  stress = 1.5 E d b / L^2 ~ 30 MPa (wood ~ 40-80), F ~ 0.13 kN per prong.
                  The BOTTOM half stays a solid square 95 x 13 tongue on the channel floor that
                  carries the load: shear at the frame mouth ~ 1.2 MPa (full-depth cut: ~ 2.7).
                  Underside flat and square at both ends; from above a shallow recess, no hole.
    lock          each end's barbs stop the plank one way: locked both ways, can't be lifted
                  (closed outside). Removing: saw the plank through.
    fitting       1 push one end into the DEEP channel, 2 line the other end up with the
                  shallow channel, 3 slide back 23.5 mm until the barbs click. Plank 457 long.

S1 chair side frame: hollow 50 x 50 posts and bottom rail, solid top rail with the 4 seat
channels only (both frames deep: the same part, mirrored).

S4 planter corner post: solid 60 x 60 x 430. Wall planks lie FACE = 9 mm inside the outer faces.
Each post takes two walls: one wall's planks DEEP, the other's SHALLOW, so the two channel
sets never meet inside the post. Going round the planter the deep wall turns like a pinwheel:
every wall is deep at one post and shallow at the other, and the four posts are the same part
turned 90 deg. The planks hold the posts together (each plank locks into two posts). 4 rows.
Top view 530 x 530, mirror-symmetric across both diagonals (the channels are hidden).
Open: the floor (a liner standing inside the posts for now).

VIEWER: 4 rows x 6 columns. Rows (back to front): 1 complete, 2 assembly step (one plank pushed
deep, before it slides back and clicks; its prongs are drawn unbent, so it shows as an
overlap), 3 exploded, 4 cut open. Columns: C1 chair, C2 chair with back, B1 bench, B2 bench
with back, P1 planter, P2 planter long. C1 and B1 carry the ornaments.
(Old list:) chair A assembled, B front plank at step 3 (prongs drawn unbent), C exploded, D cut
open at mid plank height; planter E assembled, F exploded (posts pulled out), G cut open at
z = 200 (look down into the posts); chair with back H assembled, I exploded, J cut through
the left posts' middle (look from the side: peg in the socket, barbs under the catch).
Run:  python insert_draft.py   (exports nothing)
"""

# %% Setup
from math import atan2, degrees
from build123d import *
from furniture import COLORS, MIN3, paint

COLORS["S4"] = Color(0.08, 0.08, 0.08)  # planter corner post: black like S1

# %% Scale: full size or the 3D-printed demonstrator (2026-10-16: bench 1500 -> 200 = 1 : 7.5,
# FDM 0.4 mm nozzle, PLA). The PRODUCTS are scaled; the INTERFACES are scaled too but never
# below what prints and works: pr(full, minimum). Minimums (PLA, 0.4 nozzle, 0.2 layers):
# walls >= 1.2 (3 lines), sliding clearance 0.25 per side, barbs >= 0.5, snap prongs >= 2 wide
# and long enough to stay under ~30 MPa in PLA (E ~ 3.5 GPa), gaps >= 0.6. Print the planks
# lying flat (prongs bend along the layers) and the frames on their side (channels vertical).
DEMO = True
ROD = not DEMO                # stretcher rod S3: full-size benches only, not on the prototype
S = 1 / 7.5 if DEMO else 1.0


def sc(v):
    """Product size: scaled."""
    return v * S


def pr(v, minimum):
    """Interface size: scaled, but never below the printable minimum (demonstrator only)."""
    return max(v * S, minimum) if DEMO else v


W, T, GAP = sc(95), sc(28), sc(10)  # plank section, gap between planks
P = W + GAP                   # pitch
SEAT_H, N_SEAT = sc(450), 4
WALL = pr(3, 1.2)
TUBE = pr(50, 10)             # frame members (demo: 10, not 6.7 - room for channel, socket, rod)
SEAT_Z = SEAT_H - T           # seat plank underside
Z0 = SEAT_Z - pr(8, 2)        # top rail bottom
FACE = pr(9, 1.2)             # ONE plank offset: plank face this far inside the member face - seat,
                              # back and planter alike, so one build jig (comb) holds every module
TOP = SEAT_H + FACE           # top rail top, a little above the seat
DEPTH = N_SEAT * P - GAP      # clear span between two members' inner faces
WIDTH = DEPTH + 2 * TUBE      # chair
IN = pr(23.5, 4)              # plank end inside each member when fitted
LP = DEPTH + 2 * IN           # W2 plank length
DEEP, SHALLOW = TUBE - WALL, IN + pr(1, 0.5)   # channel depths (DEEP >= 2 IN for the fitting)
CLEAR = pr(0.5, 0.25)
FUN_T, FUN_Y, FUN_Z = pr(8, 1.5), pr(3, 0.5), pr(1.5, 0.3)   # mouth flare: depth, width, thickness
CHAMFER = pr(3, 0.5)
PRONG = pr(10, 2)
SLOT_W, SLOT_L, ROOT_R = W - 2 * PRONG, pr(50, 10), pr(5, 1)   # the cut: width (y), length (x)
BARB_H = pr(1.0, 0.5)
KERF_H = pr(2, 0.6)           # horizontal saw cut at mid height under the prongs
KERF_Z = T / 2 - KERF_H / 2
BARB_Z = (KERF_Z + KERF_H + pr(2, 0.3), T - pr(2, 0.3))   # barbs only on the top half
BARB_X = tuple(v * IN / 23.5 for v in (8, 16, 18))        # slope, flat, straight face: inside IN
RECESS = pr(2, 0.8)
# planter
POST = pr(60, 12)
SKIN = FACE                   # wall planks this far inside the post's outer faces
N_ROW, ROW_Z0 = 4, sc(10)
POST_H = ROW_Z0 + N_ROW * P - GAP + sc(10)
SIDE = DEPTH + 2 * POST


def box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=MIN3)


def rect(x, yc, zc, w, h):
    """Rectangle in the plane x = const, centred (yc, zc), w along y, h along z."""
    face = (Plane(origin=(x, yc, zc), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * Rectangle(w, h)).faces()[0]
    return face.outer_wire()


# %% The interface at ONE plank end, in fitted plank coordinates:
# plank x 0..LP, y 0..W, z 0..T; this end at x = 0, the member's inner face at x = IN.
def end_features(depth):
    """Channel (depth from the inner face) + flared mouth + barb recesses: all to cut."""
    c = CLEAR
    cut = box(IN - depth, -c, -c, depth + 1, W + 2 * c, T + 2 * c)
    cut += Solid.make_loft([rect(IN - FUN_T, W / 2, T / 2, W + 2 * c, T + 2 * c),
                            rect(IN + 0.01, W / 2, T / 2, W + 2 * c + 2 * FUN_Y, T + 2 * c + 2 * FUN_Z)])
    x0, x1 = BARB_X[0] - 0.5, BARB_X[2] + 0.5
    z0, z1 = BARB_Z[0] - 0.5, BARB_Z[1] + 0.5
    for y in (-c - RECESS, W + c):
        cut += box(x0, y, z0, x1 - x0, RECESS, z1 - z0)
    return cut


def other_end(s, lp=LP):
    """A feature drawn at end a, mirrored onto end b of a plank lp long."""
    return Pos(lp, 0, 0) * mirror(s, Plane.YZ)


def barbs():
    xa, xb, xc = BARB_X
    out = []
    for y_face, s in ((0, -1), (W, 1)):
        pts = [(xa, y_face), (xb, y_face + s * BARB_H), (xc, y_face + s * BARB_H), (xc, y_face)]
        out.append(Pos(0, 0, BARB_Z[0]) * extrude(Polygon(*pts, align=None),
                                                  amount=BARB_Z[1] - BARB_Z[0], dir=(0, 0, 1)))
    return out[0] + out[1]


def slot():
    """Top half only: the 75 x 50 cut from the mid-height saw cut up, which frees two
    10 x 13 mm prongs; the saw cut (z 13..15) runs the full width, 50 deep, ending in a Ø4
    stop hole. The bottom half (z 0..13) stays a solid square tongue that carries the load."""
    y0, r = W / 2 - SLOT_W / 2, ROOT_R
    z0 = KERF_Z + KERF_H                                     # top of the saw cut
    h = T + 1 - z0
    s = box(-1, y0, z0, SLOT_L - r + 1, SLOT_W, h) + box(-1, y0 + r, z0, SLOT_L + 1, SLOT_W - 2 * r, h)
    for y in (y0 + r, y0 + SLOT_W - r):
        s += Pos(SLOT_L - r, y, z0 + h / 2) * Cylinder(r, h)
    s += box(-1, -1, KERF_Z, SLOT_L + 1, W + 2, KERF_H)                       # saw cut
    s += Pos(SLOT_L, W / 2, KERF_Z + KERF_H / 2) * Rot(90, 0, 0) * Cylinder(pr(2, 0.4), W + 2)  # stop hole
    return s


W1_H = sc(45)                 # bench / long planter plank height: stiff enough for the long span
STEP_X = IN + pr(2, 0.5)      # W1 steps down to 28 just outside the frame (sloped 45 deg)


def step_cut(extra):
    """Underside material removed at end a of a W1: everything below z = 0 up to STEP_X, then
    a 45 deg slope down to the full height (no square inside corner for a split to start)."""
    flat = box(-1, -1, -extra - 1, STEP_X + 1, W + 2, extra + 1)
    pts = [(STEP_X, 0), (STEP_X + extra, -extra), (STEP_X + extra, -extra - 1), (STEP_X, -extra - 1)]
    slope = Pos(0, W / 2, 0) * extrude(Plane.XZ * Polygon(*pts, align=None), amount=W / 2 + 1, both=True)
    return flat + slope


def plank(lp=LP):
    """W2 (457 x 95 x 28) or W1 (1447 x 95 x 45, ends stepped to 28 underneath). The top 28 mm
    is the same for both (plank z 0..28), so both fit the same channels; W1's extra depth hangs
    below (z -17..0). Ends chamfered on top and sides, underside square."""
    extra = 0 if lp == LP else W1_H - T
    p = Pos(0, 0, -extra) * Box(lp, W, T + extra, align=MIN3)
    for i in (0, -1):
        p = chamfer(p.edges().group_by(Axis.X)[i].filter_by(lambda e: e.center().Z > -extra + 0.1), CHAMFER)
    if extra:
        p -= step_cut(extra) + other_end(step_cut(extra), lp)
    p += barbs() + other_end(barbs(), lp)
    p -= slot() + other_end(slot(), lp)
    return paint(p, plank_label(lp))


def plank_label(lp):
    return "W2 plank (insert draft)" if lp == LP else "W1 plank long (insert draft)"


def planks_at(locs, lp=LP):
    return [paint(loc * plank(lp), plank_label(lp)) for loc in locs]


# %% Chair: S1
def seat_locs():
    return [Pos(TUBE - IN, i * P, SEAT_Z) for i in range(N_SEAT)]


def side_frame():
    """S1 (left), x 0..50: hollow posts and bottom rail, solid top rail, 4 deep seat channels."""
    y0, y1 = -TUBE, DEPTH + TUBE
    w = WALL
    f = (box(0, y0, 0, TUBE, TUBE, TOP) + box(0, DEPTH, 0, TUBE, TUBE, TOP)
         + box(0, y0, 0, TUBE, y1 - y0, TUBE) + box(0, y0, Z0, TUBE, y1 - y0, TOP - Z0))
    f -= (box(w, y0 + w, w, TUBE - 2 * w, TUBE - 2 * w, Z0 - w)
          + box(w, DEPTH + w, w, TUBE - 2 * w, TUBE - 2 * w, Z0 - w)
          + box(w, y0 + w, w, TUBE - 2 * w, y1 - y0 - 2 * w, TUBE - 2 * w))
    cut = end_features(DEEP)
    for loc in seat_locs():
        f -= loc * cut
    return paint(f, "S1 side frame (insert draft)")


S1 = side_frame()


# %% Planters: 4 S4 posts. A wall is drawn once as a "front wall" running +x from the post at
# the origin (end a SHALLOW there, end b DEEP in the next post); each side of the planter is
# that wall moved to its corner and turned 90 deg further (pinwheel), so P1 (square) and P2
# (long) use the same 4 posts - only the wall planks' length differs (W2 / W1).
def wall_locs():
    """Front wall: planks along x, thickness 4..32 mm inside the front face (y), width up."""
    return [Plane(origin=(POST - IN, SKIN + T, ROW_Z0 + i * P), x_dir=(1, 0, 0), z_dir=(0, -1, 0)).location
            for i in range(N_ROW)]


def wall_cuts(lp):
    a, b = end_features(SHALLOW), other_end(end_features(DEEP), lp)
    return [loc * a for loc in wall_locs()] + [loc * b for loc in wall_locs()]


def planter(name, span_x=DEPTH, span_y=DEPTH, e=0, step=False):
    """Clear spans between the posts' inner faces: span_x (front/rear), span_y (sides).
    step: the front wall's top plank pushed deep into the front-right post."""
    X, Y = span_x + 2 * POST, span_y + 2 * POST
    sides = [(Location(), span_x), (Pos(X, 0, 0) * Rot(0, 0, 90), span_y),
             (Pos(X, Y, 0) * Rot(0, 0, 180), span_x), (Pos(0, Y, 0) * Rot(0, 0, 270), span_y)]
    cuts, planks = [], []
    for k, (xf, span) in enumerate(sides):
        lp = span + 2 * IN
        cuts += [xf * c for c in wall_cuts(lp)]
        locs = wall_locs()
        if k == 0 and step:
            locs[-1] = locs[-1] * Pos(DEEP_SHIFT, 0, 0)
        planks += [paint(xf * p, p.label) for p in planks_at(locs, lp)]
    parts = []
    for (x, y), (sx, sy) in zip(((0, 0), (X - POST, 0), (X - POST, Y - POST), (0, Y - POST)),
                                ((-1, -1), (1, -1), (1, 1), (-1, 1))):
        p = box(x, y, 0, POST, POST, POST_H)
        for c in cuts:
            p -= c
        parts.append(paint(Pos(sx * e, sy * e, 0) * p, "S4 planter corner post (insert draft)"))
    return Compound(children=parts + planks, label=name)


# %% Chair back: 2 back posts S5 + 3 W2. Each post has two interfaces:
#   planks  channels on its inner face (the plank interface above; deep in both, mirrored)
#   frame   a vertical peg under it drops into a socket in S1's rear-post top. The peg is split
#           (slot + two prongs with barbs, the planks' snap idea); the barbs spring out under
#           the bottom face of S1's solid top rail, which is the catch. One straight move down.
COLORS["S5"] = Color(0.08, 0.08, 0.08)  # back post: black like S1
BACK_TILT, N_BACK, BACK_U0 = 15, 3, sc(40)  # deg back from vertical; planks start 40 up the post
BACK_LEN = BACK_U0 + N_BACK * P - GAP + sc(20)
BACK_XF = Pos(0, DEPTH, TOP) * Rot(-BACK_TILT, 0, 0)   # post: local y 0..50 (front face y = 0)
PEG, PEG_L, PEG_SLOT, PEG_SLOT_L = pr(30, 6), pr(60, 14), pr(10, 2), pr(40, 10)  # peg, slot
PEG_C = (TUBE / 2, DEPTH + TUBE / 2)                    # peg centre (x, y): S1's rear post
PEG_BARB = (pr(1.5, 0.5), pr(6, 1.5), pr(2, 0.6))                                  # barb out, slope height, flat height
CATCH_Z = Z0                                            # underside of the solid top rail (414)


def back_locs():
    """Back planks in world coordinates: x along the plank, width up the post, thickness
    FACE (9 mm) behind the post's front face - the same offset as seat and planter."""
    return [BACK_XF * Plane(origin=(TUBE - IN, FACE + T, BACK_U0 + i * P),     # front face FACE behind the post face
                            x_dir=(1, 0, 0), z_dir=(0, -1, 0)).location for i in range(N_BACK)]


def peg():
    """Split peg under the post (world), barbs on the two prongs' outer faces (x)."""
    cx, cy = PEG_C
    z0 = TOP - PEG_L
    p = box(cx - PEG / 2, cy - PEG / 2, z0, PEG, PEG, PEG_L)
    p -= box(cx - PEG_SLOT / 2, cy - PEG / 2 - 1, z0 - 1, PEG_SLOT, PEG + 2, PEG_SLOT_L + 1)
    out, rise, flat = PEG_BARB
    top = CATCH_Z - pr(0.5, 0.2)                        # straight face just under the catch
    for s in (-1, 1):
        x_face = cx + s * PEG / 2
        pts = [(x_face, top - flat - rise), (x_face + s * out, top - flat),
               (x_face + s * out, top), (x_face, top)]       # in x-z, sloped at the bottom
        b = Plane.XZ * Polygon(*pts, align=None)
        p += Pos(0, cy, 0) * extrude(b, amount=PEG / 2 - pr(2, 0.5), both=True)
    return p


def back_post():
    """S5 (left): 50 x 50 solid post leaning back 15 deg from S1's rear-post top, cut flat to
    sit on it (the lean starts above the frame); plank channels on its inner face; the peg below."""
    body = BACK_XF * box(0, 0, -0.4 * TUBE, TUBE, TUBE, BACK_LEN + 0.4 * TUBE)
    body &= box(-1, -1000, TOP, TUBE + 2, 3000, 1000)
    cut = end_features(DEEP)
    for loc in back_locs():
        body -= loc * cut
    return paint(body + peg(), "S5 back post (insert draft)")


def socket():
    """The socket in S1's rear-post top (0.25 mm clearance round the peg)."""
    cx, cy = PEG_C
    c = pr(0.25, 0.2)
    return box(cx - PEG / 2 - c, cy - PEG / 2 - c, TOP - PEG_L - 1, PEG + 2 * c, PEG + 2 * c, PEG_L + 2)


# %% Stretcher rod S3: the ONE part turned in, by hand or robot, no tools. Ø30 rod between the
# two bottom rails at mid length, nothing on the outside (outer walls closed). Frame interface:
# a keyhole in the bottom rail's inner wall + two ramps welded behind it (bayonet, below).
# Fitting (frames still loose, in a jig with the right frame on a slide): push the rod in with
# its lugs up/down through the slots, turn it 90 deg: the lugs climb the ramps at both ends and
# pull the frames together to the planks' spacing. Then the planks. Same S1 on chairs and
# benches - only the rod length changes.
ROD_D = pr(30, 4.5)
ROD_HOLE = ROD_D + 2 * CLEAR
ROD_C = (DEPTH / 2, TUBE / 2)           # (y, z): middle of the bottom rail


# Quarter-turn bayonet (A, chosen 2026-10-16): the rod turns into the frames like a turnbuckle,
# but with ONE 90 deg turn - robot-friendly (one push + one wrist turn, no regrip) and by hand.
LUG_R0, LUG_W, LUG_T = ROD_D / 2, pr(8, 1.6), pr(6, 1.5)   # lugs: from the rod surface, width, thickness
LUG_R1 = (TUBE - 2 * WALL) / 2 - pr(1, 0.25)               # lug tip radius: just inside the rail
RAMP_H = pr(3, 1)                                          # ramps rise 3 mm over the quarter turn
ROD_END = TUBE - WALL - RAMP_H - LUG_T - pr(2, 0.5)          # rod end inside the rail (x 36)


def to_rail(shape):
    """Local (axis z, from the inner wall's back face into the rail) -> world, left frame:
    local z -> -x, local y -> +z, local x -> -y; origin on the rod axis at x = 47."""
    y, z = ROD_C
    return Plane(origin=(TUBE - WALL, y, z), x_dir=(0, -1, 0), z_dir=(-1, 0, 0)).location * shape


def ramps():
    """Two quarter-ring ramps (r 15.5..21.5) welded on the inside of the inner wall: 3 mm thick
    where the lugs end up (local +x / -x = world -y / +y), sloping to ~0 at the slots (+-z).
    Mirrored on the right frame, so they slope the other way there - the turnbuckle."""
    ring = Cylinder(LUG_R1 + pr(0.5, 0.2), RAMP_H, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
        - Cylinder(ROD_HOLE / 2, 4 * RAMP_H)          # centred: clears the whole ring height
    quarter = ring & Box(2 * TUBE, 2 * TUBE, RAMP_H + 2, align=(Align.MIN, Align.MIN, Align.MIN))
    slope = atan2(RAMP_H, LUG_R1 + pr(0.5, 0.2))
    cutter = Pos(0, 0, RAMP_H) * Rot(-degrees(slope), 0, 0) * Box(100, 100, 50, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ramp = quarter - cutter
    return to_rail(ramp + Rot(0, 0, 180) * ramp)


def keyhole():
    """Ø31 hole + two lug slots (9 wide, up and down) through the bottom rail's inner wall."""
    y, z = ROD_C
    hole = Pos(TUBE - WALL / 2, y, z) * Rot(0, 90, 0) * Cylinder(ROD_HOLE / 2, WALL + 2)
    return hole + Pos(TUBE - WALL - 1, y - (LUG_W + 2 * CLEAR) / 2, z - LUG_R1 - CLEAR) * Box(
        WALL + 2, LUG_W + 2 * CLEAR, 2 * (LUG_R1 + CLEAR), align=MIN3)


def rod(span):
    """S3: Ø30 rod, end 11 mm inside each rail (x 36 .. width - 36), two lugs at each end,
    turned to their locked position (+-y, on top of the ramps)."""
    y, z = ROD_C
    width = span + 2 * TUBE
    r = Pos(width / 2, y, z) * Rot(0, 90, 0) * Cylinder(ROD_D / 2, width - 2 * ROD_END)
    lugs = [Pos(ROD_END + pr(2, 0.5), y + s * (LUG_R0 + LUG_R1) / 2, z) *
            Box(LUG_T, LUG_R1 - LUG_R0, LUG_W, align=(Align.MIN, Align.CENTER, Align.CENTER))
            for s in (-1, 1)]
    end = lugs[0] + lugs[1]
    r += end + Pos(width, 0, 0) * mirror(end, Plane.YZ)
    return paint(r, "S3 stretcher rod")





S1B = paint(S1 - socket() - keyhole() + ramps(), "S1 side frame (insert draft)")   # + socket, bayonet
S5 = back_post()


def rod_parts(width, e=0, before_turn=False):
    """The stretcher rod for a product whose frames' outer faces are x = 0 and width.
    before_turn: pushed in, lugs still up/down at the slots - before the quarter turn."""
    r = rod(width - 2 * TUBE)
    if before_turn:
        y, z = ROD_C
        r = paint(Pos(0, y, z) * Rot(90, 0, 0) * Pos(0, -y, -z) * r, r.label)
    return [r]

# %% Ornament S6: closes the socket on a chair without back. The customer's part (city crest,
# logo...): a laser-cut plate on the standard peg. Max 45 mm above the frame (< half a plank
# width), rounded outline (no points at the back of a seat), solid and low (no lever to yank).
COLORS["S6"] = Color(0.72, 0.55, 0.20)  # ornament: bronze, to show it's the custom part
ORN_BASE, ORN_H, ORN_T = pr(5, 1), W * 45 / 95, pr(10, 2)   # base, height (< half a plank width), plate
ORN_W = pr(46, PEG + 2)                                     # base / plate width (covers the socket)


def ornament():
    """S6 (left): standard split peg + base covering the socket + a crest plate facing out
    (x), round top. The ring engraved on both faces marks where the customer's crest goes."""
    cx, cy = PEG_C
    r = ORN_W / 2
    z_rect = ORN_H - ORN_BASE - r                       # straight part under the round top
    base = box(cx - r, cy - r, TOP, ORN_W, ORN_W, ORN_BASE)
    plate = box(cx - ORN_T / 2, cy - r, TOP + ORN_BASE, ORN_T, ORN_W, z_rect)
    plate += Pos(cx, cy, TOP + ORN_BASE + z_rect) * Rot(0, 90, 0) * Cylinder(r, ORN_T)
    plate &= box(cx - ORN_T, cy - r, TOP + ORN_BASE, 2 * ORN_T, ORN_W, ORN_H)
    zc = TOP + ORN_BASE + z_rect
    for s in (-1, 1):                                   # crest placeholder ring, 1 mm deep
        ring = Cylinder(ORN_W * 14 / 46, 2 * pr(1, 0.4)) - Cylinder(ORN_W * 11 / 46, 3 * pr(1, 0.4))
        plate -= Pos(cx + s * ORN_T / 2, cy, zc) * Rot(0, 90, 0) * ring
    return paint(peg() + base + plate, "S6 ornament (customer crest)")


S6 = ornament()


# %% Benches B1 / B2: the chair stretched, NO middle support (his rule: benches don't have one).
# Same S1 (end frames), same S5 back posts, same rod and knobs; seat and back planks W1 = 1400
# span + 2 x 23.5 = 1447 long. Load (1000 N mid span on ONE plank, E ~ 11 GPa):
#   95 x 28: ~ 28 MPa, ~ 30 mm sag (too much)  ->  W1 95 x 45: ~ 11 MPa, ~ 7 mm (shared: less).
# W1's ends step down to 28 underneath, so it fits the same channels (see plank()).
BENCH = sc(1500)                         # bench outer width (demo: 200)
BENCH_LP = BENCH - 2 * TUBE + 2 * IN     # W1: 1447
LONG_SPAN = BENCH_LP - 2 * IN            # 1400: P2's long walls use the same W1
DEEP_SHIFT = DEEP - IN                   # 23.5: a plank pushed to the bottom of its deep channel


def seating(name, width, lp, back=False, ornaments=False, e=0, step=False):
    """Chair (width 510, W2) or bench (width 1500, W1): end frames S1, seat planks, rod + knobs;
    back: + 2 S5 back posts + 3 back planks; ornaments: S6 in the sockets instead.
    e: exploded (frames out sideways, back / ornaments lifted). step: the front seat plank
    pushed deep into the left frame - the moment before it slides back and clicks."""
    lift = Pos(0, 0, 2 * e)
    parts = [paint(Pos(-e, 0, 0) * S1B, S1B.label),
             paint(Pos(width + e, 0, 0) * mirror(S1B, Plane.YZ), S1B.label)]
    if width > WIDTH and ROD:            # the stretcher rod is for benches only (chairs: S1's
        parts += rod_parts(width, e, before_turn=step)  # keyhole stays, on the rail's inner face)
    for i, loc in enumerate(seat_locs()):
        if i == 0 and step:
            loc = Pos(-DEEP_SHIFT, 0, 0) * loc
        parts += planks_at([loc], lp)
    top = []
    if back:
        top = [paint(Pos(-e, 0, 0) * S5, S5.label), paint(Pos(width + e, 0, 0) * mirror(S5, Plane.YZ), S5.label)]
        top += planks_at(back_locs(), lp)
    elif ornaments:
        top = [paint(Pos(-e, 0, 0) * S6, S6.label), paint(Pos(width + e, 0, 0) * mirror(S6, Plane.YZ), S6.label)]
    parts += [paint(lift * p, p.label) for p in top]
    return Compound(children=parts, label=name)


def cut_x(a, name, x):
    """Everything at x < x removed: look from the side into the left posts."""
    keep = Pos(x, -2000, -2000) * Box(5000, 5000, 5000, align=MIN3)
    return Compound(children=[paint(c & keep, c.label) for c in a.children
                              if (c & keep).volume > 0], label=name)


def cut_at(a, name, z):
    """Everything above height z removed: look down into it."""
    keep = Pos(-2000, -2000, -2000) * Box(5000, 5000, 2000 + z, align=MIN3)
    return Compound(children=[paint(c & keep, c.label) for c in a.children
                              if (c & keep).volume > 0], label=name)


# %% All products x all views. Columns: the products; rows: the views (viewer layout below).
PRODUCTS = {  # code + name: builder(name, e=..., step=...)
    "C1 chair": lambda n, **k: seating(n, WIDTH, LP, ornaments=True, **k),
    "C2 chair with back": lambda n, **k: seating(n, WIDTH, LP, back=True, **k),
    "B1 bench": lambda n, **k: seating(n, BENCH, BENCH_LP, ornaments=True, **k),
    "B2 bench with back": lambda n, **k: seating(n, BENCH, BENCH_LP, back=True, **k),
    "P1 planter": lambda n, **k: planter(n, **k),
    "P2 planter long": lambda n, **k: planter(n, span_x=LONG_SPAN, **k),
}


def cut_view(code, a, name):
    """Seating: cut lengthwise through the left frame (plank end, peg, rod from the side).
    Planters: cut at 200 mm height (look down into the posts)."""
    return cut_at(a, name, sc(200)) if code.startswith("P") else cut_x(a, name, PEG_C[0])


VIEWS = {  # row name: how to build that view of a product
    "1 complete": lambda code, b, n: b(n),
    "2 assembly step": lambda code, b, n: b(n, step=True),
    "3 exploded": lambda code, b, n: b(n, e=sc(100) if code.startswith(("C2", "B")) else sc(150)),
    "4 cut open": lambda code, b, n: cut_view(code, b(n), n),
}
def build_grid():
    """All products x all views (built only when asked - importing this file stays quick)."""
    return {view: {code: make(code, b, f"{view[2:]}: {code}") for code, b in PRODUCTS.items()}
            for view, make in VIEWS.items()}


def show_grid(grid, gap=sc(400), row_gap=sc(600)):
    """One row per view, the products left to right in the same columns."""
    from ocp_vscode import Camera, get_port, show
    if get_port() is None:
        print("OCP viewer not open (Ctrl+Shift+P -> 'OCP CAD Viewer: Open viewer'), skipping show")
        return
    widths = {code: max(grid[v][code].bounding_box().size.X for v in grid) for code in PRODUCTS}
    layout, y = [], 0
    for view, row in grid.items():
        depth, x = max(a.bounding_box().size.Y for a in row.values()), 0
        for code, a in row.items():
            bb = a.bounding_box()
            d = Pos(x + (widths[code] - bb.size.X) / 2 - bb.min.X, y - bb.min.Y, 0)
            layout.append(Compound(children=[paint(d * c, c.label) for c in a.children], label=a.label))
            x += widths[code] + gap
        y -= depth + row_gap                     # next row towards the viewer's front
    show(*layout, names=[a.label for a in layout], reset_camera=Camera.RESET)


# %% Check + show
if __name__ == "__main__":
    from itertools import combinations
    grid = build_grid()
    models = {a.label: a for row in grid.values() for a in row.values()}
    for name, a in models.items():
        bad = [(p.label, q.label, round((p & q).volume)) for p, q in combinations(a.children, 2)
               if (p & q).volume > 0.5]
        s = a.bounding_box().size
        print(f"{name:34s} {s.X:5.0f} x {s.Y:4.0f} x {s.Z:5.0f} mm  {len(a.children):2d} parts  "
              f"overlaps: {len(bad) or 'none'}", flush=True)
    show_grid(grid)
