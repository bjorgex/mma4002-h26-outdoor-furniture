"""The ONE robot rig that builds every product (demonstrator 1:7.5): jigs + layout.

  T1  kit tray     every part type has ONE fixed pocket, in the orientation the robot places it
                   in; the operator fills the kit for the order, each product program picks only
                   its pockets. Poka-yoke: a key in each plank pocket fits the plank's end cut
                   (face down only), the same key in the side-plank rack, a pin in S1's socket.
  J1  build nest   every module is built on it, plank faces DOWN on one comb (pitch P):
                     A  seat module (C, B, upside down) / back module (C2, B2, face down) /
                        planter lying on its front wall, built up like a box
                     B  the planter's rear wall module (built while A holds the front)
                   one plank offset everywhere (insert_draft.FACE) makes that possible.
  J2  finish       seating zone + planter zone; the product is located against a datum.
  J3  AMR plate    the same part as J2, on the mobile robot: ships the product.

Fixture rules (qa_notes, "What makes a good jig?"):
  3-2-1 + one datum   in J1 the LEFT member (S1 L, S5 L, planter post 0 / post 2) lies with its
                      outer face on the END STOP (x = 0); the comb locates the planks; everything
                      else is pushed -x TOWARDS the datum, so every reaction goes into the stop.
  nest only where it locates   comb ribs in the plank gaps fix the pitch P; nothing near the
                      plank ends; the envelopes of S4 / S5 are relieved.
  lead-ins            chamfers on every rib, lip and stop.
  rod rest            0.8 mm laser-cut steel blade in the gap between seat planks 2 and 3.

J1 coordinates: x along the planks (datum face x = 0), y across (row 0 = plank at y -W..0),
z up, plate top z = 0, plank faces at z = FACE. J2: product coordinates (seating at the
origin, planter at y = PZ). T1: tray corner at the origin, plate top z = TRAY_T.

    python "robot_cell/old six-product cell/jigs.py"   -> builds the jigs, checks every part in them, exports STL
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE.parent.parent / "Furniture concepts"))   # insert_draft, furniture

import insert_draft as d  # noqa: E402
from build123d import (Align, Axis, Box, Color, Location, Plane, Polygon, Pos, Text,  # noqa: E402
                       chamfer, export_stl, extrude)

from cell_parts import PARTS_DIR, ROD_BEFORE_TURN, ROD_Z, mat, planter_xf, product, unique_parts  # noqa: E402

S_PUSH = d.IN + 3                     # parts placed this far +x, then pushed towards the datum
CLR = 0.3                             # printed clearance per side
PLATE_T, WALL_H, LIP_H = 4, 5, 3
RIB_W, RIB_H = 0.8, 2.5               # comb ribs in the 1.33 mm gaps between planks
BLADE_T = 0.8
YB = 80                               # J1: position B, this far +y of position A
PZ = -110                             # J2: planter zone IN FRONT of the seating zone (behind it the
#                                       wrist needs room to put the back module on from behind)
TRAY_T, ROD_HOLDER, RACK_H = 3, 15, 15
X0, X1 = -12, d.BENCH + S_PUSH + 16   # J1 plate: chair, bench and both planters
Y_FRONT, Y_BACK = d.TUBE, -(d.DEPTH + d.TUBE)   # seat module in J1: frame posts' outer faces
JIG_DIR = PARTS_DIR / "jigs"


def box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN))


def lead_in(b, c=1.0):
    return chamfer(b.edges().group_by(Axis.Z)[-1], c)


def Rx(deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    m = np.eye(4)
    m[1:3, 1:3] = [[c, -s], [s, c]]
    return m


def T(x=0, y=0, z=0):
    m = np.eye(4)
    m[:3, 3] = x, y, z
    return m


Rz180 = np.diag([-1.0, -1.0, 1.0, 1.0])     # half turn about z (e.g. a tool about its own axis)


def loc(m):
    """4x4 -> build123d Location."""
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetValues(*[float(m[r, c]) for r in range(3) for c in range(4)])
    return Location(t)


def vol(a, b):
    c = a & b
    return c.volume if c is not None else 0.0


_PARTS = {}


def shape(code, m, label=""):
    """Unique part `code` placed by the 4x4 m."""
    if not _PARTS:
        _PARTS.update(unique_parts())
    s = loc(m) * _PARTS[code]
    s.label = label or code
    return s


# %% Where every instance goes in J1 / J2 (4x4 poses, product -> jig coordinates)
def lying(rot, plank_poses):
    """Translate a rotated module so its planks' faces (plank z = T) sit at z = FACE and the
    highest plank row is row 0 (y -W..0)."""
    face_z, top_y = [], []
    for m in plank_poses:
        a = rot @ m
        face_z.append((a @ [d.W / 2, d.W / 2, d.T, 1])[2])
        top_y.append(max((a @ [d.W / 2, y, d.T / 2, 1])[1] for y in (0, d.W)))
    assert np.ptp(face_z) < 1e-6, "planks not in one plane"
    return T(0, -max(top_y), d.FACE - face_z[0]) @ rot


def module_pose(code, module):
    """Product -> J1 for 'seat', 'back' or 'planter' (the planter lying on its front wall)."""
    _, inst = product(code)
    if module == "seat":
        return lying(Rx(180), [inst[f"seat{i}"][1] for i in (1, 2, 3, 4)])
    if module == "back":
        n = inst["back1"][1][:3, :3] @ [0, 0, 1]
        return lying(Rx(np.degrees(np.arctan2(n[1], n[2])) + 180), [inst[f"back{i}"][1] for i in (1, 2, 3)])
    return lying(Rx(90), [inst[f"front{i}"][1] for i in (1, 2, 3, 4)])


DATUM = ("S1L", "S5L", "S4_0", "S4_2")       # members that go straight onto the end stop


def j1_layout(code):
    """{instance: (part, pose in J1 when placed, pose after the push or the final J1 pose)}.
    Seating: seat module (and back module, later, same position A). Planter: front wall +
    side planks in A, rear wall module in B."""
    _, inst = product(code)
    out = {}
    if code[0] in "CB":
        mods = ["seat"] + (["back"] if code[1] == "2" else [])
        for mod in mods:
            L = module_pose(code, mod)
            for n, (c, m) in inst.items():
                if (mod == "seat" and n.startswith(("S1", "seat", "S3"))) or \
                        (mod == "back" and n.startswith(("S5", "back"))):
                    fin = L @ (ROD_BEFORE_TURN if n == "S3" else m)
                    out[n] = (c, fin if n in DATUM else T(S_PUSH) @ fin, fin)
        return out
    L = module_pose(code, "planter")
    _, _, _, xf = planter_xf(code)
    LR = T(0, YB) @ L @ np.linalg.inv(mat(xf[2]))        # rear module in B, turned like the front
    for n, (c, m) in inst.items():
        if n.startswith(("front", "S4_0", "S4_1")):
            fin = L @ m
        elif n.startswith(("rear", "S4_2", "S4_3")):
            fin = LR @ m
        else:                                             # side planks: straight down into A
            out[n] = (c, T(0, 0, 20) @ L @ m, L @ m)
            continue
        out[n] = (c, fin if n in DATUM else T(S_PUSH) @ fin, fin)
    return out


def j2_pose(code):
    """Product -> J2 (seating zone at the origin, planter zone at y = PZ)."""
    return T(0, PZ) if code[0] == "P" else np.eye(4)


# %% J1
def build_nest():
    """J1 body (PLA) and rod rest blade (steel)."""
    body = box(X0, X1, Y_BACK - 8, YB + 12, -PLATE_T, 0)
    body += lead_in(box(-6, 0, Y_BACK + 3, Y_FRONT - 3, 0, WALL_H))                       # datum A
    body += lead_in(box(-6, 0, YB - 58, YB + 3, 0, WALL_H))                                # datum B
    body += lead_in(box(X0 + 2, X1 - 2, Y_FRONT + CLR, Y_FRONT + CLR + 3, 0, WALL_H))    # fence
    body += lead_in(box(X0 + 2, X1 - 2, Y_BACK - CLR - 3, Y_BACK - CLR, 0, WALL_H))      # rear lip
    gaps = [-(i * d.P - d.GAP / 2) for i in range(1, d.N_SEAT)] + [CLR + RIB_W / 2,
                                                                   -(d.DEPTH + CLR + RIB_W / 2)]
    zones = [(d.TUBE + 4, d.WIDTH - d.TUBE - 4), (d.WIDTH + S_PUSH + 14, d.BENCH - d.TUBE - 4)]
    for y0 in (0, YB):                                        # positions A and B
        for xa, xb in zones:
            body += box(xa, xb, y0 - d.DEPTH, y0, 0, d.FACE)                              # pads
            for y in gaps:                                                                # comb
                body += lead_in(box(xa + 6, xb - 2, y0 + y - RIB_W / 2, y0 + y + RIB_W / 2, 0,
                                    d.FACE + RIB_H), 0.3)
    blade = None
    if d.ROD:                                             # rod rest (benches with the stretcher)
        xm, ym = d.BENCH / 2, -d.DEPTH / 2                # rod axis over the gap of planks 2 and 3
        top = d.TOP - ROD_Z - d.ROD_D / 2 - 0.3
        v = Plane.XZ * Polygon((xm - 12, -PLATE_T), (xm + 12, -PLATE_T), (xm + 12, top), (xm + 3, top),
                               (xm, top - 3), (xm - 3, top), (xm - 12, top), align=None)
        blade = Pos(0, ym + BLADE_T / 2, 0) * extrude(v, amount=BLADE_T)
        body -= box(xm - 12.2, xm + 12.2, ym - BLADE_T / 2 - 0.1, ym + BLADE_T / 2 + 0.1, -PLATE_T,
                    d.FACE + RIB_H + 1)
        blade.color, blade.label = Color(0.7, 0.7, 0.75), "J1a rod rest blade (0.8 steel, laser)"
    for code in ("C2", "B2", "P1", "P2"):                     # relieve S4 / S5 envelopes
        for n, (c, a, b) in j1_layout(code).items():
            if c in ("S4", "S5L", "S5R"):
                for m in (a, b):
                    bb = shape(c, m).bounding_box()
                    body -= box(max(bb.min.X, 0) - CLR, bb.max.X + CLR, bb.min.Y - CLR, bb.max.Y + CLR,
                                bb.min.Z - CLR, bb.max.Z + CLR)
    for txt, x, y in (("A  DATUM", 1, Y_FRONT + 5.2), ("B  DATUM", 1, YB + 6), ("chair R", d.WIDTH + 1, Y_FRONT + 5.2),
                      ("bench R", d.BENCH - 22, Y_FRONT + 5.2)):
        body -= Pos(x, y, -0.4) * extrude(Text(txt, 3, align=(Align.MIN, Align.CENTER)), 0.4)
    body.color, body.label = Color(0.55, 0.75, 0.55), "J1 build nest (PLA)"
    return body, blade


# %% J2 = J3
def finish_jig(label="J2 finish (PLA)"):
    """Seating located by the front posts (rail) and S1 left's outer face (stop); the planter by
    its front posts (rail) and post 0's outer face (stop). Low lips: the rod and the flip's
    fingers pass over them."""
    j = box(-12, d.BENCH + 15, PZ - 12, d.DEPTH + d.TUBE + 12, -PLATE_T, 0)
    for y0, y1 in ((-d.TUBE, d.DEPTH + d.TUBE), (PZ, PZ + d.DEPTH + 2 * d.POST)):
        j += lead_in(box(-6, d.BENCH + 10, y0 - CLR - 3, y0 - CLR, 0, LIP_H), 0.8)       # front rail
        j += lead_in(box(-6, -CLR, y0, y1 - 2, 0, LIP_H), 0.8)                           # x stop
    for txt, y in (("SEATING", -17), ("PLANTER", PZ - 7)):
        j -= Pos(2, y, -0.4) * extrude(Text(txt, 3, align=(Align.MIN, Align.CENTER)), 0.4)
    j.color, j.label = Color(0.55, 0.75, 0.55), label
    return j


# %% T1 kit tray
def flat_rot(code, n):
    return j1_layout(code)[n][1]


def kit(code):
    """{instance: pocket} for a product."""
    _, inst = product(code)
    if code[0] == "P":
        k = {f"front{i}": f"flat{i}" for i in range(1, 5)} | {f"rear{i}": f"flat{i + 4}" for i in range(1, 5)}
        k |= {"S4_0": "S4a1", "S4_2": "S4a2", "S4_1": "S4b1", "S4_3": "S4b2"}
        k |= {f"left{i}": f"rack{i}" for i in range(1, 5)} | {f"right{i}": f"rack{i + 4}" for i in range(1, 5)}
        return k
    k = {f"seat{i}": f"flat{i}" for i in range(1, 5)} | {"S1L": "S1L", "S1R": "S1R"}
    k |= {f"back{i}": f"flat{i + 4}" for i in range(1, 4) if f"back{i}" in inst}
    k |= {n: n for n in ("S3", "S5L", "S5R") if n in inst}
    k |= {n: "S6a" if n == "S6L" else "S6b" for n in ("S6L", "S6R") if n in inst}
    return k


# pocket -> (x, y) of the part's box corner on the tray, and the stand it sits on
POCKETS = {**{f"flat{k + 1}": (8, 8 + 20 * k, "flat") for k in range(8)},
           "S1L": (212, 8, "lip"), "S1R": (232, 8, "lip"),
           "S4a1": (252, 8, "lip"), "S4a2": (272, 8, "lip"), "S4b1": (252, 80, "lip"), "S4b2": (310, 80, "lip"),
           **{f"rack{k + 1}": (214 + 13 * k, 150, "rack") for k in range(8)},
           "S5L": (8, 172, "lip"), "S5R": (60, 172, "lip"),
           "S6a": (112, 180, "peg"), "S6b": (136, 180, "peg"), "S3": (160, 186, "rod")}
TRAY = (0, 330, 0, 215)


def first_pose(code, n):
    """Orientation an instance is first placed in (J1, or J2 for the ornaments)."""
    if n.startswith("S6"):
        return j2_pose(code) @ product(code)[1][n][1]
    return j1_layout(code)[n][1]


def tray_pose(code, n):
    """Pose of an instance in its kit-tray pocket (tray coordinates)."""
    c = product(code)[1][n][0]
    m = first_pose(code, n)
    m = np.block([[m[:3, :3], np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]])
    bb = shape(c, m).bounding_box()
    x, y, kind = POCKETS[kit(code)[n]]
    z = ROD_HOLDER if kind == "rod" else TRAY_T         # ornaments: peg tip on the plate, base
    return T(x - bb.min.X, y - bb.min.Y, z - bb.min.Z) @ m   # on the holder (hole = peg length)


def end_cut_key(c, m):
    """Key rib for a plank lying in pocket pose m: inside the end cut (top-half slot) of the
    plank end that is lowest / at -x, 1 mm into the cut. Returns a tray-coordinate box."""
    L = shape(c, np.eye(4)).bounding_box().max.X
    z0 = d.KERF_Z + d.KERF_H                                  # slot from z0 to T (plank coords)
    pts = []
    for xa in ((0.6, d.SLOT_L - 2), (L - d.SLOT_L + 2, L - 0.6)):
        cand = [m @ [x, y, z, 1] for x in xa for y in (d.W / 2 - d.SLOT_W / 2 + 0.6, d.W / 2 + d.SLOT_W / 2 - 0.6)
                for z in (d.T, d.T - 1.0)]                    # the 1 mm of the slot at the face
        pts.append(np.array(cand)[:, :3])
    p = min(pts, key=lambda a: (a[:, 2].min(), a[:, 0].min()))
    lo, hi = p.min(0), p.max(0)
    return box(lo[0], hi[0], lo[1], hi[1], lo[2] - 0.01, hi[2])


def kit_tray(codes=("C1", "C2", "B1", "B2", "P1", "P2")):
    """T1, built from the pockets every product uses (each pocket from its largest part)."""
    t = box(TRAY[0], TRAY[1], TRAY[2], TRAY[3], 0, TRAY_T)
    feats, keys = {}, []
    for code in codes:
        _, inst = product(code)
        for n, pk in kit(code).items():
            c = inst[n][0]
            m = tray_pose(code, n)
            bb = shape(c, m).bounding_box()
            f = feats.setdefault(pk, [bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z])
            f[0], f[1], f[2], f[3] = min(f[0], bb.min.X), max(f[1], bb.max.X), min(f[2], bb.min.Y), max(f[3], bb.max.Y)
            if c in ("W1", "W2"):
                keys.append(end_cut_key(c, m))
    for pk, (xa, xb, ya, yb, zb) in feats.items():
        kind = POCKETS[pk][2]
        if kind in ("flat", "lip"):
            ring = box(xa - CLR - 1.6, xb + CLR + 1.6, ya - CLR - 1.6, yb + CLR + 1.6, TRAY_T, TRAY_T + LIP_H)
            ring -= box(xa - CLR, xb + CLR, ya - CLR, yb + CLR, TRAY_T, TRAY_T + LIP_H + 1)
            t += lead_in(ring, 0.6)
        elif kind == "rack":
            blk = box(xa - 2, xb + 2, ya - 2, yb + 2, TRAY_T, TRAY_T + RACK_H)
            blk -= box(xa - CLR, xb + CLR, ya - CLR, yb + CLR, TRAY_T, TRAY_T + RACK_H + 1)
            t += lead_in(blk, 0.6)
        elif kind == "peg":
            blk = box(xa, xb, ya, yb, TRAY_T, TRAY_T + d.PEG_L)
            cx, cy = (xa + xb) / 2, (ya + yb) / 2
            h = d.PEG / 2 + d.PEG_BARB[0] + CLR             # the peg's barbs stick out
            blk -= box(cx - h, cx + h, cy - h, cy + h, TRAY_T, TRAY_T + d.PEG_L + 1)
            t += blk
        elif kind == "rod":
            for x in (xa + 10, xb - 22):
                blk = box(x, x + 12, ya - 3, yb + 3, TRAY_T, ROD_HOLDER)
                t += blk
        t -= Pos(xa, ya - 2.4, TRAY_T - 0.4) * extrude(Text(pk, 2, align=(Align.MIN, Align.CENTER)), 0.4)
    for k in keys:
        t += k
    t.color, t.label = Color(0.9, 0.8, 0.4), "T1 kit tray (PLA)"
    return t


def socket_key(code="C1"):
    """Pin up into S1's socket from the tray floor (S1L / S1R pockets): stops a front/back swap."""
    out = []
    for n in ("S1L", "S1R"):
        m = tray_pose(code, n)
        cx, cy = d.PEG_C
        p = m @ [cx * (1 if n == "S1L" else -1), cy, d.TOP, 1]
        h = d.PEG / 2 - 0.6
        out.append(box(p[0] - h, p[0] + h, p[1] - h, p[1] + h, TRAY_T, TRAY_T + 4))
    return out


