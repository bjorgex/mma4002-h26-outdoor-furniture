"""Split BenchInterfaceV1.STEP into parts for RoboDK (build123d, shared venv).

    python robot_cell/bench_parts.py

Writes robot_cell/benchV1_parts/:
    plank.stl, frame.stl, block.stl   one mesh per part type, in the part's own coordinates
    plank_body.stl, interface_piece.stl   the plank split: the interface piece at the y = -125 end
                                      (the one at +125 is the same piece turned 180 deg about z)
    assembly.json                     every part in the bench: type, role, 4x4 pose (mm) in STEP coordinates
STEP coordinates: planks along y, bench "up" is -z (feet at z = +77.5).
"""
import json
from pathlib import Path

import build123d as bd

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
STEP = HERE.parent / "CAD" / "BenchInterfaceV1.STEP"
OUT = HERE / "benchV1_parts"
TYPES = {"PLank150x25x5": "plank", "Part2^BenchInterfaceV0_wBackRest": "frame", "Part3^BenchInterfaceV0": "block"}


def matrix(loc):
    t = loc.wrapped.Transformation()
    return [[round(t.Value(r, c), 6) for c in range(1, 5)] for r in range(1, 4)] + [[0, 0, 0, 1]]


def main():
    OUT.mkdir(exist_ok=True)
    bench = bd.import_step(str(STEP))
    parts, count, written = [], {}, set()
    for child in bench.children:
        kind = TYPES[child.label]
        count[kind] = count.get(kind, 0) + 1
        name = f"{kind}{count[kind]}"
        z = child.bounding_box().min.Z
        role = {"frame": "side frame", "block": "block"}.get(kind, "seat plank" if z > -1 else "back plank")
        parts.append({"name": name, "type": kind, "role": role, "pose": matrix(child.location)})
        if kind not in written:                              # own coordinates: location reset to identity
            local = child.located(bd.Location())
            bd.export_stl(local, str(OUT / f"{kind}.stl"), tolerance=0.01)
            if kind == "plank":                              # the plank body and its interface piece are separate parts
                body = max(local.solids(), key=lambda s: s.volume)
                piece = min(local.solids(), key=lambda s: s.bounding_box().min.Y)     # the one at the y = -125 end
                assert abs((piece.mirror(bd.Plane.YZ) - piece).volume) < 1, "interface piece not symmetric in x"
                bd.export_stl(body, str(OUT / "plank_body.stl"), tolerance=0.01)
                bd.export_stl(piece, str(OUT / "interface_piece.stl"), tolerance=0.01)   # other end: rotz(180)
            written.add(kind)
    (OUT / "assembly.json").write_text(json.dumps(
        {"source": STEP.name, "units": "mm", "up": "-z", "parts": parts}, indent=1), encoding="utf-8")
    for p in parts:
        print(f"{p['name']:8s} {p['role']:11s} at", [p["pose"][i][3] for i in range(3)])


if __name__ == "__main__":
    main()
