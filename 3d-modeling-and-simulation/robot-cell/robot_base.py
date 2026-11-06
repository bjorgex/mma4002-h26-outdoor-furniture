"""Robot assembly base: a 300 x 300 mm plate with 8 T-slots.

Coordinates as the cell scripts: x away from the robot, y to the left, top of the plate at z = 0. The slots run
along y: standing in front of the robot and looking at it, the slot lines go left-right (perpendicular to the
line of sight). Slot 1 is the one nearest the robot, then every 30 mm.

ASSUMPTIONS (change the constants): slots centred on the plate (first slot 45 mm from the robot-side edge);
T-slot for M8 T-nuts: 9 mm opening, 6 mm neck, 15 x 6 mm head; plate 20 mm thick; slots run through end to end.

    python robot_cell/robot_base.py     -> jig-cad/Robot base/RobotBase_Tslot.STEP (+ .stl)
"""
from pathlib import Path

import build123d as bd
from build123d import Align

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = HERE.parent / "jig-cad" / "Robot base"

SIZE, THICK = 300.0, 20.0          # plate x = y, thickness (mm)
N_SLOTS, PITCH = 8, 30.0           # slots, centre to centre (mm)
FIRST = (SIZE - (N_SLOTS - 1) * PITCH) / 2          # slot 1 centre from the robot-side edge (x = 0): 45 mm
OPEN_W, NECK_H = 9.0, 6.0          # slot opening at the top, depth of the narrow neck
HEAD_W, HEAD_H = 15.0, 6.0         # wide part underneath (where the T-nut sits)


def t_slot(x):
    """One T-slot along y at distance x from the robot-side edge, cut from the top (z = 0) down."""
    neck = bd.Box(OPEN_W, SIZE + 2, NECK_H, align=(Align.CENTER, Align.CENTER, Align.MAX))
    head = bd.Box(HEAD_W, SIZE + 2, HEAD_H, align=(Align.CENTER, Align.CENTER, Align.MAX)).translate((0, 0, -NECK_H))
    return (neck + head).translate((x, SIZE / 2, 0))


def robot_base():
    plate = bd.Box(SIZE, SIZE, THICK, align=(Align.MIN, Align.MIN, Align.MAX))
    xs = [FIRST + i * PITCH for i in range(N_SLOTS)]
    for x in xs:
        plate -= t_slot(x)
    return plate, xs


def main():
    plate, xs = robot_base()
    plate.label, plate.color = "RobotBase_Tslot", bd.Color(0.70, 0.72, 0.75)
    OUT.mkdir(exist_ok=True)
    bd.export_step(plate, str(OUT / "RobotBase_Tslot.STEP"))
    bd.export_stl(plate, str(OUT / "RobotBase_Tslot.stl"))
    b = plate.bounding_box()
    print(f"RobotBase_Tslot {b.size.X:.0f} x {b.size.Y:.0f} x {b.size.Z:.0f} mm, valid {plate.is_valid}, "
          f"volume {plate.volume / 1000:.0f} cm3")
    print("slot centres from the robot-side edge (x):", ", ".join(f"{x:g}" for x in xs))
    print(OUT / "RobotBase_Tslot.STEP")


if __name__ == "__main__":
    main()
