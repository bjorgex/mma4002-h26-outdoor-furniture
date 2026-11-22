# iter 14: planks 4-6 from a second jig at the plate's far edge (base A + jig 1 move 15 mm toward the robot)

## Hypothesis
Change type: mixed (layout + jig_cad + program). Base A (ground x 480 -> 465) and the plank jig (345 -> 330) move
15 mm toward the robot; the plank jig keeps only slots 1-3 (40 x 86 mm); planks 4-6 start in a new 25 x 100 mm jig
("Plank jig 2", ground x 560..585, 5 mm from base A and 5 mm from the plate edge), at the same y and yaw as before.
Program: toolbox/far_jig.py shifts every base-A / jig-1 move by -15 mm ground x and the three group-2 pick blocks by
+195.5 mm (to the far jig). Expected: the six group-2 transfers drop from 156-169 mm Lines (1.56-1.69 s) to ~50-65 mm
(~0.55-0.65 s), about -5.5 s; the hand-over from the last group-1 place to the first far pick gets ~0.5 s longer:
net ~-5 s (105.1 -> ~100 s), 0 violations. Risks: reach / IK at the far pick (robot x ~-779), the frame phase after
the 15 mm shift (r1 at the flip / final insertion, L05), r5 of the first far-pick transfer over the placed y-124 row.

## Reason
Evidence: toolbox/move_times2.py on the iter-13 best: the plank phase is 80.6 s, ~66.6 s of it fixed (4 slow legs
+ 2 waits per plank); the rest is transfers, and the six group-2 transfers (plank6/5/4 carries and returns) are the
longest: 1.56-1.69 s, ~9.8 s together, because those planks are placed in frame 1's far column (robot x -738..-748)
while they are picked 160 mm away on the robot side of base A (x -583). The far column sits only 20 mm from the plate
edge; moving base A 15 mm inward makes room for a narrow jig there, ~50 mm from the places.
Alternatives: more program polish (via points, rotations) has little left (iters 05-13 gained 0.4-1.5 s each, the
J5 round trip is at its floor, L28/L34); rotating base A 180 deg would put the far column near the robot too, but it
turns the frame grip and the flip (a whole new frame phase, L40) - too big for one iteration. Splitting the jig keeps
every grip, orientation and order, only the distances change.
Principle: shortest route / present parts next to where they are assembled (feed each place row from its own side).

## Screening (2 mm)
- p14a (toolbox/far_jig.py, --da 15 --far 195.5): IK found for every shifted move without branch jumps (group-2 picks
  dJ ~40 deg, same J5 -90 branch); 2 mm screen 100.3 s, 0 violations at the first try. Fixture gaps
  (scratch/cell_bounds.py, L32): jig 2 x -791.4..-766.3 vs base A -761.4 (4.9 mm), plate edge -796.5 (5.1 mm); jig 1
  -576.4 vs base A -581.3 (4.9 mm). Walls (CAD): jig 2 7.5 mm (x), 3.8 mm between slots, 6.9 mm at the ends; jig 1
  outer wall 5.2 mm. Jig 2 clears the vision squares (ground y 95..195 vs squares at 3..28 / 412..437).

## Screenshots
- 00 start: base A 15 mm closer to the robot, the short jig 1 (planks 1-3, upright) on its robot side, the new narrow
  jig 2 at the plate's far edge with planks 4-6 upright (turned 80 deg); guide on base B; arm home. No overlaps.
- 01 plank3, 02 plank1, 03 plank2 released: the y-124 row of frame 1 fills robot-side-last, planks upright, jig 1
  empties; planks 4-6 still in jig 2.
- 04 plank6, 05 plank5, 06 plank4 released: the far column fills y 44 -> 74 -> 104 straight from jig 2 behind it,
  planks upright, none crooked; arm reaches over the far edge in a normal elbow-up pose; jig 2 empty after 06.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, arm at the release pose as before.
- 08 end: bench assembled in base B, arm home; base A and both jigs empty.
- topview: group-2 transfers are now short x-lines between jig 2 (x ~-779) and the far column (x ~-728), plus one
  diagonal hand-over from the last y-124 place to jig 2; the frame/home paths unchanged.

## Result
Expected ~-5 s, 0 violations; got 100.3 s (-4.8 s), 0 violations, joints 2817 -> 2538 deg. Phases: planks
80.6 -> 75.8 s, frame 18.0 / home 6.5 unchanged (the 15 mm shift of the frame grip cost nothing). The reason held:
the group-2 transfers were set by the 160 mm pick-to-place distance; feeding the far column from its own side cut
them to ~50 mm. Kept.
