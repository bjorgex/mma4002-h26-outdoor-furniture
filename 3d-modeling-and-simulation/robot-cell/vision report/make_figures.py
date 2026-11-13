"""Figures for jig_vision_report.tex from the test results (tests/vision_lab/results/). Run from this folder:
  python make_figures.py
"""
import csv
import shutil
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "tests" / "vision_lab"
MAIN = LAB / "results" / "main_run_seed7"
RACK = LAB / "results" / "rack_pose_seed11"
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
JIGS = ["Base A", "Base B", "Plank rack", "Guide small", "Guide big"]


def jpg(src, name, width=1100):
    img = cv2.imread(str(src))
    h, w = img.shape[:2]
    img = cv2.resize(img, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(FIG / name), img, [cv2.IMWRITE_JPEG_QUALITY, 88])


rows = list(csv.DictReader(open(MAIN / "results.csv", encoding="utf-8")))
cases = [("aruco", "top", "1"), ("aruco", "side", "1"), ("colour", "top", "0"), ("colour", "side", "0"),
         ("features", "top", "0"), ("features", "side", "0")]
labels, med, p90, mx, found = [], [], [], [], []
for m, pose, mk in cases:
    sel = [r for r in rows if r["method"] == m and r["pose"] == pose and r["markers"] == mk and r["disturb"] == "clean"]
    e = np.array([float(r["pos_mm"]) for r in sel if r["found"] == "1"])
    labels.append(f"{m}\n{pose}" + (" (markers)" if mk == "1" else ""))
    med.append(np.median(e)); p90.append(np.percentile(e, 90)); mx.append(e.max())
    found.append(f"{len(e)}/{len(sel)}")
fig, ax = plt.subplots(figsize=(7.2, 3.1))
x = np.arange(len(cases))
ax.bar(x - 0.25, med, 0.25, label="median", color="#2f6fb5")
ax.bar(x, p90, 0.25, label="90 %", color="#7fa7d6")
ax.bar(x + 0.25, mx, 0.25, label="worst", color="#e0322d")
for i, f in enumerate(found):
    ax.text(i, 0.012, f"found {f}", ha="center", va="bottom", fontsize=7, color="#333")
ax.set_yscale("log"); ax.set_ylim(0.01, 500)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
ax.set_ylabel("position error [mm] (log)")
ax.axhline(1, color="#888", lw=0.8, ls="--"); ax.text(len(cases) - 0.5, 1.08, "1 mm", fontsize=7, color="#555", ha="right")
ax.legend(fontsize=8, ncol=3, loc="upper left")
ax.grid(axis="y", which="both", alpha=0.2)
fig.tight_layout(); fig.savefig(FIG / "errors.pdf"); plt.close(fig)

# disturbances (top, markers on): median and worst per method
dist = ["clean", "dark", "noise", "shadow"]
fig, ax = plt.subplots(figsize=(7.2, 2.4))
for k, (m, c) in enumerate([("aruco", "#2f6fb5"), ("colour", "#e09b2d"), ("features", "#3f7d58")]):
    md, wx = [], []
    for d in dist:
        e = [float(r["pos_mm"]) for r in rows if r["method"] == m and r["pose"] == "top" and r["markers"] == "1"
             and r["disturb"] == d and r["found"] == "1"]
        md.append(np.median(e)); wx.append(max(e))
    xs = np.arange(len(dist)) + (k - 1) * 0.27
    ax.bar(xs, md, 0.25, color=c, label=f"{m} median")
    ax.scatter(xs, wx, color=c, marker="v", s=22, zorder=3)
ax.set_yscale("log"); ax.set_ylim(0.02, 30)
ax.set_xticks(range(len(dist))); ax.set_xticklabels(["clean", "darker (x0.55)", "noise + blur", "shadow band"], fontsize=8)
ax.set_ylabel("error [mm] (log)"); ax.legend(fontsize=7, ncol=3, loc="upper left"); ax.grid(axis="y", which="both", alpha=0.2)
ax.text(3.45, 0.025, "triangles = worst", fontsize=7, color="#555", ha="right")
fig.tight_layout(); fig.savefig(FIG / "disturbances.pdf"); plt.close(fig)

jpg(MAIN / "scene0_top_mk_aruco.png", "aruco_top.jpg")
jpg(MAIN / "scene0_side_plain_features.png", "features_side.jpg")
jpg(MAIN / "scene0_top_plain_colour.png", "colour_top.jpg")
jpg(RACK / "scene0_rack_mk_aruco.png", "aruco_rack.jpg")
print("figures:", *sorted(p.name for p in FIG.iterdir()))
