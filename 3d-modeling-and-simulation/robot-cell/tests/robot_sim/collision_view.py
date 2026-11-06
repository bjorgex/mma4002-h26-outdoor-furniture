"""The 3D view's collision list: collision.py's check_program (parts check on) for a cell's moves file, as JSON
for the "Collisions" panel (collision_layer.js, in /all and /sim/). One source of truth: this only calls
check_program and writes its hits out; no collision logic here.

    python tests/robot_sim/collision_view.py v8            -> tests/robot_sim/collisions/v8.json (if stale)
    python tests/robot_sim/collision_view.py v8 --force    recompute even if up to date
    python tests/robot_sim/collision_view.py all           every cell that has a moves file

Cell names as the 3D view knows them: "cell_v8" or "v8" -> tests/v8_moves.json in robot_sim/cell_v8.glb
(+ cell_layout_v8.json); "cell" or "v4" -> tests/v4_moves.json in cell.glb.
Stale = any input (moves file, cell .glb / layout, robot meshes, collision.py and the kinematics it uses) changed
since the JSON was written. The mock's view server (sim_http.py, /sim/collisions.json?cell=cell_v8) recomputes a
stale one in the background (~1.5 min for v8) and serves the last one meanwhile.
Move numbers are the program's (1-based, moves only, in stage order) = the mock's numbered "move" events (n) when
v4_replay.py plays the file, so the page can tint the colliding objects while that move plays.
"""
import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent
OUT = HERE / "collisions"
STEP = 2.0                                                  # sampling as collision.py's default (mm / deg)
GEOMETRY = "techman"     # link lengths: the 3D view's and bench_cell_v8's IK (collision.py's CLI default is "robodk";
                         # v8 gives the same hits with both, 2026-11-06)
sys.path.insert(0, str(HERE))


def version(cell):
    """'cell_v8' / 'v8' / 'cell' -> 'v8' / 'v8' / 'v4'."""
    c = (cell or "cell").strip()
    if c in ("cell", "v4"):
        return "v4"
    return c[len("cell_"):] if c.startswith("cell_") else c


def files(cell):
    """(moves json, cell glb) for a cell name; ValueError if unknown."""
    v = version(cell)
    if not v.replace("v", "").isdigit():
        raise ValueError(f"unknown cell {cell!r}")
    glb = HERE / ("cell.glb" if v == "v4" else f"cell_{v}.glb")
    return TESTS / f"{v}_moves.json", glb


def inputs(cell):
    moves, glb = files(cell)
    layout = glb.with_name(glb.name.replace("cell", "cell_layout", 1).replace(".glb", ".json"))
    deps = [moves, glb, layout, HERE / "collision.py", HERE / "tm5_links.glb", HERE / "tm5_kin.py",
            HERE / "kin_check.py", HERE / "tmflow_export.py", Path(__file__).resolve()]
    return {p.name: [round(p.stat().st_mtime, 3), p.stat().st_size] for p in deps if p.exists()}


def out_file(cell):
    return OUT / f"{version(cell)}.json"


def cached(cell):
    """The JSON written last for this cell (or None), and whether it is stale."""
    f = out_file(cell)
    if not f.exists():
        return None, True
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return None, True
    return d, d.get("inputs") != inputs(cell)


