# iter 29: size the slow-leg float margin to its error (50.1 -> 50.01 mm legs)

## Hypothesis
Change type: program. Re-run toolbox/shrink_legs.py with --target 50.01 on the iter-28 best: all 28 slow legs
50.1 -> 50.01 mm. Expected 28 x 0.09 mm / 20 mm/s = -0.126 s: exact cycle 90.403 -> ~90.277 s, rounded 90.4 -> 90.3 s,
0 violations. Risk: r3 if the judge's summed leg length falls under 50.0; IK/FK and float error are ~1e-6 mm, so a
0.01 mm margin is still ~4 orders of magnitude above it.

## Reason
Evidence: iter 28 showed the leg margin is our own fixed cost (L57) and 50.1 mm passed r3 everywhere; scratch/exact27.py
on the best gives 90.403 s exact, so a -0.126 s change crosses the 0.1 s rounding step (L55). L57's lesson says to size a
margin to the error it guards against: the error L01 found was float summation (49.99999..), i.e. ~1e-6 mm, so 0.1 mm
was still ~10^5 x that. 0.01 mm keeps a real margin (the rule's intent: never aim at the threshold exactly).
Alternatives: the L49 shallower base A pocket (J5 pre-turn in the frame lift, jig_cad) and a new foot grip are too big
and risky for the ~50 min left in the budget; every movable move is at a rule floor (iter 27/28 notes). This is the
only small, safe, measurable gain left that fits one session.
Principle: shorter fixed-cost events (slow legs), as in run B's conclusion.

## Change
- `./py toolbox/shrink_legs.py design/program.json scratch/s29a.json --target 50.01`: all 28 legs 50.10 -> 50.01 mm
  (top points moved 0.09 mm toward the event, same orientation). scratch/exact27.py: 90.403 -> 90.282 s exact.
  design/program.json = scratch/s29a.json. No tool change.

## Screenshots
- 00 start: layout unchanged; planks upright in base A's slots, frame 1 in base A, guide on base B, arm at home.
- 01 plank6 released upright in the far column, gripper above; planks 4/5 still standing in the wall slots.
- 02 plank5 released next to plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, gripper above, nothing floating.
- 04 plank3 released in the outer row, upright; planks 1/2 still in their slots.
- 05 plank1 released beside plank3, upright.
- 06 plank2 released; all six planks upright in frame 1, arm in the usual pose.
- 07 frame 1 + planks flipped and lowered through the guide into frame 2 on base B, planks vertical, arm at the usual
  release pose at the -y edge, elbow clear of the guide.
- 08 end: bench assembled in base B, arm at home, base A empty; nothing floating, crooked or interpenetrating.
- topview: same paths as iter 28 (0.09 mm shifts invisible).

## Result
Expected -0.126 s, 0 violations; got 90.4 -> 90.3 s (planks 67.5 -> 67.4, frame 17.2 / home 5.8 same rounded; exact
90.282 s), joints 2312 deg unchanged, 0 violations at 2 mm. The reason held: the leg margin only guards float error,
and 50.01 mm passes r3 on all 28 legs. Kept. This lever is now exhausted (further shrinking gains < 0.01 s per 0.01 mm
and would aim at the threshold).
