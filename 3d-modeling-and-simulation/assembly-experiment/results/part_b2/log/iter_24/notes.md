# iter 24: planks 4-6 start in slots cut into base A's far wall (plank jig 2 removed)

## Hypothesis
Change type: mixed (jig_cad + layout + program). Base A gets three more through-slots (yaw 80, as the planks sit in
frame 1) in the 20 mm strip between frame 1's far edge (robot x -741.5) and base A's far edge (-761.4), at the robot
y of each far-column place (planks 4/5/6: y ~104.7 / 74.7 / 44.7), slot centre ~robot x -751.5 (~27 mm closer to the
places than plank jig 2 at -778.7). Planks 4-6 stand on the riser (+10 mm z, tops 271 = the planks 1-3 height, so
the r3 safe height does not change). Plank jig 2 is removed. Program: the three group-2 pick blocks move by their
plank's start-position delta (generalised toolbox/base_a_slots.py), the start PTP end P16s0t gets extra z for r4 over
the higher plank6 top. Expected: the five group-2 transfer Lines (Point30/44/48/62/66: 2.83 s) drop to ~1.5 s, the
start Line Point26t gets ~+0.1 s longer: about -1.2 s (92.5 -> ~91.3 s), 0 violations.
Risks: wall thickness (computed ~4.8 mm each side, >= 3), gripper body over the placed far-column planks at the
plank5/plank4 picks (same geometry as the places), r4 at the start PTP end (L43: give >= 10 mm slack).

## Reason
Evidence: toolbox/move_times2.py on the iter-22 best: the group-2 transfers (pick top <-> place top) cost 0.50 + 0.58
+ 0.54 + 0.62 + 0.59 = 2.83 s, set by the ~45-56 mm x gap from plank jig 2 (robot x -778.7, outside base A) to the
far-column places (x -733..-722). The group-1 analogues, whose picks were moved into base A in iter 15, cost only
0.24-0.39 s. scratch/cell_bounds.py: base A's solid strip beyond frame 1 is ~20 mm wide (x -761.4..-741.5), enough
for a 5.6 mm slot turned 80 deg (x extent ~10 mm) with ~4.8 mm walls.
Alternatives: moving jig 2 closer is blocked by base A's edge (5 mm gap already, L32); the release-side / flip /
home J5 turns are exhausted (iters 08/17/21/23); structural changes (two-plank grips) do not fit the ~70 min left.
This repeats iter 15's proven pattern (-4.6 s there) for the other row.
Principle: present parts next to where they are assembled (shortest route), fewer fixtures.

## Change
- design/cad/jig_parts.py + design/build_cell.py: PLANK_SLOTS_A gains slots 4-6 at base-local (80, -5/25/55, yaw 80);
  plank jig 2 is no longer placed in the cell (PLANK_SLOTS2 = {}). Walls (scratch/wall24.py + extents): slot to pocket
  20.0 / 14.8 / 9.6 mm, to base A's outer edge ~5.0 mm, slot 4-5 / 5-6 3.9 mm (>= 3). Planks 4-6 now at robot x
  -756..-746.5 (were -783.5..-774), z 21..271.
- toolbox/base_a_slots2.py (T log): group-2 pick blocks moved by the start delta (+27.5, 0, +10), P16s0t +5 mm extra.
- 2 mm screen of the first variant: 91.3 s, 0 violations; scored as is.

## Screenshots
- 00 start: plank jig 2 gone; all six planks stand upright in base A (three in front of the y-124 arm, three in the
  far wall strip), guide on base B, arm at home. Nothing floating, no jig off the plate.
- 01 plank6 released upright in the far column (first), gripper just above; planks 4/5 still in their slots right
  next to it.
- 02 plank5 released next to plank6, upright; plank4 alone in its slot.
- 03 plank4 released; far column full, far-wall slots empty.
- 04 plank3 released in the outer y-124 place, upright.
- 05 plank1 released next to it.
- 06 plank2 released; all six planks upright in frame 1, base A slots all empty.
- 07 frame 1 + planks flipped into frame 2 through the guide on base B; arm at the release pose at the -y edge (same
  pose as iter 22).
- 08 end: bench assembled in base B, arm at home; base A empty.
- topview: the group-2 zig-zag is now short (x -756 <-> -728), no path outside base A for the plank picks; frame
  approach / flip / home paths unchanged.

## Result
Expected -1.2 s (92.5 -> ~91.3 s), 0 violations; got 91.3 s, 0 violations, joints 2377 -> 2324 deg. Plank phase
69.3 -> 68.0 s; the other phases unchanged. The reason held: the group-2 transfers were set by the jig-to-place x gap,
and base A's far strip had room for slots with >= 3.9 mm walls. One fixture fewer (plank jig 2). Kept.
