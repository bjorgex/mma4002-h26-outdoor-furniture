# iter 02: pre-rotate the gripper in the fast lift after the plank2 place (#34), so PTP #35 turns J6 less

## Hypothesis
Change type: program. Line #34 (Point41 -> Point38, the 72.2 mm fast lift after releasing plank2) gets a new end
point Point38b at the same TCP position, with the tool orientation already turned part of the way (slerp fraction g
~0.45) toward the orientation of Point25 (the next pick transit, plank6 in the turned jig row). The PTP #35 then
starts from Point38b. Point38 itself (end of the PTP #30 into the place) is unchanged. Expected: -0.6 to -0.7 s
(PTP #35 1.52 s J6-limited -> ~0.85 s J3-limited; Line #34 stays 0.72 s as long as its rotation <= 36 deg),
0 violations. Risk: the open gripper turning ~35 deg 75-125 mm over the just-placed plank tops (r1/r5), r4 on the
PTP start (unchanged position, so unlikely).

## Reason
Evidence: toolbox/move_times2.py on the iter-01 best: PTP #35 Point38 -> Point25 = 1.52 s, limited by J6 (75.8 deg),
the single most expensive plank-phase PTP (others 0.74-1.03 s, J3-limited). It is the hand-over from the y-124 place
row (planks 1-3) to the turned pick row (planks 4-6): the tool must turn ~76 deg about vertical somewhere. The Line
#34 before it is 72.2 mm at 100 mm/s = 0.72 s, and under the B2 judge a Line may turn up to 50 deg/s without costing
time, so ~36 deg of the turn is free there.
Alternatives: (a) turn the pick row of planks 4-6 further / place them differently (layout, larger change, the place
orientation is fixed by the bench); (b) shrink rotation-limited Line #77 in the frame flip (as a PTP its J3 change
54 deg = 1.08 s > 0.80 s, and merging #76+#77 into one PTP saves only ~0.12 s); (c) J5-limited moves #79 / home are
at the J5-travel floor (L28). (d) here gives the largest saving for one small program change.
Principle: do re-orientation in parallel with a translation that costs time anyway (the iter-01 idea, mirrored:
there rotation was moved out of a Line into a PTP, here into a Line that has slack).

## Screening (before the score)
- toolbox/pre_rot.py (new, T32) on step 40 toward Point25: g 0.45 = 36.0 deg extra rotation in Line #34 (still
  0.72 s, distance-limited), PTP #35 dJ 75.8 -> 39.8 deg (J6) = 0.80 s. 2 mm screen: 113.2 s, 0 violations. g 0.55
  (44 deg) would make the Line rotation-limited (0.88 s) for at most ~0.15 s off the PTP; not pursued. Scored g 0.45.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (raised), 6 planks upright in the plank jig; arm at home, nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, 5 planks in the jig; gripper raised over base A.
- 02 plank1 released: two planks upright side by side in frame 1; 4 in the jig.
- 03 plank2 released: y-124 row of frame 1 full (3 planks); the 3 turned planks in the jig; gripper at the place transit (the changed Line starts right after this).
- 04 plank6 released: 4 planks in frame 1, upright, the turned row started; arm in a normal elbow-up pose - the pre-rotated hand-over left nothing displaced.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig.
- 06 plank4 released: all 6 planks in frame 1, jig empty.
- 07 frame released: frame 1 + planks turned over and seated in the guide / frame 2 on base B, planks vertical, nothing crooked; arm reaching over the -y edge as before.
- 08 end: bench assembled in base B, arm back at home; base A and the plank jig empty.
- topview: paths as in iter 01; the PTP from the plank2 place transit to the plank6 pick (orange-red dashed) has the same TCP endpoints - only the tool orientation along it changed.

## Result
Expected -0.6 to -0.7 s, got 113.9 -> 113.2 s (-0.7 s), 0 violations. Phase planks 87.8 -> 87.1 s, others unchanged;
joint travel unchanged at 3485 deg (the J6 turn is the same, just moved from the PTP into the Line). The reason held:
PTP #35 was J6-limited and the Line before it had ~36 deg of free rotation at 50 deg/s. Kept.
Next: the same trick on the other side of PTP #35 - Line #36 Point25 -> Point26 (52.5 mm = 0.52 s) can carry ~26 deg
more of the turn (needs a separate Point25 copy since #40 returns to Point25), and the remaining J6-heavy PTPs.
