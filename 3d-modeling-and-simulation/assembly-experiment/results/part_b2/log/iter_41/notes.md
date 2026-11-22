# iter 41: pre-turn J5 at the flip PTP end Point85tt so the Point86 drop Line takes more of the turn

## Hypothesis
Change type: program. Turn Point85tt (end of the 122 deg J5-limited flip PTP, TCP z 449 over base B) by -6.5 deg about
the J5 axis (scratch/j5turn20.py idx 69): J5 122.1 -> 116.6, so the PTP is ~5.5 deg shorter (-0.11 s) and the 51 mm Line
Point86 (rot 19.5 of a 25.5 deg budget) absorbs the turn up to its distance limit. exact27: 89.9497 -> 89.843 s
(-> 89.8), 0 violations. Risk: link_3 / elbow vs the guide (L45/L51).

## Reason
Evidence: toolbox/move_times2.py on the iter-40 best: #56 Point85tt PTP 2.44 s J5-limited (122.1 deg), followed by #57
Point86 Line d 51.0 mm (0.51 s) turning only 19.5 deg, i.e. 6 deg of free rotation budget (L30/L36: free rotation in
distance-limited Lines). L65 says the next keep needs >= 0.1 s real time; this is the only distance-limited Line next
to a J5-limited PTP with that much budget left. Unlike iter 17 (turn_toward, mixes J4/J6, L48) this turns about J5
(j5turn20), and at Point85tt (z 449, above the release) J3 unfolds (-29.3 -> -27.3) so the elbow rises rather than
drops (L45 was the low release pose). Alternatives: the home-side J5 trip is exhausted (iter 08/17/23), the frame
approach is balanced (iter 23). Principle: overlap wrist travel with move time that is paid anyway.

## Screening (exact27, no collision screen)
- D -4: J5 118.7, 89.881 s; D -5.5: J5 117.4, 89.855 s (rounds 89.9); D -6.5: J5 116.6, 89.843 s (-> 89.8); D -7: 89.844
  (Point86 turns rotation-limited from ~-6.5). Only D <= -6 crosses the rounding step; scored D -6.5.

## Screenshots
- 00 start: arm at home, planks upright in base A / plank jig, frame 2 + guide on base B; nothing floating.
- 01-03 plank6/5/4 released upright in frame 1's far column, gripper vertical above; jig emptying in order.
- 04-06 plank3/1/2 released upright in the y-124 row; all six planks in frame 1 at 06, base A slots empty.
- 07 frame 1 + planks flipped into frame 2 through the guide on base B; arm at the release pose low over base B's -y edge
  (the elbow region is where the r1 Guide/link_3 hit is reported at #56/#57).
- 08 end: bench assembled in base B, arm at home; nothing crooked or out of place.
- topview: same paths as iter 40 (the change is an orientation only).

## Result
Expected 89.843 s (-0.107), 0 violations; got 89.8 s but r1 2: "Guide/link_3" at #56 (Point85tt) and #57 (Point86).
The reason held for the time (the Line had the rotation budget, cycle dropped as predicted) but not for the collision:
J3 unfolding at Point85tt did not keep the elbow clear - the turn moves J1/J2 too (L51), and Point86 then descends with
the elbow over the guide. The smaller turns that might be clean (D <= -5.5) round to 89.9 s, no gain. Rejected.
