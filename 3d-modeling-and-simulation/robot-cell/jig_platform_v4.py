"""Jig platform for the version-4 cell (bench_cell_v4.py): the ground base as a wooden plate that the
V4 jigs screw onto, a plank rack that holds the six planks upright for the robot, and all of it as one
assembly.

    python robot_cell/jig_platform_v4.py     (MSc-MechAuto-NTNU venv: build123d; ocp_vscode to show it)

The V4 jigs are used as exported (jig-cad/Jig V1/JigBaseA_V1, JigBaseB_V1, v4 split guide/*), at their
places in bench_cell_v4.py. Ground base coordinates: x away from the robot, y to the left, top of the
plate at z = 0.
    platform    770 x 440 x PLATE_T wood. In the corners, where RoboDK has the 4 red vision squares:
                pockets as deep as the squares, a push-out hole under each. M3 holes countersunk from
                below for every fixed jig, 4 holes to fix the plate to the table, the jig outlines
                scored on top as a placing aid.
    bases A, B  on 10 mm risers; 4 M3 from below through plate + riser into heat-set inserts in the base
    pad         4 M3 into inserts
    plank rack  PlankJig_V1 made real: the same slot places (2 rows of 3, pitch 30; plank 25 x 5 + 0.3
                per side), a foot and a comb 100 mm up, both with lead-ins, so a 250 mm plank stands
                straight; the planks stand on the plate. 4 M3 into inserts
    guide       inner + outer half unchanged, on base B (the start of AssembleBench)
Out: jig-cad/Jig V1/v4 platform/: one STEP per part (own coordinates), STL of the printed parts, DXF +
SVG for the laser (red = cut through, black = pocket, blue = score) and JigAssembly_V4.STEP (ground
base coordinates). Shown in the OCP CAD Viewer when it is running.
"""
import copy
import math
from pathlib import Path

import build123d as bd
import ezdxf

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
JIGS = HERE.parent / "jig-cad" / "Jig V1"
V4 = JIGS / "v4 split guide"
OUT = JIGS / "v4 platform"
PLANK = HERE.parent / "bench-cad" / "plankV3.STEP"
C, LO, HI = bd.Align.CENTER, bd.Align.MIN, bd.Align.MAX

GROUND = (770, 440)                       # bench_cell_v4.GROUND_SIZE: x away from the robot, y to the left
PLATE_T = 6.0                             # plywood; RoboDK's "Ground base" frame sits this high (GROUND_IN_WORK z)
SQUARE, SQUARE_IN, SQUARE_T = 25, 3, 3.0  # vision squares and inset as in RoboDK; 3 mm red acrylic = pocket depth
SQ_CLEAR, PUSH_OUT = 0.2, 5.0             # pocket clearance per side; hole under each square to push it out
M3, M3_CSK, INSERT = 3.4, 6.6, (4.0, 7.0) # M3 clearance, countersink (90 deg) diameter, heat-set insert hole d x depth
TABLE_HOLE, TABLE_HOLES = 5.5, [(200, 10), (700, 10), (200, 430), (700, 430)]
RISER = 10                                # RISER_A = RISER_B in bench_cell_v4.py
BASE_A, BASE_B = (480, 120), (480, 320)   # base centres
PAD_AT, PAD = (665, 220), (180, 380, 80)
RACK_AT, PITCH = (150, 190), 30           # PLANK_JIG: corner of the slot grid, plank k at (PITCH*(col+.5), PITCH*(row+.5))
RACK_X, RACK_Y, RACK_H = (-5, 95), (0, 60), 100   # 10 mm longer than PlankJig_V1 (end walls 2.2 -> 7.2 mm)
FOOT_T, COMB_T, WALL_T = 20, 10, 6
SLOT, LEAD, LEAD_D = (25.6, 5.6), (1.0, 2.0), 2.0  # slot; lead-in per side across the width / thickness, depth

