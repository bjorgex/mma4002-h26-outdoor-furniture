# iter 11: base B toward the robot, frame release on the J5 < 0 wrist branch

## Hypothesis
Change type: mixed (layout + program, one idea: re-branch the frame release). Move base B 250 mm toward the robot
(ground x 480 -> 230) so the frame release pose has a J5 < 0 IK solution (scratch/probe11.py: none at the old place,
J5 -133 at +200/+250 mm). Re-solve the release moves on that branch (toolbox/move_base_b.py, drops the flip via point
Pvia), turn the symmetric gripper 180 deg about the tool axis for all plank moves (toolbox/j6_half.py) and unwind it in
the paid lift/approach Lines before the frame grip (toolbox/j6_offsets.py) so J6 does not take over the J5 round trip,
release lift without the old pre-turn (toolbox/copy_orient.py), home re-placed on the path (home_on_path.py f 0.5).
Expected: flip 3.41 -> ~2.6 s, home trip ~-0.7 s, about -1.5 to -2 s; risk: r1 of the arm / the carried frame at base B.

## Reason
Evidence: move_times2 on the iter-10 best: flip PTPs 0.65 + 2.76 s and home PTP 2.89 s are all J5-limited; L28/L34
say the J5 round trip (-53 -> +138 -> -90, ~420 deg) is the floor at the current release place because the far
plate edge has no J5 < 0 solution. That floor is set by where base B stands, not by the move tuning of iters 05-10.
probe11 shows base B 200-250 mm closer gives a J5 < 0 release (J5 -133). Alternatives: more pre-turning in paid
Lines (iters 08-10 already took what the elbow allows, L37), shorter Lines (L33 already applied). A bold change that
removes most of a fixed J5 trip is worth more than another 0.4 s trim (AGENT.md budget note).
Principle: place the most-visited fixture where the robot is well conditioned; avoid wrist flips.

## Screening (10 mm)
- m11b (base B +200, release J5 < 0 elbow-up, planks unchanged): 108.0 s, home PTP J6 230 deg (4.6 s): J6 took over
  the round trip.
- m11g (+ planks J6 -180, unwound in the lift / frame approach Lines): 106.1 s, 4 violations: Guide/frame1 hit at the
  flip end, frame1/link_3 at the release descent, r4 x2.
- m11h (+ PTP via lifted): frame1 vs link_2/link_3 along the flip.
- m11o (elbow-down release, J3 +33): flip clean, but link_3 hits base B / guide / frame2 on the release and lift.
- m11t (base B +250, elbow-up): 105.8 s, 4 violations: Base B/Guide/frame1 + frame1/link_2 at the flip end,
  frame1/link_3 on the release descent (#67, #68), r4 home over frame1.

## Screenshots
- 00 start: base B (yellow frame 2 + guide) now at robot x ~-370..-550, close to the robot; base A, plank jig unmoved;
  the home pose has the wrist hanging over base B (arm above it, no contact visible).
- 01-06 plank releases: planks placed upright in frame 1 one by one as before; the gripper is turned 180 deg about
  its axis (camera on the other side), nothing floating or crooked.
- 07 frame released: frame 1 + planks seated in base B, but the arm is folded back over itself: the J5 < 0 wrist
  branch puts link_3/link_4 right beside and over the frame - this is the frame1/link_3 contact the score reports.
- 08 end: bench assembled in base B, arm at the new home just above it (r4 over the planks / frame).
- topview: the flip PTP is now a short swing from base A to base B across the plate centre; base B overlaps the
  previous free middle; paths otherwise as iter 10.

## Result
Expected -1.5 to -2 s, legal; got 105.8 s (-1.9 s) but 6 violations (r1 3: flip end Base B/Guide vs frame1 +
frame1/link_2, frame1/link_3 on the release descent; r4 3 incl. the new home over the planks). Rejected (not legal).
The reason held for the time: the J5 round trip is the cost and the J5 < 0 branch removes it (flip 3.41 -> 2.6 s,
home trip shorter). But it failed on geometry: at a J5 < 0 release the upper arm (link_3) sits over the carried
frame (elbow-up) or low over base B (elbow-down, tried at +200), at +200 and +250 mm alike. Making it legal would need
a different frame grip (foot grip pointing the arm away from the frame) or base B rotated - a separate iteration.
