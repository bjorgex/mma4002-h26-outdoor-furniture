"""Forward and inverse kinematics of the Techman (Omron) TM5-900, without RoboDK. Pure Python, no numpy.

    python robot_cell/tests/robot_sim/tm5_kin.py             self-test: FK -> IK -> FK round trips
    python robot_cell/tests/robot_sim/tm5_kin.py --robodk    + compare FK with RoboDK's TM5-900 (port 20500,
                                                              read only: SolveFK, nothing is moved or added)

Geometry: Techman's own nominal model of the TM5-900, tm5-900-nominal.urdf in Techman Robot's ROS driver
(github.com/TechmanRobotInc/tmr_ros1, branch noetic, tm_description/urdf/tm5-900-nominal.urdf):
    joint      origin xyz [mm]            origin rpy [deg]     limit [deg]
    J1         (0, 0, 145.2)              (0, 0, 0)            +-270
    J2         (0, 0, 0)                  (-90, -90, 0)        +-180
    J3         (429, 0, 0)                (0, 0, 0)            +-155
    J4         (411.5, 0, -122.3)         (0, 0, 90)           +-180
    J5         (0, -106, 0)               (90, 0, 0)           +-180
    J6         (0, -113.15, 0)            (90, 0, 0)           +-270
every joint turning about its own z. That is the same layout as a UR arm (shoulder offset 122.3 mm along
the parallel J2/J3/J4 axes, offset wrist), and the zero pose is the arm straight up. The real robot adds a
per-robot calibration (Delta-DH) to this nominal model; TMflow's poses therefore differ by up to a few mm
from these (see the report in __main__ for the numbers against the poses logged on our robot).

Poses are TM's: [x, y, z, rx, ry, rz] in mm and degrees, flange in the robot base frame, R = Rz Ry Rx -
the same as robomath.Pose_2_Techman and Coord_Robot_Flange in the Ethernet Slave stream.
IK: damped least squares from the current joints (the mock's moves are small steps from where the robot
is), and for big jumps from a few extra seeds, the solution nearest the current joints wins.
"""
import math

#           d1     a2     a3     d4     d5     d6   [mm]
GEOMETRY = {"techman": (145.2, 429.0, 411.5, 122.3, 106.0, 113.15),     # tm5-900-nominal.urdf (above)
            "robodk": (145.2, 429.0, 411.0, 122.3, 106.5, 114.15)}      # Omron-TM5-900.robot, measured with
                                                                       # SolveFK: a3, d5, d6 differ by 0.5-1 mm
LIMITS = [(-270, 270), (-180, 180), (-155, 155), (-180, 180), (-180, 180), (-270, 270)]
LIMIT_SLACK = 2.0                 # deg past LIMITS still accepted: our robot logged J3 = -156.0 (real_points.json)


def use(name):
    """Switch the link lengths: "techman" (default) or "robodk" (to match the RoboDK station exactly)."""
    global D1, A2, A3, D4, D5, D6, CHAIN, _FIXED
    D1, A2, A3, D4, D5, D6 = GEOMETRY[name]
    CHAIN = [((0, 0, D1), (0, 0, 0)), ((0, 0, 0), (-90, -90, 0)), ((A2, 0, 0), (0, 0, 0)),
             ((A3, 0, -D4), (0, 0, 90)), ((0, -D5, 0), (90, 0, 0)), ((0, -D6, 0), (90, 0, 0))]
    _FIXED = [pose_to_mat(list(xyz) + list(rpy)) for xyz, rpy in CHAIN]


# --- 4x4 matrices as lists of rows
def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def rot(a, b, c):
    """R = Rz(c) Ry(b) Rx(a), degrees (TM pose angles; also URDF rpy = (a, b, c))."""
    a, b, c = math.radians(a), math.radians(b), math.radians(c)
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    return [[cc * cb, cc * sb * sa - sc * ca, cc * sb * ca + sc * sa],
            [sc * cb, sc * sb * sa + cc * ca, sc * sb * ca - cc * sa],
            [-sb, cb * sa, cb * ca]]


def pose_to_mat(p):
    r = rot(*p[3:6])
    return [r[0] + [p[0]], r[1] + [p[1]], r[2] + [p[2]], [0, 0, 0, 1]]


def mat_to_pose(m):
    """-> [x, y, z, rx, ry, rz] with R = Rz Ry Rx (ry in [-90, 90])."""
    sy = math.hypot(m[0][0], m[1][0])
    if sy > 1e-9:
        rx, ry, rz = math.atan2(m[2][1], m[2][2]), math.atan2(-m[2][0], sy), math.atan2(m[1][0], m[0][0])
    else:                                                 # gimbal lock: put it all in rx
        rx, ry, rz = math.atan2(-m[1][2], m[1][1]), math.atan2(-m[2][0], sy), 0.0
    return [m[0][3], m[1][3], m[2][3]] + [math.degrees(v) for v in (rx, ry, rz)]


use("techman")


