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

## Status
- 2026-11-20: plan written. Next: v3 cell builder + `score_run.py` (Part A), then the sandbox.
