"""Jig V2: the plank rack, changed from PlankRack_V4 (jig_platform_v4.py).

    python robot_cell/jig_v2.py              (MSc-MechAuto-NTNU venv: build123d; ocp_vscode to show it)

Changes from V4:
    blind slots   the slots in the foot stop FLOOR mm above the bottom, so the planks stand on the rack's
                  own floor, not on the plate below, and the rack has an obvious bottom and top
    flanges       a tab at each end (x) at the bottom, with 2 counterbored M3 holes each: screwed from the
                  top into the jig base below. No heat-set inserts any more.
Same slot grid, slot size, lead-ins and comb as V4. The planks sit FLOOR mm higher than in V4.
Out: jig-cad/Jig V2/PlankRack_V2.STEP + .stl (rack coordinates: slot grid corner at the origin, bottom z = 0).
"""
import build123d as bd

import jig_platform_v4 as v4

OUT = v4.HERE.parent / "jig-cad" / "Jig V2"
C, LO, HI = v4.C, v4.LO, v4.HI

FLOOR = 3.0                         # material under the slots
FLANGE_L, FLANGE_T = 16.0, 6.0      # how far each tab sticks out (x), its thickness
HEAD_D, HEAD_H = 6.5, 3.2           # counterbore for an M3 socket/pan head
FLANGE_HOLES_Y = (12.0, 48.0)


def plank_rack_v2():
    (x0, x1), (y0, y1) = v4.RACK_X, v4.RACK_Y
    H = v4.RACK_H
    block = lambda xa, xb, y, w, z, h: bd.Box(xb - xa, w, h, align=(LO, LO, LO)).translate((xa, y, z))
    rack = (block(x0, x1, y0, y1 - y0, 0, v4.FOOT_T)
            + block(x0, x1, y0, y1 - y0, H - v4.COMB_T, v4.COMB_T)
            + block(x0, x1, y0, v4.WALL_T, 0, H) + block(x0, x1, y1 - v4.WALL_T, v4.WALL_T, 0, H)
            + block(x0 - FLANGE_L, x0, y0, y1 - y0, 0, FLANGE_T)
            + block(x1, x1 + FLANGE_L, y0, y1 - y0, 0, FLANGE_T))
    for row in range(2):
        for col in range(3):
            x, y = v4.PITCH * (col + 0.5), v4.PITCH * (row + 0.5)
            rack -= v4.slot(x, y, FLOOR, v4.FOOT_T)          # blind: FLOOR mm left under each plank
            rack -= v4.slot(x, y, H - v4.COMB_T, H)
    for hx in (x0 - FLANGE_L / 2, x1 + FLANGE_L / 2):
        for hy in FLANGE_HOLES_Y:
            rack -= v4.hole(hx, hy, v4.M3, FLANGE_T, FLANGE_T)
            rack -= v4.hole(hx, hy, HEAD_D, HEAD_H, FLANGE_T)
    return rack


