# Experiment design: plots, logs, rules

Companion to [README.md](README.md). Draft 2026-11-20, to agree on before Part B runs.

## 1. What the report has to show (→ the plots)

| # | Plot | Shows | x / y | Data | Report section |
|---|---|---|---|---|---|
| P1 | **Progress curve** | how fast each path improved | x: iteration (blind) / version index (human v3→v10); y: cycle time [s]. Every try a dot (kept = filled, rejected = hollow, colour = change type), best-so-far as a step line; v10 as a dashed horizontal line | `log/iterations.csv`, `results/versions.csv` | results |
| P2 | **Waterfall** | which changes bought the time | v3 cycle time → one bar per kept change (Δs, coloured by type: program / layout / jig CAD / tool) → final | `iterations.csv` (kept rows, Δ to parent) | results, DFA discussion |
| P3 | **Phase breakdown** | where the time goes | stacked bars per version (v3, v10, blind best): guide, planks, frame, take-out, home [s] | phase columns | results |
| P4 | **Before / after relative** | all metrics at once | dot plot, one row per metric, v3 = 100 %; dots for v10 and blind best (lower is better, marked per row) | both CSVs | results |
| P5 | **Trade-off scatter** | no metric gamed against another | x: cycle time; y: total joint travel (2nd panel: min clearance); every version and iteration a point, Pareto front drawn | both CSVs | discussion |
| P6 | **Layout + path, top view** | what the cell looks like | XY plan of plate, jigs, rack, AMR; TCP path coloured by phase; v3 / v10 / blind best side by side | cell json + sampled path | concept / final design |
| P7 | **Path, side view** | "travel high, descend vertically" kept | x: path length along program [m]; y: TCP z [mm]; safe height and part tops as lines; PTP segments marked | sampled path | process design |
| P8 | **Joint travel per joint** | where the robot works hardest | grouped bars J1..J6 [deg], v3 / v10 / blind best | per-joint columns | results |
| P9 | **Manipulability along the program** | stays away from singularities | x: move index; y: μ₁ (isotropy), near-singular threshold line | per-move json | robot discussion |
| P10 | **Change-type tally** | what kind of thinking helped | bars per type: tries / kept / s gained | `iterations.csv` | reflection |
| D1 | **Agent loop diagram** | the method | flowchart: brief → hypothesis → change → build → judge → keep/revert → log | drawn once (drawio) | method |
| D2 | **Data flow diagram** | how numbers are produced | program + cell → judge tools → score.json → CSV → plots | drawn once | method |
| R1 | **Renders / video** | the final cell moving | sim viewer screenshots + capture of v3 and blind best | sim_view | appendix / video |

All plots from one script, `plots.py`, reading only the CSV/JSON logs (re-runnable, no hand-edited numbers).
Same colours everywhere: v3 grey, human path blue, blind run orange; change types fixed colours.

## 2. Logs

### `results/versions.csv` and `log/iterations.csv` (same metric columns)
Identity: `label, iteration, parent, timestamp, wall_s, change_type (program|layout|jig_cad|tool|mixed), kept, reject_reason`
Hard checks: `collisions_fixtures, collisions_parts, ik_failures, line_failures, limit_hits, rule_violations`
Time: `cycle_s, cycle_ramps_s, t_<phase>...`
Motion: `tcp_path_m, j1_deg..j6_deg, joint_total_deg, n_moves, n_ptp, n_line, j5_flips`
Safety: `min_clearance_mm, ptp_near_parts, low_traverses, min_z_free_travel_mm`
Robot: `min_mu1 (worst), moves_near_singular`
Assembly: `grips, regrasps, part_flips, jig_count, jig_volume_cm3, jig_max_print_mm`

### Per iteration: `log/iter_NN/`
- `notes.md`: hypothesis ("moving the rack 150 mm toward base A cuts ~8 s from planks"), expected Δ, what was
  changed, result, why kept / rejected. Written **before** the run (hypothesis) and completed after.
- `program.json`, `cell_layout.json` (+ changed jig scripts), `score.json` (full judge output, per-move data for
  P7/P9), `topview.png` (quick P6), `diff.patch` against the parent.

### `log/tool_changes.md`
One block per change: what, why, which iteration needed it, test added, and the **judge re-check**: v3 re-scored
before/after the change must give the same numbers (otherwise the change is rejected or flagged in the report).

