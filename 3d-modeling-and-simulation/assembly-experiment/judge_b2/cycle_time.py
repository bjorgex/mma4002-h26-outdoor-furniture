"""Cycle time of a robot program: programmed speeds, plus an estimate with the controller's ramps.

    python judge/cycle_time.py design/program.json

"programmed" = every Line at its linear speed over the TCP path length, every PTP at its joint speed (program
"joint_speed", 50 deg/s) over the largest joint travel, plus every gripper wait (wait_ms); no accelerations.
"with ramps" = the same with a time-to-top-speed (PTP 150 ms, Line 300 ms): a trapezoid profile, d/v + t_ramp, or
2 sqrt(d t_ramp / v) if too short to reach v. Both ignore blending and the controller's own limits.
Part B2 judge (judge fix proposed by the Part B agent, iter 11/30): a Line's time is the larger of its TCP distance /
Line speed and its tool rotation angle / ROT_SPEED (50 deg/s, the PTP joint speed), so a pure re-orientation Line no
longer costs 0 s.
Phases by the parts of the grips: each grip's phase runs from the gripper event before it to the next grip, so the
approach moves are counted with the phase before (at most a few seconds shift between phases; the total is exact).
"""
import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tm5_kin as K                                         # noqa: E402
from program_io import load_program                         # noqa: E402

JOINT_SPEED = 50                                            # deg/s
RAMP_PTP, RAMP_LINE = 0.150, 0.300                          # s, time to top speed
ROT_SPEED = 50                                              # deg/s, a Line's tool rotation limit (judge B2)


def rot_angle(m0, m1):
    """Angle (deg) of the rotation from the orientation of 4x4 m0 to that of m1."""
    tr = sum(m0[k][i] * m1[k][i] for i in range(3) for k in range(3))     # trace(R0^T R1)
    return math.degrees(math.acos(max(-1.0, min(1.0, (tr - 1) / 2))))
PHASES = ()                                                 # (phase, (move name words, ...)): none, by grips


def phase_of_name(name):
    return next((p for p, words in PHASES if any(name.startswith(w) or f" {w}" in f" {name}" for w in words)), None)


def phase_of_grip(parts, seen):
    p = set(parts)
    if "frame2" in p:
        return "bench out"
    if "frame1" in p:
        return "frame 1 + planks"
    if any("guide" in x.lower() for x in p):
        return "guide"
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
        elif "do0" in s:                                    # a DO step without wait_ms: 500 ms (gripper) / 300 ms
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
                    ang = rot_angle(p0, p1)
                    if ang / ROT_SPEED > d / s["speed"]:           # rotation-limited Line (judge B2)
                        a, b = a + ang / ROT_SPEED, b + trapezoid(ang, ROT_SPEED, RAMP_LINE)
                    else:
                        a, b = a + d / s["speed"], b + trapezoid(d, s["speed"], RAMP_LINE)
            prev = s
        out[ph] = (a, b)
    return out, dist / 1000


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program", help="program json")
    a = ap.parse_args()
    prog = load_program(a.program)
    ph, dist = estimate(prog)
    tot = (sum(v[0] for v in ph.values()), sum(v[1] for v in ph.values()))
    n = sum("move" in s for s in prog["steps"])
    print(f"{n} moves, Line path {dist:.2f} m: {tot[0]:.1f} s at the programmed speeds, {tot[1]:.1f} s with ramps")
    for p in ph:
        print(f"    {p:18s} {ph[p][0]:6.1f} s   {ph[p][1]:6.1f} s")


if __name__ == "__main__":
    main()
