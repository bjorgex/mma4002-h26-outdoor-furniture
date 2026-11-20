# iter 16: plank pick slow lift 60 -> 50.5 mm

## Hypothesis
Change type: program (+ tool toolbox/shorten_lift.py).
Biggest phase is planks (107.6 s). After each plank grip in the jig the arm lifts 60 mm at 20 mm/s (3.0 s), then
57.5 mm fast to the transit. r3 only needs the first 50 mm out of the grip slow. Change: the slow lift's target
(Point19, Point28, Point37, Point46, Point55, Point64) lowered to grip + 50.5 mm (L01 margin); the fast Line to the
transit gets 9.5 mm longer.
Expected per pick: -9.5/20 + 9.5/100 = -0.38 s, x6 = ~-2.3 s (cycle 185.5 -> ~183.2 s, planks 107.6 -> ~105.3).
Violations 0. Risk: r5 (fast Line clearance >= 10 mm) if the plank's lower end is still inside its jig slot at
grip + 50.5 (the 60 mm may have been chosen to clear the slot).

Screen (10 mm, scratch/l16a.json): 0 violations, 183.2 s -> scored.

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
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames; arm at the plate
  edge at the release (same as iter 15). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: identical xy paths to iter 15 (the change is a vertical split point only).

## Result
Expected ~-2.3 s, violations 0. Got cycle 185.5 -> 183.2 s (-2.3 s), planks phase 107.6 -> 105.4 s, other phases
unchanged, joints 7718 deg (same), violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: frame release slow leg 75 -> 50.5 mm (~-1.0 s, toolbox/shorten_slow.py --parts frame); guide grip lift
20 + 30.5 split / guide release legs; frame carry Line Point85 (275 mm) as a PTP.