def main():
    OUT.mkdir(exist_ok=True)
    rack = plank_rack_v2()
    bd.export_step(rack, str(OUT / "PlankRack_V2.STEP"))
    bd.export_stl(rack, str(OUT / "PlankRack_V2.stl"))
    bb = rack.bounding_box()
    print(f"PlankRack_V2: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"volume {rack.volume / 1000:.1f} cm3, valid {rack.is_valid}")
    try:
        from ocp_vscode import show
        show(rack)
    except Exception:
        pass




# ---- concept (python robot_cell/jig_v2.py concept): a flat base plate with a 50 mm grid, the v6 cell on it ----
GRID, GROOVE_W, GROOVE_D = 50.0, 2.0, 1.0       # grid pitch; groove width and depth (cut into the top face)
BASE_PLATE = (600.0, 500.0, 6.0)                 # x away from the robot, y to the left (v6 ground base: 590 x 440);
                                                 # whole multiples of GRID, grooves on the edges too (half width):
                                                 # every square is a whole (GRID - GROOVE_W) square
WORK = (0.0, 67.0, 270.0, 310.0)                 # the robot's logged work plate in plate coordinates: x0, y0, size
                                                 # (bench_layout.json, ground base at transl(0, -67) in the work frame)


def grid_plate():
    sx, sy, t = BASE_PLATE
    nx, ny = round(sx / GRID), round(sy / GRID)
    assert abs(nx * GRID - sx) < 1e-6 and abs(ny * GRID - sy) < 1e-6, "plate size must be whole grid squares"
    plate = bd.Box(sx, sy, t, align=(LO, LO, HI))
    with bd.BuildPart() as grooves:
        with bd.Locations(*[(i * GRID, sy / 2, -GROOVE_D / 2) for i in range(nx + 1)]):
            bd.Box(GROOVE_W, sy, GROOVE_D)
        with bd.Locations(*[(sx / 2, j * GRID, -GROOVE_D / 2) for j in range(ny + 1)]):
            bd.Box(sx, GROOVE_W, GROOVE_D)
    return plate - grooves.part


def concept():
    """Concept STL: grid plate, bases A + B flat on it (no risers), PlankRack_V2, guide halves on base A, and
    the work plate as a 1 mm outline. In plate coordinates (top of the plate z = 0), as bench_cell_v6.py."""
    import bench_cell_v6 as cell
    jigs = v4.HERE.parent / "jig-cad" / "Jig V1"
    pos = lambda m: (m[0, 3], m[1, 3])
    base_a = v4.step_solid(jigs / "JigBaseA_V1.STEP").translate((*pos(cell.BASE_A), 0))
    base_b = v4.step_solid(jigs / "JigBaseB_V1.STEP").translate((*pos(cell.BASE_B), 0))
    halves = [bd.import_step(str(jigs / "v4 split guide" / f"JigGuide_{h}_V1.STEP")) for h in ("inner", "outer")]
    halves = [h.translate((*pos(cell.BASE_A), 0)) for h in halves]          # GUIDE_ON_A: base A coordinates
    rack = plank_rack_v2().translate((*pos(cell.PLANK_JIG), 0))
    x0, y0, wx, wy = WORK
    work = (bd.Box(wx, wy, 1, align=(LO, LO, LO)) - bd.Box(wx - 6, wy - 6, 1, align=(LO, LO, LO)).translate((3, 3, 0)))
    work = work.translate((x0, y0, 0.2))
    plate = grid_plate()
    out = OUT / "concept"
    out.mkdir(parents=True, exist_ok=True)
    everything = bd.Compound([plate, base_a, base_b, rack, *halves, work])
    bd.export_stl(everything, str(out / "Concept_V2_all.stl"))
    bd.export_stl(plate, str(out / "Concept_V2_grid_plate.stl"))
    bd.export_stl(work, str(out / "Concept_V2_work_area_outline.stl"))
    for name, s in (("base A", base_a), ("base B", base_b), ("rack", rack), ("guide inner", halves[0]),
                    ("guide outer", halves[1])):
        b = s.bounding_box()
        print(f"{name:12s} x {b.min.X:6.0f}..{b.max.X:4.0f}  y {b.min.Y:5.0f}..{b.max.Y:4.0f}  z {b.min.Z:4.0f}..{b.max.Z:4.0f}")
    try:
        from ocp_vscode import show
        show(plate, base_a, base_b, rack, *halves, work,
             names=["grid plate", "base A", "base B", "plank rack", "guide inner", "guide outer", "work area"],
             colors=["burlywood", "steelblue", "steelblue", "steelblue", "orange", "gold", "red"])
    except Exception:
        pass




# ---- concept 3 (python robot_cell/jig_v2.py concept3): bases A + B symmetric on the robot's work plate,
#      plank rack outside it, guide halves with one arm each (Bjørge's sketch "arms for the guide jig.png") ----
ARM_X, ARM_W = -2.0, 25.0          # arm column centre (base-A / guide coordinates) and width, both arms
INNER_ARM = (-2.0, 63.0)           # inner half: from the top of its seat band (y 0) up into the open seat-back corner
OUTER_ARM = (-80.0, -48.0)         # outer half: from the bottom of its seat band (y -50) down between the legs
GUIDE_Z = (20.0, 60.0)             # guide faces in base-A coordinates (on the base, 40 mm thick)
LAYOUT3 = {"A": (135.0, 122.0), "B": (135.0, 322.0), "rack": (330.0, 192.0)}   # base centres; rack slot-grid corner
# work plate x 0..270, y 67..377: bases 180 x 180 at x 45..225, A y 32..212 / B y 232..412 - mirror images about the
# plate's centre line y 222 (the robot's y 220), 145 mm of each on the plate; the rack outside, beyond its far edge


def halves_with_arms():
    jigs = v4.HERE.parent / "jig-cad" / "Jig V1" / "v4 split guide"
    inner = bd.import_step(str(jigs / "JigGuide_inner_V1.STEP"))
    outer = bd.import_step(str(jigs / "JigGuide_outer_V1.STEP"))
    z0, z1 = GUIDE_Z
    arm = lambda y0, y1: bd.Box(ARM_W, y1 - y0, z1 - z0, align=(C, LO, LO)).translate((ARM_X, y0, z0))
    inner = inner.solids()[0] + arm(*INNER_ARM)                # arms reach 2 mm into the seat band: one solid
    outer = outer.solids()[0] + arm(*OUTER_ARM)
    for name, s in (("inner", inner), ("outer", outer)):
        assert len(s.solids()) == 1, f"{name} half + arm is {len(s.solids())} solids"
    return inner, outer


def concept3():
    jigs = v4.HERE.parent / "jig-cad" / "Jig V1"
    (ax, ay), (bx, by), (rx, ry) = LAYOUT3["A"], LAYOUT3["B"], LAYOUT3["rack"]
    base_a = v4.step_solid(jigs / "JigBaseA_V1.STEP").translate((ax, ay, 0))
    base_b = v4.step_solid(jigs / "JigBaseB_V1.STEP").translate((bx, by, 0))
    inner, outer = halves_with_arms()
    out = OUT / "concept"
    out.mkdir(parents=True, exist_ok=True)
    bd.export_step(inner, str(out / "GuideInner_arm_V2.STEP"))
    bd.export_step(outer, str(out / "GuideOuter_arm_V2.STEP"))
    inner, outer = inner.translate((ax, ay, 0)), outer.translate((ax, ay, 0))
    rack = plank_rack_v2().translate((rx, ry, 0))
    x0, y0, wx, wy = WORK
    work = (bd.Box(wx, wy, 1, align=(LO, LO, LO)) - bd.Box(wx - 6, wy - 6, 1, align=(LO, LO, LO)).translate((3, 3, 0)))
    work = work.translate((x0, y0, 0.2))
    plate = grid_plate()
    bd.export_stl(bd.Compound([plate, base_a, base_b, rack, inner, outer, work]), str(out / "Concept3_all.stl"))
    for name, s in (("base A", base_a), ("base B", base_b), ("rack", rack), ("guide inner", inner),
                    ("guide outer", outer)):
        b = s.bounding_box()
        print(f"{name:12s} x {b.min.X:6.0f}..{b.max.X:4.0f}  y {b.min.Y:5.0f}..{b.max.Y:4.0f}  z {b.min.Z:4.0f}..{b.max.Z:4.0f}")
    return plate, base_a, base_b, rack, inner, outer



# ---- jig base V2 (python robot_cell/jig_v2.py base): the plate for the v7 cell, STEP + DXF/SVG for the laser ----
# v7 layout: bases A + B turned 180 deg (grip pocket away from the robot: bench_cell_v7.py), mirror images about
# the work plate's centre line y 222; plank rack outside the work plate. Holes as JigPlatform_V4: M3 countersunk
# from below into the bases' heat-set inserts (BASE_HOLES are symmetric: the same with the bases turned), 4 holes
# to the table inside the work plate. No red vision squares (2026-11-02: the robot finds the plate with a
# TM Landmark instead - where and how big still to decide).
# The rack (PlankRack_V2) is screwed from the top through its flanges: no holes.
LAYOUT7 = {"A": (135.0, 122.0), "B": (135.0, 322.0), "rack": (420.0, 192.0)}
TABLE_HOLES7 = [(20.0, 90.0), (20.0, 355.0), (250.0, 90.0), (250.0, 355.0)]   # inside the work plate, off the bases


def squares7():
    """Red vision squares: none any more (a TM Landmark finds the plate); kept so the drawings stay generic."""
    return []


def base_holes7():
    """M3 through the plate: the bases' and the rack's flange holes (bolts from the top, nuts underneath)."""
    return [to_plate(w, x, y) for w in ("A", "B") for x, y in base_flange_holes(w)] + rack_holes7()


def footprints7():
    out = []
    for w in ("A", "B"):                                  # footprint with its flanges (turned 180 deg)
        y0, y1 = (-90, 90 + FLANGE_L) if w == "A" else (-90 - FLANGE_L, 90)
        (ax, ay), (bx, by) = to_plate(w, -90, y0), to_plate(w, 90 + FLANGE_L, y1)
        out.append((min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)))
    rx, ry = LAYOUT7["rack"]
    (x0, x1), (y0, y1) = v4.RACK_X, v4.RACK_Y
    out.append((rx + x0 - FLANGE_L, ry + y0, rx + x1 + FLANGE_L, ry + y1))
    return out


