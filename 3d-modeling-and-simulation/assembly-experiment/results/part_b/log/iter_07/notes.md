# iter 07: relief recesses under the plank ends in base B

## Hypothesis
Change type: jig_cad.
The last violation, r1 "Base B/plank3" at #127 (final insertion of frame 1 + planks into frame 2), is not a sweep
collision: scratch/jig_pair.py shows plank3 > 2.7 mm from Base B until the last sample, and scratch/release_dbg.py
shows that at the release pose all plank ends sit flush (depth 0.0) on the base B pocket floor (z 9.5 base-local,
= frame 2's outer face). FCL reports planks 1,2,4,5,6 touching there (allowed release contacts) but plank3's exact
touch flips between samples -> counted as a hit (L09, cf. L05).
Change: design/cad/jig_parts.py base_b(): cut a 2 mm deep recess (plank end outline + 1 mm) under each of the 6 plank
ends in the pocket floor (floor 9.5 -> 7.5 mm there; frame 2 still sits on the floor around them), then mirror as
before. Base A, the program and layout unchanged.
Expected: violations 1 -> 0 (first legal design), cycle unchanged 229.6 s, joints unchanged. r6 still OK: the group
rests on pieces B / frame (the rest list already includes pieces B1..B6).

Build notes: first two recess outlines (plank end face, then a section 2 mm up) were too small: the plank_body end is
stepped/narrower than the body, contacts stayed (scratch/rest_local.py). Final: the plank's whole xy bounding box
+ 1 mm, 2 mm deep. scratch/release_dbg.py then showed no plank / Base B contact on move 127 at 2 mm.

## Screenshots
(Program unchanged from iter 06, so 01-08 were not re-opened; this is a reject - the key shots below.)
- 00 start: guide on raised base B, frame 1 + pieces in base A, 6 planks upright in the jig, arm at home; pieces B
  are hidden under the guide, so the float is not visible here (the judge's rest check finds it).
- 09 frame 1 + planks released into base B: turned over, planks down into frame 2, gripper at the foot, same as iter 06.
- 10 end: bench assembled in base B, base A empty, arm at home.
- topview: identical paths to iter 06; base B outline unchanged (the recesses are only 2 mm deep in the floor).

## Result
Expected violations 1 -> 0, cycle unchanged. Got: r1 1 -> 0 (the plank3 contact is gone, as planned), cycle 229.6 s
unchanged, but r6 0 -> 4: "start: piece B1/B2/B3/B6 floats". The interface pieces B sit in frame 2 at the plank
positions (same footprint as the plank ends), so the recesses removed the floor under them. Violations 1 -> 4.
Rejected (verdict NOT better). Next: keep the floor under the pieces and relieve only where the plank end pokes
through past the piece (measure piece vs plank end footprint in base B local coords first), or a shallower relief
that leaves a support ledge for each piece.
