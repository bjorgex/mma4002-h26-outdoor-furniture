# iter 06: turn the gripper toward the row-2 pick during the slow release leg after plank2

## Hypothesis
Change type: program. The empty return Line #26 Point41 -> Point26 (plank2 placed -> plank6 pick) moves 112.5 mm
but turns the tool 80 deg, so it is rotation-limited: 1.60 s instead of 1.125 s. The slow release leg before it
(#25 Point40 -> Point41, 50.5 mm at 20 mm/s = 2.53 s) has spare rotation capacity (2.53 s x 50 deg/s). Split that leg:
first K mm purely vertical (fingers clear plank2's top), then the rest of the leg vertical but turning part of the 80
deg (new tool toolbox/split_rot.py). The TCP path stays vertical above the release point (r3 only checks TCP x/y and
speed), the leg's time stays distance-limited as long as the turn fits. Expected: -0.4 to -0.47 s (planks 84.4 ->
~84.0), 0 violations. Risk: r1 fingers vs plank2 / plank1 (neighbour, same row) while turning near their tops; r2
J4/J6 along the turning Line.

## Reason
Evidence: toolbox/move_times2.py on the iter-05 best lists exactly one ROT-LIMITED move: #26 (d 112.5 mm, rot 80
deg, 1.60 s, 0.475 s over its distance time). The slow legs (~2.5 s each, ~60 s of the cycle) are fixed by r3 and
cannot be shortened, but nothing forbids them doing useful re-orientation at the same time: rotation about the
vertical tool axis keeps the TCP path vertical.
Alternatives considered: (a) hybrid Line/PTP row-2 transfers (iter 04 "next"): the vertical r4 leg is already the
shortest way out of the 100 mm sphere, so a hybrid only shortens the PTP a little (~0.1 s each, 4 r4-sensitive
edits); (b) frame approach Point80h closer to the grip (~0.2 s, L29 territory); (c) dropping the home return (3.2 s)
would game the judge (a cell cycle must return to start). This one is a single, local, cheap-to-screen edit with the
largest remaining per-move slack. Principle: overlap motion with fixed-cost events (do the re-orientation inside an
already-paid slow leg).

## Screening (before the score)
toolbox/split_rot.py on step 31 (Point41), 2 mm screens: K 30 / G 0.5 (40 deg in the last 20.5 mm), K 40 / G 0.32,
K 20 / G 0.5: all 109.4 s, 0 violations. Scored K 30 / G 0.5 (fingers 15 mm above plank2's top before turning).

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig; arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, gripper above it; 5 planks in the jig.
- 02 plank1 released: two planks upright in frame 1, 4 in the jig; normal elbow-up pose.
- 03 plank2 released (the changed leg follows): y-124 row of 3 planks upright and straight, gripper above plank2; neighbours untouched.
- 04 plank6 released: 4 planks in frame 1, 2 left in the jig, upright; nothing knocked by the turning gripper.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig.
- 06 plank4 released: all 6 planks upright in frame 1, jig empty.
- 07 frame released: frame 1 + planks turned over, seated through the guide into frame 2 on base B; arm reaching over the -y edge as before.
- 08 end: bench assembled in base B, arm at home; base A and plank jig empty.
- topview: paths as in iter 05 (the change is a vertical leg, invisible from above); nothing new crosses the plate.

## Result
Expected -0.4 to -0.47 s, got 109.9 -> 109.4 s (-0.5 s), 0 violations. Phase planks 84.4 -> 83.9 s, frame / home
unchanged, joint travel unchanged (2799 deg), 70 -> 71 moves. The reason held: #26 was 0.475 s over its distance
time purely from rotation, and the slow release leg had room to do 40 deg of it without getting slower; fingers
15 mm above the plank tops before the turn cleared everything (r1 0, free-move clearance 41.5 mm). Kept.
Next: same trick for the J6-limited PTP Point80h (0.99 s, 49 deg J6) - pre-turn during the slow release leg after
plank4 (#54); and look for other PTPs whose limiting joint is J6 next to a slow leg.