BASE_HOLES = [(x, y) for x in (-75, 75) for y in (-75, 75)]
PAD_HOLES = [(x, y) for x in (-75, 75) for y in (-175, 175)]
RACK_HOLES = [(x, y) for x in (10, 80) for y in (6, 54)]

WOOD, RED, GREY = bd.Color(0.80, 0.64, 0.42), bd.Color(0.85, 0.1, 0.1), bd.Color(0.6, 0.6, 0.62)
JIG_C, PLANK_C = bd.Color(0.35, 0.55, 0.85), bd.Color(0.72, 0.52, 0.28)
INNER_C, OUTER_C = bd.Color(0.95, 0.6, 0.15), bd.Color(0.95, 0.75, 0.2)


def at(centre, local):
    return [(centre[0] + x, centre[1] + y) for x, y in local]


def squares():
    """Lower-left corners of the 4 vision squares (bench_cell_v4.py)."""
    sx, sy = GROUND
    return [(x, y) for x in (SQUARE_IN, sx - SQUARE_IN - SQUARE) for y in (SQUARE_IN, sy - SQUARE_IN - SQUARE)]


def screw_holes():
    return at(BASE_A, BASE_HOLES) + at(BASE_B, BASE_HOLES) + at(PAD_AT, PAD_HOLES) + at(RACK_AT, RACK_HOLES)


def footprints():
    """Fixed jigs' outlines on the plate (x0, y0, x1, y1)."""
    out = [(cx - 90, cy - 90, cx + 90, cy + 90) for cx, cy in (BASE_A, BASE_B)]
    out.append((PAD_AT[0] - PAD[0] / 2, PAD_AT[1] - PAD[1] / 2, PAD_AT[0] + PAD[0] / 2, PAD_AT[1] + PAD[1] / 2))
    out.append((RACK_AT[0] + RACK_X[0], RACK_AT[1] + RACK_Y[0], RACK_AT[0] + RACK_X[1], RACK_AT[1] + RACK_Y[1]))
    return out


def hole(x, y, d, depth, z_top=0.0):
    return bd.Cylinder(d / 2, depth, align=(C, C, HI)).translate((x, y, z_top))


def platform():
    sx, sy = GROUND
    plate = bd.Box(sx, sy, PLATE_T, align=(LO, LO, HI))
    p = SQUARE + 2 * SQ_CLEAR
    for x, y in squares():
        cx, cy = x + SQUARE / 2, y + SQUARE / 2
        plate -= bd.Box(p, p, SQUARE_T, align=(C, C, HI)).translate((cx, cy, 0))
        plate -= hole(cx, cy, PUSH_OUT, PLATE_T)
    r, rc = M3 / 2, M3_CSK / 2
    for x, y in screw_holes():
        plate -= hole(x, y, M3, PLATE_T)
        plate -= bd.Cone(rc, r, rc - r, align=(C, C, LO)).translate((x, y, -PLATE_T))   # countersunk from below
    for x, y in TABLE_HOLES:
        plate -= hole(x, y, TABLE_HOLE, PLATE_T)
    return plate


def with_inserts(part, holes, bottom_z):
    d, depth = INSERT
    for x, y in holes:
        part -= bd.Cylinder(d / 2, depth, align=(C, C, LO)).translate((x, y, bottom_z))
    return part


def riser():
    """180 x 180 x RISER under a base, top at z = 0 (base-local: the base's bottom)."""
    r = bd.Box(180, 180, RISER, align=(C, C, HI))
    for x, y in BASE_HOLES:
        r -= hole(x, y, M3, RISER)
    return r


