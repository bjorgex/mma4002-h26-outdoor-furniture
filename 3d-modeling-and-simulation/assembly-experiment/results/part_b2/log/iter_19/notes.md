# iter 19: shorter escape Line after the last plank release (Point70y)

## Hypothesis
Change type: program. After the plank2 release and its slow lift, the fast Line #46 P16eu -> Point70y runs 113 mm
(1.13 s, distance-limited; rot 40 deg needs only 0.80 s) to TCP (-723, 134, 391) before the frame-approach PTP. Move
Point70y to a closer point that still satisfies the PTP start rules (>= ~110 mm from every grip/release point, out of
the placed planks' boxes or >= their top + 100 = 381, >= the 321 safe height): e.g. ~(-660, 150, 385), a ~75 mm Line
(~0.8 s, rotation-limited). Expected -0.2..-0.35 s (93.6 -> ~93.3 s), 0 violations; risk: the PTP to Point80h gets
longer (J4) or its swing clips the placed planks / frame 1 (r1/r4), so screen at --step 2.

## Reason
Evidence: toolbox/move_times2.py on the iter-18 best: #46 Point70y d 113.3 mm, rot 40.1, 1.13 s - the longest
movable non-wrist-limited move left in the plank -> frame hand-over; it is distance-limited (rot budget 0.80 s). Its
end was placed in iter 16 (reorder) over the far column at z 391, which is more than the r4 rules need when the start
is out of the y-124 plank boxes. Alternatives: the start/home/flip PTPs are J5-limited and elbow-capped (L37, L45),
iter 18 already took the start PTP to its J4 floor; plank slow legs + waits (~66 s) are rule-fixed; a bolder fixed-cost
cut (two planks per grip, planks pre-presented over frame 1) is not feasible with the fixed gripper/start state in the
time left (~95 min). Per L42, the hand-over Lines were not re-optimised after iter 16's reorder.
Principle: shortest route between the last place and the next grip, with only the clearance the rules need.

## Screening (2 mm, --no-shots; scratch/move_tcp19.py moves Point70y's TCP, prints nearest grip/release points)
- a (-660, 150, 385), full rot: Line 0.80 s (rot-limited), PTP 0.74 s (J2): 93.4 s, 0 violations (nearest event 122 mm).
- c (-680, 150, 385): Line 0.85, PTP 0.70 (J4): 93.4 s, 0 violations.
- b straight up (-638, 124, 392) / d (-650, 145, 380): PTP 0.82 / 0.78 s, no better (not screened).
- e / f (-665, 150, 378) with only 70 / 50 % of the rotation in the Line: the PTP turns J4 / J6-limited (0.78 / 0.94 s),
  no net gain.
- g / h: + Point80h slid 10 / 15 % further down its diagonal (ptp_along.py): 93.3 s but r4 1 "Point80h: TCP < 100 mm
  above Base A" - Point80h is already at its base-A limit. Scored a.

## Screenshots
- 00 start: unchanged layout; arm at home beyond the far edge, planks 1-3 in base A slots, 4-6 in jig 2, guide on
  base B. Nothing floating.
- 01 / 02 / 03 plank6 / 5 / 4 released: far column fills, planks upright in frame 1, jig 2 empties; gripper vertical
  above the released plank.
- 04 / 05 / 06 plank3 / 1 / 2 released: y-124 row fills outer to robot side, all upright, base A slots empty after 06.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, planks vertical, arm at the usual
  release pose over the -y edge.
- 08 end: bench assembled in base B, arm back at home.
- topview: the only path change is the purple Line after the last place: it now leaves plank2 diagonally toward +y
  (to ~(-660, 150)) instead of running back over the far column to (-723, 134); the PTP to the frame foot follows.

## Result
Expected -0.2..-0.35 s, 0 violations; got 93.4 s (-0.2 s from 93.6), 0 violations, joints 2257 deg unchanged.
Phases: planks 69.4, frame 17.9 -> 17.6, home 6.4. The reason held: the old Line was 113 mm, distance-limited; the new
one is 77 mm and now rotation-limited (0.80 s, 40 deg), the PTP got 0.09 s longer (J2), net -0.24 s. Moving the
rotation into the PTP does not help (J4/J6 take over, L38). Kept.
