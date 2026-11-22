# iter 09: pre-turn the tool from home in the descent to the first plank pick

## Hypothesis
Change type: program. The start PTP #2 Point1 (home) -> Point16 (1.37 s) is J5-limited (J5 -21.6 -> -90, 68.4 deg;
J6 37.5, J4 16.8 next). The fast Line #3 Point16 -> Point17 (52.5 mm, 0.52 s) and the slow leg part #4 Point17 ->
Point17s (10.5 mm, 0.53 s) turn nothing, though each could turn ~26 deg of tool rotation for free (Line time =
max(dist/speed, rot/50 deg/s)). Turn Point16 (and if needed Point17) toward the home orientation
(toolbox/turn_toward.py), so the PTP needs less J5 and the Lines do the rest of the turn while the fingers are still
>= 25 mm above plank3's top. Expected ~-0.4..-0.6 s (108.8 -> ~108.3), 0 violations. Risk: r1/r5 gripper or camera vs
the neighbouring planks in the jig while tilted; r4 is unaffected (TCP positions unchanged).

## Reason
Evidence: toolbox/move_times2.py on the iter-08 best: #2 home -> Point16 1.37 s "J5" 68.4 deg, while the next Line
#3 (0.52 s) and the slow segment #4 (0.53 s) have rot 0.0. Iter 08 used the same overlap at the other end of the
home trip (lift after the frame release) and it held (J5 follows tool rotation ~1:1), but there the elbow at the
reach edge capped it (L37); here the pick is at robot x -576 (mid reach) with the elbow high, so the cap should not
apply. Alternatives: the transfers between plank events are already single Lines (iter 04, L33); the frame flip and
home PTP are J5 floors (L28/L34); dropping or moving home only moves the same J5 travel between the two PTPs
(1.37 + 2.89 s = the 213 deg J5 floor), so the only way under it is to hide J5 inside Lines that are paid anyway.
Principle: overlap motion with already-paid (distance- or rule-limited) moves.

## Screening (before the score)
turn_toward.py on step 2 (Point16) toward step 1 (Point1), and on step 3 (Point17):
- Point16 g 0.35 only (scratch/a09a.json): 108.4 s by move_times2 (PTP 0.87 s J5 43.5; Line #3 0.61 s ROT-LIMITED,
  30 deg; total home->Point17 tool rotation ~87 deg).
- Point16 g 0.6 + Point17 g 0.28 (scratch/a09c.json): PTP 0.60 s (now J1-limited, 30.1 deg - J1 grows with g),
  Line #3 0.56 s (27.8 deg), slow #4 0.53 s (24.4 deg, fingers still >= 25 mm over plank3's top), #5 unturned.
  2 mm screen: 108.1 s, 0 violations -> scored. No further g: the PTP is J1-limited and more turn would have to
  happen in the last 40 mm while the fingers straddle the plank.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig, arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer y-124 slot, gripper vertical above it, 5 planks in the jig.
- 02 plank1 released: two planks upright in frame 1, 4 in the jig, straight.
- 03 plank2 released: the y-124 row of 3 planks upright, 3 left in the jig.
- 04 plank6 released: 4 planks in frame 1 (first of the x -745 column), 2 in the jig, upright.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig.
- 06 plank4 released: all 6 planks upright in frame 1, jig empty.
- 07 frame released: frame 1 + planks turned over, seated through the guide into frame 2 on base B; arm reaching over the -y edge as before.
- 08 end: bench assembled in base B (planks vertical, guide on top), arm at home; base A and plank jig empty.
- topview: same paths as iter 08; the change is a re-orientation on the first PTP/descent, not visible in xy (the orange home->plank3 PTP curve unchanged in shape).

## Result
Expected -0.4..-0.6 s, got 108.8 -> 108.1 s (-0.7 s), 0 violations. Phase planks 83.9 -> 83.2 s, others unchanged;
joint travel 2792 -> 2900 deg (J1 swings further at the turned Point16; tie-break only). The reason held: the start
PTP was J5-limited and the turn fits in the descent Lines for free, with no elbow cap at mid reach (unlike L37).
Kept (better, clean, shots fine). Next: the same J6/J5 overlap may fit other PTPs whose limiting joint is a wrist joint.