def slot(x, y, z0, z1):
    """Plank slot z0..z1, with the lead-in at the top."""
    (w, t), (lw, lt), e = SLOT, LEAD, 0.5
    k = (LEAD_D + e) / LEAD_D
    straight = bd.Box(w, t, z1 - z0 + e, align=(C, C, LO)).translate((x, y, z0 - e))
    funnel = bd.loft([bd.Plane(origin=(x, y, z1 - LEAD_D)) * bd.Rectangle(w, t),
                      bd.Plane(origin=(x, y, z1 + e)) * bd.Rectangle(w + 2 * lw * k, t + 2 * lt * k)])
    return straight + funnel


def plank_rack():
    """Foot (planks stand on the plate through it) + comb at the top, joined by two walls along x."""
    (x0, x1), (y0, y1) = RACK_X, RACK_Y
    block = lambda y, w, z, h: bd.Box(x1 - x0, w, h, align=(LO, LO, LO)).translate((x0, y, z))
    rack = (block(y0, y1 - y0, 0, FOOT_T) + block(y0, y1 - y0, RACK_H - COMB_T, COMB_T)
            + block(y0, WALL_T, 0, RACK_H) + block(y1 - WALL_T, WALL_T, 0, RACK_H))
    for row in range(2):
        for col in range(3):
            x, y = PITCH * (col + 0.5), PITCH * (row + 0.5)
            rack -= slot(x, y, 0, FOOT_T)
            rack -= slot(x, y, RACK_H - COMB_T, RACK_H)
    return with_inserts(rack, RACK_HOLES, 0)


def step_solid(path):
    return bd.import_step(str(path)).solids()[0]


def drawing(kind):
    """2D items (layer, "rect" (x0, y0, x1, y1) | "circle" (x, y, r)) for the laser, and the sheet size."""
    pocket = f"FILL_{SQUARE_T:g}MM_POCKET"
    if kind == "platform":
        sx, sy = GROUND
        items = [("CUT_THROUGH", "rect", (0, 0, sx, sy))]
        items += [("CUT_THROUGH", "circle", (x, y, M3 / 2)) for x, y in screw_holes()]
        items += [("CUT_THROUGH", "circle", (x, y, TABLE_HOLE / 2)) for x, y in TABLE_HOLES]
        for x, y in squares():
            items.append((pocket, "rect", (x - SQ_CLEAR, y - SQ_CLEAR, x + SQUARE + SQ_CLEAR, y + SQUARE + SQ_CLEAR)))
            items.append(("CUT_THROUGH", "circle", (x + SQUARE / 2, y + SQUARE / 2, PUSH_OUT / 2)))
        items += [("SCORE", "rect", f) for f in footprints()]
        return items, (sx, sy)
    if kind == "riser":
        items = [("CUT_THROUGH", "rect", (0, 0, 180, 180))]
        items += [("CUT_THROUGH", "circle", (x + 90, y + 90, M3 / 2)) for x, y in BASE_HOLES]
        return items, (180, 180)
    gap = 5                                                    # 4 red squares in a row
    items = [("CUT_THROUGH", "rect", (i * (SQUARE + gap), 0, i * (SQUARE + gap) + SQUARE, SQUARE)) for i in range(4)]
    return items, (4 * SQUARE + 3 * gap, SQUARE)


LAYERS = {"CUT_THROUGH": (1, 'fill="none" stroke="#ff0000" stroke-width="0.1"'),
          "SCORE": (5, 'fill="none" stroke="#0000ff" stroke-width="0.1"')}


def layer_style(name):
    return LAYERS.get(name, (7, 'fill="#000000" stroke="none"'))      # pockets: black fill


def layers(items):
    """Layer names in laser order, bottom to top: pockets, score, cut (cut lines never hidden under a pocket)."""
    return sorted(dict.fromkeys(layer for layer, *_ in items), key=lambda n: {"SCORE": 1, "CUT_THROUGH": 2}.get(n, 0))


