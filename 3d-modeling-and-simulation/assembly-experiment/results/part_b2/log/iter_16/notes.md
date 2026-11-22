# iter 16: place the far column (planks 6, 5, 4) first, then the y-124 row (3, 1, 2)

## Hypothesis
Change type: program. New order: home -> plank6 -> plank5 -> plank4 (jig 2 -> far column) -> plank3 -> plank1 ->
plank2 (base A slots -> y-124 row) -> frame. The plank4 release lands 24 mm from the plank3 pick, so the 163 mm
hand-over Line (#26, 1.63 s) + the 40 deg rotation Lines become a 50.5 mm slow lift (the 80 deg re-orientation done
inside it once the fingers clear the plank top) + a ~26 mm Line. The start PTP goes to a transit over plank6 (TCP
~380, pre-turned) + a vertical Line down; the end goes plank2 release -> slow lift (with rotation) -> Line to Point70y
-> the old frame approach. Expected: hand-over -1.4 s, start +0.2..0.3 s, end +0.2 s: net ~-1.0 s (95.3 -> ~94.3 s),
0 violations. Risks: r4 at the new start PTP end (plank6 thin box, L14/L25), the gripper body over the placed far
column at the base A slot picks (12 mm, same as now over the y-124 row), carried planks 3/1/2 next to placed plank4
(~10 mm in x), rotation limits on the new Lines.

## Reason
Evidence: toolbox/move_times2.py on the iter-15 best: the single largest non-fixed move in the plank phase is #26, the
163 mm hand-over from the last y-124 place (plank2, robot x -638) to the first jig-2 pick (plank6, x -779): 1.63 s,
plus the 1.02 s rotation-limited Line #24 before it. With the far column placed first, the last far place (plank4,
x -723, y 103) is 24 mm from the first base-A slot pick (plank3, x -698, y 102), so the hand-over shrinks to the
length of the hand-over between neighbouring planks (~0.3 s). The order still respects L07 (outer first,
robot-side last: the far column is the outer one).
Alternatives: gripping two planks at once (5 + 5 mm inside the 12 mm finger gap) would halve the slow legs but the two
planks go to places 30 mm apart, so no; the frame/home J5 round trip is at its floor (L28/L34); the per-move polish
left is a few tenths. Reordering keeps every grip and slow leg, only the route changes.
Principle: shortest route through the pick/place points (order operations to minimise travel).

## Screening (2 mm)
- r16a (toolbox/reorder16.py, z0 380, g0 0.5): first build used the LAST "Point1" as the head end (whole program
  duplicated, r1/r6/r8 everywhere, L44); fixed: 94.6 s, 0 violations. Start PTP J4-limited 46.8 deg (0.94 s).
- r16b (+ home on the joint path Point88ht -> P16s0, f 0.75, toolbox/home_on_path.py): 94.4 s, 0.
- r16c (z0 368, g0 0.55, home f 0.75): 94.4 s, 0, joints 2215 (lower). Scored r16c.

## Screenshots
- 00 start: same layout as iter 15; arm at the new home, gripper hanging just beyond the plate's far edge at
  robot y ~-200 (in the air, nothing under it but the table edge); planks 1-3 in base A slots, 4-6 in jig 2.
- 01 plank6 released: upright in the far column (y 44), gripper over it, jig 2 has planks 5/4 left.
- 02 plank5 released: far column 2 of 3, upright, nothing crooked.
- 03 plank4 released: far column full, jig 2 empty, planks 1-3 still upright in the base A slots beside it.
- 04 / 05 / 06 plank3 / 1 / 2 released: the y-124 row fills outer to robot-side, all upright next to the far
  column; base A slots empty after 06; arm in a normal elbow-up pose.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, arm at the release pose as
  before; base A empty.
- 08 end: bench assembled in base B, arm back at home.
- topview: the hand-over is now the short plank4 -> plank3 hop (no long diagonal across base A); start is a dashed
  PTP from home to jig 2; the frame/home paths unchanged.

## Result
Expected ~-1.0 s, 0 violations; got 94.4 s (-0.9 s), 0 violations, joints 2206 -> 2215 deg. Phases: planks
70.8 -> 69.8 s, frame 18.0 -> 18.2 (the plank2 -> Point70y approach is ~0.2 s longer), home 6.5 -> 6.4. The reason
held: the 163 mm hand-over + its rotation Line (2.7 s) became a slow lift with the turn inside it + a 26 mm Line; the
start cost +0.3 s as estimated and was partly won back by putting home on the joint path. Kept.
