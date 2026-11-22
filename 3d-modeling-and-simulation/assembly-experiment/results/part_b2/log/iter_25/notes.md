# iter 25: shorten the plank -> frame hand-over Line Point70y (move its rotation into the slow lift, lower its end)

## Hypothesis
Change type: program. #47 Point70y (P16eu -> Point70y, 76.8 mm, rot 40.1 deg) is rotation-limited at 0.80 s. The
slow lift before it, #46 P16eu (33.5 mm at 20 mm/s = 1.675 s), turns only 60.1 deg of its ~84 deg budget. (1) Turn
P16eu toward Point70y's orientation by g ~0.5 (toolbox/turn_toward.py), so ~20 deg of the turn moves into the paid
slow leg; (2) lower Point70y's end: at y 150 it is out of every placed-plank box, so it only needs >= 100 mm (+ slack)
from the plank2 release point Point40 (horizontal 33.7 mm -> TCP z >= ~360) and the 321 safe height; try TCP z 370 /
375 (was 385). Expected: Point70y 0.80 -> ~0.65 s, Point80h PTP equal or slightly faster: about -0.15 s
(91.3 -> ~91.15 s), 0 violations. Risk: r4 near Point40 / over plank2's box on the PTP Point80h start (L29, screen at
2 mm), the wrist camera swinging over the placed planks during the bigger turn in P16eu.

## Reason
Evidence: toolbox/move_times2.py on the iter-24 best: #47 Point70y d 76.8 mm, rot 40.1, 0.80 s "ROT-LIMITED", while
#46 P16eu has 60.1 deg in a 1.675 s slow leg (23 deg unused); Point70y ends at TCP z 385, which was needed when its
start/end were inside plank boxes (L29 moved it 30 mm in +y out of them, but kept the height). The plank phase is
~98 % rule-fixed (slow legs + waits), the flip / release / home are J5-limited and elbow-capped (L28, L37, L45, L51),
and the frame-grip pre-turn needs a jig change (iter 21) that does not fit the ~40 min left; this is the largest
non-fixed, non-J5 move left that a program-only change can cut.
Principle: overlap motion with an already-paid fixed-cost event (rotation inside a slow leg, L36); shortest route
once the r4 reason for a detour is gone (L29/L30: end moves ~105-110 mm from the nearest event point).

## Change
- toolbox/turn_toward.py design/program.json -> scratch/k25a.json 58 59 0.5: P16eu -> P16eut, rot 60.1 -> 80.1 deg
  (still 1.68 s, distance-limited), J6 95 -> 73.
- toolbox/turn_toward.py k25a 59 59 0 0 0 -15 (g 0 = orientation kept, TCP dz -15): Point70y -> Point70yt at TCP z 370
  (k25b); dz -10 (z 375) = k25c. move_times2: Point70yt 63.7 mm, rot 20.0, 0.64 s; Point80h PTP now J4-limited 37.9
  deg, 0.76 s (+0.02).
- 2 mm screens: k25b 91.1 s, k25c 91.2 s, both 0 violations. Scored k25b.

## Screenshots
- 00 start: unchanged layout; six planks upright in base A's slots, guide on base B, arm at home beyond the far edge.
- 01 plank6 released upright in the far column, gripper just above; planks 4/5 still in their slots.
- 02 plank5 released next to plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, far-wall slots empty.
- 04 plank3 released in the outer y-124 place, upright.
- 05 plank1 released next to it, upright.
- 06 plank2 released; all six planks upright in frame 1, base A slots empty; gripper straight above plank2.
- 07 frame 1 + planks flipped into frame 2 through the guide on base B, planks vertical; arm at the usual release pose
  over the -y edge.
- 08 end: bench assembled in base B, arm at home; base A empty; nothing floating or crooked.
- topview: same paths as iter 24; the hand-over from the last place (x -638, y 124) to the frame foot is a slightly
  shorter segment (end at y 150), frame approach / flip / home arcs unchanged.

## Result
Expected about -0.15 s (91.3 -> ~91.15), 0 violations; got 91.1 s (-0.16 s programmed: Point70y 0.80 -> 0.64, Point80h
+0.02), 0 violations, joints 2324 -> 2328 deg; phase "frame 1 + planks" 17.4 -> 17.3, others unchanged. The reason
held: Point70y was rotation-limited with spare budget in the paid slow lift before it, and its 385 mm end height was
a leftover of the in-box start (L29); at y 150 the r4 near-point limit (~360) binds instead. Kept. Small gain: the
program-only moves are now at their rule floors; the next real gains need fewer J5 degrees (another frame grip or
release orientation) or the iter-21 jig change.
