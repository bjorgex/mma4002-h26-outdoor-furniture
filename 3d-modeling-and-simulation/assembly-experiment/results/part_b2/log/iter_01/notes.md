# iter 01: drop the rotation-limited Line Point65 -> Point70, PTP straight from Point65 to Point80h

## Hypothesis
Change type: program. Remove move #68 (Line Point65 -> Point70, the move after the plank4 place transit) so the
frame-approach PTP #69 starts at Point65 and goes straight to Point80h. Expected: -1.1 s (Line 1.52 s + PTP 0.78 s
= 2.30 s replaced by one PTP whose largest joint change is J6 56.8 deg = 1.14 s), 0 violations. Risk: r4 "TCP < 100 mm
above plank3/plank4" near the PTP start (L29: Point70 was moved out of the plank boxes for that reason) and wrist
vs the standing planks in frame 1 (L19).

## Reason
Evidence: with the B2 judge (Line time = max(dist/speed, rot/50 deg/s)), toolbox/move_times2.py shows only two
rotation-limited Lines; #68 Point65 -> Point70 is the bigger one: 39 mm but 76 deg of tool rotation = 1.52 s
(was 0.39 s under run B's judge), plus the PTP Point70 -> Point80h 0.78 s. A Line that mainly re-orients is now
the most expensive way to re-orient; a PTP spreads the re-orientation over joints that move in parallel. Joint
deltas Point65 -> Point80h: J1 18.6, J2 25.5, J3 4.9, J4 30.8, J5 36.8, J6 56.8 -> 1.14 s.
Alternatives: (a) make #68 a PTP (J5 74.5 deg = 1.49 s, no gain); (b) split the rotation between the Line and the
PTP (~-0.8 s, keeps an extra move); (c) merge the flip moves Point82/83/84 (-0.6 s, but crosses J5 = 0 in a
non-J5-only move, more risk). The direct PTP is the largest, simplest saving; it is tried first, (b) is the
fallback if r4 fires near plank3/plank4.
Principle: shortest route / fewest moves; avoid paying for re-orientation in a TCP-speed-limited Line.

## Screening (before the score)
- Direct PTP Point65 -> Point80h (scratch/a01.json): 113.7 s but r4 1 "PTP #68 (Point80h): TCP < 100 mm above
  plank3" (L29 again, see L31). Dropped.
- Fallback (b), toolbox/partial_rot.py: Point70 keeps its position, its orientation = slerp(Point65, Point70, f).
  2 mm screens: f 0 -> 114.1 s, 0 violations; f 0.25 -> 113.9 s, 0 violations (Line 19 deg = 0.39 s, PTP 49 deg
  J6 = 0.99 s). Scored: f 0.25. Revised expectation: -1.0 s.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (raised riser), 6 planks upright in the plank jig; arm at home over base B, nothing floating.
- 01 plank3 released: plank3 standing in frame 1 (outer slot), 5 planks in the jig; gripper raised over base A.
- 02 plank1 released: two planks in frame 1, upright, side by side; 4 left in the jig.
- 03 plank2 released: the y-124 row of frame 1 full (3 planks); jig holds the 3 turned planks.
- 04 plank6 released: 4 planks in frame 1, upright; the arm over base A in a normal elbow-up pose.
- 05 plank5 released: 5 planks in frame 1; one plank (plank4) left in the jig.
- 06 plank4 released: all 6 planks in frame 1, jig empty; gripper at the place transit (the changed move follows this).
- 07 frame released: frame 1 + planks turned over and seated in the guide / frame 2 on base B, planks vertical, nothing crooked; arm reaching over the -y edge (as in iter 00).
- 08 end: bench assembled in base B, arm back at home; base A and the plank jig empty.
- topview: same paths as iter 00 except the short Line after the plank4 place transit now carries less rotation; the frame-approach PTP (purple) still leaves the y-124 plank row before descending to the foot grip.

## Result
Expected -1.0 s (revised after screening; first idea -1.1 s), got 114.9 -> 113.9 s (-1.0 s), 0 violations. Phase
"frame 1 + planks" 20.2 -> 19.3 s (the Line + PTP into the frame grip), other phases unchanged; joint travel
3670 -> 3485 deg. The reason held: the Line was rotation-limited (76 deg = 1.52 s) and moving 3/4 of its rotation
into the following PTP, which runs it in parallel with the other joints, removed ~1 s. The first form (dropping the
Line) failed on r4 as L29 predicted - the Line also carries the TCP out of the plank boxes. Kept.
Next: the other rotation-limited Line, #77 Point83 (40 deg, 0.8 s, pure re-orientation inside the frame flip).
