# iter 48: iter 46's J5 pre-turn with a guide edge notch sized from a swept-volume probe

## Hypothesis
iter 46/47 program (j5turn20 D -6 at Point88htt, exact 89.730 s) + GUIDE_EDGE_NOTCH widened to guide-local x -17..64,
y -95..-53, z 15..40 (iter 47: x 26..64, y -95..-62, z 15..35). Expected 89.7 s (-0.1 s), 0 violations if the cut
covers link_3's sweep. Change type: mixed (program scored in iter 46 + jig_cad).

## Reason
Evidence: L72 asked for a swept-volume probe before another cut. scratch/sweep48.py (link_3/4 vertices inside the
guide's local box over all 2 mm samples of #61) gives x -11.8..57.4, y -90..-46.7, z 20..34.2 - the iter-47 cut missed
the whole x < 26 part, which explains why the contact stayed. The cut cannot reach y -46.7: a slot corner sits at
(26.9, -49.6) (scratch/strip47.py), so y -53 is the deepest that keeps a >= 3 mm wall. The probe is a bounding box of
link vertices inside the guide's bounding box, so the real penetration is likely smaller than y -46.7 - the cut to -53
may suffice. Alternatives: the other program moves are at rule floors (L65); this is the only open -0.1 s.
DFA/cell principle: trim fixture material that has no function where the robot passes.

## Screenshots
(Out of time: opened 07, 08 and topview; moves up to #58 are identical to iter 46/47, and the candidate is rejected.)
- 07 frame 1 released: frame 1 with all planks upright through the guide into frame 2 on base B; the gripper sits beside
  it, the arm reaches over base B's far side. Nothing floating.
- 08 end: bench assembled in base B, arm back at home, base A empty, guide still on base B.
- topview: same layout as best; the plank zig-zag over base A and the frame route, nothing new.
- 00-06: not opened.

## Result
Expected 89.7 s / 0 violations; got 89.7 s with r1 1 "Guide/link_3" at #61 again. The probe was right that the
iter-47 cut missed x < 26, but the slot at y -49.6 caps the cut at y -53, and link_3 still reaches the guide in the
remaining strip (y -53..-46.7) or below z 15 local. The evidence half of the reason held (the sweep is wider than the
old cut); the hope that the bbox overstated the depth did not. Rejected. The base-B J5 turn needs either a smaller turn
(D ~ -3, sized with elbow43) or a guide with that slot moved; a cut alone cannot clear it.
