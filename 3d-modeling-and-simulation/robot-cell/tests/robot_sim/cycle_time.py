"""Cycle time of a robot program without RoboDK: cycle_times.py's estimate, plus one with TMflow's ramps.

    python tests/robot_sim/cycle_time.py bench_tmflow/v7/AssembleBench.zip
    python tests/robot_sim/cycle_time.py tests/v4_moves.json            (move names -> cycle_times.py's phases)
    python tests/robot_sim/cycle_time.py tests/robot_sim/ref/v6_program.json --csv     one CSV row, cycle_times.csv columns

"programmed" = cycle_times.py's model: every Line at its linear speed over the TCP path length, every PTP at
JOINT_SPEED (50 deg/s) over the largest joint travel, plus every gripper wait; no accelerations.
"with ramps" = the same with the point's time-to-top-speed from the TMflow export (Omron_DAM / the v7 export:
PTP PSTTTS 150 ms, Line LSTTTS 300 ms): a trapezoid profile, d/v + t_ramp, or 2 sqrt(d t_ramp / v) if too short to
reach v. Both ignore blending (the post sets BlendValue 1 %) and the controller's own limits.
Phases: by the move names when they are RoboDK's (moves files: cycle_times.PHASES); for a TMflow export (no names)
by the parts of the grips: each grip's phase runs from the gripper event before it to the next grip, so the
approach moves are counted with the phase before (at most a few seconds shift between phases; the total is exact).
"""
import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tm5_kin as K                                         # noqa: E402
from tmflow_export import load_program                      # noqa: E402

JOINT_SPEED = 50                                            # deg/s, cycle_times.JOINT_SPEED
RAMP_PTP, RAMP_LINE = 0.150, 0.300                          # s, PSTTTS / LSTTTS in the exports
PHASES = (("guide to A", ("guide B-A",)), ("planks", ("plank",)), ("guide to B", ("guide A-B",)),
          ("frame 1 + planks", ("sub",)), ("inner half out", ("inner",)), ("outer half out", ("outer",)),
          ("bench to AMR", ("bench",)), ("home", ("Home", "back")))          # cycle_times.PHASES


def phase_of_name(name):
    return next((p for p, words in PHASES if any(name.startswith(w) or f" {w}" in f" {name}" for w in words)), None)


def phase_of_grip(parts, seen):
    p = set(parts)
    if "frame2" in p:
        return "bench to AMR"
    if "frame1" in p:
        return "frame 1 + planks"
    if {"Guide inner", "Guide outer"} <= p:
        return "guide to B" if "planks" in seen else "guide to A"
    if "Guide inner" in p:
        return "inner half out"
    if "Guide outer" in p:
        return "outer half out"
    return "planks" if any(x.startswith("plank") for x in p) else "other"


def trapezoid(d, v, ramp):
    if d <= 0:
        return 0.0
    return d / v + ramp if d >= v * ramp else 2 * math.sqrt(d * ramp / v)


def estimate(program):
    """{phase: (programmed s, with ramps s)}, totals, path length (m)."""
    T = K.pose_to_mat(program.get("tcp", {}).get("pose", [0, 0, 160, 0, 0, 0]))
    js = program.get("joint_speed", JOINT_SPEED)
    named = any(phase_of_name(s.get("name", "")) for s in program["steps"] if "move" in s)
    # phase per step
    labels, cur = [], None
    if not named:
        seen, grip_at = [], {}
        for i, s in enumerate(program["steps"]):
            if s.get("gripper") == "grip":
                grip_at[i] = phase_of_grip(s["parts"], seen)
                seen.append(grip_at[i])
        last = None                                          # last gripper event: (kind, phase)
        for i, s in enumerate(program["steps"]):
            if s.get("gripper") == "grip":
                last = ("grip", grip_at[i])
            elif s.get("gripper") == "release":
                last = ("release", last[1] if last else "home")
            if last and last[0] == "grip":
                labels.append(last[1])
            else:                                            # start, or after a release: the next grip's phase
                labels.append(next((p for k, p in grip_at.items() if k > i), "home"))
    out, prev, dist = {}, None, 0.0
    for i, s in enumerate(program["steps"]):
        ph = (phase_of_name(s.get("name", "")) or cur or "home") if named else labels[i]
        if named and "move" in s:
            cur = ph
        if named and "move" not in s:
            ph = cur or "home"
        a, b = out.get(ph, (0.0, 0.0))
        if "wait_ms" in s:
            w = s["wait_ms"] / 1000
            a, b = a + w, b + w
        elif "do0" in s:                                    # moves file without the waits: bench_cell's gripper()
            w = (500 if s.get("gripper") else 300) / 1000
            a, b = a + w, b + w
        elif "move" in s:
            if prev is not None:
                if s["move"] == "ptp":
                    d = max(abs(u - v) for u, v in zip(prev["joints"], s["joints"]))
                    a, b = a + d / s.get("joint_speed", js), b + trapezoid(d, s.get("joint_speed", js), RAMP_PTP)
                else:
                    p0, p1 = K.matmul(K.pose_to_mat(prev["flange"]), T), K.matmul(K.pose_to_mat(s["flange"]), T)
                    d = math.dist([p0[k][3] for k in range(3)], [p1[k][3] for k in range(3)])
                    dist += d
                    a, b = a + d / s["speed"], b + trapezoid(d, s["speed"], RAMP_LINE)
            prev = s
        out[ph] = (a, b)
    return out, dist / 1000


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program", help="TMflow zip, program json or tests/vN_moves.json")
    ap.add_argument("--csv", action="store_true", help="print a cycle_times.csv-style row")
    a = ap.parse_args()
    K.use("robodk")
    prog = load_program(a.program)
    ph, dist = estimate(prog)
    tot = (sum(v[0] for v in ph.values()), sum(v[1] for v in ph.values()))
    n = sum("move" in s for s in prog["steps"])
    if a.csv:
        print(",".join([f"{tot[0]:.1f}", f"{dist:.2f}"] + [f"{ph[p][0]:.1f}" if p in ph else "" for p, _ in PHASES]))
        return
    print(f"{n} moves, Line path {dist:.2f} m: {tot[0]:.1f} s at the programmed speeds (cycle_times.py's model), "
          f"{tot[1]:.1f} s with TMflow's ramps")
    for p, _ in PHASES:
        if p in ph:
            print(f"    {p:18s} {ph[p][0]:6.1f} s   {ph[p][1]:6.1f} s")
    for p in ph:
        if p not in dict(PHASES):
            print(f"    {p:18s} {ph[p][0]:6.1f} s   {ph[p][1]:6.1f} s")


if __name__ == "__main__":
    main()
