"""Backrest options on the SHS 50x50x3 tube frame S1, shown side by side in the OCP viewer
(chair C1 + W2 back planks). The option number is engraved in the top back plank.

S1's rear post is x 0..50, y 410..460, z 0..422. Its top (x 0..50, y 410..460, z 422..450) is
the only free spot behind the seat planks, so every back rises from there.

Bolt-on flat-bar backs (orange S5), numbers kept from the flat-plate round:
    2   post-top bracket: foot plate on the rear post's top, 2 bolts into rivnuts, 15 deg arm
    5   seat tray: plate on the top rail under the seat planks, shares their fixings, rises into the arm
Tube backs (the rear post continues up, kinked 15 deg at the top rail):
    15  kinked frame S2: welded, rear post and back are one part
    23  plug-in back: the same kinked tube as a loose part with a 43x43 spigot that drops into
        the rear post through a square hole in the top rail. 0 bolts, 0 welds on site.
Armrests (posts outside the plank zone, so the posts can simply continue up):
    21  S7 = S1 with both posts grown to armrest height + top tube (one welded part)
    20  S6 plug-in armrest: the same inverted U as a loose part, spigots into both posts
Dropped: 3 full-height bracket and 14 centre spine (not liked, 2026-10-15). With the flat-plate frame: 13 pocket hook, 17 fold-down, 18 floor post (they hooked or
bolted onto the flanges), and armrest + back (22): the back planks cover the rear post's top
(x 0..50), so an armrest tube in the same plane can't reach the back post.

Rule: seen from the side, everything below the seat stays inside S1's outline (y -50..460,
z <= 422); the angle only starts at the top rail.

Run:  python back_options.py   (imports the parts from furniture.py, exports nothing)
"""

# %% Setup
from build123d import *
import furniture as f
from furniture import (DEPTH, FRAME_TOP, HOLE_E, L_SHORT, MIN3, N_BACK, N_SEAT, P, SEAT_H, TUBE,
                       TUBE_WALL, GAP, W, hole_y, hole_z, paint, plank, seat, show_row,
                       side_frame, tube)

f.COLORS["S5"] = Color(0.90, 0.55, 0.10)  # every bolt-on / plug-in back part: orange
f.COLORS["S6"] = Color(0.55, 0.25, 0.60)  # plug-in armrest: purple
f.COLORS["S7"] = Color(0.25, 0.25, 0.28)  # side frame with armrest: dark grey

# %% Shared pieces
A_T = 10                     # flat bar thickness
A_TILT = 15
A_Y = DEPTH + 6              # flat-bar arm's front face: 6 mm behind the last seat plank
FOOT_Z = FRAME_TOP + A_T     # top of the foot plate on the rear post (432)
R_Y = DEPTH                  # rear post: y 410..460
OUTLINE_Y = DEPTH + TUBE     # 460: back of S1
SPIGOT, SPIGOT_L = 43, 250   # loose tube in the 44x44 bore of the posts
ARM_Z = SEAT_H + 200         # armrest top
ENGRAVE, FONT = 3, 60        # option number in the top plank: depth, height


def flat(length, holes=(), w=TUBE, t=A_T):
    """Flat bar w (x) by t (y), z = 0..length, Ø8 holes along y at heights `holes`."""
    b = Box(w, t, length, align=MIN3)
    for u in holes:
        b -= Pos(HOLE_E, t / 2, u) * hole_y(t + 2)
    return b


def arm(z, u0, y=A_Y):
    """Flat bar tilted back from (y, z) carrying the back planks. Returns (part, plank locations)."""
    xf = Pos(0, y, z) * Rot(-A_TILT, 0, 0)
    length = u0 + N_BACK * P - GAP + 15
    return (xf * flat(length, [u0 + i * P + W / 2 for i in range(N_BACK)]),
            [xf * Pos(0, 0, u0 + i * P) for i in range(N_BACK)])


