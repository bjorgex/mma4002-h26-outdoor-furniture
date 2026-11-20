# iter 25: the guide stays on base B (no guide trip to base A and back)

## Hypothesis
Change type: program (+ tool toolbox/drop_range.py).
The guide goes base B -> base A (#2..#13, ~22 s from home to the plank3 pick) and back (#81..#92, ~24 s) only so
the planks are placed through its slots over frame 1. But in phase 3 the guide is lifted off and frame 1 holds the
six planks upright on its own (also while it is carried and flipped), and the guide ends where it started (base B,
needed there for the final insertion). The judge has no rule that the guide must visit base A. So: drop
everything between the start home Point1 and the first PTP to Point16 (plank3 pick transit), and between Point70
(lift over the last placed plank, TCP 391) and the PTP to Point80h (frame approach); the guide never moves.
Expected: cycle 165.8 -> ~120 s (-45 s: guide phase ~40 -> 0, planks ~unchanged, "home"/frame phases +- a few s for
the new direct PTPs Point1 -> Point16 and Point70 -> Point80h), violations 0.
Risk: r4/r1 on the new PTPs (Point1 -> Point16 swings over the plank jig and base A; Point70 -> Point80h over the
standing planks); r6 if a plank was resting on the guide rather than on frame 1 / its pieces.
Process trade-off (not a judge rule, flag in the report): the planks lose the guide's lead-in over frame 1; they
go straight down into frame 1's interface pieces on robot accuracy alone.

Screens (all --step 2 --no-shots):
- a: guide steps dropped (toolbox/drop_range.py Point1:Point16 Point70:Point80h), old home: r4 1 ("PTP move #2
  (Point16): TCP < 100 mm above plank6"), 119.1 s - the home -> Point16 PTP comes from the -y side over plank6 (L23).
- b: a + Point16 (both uses) moved 10 mm to the outer side (dy +20): r4 1 above plank3 instead. Dropped.
- c: a + home on the joint path Point88h -> Point16 (toolbox/home_on_path.py f 0.5): 0 violations, 118.3 s, but
  home TCP (-687, -348, 671) off the plate edge and high.
- d: f 0.7: 0 violations, 118.3 s, home TCP (-685, -249, 517) -> installed and scored.
The DO sequence stays consistent: every grip (DO0=1) now follows a release (DO0=0); the guide's "open" step
(DO0=1, null) went with the guide moves.

## Screenshots
- 00 start: guide (yellow) on base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the jig; arm in
  the new home over the base B corner, gripper well above the guide.
- 01 plank3 released upright in frame 1 on base A (no guide there now), vertical; 5 planks in the jig; gripper above.
- 02 plank6 placed: two upright in frame 1, both vertical, nothing leaning; gripper clear above.
- 03 plank1 placed: three upright; three in the jig.
- 04 plank5 placed: four upright; two in the jig.
- 05 plank2 placed: five upright; one in the jig.
- 06 plank4 placed: all six upright in frame 1, jig empty; guide still untouched on base B.
- 07 frame 1 + planks turned over and lowered through the guide into frame 2 on base B, planks vertical, frame 1
  level on top; arm reaching out past the plate edge at y ~-250 (same release pose as iter 24). Base A empty.
- 08 end: bench assembled in base B with the guide in it (as in v3's end state), base A and jig empty; arm in home
  (same as 00), gripper well above the bench.
- topview: the base B <-> base A guide carries are gone; home -> plank3 pick is one long PTP across the plate;
  plank picks/places unchanged; the frame grip approach now comes straight from the last plank place.

## Result
Expected ~-45 s. Got 165.8 -> 118.3 s (-47.5 s): guide phase 40.7 -> 0, planks 96.2 -> 89.9 (the start PTP to
plank3 now counts here), frame 23.9 -> 21.6 (approach from base A instead of base B), home 4.9 -> 6.8.
Joints 6110 -> 4386 deg, 108 -> 84 moves. Violations 0 at 2 mm, free-move clearance 41.5 mm. Kept.
Note for the report (process trade-off, no judge rule): without the guide over frame 1, the planks lose its lead-in
while they are placed; they rely on robot accuracy + the interface pieces. Frame 1 already holds them upright alone
in phase 3/4 of v3, so the guide was an alignment aid there, not a support. On the real cell, a trial insertion
should confirm the planks find the pieces without the guide; if not, a cheap fixed (never moved) guide on base A
would restore that at almost no cycle cost.
