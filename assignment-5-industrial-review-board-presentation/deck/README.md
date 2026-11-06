# IRB deck: build and sources

The Industrial Review Board deck (`../MMA4002_IRB_Outdoor_Bench.pptx`) is generated. Edit it in PowerPoint
for small changes. For structural changes, edit `build_deck.js` and rebuild:

```
cd assignment-5-industrial-review-board-presentation/deck
npm install          # pptxgenjs, react-icons, sharp (node_modules is gitignored)
node build_deck.js   # writes ../MMA4002_IRB_Outdoor_Bench.pptx and applies the theme (apply_theme.js)
```

Rebuilding overwrites the .pptx, so edits made in PowerPoint are lost. Each slide has speaker notes
with a suggested speaker.

## Media (`media/`)

| File | What | Made with |
|---|---|---|
| `v8_assembly_sim.mp4` (+ `_poster.jpg`) | the v8 assembly in our own simulator, 2× speed, about 60 s | `capture/shoot.py` (Playwright records `/all`, 3D pane maximised), `capture/tomp4.py` |
| `sim_*.jpg`, `cell_iso.jpg`, `dashboard_v8.jpg` | frames and views of the v8 cell | `capture/shoot.py`, `capture/shoot_cell.py`, cropped by `capture/prep.py` |
| `p_*.jpg` | bench variants from the configurator (`index.html`) | `capture/shoot_cfg2.py` |
| `guide_split.jpg`, `jig_v3_3d.jpg`, `tmflow_demo.jpg` | existing repo images (Jig V3, `robot-cell/tests/`) | `capture/prep.py` |

The capture scripts expect the simulator running (`python tests/tmflow_mock.py serve --sim` in
`robot-cell/`, see `SIM_README.md`) and Playwright with Chrome (`pip install playwright imageio-ffmpeg pillow`).
`capture/render.ps1` exports every slide to PNG through PowerPoint, for checking the layout.

## Where the numbers come from

- Architecture, BOM, frame drawing: `index.html` (`PROFILE`, `SEAT_SLOTS`, `BACK_SLOTS`, `bom()`), Assignment 1 report.
- Interface tolerances and chamfers, jig rules, guide split, cycle-time history: `3d-modeling-and-simulation/qa_notes.md`,
  `robot-cell/cycle_times.csv`.
- v8 stages, 333 s, the remaining collision (#120): `robot-cell/Next steps.md`.
- Lab-verified bridge (100 Hz state, 20/50 mm moves, gripper hand-over): `robot-cell/TM bridge plan.md`.
- AMR over ARCL and the vision base: `robot-cell/AMR delivery plan.md`.
- RoboDK comparison (0.005 mm, same first collision): `robot-cell/tests/robot_sim/OWN_TOOL.md`.
- Takt, cycle and utilisation: Assignment 3 (Lean) report. These are estimates, not measurements.
