# iter 51: J5 pre-turn D -3 at Point88htt (no guide notch)

## Hypothesis
scratch/j5turn20.py step 75 D -3 (J5 123.0 -> 120.2). exact27: home 5.740 -> 5.683 s, total 89.787 s -> still 89.8 s
(tie). elbow43 (run first, L75) gives min 0.0 mm link_3 vs Guide on #61, so I expect r1 >= 1 and a reject.
Change type: program.

## Reason
Evidence: iters 46-50 closed the D <= -5 turn; nobody had probed the smaller, notch-free turns that iter 49 called "clean".
elbow43 on D -3 shows 0.0 mm on #61 samples 11-20 without the notch, so even small turns hit the guide's top edge
without iter 48's cut, and the cycle gain (-0.057 s) does not cross a rounding step. Alternatives: no other movable move
has slack (L65); ~7 min of budget is left, too little for a geometry change. Scored only because decide needs a score
(L64/L75). DFA/cell principle: none new.

## Screenshots
(Budget used up; candidate rejected on a measured collision before scoring.) Moves up to #60 are identical to the best.

## Result
Expected 89.8 s tie with r1 >= 1; got 89.8 s, joints 2288 (+3), r1 1 "Guide/link_3" at #61. The reason held: elbow43
predicted the hit. Any J5 turn at Point88htt hits the guide edge without a cut, and with the cut the slot caps it
(iter 48). Rejected.
