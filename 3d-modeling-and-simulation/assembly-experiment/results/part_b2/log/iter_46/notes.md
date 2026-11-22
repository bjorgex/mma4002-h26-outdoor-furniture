# iter 46: J5 pre-turn of 6 deg at the high lift end Point88htt (freed by iter 45's guide notch)

## Hypothesis
j5turn20 D -6 on Point88htt (step 75; J5 123.0 -> 117.4). The J5-limited home PTP (110 deg, 2.20 s) gets ~5.6 deg
shorter; the Line #61 (53.5 mm, rot 15.4 -> ~21) stays distance-limited. exact27: 89.843 -> 89.730 s -> 89.7 s (-0.1 s),
0 violations expected. Change type: program.

## Reason
Evidence: exact27 shows the home leg is J5-limited (move_times2 #62: dJ 110.1 J5, 2.20 s) and the Line before it (#61,
53.5 mm, 0.53 s) has spare rotation (15.4 of ~26 deg). L51/L56 said a J5 turn at Point88ht put link_3 into the guide -
but iter 45 found that contact zone was the guide's unused outer corner and notched it, so the old floor may be gone.
Alternatives: a further turn at the flip end Point85tt (k46a/b) raises time because Point86 is rotation-limited; lowering
Point88htt is pinned by r4 (103.5 mm from the release point). With ~15 min left, this is the only >= 0.1 s candidate.
Principle: hide joint motion inside moves that are already paid for (re-orient during a distance-limited Line).
Added mid-iteration (mixed): the first screen hit Guide/link_3 at #61 on the guide's far top edge (world -721.5/-190.3,
~35 mm from the iter-45 notch), so I added a 10 mm edge strip notch GUIDE_EDGE_NOTCH (local x 26..64, y -95..-80, z 15..35).

## Screenshots
(Out of time: I opened only 07 and 08. The candidate is rejected anyway.)
- 07 frame 1 released: frame 1 + planks upright through the guide into frame 2 on base B, arm over base B's far side.
- 08 end: bench assembled in base B, arm at home, base A empty; nothing floating.
- 00-06 and topview: not opened (the program up to move #58 is the same as iter 45).

## Result
Expected 89.7 s / 0 violations; got 89.7 s (exact 89.730) but r1 1 "Guide/link_3" at #61, even with the edge strip. The
contact moved to the strip's inner wall (world y -180.3 = local y -80): link_3 sweeps more than 10 mm into the guide
edge. The time half of the reason held (home PTP J5-limited, Line #61 has spare rotation); the clearance half did not:
iter 45's notch does not cover the lift path. A wider strip (y to about -65), checked for slots first, might make it legal.
Rejected.
