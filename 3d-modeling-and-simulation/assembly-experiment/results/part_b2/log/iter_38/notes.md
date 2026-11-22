# iter 38: split the start Line #3 (P16s0tt -> Point26t) at a joint-space midpoint orientation

## Hypothesis
Insert a midpoint Point26tm into the fast rotating Line P16s0tt -> Point26t: TCP at half the straight distance,
orientation = FK of the joint-space midpoint (scratch/split38.py). Expected: joint travel -5..-10 deg (J3 bulge inside
the Line), cycle unchanged only if both halves stay distance-limited (32.5 mm / 16.3 deg each). Change type: program.
Screens before scoring already say it fails (see Result); scored anyway to close the idea with judge numbers.

## Reason
Evidence: scratch/travel38.py (new: sampled joint travel per move vs |end - start|) on the iter-37 best shows the
largest in-move detour in Line #3: J3 9.3 + J2 2.8 deg extra (the TCP-straight Line with a 31.9 deg tool turn bends
the elbow); other detours are 5-6 deg (P16eut J4, Point80Ltt J4). exact27 = 89.940 s, and iters 33-37 showed no
movable move holds the 0.09 s to the next rounding step, so the joint-travel tie-break is the only reachable "better"
with ~20 min of budget left. Alternatives screened first: undoing part of the iter-22 J5 pre-turn at P16s0tt
(j5turn20 D -0.3/-0.6/-1.0) to reduce the J4 detour there - J4 moved the wrong way (-63.6 -> -64.1) and cycle rose
(+0.006..+0.019 s), dropped. DFA / cell principle: smooth joint paths, minimise joint travel.

## Screenshots
- 00 start: frame 1 + pieces in base A, planks upright in base A edge slots / plank jig, guide on base B; arm at home high over the far edge.
- 01 plank6 released: one plank upright in frame 1, gripper straight above; nothing floating.
- 02 plank5 released: two planks upright, nothing crooked.
- 03 plank4 released: three planks placed, vertical.
- 04 plank3 released: four placed, two left in their slots.
- 05 plank1 released: five planks upright and parallel.
- 06 plank2 released: all six in frame 1, slots empty.
- 07 frame 1 released: frame 1 + planks upside down through the guide into base B, arm from -y at the base B edge; nothing intersecting.
- 08 end: bench assembled in base B, arm back at home.
- topview: TCP path as iter 37 (the split point lies on the straight start Line; not visible as a change).

## Result
Screens (before scoring): the joint-space midpoint orientation is not on the slerp path: halves 16.1 + 17.4 = 33.5
deg vs 31.9 direct, so the second half becomes rotation-limited (17.4/50 = 0.348 s > 0.326 s). exact27: planks
67.352 -> 67.375 s (total 89.962 -> rounds to 90.0, worse); travel38: total 2272.2 -> 2273.4 deg (worse: the Line's
J3 bulge comes from the TCP constraint, the midpoint only moves it, and adds J2/J3 back-and-forth at the joint).
The reason did not hold: the evidence (a 9 deg J3 bulge) was right, but it is a property of a TCP-straight Line with
that tool turn, not removable by re-shaping the orientation path within the Line's rotation budget. Scored (decide
requires a score): 0 violations, cycle 90.0 s (+0.1), joints 2278 (+1) -> NOT better; rejected as predicted.
