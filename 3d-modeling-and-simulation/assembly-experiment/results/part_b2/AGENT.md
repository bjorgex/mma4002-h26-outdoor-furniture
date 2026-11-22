# AGENT.md (run B2): improve the bench assembly cell further

You are improving a robot cell that assembles a small outdoor bench (1:7.5 demonstrator) with an Omron TM5-900 arm
and a parallel gripper (EGP). This is the **second run (B2)**. The first run (B) started from the cell's first
working version, **v3** (239.8 s, 28 rule violations), and in 30 iterations reached a legal design at 112.9 s. You
start from that design (`design/` = `best/` = run B's iter 30) and make it faster still, while it stays legal (the
hard constraints below). You work alone, in this folder only, in iterations: one
change, build, simulate, score, keep or reject, log. Every number comes from the frozen judge in `judge/`.

## The cell (v3) and what it does
- Robot at the origin of the robot base frame; the work plate (590 x 440 mm "ground base") lies at x -206..-796 mm.
  Everything is placed on the ground base frame (`design/build_cell.py`: x away from the robot, y to the left).
- Jigs: **base A** (pocket for frame 1, 180 x 180 mm on a 10 mm riser), **base B** (frame 2, mirrored), the
  **plank jig** (6 slots, 2 rows of 3, planks stand upright), and a **double-sided guide** (a plate with 6 slots
  that holds the planks upright over a frame; a grip pocket in the side of its short arm).
- Start: base A holds frame 1 + 6 interface pieces (piece A1..A6), base B holds frame 2 + 6 interface pieces
  (piece B1..B6) with the guide lying on top, the planks (plank1..plank6) stand in the plank jig.
