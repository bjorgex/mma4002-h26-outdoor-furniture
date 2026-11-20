# iter 30: shorter fast lift Point80u -> Point80L after the frame-foot grip

## Hypothesis
Change type: program (+ scratch tool scratch/lift_frac.py).
After the frame-1 foot grip and the 50.5 mm slow lift, the fast diagonal Line Point80u -> Point80L (dx +30, dz +100,
104.4 mm, 1.04 s) climbs higher than r4 needs before the PTP Point82 (the flip). Ending it at a fraction f of the way
(f 0.6-0.8: TCP z ~144-164, still >= 110 mm from the grip point Point81) saves 0.2-0.4 s of Line; the PTP to Point82
gets a slightly larger J2/J3 change (+~0.05-0.15 s, currently J2 28.7 deg = 0.57 s).
Note (judge model): a Line's time is its TCP distance only, so the pure-rotation Line Point82 -> Point83 costs 0 s;
the flip sequence there is already near minimal, which is why I chose the lift instead.
Expected: -0.15 to -0.3 s (113.4 -> ~113.2 s), violations 0.
Risks: r4 box check (TCP < 100 mm above base A at the PTP start), r1/r5 of the carried frame + planks against the
guide / base A / jig on the lower, joint-interpolated PTP swing (L19), IK branch along the shortened Line (L06).

Screens (all --step 2 --no-shots, scratch/lift_frac.py): v30c f 0.8 113.2 s, v30b f 0.7 113.1 s, v30a f 0.6 113.0 s,
v30d f 0.55 (TCP z 158.7, ~106 mm from the grip point Point81) 112.9 s - all 0 violations. Scoring v30d.

## Screenshots
- 00 start: six planks upright in the plank jig (row 1 turned), guide on base B, frame 1 + pieces in base A, arm in
  home; nothing floating or intersecting - same as iter 29.
- 01 plank3 released upright in frame 1, gripper straight above it; 5 planks left in the jig.
- 02 plank1 placed beside plank3, both vertical.
- 03 plank2 placed: A1-3 row complete; row 1 untouched in the jig.
- 04 plank6 placed at the far corner, upright; arm over base A.
- 05 plank5 placed; plank4 alone in the jig, upright.
- 06 plank4 placed: all six upright in frame 1, jig empty, nothing leaning.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical, frame 1 level;
  base A and the jig empty; arm past the plate edge as in iter 29 (the change is only in the lift before the flip).
- 08 end: bench assembled in base B, arm back in home.
- topview: same paths as iter 29; the short diagonal lift out of the frame-foot grip at (-747, 196) is a little
  shorter before the dashed flip PTP; nothing else moved.

## Result
Expected -0.15 to -0.3 s; got 113.4 -> 112.9 s (-0.5 s): "frame 1 + planks" 18.8 -> 18.3 (Line Point80u -> Point80L
104.4 -> ~57 mm, -0.47 s; the PTP to Point82 still J2-limited, ~unchanged). Joints 3679 -> 3670. 0 violations at
2 mm, free-move clearance 41.5 mm. Kept.
