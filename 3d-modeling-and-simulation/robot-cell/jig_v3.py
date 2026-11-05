"""Jig V3 assembly: ihammer18's JigV3 (jig-cad/JigV3.STEP, 2026-11-05) on the Jig V2 plate, in the v7 layout.

JigV3 replaces bases A + B and the guide of Jig V2:
    JigV3.STEP     Part1 = base 180 x 180 x 40, Part2 = the guide (two solids), modelled upside down
                   (base z -40..0, guide z -60..-20) -> turned over about x: base z 0..40, guide z 20..60
    base A         the whole JigV3 (base + guide: the guide starts and ends the cycle on A, as in v7)
    base B         JigV3's base only
    layout         v7 (jig_v2.LAYOUT7): A at (135, 122), B at (135, 322), both turned 180 deg about z;
                   plank rack PlankRack_V2 at (420, 192); plate JigBase_V2 600 x 500 x 6, top at z = 0
ASSUMPTIONS to check: B uses the same base as A (JigV3 has one base, V2 had mirrored A/B); the 180 deg turn keeps
v7's orientation, but which side of JigV3 is the guide's grip pocket is not checked yet.

    python robot_cell/jig_v3.py          -> jig-cad/Jig V3/JigAssembly_V3.STEP (+ .stl)   (repo .venv / build123d)
"""
from pathlib import Path

import build123d as bd

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
JIG = HERE.parent / "jig-cad"
OUT = JIG / "Jig V3"
LAYOUT = {"A": (135.0, 122.0), "B": (135.0, 322.0), "rack": (420.0, 192.0)}   # = jig_v2.LAYOUT7
TURN = 180                                                                    # bases turned about z, as in v7

COLORS = {"plate": (0.80, 0.64, 0.42), "base": (0.35, 0.55, 0.85), "guide": (0.95, 0.65, 0.15),
          "rack": (0.45, 0.47, 0.50)}


def jig_v3_parts():
    """JigV3's base and guide solids, turned right side up (base bottom at z = 0, centred on the origin)."""
    asm = bd.import_step(str(JIG / "JigV3.STEP"))
    base, guide = None, []
    for child in asm.children:
        for s in child.solids():
            s = s.rotate(bd.Axis.X, 180)
            if child.label.startswith("Part1"):
                base = s
            else:
                guide.append(s)
    assert base is not None and len(guide) == 2, "JigV3.STEP: expected Part1 (base) + Part2 (2 guide solids)"
    return base, guide


def place(shape, where):
    return shape.rotate(bd.Axis.Z, TURN).translate((*LAYOUT[where], 0))


def assembly():
    base, guide = jig_v3_parts()
    plate = bd.import_step(str(JIG / "Jig V2" / "JigBase_V2.STEP"))
    rack = bd.import_step(str(JIG / "Jig V2" / "PlankRack_V2.STEP")).translate((*LAYOUT["rack"], 0))
    parts = [("JigBase_V2 plate", plate, "plate"),
             ("JigV3 base A", place(base, "A"), "base"),
             ("JigV3 guide half 1 (on A)", place(guide[0], "A"), "guide"),
             ("JigV3 guide half 2 (on A)", place(guide[1], "A"), "guide"),
             ("JigV3 base B", place(base, "B"), "base"),
             ("PlankRack_V2", rack, "rack")]
    for name, s, kind in parts:
        s.label, s.color = name, bd.Color(*COLORS[kind])
    asm = bd.Compound(children=[s for _, s, _ in parts], label="JigAssembly_V3")
    OUT.mkdir(exist_ok=True)
    bd.export_step(asm, str(OUT / "JigAssembly_V3.STEP"))
    bd.export_stl(asm, str(OUT / "JigAssembly_V3.stl"))
    for name, s, _ in parts:
        b = s.bounding_box()
        print(f"{name:28s} x {b.min.X:6.1f}..{b.max.X:6.1f}  y {b.min.Y:6.1f}..{b.max.Y:6.1f}  z {b.min.Z:5.1f}..{b.max.Z:5.1f}")
    clash = place(base, "A").intersect(place(base, "B"))
    print("bases A/B overlap volume:", round(clash.volume, 1) if clash else 0)
    print(OUT / "JigAssembly_V3.STEP")


if __name__ == "__main__":
    assembly()
