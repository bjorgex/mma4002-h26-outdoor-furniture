"""TEST ONLY: adds a marker tab to Guide small's tip, temporarily overwrites jig_parts/guide_1_v5.stl,
regenerates cell_v9.glb, and leaves it in place for a collision check. restore_guide_tab_test.py puts
the original back. Do not commit while the modified STL is in place.
"""
import shutil
from pathlib import Path
import build123d as bd
from build123d import Align
import jig_v3

HERE = Path(__file__).resolve().parent
STL = HERE / "jig_parts" / "guide_1_v5.stl"
BACKUP = HERE / "jig_parts" / "guide_1_v5.stl.orig"

# tip region found by ray-casting the top (guide_flat_check.py): left tip x -73.4..-44.4, y 61.2..90
TAB_X = (-86.0, -31.0)     # 55 mm wide, centred on the tip's x range (-73.4..-44.4, centre -58.9)
TAB_Y = (90.0, 145.0)      # 55 mm long, extending outward from the tip's y max (90) into open space
TAB_Z = (20.0, 60.0)       # same wall height as the rest of the arm (flush top at z=60, for the marker)

if not BACKUP.exists():
    shutil.copy(STL, BACKUP)

small, big = jig_v3.jig_v3_parts()[1]
tab = bd.Box(TAB_X[1] - TAB_X[0], TAB_Y[1] - TAB_Y[0], TAB_Z[1] - TAB_Z[0],
             align=(Align.MIN, Align.MIN, Align.MIN)).translate((TAB_X[0], TAB_Y[0], TAB_Z[0]))
new_small = small + tab
bd.export_stl(new_small, str(STL), tolerance=0.05, angular_tolerance=0.2)
b = new_small.bounding_box()
print(f"modified guide_1_v5.stl written: bbox x {b.min.X:.1f}..{b.max.X:.1f} y {b.min.Y:.1f}..{b.max.Y:.1f} z {b.min.Z:.1f}..{b.max.Z:.1f}")
print(f"tab: x {TAB_X} y {TAB_Y} z {TAB_Z}")
