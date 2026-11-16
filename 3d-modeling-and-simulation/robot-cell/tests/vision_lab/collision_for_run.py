"""collision.py for v9 and v10 with the jigs (and the parts on them) where a walkthrough run put them.
  python tests/vision_lab/collision_for_run.py results/walkthrough_<stamp>     -> collision_v9.txt, collision_v10.txt
The moves come from the run's last measuring photo (its sim truth: every moved object's T_move). v10 = tests/v10_moves.json
(build it from that run's moves.json first: bench_cell_v10.py <run>/moves.json).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CELL = HERE.parents[1]
run = Path(sys.argv[1]) if Path(sys.argv[1]).is_absolute() else HERE / sys.argv[1]
photo = sorted((run / "real_shots").glob("*.json"))[-1]
shift = []
for n, o in json.loads(photo.read_text())["objects"].items():
    T = np.array(o["T_move"])
    if np.linalg.norm(T[:3, 3]) > 0.01 or abs(T[1, 0]) > 1e-6:
        shift += ["--shift", f"{n}:{T[0, 3]:.3f},{T[1, 3]:.3f},{T[2, 3]:.3f},{np.degrees(np.arctan2(T[1, 0], T[0, 0])):.4f}"]
for v in sys.argv[2:] or ("v9", "v10"):
    r = subprocess.run([sys.executable, str(HERE.parent / "robot_sim" / "collision.py"), str(HERE.parent / f"{v}_moves.json"),
                        "--cell", str(HERE.parent / "robot_sim" / "cell_v9.glb"), "--parts", "--list", *shift],
                       capture_output=True, text=True, cwd=CELL)
    (run / f"collision_{v}.txt").write_text(r.stdout + r.stderr)
    print(v, "\n".join(l for l in r.stdout.splitlines() if "shifted by" not in l)[-1500:] or r.stderr[-800:], flush=True)
