
import json
import adsk.core, adsk.fusion

# Data in a file next to this script (the Fusion MCP drops scripts over ~15 kB):
#   parts       [(code, name, step path, library x mm)]
#   assemblies  {name: (offset x, offset y mm, [(instance, code, 4x4 pose mm)])}
DATA = json.load(open("C:/Users/bjoer/devStudiet/MSc-MechAuto-NTNU/H26/MMA4002-DAM/3 Assignments/2 Product Architecture/robot_cell/fusion_data.json", encoding="utf-8"))
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
