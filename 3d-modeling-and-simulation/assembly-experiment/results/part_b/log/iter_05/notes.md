# iter 05: raise the plank1 transit (Point56) so plank1 clears plank2

## Hypothesis
Change type: program.
r1 "plank1/plank2" at move 76 (PTP Point52 -> Point56, carrying plank1 from the plank jig to above its slot in the
guide on base A). plank1's slot (TCP robot x -683, y 124) is in the same row as plank2 (x -653, y 124, placed
earlier), and the PTP arrives from the robot side, so plank1 crosses plank2 30 mm before its slot. During transit the
TCP is only ~125 mm above the release height, so plank1's lower end sweeps through plank2's top. Raise Point56 (the
PTP target, same orientation; toolbox/shift_moves.py) by +80 mm; the following fast Line Point57 down to the slow leg
gets 80 mm longer.
Expected: violations 3 -> 2 (r1 2 -> 1), no new r4 (the PTP ends higher, farther from parts), cycle +0.5..+1 s
(0.8 s extra line at 100 mm/s, PTP unchanged-ish).

Revised before the 2 mm score (screens only, `collision.py --parts --step 2`):
- +80 mm on Point56: still plank1/plank2 at #76 (scratch/plank_pair.py: plank1 bottom 236 vs plank2 top 280.6 at the
  end of the PTP; the planks are 250 mm long, the transit is only ~145 mm above the guide release). Would need ~+140
  (+1.4 s).
- Swap the plank2 and plank1 blocks (place -683 before -653; toolbox/swap_blocks.py): plank1 now hits plank2 *in the
  plank jig* (#50): plank1's slot (-370) is on the robot side of plank2's (-400), so picks must go outer-first,
  places must go robot-side-last. The two orders conflict with the current slot assignment.
Final change (type: mixed, one idea: "reassign the plank1 / plank2 jig slots"): plank1 starts in plank2's old slot
and vice versa (build_cell.py, identical planks, the jig is unchanged), and the two pick blocks swap their place
halves (pick -400 -> place -683, pick -370 -> place -653; grip events renamed; toolbox/swap_places.py). Place order in
the y124 guide row becomes -713, -683, -653: nothing passes over a placed plank. No extra moves.
Expected: violations 3 -> 2 (r1 at #76 gone), cycle -0.1..+0.1 s (the PTPs change a bit). Risk (L05): plank poses
change by hundredths -> the final insertion contact may move.
2 mm parts check before scoring: only #127 Base B/plank3 left.

## Screenshots
- 00 start: plank jig between robot and base A, 6 planks upright (plank1/plank2 now swapped, same slots occupied); guide on raised base B; arm at home. Nothing floating.
- 01 guide released on base A: guide flat over frame 1; gripper horizontal beside base A; jig untouched.
- 02 plank3: upright in the guide (far end of the y124 row), gripper above; 5 planks in the jig.
- 03 plank6: second plank upright in the y44 row; jig loses its outer slot in the other row.
- 04 plank1 (now 3rd): placed at x -683 next to plank3, upright; jig's middle outer slot empty (plank1's new start slot). Not crooked.
- 05 plank5: y74 row; 4 planks in the guide; 2 left in the jig (robot-side slots).
- 06 plank2 (now 5th): placed at -653, the robot-side end of the y124 row, nothing passed over; one plank left in the jig.
- 07 plank4: all 6 planks upright in the guide, jig empty, arm elbow-up over base A.
- 08 guide back on base B: guide flat on the riser; 6 planks upright in frame 1; gripper beside base B.
- 09 frame 1 + planks released into frame 2: turned over, planks down in base B; wrist at the plate edge, as in iter 04.
- 10 end: bench assembled in base B, base A empty, arm at home.
- topview: same paths as iter 04; the two plank transits now cross to the other slot (pick -400 -> place -683, pick -370 -> place -653); nothing new crosses a jig.

## Result
Expected violations 3 -> 2, cycle +-0.1 s. Got (2 mm): violations 2 (r1 1, r3 1), cycle 247.9 s (unchanged per
phase), joints 9006 deg (unchanged at 0.1 deg). As predicted; the final-insertion contact (#127 Base B/plank3) is
unchanged, no new one (L05 risk did not bite).
Dead ends (L07): +80 mm transit (still hits, would need +140 / +1.4 s); swapping the plank blocks (then plank1 hits
plank2 in the jig).
Kept: verdict BETTER (3 -> 2), screenshots fine. Left: Base B/plank3 at the frame release (#127, CAD slack in the
base B pocket / guide slots, L05) and the r3 side exit out of the foot grip (#128).
