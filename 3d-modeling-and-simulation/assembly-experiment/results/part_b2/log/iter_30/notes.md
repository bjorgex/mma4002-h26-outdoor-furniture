# iter 30: lower the plank -> frame hand-over end Point70yt toward its r4 floor (370 -> ~364 mm)

## Hypothesis
Change type: program. #47 Point70yt (P16eut -> Point70yt, 64.1 mm, rot 20 deg) is distance-limited at 0.64 s; its end
is at TCP z 370, 109.7 mm from the plank2 release point Point40. Lower it by 4-6 mm (toolbox/turn_toward.py g 0 with
dz): Line ~64.1 -> ~59-61 mm, expected -0.03..-0.05 s; the following Point80h PTP (J4-limited, 0.76 s) should be equal
or slightly shorter (its start comes closer to its end at z 142). Exact 90.282 -> ~90.24 s, rounded 90.3 -> 90.2 s,
0 violations. Risk: r4 near Point40 at the PTP start (distance ~102-104 mm, L43 slack), the link_6 camera over the
placed planks (L54).

## Reason
Evidence: toolbox/move_times2.py on the iter-29 best: #47 Point70yt d 64.1 mm, rot 20.0 (0.40 s rotation budget), 0.64 s,
distance-limited; iter 25 chose z 370 after screening only 370 / 375, while its own notes put the r4 near-point floor at
~360 (L53: re-derive a coordinate from the constraint that binds, not from the last value tried). Exact cycle 90.282 s
needs only -0.033 s to round to 90.2 (L55). Alternatives: Point85tt / Point88htt / Point80h / Point26t are all at rule
floors (r4 101 mm, elbow over the guide L56, base A box, camera L54); the base A pocket jig change (L49) does not fit
the ~45 min left. This is the one distance-limited Line left with measured slack to its floor.
Principle: shortest route once the binding constraint is known (L30: end fast Lines ~102-105 mm from the nearest event).

## Change
- `./py toolbox/turn_toward.py design/program.json scratch/n30{b,a,c}.json 59 59 0 0 0 -4/-6/-8`: Point70yt TCP z
  370 -> 366 / 364 / 362, orientation kept. scratch/exact27.py: 90.282 -> 90.261 / 90.250 / 90.240 s (less than the
  Line alone, ~-0.06 s, because the Point80h PTP grew slightly). -10 mm would be ~100.3 mm from Point40: not tried.
- 2 mm screens: n30c 90.2 s, n30a 90.3 s (90.250 rounds up), both 0 violations. design/program.json = n30c. No tool
  change.

## Screenshots
- 00 start: layout unchanged; six planks upright in base A's slots, frame 1 in base A, guide on base B, arm at home.
- 01 plank6 released upright in the far column, gripper just above; planks 4/5 still in their slots.
- 02 plank5 released next to plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, gripper above, nothing floating.
- 04 plank3 released in the outer row, upright; planks 1/2 still in base A's slots.
- 05 plank1 released beside plank3, upright.
- 06 plank2 released; all six planks upright in frame 1, gripper straight above plank2.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical; arm in the usual
  release pose at the -y edge, elbow clear of the guide.
- 08 end: bench assembled in base B, arm at home, base A empty; nothing floating, crooked or interpenetrating.
- topview: same paths as iter 29; the hand-over end near (-660, 150) is 8 mm lower, invisible in plan.

## Result
Expected -0.03..-0.05 s, 0 violations; got 90.3 -> 90.2 s (exact 90.282 -> 90.240, frame phase 17.2 -> 17.1), joints
2312 deg unchanged, 0 violations at 2 mm. The reason held: iter 25 had stopped 10 mm above the r4 near-point floor;
the gain was ~30 % smaller than the Line alone because the following J4-limited PTP got slightly longer. Kept. This
end is now ~102 mm from Point40, at its floor.
