# vision_lab: finding the jigs with a camera

Result and reasons: [vision report/jig_vision_report.pdf](<../../vision report/jig_vision_report.pdf>).
In short: **use ArUco markers** (median 0.14 mm, worst 0.5 mm in the sim; colour and features are worse).
For the plank rack, take a second photo straight above it.

All scripts run from `robot-cell/` with the shared venv (`opencv-contrib-python>=4.10,<5`: OpenCV 5.0's Python has
no `calibrateHandEye`).

## Real robot (next lab session)

**Camera, first choice: the TM5's own camera.** In a TMflow vision job, the *External Detection* step sends the
image over HTTP to `tm_camera.py calib|photo` (port 6189; it logs every request to `tm_camera.log`). Not yet tried
on our robot, so check first that our TMflow version has the step. Then use `tm_camera.py` wherever the table says
`real_capture.py`. Fallback: a **USB webcam** on the tool or above the table (`real_capture.py`).
The scripts only **read** the robot (Modbus 7001 = the current TCP pose). You jog it by hand.

| Step | Command |
|---|---|
| 1. Print (at 100 %, check the 100 mm bar) | `python tests/vision_lab/print_markers.py` → `print/jig_markers_30mm.pdf`, `print/charuco_board.pdf` |
| 2. See what the camera sees | `python tests/vision_lab/real_capture.py live --cam 0` |
| 3. **Jigs off the plate.** Board flat on the empty plate (like TMflow's calibration). Lens: 15 board photos, tilted, all over the image | `real_capture.py calib` ×15, then `calibrate.py intrinsics tests/vision_lab/calib_shots` (RMS < 0.5 px) |
| 4a. Camera on the tool: board still, 10–15 robot poses | new folder: `real_capture.py calib --out tests/vision_lab/he_shots` ×15, then `calibrate.py handeye tests/vision_lab/he_shots` |
| 4b. or a fixed camera: one board photo + 3 touched points | `calibrate.py fixed board.png --O x y z --X x y z --Y x y z` |
| 5. Jigs back in, where the program was taught. Taught layout: overview photo + one above the rack | `real_capture.py photo` ×2, then `real_setup.py real_shots/a.json real_shots/b.json --size 30 --z "Base A=…" …` |
| 6. Measure | `real_capture.py photo` (×2), then `jig_vision.py real_shots/c.json real_shots/d.json --methods aruco --save moves.json` |
| 7. Check | Move a jig 10 mm along a T-slot; step 6 must report about 10 mm. |

Marker ids: 1 Base A, 2 Base B, 3 Plank rack, 4 Guide small, 5 Guide big (DICT_4X4_50). The board is a ChArUco
7×5 grid of 30 mm squares with 22 mm markers, DICT_5X5_100.
Measure each marker's height with the TCP tip (`--z`). A 1 mm height error costs up to 0.4 mm at the image edge.
Use the result like this: `new point = T_move @ taught point` (`jig_vision.move_point`).

## Simulator (testing without the robot)

| File | What it does |
|---|---|
| `sim_camera.py` | `snap` (photo), `pose`, `move` through the mock's Listen node |
| `renderer.py` | A headless browser on `/all?renderer` that renders photos for scripts |
| `jig_vision.py` | The three methods (`aruco`, `colour`, `features`), errors, overlays, several photos combined, `--save` |
| `jig_vision_test.py` | The method comparison: random layouts, 2 poses, markers on/off, disturbances → `results/<stamp>/summary.md` |
| `sim_v10_walkthrough.py` | The whole lab procedure on the sim robot, with a picture per step (calibration mode: empty plate), then program v10 (`bench_cell_v10.py`) from the measured jig moves |
| `calibrate_test.py` | The real-robot procedure in the sim, against known answers → `results/calib_<stamp>/report.json` |
| `calibrate.py`, `real_capture.py`, `tm_camera.py`, `real_setup.py`, `print_markers.py` | The real-robot tools (above) |

The sim side is in `tests/robot_sim/`:
- `vision_layer.js`: the tool camera, the position pass and the calibration board
- `jig_layer.js`: the jig mover and the markers
- `vision_api.py`: the `/vision/*` routes

See `OWN_TOOL.md`.
Generated files are gitignored: `sim_shots/`, `results/*/`, `sim_jig_offsets.json`.

Older lab scripts from 12 Nov (TMflow vision via the GUI/Listen): `jog.py`, `approach.py`, `back_to_cam.py`,
`mb_*.py`, `listen_try.py`, `slow_*.py`.
