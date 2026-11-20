# Tool changes

One block per change to a tool in `toolbox/` (`## T<NN> (iter NN) <title>`: what, why, which iteration needed it, how it was tested), and any PROPOSED JUDGE FIX.

## T01 (iter 01) toolbox/slow_approach.py
What: post-processes a program json: for every grip/release with a vertical slow leg shorter than 50 mm, extends the
leg to 50.5 mm (in: retarget the preceding fast move up + insert a slow Line to the old leg top; out: insert a slow
Line up after the leg). IK via judge/tm5_kin seeded with the move's own joints. Non-vertical legs are reported, not touched.
Why: 12 of the 18 r3 violations in v3 were short slow legs. Needed by iter 01.
Tested: run on the v3 program (scratch/program_v3.json) -> 12 edits; judge 10 mm screen and 2 mm score: r3 18 -> 6,
no new kinematic problems. First version used exactly 50.0 mm and failed one event (L01) -> 0.5 mm margin.
Usage: `./py toolbox/slow_approach.py design/program.json` (in place; idempotent on already-fixed legs).

## T02 (iter 02) toolbox/guide_vertical.py
What: rewrites both guide transfers for the vertical grip notch: J6 += --j6 (default +90; iter 02 uses -90) on every
move from the approach to the retreat (flange from FK; a rotation about the flange axis), the fast Line that went
down beside the guide now ends 50.5 mm above the grip point, the release's horizontal slide out becomes a slow
vertical Line up 50.5 mm. Works on the iter-01 program by step names (Point5..Point15, second Point15..Point5).
Why: iter 02 (guide grip from above, r3 x4). Tested: 10 mm screens with +90 and -90 (both r3 6 -> 2; showed the
camera/plate hits, L04), then 2 mm score.
Usage: `./py toolbox/guide_vertical.py best/program.json --out design/program.json --j6 -90` (iter-01 program only).

## T03 (iter 02) toolbox/shift_moves.py
What: raises / lowers named moves (NAME[@occurrence]) by dz in robot z, same orientation, joints by IK seeded with
the move's own joints; fails if no IK.
Why: iter 02 raised base B by 70 mm; all base-B moves had to follow. Tested: 13+1 moves +70, 10 mm screen and 2 mm
score: r2 0 (all reachable, no limit hits).
Usage: `./py toolbox/shift_moves.py design/program.json 70 Point6 Point7@2 ...`

## T04 (iter 03) toolbox/shift_moves.py: --dx / --dy and NAME@all
What: the shift is now (dx, dy, dz) in the robot base frame (dz stays positional); NAME@all picks every move with that
name. Why: iter 03 moved the plank jig 60 mm (ground y -60 = robot (-0.025, +60, +0.028)); all 36 pick moves had to
follow. Tested: 36 moves shifted, all IK ok; 10 mm screen and 2 mm score r2 0.
Usage: `./py toolbox/shift_moves.py design/program.json 0.028 --dx -0.025 --dy 60 Point16@all Point17@all ...`

## T05 (iter 04) toolbox/insert_lift.py
What: inserts a fast Line before a named move: the previous move's flange shifted by (dx, dy, dz) robot base, same
orientation, joints by IK seeded with the previous joints; refuses solutions that jump > 60 deg in any joint (IK
branch change, L06). Why: iter 04 needed a lift out of the frame grip before the PTP Point82 (r4).
Tested: dz 120 -> "no IK"; dx 60 / dz 140 and dx 30 / dz 100 inserted, 10 mm screens, 2 mm score r2 0.
Usage: `./py toolbox/insert_lift.py design/program.json Point82 100 --dx 30 --name Point80L`

