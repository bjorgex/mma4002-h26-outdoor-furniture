# iter 14: frame-1 approach with one PTP + vertical Line instead of the Lines via (-500, 0)

## Hypothesis
Change type: program (+ tool toolbox/frame_ptp.py).
After the guide release on base B the arm goes Point6u (TCP z 181) -> Line Point5 (281 mm up, 2.8 s) -> Line
Point76 (191 mm, 1.9 s) -> Point77 (0) -> PTP Point78 (0.6) -> PTP Point79 (1.3) -> Line Point80 (492 mm diagonal
down to the frame-foot grip + 60, 4.9 s) = 11.5 s.
Change: Line up from Point6u to TCP z ZA (new Point6h), one PTP to Point80h (Point80 flange at TCP z ZB), fast Line
straight down to Point80 (unchanged slow legs after it). Constraints (L13-L15): PTP ends >= 100 mm from all
grip/release points (plank4 release is 93 mm horizontally from the foot grip -> ZB >= ~310), >= 100 mm over unheld
parts under the TCP (plank tops 281 -> ZB >= 381 if the foot is inside a plank box), max TCP z >= 311 (low
traverse), ZA >= guide top + 100.
Expected: ZA ~330: up 1.5 s; PTP ~2.5 s; down ~3 s => ~7 s, i.e. -4 to -5 s (cycle 190.8 -> ~186.5 s, phase
"frame 1 + planks" 29.2 -> ~25). Violations 0. Risk: r1/r5 of the gripper / camera vs plank tops and frame 1 during
the vertical descent at the foot (the old path came in diagonally from the robot side), IK branch at ZB.

Screens / scores:
- vertical approach at the foot: no IK at flange z 385 (L16 = L06 again). Changed the tool: the PTP ends at fraction
  f along the old diagonal Line Point79 -> Point80 (same tilted orientation), the rest of that Line stays.
- za 330 / f 0.35 (10 mm): clean, 187.1 s. za 300 / f 0.4 and za 320 / f 0.5: r3 low traverse on the remaining Line
  (start < 311, L17) + r4 near. za 300 / f 0.38: r4 near (a plank release point). za 280 / f 0.35: clean, 186.6 s
  -> scored.
- The PTP Point6v -> Point80h now includes the J5 sign change (97.8 -> -52.8 deg, 3.0 s): wrist_flips is a metric,
  not a rule; before, it was done in the small PTPs Point78/Point79.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over, flat; gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright and vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated over the plate near the
  robot, clear of everything (unchanged state - the change starts right after this release).
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames; arm over the plate
  edge (same as iter 13). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: the solid Lines base B -> (-500, 0) and the small PTPs around (-450, -60) are gone; instead a dashed PTP
  arc from above base B (-614, -170) up to the diagonal at ~(-615, 70) and the remaining solid diagonal to the foot
  (-747, 196). Other paths unchanged.

## Result
Expected -4 to -5 s, violations 0. Got cycle 190.8 -> 186.6 s (-4.2 s), phase "frame 1 + planks" 29.2 -> 24.9 s,
other phases unchanged, joints 8085 -> 7766 deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: the retreat after the frame release (Point88 -> Line Point90 342 mm -> Point91 -> PTP Point92 -> Line Point1,
~5.7 s) as Line up + one PTP home (~-2.5 s); frame release slow leg 75 -> 50.5 mm (~-1.2 s); plank pick slow lift
60 -> 50.5 mm.
