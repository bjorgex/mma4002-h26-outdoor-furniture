# iter 22: plank transits offset sideways out of the plank's thin xy box, lowered to event + 102

## Hypothesis
Change type: program (+ tool toolbox/side_transit.py).
Each plank pick/place has 4 fast 67 mm Lines (transit <-> slow start), 24 x 0.67 s = 16 s. The transits sit at event
+ 117.5 only because they are straight over the plank, so r4's box check needs TCP >= plank top + 100 (L14/L15). The
plank's xy box is only ~5 mm thick (jig: y 72.3..77.4). Offset every plank transit 10 mm along the plank's thin axis
(out of its box, not into a neighbour's) and lower it to event + 102: then only the 100 mm sphere around grip/release
points binds (sqrt(10^2 + 102^2) = 102.5 >= 100, neighbours >= 30 mm away). The fast Line becomes a short diagonal
(~52.5 mm, < 100 mm horizontal), the last 50.5 mm stay vertical.
Expected: 67 -> 52.5 mm per leg, -0.145 s x 24 = ~-3.5 s (cycle 175.0 -> ~171.5 s, planks phase). Violations 0.
Risk: PTP samples near the ends passing over the plank box below top + 100 (L15, 2 mm only), carried plank bottoms
15 mm lower in the transfer PTPs (L07), r5 of the open fingers over neighbouring plank tops.

Screens (10 mm): a (picks -y, releases +x/+y) 0 violations 171.7 s; b (picks +y, releases -x/-y) 0, 171.5 s.
First 2 mm score (b): r4 3 (PTP #16/#38/#60 "TCP < 100 mm above plank3/6/5": the curved PTP crosses the 5 mm box
near its end/start, L22 = L15 again). Screened a at --step 2: 0 violations, so a was installed and scored.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over, flat; gripper at the grip pocket; planks still in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright, vertical; gripper clear above (no longer exactly over the plank: side offset).
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated near the robot.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames, frame 1 level on top;
  arm at the plate edge. Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: plank transfer PTPs now end 10 mm beside the pick / place points (small diagonal stubs at the jig and over
  base A); guide and frame paths unchanged.

## Result
Expected ~-3.5 s. Got cycle 175.0 -> 171.7 s (-3.3 s), planks phase 100.0 -> 96.6 s, others unchanged, joints
7410 -> 7157 deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept. Variant b (other sign) was 0.2 s
faster but fails r4 at 2 mm. Next: the same side-offset idea for other transits (guide over base A Point14h/Point15v,
frame release Point88h), and a slightly smaller dz (sphere margin now 2.5 mm).
