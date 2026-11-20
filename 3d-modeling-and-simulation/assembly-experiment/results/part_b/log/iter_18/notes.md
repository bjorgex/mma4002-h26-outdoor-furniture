# iter 18: lift after the guide release on base A as a short vertical Line + the existing PTP

## Hypothesis
Change type: program (+ tool toolbox/lift_ptp.py).
After the guide release on base A the arm does Point14u (TCP z 111.5) -> fast Line Point15 (350 mm diagonal up to TCP
z 461, 3.50 s) -> PTP Point16 (2.64 s) over the first plank pick. The 461 mm height is a leftover of the v3 route.
Change: Point15 replaced by Point15v = the Point14u flange straight up to TCP z ZV, then the same PTP Point16
(unchanged joints).
Constraints (L13-L15): Point15v >= 100 mm from every grip/release point: the nearest plank release point (-653, 124,
265.6) is 60 mm away horizontally -> TCP z >= ~346 -> ZV 355 (108 mm); TCP well above the guide top; the PTP travels
> 100 mm and ends at 363 (>= 311). Risk: r1/r5 of the wrist vs the planks in the jig during the PTP (its start is
106 mm lower than before).
Expected: Line 3.50 -> ~2.44 s, PTP ~2.6 s (similar joint delta) => ~-1.0 s (cycle 182.2 -> ~181.2 s, guide phase or
planks phase -1.0). Violations 0.

Screens (10 mm): ZV 355 (scratch/p18a.json) 0 violations, 181.2 s; ZV 380 (p18b) 0 violations, 181.5 s. Scored 355.

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
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames, frame 1 level on
  top; arm at the plate edge at the release (same as iter 17). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: the first PTP arc to the plank jig now starts straight above the guide grip on base A (-614, 170); the
  old solid diagonal Line toward (-589, 170) up to z 461 is gone. Other paths unchanged.

## Result
Expected ~-1.0 s, violations 0. Got cycle 182.2 -> 181.2 s (-1.0 s), planks phase 105.4 -> 104.4 s, other phases
unchanged, joints 7718 -> 7680 deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: guide return approach PTP Point14h + Line 239 mm down (Point14, 2.4 s) and carry Line Point11r 239 mm up:
lower the PTP end points as far as r4 allows (plank release points 60 mm away horizontally -> TCP >= ~346, then
the placed planks' tops 281 + 100 = 381 if the PTP passes over them); frame carry Line Point85 (275 mm) as a PTP.
