# Lessons (problems and fixes)

One block per problem, written at once (AGENT.md "Self-learning rule"). Read in full at the start of every iteration.

## L01 (iter 01) A slow leg of exactly 50.0 mm still fails r3
**Problem:** after extending the frame-grip approach leg to exactly 50.0 mm, r3 still said "move #116 (line, 100.0 mm/s) inside the last/first 50 mm".
**Cause:** score.py walks back move by move and stops only when the summed path length is >= 50; with float error it ends at 49.99..., so the next (fast) move is checked and flagged even though none of its points are inside.
**Fix:** toolbox/slow_approach.py extends legs to 50.5 mm (MARGIN = 0.5).
**Lesson:** always give judge thresholds a small margin (approach legs 50.5 mm, clearances > 10 mm with slack), never aim at the exact limit.

## L02 (iter 01) sed / chained shell edits are denied in this session
**Problem:** a Bash command chaining `sed -i` edits + rerun was denied ("don't ask mode").
**Cause:** the permission mode blocks some shell commands (in-place sed edits, long chains).
**Fix:** edit files with the Edit/Write tools; keep Bash for `./py ...` runs.
**Lesson:** use Edit/Write for file changes, Bash only for running ./py scripts and simple listing.

## L03 (iter 01) The 10 mm screen under-counts r1/r5
**Problem:** screen at --step 10 gave 14 violations (r1 5, r5 2); the 2 mm score gave 17 (r1 6, r5 4).
**Cause:** coarse sampling misses short contacts and low-clearance samples; also r1 counts per move, so splitting a colliding move into two adds a violation.
**Fix:** none needed; scored at 2 mm.
**Lesson:** treat the 10 mm screen as optimistic for r1/r5; don't split a move that already collides (fix the collision first) - each piece is counted.

## L04 (iter 02) Turning J6 by 90 deg puts the TM5 wrist camera into the plate
**Problem:** rotating the gripper 90 deg about the tool axis (J6 +-90) for the guide grip gave r1 hits "Ground base plate/link_6, Table/link_6" (7 moves); link_6 then reaches 55 mm below the plate top at the grip point (scratch/link6_low.py).
**Cause:** link_6 carries the built-in camera, offset ~62 mm from the wrist axis. With the tool horizontal and TCP 50 mm above the plate, the camera must point sideways (J6 as in v3); +-90 points it down at one of the two bases (the 180 deg guide flip about the tool axis couples both bases, so no sign works for both).
**Fix:** raise base B on an 80 mm riser (+70) and shift its moves +70 (toolbox/shift_moves.py), J6 -90.
**Lesson:** with a horizontal tool near the plate, check link_6 (camera) height before changing J6; the gripper body is not the only thing around the wrist.

## L05 (iter 03) Moving the plank jig created a contact at the final insertion (L03 again for the screen)
**Problem:** after moving only the plank jig (+ the pick moves), the 2 mm score showed a new r1 "Base B/plank3" at move
126 (frame 1 + planks lowered into frame 2); the 10 mm screen showed r1 0 (and missed plank1/plank2 too).
**Cause:** (suspected) a carried part keeps the pick-time offset to the TCP; the pick moved by robot (-0.025, 60, 0.028)
while the jig moved by exactly ground -60 y, so plank3's pose in frame 1 changed by hundredths of a mm - enough to tip
an already zero-clearance contact at base B. The final insertion has no slack.
**Fix:** none this iteration (net 8 -> 4); the frame-release cluster is the next target.
**Lesson:** the final insertion into base B is at ~0 mm clearance: after any change that touches plank poses, expect
the 2 mm score to flip contacts there; give that pocket / the guide slots slack (CAD) instead of relying on luck.