- What v3 did (for reference; `design/program.json` is now run B's 84-move program, see below):
  1. guide: base B -> turned over in the air -> onto base A (over frame 1),
  2. planks 1-6 (order 3, 6, 2, 5, 1, 4): plank jig -> straight down through the guide into frame 1, pushed home,
  3. guide: lifted off over the plank tops -> turned over -> back onto base B,
  4. frame 1 with its planks: gripped at a leg foot, turned over (planks down) in the middle of the plate, lowered
     through the guide into frame 2. End: the bench is assembled in base B.
  The wrist changes branch (J5 through 0) only in a J5-only joint move. The grips the program uses are in
  `design/build_cell.py` (PLANK_GRIP, PLANK_PUSH, GUIDE_GRIP, FOOT_GRIP: the TCP pose in the part's coordinates).
- Gripper: DO0; a grip / release step waits 500 ms, other DO steps 300 ms. TCP = flange + 160 mm along z.
- Baseline score: see `log/iter_00/` and the first row of `log/iterations.csv` (the judge scored v3 before you
  started; it breaks several hard rules - making it legal is part of the job).

## Where run B ended (your start)
- Layout: base B on an 80 mm riser; plank jig moved toward base A, its robot-side row (planks 4-6) turned 80 deg;
  plank1/plank2 start slots swapped so the pick and place orders agree; a small relief in the base B pocket.
- Program (84 moves): **no guide trip** - frame 1 holds the planks alone, the guide stays on base B all cycle. Planks
  picked outer-first, placed robot-side-last through 10 mm side-offset transits ~102 mm over the grip/release point,
  50.5 mm slow vertical legs. Frame 1 gripped at a leg foot, short lift, flipped, lowered through the guide into
  frame 2.
- Run B's own conclusion: ~70 % of the cycle is now fixed cost: the 50 mm slow legs at 20 mm/s (2.5 s each, 2 per
  plank + the frame) and the gripper waits. More gains need **fewer or shorter fixed-cost events** (fewer grips /
  releases / slow legs, e.g. a different jig or grip strategy), or a better route / layout - not faster moves.
  Everything run B learned is in `log/lessons.md` (L01-L30, marked "B iter") and its tools are in `toolbox/`
  (`toolbox/README.md`, and run B's tool log at the top of `log/tool_changes.md`).
- **Judge change for B2** (run B's own proposed judge fix, applied): a Line's time is now the larger of its TCP
  distance / speed and its tool rotation angle / 50 deg/s, so a pure re-orientation Line no longer costs 0 s. The
  baseline (iter 00) is run B's final design scored with this judge.

## What you may change
1. **the program**: moves, order of operations, approach paths, grips (`design/program.json`),
2. **the jig / fixture layout**: positions and rotations (the constants in `design/build_cell.py`),
3. **the jig and fixture 3D models**: build123d scripts in `design/cad/` -> STL in `design/meshes/jig/` -> the cell
   (`design/build_cell.py` builds `design/cell.glb` + `design/cell_layout.json`; the judge rebuilds it before scoring),
4. **the tools**: write your own in `toolbox/` (program generator, planner, layout search, extra checks, ...).
   The judge (`judge/`) is frozen and hashed: you may read and import it, never change it. If you find a bug in
   it, write a "PROPOSED JUDGE FIX" block in `log/tool_changes.md`; it is applied after the run, then everything is
   re-scored.

Fixed, not up to you (changing them = a violation, or gaming the judge): speeds (Line <= 100 mm/s, the last/first
50 mm at a part <= 20 mm/s, PTP <= 50 deg/s), gripper waits, the robot and where it stands, the gripper's geometry
and stroke (no `egp_gap`), the TCP, the bench product (frames, planks, interface pieces: meshes in
`design/meshes/bench/` and how they go together), the table and the work plate (size and place).

## Hard constraints (any violation = rejected, no matter how fast)
The judge counts them (`rule_violations` = the sum; `log/iter_NN/score.json` "violations" says what and where):
1. No collisions: robot + gripper vs fixtures, carried parts vs everything, at 2 mm / 2 deg sampling (`r1`).
2. Every target reachable, every Line followable, no joint limits (`r2`: ik/line failures, limit hits).
3. Free moves above a safe height (no low traverses); the last 50 mm into and the first 50 mm out of every
   grip / release are vertical Lines (from / to above) at <= 20 mm/s (`r3`). So: grab from above.
4. No PTP within 100 mm of a grip / release point, nor with the TCP less than 100 mm above a jig or a part (`r4`).
5. Min clearance >= 10 mm in free moves (PTP and fast Lines) (`r5`).
6. A released part rests on something (pocket, plank jig, frame), never in the air (`r6`); every part and jig rests
   on something at the start too.
7. Jigs / fixtures: on the work plate, printable (<= 250 mm per print part, or split it), wall >= 3 mm (not checked
   by the judge: check it yourself in the CAD), fixed to the plate (they move only if the robot moves them on
   purpose) (`r7`).
8. The bench product does not change, and it is assembled at the end: every part within 2 mm of its place in the
   bench (`r8`). `r_fixed` counts changed fixed parameters.

## Keep / reject rule
Pass every hard constraint, then the lowest cycle time (`cycle_s`); ties broken by `joint_travel_deg`.
Until a legal design exists: fewer violations is better. The judge's rank is
`(fails a rule?, rule_violations, cycle_s, joint_travel_deg)`, lower is better; `judge/iterate.py score` prints the
verdict against the best so far, and `decide ... keep` is refused unless the verdict is "better". You may still
reject a "better" candidate (e.g. the screenshots show a part crooked in its pocket): say why.

## One iteration (one session = one iteration; then stop, the runner starts the next)
0. `./py judge/iterate.py status` (best so far, budget, next iteration number NN). **Read `log/lessons.md` in full**
   and "Learned during the run" below, and apply them. Look at the last iterations (`log/iterations.csv`,
   `log/iter_*/notes.md`) so you don't repeat a rejected idea unchanged.
1. Choose ONE change (see the practice and heuristics below). Write `log/iter_NN/notes.md`:
   `# iter NN: <title>`, `## Hypothesis` (what you change, the expected delta in s / violations, the change
   type: program | layout | jig_cad | tool | mixed) and `## Reason` (see "Reasons" below), **before** you run
   anything that scores it. `iterate.py score` refuses without both.
2. Make the change in `design/` (and your tools in `toolbox/`). Screen as often as you like:
   `./py design/build_cell.py && ./py judge/score.py design/program.json design/cell.glb --step 10 --no-shots`
   (coarse, ~15 s; only the 2 mm score counts). Single checks: `./py judge/collision.py ...`,
   `./py judge/kin_check.py ...`, `./py judge/cycle_time.py ...`.
3. Score it: `./py judge/iterate.py score NN --type <type>` (2 mm, ~1-2 min). Writes `log/iter_NN/score.json`,
   `shots/`, `topview.png`, `diff.patch` and copies of the program, layout and scripts.
4. **Screenshots (hard rule)**: open every image in `log/iter_NN/shots/` and `topview.png` (Read tool) and write
   under `## Screenshots` in notes.md what you see in each (a line per shot at least): parts where they should be,
   nothing floating, crooked, inside another part, no jig in an odd place, the arm in a sensible pose. Keeping is
   refused without it.
5. `## Result`: expected vs got (delta per phase), why kept / rejected. Then
   `./py judge/iterate.py decide NN keep|reject --reason "..."`. Reject restores `design/` from `best/`.
6. Log every problem in `log/lessons.md` (below) and every tool change in `log/tool_changes.md`. Then end the session.

If a session runs out of time before `decide`, the runner rejects that iteration. Keep iterations small.

## Reasons (new in B2, hard rule)
Every change needs a written reason, so a reader of the report can follow *why* each step was taken, not only what
changed. In `## Reason` (at least a few sentences):
- **Evidence:** the number, shot or lesson that points to this change (e.g. "phase planks = 61 s, of which 30 s are
  slow legs"; "shot 03 shows the arm swinging over base A"; "L25: question whole phases").
- **Why this and not something else:** the alternatives you considered and why you chose this one now.
- **DFA / cell principle** it follows (e.g. fewer handling events, shortest route, present parts in assembly
  orientation), if any.
The first 400 characters go into the `reason` column of `log/iterations.csv`; put the core of it first.
In `## Result`, say whether the reason held (was the evidence right?) - also for rejected iterations.

## Self-learning rule (lessons)
Every time you run into a problem - a tool error, a failed build, a check you misread, a dead end, a wrong
assumption - write one block in `log/lessons.md` **at once, before working around it**:
```
## L<NN> (iter NN) <short title>
**Problem:** what happened (the exact error / number)
**Cause:** why (once known)
**Fix:** what you did
**Lesson:** the rule you follow from now on
```
Read `log/lessons.md` in full at the start of every iteration and apply it (run B's lessons included). New
lessons continue the numbering after run B's last one. Repeating a logged mistake is itself
logged ("L07 again" in the new block's title). A lesson that has become a standing rule is copied into
"Learned during the run" at the end of this file, marked with its L-number.

## Logs (kept for the report; the judge writes iterations.csv and run.jsonl)
- `log/iter_NN/notes.md`: hypothesis (before), screenshots, result (after).
- `log/tool_changes.md`: one block per change to a tool in `toolbox/` (or a proposed judge fix):
  `## T<NN> (iter NN) <title>`, what, why, which iteration needed it, how you tested it.
- `log/lessons.md`: as above.
- `log/summary.md`: when the budget is used up (or you are sure nothing more can be gained): what worked, what
  did not, the final design in a few lines, and for every kept change its reason in one line. The runner also asks
  for it in a last short session after the time budget.

## Budget
**3 hours of wall time** (`./py judge/iterate.py status` shows the minutes left); no new iteration starts after
that, and a session that runs more than 20 min past it is stopped and its iteration rejected. The run also stops
after 8 iterations in a row without a keep. Gains are harder now than in run B: a bold change that removes a whole
fixed-cost event is worth more than a tenth of a second, but keep each iteration small enough to finish in
~10-15 min.

## Process best practice
- **One change per iteration**, so every delta has one cause. A combined change is allowed only after both parts
  were tested alone.
- **Hypothesis first**: write the expected delta before running; compare after.
- **Biggest phase first** (`phases_s` in the score: where the time goes), not the easiest change.
- **Coarse then fine**: collision step 10 mm to screen, 2 mm to accept.
- **Keep best-so-far**; a rejected change is reverted, its reason logged.
- **After 3 rejections in a row, switch change type** (program -> layout -> jig CAD) to avoid getting stuck.
- **Don't game the judge**: no fewer checks, no skipped parts, no speed changes.

## Design heuristics (generic DFA + robot cell practice)
- Present parts in the orientation they are assembled in; avoid flips and regrasps.
- Assemble top-down along one axis (z), gravity helps insertion; add chamfers / lead-ins to pockets.
- Fewer fixtures and fixture parts; symmetric parts where orientation does not matter.
- Place the most-visited fixtures close together and close to the robot's well-conditioned zone (manipulability:
  `max_mu1_vfix`, `near_singular` in the score).
- Order operations to minimise travel (shortest route through the pick / place points).
- Minimise J1 swings and J6 rotation; avoid wrist flips.

## Working here
- Stay in this folder. Don't read or search anything outside it, no internet, no git. Python: `./py <script>`
  (numpy, trimesh, python-fcl, build123d, matplotlib, scipy are installed). Scratch files go in `scratch/`.
- Kinematics for your own tools: `import sys; sys.path.insert(0, "judge"); import tm5_kin as K; K.use("station")`
  (`K.ik(flange_pose, near_joints)`, `K.fk(joints)`, poses `[x, y, z, rx, ry, rz]` mm / deg, flange in the robot
  base frame; TCP = flange * (0, 0, 160)). The program format is in `judge/program_io.py`. A PTP drives to the
  stored joints; a Line drives the TCP straight to `flange * tcp` from where the arm is (its stored joints are only
  checked against where it ends). `pose_base` in the v3 program = the TCP in the ground base frame (info only).
- The cell's ground base in robot base coordinates is `ground_base_in_robot_base` in `design/cell_layout.json`.
- A judge run at 2 mm takes ~1 min plus ~20 s for the shots; run independent screens in parallel if useful.

## Learned during the run
(Standing rules the agent learned, copied from `log/lessons.md`; each marked with its L-number.)
- Never aim at a judge threshold exactly: approach legs 50.1 mm (toolbox/shrink_legs.py; 0.1 mm covers float error,
  0.5 mm cost 0.7 s), keep slack on clearances. (L01, L57)
- Edit files with Edit/Write; Bash only for `./py ...` runs and listing (in-place sed / long chains get denied). (L02)
- Measure a part contact (scratch/plank_pair.py) before fixing it; carried planks sweep ~250 mm down, so picks go
  outer-first and places robot-side-last - reassign identical parts' start slots rather than raise transits. (L07)
- Measure footprints from the judge's meshes (design/meshes/bench), not the STEP; before cutting a jig surface,
  check every part resting on it at start and end (scratch/footprints_b.py, scratch/contact_pts.py). (L10, L12)
- Parallel screens = parallel Bash tool calls, each a single `./py ...`; no `&`, subshells, `-c` or chains. (L02, L08, L11)
- Every PTP: both ends >= 100 mm from ALL grip/release points, TCP >= top + 100 over every unheld part/jig under it
  (incl. the part about to be picked and the part just released), max TCP z >= 311 if it travels > 100 mm; the
  10 mm screen misses r4 near the ends - only the 2 mm score counts. (L13, L14, L15)
- To shorten a Line with a PTP near the reach edge, end the PTP ON the existing Line (known IK), and keep the rest of
  the Line reaching TCP z >= 311 if it still travels > 100 mm. (L16, L17)
- Append to logs with Edit (anchored on the last line), never Write an existing log file. (L18)
- A PTP end lowers the whole swing (check what the wrist passes mid-swing); look for joints turning the long way
  (scratch/move_times.py, scratch/j6_list.py) - J6 +-360 keeps the pose (toolbox/j6_wrap.py). (L19)
- For r4-sensitive changes near thin parts (planks: 5 mm box), screen with `--step 2 --no-shots`; 10 mm misses it. (L22)
- Probe a wrist-branch change on a rotating Line with kin_check.follow_line first (J4/J6 limits). (L24)
- Before tuning a phase, ask whether the phase (fixture trip, flip, regrasp) is needed at all; an r4 thin-box hit
  at a PTP end is fixed by changing where the PTP comes from, not the end point. (L25)
- When a part's presentation turns, re-place its side-offset transits on the side away from the incoming PTPs
  (toolbox/rotate_picks.py --mirror). (L27)
- J5 sign changes are allowed inside a PTP (the "J5-only flip" is a v3 convention); to lift a J5-limited swing for free,
  add a joint-space via point (toolbox/ptp_via.py) whose other joint deltas stay below J5's in each half. (L34, L35)
- Re-orienting inside a slow leg is free (toolbox/split_rot.py, turn_toward.py), but near the reach edge a J5 change
  at fixed TCP folds the elbow: check K.frames z of joints 3/4 vs the fixtures below (scratch/probe08c.py). (L36, L37)
- A carry parallel to placed parts within ~10 mm: check the PTP midpoint TCP (ptp_via prints it) and bend it away
  with a via point - free while the same joint limits both halves. (L41)
- Raising any part/jig top raises the global r3 safe height (tallest start top + 50): re-check every Line > 100 mm
  horizontal; give PTP ends near grip points ~10 mm slack over 100 mm. (L43)
- The judge ranks on cycle_s rounded to 0.1 s (joints to 1 deg): check the exact totals (scratch/exact27.py) of best and
  candidate before scoring a sub-0.1 s change. (L55)
