"""Rack marker plate (Bjorge 2026-11-17): a small bracket carrying the plank rack's ArUco marker, bolted
to the T-slot plate next to the rack instead of gluing the marker to the rack itself.

Why: the rack's own top is where planks stand once loaded, so a marker glued there gets covered (the vision
report's fix so far: a second photo taken straight above the rack). A ~160 mm post to lift the marker above
the standing planks was looked at and dropped as impractical (Next steps.md, 2026-11-12). Both overview
and rack-only camera poses used for jig vision look straight down (POSES in jig_vision_test.py: rx=180,
ry=0 - no tilt toward either side), so a marker only needs to stay flat and face up and clear of the
planks' footprint HORIZONTALLY - it does not need height to dodge occlusion, just X/Y offset.

This plate bolts into the SAME two T-slot lines (x=45, x=75) the rack's own flange already uses, at a
y position just past the rack's own footprint (rack spans plate y 89..211, jig_v5_layout.json) - so it
reuses the established 2-bolt-on-a-T-slot-pair pattern, doesn't touch the rack body itself, and needs no
new T-slot position. Direction picked here: y > 211 (past the rack's far end, "hi" flange side) - the
other direction (y < 89) is a one-constant flip (SIDE = "lo") if the real cell's clearance favours it;
check against the physical AMR/robot sweep before printing either way, this script only checks against
the OTHER jig parts' known plate positions (jig_v5_layout.json), not moving equipment.

    python robot_cell/rack_marker_plate.py
Out: jig-cad/Rack marker plate/RackMarkerPlate.STEP (+ .stl)
"""
import json
from pathlib import Path

import build123d as bd
from build123d import Align

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = HERE.parent / "jig-cad" / "Rack marker plate"

SIDE = "hi"                                           # "hi": y > 211 (past the rack's far end); "lo": mirror, y < 89
BOLT_XS = (45.0, 75.0)                                 # same T-slot lines the rack's own flange bolts into
RACK_Y = (89.0, 211.0)                                 # the rack's own footprint on the plate (jig_v5_layout.json)
THICK = 6.0                                            # matches the rack flange thickness (jig_v2.FLANGE_T)
BOLT_D, CB_D, CB_H = 9.0, 14.5, 9.0                    # M8 clearance + counterbore for the head (jig_v5.py)
PLATE_W = 60.0                                         # x: 45-15 .. 75+15, 15 mm clear of each bolt's counterbore
BOLT_IN = 10.0                                         # bolt row, this far in from the plate's inner (rack-side) edge
GAP = 8.0                                              # clear gap from the bolt row to the marker zone
MARKER = 44.0                                          # the physical marker: black square, mm
MARKER_ZONE = 55.0                                     # engraved square the sticker sits in (marker + ~5.5 mm margin/side)
EDGE_OUT = 4.0                                         # clear gap from the marker zone to the plate's outer edge
ENGRAVE_D = 0.3                                        # depth of the engraved placement outline, mm

PLATE_L = BOLT_IN + GAP + MARKER_ZONE + EDGE_OUT        # 77 mm


def build():
    cx0 = sum(BOLT_XS) / 2                            # 60: midpoint of the two T-slot lines
    x0, x1 = cx0 - PLATE_W / 2, cx0 + PLATE_W / 2       # (30, 90): 15 mm clear of each bolt's counterbore
    if SIDE == "hi":
        y_in, sign = RACK_Y[1], 1                       # 211, grows toward +y
    else:
        y_in, sign = RACK_Y[0], -1                      # 89, grows toward -y
    y0, y1 = sorted((y_in, y_in + sign * PLATE_L))
    bolt_y = y_in + sign * BOLT_IN
    marker_cy = y_in + sign * (BOLT_IN + GAP + MARKER_ZONE / 2)

    plate = bd.Box(x1 - x0, y1 - y0, THICK, align=(Align.MIN, Align.MIN, Align.MIN)).translate((x0, y0, 0))
    for bx in BOLT_XS:
        plate -= bd.Cylinder(BOLT_D / 2, THICK + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((bx, bolt_y, -1))
        plate -= bd.Cylinder(CB_D / 2, CB_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((bx, bolt_y, THICK - CB_H))
    cx = (x0 + x1) / 2
    outline = bd.Box(MARKER_ZONE, MARKER_ZONE, ENGRAVE_D, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((cx, marker_cy, THICK - ENGRAVE_D))
    inner = bd.Box(MARKER_ZONE - 2, MARKER_ZONE - 2, ENGRAVE_D, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((cx, marker_cy, THICK - ENGRAVE_D))
    plate -= (outline - inner)                          # a thin 1 mm groove outlining the marker zone, not a pocket
    return plate, (x0, x1, y0, y1), [(bx, bolt_y) for bx in BOLT_XS], (cx, marker_cy)


def main():
    plate, (x0, x1, y0, y1), bolts, marker_c = build()
    plate.label, plate.color = "RackMarkerPlate", bd.Color(0.5, 0.5, 0.55)
    OUT.mkdir(parents=True, exist_ok=True)
    bd.export_step(plate, str(OUT / "RackMarkerPlate.STEP"))
    bd.export_stl(plate, str(OUT / "RackMarkerPlate.stl"))

    b = plate.bounding_box()
    print(f"plate footprint: plate x {x0:.0f}..{x1:.0f}  y {y0:.0f}..{y1:.0f}  (side={SIDE})")
    print(f"bounding box:    x {b.min.X:.1f}..{b.max.X:.1f}  y {b.min.Y:.1f}..{b.max.Y:.1f}  z {b.min.Z:.1f}..{b.max.Z:.1f}")
    print(f"bolts (T-slot x, y): {bolts}")
    print(f"marker zone centre (plate x, y): {marker_c}  size {MARKER_ZONE} mm (marker {MARKER} mm + margin)")
    print(f"rack's own footprint for reference: y {RACK_Y[0]:.0f}..{RACK_Y[1]:.0f}")
    print("CHECK BEFORE PRINTING: clearance against the robot's sweep and the AMR path at this plate position -"
          " this script only checked against the other jig parts' known positions (jig_v5_layout.json), not"
          " moving equipment.")
    print(OUT / "RackMarkerPlate.STEP")


if __name__ == "__main__":
    main()
