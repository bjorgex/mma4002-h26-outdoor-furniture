# iter 07: pre-turn the tool (J6) during the slow release leg after plank4

## Hypothesis
Change type: program. The PTP #58 Point70 -> Point80h (to the frame-foot grip) is J6-limited: J6 74.9 -> 25.5
(49.4 deg, 0.99 s); next joint J4 33.7 deg (0.67 s). Turn the tool -20 deg about its own (vertical) axis already in
the upper 20.5 mm of the slow release leg after plank4 (#55, 2.52 s, spare rotation capacity), keep that yaw on the
fast up-line (Point65) and the Line to Point70 (new tool toolbox/yaw_steps.py + toolbox/split_rot.py G 1). Then the
PTP's J6 delta is ~29 deg < J4's 33.7, so it becomes J4-limited: expected -0.3 s (109.4 -> ~109.1), 0 violations.
Risk: r1 fingers vs plank4 / plank5 tops while turning (split at 30 mm like iter 06), r4 at Point70's PTP start
(TCP unchanged, so unlikely), J4/J6 along the turning Line.

## Reason
Evidence: toolbox/move_times2.py on the iter-06 best: #58 Point80h 0.99 s "J6" (49.3 deg), and show_joints gives
J4 33.7 deg as its second joint, so ~0.32 s of it is J6 alone. The slow leg #55 right before it (50.5 mm at 20 mm/s,
2.52 s) turns nothing. Iter 06 proved the same overlap on the plank2 release leg (-0.5 s, clean).
Alternatives: the J5-limited home PTP (3.2 s) and frame flip (2.69 s) are at their J5 floor (L28, L34); the slow legs
and waits are fixed by r3; a jig/grip change to remove events is bigger but needs several iterations. This is the
largest remaining single-move slack that one local edit can take.
Principle: overlap motion with already-paid fixed-cost events (re-orient inside a slow leg).

## Screening (before the score)
yaw_steps.py sign probe: +20 raised J6 at Point70 to 94.9 (wrong way), -20 lowered it to 54.9 (PTP J6 delta 29.4 <
J4 33.7). split_rot.py step 67 (Point68) K 30 G 1 -> one 2 mm screen: 109.1 s, 0 violations.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig; arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, gripper above it, 5 planks left in the jig.
- 02 plank1 released: two planks upright in frame 1, 4 in the jig; normal elbow-up pose.
- 03 plank2 released: y-124 row of 3 planks upright and straight; neighbours untouched.
- 04 plank6 released: 4 planks in frame 1, 2 left in the jig, upright.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig.
- 06 plank4 released (the changed leg follows): all 6 planks upright and straight in frame 1, jig empty, gripper right above plank4.
- 07 frame released: frame 1 + planks turned over, seated through the guide into frame 2 on base B; arm reaching over the -y edge as before.
- 08 end: bench assembled in base B (planks vertical, guide on top), arm back at home; base A and plank jig empty.
- topview: paths as in iter 06; the change is a rotation on a vertical leg, invisible from above; nothing new crosses the plate.

## Result
Expected -0.3 s, got 109.4 -> 109.1 s (-0.3 s), 0 violations. Phase frame 1 + planks 18.7 -> 18.4 s, planks / home
unchanged, joint travel 2799 deg (same), 71 -> 72 moves. The reason held: #58 is now J4-limited (0.67 s); the
20-deg turn fits in the upper 20.5 mm of the slow leg (1.02 s x 50 deg/s), fingers clear plank4 before turning
(r1 0, free-move clearance 41.5 mm unchanged). Kept.
Next: remaining J-limited PTPs are J3 (plank transfers) and J5 (flip / home, at their floor); further gains need
fewer fixed-cost events (e.g. the 10.5 mm "s" pre-legs at 20 mm/s at every pick: check whether the slow leg could
start lower / be shared), not more re-orientation tricks.
