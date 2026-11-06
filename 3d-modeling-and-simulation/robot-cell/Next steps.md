# Next steps — robot cell v8 (Jig V5, own sim tool)

**Program:** [bench_cell_v8.py](bench_cell_v8.py) → [tests/v8_moves.json](tests/v8_moves.json) · **Jig:** [jig_v5.py](jig_v5.py), [Jig V5 assembly](<../jig-cad/Jig V5/JigAssembly_V5.STEP>) · **Own tools:** [tests/robot_sim/OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md) · **TMflow:** [bench_tmflow/v8/AssembleBench.zip](bench_tmflow/v8/AssembleBench.zip)

## 1. Status (2026-11-06, afternoon; big-half ending reworked while Bjørge was away)
- **Jig V5 bases turned 180°**: the frame's feet now face the robot. With the feet away from it, the flipped bench was held from below at the far edge and the arm went through the bench.
- **Flip** = a turn about an axis along plate x, lifted 160 mm. The foot goes over the top, away from the arm, and the bench is held at its outer foot. Collision-free.
- **The guide comes out before the bench is lifted.**
  - Small half: lift 25 mm off the bosses, slide out, up, onto the start base.
  - Big half: lift 90 mm (above the rack and the small half), turn 45°, slide out, then **park it on the AMR plate**.
  - Then the bench goes onto the AMR, and the big half goes from the AMR onto B, gripped on its outer arm.
  - Why the parking: set straight onto B, the gripper hit the finished bench still on A.
- **Collision checker fixed:** it now checks carried parts against the robot arm too, and no longer ignores the first moves after a grip.
- **Collisions in the 3D sim:** colliding objects turn red, and a "Collisions" panel in the 3D pane lists every hit.
- **Teach tool:** jog the robot to a grip or approach point and press Enter, and the correction is saved to `teach_v8.json`. See "Teaching the grip points" in [OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md).
- **Checks:**
  - reach: clean, no joint limits
  - fixtures: free
  - parts: 1 hit, the big half's slide out through seat planks 1–3 (§5)
- **Cycle:** about 333 s at the programmed speeds.

## 2. Where we left off
v8 runs. One hit is left: the big half's slide out (#120). In the CAD the big half is locked between the planks (§5).

## 3. Next
1. Start the mock if it isn't running: from `3d-modeling-and-simulation/robot-cell/`, run `python tests/tmflow_mock.py serve --sim`. Open http://127.0.0.1:8090/all and run the scenario **v8-full**. The Collisions panel is at the top right, the Manipulability panel at the bottom left.
2. Big half: try the 45° turn on the real jig with the bench flipped into it. In the CAD it's locked (§5). If it is locked for real too, the big half needs more clearance or a tooth removed (ihammer18).
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
| 6 | big half out (lift 90, turn 45°, slide) → parked on the AMR plate | 1 (#120, §5) |
| 7 | finished bench A → AMR (far half of the AMR plate) | 0 |
| 8 | big half AMR → B (other arm), home | 0 |

## 5. Open questions / known limits
- **Big half locked in the CAD:** with the small half out, no slide or turn frees it. Checked as a 2D search with 1 mm and 1° steps, with the guide either way up, even with 1.8 mm extra clearance:
  - the seat planks block −x until the half moves −y
  - the back planks block −y until it moves −x
  - So #120 (slide out) collides with seat planks 1–3.
- **The 45° turn (#119) is only partly checked.** It shows no hit because the checker allows contacts that already exist at the grip for 2 moves, and the planks already touch the big half there.
- **AMR plate assumption:** 300 × 320 holds both the bench (far half) and the parked big half (near half, about 10 mm gap, overhanging the edge by about 4 mm).
- **Model fit:** after the flip, the seat planks sit 1.6 mm into the big half's teeth. Either the frame/plank offset in `T_IN` is wrong, or the guide isn't quite symmetric.
- **Assumptions:**
  - T-slot plate = the logged work plate; AMR at plate (100, −370)
  - rack slot 4 empty; pick order 2, 1, 3, 5, 6
  - foot-grip tilt 45°; big-half grip tilt 15° (stage 3 only)
- **Closest approach:** the flip comes within 2.0 mm of the fixtures at #85 (sub pick out).
