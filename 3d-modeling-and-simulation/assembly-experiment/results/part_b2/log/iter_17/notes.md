# iter 17: end the frame flip short of its final tilt, finish the turn in the fast descent Line Point86

## Hypothesis
Change type: program. The flip PTP Pvia -> Point85 (#55, 2.76 s) is J5-limited (138 deg). The fast vertical Line
after it (#56 Point86, 52.5 mm, 0.53 s) turns nothing, but could turn ~26 deg for free (rot/50 deg/s <= 0.53 s).
Turn Point85 (TCP kept) back toward Pvia by a fraction g (toolbox/turn_toward.py step 68 -> 67), so the PTP needs
less J5 and Point86 does the rest of the turn while the frame + planks are still above the guide. Expected: ~-0.4 s
(J5 ~20 deg less = 0.4 s at 50 deg/s), 0 violations. Risk: the carried frame/planks swing about the TCP during the
descent, close to the guide slots on base B (r1); the Line becomes rotation-limited if g is too large.

## Reason
Evidence: toolbox/move_times2.py on the iter-16 best: #55 Point85 2.76 s "J5" 138.1 deg, the largest single
movable move left; the next move #56 is a 52.5 mm fast Line with rot 0.0, i.e. 0.53 s of unused rotation budget
(~26 deg). Iters 08/09/10 used exactly this overlap at the other wrist-limited moves (home trip ends, frame lift
side of the flip, all kept); the release side of the flip has never been tried (grep Point85/86 in the notes).
Alternatives: a J5 < 0 release (L28/L34/L40: no solution or arm collisions), turning in the release slow lift (L37:
elbow folds into the guide), more pre-turn on the frame-lift side (iter 10 already tuned it); the plank phase is
~66 of its 70 s fixed cost. This is the cheapest untried overlap of a J5-limited PTP with a paid Line.
Principle: minimise wrist travel time by overlapping it with moves that must be paid anyway.

## Screening (2 mm, --no-shots, toolbox/turn_toward.py design/program.json out 68 67 g)
- g 0.10 (J5 138.1 -> 124.8): 94.1 s, 0 violations.
- g 0.12 (J5 122.1, J3 -29.3): 94.0 s, 0 violations. Scored this one.
- g 0.15 / 0.20: 94.0 s but r1 2 "Guide/link_3" at #55/#56 (elbow folds onto the guide, L45 = L37 again).
- g 0.15 + TCP dz +15: 94.1 s, 0 (the longer Line eats the gain).

## Screenshots
- 00 start: unchanged layout; planks 1-3 upright in the base A slots, 4-6 in jig 2 at the far edge, guide on base B,
  arm at home with the gripper beyond the plate's far edge in the air. Nothing floating.
- 01 plank6 released: upright in the far column, gripper right above it, planks 5/4 still in jig 2.
- 02 plank5 released: far column 2 of 3, upright, jig 2 holds plank4 only.
- 03 plank4 released: far column full, jig 2 empty, planks 1-3 still in the base A slots.
- 04 plank3 / 05 plank1 / 06 plank2 released: the y-124 row fills outer to robot-side, all upright; base A slots
  empty after 06; arm elbow-up, normal pose.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, planks vertical and straight, the
  arm at the release pose with the elbow beside (not on) the guide, as in iter 16.
- 08 end: bench assembled in base B (planks upright in both frames), arm back at home.
- topview: paths identical to iter 16 (the change is an orientation only, at the base B release approach).

## Result
Expected ~-0.4 s, 0 violations; got 94.0 s (-0.4 s from 94.4), 0 violations, joints 2215 -> 2224 deg. Phases: frame
18.2 -> 17.9 s (planks 69.8 and home 6.4 unchanged). The reason held partly: the Line Point86 did take ~15 deg of
the flip's turn for free, but the budget was capped by the elbow over the guide (L45) at ~16 deg of J5, not by the
Line's 26 deg rotation budget. Kept.
