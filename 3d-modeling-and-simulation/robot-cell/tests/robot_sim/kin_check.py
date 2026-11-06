"""Reachability / IK check of a robot program with our own TM5-900 kinematics (tm5_kin.py), no RoboDK.

    python tests/robot_sim/kin_check.py bench_tmflow/v7/AssembleBench.zip          a TMflow export (RoboDK's joints in it)
    python tests/robot_sim/kin_check.py tests/v4_moves.json                       a moves file (tests/vN_moves.json)
    python tests/robot_sim/kin_check.py tests/robot_sim/ref/v7_program.json -v    every move, not only the problems
    python tests/robot_sim/kin_check.py X --geometry techman                       Techman's nominal link lengths

Per move (program file format: tmflow_export.py):
    limits     the joints inside tm5_kin.LIMITS, |J1| <= 100 (robot_cell.ik's "shoulder facing the cell")
    fk         FK(joints) against the stored flange pose: does our model put the flange where RoboDK did
    ik         our IK of the flange pose, seeded with the joints of the move before: same joints as RoboDK's?
               (PTP targets: TMflow drives to the stored joints, a different IK answer is only informative)
    line       Line moves followed in small Cartesian steps (TCP straight, orientation slerped) from the joints
               the move starts in: does the arm end in RoboDK's joints (else the line changes posture / the post's
               joints are not the ones the robot will have), does J5 change sign (wrist flip through the
               singularity), how close |J5| gets to 0, the largest joint step per mm of TCP path (near-singular)
Exit code 1 if a move breaks a limit, a line cannot be followed, or a line ends in another posture.
"""
import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tm5_kin as K                                       # noqa: E402
from tmflow_export import load_program, inv, mul          # noqa: E402

J1_MAX = 100                                              # robot_cell.ik / bench_cell_v7.elbow_up
JOINT_TOL = 0.5                                           # deg: "same joints"
STEP_MM, STEP_DEG = 2.0, 1.0                              # line sampling


