# iter 11: outbound guide transfer with PTPs instead of long 100 mm/s Lines

## Hypothesis
Change type: program (+ tool toolbox/guide_ptp.py).
The guide phase (62.4 s) is mostly long fast Lines at 100 mm/s (a Line's time = TCP path / 100 mm/s), while a PTP
costs max joint delta / 50 deg/s. Outbound guide transfer today:
- approach: PTP Point3 -> Line Point4 (83 mm) -> Line Point5 (204 mm, above base B at TCP z 461) -> Line Point6
  (280 mm down to grip + 50.5) = 5.7 s;
- carry: Line Point9 up 280 mm -> Line Point10 340 mm across to base A -> PTP Point11 (J6 flip 180 deg, 3.6 s) ->
  Line Point12 350 mm down = 13.3 s.
Change:
- approach: PTP Point3 -> new PTP Point6h straight to above the guide grip (TCP z ~265: >= 100 mm above the guide
  top 151 and the grip point 131, r4) -> fast Line down to Point6 (unchanged). Expected ~1.7 + 0.8 s.
- carry: fast Line up from Point8u to TCP z Zb (>= 232: 100 mm from the grip point), one PTP Point11h that does the
  move to base A and the 180 deg flip together (3.6 s, J6 dominates) ending at TCP z Zc over base A, fast Line down
  to Point12 (unchanged). Zb / Zc chosen as low as the screen allows (the flipping guide hangs up to ~180 mm below
  the TCP; r1/r5 >= 10 mm clearance).
Expected: guide phase -9 to -10 s (cycle 211.8 -> ~202 s), violations stay 0. Risk: r1/r5 from the guide sweeping
during the combined flip, r4 if the PTP passes < 100 mm above base A / base B contents.

Screens (10 mm, scratch/g11a..d.json): zb 245 / zc 220 -> r1 link_5 vs planks in the jig, low traverse, r4 (Point11h
75 mm from the plank3 release point at TCP z 265, L13); zc 355 fixes r3/r4; zb 245 -> r1 link_6/plank6; zb 300 and
340 clean. Scored with zb 320 (20 mm slack over the clean screen), zc 355, za 265.

## Screenshots
- 00 start: guide on raised base B over frame 2, frame 1 + pieces in base A, 6 planks upright in the plank jig, arm home.
- 01 guide released on base A over frame 1, turned over (yellow side up, seated flat); base B shows frame 2 + pieces;
  planks still in the jig; gripper beside the guide at the grip pocket, wrist clear of the plank jig.
- 02 plank3 upright in the guide over frame 1, gripper above it; 5 planks in the jig.
- 03 plank6 placed: two upright, vertical; gripper clear above.
- 04 plank1 placed: three upright, three in the jig; nothing tilted.
- 05 plank5 placed: four upright, two left in the jig.
- 06 plank2 placed: five upright, one left in the jig.
- 07 plank4 placed: all six upright in guide / frame 1, jig empty.
- 08 guide back on base B over frame 2; six planks standing vertical in frame 1; arm clear (same as iter 10).
- 09 frame 1 + planks turned over and lowered into base B, planks vertical between the frames; arm over the plate
  edge (same as iter 10). Nothing floating.
- 10 end: bench assembled in base B, base A and plank jig empty, arm home.
- topview: the outbound guide approach is now one dashed PTP arc from home to above base B (no Point4/Point5 lines);
  the carry is a short vertical Line + one dashed PTP arc base B -> base A; the return transfer is unchanged (solid
  lines via (-500, 0)).

## Result
Expected guide phase -9 to -10 s, violations 0. Got cycle 211.8 -> 202.8 s (-9.0 s), guide phase 62.4 -> 53.4 s,
other phases unchanged, joints 8844 -> 8487 deg, violations 0 at 2 mm (free-move clearance min still 31.8 mm).
Kept. Next: the same change for the return guide transfer (Point72/Point15/Point14 lines, Point11/Point74/Point9/
Point75 = ~16 s of Lines + PTP), then the frame-1 transfer lines (Point80 492 mm, Point85, Point90).
