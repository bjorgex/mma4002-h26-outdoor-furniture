"""Which jig-vision method works best? Random jig layouts in the sim, photos, every method, errors against the truth.

Needs the mock (python tests/tmflow_mock.py serve --sim). Starts its own headless renderer (renderer.py).
  python tests/vision_lab/jig_vision_test.py [--n 10] [--seed 1]
Writes tests/vision_lab/results/<stamp>/: results.csv (one row per photo x method x jig), summary.md, overlays.

Scenes: Base A, Base B and the plank rack each moved by up to +-30 mm and +-10 deg; the two guide halves sit in
Base B and move with it (as on the real jig), the parts on a base move with it. Photos:
  pose "top"   camera 520 mm above the middle of the jigs, looking straight down (the references are taken here)
  pose "side"  another place and a 30 deg turned wrist (tests that the methods don't depend on the reference pose)
each with markers on and off. Disturbances on the "top" photos (as in a lab): darker (x0.55), noise + blur, a shadow.
"""
import argparse
import csv
import json
import math
import random
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jig_vision as jv  # noqa: E402
import renderer  # noqa: E402
import sim_camera  # noqa: E402

POSES = {"top": [-365, -68, 573, 180, 0, -180], "side": [-300, -20, 560, 180, 0, -150],
         "rack": [-264, -60, 573, 180, 0, -180]}     # "rack": the camera straight above the plank rack
MOVED = ["Base A", "Base B", "Plank rack"]
ON_B = ["Guide small", "Guide big"]                     # sit in Base B, move with it


def post(path, body):
    code, r = sim_camera.http("POST", path, body)
    if code != 200:
        raise RuntimeError(f"{path}: {code} {r}")
    return r


def photo(xyz=False):
    time.sleep(0.6)
    return jv.Photo(sim_camera.snap(timeout=120, renderer=True, xyz=xyz)["json"])


def go(pose):
    post("/vision/jog", {"to": pose, "speed": 100})
    time.sleep(1.0)


def follow(T_b, pivot_b, pivot_g):
    """The guide's offset (about its own pivot) when it moves rigidly with Base B by T_b (about B's pivot)."""
    r = math.radians(T_b["rz"])
    Rm = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
    pb, pg = np.array(pivot_b[:2]), np.array(pivot_g[:2])
    new = Rm @ (pg - pb) + pb + [T_b["x"], T_b["y"]]
    d = new - pg
    return {"x": float(d[0]), "y": float(d[1]), "z": 0, "rz": T_b["rz"]}