def jig_base_v2():
    plate = grid_plate()
    t = BASE_PLATE[2]
    p, sq_t = v4.SQUARE + 2 * v4.SQ_CLEAR, v4.SQUARE_T
    for x, y in squares7():
        cx, cy = x + v4.SQUARE / 2, y + v4.SQUARE / 2
        plate -= bd.Box(p, p, sq_t, align=(C, C, HI)).translate((cx, cy, 0))
        plate -= v4.hole(cx, cy, v4.PUSH_OUT, t)
    for x, y in base_holes7():
        plate -= v4.hole(x, y, v4.M3, t)
    for x, y in TABLE_HOLES7:
        plate -= v4.hole(x, y, v4.TABLE_HOLE, t)
    return plate


def drawing7():
    sx, sy, _ = BASE_PLATE
    grid = f"FILL_{GROOVE_D:g}MM_GRID"
    pocket = f"FILL_{v4.SQUARE_T:g}MM_POCKET"
    h = GROOVE_W / 2
    items = [("CUT_THROUGH", "rect", (0, 0, sx, sy))]
    items += [(grid, "rect", (max(0, i * GRID - h), 0, min(sx, i * GRID + h), sy)) for i in range(round(sx / GRID) + 1)]
    items += [(grid, "rect", (0, max(0, j * GRID - h), sx, min(sy, j * GRID + h))) for j in range(round(sy / GRID) + 1)]
    c = v4.SQ_CLEAR
    for x, y in squares7():
        items.append((pocket, "rect", (x - c, y - c, x + v4.SQUARE + c, y + v4.SQUARE + c)))
        items.append(("CUT_THROUGH", "circle", (x + v4.SQUARE / 2, y + v4.SQUARE / 2, v4.PUSH_OUT / 2)))
    items += [("CUT_THROUGH", "circle", (x, y, v4.M3 / 2)) for x, y in base_holes7()]
    items += [("CUT_THROUGH", "circle", (x, y, v4.TABLE_HOLE / 2)) for x, y in TABLE_HOLES7]
    items += [("SCORE", "rect", f) for f in footprints7()]
    return items, (sx, sy)


