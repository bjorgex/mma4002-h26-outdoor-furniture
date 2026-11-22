# iter 26: lower the start PTP end P16s0t beside plank6's thin box (shorter first approach Line)

## Hypothesis
Change type: program. #3 Point26t (P16s0t -> Point26t) is a 76.5 mm fast Line, distance-limited at 0.77 s (rot 31.8 deg
= 0.64 s budget). P16s0t sits straight over the plank6 pick at TCP z 383 because the r4 box check needs TCP >= plank6
top (271) + 100 while inside its xy box. Base A's slots hold the planks thin in x, so moving P16s0t 12 mm in -x (the
side home comes from, L27) takes it out of the box; then only the 100 mm distance to the grip/release points binds
(plank6 grip -751/44.6/256 and the plank6 release Point31 -733/44.5/265.6 -> TCP z >= ~366 with dx -12). Variants TCP
z 368 / 372, orientation kept (toolbox/turn_toward.py g 0 + shift). Expected: Line 76.5 -> ~63 mm, 0.77 -> ~0.64 s
(rot-limited), start PTP about equal: about -0.12 s (91.1 -> ~91.0 s), 0 violations. Risk: r4 thin-box clip at the PTP
end (L22/L23: screen at 2 mm), the PTP limit moving from J5 to J1.

## Reason
Evidence: toolbox/move_times2.py on the iter-25 best: #3 Point26t d 76.5 mm, rot 31.8, 0.77 s - the largest
distance-limited fast Line left at a pick; its start height 383 is set by the r4 box rule over plank6, which a
sideways offset escapes (L22 used the same 10 mm side-offset trick for the plank transits in run B; L29/L53: re-derive
a point's coordinates from the constraints that still bind). The rest of the plank phase is rule-fixed slow legs and
waits, and the J5-limited flip / home are elbow-capped (L37, L45, L51); the iter-21 jig change (shallower base A pocket)
is too big for the ~65 min left. Alternatives: lowering P16s0t straight down violates r4 (box); a PTP straight to
Point26t is impossible (r4 near point, 50 mm slow leg).
Principle: shortest route once a detour's reason (r4 box) is removed; small but program-only and low risk.

## Change
- toolbox/turn_toward.py design/program.json -> scratch/k26a.json 2 2 0 -12 0 -15 (P16s0t -> P16s0tt, TCP dx -12, z
  368) and k26b ... -12 0 -11 (z 372). 2 mm screens: k26a 91.0 s but r1 1 ("move #2 (P16s0tt): link_6/plank4", the
  wrist camera over the neighbouring plank); k26b 91.0 s, 0 violations. Scored k26b. Start PTP 0.41 -> 0.40 s (still
  J5), Point26t 0.77 -> ~0.67 s.

## Screenshots
- 00 start: layout unchanged; six planks upright in base A's slots, guide on base B, arm at home over the far edge.
- 01 plank6 released upright in the far column, gripper above it; planks 4/5 in their slots.
- 02 plank5 released beside plank6, upright; plank4 alone in the slots.
- 03 plank4 released; far column full, base A wall slots empty.
- 04 plank3 released in the outer y-124 place, upright.
- 05 plank1 released next to it, upright.
- 06 plank2 released; all six planks upright in frame 1, gripper straight above plank2.
- 07 frame 1 + planks flipped into frame 2 through the guide on base B, planks vertical; arm at the usual release pose
  over the -y edge.
- 08 end: bench assembled in base B, arm at home; base A empty; nothing floating or crooked.
- topview: same paths as iter 25 except the first (yellow) PTP, which now ends ~12 mm short of the plank6 pick in -x;
  the short approach Line from there to the pick is the only new segment.

## Result
Expected about -0.12 s (91.1 -> ~91.0), 0 violations; got 91.0 s (programmed -0.11 s: Point26t 0.77 -> 0.67, start
PTP -0.01), 0 violations, joints 2328 -> 2315 deg; phase planks 68.0 -> 67.9, others unchanged. The reason held: the
383 mm start height was set only by the r4 box over plank6, which the -x side offset escapes; the floor is now the
wrist camera over plank4 (z 368 hit, 372 clean - L54), not r4. Kept. The program-only gains left are ~0.1 s each.
