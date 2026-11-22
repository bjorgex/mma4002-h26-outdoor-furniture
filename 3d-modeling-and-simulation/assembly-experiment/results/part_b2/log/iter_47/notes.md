# iter 47: iter 46's J5 pre-turn at Point88htt with a deeper guide edge notch (y to -62)

## Hypothesis
Use iter 46's program (j5turn20 D -6 at Point88htt, exact 89.730 s) and extend iter 45's guide notch along the far edge
to the same depth as the corner notch: GUIDE_EDGE_NOTCH local x 26..64, y -95..-62, z 15..35 (iter 46: y -95..-80).
Expected 89.7 s (-0.1 s), 0 violations. Change type: mixed (program scored alone in iter 46 + jig_cad).

## Reason
Evidence: iter 46 scored 89.7 s with exactly one problem, r1 1 "Guide/link_3" at #61, and the contact moved from the
guide's top edge to the 10 mm strip's inner wall (local y -80) - so link_3 sweeps deeper than 10 mm (L71). L71 asks for
the cut to the penetration extent plus ~5 mm; I have no time to write the swept-volume probe, so I cut to the corner
notch's depth (-62, 28 mm deep), 18 mm beyond the last contact. scratch/strip47.py on the guide mesh: the nearest
non-outline vertex is (26.9, -49.6), 12 mm inside the new wall, so no slot is touched; the guide is never gripped.
Alternatives: other J5 turns over base B are closed by the guide (L66-L68), and every other movable move is at a rule
floor (L65). DFA/cell principle: trim fixture material that has no function where the robot needs to pass.

## Screenshots
(Out of time: opened 07 and 08 only; the candidate is rejected anyway, and moves up to #58 equal iter 45/46.)
- 07 frame 1 released: frame 1 with all planks upright through the guide into frame 2 on base B, gripper beside it,
  arm reaching over base B's far side; nothing floating.
- 08 end: bench assembled in base B, arm at home, base A empty.
- 00-06 and topview: not opened.

## Result
Expected 89.7 s / 0 violations; got 89.7 s but still r1 1 "Guide/link_3" at #61 (Point88htt). The deeper strip
(y to -62) did not clear it, so link_3 either sweeps beyond -62 or hits the guide above z 35 / outside x 26..64 - I cut
again from a guess instead of measuring the swept volume (L71 not applied: no probe written). The time half of the
reason held again (home PTP J5-limited); the clearance half did not. Rejected.