def base():
    OUT.mkdir(exist_ok=True)
    plate = jig_base_v2()
    bd.export_step(plate, str(OUT / "JigBase_V2.STEP"))
    items, size = drawing7()
    v4.write_dxf(OUT / "JigBase_V2.dxf", items)
    v4.write_svg(OUT / "JigBase_V2.svg", items, size)
    for w in ("A", "B"):
        bb = base_v2(w)
        bd.export_step(bb, str(OUT / f"JigBase{w}_V2.STEP"))
        bd.export_stl(bb, str(OUT / f"JigBase{w}_V2.stl"))
        print(f"JigBase{w}_V2: {bb.bounding_box().size}, valid {bb.is_valid}, solids {len(bb.solids())}")
    # everything for the laser on one sheet (the plate only, now that the red squares are gone)
    v4.write_svg(OUT / "JigBase_V2_all.svg", items, size)
    v4.write_dxf(OUT / "JigBase_V2_all.dxf", items)
    b = plate.bounding_box()
    print(f"JigBase_V2: {b.size.X:.0f} x {b.size.Y:.0f} x {b.size.Z:.0f} mm, valid {plate.is_valid}; "
          f"{len(base_holes7())} M3 (base + rack flanges), {len(TABLE_HOLES7)} table holes")



# ---- bases A + B V2 (made by base()): the V1 bases 10 mm taller (the riser built in: the guide's grip height
#      and the gripper's 3 mm over the plate stay as in v6) and flanges at the bottom, screwed from the top through
#      the plate (M3 + nut underneath). Flanges only where the gripper never goes low: base-local +x (the backrest
#      side, towards the robot once the bases are turned 180 deg) and the outer side (A: local +y, B: local -y);
#      none between A and B (the frame-foot grip) or at the guide's grip pocket (local -x).
BASE_EXTRA = 10.0                               # = RISER_A/B in v4-v6
BASE_FLANGE_HOLES = (-60.0, 0.0, 60.0)          # along each flanged side


