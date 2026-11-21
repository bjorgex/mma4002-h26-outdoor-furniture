# Assembly experiment: from an inefficient cell to an efficient one

**Question:** starting from the first working bench cell (v3), how far can an AI agent improve the automated
assembly with our own sim tools (no RoboDK), and how does that compare to the path we took by hand (v3 → v10)?
Feeds DAM Assignment 4 (DFA²: initial design → changes → evaluate again) and the final report.

Everything runs on **bj-hserver** (20 cores, CPU tools: numpy, trimesh, python-fcl, build123d). No RoboDK anywhere.

## Part A: score the versions we already have
One scorer, `score_run.py`, runs the own tools (`../robot-cell/tests/robot_sim/`: collision.py, cycle_time.py,
kin_check.py, manipulability.py) on one program + cell and writes one row to `results/versions.csv`.
Versions: v3, v4, v5, v6, v7, v8, v8x2, v9, v9x2, v10, each with its own cell model (`VERSIONS` in `score_run.py`).

```
python score_run.py --version v9                      one version
python score_run.py --all --jobs 10                   all of them (the server: run_part_a.sh, commits + pushes)
python score_run.py <program> <cell.glb> --label try1 any program + cell (Part B uses this)
```
- **v3 cell:** `cell_layout.py --cell v3` → `cell_v3.glb` from `bench_cell_v3.py`'s constants (no RoboDK). Check:
  fixtures free (as RoboDK said); the parts check finds the same hits as v4 (forearm over standing planks 4/5 on the
  guide pick, plank1/plank2 on the place travel). RoboDK's v3 check had no parts check, so those hits are real.
- **Geometry:** v3–v7 joints come from RoboDK's station (`robodk` link lengths), v8+ from our IK (`techman`).
- **v10** = v9's program moved to one camera-found layout (`v10_moves.json` `jig_moves`): v9's cell with each carrier
  and what sits on it shifted the same way (frame 1, pieces A and the guides ride on Base B).
- **Definitions** of every column are in `score_run.py`'s docstring (e.g. `ptp_near_parts` = PTP moves starting or
  ending within 100 mm of a grip/release point; `low_traverses` = moves > 100 mm sideways whose TCP stays below the
  tallest object + 50 mm).
- **Empty in Part A:** `iteration`, `wall_time_s`, `kept`, `tool_changes` (Part B only). `min_clearance_mm` is empty
  if every sample collides (never so far).

## Part B: blind run from v3
- **Sandbox** (`make_sandbox.py` → `~/dev/assembly-blind/` on the server): v3's program, v3's cell (layout json,
  jig + bench meshes, the build123d jig/bench scripts for v3) and the tools. No git history, no v4+ scripts,
  moves, cells or reports, tool docstrings scrubbed of later design ideas. A leak check (grep for the later ideas)
  must pass before a run.
- **Agent:** headless `claude -p` in the sandbox, with `AGENT.md` as its brief. It may change:
  1. the program (moves, order of operations, approach paths),
  2. the jig / fixture layout (positions, rotations),
  3. the jig and fixture 3D models (build123d scripts → STL → cell model),
  4. the tools themselves (fix a bug, add a metric or feature).
  The bench product (frame, planks, interface pieces) stays as it is.
- **Loop:** propose → build → simulate → score → keep or reject. Budget: max 30 iterations or 5 in a row
  without improvement.
- **Logs** (for the report, written as it goes):
  - `log/iterations.csv`: one row per iteration, the same columns as Part A + kept/rejected.
  - `log/iter_NN.md`: what it changed, why, the result.
  - `log/tool_changes.md`: every change to a tool (what, why, diff path), so tool changes can be told apart
    from design changes.
- **Rules given to it:** travel high, descend vertically, no PTP near parts, least movement and rotation,
  grab from above, collision-free (fixtures and parts), reachable (IK).

## Metrics (one row per run)
| Group | Columns |
|---|---|
| Time | cycle_s (programmed), cycle_ramps_s, time per phase |
| Motion | tcp_path_m, joint_travel_deg (per joint + total), j6_total_deg, n_moves, n_ptp, n_line, wrist (J5) flips |
| Safety | collisions_fixtures, collisions_parts, min_clearance_mm, ptp_near_parts, low_traverses |
| Robot | ik_failures, line_failures, limit hits, min manipulability, moves near singular |
| Assembly | grips, regrasps, part flips, jig parts (count), jig volume |
| Process (Part B) | iteration, wall time, kept/rejected, tool changes |

