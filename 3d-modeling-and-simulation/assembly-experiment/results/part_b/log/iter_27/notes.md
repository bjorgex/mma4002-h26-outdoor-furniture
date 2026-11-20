# iter 27: planks 4-6 presented pre-rotated 80 deg in the jig, placed as a group after 3, 1, 2

## Hypothesis
Change type: mixed (jig_cad + layout + program; tested together because the slot rotation alone makes the
interleaved order worse - each part depends on the other).
The planks phase (89.0 s) has five J6-limited PTPs (#19, 24, 41, 46, 63: 1.43-1.57 s, J6 ~75 deg) because planks 4-6
sit in frame 1 turned 80 deg about vertical vs the jig (scratch/yaw27.py: delta 0 for 1-3, 80 for 4-6), and the
order 3, 6, 1, 5, 2, 4 alternates the two orientations. Change:
1. jig CAD: the row-1 slots (planks 4-6) turned 80 deg about their centres; the block 60 -> 66 mm deep in y so the
   outer wall stays >= 3 mm (rotated slot reaches y 58.1, wall 7.9).
2. build_cell: planks 4-6 start turned 80 deg about their slot centres.
3. program: their pick moves rotated with the plank (toolbox/rotate_picks.py, J6 seeded -80), then the blocks
   reordered to 3, 1, 2, 6, 5, 4 (toolbox/swap_blocks.py): picks stay outer-column-first per row (row 0 empties
   before row 1 is picked), places stay robot-side-last within each frame-1 row (A1-3 row along x, A4-6 row at the
   far end).
Expected: one J6 turn instead of five: ~-0.7 s on four PTPs = ~-2.8 s (117.5 -> ~114.7 s), violations 0.
Risks: r4 thin-box hits near the changed PTP ends (L23/L25), carried plank 5/4 passing the row-0 slots (now empty),
the rotated plank box (+-13 mm in y) under the row-0 pick transits.

Screens (all --step 2 --no-shots):
- r27d (rigid rotation + reorder): 116.0 s, r4 3 ("PTP #35 (Point25): TCP < 100 mm above plank6", same plank5/4):
  the rotated side offset of the pick transits now points at the robot, the PTPs from base A cross the thin box (L27).
- r27f (+ rotate_picks.py --mirror: transits on the outer side): 115.8 s, r4 1 ("PTP #35 (Point25): TCP < 100 mm
  above plank2"): the new PTP plank2 place -> plank6 pick starts over plank2 just released (top ~281, transit 367.5).
- r27h / r27g (+ Point38, the plank2 place transit, both uses, +15 / +20 mm): both 0 violations, 116.1 / 116.2 s.
  Scored r27g (+20, ~7 mm slack over the 380.7 limit, L01).

## Screenshots
- 00 start: plank jig (now 66 mm deep) with row 0 planks 1-3 as before and row 1 planks 4-6 standing turned ~80 deg
  (thin side toward the robot in the top view); guide on base B, frame 1 + pieces in base A; arm in home. Nothing
  floating or intersecting.
- 01 plank3 released upright in frame 1 (A3 position, far end of the A1-3 row), vertical; 5 planks in the jig.
- 02 plank1 placed next to plank3, both vertical; row 0 of the jig now holds only plank2.
- 03 plank2 placed: the A1-3 row complete (three upright); row 1 (turned planks 4-6) untouched in the jig.
- 04 plank6 placed at the far corner of frame 1 (A4-6 row), turned as the row needs, upright; arm over base A.
- 05 plank5 placed: two in the A4-6 row; plank4 alone in the jig, still upright.
- 06 plank4 placed: all six upright in frame 1, jig empty; nothing leaning.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B (same pose as iter 26), planks
  vertical, frame 1 level on top; arm reaching past the plate edge as before.
- 08 end: bench assembled in base B with the guide; base A and jig empty; arm back in home.
- topview: row-1 slots drawn turned (vertical dashes at y ~45), row 0 horizontal; pick <-> place PTP arcs group into
  two fans (A1-3 row, then A4-6 row); frame and home paths unchanged; jig clear of base A.

## Result
Expected ~-2.8 s; got 117.5 -> 116.2 s (-1.3 s): planks 89.0 -> 87.8, frame / home unchanged; joints 4084 -> 3816.
Why less: the J6 turn is gone from the row-1 PTPs, but they are now J2/J3-limited at 0.9-1.0 s (not ~0.75 s),
the one remaining turn (plank2 place -> plank6 pick, 1.52 s) stays, and the plank2 transit +20 mm costs 0.4 s.
0 violations at 2 mm; free-move clearance 41.5 mm. Jig: wall 7.9 mm at the turned slots (>= 3), 90 x 66 x 40
(< 250 mm). Kept.
Next: the planks phase is now dominated by fixed slow legs + waits (~66 s); the remaining big PTPs are
home -> plank3 (1.37 s), plank2 -> plank6 (1.52 s) and the 3.2 s return home.