def base_flange_holes(which):
    """Hole centres in base-local coordinates (centre of the 180 x 180 footprint)."""
    side_y = 90 + FLANGE_L / 2 if which == "A" else -(90 + FLANGE_L / 2)
    return [(90 + FLANGE_L / 2, t) for t in BASE_FLANGE_HOLES] + [(t, side_y) for t in BASE_FLANGE_HOLES]


def base_v2(which):
    jigs = v4.HERE.parent / "jig-cad" / "Jig V1"
    b = v4.step_solid(jigs / f"JigBase{which}_V1.STEP").translate((0, 0, BASE_EXTRA))
    b += bd.Box(180, 180, BASE_EXTRA, align=(C, C, LO))
    ys = (-90, 90 + FLANGE_L) if which == "A" else (-90 - FLANGE_L, 90)
    b += bd.Box(FLANGE_L, ys[1] - ys[0], FLANGE_T, align=(LO, LO, LO)).translate((90, ys[0], 0))       # +x side
    y0 = 90 if which == "A" else -90 - FLANGE_L
    b += bd.Box(180, FLANGE_L, FLANGE_T, align=(C, LO, LO)).translate((0, y0, 0))                        # outer side
    for x, y in base_flange_holes(which):
        b -= v4.hole(x, y, v4.M3, FLANGE_T, FLANGE_T)
        b -= v4.hole(x, y, HEAD_D, HEAD_H, FLANGE_T)
    return b


def to_plate(which, x, y):
    """Base-local -> plate coordinates: the bases are turned 180 deg about their centre."""
    cx, cy = LAYOUT7[which]
    return cx - x, cy - y


def rack_holes7():
    rx, ry = LAYOUT7["rack"]
    (x0, x1), _ = v4.RACK_X, v4.RACK_Y
    return [(rx + hx, ry + hy) for hx in (x0 - FLANGE_L / 2, x1 + FLANGE_L / 2) for hy in FLANGE_HOLES_Y]


def all_stl():
    """Everything of Jig V2 in place, in plate coordinates (top of the plate z = 0): the plate, bases A + B (turned
    180 deg, on the plate), the guide halves with their arms on base A (start/end of the cycle), the plank rack and
    (no red squares: a TM Landmark finds the plate). One STL (Jig_V2_all.stl) and a coloured 3MF (Jig_V2_all.3mf)."""
    sq_t = v4.SQUARE_T
    parts = [("plate", jig_base_v2(), (0.80, 0.64, 0.42))]
    for w in ("A", "B"):
        parts.append((f"base {w}", base_v2(w).rotate(bd.Axis.Z, 180).translate((*LAYOUT7[w], 0)), (0.35, 0.55, 0.85)))
    inner, outer = halves_with_arms()                       # base-A coordinates, guide on the base at z 20..60
    for name, h, c in (("guide inner", inner, (0.95, 0.6, 0.15)), ("guide outer", outer, (0.95, 0.75, 0.2))):
        parts.append((name, h.translate((0, 0, BASE_EXTRA)).rotate(bd.Axis.Z, 180).translate((*LAYOUT7["A"], 0)), c))
    parts.append(("plank rack", plank_rack_v2().translate((*LAYOUT7["rack"], 0)), (0.45, 0.47, 0.5)))
    bd.export_stl(bd.Compound([s for _, s, _ in parts]), str(OUT / "Jig_V2_all.stl"))
    mesher, skipped = bd.Mesher(), []
    for name, s, c in parts:
        s.label, s.color = name, bd.Color(*c)
        try:
            mesher.add_shape(s, linear_deflection=0.05, angular_deflection=0.2)
        except RuntimeError:                                # 3MF wants a valid closed mesh per part
            skipped.append(name)
    mesher.write(str(OUT / "Jig_V2_all.3mf"))
    print("3MF:", f"{len(parts) - len(skipped)}/{len(parts)} parts", f"(not in it: {skipped})" if skipped else "")
    for name, s, _ in parts[:5]:
        b = s.bounding_box()
        print(f"{name:12s} x {b.min.X:5.0f}..{b.max.X:4.0f}  y {b.min.Y:5.0f}..{b.max.Y:4.0f}  z {b.min.Z:4.0f}..{b.max.Z:4.0f}")