## L06 (iter 04) Frame lift-out: a diagonal Line hits the guide, a vertical lift is out of reach
**Problem:** to fix r4 (PTP Point82 right after the frame grip) (a) turning the PTP into a straight Line gave a new r1
Guide/frame1 at the same move and +3.7 s; (b) a straight-up Line from Point80u has no IK above +70 mm flange z
(IK jumps to J1 -200, another branch; scratch/probe_lift.py).
**Cause:** the frame foot grip at robot x -747 / y 196 is at the edge of the reach with the horizontal tool; the
carried frame + upright planks sweep a large volume, and a straight line toward the robot drags it low past base B.
**Fix:** lift diagonally toward the robot (dx +60, dz +140 flange), which stays on the branch, then the PTP.
**Lesson:** before adding a lift, probe IK along it (scratch/probe_lift.py pattern) and reject solutions that change
branch (toolbox/insert_lift.py now refuses > 60 deg joint jumps); near the reach edge, move inward while lifting.

## L07 (iter 05) Carried planks hit standing planks: pick order and place order conflict
**Problem:** r1 plank1/plank2 at the plank1 transit (#76). Raising the transit +80 mm: still a hit. Swapping the
plank2 / plank1 blocks: new hit plank1/plank2 *in the plank jig* (#50).
**Cause:** planks are 250 mm long, carried only ~125-145 mm above their pick / release height, so a carried plank's
lower end sweeps through any upright plank it passes over: in the jig (picks must go outer-first, away from the
robot) and in the guide (places must go robot-side-last). With plank1 in the robot-side jig slot but the outer
guide slot, both orders fail.
**Fix:** swap plank1 / plank2 start slots (build_cell.py PLANK_SLOT) + swap the place halves of the two blocks
(toolbox/swap_places.py). No extra moves, cycle unchanged.
**Lesson:** measure the actual contact first (scratch/plank_pair.py: carried part bounds vs the other part per
sample) before choosing a fix; for identical parts, reassign start slots so pick order and place order agree
instead of raising transits (costs time).

## L08 (iter 07) L02 again: inline `./py -c "..."` is denied too
**Problem:** a one-off `./py -c "import build123d ..."` (and a chained `cd && cat ...` read) was denied in don't-ask mode.
**Cause:** same as L02: only plain `./py <script>` runs and simple listing pass.
**Fix:** wrote the snippet to scratch/bench_bounds.py and ran that; read logs with the Read tool.
**Lesson:** every probe goes into a scratch/*.py file first; never inline Python or chained shell reads.

## L11 (iter 08) L02/L08 again: a background subshell + chained runs was denied
**Problem:** `(./py a.py > x &) ; ./py b.py | tail; sleep 1; cat x` was denied in don't-ask mode.
**Cause:** same as L02/L08 (subshells, sleep, chains).
**Fix:** ran the two ./py scripts as separate Bash calls in the same message (parallel tool calls).
**Lesson:** for parallel screens use parallel Bash tool calls, each a single `./py ...`, never `&`/subshells.

## L12 (iter 08) The STEP plank is a plain box; the plank mesh end is two 2 mm tabs around the piece
**Problem:** slicing the STEP plank's lowest 1 mm gave the whole 25 x 5 end (2.1 cm3 removed = iter 07 again).
**Cause:** plank_body.stl (what the judge uses) has a 2 mm tab at each end of its 25 mm width with the interface piece
between them (scratch/footprints_b.py); the STEP plank has a flat end.
**Fix:** build the tab rectangles from the STEP end face (2 mm at each end of the long edge, + 0.75 mm).
**Lesson:** the judge's meshes (design/meshes/bench) are the truth, not the STEP; measure footprints from the meshes.

## L13 (iter 11) A PTP replacing Lines: r4 counts EVERY grip/release point, and the wrist sweeps the plank jig
**Problem:** first screen of the guide carry as one PTP (TCP z 245 -> 220): r4 "Point11h within 100 mm of a grip/
release point", r3 low traverse (max TCP z < 311 = tallest object + 50), r1 link_5 / link_6 vs the planks in the jig.
**Cause:** the near check uses all grip/release points of the whole program (the plank release points over base A
at TCP z 265 were 75 mm away), the low-traverse check needs the move's highest TCP point >= 311 mm when it travels
> 100 mm horizontally, and during the J1 swing the wrist / camera passes over the plank jig (plank tops z 261).
**Fix:** PTP end over base A at flange z 355 (104 mm from the nearest plank release point), start over base B at 320.
**Lesson:** before a new PTP, check its endpoints against all grip/release TCP points (not just the current part),
end above 311 mm if it travels > 100 mm, and keep the wrist >= ~60 mm over the plank tops when J1 swings past the jig.

## L09 (iter 07) The last r1 (Base B/plank3 at #127) is a zero-depth resting contact, not a sweep
**Problem:** r1 "Base B/plank3" at the final insertion move persisted through iters 03-06.
**Cause:** scratch/jig_pair.py + scratch/release_dbg.py: plank3 never penetrates Base B on the way down; at the
release pose all 6 plank ends sit flush (depth 0.0) on the base B pocket floor (frame outer face = plank ends,
z 9.5 base-local). FCL reports 5 of the 6 touching at the release pose (allowed), but plank3's exact-touch flips
between samples, so it's counted as a hit. Pure numerical luck (cf. L05).
**Fix:** (iter 07) relief recesses in the base B pocket floor under the plank ends, so planks never touch the jig.
r1 went to 0, but see L10.
**Lesson:** a flush zero-depth contact is a coin flip for the checker; design 1-2 mm of relief where a part end
lands flush on a jig, rather than nudging poses.

## L10 (iter 07) Relief under the plank ends made 4 interface pieces B float at the start
**Problem:** with 2 mm recesses (plank xy bbox + 1 mm) in the base B floor: r1 0 but r6 4 ("start: piece B1, B2,
B3, B6 floats"); also the first two recess outlines (end face / a section) were too small because plank_body's end
is narrower than its body.
**Cause:** the interface pieces B stand in frame 2 at the plank positions and rest on the same floor patch the
plank ends land on; the recess took away their support. The judge's rest check drops each part a little and needs
a contact.
**Fix:** none this iteration (rejected).
**Lesson:** before cutting a jig surface, list every part that rests on it at the start AND the end (score.json
"rest" + a start rest check) and keep a support ledge for each; measure the real mesh footprints (scratch/
rest_local.py) instead of assuming from the STEP.

## L14 (iter 13) r4 "TCP < 100 mm above plankN": the part about to be picked is not held during the PTP to it
**Problem:** lowering every plank transit to event + 102.5 mm (pick TCP z 348): r4 6 ("PTP move #16 (Point16): TCP <
100 mm above plank3", one per pick).
**Cause:** r4's box check treats every part not yet gripped as an obstacle; the PTP ending over the plank to pick has
its TCP inside that plank's xy box, so the TCP must be >= plank top (261) + 100 = 361, not just 100 mm from the grip
point (346).
**Fix:** pick transits at TCP z ~363, place transits at event + 102.5 (~368: the placed planks are not under the TCP).
**Lesson:** a PTP endpoint above a part to grip needs TCP >= that part's top + 100 (L13 check list: grip/release
points, tops of all unheld parts under the path, 311 low-traverse).

## L15 (iter 13) L03/L14 again: the 10 mm screen missed r4 over the plank just released
**Problem:** screen (10 mm) of pick transits 363 / place transits event + 102.5 (~368): 0 violations; the 2 mm score:
r4 2 ("PTP move #27 (Point25): TCP < 100 mm above plank3", same for plank1).
**Cause:** the PTP leaving a place transit starts directly over the plank just released (now unheld, top 280.7), so
it needs TCP >= 380.7; the coarse sampling only caught it at the first sample in 2 of 6 cases by luck.
**Fix:** place transits at event + 117.5 too (TCP ~383).
**Lesson:** after a release the part becomes an obstacle for the next PTP's start: both ends of every PTP must be
>= 100 mm over the top of any unheld part under them; don't trust a 10 mm screen for r4 box checks near the ends.

## L16 (iter 14) L06 again: no IK for a point straight above the frame-foot grip
**Problem:** toolbox/frame_ptp.py first version put the PTP end at the Point80 flange xy at flange z 385: "no IK for
Point80h at z 385.0".
**Cause:** same as L06: the foot grip is at the reach edge with the tilted tool (rx -120); straight up has no IK
above ~+70 mm. I had read L06 but designed the vertical approach anyway.
**Fix:** PTP to a point at fraction f along the existing diagonal Line Point79 -> Point80 (IK exists along it), then
the rest of the Line.
**Lesson:** to shorten a Line with a PTP, end the PTP ON the existing (known-reachable) Line, not at a new point.

## L17 (iter 14) The Line after a new PTP can become a low traverse
**Problem:** screens with f 0.4 / 0.5 along the diagonal: r3 "low traverse: move #96 below the safe height (311 mm)".
**Cause:** the remaining Line still travels > 100 mm horizontally, so its highest TCP point (its start) must be
>= 311; at f 0.4 the start was 310.
**Fix:** f 0.35 (Line starts at TCP ~329).
**Lesson:** any move (Line too) travelling > 100 mm horizontally must reach >= 311 TCP z somewhere; check that when
splitting a long descending Line.

## L18 (iter 14) Write on an existing log file replaced it (lessons.md wiped to 3 blocks)
**Problem:** I used Write with only the new blocks to "append" to log/lessons.md; the file then held only L15-L17.
**Cause:** Write overwrites the whole file; it is not an append.
**Fix:** rewrote the full file from the copy read at the start of the session (all blocks L01-L17 restored).
**Lesson:** to append to a log, use Edit anchored on the last block's last line; never Write an existing log file
unless the full content is in the call.

## L19 (iter 19) The low r4 window under the plank release points is blocked by the arm, not by r4
**Problem:** PTP ends over the base A guide grip at TCP 173 / 182 (below the plank release points, |dz| >= 80):
r4 0, but r1 link_4/link_5 vs plank1..5 in the plank jig (Point11h, carry) and EGP/plank2 + r4 "TCP < 100 mm above
plank1" (Point14h, return over the placed planks).
**Cause:** a PTP interpolates joints, so a low end point drags the wrist low through the middle of the J1 swing,
which crosses the plank jig (~68 % of the way); on the return the TCP passes over the standing planks (top 281).
**Fix:** dropped the idea; iter 19 changed to the J6 wrap (below).
**Lesson:** a PTP end lowers the whole swing, not just the end; check what the wrist passes over mid-swing before
lowering an end point. Look for the cheapest gains first: per-move times (scratch/move_times.py) and J6 values
(scratch/j6_list.py) - a joint going the long way round (> 180 deg) is a free win.

## L20 (iter 20) Reversing a carried-part flip direction needs height, found by a z sweep
**Problem:** guide return grip wrapped to J6 +180 (shorter PTP from plank4): the +180 -> 0 flip turns the guide the
other way; with the lift end Point11r at flange z 375 (was 350): r1 Guide/plank6 at #89 (10 mm screen).
**Cause:** the reversed rotation swings the guide's far end down over the standing planks in frame 1.
**Fix:** sweep the lift end z (375 hit, 400 / 450 clean), scored 410 for slack: 0 violations, -1.5 s.
**Lesson:** when a J6 wrap reverses a flip with a part held, raise the lift before the flip and sweep its z in
parallel screens; a 100 mm/s lift costs only 0.25 s per 25 mm, far less than a long J6 turn.

## L21 (iter 21) L19 again: a side offset clears r4 but not the wrist sweep over the plank jig
**Problem:** Point11h moved 40/40 mm sideways (117 mm from the nearest plank release point, so r4 holds at any z),
then lowered: flange z 260 / 280 / 290 all gave r1 link_5 (and EGP) vs plank1..5 in the jig at #10; 300 was clean.
Also `scratch/move_times.py` needs the program path as an argument (IndexError without it).
**Cause:** same as L19: the PTP end height sets how low the wrist passes over the plank jig mid-swing; the floor is
~300 flange z whatever the xy offset.
**Fix:** scored z 310 (-0.4 s instead of the hoped -0.8 s).
**Lesson:** for the guide carry PTPs over the plank jig the wrist floor is ~300 flange z; gains below that need the
plank jig moved or the swing routed differently, not a different end point. Run move_times.py with the program path.

## L22 (iter 22) L15 again: side-offset transits clean at 10 mm, r4 3 at 2 mm
**Problem:** plank transits offset 10 mm out of the plank's thin box and lowered to event + 102 (variant sg +1 /
sr -1): 10 mm screen 0 violations, 2 mm score r4 3 ("PTP move #16 (Point16): TCP < 100 mm above plank3", #38 above
plank6, #60 above plank5).
**Cause:** a 5 mm thin box is crossed by the curved PTP path within a few mm of its end/start; the 10 mm sampling
steps over it. The 10 mm screen cannot judge thin-box r4 at all.
**Fix:** screened the other sign variant at --step 2 directly with judge/score.py before deciding (see iter 22 notes).
**Lesson:** for any r4-sensitive change near thin parts, screen with `--step 2 --no-shots` (~15-60 s), not 10.

## L23 (iter 23) Moving a PTP's START sideways bends its path over a thin plank box at the other end
**Problem:** Point15v (start of the PTP to the plank3 pick) moved dx +40 / dy +40: r4 "PTP move #16 (Point16): TCP <
100 mm above plank6" at z 250, 290 and 330 alike. Also: chaining set_ptp_xyz on an output that already had the
offset doubled it (dx 80) - rebuild every variant from design/program.json or a known file.
**Cause:** a PTP interpolates joints; the J1/J2 change at the start reshapes the approach near Point16, which sits
only 10 mm beside plank3's box and 20 mm from plank6's. The end height, not the start height, was not the problem.
**Fix:** dy +40 only (dx 0) at flange z 320: clean.
**Lesson:** when a PTP ends next to a thin part, prefer start offsets that keep J1 close to the end's J1 (here: no
x shift), and screen x and y offsets separately at 2 mm.

## L24 (iter 24) The frame flip cannot stay on the J5 < 0 wrist branch
**Problem:** dropping the J5-only flip Point84 and following the flip Line Point83 -> Point85 on the J5 < 0 branch
(scratch/wrist24.py): "FAIL Point85 110 160" - not followable at 69 %, J4 at -172 and running toward -180, IK None.
**Cause:** on the other wrist branch J4 = J4 - 180; the frame flip turns J4 by ~+106 the other way, so it runs into
the -180 limit. That is why v3 flips J5 before the Line.
**Fix:** dropped; changed the home pose instead (the J5 > 0 branch at the end and at the start made the old home
on J5 < 0 cost two branch changes).
**Lesson:** before switching a wrist branch on a long rotating Line, probe it with kin_check.follow_line (J4/J6
limits). Look for branch changes caused by a fixed-looking pose (home) - the judge has no home rule.

## L25 (iter 25) L23 again: a new PTP from the -y side bends over the thin plank6 box; and question whole phases
**Problem:** after dropping the guide trip, the new PTP home -> Point16 (plank3 pick transit) gave r4 "TCP < 100 mm
above plank6"; moving Point16 10 mm to the outer side (dy +20) gave r4 above plank3 instead.
**Cause:** same as L23: the joint-interpolated approach from the old home (y -197) sweeps over the neighbouring
thin box near the PTP end; nudging the end point only moves which box it clips.
**Fix:** put home on the joint path of the end lift -> Point16 (home_on_path.py Point88h Point16, f 0.7): clean.
**Lesson:** fix an r4 thin-box hit at a PTP end by changing where the PTP comes from (its start / home), not the end.
Bigger one: 24 iterations polished moves inside a phase (guide) that was not needed - frame 1 already holds the
planks alone in v3's phase 3/4. Before tuning a phase, ask whether the phase (a fixture trip, a flip, a regrasp)
is needed at all; check the DO grip/release sequence stays consistent when steps are removed.

## L26 (iter 26) A shorter reach does not shorten a PTP whose time is set by J6
**Problem:** moving the plank jig 100 mm toward base A was expected to save ~3.5 s; it saved 0.8 s, and the three
place PTPs to the A4..A6 row got slower (1.44 -> 1.52 s).
**Cause:** a PTP's time is set by its largest joint change; those planks turn ~75 deg about vertical (J6 162 -> 87),
which no layout shift removes; only the J2/J3-limited PTPs gained.
**Fix:** kept (still better); the J6 turn is the next target (present those planks pre-rotated).
**Lesson:** before a layout change aimed at PTP time, list each PTP's limiting joint (scratch/j6_list.py) and
count only the PTPs limited by the joints the change affects.

## L27 (iter 27) L23 again: rotating a pick block with its plank also rotates the transit's side offset
**Problem:** planks 4-6 turned 80 deg in the jig, their pick moves rotated rigidly with them (toolbox/rotate_picks.py):
2 mm screen r4 3 ("PTP move #35 (Point25): TCP < 100 mm above plank6", same for plank5 / plank4).
**Cause:** the iter-22 transit sits 10 mm beside the plank's thin box on the -y robot side; turned 80 deg with the
plank it now sits on the robot side (+x), so the PTP arriving from base A (outer side) crosses the thin box at its end.
**Fix:** rotate_picks.py --mirror puts those transits on the other side of the grip point (outer side).
**Lesson:** when a part's presentation turns, re-check which side its side-offset transit is on relative to where
the PTPs come from and go to; a rigid copy of the old moves is not enough.

## L28 (iter 28) The frame release has no J5 < 0 wrist solution; J5 sets the whole end of the cycle
**Problem:** toolbox/flip_branch.py (flip PTP onto the other wrist branch at Point85): "no IK on the other branch";
scratch/alt28.py (multi-seed DLS) finds only J5 +138 solutions near J1 20 (the others are J1 -143, the far side).
**Cause:** the TM5 wrist is not spherical; at the reach edge (TCP -747/-197, tilted tool) the J5-flipped solution
moves the wrist out of reach. The cycle's J5 path -90 (planks) -> -53 (frame grip) -> +138 (release) -> -90 is
already the minimum J5 travel (456 deg); the home leg (4.57 s) is purely J5-limited.
**Fix:** dropped the idea before scoring; changed to the Line -> PTP flip at the same branch.
**Lesson:** before a branch-change idea, list every IK solution of the critical poses (scratch/alt28.py <prog>
<name>); for a J5-limited stretch, total J5 travel over the cycle is the floor - only a different grip/presentation
changes it.

## L29 (iter 29) L25 again: a steeper PTP descent clips the box of the part under the PTP START
**Problem:** sliding the frame-approach PTP end Point80h down the diagonal (f 0.52 / 0.60 / 0.68): r4 "PTP #69
(Point80h): TCP < 100 mm above plank4" (at f 0.52 / 0.60 also within 100 mm of the plank4 release point).
**Cause:** the PTP starts at Point70 right over plank4 (TCP 391, limit 381); a lower end makes the joint path drop
below 381 while still in plank4's xy box. Also the low-traverse rule (L17) only binds a Line travelling > 100 mm
horizontally - an L17 limit can be escaped by ending the PTP where <= 100 mm horizontal is left.
**Fix:** moved the Line end Point70 30 mm in +y (out of all plank boxes); f 0.76 then clean (-2.4 s).
**Lesson:** when lowering a PTP end, check the boxes under its START too and move a Line-end start out of them;
re-read old "rule limits" (L17) for their exact condition - a long Line forced high may be cut short instead.

## L30 (iter 30) A Line's time is its TCP distance only: move_times "d=0.0, 0.00 s" on a re-orienting Line
**Problem:** I planned to merge the flip PTPs Point82 / Point84 around the Line Point83; move_times showed that Line
at 0.00 s although Point82 and Point83 have very different joints (J2 -40 vs -12, J5 -48 vs -14).
**Cause:** judge/cycle_time.py times a Line by TCP travel only; Point82 -> Point83 turns the tool about the TCP, so
it is "free". Any merge there would only add time (logged as a PROPOSED JUDGE FIX in tool_changes.md).
**Fix:** dropped the merge; shortened the over-long fast lift after the frame grip instead (-0.5 s).
**Lesson:** read how the judge times a move type before targeting it; over-long fast Lines next to an r4 limit
(PTP start >= 100 mm from the grip point) are cheap wins - end them at ~105 mm from the nearest grip point.
