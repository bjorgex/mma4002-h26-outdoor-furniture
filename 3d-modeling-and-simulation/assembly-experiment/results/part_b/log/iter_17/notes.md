# iter 17: frame release slow leg 75 -> 50.5 mm

## Hypothesis
Change type: program (tool toolbox/shorten_slow.py, unchanged, --parts frame).
The frame-1 + planks insertion into base B ends with a fast Line Point86 (45 mm) and a slow vertical Line Point87
(75 mm at 20 mm/s, 3.75 s) to the release. r3 needs only the last 50 mm slow. Change: Point86 lowered 24.5 mm so the
slow leg is 50.5 mm (L01 margin).
Expected: -24.5/20 + 24.5/100 = -0.98 s (cycle 183.2 -> ~182.2 s, phase "frame 1 + planks" 24.9 -> ~23.9).
Violations 0. Risk: r5 (fast Line clearance >= 10 mm) / r1 if the plank ends are already entering the guide slots /
frame 2 within the last 75 mm (the 75 mm may have covered the insertion through the guide).

Screen (10 mm, scratch/f17a.json): 0 violations, 182.2 s -> scored.

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
  top; arm at the plate edge at the release (same pose as iter 16). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: same xy paths as iter 16 (the change is a vertical split point only).

## Result
Expected -0.98 s, violations 0. Got cycle 183.2 -> 182.2 s (-1.0 s), phase "frame 1 + planks" 24.9 -> 23.9 s, other
phases unchanged, joints 7718 deg (same; the 10 mm screen showed 7691 - a sampling artefact), violations 0 at 2 mm
(free-move clearance min 33.3 mm). Kept.
Next: frame carry Line Point85 (275 mm, 2.75 s) + Point86 as a PTP (L13-L15 checks); guide carry Line Point11r
(239 mm up) partly as PTP; plank place slow legs/transits.
