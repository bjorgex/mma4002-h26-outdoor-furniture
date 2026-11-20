# iter 04: frame lift-out PTP (Point82) -> fast Line

## Hypothesis
Change type: program.
r4: "PTP move #121 (Point82): starts/ends within 100 mm of a grip/release point; TCP < 100 mm above Base A". The PTP
starts at Point80u, only 50.5 mm above the frame grip. Point80u and Point82 have the same flange orientation
(-120, -0.06, -170), so move 121 can be a Line (100 mm/s) instead: a straight diagonal rise from TCP z 84 to 461 robot
(top of the path is far above the safe height, so no low traverse). r4 does not apply to Lines.
Expected: violations 4 -> 3 (r4 1 -> 0), no new r1/r5 (the PTP had 62 mm clearance; the line path is similar).
Cycle: +0..+2 s (the line is ~440 mm at 100 mm/s = 4.4 s; the PTP took about the same at 50 deg/s).

Revised before the 2 mm score (screens only, L06): the PTP->Line gave a new r1 Guide/frame1 and +3.7 s. A straight-up
lift has no IK above +70 mm (reach edge). A lift toward the robot (dx +60, dz +140 flange) ended within 100 mm of a
plank release point (the planks are released high, TCP z ~265). Final change: insert a fast Line Point80L after
Point80u, flange dx +30 / dz +100 (TCP ~154 mm from the frame grip, >= 109 mm from every plank release point),
keep the PTP Point82 after it (toolbox/insert_lift.py). Expected: violations 4 -> 3 (r4 0), cycle +0.5..+1 s.
10 mm screen: violations 1 (r1 0, r3 1), cycle 247.9 s (+0.9).

## Screenshots
- 00 start: plank jig between the robot and base A, 6 planks upright; guide on the raised base B; arm at home. Nothing floating.
- 01 guide released on base A: guide flat over frame 1; gripper horizontal beside base A; planks untouched in the jig.
- 02 plank3: upright through the guide into frame 1, gripper above it; 5 planks left in the jig.
- 03 plank6 / 04 plank2 / 05 plank5 / 06 plank1 / 07 plank4: one more upright plank in the guide each time, none crooked or floating; the jig empties in order; arm elbow-up over base A.
- 08 guide back on base B: guide flat over frame 2 on the riser; 6 planks upright in frame 1 on base A; gripper beside base B.
- 09 frame 1 + planks released: frame 1 turned over, planks down into frame 2 on base B; wrist at the plate edge (y ~ -230) as in iter 03. Same as before; the new lift only changes the path before the turn-over.
- 10 end: bench assembled in base B (frames top and bottom, 6 planks between), base A empty, arm at home.
- topview: same paths as iter 03 plus a short line from the frame grip (-747, 196) toward the robot before the dashed PTP; nothing new crosses a jig.

## Result
Expected violations 4 -> 3 (r4 0), cycle +0.5..+1 s. Got (2 mm): violations 3 (r1 2, r3 1, r4 0), cycle 247.9 s
(+0.9: frame 1 + planks 28.3 -> 29.2, rest unchanged), joints 9006 deg (+12). As predicted.
- r4 gone. r1 unchanged (plank1/plank2 at move 76; Base B/plank3 at the final insertion, now move 127), r3 unchanged
  (the side slide out of the foot grip after the frame release).
- Dead ends this iteration (L06): PTP->Line (new r1 Guide/frame1, +3.7 s); vertical lift (no IK > +70 mm);
  lift dx +60 / dz +140 (start within 100 mm of a plank release point).
Kept: verdict BETTER (4 -> 3), screenshots fine. Next: the frame release (Base B/plank3 contact: CAD slack in base B
pocket / guide slots, L05; the r3 side exit of the foot grip), and plank1/plank2 at the pick (move 76).