def all_jigs():
    body, blade = build_nest()
    tray = kit_tray()
    for k in socket_key():
        tray += k
    out = {"J1": body, "J2": finish_jig(), "T1": tray}
    if blade is not None:
        out["J1a"] = blade
    return out


if __name__ == "__main__":
    only = sys.argv[1:]                                  # e.g. "J2 T1": rebuild just those jigs
    if only:
        jigs = {}
        if "T1" in only:
            jigs["T1"] = kit_tray()
            for k in socket_key():
                jigs["T1"] += k
        if "J2" in only:
            jigs["J2"] = finish_jig()
    else:
        jigs = all_jigs()
    JIG_DIR.mkdir(parents=True, exist_ok=True)
    for name, s in jigs.items():
        export_stl(s, str(JIG_DIR / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.3)
        print(name, [round(v, 1) for v in s.bounding_box().size], "mm ->", f"parts/jigs/{name}.stl", flush=True)
    j1, j2, t1 = jigs.get("J1"), jigs.get("J2"), jigs.get("T1")
    for code in ("C1", "C2", "B1", "B2", "P1", "P2"):
        _, inst = product(code)
        bad = []
        for n, (c, a, b) in (j1_layout(code).items() if j1 else ()):
            for tag, m in (("J1 placed", a), ("J1 final", b)):
                for j in [j1] + ([jigs["J1a"]] if "J1a" in jigs else []):
                    v = vol(shape(c, m), j)
                    if v > 0.01:
                        bad.append(f"{n} {tag} {v:.2f}")
        for n, (c, m) in inst.items():
            v = vol(shape(c, j2_pose(code) @ m), j2) if j2 else 0
            if v > 0.01:
                bad.append(f"{n} J2 {v:.2f}")
            v = vol(shape(c, tray_pose(code, n)), t1) if t1 else 0
            if v > 0.01:
                bad.append(f"{n} T1 {v:.2f}")
        print(f"{code}: {'all clear' if not bad else bad}", flush=True)
    if t1 is None:
        sys.exit()
    # poka-yoke: a plank face UP in its pocket must hit the key
    m = tray_pose("C1", "seat1")
    up = m @ T(0, d.W, d.T) @ Rx(180)
    print("poka-yoke, plank face up in pocket flat1 -> overlap with T1:", round(vol(shape("W2", up), t1), 2), "mm3")
