# iter 42: iter 41's J5 pre-turn at Point85tt, with the flip end shifted sideways to clear the elbow off the guide

## Hypothesis
Change type: program. Same J5 pre-turn as iter 41 (j5turn20 idx 69, D -6.5: J5 122.1 -> 116.6, exact 89.843 s), plus
Point85tt's flange shifted 4 mm radially toward the robot at the same z (toolbox/set_ptp_xyz.py --dx 3.77 --dy 1.34).
Point86 is rotation-limited at D -6.5, so the few mm extra Line distance is free (exact27: 89.8434 s -> 89.8). Expected
-0.1 s, 0 violations if the shift lifts link_3 clear of the guide.

## Reason
Evidence: iter 41 reached 89.8 s (-0.107 s, the only >= 0.1 s gain left after L65) but failed on r1 2 "Guide/link_3" at
#56/#57; L60 says a collision floor next to a time gain is paid back with a free coordinate, and here the PTP end's xy is
free: Point86 is rotation-limited after the turn, so a small sideways offset of Point85tt costs ~0.000-0.002 s (exact27).
Alternatives: a smaller turn (D -6: 89.847 s) also hit at 2 mm (screened this iter, r1 2); raising Point85tt 4 mm costs
+0.04 s (Point86 distance-limited again), too much. Screened shifts 4 / 8 mm inward and 4 / 8 mm outward: all r1 2 at
the same moves. Principle: overlap wrist travel with move time already paid.

## Screenshots
- 00 start: arm at home over base A, planks upright in base A / plank jig, frame 2 + guide on base B; nothing floating.
- 01-03 plank6/5/4 released upright into frame 1's far column, gripper vertical above; the jig empties in order.
- 04-06 plank3/1/2 released upright into the second row; all six planks are in frame 1 by 06.
- 07 frame 1 + planks flipped into frame 2 through the guide on base B. The arm is at the low release pose at base B's -y
  edge, with the elbow/forearm low beside the guide (that is where the r1 Guide/link_3 hits at #56/#57 are reported).
- 08 end: bench assembled in base B, arm back at home; nothing crooked.
- topview: same paths as iter 40/41 (the change is a 4 mm shift of one PTP end plus an orientation change).

## Result
Expected 89.843 s with 0 violations. Got 89.8 s but r1 2 ("Guide/link_3" at #56 Point85tt and #57 Point86), the same as
iter 41. The reason held for the time saving but not for the collision: none of the screened shifts of Point85tt
(inward 4/8 mm, outward 4/8 mm), nor the smaller turn D -6, removed the hit. So the contact does not come from where the
PTP end sits. It must come from the turned orientation along the Point86 descent and/or the PTP's joint path, and the end
pose stays the same. Rejected. A real fix needs a link_3-vs-guide distance probe along #56/#57, or a guide jig_cad change
(L66).
