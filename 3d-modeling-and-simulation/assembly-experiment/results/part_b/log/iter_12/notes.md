# iter 12: return guide transfer with PTPs instead of long 100 mm/s Lines

## Hypothesis
Change type: program (+ tool toolbox/guide_ptp_return.py).
Same idea as iter 11, now for the return transfer (guide base A -> base B), today ~22 s of Lines:
- approach: Point70 -> PTP Point71 (0.6) -> Line Point72 306 mm (3.1) -> Line Point15 191 mm (1.9) -> Line Point14
  350 mm down (3.5) = 9.1 s. New: PTP Point14h (Point14 flange at TCP z ZA) -> Line down to Point14.
- carry: Point73u -> Line Point11 350 up (3.5) -> Line Point74 340 across (3.4) -> PTP Point9 flip (3.6) -> Line
  Point75 280 down (2.8) = 13.3 s. New: Line up to ZB -> one PTP Point9r (move + 180 deg flip, Point9 flange at ZC)
  -> Line down to Point75.
Constraints (L13): plank release points over base A are 60 mm horizontally from the guide grip xy at TCP z 265.6, so
the PTP endpoints there need TCP z >= ~345 -> ZA = ZB = 350 (also guide bottom ~TCP-20 over plank tops ~281 -> lift
>= ~311). Over base B: ZC >= guide release 131 + 100, guide hangs ~180 below TCP during the flip over frame 2 (top
111) -> try ZC 320..355.
Expected: approach 9.1 -> ~2 (PTP) + 2.4 = ~4.4 s; carry 13.3 -> 2.4 + 3.6 + 1.4..1.7 = ~7.5 s; total ~-10 s
(cycle 202.8 -> ~193 s), violations stay 0. Risk: r1/r5 from the swinging guide vs planks/frames, r4.

Screens (10 mm): ZA 350 / ZB 350 / ZC 340 (scratch/g12a.json): 0 violations, 195.0 s, free-move clearance 31.7 mm;
ZC 300 (g12b.json): 0 violations, 194.6 s, free-move clearance 40.1 mm. Scored ZC 300.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over and flat; gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright and vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2 (yellow side up, flat in place); six planks vertical in frame 1; arm retreated
  toward the robot, clear of everything.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames; arm over the plate
  edge (same as iter 11). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: the return approach is now one dashed PTP arc from the last plank place to above the guide on base A (the
  solid lines via (-500, 0) are gone); the return carry is one dashed PTP arc base A -> base B (the other dashed arc
  from home is the outbound transfer). Only the frame-1 approach / retreat still go via (-500, 0) as Lines.

## Result
Expected ~-10 s, violations 0. Got cycle 202.8 -> 194.6 s (-8.2 s), guide phase 53.4 -> 45.2 s, other phases
unchanged, joints 8487 -> 8207 deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Slightly less than
expected (the approach PTP from the last plank place is longer than estimated). Kept.
Next: the frame-1 transfer Lines (Point76/Point77/Point78/Point79 + the 492 mm Line Point80, ~8 s; Point90/Point91
on the way home, ~4 s) as PTPs + short vertical Lines; then the frame release leg (75 -> 50.5 mm, ~-1.2 s).
