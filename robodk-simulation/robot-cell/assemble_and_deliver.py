"""The whole cycle (station script "Assemble and deliver"): the robot program AssembleBench builds the
bench and sets it down on the AMR, then the AMR drives it 2 m along the table and back (amr_drive.py).

    python robot_cell/assemble_and_deliver.py      also works from outside RoboDK
"""
import time

from robodk import robolink

import amr_drive


def main():
    RDK = robolink.Robolink()
    prog = RDK.Item("AssembleBench", robolink.ITEM_TYPE_PROGRAM)
    if not prog.Valid():
        raise SystemExit("no AssembleBench in the open station")
    t0 = time.time()
    prog.RunProgram()
    time.sleep(1)
    while prog.Busy():
        time.sleep(0.2)
    print(f"AssembleBench done after {time.time() - t0:.0f} s (at the simulation speed)")
    amr_drive.main()


if __name__ == "__main__":
    main()