### `log/lessons.md` — problems and fixes (self-learning)
Every time the agent runs into a problem (a tool error, a failed build, a check it misread, a dead end, a wrong
assumption), it writes one block **at once, before working around it**:
`## L<NN> (iter NN) <short title>` → **Problem** (what happened, exact error) → **Cause** (once known) →
**Fix** (what it did) → **Lesson** (the rule it follows from now on).
- It **reads `lessons.md` at the start of every iteration** and applies the lessons; repeating a logged mistake is
  itself logged ("L07 again").
- A lesson that became a standing rule is copied into `AGENT.md` under "Learned during the run" (marked as such,
  so the report can tell the rules we gave from the rules it learned).
- For the report: count of problems per type and how many repeated after their lesson (does it actually learn?).

### `log/run.jsonl`
Machine log: start/stop, budget used, wall time per step. Token use, if `claude -p` reports it.

### Screenshots per iteration: `log/iter_NN/shots/`
3D renders of the cell at key steps (after the guides, after each plank, finished bench), iso + top view. The agent
must look at them and write what it sees in `notes.md` before it may keep a change (a hard rule): catches what the
judge can't (a part floating, crooked in its pocket, a jig in an odd place).

## 3. Fair test: the judge is frozen
- The scoring tools (collision.py, kin_check.py, cycle_time.py, manipulability.py, score_run.py, tm5_kin.py,
  robot meshes) are copied in as `judge/`, read-only, with a SHA-256 list. Every score is run with that copy.
- The agent may build its own tools in `toolbox/` (planners, layout search, new checks) and may *propose* a judge
  fix in `tool_changes.md`; it is applied only by us after the run, then everything is re-scored.
- Fixed and not up to the agent: speeds (Line 100 mm/s, 20 mm/s near parts, PTP 50 °/s), gripper waits, robot,
  gripper geometry and stroke, the bench parts, table/plate size. Otherwise "faster" = "turned the speed up".
- The human versions are scored by the same frozen judge, under the same rules (some, e.g. v7/v8, may then show
  violations — that is a result, not a problem).

## 4. Ground rules and best practice for the agent (its `AGENT.md`)

### Hard constraints (any violation = rejected, no matter how fast)
1. No collisions: robot + gripper vs fixtures, carried parts vs everything, at 2 mm / 2° sampling.
2. Every target reachable, every Line followable (kin_check clean), no joint limits.
3. Free moves above a safe height; the last 50 mm into and out of a part are vertical Lines at 20 mm/s.
4. No PTP within 100 mm above a part or fixture.
5. Min clearance ≥ 10 mm in free moves.
6. A released part rests on something (pocket, rack, frame), never in the air. (Needs a check in the judge.)
7. Jigs/fixtures: on the work plate, printable (≤ 250 mm per print part or split), wall ≥ 3 mm, fixed to the plate
   (they move only if the robot moves them on purpose).
8. The bench product does not change.

### Process best practice
- **One change per iteration**, so every Δ in P2 has one cause. A combined change is allowed only after both
  parts were tested alone.
- **Hypothesis first**: write the expected Δ before running; compare after.
- **Biggest phase first** (Pareto on P3), not the easiest change.
- **Coarse then fine**: collision step 10 mm to screen, 2 mm to accept.
- **Keep best-so-far**; a rejected change is reverted, its reason logged.
- **After 3 rejections in a row, switch change type** (program → layout → jig CAD) to avoid getting stuck.
- **Don't game the judge**: no fewer checks, no skipped parts, no speed changes.

### Design heuristics (generic DFA + robot cell practice)
- Present parts in the orientation they are assembled in; avoid flips and regrasps.
- Assemble top-down along one axis (z), gravity helps insertion; add chamfers / lead-ins to pockets.
- Fewer fixtures and fixture parts; symmetric parts where orientation does not matter.
- Place the most-visited fixtures close together and close to the robot's well-conditioned zone (P9).
- Order operations to minimise travel (shortest route through pick/place points).
- Minimise J1 swings and J6 rotation; avoid wrist flips.

## 5. Decisions (agreed 2026-11-20)
1. **Keep/reject**: pass every hard constraint, then lowest cycle time; ties broken by joint_total_deg.
2. **A/B on the rules**: not now. One run with `AGENT.md`; the run without best practice later if there's time.
3. **Rule 6 (part rests on something)**: added to the judge before the run.
4. **Screenshots**: hard rule, see "Screenshots per iteration".
5. **Self-learning**: `log/lessons.md`, every problem + fix logged and re-read each iteration (Bjørge, 2026-11-20).
