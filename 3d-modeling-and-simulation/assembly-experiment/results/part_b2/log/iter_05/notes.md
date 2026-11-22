# iter 05: frame flip as one joint move (drop Point82 / Line Point83 / J5-only Point84)

## Hypothesis
Change type: program. After the frame-foot grip and lift (Point80L), the program goes PTP Point82 (0.61 s) ->
rotation-limited Line Point83 (0.80 s) -> J5-only PTP Point84 (0.57 s) -> PTP Point85 (2.48 s) = 4.46 s. Replace the
three intermediate moves with one PTP Point80L -> Point85 (toolbox/drop_move.py 77 78 79). The judge allows a J5 sign
change inside a PTP (kin_check: "allowed in a joint move"); J5 goes -53.8 -> +138.1 = 192 deg = 3.84 s at 50 deg/s.
Expected: -0.6 s (frame phase 19.3 -> 18.7), 0 violations. Risk: the joint-interpolated swing carries frame 1 + 6
planks from a low start (TCP 139) without the high via point (TCP 461) -> r1/r5 vs base B / guide / base A.

## Reason
Evidence: toolbox/move_times2.py on the iter-04 best: the frame flip Point80L -> Point85 costs 4.46 s, but the J5
change it needs (-53.8 -> +138.1, 192 deg) sets a floor of 3.84 s; the intermediate via points (high Point82, the
re-orienting Line, the v3 "J5-only flip" convention) add ~0.6 s above that floor. The J5-only flip is v3's convention,
not a judge rule (kin_check counts PTP J5 sign changes as allowed; only J5 sign changes along Lines fail).
Alternatives checked first: (a) run the whole cycle on the J5 > 0 wrist branch (would remove ~290 deg of J5 travel,
~3-5 s): scratch/alt28.py shows the frame-foot grip Point81 has no J5 > 0 solution near J1 -36 (only J1 -200) and
the outer plank place Point31 none either, so it is impossible (L34). (b) keep Point82 and drop only Point83/84:
10 mm screen 110.4 s (-0.1 s). (c) hybrid Lines for the four long row-2 plank transfers (~-0.8 s, but 4 separate
r4-sensitive edits). Dropping all three via points is a one-line change with the largest gain per edit;
10 mm screen: 109.9 s, 0 violations, free-move clearance 48.7 mm.
First 2 mm score of the plain drop: r4 1 (TCP < 100 mm above Base A on the new PTP; L35). Fix within the same change:
a joint-space via point on the path (toolbox/ptp_via.py, f 0.3, J2 -45, J3 -20) lifts the swing; J5 still limits
both halves (57.6 + 134.3 deg), so no time is added. 2 mm screens: f 0.3 and f 0.4 variants both 0 violations,
109.9 s; scored f 0.3 (less joint travel).
Principle: fewer moves / shortest joint path; the slowest joint (J5) sets the move time, so via points that do not
shorten J5 travel are pure cost.

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig; arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, gripper above it; 5 planks in the jig.
- 02 plank1 released: two planks upright in frame 1, 4 in the jig; normal elbow-up pose.
- 03 plank2 released: y-124 row of frame 1 full; the 3 turned planks remain in the jig.
- 04 plank6 released: 4 planks upright in frame 1, 2 in the jig.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig, upright.
- 06 plank4 released: all 6 planks in frame 1, jig empty, nothing crooked.
- 07 frame released: frame 1 + planks turned over and seated through the guide into frame 2 on base B, planks vertical; arm reaching over the -y edge (same release pose as before - only the path to it changed).
- 08 end: bench assembled in base B, arm back at home; base A and the plank jig empty.
- topview: plank paths unchanged; the frame flip is now one dashed arc from the frame foot (top left) bulging out past the plate's -x edge (the lifted via, TCP z 634) and down to the release at y -197; the old via Point82 near the plate centre is gone. Table collision checked by r1 (0).

## Result
Expected -0.6 s, got 110.5 -> 109.9 s (-0.6 s), 0 violations (after the via-point fix for the r4 hit, L35). Phase
frame 19.3 -> 18.7 s, planks / home unchanged; joint travel 3029 -> 2799 deg, 72 -> 70 moves. The reason held: the
flip was ~0.6 s above its J5 floor, and the J5-only flip was a convention, not a rule; via points cost nothing as long
as they keep J5 the limiting joint. Kept.
Next: the home leg (Point88h -> Point1 -> Point16, 4.57 s) is at its J5 floor; the remaining frame-phase slack is
the grip approach (Point70 Line + Point80h PTP + 76.7 mm Line) and the lift (Point80u + Point80L); the four long
row-2 plank transfers (hybrid Line/PTP, ~-0.8 s) are still open.
