# iter 03: move the plank jig 40 mm closer to base A (ground x 250 -> 290) to shorten the J3-limited plank PTPs

## Hypothesis
Change type: layout (+ the pick moves shifted with the jig, toolbox/shift_moves.py, robot dx -40). PLANK_JIG ground
x 250 -> 290; all 30 pick moves (Point16/17/17s/18/19, 34/35/35s/36/37, 52/53/53s/54/55, 25/26/26s/27/28,
43/44/44s/45/46, 61/62/62s/63/64) shifted by robot dx -40. Expected: -0.8 s (the 11 J3-limited plank PTPs, 0.74-1.03 s,
each lose ~0.05-0.1 s), 0 violations. Risk: r4/r1 with the home PTP (home sits on the old joint path to Point16,
L25), jig vs base A riser (gap ~55 mm in the top view), carried plank vs base A edge.

## Reason
Evidence: toolbox/move_times2.py on the iter-02 best: 11 of the 12 plank-phase PTPs are J3-limited (0.74-1.03 s,
~10.5 s in total); they swing between the pick row at robot x -471..-531 and the base A places at x -653..-748, i.e.
a reach change that J3 (elbow) pays for. The rest of the plank phase is fixed cost (slow legs, waits) or already
minimal fast legs (52.5 mm r4 escapes). L26 showed the same shift (run B iter 26, +100 mm) cut the J3-limited PTPs;
the top view shows ~55 mm still free between the jig and base A.
Alternatives: (a) pre-rotate Line #36 (iter-02 trick again): <= 0.2 s; (b) put the jig beside base A at +y (lateral
J1 swing instead of J3): bigger gain but collides with the frame-foot grip at y 196 and needs a new program;
(c) slow legs/waits are fixed. (b) is the bolder follow-up if this confirms the J3 model; this is the cheap test.
Principle: place the most-visited fixtures close together (shortest route between pick and place).

## Screening (before the score)
- ground x 290 (robot dx -40, scratch/k03a.json), 2 mm: 112.1 s, 0 violations.
- ground x 300 (dx -50, k03b): 111.8 s, 0 violations, BUT scratch/cell_bounds.py shows the jig at robot x -596.4 vs
  the base A riser at -596.3: the two fixtures touch/overlap by 0.1 mm, which the judge does not check (L32). Dropped.
- ground x 295 (dx -45, k03c): 112.0 s, 0 violations, jig edge -591.4 -> 4.9 mm gap to base A. Scored this one.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig, now right next to base A with a small gap; arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, 5 planks in the jig; gripper raised over base A.
- 02 plank1 released: two planks upright side by side in frame 1; 4 in the jig; arm in a normal elbow-up pose.
- 03 plank2 released: y-124 row of frame 1 full (3 planks, upright); the 3 turned planks in the jig.
- 04 plank6 released: 4 planks in frame 1, upright; 2 left in the jig.
- 05 plank5 released: 5 planks in frame 1; plank4 alone in the jig, upright.
- 06 plank4 released: all 6 planks in frame 1, jig empty, nothing crooked.
- 07 frame released: frame 1 + planks turned over and seated through the guide into frame 2 on base B, planks vertical; arm reaching over the -y edge as before.
- 08 end: bench assembled in base B, arm back at home; base A and plank jig empty.
- topview: plank jig now at robot x -501..-591, abutting base A (gap ~5 mm); pick-to-place PTPs (dashed) visibly shorter; frame and home paths unchanged.

## Result
Expected -0.8 s, got 113.2 -> 112.0 s (-1.2 s), 0 violations. Phase planks 87.1 -> 85.8 s, the others unchanged;
joint travel 3485 -> 3326 deg. The reason held: the plank PTPs are J3-limited by the pick-place reach difference,
and shrinking it by 45 mm cut them more than estimated. The layout is now at the limit for this direction (the jig
abuts base A); further gains on these PTPs need the jig placed differently (beside base A, lateral swing). Kept.
