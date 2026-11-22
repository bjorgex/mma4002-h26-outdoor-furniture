# iter 04: plank transfers as one straight Line between slow-leg tops (drop fast lift + PTP + fast descent)

## Hypothesis
Change type: program. Between two plank events (pick -> place and place -> next pick) the program does: slow leg up
(50.5 mm) -> fast Line up 52.5 mm (r4 escape) -> PTP -> fast Line down 52.5 mm -> slow leg down. Replace the fast
up + PTP + fast down by ONE fast Line from the top of one slow leg to the top of the next (toolbox/drop_move.py drops
the fast-up Line and the PTP; the fast-down Line then starts at the slow-leg top). No PTP = no r4 at all there; the
Line starts/ends at TCP z 296-316, so it reaches >= 311 (low-traverse rule) on every transfer. Expected: carry
pick -> place ~147-210 mm at 100 mm/s (1.5-2.1 s) instead of 0.52 + PTP 0.6-0.9 + 0.52 = 1.7-1.9 s: -0.1 to -0.3 s per
transfer, ~-1.5 s in total, 0 violations. Risk: r5 (>= 10 mm clearance in fast moves) / r1 - the carried plank's
lower end at TCP 296 is ~60 mm above the plate and sweeps over the plank jig walls / base A riser / frame 1; the
empty gripper passes 35 mm over the placed plank tops. Line followability (r2) on long Lines.

## Reason
Evidence: toolbox/move_times2.py on the iter-03 best: each transfer between two plank events costs
fast-up 0.52 + PTP 0.62-0.91 + fast-down 0.52 s = 1.66-1.95 s, 11 transfers ~20 s. The fast 52.5 mm legs exist only
because a PTP must end >= 100 mm from a grip/release point (r4); a Line has no such rule, and the straight distance
between the two slow-leg tops is only ~150-210 mm (1.5-2.1 s at 100 mm/s). Iter 03 noted the jig now abuts base A,
so the pick-place distance is short enough for a straight Line to beat the detour up-and-over.
Alternatives: (a) pre-rotate Line #36 (iter-02 follow-up, <= 0.2 s); (b) plank jig beside base A (bigger layout
change, frame-foot grip conflict); (c) fewer grip events (two planks per grip: needs a new jig + gripper stroke
check, too large for one iteration). This one removes 2 moves per transfer and the r4 constraint that forced them;
it is a program-only change and quick to screen per transfer.
Principle: shortest route (straight path instead of up-over-down), fewer moves.

## Screening (before the score)
- All 11 transfers merged (scratch/m04all.json), 2 mm: 111.5 s, 0 violations. Carries only (m04c): 111.5 s; returns
  only (m04r): 112.0 s. Per transfer (move_times2): merged Line vs old up+PTP+down: plank3 carry 1.47 vs 1.73,
  return->plank1 1.76 vs 1.82, plank1 carry 1.47 vs 1.66, return->plank2 1.76 vs 1.74 (worse), plank2 carry 1.47 vs
  1.88, return->plank6 1.60 (80 deg rotation, rot-limited) vs 2.01, plank6 carry 1.73 vs 1.79; the long row-2
  transfers (return->plank5 2.03 vs 1.88, plank5 carry 2.00 vs 1.86, return->plank4 2.30 vs 1.95, plank4 carry 2.30
  vs 1.94) are slower: a 200-230 mm straight Line at 100 mm/s loses to a PTP.
- Selective (only the 6 that gain; scratch/m04s.json, drop steps 8 9 14 15 21 22 34 35 40 41 47 48): 110.5 s,
  0 violations. Scored this one.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig next to base A; arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, 5 planks in the jig; gripper above it after the slow lift.
- 02 plank1 released: two planks upright side by side in frame 1, 4 in the jig; arm elbow-up, normal pose.
- 03 plank2 released: y-124 row of frame 1 full (3 planks upright); the 3 turned planks in the jig.
- 04 plank6 released: 4 planks in frame 1, upright; 2 left in the jig, nothing tilted by the straight transfers.
- 05 plank5 released: 5 planks in frame 1; plank4 alone in the jig, upright.
- 06 plank4 released: all 6 planks in frame 1, jig empty, nothing crooked.
- 07 frame released: frame 1 + planks turned over and seated through the guide into frame 2 on base B, planks vertical; arm reaching over the -y edge as before.
- 08 end: bench assembled in base B, arm back at home; base A and the plank jig empty.
- topview: the first six transfers are now solid straight Lines between jig and base A (no dashed PTP detours); the row-2 transfers to plank5/plank4 keep their PTPs; frame and home paths unchanged.

## Result
Expected ~-1.5 s, got 112.0 -> 110.5 s (-1.5 s), 0 violations. Phase planks 85.8 -> 84.4 s, others unchanged; joint
travel 3326 -> 3029 deg, 84 -> 72 moves. The reason held for short transfers (<= ~175 mm straight): dropping the
r4-forced 52.5 mm legs and the PTP wins. It does not hold for the long row-2 transfers (200-230 mm): there a PTP
(~0.85 s) plus two 0.52 s legs beats a 2.0-2.3 s Line - the Line at 100 mm/s is the bottleneck, not the legs. The
carried plank 60-80 mm over the plate cleared jig, base A and frame 1 (r1/r5 0). Kept.
Next: for the long transfers, a hybrid: Line from the slow-leg top to a point ~100 mm from the event, PTP across,
then a Line down (only one r4 leg), or bring the row-2 places closer to the pick row.
