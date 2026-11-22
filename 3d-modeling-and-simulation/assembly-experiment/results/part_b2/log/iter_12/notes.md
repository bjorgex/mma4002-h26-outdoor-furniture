# iter 12: plank jig as one column along base A, slots aligned with the place rows

## Hypothesis
Change type: jig_cad (+ layout, + the pick blocks moved rigidly with their planks; no new moves). The plank jig
becomes a 40 x 168 mm column next to base A (same 5 mm gap): planks 1-3 (row 0, yaw 0) at robot x -575, y 127 / 157 /
187 (plank3 / plank1 / plank2), planks 4-6 (row 1, yaw 80) at robot x -583, y 105 / 75 / 45 (plank4 / 5 / 6) - the
same y as their places in frame 1 (103 / 74 / 44). Slot orientations unchanged, so every pick block is only
translated (toolbox/shift_moves.py per plank, joints by IK). Expected: about -1.5 s (group 1 transfer Lines
147 -> 140 / 115 / 102 mm, -0.85 s; shorter return Lines ~-0.4 s; group 2 PTPs ~-0.2 s); 0 violations, risk r4 at the
PTP ends near the new neighbours and the forearm over the jig on the frame trip.

## Reason
Evidence: move_times2 on the iter-10 best: of the 83.2 s plank phase, 66.7 s are fixed (4 slow legs x 2.53 s + 2
waits per plank); the remaining ~16.5 s are transfers, set by the pick-to-place distance: group 1 transfers are
147 mm Lines (1.47 s each) and the return Lines 112-175 mm, group 2 PTPs 0.82-0.91 s (J3, i.e. reach). The 2 x 3 jig
puts picks 137 mm (x) and up to 227 mm away from their places, and its robot-side row is 60 mm farther than needed.
Alternatives: more move tuning (iters 05-10 took the move-level gains; the flip/home J5 round trip needs a different
frame grip, iter 11 / L40); gripping two planks at once is not possible with the fixed gripper. A layout change of
the most-visited fixture is the biggest remaining lever on the non-fixed time.
Principle: place the most-visited fixture close to the assembly point; present parts in their assembly orientation
and order (pick y = place y, so carries run straight; pick order still outer-first in the jig (L07): each carried
plank only crosses slots already emptied).

## Screening (2 mm)
- n12a (jig column + pick blocks moved, toolbox/move_picks.py): 105.5 s, r1 1: plank4 carried past placed planks 1/2
  (PTP #52 Point61 -> Point65, L41).
- n12c / n12d (+ via point Pv4 on that PTP, TCP -15 / -22 mm in y): 105.5 s, 0 violations; scored n12d (more slack).

## Screenshots
- 00 start: new narrow plank jig as a column right beside base A (x ~-555..-590, y 27..195), 6 planks upright in it,
  frame 1 + pieces in base A, guide on base B; arm at home over the plate, nothing floating.
- 01 plank3 released: plank3 upright in frame 1's y-124 row, the other 5 still in the jig column; arm above base A.
- 02 plank1 released, 03 plank2 released: the y-124 row filling robot-side-last, jig column emptying from the
  plank3 slot outward; planks straight, gripper above.
- 04 plank6, 05 plank5, 06 plank4 released: the x -743 row fills in y 44 -> 74 -> 103; all six upright in frame 1,
  jig empty after 06; nothing crooked or in another part.
- 07 frame 1 + planks released: flipped into frame 2 on base B through the guide, arm at the release pose as in
  iter 10 (frame phase unchanged).
- 08 end: bench assembled in base B, arm back at home; jig and base A empty.
- topview: plank carries now short and mostly along x from the column to frame 1; group-2 PTPs run straight in x at
  their place y (via Pv4 bends plank4's away from the y-124 row); frame/home paths as before.

## Result
Expected ~-1.5 s, 0 violations; got 105.5 s (-2.2 s), 0 violations, joints 3014 -> 2956 deg. Phases: planks
83.2 -> 81.0 s (-2.2), frame 18.0 and home 6.5 unchanged. The reason held: the non-fixed plank time was distance-bound
and the layout cut it more than estimated (the return Lines and the group-2 PTPs gained too). Kept.
