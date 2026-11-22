# iter 36: remove the J6 detour around home (Point1 / P16s0tt) (tie-break on joint travel)

## Hypothesis
Raise J6 of home Point1 (steps 1 and 76) and of the start PTP end P16s0tt (step 2) toward the J6 of their neighbours
(Point88htt 61.9, Point26t 66.9), so J6 runs monotonically through the home pair instead of 61.9 -> 26.5 -> 17.8 ->
66.9. A J6 change at fixed other joints is a pure twist about the tool axis (TCP fixed). Expected: cycle unchanged
(89.940 exact; the home PTPs are J5-limited, Line #3 Point26t is distance-limited at 65.1 mm with rot 31.8 <= 32.5),
joint travel -40 to -88 deg, 0 violations if Line #3's rotation stays <= 32.5 deg and the link_6 camera, which turns
with J6, stays clear of plank4 (L51/L54/L60). Change type: program.

## Reason
Evidence: show_joints on the iter-35 best: J6 goes 61.9 (Point88htt) -> 26.5 (Point1) -> 17.8 (P16s0tt) -> 66.9
(Point26t) -> 87.2, i.e. ~93 deg of J6 travel where ~25 would do; the PTPs on both sides are J5-limited (110.1 / 20.1
deg), so their J6 deltas are free to shrink. exact27 gives 89.940 s; iter 33/34 showed no movable move has the 0.09 s
needed for the next rounding step, so the only "better" left in a short session is the joint_travel tie-break.
Why this and not something else: ~35 min of budget is left, too little for a structural change (fewer slow legs /
grips); iter 35 removed the J3 detour at the same place, J6 is the bigger one. DFA / cell principle: smooth joint
paths, minimise J6 rotation (AGENT heuristics). Risk: the camera on link_6 rotates with J6 over plank4 at low home /
P16s0tt heights (L54/L60) - screen several J6 values at 2 mm.

## Screenshots
- 00 start: frame 1 + pieces in base A, planks upright in base A edge slots / plank jig, frame 2 under the guide in base B; arm at home over the far edge, gripper above the planks, same pose as iter 35 (home unchanged).
- 01 plank6 released: one plank upright in frame 1, gripper straight above; nothing floating.
- 02 plank5 released: two planks placed, upright, nothing crooked.
- 03 plank4 released: three planks in frame 1, vertical.
- 04 plank3 released: four planks placed, two left in their slots.
- 05 plank1 released: five planks upright and parallel.
- 06 plank2 released: all six in frame 1, plank slots empty.
- 07 frame 1 released: frame 1 + planks upside down through the guide into base B, planks vertical, arm from the -y side at the base B edge; nothing intersecting.
- 08 end: bench assembled in base B under the guide, base A empty, arm back at home (same as start pose).
- topview: TCP path identical to iter 35 (the change is a twist about the tool axis, TCP fixed); start PTP (orange dashed) unchanged in shape.

## Result
Expected: cycle unchanged, joints -40 to -88 deg, 0 violations. Got: cycle 89.9 s (exact 89.940, unchanged), joints 2301 ->
2280 deg (-21), 0 violations (2 mm). The full monotonic J6 (P16s0tt J6 ~64) was not free: Line #3 to Point26t then
became rotation-limited (+0.38 s at J6 64, +0.12 s at 45, +0.005 s at 32); J6 28 (was 17.8) is the largest value with
the exact cycle unchanged. Home Point1 (J6 26.5) already lay between its neighbours, so only P16s0tt carried the
detour. The reason held partly: the detour was real, but most of it is the price of Line #3's rotation budget, not
waste. Kept on the tie-break.