def disturb(img, kind, rng):
    if kind == "dark":
        return np.clip(img.astype(np.float32) * 0.55, 0, 255).astype(np.uint8)
    if kind == "noise":
        n = rng.normal(0, 8, img.shape)
        return cv2.GaussianBlur(np.clip(img + n, 0, 255).astype(np.uint8), (5, 5), 1.2)
    if kind == "shadow":                                # a soft dark band across the jigs (an arm or a person)
        h, w = img.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        band = np.exp(-((xx * 0.6 + yy * 0.8 - 0.55 * (w * 0.6 + h * 0.8)) / 120.0) ** 2)
        return np.clip(img * (1 - 0.6 * band[..., None]), 0, 255).astype(np.uint8)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--methods", default="aruco,colour,features")
    ap.add_argument("--poses", default="top,side")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    nrng = np.random.default_rng(a.seed)
    out = HERE / "results" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    renderer.start()

    # references: jigs at CAD, top pose, markers off and on (colour/features learn from the matching one)
    post("/vision/jigs/set", {"reset": True})
    go(POSES["top"])
    refs = {}
    for mk in (False, True):
        post("/vision/markers", {"on": mk})
        refs[mk] = photo(xyz=True)
    model = refs[True].model
    print("references:", refs[False].json.name, refs[True].json.name)

    rows = []
    for i in range(a.n):
        offs = {n: {"x": rng.uniform(-30, 30), "y": rng.uniform(-30, 30), "z": 0, "rz": rng.uniform(-10, 10)} for n in MOVED}
        for g in ON_B:
            offs[g] = follow(offs["Base B"], model["Base B"]["pivot"], model[g]["pivot"])
        post("/vision/jigs/set", {"reset": True, "offsets": offs})
        for pose in a.poses.split(","):
            go(POSES[pose])
            for mk in (False, True):
                post("/vision/markers", {"on": mk})
                ph = photo()
                variants = [("clean", ph)]
                if pose == "top":
                    for kind in ("dark", "noise", "shadow"):
                        v = jv.Photo(ph.json); v.img = disturb(ph.img, kind, nrng); variants.append((kind, v))
                for kind, v in variants:
                    for m, fn in jv.METHODS.items():
                        if m not in a.methods.split(",") or (m == "aruco" and not mk):
                            continue
                        t0 = time.perf_counter()
                        res = fn(v, refs[mk])
                        ms = (time.perf_counter() - t0) * 1000
                        err = jv.errors(v, res)
                        for n in jv.JIGS:
                            e = err[n]
                            rows.append({"scene": i, "pose": pose, "markers": int(mk), "disturb": kind, "method": m, "jig": n,
                                         "found": int(e is not None), "pos_mm": round(e["pos_mm"], 3) if e else "",
                                         "rz_deg": round(e["rz_deg"], 3) if e else "", "ms": round(ms),
                                         "why": res[n].get("why", "")})
                        if i == 0 and kind == "clean":
                            jv.overlay(v, res, f"{m} - {pose}, markers {'on' if mk else 'off'}", out / f"scene0_{pose}_{'mk' if mk else 'plain'}_{m}.png")
        print(f"scene {i + 1}/{a.n} done")

    post("/vision/jigs/set", {"reset": True})
    with open(out / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    summary(rows, out, a, refs)
    print("results:", out)


def summary(rows, out, a, refs):
    def stats(sel):
        f = [r for r in sel if r["found"]]
        if not sel:
            return None
        pos = np.array([r["pos_mm"] for r in f]) if f else np.array([np.nan])
        ang = np.array([r["rz_deg"] for r in f]) if f else np.array([np.nan])
        return {"found": f"{len(f)}/{len(sel)}", "pos_med": np.median(pos), "pos_max": np.max(pos),
                "rz_med": np.median(ang), "rz_max": np.max(ang), "ms": np.median([r["ms"] for r in sel])}

    lines = [f"# Jig vision: which method works best (sim, {a.n} random layouts, seed {a.seed})", "",
             "Error = found position of each jig's pivot vs the truth (mm) and its turn (deg). "
             "found = jig located / tries. Moves: up to +-30 mm, +-10 deg.", ""]
    def table(title, keyf, keys):
        lines.extend([f"## {title}", "", "| method | case | found | pos median mm | pos max mm | rz median deg | rz max deg | time ms |",
                      "|---|---|---|---|---|---|---|---|"])
        for m in ("aruco", "colour", "features"):
            for k in keys:
                s = stats([r for r in rows if r["method"] == m and keyf(r) == k])
                if s:
                    lines.append(f"| {m} | {k} | {s['found']} | {s['pos_med']:.2f} | {s['pos_max']:.2f} | {s['rz_med']:.2f} | {s['rz_max']:.2f} | {s['ms']:.0f} |")
        lines.append("")
    table("Clean photos, by camera pose and markers", lambda r: f"{r['pose']}, markers {'on' if r['markers'] else 'off'}" if r["disturb"] == "clean" else None,
          ["top, markers off", "top, markers on", "side, markers off", "side, markers on"])
    table("Lab-like disturbances (top pose, markers on)", lambda r: r["disturb"] if r["pose"] == "top" and r["markers"] else None,
          ["clean", "dark", "noise", "shadow"])
    table("Per jig (clean, top, markers on)", lambda r: r["jig"] if r["pose"] == "top" and r["markers"] and r["disturb"] == "clean" else None, jv.JIGS)
    why = {}
    for r in rows:
        if not r["found"]:
            why.setdefault((r["method"], r["jig"], r["why"]), 0)
            why[(r["method"], r["jig"], r["why"])] += 1
    if why:
        lines.extend(["## Not found: why", "", "| method | jig | reason | times |", "|---|---|---|---|"])
        lines += [f"| {m} | {j} | {w} | {n} |" for (m, j, w), n in sorted(why.items())]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
