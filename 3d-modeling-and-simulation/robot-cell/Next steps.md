# Next steps — robot cell v8 (Jig V5, own sim tool)

**Program:** [bench_cell_v8.py](bench_cell_v8.py) → [tests/v8_moves.json](tests/v8_moves.json) · **Jig:** [jig_v5.py](jig_v5.py), [Jig V5 assembly](<../jig-cad/Jig V5/JigAssembly_V5.STEP>) · **Own tools:** [tests/robot_sim/OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md) · **TMflow:** [bench_tmflow/v8/AssembleBench.zip](bench_tmflow/v8/AssembleBench.zip)

## 1. Status (2026-11-06, built overnight)
- v8 built without RoboDK: own TM5 kinematics, collision check, cycle time, TMflow export ([OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md)).
- **Collision-free** (fixtures + carried parts, 2 mm samples), every target in reach, no joint past a limit, no wrist/elbow flips inside a stage. Full replay finished in the mock (exit 0).
- Cycle: 313 s programmed, ≈ 345 s with TMflow's acceleration ramps.
- Manipulability: map + layers in the 3D view ("Manipulability" panel, bottom left); standalone page [manipulability.html](tests/robot_sim/manipulability/manipulability.html).

## 2. Where we left off
Program runs clean in the sim; decisions made while Bjørge slept need his review (§5).

## 3. Next
1. Mock running? Otherwise, from `3d-modeling-and-simulation/`: `python robot-cell/tests/tmflow_mock.py serve --sim`, then open http://127.0.0.1:8090/all → scenario **v8-full**.
2. Watch the run with the Manipulability panel on (path colouring, live gauge). Check the 3 decisions in §5, especially the new stage order.
3. Search `# DECISION 2026-11-06` in [bench_cell_v8.py](bench_cell_v8.py) and change what's wrong; then re-run: `python bench_cell_v8.py` → `python tests/robot_sim/cell_layout.py --cell v8` → `python tests/robot_sim/collision.py tests/v8_moves.json --cell tests/robot_sim/cell_v8.glb --parts`.
4. Test-import `bench_tmflow/v8/AssembleBench.zip` in TMflow (it has no RoboDK zip tag — unknown if TMflow accepts it).
5. Commit is local only (not pushed) — push when happy.

## 4. Stages (start base B, finish base A)
| # | Stage | Collisions | Worst μ1 |
|---|---|---|---|
| 1 | 5 planks (1,2,3,5,6) rack → frame 1 on B | 0 | 3.1 |
| 2 | small guide half B → A | 0 | 2.1 |
| 3 | big guide half B → A (lift above planks, then turn −45°) | 0 | 2.1 |
| 4 | frame 1 + planks flipped into frame 2 on A | 0 | 4.6 (foot grip at plate corner) |
| 5 | finished bench A → AMR | 0 | 3.1 |
| 6 | small half A → B | 0 | 2.1 |
| 7 | big half A → B, home | 0 | 2.1 |

## 5. Open questions / decisions to review
- **DECISION 1:** big half lifted until 15 mm above the plank tops, then turned −45° (turning among the planks always collides).
- **DECISION 2:** gripper = Robotiq Hand-E, finger gap per move; guide arms measured 17 mm at the grip point.
- **DECISION 3 (most important):** the big half is trapped under the turned-over bench on JigV3 → new order: bench to the AMR **first**, then both guide halves back to B.
- Assumptions: T-slot plate = the logged work plate; AMR at plate (100, −370); rack slot 4 empty; pick order 2,1,3,5,6; flip height 340; foot-grip tilt 30°.
- Closest approach: "sub pick" 1.4 mm / "sub pick out" 2.2 mm to the base edge (by design, as v7).
- Stage 4 μ1 up to 4.6: OK but not great; better only by moving the frame-foot grip.
