"""Write the Fusion 360 script that builds the demonstrator: one component per unique part
(frame first, then the planks, back post, ornament, rod, planter post), then the six products
C1 C2 B1 B2 P1 P2 as assemblies of occurrences of those components. Run it in Fusion (Scripts and Add-Ins, or over MCP).

    python "robot_cell/old six-product cell/fusion_build.py"   -> fusion_script.py + fusion_data.json next to it
"""
import json

import numpy as np

from cell_parts import PARTS_DIR, HERE, product

ORDER = ["S1L", "S1R", "W2", "W1", "S5L", "S5R", "S6L", "S6R", "S4"]   # no S3 rod on the prototype
NAMES = {"S1L": "S1 side frame L", "S1R": "S1 side frame R", "W2": "W2 plank chair",
         "W1": "W1 plank bench", "S5L": "S5 back post L", "S5R": "S5 back post R",
         "S6L": "S6 ornament L", "S6R": "S6 ornament R", "S3": "S3 stretcher rod",
         "S4": "S4 planter corner post"}
PRODUCTS = {"C1": "C1 chair", "C2": "C2 chair with back", "B1": "B1 bench", "B2": "B2 bench with back",
            "P1": "P1 planter", "P2": "P2 planter long"}
COLUMN_X = {"C1": 0, "C2": 120, "B1": 240, "B2": 490, "P1": 740, "P2": 870}

TEMPLATE = r'''
import json
import adsk.core, adsk.fusion

# Data in a file next to this script (the Fusion MCP drops scripts over ~15 kB):
#   parts       [(code, name, step path, library x mm)]
#   assemblies  {name: (offset x, offset y mm, [(instance, code, 4x4 pose mm)])}
DATA = json.load(open(__DATA__, encoding="utf-8"))
PARTS, ASSEMBLIES = DATA["parts"], DATA["assemblies"]
Y_UP = [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]   # model z-up -> Fusion y-up


def matrix(m, y_up=True):
    """4x4 (mm, model z-up) -> Fusion Matrix3D (cm; y-up only at the top level: a child's
    transform is relative to its parent, which is already turned)."""
    a = [[sum(Y_UP[i][k] * m[k][j] for k in range(4)) for j in range(4)] for i in range(4)] if y_up else m
    flat = []
    for i in range(4):
        for j in range(4):
            flat.append(a[i][j] / 10 if (j == 3 and i < 3) else a[i][j])
    t = adsk.core.Matrix3D.create()
    t.setWithArray(flat)
    return t


def run(context):
    app = adsk.core.Application.get()
    for i in reversed(range(app.documents.count)):        # rebuild from scratch
        if app.documents.item(i).name.startswith("DAM demonstrator"):
            app.documents.item(i).close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "DAM demonstrator 1-7.5"
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    im = app.importManager
    comps = {}
    # Every group component sits at identity and every occurrence gets its full matrix: Fusion
    # applies a parent's transform unreliably to children added later.
    def group(name):
        g = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        g.component.name = name
        return g.component

    src = group("STEP sources")                         # the imports themselves, hidden
    for code, name, path, x in PARTS:                   # frame first, then planks, ...
        before = src.occurrences.count
        im.importToTarget(im.createSTEPImportOptions(path), src)
        occ = src.occurrences.item(before)
        occ.component.name = name
        occ.isLightBulbOn = False
        comps[code] = occ.component
    lib = group("Parts (one of each)")
    for code, name, path, x in PARTS:
        lib.occurrences.addExistingComponent(comps[code], matrix([[1, 0, 0, x], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    for asm_name, (dx, dy, insts) in ASSEMBLIES.items():
        a = group(asm_name)
        for inst, code, m in insts:
            t = [[m[i][j] + ((dx, dy, 0)[i] if j == 3 and i < 3 else 0) for j in range(4)] for i in range(4)]
            a.occurrences.addExistingComponent(comps[code], matrix(t))
    for o in root.allOccurrences:                       # copies inherit the hidden sources' state
        if o.assemblyContext and o.assemblyContext.component.name != "STEP sources":
            o.isLightBulbOn = True
    if design.snapshots.hasPendingSnapshot:             # parametric design: keep the positions
        design.snapshots.add()
    app.activeViewport.fit()
'''


def script():
    parts, x = [], 0
    for code in ORDER:
        parts.append((code, NAMES[code], str(PARTS_DIR / f"{code}.step").replace("\\", "/"), x))
        x += 230 if code == "W1" else 90
    asm = {}
    for code, title in PRODUCTS.items():
        _, p = product(code)
        asm[title] = (COLUMN_X[code], -200, [(n, c, m.tolist()) for n, (c, m) in p.items()])
    data = HERE / "fusion_data.json"
    data.write_text(json.dumps({"parts": parts, "assemblies": asm}), encoding="utf-8")
    return TEMPLATE.replace("__DATA__", json.dumps(str(data).replace("\\", "/")))


if __name__ == "__main__":
    out = HERE / "fusion_script.py"
    out.write_text(script(), encoding="utf-8")
    print("wrote", out)
