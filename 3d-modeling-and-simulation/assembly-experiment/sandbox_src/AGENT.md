# AGENT.md: improve the bench assembly cell

You are improving a robot cell that assembles a small outdoor bench (1:7.5 demonstrator) with an Omron TM5-900 arm
and a parallel gripper (EGP). You start from the cell's first working version, **v3**, and make it as fast as you
can while it stays legal (the hard constraints below). You work alone, in this folder only, in iterations: one
change, build, simulate, score, keep or reject, log. Every number comes from the frozen judge in `judge/`.

## The cell (v3) and what it does
- Robot at the origin of the robot base frame; the work plate (590 x 440 mm "ground base") lies at x -206..-796 mm.
  Everything is placed on the ground base frame (`design/build_cell.py`: x away from the robot, y to the left).
- Jigs: **base A** (pocket for frame 1, 180 x 180 mm on a 10 mm riser), **base B** (frame 2, mirrored), the
  **plank jig** (6 slots, 2 rows of 3, planks stand upright), and a **double-sided guide** (a plate with 6 slots
  that holds the planks upright over a frame; a grip pocket in the side of its short arm).
- Start: base A holds frame 1 + 6 interface pieces (piece A1..A6), base B holds frame 2 + 6 interface pieces
  (piece B1..B6) with the guide lying on top, the planks (plank1..plank6) stand in the plank jig.
- The v3 program (`design/program.json`, 120 moves):
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
   `# iter NN: <title>`, `## Hypothesis` (what you change, why, the expected delta in s / violations, the change
   type: program | layout | jig_cad | tool | mixed), **before** you run anything that scores it.
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
Read `log/lessons.md` in full at the start of every iteration and apply it. Repeating a logged mistake is itself
logged ("L07 again" in the new block's title). A lesson that has become a standing rule is copied into
"Learned during the run" at the end of this file, marked with its L-number.

## Logs (kept for the report; the judge writes iterations.csv and run.jsonl)
- `log/iter_NN/notes.md`: hypothesis (before), screenshots, result (after).
- `log/tool_changes.md`: one block per change to a tool in `toolbox/` (or a proposed judge fix):
  `## T<NN> (iter NN) <title>`, what, why, which iteration needed it, how you tested it.
- `log/lessons.md`: as above.
- `log/summary.md`: when the budget is used up (or you are sure nothing more can be gained): what worked, what
  did not, the final design in a few lines.

## Budget
At most 30 iterations, and the run stops after 5 iterations in a row without a keep. Spend them well.

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
