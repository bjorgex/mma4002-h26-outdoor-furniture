# v11 one-plank test — where we stopped (2026-11-20, ~19:15)

Real TM5 robot, TMflow project **HandE_Bridge_v1** (Listen mode), step tool `tests/step_run.py --cell v11_1plank`.

## Start next session
1. TMflow: open **HandE_Bridge_v1**, speed **10–20 %** (it was at 90 % at the crash), robot clear above the plate, Start.
2. Remove the bad point (saved at the crash pose, see below):
   `C:\Users\bjoer\dev\studyDev\MSc-MechAuto-NTNU\.venv\Scripts\python.exe tests\robot_sim\teach.py v11_1plank --clear "frame flip over pick"`
   then `... teach.py v11_1plank --rebuild`
3. Step tool, from the step after the last good point:
   `C:\Users\bjoer\dev\studyDev\mma4002-h26-outdoor-furniture\3d-modeling-and-simulation\robot-cell\step_v11.ps1 --from 33`
   (33 = big half to B place; 37 = frame flip over pick). The part (guide big half) must be in the gripper for 33,
   or start at 36/37 if the guides are already in place on Base B.

## Taught (teach_v11_1plank.json) — good
plank pick, plank pick approach, plank above guide, plank above interface, plank place (via the step tool),
small half to B: pick approach, pick, place approach, place; big half to B: pick approach, pick, place approach.
`teach.py v11_1plank --show` lists them with the corrections.

## Bad — clear it
**frame flip over pick** (19:10): saved at the crash pose x -204.08 y -170.31 z 275.87 rx -85.42 ry 0.85 rz 83.13
(+49.5 deg rotation, +161 mm) — the arm had swung ~90 deg after a `set` and faulted. Not a real taught point.

## What happened
A `set X Y Z RX RY RZ` before a step gave a target the arm reached with a ~90 deg wrist swing (tool horizontal,
J5 124 deg) at 90 % speed → robot error, step tool lost the Listen connection (WinError 10054). `set` now refuses
targets > 150 mm / > 60 deg from the STEP'S OWN target (goto: from the current pose) or a different joint setup, and prints what it read.

## Settings changed today (HandE_Bridge_v1 Variables)
`..._SET1_var_release_pos = "10"` (open width), `var_grip_force = "100"`, `var_reset = true` (needed, else the
gripper setup FAILs and ignores the new values). Program: `plank above interface` step (15 mm over the place).

## Step tool commands (tests/step_run.py)
Enter = next · s = skip · q = stop · x|y|z <mm>, rx|ry|rz <deg> (nudge) · set X Y Z RX RY RZ (next step's target) ·
goto X Y Z RX RY RZ (straight there) · save · b = back · step <n> · open/close · `--from <n>` on start.
Before each step it shows now / next / diff; after `save` the saved pose as a `set ...` line.
