"""Assembly programs for the ONE rig (jigs.py), as JSON for robot_cell.py. One program per
product; every program uses the same kit tray, jigs and AMR.

Cell (world, mm; robot base at the origin on the table top z = 0, facing +x):
  T1  kit tray     on the table                   every part in its own pocket
  J1  build nest   on a riser (RISER)             position A (+ B for the planter's rear wall)
  J2  finish       on a riser                     seating zone / planter zone
  J3  AMR plate    on the AMR's top module        the product leaves the cell on it

Programs (fixture rule: the datum member first, then everything pushed TOWARDS it):
  C1 C2 B1 B2  S1 left on the J1 datum -> 4 seat planks (pushed -x) -> rod (B, pushed) -> S1 right
               (pushed) -> rod quarter turn (B) -> flip to J2 -> back module on J1 (C2 B2: S5 left,
               3 back planks, S5 right) and onto the seat / ornaments (C1 B1) -> J3 -> AMR leaves
  P1 P2        rear wall module in J1 B (post 2 datum, 4 planks, post 3) -> front wall module in
               J1 A (post 0 datum, 4 planks, post 1) -> 8 side planks straight down into the
               front posts -> rear module turned over and down onto them -> planter stood up
               onto J2 -> J3 -> AMR leaves

    python "robot_cell/old six-product cell/cell_sequence.py"   -> sequence_<C1|C2|B1|B2|P1|P2>.json next to it
"""
import json
import os

import numpy as np

from cell_parts import DIMS, HERE, PARTS_DIR, product
import jigs as J

D = DIMS
LIFT = 60
RISER = float(os.environ.get("DAM_RISER", 120))      # J1 / J2 risers: room for the wrist (flip)
J1W = J.T(380, -200, RISER)                           # J1 position A origin in the cell
J2W = J.T(470, -30, RISER)
J3W = J.T(250, 420, RISER) @ np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
#     J3 on the docked AMR, turned 90 deg: the product points away from the robot (+y), like at J2
T1W = J.T(120, -500, 0)
AMR_DRIVE = 1400                                      # the AMR leaves along +y
COLOURS = {"S1": [0.15, 0.15, 0.15, 1], "S5": [0.15, 0.15, 0.15, 1], "S3": [0.6, 0.6, 0.65, 1],
           "S4": [0.15, 0.15, 0.15, 1], "S6": [0.72, 0.55, 0.20, 1], "W": [0.72, 0.52, 0.30, 1]}
T, Rx, inv = J.T, J.Rx, np.linalg.inv