def compute(cell):
    """Run check_program (parts on) on the cell's moves file and write the JSON. Returns it."""
    from collision import check_program                    # trimesh + fcl: only when needed
    import tm5_kin
    tm5_kin.use(GEOMETRY)
    moves, glb = files(cell)
    if not moves.exists():
        raise FileNotFoundError(f"{moves.name} not found")
    if not glb.exists():
        raise FileNotFoundError(f"{glb.name} not found")
    before = inputs(cell)
    prog = json.loads(moves.read_text(encoding="utf-8"))
    steps = prog["steps"]
    if all("stage" in s for s in steps):                   # v4_replay plays stage by stage: same order here
        steps = sorted(steps, key=lambda s: s["stage"])
    prog = {**prog, "steps": steps}
    mv = [s for s in steps if "move" in s]
    t0 = time.time()
    hits = check_program(prog, str(glb), STEP, parts=True)
    for h in hits:
        s = mv[h["move"] - 1]
        h["stage"] = s.get("stage")
        h["pairs"] = [list(p) for p in h["pairs"]]
        h["objects"] = sorted({n for p in h["pairs"] for n in p})
    d = {"cell": version(cell), "moves_file": f"tests/{moves.name}", "cell_file": f"tests/robot_sim/{glb.name}",
         "n_moves": len(mv), "free": not hits, "hits": hits, "step": STEP, "geometry": GEOMETRY,
         "generated": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": round(time.time() - t0, 1),
         "inputs": before}
    OUT.mkdir(exist_ok=True)
    out_file(cell).write_text(json.dumps(d, indent=1), encoding="utf-8")
    return d


# ---- for the view server (sim_http.py): stale -> recompute in a background thread, one per cell --------------
_RUNNING, _ERR, _LOCK = {}, {}, threading.Lock()


def status(cell):
    """What the page gets: the last JSON (may be stale) + {"state": "ok" | "computing" | "error", ...}."""
    v = version(cell)
    moves, glb = files(cell)                                # ValueError for a bad name
    if not moves.exists() or not glb.exists():
        return {"cell": v, "hits": None, "state": "none",
                "error": f"no {moves.name if not moves.exists() else glb.name}: nothing to check"}
    d, stale = cached(cell)
    with _LOCK:
        failed = _ERR.get(v)
        if stale and v not in _RUNNING and not (failed and failed[0] == inputs(cell)):   # no retry loop on an error
            _ERR.pop(v, None)
            t = threading.Thread(target=_bg, args=(v,), daemon=True)
            _RUNNING[v] = time.time()
            t.start()
        running = v in _RUNNING
        started = _RUNNING.get(v)
        err = _ERR.get(v, (None, None))[1]
    out = dict(d or {"cell": v, "hits": None})
    out.pop("inputs", None)
    out["state"] = "error" if err and not running else "computing" if running else "ok"
    out["stale"] = bool(stale)
    if running:
        out["running_s"] = round(time.time() - started, 1)
    if err:
        out["error"] = err
    return out


def _bg(v):
    """In a child process: ~1.5 min of fcl in the server's own process would hold the GIL and stall the mock's
    joint stream, and tm5_kin.use() is process-wide (the mock's IK)."""
    before = inputs(v)
    try:
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), v, "--force"], capture_output=True,
                           text=True, cwd=str(TESTS.parent), timeout=1800)
        if r.returncode:
            raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip()
                               else f"exit code {r.returncode}")
    except Exception as e:                                  # shown in the panel
        with _LOCK:
            _ERR[v] = (before, f"{type(e).__name__}: {e}")
    finally:
        with _LOCK:
            _RUNNING.pop(v, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cell", help='"v8", "cell_v8", "cell" (v4) or "all"')
    ap.add_argument("--force", action="store_true", help="recompute even if up to date")
    a = ap.parse_args()
    cells = [p.name.split("_")[0] for p in sorted(TESTS.glob("v*_moves.json"))] if a.cell == "all" else [a.cell]
    for c in cells:
        try:
            files(c)
        except ValueError as e:
            raise SystemExit(str(e))
        d, stale = cached(c)
        if a.force or stale:
            print(f"{version(c)}: checking {files(c)[0].name} in {files(c)[1].name} ...", flush=True)
            d = compute(c)
        print(f"{version(c)}: {out_file(c).relative_to(TESTS.parent)}  ({d['generated']}, {d['n_moves']} moves): "
              + ("collision-free" if d["free"] else f"{len(d['hits'])} hits"))
        for h in d["hits"]:
            pairs = [f"{p}/{q}" for p, q in h["pairs"]]
            print(f"    move #{h['move']} ({h['name']}, {h['check']}): {', '.join(pairs[:6])}"
                  f"{' ...' if len(pairs) > 6 else ''}")


if __name__ == "__main__":
    main()
