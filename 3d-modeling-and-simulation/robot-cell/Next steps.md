# Next steps — robot cell v8 (Jig V5, own sim tool)

**Program:** [bench_cell_v8.py](bench_cell_v8.py) → [tests/v8_moves.json](tests/v8_moves.json) · **Jig:** [jig_v5.py](jig_v5.py), [Jig V5 assembly](<../jig-cad/Jig V5/JigAssembly_V5.STEP>) · **Own tools:** [tests/robot_sim/OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md) · **TMflow:** [bench_tmflow/v8/AssembleBench.zip](bench_tmflow/v8/AssembleBench.zip)

## 0b. As built (2026-11-07)
- **Rack and base B are planned where they really sit** (`AS_BUILT_RACK` −2.1/−14.8 mm, `AS_BUILT_B` +8.5/−7.6 mm in [bench_cell_v8.py](bench_cell_v8.py)); program, 3D sim and collision check all use them. Jig design files unchanged.
- Taught corrections rebased to small residuals; **stage 1 on the robot unchanged (0.00 mm)**, stages 2–6 moved ≤ 8.5 mm towards reality.
- **Step tool:** [tests/step_run.py](tests/step_run.py) — Enter/s, `x|y|z`, `rx|ry|rz`, `b`, `step n`, `open`/`close`, `save`, `f`. Push moves after the plank release removed.
- Collisions: 5 moves, all with the big guide half (#64/65 place by plank 6, #105 slide out, #108/109 place onto B by planks 5/6). Stages 2–7 not taught yet.
- **OPEN:** base B fits better turned ~1.5° — check on the real cell; the flip (stage 4) assumes B ∥ A.
- **Big guide half out with frame 2 on (stage 6, #105): accepted as forced** (Bjørge 2026-11-07) — it comes out by force, the planks flex. Proposed motion: lift straight up to the middle of the bench (where the planks flex most), turn 45° there, then out; in the sim mark that hit as expected. Waiting: "middle" = half the bench height? implement now or later?

## 0. Real robot, 2026-11-06 evening
- **Run on the real robot from the page:** `python tests/demo_viewer.py view --robot 10.0.12.101 --port 8092 --cell cell_v8`, then http://127.0.0.1:8092/all → preset → **Run** (same page as the sim; the 3D arm follows the real joints). Run answers every "Enter" prompt; Stop only kills the script (queued moves still run: E-stop). Use `v8-full`, not `-fast`, on the robot.
- **Bridge check passed** (`hande_bridge.py check`): RELEASE, GRIP, Home2 all answer.
- **GRIP1 target must be fully closed (255).** It was 80 (~34 mm gap) → every grip reported "object loss".
- **After a GripLost:** clear the error in TMflow and restart HandE_Bridge_v1, else the Listen node answers status but not scripts (the run hangs at connect).
- **Every run starts with RELEASE** (gripper open) — `v4_replay.py`.
- **Plank picks taught** (`teach_v8.json`): plank 2 taught, copied to 1, 3, 5, 6 (one rack). Shift on the plate −2.1, −14.8, +3.7 mm, plus `PLANK_PICK_DZ = −10` in `bench_cell_v8.py`. Checked on the robot: goes to the taught pose to 0.01 mm, fingers straight.
- **The Hand-E sits tilted on the flange (~2–3°): it is NOT symmetric about the tool axis.** The taught wrist half-turn must stay (J6 ≈ 238° at the picks). The places still use the old wrist side → the gripper is crooked there. Fix: teach plank 2's place, then model the mounting tilt once as a fixed tool rotation for all grips.
- **Plank guide in the model ≠ the real one** (real: one M8 hole on each of 4 sides). Need its CAD or measurements to fix `jig_v5.py`; the −14.8 mm y shift is probably this.

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
0. At the robot: teach **plank 2's place** (jog to the place in frame 1, fingers straight; `teach.py v8 "plank2 place" --real --with-rotation`). From pick + place, separate the gripper's mounting tilt from the rack offset and put the tilt in the program for all grips. Then a full `v8-full` run at 10–20 %.
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
| 6 | big half out (lift 90, turn 45°, slide) → straight onto B (grip tilted −10°); never onto the AMR | 1 (#120, §5); the EGP box model grazes plank 6 at the place (an 82 × 78 mm body clears it: check the real Hand-E) |
| 7 | finished bench A → AMR, home | 0 |

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