def foot():
    """10 mm plate on the rear post's top, 2 bolts down into rivnuts in the top wall.
    Returns (plate, bolt holes to cut from the frame too)."""
    holes = [Pos(HOLE_E, y, FRAME_TOP + 3) * hole_z(A_T + 2 * TUBE_WALL + 2) for y in (R_Y + 12, R_Y + 38)]
    plate = Pos(0, R_Y, FRAME_TOP) * Box(TUBE, TUBE, A_T, align=MIN3)
    for h in holes:
        plate -= h
    return plate, holes


K_U0 = 30                    # first back plank along the kinked tube
K_LEN = K_U0 + N_BACK * P - GAP + 15
K_XF = Pos(0, R_Y, FRAME_TOP) * Rot(-A_TILT, 0, 0)
ABOVE_RAIL = Pos(-100, -100, FRAME_TOP) * Box(300, OUTLINE_Y + 100, 1000, align=MIN3)  # z>=422, y<=460


def kinked_tube():
    """50x50 tube rising from the rear post's top, tilted back, mitred at the top rail and
    trimmed at the frame's back face. Ø8 interface holes in its front wall."""
    t = Pos(TUBE / 2, TUBE / 2, -20) * tube(TUBE, TUBE, K_LEN + 20)
    for i in range(N_BACK):
        t -= Pos(HOLE_E, TUBE_WALL / 2, K_U0 + i * P + W / 2) * hole_y(TUBE_WALL + 2)
    return (K_XF * t) & ABOVE_RAIL


def spigot(y):
    """Loose 43x43 tube standing in a post (post centre y), top flush with the top rail."""
    return Pos(TUBE / 2, y, FRAME_TOP - SPIGOT_L) * tube(SPIGOT, SPIGOT, SPIGOT_L)


def bore(y):
    """Square hole in the top rail's top wall above a post, for a spigot."""
    return Pos(TUBE / 2, y, FRAME_TOP - TUBE_WALL / 2) * Box(SPIGOT, SPIGOT, TUBE_WALL + 2)


def post_up(y, top=ARM_Z - TUBE):
    """Post continued above the top rail, z 422..top, centred on y."""
    return Pos(TUBE / 2, y, FRAME_TOP) * tube(TUBE, TUBE, top - FRAME_TOP)


def arm_rail():
    """Armrest top tube along y over both posts, z ARM_Z-50..ARM_Z."""
    return Pos(TUBE / 2, OUTLINE_Y, ARM_Z - TUBE / 2) * Rot(90, 0, 0) * tube(TUBE, TUBE, DEPTH + 2 * TUBE)


def engrave_top(parts, n):
    """Engrave n into the front face of the highest plank."""
    i = max((i for i, k in enumerate(parts) if k.label.startswith("W")),
            key=lambda i: parts[i].bounding_box().max.Z)
    top = parts[i]
    face = max((fc for fc in top.faces() if fc.normal_at().Y < -0.5), key=lambda fc: fc.area)
    nrm = face.normal_at()
    pl = Plane(origin=face.center() - nrm * ENGRAVE, x_dir=(1, 0, 0), z_dir=nrm)
    parts[i] = paint(top - extrude(pl * Text(str(n), FONT), amount=ENGRAVE + 1), top.label)


def chair(n, name, brackets, planks, extra=(), seat_dz=0, frame=None, cuts=()):
    """C1 seat (planks raised by seat_dz) + each bracket left and mirrored right
    + W2 back planks at `planks` + `extra` parts as they are.
    frame: replaces S1 (left; mirrored for the right). cuts: holes cut into every plank."""
    label = f"{n} {name}"
    parts = [paint(Pos(0, 0, seat_dz) * k, k.label) if seat_dz and k.label.startswith("W") else k
             for k in seat(L_SHORT, False, label).children]
    if frame is not None:
        parts[:2] = [frame, paint(Pos(L_SHORT, 0, 0) * mirror(frame, Plane.YZ), frame.label)]
    for b in brackets:
        parts += [b, paint(Pos(L_SHORT, 0, 0) * mirror(b, Plane.YZ), b.label)]
    parts += [paint(loc * Rot(90, 0, 0) * plank(L_SHORT), "W2 plank short") for loc in planks]
    parts += list(extra)
    if cuts:
        for i, k in enumerate(parts):
            if k.label.startswith("W"):
                parts[i] = paint(k - Compound(children=list(cuts)), k.label)
    if planks:
        engrave_top(parts, n)
    return Compound(children=parts, label=label)