def preview_svg():
    """A readable picture of the jig base (not for the laser - the laser files keep hairlines): the plate in wood
    colour, grid grooves, pockets filled, holes, the bases / rack / guide footprints filled and labelled, the
    robot's work plate, a legend. Out: JigBase_V2_preview.svg (plate coordinates, y up as in the other drawings)."""
    sx, sy, _ = BASE_PLATE
    m, leg = 40, 230                                         # margin, legend width
    W, H = sx + 2 * m + leg, sy + 2 * m + 40
    Y = lambda y: m + 20 + sy - y                             # SVG y down
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 2}" height="{H * 2}" viewBox="0 0 {W} {H}" '
           'font-family="Arial, Helvetica, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="{m}" y="{m - 8}" font-size="16" font-weight="bold">Jig base V2 - 600 x 500 x 6 mm plywood</text>']
    rect = lambda x0, y0, x1, y1, style: (f'<rect x="{x0 + m:.2f}" y="{Y(y1):.2f}" width="{x1 - x0:.2f}" '
                                          f'height="{y1 - y0:.2f}" {style}/>')
    circ = lambda x, y, r, style: f'<circle cx="{x + m:.2f}" cy="{Y(y):.2f}" r="{r:.2f}" {style}/>'
    text = lambda x, y, t, size=11, extra="": (f'<text x="{x + m:.1f}" y="{Y(y):.1f}" font-size="{size}" '
                                               f'text-anchor="middle" {extra}>{t}</text>')
    out.append(rect(0, 0, sx, sy, 'fill="#e2bf8a" stroke="#c0392b" stroke-width="1.2"'))           # plate, cut outline
    h = GROOVE_W / 2
    for i in range(round(sx / GRID) + 1):
        out.append(rect(max(0, i * GRID - h), 0, min(sx, i * GRID + h), sy, 'fill="#8d6e4a"'))
    for j in range(round(sy / GRID) + 1):
        out.append(rect(0, max(0, j * GRID - h), sx, min(sy, j * GRID + h), 'fill="#8d6e4a"'))
    x0, y0, wx, wy = WORK
    out.append(rect(x0, y0, x0 + wx, y0 + wy, 'fill="#ff000014" stroke="#e00000" stroke-width="2" stroke-dasharray="8 5"'))
    out.append(text(x0 + wx / 2, y0 + wy + 6, "robot work plate 270 x 310", 12, 'fill="#c00000" font-weight="bold"'))
    for (fx0, fy0, fx1, fy1), name in zip(footprints7(), ("BASE A", "BASE B", "PLANK RACK")):
        out.append(rect(fx0, fy0, fx1, fy1, 'fill="#4a7fc177" stroke="#1f4fa0" stroke-width="1.2"'))
        out.append(text((fx0 + fx1) / 2, (fy0 + fy1) / 2 + 4, name, 14, 'fill="#0d2d66" font-weight="bold"'))
    for w in ("A", "B"):                                     # flange strips, darker
        y0f, y1f = (90, 90 + FLANGE_L) if w == "A" else (-90 - FLANGE_L, -90)
        for (ax, ay), (bx, by) in ((to_plate(w, 90, -90), to_plate(w, 90 + FLANGE_L, 90 + FLANGE_L if w == "A" else 90)),
                                   (to_plate(w, -90, y0f), to_plate(w, 90, y1f))):
            out.append(rect(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), 'fill="#1f4fa055"'))
    c = v4.SQ_CLEAR
    for x, y in squares7():
        out.append(rect(x - c, y - c, x + v4.SQUARE + c, y + v4.SQUARE + c, 'fill="#d01818" stroke="#000" stroke-width="0.6"'))
        out.append(circ(x + v4.SQUARE / 2, y + v4.SQUARE / 2, v4.PUSH_OUT / 2, 'fill="#ffffff" stroke="#000" stroke-width="0.6"'))
    for x, y in base_holes7():
        out.append(circ(x, y, 2.4, 'fill="#ffffff" stroke="#c0392b" stroke-width="1"'))
    for x, y in TABLE_HOLES7:
        out.append(circ(x, y, v4.TABLE_HOLE / 2 + 0.6, 'fill="#ffffff" stroke="#7a1fa2" stroke-width="1.4"'))
    out.append(f'<polygon points="{m - 34},{Y(220) - 9} {m - 6},{Y(220)} {m - 34},{Y(220) + 9}" fill="#222"/>')
    out.append(f'<text x="{m - 20}" y="{Y(220) - 14}" font-size="11" text-anchor="middle">robot</text>')
    out.append(f'<text x="{m + sx / 2}" y="{Y(0) + 18}" font-size="11" text-anchor="middle">x [mm] 0 - 600, away from the robot -&gt;   (AMR on this side, y &lt; 0)</text>')
    for i in range(0, round(sx) + 1, 100):
        out.append(f'<text x="{m + i}" y="{Y(0) + 32}" font-size="9" text-anchor="middle" fill="#555">{i}</text>')
    for j in range(0, round(sy) + 1, 100):
        out.append(f'<text x="{m - 6}" y="{Y(j) + 3}" font-size="9" text-anchor="end" fill="#555">{j}</text>')
    lx, ly = m + sx + 25, m + 30
    items = [('<rect width="18" height="12" fill="#e2bf8a" stroke="#c0392b" stroke-width="1.2"/>', "plate, cut outline (red)"),
             ('<rect width="18" height="3" y="5" fill="#8d6e4a"/>', f"grid groove {GROOVE_W:g} x {GROOVE_D:g} mm, every {GRID:g} mm"),
             ('<circle cx="9" cy="6" r="3" fill="#fff" stroke="#c0392b" stroke-width="1"/>', "M3 hole: base / rack flange"),
             ('<circle cx="9" cy="6" r="4" fill="#fff" stroke="#7a1fa2" stroke-width="1.4"/>', "5.5 mm: plate to the table"),
             ('<rect width="18" height="12" fill="#4a7fc177" stroke="#1f4fa0" stroke-width="1.2"/>', "jig footprint (scored line)"),
             ('<rect width="18" height="12" fill="#1f4fa055"/>', "base flange (screwed from top)"),
             ('<rect width="18" height="12" fill="#ff000014" stroke="#e00000" stroke-width="2" stroke-dasharray="5 3"/>', "robot work plate (table)")]
    out.append(f'<text x="{lx}" y="{ly - 12}" font-size="13" font-weight="bold">Legend</text>')
    for k, (sym, label) in enumerate(items):
        out.append(f'<g transform="translate({lx},{ly + 22 * k})">{sym}<text x="26" y="10" font-size="11">{label}</text></g>')
    ly2 = ly + 22 * len(items) + 20
    notes = ["Bases A + B turned 180 deg:", "backrest towards the robot,", "guide grip pocket away from it.",
             "No red squares: a TM Landmark", "finds the plate (place: to decide).", "Laser files: JigBase_V2.dxf / .svg."]
    for k, t in enumerate(notes):
        out.append(f'<text x="{lx}" y="{ly2 + 15 * k}" font-size="10" fill="#333">{t}</text>')
    out.append("</svg>")
    (OUT / "JigBase_V2_preview.svg").write_text("\n".join(out), encoding="utf-8")
    print(OUT / "JigBase_V2_preview.svg")


