"""Quick STEP viewer for OCP CAD Viewer.

Requires the VS Code Python interpreter to be set to the MSc-MechAuto-NTNU
venv (Ctrl+Shift+P -> Python: Select Interpreter -> Enter interpreter path):
  C:\\Users\\bjoer\\dev\\studyDev\\MSc-MechAuto-NTNU\\.venv\\Scripts\\python.exe

Run (the green ▶ button, or "Run Python File in Terminal") and pick a file
from the list - no editing needed to switch models.
"""
from pathlib import Path

from build123d import import_step
from ocp_vscode import show

BENCH_CAD_DIR = Path(__file__).parent / "3d-modeling-and-simulation" / "bench-cad"

files = sorted(p for p in BENCH_CAD_DIR.iterdir() if p.suffix.lower() == ".step")

if not files:
    raise SystemExit(f"No .STEP files found in {BENCH_CAD_DIR}")

print(f"STEP files in {BENCH_CAD_DIR}:\n")
for i, f in enumerate(files, 1):
    print(f"  {i}. {f.name}")

choice = input(f"\nPick a file [1-{len(files)}]: ").strip()
selected = files[int(choice) - 1]

print(f"Loading {selected.name} ...")
show(import_step(str(selected)))
