# iter 39: J5 pre-turn at P16eut 0.5 deg smaller (J4 bulge in the lift Line, tie-break on joint travel)

## Hypothesis
Turn P16eut (end of the slow lift after the last plank release, steps idx 58) by J5 -0.5 deg about the J5 axis
(scratch/j5turn20.py, TCP kept). Expected: joint travel -1 deg (travel38: 2272.2 -> 2271.3 sampled), cycle 89.946 s
exact (+0.006, still rounds to 89.9), 0 violations (0.5 deg tool turn high above the placed planks). Change type: program.

## Reason
Evidence: scratch/travel38.py on the iter-37 best: the second-largest in-move detour is the Line P16ek -> P16eut, J4
5.6 + J3 2.3 deg extra; unlike Line #3 (L64) its end pose is a free choice (iter-22 style J5 pre-turn), so it can be
changed. Screens of D (scratch/exact27.py + travel38): -3 -> travel -5.2 but 89.979 s (rounds 90.0); -1 -> -1.8 deg but
89.953 (x.x5, L58); +3 -> +5 deg; -0.5 -> -0.9 deg at 89.946 s. With ~20 min of budget and iters 33-37 showing no
movable move holds the 0.09 s to the next rounding step, the joint-travel tie-break is the only reachable "better".
Alternative (Line #3 split) was closed in iter 38. DFA / cell principle: smooth joint paths, minimise joint travel.

## Screenshots
- 00 start: frame 1 + pieces in base A, planks upright in the base A edge slots / plank jig, guide on base B; arm at home high over the far edge.
- 01 plank6 released: one plank upright in frame 1, gripper straight above; nothing floating.
- 02 plank5 released: two planks upright, nothing crooked.
- 03 plank4 released: three placed, vertical.
- 04 plank3 released: four placed, two left in their slots.
- 05 plank1 released: five upright and parallel.
- 06 plank2 released: all six in frame 1, slots empty; arm above (the changed P16eut lift follows - no visible difference).
- 07 frame 1 released: frame 1 + planks upside down through the guide into base B, arm from -y at the base B edge; nothing intersecting.
- 08 end: bench assembled in base B, base A empty, arm back at home.
- topview: TCP path identical to iter 37 (only a 0.5 deg tool turn at P16eut).

## Result
Expected: joints -1 deg, cycle 89.946 exact (89.9), 0 violations. Got: 0 violations at 2 mm, cycle 89.9 s, joints 2277 ->
2276 deg (-1); judge verdict BETTER. The reason held: the J4 bulge in the lift Line depends on its end pose; a small J5
turn trims it. Larger turns (-1, -3) cost cycle via the next Line/PTP, so the gain is capped by the 89.95 rounding step.
Kept on the tie-break.
