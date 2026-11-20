# iter 19: J6 unwrapped +360 deg from the guide flip to the plank6 pick and over the guide return

## Hypothesis (first idea, dropped at screen)
Lower PTP Point11h (guide carry end over base A) from TCP 355 into the r4 window below the plank release points
(173 / 182) to cut the 244 mm Line down. 10 mm screens: r1 link_4/link_5 vs plank1..5 in the plank jig (the wrist
drops mid-swing); same idea for Point14h: r1 EGP/plank2 + r4 over plank1. Dropped (L19), nothing scored.

## Hypothesis
Change type: program (+ tool toolbox/j6_wrap.py).
Per-move times show two long PTPs set by J6 alone: #33 Point25 -> Point29 (plank6 pick -> place) J6 -202 -> 87 =
289 deg, 5.80 s; #83 Point70 -> Point14h (to the guide on base A) J6 52 -> -180 = 232 deg, 4.65 s. J6 is +-270, so
the same poses can be reached with J6 + 360. Change: J6 + 360 for Point11h .. Point25 (guide flip ends at +180
instead of -180, plank3 pick/place and the plank6 pick at ~154..160) and for Point14h .. Point11r (guide grip on
base A at +180). Poses unchanged; the guide flips the other way round the tool axis (J6 0 -> +180 instead of -180),
same 180 deg. Moves: #10 Point11h J6 delta 180 (same), #16 Point16 26 (same), #33 289 -> 71 (other joints up to
64 deg -> ~1.3 s), #83 232 -> 128 (~2.6 s), #89 Point9r 180 (same).
Expected: -4.5 s (#33) -2.1 s (#83) = ~-6.6 s (cycle 181.2 -> ~174.6 s; planks phase 104.4 -> ~99.9, guide phase
-2.1 if #83 is counted there). Violations 0. Risk: r1/r5 of the camera (link_6) / gripper vs the plate or base A
during the opposite flip direction (L04), and the reverse sweep of the carried guide.

Screens (10 mm): w19a (Point11h .. Point25 +360 only): 0 violations, 176.9 s. w19b (+ Point14h .. Point11r +360):
174.8 s but r1 Guide/plank6 at #89 Point9r: the return flip +180 -> 0 now turns the guide the other way, into the
standing planks; the old direction would need J6 +360 at base B (> 270). Scored w19a only.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over, flat (same pose as iter 18 despite the opposite flip
  direction); gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed (the changed move): two upright and vertical in the outer guide row; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated near the robot.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames, frame 1 level on
  top; arm at the plate edge at the release (same as iter 18). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: same TCP paths as iter 18 (only the wrist angle changed; the plank6 PTP arc to (-748, 44) is shorter
  in time, not in xy).

## Result
Expected ~-6.6 s (both parts); the return part failed at screen, so expected for the scored part ~-4.5 s.
Got cycle 181.2 -> 176.9 s (-4.3 s), planks phase 104.4 -> 100.0 s, other phases unchanged, joints 7680 -> 7462 deg,
violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: #83 Point70 -> Point14h (232 deg J6, 4.65 s): the guide return flip direction is fixed by plank6 (w19b);
options: lift the guide higher before the flip at Point11r/Point9r so the opposite flip clears the planks, or
re-grip the guide on base A from the other side; also check other long PTPs with scratch/j6_list.py.
