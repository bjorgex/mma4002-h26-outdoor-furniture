import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

HERE = Path(__file__).resolve().parent
layout = json.loads((HERE / "jig_v5_layout.json").read_text())

import rack_marker_plate as rmp
plate, (x0, x1, y0, y1), bolts, marker_c = rmp.build()

fig, ax = plt.subplots(figsize=(7, 7))
ax.add_patch(patches.Rectangle((0, 0), 300, 300, fill=False, edgecolor="black", linewidth=1.5))
for sx in layout["tslots_x"]:
    ax.plot([sx, sx], [0, 300], color="#ccc", linewidth=1, zorder=0)

# rack footprint (approx, from RACK_Y + flange span known from jig_v5_layout rack holes)
rack_y = rmp.RACK_Y
ax.add_patch(patches.Rectangle((30, rack_y[0]), 70, rack_y[1] - rack_y[0], fill=True, facecolor="#9ab", alpha=0.5, edgecolor="#456"))
ax.text(65, sum(rack_y) / 2, "Plank rack\n(existing)", ha="center", va="center", fontsize=9)

for name, key in (("Base A", "base_A"), ("Base B", "base_B")):
    at = layout[key]["at"]
    ax.add_patch(patches.Rectangle((at[0] - 45, at[1] - 60), 90, 120, fill=True, facecolor="#a97", alpha=0.4, edgecolor="#753"))
    ax.text(at[0], at[1], name, ha="center", va="center", fontsize=9)

# new marker plate
ax.add_patch(patches.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True, facecolor="#4a7", alpha=0.7, edgecolor="#163"))
ax.text((x0 + x1) / 2, y0 - 8, "NEW: rack marker plate", ha="center", va="top", fontsize=9, color="#163", fontweight="bold")
for bx, by in bolts:
    ax.add_patch(patches.Circle((bx, by), rmp.CB_D / 2, fill=False, edgecolor="black"))
mc = marker_c
ax.add_patch(patches.Rectangle((mc[0] - rmp.MARKER_ZONE / 2, mc[1] - rmp.MARKER_ZONE / 2), rmp.MARKER_ZONE, rmp.MARKER_ZONE,
                                fill=False, edgecolor="#163", linewidth=1.5, linestyle="--"))
ax.text(mc[0], mc[1], f"{rmp.MARKER:.0f}mm\nmarker", ha="center", va="center", fontsize=8, color="#163")

ax.set_xlim(-10, 310); ax.set_ylim(-10, 310); ax.set_aspect("equal")
ax.set_xlabel("plate x (mm, away from robot)"); ax.set_ylabel("plate y (mm)")
ax.set_title("Rack marker plate - top view (plate coords)")
fig.tight_layout()
fig.savefig(HERE / "rack_marker_plate_top.png", dpi=150)
print(HERE / "rack_marker_plate_top.png")
