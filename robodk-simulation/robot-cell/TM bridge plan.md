# TM bridge — RoboDK plans, the lab TM5-900 runs it (plan, 2026-10-16)

Goal: run sequences planned in RoboDK (the robot-cell scripts) on the real TM5-900 over the
network, including the Robotiq Hand-E, without USB export.

## Verified on the robot today
| What | Result |
|---|---|
| Network | robot `10.0.12.101`, laptop `Ethernet 3` `10.0.12.11/24` |
| State stream | Ethernet Slave 5891 (~100 Hz) and Modbus 502 give joints + flange pose |
| Listen node 5890 | `$TMSTA` status (`true,Listen1`), `$TMSCT` scripts answered `OK` |
| Motion | `Line("CAP",…)` + `QueueTag` moved exactly 20 mm and 50 mm; "done" detected |
| Gripper handover | `ScriptExit()` → GRIP → next Listen node in ~6 s |
| Gripper status | GRIP on air = "loss" (no object) → FAIL exit |
| Tool | `tests/listen_pick_place_test.py` — `teach`, `run`, `status`, `pass`, `up` |

## Steps
0. **Test RoboDK's own TM driver** (motion only) — connect to `10.0.12.101:5890`, read the
   real joints, one small move. Decides whether we need our own motion layer at all.
   Also compare RoboDK's forward kinematics with the robot's reported flange pose
   (checks the model and the Rx/Ry/Rz angle convention).
1. **`tm_listen.py`** — move `packet`, `Listen`, `read_state`, `line` out of the test
   script into a small module; add `ptp(joints)` (`PTP("JPP",…)`).
2. **Generic TMflow project "Bridge"** — one Listen node in a loop, gripper on demand:
   `Start → SET (initialize) → Listen ⇄ Gateway(var_grip) → GRIP / RELEASE → back to Listen`.
   The bridge sends `var_grip = 1` (grip) or `2` (release), then `ScriptExit()`.
   GRIP's FAIL exit also loops back (dry runs grip on air).
3. **Step list from RoboDK** — one function in the cell scripts writes the sequence as JSON:
   `ptp(joints)`, `line(pose)`, `grip`, `release`, `wait(ms)`.
4. **`tm_bridge.py` player** — streams the step list: `--above` dry run, `--step`
   (Enter per step), speed cap, log of every packet.
5. **Calibration** — teach 3 points on the real table → RoboDK cell frame; set the Hand-E
   TCP; verify with a slow touch test before any real pick.
6. **First real run** — one simple pick/place from RoboDK, then a product sequence.

## Open questions
- Goal: full bench assembly with demonstrator parts, or proof that RoboDK drives the lab robot?
- Can the Listen node write the Hand-E registers directly (`modbus_write` on the component's
  Modbus device)? Would remove the gripper handover.
- Project speed is stuck at 5 % in Manual mode — fine for testing, slow for a full sequence.
