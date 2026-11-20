# iter 01: slow vertical 50 mm approach/retreat at every grip/release (tool)

## Hypothesis
Change type: tool (+ program it generates).
v3 has 18 r3 violations. 12 of them are of one kind: a vertical grip/release whose slow (20 mm/s) vertical leg is
shorter than 50 mm (40 mm for plank grips, guide release, frame grip; 20 mm for guide grip out; 0 mm before the
frame-lift PTP), so the adjacent fast move is inside the last/first 50 mm.
New tool `toolbox/slow_approach.py`: for every grip/release whose adjacent slow leg is vertical, extend that leg to
exactly 50 mm (point P50 = event TCP + 50 mm z, same orientation):
- in: retarget the fast move before the slow leg to P50, then a slow Line to the old leg top;
- out: insert a slow Line to P50 before the next fast move.
Events whose slow leg is not vertical (the guide's horizontal slide, frame release) are left alone (later iteration).
Expected: r3 18 -> 6 (planks 6, guide grip out 2, guide release in 2, frame grip in 1, frame grip out 1);
rule_violations 28 -> 16 (r4/r5 unchanged; r5 might shift slightly). Cycle +~6-8 s (extra slow mm).

## Screenshots
- 00 start: guide (yellow) on base B, frame 1 in base A, 6 planks upright in the plank jig in the middle; arm at home. Nothing floating.
- 01 after guide release: guide turned over and lying on base A over frame 1; base B empty frame 2 visible; arm above base A in a normal pose.
- 02 plank3 placed: plank3 stands upright in the guide slot over frame 1; 5 planks left in the jig.
- 03 plank6: two planks upright in the guide; gripper above, sensible pose.
- 04 plank2 / 05 plank5 / 06 plank1 / 07 plank4: planks added one by one, all upright, none crooked or floating; jig empties in order; arm reaches over base A from the robot side.
- 08 guide release on base B: guide back on base B (frame 2), the 6 planks stand in frame 1 on base A without the guide; arm folded near the plate edge, fine.
- 09 frame 1 + planks released: frame 1 turned over, planks down into frame 2 on base B, guide on top; wrist at the plate edge (y ~ -230), pose plausible.
- 10 end: bench assembled in base B (planks between the two frames), arm back at home.
- topview: TCP path as in v3, plus the new short vertical legs (not visible at this scale); the frame-release exit (low traverse at y -218) still visible at the bottom.

## Result
Expected r3 18 -> 6, violations 28 -> 16, cycle +6-8 s.
Got (2 mm): r3 18 -> 6 exactly as predicted; r1 5 -> 6, r5 4 (unchanged) -> violations 17; cycle 239.8 -> 246.6 s (+6.8 s:
guide +3.3, planks +2.5, frame +1.0).
The extra r1 is not a new collision: the guide-grip retreat is now two moves (Point8 slow 20 mm, Point8u slow 30.5 mm)
and the pre-existing link_3/plank4/plank5 contact at the guide grip on base B is counted per move.
(The 10 mm screen showed r5 2; at 2 mm it is 4 again: coarse screen under-counts clearance, see L03.)
Keep: 28 -> 17 violations, verdict BETTER. Next: the guide grip/release (horizontal slide into the side pocket, link_3
hits planks 4/5 there) is the biggest remaining cluster (r1 6, r3 4, r5 4).
