# iter 08: plank-end relief in base B that keeps the floor under the pieces B

## Hypothesis
Change type: jig_cad.
Follow-up of iter 07 (rejected): the last violation is r1 "Base B/plank3" at #127, a flush zero-depth contact of the
plank ends on the base B pocket floor (L09). Iter 07's 2 mm recess (plank bbox + 1 mm) fixed it but cut away the
floor under interface pieces B1/B2/B3/B6 (r6 4, L10).
Change: design/cad/jig_parts.py base_b(): recess only the plank-end footprint at the final release minus the
piece B footprints (measured in Base B local coordinates with scratch/footprints_b.py), so every piece keeps
its floor patch. If a plank end lies entirely on a piece (plank rests on the piece), no recess is needed there.
Expected: violations 1 -> 0 (first legal design), cycle 229.6 s and joints unchanged; r6 0.

Build notes: scratch/footprints_b.py showed the plank mesh end is two 2 x 5 mm tabs at the ends of its 25 mm width,
with the piece B (21 x 5) between them (L12). The STEP plank's end face is stepped (21.4 mm), so the tab positions are
taken from the plank's full extent along its width. Final: 12 recesses, tab + 0.75 mm, 2 mm deep (0.6 cm3; floor
left 7.5 mm, so walls stay >= 3 mm). Pieces lose <= 0.8 mm at their ends. scratch/contact_pts.py: no plank / Base B
contact at all at the final release (iter 06 had 6 flush ones).

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1 (turned over), base B shows frame 2 + red pieces, arm pulled back.
- 02 plank3 standing in the guide over frame 1, upright; others still in the jig.
- 03 plank6 placed: two planks upright in base A; gripper above, nothing tilted.
- 04 plank1 placed: three upright, jig holds three; no plank crossing another.
- 05 plank5 placed: four upright in base A; jig two left.
- 06 plank2 placed: five upright; one left in the jig.
- 07 plank4 placed: all six upright in the guide / frame 1, plank jig empty.
- 08 guide released back on base B (over frame 2), six planks free-standing in frame 1, arm clear of them.
- 09 frame 1 + planks turned over and lowered into base B: bench upright in base B, planks vertical between the two
  frames; gripper at the foot, arm reaching over the plate edge (same pose as iter 06). Nothing floating.
- 10 end: bench assembled in base B (backrest + seat planks), base A and plank jig empty, arm at home.
- topview: paths identical to iter 06 (program unchanged), base outlines unchanged.

## Result
Expected violations 1 -> 0, cycle unchanged. Got exactly that: violations 0 (r1 0, r6 0), cycle 229.6 s, joints
8923 deg, phases unchanged. First legal design. Kept.
Next: now optimise time; biggest phase is planks (127.2 s, 6 x ~21 s).
