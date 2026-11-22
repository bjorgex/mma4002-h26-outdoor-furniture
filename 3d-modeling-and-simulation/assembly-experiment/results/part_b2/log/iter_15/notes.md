# iter 15: planks 1-3 start in slots cut into base A, right in front of their places (plank jig 1 removed)

## Hypothesis
Change type: mixed (jig_cad + layout + program). Base A gets three 25.6 x 5.6 mm through-slots in its free corner
(robot-side of frame 1's y-124 arm, below it in y): one per y-124 place, at the place's x (robot x -698 / -668 /
-638), plank centre ~22 mm from the row (robot y ~102). Planks 1-3 stand in them on the base A riser (10 mm higher
than on the plate). Plank jig 1 is removed (one fixture fewer). Program (toolbox/base_a_slots.py): the three group-1
pick blocks move by the plank start-pose delta (+10 mm z); the plank1 -> plank2 return (lift + PTP + down) becomes one
Line; the start PTP end Point16t gets +3.5 mm for r4 slack vs the plank3 release point. Expected: the five group-1
transfers drop from 1.02-1.47 s (6.5 s) to ~0.25-0.5 s (~1.8 s): about -4.5 s (100.3 -> ~96 s), 0 violations.
Risks: base A wall thickness between slots and the frame pocket; the start PTP (r4 over plank3/plank1 thin boxes,
L23/L25); the gripper body only ~12 mm over the placed planks' tops at the plank1/plank2 picks.

## Reason
Evidence: toolbox/move_times2.py on the iter-14 best: the group-1 transfers are 1.40 + 1.43 + 1.15 + 1.47 (lift+PTP+
down) + 1.02 s = 6.5 s, set by the ~100-145 mm from plank jig 1 (robot x -560, beside base A) to the y-124 places
(x -638..-698). scratch/free_a.py shows base A is solid and free of frame 1 in the whole corner x -715..-585,
y 10..112, i.e. directly in front of those places. Iter 14 showed the same idea for the far column (feed each
place row from its own side, -4.8 s).
Alternatives: a separate jig on the +y side of base A has no room (plate edge 20 mm away); moving jig 1 cannot get
closer than base A's edge (x -581); program polish has ~0.5 s left at most. Slots inside base A also remove a
fixture.
Principle: present parts next to where they are assembled, shortest route, fewer fixtures.

## Screening (2 mm)
- Walls (scratch/wall15.py): slot-to-pocket 14.3 / 14.3 / 6.3 mm, slot-to-slot 4.4 mm (>= 3). Plank jig 1 removed.
- p15a (dz16 3.5): 95.1 s but r3 1 (safe height rose to 321: the 160 mm Line plank2 -> plank6 pick starts at 316)
  and r4 1 (Point16t), see L43.
- p15b (dz16 12, + 7 mm fast vertical Line Point41u before the long Line): 95.3 s, 0 violations. p15c (dz16 25):
  95.4 s, 0. Scored p15b.

## Screenshots
- 00 start: plank jig 1 gone; planks 1-3 stand upright in base A's free corner (in front of frame 1's y-124 arm,
  row of three along x), planks 4-6 in jig 2 at the far edge, guide on base B, arm home. Nothing floating.
- 01 plank3 released: plank3 upright in the outer y-124 place, the other two still in the base A slots; gripper
  just above it.
- 02 plank1 released: middle place filled, plank2 alone in its slot, arm in a normal elbow-up pose.
- 03 plank2 released: y-124 row full (3 upright), base A slots empty, planks 4-6 still in jig 2.
- 04 / 05 / 06 plank6 / 5 / 4 released: the far column fills from jig 2 behind it, all upright, none crooked;
  jig 2 empty after 06.
- 07 frame 1 + planks released: flipped into frame 2 through the guide on base B, arm at the release pose as
  before; base A empty (slots visible as faint lines).
- 08 end: bench assembled in base B, arm home.
- topview: the group-1 transfers are now short zig-zags (~25-45 mm) between the base A slots and the y-124 row; the
  frame / home paths are unchanged.

## Result
Expected ~-4.5 s, 0 violations; got 95.3 s (-5.0 s), 0 violations, joints 2538 -> 2206 deg. Phases: planks
75.8 -> 70.8 s; frame 18.0 / home 6.5 unchanged. The reason held: the group-1 transfers were set by the jig-1-to-
place distance; feeding the row from slots right in front of it cut them to a few tenths of a second each (the cost:
+0.2 s for the higher start PTP end and the 7 mm safe-height lift). Kept; plank jig 1 is no longer needed.
