"""Double-sided plank guide: the guide (Part2) of JigAssemDraft1 with the lead-in on both faces, so it
can be flipped from base A (frame 1) onto the mirrored base B (frame 2).

    python robot_cell/jig_guide.py           (shared venv: build123d)

Same outline (40 mm thick) and the same slot sizes as the original: entry 29.8 x 11.25 mm on each
face, tapering over LEAD mm to the straight 25.65 x 5.65 mm section in the middle (original: one
28 mm lead-in, 12 mm straight). Slots sit where the bench's planks are.
Out: JigGuide_DoubleSided.STEP (next to JigAssemDraft1.STEP), coordinates as in JigAssemDraft1.
"""
import json
from pathlib import Path

import build123d as bd
import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
SRC = HERE.parent / "CAD" / "JigAssemDraft1.STEP"
OUT = HERE.parent / "CAD" / "JigGuide_DoubleSided.STEP"
ENTRY = (29.8, 11.25)            # slot width x thickness at a face
STRAIGHT = (25.65, 5.65)         # in the middle (plank 25 x 5)
LEAD = 15.0                      # lead-in depth from each face
Z_TOP, Z_BOT = -60.0, -20.0      # guide faces in JigAssemDraft1 coordinates (entry face of the original: -60)


def plank_slots():
    """Centre (x, y) and width direction of each plank in JigAssemDraft1 coordinates."""
    asm = json.loads((HERE / "benchV1_parts" / "assembly.json").read_text())["parts"]
    out = []
    for p in asm:
        if p["type"] != "plank":
            continue
        P = np.array(p["pose"])
        c = P @ [0, 0, 2.5, 1]                       # centre of the cross-section (plank local z: 0..5)
        u = P[:3, 0]                                  # width direction
        out.append(((c[0] - 2.715, c[2] + 21.877), (u[0], u[2])))   # bench in the jig: x - 2.715, y = z + 21.877
    return out


def rect(centre, u, z, size):
    plane = bd.Plane(origin=(centre[0], centre[1], z), x_dir=(u[0], u[1], 0), z_dir=(0, 0, 1))
    return plane * bd.Rectangle(*size)


def main():
    src = bd.import_step(str(SRC))
    old = [ch for ch in src.children if ch.label.startswith("Part2")][0]
    top_face = max(old.faces().filter_by(bd.Axis.Z), key=lambda f: f.center().Z)     # z = -20
    outline = bd.Face(top_face.outer_wire())
    guide = bd.extrude(outline, amount=Z_BOT - Z_TOP, dir=(0, 0, -1))              # solid -60..-20
    e = 0.5                                                                         # cut a bit past the faces
    for centre, u in plank_slots():
        slot = (bd.loft([rect(centre, u, Z_TOP - e, ENTRY), rect(centre, u, Z_TOP + LEAD, STRAIGHT)])
                + bd.extrude(rect(centre, u, Z_TOP + LEAD, STRAIGHT), amount=(Z_BOT - Z_TOP) - 2 * LEAD)
                + bd.loft([rect(centre, u, Z_BOT - LEAD, STRAIGHT), rect(centre, u, Z_BOT + e, ENTRY)]))
        guide -= slot
    guide.label = "JigGuide_DoubleSided"
    bd.export_step(guide, str(OUT))
    print(f"{OUT.name}: {guide.volume / 1000:.1f} cm3 (original {old.volume / 1000:.1f} cm3), "
          f"{len(plank_slots())} slots, lead-in {LEAD:.0f} mm on both faces")


if __name__ == "__main__":
    main()
