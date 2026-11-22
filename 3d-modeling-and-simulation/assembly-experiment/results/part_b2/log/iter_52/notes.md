# iter 52: no change - re-score the best (budget end, no live idea)

## Hypothesis
No design change. Re-score iter 45's best as it is to confirm it at 2 mm before the run ends. Expected delta: 0.0 s,
0 violations, "NOT better" -> reject. Change type: program (none made).

## Reason
Evidence: status shows 9 min of budget left and a no-keep streak of 6. toolbox/move_times2.py on the best (89.8 s): 70 s
is slow legs (28 x 2.5 s) and 7 s gripper waits; every movable move is at a floor already measured: Point80h (base A box,
L59), Point70yttt / Point86 rot-limited by 0.01 s (L69), Point88htt / Point85tt J5 turns blocked by link_3 vs the guide
slot (L66-L76), start PTP by link_6 over plank4 (L54/L60). The only gains left need a fixed-cost event removed (a new
plank jig / grip strategy), which does not fit in 9 min. L75/L76: don't spend the last minutes on a probe-killed idea;
write the summary instead. The runner still needs a decided iteration, so this one is a plain re-score, rejected.
DFA principle: none (no change).

## Screenshots
- 00 start: planks 1-6 stand in the base A slots, frame 1 is in base A, frame 2 + pieces + guide are on base B (riser), the arm is at home. Nothing floats.
- 01 plank6 released: placed upright in frame 1's far column, the gripper is above it, the other planks are still in the slots.
- 02 plank5 released: two planks in the far column, upright, the arm is over base A.
- 03 plank4 released: the far column is full, the gripper is lifting.
- 04 plank3 released: the first plank of the y-124 row is upright, nothing tilted.
- 05 plank1 released: two planks in the y-124 row, the slots are emptying in order.
- 06 plank2 released: all six planks stand in frame 1, upright, aligned.
- 07 frame 1 released: frame 1 + planks flipped and inside the guide/frame 2 on base B, the arm is at the far reach on the -y side, no part crooked.
- 08 end: the bench is assembled on base B, base A is empty, the arm is back at home.
- topview: the same TCP path as iter 45 (pick/place zig-zag over base A, PTP arcs to home and to base B).

## Result
Expected 0.0 s / 0 violations, got 89.8 s, 0 violations, 2285 deg, identical to iter 45, so the best is confirmed at 2 mm.
The verdict is "NOT better", as expected, so I rejected it. The reason held: no change was made, so there is no delta to
explain. log/summary.md was written in this session (L76: write the summary when under ~15 min is left).
