"""Guide split V6 PROPOSAL (Bjørge 2026-11-07): JigV3's guide re-split so the big half can come off the finished
bench without being trapped.

Now (JigV3): the seat planks (P1-P3) sit between the big half (one wide face + the teeth between the planks) and the
small half (the other wide face) - already as wanted. The back-rest planks (P5, P6) sit between the big half's long
face above them and the small half's long face below, BUT the big half also has the tooth between P5 and P6 and the
end wall at P5: those lock it (it can only leave the way it came, through the planks).
Proposal: the tooth between the back-rest slots (P5 | P6) moves to the small half (+ its mirror image: the guide is
symmetric). Then the big half touches the back-rest planks only on one long face (and P5's open end) and the seat
planks from one side + between them -> it slides straight out towards the robot (-x on the plate); the small half
(back-rest floor + the tooth + P6's end, seat planks on one face) then slides out towards the AMR (-y).
Check (planks as in stage 6, shrunk 2 mm per side: the model's planks overlap the guide ~1.6 mm): new big half free
for 200 mm towards the robot (old: blocked after 2.5 mm by plank 5); new small half then free towards the AMR.

    python robot_cell/guide_split_v6.py
Out (Jig V5 untouched): jig-cad/Jig V6 proposal/
    GuideSplit_V6_small.STEP, GuideSplit_V6_big.STEP      the two new halves, JigV3 base-local (as guide_*_v5.stl)
    JigAssembly_V6_proposal.STEP (+ .stl)                 Jig V5's assembly with the new halves on base A
    guide_split_v6_top.png                                top view: new halves + planks as they stand in stage 6
and prints a check: the big half slid -x in 1 mm steps against the planks (stage 6, bench on A).
"""
import sys
from pathlib import Path

import build123d as bd
import numpy as np
import trimesh

import jig_v3
import jig_v5
import bench_cell_v8 as v8

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "jig-cad" / "Jig V6 proposal"
# What moves from the big half to the small half: the tooth between the back-rest slots (P5 | P6), base-local x/y
# (guide_*_v5.stl / JigV3 frame; the guide is extruded z 20..60), on the side the back-rest planks stand in stage 6
# (local x < 0) + mirrored. Its ceiling-side edge is exactly the big half's long face (corners (-62.6, 41.6) and
# (-61.9, 37.3)); towards the small half it reaches past the tooth (the face there is slightly curved) - that side is
# the small half's anyway. (P5's slot end at y ~12 is open: nothing to move there.)
MOVE = [[(-62.62, 41.6), (-53.5, 42.9), (-52.9, 37.9), (-61.92, 37.3)]]   # ceiling corners 0.02 mm into the big
# half: with the edge exactly on its face the BRep cut silently does nothing on one side


def prism(poly):
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))
    if area < 0:                                                  # counter-clockwise, else the cut silently fails
        poly = poly[::-1]
    with bd.BuildPart() as bp:
        with bd.BuildSketch(bd.Plane.XY.offset(-5)):
            bd.Polygon(*poly, align=None)
        bd.extrude(amount=75)
    return bp.part


def planks_local():
    """Back-rest + seat plank meshes in the guide's base-local frame, as they stand in stage 6 (bench on A)."""
    M = v8.FINISH @ v8.FLIP @ np.linalg.inv(v8.START)
    to_local = np.linalg.inv(v8.FINISH @ v8.GUIDE_ON_B)
    out = {}
    for k in v8.PLANKS:
        m = trimesh.load(str(v8.PARTS / "plank_body.stl"))
        m.apply_transform(to_local @ M @ v8.START @ v8.T_IN @ v8.asm[f"plank{k}"])
        out[k] = m
    return out


