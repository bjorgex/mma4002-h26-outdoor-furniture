# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Coursework for **MMA4002 Design for Automated Manufacturing** (NTNU Ålesund), organized as one
folder per assignment (`assignment-1-...` through `assignment-5-...`), plus two shared working
folders used across assignments: the public-facing configurator (`index.html`) and the CAD/CAM/
simulation work (`3d-modeling-and-simulation/`). Most assignment folders just hold the submitted
PDF/brief for that assignment — the active files live in the two shared folders below.

There is no build, lint, or test tooling in this repo (no `package.json`, no `requirements.txt`,
no CI config). The site is a static file you open directly; the Python files are run individually
as scripts.

## `index.html` — the Kaia front page and 3D configurator

One self-contained file (page + three.js configurator + QR code), no build step, no local
dependencies. It pulls two things from the open web at runtime: three.js r128 from cdnjs and
Archivo/IBM Plex Mono from Google Fonts. Everything else, including the QR encoder, is inlined.
There is no model-loading code anywhere in it (no GLTFLoader/STLLoader/etc.) — the entire bench,
every side design, and every plank is procedurally generated three.js geometry, driven by the
`cfg` object and the `SIDES` table.

- Run it: open the file directly, or `python3 -m http.server 8000` to serve it.
- Publish: GitHub Pages, branch `main`, root folder. Then set `SITE_URL` near the bottom of the
  file to the published address — the QR code encodes that.
- The plank-angle sliders sit behind a client-side sign-in gate (see README.md) — a UX convenience,
  not a security boundary; never put anything behind it that needs real protection.
- `index_assignment1_old.html` is an archived snapshot of this file, kept for reference while a
  simplified rebuild (single side design, laser-cut-or-logo-shield plank option instead of the
  current side/angle customization) is in progress.

## `3d-modeling-and-simulation/` — CAD, concept models, and the RoboDK cell

All CAD and simulation work was consolidated here from the previous `3d-models/`,
`assignment-2-product-architectures/cad/`, `.../furniture-concepts/`, and `robodk-simulation/`
locations. `assignment-2-product-architectures/` now holds only that assignment's write-up PDF.

- **`bench-cad/`** — STEP exports of the current bench design. `BenchInterfaceV2.STEP` and
  `BenchWOBackrestV2.STEP` are the latest version.
- **`jig-cad/`** — STEP exports of the assembly jig (`Jig V1/`, including the split/double-sided
  guide variants described in `qa_notes.md`).
- **`concept-models/`** — parametric generation scripts for an earlier, different concept family
  (welded square-tube steel frames + planks: products B1/B2/C1/C2/P1/P2), built with
  [build123d](https://github.com/gumyr/build123d). Each script is run directly, e.g.
  `python furniture.py`, and writes `parts/*.stl` and `assemblies/*.stl`/`*.3mf` (3MF keeps
  colours). `all_models.py` ties the others together and can preview in VS Code via `ocp_vscode`.
  `furniture.py` documents the shared part interface (plank section, pitch, fixing positions)
  that every variant in this folder is built against — read it first when touching these scripts.
- **`robot-cell/`** — the RoboDK cell (Omron TM5-900) that assembles the demonstrator at 1:7.5
  scale. Needs only the `robodk` package (no numpy) since RoboDK's own bundled Python runs it too.
  Primary entry point, `robot_cell.py`:
  ```
  python robot_cell.py build B2   # new station: table, robot, gripper, nests, parts
  python robot_cell.py play B2    # run the assembly, check reach + collisions per step
  ```
  One RoboDK instance (port 20500) is the licensed main station (saves stations, exports to
  TMflow). To build/test in a second, unlicensed RoboDK instance without touching that station:
  `$env:ROBODK_API_PORT=20601; python robot_cell.py build B2` (PowerShell).
  `bench_cell_v3.py`/`bench_cell_v4.py` are prior assembly-sequence versions (see `qa_notes.md` for
  what changed between them); `jig_parts_v4.py` generates the split jig guide. `old six-product
  cell/` is the earlier six-product-family cell this one superseded, kept for its sequences/
  reports. `tests/tmflow_export_test.py` and `tests/listen_pick_place_test.py` exercise the RoboDK
  → TMflow export and the Ethernet-Slave point listener respectively.
- **`simulations-html/`** — exported interactive RoboDK simulations (`.html`, tens of MB each).
  Tracked via Git LFS — see `.gitattributes`.
- **`qa_notes.md`** — a running, dated Q&A log of the jig/interface/RoboDK design decisions
  (fixture design rules, snap-fit interface tradeoffs, cycle times, TMflow export quirks, AMR
  integration). Read this before changing jig or robot-cell logic — it explains *why*, not just
  *what*.

## Collaboration tools

- **Miro** is used for team collaboration and diagramming — e.g. value stream maps.
- **Overleaf** is used for writing the assignment reports.
