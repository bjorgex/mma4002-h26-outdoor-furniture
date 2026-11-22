# iter 34: remove the J2 detour at the flip via point Pvia (tie-break on joint travel)

## Hypothesis
Set Pvia's J2 from -45.0 (a hand-set lift override from iter 05, L35) to ~-48.6 (= Point80Ltt's J2), so J2 runs
monotonically -48.6 -> -72 through the flip instead of rising 3.6 deg and coming back. Expected: cycle unchanged
(89.940 exact, J5 limits both PTP halves), joint travel -7 deg (2312 -> ~2305), 0 violations if the lower swing
still clears base A / frame parts (r4). Change type: program.

## Reason
Evidence: scratch/exact27.py gives 89.940 s exact; the next rounding step (89.85) needs -0.09 s, and iter 33 left every
movable move within 1-2 mm of a rule floor. The keep rule breaks cycle ties by joint_travel_deg, so a change that keeps
cycle at 89.9 and cuts >= 1 deg of joint travel is a valid "better". show_joints on the best: through the flip
Point80Ltt -> Pvia -> Point85tt every joint is monotonic except J2 (-48.6 -> -45.0 -> -72.0), a 7.2 deg detour set by
hand in iter 05 to lift the swing over base A (L35). J2 is far from limiting either half (J5 23.9 / 122.1 deg).
Why this and not something else: the other detours (J3/J6 at the frame lift, ~47 deg each) come from iter 20's J5
pre-turns that save time - undoing them costs time. The home PTP pair has only a 2.8 deg J3 detour. With 40 min left,
a structural change (fewer slow legs/grips) cannot be built and verified in one session.
DFA / cell principle: minimise joint travel / smooth joint paths (no back-and-forth of a joint inside one motion).
Risk: the via point was raised for r4 over base A; screen J2 -48.6 and an intermediate -47 at 2 mm.

## Screenshots
- 00 start: frame 1 + pieces in base A, frame 2 under the guide in base B on its riser, planks upright in the base A edge slots / plank jig; arm at home over the far edge.
- 01 plank6 released: one plank upright in frame 1, the others in their slots; gripper above, nothing floating.
- 02 plank5 released: two planks in frame 1, vertical; arm pose as in iter 33.
- 03 plank4 released: three planks in frame 1, upright, nothing crooked.
- 04 plank3 released: four planks in frame 1, the last two still in their slots.
- 05 plank1 released: five planks upright and parallel.
- 06 plank2 released: all six planks in frame 1, slots empty; gripper above the last plank.
- 07 frame 1 released: frame 1 + planks upside down through the guide into base B, planks vertical, arm at the base B edge from the -y side; nothing intersecting.
- 08 end: bench assembled in base B under the guide, base A empty, arm back at home.
- topview: same TCP path as iter 33; the flip PTP (dashed, from the frame grip toward -x) bends a little differently only in z, nothing new over the plank rows.

## Result
Expected: cycle unchanged, joints -7 deg, 0 violations. Got: cycle 89.9 s (exact 89.940, unchanged), joints 2312 -> 2304
deg (-8), 0 violations, free-move clearance unchanged (30.7 mm). Variant J2 -47 also clean (2308 deg); took -48.6 (no
J2 back-and-forth at all). The reason held: the J2 rise at Pvia was a pure detour (J5 limits both halves), and the
lower swing still clears base A's r4 box. Kept on the tie-break (equal cycle, less joint travel). Cycle-time gains now
need structural change (fewer slow legs / grips, another frame grip for the J5 round trip).
