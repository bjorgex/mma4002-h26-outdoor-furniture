# iter 02: guide gripped from above - grip pocket becomes a vertical through-notch (mixed: jig_cad + program)

## Hypothesis
Change type: mixed (jig_cad + program; inseparable - the notch alone changes nothing, the vertical approach alone
cannot enter the closed side pocket).
4 of the 6 r3 violations are the guide grip / release: the fingers slide horizontally 25 mm into the 20 x 10 mm
side pocket (grip in, release out, twice). Change:
- CAD (`design/cad/jig_parts.py`): the grip pocket is cut through the full guide thickness (z 20..60) -> a vertical
  notch in the short arm's side face (same x/y footprint, widened from 20 to 24 mm in y for finger slack). It is
  symmetric in z, so it works for both guide orientations.
- Program (`toolbox/guide_vertical.py`): while the robot handles the guide, J6 -90 deg (rotation about the tool
  axis = the flange axis, so the gripper body - nearly square, 94 x 90 - barely changes envelope) so the fingers
  open across the notch (guide y) instead of along z. The horizontal 25 mm slide in / out is replaced by a slow
  50.5 mm vertical Line down into / up out of the notch at the event point; the fast free moves end / start 50 mm
  higher (the old fast Lines went down to z 50 next to the guide: clearance 3-5 mm, r5 x4).
Expected: r3 6 -> 2 (guide x4 fixed; frame release out + low traverse remain), r5 4 -> 0..2 (fast moves now end
50 mm higher), r1 unchanged (6: link_3 vs planks 4/5 at the base-B guide grip, plank1/plank2) -> violations
17 -> ~9-11. Cycle: about -1..+2 s (slide 25 mm slow removed, 50 mm vertical slow added, but fast descents shorter).

### Addendum after the first screens (before the 2 mm score)
Screening showed that rotating J6 by +-90 turns the TM5's wrist camera (link_6) straight down at one of the two
bases (-55 mm below the plate at the grip point; J6 -90 -> base B, +90 -> base A; the 180 deg guide flip about the
tool axis couples the two, so no sign works for both - L04). Scope extended (layout): base B riser 10 -> 80 mm
(+70), J6 -90, and every move at base B shifted +70 mm with IK (`toolbox/shift_moves.py`: guide grip / release legs
at base B, frame-release Point85-Point90). r8 is relative to frame2, so the raise is legal. Screen (10 mm): 7
violations (r1 5 = old link_3/planks 4/5 at the base-B guide grip, r3 1 frame release slide, r4 1), cycle 247.5 s.
Revised expectation at 2 mm: violations 17 -> 7-9, cycle ~247-248 s.

## Screenshots
- 00 start: base B now on a tall grey riser (80 mm) with the yellow guide on it; base A low with frame 1; 6 planks upright in the plank jig; arm at home. Nothing floating.
- 01 guide released on base A: guide turned over, lying flat on base A over frame 1; base B shows empty frame 2 on its riser; gripper horizontal beside base A at guide height, camera up; pose sensible.
- 02 plank3: plank3 upright through the guide slot into frame 1; gripper above it; 5 planks left in the jig.
- 03 plank6 / 04 plank2 / 05 plank5 / 06 plank1 / 07 plank4: planks added one per shot, all upright and straight in the guide, none floating or crooked; the jig empties in order.
- 08 guide back on base B: guide flat on the raised base B over frame 2; 6 planks stand in frame 1 on base A; gripper horizontal beside base B at the guide's height, arm folded near the plate edge - fine.
- 09 frame 1 + planks released: frame 1 turned over, planks down through the guide into frame 2 on the raised base B; wrist at the plate edge (y ~ -230, outside the plate in the top view), as in iter 01, now 70 mm higher.
- 10 end: bench assembled on base B (frames top and bottom, 6 planks between), guide below the top frame; arm at home.
- topview: same route as iter 01; the guide grip / release now end in a point (no 25 mm slide stubs at x -589/-614); the frame-release side slide (y -218) is still there.

## Result
Expected (revised) violations 17 -> 7-9, cycle ~247-248 s. Got (2 mm): violations 8 (r1 6, r3 1, r4 1, r5 0), cycle
247.5 s (+0.9 vs iter 01: guide -0.4, planks +0.8, frame -0.2, home +0.7), joints 8957 deg.
- r3 6 -> 1: the 4 guide events are vertical now; the low traverse is gone too (the frame-release slide is 70 mm
  higher). Left: the frame-release out leg (sideways slide).
- r5 4 -> 0 (fast moves end 50 mm above the notch; min free clearance 31.8 mm).
- r1 6 -> 6: the old link_3 vs planks 4/5 at the base-B guide grip (5 moves) + plank1/plank2 (move 76), unchanged.
Kept: verdict BETTER (17 -> 8 violations), screenshots fine. Next: the link_3 vs planks 4/5 cluster (5 r1) - the
elbow passes over the plank jig when reaching base B; move the plank jig or base B (layout), or change J1/elbow.