def frame(p, z, x):
    """Pose with origin p, z axis z, x axis (made orthogonal) x."""
    z = np.asarray(z, float) / np.linalg.norm(z)
    x = np.asarray(x, float) - np.dot(x, z) * z
    x /= np.linalg.norm(x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, np.cross(z, x), z, p
    return m


class Seq:
    def __init__(self):
        self.steps = []

    def step(self, label, tool, attach, moves, detach=None):
        self.steps.append(dict(label=label, tool=tool, attach=attach, detach=detach or attach,
                               moves=[[k, None if m is None else (m if np.isscalar(m) else np.round(m, 5).tolist())]
                                      for k, m in moves]))

    def pick_place(self, label, tool, name, pick, place, grip, push=None):
        """pick / place: object poses; grip: tool pose in the object's coordinates;
        push: the object's pose after a straight move from place."""
        up = T(0, 0, LIFT)
        moves = [("J", up @ pick @ grip), ("L", pick @ grip), ("attach", None),
                 ("L", up @ pick @ grip), ("J", up @ place @ grip), ("L", place @ grip)]
        if push is not None:
            moves.append(("L", push @ grip))
            place = push
        moves += [("detach", None), ("L", place @ grip @ T(0, 0, -LIFT))]
        self.step(label, tool, [name], moves)

    def carry(self, label, tool, names, a, b, grip, lift=100, approach=None):
        """Move a group (reference pose a -> b, grip in the reference's coordinates); the last
        part of the move is straight along `approach` (world vector, default straight down)."""
        back = T(0, 0, -LIFT)
        ap = np.eye(4) if approach is None else T(*approach)
        moves = [("J", a @ grip @ back), ("L", a @ grip), ("attach", None),
                 ("L", T(0, 0, lift) @ a @ grip), ("J", T(0, 0, lift) @ ap @ b @ grip),
                 ("L", ap @ b @ grip), ("L", b @ grip), ("detach", None), ("L", b @ grip @ back)]
        self.step(label, tool, names, moves)


# %% Grips (tool pose in the part's own coordinates)
def plank_grip(c, extra):
    L = J.shape(c, np.eye(4)).bounding_box().max.X
    gx = L / 4 if c == "W1" else L / 2                   # W1: clear of the rod rest blade
    return frame((gx, D["W"] / 2, -extra), (0, 0, 1), (-1, 0, 0))  # vacuum on the back face; the
    #                                                              arm (and fingers) point away from the datum


def axis_to(m, world):
    """The local unit axis (+-x, +-y, +-z) that the pose m turns closest to `world`."""
    axes = [np.eye(3)[i] * s for i in range(3) for s in (1, -1)]
    return max(axes, key=lambda a: np.dot(m[:3, :3] @ a, world))


def fingers_from_above(c, m, below_top, close_world=(1, 0, 0)):
    """Fingers from above, `below_top` under the part's top face, closing along close_world."""
    up = axis_to(m, [0, 0, 1])
    s = J.shape(c, np.eye(4)).bounding_box()
    lo, hi = np.array([s.min.X, s.min.Y, s.min.Z]), np.array([s.max.X, s.max.Y, s.max.Z])
    p = (lo + hi) / 2
    k = int(np.argmax(np.abs(up)))
    p[k] = (hi[k] if up[k] > 0 else lo[k]) - np.sign(up[k]) * below_top
    return frame(p, -up, axis_to(m, close_world))


def side_plank_grip(c, m):
    """Fingers across the thickness, 14 mm under the top end (below the end cut)."""
    up = axis_to(m, [0, 0, 1])
    L = J.shape(c, np.eye(4)).bounding_box().max.X
    x = (L - 14) if up[0] > 0 else 14
    return frame((x, D["W"] / 2, D["T"] / 2), -up, axis_to(m, [1, 0, 0]))


POST_END = frame((D["POST"] / 2, D["POST"] / 2, D["POST_H"]), (0, 0, -1), (1, 0, 0))   # vacuum, S4 top end
POST_FOOT = frame((D["POST"] / 2, D["POST"] / 2, 0), (0, 0, 1), (1, 0, 0))             # vacuum, S4 bottom end


def tray(code, n):
    return T1W @ J.tray_pose(code, n)


# %% Programs
def build(code):
    _, inst = product(code)
    lay = J.j1_layout(code)
    seq = Seq()
    if code[0] == "P":
        planter(code, inst, lay, seq)
        final = J2W @ J.j2_pose(code)
        ref, g = "S4_0", POST_END
        seq.carry("planter onto the AMR", "V", list(inst), final @ inst[ref][1], J3W @ J.j2_pose(code) @ inst[ref][1], g)
    else:
        seating(code, inst, lay, seq)
        F = J2W
        g = flip_grip()
        seq.carry(f"{code} onto the AMR", "F", list(inst), F, J3W, g, approach=(0, 0, 40))
    seq.steps.append(dict(label="AMR drives the product away", tool="V", attach=[], detach=[],
                          moves=[["amr", AMR_DRIVE]]))
    return finish(code, inst, lay, seq)


def flip_grip():
    """Fingers on S1 left's front post from outside (-x), in product coordinates."""
    zm = (D["TUBE"] + D["Z0"]) / 2
    return frame((D["TUBE"] / 2, -D["TUBE"] / 2, zm), (1, 0, 0), (0, -1, 0))


def seating(code, inst, lay, seq):
    width = product(code)[0]
    extra = D["W1_EXTRA"] if code[0] == "B" else 0
    s1 = frame((D["TUBE"] / 2, D["DEPTH"] / 2 + 8, 0), (0, 0, 1), (0, -1, 0))     # bottom rail, arm out
    s1r = frame((-D["TUBE"] / 2, D["DEPTH"] / 2 + 8, 0), (0, 0, 1), (0, 1, 0))

    def put(n, label, tool, grip):
        c, a, b = lay[n]
        seq.pick_place(label, tool, n, tray(code, n), J1W @ a, grip, push=None if n in J.DATUM else J1W @ b)

    put("S1L", "S1 left onto the J1 datum", "V", s1)
    for i in range(1, 5):
        put(f"seat{i}", f"seat plank {i}: into the comb, push into S1 left", "V", plank_grip(lay[f"seat{i}"][0], extra))
    if "S3" in inst:
        c, a, b = lay["S3"]
        ang = np.radians(60)                     # quarter turn from 60 deg one side to 30 the other
        p = (J1W @ b @ [width / 2, *D["ROD_C"], 1])[:3]
        rod = inv(J1W @ b) @ frame(p, (0, np.sin(ang), -np.cos(ang)), (0, np.cos(ang), np.sin(ang)))
        put("S3", "rod onto the rest blade, push into S1 left", "F", rod)
    put("S1R", "S1 right: lower, push on", "V", s1r)
    L = J1W @ J.module_pose(code, "seat")
    if "S3" in inst:
        before, turned = J1W @ lay["S3"][2], L
        seq.step("rod: quarter turn, the ramps pull the frames together", "F", ["S3"],
                 [("J", T(0, 0, LIFT) @ before @ rod), ("L", before @ rod), ("attach", None),
                  ("L", turned @ rod), ("detach", None), ("L", turned @ rod @ T(0, 0, -LIFT))])
    seat_mod = [n for n in inst if n.startswith(("S1", "seat", "S3"))]
    g = flip_grip()
    high, back = T(0, 0, 130), T(0, 0, -LIFT)
    seq.step("flip the seat module upright onto J2", "F", seat_mod,
             [("J", L @ g @ back), ("L", L @ g), ("attach", None), ("L", high @ L @ g),
              ("J", high @ J2W @ g), ("L", J2W @ g), ("detach", None), ("L", J2W @ g @ back)])
    if code[1] == "1":
        for n in ("S6L", "S6R"):
            x = D["PEG_C"][0] * (1 if n == "S6L" else -1)
            g = frame((x, D["PEG_C"][1], D["TOP"] + D["ORN_H"] - 2.5), (0, 0, -1), (1, 0, 0))
            seq.pick_place(f"ornament {n[-1]}: peg straight down into the socket", "F", n, tray(code, n),
                           J2W @ inst[n][1], g)
        return
    bx = D["BACK_XF"]
    mid = bx @ np.array([D["TUBE"] / 2, D["TUBE"], D["BACK_LEN"] / 2, 1])
    s5 = frame(mid[:3], -bx[:3, 1], (1, 0, 0))
    s5r = frame(mid[:3] * [-1, 1, 1], -bx[:3, 1], (1, 0, 0))
    put("S5L", "S5 left onto the J1 datum", "V", s5)
    for i in range(1, 4):
        put(f"back{i}", f"back plank {i}: into the comb, push into S5 left", "V", plank_grip(lay[f"back{i}"][0], extra))
    put("S5R", "S5 right: lower, push on", "V", s5r)
    K = J1W @ J.module_pose(code, "back")
    g = inst["back3"][1] @ plank_grip(inst["back3"][0], extra) @ J.Rz180   # arm towards +x: the wrist
    #                                                     stays high when it places the back from behind
    seq.carry("back module: pegs straight down into S1's sockets", "V",
              [n for n in inst if n.startswith(("S5", "back"))], K, J2W, g, lift=D["PEG_L"] + 80,
              approach=(0, 0, D["PEG_L"] + 10))


def planter(code, inst, lay, seq):
    extra = {c: (D["W1_EXTRA"] if c == "W1" else 0) for c in ("W1", "W2")}

    def put(n, label, tool, grip):
        c, a, b = lay[n]
        seq.pick_place(label, tool, n, tray(code, n), J1W @ a, grip, push=None if n in J.DATUM else J1W @ b)

    def post(n):
        return fingers_from_above("S4", J1W @ lay[n][1], 4)

    for wall, (pa, pb), pos in (("rear", (2, 3), "B"), ("front", (0, 1), "A")):
        put(f"S4_{pa}", f"post {pa} onto the J1 {pos} datum", "F", post(f"S4_{pa}"))
        for i in range(1, 5):
            n = f"{wall}{i}"
            put(n, f"{wall} plank {i}: into the comb ({pos}), push into post {pa}", "V",
                plank_grip(lay[n][0], extra[lay[n][0]]))
        put(f"S4_{pb}", f"post {pb}: lower, push on", "F", post(f"S4_{pb}"))
    for side in ("left", "right"):
        for i in range(1, 5):
            n = f"{side}{i}"
            c, a, b = lay[n]
            seq.pick_place(f"{side} plank {i}: straight down into the front posts", "F", n, tray(code, n),
                           J1W @ a, side_plank_grip(c, J1W @ b), push=J1W @ b)
    # rear module: from B, turned over (180 deg about y = the post axis: one wrist turn), down onto
    # the side planks; vacuum on post 2's foot (its end faces +y, away from A)
    rear = [f"S4_{k}" for k in (2, 3)] + [f"rear{i}" for i in range(1, 5)]
    LA = J1W @ J.module_pose(code, "planter")
    seq.carry("rear wall module: turned over, down onto the side planks", "V", rear,
              J1W @ lay["S4_2"][2], LA @ inst["S4_2"][1], POST_FOOT, lift=110, approach=(0, 0, 20))
    # stand the planter up onto J2: vacuum on post 0's top end
    seq.carry("planter: stood up onto J2", "V", list(inst), LA @ inst["S4_0"][1],
              J2W @ J.j2_pose(code) @ inst["S4_0"][1], POST_END, lift=120)


def finish(code, inst, lay, seq):
    parts = {}
    for n, (c, m) in inst.items():
        key = "W" if c.startswith("W") else c[:2]
        parts[n] = dict(stl=str(PARTS_DIR / f"{c}.stl"), colour=COLOURS[key],
                        start=np.round(tray(code, n), 5).tolist(),
                        final=np.round(J3W @ J.j2_pose(code) @ m, 5).tolist())
    return dict(product=code, parts=parts, steps=seq.steps, fixtures=fixtures(), amr=amr())


def fixtures():
    """Jigs (STL) and plain boxes, with their cell poses. parent 'AMR' = rides on the AMR."""
    jd = str(J.JIG_DIR)
    green, steel, yellow, grey = [0.55, 0.75, 0.55, 1], [0.7, 0.7, 0.75, 1], [0.9, 0.8, 0.4, 1], [0.6, 0.6, 0.6, 1]
    f = [dict(name="T1 kit tray", stl=f"{jd}/T1.stl", pose=T1W.tolist(), colour=yellow),
         dict(name="J1 build nest", stl=f"{jd}/J1.stl", pose=J1W.tolist(), colour=green),
         *([dict(name="J1a rod rest blade", stl=f"{jd}/J1a.stl", pose=J1W.tolist(), colour=steel)] if J.d.ROD else []),
         dict(name="J2 finish", stl=f"{jd}/J2.stl", pose=J2W.tolist(), colour=green),
         dict(name="J3 AMR plate", stl=f"{jd}/J2.stl", pose=J3W.tolist(), colour=green, parent="AMR"),
         # risers: narrower than the jigs, so the wrist has room beside them
         dict(name="J1 riser", box=[[J1W[0, 3] + 16, J1W[1, 3] - 70, 0], [J1W[0, 3] + 205, J1W[1, 3] + 88, RISER - J.PLATE_T]], colour=grey),
         dict(name="J2 riser", box=[[J2W[0, 3] + 16, J2W[1, 3] + J.PZ + 5, 0], [J2W[0, 3] + 205, J2W[1, 3] + 60, RISER - J.PLATE_T]], colour=grey),
         dict(name="AMR top module", box=[[J3W[0, 3] - 60, J3W[1, 3] + 20, -367],          # J3 is turned 90 deg:
                                          [J3W[0, 3] - J.PZ - 5, J3W[1, 3] + 195, RISER - J.PLATE_T]],   # its y -> -x
              colour=[0.85, 0.85, 0.88, 1], parent="AMR")]
    return f


def amr():
    """Omron LD-250 (RoboDK library) on the floor (table top 750 above it), under J3."""
    return dict(robot="C:/RoboDK/Library/Add-in - Sensor2D safety sensor with AGV/Parts/Omron-LD-250.robot",
                pose=(T(J3W[0, 3] + 22, J3W[1, 3] + 100, -750) @ J3W[:4, :4] @ T(*(-J3W[:3, 3]))).tolist(),
                drive=[0, 1, 0])


if __name__ == "__main__":
    for code in ("C1", "C2", "B1", "B2", "P1", "P2"):
        s = build(code)
        out = HERE / f"sequence_{code}.json"
        out.write_text(json.dumps(s, indent=1, default=float), encoding="utf-8")
        print(f"{code}: {len(s['steps'])} steps, {len(s['parts'])} parts -> {out.name}", flush=True)