## Part B: how it is built (2026-11-20)
- **Judge** (`judge/`, frozen; copied read-only into the sandbox with a SHA-256 list): the own tools trimmed to what
  scoring needs, no RoboDK package anywhere (`tm5_kin` link lengths "station" = the v3 program's, same numbers as
  Part A's "robodk"; `program_io.py` instead of the TMflow exporter). `score.py` = `score_run.py`'s metrics + the
  hard-rule columns (`rule_violations`, `r1`..`r8`, `r_fixed`, see its docstring) incl. **rule 6** (a released part,
  moved 2 mm down, must hit something; collision.py `rest`) and **rule 8** (bench parts unchanged and assembled
  within 2 mm at the end). `shots.py`: headless matplotlib renders (iso + top) at the start, after every release
  and at the end, plus `topview.png` with the TCP path. `iterate.py`: score / decide / status, the keep rule
  `(fails a rule?, rule_violations, cycle_s, joint_travel_deg)`, `iterations.csv`, `run.jsonl`, best/ snapshot.
- **Judge re-check** (`rescore_check.py` -> `results/judge_check.csv`): v3 and v10 re-scored with the judge, every
  Part A column unchanged (phases now named by grips: v3 "other" -> "guide"). v3: 28 violations (5 part
  collisions, 18 approach, 1 PTP near, 4 clearance < 10 mm). v10's rule columns are not comparable (other gripper
  with `egp_gap`, other plate and frame model).
- **Sandbox** (`make_sandbox.py` -> `~/dev/assembly-blind/`): `AGENT.md` (`sandbox_src/AGENT.md`), `judge/`,
  `design/` (v3 program, `build_cell.py` = the v3 cell from constants with numpy, identical to `cell_v3.glb`,
  jig/bench STLs, `cad/` jig_parts / jig_guide / bench_parts + STEP inputs), `toolbox/`, `log/`, `best/`. Leak check
  (later ideas, v4+ names, RoboDK, repo paths) must pass, also at every runner start.
- **Runner** `run_part_b.sh`: baseline (iter 00), then one headless `claude -p` session per iteration
  (`--permission-mode dontAsk` + `~/dev/assembly-blind.settings.json` from outside the sandbox: Read/Edit/Write/
  Glob/Grep + `./py`, ls, cp, mv, mkdir, diff; no web, no git; editing judge/, best/ and the judge's logs and reading
  the repo denied), `stream_filter.py` writes `log/run.jsonl` as it happens, a watchdog puts
  back changed judge files, at the end `log/` + `best/` go to `results/part_b/` (raw claude streams gzipped, shots of
  kept iterations only) and are committed + pushed from the server. Watch: `watch_server.ps1`.

## Part B2: second blind run from Part B's best (2026-11-22)
- Why: Part B hit its 30-iteration cap while still improving (iter 30 kept). B2 starts from Part B's best and carries
  over its lessons (L01-L30), standing rules and toolbox.
- Changes vs B, each with its reason in `report/part_b2_report.tex` section 1: 3 h wall-time budget (`run_part_b2.sh`,
  `BUDGET_S`), no-keep streak 8, `judge_b2/` = Part B's judge + its own proposed fix (a Line's time includes tool
  rotation at 50 deg/s: Part B best 112.9 -> 114.9 s) + a mandatory `## Reason` section and `reason` column,
  `sandbox_src/AGENT_B2.md`, sandbox `make_sandbox_b2.py` (leak check allows lines Part B wrote itself).
- Reports: `report/part_b_report.pdf`, `report/part_b2_report.pdf` (`report/build_figs.py part_b|part_b2`).

## Status
- 2026-11-20: plan written. Next: v3 cell builder + `score_run.py` (Part A), then the sandbox.
- 2026-11-20: Part A done (`results/versions.csv`). Part B built: judge with rule 6 + screenshots, judge re-check OK
  (v3, v10), sandbox + leak check PASS, harness smoke test, then the blind run launched on bj-hserver
  (`results/part_b.log`; stop: `kill $(cat ~/dev/assembly-blind/log/runner.pid)`). Next: `plots.py` from the logs.
- 2026-11-22: Part B report written (`report/part_b_report.pdf`). Part B2 launched 00:16 on bj-hserver (3 h).
