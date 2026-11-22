# iter 28: shrink the r3 slow-leg margin from 0.5 mm to 0.1 mm (50.5 -> 50.1 mm legs)

## Hypothesis
Change type: program (+ tool toolbox/shrink_legs.py). Every grip/release has a 50.5 mm slow vertical leg in and out
(28 legs: 6 planks x 4 + frame x 4) at 20 mm/s. The extra 0.5 mm over r3's 50 mm (L01) costs 0.025 s per leg. Moving
each leg's top point 0.4 mm toward its event point (same orientation, IK near the old joints) makes the legs 50.1 mm:
-0.02 s per leg, the neighbouring fast Lines grow by <= 0.4 mm (+0.004 s each, transfers between two lowered tops
barely change). Expected about -0.5 s (90.9 -> ~90.4 s), 0 violations. Risk: r3 if the float sum along a leg ends
under 50.0 (L01); 0.1 mm is ~4 orders of magnitude above the IK/FK error, so I expect none. r4/r5 move by 0.4 mm only.

## Reason
Evidence: toolbox/move_times2.py on the iter-27 best: of 90.9 s, 28 slow legs x 2.53 s = 70.8 s and 7 s of waits are
fixed cost; every movable move left is at a rule floor (iter 27: r4 near-point, elbow over the guide, base A / frame1
box at Point80h, J5 limits). The one fixed cost that is ours, not the judge's, is the 0.5 mm margin from L01: 28 x
0.5 mm / 20 mm/s = 0.7 s. L01 found that exactly 50.0 mm fails because the summed path ends at 49.99..; that is a
float-rounding problem, so a 0.1 mm margin keeps the rule's intent (never aim at the threshold exactly) at a fifth of
the cost.
Alternatives: the L49 shallower base A pocket (J5 pre-turn in the frame lift) is capped by the far frame end dropping
~3 mm per deg into base A (<= ~0.2 s, risky jig CAD); a different foot grip to split the flip over J4/J5/J6 is too big
for the ~45 min left; lowering Point80h is blocked by frame1's box (top 40.7 + 100 = 140.7 vs 142.5).
Principle: shorter fixed-cost events (slow legs) - the only remaining lever per run B's conclusion.

## Change
- new toolbox/shrink_legs.py: for each grip/release, sums the contiguous slow Lines before/after the event and moves
  the leg's top point (always a Line end here, no PTP skipped) (L - 50.1) mm toward the event point, same orientation,
  IK near the old joints (refuses jumps > 5 deg). All 28 legs 50.50 -> 50.10 mm. design/program.json = scratch/s28a.json.
- 2 mm screen (no shots): 90.4 s, 0 violations, joints 2312 deg.

## Screenshots
- 00 start: layout unchanged; planks upright in base A's slots, frame 1 in base A, guide on base B, arm at home.
- 01 plank6 released upright in the far column, gripper straight above; planks 4/5 still in their slots.
- 02 plank5 released next to plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, nothing left in the wall slots.
- 04 plank3 released in the outer row, upright; planks 1/2 still standing in their slots.
- 05 plank1 released beside plank3, upright.
- 06 plank2 released; all six planks upright in frame 1, gripper above, arm in the usual pose.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical, arm at the usual
  release pose at the -y edge, elbow clear of the guide.
- 08 end: bench assembled in base B, arm back at home, base A empty; nothing floating, crooked or interpenetrating.
- topview: same paths as iter 27 (0.4 mm z shifts are invisible).

## Result
Expected about -0.5 s, 0 violations; got 90.9 -> 90.4 s (planks 67.9 -> 67.5, frame 17.2 and home 5.8 rounded the
same; move_times2 cumulative 90.9 -> 90.4 s), joints 2316 -> 2312 deg, 0 violations at 2 mm. The reason held: the 0.5 mm margin was a pure
fixed cost of ours; 50.1 mm legs pass r3 everywhere (the float sum error is far below 0.1 mm). Kept.
