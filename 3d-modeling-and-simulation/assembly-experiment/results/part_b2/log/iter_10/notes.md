# iter 10: pre-turn frame 1 toward the flip during its lift out of base A

## Hypothesis
Change type: program. The frame flip (Point80L -> Pvia -> Point85, 1.15 + 2.69 s) is J5-limited: J5 -53.8 -> +138.1
(192 deg, floor 3.84 s). The lift after the frame grip (#63 slow 40 mm 2.0 s, #64 slow 10.5 mm 0.53 s, #65 fast
57.4 mm 0.57 s) turns nothing, though it could turn ~100 + 26 + 28 deg for free. Turn Point80 / Point80u / Point80L
toward the Pvia orientation (toolbox/turn_toward.py, g 0.15 / 0.27 cumulative / 0.6), so J5 starts the flip at
~-32.5, and move Pvia's J6 (29.5 -> 12) and J5 (3.7 -> 0) to rebalance the two PTP halves (scratch/set_joints.py,
joints by FK). Expected -0.4 s (108.1 -> ~107.7), 0 violations. Risk: r1 frame/planks vs base A / plank jig while
tilted low over the pocket.

## Reason
Evidence: toolbox/move_times2.py on the iter-09 best: #66 Pvia 1.15 s J5 57.6 and #67 Point85 2.69 s J5 134.3 = 3.84 s,
the J5 floor of the flip (L28/L34), while the three lift Lines before it have rot 0.0. Iter 08/09 showed J5 follows
tool rotation inside paid Lines (home trip, both ends); the frame grip is the remaining wrist-limited PTP pair with
idle Lines in front. Alternatives considered: closing the cycle at the release pose (no home PTP) saves only 0.05 s
(J5 travel is the same, home lies on the J5 path); turning in the release descent is unsafe (planks already in the
guide slots); more transfer gains need layout moves already done (iter 03). Screens: slerping harder (g 0.95) pushes
the turn into J4/J6 (J5 only -25, PTP J6-limited 1.75 s), so the turn is kept moderate.
Principle: overlap motion with already-paid moves.

## Screening (before the score)
- f10c (Point80L g 0.45): 107.8 s, 0 violations at 2 mm. f10d (+Point80u g 0.12): 107.8 s, clean.
- f10e (Point80 0.15, Point80u 0.3, Point80L 0.6): PTP became J6-limited (Pvia J6 29.5 vs -16.3).
- f10f = f10e + Pvia J6 12 / J5 0: PTPs 0.65 + 2.76 s (J5), 2 mm screen 107.7 s, 0 violations -> scored.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig, arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer y-124 slot, gripper vertical above it, 5 planks left in the jig.
- 02 plank1 released: two planks upright in frame 1, 4 in the jig, straight.
- 03 plank2 released: the y-124 row of 3 planks upright, 3 left in the jig.
- 04 plank6 released: 4 planks in frame 1, 2 in the jig, upright.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig.
- 06 plank4 released: all 6 planks upright in frame 1, jig empty.
- 07 frame released: frame 1 + planks turned over, seated through the guide into frame 2 on base B, arm reaching over the -y edge as before; nothing crooked.
- 08 end: bench assembled in base B (planks vertical, guide on top), arm at home; base A and plank jig empty.
- topview: same TCP paths as iter 09; the change is a re-orientation during the frame lift and a via-point joint
  change (the dashed flip PTP leaves base A at the same place).

## Result
Expected -0.4 s, got 108.1 -> 107.7 s (-0.43 s by move_times2), 0 violations. Phase frame 1 + planks 18.4 -> 18.0 s,
others unchanged; joint travel 2900 -> 3014 deg (tie-break only). The reason held: the flip pair was J5-limited and
~20 deg of J5 fits into the paid lift Lines; harder slerps go into J4/J6 rather than J5 (g 0.95: J5 only -25, PTP
J6-limited), so the gain stops there. Kept (better, clean, shots fine).
