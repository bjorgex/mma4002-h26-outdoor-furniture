# Next steps — robot cell v8 (Jig V5, own sim tool)

**Program:** [bench_cell_v8.py](bench_cell_v8.py) → [tests/v8_moves.json](tests/v8_moves.json) · **Jig:** [jig_v5.py](jig_v5.py), [Jig V5 assembly](<../jig-cad/Jig V5/JigAssembly_V5.STEP>) · **Own tools:** [tests/robot_sim/OWN_TOOL.md](tests/robot_sim/OWN_TOOL.md) · **TMflow:** [bench_tmflow/v8/AssembleBench.zip](bench_tmflow/v8/AssembleBench.zip)

## 0e. 2026-11-07 evening: back-end grip, guide split V6 proposal
- **Stage 6 program now: the big half's free back end** (`BIG_GRIP_BACK = "end"`). It's the B-side leg's far corner, gripped across the 10 mm wall and leaning 55° away from the robot. It travels at 290 mm there, since 450 is out of reach. On B it's **let go 18 mm above the seat** (`END_DROP`) and falls onto its own bosses, so the fingers stay above the small half, which sits flush in that corner. **Whole program: no gripper or arm hit**; 2 hits left, both the loose guide passing the bench on the way out.
- **Guide split V6 proposal** (Bjørge's idea), in [Jig V6 proposal](<../jig-cad/Jig V6 proposal>), made by [guide_split_v6.py](guide_split_v6.py). Jig V5 is untouched.
  - The tooth between the back-rest slots (P5 | P6), plus its mirror image, moves from the big half to the small half.
  - Check against the planks as in stage 6: the **new big half slides 200 mm straight towards the robot without touching a plank** (the old one is blocked after 2.5 mm by plank 5). The small half then slides out towards the AMR.
  - Files: `JigAssembly_V6_proposal.STEP` (Jig V5 with the new halves), `GuideSplit_V6_small.STEP` and `GuideSplit_V6_big.STEP` (base-local), `guide_split_v6_top.png`.
  - Not in the program yet. Stage 6 would become: big half first (lift ~90 mm over the rack's height, slide −x out), then the small half (−y).

## 0d. 2026-11-07 day: stage 6 reworked, XYZ axes
- **Stage 6, big half out of the bench** (`BIG_SIDE_IN`, `BIG_SNAP`, `BIG_HELP_MS`, `BIG_EXIT` in [bench_cell_v8.py](bench_cell_v8.py)):
  1. Comes in at a slant past frame 1's edge (120 mm, 75° up, towards −x; the only free line). The approach is **collision-free** now (old #96 gone).
  2. Lifts 90 mm to the middle of the bench, with the guide's bottom above the plank rack's height.
  3. Turns 30° about z, away from the AMR (+30°: the guide's closest point to the AMR goes from 182 to 192 mm). On the real jig this snaps the guide off.
  4. **Waits 5 s** (TMflow WaitFor; the full run and step_run sleep) so people can help.
  5. Goes back out the way it came in, then up, onto the start base.
- Left in the model (accepted): #99 the turn (gripper vs frame 1 / planks 1–2; a smaller lift doesn't help), #100–101 the way out (the guide passes the bench).
- **3D view:** "Base XYZ" / "Tool XYZ" buttons in the Simulator bar: labelled axes of the robot base frame and the tool frame at the fingertips (the Adjust panel's Base / Tool).
- The timeline doesn't show the 5 s wait yet. Only the run does it.
- **Side grip on the tab's end (from the robot side), tested and parked** (`BIG_GRIP_BACK = "side"` is in the code, default `"top"`):
  - Rack where it is: only a steep grip (65° down) clears the rack, and then the 30° turn hits frame 1 and planks 1–2 just as the top grip does (the fingers sit under frame 1's edge, between the planks).
  - Rack towards the robot (−x): the rack ends up under the upper arm.
  - Rack towards B (+y): clears A, but blocks setting the guide down on B, and the plate has no room for both.
  - So the turn hit is not about the grip: anything holding the tab is under frame 1's edge beside planks 1–2.
- **NOW: stage 6 grips the big half's U-leg at its robot end** (`BIG_GRIP_BACK = "leg"`, `BIG_LEG`; Bjørge's screenshot idea):
  - the leg on base B's side, plate x 140 (11.5 mm in from the end), fingers across the 41 mm leg (Hand-E opens to 50), gripper leaning 45° out of the bench
  - **Whole program: 2 hits, both the loose guide passing the bench on the way out (#100–101, accepted).** No gripper or arm hit anywhere.
  - The AMR-side leg (as marked) works at A, but at B its lean points back at the bench on A → wrist hits frame 1.
  - Check at the robot: the snap turn is stiff (μ1 3.7) and 3.5° from a joint limit; the 41 mm leg leaves 4.5 mm per finger when open.
- **Free back end of the big half (`"end"`, Bjørge's 2nd screenshot), tested:**
  - Clean at A (fingers across the 10 mm wall, leaning 55° away from the robot): pick, lift and turn have no gripper or arm hit.
  - But the small half sits flush inside that corner (0 mm gap). On B (small half already back) the inner finger has no room.
  - Swapping stages 5/6 moves the clash to A. Not usable unless the guide gets a gap there (CAD) or another place for the small half.

## 0c. Night of 2026-11-07: guide grips, AMR, sim tools
- **Guide halves gripped by the grip tab** (10 mm wide, on top, middle): small y 22, big y −60 (`GUIDE_TAB`). Base A moved in line with base B. Rack = the 4-hole PlankRack_V3 (`RACK_STL`).
- **Big half, stage 3 (B → A): collision-free.** Found by search (collision.py per candidate): grip **turned 180°** (`GUIDE_SPIN` big 0: the TM5 wrist housing ends up away from planks 1–3) + **tilted 20° away from the planks** (`GRIP_ROLL` big 20), old side tilt off (`GRIP_TILT` 0). Small half tilted 10° → its wrist clears frame 1.
  - Ruled out: tilt only (9+ hits: the wrist hits the planks), gripping further out on the tab, flipped wrist (J5 > 0: the upper arm goes into the bases).
- **Left: 4 hits, all stage 6 (big half out of the bench on A):** #96 approach (frame 1 lies above the tab after the flip) + #99–101 the forced removal (accepted). Options: grip the big half elsewhere in stage 6, or a longer tab on the big half (CAD).
- **AMR:** simplified Omron LD-250 in the 3D cell (`amr_ld250.py`; RoboDK's model can't be exported).
- **Sim page:** Mock/Real switch, Run/Pause/Stop/Reset, timeline (click = jump, drag = speed-limited, play/pause/step), Adjust-step panel (base/tool, X…RZ, history, Save = teach), errors shown.
- Nothing of this committed yet.

## 0b. As built (2026-11-07)
- **Rack and base B are planned where they really sit** (`AS_BUILT_RACK` −2.1/−14.8 mm, `AS_BUILT_B` +8.5/−7.6 mm in [bench_cell_v8.py](bench_cell_v8.py)); program, 3D sim and collision check all use them. Jig design files unchanged.
- Taught corrections rebased to small residuals; **stage 1 on the robot unchanged (0.00 mm)**, stages 2–6 moved ≤ 8.5 mm towards reality.
- **Step tool:** [tests/step_run.py](tests/step_run.py) — Enter/s, `x|y|z`, `rx|ry|rz`, `b`, `step n`, `open`/`close`, `save`, `f`. Push moves after the plank release removed.
- Collisions: 5 moves, all with the big guide half (#64/65 place by plank 6, #105 slide out, #108/109 place onto B by planks 5/6). Stages 2–7 not taught yet.
- **OPEN:** base B fits better turned ~1.5° — check on the real cell; the flip (stage 4) assumes B ∥ A.
- **Big guide half out with frame 2 on (stage 6, #105): accepted as forced** (Bjørge 2026-11-07) — it comes out by force, the planks flex. Proposed motion: lift straight up to the middle of the bench (where the planks flex most), turn 45° there, then out; in the sim mark that hit as expected. Waiting: "middle" = half the bench height? implement now or later?

## 0. Real robot, 2026-11-06 evening
- **Run on the real robot from the page:** `python tests/demo_viewer.py view --robot 10.0.12.101 --port 8092 --cell cell_v8`, then http://127.0.0.1:8092/all → preset → **Run** (same page as the sim; the 3D arm follows the real joints). Run answers every "Enter" prompt; Stop only kills the script (queued moves still run: E-stop). (The "-fast" presets are gone: 1× is real time; speed up with Robot speed.)
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
