# iter 49: smaller J5 pre-turn (D -5.5) at Point88htt with iter 48's guide edge notch

## Hypothesis
j5turn20 D -5.5 on Point88htt (step 75; J5 123.0 -> 117.8) instead of iter 46-48's D -6, plus iter 48's
GUIDE_EDGE_NOTCH (guide-local x -17..64, y -95..-53, z 15..40). exact27: 89.740 s (best 89.843) -> 89.7 s (-0.1 s),
0 violations if the 0.5 deg smaller turn gives link_3 the last ~0.7 mm. Change type: mixed (program + jig_cad).

## Reason
Evidence: iter 48 scored 89.7 s with exactly one problem, r1 1 "Guide/link_3" at #61, after a cut capped at y -53 by a
slot; L73 says size the program change instead. exact27 sweep: D -3 89.783, D -4 89.768 (both round to 89.8 = no gain),
D -5.5 89.740 (rounds 89.7 with 0.01 s margin), D -6 89.730 (hits). L68 measured ~1.3 mm clearance per deg of turn, so
D -5.5 buys ~0.7 mm over D -6 - the only remaining variant that both rounds down and is less deep. Alternatives: smaller
D gives no rounded gain; other moves are at rule floors (L65). DFA/cell principle: trim fixture material without a job
where the arm passes, and turn the wrist during a paid Line.

## Screenshots
(Out of time: opened 07 and 08; moves up to #60 are identical to iter 48, and the candidate is rejected.)
- 07 frame 1 released: frame 1 with all planks upright through the guide into frame 2 on base B; the gripper is beside
  it, the arm reaches over base B's far side. Nothing floating.
- 08 end: bench assembled in base B, arm back at home, base A empty, guide still on base B.
- 00-06, topview: not opened (same as iter 48).

## Result
Expected 89.7 s / 0 violations; got 89.7 s with r1 1 "Guide/link_3" at #61 again (joints 2289). The 0.5 deg smaller turn
(~0.7 mm by L68) was not enough. The reason held for the time (exact27 89.740 -> 89.7) but not for the clearance:
with the notch capped at y -53, the base-B J5 turn needs D >= ~-5 to be clean, and those round to 89.8. Rejected.
This line is closed unless the guide slot near y -49.6 moves.