def main():
    small, big = jig_v3.jig_v3_parts()[1]                         # guide[0] = small (inner U), guide[1] = big
    tm_small = trimesh.load(str(v8.JIG / "guide_1_v5.stl")); tm_big = trimesh.load(str(v8.JIG / "guide_2_v5.stl"))
    planks = planks_local()
    prisms = [prism([(sx * x, y) for x, y in poly]) for poly in MOVE for sx in (1, -1)]   # + the mirror image
    new_big, new_small, moved = big, small, 0.0
    for pr in prisms:                                             # one at a time (a union of separate prisms only
        piece = big & pr                                          # cut one of them)
        moved += piece.volume
        new_big = new_big - pr
        new_small = new_small + piece
    parts = sorted(new_big.solids(), key=lambda x: -x.volume)
    print("big half pieces after the cut (mm^3):", [round(x.volume, 1) for x in parts], "-> slivers < 10 mm^3 dropped")
    new_big = parts[0]                                            # drop slivers the cut may leave
    print(f"moved from big to small: {moved:.0f} mm^3 (big {big.volume:.0f} -> {new_big.volume:.0f}); solids: big {len(new_big.solids())}, "
          f"small {len(new_small.solids())}")
    OUT.mkdir(exist_ok=True)
    new_small.label, new_big.label = "Guide small V6 (proposal)", "Guide big V6 (proposal)"
    new_small.color, new_big.color = bd.Color(0.95, 0.55, 0.10), bd.Color(0.95, 0.80, 0.20)
    bd.export_step(new_small, str(OUT / "GuideSplit_V6_small.STEP"))
    bd.export_step(new_big, str(OUT / "GuideSplit_V6_big.STEP"))
    # assembly: Jig V5's, the old guide halves swapped for the new ones
    v5 = bd.import_step(str(HERE.parent / "jig-cad" / "Jig V5" / "JigAssembly_V5.STEP"))
    keep = [ch for ch in v5.children if "guide" not in (ch.label or "").lower()]
    for s, name in ((new_small, "Guide small V6 (on A)"), (new_big, "Guide big V6 (on A)")):
        p = jig_v3.place_at(s, jig_v5.BASES["A"], jig_v5.BASE_TURN)
        p.label, p.color = name, s.color
        keep.append(p)
    asm = bd.Compound(children=keep, label="JigAssembly_V6_proposal")
    bd.export_step(asm, str(OUT / "JigAssembly_V6_proposal.STEP"))
    bd.export_stl(asm, str(OUT / "JigAssembly_V6_proposal.stl"))
    for s, f in ((new_small, "guide_small_v6.stl"), (new_big, "guide_big_v6.stl")):
        bd.export_stl(s, str(OUT / f), tolerance=0.05, angular_tolerance=0.2)

    # check: the new big half slid -x (plate) = local -y, against the planks (stage 6)
    tb = trimesh.load(str(OUT / "guide_big_v6.stl")); ts = trimesh.load(str(OUT / "guide_small_v6.stl"))
    cm = trimesh.collision.CollisionManager()
    for k, m in planks.items():                                   # shrunk 2 mm per side across the plank: the
        cm.add_object(f"plank{k}", shrink(m, 2.0))                # model's planks overlap the guide ~1-1.6 mm at the seat
    first = None
    for s in np.arange(0.5, 200.5, 1.0):
        T = trimesh.transformations.translation_matrix([0, -s, 0])
        hit, names = cm.in_collision_single(tb, transform=T, return_names=True)
        if hit and first is None:
            first = (s, sorted(names))
    print("big half slid towards the robot (plate -x), planks in the way:", "none (0..200 mm)" if first is None
          else f"from {first[0]:.1f} mm: {first[1]}")
    hit, names = cm.in_collision_single(tb, return_names=True)
    print("big half at its seat touches:", sorted(names) if hit else "nothing")
    # the old big half, same test, for comparison
    first = None
    for s in np.arange(0.5, 200.5, 1.0):
        hit, names = cm.in_collision_single(tm_big, transform=trimesh.transformations.translation_matrix([0, -s, 0]),
                                            return_names=True)
        if hit and first is None:
            first = (s, sorted(names))
    print("OLD big half, same slide:", "free" if first is None else f"blocked from {first[0]:.1f} mm by {first[1]}")
    # then the new small half (big half gone): along its tooth faces, away from the planks (local +x = plate -y)
    best = None
    for ang in (0, 8, -8, 16, -16, 24, -24):
        a = np.radians(ang); dv = np.array([np.cos(a), np.sin(a), 0.0])
        first = None
        for s_ in np.arange(0.5, 120.5, 1.0):
            hit, names = cm.in_collision_single(ts, transform=trimesh.transformations.translation_matrix(dv * s_),
                                                return_names=True)
            if hit:
                first = s_; break
        if first is None and (best is None or abs(ang) < abs(best)):
            best = ang
    print("small half (after the big one), straight out free of the planks:",
          "no direction found" if best is None else f"yes, local +x turned {best:+d} deg (~ towards the AMR, plate -y)")
    draw(tb, ts, planks, OUT / "guide_split_v6_top.png")
    print(OUT)


def shrink(m, e):
    """The plank shrunk by e mm on each side of its cross-section (its oriented box's two short axes), length kept."""
    T = m.bounding_box_oriented.primitive.transform
    ext = m.bounding_box_oriented.primitive.extents
    k = np.ones(3)
    for i in np.argsort(ext)[:2]:
        k[i] = max(0.05, (ext[i] - 2 * e) / ext[i])
    S = T @ np.diag([*k, 1]) @ np.linalg.inv(T)
    out = m.copy(); out.apply_transform(S)
    return out


def draw(big, small, planks, path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    T = v8.FINISH @ v8.GUIDE_ON_B
    fig, ax = plt.subplots(figsize=(10, 9))
    for m, col in ((small, "darkorange"), (big, "goldenrod")):
        mm = m.copy(); mm.apply_transform(T)
        s = mm.section(plane_origin=[0, 0, 40], plane_normal=[0, 0, 1])
        for e in s.entities:
            P = s.vertices[e.points]; ax.fill(P[:, 0], P[:, 1], color=col)
    for m, col in ((small, "saddlebrown"), (big, "black")):  # the top (z 52): the grip tabs stick out there
        mm = m.copy(); mm.apply_transform(T)
        s = mm.section(plane_origin=[0, 0, 52], plane_normal=[0, 0, 1])
        for e in s.entities:
            P = s.vertices[e.points]; ax.plot(P[:, 0], P[:, 1], color=col, lw=1, ls="--")
    for k, m in planks.items():
        mm = m.copy(); mm.apply_transform(T)
        s = mm.section(plane_origin=[0, 0, 40], plane_normal=[0, 0, 1])
        if s is None:
            continue
        for e in s.entities:
            P = s.vertices[e.points]; ax.fill(P[:, 0], P[:, 1], color="saddlebrown")
        cc = s.vertices.mean(0); ax.text(cc[0], cc[1], f"P{k}", fontsize=10, weight="bold")
    ax.annotate("big half grip tab", xy=(160, 52), xytext=(140, 70), arrowprops=dict(arrowstyle="->"))
    ax.annotate("big half slides out this way", xy=(140, 52), xytext=(205, 40), arrowprops=dict(arrowstyle="->"))
    ax.set_aspect("equal"); ax.grid(alpha=.3)
    ax.set_title("\n".join(["Guide split V6 proposal, base A: filled = z 40, dashed = top z 52 with the grip tabs",
                            "(orange = small half, gold = big half, brown = planks)"]))
    ax.set_xlabel("plate x (robot to the left)"); ax.set_ylabel("plate y (AMR down, base B up)")
    plt.tight_layout(); plt.savefig(path, dpi=80)


if __name__ == "__main__":
    main()
