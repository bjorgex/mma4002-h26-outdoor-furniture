# iter 22: hide more of the home-trip J5 turn in the first pick's slow descent (split Point27's leg)

## Hypothesis
Change type: program. The first pick's slow approach #5 Point26s -> Point27 (TCP 286 -> 246, 40 mm, 2.0 s) turns
nothing, but the fingers are still above plank6's top (261) for its first ~20 mm. Insert a slow Line point Point26d
K mm below Point26s with the grip orientation (toolbox/insert_slow_point.py), then turn P16s0t, Point26t and Point26s
by J5 +D (scratch/j5turn20.py) so the new K mm segment turns ~D deg for free, and move home back onto the joint path
Point88ht -> P16s0t (toolbox/home_on_path.py) so the two home PTPs share the smaller J5 total. Expected: home leg J5
161 -> ~161-D; with D ~30-40 (K 15-20 mm, budget 2.5 deg/mm): -0.6..-0.8 s (93.2 -> ~92.5 s), 0 violations.
Risk: the tilted fingers / camera vs plank6 (being picked) and plank5 (30 mm in y) in the low segment (r1/r5);
J4/J1 take over the PTP limit (L38).

## Reason
Evidence: toolbox/move_times2.py on the iter-20 best: the home trip is #61 Point1 2.75 s (J5 137.5) + #2 P16s0t 0.47 s
(J5 23.6, J4 19.9 next) = 3.2 s, purely J5-limited (Point88ht J5 +123 -> P16s0t -38; J4 74, J1 46 are far below).
Iter 18 hid 24 deg in the 10.5 mm segment Point26s and stopped there, but #5 Point27 (40 mm slow, rot 0.0) starts with
the TCP 25 mm above the plank top, so ~15-20 mm more of slow leg can turn the tool. The release side is elbow-capped
(L37/L45), the frame flip is capped by base A engagement (L49, iter 21) and the guide (L45); plank legs and waits are
fixed. Alternatives considered: shallower base A pocket so the frame lift can turn (jig_cad, ~0.4 s, unsure because the
far frame end swings down, iter 21); PTP end along the frame diagonal (~0.1 s). This one is program-only, larger, and
uses existing tools.
Principle: overlap wrist travel with rule-limited slow legs that are paid anyway.

## Screening (2 mm, --no-shots)
- K 15 / D 30 (v22a4, home_on_path f 0.85 Point88ht -> P16s0t): 92.6 s, 0 violations, joints 2290.
- K 20 / D 40: P16s0t IK went to J4 -118 / J6 -29 (near J5 = 0), start PTP J4-limited - not screened (L50).
- K 20 / D 35 (v22c4): 92.5 s, 0 violations, joints 2377 (J4 swings at P16s0t, J5 -6.6). Scored this one (lowest cycle).

## Screenshots
- 00 start: layout unchanged; arm at the new home (TCP z 391, beyond the plate's far edge, gripper tilted); planks 1-3
  in base A slots, 4-6 upright in jig 2, guide on base B. Nothing floating.
- 01 plank6 released: upright in frame 1's far column, gripper vertical above it; plank5/4 still in jig 2.
- 02 plank5 released: far column 2 of 3, upright; plank4 alone in jig 2.
- 03 plank4 released: far column full, jig 2 empty.
- 04 / 05 / 06 plank3 / 1 / 2 released: y-124 row fills outer to robot-side, all upright; base A slots empty after 06;
  arm in the usual elbow-up pose.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, planks vertical, arm at the release
  pose reaching over the -y edge, as in iter 20.
- 08 end: bench assembled in base B, arm back at home (same pose as 00).
- topview: same paths as iter 20; the start PTP (orange dashed) now comes from home at y ~0 instead of y -197 (home
  moved along the joint path).

## Result
Expected -0.6..-0.8 s, got -0.7 s (93.2 -> 92.5 s), 0 violations. Per phase: home 6.4 -> 5.8 s, planks 69.4 -> 69.3,
frame unchanged. The new slow segment Point26d turns 35 deg in 20 mm (1.0 s, no added time); the home PTP J5 137.5 ->
110.1 deg (2.75 -> 2.20 s), start PTP 0.47 -> 0.39 s. The reason held: the first 20 mm of the pick's slow leg had free
rotation budget, and the fingers clear plank6 there (r1/r5 0 at 2 mm). Joint travel rose 2267 -> 2377 deg because of
the J4/J6 swing near J5 = 0 at P16s0t (L50); cycle is the ranking criterion, so kept.