## T06 (iter 05) toolbox/swap_blocks.py
What: swaps two whole pick-and-place blocks (from the block's starting PTP to the PTP after its release); no new IK.
Why: iter 05 tried reordering plank1 / plank2. Tested: swap Point34 <-> Point52 blocks, 2 mm parts check: ran fine,
but the idea failed (L07). Usage: `./py toolbox/swap_blocks.py design/program.json Point34 Point52`

## T07 (iter 05) toolbox/swap_places.py
What: swaps the place halves (from the place PTP to the PTP after the release) of two blocks and renames the grip
before each half to the parts that half releases. Use with a start-slot swap in build_cell.py (PLANK_SLOT).
Why: iter 05 (plank1 / plank2 slot reassignment, L07). Tested: Point38 <-> Point56 on the iter-04 program, 2 mm parts
check (r1 at #76 gone) and 2 mm score (r2 0, r8 0). Usage: `./py toolbox/swap_places.py design/program.json Point38 Point56`
Also scratch/plank_pair.py: distance carried part vs another part along one move (diagnostic).

## T08 (iter 09) toolbox/drop_push.py (+ scratch/move_times.py)
What: after every plank release, replaces [slow up, DO1, down, up, DO0, fast transit] (the "push home") by
[slow vertical up 50.5 mm (IK seeded from the release joints, refuses > 60 deg jumps), fast transit]. Gripper ends
open as before. scratch/move_times.py prints the programmed time per move (cycle_time.py rules) to find where time goes.
Why: iter 09, the push was a no-op (plank released at its home pose already) costing ~2 s per plank.
Tested: run on the iter-08 program -> 6 pushes removed; 2 mm score: violations 0, cycle 229.6 -> 217.7 s.
Usage: `./py toolbox/drop_push.py design/program.json`

## T09 (iter 10) toolbox/shorten_slow.py
What: for every grip/release event of parts starting with --parts (default plank, --event release), if the slow
vertical leg before it is longer than --leg (50.5), lowers the end of the preceding fast Line so the leg becomes
--leg (same xy/orientation, IK seeded from its own joints, refuses > 60 deg jumps). Skips non-vertical legs.
Why: iter 10, plank places had 75 mm slow legs (r3 needs 50). Tested: 6 legs shortened on the iter-09 program,
10 mm screen and 2 mm score: violations 0, cycle 217.7 -> 211.8 s.
Usage: `./py toolbox/shorten_slow.py design/program.json [--parts frame --event release]`

## T10 (iter 11) toolbox/guide_ptp.py (+ scratch/dump_range.py, scratch/cell_bounds.py)
What: rewrites the outbound guide transfer: Point4/Point5 Lines -> one PTP Point6h (Point6 flange at --za) before
the fast Line down to Point6; Point9/Point10/Point11/... -> fast Line Point9h up to --zb + one PTP Point11h (the
flip, Point11 flange at --zc) before the Line down to Point12. IK seeded from the replaced moves, refuses > 60 deg
jumps. scratch/dump_range.py prints moves by step index; scratch/cell_bounds.py prints every object's bounds.
Why: iter 11, long 100 mm/s Lines cost more than PTPs (50 deg/s). Tested: 4 parameter screens at 10 mm (L13), then
the 2 mm score with za 265 / zb 320 / zc 355: violations 0, cycle 211.8 -> 202.8 s.
Usage: `./py toolbox/guide_ptp.py best/program.json --out design/program.json --zb 320 --zc 355`

## T11 (iter 12) toolbox/guide_ptp_return.py
What: the iter-11 rewrite for the return guide transfer: [Point71, Point72, Point15] after Point70 -> one PTP Point14h
(Point14 flange at --za, IK seeded from Point15) before the Line down to Point14; [Point11, Point74, Point9] after
Point73u -> Line Point11r up to --zb + PTP Point9r (Point9 flange at --zc, flip included) before Point75. Reuses
at_z/first from guide_ptp.py. Why: iter 12, ~22 s of 100 mm/s Lines. Tested: 10 mm screens zc 340 / 300 (0
violations each), then the 2 mm score with za 350 / zb 350 / zc 300: violations 0, cycle 202.8 -> 194.6 s.
Usage: `./py toolbox/guide_ptp_return.py best/program.json --out design/program.json --za 350 --zb 350 --zc 300`

## PROPOSED JUDGE FIX (noted iter 11): Line time ignores orientation change
cycle_time.py times a Line as TCP distance / speed only, so a Line with a large reorientation and ~0 mm TCP travel
costs 0 s (v3 already has such moves: Point2, Point70, Point77, Point83 with d = 0). A real controller also limits
the rotational speed of a Line. Suggested: time = max(dist / speed, rot_angle / joint_speed or a TCP rotation
limit). I have not exploited this (no new zero-length reorientation Lines); listed so the re-score is fair.

## T12 (iter 13) toolbox/lower_transit.py
What: for every grip/release of parts starting with --parts (plank), every move between the neighbouring events with
the same flange xy (--xy 2 mm) and flange z more than --min above the event point is a transit point; its flange z
becomes event z + --dz (--dz-grip for grips if given), IK seeded from its own joints, refuses > 60 deg jumps. Why:
iter 13, the plank transits at TCP z 391 cost fast vertical Lines. Tested: screens dz 102.5 (r4 6, L14), dz-grip
117.5 / dz 102.5 (10 mm clean, 2 mm r4 2, L15), then the 2 mm score with dz 117.5: violations 0, 194.6 -> 190.8 s.
Note: Point70 (a reorientation Line after the last place, different flange orientation) is not matched and stays at
TCP 391, so it is now an 8 mm Line instead of 0 mm (no new zero-length reorientation Line).
Usage: `./py toolbox/lower_transit.py best/program.json --out design/program.json --min 100 --dz 117.5`

## T13 (iter 14) toolbox/frame_ptp.py
What: after the guide release on base B, Point6u -> new Line Point6v (Point6u flange at --za) -> new PTP Point80h
(the point at fraction --f along the old diagonal Line Point79 -> Point80, same tilted orientation, IK seeded from
the interpolated joints, refuses > 30 deg jumps) -> the rest of Line Point80. Removes Point5, Point76..Point79.
Why: iter 14, ~11.5 s of Lines + small PTPs on the frame-1 approach. Tested: 10 mm screens za/f 330/0.35 (clean,
187.1 s), 300/0.4 and 320/0.5 (r3 low traverse of the remaining Line + r4 near), 300/0.38 (r4 near), 280/0.35
(clean, 186.6 s), then the 2 mm score with 280/0.35: violations 0, 190.8 -> 186.6 s.
Usage: `./py toolbox/frame_ptp.py best/program.json --out design/program.json --za 280 --f 0.35`

## T14 (iter 15) toolbox/retreat_ptp.py
What: after the frame-1 release, Point88 -> new Line Point88h (Point87 flange z + --dz, IK via guide_ptp.at_z) ->
the existing PTP Point92 -> Line Point1; removes Point90, Point91. Why: iter 15, the 342 mm diagonal retreat Line
(3.4 s). Tested: 10 mm screens dz 110 / 130 / 160 (all clean), then the 2 mm score with dz 110: violations 0,
186.6 -> 185.5 s.
Usage: `./py toolbox/retreat_ptp.py best/program.json --out design/program.json --dz 110`

## T15 (iter 16) toolbox/shorten_lift.py
What: mirror of shorten_slow.py for the lift AFTER a grip/release: lowers the slow vertical Line's target to the
event flange z + LEG (default 50.5), IK seeded from its own joints, refuses > 60 deg jumps; the following fast Line
keeps its target. Why: iter 16, plank pick lifts were 60 mm slow (r3 needs 50). Tested: 6 lifts shortened, 10 mm
screen and 2 mm score clean, 185.5 -> 183.2 s.
Usage: `./py toolbox/shorten_lift.py design/program.json [--parts plank --event grip --leg 50.5]`

## T18 (iter 18) toolbox/lift_ptp.py
What: replaces the 350 mm diagonal Line Point15 after the guide release on base A by a vertical Line Point15v (the
Point14u flange raised to TCP z TCPZ, IK via guide_ptp.at_z, branch-jump guard), followed by the unchanged PTP Point16.
Why: iter 18, the old Line climbed to TCP z 461 for no reason (3.5 s). Tested: TCPZ 355 / 380 10 mm screens clean,
2 mm score clean, 182.2 -> 181.2 s.
Usage: `./py toolbox/lift_ptp.py IN.json --out OUT.json [--tcpz 355]`

## T19 (iter 19) toolbox/j6_wrap.py, toolbox/set_ptp_z.py
What: j6_wrap.py adds --turn (default 360) to J6 for every move from --from (n-th) through --to (n-th), same poses,
refuses |J6| > 270. set_ptp_z.py moves one named step straight to a new flange z (IK via guide_ptp.at_z).
Why: iter 19; set_ptp_z for the low Point11h / Point14h screens (dead end, L19), j6_wrap for the 289 deg J6 turn in
PTP #33. Tested: j6_wrap Point11h..Point25(2nd) 10 mm screen + 2 mm score clean, 181.2 -> 176.9 s; the
Point14h..Point11r range screened r1 1 (guide flips into plank6).
Usage: `./py toolbox/j6_wrap.py IN.json --out OUT.json --from Point11h --to Point25 --to-nth 2`

## T21 (iter 21) toolbox/set_ptp_xyz.py: move a step to an xy offset + absolute flange z
What: like set_ptp_z.py, plus --dx/--dy (robot base mm) and --ref (take the flange xy from the next step of that name,
e.g. the Line end below it). Keeps the orientation, IK seeded from the step's joints, refuses > 60 deg branch jumps.
Why: iter 21, to put the guide-carry PTP end beside (not above) the grip pocket so r4's 100 mm sphere around the
plank release points no longer forces it up. Tested: 6 variants screened at 10 mm (IK fine, branch kept), the
(40, 40, 310) variant scored at 2 mm with 0 violations.
Usage: `./py toolbox/set_ptp_xyz.py IN.json --out OUT.json --name Point11h --ref Point12 --dx 40 --dy 40 --z 310`

## T22 (iter 22) toolbox/side_transit.py: plank transits beside the plank's thin box
What: for every single-plank grip/release, moves the transit points (same xy as the event, > MIN above it) OFF mm
along the plank's thin xy axis (start box for picks, nearest piece A box for places; signs --sg / --sr) and to event
z + DZ; IK seeded, > 60 deg jumps refused.
Why: iter 22, r4's box check (top + 100) no longer applies beside a 5 mm thick plank, only the 100 mm sphere, so the
fast 67 mm Lines become ~52 mm diagonals (-3.3 s).
Tested: both sign variants screened at 10 mm and 2 mm (--sg 1 --sr -1 fails r4 at 2 mm; defaults --sg -1 --sr 1 clean);
scored at 2 mm with 0 violations.
Usage: `./py toolbox/side_transit.py design/program.json --out OUT.json --off 10 --dz 102`

## T24 (iter 24) toolbox/home_on_path.py: home pose on the joint path between the last lift and the first approach
What: sets the first and last move (both named Point1) to the joints at fraction f of the joint path from A
(default Point88h, the last lift) to B (default Point6h, the first approach), flange by FK, and drops the moves
between home and B at the start and between A and home at the end (non-move steps kept).
Why: iter 24, the old home on the J5 < 0 branch cost two wrist branch changes per cycle (-4.2 s).
Tested: f 0.4 and 0.6 screened at --step 2 (both 0 violations, 165.8 s); f 0.6 scored at 2 mm, 0 violations.
Usage: `./py toolbox/home_on_path.py design/program.json OUT.json 0.6 [A] [B]`

## T25 (iter 25) toolbox/drop_range.py: cut whole step ranges between two named moves
What: drops every step (moves AND DO/wait steps) strictly between a move named FROM and the next move named TO,
for each FROM:TO pair given; prints what it drops.
Why: iter 25 removed the guide's round trip (base B -> A -> B) including its grip/release DO steps.
Tested: g25a (Point1:Point16 Point70:Point80h) dropped 30 steps, listed names checked by hand; 2 mm screen ran
(r4 1 from the new home PTP, fixed with home_on_path.py Point88h Point16 f 0.7).
Usage: `./py toolbox/drop_range.py IN.json OUT.json FROM:TO [FROM:TO ...]`

## T27 (iter 27) toolbox/rotate_picks.py: turn a plank's pick block with its jig slot
What: for each named plank, applies the rigid motion of its start pose (ANGLE deg about the vertical through its
slot centre, ground frame, from build_cell PLANK_JIG/PITCH/PLANK_SLOT) to every move of its pick block (the PTP to
the pick transit .. before the next PTP), IK seeded with J6 - ANGLE, > 60 deg jumps refused. --mirror puts the
side-offset transits on the other side of the grip point (L27).
Why: iter 27, planks 4-6 presented turned 80 deg (as they sit in frame 1) to drop the J6 turns.
Tested: without --mirror r4 3 (L27); with --mirror + reorder (swap_blocks.py) + plank2 transit +20 mm: 0 violations
at 2 mm, 116.2 s; scored.
Usage: `./py toolbox/rotate_picks.py IN.json OUT.json 80 plank4 plank5 plank6 --mirror`

## T28 (iter 28) toolbox/line_to_ptp.py, toolbox/flip_branch.py
What: line_to_ptp.py turns a named Line into a PTP (same joints, joint_speed 49.95). flip_branch.py (unused in the
kept design) replaces the moves between two names with one PTP onto the other wrist branch and re-solves the
following Lines; it stops with "no IK on the other branch" when that branch does not exist (L28).
Why: iter 28, the frame flip Line (2.75 s) is only J5 124 deg = 2.48 s as a PTP.
Tested: line_to_ptp + set_ptp_z (Point85 flange z 371): 2 mm screen 0 violations 115.8 s; scored, kept.
Usage: `./py toolbox/line_to_ptp.py IN.json OUT.json Point85`

## T29 (iter 29) toolbox/ptp_along.py: slide a PTP end along the Line that follows it
What: moves the PTP's flange position to fraction F toward the next Line's end (orientation kept, IK seeded by joint
interpolation, branch jumps > 30 deg refused); prints the new TCP, the Line length and horizontal length left.
Why: iter 29, the frame-grip approach Line (319.5 mm, 3.2 s) could be cut once <= 100 mm horizontal is left (L29).
Tested: f 0.52 / 0.60 / 0.68 / 0.76 on design/program.json, each 2 mm-screened; f 0.76 + set_ptp_xyz Point70 dy +30
scored 0 violations, 113.4 s, kept.
Usage: `./py toolbox/ptp_along.py IN.json --ptp Point80h --line Point80 --f 0.76 --out OUT.json`

## T30 (iter 30) scratch/lift_frac.py
What: moves the end of a named Line to fraction F of the way from the previous move (flange xyz lerp, same
orientation), IK seeded from the old joints, refuses jumps >= 60 deg. Why: iter 30, shorten the fast lift
Point80u -> Point80L after the frame-foot grip. Tested: f 0.8 / 0.7 / 0.6 / 0.55, each 2 mm-screened clean; f 0.55
scored 112.9 s, 0 violations. Usage: `./py scratch/lift_frac.py IN.json OUT.json Point80L 0.55`

## PROPOSED JUDGE FIX (iter 30) cycle_time: a Line's time ignores orientation change
judge/cycle_time.py `estimate()` times a Line as TCP distance / speed only, so a pure re-orientation Line (TCP fixed,
tool turning) costs 0 s; v3 and the final program both contain one (Point82 -> Point83, the tool turns ~35 deg about
the TCP: 0.00 s). A real TM controller limits the rotational speed of a Line too. Suggested fix: time = max(TCP
distance / speed, rotation angle / a rotational speed limit, e.g. the PTP joint speed), or the largest joint change /
joint speed. Effect on the final program: a few tenths of a second; no program relied on it on purpose.
