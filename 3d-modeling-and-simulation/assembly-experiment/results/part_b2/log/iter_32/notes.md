# iter 32: pre-turn the tool in Line #47 (Point70ytt) toward Point80h so the frame-approach PTP is no longer J4-limited

## Hypothesis
Turn Point70ytt's tool orientation 40 % of the way toward Point80h's (toolbox/turn_toward.py 59 60 0.4, TCP kept).
The Line #47 (57.4 mm, rot 20 -> 28.9 deg) stays at ~0.58 s, the PTP #48 Point80h drops from J4 39.1 deg (0.78 s)
to J2 26.2 deg (0.52 s). Expected: -0.26 s exact (90.240 -> 89.985, rounds to 90.0), 0 violations. Change type: program.

## Reason
Evidence: toolbox/move_times2.py on the iter-30 best: #47 Point70ytt d 57.4 mm, rot 20.0 deg = 0.574 s distance-limited,
i.e. 8.7 deg of unused rotation budget (L30/L36: free rotation in distance-limited Lines), and the next PTP #48 Point80h
is J4-limited (39.1 deg, 0.78 s). show_joints: Point70ytt J4 -8.5, Point80h J4 -47.6; a slerp of the TCP orientation
toward Point80h moves J4 to -33 at g 0.4 while J2/J3/J6 also move toward Point80h's values, so no other joint takes
over above 26 deg (L38: print joints per g, stop where a second joint limits). scratch/exact27.py: g 0.15 / 0.2 / 0.3 /
0.4 / 0.5 -> 90.13 / 90.10 / 90.05 / 89.985 / 89.99 s; g 0.4 is the optimum (the Line becomes rot-limited at 28.9 deg).
Why this: every other movable move is at a rule floor (iter 27-31: r4 near points, base A box at Point80h (L59), elbow
over the guide); iter 31 attacked the same PTP via its end height and failed on r4, this attacks its limiting joint
instead, and the TCP path endpoints are unchanged, so r4 end conditions hold. Risk: the PTP's joint path changes shape
(L23/L29), so screen at 2 mm.
DFA / cell principle: shortest motion (joint-space balancing), no new events.

## Screenshots
- 00 start: frame 1 + pieces in base A, frame 2 in base B under the guide, planks upright in the base A edge slots / plank jig; arm at home over the far edge, same as iter 30.
- 01 plank6 released: plank6 stands in frame 1, the other five still upright in their slots; gripper over it, nothing floating.
- 02 plank5 released: two planks in frame 1, upright; arm pose as in iter 30.
- 03 plank4 released: three planks in frame 1, upright; no crooked parts.
- 04 plank3 released: four planks; the remaining two stand in their slots.
- 05 plank1 released: five planks in frame 1, all upright.
- 06 plank2 released: all six planks in frame 1, parallel, slots empty; gripper above the last plank (before the changed Line #47).
- 07 frame 1 released: frame 1 + planks upside down through the guide in base B, planks vertical, arm reaching to the base B edge from the -y side as before.
- 08 end: assembled bench in base B under the guide, base A empty, arm back at home; nothing floating.
- topview: TCP path unchanged in xy (the change is orientation only); the Point70 -> Point80h PTP (dashed purple, top) still runs outside the plank rows.

## Result
Expected -0.26 s (90.240 -> 89.985), got 90.0 s (exact 89.985), 0 violations, joints 2312 deg (unchanged). Phase
"frame 1 + planks" 17.1 -> 16.9 s; planks / home unchanged. The reason held: Line #47 had unused rotation budget and the
J4-limited PTP gave it up to J2 (26.2 deg) at g 0.4; the TCP endpoints did not move so r4 stayed clean, and the reshaped
joint path cleared everything at 2 mm. Kept.
