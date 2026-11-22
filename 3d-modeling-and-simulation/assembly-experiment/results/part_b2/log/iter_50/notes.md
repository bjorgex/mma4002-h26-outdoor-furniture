# iter 50: J5 pre-turn D -5.2 at Point88htt with iter 48's guide edge notch

## Hypothesis
j5turn20 D -5.2 on Point88htt (step 75; J5 123.0 -> 118.1) plus iter 48's GUIDE_EDGE_NOTCH. exact27 phase sum
67.352 + 16.751 + 5.642 = 89.745 s -> 89.7 s (-0.1 s) if clean. But elbow43 (run before this note, as L74 asks) gives
min 0.0 mm link_3 vs Guide on #61 samples 10-24, so I expect r1 >= 1 and a reject. Change type: mixed (program + jig_cad).

## Reason
Evidence: L74 asked to measure the clearance at the rounding window's edge before scoring. exact27 puts that edge at
D ~ -5.2 (89.745 s, the last value that rounds to 89.7); elbow43 on it shows 0.0 mm through the middle of the Line #61
(start 17.2, end 1.2 mm). So the window and the clean range do not overlap: this iteration documents that the base-B
J5 turn at Point88htt is closed with the current guide slots. Alternatives: other moves are at rule floors (L65); with
~7 min of budget left there is no time for a geometry change (moving the slot at y -49.6 would move the plank positions
in frame 2 = the product). Scored only because decide needs a score (L64). DFA/cell principle: none new.

## Screenshots
(Budget nearly used up; candidate rejected on a measured collision.)
- 08 end: bench assembled in base B (planks upright through the guide into frame 2), base A empty, arm in the end
  pose over the plate's far side. Nothing floating or crooked.
- 00-07, topview: not opened (moves up to #60 identical to iter 49 / best; rejected).

## Result
Expected 89.7 s with r1 >= 1 (from elbow43); got exactly that: 89.7 s, r1 1 "Guide/link_3" at #61, joints 2289.
The reason held: the clearance probe predicted the hit correctly before scoring. The Point88htt J5 turn is closed:
the rounding window (D <= -5.2) and the clean range (D >= ~-5) do not overlap with the guide slot at y -49.6. Rejected.
