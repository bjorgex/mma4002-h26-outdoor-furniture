import trimesh
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent

for name in ("guide_1_v5", "guide_2_v5"):
    m = trimesh.load(HERE / "jig_parts" / f"{name}.stl")
    fn = m.face_normals
    up = fn[:, 2] > 0.995                      # near-perfectly horizontal, facing up
    tris = m.triangles[up]
    zs = tris[:, :, 2].flatten()
    print(f"\n=== {name} ===")
    print(f"bbox: x {m.bounds[0][0]:.1f}..{m.bounds[1][0]:.1f}  y {m.bounds[0][1]:.1f}..{m.bounds[1][1]:.1f}"
          f"  z {m.bounds[0][2]:.1f}..{m.bounds[1][2]:.1f}")
    print(f"up-facing triangles: {up.sum()} / {len(fn)}, z range among them: {zs.min():.2f}..{zs.max():.2f}" if up.sum() else "no up-facing triangles found")
    if not up.sum():
        continue
    # histogram of z levels among up-facing faces, rounded to 0.5mm, to find the dominant flat plateau(s)
    zr = np.round(zs * 2) / 2
    vals, counts = np.unique(zr, return_counts=True)
    order = np.argsort(-counts)
    print("top z-levels by up-facing area (z, relative face count):")
    for i in order[:5]:
        print(f"  z={vals[i]:.1f}  n={counts[i]}")

    fig, ax = plt.subplots(figsize=(6, 6))
    m.show
    # rasterize a top-down occupancy of up-facing triangles at the dominant z level
    top_z = vals[order[0]]
    sel = up.copy()
    sel[up] = np.isclose(tris[:, :, 2].mean(axis=1), top_z, atol=1.0)
    flat_tris = m.triangles[sel]
    for t in flat_tris:
        ax.fill(t[:, 0], t[:, 1], color="#4a7", alpha=0.6, edgecolor="none")
    ax.set_title(f"{name}: up-facing area near z={top_z:.1f}mm")
    ax.set_xlabel("local x (mm)"); ax.set_ylabel("local y (mm)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(HERE / f"{name}_topflat.png", dpi=150)
    print("saved", HERE / f"{name}_topflat.png")
