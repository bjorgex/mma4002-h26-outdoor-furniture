# iter 45: notch the guide's outer corner so iter 41's J5 pre-turn at Point85tt clears link_3

## Hypothesis
Cut a 25 x 28 x 15 mm notch (guide-local x > 63, y < -62, z < 35, the face that is up on base B) out of the guide's
far corner, and use iter 41's program (j5turn20 D -6.5 at Point85tt). Expected: 89.8 s (-0.1 s), 0 violations.
Change type: mixed (jig_cad + the program variant already scored alone in iter 41).

## Reason
Evidence: iter 41 scored 89.8 s with exactly one problem, r1 2 "Guide/link_3" at #56/#57; L66-L68 closed the base-B J5
turn for program-only changes. scratch/elbow45.py on the iter-41 program locates the contact: guide point world
(-770.8, -187.2, 149) = guide-local (85, -87, 22), i.e. the top edge of the guide's outermost corner. scratch/corner45.py
shows no slot within 45 mm of it (only outline vertices), and the guide is never moved or gripped any more (no guide
trip since run B), so that corner holds nothing: it only guides planks in the middle. Why this and not something else:
4 program rejections in a row (rule: switch change type), and L66 says only a guide change can free the base-B J5 trip;
the other option (moving base B) would move every frame release point. DFA principle: a fixture should have no material
where the robot needs to pass; trim the jig to its function.

## Screenshots
- 00 start: frame 1 + planks 1-3 in base A slots, planks 4-6 in the far strip, guide on base B over frame 2; arm at home.
- 01-06 (plank6, 5, 4, 3, 1, 2 released): each plank stands upright in frame 1 on base A, gripper just above; nothing
  floating or crooked, the guide on base B unchanged (the notch is at its far corner, too small to see at this scale).
- 07 frame 1 released: frame 1 with all six planks upright through the guide into frame 2 on base B; arm reaching over
  base B's far side, as in iter 40.
- 08 end: bench assembled in base B, arm at home, base A empty.
- topview: same TCP path as iter 40/41; no jig moved.

## Result
Expected 89.8 s / 0 violations; got 89.8 s, 0 violations (phase frame 1 + planks 16.9 -> 16.8 s, others equal), joints
2285 (+10, irrelevant: cycle decides). Probe after the cut: link_3 min 3.4 mm (now at the notch's inner edge, local x 63),
judge min clearance 3.2 mm. The reason held: the contact was only the guide's unused corner, and the notch (25 x 28 x
15 mm, no slot within 45 mm, walls unchanged) freed the iter-41 J5 turn. Kept.
