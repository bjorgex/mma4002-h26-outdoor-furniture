"""Every model in one file: products on the front row, backrest options behind, then the
screwless plank interfaces (one column each: chair, chair + back, planter).

Writes assemblies/all models.stl and .3mf (3MF keeps the colours) and shows the same
layout in the OCP viewer.  Run:  python all_models.py
"""

# %% Layout
from pathlib import Path
from build123d import *
from furniture import OUT, paint, products
from back_options import options
from interface_options import grid

ROW_GAP = 1000  # mm between the rows (y)


def row(items, y, gap=300):
    """Place {name: Compound} side by side along x at depth y; returns the placed copies."""
    x, placed = 0, {}
    for name, a in items.items():
        bb = a.bounding_box()
        d = Pos(x - bb.min.X, y - bb.min.Y, 0)
        placed[name] = Compound(children=[paint(d * c, c.label) for c in a.children], label=name)
        x += bb.size.X + gap
    return placed


front = row(products, 0)
back = row(options, max(a.bounding_box().max.Y for a in front.values()) + ROW_GAP)
joints = grid(max(a.bounding_box().max.Y for a in back.values()) + ROW_GAP)  # column per interface
everything = {**front, **back, **joints}

# %% Export one file
# 3MF first: after the combined STL export the 3MF mesher stalls on the planter planks
parts = [c for a in everything.values() for c in a.children]
m = Mesher()
for k, c in enumerate(parts):
    if k % 50 == 0:
        print(f"  3MF: part {k} of {len(parts)}", flush=True)
    try:
        m.add_shape(c)
    except RuntimeError:  # a frame with an edge-only contact (lib3mf rejects it)
        print(f"  skipped in 3MF (invalid mesh): {c.label}", flush=True)
m.write(str(OUT / "assemblies" / "all models.3mf"))
# Compound(children=...) re-parents what it is given, so wrap the whole models (they keep
# their own parts); wrapping the parts directly would empty the models before show()
export_stl(Compound(children=list(everything.values())), str(OUT / "assemblies" / "all models.stl"))
print(f"{len(everything)} models, {len(parts)} parts -> assemblies/all models.stl/.3mf")

# %% Show in OCP viewer
from ocp_vscode import Camera, get_port, show

if get_port() is not None:
    show(*everything.values(), names=list(everything), reset_camera=Camera.RESET)
