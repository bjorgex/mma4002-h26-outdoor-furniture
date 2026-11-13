# Own robot-cell tool: what RoboDK did, without RoboDK

Four command-line tools in `tests/robot_sim/`, all pure Python + trimesh/python-fcl in the shared venv.
They take a **program**: a TMflow export (`bench_tmflow/vN/AssembleBench.zip`), a moves file
(`tests/vN_moves.json`) or a program json (see `tmflow_export.py`'s docstring: a moves file plus
`base`, `tcp`, `wait_ms`, messages). Run them from `robot-cell/`.

| RoboDK did | Own tool | Command |
|---|---|---|
| IK / reachability (`robot_cell.ik`, `MoveL_Test`) | `kin_check.py` | `python tests/robot_sim/kin_check.py bench_tmflow/v7/AssembleBench.zip [-v]` |
| Collision check over the program (`check()`, `check_parts()`) | `collision.py` | `python tests/robot_sim/collision.py <program> --cell v7 [--parts] [--shift "Base B:0,-30,0"]` |
| TMflow export (Omron post, `MakeProgram`) | `tmflow_export.py` | `python tests/robot_sim/tmflow_export.py export <program> -o out/AssembleBench.zip` |
| Cycle time (`cycle_times.py`) | `cycle_time.py` | `python tests/robot_sim/cycle_time.py <program>` |

Reference programs (RoboDK's v3/v4/v6/v7 exports turned into program json, with RoboDK's joints):
`tests/robot_sim/ref/vN_program.json` (`python tests/robot_sim/tmflow_export.py selftest` rewrites them).

From Python, e.g. a v8 cell built without RoboDK:

```python
from collision import check_program
hits = check_program("tests/v8_moves.json", "tests/robot_sim/cell_v8.glb", parts=True)   # [] = free
```

