# iter 06: vertical exit out of the frame release

## Hypothesis
Change type: program.
r3 at #128: after "release frame 1 with the planks" (end of Point87) the gripper leaves with Point88, a slow Line
sideways/down (dy -21, dz -12.5 flange), then Point89 (+150 x) and Point90 (up/in to the home side), all at 20 mm/s
(~23 s of slow travel). Replace the exit by: Point88 = a slow vertical Line straight up 50.5 mm from the release point
(reverse of the insertion; the open fingers slide up off the foot, which now points up), then drop Point89 and run
Point90 as a fast Line (100 mm/s, it is a free move after the 50 mm leg).
Expected: violations 2 -> 1 (r3 0; r1 Base B/plank3 at #127 unchanged), cycle about -15 s (phase "frame 1 + planks"
/ "home"), as long as the new straight path to Point90 keeps >= 10 mm clearance (r5) and the fingers clear the foot.

Done with toolbox/shift_moves.py (Point88 -> Point87 flange + 50.5 mm z, IK on the same branch, joints within ~5 deg
of Point87), Point89 deleted, Point90 speed 20 -> 100 (Edit). 10 mm screen: 0 violations, cycle 229.6 s.

## Screenshots
- 00 start: as iter 05: guide on raised base B, frame 1 + pieces in base A, 6 planks upright in the jig, arm at home.
- 01 guide on base A: flat over frame 1, gripper horizontal beside it; nothing floating.
- 02 plank3: upright in the outer y124 slot of the guide; 5 planks in the jig.
- 03 plank6: second plank upright, y44 row; jig outer slot empty.
- 04 plank1: third plank upright beside plank3; not crooked.
- 05 plank5: 4 planks in the guide, 2 left in the jig.
- 06 plank2: robot-side end of the y124 row; 1 plank left in the jig.
- 07 plank4: all 6 upright in the guide, jig empty, arm over base A.
- 08 guide back on base B: flat on the riser, 6 planks upright in frame 1, gripper beside base B.
- 09 frame 1 + planks released into frame 2: turned over, planks down into base B, gripper at the foot (now pointing up)
  at the plate edge; same pose as iter 05 (the change is after this shot).
- 10 end: bench assembled in base B, base A empty, arm at home; nothing knocked over by the new exit.
- topview: the frame-release exit now goes straight from the release point (-747, -197) to the home side
  (one fast line) instead of the old slow dogleg via x -600; no new crossings over a jig.

## Result
Expected violations 2 -> 1, cycle about -15 s. Got (2 mm): violations 1 (r1 1 at #127 Base B/plank3, unchanged; r3 0),
cycle 247.9 -> 229.6 s (-18.3 s, all in "home": 27.0 -> 8.8 s; the slow 20 mm/s dogleg was ~18 s), joints
9006 -> 8923 deg. min free clearance still 31.8 mm (the new fast line is not the bottleneck).
Kept: verdict BETTER, screenshots fine. Left: the zero-clearance final insertion contact Base B/plank3 (#127, L05):
next a jig_cad change (slack / lead-in in the base B pocket where plank3 lands) or a few-mm shift of the insertion.
