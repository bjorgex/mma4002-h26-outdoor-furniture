"""Print test of THE INTERFACE only - the plank-end snap, demonstrator 1:7.5 (insert_draft.py, DEMO = True).

Not a product: the smallest piece of the real chair that has the interface in it.
    S1 slice   29 mm of S1's solid top rail with seat channels 1 and 2 - cut out of the real S1,
               so channels, mouth flare, barb recesses and the wall between two channels are the
               ones the demonstrator gets                                           print 2
    W2 plank   the real chair plank, interface at both ends                         print 2
Together they make a 75 mm wide strip of the chair seat: 2 planks between 2 frame slices. The
slice is symmetric across its width, so the same print is the left and (turned 180 deg) the right.

Print: PLA, 0.4 nozzle, 0.2 layers. Slice on its outer face (channels open upward, the way S1
gets printed), plank flat (prongs bend along the layers). The STLs are already in that pose.

Test - the robot cell's move, frame pushed ONTO the plank end:
    1 hold a plank, push a slice straight onto one end: does it go in and click?
    2 pull: does it hold? (no way back - it's sawn off in real life; print spare planks)
    3 the second plank next to it, then the other slice on the other ends: a rigid strip?

Run:  python interface_test.py   -> interface_test/S1 slice.stl, interface_test/W2 plank.stl
"""

# %% Setup
import sys
from itertools import combinations
from pathlib import Path

from build123d import Box, Compound, Plane, Pos, Rot, export_stl, mirror

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(HERE))
import insert_draft as d  # noqa: E402
from furniture import MIN3, paint  # noqa: E402

assert d.DEMO, "the print test is for the demonstrator: set DEMO = True in insert_draft.py"
OUT = HERE / "interface_test"
MARGIN = 3        # rail kept outside the two channels (wall left: 3 - 0.25 - 0.8 = 1.95 mm)
N = 2             # seat channels / planks in the test

# %% The two print parts
y0, y1 = -MARGIN, (N - 1) * d.P + d.W + MARGIN
SLICE = paint(d.S1B & Pos(0, y0, d.Z0) * Box(d.TUBE, y1 - y0, d.TOP - d.Z0, align=MIN3),
              "S1 slice (interface test)")
PLANK = d.plank(d.LP)

# %% Check: the strip assembled - planks in their fitted pose, nothing overlaps
strip = [SLICE, paint(Pos(d.WIDTH, 0, 0) * mirror(SLICE, Plane.YZ), SLICE.label)]
strip += d.planks_at(d.seat_locs()[:N])
bad = [(p.label, q.label, round((p & q).volume, 3)) for p, q in combinations(strip, 2)
       if (p & q).volume > 1e-3]
bb = SLICE.bounding_box().size
print(f"S1 slice   {bb.X:5.1f} x {bb.Y:5.1f} x {bb.Z:5.1f} mm")
bb = PLANK.bounding_box().size
print(f"W2 plank   {bb.X:5.1f} x {bb.Y:5.1f} x {bb.Z:5.1f} mm")
print(f"strip      {d.WIDTH:5.1f} mm wide, {len(strip)} parts, overlaps: {bad or 'none'}")
print(f"channel    {d.W + 2 * d.CLEAR:.2f} x {d.T + 2 * d.CLEAR:.2f} mm for a {d.W:.2f} x {d.T:.2f} plank "
      f"(calliper both after printing)")
print(f"barb       {d.BARB_H} out, {d.CLEAR} clearance -> the prong bends {d.BARB_H - d.CLEAR:.2f} mm going in "
      f"and the catch overlaps {d.BARB_H - d.CLEAR:.2f} mm")
print(f"wall between channels {d.GAP - 2 * d.CLEAR:.2f} mm, recesses {d.RECESS} deep from both sides "
      f"-> {'open window at the barbs' if 2 * d.RECESS >= d.GAP - 2 * d.CLEAR else 'closed'}")

# %% Export in print pose: slice on its outer face (x = 0 -> bed), plank flat as it is
OUT.mkdir(exist_ok=True)
for name, part in (("S1 slice", Rot(0, -90, 0) * SLICE), ("W2 plank", PLANK)):
    b = part.bounding_box().min
    export_stl(Pos(-b.X, -b.Y, -b.Z) * part, str(OUT / f"{name}.stl"), tolerance=0.005, angular_tolerance=0.1)
    print(f"-> interface_test/{name}.stl")

# %% Show (OCP viewer, if open): the assembled strip
if __name__ == "__main__":
    from ocp_vscode import get_port, show
    if get_port() is None:
        print("OCP viewer not open, skipping show")
    else:
        show(Compound(children=strip, label="strip"), names=["strip (2 x S1 slice + 2 x W2)"])
