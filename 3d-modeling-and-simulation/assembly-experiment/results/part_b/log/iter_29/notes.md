# iter 29: frame-grip approach PTP ends further down the diagonal Line (short Line)

## Hypothesis
Change type: program (+ tool: toolbox/ptp_along.py).
The diagonal fast Line Point80h -> Point80 to the frame-1 foot grip is the longest single move left (319.5 mm,
3.2 s). Its PTP end Point80h sits at f 0.35 of the old diagonal only because the rest of the Line travelled
> 100 mm horizontally and so had to start >= 311 TCP z (L17). If the PTP ends where <= 100 mm horizontal is left
(f ~0.52 of the current Line: TCP z ~201, 98 mm horizontal, 153 mm left), the low-traverse rule no longer applies
to the Line, and r4 still holds (~198 mm from the grip point Point81). PTP Point70 -> new Point80h: max dq J4 40 deg
= 0.79 s (was 0.91), Line 1.53 s (was 3.2).
Expected: ~-1.8 s (115.8 -> ~114 s), violations 0.
Risks: r4 box check (TCP < 100 mm above frame 1 / the standing planks / base A at the new end), r5 clearance of the
lower PTP swing vs the six standing planks and the plank jig (L19: a low PTP end lowers the whole swing), r1 of the
wrist / camera.

Screens (all --step 2 --no-shots):
- u29a f 0.52 (TCP z 201): 114.0 s, r4 1 (#69 Point80h: within 100 mm of the plank4 release point; TCP < 100 mm
  above plank4). u29b f 0.60: 113.8 s, same r4. u29c f 0.68: 113.5 s, r4 "TCP < 100 mm above plank4" only.
- Cause: the PTP START Point70 sits right over plank4 (TCP 391, limit 381); the steeper descent now dips below 381
  while still inside plank4's box (L25: fix where the PTP comes from). Point70 is a Line end, so it can move.
- u29d (f 0.68 + Point70 dy +30, out of the plank boxes): 113.6 s, 0 violations; u29e (Point70 z +40 instead):
  113.9 s, 0 violations.
- u29f (f 0.76 of the original Line, TCP z 142.5, 116 mm from the grip point Point81, 77 mm Line left + Point70
  dy +30): 113.4 s, 0 violations. Scoring u29f.

## Screenshots
- 00 start: same as iter 28 - six planks upright in the plank jig (row 1 turned), guide on base B, frame 1 + pieces
  in base A, arm in home; nothing floating or intersecting.
- 01 plank3 released upright in frame 1; gripper straight above; 5 planks left in the jig.
- 02 plank1 placed next to plank3, both vertical.
- 03 plank2 placed: A1-3 row complete; row 1 untouched in the jig.
- 04 plank6 placed at the far corner, upright; arm over base A.
- 05 plank5 placed; plank4 alone in the jig, upright.
- 06 plank4 placed: all six upright in frame 1, jig empty, nothing leaning.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical, frame 1 level -
  same end pose as iter 28 (the change is only in the approach to the frame grip); arm past the plate edge as before.
- 08 end: bench assembled in base B, base A and jig empty, arm in home.
- topview: the PTP into the frame-foot grip is now a dashed arc from ~(-735, 135) curving down to ~(-710, 165), then
  a short solid Line to the foot at (-747, 196) (was a long straight diagonal from (-587, 68)); it stays over base A
  beside the plank row; all other paths unchanged.

## Result
Expected ~-1.8 s; got 115.8 -> 113.4 s (-2.4 s): "frame 1 + planks" 21.2 -> 18.8 (Line 3.2 -> 0.77 s, PTP 0.91 ->
~0.95 s, the Point70 lift Line +0.1 s; f 0.76 went further than the planned 0.52); planks and home unchanged;
joints 3709 -> 3679. 0 violations at 2 mm, free-move clearance 41.5 mm. Kept.