def drilled(holes, label="S1 side frame"):
    fr = side_frame(False)
    for h in holes:
        fr -= h
    return paint(fr, label)


# %% 2 post-top bracket: foot on the rear post's top, arm up from it
def chair_2():
    plate, holes = foot()
    a, locs = arm(FOOT_Z, 20)
    return chair(2, "post-top bracket", [paint(plate + a, "S5 back bracket")], locs, frame=drilled(holes))


# %% 5 seat tray: plate on the top rail under the seat planks, rising into the arm
def chair_5():
    t = 6
    tray = Pos(0, -TUBE, FRAME_TOP) * Box(TUBE, DEPTH + 2 * TUBE, t, align=MIN3)
    for i in range(N_SEAT):  # the seat planks' fixings go through it
        tray -= Pos(HOLE_E, i * P + W / 2, FRAME_TOP + t / 2) * hole_z(t + 2)
    a, locs = arm(FRAME_TOP + t, 30)
    return chair(5, "seat tray", [paint(tray + a, "S5 seat-tray bracket")], locs, seat_dz=t)


# %% 15 kinked frame S2: the rear post continues up and kinks back at the top rail (welded)
def k_locs():
    return [K_XF * Pos(0, 0, K_U0 + i * P) for i in range(N_BACK)]


def chair_15():
    frame = paint(side_frame(False) + kinked_tube(), "S2 side frame, kinked back")
    return chair(15, "kinked frame", [], k_locs(), frame=frame)


# %% 23 plug-in back: the kinked tube as a loose part, spigot into the rear post
def chair_23():
    back = paint(kinked_tube() + spigot(R_Y + TUBE / 2), "S5 plug-in back")
    return chair(23, "plug-in back", [back], k_locs(), frame=drilled([bore(R_Y + TUBE / 2)]))


# %% Armrests: the posts stand outside the plank zone, so they simply continue up
def arm_frame():
    return post_up(-TUBE / 2) + post_up(R_Y + TUBE / 2) + arm_rail()


def chair_21():
    """S7 = S1 grown to armrest height: leg and armrest one welded part."""
    s7 = paint(side_frame(False) + arm_frame(), "S7 side frame with armrest")
    return chair(21, "armrest frame S7", [], [], frame=s7)


def chair_20():
    """S6: the same inverted U as a loose part, spigots into both posts."""
    ys = (-TUBE / 2, R_Y + TUBE / 2)
    s6 = paint(arm_frame() + spigot(ys[0]) + spigot(ys[1]), "S6 plug-in armrest")
    return chair(20, "plug-in armrest S6", [s6], [], frame=drilled([bore(y) for y in ys]))


# %% Show
builders = [chair_2, chair_5, chair_15, chair_23, chair_21, chair_20]
options = {c.label: c for c in (b() for b in builders)}
if __name__ == "__main__":
    from itertools import combinations
    for name, a in options.items():
        s = a.bounding_box().size
        bad = [(p.label, q.label, round((p & q).volume)) for p, q in combinations(a.children, 2)
               if (p & q).volume > 0.5]
        below = [c.label for c in a.children if not c.label.startswith("W")
                 and (c & (Pos(-100, OUTLINE_Y, -1) * Box(1000, 1000, FRAME_TOP + 1, align=MIN3))).volume > 0.5]
        print(f"{name:26s} {s.X:5.0f} x {s.Y:5.0f} x {s.Z:5.0f} mm  overlaps: {bad or 'none'}"
              f"  behind S1 below seat: {below or 'none'}")
    show_row(options, gap=400)
