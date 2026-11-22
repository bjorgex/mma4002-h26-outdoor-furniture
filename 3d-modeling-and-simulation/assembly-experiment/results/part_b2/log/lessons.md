# Lessons (problems and fixes)

L01-L30 are from run B (headings tagged "B iter NN"); run B2's lessons follow under "Run B2" and continue the numbering (L31, ...).

One block per problem, written at once (AGENT.md "Self-learning rule"). Read in full at the start of every iteration.

## L01 (B iter 01) A slow leg of exactly 50.0 mm still fails r3
**Problem:** after extending the frame-grip approach leg to exactly 50.0 mm, r3 still said "move #116 (line, 100.0 mm/s) inside the last/first 50 mm".
**Cause:** score.py walks back move by move and stops only when the summed path length is >= 50; with float error it ends at 49.99..., so the next (fast) move is checked and flagged even though none of its points are inside.
**Fix:** toolbox/slow_approach.py extends legs to 50.5 mm (MARGIN = 0.5).
**Lesson:** always give judge thresholds a small margin (approach legs 50.5 mm, clearances > 10 mm with slack), never aim at the exact limit.

## L02 (B iter 01) sed / chained shell edits are denied in this session
**Problem:** a Bash command chaining `sed -i` edits + rerun was denied ("don't ask mode").
**Cause:** the permission mode blocks some shell commands (in-place sed edits, long chains).
**Fix:** edit files with the Edit/Write tools; keep Bash for `./py ...` runs.
**Lesson:** use Edit/Write for file changes, Bash only for running ./py scripts and simple listing.

## L03 (B iter 01) The 10 mm screen under-counts r1/r5
**Problem:** screen at --step 10 gave 14 violations (r1 5, r5 2); the 2 mm score gave 17 (r1 6, r5 4).
**Cause:** coarse sampling misses short contacts and low-clearance samples; also r1 counts per move, so splitting a colliding move into two adds a violation.
**Fix:** none needed; scored at 2 mm.
**Lesson:** treat the 10 mm screen as optimistic for r1/r5; don't split a move that already collides (fix the collision first) - each piece is counted.

## L04 (B iter 02) Turning J6 by 90 deg puts the TM5 wrist camera into the plate
**Problem:** rotating the gripper 90 deg about the tool axis (J6 +-90) for the guide grip gave r1 hits "Ground base plate/link_6, Table/link_6" (7 moves); link_6 then reaches 55 mm below the plate top at the grip point (scratch/link6_low.py).
**Cause:** link_6 carries the built-in camera, offset ~62 mm from the wrist axis. With the tool horizontal and TCP 50 mm above the plate, the camera must point sideways (J6 as in v3); +-90 points it down at one of the two bases (the 180 deg guide flip about the tool axis couples both bases, so no sign works for both).
**Fix:** raise base B on an 80 mm riser (+70) and shift its moves +70 (toolbox/shift_moves.py), J6 -90.
**Lesson:** with a horizontal tool near the plate, check link_6 (camera) height before changing J6; the gripper body is not the only thing around the wrist.

## L05 (B iter 03) Moving the plank jig created a contact at the final insertion (L03 again for the screen)
**Problem:** after moving only the plank jig (+ the pick moves), the 2 mm score showed a new r1 "Base B/plank3" at move
126 (frame 1 + planks lowered into frame 2); the 10 mm screen showed r1 0 (and missed plank1/plank2 too).
**Cause:** (suspected) a carried part keeps the pick-time offset to the TCP; the pick moved by robot (-0.025, 60, 0.028)
while the jig moved by exactly ground -60 y, so plank3's pose in frame 1 changed by hundredths of a mm - enough to tip
an already zero-clearance contact at base B. The final insertion has no slack.
**Fix:** none this iteration (net 8 -> 4); the frame-release cluster is the next target.
**Lesson:** the final insertion into base B is at ~0 mm clearance: after any change that touches plank poses, expect
the 2 mm score to flip contacts there; give that pocket / the guide slots slack (CAD) instead of relying on luck.

## L06 (B iter 04) Frame lift-out: a diagonal Line hits the guide, a vertical lift is out of reach
**Problem:** to fix r4 (PTP Point82 right after the frame grip) (a) turning the PTP into a straight Line gave a new r1
Guide/frame1 at the same move and +3.7 s; (b) a straight-up Line from Point80u has no IK above +70 mm flange z
(IK jumps to J1 -200, another branch; scratch/probe_lift.py).
**Cause:** the frame foot grip at robot x -747 / y 196 is at the edge of the reach with the horizontal tool; the
carried frame + upright planks sweep a large volume, and a straight line toward the robot drags it low past base B.
**Fix:** lift diagonally toward the robot (dx +60, dz +140 flange), which stays on the branch, then the PTP.
**Lesson:** before adding a lift, probe IK along it (scratch/probe_lift.py pattern) and reject solutions that change
branch (toolbox/insert_lift.py now refuses > 60 deg joint jumps); near the reach edge, move inward while lifting.

## L07 (B iter 05) Carried planks hit standing planks: pick order and place order conflict
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

