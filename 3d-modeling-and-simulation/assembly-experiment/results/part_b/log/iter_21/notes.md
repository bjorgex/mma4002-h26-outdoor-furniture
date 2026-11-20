# iter 21: guide placement on base A: PTP end Point11h offset sideways and lower, short diagonal Line down

## Hypothesis
Change type: program (+ tool toolbox/set_ptp_xyz.py).
#11 Line Point11h -> Point12 drops the carried guide 244 mm straight down (2.44 s). Point11h sits straight over the
grip pocket at TCP 355 only because the nearest plank release point (-653, 124, 265.6) is 60 mm away horizontally
(r4 needs >= 100 mm, L13). Lowering it straight down failed (L19: wrist mid-swing into the plank jig).
Change: put Point11h off to the side, away from the plank release points (+x toward the robot, +y), e.g. dx = dy =
+40 mm (117 mm horizontally from the nearest release point, so r4's 100 mm sphere holds at any z) and lower (TCP z
~260-320); the Line into Point12 becomes a short diagonal (< 100 mm horizontal, so no 311 rule), the last 50.5 mm
stay vertical. Same orientation, so the PTP joint delta (J6 180 flip, 3.6 s) is unchanged.
Expected: Line 244 -> ~160 mm => ~-0.8 s (cycle 175.4 -> ~174.6 s, guide phase). Violations 0. Risk: r4 "TCP < 100 mm
above" frame 1 / base A under the new end, r1/r5 wrist vs the plank jig mid-swing with a lower end (L19), the
carried guide vs frame 1 pieces on the diagonal.

Screens (10 mm, dx/dy offset, flange z): (40, 40, 260) r1 link_5 vs plank1..5 in the jig at #10; (40, 40, 290) same;
(60, 60, 290) same; (60, 0, 280) EGP/plank3 + link_5; (0, 60, 280) link_5; (40, 40, 300) 0 violations, 174.9 s.
r4 is solved by the side offset, but the wrist floor of L19 (~300 flange z) stays. Scored (40, 40, 310) for slack (L03).

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over and flat; gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright and vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated near the robot.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames, frame 1 level on top;
  arm at the plate edge at the release. Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: the outbound guide PTP now ends at (-574, 210) (inside the plate, y < 220) and a short diagonal Line
  goes to the grip pocket over base A; other paths unchanged.

## Result
Expected ~-0.8 s (z 260); at the scored z 310 ~-0.45 s. Got cycle 175.4 -> 175.0 s (-0.4 s), guide phase 43.7 -> 43.4,
others unchanged, joints 7392 -> 7410 deg (J1 now swings 62 deg in the PTP instead of 53), violations 0 at 2 mm
(free-move clearance min 33.3 mm). Kept. The lower window is blocked by the wrist over the plank jig, not r4.
Next: the same side offset for the return PTP Point14h (+ Line Point14 239 mm down) and the lift Point11r (410)
- the return passes over the standing planks (top 281) so its floor is ~381+; the guide release lift Point15v (355).
