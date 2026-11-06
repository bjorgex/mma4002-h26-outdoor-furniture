# Next steps — robot cell v8 (Jig V5, own sim tool)

**Program:** [bench_cell_v8.py](bench_cell_v8.py) → [tests/v8_moves.json](tests/v8_moves.json) · **Jig:** [jig_v5.py](jig_v5.py), [Jig V5 assembly](<../jig-cad/Jig V5/JigAssembly_V5.STEP>) · **Own tools:** [tests/robot_sim/OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md) · **TMflow:** [bench_tmflow/v8/AssembleBench.zip](bench_tmflow/v8/AssembleBench.zip)

## 1. Status (2026-11-06, afternoon)
- **Jig V5 bases turned 180°**: the frame's feet now face the robot. With the feet away from it, the flipped bench was held from below at the far edge and the arm went through the bench.
- **Flip** = a turn about an axis along plate x, lifted 160 mm. The foot goes over the top, away from the arm, and the bench is held at its outer foot. Collision-free.
- **The guide comes out before the bench is lifted.** Small half: lift 25 mm off the bosses, slide out, up, onto the start base. Big half: lift, turn 45°, slide out, onto the start base. After that the bench goes to the AMR.
- **Collision checker fixed:** it now checks carried parts against the robot arm too, and no longer ignores the first moves after a grip.
- **Collisions in the 3D sim:** colliding objects turn red, and a "Collisions" panel in the 3D pane lists every hit.
- **Teach tool:** jog the robot to a grip or approach point and press Enter, and the correction is saved to `teach_v8.json`. See "Teaching the grip points" in [OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md).
- **Checks:**
  - reach: clean, no joint limits
  - fixtures: free
  - parts: 4 known hits, all on the big half in stage 6 (§5)
- **Cycle:** about 306 s at the programmed speeds.

## 2. Where we left off
v8 runs; only the big guide half's way back (stage 6) still has hits in the model.

## 3. Next
1. Start the mock if it isn't running: from `3d-modeling-and-simulation/robot-cell/`, run `python tests/tmflow_mock.py serve --sim`. Open http://127.0.0.1:8090/all and run the scenario **v8-full**. The Collisions panel is at the top right, the Manipulability panel at the bottom left.
2. Big half, stage 6: decide on the real jig how the 45° turn comes out, and where to grip it so the gripper doesn't touch the finished bench while setting the half down on B.
3. Check on the real jig that the seat planks fit the big half's teeth after the flip. The model is 1.6 mm off.
4. At the robot: teach the grip points with `python tests/robot_sim/teach.py v8 --list`, then `... "<move name>" --real`, then `--rebuild`.
5. Test-import [AssembleBench.zip](bench_tmflow/v8/AssembleBench.zip) in TMflow. It is packed in Python without RoboDK's tag.

## 4. Stages (start base B, finish base A)
| # | Stage | Collisions |
|---|---|---|
| 1 | 5 planks (1, 2, 3, 5, 6): rack → frame 1 on B | 0 |
| 2 | small guide half B → A | 0 |
| 3 | big guide half B → A (lifted above the planks, turned −45°; grip tilted 15°) | 0 |
| 4 | frame 1 + planks turned over into frame 2 on A | 0 |
| 5 | small half out of the bench (lift, slide) → B | 0 |
| 6 | big half out (lift, turn 45°, slide) → B | 4 (known, §5) |
| 7 | finished bench A → AMR, home | 0 |

## 5. Open questions / known limits
- **Stage 6, big half:**
  - **Turn and slide (#119–120):** in the model the 45° turn and slide still rub the planks and the small half. Bjørge said to leave this detail for now.
  - **Set-down on B (#123–124):** the gripper touches the finished bench on A.
- **Model fit:** after the flip, the seat planks sit 1.6 mm into the big half's teeth. Either the frame/plank offset in `T_IN` is wrong, or the guide isn't quite symmetric.
- **Assumptions:**
  - T-slot plate = the logged work plate; AMR at plate (100, −370)
  - rack slot 4 empty; pick order 2, 1, 3, 5, 6
  - foot-grip tilt 45°; big-half grip tilt 15° (stage 3 only)
- **Closest approach:** the flip comes within 2.0 mm of the fixtures at #85 (sub pick out).
