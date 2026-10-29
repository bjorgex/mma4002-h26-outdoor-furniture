"""Quick STEP viewer for OCP CAD Viewer.

Requires the VS Code Python interpreter to be set to the MSc-MechAuto-NTNU
venv (Ctrl+Shift+P -> Python: Select Interpreter -> Enter interpreter path):
  C:\\Users\\bjoer\\dev\\studyDev\\MSc-MechAuto-NTNU\\.venv\\Scripts\\python.exe

Run (the green ▶ button, or "Run Python File in Terminal") and pick a file
from the list - no editing needed to switch models. Parts labelled with
"plank" (the timber slats) are tinted wood; everything else (the bent
flat-bar frame) is tinted steel.
"""
from pathlib import Path

from build123d import Color, import_step
from ocp_vscode import show

BENCH_CAD_DIR = Path(__file__).parent / "3d-modeling-and-simulation" / "bench-cad"

STEEL = Color(0.62, 0.65, 0.68)
WOOD = Color(0.72, 0.52, 0.28)


def paint(shape):
    targets = shape.children or [shape]
    for part in targets:
        label = part.label or shape.label
        part.color = WOOD if "plank" in label.lower() else STEEL


files = sorted(p for p in BENCH_CAD_DIR.iterdir() if p.suffix.lower() == ".step")

if not files:
    raise SystemExit(f"No .STEP files found in {BENCH_CAD_DIR}")

print(f"STEP files in {BENCH_CAD_DIR}:\n")
for i, f in enumerate(files, 1):
    print(f"  {i}. {f.name}")

choice = input(f"\nPick a file [1-{len(files)}]: ").strip()
selected = files[int(choice) - 1]

print(f"Loading {selected.name} ...")
model = import_step(str(selected))
paint(model)
show(model)
