# iter 37: home J6 26.5 -> 28 (last J6 detour at home, tie-break on joint travel)

## Hypothesis
Set J6 of home Point1 (first and last move) from 26.5 to 28.0 (= P16s0tt's J6 since iter 36). J6 then runs
61.9 (Point88htt) -> 28 (Point1) -> 28 (P16s0tt) instead of 61.9 -> 26.5 -> 28: joint travel -3 deg (2280 -> ~2277),
cycle unchanged (both home PTPs are J5-limited: 110.1 / 20.1 deg; no Line touches home), 0 violations (a 1.5 deg twist
about the tool axis at TCP z 401, far above everything). Change type: program.

## Reason
Evidence: show_joints on the iter-36 best: J6 61.9 (Point88htt) -> 26.5 (Point1) -> 28.0 (P16s0tt) -> 66.9; iter 36 raised
P16s0tt to 28 (L61: Line #3's rotation budget caps it) but left home at 26.5, so home is now 1.5 deg *outside* its
neighbours - a 2 x 1.5 deg detour. Any home J6 in [28, 61.9] gives the same minimum; 28 is the smallest twist (least
link_6 camera movement over plank4, L51/L60). exact27 = 89.940 s and iter 33 showed no movable move holds the 0.09 s to
the next rounding step, so with ~30 min of budget the joint-travel tie-break is the only "better" reachable.
Alternatives: the other joints at home are already monotonic (J1, J2, J4, J5; J3 fixed in iter 35); the flip via Pvia is
monotonic in every joint. DFA / cell principle: minimise J6 rotation, smooth joint paths.

## Screenshots
- 00 start: frame 1 + pieces in base A, planks upright in the base A edge slots / plank jig, frame 2 under the guide in base B; arm at home over the far edge, gripper high above the planks (1.5 deg twist not visible).
- 01 plank6 released: one plank upright in frame 1, gripper straight above; nothing floating.
- 02 plank5 released: two planks placed upright, nothing crooked.
- 03 plank4 released: three planks placed, vertical.
- 04 plank3 released: four planks placed, two left in their slots.
- 05 plank1 released: five planks upright and parallel.
- 06 plank2 released: all six in frame 1, plank slots empty.
- 07 frame 1 released: frame 1 + planks upside down through the guide into base B, planks vertical, arm from the -y side at the base B edge; nothing intersecting.
- 08 end: bench assembled in base B under the guide, base A empty, arm back at home (same pose as the start).
- topview: TCP path identical to iter 36 (twist about the tool axis at home only).

## Result
Expected: cycle unchanged, joints -3 deg, 0 violations. Got: cycle 89.9 s (exact 89.940, unchanged), joints 2280 -> 2277
deg (-3), 0 violations at 2 mm. The reason held: home was 1.5 deg outside its J6 neighbours after iter 36, and both home
PTPs are J5-limited, so the twist was free. Kept on the tie-break. Remaining joint detours around home: none (all six
joints now monotonic through Point88htt -> Point1 -> P16s0tt).

