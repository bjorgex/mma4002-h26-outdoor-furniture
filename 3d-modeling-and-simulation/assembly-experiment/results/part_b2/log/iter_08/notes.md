# iter 08: pre-turn the wrist toward home during the lift after the frame release

## Hypothesis
Change type: program. The home PTP #72 Point88h -> Point1 (3.20 s) is J5-limited (J5 138.1 -> -21.6, 159.6 deg).
Split the slow up-leg after the frame release (#70, 50.5 mm, 2.52 s) at 30 mm (split_rot.py G 0) and turn the
tool toward the home orientation in the upper 20.5 mm (1.02 s = 51 deg of tool rotation free, slerp g ~0.30) and
during the fast lift Point88h (0.59 s, ~30 deg more, g ~0.47) with a new tool toolbox/turn_toward.py.
scratch/probe08.py: at g 0.47 J5 is ~72, so the home PTP J5 delta drops to ~94 deg (~1.9 s). Expected ~-1.2 s
(109.1 -> ~107.9), 0 violations. Risk: r1 gripper vs the frame foot / guide while turning, line followability.

## Reason
Evidence: toolbox/move_times2.py on the iter-07 best: the home PTP is the single longest move (3.20 s, J5 159.6 deg);
the slow leg right before it turns nothing. scratch/probe08.py shows that slerping the TCP orientation from the
release pose toward home lowers J5 almost 1:1 (rot 51 deg -> J5 101.6; rot 77 -> J5 76) on the same wrist branch, no
singularity on the way (J5 stays >> 0). L28/L34 said J5 travel is at its floor for a fixed set of poses - but that
counted only PTPs; a vertical Line may re-orient for free while its TCP distance sets its time (iter 06/07 used this
for J6). Alternatives: the frame flip (3.84 s, J5) could absorb J5 in the slow lift after the frame grip, but there
the frame + 6 planks are still in base A's pocket (collision risk); the release side has an empty gripper, so it is
the safer first test. Principle: overlap motion with already-paid fixed-cost events.

## Screening (before the score)
All 2 mm, --no-shots (L22). Slow leg split at 30 mm (scratch/z08a.json), then turn_toward Point88 / Point88h:
- g 0.29 / 0.46: 107.9 s but r1 5 (link_3/link_4 vs Guide, Base B, frame2) - the elbow folds down (J3 -30 -> -80).
- g 0.12 / 0.22: 108.6 s, r1 2 + r5 1 (Guide/link_3, 3.8 mm). g 0.20 / 0.30: 108.4 s, r1 4 + r5 1.
- g 0.08 / 0.19: 108.7 s, r1 1 (Guide/link_3).
- no slow-leg turn, Point88h moved 100 mm inward + 40 up, g 0.33: 109.1 s (longer Line eats the gain), r1 1.
- g 0.06 / 0.15: 108.8 s, 0 violations, free-move clearance 32.2 mm -> scored.
scratch/probe08c.py (orientation sampling with an elbow-height filter): at the fixed release TCP no orientation lowers
J5 without dropping the elbow (L37).

## Screenshots
- 00 start: frame 1 + pieces A in base A, guide on base B (riser), 6 planks upright in the plank jig, arm at home; nothing floating.
- 01 plank3 released: plank3 upright in frame 1's outer slot, gripper above it, 5 planks left in the jig.
- 02 plank1 released: two planks upright in frame 1, 4 in the jig; elbow-up pose as before.
- 03 plank2 released: the y-124 row of 3 planks upright and straight.
- 04 plank6 released: 4 planks in frame 1, 2 left in the jig, upright.
- 05 plank5 released: 5 planks in frame 1, plank4 alone in the jig.
- 06 plank4 released: all 6 planks upright in frame 1, jig empty, gripper above plank4.
- 07 frame released: frame 1 + planks turned over, seated through the guide into frame 2 on base B; arm reaching over the -y edge as before (the changed lift follows this shot).
- 08 end: bench assembled in base B (planks vertical, guide on top), arm back at home; base A and plank jig empty.
- topview: same paths as iter 07; the change is a re-orientation on the vertical lift at (-747, -197), invisible from above.

## Result
Expected -1.2 s (with g 0.29 / 0.46), got 109.1 -> 108.8 s (-0.3 s) with the reduced turn g 0.06 / 0.15, 0
violations. Phase home 6.8 -> 6.5 s, others unchanged; joint travel 2799 -> 2792 deg; 72 -> 73 moves. The reason held
only partly: J5 does follow the tool rotation almost 1:1 and the slow leg has the spare time, but at the reach edge
the J5 decrease needs the elbow to fold, and the elbow then hits the guide on base B (L37); only ~15 deg of J5
(138 -> 123) fit. Kept (better, clean, shots fine).
Next: the same overlap at the frame-grip lift (flip is J5-limited, 3.84 s) is limited by the carried frame in base
A's pocket; a bigger gain needs the release pose moved inward (base B layout) so the elbow has room.
