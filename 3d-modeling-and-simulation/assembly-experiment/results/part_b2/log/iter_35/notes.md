# iter 35: remove the J3 detour at home (Point1) (tie-break on joint travel)

## Hypothesis
Set home Point1's J3 (both occurrences, steps 1 and 76) from -58.7 to about -60.5, between its neighbours
Point88htt (-61.9) and P16s0tt (-60.1), so J3 runs monotonically through the home pair instead of rising and
coming back. Expected: cycle unchanged (89.940 exact; the home PTPs are J5/J4-limited), joint travel -2 to -3 deg
(2304 -> ~2301), 0 violations if home stays clear of plank4 (link_6, L51). Change type: program.

## Reason
Evidence: show_joints on the iter-34 best: through Point88htt -> Point1 -> P16s0tt every joint is monotonic except J3
(-61.9 -> -58.7 -> -60.1), a 2.8 deg back-and-forth; iter 34 noted it as the last detour left after removing Pvia's
J2 rise. exact27 gives 89.940 s, and the next rounding step (89.85) needs -0.09 s that no movable move has (iter 33:
all within 1-2 mm of a rule floor). The keep rule breaks cycle ties by joint_travel_deg, so >= 1 deg less is "better".
Why this and not something else: with ~35 min of budget left, a structural change (fewer slow legs / grips) cannot be
built and verified in one session; the other joint detours (J3/J6 at the frame lift) are iter 20's time-saving
pre-turns. DFA / cell principle: smooth joint paths, no back-and-forth of a joint inside one motion.
Risk: L51 - home moving lower brings link_6 near plank4; J3 -1.8 deg moves the TCP only a few mm; screen at 2 mm.

## Screenshots
- 00 start: frame 1 + pieces in base A, planks upright in base A edge slots / plank jig, frame 2 under the guide in base B; arm at home over the far edge, gripper above the planks as before.
- 01 plank6 released: one plank upright in frame 1, gripper above; nothing floating.
- 02 plank5 released: two planks placed, upright; arm pose unchanged vs iter 34.
- 03 plank4 released: three planks in frame 1, vertical, nothing crooked.
- 04 plank3 released: four planks placed, two still in their slots.
- 05 plank1 released: five planks upright and parallel.
- 06 plank2 released: all six in frame 1, slots empty.
- 07 frame 1 released: frame 1 + planks upside down through the guide into base B, planks vertical, arm from the -y side at the base B edge; nothing intersecting.
- 08 end: bench assembled in base B under the guide, base A empty, arm back at home (pose visually identical to iter 34).
- topview: same TCP path as iter 34; the home PTPs (dashed, far left) unchanged in shape.

## Result
Expected: cycle unchanged, joints -2 to -3 deg, 0 violations. Got: cycle 89.9 s (exact 89.940, unchanged), joints 2304 ->
2301 deg (-3), 0 violations. First try (J3 -60.5) hit link_6/plank4 at moves #1/#2 (L60, L51 again), J3 -60.1 alone still
hit at #2; J3 -60.1 with J2 -37.7 -> -36.0 (inside J2's monotonic range -55.1..-33.1, no extra J2 travel) lifts the wrist
back and is clean. The reason held only partly: the J3 rise was not a pure detour but the link_6 clearance over plank4,
which J2 can provide for free. Kept on the tie-break. Further cycle gains need structural change.