def slerp_R(Ra, Rb, f):
    """Rotation f of the way from Ra to Rb (3x3 lists)."""
    Rt = [[sum(Ra[k][i] * Rb[k][j] for k in range(3)) for j in range(3)] for i in range(3)]   # Ra^T Rb
    c = max(-1.0, min(1.0, (Rt[0][0] + Rt[1][1] + Rt[2][2] - 1) / 2))
    a = math.acos(c)
    if a < 1e-9:
        return [r[:] for r in Ra]
    if math.pi - a < 1e-6:                                # 180 deg: axis from the diagonal
        ax = [math.sqrt(max(0.0, (Rt[i][i] + 1) / 2)) for i in range(3)]
        i = max(range(3), key=lambda k: ax[k])
        for j in range(3):
            if j != i:
                ax[j] = math.copysign(ax[j], Rt[i][j] + Rt[j][i])
    else:
        ax = [Rt[2][1] - Rt[1][2], Rt[0][2] - Rt[2][0], Rt[1][0] - Rt[0][1]]
    n = math.sqrt(sum(v * v for v in ax))
    x, y, z = (v / n for v in ax)
    t = a * f
    cc, s, v = math.cos(t), math.sin(t), 1 - math.cos(t)
    R = [[x * x * v + cc, x * y * v - z * s, x * z * v + y * s],
         [y * x * v + z * s, y * y * v + cc, y * z * v - x * s],
         [z * x * v - y * s, z * y * v + x * s, z * z * v + cc]]
    return [[sum(Ra[i][k] * R[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def line_poses(fa, fb, T, step_mm=STEP_MM, step_deg=STEP_DEG):
    """Flange poses (4x4) along a Line move from flange fa to fb (4x4): TCP (flange * T) straight, orientation
    slerped. Ends included, start excluded."""
    ta, tb = mul(fa, T), mul(fb, T)
    d = math.dist([ta[i][3] for i in range(3)], [tb[i][3] for i in range(3)])
    Ra, Rb = [r[:3] for r in ta[:3]], [r[:3] for r in tb[:3]]
    ang = math.degrees(math.acos(max(-1.0, min(1.0, (sum(Ra[k][i] * Rb[k][i] for i in range(3) for k in range(3)) - 1) / 2))))
    n = max(2, math.ceil(d / step_mm), math.ceil(ang / step_deg))
    Tinv = inv(T)
    out = []
    for i in range(1, n + 1):
        f = i / n
        R = slerp_R(Ra, Rb, f)
        p = [ta[k][3] + (tb[k][3] - ta[k][3]) * f for k in range(3)]
        tcp = [R[0] + [p[0]], R[1] + [p[1]], R[2] + [p[2]], [0, 0, 0, 1]]
        out.append(mul(tcp, Tinv))
    return out, d, ang


def joint_path(q0, q1, step_deg=STEP_DEG):
    """Joint-space interpolation of a PTP move (synchronous: all joints start and stop together)."""
    n = max(2, math.ceil(max(abs(a - b) for a, b in zip(q0, q1)) / step_deg))
    return [[a + (b - a) * i / n for a, b in zip(q0, q1)] for i in range(1, n + 1)]


def follow_line(q0, poses):
    """Joints along a list of flange poses, each IK seeded with the step before (no extra seeds: a real
    controller follows continuously). Returns (joints list, None) or (partial list, index where it failed)."""
    q, out = list(q0), []
    for i, m in enumerate(poses):
        s = K.ik(K.mat_to_pose(m), q, seeds=False)
        if s is None or max(abs(a - b) for a, b in zip(s, q)) > 20:
            return out, i
        q = s
        out.append(q)
    return out, None


def check(program, verbose=False, report=print):
    """Walk the program as the robot would: after a PTP the arm has the stored joints, after a Line the joints it
    followed the line with (TMflow and RoboDK keep the posture in a Line; the joints stored with a Line target are
    then only RoboDK's IK answer, and may be another posture). Returns (stats, problems, actual joints per move)."""
    T = K.pose_to_mat(program.get("tcp", {}).get("pose", [0, 0, 160, 0, 0, 0]))
    moves = [s for s in program["steps"] if "move" in s]
    stats = {"moves": len(moves), "limit": 0, "fk_mm": 0.0, "fk_deg": 0.0, "ik_differs": 0, "ik_differs_line": 0,
             "ik_max": 0.0, "line_fail": 0, "line_posture": 0, "line_end_max": 0.0, "j5_flip_line": 0,
             "j5_flip_ptp": 0, "min_j5_line": 999.0, "max_deg_per_mm": 0.0, "j1": 0, "limit_path": 0, "line_j6_turn": 0}
    problems, actual = [], []
    prev, qa = None, None                                  # move before, the joints the arm has after it
    for i, s in enumerate(moves):
        q, fl = s["joints"], s["flange"]
        tag = f"#{i + 1:3d} {s['move']:4s} {s.get('name', '')}"
        notes, bad = [], False
        e = K.pose_error(fl, K.fk(q))
        stats["fk_mm"], stats["fk_deg"] = max(stats["fk_mm"], e[0]), max(stats["fk_deg"], e[1])
        reached = q
        if prev is not None:
            mine = K.ik(fl, qa)
            d = 999.0 if mine is None else max(abs(a - b) for a, b in zip(mine, q))
            if d > JOINT_TOL:
                stats["ik_differs"] += 1
                stats["ik_differs_line"] += s["move"] == "line"
                if verbose:
                    notes.append("our IK (nearest the joints before): " + ("no solution" if mine is None else
                                 f"differs by {d:.1f} deg: [{', '.join(f'{v:.1f}' for v in mine)}]"))
            else:
                stats["ik_max"] = max(stats["ik_max"], d)
            if s["move"] == "line":
                poses, dist, ang = line_poses(K.pose_to_mat(K.fk(qa)), K.pose_to_mat(fl), T)
                path, fail = follow_line(qa, poses)
                if fail is not None:
                    stats["line_fail"] += 1
                    bad = True
                    notes.append(f"LINE NOT FOLLOWABLE at {100 * fail / len(poses):.0f} % (IK jump / no solution)")
                    reached = q
                else:
                    reached = path[-1]
                    end = max(abs(a - b) for a, b in zip(reached, q))
                    turn = all(abs(a - b) < JOINT_TOL for a, b in zip(reached[:5], q[:5])) and                         abs(abs(reached[5] - q[5]) - 360) < JOINT_TOL
                    if turn:
                        stats["line_j6_turn"] += 1
                        notes.append(f"stored J6 {q[5]:.1f} is one turn from the {reached[5]:.1f} the line ends in "
                                     f"(same pose; matters only if the controller used the stored joints)")
                    elif end > JOINT_TOL:
                        stats["line_posture"] += 1
                        bad = True
                        notes.append(f"STORED JOINTS ARE ANOTHER POSTURE than the line ends in (max {end:.1f} deg): "
                                     f"stored [{', '.join(f'{v:.1f}' for v in q)}], robot "
                                     f"[{', '.join(f'{v:.1f}' for v in reached)}]")
                    else:
                        stats["line_end_max"] = max(stats["line_end_max"], end)
                    if any(not K.within_limits(p, 0) for p in path):
                        stats["limit_path"] += 1
                        bad = True
                        notes.append("JOINT LIMIT reached along the line")
                    j5 = [qa[4]] + [p[4] for p in path]
                    stats["min_j5_line"] = min(stats["min_j5_line"], min(abs(v) for v in j5))
                    if any(a * b < 0 for a, b in zip(j5, j5[1:])):
                        stats["j5_flip_line"] += 1
                        bad = True
                        notes.append("J5 CHANGES SIGN along the line (wrist singularity)")
                    seg = [qa] + path
                    mm = dist / len(poses)
                    if mm > 0.2:                                    # only for moves that translate
                        rate = max(max(abs(a - b) for a, b in zip(u, v)) / mm for u, v in zip(seg, seg[1:]))
                        stats["max_deg_per_mm"] = max(stats["max_deg_per_mm"], rate)
            elif qa[4] * q[4] < 0:
                stats["j5_flip_ptp"] += 1
                if verbose:
                    notes.append("J5 changes sign (joint move: allowed)")
        if not K.within_limits(reached, 0):
            stats["limit"] += 1
            bad = True
            notes.append("JOINT LIMIT " + ", ".join(f"J{k + 1}={v:.1f}" for k, (v, (lo, hi)) in
                                                   enumerate(zip(reached, K.LIMITS)) if not lo <= v <= hi))
        if abs(reached[0]) > J1_MAX:
            stats["j1"] += 1
            notes.append(f"|J1| {abs(reached[0]):.1f} > {J1_MAX} (shoulder away from the cell)")
        if bad:
            problems.append((tag, notes))
        if verbose or bad or notes:
            report(f"{tag}: " + ("; ".join(notes) if notes else "ok"))
        actual.append(reached)
        prev, qa = s, reached
    return stats, problems, actual


def summary(stats, report=print):
    s = stats
    report(f"{s['moves']} moves: joint limits broken at a target {s['limit']}, along a line {s['limit_path']}, "
           f"|J1| > {J1_MAX}: {s['j1']}")
    report(f"  FK(joints) vs stored flange: max {s['fk_mm']:.3f} mm / {s['fk_deg']:.4f} deg")
    report(f"  our IK (seeded with the move before) != stored joints (> {JOINT_TOL} deg): {s['ik_differs']} moves "
           f"({s['ik_differs_line']} of them Line moves); agreeing moves within {s['ik_max']:.4f} deg")
    report(f"  Line moves: not followable {s['line_fail']}, stored joints another posture {s['line_posture']}, "
           f"stored J6 one turn off {s['line_j6_turn']} "
           f"(others within {s['line_end_max']:.4f} deg), J5 sign change {s['j5_flip_line']}, "
           f"min |J5| {s['min_j5_line']:.1f} deg, max joint step {s['max_deg_per_mm']:.2f} deg per mm of TCP path")
    report(f"  PTP moves with a J5 sign change (allowed in a joint move): {s['j5_flip_ptp']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program", help="TMflow zip, program json or tests/vN_moves.json")
    ap.add_argument("--geometry", choices=list(K.GEOMETRY), default="robodk",
                    help="link lengths: robodk (default, = the station's robot) or techman (nominal URDF)")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    K.use(a.geometry)
    prog = load_program(a.program)
    stats, problems, _ = check(prog, a.verbose)
    summary(stats)
    bad = stats["limit"] + stats["line_fail"] + stats["line_posture"] + stats["limit_path"] + stats["j5_flip_line"]
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