def sim_parts():
    """STLs for the RoboDK v7 cell (bench_cell_v7.py) in robot_cell/jig_parts/, in the frames the cell scripts use:
    ground_base_v7 (plate, top z = 0), base_a/b_v7 (base-A/B coordinates of V1: the 10 mm extension below z 0, so
    the base frame sits 10 mm over the plate as before), guide_inner/outer_v7 (base-A coordinates, with the arms),
    plank_rack_v7 (rack coordinates: slot-grid corner, bottom z = 0)."""
    jp = v4.HERE / "jig_parts"
    inner, outer = halves_with_arms()
    for name, shape in (("ground_base_v7", jig_base_v2()),
                        ("base_a_v7", base_v2("A").translate((0, 0, -BASE_EXTRA))),
                        ("base_b_v7", base_v2("B").translate((0, 0, -BASE_EXTRA))),
                        ("guide_inner_v7", inner), ("guide_outer_v7", outer), ("plank_rack_v7", plank_rack_v2())):
        bd.export_stl(shape, str(jp / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2)
        print(name, shape.bounding_box().size)


if __name__ == "__main__":
    import sys
    {"concept": concept, "concept3": concept3, "base": base, "all": all_stl, "preview": preview_svg, "sim": sim_parts}.get((sys.argv[1:] or ["main"])[0], main)()
