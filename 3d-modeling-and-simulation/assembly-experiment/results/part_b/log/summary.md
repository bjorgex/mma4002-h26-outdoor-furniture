# Summary (30 iterations, 2026-11-20)

**Result:** v3 239.8 s with several hard-rule violations -> final (iter 30) **112.9 s, 0 violations** at 2 mm
(joints 8911 -> 3670 deg, TCP path 15.7 -> 7.8 m). 29 of 30 iterations kept (iter 07 rejected).

## Final design
- Layout: base B on an 80 mm riser; plank jig moved toward base A, its robot-side row (planks 4-6) turned 80 deg so
  the place PTPs don't turn J6 ~75 deg; plank1/plank2 start slots swapped so pick and place orders agree.
- Jig CAD: small relief in the base B pocket where plank ends land flush (keeping support ledges for pieces B).
- Program (84 moves): **no guide trip** - frame 1 holds the planks alone, so the guide stays on base B the whole
  cycle. Planks picked outer-first and placed robot-side-last through 10 mm side-offset transits at ~102 mm over the
  grip/release point; 50.5 mm slow vertical legs. Frame 1 gripped at a leg foot via a short PTP-on-the-diagonal
  approach, short lift, flip (J5-only PTP + PTP flip), lowered through the guide into frame 2. Home placed on the
  joint path of the return PTP.

## What worked (largest gains)
- Dropping the guide trip entirely (iter 25: -47 s). Lesson L25: question whether a phase is needed before tuning it.
- Home pose on the right wrist branch and on the return path (iter 06, 24, 25: ~-20 s).
- Plank transit heights / side offsets just above the r4 limits, shortened slow legs to 50.5 mm (iters 9-23).
- J6 wraps and pre-rotated plank presentation (iters 19, 27), PTP replacing long Lines near reach edge (14, 28, 29, 30).

## What did not
- Relief cut that removed the interface pieces' support (iter 07, r6).
- Lower guide-carry PTP ends (wrist sweeps the plank jig, L19/L21); the frame flip on the other wrist branch (no IK,
  L24/L28).

## What is left
~70 % of the cycle is fixed: 50 mm slow legs at 20 mm/s (12 x 2.5 s + frame) and gripper waits. Further gains need
fewer approaches (e.g. gripping two planks at once with a different jig), not faster moves. A proposed judge fix
(Line time ignoring re-orientation) is in tool_changes.md.
