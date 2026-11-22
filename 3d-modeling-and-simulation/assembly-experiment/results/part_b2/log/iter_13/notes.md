# iter 13: group-2 plank transfers as single Lines (re-test of iter 04's merge after the iter-12 layout)

## Hypothesis
Change type: program. The four remaining "fast up 52.5 + PTP (+ via) + fast down 52.5" transfers of planks 5/4
(return plank6 -> plank5 pick, plank5 carry, return plank5 -> plank4 pick, plank4 carry) become one straight Line
from one slow-leg top to the next (toolbox/drop_move.py, steps 42 43 49 50 55 56 62 63 64). Expected: each transfer
~156-169 mm at 100 mm/s = 1.56-1.69 s instead of 1.72-1.76 s: about -0.4 s in total (105.5 -> ~105.1), 0 violations.
Risk: r1/r5 of the carried plank's lower end along the straight path (plank4 runs at y ~104 beside the placed y-124
row, L41) and line followability; I keep only the transfers that gain (L33).

## Reason
Evidence: toolbox/move_times2.py on the iter-12 best: the group-2 transfers still cost 0.52 + 0.68-0.72 + 0.52 =
1.72-1.76 s (plank4 carry 0.52 + 0.33 + 0.35 + 0.52), while after iter 12's column jig their straight distances are
only 156-169 mm - below L33's break-even (~(1.04 s + PTP s) x 100 mm = ~174 mm). In iter 04 these four were slower
as Lines (200-230 mm then), so they were left as PTPs; the layout change made the old decision stale.
Alternatives: removing fixed-cost events (slow legs, waits: ~78 s of the cycle) needs a different gripper / product
start and is not open; the J5 round trip of the flip / home is at its floor (L28, L34, iter 11 rejected); the
remaining non-fixed time is in these transfers. Cheap, program-only, one cause.
Principle: shortest route (straight path, fewer moves).

## Screening (2 mm)
- p13a (all four merged, drop steps 42 43 49 50 55 56 62 63 64): 105.1 s, 0 violations. Per transfer
  (move_times2): return->plank5 1.69 vs 1.76, plank5 carry 1.61 vs 1.74, return->plank4 1.64 vs 1.72, plank4 carry
  1.56 vs 1.72 - all four gain, so all kept. The plank4 straight carry needs no via point (L41's bulge was a PTP effect).

## Screenshots
- 00 start: column plank jig beside base A with 6 upright planks, frame 1 + pieces in base A, guide on base B; arm home.
- 01 plank3, 02 plank1, 03 plank2 released: the y-124 row of frame 1 fills robot-side-last, planks upright, gripper
  above; jig column empties from the plank3 slot outward. Same as iter 12 (group 1 unchanged).
- 04 plank6, 05 plank5, 06 plank4 released: the x -743 row fills y 44 -> 74 -> 104, all upright, none crooked or in
  another part; arm in a normal elbow-up pose over base A; jig empty after 06.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, arm at the release pose as before.
- 08 end: bench assembled in base B, arm at home, base A and jig empty.
- topview: the group-2 transfers are now straight solid lines in x at y 44 / 74 / 104 (no dashed PTP arcs or via
  bend); group 1 and the frame/home paths unchanged.

## Result
Expected ~-0.4 s, 0 violations; got 105.1 s (-0.4 s), 0 violations, joints 2956 -> 2817 deg. Phases: planks
81.0 -> 80.6 s, frame 18.0 / home 6.5 unchanged. The reason held: after iter 12 these transfers were below the
L33 break-even. Kept.