## L08 (B iter 07) L02 again: inline `./py -c "..."` is denied too
**Problem:** a one-off `./py -c "import build123d ..."` (and a chained `cd && cat ...` read) was denied in don't-ask mode.
**Cause:** same as L02: only plain `./py <script>` runs and simple listing pass.
**Fix:** wrote the snippet to scratch/bench_bounds.py and ran that; read logs with the Read tool.
**Lesson:** every probe goes into a scratch/*.py file first; never inline Python or chained shell reads.

## L11 (B iter 08) L02/L08 again: a background subshell + chained runs was denied
**Problem:** `(./py a.py > x &) ; ./py b.py | tail; sleep 1; cat x` was denied in don't-ask mode.
**Cause:** same as L02/L08 (subshells, sleep, chains).
**Fix:** ran the two ./py scripts as separate Bash calls in the same message (parallel tool calls).
**Lesson:** for parallel screens use parallel Bash tool calls, each a single `./py ...`, never `&`/subshells.

## L12 (B iter 08) The STEP plank is a plain box; the plank mesh end is two 2 mm tabs around the piece
**Problem:** slicing the STEP plank's lowest 1 mm gave the whole 25 x 5 end (2.1 cm3 removed = iter 07 again).
**Cause:** plank_body.stl (what the judge uses) has a 2 mm tab at each end of its 25 mm width with the interface piece
between them (scratch/footprints_b.py); the STEP plank has a flat end.
**Fix:** build the tab rectangles from the STEP end face (2 mm at each end of the long edge, + 0.75 mm).
**Lesson:** the judge's meshes (design/meshes/bench) are the truth, not the STEP; measure footprints from the meshes.

## L13 (B iter 11) A PTP replacing Lines: r4 counts EVERY grip/release point, and the wrist sweeps the plank jig
**Problem:** first screen of the guide carry as one PTP (TCP z 245 -> 220): r4 "Point11h within 100 mm of a grip/
release point", r3 low traverse (max TCP z < 311 = tallest object + 50), r1 link_5 / link_6 vs the planks in the jig.
**Cause:** the near check uses all grip/release points of the whole program (the plank release points over base A
at TCP z 265 were 75 mm away), the low-traverse check needs the move's highest TCP point >= 311 mm when it travels
> 100 mm horizontally, and during the J1 swing the wrist / camera passes over the plank jig (plank tops z 261).
**Fix:** PTP end over base A at flange z 355 (104 mm from the nearest plank release point), start over base B at 320.
**Lesson:** before a new PTP, check its endpoints against all grip/release TCP points (not just the current part),
end above 311 mm if it travels > 100 mm, and keep the wrist >= ~60 mm over the plank tops when J1 swings past the jig.

## L09 (B iter 07) The last r1 (Base B/plank3 at #127) is a zero-depth resting contact, not a sweep
**Problem:** r1 "Base B/plank3" at the final insertion move persisted through iters 03-06.
**Cause:** scratch/jig_pair.py + scratch/release_dbg.py: plank3 never penetrates Base B on the way down; at the
release pose all 6 plank ends sit flush (depth 0.0) on the base B pocket floor (frame outer face = plank ends,
z 9.5 base-local). FCL reports 5 of the 6 touching at the release pose (allowed), but plank3's exact-touch flips
between samples, so it's counted as a hit. Pure numerical luck (cf. L05).
**Fix:** (iter 07) relief recesses in the base B pocket floor under the plank ends, so planks never touch the jig.
r1 went to 0, but see L10.
**Lesson:** a flush zero-depth contact is a coin flip for the checker; design 1-2 mm of relief where a part end
lands flush on a jig, rather than nudging poses.

## L10 (B iter 07) Relief under the plank ends made 4 interface pieces B float at the start
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

## L14 (B iter 13) r4 "TCP < 100 mm above plankN": the part about to be picked is not held during the PTP to it
**Problem:** lowering every plank transit to event + 102.5 mm (pick TCP z 348): r4 6 ("PTP move #16 (Point16): TCP <
100 mm above plank3", one per pick).
**Cause:** r4's box check treats every part not yet gripped as an obstacle; the PTP ending over the plank to pick has
its TCP inside that plank's xy box, so the TCP must be >= plank top (261) + 100 = 361, not just 100 mm from the grip
point (346).
**Fix:** pick transits at TCP z ~363, place transits at event + 102.5 (~368: the placed planks are not under the TCP).
**Lesson:** a PTP endpoint above a part to grip needs TCP >= that part's top + 100 (L13 check list: grip/release
points, tops of all unheld parts under the path, 311 low-traverse).

## L15 (B iter 13) L03/L14 again: the 10 mm screen missed r4 over the plank just released
**Problem:** screen (10 mm) of pick transits 363 / place transits event + 102.5 (~368): 0 violations; the 2 mm score:
r4 2 ("PTP move #27 (Point25): TCP < 100 mm above plank3", same for plank1).
**Cause:** the PTP leaving a place transit starts directly over the plank just released (now unheld, top 280.7), so
it needs TCP >= 380.7; the coarse sampling only caught it at the first sample in 2 of 6 cases by luck.
**Fix:** place transits at event + 117.5 too (TCP ~383).
**Lesson:** after a release the part becomes an obstacle for the next PTP's start: both ends of every PTP must be
>= 100 mm over the top of any unheld part under them; don't trust a 10 mm screen for r4 box checks near the ends.

## L16 (B iter 14) L06 again: no IK for a point straight above the frame-foot grip
**Problem:** toolbox/frame_ptp.py first version put the PTP end at the Point80 flange xy at flange z 385: "no IK for
Point80h at z 385.0".
**Cause:** same as L06: the foot grip is at the reach edge with the tilted tool (rx -120); straight up has no IK
above ~+70 mm. I had read L06 but designed the vertical approach anyway.
**Fix:** PTP to a point at fraction f along the existing diagonal Line Point79 -> Point80 (IK exists along it), then
the rest of the Line.
**Lesson:** to shorten a Line with a PTP, end the PTP ON the existing (known-reachable) Line, not at a new point.

## L17 (B iter 14) The Line after a new PTP can become a low traverse
**Problem:** screens with f 0.4 / 0.5 along the diagonal: r3 "low traverse: move #96 below the safe height (311 mm)".
**Cause:** the remaining Line still travels > 100 mm horizontally, so its highest TCP point (its start) must be
>= 311; at f 0.4 the start was 310.
**Fix:** f 0.35 (Line starts at TCP ~329).
**Lesson:** any move (Line too) travelling > 100 mm horizontally must reach >= 311 TCP z somewhere; check that when
splitting a long descending Line.

## L18 (B iter 14) Write on an existing log file replaced it (lessons.md wiped to 3 blocks)
**Problem:** I used Write with only the new blocks to "append" to log/lessons.md; the file then held only L15-L17.
**Cause:** Write overwrites the whole file; it is not an append.
**Fix:** rewrote the full file from the copy read at the start of the session (all blocks L01-L17 restored).
**Lesson:** to append to a log, use Edit anchored on the last block's last line; never Write an existing log file
unless the full content is in the call.

## L19 (B iter 19) The low r4 window under the plank release points is blocked by the arm, not by r4
**Problem:** PTP ends over the base A guide grip at TCP 173 / 182 (below the plank release points, |dz| >= 80):
r4 0, but r1 link_4/link_5 vs plank1..5 in the plank jig (Point11h, carry) and EGP/plank2 + r4 "TCP < 100 mm above
plank1" (Point14h, return over the placed planks).
**Cause:** a PTP interpolates joints, so a low end point drags the wrist low through the middle of the J1 swing,
which crosses the plank jig (~68 % of the way); on the return the TCP passes over the standing planks (top 281).
**Fix:** dropped the idea; iter 19 changed to the J6 wrap (below).
**Lesson:** a PTP end lowers the whole swing, not just the end; check what the wrist passes over mid-swing before
lowering an end point. Look for the cheapest gains first: per-move times (scratch/move_times.py) and J6 values
(scratch/j6_list.py) - a joint going the long way round (> 180 deg) is a free win.

## L20 (B iter 20) Reversing a carried-part flip direction needs height, found by a z sweep
**Problem:** guide return grip wrapped to J6 +180 (shorter PTP from plank4): the +180 -> 0 flip turns the guide the
other way; with the lift end Point11r at flange z 375 (was 350): r1 Guide/plank6 at #89 (10 mm screen).
**Cause:** the reversed rotation swings the guide's far end down over the standing planks in frame 1.
**Fix:** sweep the lift end z (375 hit, 400 / 450 clean), scored 410 for slack: 0 violations, -1.5 s.
**Lesson:** when a J6 wrap reverses a flip with a part held, raise the lift before the flip and sweep its z in
parallel screens; a 100 mm/s lift costs only 0.25 s per 25 mm, far less than a long J6 turn.

## L21 (B iter 21) L19 again: a side offset clears r4 but not the wrist sweep over the plank jig
**Problem:** Point11h moved 40/40 mm sideways (117 mm from the nearest plank release point, so r4 holds at any z),
then lowered: flange z 260 / 280 / 290 all gave r1 link_5 (and EGP) vs plank1..5 in the jig at #10; 300 was clean.
Also `scratch/move_times.py` needs the program path as an argument (IndexError without it).
**Cause:** same as L19: the PTP end height sets how low the wrist passes over the plank jig mid-swing; the floor is
~300 flange z whatever the xy offset.
**Fix:** scored z 310 (-0.4 s instead of the hoped -0.8 s).
**Lesson:** for the guide carry PTPs over the plank jig the wrist floor is ~300 flange z; gains below that need the
plank jig moved or the swing routed differently, not a different end point. Run move_times.py with the program path.

## L22 (B iter 22) L15 again: side-offset transits clean at 10 mm, r4 3 at 2 mm
**Problem:** plank transits offset 10 mm out of the plank's thin box and lowered to event + 102 (variant sg +1 /
sr -1): 10 mm screen 0 violations, 2 mm score r4 3 ("PTP move #16 (Point16): TCP < 100 mm above plank3", #38 above
plank6, #60 above plank5).
**Cause:** a 5 mm thin box is crossed by the curved PTP path within a few mm of its end/start; the 10 mm sampling
steps over it. The 10 mm screen cannot judge thin-box r4 at all.
**Fix:** screened the other sign variant at --step 2 directly with judge/score.py before deciding (see iter 22 notes).
**Lesson:** for any r4-sensitive change near thin parts, screen with `--step 2 --no-shots` (~15-60 s), not 10.

## L23 (B iter 23) Moving a PTP's START sideways bends its path over a thin plank box at the other end
**Problem:** Point15v (start of the PTP to the plank3 pick) moved dx +40 / dy +40: r4 "PTP move #16 (Point16): TCP <
100 mm above plank6" at z 250, 290 and 330 alike. Also: chaining set_ptp_xyz on an output that already had the
offset doubled it (dx 80) - rebuild every variant from design/program.json or a known file.
**Cause:** a PTP interpolates joints; the J1/J2 change at the start reshapes the approach near Point16, which sits
only 10 mm beside plank3's box and 20 mm from plank6's. The end height, not the start height, was not the problem.
**Fix:** dy +40 only (dx 0) at flange z 320: clean.
**Lesson:** when a PTP ends next to a thin part, prefer start offsets that keep J1 close to the end's J1 (here: no
x shift), and screen x and y offsets separately at 2 mm.

## L24 (B iter 24) The frame flip cannot stay on the J5 < 0 wrist branch
**Problem:** dropping the J5-only flip Point84 and following the flip Line Point83 -> Point85 on the J5 < 0 branch
(scratch/wrist24.py): "FAIL Point85 110 160" - not followable at 69 %, J4 at -172 and running toward -180, IK None.
**Cause:** on the other wrist branch J4 = J4 - 180; the frame flip turns J4 by ~+106 the other way, so it runs into
the -180 limit. That is why v3 flips J5 before the Line.
**Fix:** dropped; changed the home pose instead (the J5 > 0 branch at the end and at the start made the old home
on J5 < 0 cost two branch changes).
**Lesson:** before switching a wrist branch on a long rotating Line, probe it with kin_check.follow_line (J4/J6
limits). Look for branch changes caused by a fixed-looking pose (home) - the judge has no home rule.

## L25 (B iter 25) L23 again: a new PTP from the -y side bends over the thin plank6 box; and question whole phases
**Problem:** after dropping the guide trip, the new PTP home -> Point16 (plank3 pick transit) gave r4 "TCP < 100 mm
above plank6"; moving Point16 10 mm to the outer side (dy +20) gave r4 above plank3 instead.
**Cause:** same as L23: the joint-interpolated approach from the old home (y -197) sweeps over the neighbouring
thin box near the PTP end; nudging the end point only moves which box it clips.
**Fix:** put home on the joint path of the end lift -> Point16 (home_on_path.py Point88h Point16, f 0.7): clean.
**Lesson:** fix an r4 thin-box hit at a PTP end by changing where the PTP comes from (its start / home), not the end.
Bigger one: 24 iterations polished moves inside a phase (guide) that was not needed - frame 1 already holds the
planks alone in v3's phase 3/4. Before tuning a phase, ask whether the phase (a fixture trip, a flip, a regrasp)
is needed at all; check the DO grip/release sequence stays consistent when steps are removed.

## L26 (B iter 26) A shorter reach does not shorten a PTP whose time is set by J6
**Problem:** moving the plank jig 100 mm toward base A was expected to save ~3.5 s; it saved 0.8 s, and the three
place PTPs to the A4..A6 row got slower (1.44 -> 1.52 s).
**Cause:** a PTP's time is set by its largest joint change; those planks turn ~75 deg about vertical (J6 162 -> 87),
which no layout shift removes; only the J2/J3-limited PTPs gained.
**Fix:** kept (still better); the J6 turn is the next target (present those planks pre-rotated).
**Lesson:** before a layout change aimed at PTP time, list each PTP's limiting joint (scratch/j6_list.py) and
count only the PTPs limited by the joints the change affects.

## L27 (B iter 27) L23 again: rotating a pick block with its plank also rotates the transit's side offset
**Problem:** planks 4-6 turned 80 deg in the jig, their pick moves rotated rigidly with them (toolbox/rotate_picks.py):
2 mm screen r4 3 ("PTP move #35 (Point25): TCP < 100 mm above plank6", same for plank5 / plank4).
**Cause:** the iter-22 transit sits 10 mm beside the plank's thin box on the -y robot side; turned 80 deg with the
plank it now sits on the robot side (+x), so the PTP arriving from base A (outer side) crosses the thin box at its end.
**Fix:** rotate_picks.py --mirror puts those transits on the other side of the grip point (outer side).
**Lesson:** when a part's presentation turns, re-check which side its side-offset transit is on relative to where
the PTPs come from and go to; a rigid copy of the old moves is not enough.

## L28 (B iter 28) The frame release has no J5 < 0 wrist solution; J5 sets the whole end of the cycle
**Problem:** toolbox/flip_branch.py (flip PTP onto the other wrist branch at Point85): "no IK on the other branch";
scratch/alt28.py (multi-seed DLS) finds only J5 +138 solutions near J1 20 (the others are J1 -143, the far side).
**Cause:** the TM5 wrist is not spherical; at the reach edge (TCP -747/-197, tilted tool) the J5-flipped solution
moves the wrist out of reach. The cycle's J5 path -90 (planks) -> -53 (frame grip) -> +138 (release) -> -90 is
already the minimum J5 travel (456 deg); the home leg (4.57 s) is purely J5-limited.
**Fix:** dropped the idea before scoring; changed to the Line -> PTP flip at the same branch.
**Lesson:** before a branch-change idea, list every IK solution of the critical poses (scratch/alt28.py <prog>
<name>); for a J5-limited stretch, total J5 travel over the cycle is the floor - only a different grip/presentation
changes it.

## L29 (B iter 29) L25 again: a steeper PTP descent clips the box of the part under the PTP START
**Problem:** sliding the frame-approach PTP end Point80h down the diagonal (f 0.52 / 0.60 / 0.68): r4 "PTP #69
(Point80h): TCP < 100 mm above plank4" (at f 0.52 / 0.60 also within 100 mm of the plank4 release point).
**Cause:** the PTP starts at Point70 right over plank4 (TCP 391, limit 381); a lower end makes the joint path drop
below 381 while still in plank4's xy box. Also the low-traverse rule (L17) only binds a Line travelling > 100 mm
horizontally - an L17 limit can be escaped by ending the PTP where <= 100 mm horizontal is left.
**Fix:** moved the Line end Point70 30 mm in +y (out of all plank boxes); f 0.76 then clean (-2.4 s).
**Lesson:** when lowering a PTP end, check the boxes under its START too and move a Line-end start out of them;
re-read old "rule limits" (L17) for their exact condition - a long Line forced high may be cut short instead.

## L30 (B iter 30) A Line's time is its TCP distance only: move_times "d=0.0, 0.00 s" on a re-orienting Line
**Problem:** I planned to merge the flip PTPs Point82 / Point84 around the Line Point83; move_times showed that Line
at 0.00 s although Point82 and Point83 have very different joints (J2 -40 vs -12, J5 -48 vs -14).
**Cause:** judge/cycle_time.py times a Line by TCP travel only; Point82 -> Point83 turns the tool about the TCP, so
it is "free". Any merge there would only add time (logged as a PROPOSED JUDGE FIX in tool_changes.md).
**Fix:** dropped the merge; shortened the over-long fast lift after the frame grip instead (-0.5 s).
**Lesson:** read how the judge times a move type before targeting it; over-long fast Lines next to an r4 limit
(PTP start >= 100 mm from the grip point) are cheap wins - end them at ~105 mm from the nearest grip point.

# Run B2

## L31 (iter 01) L02/L11 again: a `for` loop over ./py runs was denied; and a direct PTP re-hit plank3's box
**Problem:** (a) `for f in 0 0.25 0.5; do ./py ...; done; ./py ... | sed` denied in don't-ask mode. (b) dropping
the rotation-limited Line Point65 -> Point70 (PTP straight Point65 -> Point80h): r4 "PTP move #68 (Point80h): TCP <
100 mm above plank3".
**Cause:** (a) same as L02/L11: only single `./py` runs pass. (b) same as L29: the Line to Point70 exists to carry
the TCP out of the placed planks' boxes (y 124 row) before the descending PTP.
**Fix:** (a) separate parallel Bash calls. (b) keep the Line's translation, give its end only part of the rotation
(toolbox/partial_rot.py), the PTP does the rest.
**Lesson:** a Line that looks like a pure re-orientation may also be an r4 escape route; keep its translation and
only move the rotation into the next PTP.

## L32 (iter 03) The judge does not flag two fixtures overlapping
**Problem:** plank jig at ground x 300 scored 0 violations (111.8 s), but scratch/cell_bounds.py showed the jig's edge
at robot x -596.4 and the base A riser at -596.3: the two fixtures touch / overlap by 0.1 mm.
**Cause:** r1/r7 check the robot and carried parts against fixtures, and fixtures on the plate; fixture vs fixture
is not checked.
**Fix:** used ground x 295 (4.9 mm gap).
**Lesson:** after any layout move, run scratch/cell_bounds.py and check fixture-to-fixture gaps yourself (keep >= ~5 mm).

## L33 (iter 04) A straight Line between slow-leg tops does not beat up + PTP + down on long transfers
**Problem:** merging all 11 plank transfers into single Lines gave only -0.5 s (expected ~-1.5 s); 5 transfers got
slower (e.g. return->plank4 1.95 -> 2.30 s).
**Cause:** a Line runs at 100 mm/s TCP; a PTP crosses 200+ mm in ~0.85 s. The 2 x 0.52 s r4 legs only pay off when
the straight distance is <= ~175 mm (break-even ~ 1.04 s + PTP time, in mm x 100).
**Fix:** merged only the 6 transfers that gain (per-move times from toolbox/move_times2.py on the all-merged screen).
**Lesson:** when replacing a move pattern everywhere, screen the all-in variant once, then compare per occurrence and
keep only the ones that gain; break-even for Line-vs-(leg+PTP+leg) is ~ (1.04 s + PTP s) x 100 mm.

## L34 (iter 05) The whole cycle cannot run on the J5 > 0 wrist branch
**Problem:** idea: planks + frame grip on J5 > 0 (no wrist flips, ~290 deg less J5 travel). scratch/alt28.py: frame
grip Point81 has J5 > 0 solutions only at J1 -200 (far side); plank place Point31 (x -748) only at J1 -174; Point18
on J5 +90 needs J4 175 (at the limit).
**Cause:** the TM5 wrist is offset (non-spherical); at the plate's far edge the flipped wrist is out of reach (L28).
**Fix:** dropped before any edit; changed to removing via points in the J5-limited flip instead.
**Lesson:** the outer plank places and the frame-foot grip pin the planks/frame grip to J5 < 0; J5 savings must come
from fewer via points or other grips, not from a branch change.

## L35 (iter 05) L15/L22 again: 10 mm screen clean, 2 mm score r4 "TCP < 100 mm above Base A"
**Problem:** the direct PTP Point80L -> Point85 screened 0 violations at 10 mm; the 2 mm score: r4 1 ("PTP move #64
(Point85): TCP < 100 mm above Base A").
**Cause:** without the high via Point82 the joint swing from the low lift end (TCP 139) stays < base A top + 100 for
a short stretch; I screened at 10 mm although the change was r4-sensitive (L22).
**Fix:** toolbox/ptp_via.py: a PTP via point ON the joint path (f 0.3) with J2/J3 overridden to lift it (J2 -45,
J3 -20); J5 still limits both halves, so the time is unchanged (109.9 s) and r4 is 0 at 2 mm.
**Lesson:** screen every PTP-shape change at --step 2; to lift a J5-limited swing for free, add a joint-space via
point whose other joint deltas stay below the J5 delta in each half.

## L36 (iter 06) L21 again: scratch/dump_steps.py run without its range arguments
**Problem:** `./py scratch/dump_steps.py design/program.json` -> IndexError (sys.argv[2]).
**Cause:** the scratch probes take positional args (dump_steps: PROG LO HI move numbers), like move_times.py in L21.
**Fix:** `./py scratch/dump_steps.py design/program.json 24 27`.
**Lesson:** read a scratch script's first lines for its arguments before running it. Also (iter 06 finding): slow
vertical legs (2.5 s each) have spare rotation capacity - re-orientation about the tool axis can be done inside
them (toolbox/split_rot.py) once the fingers clear the part top.

## L37 (iter 08) Turning the tool toward home at the frame release folds the elbow into the guide
**Problem:** slerping the tool toward the home orientation in the slow lift after the frame release (g 0.29 / 0.46,
probe08 predicted -1.2 s) gave r1 5: link_3/link_4 vs Guide, Base B, frame2 (#71/#72); g 0.12 / 0.22 still hit
Guide/link_3 (r5 3.8 mm); only g 0.06 / 0.15 was clean (-0.3 s).
**Cause:** the release pose (TCP -747/-197) is at the reach edge; at a fixed TCP any J5 decrease needs J3 to fold
(-30 -> -80), which drops the elbow (frame z ~250) onto the guide on base B. scratch/probe08c.py (orientation sampling
with an elbow-height filter) found no J5 drop at the fixed TCP; a lift moved 100 mm inward + 40 up allows J5 93 but
the longer Line eats the gain.
**Fix:** kept the small clean turn (g 0.06 / 0.15).
**Lesson:** before a J5 pre-turn near the reach edge, check the elbow (K.frames z of joint 3/4) at fixed TCP, not just
J5 in the IK; the J5 budget there is set by the elbow clearance over the fixtures below it.

## L38 (iter 09) Pre-turning a PTP end toward the previous pose moves the limit to another joint (J1)
**Problem:** turning Point16 toward home cut the start PTP's J5 delta 68 -> 27 deg, but the PTP became J1-limited
(30 deg, J1 -18.6 -> -37.9 at g 0.6), so the gain stopped at -0.77 s for that move.
**Cause:** at a fixed TCP the turned tool orientation is reached with a different J1/J6 split; J1 moved away from home.
**Fix:** stopped at g 0.6 (Point16) / 0.28 (Point17), where J1, J5 and the Line rotation budgets are about equal.
**Lesson:** when pre-turning a PTP end, print the new joints of every g (turn_toward prints them) and stop where a
second joint takes over the limit; balance the PTP's max joint delta against the Lines' rot/50 budget.

## L39 (iter 10) L02 again: a `cat >> file <<EOF ... && ./py ...` append was denied; and slerp != J5 turn
**Problem:** (a) appending Screenshots/Result to notes.md with a heredoc chained to `decide` was denied (don't-ask
mode). (b) Slerping the frame-lift poses toward Pvia's orientation: g 0.3-0.6 moved J5 ~10-20 deg, but g 0.95 moved
J5 only to -25 while J6 went to -58 and J4 to -79, making the next PTP J6-limited (1.75 s, worse).
**Cause:** (a) L02: only single `./py` runs pass. (b) a straight orientation slerp is not a straight J5 path; past a
point the rotation is taken by J4/J6, and the via point's J6 then sets the limit.
**Fix:** (a) Edit for the notes, `decide` as its own call. (b) moderate g (0.15 / 0.27 / 0.6) and moved the via
point's J6 (29.5 -> 12, scratch/set_joints.py) so J5 limits both PTP halves again: -0.43 s.
**Lesson:** log files only via Edit/Write, never shell appends. When pre-turning before a J5-limited PTP pair, check
J4/J6 of the turned pose and rebalance the via point's other joints, not only J5.

## L40 (iter 11) A J5 < 0 frame release exists closer to the robot, but the arm folds over the carried frame
**Problem:** base B moved 200 / 250 mm toward the robot so the release pose has a J5 < 0 solution (scratch/probe11.py):
106.1 / 105.8 s, but r1 frame1/link_3 on the release descent (elbow-up), link_3 vs base B / guide / frame2 (elbow-down,
J3 +33), Guide/frame1 at the flip end; first try also had the home PTP J6-limited (230 deg, 108.0 s).
**Cause:** (a) the other wrist branch has J6 about 180 deg away (and J4 ~-130), so the J5 round trip turns into a J6 /
J4 round trip unless the symmetric gripper is turned 180 deg for the planks (toolbox/j6_half.py) and unwound in paid
Lines (toolbox/j6_offsets.py). (b) with the foot grip's tool orientation, the J5 < 0 wrist puts the forearm right over
the frame at the release; the elbow-down solution drops link_3 onto base B instead.
**Fix:** rejected; time saving confirmed (-1.9 s), geometry not solved.
**Lesson:** a branch change needs a collision check of the arm links at the target pose (K.frames vs the carried part
and fixtures) before building the program; the release orientation (set by the foot grip) decides where the forearm
goes - a J5 < 0 release needs a different frame grip or base B yaw, not only a move.

## L41 (iter 12) A carry along a place row's y grazes the planks already placed in the neighbouring row
**Problem:** plank jig re-laid as one column with pick y = place y: 2 mm screen 105.5 s but r1 1 ("move #52
(Point65): plank1/plank4, plank2/plank4"): plank4 (pick y 105, place y 103) passes the placed planks 1/2 (y 121.7).
**Cause:** a straight-y carry leaves only ~4 mm to the row at y 124, and the PTP's joint path bulges +6 mm in y mid-way
(ptp_via f 0.5 printed TCP y 109 between ends at 107 / 103); the 250 mm plank's lower end sweeps through them.
**Fix:** joint-space via point Pv4 at f 0.5, TCP moved -22 mm in y (toolbox/ptp_via.py + set_ptp_xyz.py): clean, J3
still limits both halves, 0.0 s cost.
**Lesson:** when a carry runs parallel to placed parts within ~10 mm, check the PTP midpoint's TCP (ptp_via prints it)
and bend it away with a via point; it is free while the same joint limits both halves.

## L42 (iter 13) A per-occurrence decision (L33) goes stale after a layout change
**Problem:** iter 04 left the four group-2 transfers as up + PTP + down because as Lines they were slower (200-230 mm
then); after iter 12's column jig they were 156-169 mm, and nobody re-checked until iter 13 (-0.4 s, free).
**Cause:** the L33 break-even (~174 mm) depends on the layout; the old choice was kept by inertia.
**Fix:** merged them (toolbox/drop_move.py), all four gained.
**Lesson:** after every layout change, re-run move_times2 and re-apply the per-occurrence rules (Line vs PTP
break-even, via points) to every transfer, not just the ones the change targeted.

## L43 (iter 15) Raising a part's start height raises the r3 safe height for the whole program
**Problem:** planks 1-3 moved into base A slots (standing on the riser, tops 271 instead of 261): 2 mm screen r3 1
("low traverse: move #25 below the safe height (321 mm)") on the 160 mm Line plank2 release -> plank6 pick, which
never goes near those planks; plus r4 at the start PTP end Point16t although its end point was > 100 mm from every
grip/release point (+3.5 mm slack was not enough; +12 mm was clean).
**Cause:** the safe height is the tallest object's top at the start + 50, global for every move; the r4 near check is
not just the end-point distance I computed (joint-path / sampling near the end).
**Fix:** a 7 mm fast vertical Line (Point41u) before the long Line; Point16t +12 mm.
**Lesson:** after any change that raises a part or jig top, re-check every Line > 100 mm horizontal against the new
safe height (top + 50); give PTP ends near grip points >= ~10 mm slack over the computed 100 mm.

## L44 (iter 16) A name -> index map picks the LAST "Point1" (home is the first and the last move)
**Problem:** the first build of toolbox/reorder16.py scored r1 on #91..#120, r6 2, r8 everywhere (moves up to #120 in
a 61-move program).
**Cause:** `{s["name"]: i ...}` keeps the last occurrence; Point1 is both the first and the last move, so the "head"
segment up to Point1 copied the whole old program in front of the new one.
**Fix:** map names to their first occurrence (setdefault).
**Lesson:** when slicing a program by step names, use the first occurrence and assert the move count is what you
expect; home (Point1) is always duplicated.

## L45 (iter 17) L37 again: un-turning the flip end over base B folds the elbow (link_3) into the guide
**Problem:** turning Point85 back toward Pvia (turn_toward.py 68 67 g) so Point86 finishes the turn: g 0.10 clean
(94.1 s), g 0.15 / 0.20 r1 2 "Guide/link_3" at #55 and #56.
**Cause:** same as L37: at the reach edge over base B, a smaller J5 at fixed TCP needs J3 to fold (-27.7 -> -30.3 /
-32.7), dropping the elbow onto the guide.
**Fix:** kept g small (see iter 17 notes for the scored value).
**Lesson:** any J5 reduction near the base B release pose is capped by the elbow over the guide (~J3 -29); expect only
~10-15 deg there and screen fine steps of g at 2 mm.

## L46 (iter 18) L42 again: a reorder (iter 16) silently dropped iter 09's slow-segment pre-turn at the start
**Problem:** move_times2 on the iter-17 best showed the first pick's slow segment Point26s with rot 0.0 while the start
PTP was J5-limited (0.92 s); iter 09 had already hidden ~24 deg there, but iter 16 rebuilt the start for plank6.
**Cause:** toolbox/reorder16.py built new start moves from the pick block, without the pre-turn tweaks of iter 09.
**Fix:** re-applied it (turn_toward Point26 g 0.75, P16s0 g 0.55): -0.4 s.
**Lesson:** after any reorder / rebuild of a segment, re-list every earlier per-move optimisation that touched it
(pre-turns in slow legs, via points, J6 wraps) and re-apply them; scan move_times2 for "rot 0.0" slow legs next to a
J5-limited PTP.

## L47 (iter 19) L31 again: a `for` loop over ./py runs denied (a plain `&&` chain of ./py runs passed)
**Problem:** `for f in a b c d; do ./py toolbox/move_times2.py ...; done` denied in don't-ask mode.
**Cause:** same as L02/L31: loops are blocked; a short `cd && ./py ... && ./py ...` chain was allowed this session.
**Fix:** separate parallel Bash calls.
**Lesson:** never use shell loops; one `./py` per Bash call (parallel calls).

## L48 (iter 20) L39 again: slerping toward a joint-space via point turns J6, not J5
**Problem:** turn_toward.py Point80Lt -> Pvia g 0.15-0.35: J5 only -33.2 -> -29.5, J6 -16.9 -> -34.6 (away from Pvia's
J6 12), so the J5-limited Pvia PTP would not gain.
**Cause:** Pvia's joints were hand-set (J5 0, J6 12, J2/J3 overrides), so its tool orientation is not "J5 turned";
a straight orientation slerp toward it is mostly a J6/J4 rotation (as L39).
**Fix:** scratch/j5turn20.py: take the orientation of FK(q with J5 + D), keep the TCP, IK; then rebalance the via
point's J3/J6/J1 (set_joints.py) so J5 limits again: -0.18 s.
**Lesson:** to pre-turn J5 in a Line, turn about the J5 axis (j5turn20), not toward a target pose; then re-balance
the next via point's other joints, which a fixed-TCP J5 turn pushes away (J3 folds ~1.3 deg per J5 deg here).

## L49 (iter 21) No tilt of frame 1 during its 50 mm lift out of base A: the planks are still in base A's slots
**Problem:** J5 pre-turn of 5-20 deg in the slow lift after the frame grip (Point80t/80ut/80Lt, scratch/turn21.py):
92.8-93.0 s but always r1 2 ("move #51 (Point80t): Base A/plank1..6", "#53 Point80Lt: Base A/frame1"); splitting the
leg to turn only above 20 mm moved the hits to Point80ut / Point80Lt, even at D 5.
**Cause:** frame 1 sits in base A's pocket and the plank ends stand in base A's floor slots, so the carried assembly
keeps touching base A for the whole 50 mm lift; judge/collision.py allows only the grip-pose contacts, and only in
the first two moves after a grip. A turn about the foot grip swings the far frame end (180 mm) down into base A.
**Fix:** rejected; no program-only way (turning above the pocket costs Line time 1:1 with the J5 saved).
**Lesson:** read the judge's contact allowances (collision.py docstring) before turning a carried part near where it
was gripped; a carried part still engaged in a jig cannot rotate. The grip-side J5 saving needs a shallower base A
pocket / slots (jig_cad).

## L50 (iter 22) A J5 turn that brings a pose near J5 = 0 makes J4/J6 swing (wrist singularity)
**Problem:** j5turn20 D 40 on P16s0t (J5 -38 -> -4): J4 -35 -> -118, J6 62 -> -29, the start PTP became J4-limited
(no gain over D 30); D 35 (J5 -6.6) still swung J4 to -62 and raised joint travel 2290 -> 2377 deg for -0.07 s.
**Cause:** near J5 = 0 the TM5 wrist is singular; a small orientation change needs large opposite J4/J6 moves.
**Fix:** kept D 35 (still the fastest legal variant); D 30 would be the cleaner choice at +0.07 s.
**Lesson:** when pre-turning a PTP end toward J5 = 0, print J4/J6 for each D and stop before |J5| < ~10 deg; check that
the PTP's limiting joint is still J5 after home_on_path.

## L51 (iter 23) L37/L45 again: a J5 turn at the high lift end Point88ht still puts link_3 into the guide
**Problem:** j5turn20 D -15 / -20 on Point88ht (TCP z 458) + home_on_path f 0.85: 2 mm screen r1 3-4 ("move #61
(Point88ht): Guide/link_3", "#62 (Point1): Guide/link_3", and "#1/#2: link_6/plank4" because home moved 10-13 mm lower).
**Cause:** J3 stayed at -62.4 in the IK, so I assumed the elbow does not drop; but J1 (-4..-6) and J2 (-2) changed,
which swings the elbow sideways/down over the guide. J3 alone is not an elbow-height test (L37 said: K.frames z).
**Fix:** see iter 23 notes (move the lift end inward / up so the elbow clears).
**Lesson:** judge elbow clearance by link_3/link_4 frame positions vs the guide box, not by J3; and re-check the start
PTP whenever home_on_path moves home (a lower home brings link_6 near plank4).

## L52 (iter 24) A wall check printed "outer 0.00" for every slot, including the old, proven ones
**Problem:** scratch/wall24.py gave slot-to-outer-edge distance 0.00 mm for all six base A slots.
**Cause:** the "outside" solid (big box minus the base block) spanned z -1..21 while the slots also run z -1..21
(through-cut overshoot), so they overlap below z 0 / above z 20 regardless of x.
**Fix:** computed the outer walls from the yawed slot extents (12.8 cos + 2.8 sin = 5.0 mm half-width in x -> 5.0 mm
wall); the pocket / slot-to-slot distances were valid.
**Lesson:** sanity-check a new measurement on a case with a known answer (the iter-15 slots) before trusting it; give
"outside" test solids the same z range as the part, not the cutter's overshoot. Also (iter 24 finding): every fixture
edge strip that faces a place row is a candidate slot location - iter 15's trick applied to the other row gave -1.2 s.

## L53 (iter 25) L02/L47 again: `sed -n ... ; grep ...` chain to read a log was denied; and a detour height outlives its reason
**Problem:** (a) a Bash call chaining `sed -n '/## Result/,$p' notes.md; grep -n ... build_cell.py` was denied in
don't-ask mode. (b) Point70y still ended at TCP z 385 (the "100 mm over the plank tops" height) although iter 29 of run
B had moved it 30 mm in +y out of every plank box; only the r4 near-point limit (~360) applied.
**Cause:** (a) same as L02: reads go through the Read tool. (b) when L29 moved the point out of the boxes, the old
height was kept by inertia (like L42).
**Fix:** (a) Read tool. (b) iter 25: z 370 + rotation moved into the slow lift P16eu: -0.16 s.
**Lesson:** read files with Read, never sed/grep chains. When a point is moved to escape a constraint, re-derive every
other coordinate of it from the constraints that still bind (here r4 near-point distance), not from its old value.

## L54 (iter 26) L04 again: a PTP end lowered beside a thin plank box put the wrist camera (link_6) into the next plank
**Problem:** start PTP end P16s0t moved 12 mm in -x out of plank6's box and lowered to TCP z 368 (r4 limits satisfied):
2 mm screen r1 1 ("move #2 (P16s0tt): link_6/plank4").
**Cause:** the r4 rules bound only the TCP; the camera on link_6 sticks out ~62 mm sideways and passes over the
neighbouring standing planks (tops 271) when the end is low.
**Fix:** z 372 (4 mm higher) was clean; scored that.
**Lesson:** when lowering a PTP end over standing parts, screen 2-3 heights at 2 mm in parallel; after r4, the link_6
camera over the neighbouring parts is the next floor.

## L55 (iter 27) A -0.05 s gain is invisible: the judge rounds cycle_s to 0.1 s and joint travel to 1 deg
**Problem:** Point88ht lowered 5 mm (Line 59.5 -> 54.5 mm, move_times2 -0.05 s, 0 violations): iterate.py score gave
cycle 91.0 s = best, joints 2316 vs 2315 deg -> "NOT better (reject it)".
**Cause:** score.json stores cycle_s rounded to 0.1 s (and joint_travel_deg to 1 deg); the rank compares those rounded
values, so a gain smaller than the distance to the next rounding step does not count, and a 1 deg joint increase
decides the tie.
**Fix:** computed the exact totals (scratch/exact27.py = judge cycle_time.estimate) and tightened two more r4-bound ends
(Point80Lt -3, Point85t -2 mm) to reach 90.944 s exact -> 90.9 s; kept.
**Lesson:** before scoring a sub-0.1 s change, compute the exact unrounded cycle of best and candidate (sum of
move_times2) and check that the rounded value drops (or that joint travel does not rise); bundle tiny gains only after
each was screened alone.

## L56 (iter 27) L51 again: Point88ht 8 mm lower (TCP z 450) put link_3 into the guide
**Problem:** n27b (Point88ht dz -8, still 102 mm over the release point): 2 mm screen r1 1 "move #61 (Point88htt):
Guide/link_3"; dz -5 (z 453) was clean.
**Cause:** same as L37/L51: at the base B release pose the elbow hangs just over the guide; any lower lift end drops it.
**Fix:** kept z 453.
**Lesson:** Point88ht's floor is the elbow (~453), not r4; don't try lower without moving the lift end inward.

## L57 (iter 28) A safety margin chosen once (L01: 0.5 mm) became a 0.7 s fixed cost nobody re-sized
**Problem:** 28 slow legs at 50.5 mm = 0.5 mm x 28 / 20 mm/s = 0.7 s spent on a margin against float rounding;
27 iterations treated the 50.5 mm legs as fixed cost.
**Cause:** L01's fix (summed path 49.99.. at exactly 50.0) needs a margin of ~1e-6 mm, but 0.5 mm was picked and then
copied as a standing rule (like L42 / L53: a value outlives its reason).
**Fix:** toolbox/shrink_legs.py --target 50.1: all legs 50.1 mm, 2 mm score 0 violations, -0.5 s.
**Lesson:** size a margin to the error it guards against (float: 0.1 mm), and when everything looks "fixed", list the
fixed costs that are ours (margins, slack heights) rather than the judge's, multiplied by how often they occur.

## L58 (iter 30) Lowering a Line end also changes the next PTP: the net gain was ~30 % below the Line's own saving
**Problem:** Point70yt 8 mm lower: the Line alone should save ~0.06 s, exact cycle dropped only 0.042 s (dz -6: 0.032 s,
landing on 90.250 exact, which rounds UP to 90.3).
**Cause:** the J4-limited Point80h PTP starts at that point, and its joint delta grew a little.
**Fix:** took the largest variant still with ~2 mm r4 slack (dz -8, ~102 mm from Point40): 90.240 -> 90.2 s.
**Lesson:** screen a moved PTP endpoint with scratch/exact27.py over a few offsets before picking one (the next PTP
changes too), and never accept an exact total of x.x5 - it can round either way.

## L59 (iter 31) Point80h's floor is the Base A box (r4), not the 100 mm near-point distance to the frame grip
**Problem:** Point80h slid 11.6 / 15.4 / 19.3 mm down its Line (TCP z 133.6 / 130.6 / 127.7, still >= 101 mm from
Point81): 2 mm screens all r4 1 "PTP move #48 (Point80h): TCP < 100 mm above Base A".
**Cause:** I computed only the near-point distance; the end is inside base A's xy footprint, so TCP z must be >= base A
top + 100 - and the iter-15/24 plank slots made base A a large footprint under the whole frame approach.
**Fix:** none; rejected (Point80h already 1.3 mm over the base A floor 141.2; sideways moves gain only 0.02 s).
**Lesson:** for a PTP end over a fixture, check BOTH r4 limits (near-point distance AND top of every jig/part box under
it: scratch/cell_bounds.py) before predicting slack; the larger one is the floor.

## L60 (iter 35) L51 again: home J3 -58.7 -> -60.5 put link_6 into plank4 (moves #1/#2)
**Problem:** removing the 2.8 deg J3 detour at home (Point1 J3 -60.5): 2 mm screen r1 2 "move #1 (Point1): link_6/plank4",
"#2 (P16s0tt): link_6/plank4"; cycle unchanged, joints 2301.
**Cause:** the J3 rise at home is not a pure detour: it lifts the wrist (camera on link_6) over plank4 on the start PTP;
L51 already said a lower home brings link_6 near plank4. I had read it and still tried the larger change first.
**Fix:** use the smallest J3 that removes the detour (-60.1 = P16s0tt's J3) and compensate with J2 inside its monotonic
range (-55.1..-33.1), screened at 2 mm.
**Lesson:** a joint "detour" next to a known collision floor is usually the clearance; when removing one, try the
boundary value first and pay the height back with a joint that has free monotonic range.

## L61 (iter 36) A J6 "detour" at a PTP end is the next Line's rotation budget, not waste
**Problem:** P16s0tt J6 17.8 -> 64 (monotonic J6 through the start) made exact cycle 89.940 -> 90.32 s; J6 45: +0.12 s.
**Cause:** a twist about the tool axis changes the orientation the next Line (#3 Point26t, 65.1 mm, rot 31.8) must
cover; at 32.5 deg it becomes rotation-limited. Home Point1 was already between its neighbours, so no free J6 there.
**Fix:** swept J6 with scratch/exact27.py (24/28 free, 32 +0.005): J6 28, joints -21 deg, cycle unchanged.
**Lesson:** before removing a joint detour at a PTP end that starts a Line, sweep it with exact27 - the Line's rot/50
budget caps it; take the largest value with the exact total unchanged (never one landing on x.x5, L58).

## L62 (iter 37) L36 again: scratch/set_joints.py IDX 0 -> KeyError 'move'
**Problem:** `./py scratch/set_joints.py design/program.json out.json 0 J6=28` -> `KeyError: 'move'`.
**Cause:** IDX is the steps-list index, and steps[0] is not a move; the move numbers printed by toolbox/show_joints.py
(Point1 = 1 and 76) are the same as the steps indices.
**Fix:** IDX 1 and 76 (both home occurrences, L44).
**Lesson:** use show_joints' numbers directly as set_joints IDX; remember home is two steps (first and last move).

## L63 (iter 38) L02/L08 again: a `sed ...; ./py -c ...; python3 -c ...` chain was denied
**Problem:** a Bash call chaining sed, `./py -I -c` and `python3 -c` to peek at program steps was denied (don't-ask mode).
**Cause:** same as L02/L08: inline Python and chains are blocked.
**Fix:** wrote the probe as scratch/split38.py and ran it alone.
**Lesson:** under time pressure too: every probe is a scratch file + a single `./py` call.

## L64 (iter 38) A joint bulge inside a rotating Line cannot be split away; and decide needs a score
**Problem:** splitting the start Line #3 (J3 bulge 9.3 deg, scratch/travel38.py) at a joint-space midpoint orientation
(scratch/split38.py): rotation halves 16.1 + 17.4 = 33.5 deg vs 31.9 direct, second half rotation-limited, cycle 90.0 s
(+0.1), joints +1. Also `decide 38 reject` without a score -> "score iteration 38 first".
**Cause:** the bulge comes from holding the TCP on a straight line while the tool turns; a midpoint orientation off the
slerp only adds rotation to a Line already at its rot/50 budget. iterate.py refuses decide before score.
**Fix:** scored the candidate anyway and rejected it.
**Lesson:** in-Line joint detours are fixed by the Line's end poses, not by splitting it; use scratch/travel38.py to
find detours, but only end-pose changes (PTP ends, pre-turns) can remove them. Always score before decide, even a
candidate known to be worse.

## L65 (iter 40) L02/L63 again: `head ... && ./py ... | sort | tail` denied; and the design now sits 0.0003 s under a rounding step
**Problem:** (a) a Bash call chaining head, a ./py run and a sort/tail pipe was denied (don't-ask mode). (b) Point80Ltt J5
turns of -1 / -3 deg cut sampled joint travel 2-8 deg but raised exact cycle to 89.963 / 89.998 (rounds 90.0); only
-0.2 deg fit (89.9497 exact, joints -1).
**Cause:** (a) same as L02. (b) Pvia and Point85tt are J5-limited, so the J5 sum from Point80ut onward is fixed; any extra
J5 at Point80Ltt costs time 1:1, and +D makes the Line rotation-limited (27.5 deg in 55 mm).
**Fix:** (a) Read tool + single ./py calls. (b) took -0.2 deg; kept on the tie-break.
**Lesson:** read scratch scripts with Read, run one ./py per call. The best is now 89.9497 exact: no tie-break change that
adds even 0.001 s is possible - the next keep must cut real time (>= 0.1 s, i.e. a fixed-cost event).

## L66 (iter 41) L45/L51 again: a J5 pre-turn at the flip PTP end Point85tt (z 449) puts link_3 into the guide
**Problem:** j5turn20 D -6.5 on Point85tt (J5 122.1 -> 116.6, J3 -29.3 -> -27.3): 89.8 s but 2 mm score r1 2 "Guide/link_3"
at #56 (Point85tt) and #57 (Point86).
**Cause:** as L51: J1/J2 change with the turn (J2 -72 -> -73.8) and lower the elbow over the guide; J3 unfolding is not
an elbow-height test. The descent Point86 then carries the elbow down onto the guide.
**Fix:** rejected; D <= -5.5 (maybe clean) only reaches 89.855 s exact (rounds 89.9).
**Lesson:** every J5 reduction anywhere over base B (release pose, lift end, flip end) is capped by link_3 vs the guide;
consider the base-B side J5 trip exhausted. Only a guide/riser change (jig_cad) or a different flip pose can free it.

## L67 (iter 42) L66 again: shifting the turned flip end Point85tt +-4/8 mm in xy did not move the Guide/link_3 hit
**Problem:** j5turn20 D -6.5 (and D -6) on Point85tt plus set_ptp_xyz shifts of 4 / 8 mm radially inward and outward:
every 2 mm screen gave the same r1 2 "Guide/link_3" at #56/#57 (J3 ranged -22 .. -33.6 across the variants).
**Cause:** not fully known. The hit does not depend on where the PTP end sits, so it is most likely along the Point86
descent, where the turned start orientation slerps into the unchanged low release pose with the forearm beside the guide.
J3 at the end pose is not the test (L51).
**Fix:** none; rejected. I screened 5 variants blind, with no distance measurement.
**Lesson:** before a third blind attempt at a known collision, write the probe first: min distance link_3 vs the hit
part per sample of the hitting moves (judge/collision.py's robot_poses + trimesh min_distance). Then decide if any
program-only variant can clear it. Treat the base-B J5 turn as closed unless the guide geometry changes.

## L68 (iter 43) The probe settled in 2 runs what 7 blind screens did not; and a tiny J5 turn raised joint travel
**Problem:** scratch/elbow43.py (link_3/4 vs Guide per sample) showed the closest point is the END of PTP #56 Point85tt
(best 5.3 mm; D -4 and D -6.5 0.0 mm), not the Point86 descent as L67 guessed. D -1.5 was clean (2.6 mm), 89.924 s exact,
but joints 2278 vs 2275 -> not better.
**Cause:** clearance drops ~1.3+ mm per deg of turn; a fixed-TCP J5 turn also moves J1/J2/J3/J6 (L48), adding more
sampled travel than the 1.3 deg of J5 saved.
**Fix:** rejected.
**Lesson:** probe distance first (scratch/elbow43.py PROG LO HI), then size the change from it. For a tie-break gain,
check joint travel of the candidate (scratch/travel38.py) before scoring, not only exact27.

## L69 (iter 44) L55/L58 again: screened f 0.982 with exact27, then scored f 0.9 unscreened -> 90.0 s
**Problem:** partial_rot.py step 59 (Point70yttt, the only ROT-LIMITED Line) f 0.982: 89.947 exact; I then scored f 0.9
without exact27: 90.0 s (worse than 89.9).
**Cause:** the Line end is the next PTP's start; more rotation moved out of the Line raised PTP #48's joint deltas (J4 +3.5)
more than the 0.01 s the Line saved.
**Fix:** rejected.
**Lesson:** run exact27 on the exact variant you score, every time; a 0.01 s rot-limit is not worth an iteration.

## L70 (iter 45) Three iterations treated a jig collision as an arm limit; the hit was an unused guide corner
**Problem:** iters 41-43 tried to steer link_3 around the guide (program only) and called the base-B J5 turn "closed"
(L66-L68), yet the contact (scratch/elbow45.py, which prints the contact point) sat on the guide's far outer corner.
**Cause:** I probed only the distance (elbow43), not WHERE on the fixture the contact was; the guide's corner has had no
function since run B dropped the guide trip (no slot within 45 mm, never gripped).
**Fix:** a 25 x 28 x 15 mm notch in that corner (design/cad/jig_parts.py GUIDE_NOTCH): iter 41's program became legal,
89.8 s.
**Lesson:** when the arm hits a fixture, print the contact point on the fixture first and ask whether that material has a
job; trimming a jig is often cheaper than any program change.

## L71 (iter 46) A notch sized from one contact point only moved the contact to the notch's wall
**Problem:** J5 turn D -6 at Point88htt (exact 89.730 s) hit Guide/link_3 at #61 on the guide's far top edge; a 10 mm
edge strip notch (local y -95..-80) moved the contact to the strip's inner wall (world y -180.3), still r1 1.
**Cause:** elbow45.py prints only the closest point at the worst sample, not how deep the link sweeps into the guide;
I sized the cut from that point instead of from the link's swept volume.
**Fix:** none (out of time; rejected).
**Lesson:** before cutting a notch, find the link's full penetration extent over the hitting move (e.g. slice the
guide at several y/x offsets and re-probe, or measure the link's min y over the samples) and cut to that plus ~5 mm,
after checking it stays clear of the slots.

## L72 (iter 47) L71 again: deepened the notch by a guess (y -80 -> -62), contact still at #61
**Problem:** GUIDE_EDGE_NOTCH x 26..64, y -95..-62, z 15..35 with iter 46's J5 turn: 89.7 s but r1 1 "Guide/link_3" at #61.
**Cause:** no swept-volume probe; link_3 passes outside the cut box (deeper in y, higher in z, or beyond x 26..64).
**Fix:** none (16 min budget; rejected).
**Lesson:** with little time left, don't spend the iteration on a guessed cut; write the probe (link_3 vertices inside the
guide's bounds over all samples of #61, in guide-local coords) first, or pick a change that needs no probe.

## L73 (iter 48) The swept-volume probe showed the cut cannot clear: a slot sits inside link_3's sweep
**Problem:** scratch/sweep48.py (link_3 vertices inside the guide box over #61) gave x -11.8..57.4, y -90..-46.7, z 20..34.2;
a slot corner at (26.9, -49.6) capped the notch at y -53; scored anyway: r1 1 "Guide/link_3" at #61. Also
trimesh.proximity.signed_distance failed: `ModuleNotFoundError: No module named 'rtree'`.
**Cause:** link_3 sweeps up to the slot row; the guide material it hits has a job (slot wall). rtree is not installed.
**Fix:** rejected. Probe ran in bbox-only mode (MARGIN arg > 0 skips signed_distance).
**Lesson:** run the swept-volume probe BEFORE writing the hypothesis, and if the sweep overlaps functional material, drop
the cut and size the program change instead (smaller J5 turn via elbow43). No rtree here: avoid trimesh proximity/contains.

## L74 (iter 49) L73 again: sized the smaller turn from the exact27 rounding window, not from elbow43's distance
**Problem:** D -5.5 (instead of -6) at Point88htt + iter 48's notch: 89.740 exact, but r1 1 "Guide/link_3" at #61.
**Cause:** I picked D from the cycle rounding window (D must be <= ~-5.3 to round to 89.7) and assumed ~0.7 mm gained was
enough, without running elbow43 on the candidate; the window and the clean range do not overlap.
**Fix:** rejected (out of time).
**Lesson:** when both a rounding window and a clearance floor bind, measure the clearance (elbow43) at the window's edge
first; if it is negative there, the idea is dead without a geometry change - don't score it.

## L75 (iter 50) L74 applied: probe killed D -5.2 before scoring, but the iteration still had to be spent
**Problem:** D -5.2 at Point88htt (exact 89.745 s, last value rounding to 89.7): elbow43 min 0.0 mm on #61; scored anyway
(decide needs a score): r1 1 "Guide/link_3" at #61.
**Cause:** with ~10 min of budget I picked the one idea left that needed no new tool, and it was the one L74 had flagged.
**Fix:** rejected.
**Lesson:** run the probes (elbow43, exact27) BEFORE writing notes.md and pick a different idea if the probe kills it;
a probe-killed idea should not consume an iteration number.

## L76 (iter 51) L75 again: with ~7 min left the probe killed the only quick idea, scored anyway
**Problem:** D -3 at Point88htt: exact27 89.787 s (89.8 tie), elbow43 0.0 mm on #61; scored: r1 1 Guide/link_3, joints 2288.
**Cause:** the session started with 10 min of budget; no time to find a fresh idea after the probe.
**Fix:** rejected (summary left for the runner's final session; decide did not report the budget used up).
**Lesson:** the base-B J5 turn at Point88htt is closed at every size without moving the guide slot; and when the budget
left is under ~15 min, write the summary instead of spending an iteration on a probe-killed idea.

## L77 (iter 52) L76 applied: with 9 min left there was no idea worth an iteration number
**Problem:** the session started with 9 min of budget and a no-keep streak of 6. Every movable move in move_times2 is at a
measured floor.
**Cause:** the run's last gains (iters 41-51) all hit the same link_3/guide floor, and the remaining time leaves no room
for a fixed-cost (jig/grip) change.
**Fix:** re-scored the unchanged best (confirmed 89.8 s, 0 violations), rejected it, and wrote log/summary.md.
**Lesson:** when the budget is nearly gone, spend the session on the summary and a confirmation score, not on a guessed
change; the next real gain needs a fixed-cost event removed (fewer grips/releases, guide slot moved).

## L78 (iter 53) L77 again: the last two sessions had too little budget for a change
**Problem:** iter 53 started with 8 min left and a streak of 7; again only a confirmation re-score fit, and it ended the run (streak 8/8).
**Cause:** iters 46-51 spent the run's last half hour on one closed idea (base-B J5 turn), leaving no time for a fixed-cost change.
**Fix:** re-scored the unchanged best (89.8 s, 0 violations), rejected, updated log/summary.md.
**Lesson:** start any fixed-cost (jig/grip) change while 30+ min remain; once an idea is closed by a probe, switch change type at once instead of resizing it.