def write_svg(path, items, size):
    w, h = size
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"'
             f' width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">']
    for name in layers(items):
        lines.append(f'  <g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}" {layer_style(name)[1]}>')
        for layer, shape, d in items:
            if layer != name:
                continue
            if shape == "rect":
                x0, y0, x1, y1 = d
                lines.append(f'    <rect x="{x0:.3f}" y="{h - y1:.3f}" width="{x1 - x0:.3f}" height="{y1 - y0:.3f}" />')
            else:
                lines.append(f'    <circle cx="{d[0]:.3f}" cy="{h - d[1]:.3f}" r="{d[2]:.3f}" />')
        lines.append("  </g>")
    path.write_text("\n".join(lines + ["</svg>", ""]), encoding="utf-8")


def write_dxf(path, items):
    """Opens in Inkscape (Read from file scaling = mm): pockets as solid hatches, so they come in filled
    (engraved), not as outlines (cut); no $PDMODE, which Inkscape's import reports as an error."""
    doc = ezdxf.new(units=ezdxf.units.MM)
    del doc.header["$PDMODE"]
    msp = doc.modelspace()
    order = layers(items)
    for name in order:
        doc.layers.add(name, color=layer_style(name)[0])
    for layer, shape, d in sorted(items, key=lambda item: order.index(item[0])):
        if shape == "rect":
            x0, y0, x1, y1 = d
            corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            if layer in LAYERS:
                msp.add_lwpolyline(corners, close=True, dxfattribs={"layer": layer})
            else:
                msp.add_hatch(color=7, dxfattribs={"layer": layer}).paths.add_polyline_path(corners, is_closed=True)
        else:
            msp.add_circle(d[:2], d[2], dxfattribs={"layer": layer})
    doc.saveas(path)


def named(shape, label, colour):
    shape.label, shape.color = label, colour
    return shape


