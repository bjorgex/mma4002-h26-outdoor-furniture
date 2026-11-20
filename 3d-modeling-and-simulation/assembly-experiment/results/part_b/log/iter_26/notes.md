# iter 26: plank jig moved toward base A (shorter pick <-> place PTPs)

## Hypothesis
Change type: layout (+ program: pick moves shifted with toolbox/shift_moves.py, home re-placed with
toolbox/home_on_path.py).
The planks phase (89.9 s) is 74 % fixed slow legs + waits, but its 12 pick <-> place PTPs take ~13 s (0.9-1.5 s
each, 44-73 deg of J2/J3 reach change: plank jig at robot x -356..-446, frame 1 at -615..-757). With the guide
trip gone (iter 25) the 150 mm gap between the jig and base A is free. Move the plank jig D = 100 mm away from the
robot (ground x 150 -> 250; robot x -456..-546, 50 mm gap to base A) and shift all 30 pick moves (Point16..19,
25..28, 34..37, 43..46, 52..55, 61..64 + the 's' legs) by robot dx -100. Heights stay (r4 transits unchanged).
Expected: PTPs ~1/3 shorter in reach -> about -0.3 s each, ~-3.5 s in planks; home -> Point16 PTP changes too
(re-place home on the Point88h -> Point16 path, f 0.7): +-0.5 s. Total ~-3 to -4 s, violations 0.
Risks: r1 of the carried plank's lower end vs the frame 1 / base A edge (sweeps lower now near base A), the arm vs
the jig during the frame grip approach (Point80h -> Point80); IK at the farther picks. Fallback D = 60.

Screen (--step 2 --no-shots, scratch/j26b.json): 0 violations, 117.5 s. Home re-placed on the Point88h -> Point16
joint path (f 0.7): TCP (-737, -278, 489).

## Screenshots
- 00 start: plank jig now at robot x ~-456..-546 (between the robot and base A, ~50 mm gap), 6 planks upright in
  it; guide on base B over frame 2, frame 1 + pieces in base A; arm in home over the base B corner, gripper high.
- 01 plank3 released upright in frame 1 (base A), vertical; 5 planks in the jig; gripper above it.
- 02 plank6 placed: two upright in frame 1, both vertical; arm over base A, nothing touching the jig.
- 03 plank1 placed: three upright, three in the jig; no lean.
- 04 plank5 placed: four upright; two left in the jig.
- 05 plank2 placed: five upright; one (plank4) in the jig.
- 06 plank4 placed: all six upright in frame 1, jig empty; guide still on base B.
- 07 frame 1 + planks turned over and lowered through the guide into frame 2 on base B; planks vertical, frame 1
  level on top; arm reaching past the plate edge at y ~-250 (as iter 25); base A and the jig empty.
- 08 end: bench assembled in base B with the guide (same end state as iter 25); arm back in home, gripper high.
- topview: the pick <-> place PTP arcs are visibly shorter (jig at x -456..-546); frame approach and flip paths
  unchanged; the jig is clear of base A and of the frame path.

## Result
Expected ~-3.5 s; got 118.3 -> 117.5 s (-0.8 s): planks 89.9 -> 89.0, frame and home unchanged. Joints 4386 -> 4084.
Why less than expected: the three PTPs to the A4..A6 row (Point29, 47, 65) are J6-limited (the plank turns ~75 deg
about vertical: J6 162 -> 87), so they got slightly LONGER (1.44 -> 1.52 s etc.); the other three place PTPs and the
three return PTPs gained ~0.3 s each. 0 violations at 2 mm, free-move clearance 41.5 mm. Kept.
Next: the J6-limited row - present those three planks in the jig already turned 90 deg (jig CAD / slot rotation),
so their pick -> place PTPs lose the 75 deg J6 turn.
