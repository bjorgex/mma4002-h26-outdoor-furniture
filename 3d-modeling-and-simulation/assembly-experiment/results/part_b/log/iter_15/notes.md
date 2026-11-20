# iter 15: retreat after the frame release as Line up + one PTP

## Hypothesis
Change type: program (+ tool toolbox/retreat_ptp.py).
After the frame-1 release in base B the arm goes Point88 (TCP 398.5, 50.5 mm above the release) -> Line Point90
(342 mm diagonal, 3.42 s) -> Line Point91 (70 mm, 0.70 s) -> PTP Point92 (0.58 s) -> Line Point1 (1.04 s) = 5.74 s.
Change: Point88 -> fast Line straight up to Point88h (Point87 flange + --dz) -> one PTP to the Point92 joints
(J1 20.8 -> -50.7, J5 138 -> -14.6: ~153 deg, ~3.05 s) -> Line Point1 (unchanged). Removes Point90, Point91.
Constraints (L13-L15): Point88h >= 100 mm from the release point (dz >= 100.5) and TCP >= 100 mm over the top of the
just-released bench under it (unknown, screen dz 110 / 130 / 150); Point92 is unchanged.
Expected: Line up ~0.5-1.0 s + PTP ~3.05 s instead of 4.12 s => ~-0.6 to -1.1 s (cycle 186.6 -> ~185.7 s, phase
"home" 8.8 -> ~7.9 or the frame phase). Violations 0. Risk: r1/r5 of the arm vs the bench / base B during the
J1+J5 swing, r4 box over the bench.

Screens (10 mm): dz 110 / 130 / 160: all 0 violations, 185.5 / 185.7 / 186.0 s -> scored dz 110 (Point88h TCP 458.5).

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over, flat; gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright and vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated near the robot.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames; arm over the plate
  edge at the release (same pose as iter 14). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home (same pose as at the start).
- topview: the solid diagonal Line from base B (-747, -197) to (-500, 0) is gone; a dashed PTP arc from above base B
  to Point92 (-565, 78) then the short Line home. Other paths unchanged.

## Result
Expected -0.6 to -1.1 s, violations 0. Got cycle 186.6 -> 185.5 s (-1.1 s), phase "home" 8.8 -> 7.7 s, other phases
unchanged, joints 7766 -> 7718 deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: frame release slow leg 75 -> 50.5 mm (~-1.2 s); plank pick slow lift 60 -> 50.5 mm (~-0.5 s x6); the frame
carry Line Point85 (275 mm, 2.75 s) as a PTP.