def frames(joints):
    """Joint frames J1..J6 (J6 = flange) in the base frame, for the given joints [deg]."""
    out, t = [], [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    for fixed, q in zip(_FIXED, joints):
        c, s = math.cos(math.radians(q)), math.sin(math.radians(q))
        t = matmul(matmul(t, fixed), [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        out.append(t)
    return out


def fk_mat(joints):
    return frames(joints)[-1]


def fk(joints):
    """Flange pose [x, y, z, rx, ry, rz] (TM convention) for joints [deg]."""
    return mat_to_pose(fk_mat(joints))


def within_limits(joints, margin=-LIMIT_SLACK):
    return all(lo + margin <= q <= hi - margin for q, (lo, hi) in zip(joints, LIMITS))


def reachable(pose):
    """Quick reach check: the wrist centre (J5 axis point) within the J2/J3 arm's annulus."""
    m = pose_to_mat(pose)
    wc = [m[i][3] - D6 * m[i][2] for i in range(3)]       # flange z back to the J5 axis
    r = math.sqrt(max(0.0, wc[0] ** 2 + wc[1] ** 2 - D4 ** 2))
    d = math.hypot(r, wc[2] - D1)
    return abs(A2 - A3) - D5 <= d <= A2 + A3 + D5


def _err(target, m):
    """6-vector: position error [mm] and rotation error [rad] (axis * angle), target vs current."""
    dp = [target[i][3] - m[i][3] for i in range(3)]
    # R_err = R_t R_c^T, rotation vector from its skew part
    r = [[sum(target[i][k] * m[j][k] for k in range(3)) for j in range(3)] for i in range(3)]
    v = [r[2][1] - r[1][2], r[0][2] - r[2][0], r[1][0] - r[0][1]]
    s, c = math.sqrt(sum(x * x for x in v)) / 2, (r[0][0] + r[1][1] + r[2][2] - 1) / 2
    ang = math.atan2(s, c)
    if s < 1e-9:
        if c > 0:
            return dp + [0.0, 0.0, 0.0]
        # 180 deg: axis from the diagonal
        ax = [math.sqrt(max(0.0, (r[i][i] + 1) / 2)) for i in range(3)]
        return dp + [math.pi * a for a in ax]
    return dp + [x / (2 * s) * ang for x in v]


def _jacobian(fr):
    """Geometric Jacobian (6x6, rows vx vy vz wx wy wz) from the joint frames."""
    p = [fr[-1][i][3] for i in range(3)]
    cols = []
    for f in fr:
        z, o = [f[i][2] for i in range(3)], [f[i][3] for i in range(3)]
        d = [p[i] - o[i] for i in range(3)]
        cols.append([z[1] * d[2] - z[2] * d[1], z[2] * d[0] - z[0] * d[2], z[0] * d[1] - z[1] * d[0]] + z)
    return [[cols[j][i] for j in range(6)] for i in range(6)]


def _solve(a, b):
    """Gaussian elimination with partial pivoting, a (n x n) x = b."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n + 1):
                m[r][k] -= f * m[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][k] * x[k] for k in range(r + 1, n))) / m[r][r]
    return x


def _dls(target, seed, iters=100, tol_mm=1e-3, tol_rad=1e-6):
    q = list(seed)
    W = 300.0                                             # mm per rad: weighs rotation against position
    for _ in range(iters):
        fr = frames(q)
        e = _err(target, fr[-1])
        if math.sqrt(sum(x * x for x in e[:3])) < tol_mm and math.sqrt(sum(x * x for x in e[3:])) < tol_rad:
            return q
        J = _jacobian(fr)
        J = J[:3] + [[W * x for x in row] for row in J[3:]]
        e = e[:3] + [W * x for x in e[3:]]
        # dq = J^T (J J^T + l^2 I)^-1 e, damping grows near singularities via the error size
        lam2 = 1.0 + 1e-4 * sum(x * x for x in e)
        JJt = [[sum(J[i][k] * J[j][k] for k in range(6)) + (lam2 if i == j else 0) for j in range(6)] for i in range(6)]
        y = _solve(JJt, e)
        dq = [sum(J[k][i] * y[k] for k in range(6)) for i in range(6)]
        step = max(abs(x) for x in dq)
        if step > 0.3:                                    # at most ~17 deg per iteration
            dq = [x * 0.3 / step for x in dq]
        q = [a + math.degrees(b) for a, b in zip(q, dq)]
    return None


def _wrap_near(q, near):
    """Each joint +-360 deg to the turn nearest the reference, if that stays inside the limits."""
    out = []
    for a, b, (lo, hi) in zip(q, near, LIMITS):
        best = min((a + k * 360 for k in (-1, 0, 1) if lo - LIMIT_SLACK <= a + k * 360 <= hi + LIMIT_SLACK), key=lambda x: abs(x - b),
                   default=a)
        out.append(best)
    return out


def ik(pose, near, seeds=True):
    """Joints [deg] that put the flange at pose (TM convention), nearest to `near`; None if out of reach
    or outside the joint limits. `near` is also the first seed (fast for small steps)."""
    if not reachable(pose):
        return None
    target = pose_to_mat(pose)
    found = []
    q = _dls(target, near)
    if q is not None:
        q = _wrap_near(q, near)
        if within_limits(q):
            if max(abs(a - b) for a, b in zip(q, near)) < 30 or not seeds:
                return q
            found.append(q)
    if seeds:                                             # a big jump: try the other branches too
        for s in ([near[0], near[1], near[2], near[3], -near[4], near[5]],
                  [near[0], -near[1], -near[2], -near[3], near[4], near[5]],
                  [0, 0, 90, 0, 90, 0], [0, 0, -90, 0, -90, 0], [0, 30, -120, 0, -90, 0], [0, -30, 120, 0, 90, 0],
                  [90, 0, 90, 0, 90, 0], [-90, 0, 90, 0, 90, 0]):
            q = _dls(target, s)
            if q is not None:
                q = _wrap_near(q, near)
                if within_limits(q):
                    found.append(q)
    if not found:
        return None
    return min(found, key=lambda q: sum((a - b) ** 2 for a, b in zip(q, near)))


class TM5Kin:
    """Drop-in for tmflow_mock.RoboDK: ik(flange, near), fk(joints), show(joints) (show is a no-op;
    the browser view reads the joints from the mock's SSE stream)."""

    def ik(self, flange, near):
        return ik(flange, near)

    def fk(self, joints):
        return fk(joints)

    def show(self, joints):
        pass


def pose_error(p, q):
    """(position error mm, orientation error deg) between two TM poses."""
    e = _err(pose_to_mat(p), pose_to_mat(q))
    return math.sqrt(sum(x * x for x in e[:3])), math.degrees(math.sqrt(sum(x * x for x in e[3:])))


if __name__ == "__main__":
    import json
    import random
    import sys
    import time
    from pathlib import Path

    CELL = Path(__file__).resolve().parents[2]
    random.seed(4002)
    sets = [[0] * 6, [-4.5, 24.7, -142.5, 26.3, -87.2, 18.3], [-25.5, 5.5, -130.2, 33.2, -92.8, 13.4],
            [29.3, -39.9, 110.0, 19.9, 90.0, 119.3]]
    sets += [[round(random.uniform(lo * 0.8, hi * 0.8), 2) for lo, hi in LIMITS] for _ in range(16)]

    print("IK round trips (FK -> IK from a seed 5-40 deg away -> FK):")
    worst, t0, fails = (0, 0), time.time(), 0
    for q in sets:
        p = fk(q)
        near = [a + random.uniform(-40, 40) for a in q]
        s = ik(p, near)
        if s is None:
            fails += 1
            continue
        e = pose_error(p, fk(s))
        worst = (max(worst[0], e[0]), max(worst[1], e[1]))
    print(f"  {len(sets) - fails}/{len(sets)} solved, worst {worst[0]:.2e} mm / {worst[1]:.2e} deg, "
          f"{(time.time() - t0) / len(sets) * 1000:.0f} ms each")

    real = json.loads((CELL / "real_points.json").read_text())
    pts = json.loads((CELL / "tests" / "listen_test_points.json").read_text())
    real = [(r["label"], r["joints"], r["flange"]) for r in real] + [(k, v["joints"], v["flange"]) for k, v in pts.items()]
    robot = None
    if "--robodk" in sys.argv:
        from robodk import robolink, robomath
        robot = robolink.Robolink().ItemList(robolink.ITEM_TYPE_ROBOT)[0]
        ref = []
        for q in sets + [r[1] for r in real]:
            try:
                ref.append((q, robomath.Pose_2_Techman(robot.SolveFK(q))))
            except Exception:                             # RoboDK refuses joints past its limits (J3 -156)
                pass
    for geo in GEOMETRY:
        use(geo)
        print(f"geometry '{geo}' {GEOMETRY[geo]}:")
        e = [pose_error(f, fk(j)) for _, j, f in real]
        print(f"  FK vs the {len(real)} poses logged on our TM5-900 (real_points.json, listen_test_points.json): "
              f"max {max(x[0] for x in e):.2f} mm, {max(x[1] for x in e):.2f} deg")
        if robot:
            e = [pose_error(p, fk(q)) for q, p in ref]
            print(f"  FK vs RoboDK '{robot.Name()}' SolveFK, {len(ref)} joint sets: "
                  f"max {max(x[0] for x in e):.4f} mm, {max(x[1] for x in e):.5f} deg")
            e, n = [], 0
            for q, p in ref:                              # our IK, checked with RoboDK's FK
                s_ = ik(p, [a + random.uniform(-20, 20) for a in q])
                if s_ is not None:
                    n += 1
                    e.append(pose_error(p, robomath.Pose_2_Techman(robot.SolveFK(s_))))
            print(f"  our IK -> RoboDK FK, {n}/{len(ref)} solved: "
                  f"max {max(x[0] for x in e):.4f} mm, {max(x[1] for x in e):.5f} deg")
    use("techman")
