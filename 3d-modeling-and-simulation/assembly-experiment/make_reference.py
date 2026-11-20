"""Write judge/reference.json for the Part B judge's rule 8 (bench unchanged + assembled) and the fixed objects.

    python make_reference.py          (shared venv: trimesh) - from the v3 cell (cell_v3.glb + cell_layout_v3.json)
                                      and the bench's assembly.json (benchV1_parts/)

Per bench part: its mesh in its own coordinates (volume, bounds) and "asm", its pose in the bench's (STEP)
coordinates: frame1/2 and plank k as in assembly.json, piece A k = plank k's (the y = -125 end piece in its own
coordinates), piece B k = plank k's turned 180 deg about z (the other end). Fixed: the table and plate bounds.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SIM = HERE.parent / "robot-cell" / "tests" / "robot_sim"
PARTS = HERE.parent / "robot-cell" / "benchV1_parts"
sys.path.insert(0, str(HERE / "judge"))
import collision                                            # noqa: E402

RZ = np.diag([-1.0, -1.0, 1.0, 1.0])


def main(glb=SIM / "cell_v3.glb", layout=SIM / "cell_layout_v3.json", out=HERE / "judge" / "reference.json"):
    cell = collision.load_cell(str(glb))
    lay = {o["name"]: np.array(o["pose"]) for o in json.loads(Path(layout).read_text())["objects"]}
    asm = {p["name"]: np.array(p["pose"]) for p in json.loads((PARTS / "assembly.json").read_text())["parts"]}
    ref = {"source": "the v3 cell and the bench's assembly.json", "parts": {}, "fixed": {}}
    for n in ["frame1", "frame2"] + [f"plank{k}" for k in range(1, 7)] + [f"piece {s}{k}" for s in "AB" for k in range(1, 7)]:
        m = cell[n][1].copy()
        m.apply_transform(np.linalg.inv(lay[n]))
        if n.startswith("piece"):
            A = asm[f"plank{n[-1]}"] @ (RZ if n[6] == "B" else np.eye(4))
        else:
            A = asm[n]
        ref["parts"][n] = {"volume": round(float(abs(m.volume)), 2), "bounds": np.round(m.bounds, 3).tolist(),
                           "asm": np.round(A, 6).tolist()}
    for n in ("Table", "Ground base plate"):
        ref["fixed"][n] = np.round(cell[n][1].bounds, 3).tolist()
    Path(out).write_text(json.dumps(ref, indent=1))
    print(f"{out}: {len(ref['parts'])} bench parts, fixed {list(ref['fixed'])}")


if __name__ == "__main__":
    main()
