# Vision/assembly configuration history

What was tried, what happened, and what to watch for next time - newest first. Written mostly from the
Spotlight Guide (tests/tmflow_all_view.html's "Review" step), one entry per configuration attempt (sim or
real). Not a replacement for Next steps.md (the overall project log) - this is specifically about vision
configuration attempts: jig layouts tried, calibration/measurement results, and anything that went wrong.

Format per entry: date, what was configured (jig layout, scenario run), the result (errors from
jig_vision.py/calibrate.py, or a reach/collision failure), and a one-line takeaway if there is one.

---

## 2026-11-20 — first real-robot vision session (TM wrist camera)
- **Camera route:** TMflow vision job FindPlank = INITIATE → External Detection (setting `laptop_jig`, POST to
  `tm_camera.py` on the laptop :6189) → FINISH. The laptop answers with the OMRON landmark (`landmark.py`) so TMflow
  accepts the job. A photo from ANY pose: vision editor → Save (the job tests itself and sends the image) → Cancel.
- **Calibration:** Techman's own calibration plate (chessboard, 17×12 inner corners, 10 mm) as a `--board tm` mode in
  `calibrate.py`; 13 robot poses → `camera_tm.json`: 0.25 px, hand-eye spread 0.34 mm. Plate surface at Z 0.9.
- **Landmark size:** the outline found is the OUTER black frame = **50 mm** (white square 40). With 40 the heights came
  out ~65 mm too high and the 10 mm test read 7.3 mm; with 50: 9.1 mm for a ~10 mm hand move.
- **Cell vs CAD:** the real Base A/B are swapped vs v9/v10's names (A = start base with the guide); the rack sits
  ~28 mm further in −Y than the CAD. → v11 (`bench_cell_v11_1plank.py`, one-plank test).
- **Discussion (Bjørge):** vision is best used for **calibrating the positions** (where the jigs/rack really are, to
  get the robot roughly there) — the exact grip points are then taught by hand (jog + save). Not for driving every
  grip from the camera.
- **Near miss:** a scripted "straight up" Direct Move ran on TMflow's **Tool** tab instead of Base → the robot went
  579 mm-along-tool = DOWN into the rack; E-stop by Bjørge before the plank broke. `tm_goto.py` now stops if the first
  hold does not bring the robot closer to the target (and Direct Move must be on the Base tab).
