"""Cycle-time log: how long one assembly takes, per assembly-method version of the Bench V1 cell.

    python robot_cell/cycle_times.py        open every version's saved station, measure, log, compare
    (RoboDK's own Python is enough; the main RoboDK)

The time is the robot program "AssembleBench" at its programmed speeds: every step of its path at the
linear speed in force (100 mm/s, 20 mm/s near parts) or, for joint moves, at JOINT_SPEED, plus every
gripper wait; no accelerations. The phases split it by the move names. The AMR's drive is not part of
it. (RoboDK's own estimate, Program -> Update, is unreliable here: 81 s or 212 s for the same v4
program; a real-time RoboDK simulation of v4 took 353 s against 345 s calculated.)
Each version's build logs itself (source "build", with its collision result).
Log: robot_cell/cycle_times.csv, one row per measurement, the phases in seconds.
"""
import csv
import datetime
import re
from pathlib import Path

from robodk import robolink

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
LOG = HERE / "cycle_times.csv"
PROGRAM = "AssembleBench"
JOINT_SPEED = 50          # deg/s, the joint speed the builds program (shown nowhere in the instruction names)
VERSIONS = {        # version: build script, station, assembly method
    "v3": ("bench_cell_v3.py", "Bench V1 cell v3",
           "one double-sided guide B->A->B, frame 1 + planks flipped into frame 2; guide stays trapped, no hand-over"),
    "v4": ("bench_cell_v4.py", "Bench V1 cell v4",
           "v3 with the guide cut in two halves (taken out onto a pad), bench set down on the AMR"),
}
PHASES = (          # (column, words in the move names)
    ("guide to A", ("guide B-A",)), ("planks", ("plank",)), ("guide to B", ("guide A-B",)),
    ("frame 1 + planks", ("sub",)), ("inner half out", ("inner",)), ("outer half out", ("outer",)),
    ("bench to AMR", ("bench",)), ("home", ("Home", "back")))
COLUMNS = (["logged", "version", "source", "instructions", "cycle_s", "path_m", "collisions", "fingertips_out_mm"]
           + [p for p, _ in PHASES] + ["method"])


def phase_of(name):
    return next((p for p, words in PHASES if any(f"({w}" in name for w in words)), "home")


def measure(prog):
    """Instructions, path length, time at the programmed speeds and the time per phase of a program."""
    n, _, dist, ok, msg = prog.Update()
    if ok != 1:
        raise RuntimeError(f"{prog.Name()} does not run: {msg}")
    speed, moves, waits, phase = 100.0, [], {}, "home"
    for name, kind, movetype, *_ in (prog.Instruction(i) for i in range(prog.InstructionCount())):
        if kind == robolink.INS_TYPE_CHANGESPEED:
            speed = float(re.search(r"([\d.]+) mm/s", name).group(1))
        elif kind == robolink.INS_TYPE_PAUSE:                         # a wait belongs to the move before it
            waits[phase] = waits.get(phase, 0.0) + float(re.search(r"([\d.]+) ms", name).group(1)) / 1000
        elif kind == robolink.INS_TYPE_MOVE:
            phase = phase_of(name)
            moves.append((phase, movetype == robolink.MOVE_TYPE_JOINT, speed))
    msg, path, status = prog.InstructionListJoints(5, 5, flags=1)     # rows: joints, ERROR, MM, DEG, MOVE_ID
    phases = dict(waits)
    for c in range(path.size(1)):
        phase, joint, v = moves[int(path[9, c]) - 1]
        phases[phase] = phases.get(phase, 0.0) + (path[8, c] / JOINT_SPEED if joint else path[7, c] / v)
    return {"instructions": int(n), "cycle_s": round(sum(phases.values()), 1), "path_m": round(dist / 1000, 2),
            **{p: round(v, 1) for p, v in phases.items() if v > 0}}


def log(version, prog, source, collisions="", fingertips=""):
    """Measure prog and append a row for this version to the log; returns the row."""
    row = {"logged": datetime.datetime.now().isoformat(timespec="seconds"), "version": version, "source": source,
           "collisions": collisions, "fingertips_out_mm": fingertips, "method": VERSIONS[version][2],
           **measure(prog)}
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow(row)
    return row


def main():
    RDK = robolink.Robolink()
    RDK.COM.settimeout(600)
    for version, (script, station, method) in VERSIONS.items():
        rdk = HERE / f"{station}.rdk"
        if not rdk.exists():
            print(f"{version}: no saved station ({rdk.name}) - run {script} first")
            continue
        st = next((s for s in RDK.getOpenStations() if s.Name() == station), None) or RDK.AddFile(str(rdk))
        RDK.setActiveStation(st)
        row = log(version, RDK.Item(PROGRAM, robolink.ITEM_TYPE_PROGRAM), "measure")
        parts = ", ".join(f"{p} {row[p]:.0f} s" for p, _ in PHASES if p in row)
        print(f"{version}: {row['cycle_s']:.0f} s per bench at the programmed speeds ({row['instructions']} instructions, {row['path_m']} m)  [{parts}]")
    print(f"log: {LOG}")


if __name__ == "__main__":
    main()
