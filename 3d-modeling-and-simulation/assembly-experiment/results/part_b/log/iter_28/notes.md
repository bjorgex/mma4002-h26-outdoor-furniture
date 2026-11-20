# iter 28: frame flip as one PTP onto the other wrist branch (short return home)

## Hypothesis
Change type: program (+ tool: toolbox/flip_branch.py).
The end of the cycle is set by J5: the frame is released on the J5 > 0 branch (J5 138), home/Point16 is on J5 -90,
so the return PTP Point88h -> home -> Point16 turns J5 ~228 deg (3.2 + 1.37 s). The flip before it costs a J5-only
PTP Point84 (0.57 s) + the rotating Line Point84 -> Point85 (2.75 s). L24: the flip Line can't stay on J5 < 0 (J4
hits -180) - but a PTP interpolates joints, so it has no J4 limit problem mid-way. Change: replace Point83 (0-s
Line), Point84 and the Line to Point85 by one PTP Point82 -> Point85 on the other wrist solution (J4 -133, J5 -138,
J6 220), re-solve the release Lines on that branch, home re-placed on the new Point88h -> Point16 path.
Estimate: flip PTP max dq J6 ~188 deg = 3.8 s (was 0.57 + 0 + 0.57 + 2.75 = 3.9 s), return PTP max dq J4 ~126 deg =
2.5 s (was 4.6 s): ~-2.1 s (116.2 -> ~114 s), violations 0.
Risks: the carried frame + 6 planks swept by a joint-interpolated flip (r1 vs base A/B, guide, jig, plate), r5
clearance, J6 near +270; the home PTP sweeping over the plank jig (L25).

Dropped before any screen: the release pose has no J5 < 0 solution (scratch/alt28.py, L28). J5 travel over the cycle
(-90 -> -53 -> +138 -> -90 = 456 deg) is already minimal; the home leg is pure J5.

### Revised hypothesis (scored)
Change type: program (+ tool: toolbox/line_to_ptp.py). The flip Line Point84 -> Point85 (275 mm, 2.75 s) turns J5
by only 124 deg = 2.48 s as a PTP; and its end Point85 (TCP z 468, 120 mm over the release point Point87 at 348) can
come down to TCP 451 (103 mm, r4 still holds), shortening the fast Line to Point86 from 69.5 to 52.5 mm (-0.17 s).
Expected: -0.27 - 0.17 = ~-0.45 s (116.2 -> ~115.8 s), violations 0. Risk: the joint-interpolated flip sweeps the
carried frame + planks differently (r1/r5 vs base B, the guide).
Screens (--step 2 --no-shots): q28a (PTP only) 116.0 s, 0 violations; q28b (+ z 451) 115.8 s, 0 violations. Scoring q28b.

## Screenshots
- 00 start: same as iter 27 - six planks upright in the jig (row 1 turned), guide on base B, frame 1 + pieces in
  base A, arm in home; nothing floating or intersecting.
- 01 plank3 released upright in frame 1; gripper above; 5 planks left in the jig.
- 02 plank1 placed beside plank3, both vertical.
- 03 plank2 placed: A1-3 row complete, row 1 untouched in the jig.
- 04 plank6 placed at the far corner (A4-6 row), upright; arm over base A.
- 05 plank5 placed; plank4 alone in the jig, upright.
- 06 plank4 placed: all six upright in frame 1, jig empty.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical, frame 1 level on
  top - same end pose as iter 27 (the PTP changes only the path, not the release pose); arm past the plate edge.
- 08 end: bench assembled in base B, base A and jig empty, arm in home.
- topview: unchanged except the flip segment from the plate middle to the base B release: now a dashed (PTP) arc
  instead of a straight line, staying over the plate / base B corner area; plank paths unchanged.

## Result
Expected ~-0.45 s; got 116.2 -> 115.8 s (-0.4 s): "frame 1 + planks" 21.6 -> 21.2, planks and home unchanged;
joints 3816 -> 3709. 0 violations at 2 mm, free-move clearance 41.5 mm. Kept.
Next: remaining end-of-cycle time is J5-bound (L28); Point88h (TCP 458) could drop to ~451 (-0.07 s); bigger gains
need a different frame grip / release pose (J5 138 at the release).