def main():
    OUT.mkdir(exist_ok=True)
    base_a = step_solid(JIGS / "JigBaseA_V1.STEP")
    base_b = step_solid(JIGS / "JigBaseB_V1.STEP")
    pad = step_solid(V4 / "ParkingPad_V1.STEP")
    parts = {"JigPlatform_V4": platform(),
             "RedSquare_V4": bd.Box(SQUARE, SQUARE, SQUARE_T, align=(LO, LO, HI)),
             "Riser_V4": riser(),
             "JigBaseA_V4": with_inserts(base_a, BASE_HOLES, 0),
             "JigBaseB_V4": with_inserts(base_b, BASE_HOLES, 0),
             "ParkingPad_V4": with_inserts(pad, PAD_HOLES, -PAD[2]),
             "PlankRack_V4": plank_rack()}
    printed = ("Riser_V4", "JigBaseA_V4", "JigBaseB_V4", "ParkingPad_V4", "PlankRack_V4")
    for name, s in parts.items():
        s.label = name
        bd.export_step(s, str(OUT / f"{name}.STEP"))
        if name in printed:
            bd.export_stl(s, str(OUT / f"{name}.stl"), tolerance=0.05)
    for kind, name in (("platform", "JigPlatform_V4"), ("riser", "Riser_V4"), ("squares", "RedSquares_x4")):
        items, size = drawing(kind)
        write_svg(OUT / f"{name}.svg", items, size)
        write_dxf(OUT / f"{name}.dxf", items)

    # assembly in ground base coordinates, as at the start of AssembleBench (guide on base B, planks in the rack)
    guide_on_b = lambda g: g.rotate(bd.Axis.X, 180).translate((*BASE_B, RISER + 80))   # BASE_B * GUIDE_ON_B
    plank = bd.import_step(str(PLANK)).rotate(bd.Axis.X, 90)          # standing: length up, width along x
    planks = []
    for k in range(1, 7):                                             # bench_cell_v4.py's plank start poses
        row, col = divmod(k - 1, 3)
        xy = (RACK_AT[0] + PITCH * (col + 0.5), RACK_AT[1] + PITCH * (row + 0.5) + 2.5)
        planks.append(named(plank.translate((*xy, 125)), "Plank V3", PLANK_C))   # copies share one STEP label
    sq = parts["RedSquare_V4"]
    rack = named(parts["PlankRack_V4"].translate((*RACK_AT, 0)), "Plank rack", JIG_C)
    children = [
        named(parts["JigPlatform_V4"].translate((0, 0, 0)), "Platform", WOOD),
        bd.Compound(label="Red squares", children=[named(sq.translate((x, y, 0)), "Red square", RED)
                                                   for x, y in squares()]),
        named(parts["Riser_V4"].translate((*BASE_A, RISER)), "Riser A", GREY),
        named(copy.deepcopy(parts["Riser_V4"]).translate((*BASE_B, RISER)), "Riser B", GREY),   # own label
        named(parts["JigBaseA_V4"].translate((*BASE_A, RISER)), "Base A", JIG_C),
        named(parts["JigBaseB_V4"].translate((*BASE_B, RISER)), "Base B", JIG_C),
        named(guide_on_b(step_solid(V4 / "JigGuide_inner_V1.STEP")), "Guide inner", INNER_C),
        named(guide_on_b(step_solid(V4 / "JigGuide_outer_V1.STEP")), "Guide outer", OUTER_C),
        named(parts["ParkingPad_V4"].translate((*PAD_AT, PAD[2])), "Parking pad", GREY),
        rack,
        bd.Compound(label="Planks V3", children=planks),
    ]
    asm = bd.Compound(label="JigAssembly_V4", children=children)
    bd.export_step(asm, str(OUT / "JigAssembly_V4.STEP"))

    for name, s in parts.items():
        bb = s.bounding_box()
        print(f"{name:15s} {s.volume / 1000:7.1f} cm3  x {bb.min.X:6.1f}..{bb.max.X:6.1f}"
              f"  y {bb.min.Y:6.1f}..{bb.max.Y:6.1f}  z {bb.min.Z:6.1f}..{bb.max.Z:6.1f}")
    insert = 4 * math.pi * (INSERT[0] / 2) ** 2 * INSERT[1] / 1000
    for name, before in (("JigBaseA_V4", base_a), ("JigBaseB_V4", base_b), ("ParkingPad_V4", pad)):
        print(f"{name}: insert holes remove {(before.volume - parts[name].volume) / 1000:.3f} cm3"
              f" (4 full holes: {insert:.3f}; less = a hole runs into the pocket)")
    clash = sum(getattr(s & rack, "volume", 0.0) for p in planks for s in p.solids())
    play = SLOT[1] - 5
    print(f"planks in the rack: overlap {clash:.3f} mm3, lean <= {math.degrees(math.atan(play / (RACK_H - LEAD_D))):.2f} deg"
          f" ({250 * play / (RACK_H - LEAD_D):.1f} mm at the top; PlankJig_V1: {250 * play / 40:.1f} mm)")
    lengths = (8, 10, 12, 16, 20, 25, 30)
    fit = lambda need: max([l for l in lengths if l <= need] or [lengths[0]])
    print(f"screws: 8 x M3x{fit(PLATE_T + RISER + 6)} countersunk (bases), 8 x M3x{fit(PLATE_T + 6)} countersunk"
          f" (pad, rack); 16 M3 heat-set inserts ({INSERT[0]} x {INSERT[1]} mm holes); 4 red squares"
          f" {SQUARE} x {SQUARE} x {SQUARE_T:g}")
    print(f"laser: platform {GROUND[0]} x {GROUND[1]} mm sheet; engrave pockets {SQUARE_T:g} mm, score, then cut;"
          f" countersink the {len(screw_holes())} M3 holes from below by hand")

    try:
        from ocp_vscode import get_port, show
    except ImportError:
        print("no ocp_vscode in this venv: files written, not shown")
        return
    if get_port():
        show(asm)
    else:                                                      # show() would only print its own traceback
        print("OCP CAD Viewer not running: open it in VS Code and run again (files are written)")


if __name__ == "__main__":
    main()
