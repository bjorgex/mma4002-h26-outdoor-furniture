# iter 23: guide-grip transits over base A (Point15v, Point14h) offset sideways and lowered

## Hypothesis
Change type: program (existing tool toolbox/set_ptp_xyz.py).
After releasing the guide on base A the arm climbs a vertical 243.5 mm Line (#15 Point14u -> Point15v, TCP z 355),
and before picking it up again it drops a 238.7 mm Line (#84 Point14h, TCP z 350 -> Point14). They are that high
only because the plank release points over base A (Point40 etc., TCP z 265) are 60 mm away horizontally (r4 sphere).
Point11h (iter 21) already sits 40/40 mm sideways (dx +40, dy +40 flange), 117 mm from every plank release point, so
r4 holds at any z there. Move Point15v and Point14h to the same xy and lower them (screen z 310 / 280 / 250 TCP-ish).
The fast Lines become short diagonals (< 100 mm horizontal), last 50.5 mm stay vertical.
Expected: 2 x (239 -> ~150..180 mm) = -1.2..-1.8 s (guide and planks phases), violations 0.
Risk: the PTP Point15v -> Point16 swing passes over the plank jig lower (L19/L21, but no guide held now); the
PTP Point70 -> Point14h passes over the standing planks (top 281) lower; r5 of the fingers vs the guide on the
diagonal leg.

Screens (all --step 2 --no-shots, L22):
- a: both 40/40 sideways, z 250: r4 1 (PTP #16 Point16 "TCP < 100 mm above plank6"), 169.7 s.
- b: both 40/40, z 290: same r4 1, 170.4 s. e: Point14h 250 + Point15v 40/40 z 330: same r4 1. So the dx +40 of
  Point15v bends the PTP to the plank3 pick over plank6's thin box, whatever the z.
- c: Point14h only 40/40 z 250: 0, 170.8 s. d: Point14h 40/40 z 200: 0, 170.4 s. f: z 160: r4 1 (#83 over plank3).
- g = d + Point15v dy +40 only (dx 0), flange z 320: 0 violations, 170.0 s -> installed and scored.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the jig, arm home.
- 01 guide released on base A over frame 1, flat; gripper still at the grip pocket (horizontal tool), planks in jig.
- 02 plank3 upright in the guide over frame 1, gripper just above it; 5 planks in the jig.
- 03 plank6 placed: two upright, vertical; gripper clear above, nothing tilted.
- 04 plank1 placed: three upright, three in the jig.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty, gripper above.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated toward the robot.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames, frame 1 level on top;
  arm at the plate edge. Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home (same as iter 22).
- topview: new corner at (-574, 210) for the drop to the guide grip (diagonal stub) and at (-614, 210) for the climb
  after the release; other paths unchanged.

## Result
Expected -1.2..-1.8 s. Got 171.7 -> 170.0 s (-1.7 s): guide 43.4 -> 42.1 (Point14h drop 239 -> ~110 mm diagonal),
planks 96.6 -> 96.2 (Point15v climb 244 -> ~214 mm). Joints 7157 -> 7107 deg. Violations 0 at 2 mm, free-move
clearance 33.3 mm. Kept. Point15v cannot move in x (PTP to the plank3 pick then crosses plank6's box); Point14h floor
~200 (160 crosses plank3's box over base A).
