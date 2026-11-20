# iter 13: lower the plank transit points from TCP z 391 to grip/release + 102.5 mm

## Hypothesis
Change type: program (+ tool toolbox/lower_transit.py).
Biggest phase is planks (111.4 s). Every plank pick and place goes through a transit point at TCP z ~391 (PTP
endpoints), reached by fast vertical Lines: pick down 94.5 mm / up 85 mm, place down 75 / up 75 mm. The PTP rules
only need the endpoints >= 100 mm from every grip/release point (r4 near) and TCP >= 100 mm above unheld parts/jigs
under the path (plank tops in the jig 261 -> 361 only directly over them; placed planks 281 -> 381 only directly
over them, the PTP paths don't pass over them), and > 311 for the low-traverse check.
Change: every transit point (same xy as a plank grip/release event, between the neighbouring events) gets TCP z =
event TCP z + 102.5 (pick ~348, place ~368); IK re-seeded, the slow legs unchanged.
Expected per plank: -0.43 (pick down) -0.43 (pick up) -0.23 (place down) -0.23 (place up) = ~-1.3 s, x6 = ~-8 s,
cycle 194.6 -> ~187 s, planks phase 111.4 -> ~104. PTP times about the same. Violations stay 0. Risk: r5/r1 from
the carried plank (bottom = TCP - 235, i.e. ~113 mm leaving the jig, ~133 mm arriving over the guide at ~81) or a
PTP sagging over a standing plank (r4).

Screens / scores:
- dz 102.5 everywhere (10 mm, scratch/t13a.json): 187.2 s but r4 6: the PTP into each pick ends over the plank to
  pick, which is not held yet -> TCP must be >= plank top 261 + 100 (L14).
- pick dz 117.5 (TCP 363) / place 102.5 (10 mm, t13b): 0 violations, 188.7 s; 2 mm score: r4 2 - the PTP leaving a
  place transit starts over the plank just released (top 281) (L15).
- dz 117.5 everywhere (pick TCP 363, place 383): scored.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over and flat; gripper at its grip pocket; planks in the jig.
- 02 plank3 upright in the guide over frame 1, gripper just above it (a bit lower than before); 5 planks in the jig.
- 03 plank6 placed: two upright and vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two in the jig.
- 06 plank2 placed: five upright, one in the jig; no plank crossing another.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2, flat; six planks vertical in frame 1; arm retreated, clear of everything.
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames; arm over the plate
  edge (same as iter 12). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: same xy paths as iter 12 (the change is vertical only): the plank PTP arcs jig <-> base A unchanged.

## Result
Expected ~-8 s with transits at +102.5; the r4 box rule (L14/L15) forces +117.5 on both sides, so the gain is
smaller: cycle 194.6 -> 190.8 s (-3.8 s), planks phase 111.4 -> 107.6, other phases unchanged, joints 8207 -> 8085
deg, violations 0 at 2 mm (free-move clearance min 33.3 mm). Kept.
Next: plank pick slow lift 60 -> 50.5 mm (~-0.48 s x6 = ~-2.9 s); frame release leg 75 -> 50.5 (~-1.2 s); the
frame-1 transfer Lines (Point76..Point80 ~8 s, Point90/91 ~4 s) as PTPs.
