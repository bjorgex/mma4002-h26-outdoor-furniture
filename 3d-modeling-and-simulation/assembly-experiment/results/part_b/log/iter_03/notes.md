# iter 03: plank jig moved 60 mm toward base A (layout + plank-pick moves shifted)

## Hypothesis
Change type: layout (the program's plank-pick moves follow the jig; no other program change).
5 of the 8 violations are r1 link_3 vs plank4/plank5 while the guide is gripped at base B (moves 6-10): planks 4-6
stand in the jig row on the base-B side (robot y ~ -17), under the forearm reaching to base B (robot y -170).
Change: PLANK_JIG ground y 190 -> 130 (robot y +60), so the jig rows sit at robot y ~ +45 / +75, away from the base-B
reach and closer to base A (where the planks go). All pick moves at the jig (Point16..19, 25..28, 34..37, 43..46,
52..55, 61..64 incl. the *s legs, every occurrence) are shifted by +60 mm robot y with IK (toolbox/shift_moves.py,
now with --dx/--dy and NAME@all).
Expected: r1 6 -> 1 (the link_3 cluster gone; plank1/plank2 at move 76 may stay), violations 8 -> 3.
Cycle: about -1..-3 s (the jig -> base A transfers get shorter, the base-A side PTPs swing less J1).

## Screenshots
- 00 start: plank jig now at robot y ~30..90 (between the robot and base A), 6 planks upright in it; guide on the raised base B; arm at home. Nothing floating.
- 01 guide released on base A: guide flat over frame 1, gripper horizontal beside base A; planks still in the jig, untouched; base B shows frame 2.
- 02 plank3: upright through the guide into frame 1, gripper above; 5 planks left in the jig.
- 03 plank6 / 04 plank2 / 05 plank5 / 06 plank1 / 07 plank4: one more upright plank per shot in the guide, none crooked or floating; the jig empties in order; arm reaches over base A in a normal elbow-up pose.
- 08 guide back on base B: guide flat over frame 2 on the riser; 6 planks stand in frame 1 on base A; gripper horizontal beside base B, arm well clear of the (empty) jig.
- 09 frame 1 + planks released: frame 1 turned over, planks down through the guide into frame 2 on base B; wrist at the plate edge (y ~ -230) as in iter 02.
- 10 end: bench assembled in base B (frames top and bottom, 6 planks between), arm at home.
- topview: the plank-pick ends now at y 45..75; the jig -> base A paths are shorter and nearly parallel; nothing crosses the base-B approach any more.

## Result
Expected violations 8 -> 3 (r1 6 -> 1), cycle -1..-3 s. Got (2 mm): violations 4 (r1 2, r3 1, r4 1), cycle 247.0 s (-0.5:
planks -0.6, rest unchanged), joints 8994 deg (+37).
- r1: the 5 link_3 vs plank4/5 hits are gone, as predicted. plank1/plank2 at move 76 (carried plank1 brushing plank2 in
  the jig on the way out) is still there. A new hit, Base B/plank3 at move 126 (the final insertion), appeared: the
  base-B geometry did not change, so it must come from a tiny change of plank3's pose in frame 1 (the shift is
  60 mm robot y, the jig moved 60 mm ground y: ~0.03 mm difference in x/z) - a marginal contact that iter 02 missed
  by a hair (L05). 10 mm screen showed r1 0 (L03 again).
- Cycle only -0.5 s: the plank transfers are PTPs whose time is set by the largest joint move, not the distance.
Kept: verdict BETTER (8 -> 4), screenshots fine. Next: the frame release (r3 side slide out, r4 PTP Point82 after the
frame grip, Base B/plank3 contact) - one cluster, the final insertion; then plank1/plank2 at the pick.
