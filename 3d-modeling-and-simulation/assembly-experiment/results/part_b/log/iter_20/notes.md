# iter 20: guide return grip at J6 +180 (short way from plank4), lift Point11r higher so the opposite flip clears

## Hypothesis
Change type: program (tools: toolbox/j6_wrap.py, toolbox/set_ptp_z.py, no new tool).
#83 Point70 -> Point14h (to the guide on base A) is the longest PTP: J6 52 -> -180 = 232 deg, 4.65 s. With J6
+360 for Point14h .. Point11r (guide grip at +180) it is 128 deg (~2.6 s; J4 64, J5 60 next). w19b showed the
return flip Point11r -> Point9r (+180 -> 0) then turns the guide the other way and hits plank6 (r1 Guide/plank6 at
#89). Change: same wrap + Point11r (end of the vertical lift with the guide) raised by DZ so the reversed flip passes
over the plank tops. Cost: Line #88 +DZ/100 s, PTP #89 unchanged unless J2/J3 grow past 180 deg of J6.
Expected: -2.1 s (#83) + DZ/100 s (#88) => with DZ ~100: ~-1.1 s (cycle 176.9 -> ~175.8 s, guide phase). Violations
0. Risk: the guide still sweeps the planks (needs larger DZ, gain gone), r1/r5 of link_6 vs the plate.

Screens (10 mm, Point11r flange z, was 350): 375 (x20d) r1 Guide/plank6 at #89 (still sweeps the planks); 400
(x20c) 0 violations, 175.3 s; 450 (x20b) 0, 175.8 s. Scored 410 (10 mm slack over the 400 screen, L03).

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over, flat; gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright and vertical in the guide; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat (same pose as iter 19 despite the reversed return flip); six planks
  vertical in frame 1; arm retreated near the robot.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames, frame 1 level on
  top; arm at the plate edge at the release. Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: same TCP xy paths as iter 19 (the change is J6 and a higher vertical lift over base A, not visible in xy).

## Result
Expected ~-1.1 s (DZ 100) / ~-1.5 s (DZ 60). Got cycle 176.9 -> 175.4 s (-1.5 s), guide phase 45.2 -> 43.7 s,
others unchanged, joints 7462 -> 7392 deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: the remaining long moves are the frame carry Line Point85 (275 mm, 2.75 s), Point80 diagonal (3.2 s), the
guide Lines over base A (#11, #15, #84 ~2.4 s each) and PTP #10/#89 (3.6 s, J6 180 flip - fixed by the guide turn).