The cell argument is `"v6"`/`"v7"` (built from `bench_cell_vN.py`'s constants), a cell `.glb` in robot
base coordinates (as `cell_layout.py` writes; kinds read from the `cell_layout*.json` with the same suffix),
a layout json, or a dict `{name: (kind, trimesh)}`.

## Results against RoboDK (v3-v7)

- **Kinematics:** FK(RoboDK's joints) = RoboDK's flange within 0.005 mm (v7) / 0.05 mm (v3-v6). No limit
  broken, every Line followable. Flags: v7 moves #125/#126 (bench re-grip "pick out low" / "pick") are stored
  with the other wrist (J4 -178.8, J5 +90) than the line reaches them in (J5 -90); v6 #138/#139 stored with
  J6 one turn off. Harmless if TMflow takes Line targets as Cartesian, a wrist flip if it uses the stored joints.
- **Collisions:** v6 free (RoboDK: none), parts check free too; v6 with the plank jig 40 mm higher: 2 moves
  flagged, base B 25 mm higher: 10 moves, guide outer half 40 mm lower: 2 parts hits; v5 moves on `cell_v5.glb`:
  free. One run takes ~2 min at `--step 2` (pure-Python IK along the lines); `--step 5` for quick checks. v7: first collision at "guide A-B pick out low" (move #75, wrist vs
  plank rack), the same move RoboDK stopped at (instruction 164); RoboDK stops at the first collision, ours lists
  all (29 moves; plank rack vs wrist during the guide stages, link 6 vs base B / table at the frame-1 place).
- **TMflow export:** import -> export gives byte-identical `.flow`, `.dat`, `.prog`, `ConfigData.xml` for all four
  exports. From `tests/v4_moves.json` (RoboDK's station data): same moves, speeds, I/O, waits; poses within
  0.05 mm, joints within 0.001 deg (rounding of the moves file).
- **Cycle time:** v3 239.8 s, v4 345.1 s, v6 330.2 s, v7 340.7 s = `cycle_times.csv` (v6 there: 330.1 s).

## What still needs RoboDK (or isn't done)

- **Zip tag:** the exports carry a 192-character comment written by RoboDK's `TMExportZip.exe` (an encrypted
  vendor/password tag TMflow's import checks). Run outside RoboDK, that exe fails here
  ("ZipDirectory error: Ugyldig referanse"), so `--packer auto` falls back to a pure-Python zip: same files,
  same encryption (ZipCrypto, password `robodk1234`), no tag. **Untested whether TMflow imports it** - try one
  on the robot / TMflow before relying on it.
- `<Custom max>` in the `.dat` (113, v7: 112): unexplained; the importer keeps it, default 113.
- **Planning** (`bench_cell_vN.py`'s target poses, `elbow_up`, wrist swaps, `follow`) is still RoboDK code; these
  tools check and export a program, they don't make one. The v8 builder supplies the moves.
- Collision model differences: Techman's link meshes (not RoboDK's), the EGP as three boxes, the AMR's LD-250
  left out (v7 switches it off as well); the parts check's allowed contacts are rules (see `collision.py`),
  not RoboDK's exact pair lists.
- Phases in `cycle_time.py` for a TMflow export are cut at the gripper events (no move names in the zip):
  totals exact, phase split a few seconds off.

## Teaching the grip points on the real robot (`teach.py`)

The program's grip points come from CAD; on the real cell a part is a few mm off. `teach.py` lets you put
the gripper where a grip really is and stores the difference; the next build uses it.

**How it reads the robot:** the Ethernet Slave stream (port 5891, `Coord_Robot_Flange` + `Joint_Angle`), the
same read-only stream `log_points.py` used on 2026-10-16. It never moves the arm. The **Point button on the
end module can't be "heard"**: it makes a Point node inside TMflow, and that doesn't go out on any port we use.
**Enter on the laptop** does the same job.

**Once, in TMflow:** the Ethernet Slave is on (Setting → Connection → Ethernet Slave, data table with
`Joint_Angle` and `Coord_Robot_Flange`, enabled). The laptop is on the robot's network (10.0.12.x).
`python log_points.py --show` should print a pose.

**At the robot** (from `robot-cell/`):
1. `python tests/robot_sim/teach.py v8 --list`: every grip event as *approach → GRIP* (taught ones marked `*`).
2. Put the part where it really sits. Jog (manual mode, slow) or hand-guide until the fingertips are where
   they should be when the gripper closes on it. The gripper should be open at the program's gap, not pressing
   on the part.
3. `python tests/robot_sim/teach.py v8 "plank2 pick" --real`. The line updates live with how far you are from
   the plan (plate dx dy dz). When it looks right, keep still and press **Enter** (`q` = cancel).
   - It refuses if the arm is still moving, or if it's more than 30 mm from the plan (`--max-mm`).
   - Only the position is stored. Add `--with-rotation` if you deliberately corrected the angle (after
     hand-guiding the angle drifts, so the default is safer).
   - A taught grip moves its approach (the moves straight above it) and its follow moves (pick out / lift /
     push / place out) by the same amount, so "straight down" stays straight. To teach an approach
     separately: `teach.py v8 "plank2 pick approach" --real`.
4. Repeat for the other grips. `teach.py v8 --show` lists them; `--clear "<name>"` (or `all`) forgets them.
5. `python tests/robot_sim/teach.py v8 --rebuild` rewrites `tests/v8_moves.json` and
   `bench_tmflow/v8/AssembleBench.zip` with the corrections (`--out x.zip` to write somewhere else).
   Then re-run `collision.py` (step 3 in Next steps).

**Where it's stored:** `robot-cell/teach_v8.json`. Each correction is in the grip's own TCP frame, and that frame is
fixed to the part, so it still applies after a base is moved or turned on the plate. If the plate/work frame
in `bench_layout.json` is re-logged, check the taught points again: they also absorbed the old frame's error.

**Safety:** the first run after a rebuild goes in manual mode at low project speed (10-20 %), step by step,
with a hand on the stop. Watch every corrected approach go down. Check that the correction is the size you
expect (`--show`). A wrong move name taught at the wrong spot is the typical mistake. Nobody near the arm
while it runs.

Test without the robot: `python tests/tmflow_mock.py serve --sim --listen 7990 --slave 7991 --view 0`, move the
mock's arm through its Listen port, then `teach.py v8 "plank2 pick" --port 7991 --now` (`--now` = no Enter).
Set `TEACH_FILE` to write a scratch file instead of `teach_v8.json`.

## Tool camera, free move and jig mover (3D view)

A mock of an eye-in-hand camera, so vision code can be written and tested without the robot.

**Tool camera panel** (`vision_layer.js`, bottom right)
- The camera sits where the TM5's built-in camera is: the lens of the end module's housing in Techman's link_6 mesh
  (`tm5_links.glb`), at x 0, y +75 mm, just in front of the housing face (z 53) in the joint-6 frame. You can change it
  under ⚙. It looks the way the fingers point, with a 45° vertical FOV (a guess; check it against the real camera) at
  1280×960. **Camera view** shows it live.
- **📷 Photo** saves `tests/vision_lab/sim_shots/<stamp>.png` + `.json`. The JSON holds the pinhole `K`, `T_base_cam`
  (OpenCV axes: x right, y down, z forward; mm, robot base), `T_base_flange`, the joints, and under `objects` the
  **true** pose of every moved jig, so a detector can check itself.
- **✥ Free move** jogs the sim arm through the mock's Listen node. The **Tool frame / Base frame** switch picks the
  axes: **Tool** (default) moves along the tool tip's own X Y Z, the **Tool XYZ** triad (turned on with Free move),
  and ⟲ ⟳ turn about the tool's Z. **Base** moves along the robot base's X Y Z. The arrow pad is ±X / ±Y, then
  +Z / −Z (the ⬆⬇ shows which way that is now) and ±Rz, in the triads' colours (X red, Y green, Z blue). Keyboard:
  arrows, PgUp/PgDn, Q/E. Step 1–50 mm/deg; "Look down" points the camera straight down. **Only the arm moves**:
  the program, the taught points and the cell files stay as they are (unlike *Adjust step*). The mock must be idle at
  its Listen node, not in the middle of a run.

**Jigs panel** (`jig_layer.js`, bottom left, **Move jigs**)
- **Select:** tick jigs in the list, or click them in 3D (Ctrl-click adds/removes).
- **🔗 Lock together:** the selected jigs become one group. Selecting one of them selects the whole group, so they
  always move together. **Unlock** takes the selected out of their groups.
- **Move:** drag the arrows, switch to **Turn Rz** for the ring (it turns about the selection's centre), or type the
  first selected jig's offset; the rest of the selection moves by the same amount. "Take along" also moves the parts
  sitting on a moved jig.
- The state is saved per cell in the browser (shared between tabs) and in `tests/vision_lab/sim_jig_offsets.json`
  (offsets, locks, truth). **The program and the collision check do not follow moved jigs**: vision has to find them.

**From scripts** (needs the `/all` page open, since the page renders the photo; if several tabs are open, the visible
one answers):
```
python tests/vision_lab/sim_camera.py move -400 60 520 180 0 -180   # flange pose; up, over, down via the Listen node
python tests/vision_lab/sim_camera.py pose
python tests/vision_lab/sim_camera.py snap                         # prints the .png and .json paths
```
Server routes: `robot_sim/vision_api.py` (`/vision/snap|request|result|jigs|pose|jog`).

**Vision test additions (2026-11-13):**
- **ArUco markers** on the jigs: the Jigs panel's **Markers** button, or `POST /vision/markers`. Each marker sits on a flat spot found from the meshes, on a tab where the spot is too small.
- A **ChArUco calibration board**: `POST /vision/board {on, pose}`.
- **Position pass:** a photo requested with `xyz` also saves `<stamp>.xyz.f32`, the 3D point and object of every pixel.
- **Scripted jig moves:** `POST /vision/jigs/set`.
- **A headless renderer page,** `/all?renderer` (`tests/vision_lab/renderer.py`). It draws no live view, only photos, and only it answers photo requests sent with `renderer: true`.

Tests and the real-robot tools: [tests/vision_lab/README.md](../vision_lab/README.md).

