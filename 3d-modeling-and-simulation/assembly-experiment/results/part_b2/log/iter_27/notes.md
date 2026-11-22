# iter 27: lower the post-release lift end Point88ht to ~105 mm over the frame release point

## Hypothesis
Change type: program. #61 Point88ht is a 59.5 mm fast Line (rot 15.4 deg = 0.31 s budget), distance-limited at 0.59 s;
it ends at TCP z 458, 110 mm straight above the frame release point Point87 (348). Only r4 (the home PTP must start
>= 100 mm from every grip/release point) binds its height. Lowering it by 3-5 mm (TCP z 455 / 453) shortens the Line
to ~56.5 / 54.5 mm: about -0.03 / -0.05 s (91.0 -> ~90.95 s), 0 violations; the J5-limited home PTP (110 deg) should be
unchanged. Risk: r4 near-point at the PTP start (L43: keep ~5-10 mm slack, screen at 2 mm); elbow over the guide (L51)
is unlikely for a pure 3-5 mm TCP drop at fixed orientation.

## Reason
Evidence: toolbox/move_times2.py on the iter-26 best: of the remaining movable moves, #61 Point88ht 0.59 s is distance-
limited with 0.28 s of unused rotation budget, and its 110 mm height over the release point has 10 mm more than r4 needs
(L30: end over-long fast Lines at ~105 mm from the nearest grip point). Everything else in the cycle is fixed slow legs
and waits, or balanced J-limited PTPs (frame approach J2 = J4, iter 23; flip/home J5 capped by the elbow, L37/L45/L51).
Alternatives: the shallower base A pocket that would allow a J5 pre-turn in the frame lift (L49, ~0.4 s) is a jig CAD
change with r6/rest risks that does not fit the ~50 min left; Point80Lt (106.8 mm from the grip) and Point85t (103 mm)
are already at the r4 limit.
Principle: shortest route - remove the last slack above a rule limit; small, program-only, low risk.

## Hypothesis amendment (after the first score)
The first score (Point88ht z 453 alone, scratch/m27a.json) gave the expected -0.05 s (exact 91.040 -> 90.990 s) but the
judge stores cycle_s rounded to 0.1 s, so both read 91.0 and joints 2316 > 2315 -> "NOT better" (L55). Same idea
applied to the other two r4-bound lift/approach ends of the frame phase, each screened at 2 mm: Point80Lt TCP -3 mm
(106.8 -> ~104 mm from the frame grip point; rot-limited 0.55 s floor) and Point85t TCP -2 mm (103 -> 101 mm over the
release point; Point86 52.5 -> 50.5 mm). Point88ht at z 450 hit Guide/link_3 (L51 again), so 453 stays. Expected
exact 90.944 s -> 90.9 s, 0 violations.

## Change
- toolbox/turn_toward.py (g 0, TCP shift only): idx 75 Point88ht dz -5 (m27a), idx 67 Point80Lt dz -3, idx 69 Point85t
  dz -2 -> scratch/n27d.json (copied to design/program.json). Side screens: n27b (Point88ht dz -8 + Point80Lt -3): r1 1
  Guide/link_3 at #61; n27c (dz -5 + Point80Lt -3): 0 violations, 90.964 s (still 91.0).

## Screenshots
- 00 start: layout unchanged; six planks upright in base A's slots, frame 1 in base A, guide on base B, arm at home.
- 01 plank6 released upright in the far column, gripper straight above it; planks 4/5 in their slots.
- 02 plank5 released beside plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, base A wall slots empty.
- 04 plank3 released in the outer y-124 row, upright, gripper above it.
- 05 plank1 released next to it, upright.
- 06 plank2 released; all six planks upright in frame 1.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical; arm at the usual
  release pose over the -y edge, elbow well clear of the guide.
- 08 end: bench assembled in base B, arm at home; base A empty; nothing floating, crooked or interpenetrating.
- topview: same paths as iter 26; the changes are 2-5 mm in z and not visible in the top view.

## Result
Expected (first version) -0.05 s; got exactly that (91.040 -> 90.990 s) but it rounded to 91.0 with joints +1 deg ->
"NOT better" (L55). Amended version (three r4-bound lift/approach ends tightened): expected exact 90.944 s, got 90.9 s
(frame phase 17.28 -> 17.24, home 5.82 -> 5.77), 0 violations, joints 2316 deg. The reason held: each of the three
ends had only r4 slack above it; the floor at Point88ht is the elbow over the guide (z 450 hit Guide/link_3, L51), not
r4. Point85t now sits ~101 mm over the release point, scored clean at 2 mm. Kept. The program-level slack is now gone;
further gains need a fixed-cost change (jig CAD: shallower base A pocket, L49).
