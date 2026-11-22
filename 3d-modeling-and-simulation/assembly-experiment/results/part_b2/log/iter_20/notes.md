# iter 20: more pre-turn in the fast frame-lift Line (Point80Lt) before the J5-limited flip

## Hypothesis
Change type: program. The fast Line #53 Point80ut -> Point80Lt (57.4 mm, 0.57 s) turns the tool only 19.7 deg of
its 28.7 deg budget (rot/50 <= dist/100). Turn Point80Lt further toward Pvia (toolbox/turn_toward.py 66 67 g) so the
Line uses ~27 deg, and lower the J5 delta of the J5-limited PTP #54 Pvia (33.2 deg, 0.66 s). Pvia's other joint deltas
(J3 29.8, J6 28.9, J1 23.9) are close behind, so rebalance Pvia's J3/J6/J1 (scratch/set_joints.py) so J5 limits both
halves again. Expected -0.1..-0.18 s (93.4 -> ~93.25 s), 0 violations; risk: the turned frame (still near base A's
pocket and the plank tops) clips base A (r1/r4), or J4/J6 take the rotation instead of J5 (L39). Screen at 2 mm.

## Reason
Evidence: toolbox/move_times2.py on the iter-19 best: the frame flip #54 Pvia (0.66 s, J5 33.2) + #55 Point85t
(2.44 s, J5 122.1) = 3.1 s is the largest movable block left, J5-limited; #53 has 9 deg of unused rotation budget and
#56 Point86 6.7 deg, but #56's side is capped by the elbow over the guide (L37/L45, iter 17). The start/home J5 is
already hidden in slow legs (iter 09/18) or elbow-capped (iter 08); the plank phase is ~90 % fixed (slow legs, waits).
Alternatives: bolder fixed-cost cuts (two planks per grip, a new jig) do not fit in the ~80 min left; Point80h /
Point85t / Point88ht are at their r4 limits (iter 19 notes, L13). Principle: overlap motion with already-paid moves
(re-orient inside a Line whose time is set by its distance).

## Screening (2 mm, --no-shots)
- turn_toward.py 66 67 g 0.15 / 0.25 / 0.35 (slerp toward Pvia): J5 only -33.2 -> -29.5 while J6 ran -16.9 -> -34.6
  (away from Pvia's 12): useless (L39 again, see L48). Not screened.
- New scratch/j5turn20.py: give Point80Lt the orientation a J5 +D turn would give, TCP held, IK. J5 follows ~0.85 D,
  J3 folds (-49.8 -> -63), so Pvia's J3/J6/J1 were rebalanced (scratch/set_joints.py) to keep J5 the limit:
  - a D 6, Pvia J3 -32 J6 8: Line rot 23.6, Pvia 0.56 s (J5): 93.3 s, 0 violations.
  - b D 9, Pvia J3 -35 J6 6 J1 -21: rot 25.8, Pvia 0.52 s (J3): 93.2 s, 0.
  - c D 11, Pvia J3 -39.5 J6 5 J1 -22: rot 27.4 (budget 28.7), Pvia 0.48 s (J5 23.9): 93.2 s, 0 -> scored.

## Screenshots
- 00 start: same layout; arm at home over the far edge, planks 1-3 in base A slots, 4-6 in jig 2, guide on base B.
- 01 / 02 / 03 plank6 / 5 / 4 released: the far column fills, planks upright in frame 1, jig 2 empties; gripper
  vertical above the released plank, nothing floating.
- 04 / 05 / 06 plank3 / 1 / 2 released: the y-124 row fills outer to robot side, all upright; base A slots empty.
- 07 frame 1 + planks released: flipped and seated through the guide into frame 2 on base B, planks vertical, arm at
  the usual release pose over the -y edge.
- 08 end: bench assembled in base B, guide on top, arm back at home.
- topview: paths as in iter 19; the flip PTP (dashed purple from the frame foot at (-732, 196)) now leaves over the far
  edge at a lower via point (TCP z 447 instead of 616), invisible in xy except a slightly different arc.

## Result
Expected -0.1..-0.18 s; got 93.4 -> 93.2 s (-0.18 s by move_times: Pvia 0.66 -> 0.48 s), 0 violations, joints
2257 -> 2267 deg. Phases: frame 17.6 -> 17.4, planks / home unchanged. The reason held: #53 had unused rotation budget
and the J5-limited via PTP absorbed it - but only with a J5-axis turn (slerp toward Pvia moved J6), and only after
rebalancing Pvia's J3/J6/J1, which lowered the via point 170 mm without any r1/r4 hit. Kept.
