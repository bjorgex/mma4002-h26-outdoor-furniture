# iter 18: hide more of the start J5 turn in the first slow approach segment (Point26s)

## Hypothesis
Change type: program. The start PTP Point1 -> P16s0 (#2, 0.92 s) is J5-limited (45.8 deg; J4 18.1 next). The fast
Line #3 Point26 already turns 32.5 deg (capacity ~36), but the slow segment #4 Point26s (10.5 mm at 20 mm/s, 0.53 s)
turns nothing, though it could turn ~26 deg for free while the fingers are still >= 25 mm over plank6's top. Leave
Point26 partly tilted (turn_toward Point26 -> P16s0 by g1) so Point26s finishes the turn, and turn P16s0 further toward
home (g2) so Line #3 again uses its budget. Expected: start PTP J5 ~46 -> ~25 deg, ~-0.4 s (94.0 -> ~93.6 s),
0 violations. Risk: the tilted gripper/camera vs the neighbouring plank5 in jig 2 (30 mm in y) during Point26s (r1/r5);
J1/J4 take over the PTP limit (L38).

## Reason
Evidence: toolbox/move_times2.py on the iter-17 best: #2 P16s0 0.92 s "J5" 45.8 deg, #4 Point26s 0.53 s rot 0.0
(26 deg of unused rotation budget), #3 Point26 0.72 s rot 32.5 (near its 36 deg budget). Iter 09 used exactly this
overlap (Point17 g 0.28 turned in the slow segment) when the first pick was plank3; iter 16's reorder put the start at
plank6 and the slow-segment turn was not carried over (Point26s rot 0.0). Alternatives: the home trip end (J5 2.75 s)
is elbow-capped at the release pose (L37/L45); the frame flip J5 is capped the same way (iter 17); plank slow legs and
waits are fixed (~66 s). Home is on the joint path (iter 16), so the only lever on the home trip's J5 total is how much
of it Lines that are paid anyway absorb - this is the cheapest untried one.
Principle: overlap wrist travel with moves that must be paid anyway (rule-limited slow legs).

## Screening (2 mm, --no-shots; turn_toward.py Point26 (3) -> P16s0 (2) g1, then P16s0 (2) -> Point1 (1) g2)
- g1 0.75 / g2 0.3 (s18b): move_times2 start PTP 0.67 s, Line #3 rot only 21.3 (budget left) - not screened.
- g1 0.75 / g2 0.45 (s18d): 93.7 s, 0 violations (PTP 0.55 s J5 27.4).
- g1 0.75 / g2 0.55 (s18c): 93.6 s, 0 violations (PTP 0.47 s J5 23.6, J4 19.9 next; Line #3 rot 32.9, Point26s
  rot 24.4 of 26). Scored s18c. Going further would gain < 0.1 s (J4 floor).

## Screenshots
- 00 start: layout unchanged; arm at home with the gripper beyond the plate's far edge; planks 1-3 in base A slots,
  4-6 upright in jig 2; guide on base B. Nothing floating.
- 01 plank6 released: upright in the far column, gripper vertical above it; planks 5/4 still in jig 2.
- 02 plank5 released: far column 2 of 3, upright; jig 2 holds plank4.
- 03 plank4 released: far column full, jig 2 empty; planks 1-3 still in base A slots.
- 04 / 05 / 06 plank3 / 1 / 2 released: y-124 row fills outer to robot-side, all upright; base A slots empty after 06;
  arm elbow-up, normal pose.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, planks vertical, arm at the
  release pose reaching over the -y edge as in iter 17.
- 08 end: bench assembled in base B, arm back at home.
- topview: same paths as iter 17 (the change is orientation-only on the start descent to plank6).

## Result
Expected ~-0.4 s, 0 violations; got 93.6 s (-0.4 s from 94.0), 0 violations, joints 2224 -> 2257 deg. Phases: planks
69.8 -> 69.4 (the start PTP 0.92 -> 0.47 s), frame 17.9 and home 6.4 unchanged. The reason held: the slow segment
Point26s took 24.4 deg of the turn for free (fingers still 25 mm over plank6's top, no contact), and J4 now nearly
co-limits the start PTP as L38 predicted. Kept.
