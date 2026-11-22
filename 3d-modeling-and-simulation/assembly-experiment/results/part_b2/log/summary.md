# Run B2 summary

Start: run B's final design rescored with the B2 judge (iter 00). End: iter 45's design, **89.8 s, 0 rule violations,
2285 deg joint travel** (phases: planks 67.4 s, frame 1 + planks 16.8 s, home 5.7 s). 52 iterations, 36 kept after the
baseline. Iters 46-52 were all rejected, and the run ended on the time budget.

## Final design in a few lines
- Planks 1-3 and 4-6 start in slots cut into base A (iters 15, 24), right in front of their place rows; both plank jigs
  are gone. Each plank is picked and placed through the same 50 mm slow legs, and the transfers are single Lines.
- Places: far column first (6, 5, 4), then the y-124 row (3, 1, 2) (iter 16).
- Frame 1 is gripped at a leg foot, lifted, flipped in one J5-limited PTP pair via Pvia, and lowered into frame 2 on
  base B. A notch in the guide's unused outer corner (iter 45) lets the arm take a shorter J5 turn.
- Slow legs are 50.1 mm (iter 28: the margin is sized to float error). The tool pre-turns inside slow and fast Lines
  wherever the next PTP is J5/J6-limited.

## What worked
- **Removing fixed-cost travel through layout/jig changes** gave the biggest steps: the column plank jig (iter 12), then
  the planks in base A slots (iters 14, 15, 24), which shortened every transfer and removed a jig.
- **Hiding wrist turns inside slow legs and fast Lines** that had spare rotation budget (iters 02, 06-10, 17-23, 32).
  The rot/50 budget of a distance-limited Line costs nothing.
- **Re-sizing our own margins** (iter 28 leg margin, iters 27/30/33 r4 slack) and checking the exact unrounded total
  (exact27) before scoring sub-0.1 s changes.
- **Tie-breaks on joint travel** (iters 34-40): removing joint detours at home and at via points.
- **Trimming fixture material that has no job** (iter 45): the arm's contact point was on an unused guide corner.

## What did not work
- Changing the wrist branch for the frame release or the whole cycle (iters 05, 11, L28/L34/L40): out of reach, or the
  forearm folds over the frame.
- Tilting frame 1 while it is still engaged in base A (iter 21, L49).
- Any further J5 turn over base B (iters 41-43, 46-51): link_3 meets the guide. The material it hits holds a slot (L73).
- Splitting rotating Lines, or moving rotation between rotation-limited Lines and PTPs (iters 38, 44): the next move
  pays it back.

## Where the time is now
About 70 s of the 89.8 s is 28 slow legs (2.5 s each) and 7 s is gripper waits. The movable moves left are at measured
floors. Further gains need a fixed-cost event removed: fewer grips or releases (e.g. planks that drop into frame 1
straight from their slots, or a multi-plank grip), or a guide with its slot moved away from link_3's sweep, which would
free the base-B J5 turn (~0.2 s).

## Kept changes and their reasons (one line each)
- 01: the Line Point65 -> Point70 only rotated; its translation was kept, and the PTP takes the rotation.
- 02, 06, 07, 09, 18, 22: pre-turn the tool in Lines next to J5/J6-limited PTPs (spare rot budget).
- 03: move the plank jig closer to base A to shorten the J3-limited plank PTPs.
- 04, 13: plank transfers as single Lines where they are shorter than the ~175 mm break-even (L33/L42).
- 05: the frame flip as one joint move, with a via point to keep r4.
- 08, 10, 17, 20, 23: pre-turn the wrist around the frame lift/flip/release to shorten J5-limited PTPs.
- 12: the plank jig as one column aligned with the place rows (shorter transfers).
- 14, 15, 24: planks start in base A slots or near jigs right in front of their places (shortest route, fewer jigs).
- 16: place order far column first, so carried planks never sweep over placed ones.
- 19, 25, 26, 27, 30, 33: end r4-bound points at their measured floors instead of old slack values.
- 28: the slow-leg margin 0.5 -> 0.1 mm (the margin guards against float error, nothing bigger).
- 29: tried 50.01 mm legs (kept per the log).
- 32: pre-turn in Line #47 so the frame-approach PTP is no longer J4-limited.
- 34-40: remove joint detours (tie-break on joint travel).
- 45: notch the guide's unused corner, so iter 41's J5 pre-turn becomes legal (-0.1 s).

Run end: iter 53 (an unchanged re-score, 89.8 s, 0 violations) was the 8th iteration in a row without a keep, so the run
stopped on the streak rule with the time budget also gone. The final design is iter 45 (89.8 s, 2285 deg, legal).
