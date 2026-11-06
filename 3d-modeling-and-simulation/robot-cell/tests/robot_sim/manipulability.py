"""Manipulability (velocity ellipsoids) of the TM5-900 with our gripper, for the bench cell.

Theory: Modern Robotics 5.4 (pp. 195-197). For a Jacobian J (here the BODY Jacobian J_b of the TCP, MR row
order [omega; v]) A = J J^T; the ellipsoid  qdot^T ... : twists V = J qdot with |qdot| = 1 fill
V^T A^-1 V <= 1, principal axes = eigenvectors of A, semi-axes sqrt(lambda_i). Measures:
    mu1 = sqrt(lmax/lmin)  isotropy (1 = round, -> inf at a singularity)
    mu2 = lmax/lmin        condition number of A (= mu1^2)
    mu3 = sqrt(det A)      volume (-> 0 at a singularity)
J_w = top 3 rows (angular), J_v = bottom 3 rows (linear velocity of the TCP, in the TCP frame).
"full" = the whole 6x6 J_b with v divided by L_CHAR (rad/s and m/s mixed: needs a length scale).

    python tests/robot_sim/manipulability.py map     [--z 0,50,100,150] [--tool down|best|both] [--cell v7|v8]
                                                     [--measure mu1|mu3] [--jac vfix|v|w|full] [--step 20]
    (vfix = linear TCP velocity with the orientation held, A_fix = (C^T C)^-1, C = last 3 columns of J^-1: what a
     straight tool-down move sees; J_v alone hardly reacts to the TM5's singularities, see `sanity`)
    python tests/robot_sim/manipulability.py slice   vertical slices through the base axis (all tool directions)
    python tests/robot_sim/manipulability.py targets [--moves tests/v5_moves.json] [--thr 3]
    python tests/robot_sim/manipulability.py sanity  Jacobian check (analytic vs finite differences) + singular poses
    python tests/robot_sim/manipulability.py all     everything + manipulability/manip_data.json for the viewer
                                                     (manipulability/manipulability.html) + iso-surface GLB/STL

Kinematics: tm5_kin.py (Techman nominal URDF). TCP = flange * transl(0, 0, tip_mm) (bench_layout.json, 160 mm,
the same tool the bench_cell_v*.py scripts add). Joint limits from tm5_kin.LIMITS.

Two facts the whole analysis leans on:
  * the TCP lies on the J6 axis, so turning the tool about its own z only changes theta6: mu does not depend on
    the yaw of the gripper (J6 has +-270 deg, so the yaw never limits reach). A tool orientation = a direction.
  * the arm is symmetric about the J1 axis (J1 +-270 deg), so for one IK branch mu depends only on the
    horizontal distance rho from the J1 axis and on z. The slices (rho, z) are therefore computed with IK once
    (batched numpy IK from many seeds; kept on the program's IK branch = the signs of the three factors of
    det J, as in v5_moves.json's Home), and the horizontal maps are
    read off them; `map` spot-checks this with direct IK at random grid points.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
CELL = HERE.parents[1]
OUT = HERE / "manipulability"
sys.path.insert(0, str(HERE))
import tm5_kin as K                                                  # noqa: E402

LAYOUT = json.loads((CELL / "bench_layout.json").read_text(encoding="utf-8"))
TIP = float(LAYOUT["tip_mm"])
L_CHAR = 0.5                         # m: length scale for the 6x6 measure (v / L next to omega)
JACS = ("v", "vfix", "w", "full")    # J_v (MR 5.4), J_v with orientation held, J_w, 6x6
HOME = [-14.0892, 2.9168, -80.0986, -12.7472, -90.0099, 75.8867]    # v5_moves.json "Home" (the program's branch)
SLICE_AZ = 180.0                     # deg: slice plane azimuth in the robot base frame (-x: towards the cell)
S_RANGE, Z_RANGE = (-1000, 1000), (-350, 1150)                     # mm, robot base frame
STEP = int(__import__("os").environ.get("MANIP_STEP", "20"))       # grid step [mm] (--step; env for the workers)
FULL_THR = 15.0                      # 6x6 mu1 (L = 0.5 m): good poses sit at 5-8 -> > 15 = near-singular
MU1_THR = 3.0                        # flag: semi-axis ratio > 3 (mu2 > 9) counts as near-singular
LIMIT_WARN = 10.0                    # deg from a joint limit
SING = {"elbow": math.sin(math.radians(8)), "wrist": math.sin(math.radians(30)), "shoulder": 100.0}
# contour levels: elbow |sin th3| < sin 8 deg, wrist |sin th5| < sin 30 deg (approaching), shoulder |d_sh| < 100 mm

# tool z directions, in (out, tangential, up) of the point's own vertical plane; "best" = min over all
ORIENT = {"down": (0, 0, -1), "down45out": (1, 0, -1), "down45in": (-1, 0, -1), "out": (1, 0, 0),
          "in": (-1, 0, 0), "up45out": (1, 0, 1), "up": (0, 0, 1), "side": (0, 1, 0)}


# ------------------------------------------------------------------ kinematics
def adjoint(T):
    R, p = T[:3, :3], T[:3, 3]
    ph = np.array([[0, -p[2], p[1]], [p[2], 0, -p[0]], [-p[1], p[0], 0]])
    return np.block([[R, np.zeros((3, 3))], [ph @ R, R]])


def tcp_frames(q):
    fr = [np.array(f, float) for f in K.frames(q)]
    T = fr[-1].copy()
    T[:3, 3] += TIP * T[:3, 2]
    return fr, T


def jacobians(q):
    """(J_s, J_b, T_tcp): space and body Jacobians of the TCP, MR order [omega; v], v in mm/rad."""
    fr, T = tcp_frames(q)
    Js = np.zeros((6, 6))
    for i, f in enumerate(fr):            # joint i turns about z of its frame (frame i includes its rotation)
        w, o = f[:3, 2], f[:3, 3]
        Js[:, i] = np.r_[w, -np.cross(w, o)]
    Jb = adjoint(np.linalg.inv(T)) @ Js
    return Js, Jb, T


def jb_numeric(q, h=1e-6):
    """Body Jacobian by finite differences: column i = vee(T^-1 dT/dtheta_i)."""
    Ti = np.linalg.inv(tcp_frames(q)[1])
    cols = []
    for i in range(6):
        qp, qm = list(q), list(q)
        qp[i] += math.degrees(h)
        qm[i] -= math.degrees(h)
        S = Ti @ (tcp_frames(qp)[1] - tcp_frames(qm)[1]) / (2 * h)
        cols.append([S[2, 1], S[0, 2], S[1, 0], S[0, 3], S[1, 3], S[2, 3]])
    return np.array(cols).T


def measures(J):
    """mu1, mu2, mu3 and (eigvals, eigvecs) of A = J J^T."""
    A = J @ J.T
    lam, vec = np.linalg.eigh(A)
    lam = np.clip(lam, 0, None)
    lmin, lmax = lam[0], lam[-1]
    mu2 = lmax / lmin if lmin > 1e-18 else np.inf
    return math.sqrt(mu2), mu2, math.sqrt(max(np.prod(lam), 0.0)), lam, vec


def analyse(q):
    """All measures for joints q [deg]. J_v in m/s per rad/s, J_w rad/s per rad/s."""
    _, Jb, T = jacobians(q)
    Jw, Jv = Jb[:3], Jb[3:] / 1000.0
    full = np.vstack([Jw, Jv / L_CHAR])
    out = {"T": T}
    for name, J in (("v", Jv), ("w", Jw), ("full", full)):
        m1, m2, m3, lam, vec = measures(J)
        out[name] = (m1, m2, m3)
        if name == "v":
            out["A_v_base"] = T[:3, :3] @ (Jv @ Jv.T) @ T[:3, :3].T     # ellipsoid matrix in the base frame
    # vfix: linear TCP velocities with the orientation HELD (omega = 0, a straight tool-down move):
    # qdot = J^-1 [0; v] = C v, |qdot| <= 1  ->  v^T (C^T C) v <= 1, i.e. A_fix = (C^T C)^-1
    C = np.linalg.pinv(np.vstack([Jw, Jv]), rcond=1e-12)[:, 3:]
    lam = np.clip(np.linalg.eigvalsh(C.T @ C), 1e-30, None)            # eigenvalues of A_fix^-1
    out["vfix"] = (math.sqrt(lam[-1] / lam[0]), lam[-1] / lam[0], 1 / math.sqrt(np.prod(lam)))
    out["A_fix_base"] = T[:3, :3] @ np.linalg.inv(C.T @ C) @ T[:3, :3].T
    s3, s5 = math.sin(math.radians(q[2])), math.sin(math.radians(q[4]))
    Jg = np.vstack([Jb[3:], Jb[:3]])
    # det J = A2 A3 sin(th3) sin(th5) d_sh (checked numerically): d_sh = distance of the J5 origin from the
    # plane through the J1 axis containing the J2 axis direction -> shoulder singularity when d_sh = 0
    d_sh = np.linalg.det(Jb) / (K.A2 * K.A3 * s3 * s5) if abs(s3 * s5) > 1e-9 else np.nan
    margin = min(min(qi - lo, hi - qi) for qi, (lo, hi) in zip(q, K.LIMITS))
    out.update(s3=s3, s5=s5, d_sh=abs(d_sh), margin=margin, det=abs(np.linalg.det(Jg)))
    return out


def tool_matrix(p, zdir):
    """4x4 TCP pose at p (mm, base frame) with the tool z along zdir (any yaw: mu does not depend on it)."""
    z = np.asarray(zdir, float)
    z /= np.linalg.norm(z)
    a = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(a, z)
    x /= np.linalg.norm(x)
    T = np.eye(4)
    T[:3, :3] = np.c_[x, np.cross(z, x), z]
    T[:3, 3] = p
    return T


def flange_pose(T_tcp):
    F = T_tcp.copy()
    F[:3, 3] -= TIP * F[:3, 2]
    return K.mat_to_pose(F.tolist())


def local_dir(name, s, az_deg=SLICE_AZ):
    """Orientation name -> tool z in the base frame at signed slice coordinate s (out = away from the J1 axis)."""
    o, t, u = ORIENT[name]
    az = math.radians(az_deg)
    e_s = np.array([math.cos(az), math.sin(az), 0.0]) * (1 if s >= 0 else -1)
    e_t = np.array([-math.sin(az), math.cos(az), 0.0])
    return o * e_s + t * e_t + np.array([0, 0, u])


# ------------------------------------------------------------------ slices (batched numpy IK)
_FIXED_NP = np.array(K._FIXED, float)                                # the 6 fixed link transforms of tm5_kin


def fk_batch(Q):
    """Q (N, 6) rad -> joint frames (N, 6, 4, 4) and TCP (N, 4, 4), same chain as tm5_kin.frames."""
    n = len(Q)
    T = np.broadcast_to(np.eye(4), (n, 4, 4)).copy()
    fr = np.empty((n, 6, 4, 4))
    for i in range(6):
        c, s = np.cos(Q[:, i]), np.sin(Q[:, i])
        Rz = np.zeros((n, 4, 4))
        Rz[:, 0, 0], Rz[:, 0, 1], Rz[:, 1, 0], Rz[:, 1, 1], Rz[:, 2, 2], Rz[:, 3, 3] = c, -s, s, c, 1, 1
        T = T @ _FIXED_NP[i] @ Rz
        fr[:, i] = T
    tcp = T.copy()
    tcp[:, :3, 3] += TIP * T[:, :3, 2]
    return fr, tcp


def jac_batch(fr, tcp):
    """Space-frame geometric Jacobian at the TCP point, rows [v; w] (N, 6, 6), v in mm/rad."""
    z, o = fr[:, :, :3, 2], fr[:, :, :3, 3]
    v = np.cross(z, tcp[:, None, :3, 3] - o)
    return np.concatenate([v, z], 2).transpose(0, 2, 1)


def ik_batch(targets, seeds, iters=80, W=300.0):
    """Damped least squares (as tm5_kin._dls) for N TCP targets (N, 4, 4) from seeds (N, 6) rad, all at once.
    -> joints (N, 6) rad and a converged mask."""
    Q = seeds.copy()
    ok = np.zeros(len(Q), bool)
    for _ in range(iters):
        fr, T = fk_batch(Q)
        dp = targets[:, :3, 3] - T[:, :3, 3]
        R = targets[:, :3, :3] @ T[:, :3, :3].transpose(0, 2, 1)
        vee = np.stack([R[:, 2, 1] - R[:, 1, 2], R[:, 0, 2] - R[:, 2, 0], R[:, 1, 0] - R[:, 0, 1]], 1)
        sn = np.linalg.norm(vee, axis=1) / 2
        cs = (np.trace(R, axis1=1, axis2=2) - 1) / 2
        ang = np.arctan2(sn, cs)
        dr = vee * np.where(sn > 1e-9, ang / np.maximum(2 * sn, 1e-12), 0.5)[:, None]
        ok = (np.linalg.norm(dp, axis=1) < 1e-2) & (np.linalg.norm(dr, axis=1) < 1e-5)
        if ok.all():
            break
        J = jac_batch(fr, T)
        J[:, 3:] *= W
        e = np.concatenate([dp, W * dr], 1)
        lam2 = 1.0 + 1e-4 * np.sum(e * e, 1)
        A = J @ J.transpose(0, 2, 1) + lam2[:, None, None] * np.eye(6)
        dq = (J.transpose(0, 2, 1) @ np.linalg.solve(A, e[..., None]))[..., 0]
        step = np.abs(dq).max(1)
        dq *= np.where(step > 0.3, 0.3 / np.maximum(step, 1e-12), 1.0)[:, None]
        dq[ok] = 0
        Q += dq
    return Q, ok


def analyse_batch(Qdeg):
    """analyse() for many joint sets (N, 6) deg -> dict of (N,) arrays (mu1/mu3 per Jacobian, s3, s5,
    signed d_sh, margin). Body-frame measures: eigenvalues are frame independent, so the space-frame
    geometric Jacobian at the TCP point (rotated) gives the same numbers as J_b."""
    Q = np.radians(Qdeg)
    fr, T = fk_batch(Q)
    Jg = jac_batch(fr, T)                                             # [v; w], v in mm/rad
    Jv, Jw = Jg[:, :3] / 1000.0, Jg[:, 3:]
    out = {}

    def mus(J):
        lam = np.clip(np.linalg.eigvalsh(J @ J.transpose(0, 2, 1)), 1e-30, None)
        return np.sqrt(lam[:, -1] / lam[:, 0]), np.sqrt(np.prod(lam, 1))
    out["mu1_v"], out["mu3_v"] = mus(Jv)
    out["mu1_w"], out["mu3_w"] = mus(Jw)
    out["mu1_full"], out["mu3_full"] = mus(np.concatenate([Jw, Jv / L_CHAR], 1))
    out["mu2_v"] = out["mu1_v"] ** 2
    full = np.concatenate([Jw, Jv], 1)
    good = np.abs(np.linalg.det(full)) > 1e-14
    C = np.full((len(Q), 6, 3), np.nan)
    C[good] = np.linalg.inv(full[good])[:, :, 3:]
    lam = np.clip(np.linalg.eigvalsh(np.nan_to_num(C.transpose(0, 2, 1) @ C, nan=0)), 1e-30, None)
    out["mu1_vfix"] = np.where(good, np.sqrt(lam[:, -1] / lam[:, 0]), np.inf)
    out["mu3_vfix"] = np.where(good, 1 / np.sqrt(np.prod(lam, 1)), 0.0)
    s3, s5 = np.sin(Q[:, 2]), np.sin(Q[:, 4])
    det = np.linalg.det(Jg)                                           # mm^3
    out["s3"], out["s5"] = s3, s5
    out["d_sh"] = det / (K.A2 * K.A3 * np.where(np.abs(s3 * s5) > 1e-9, s3 * s5, 1e-9))   # signed, mm
    lo, hi = np.array(K.LIMITS).T
    out["margin"] = np.min(np.minimum(Qdeg - lo, hi - Qdeg), 1)
    return out


def branch(Qdeg):
    """IK branch signature (shoulder, elbow, wrist) = signs of the three factors of det J."""
    a = analyse_batch(np.atleast_2d(Qdeg))
    return np.stack([np.sign(a["d_sh"]), np.sign(a["s3"]), np.sign(a["s5"])], 1)


def slice_grid():
    s = np.arange(S_RANGE[0], S_RANGE[1] + 1, STEP, dtype=float)
    z = np.arange(Z_RANGE[0], Z_RANGE[1] + 1, STEP, dtype=float)
    return s, z


def _point(s, z, az=SLICE_AZ):
    a = math.radians(az)
    return np.array([s * math.cos(a), s * math.sin(a), z])


SEEDS_ARM = [(0, -90, 0, -90), (0, 90, 0, 90), (30, -120, 0, -90), (-30, 120, 0, 90), (0, -90, 0, 90),
             (0, 90, 0, -90), (-30, -100, 0, -90), (30, 100, 0, 90), (60, -60, 0, -90), (-60, 60, 0, 90)]


def compute_slice(name, chunk=4000):
    """IK for every (s, z) cell of the slice, many seeds, batched. status: 1 = solved on the program's branch
    (same shoulder/elbow/wrist signs as the v5 'Home' pose), 2 = reachable only on another branch,
    0 = unreachable (out of reach or past the joint limits)."""
    s, z = slice_grid()
    S, Z = np.meshgrid(s, z)
    n = S.size
    P = np.stack([S.ravel() * math.cos(math.radians(SLICE_AZ)), S.ravel() * math.sin(math.radians(SLICE_AZ)),
                  Z.ravel()], 1)
    Tt = np.stack([tool_matrix(P[k], local_dir(name, S.ravel()[k])) for k in range(n)])
    want = branch(HOME)[0]
    lo, hi = np.array(K.LIMITS).T
    best_q = np.full((n, 6), np.nan)
    status = np.zeros(n, int)
    face = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
    # tm5_kin.reachable(), vectorised: the J5-axis point within the J2/J3 arm's annulus -> else skip (status 0)
    wc = Tt[:, :3, 3] - (TIP + K.D6) * Tt[:, :3, 2]
    r = np.sqrt(np.maximum(0, wc[:, 0] ** 2 + wc[:, 1] ** 2 - K.D4 ** 2))
    d = np.hypot(r, wc[:, 2] - K.D1)
    status[(d < abs(K.A2 - K.A3) - K.D5 - 1) | (d > K.A2 + K.A3 + K.D5 + 1)] = -1
    for j1 in (face - 180, face, face - 90, face + 90):                 # J1 seeds: facing / turned away
        for arm in SEEDS_ARM:
            todo = np.where((status == 0) | (status == 2))[0]
            if not len(todo):
                break
            for c0 in range(0, len(todo), chunk):
                idx = todo[c0:c0 + chunk]
                seed = np.c_[j1[idx], np.tile(arm, (len(idx), 1)), np.zeros(len(idx))]
                Q, ok = ik_batch(Tt[idx], np.radians(seed))
                Qd = np.degrees(Q)
                Qd = (Qd + 180) % 360 - 180                            # into (-180, 180]; all limits allow it
                inlim = np.all((Qd >= lo - K.LIMIT_SLACK) & (Qd <= hi + K.LIMIT_SLACK), 1)
                good = ok & inlim
                if not good.any():
                    continue
                sig = branch(Qd[good])
                on = np.all(sig == want, 1)
                gi = idx[good]
                status[gi[on]], best_q[gi[on]] = 1, Qd[good][on]
                other, m0 = gi[~on], status[gi[~on]] == 0
                status[other[m0]], best_q[other[m0]] = 2, Qd[good][~on][m0]
    res = {k: np.full(n, np.nan) for k in [f"mu{k}_{m}" for m in JACS for k in (1, 3)] +
           ["mu2_v", "s3", "s5", "d_sh", "margin"]}
    status[status < 0] = 0
    have = status > 0
    if have.any():
        a = analyse_batch(best_q[have])
        for k in res:
            res[k][have] = a[k]
    res = {k: v.reshape(S.shape) for k, v in res.items()}
    return dict(name=name, status=status.reshape(S.shape), joints=best_q.reshape(S.shape + (6,)), **res)


def slices(force=False):
    OUT.mkdir(exist_ok=True)
    cache = OUT / f"slices_cache_{STEP}mm.npz"
    key = np.array([TIP, STEP, *S_RANGE, *Z_RANGE, L_CHAR, SLICE_AZ, *HOME, 2])
    if cache.exists() and not force:
        d = np.load(cache, allow_pickle=True)
        if d["key"].shape == key.shape and np.allclose(d["key"], key):
            return d["data"].item()
    import time
    data = {}
    for nm in ORIENT:
        t0 = time.time()
        data[nm] = compute_slice(nm)
        print(f"  slice tool {nm:9s}: {np.bincount(data[nm]['status'].ravel(), minlength=3).tolist()} "
              f"(unreachable, program branch, other branch) {time.time() - t0:.0f} s", flush=True)
    best = {}
    stack = lambda k: np.stack([np.where(data[n]["status"] == 1, data[n][k], np.inf) for n in ORIENT])
    pick = lambda k, idx: np.take_along_axis(np.stack([data[n][k] for n in ORIENT]), idx[None], 0)[0]
    for m in JACS:                         # per Jacobian: the tool direction with the smallest mu1
        idx = np.argmin(np.nan_to_num(stack(f"mu1_{m}"), nan=np.inf), axis=0)
        best[f"mu1_{m}"], best[f"mu3_{m}"], best[f"which_{m}"] = pick(f"mu1_{m}", idx), pick(f"mu3_{m}", idx), idx
        if m == "vfix":
            for k in ("mu2_v", "s3", "s5", "d_sh", "margin"):
                best[k] = pick(k, idx)
    any1 = np.max(np.stack([data[n]["status"] == 1 for n in ORIENT]), 0)
    any2 = np.max(np.stack([data[n]["status"] for n in ORIENT]), 0) > 0
    best["status"] = np.where(any1, 1, np.where(any2, 2, 0))
    for k in best:
        if k != "status" and not k.startswith("which"):
            best[k] = np.where(best["status"] == 1, best[k], np.nan)
    best["name"] = "best"
    data["best"] = best
    np.savez_compressed(cache, key=key, data=np.array(data, dtype=object))
    return data


# ------------------------------------------------------------------ cell layout (ground frame)
def stl_hull(path, M):
    """XY convex hull of an STL placed with M (4x4, into the ground frame) -> list of [x, y]; and z range."""
    import trimesh
    from scipy.spatial import ConvexHull
    m = trimesh.load_mesh(path)
    v = m.vertices @ M[:3, :3].T + M[:3, 3]
    h = ConvexHull(v[:, :2])
    pts = v[h.vertices, :2]
    return pts.round(1).tolist(), [float(v[:, 2].min()), float(v[:, 2].max())]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def to_np(m):
    return np.array([[m[i, j] for j in range(4)] for i in range(4)])


def cell_layout(cell):
    """-> dict(name, G (ground in robot base, 4x4), fixtures [{name, xy, z}], note)."""
    W = np.array(LAYOUT["work_frame"])
    jig = CELL / "jig_parts"
    note = ""
    if cell == "v8":
        try:
            sys.path.insert(0, str(CELL))
            import bench_cell_v8 as v8
            G = np.array(v8.PLATE, float)                           # plate frame (top z = 0) in robot base coords
            fx = []
            for nm, kind, src, M, _c in v8.cell_objects():
                if kind not in ("plate", "jig", "amr", "guide") or nm == "AMR top module":
                    continue
                if isinstance(src, tuple):                         # box (lo, hi) in its own frame
                    (x0, y0, z0), (x1, y1, z1) = src
                    pts = (np.c_[rect(x0, y0, x1, y1), np.zeros(4), np.ones(4)] @ np.asarray(M).T)[:, :2]
                    fx.append(dict(name=nm, xy=pts.round(1).tolist(), z=[float(M[2][3] + z0), float(M[2][3] + z1)]))
                else:
                    xy, zr = stl_hull(src, np.asarray(M, float))
                    fx.append(dict(name=nm, xy=xy, z=zr))
            return dict(name="v8", G=G, fixtures=fx,
                        note="v8: bench_cell_v8.py T-slot plate (jig_v5_layout.json), plate top z = 0")
        except Exception as e:                                      # not there yet / other constant names
            note = f"v8 not usable ({type(e).__name__}: {e}); used v7. "
            cell = "v7"
    sys.path.insert(0, str(CELL))
    import bench_cell_v7 as v7
    G = W @ to_np(v7.GROUND_IN_WORK)
    sx, sy, st = v7.GROUND_SIZE
    fx = [dict(name="ground base (jig base)", xy=rect(0, 0, sx, sy), z=[-st, 0]),
          dict(name="work plate (table)", xy=rect(*v7.WORK_PLATE), z=[-st, -st])]
    for nm, M, stl in (("base A", v7.BASE_A, "base_a_v7"), ("base B", v7.BASE_B, "base_b_v7"),
                       ("plank rack", v7.PLANK_JIG, "plank_rack_v7"),
                       ("guide (on A)", v7.BASE_A * v7.GUIDE_ON_A, "guide_inner_v7")):
        xy, zr = stl_hull(jig / f"{stl}.stl", to_np(M))
        fx.append(dict(name=nm, xy=xy, z=zr))
    ax, ay = v7.AMR_AT.Pos()[:2]
    fx.append(dict(name="AMR plate", xy=rect(ax, ay, ax + v7.AMR_PLATE[0], ay + v7.AMR_PLATE[1]), z=[-10, 0]))
    return dict(name="v7", G=G, fixtures=fx, note=note + "v7: bench_cell_v7.py ground base (Jig V2)")


# ------------------------------------------------------------------ horizontal maps
MAP_KEYS = tuple(f"mu{k}_{m}" for m in JACS for k in (1, 3)) + ("margin", "s3", "s5", "d_sh")


def lookup(sl, rho, zr):
    """Nearest slice cell at s = +rho (the program's branch faces the point), z = zr."""
    s, z = slice_grid()
    j = np.clip(np.rint((rho - s[0]) / STEP).astype(int), 0, len(s) - 1)
    i = np.clip(np.rint((zr - z[0]) / STEP).astype(int), 0, len(z) - 1)
    out = {k: sl[k][i, j] for k in MAP_KEYS}
    out["status"] = np.where((zr < z[0]) | (zr > z[-1]) | (rho > s[-1]), 0, sl["status"][i, j])
    return out


def horizontal_maps(data, lay, heights, step=STEP):
    G = lay["G"]
    base = (np.linalg.inv(G) @ np.r_[0, 0, 0, 1])[:2]                 # robot base in the ground frame
    xs = np.arange(math.floor(base[0] - 1000), base[0] + 1001, step)
    ys = np.arange(math.floor(base[1] - 1000), base[1] + 1001, step)
    X, Y = np.meshgrid(xs, ys)
    maps = {}
    for h in heights:
        P = np.stack([X, Y, np.full_like(X, h), np.ones_like(X)], -1) @ G.T
        rho, zr = np.hypot(P[..., 0], P[..., 1]), P[..., 2]
        maps[h] = {v: lookup(data[v], rho, zr) for v in ("down", "best")}
    return dict(x=xs, y=ys, base=base, maps=maps)


def spot_check(data, lay, heights, n=25, seed=1):
    """Rotational symmetry check: at random map points, direct IK (tool down) on the program's branch vs IK at the
    same (rho, z) turned into the slice plane. -> (n, max rel. diff of mu1 over the Jacobians, max rel. diff of
    the slice's nearest grid cell = the grid's own resolution error)."""
    rng = np.random.default_rng(seed)
    G = lay["G"]
    s, z = slice_grid()
    sym, grid, cnt = [], [], 0
    want = branch(HOME)[0]
    for _ in range(n * 6):
        if cnt >= n:
            break
        x, y = rng.uniform(-700, 800), rng.uniform(-300, 800)
        h = heights[rng.integers(len(heights))]
        p = (G @ np.r_[x, y, h, 1])[:3]
        rho = math.hypot(p[0], p[1])
        ref = lookup(data["down"], np.array(rho), np.array(p[2]))
        if ref["status"] != 1:
            continue
        i, j = int(np.rint((p[2] - z[0]) / STEP)), int(np.rint((rho - s[0]) / STEP))
        q_s = list(data["down"]["joints"][i, j])
        q_s[0] = (q_s[0] + math.degrees(math.atan2(p[1], p[0])) - SLICE_AZ + 180) % 360 - 180
        p2 = _point(rho, p[2])
        q = K.ik(flange_pose(tool_matrix(p, (0, 0, -1))), q_s, seeds=False)
        q2 = K.ik(flange_pose(tool_matrix(p2, (0, 0, -1))), list(data["down"]["joints"][i, j]), seeds=False)
        if q is None or q2 is None or not (np.all(branch(q)[0] == want) and np.all(branch(q2)[0] == want)):
            continue
        cnt += 1
        a1, a2 = analyse(q), analyse(q2)
        sym.append(max(abs(a1[m][0] / a2[m][0] - 1) for m in JACS))
        grid.append(max(abs(a1[m][0] / ref[f"mu1_{m}"] - 1) for m in JACS))
    return cnt, max(sym, default=np.nan), float(np.median(grid)) if grid else np.nan


# ------------------------------------------------------------------ targets
def find_moves(cell):
    for v in (["v8"] if cell == "v8" else []) + ["v7", "v6", "v5", "v4"]:
        p = CELL / "tests" / f"{v}_moves.json"
        if p.exists():
            return p
    return None


def target_table(moves_path, thr=MU1_THR):
    d = json.loads(Path(moves_path).read_text(encoding="utf-8"))
    rows = []
    for k, st in enumerate(d["steps"]):
        if "joints" not in st:
            continue
        q = st["joints"]
        a = analyse(q)
        p = a["T"][:3, 3]
        rows.append(dict(i=k, stage=st.get("stage"), name=st.get("name", ""), move=st.get("move", ""), q=q,
                         p=p.round(1).tolist(), z_tool=a["T"][:3, 2].round(3).tolist(),
                         v=[float(x) for x in a["v"]], w=[float(x) for x in a["w"]],
                         vfix=[float(x) for x in a["vfix"]], A_fix=a["A_fix_base"].tolist(),
                         full=[float(x) for x in a["full"]], margin=float(a["margin"]),
                         s3=float(a["s3"]), s5=float(a["s5"]), d_sh=float(a["d_sh"]),
                         A=a["A_v_base"].tolist(),
                         flag=bool(a["vfix"][0] > thr or a["full"][0] > FULL_THR or a["margin"] < LIMIT_WARN)))
    return d.get("station", moves_path.name), rows


def ellipse_2d(A, axes, n=48):
    """Shadow of the ellipsoid {A^1/2 u, |u| = 1} on the plane of the two base axes -> (n, 2) points."""
    P = np.eye(3)[list(axes)]
    A2 = P @ A @ P.T
    lam, vec = np.linalg.eigh(A2)
    t = np.linspace(0, 2 * np.pi, n)
    return (vec @ (np.sqrt(np.clip(lam, 0, None))[:, None] * np.vstack([np.cos(t), np.sin(t)]))).T


# ------------------------------------------------------------------ sanity
def sanity():
    print("1) analytic body Jacobian vs finite differences (vee(T^-1 dT/dth_i)):")
    rng = np.random.default_rng(4002)
    worst = 0
    for _ in range(20):
        q = [rng.uniform(0.8 * lo, 0.8 * hi) for lo, hi in K.LIMITS]
        worst = max(worst, np.abs(jacobians(q)[1] - jb_numeric(q)).max())
    print(f"   20 random poses: max |J_b - J_b,num| = {worst:.2e} (mm/rad, rad/rad)")
    print("2) det J = A2 A3 sin(th3) sin(th5) d_sh  -> the three singularity families of the TM5 (UR layout):")
    rows = []
    base = [-18.4, 13.8, -109.6, 6.0, -90.0, 161.5]               # plank pick, v5_moves.json
    cases = [("plank pick (v5 program)", base)]
    cases += [(f"wrist  th5 = {t5:g}", base[:4] + [t5, base[5]]) for t5 in (-30, -10, -3, -1, -0.1)]
    cases += [(f"elbow  th3 = {t3:g}", [0, 20, t3, -20, -90, 0]) for t3 in (-60, -20, -5, -1, -0.1)]
    # shoulder: put the J5 origin onto the plane through J1 containing J2's direction (solve th2 numerically)
    from scipy.optimize import brentq
    for off in (20, 5, 1, 0.1):
        try:
            t2s = brentq(lambda t: np.linalg.det(jacobians([0, t, -100, 10, -90, 0])[1]), -60, 60)
            cases.append((f"shoulder th2 = th2* + {off:g}", [0, t2s + off, -100, 10, -90, 0]))
        except ValueError:
            break
    print(f"   {'pose':30s} {'mu1(J_v)':>9s} {'mu3(J_v)':>9s} {'mu1(J_w)':>9s} {'mu1(vfix)':>10s} {'mu1(6x6)':>10s} "
          f"{'mu3(6x6)':>9s} {'|det J|':>10s}")
    for nm, q in cases:
        a = analyse(q)
        print(f"   {nm:30s} {a['v'][0]:9.2f} {a['v'][2]:9.4f} {a['w'][0]:9.2f} {a['vfix'][0]:10.1f} {a['full'][0]:10.1f} "
              f"{a['full'][2]:9.2e} {a['det']:10.3g}")
        rows.append(dict(pose=nm, q=q, mu1_v=a["v"][0], mu3_v=a["v"][2], mu1_w=a["w"][0], mu1_vfix=a["vfix"][0], mu1_full=a["full"][0],
                         mu3_full=a["full"][2]))
    print("   -> 6x6 mu1 -> inf and mu3 -> 0 at all three; J_v alone only at the elbow (stretched arm: no radial\n"
          "      tip speed) - at the wrist/shoulder singularity the 3 wrist joints still move the TCP every way,\n"
          "      the lost direction is a rotation (wrist) or a combined twist (shoulder).")
    return rows


# ------------------------------------------------------------------ plots (PNG)
def _cmap():
    import matplotlib
    cm = matplotlib.colormaps["viridis_r"].copy()
    cm.set_bad((0, 0, 0, 0))
    return cm


def plot_maps(hm, lay, heights, variant, measure, jac, thr):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, ListedColormap
    key = f"{measure}_{jac}"
    n = len(heights)
    fig, axs = plt.subplots(1, n, figsize=(5.2 * n, 5.6), squeeze=False, constrained_layout=True)
    ext = [hm["x"][0], hm["x"][-1], hm["y"][0], hm["y"][-1]]
    vmin, vmax = (1, 30) if measure == "mu1" else None, None
    for ax, h in zip(axs[0], heights):
        m = hm["maps"][h][variant]
        st = m["status"]
        val = np.where(st == 1, m[key], np.nan)
        ax.imshow(np.where(st == 0, 1.0, np.nan), extent=ext, origin="lower", cmap=ListedColormap(["#9a9a9a"]))
        ax.imshow(np.where(st == 2, 1.0, np.nan), extent=ext, origin="lower", cmap=ListedColormap(["#d6d6d6"]))
        if measure == "mu1":
            im = ax.imshow(val, extent=ext, origin="lower", cmap=_cmap(), norm=LogNorm(1, 30))
        else:
            im = ax.imshow(val, extent=ext, origin="lower", cmap=_cmap().reversed())
        X, Y = np.meshgrid(hm["x"], hm["y"])
        if measure == "mu1":
            ax.contour(X, Y, np.nan_to_num(val, nan=0), levels=[thr], colors="red", linewidths=0.8)
        ax.contour(X, Y, np.where(st == 1, m["margin"], 99), levels=[LIMIT_WARN], colors="orange",
                   linewidths=0.8, linestyles="--")
        for f in lay["fixtures"]:
            xy = np.array(f["xy"] + f["xy"][:1])
            ax.plot(xy[:, 0], xy[:, 1], "k-", lw=0.8)
            ax.text(*np.mean(f["xy"], 0), f["name"], fontsize=6, ha="center", va="center")
        b = hm["base"]
        ax.add_patch(plt.Circle(b, 75, fc="none", ec="k", lw=1.2))
        ax.plot(*b, "k+")
        ax.text(b[0], b[1] - 110, "robot base", fontsize=7, ha="center")
        ax.set_title(f"TCP z = {h} mm (ground frame), tool {variant}")
        ax.set_xlabel("x [mm] (away from the robot)")
        ax.set_ylabel("y [mm]")
        ax.set_aspect("equal")
    lbl = {"mu1": f"$\\mu_1$ of $J_{{{jac}}}$ (log)", "mu3": f"$\\mu_3$ of $J_{{{jac}}}$"}[measure]
    fig.colorbar(im, ax=axs[0].tolist(), shrink=0.8, label=lbl)
    fig.suptitle(f"TM5-900 manipulability, cell {lay['name']}: dark grey unreachable, light grey only in another "
                 f"IK branch, red = mu1 {thr:g}, orange dashed = {LIMIT_WARN:g} deg from a joint limit", fontsize=9)
    p = OUT / f"map_{lay['name']}_{variant}_{measure}_{jac}.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def sing_contours(sl):
    """Singularity families on a slice: (label, array, level)."""
    st = sl["status"] == 1
    return [("elbow (arm stretched, th3 = 0)", np.where(st, np.abs(sl["s3"]), 1), SING["elbow"]),
            ("wrist (th5 -> 0)", np.where(st, np.abs(sl["s5"]), 1), SING["wrist"]),
            ("shoulder (wrist point on the J1-J2 plane)", np.where(st, np.abs(sl["d_sh"]), 999), SING["shoulder"])]


def plot_slices(data, jac="v", thr=MU1_THR, names=("down", "best", "out", "side")):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, ListedColormap
    s, z = slice_grid()
    S, Z = np.meshgrid(s, z)
    fig, axs = plt.subplots(2, 2, figsize=(14, 11), constrained_layout=True)
    for ax, nm in zip(axs.flat, names):
        sl = data[nm]
        st = sl["status"]
        ext = [s[0], s[-1], z[0], z[-1]]
        ax.imshow(np.where(st == 0, 1.0, np.nan), extent=ext, origin="lower", cmap=ListedColormap(["#9a9a9a"]))
        ax.imshow(np.where(st == 2, 1.0, np.nan), extent=ext, origin="lower", cmap=ListedColormap(["#d6d6d6"]))
        im = ax.imshow(np.where(st == 1, sl[f"mu1_{jac}"], np.nan), extent=ext, origin="lower", cmap=_cmap(),
                       norm=LogNorm(1, 30))
        cols = {"elbow": "red", "wrist": "magenta", "shoulder": "cyan"}
        for lab, arr, lev in sing_contours(sl):
            c = ax.contour(S, Z, arr, levels=[lev], colors=cols[lab.split()[0]], linewidths=1.2)
            segs = [g for g in c.allsegs[0] if len(g) > 2]
            if segs:
                seg = max(segs, key=len)
                ax.text(*seg[len(seg) // 2], lab.split(" (")[0], color=cols[lab.split()[0]], fontsize=8,
                        fontweight="bold")
        ax.add_patch(plt.Rectangle((-75, -50), 150, 50 + K.D1, fc="0.3", ec="k"))
        ax.axvline(0, color="k", lw=0.5, ls=":")
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title(f"tool {nm}" + (" (min mu1 over the 8 directions)" if nm == "best" else ""))
        ax.set_xlabel("s [mm] = horizontal distance from the J1 axis (+ towards the cell; - = mirror, J1 turned 180)")
        ax.set_ylabel("z [mm] (robot base frame)")
        ax.set_aspect("equal")
    fig.colorbar(im, ax=axs.ravel().tolist(), shrink=0.6, label=f"$\\mu_1$ of $J_{{{jac}}}$ (log)")
    fig.suptitle("Vertical slice through the J1 axis (the same in every direction: the arm is symmetric about J1). "
                 f"Contours: red elbow |sin th3| < {SING['elbow']:.2f}, magenta wrist |sin th5| < {SING['wrist']:.2f}, "
                 f"cyan shoulder |d_sh| < {SING['shoulder']:g} mm. Dark grey unreachable, light grey only on another IK branch",
                 fontsize=9)
    p = OUT / f"slice_{jac}.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p


def plot_targets(station, rows, lay, thr, tag):
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
    seen, sc = [], 60 / 0.9                                           # 0.9 m/s semi-axis -> 60 mm on the plot
    Gi = np.linalg.inv(lay["G"])
    for r in rows:
        p = np.array(r["p"])
        if any(np.linalg.norm(p - x) < 5 for x in seen):
            continue
        seen.append(p)
        pg = (Gi @ np.r_[p, 1])[:3]
        A = Gi[:3, :3] @ np.array(r["A"]) @ Gi[:3, :3].T
        c = "red" if r["flag"] else "tab:blue"
        for ax, axes in ((axs[0], (0, 1)), (axs[1], (0, 2))):
            e = ellipse_2d(A, axes) * sc
            ax.plot(pg[axes[0]] + e[:, 0], pg[axes[1]] + e[:, 1], c, lw=0.8)
            ax.plot(pg[axes[0]], pg[axes[1]], ".", color=c, ms=3)
            if r["flag"]:
                ax.text(pg[axes[0]], pg[axes[1]], f" {r['i']}", fontsize=6, color="red")
    for f in lay["fixtures"]:
        xy = np.array(f["xy"] + f["xy"][:1])
        axs[0].plot(xy[:, 0], xy[:, 1], "k-", lw=0.6)
        axs[1].plot([xy[:, 0].min(), xy[:, 0].max()], [f["z"][1]] * 2, "k-", lw=0.6)
    b = (Gi @ np.r_[0, 0, 0, 1])[:3]
    axs[0].add_patch(plt.Circle(b[:2], 75, fc="none", ec="k"))
    axs[1].add_patch(plt.Rectangle((b[0] - 75, b[2] - 50), 150, 50 + K.D1, fc="0.5"))
    for ax, t in zip(axs, ("top view (x, y)", "side view (x, z)")):
        ax.set_aspect("equal")
        ax.set_title(f"{station}: J_v ellipsoids (shadows), {t}; 60 mm = 0.9 m/s per rad/s; red = flagged")
        ax.set_xlabel("x [mm] (cell ground frame)")
    axs[0].set_ylabel("y [mm]")
    axs[1].set_ylabel("z [mm]")
    p = OUT / f"targets_{tag}.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


# ------------------------------------------------------------------ iso-surface, JSON for the viewer
def iso_surface(sl, thr, key="mu1_vfix", n_az=72):
    """Surface of revolution of the key = thr contour of the slice's s >= 0 half (robot base frame, mm)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s, z = slice_grid()
    S, Z = np.meshgrid(s, z)
    val = np.where((sl["status"] == 1) & (S >= 0), sl[key], np.nan)
    fig, ax = plt.subplots()
    cs = ax.contour(S, Z, np.nan_to_num(val, nan=1.0), levels=[thr])
    plt.close(fig)
    verts, faces = [], []
    ph = np.linspace(0, 2 * np.pi, n_az, endpoint=False)
    for seg in cs.allsegs[0]:
        if len(seg) < 3:
            continue
        seg = seg[::2] if len(seg) > 200 else seg
        o = len(verts)
        for rr, zz in seg:
            verts += [[rr * math.cos(a), rr * math.sin(a), zz] for a in ph]
        for k in range(len(seg) - 1):
            for m in range(n_az):
                a, b = o + k * n_az + m, o + k * n_az + (m + 1) % n_az
                c, d = a + n_az, b + n_az
                faces += [[a, b, d], [a, d, c]]
    return np.array(verts), np.array(faces, int)


def r_(a, nd=3):
    a = np.asarray(a, float)
    return [None if not np.isfinite(x) else round(float(x), nd) for x in a.ravel()]


JSON_ORIENT = ("down", "best", "down45out", "out", "up", "side")


def write_json(data, lay, targets, iso, thr, iso_key):
    """manip_data.json for manipulability.html: the slices (the viewer builds the horizontal maps from them by
    the J1 symmetry, like horizontal_maps()), fixtures, program targets, iso-surface; all in the cell frame."""
    s, z = slice_grid()
    sl_out = {}
    for nm in JSON_ORIENT:
        sl = data[nm]
        st = sl["status"]
        d = dict(status=st.ravel().tolist(),
                 sing={lab.split()[0]: _segs(s, z, arr, lev) for lab, arr, lev in sing_contours(sl)})
        for m in ("v", "vfix", "full"):
            for k in (1, 3):
                d[f"mu{k}_{m}"] = r_(np.log10(np.where(st == 1, sl[f"mu{k}_{m}"], np.nan)), 2)
        d["margin"] = r_(np.where(st == 1, sl["margin"], np.nan), 0)
        sl_out[nm] = d
    G = lay["G"]
    Gi = np.linalg.inv(G)
    progs = {}
    for station, rows in targets:
        lst = []
        for r in rows:
            pg = (Gi @ np.r_[r["p"], 1])[:3]
            e = {}
            for key, A in (("v", r["A"]), ("fix", r["A_fix"])):
                A = Gi[:3, :3] @ np.array(A) @ Gi[:3, :3].T
                lam, vec = np.linalg.eigh(A)
                e[key] = dict(A=np.round(A, 5).tolist(), axes=(vec * np.sqrt(np.clip(lam, 0, None))).T.round(4).tolist())
            lst.append(dict(i=r["i"], name=r["name"], stage=r["stage"], p=pg.round(1).tolist(), ell=e,
                            mu1_v=round(r["v"][0], 2), mu2_v=round(r["v"][1], 2), mu3_v=round(r["v"][2], 4),
                            mu1_w=round(r["w"][0], 2), mu1_vfix=round(r["vfix"][0], 2),
                            mu1_full=round(r["full"][0], 2), margin=round(r["margin"], 1), flag=r["flag"]))
        progs[station] = lst
    iv, ifc = iso
    ivg = (np.c_[iv, np.ones(len(iv))] @ Gi.T)[:, :3] if len(iv) else np.zeros((0, 3))
    out = dict(cell=lay["name"], note=lay["note"], tip_mm=TIP, thr=thr, full_thr=FULL_THR, limit_warn=LIMIT_WARN,
               l_char=L_CHAR, G=np.round(G, 6).tolist(), base=(Gi @ np.r_[0, 0, 0, 1])[:3].round(1).tolist(),
               base_r=75, base_h=K.D1, slice_az=SLICE_AZ, step=STEP, orient=list(JSON_ORIENT),
               slice=dict(s=s.tolist(), z=z.tolist(), data=sl_out),
               fixtures=lay["fixtures"], programs=progs, iso_key=iso_key,
               iso=dict(v=np.round(ivg, 1).ravel().tolist(), f=np.asarray(ifc).ravel().tolist()))
    p = OUT / "manip_data.json"
    p.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    return p


def _segs(s, z, arr, lev):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    S, Z = np.meshgrid(s, z)
    fig, ax = plt.subplots()
    cs = ax.contour(S, Z, arr, levels=[lev])
    plt.close(fig)
    return [np.round(seg[:: max(1, len(seg) // 150)], 0).tolist() for seg in cs.allsegs[0] if len(seg) > 3]


# ------------------------------------------------------------------ CLI
def summary(data, hm, lay, heights, thr, jac="vfix"):
    key = f"mu1_{jac}"
    print(f"summary for mu1 of {jac}:")
    sl = data["down"]
    s, z = slice_grid()
    st = sl["status"] == 1
    print(f"slice 'down' (TCP z rel. robot base): program-branch cells {st.sum()}, "
          f"only other branch {(sl['status'] == 2).sum()}")
    for zz in (0, 100, 300, 500):
        i = int(np.argmin(abs(z - zz)))
        ok = st[i] & (s >= 0)
        if ok.any():
            row = sl[key][i]
            good = s[ok & (row < 2)]
            bad = s[ok & (row > thr)]
            print(f"  z_base {zz:4d}: reach s {s[ok].min():.0f}..{s[ok].max():.0f} mm, mu1 < 2 for s in "
                  f"{(good.min(), good.max()) if len(good) else '-'}, mu1 > {thr:g} at s = "
                  f"{np.round(bad).astype(int).tolist()[:6]}{' ...' if len(bad) > 6 else ''}; min mu1 "
                  f"{np.nanmin(row[ok]):.2f} at s = {s[ok][np.nanargmin(row[ok])]:.0f}")
    for h in heights:
        for v in ("down", "best"):
            m = hm["maps"][h][v]
            ok = m["status"] == 1
            mu = m[key][ok]
            near = ok & (m["margin"] < LIMIT_WARN)
            print(f"  map z={h:3d} tool {v:4s}: reachable {ok.mean() * 100:4.1f}% of the square, mu1 median "
                  f"{np.median(mu):.2f}, >{thr:g}: {(mu > thr).mean() * 100:4.1f}%; within {LIMIT_WARN:g} deg of a "
                  f"limit: {near.sum() / max(ok.sum(), 1) * 100:4.1f}% (median mu1 there "
                  f"{np.median(m[key][near]) if near.any() else float('nan'):.2f})")
    for f in lay["fixtures"]:
        xy = np.array(f["xy"])
        xs, ys = hm["x"], hm["y"]
        msk = np.zeros((len(ys), len(xs)), bool)
        from matplotlib.path import Path as MPath
        X, Y = np.meshgrid(xs, ys)
        msk = MPath(xy).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
        vals = []
        for h in heights:
            m = hm["maps"][h]["down"]
            ok = msk & (m["status"] == 1)
            vals.append(f"z{h}: {np.nanmin(m[key][ok]):.2f}-{np.nanmax(m[key][ok]):.2f} "
                        f"({(msk & (m['status'] != 1)).sum() / max(msk.sum(), 1) * 100:.0f}% unreach)"
                        if ok.any() else f"z{h}: unreachable")
        print(f"  over {f['name']:24s} mu1, tool down: " + "; ".join(vals))


def main(argv=None):
    import matplotlib
    matplotlib.use("Agg")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["map", "slice", "targets", "sanity", "all"])
    ap.add_argument("--z", default="0,50,100,150")
    ap.add_argument("--tool", default="both", choices=["down", "best", "both"])
    ap.add_argument("--cell", default="v8", choices=["v7", "v8"])
    ap.add_argument("--measure", default="mu1", choices=["mu1", "mu3"])
    ap.add_argument("--jac", default="vfix", choices=["v", "vfix", "w", "full"],
                    help="v = J_v (MR 5.4), vfix = J_v with the orientation held (default), w = J_w, full = 6x6")
    ap.add_argument("--moves", default=None, help="moves JSON (default: newest tests/v*_moves.json)")
    ap.add_argument("--thr", type=float, default=MU1_THR)
    ap.add_argument("--force", action="store_true", help="recompute the slices (cache: manipulability/)")
    ap.add_argument("--step", type=int, default=None, help="grid step mm (default 20; 10 = fine, ~4x slower)")
    a = ap.parse_args(argv)
    global STEP
    if a.step:
        import os
        os.environ["MANIP_STEP"] = str(a.step)
        STEP = a.step
    OUT.mkdir(exist_ok=True)
    heights = [int(float(v)) for v in a.z.split(",")]
    if a.cmd == "sanity":
        sanity()
        return
    lay = cell_layout(a.cell)
    print(f"cell: {lay['note']}  (TCP = flange + {TIP:g} mm along tool z)")
    data = slices(a.force)
    if a.cmd in ("slice", "all"):
        for jac in ("v", "vfix", "full"):
            print("wrote", plot_slices(data, jac, a.thr))
    hm = None
    if a.cmd in ("map", "all"):
        hm = horizontal_maps(data, lay, heights)
        n, e, g = spot_check(data, lay, heights)
        print(f"symmetry check: direct IK at {n} random map points vs the same (rho, z) in the slice plane: max rel. "
              f"diff of mu1 {e:.1e}; nearest-grid-cell lookup error (median) {g * 100:.0f}% at {STEP} mm")
        for v in (("down", "best") if a.tool == "both" else (a.tool,)):
            print("wrote", plot_maps(hm, lay, heights, v, a.measure, a.jac, a.thr))
            if a.cmd == "all" and a.measure == "mu1":
                print("wrote", plot_maps(hm, lay, heights, v, "mu3", a.jac, a.thr))
        summary(data, hm, lay, heights, a.thr, a.jac)
    targets = []
    if a.cmd in ("targets", "all"):
        files = [Path(a.moves)] if a.moves else [p for p in (find_moves(a.cell),) if p]
        if a.cmd == "all" and not a.moves:
            files = sorted((CELL / "tests").glob("v*_moves.json"))
        for mp in files:
            mp = mp if mp.is_absolute() else (Path.cwd() / mp)
            station, rows = target_table(mp, a.thr)
            targets.append((station, rows))
            tag = mp.stem
            print(f"\n{station} ({mp.name}): {len(rows)} targets; flag = mu1(vfix) > {a.thr:g} or mu1(6x6) > "
                  f"{FULL_THR:g} or < {LIMIT_WARN:g} deg from a joint limit")
            print(f"  {'#':>3s} {'name':34s} {'mu1v':>6s} {'mu2v':>6s} {'mu3v':>7s} {'mu1w':>6s} {'mu2w':>6s} "
                  f"{'mu3w':>6s} {'mu1fx':>6s} {'mu1_6':>6s} {'lim':>5s} {'th3':>6s} {'th5':>6s}")
            for r in rows:
                if r["flag"] or a.cmd == "targets":
                    print(f"  {r['i']:3d} {r['name'][:34]:34s} {r['v'][0]:6.2f} {r['v'][1]:6.2f} {r['v'][2]:7.4f} "
                          f"{r['w'][0]:6.2f} {r['w'][1]:6.2f} {r['w'][2]:6.3f} {r['vfix'][0]:6.2f} {r['full'][0]:6.2f} "
                          f"{r['margin']:5.1f} {r['q'][2]:6.1f} {r['q'][4]:6.1f}" + ("  <-- FLAG" if r["flag"] else ""))
            for k in ("v", "vfix", "full"):
                mu = np.array([r[k][0] for r in rows])
                print(f"  mu1({k}): min {mu.min():.2f}, median {np.median(mu):.2f}, max {mu.max():.2f}")
            print(f"  flagged {sum(r['flag'] for r in rows)} of {len(rows)}")
            (OUT / f"targets_{tag}.json").write_text(json.dumps(rows, indent=0), encoding="utf-8")
            print("wrote", plot_targets(station, rows, lay, a.thr, tag))
    if a.cmd == "all":
        iso_key = f"mu1_{a.jac}"
        iv, ifc = iso_surface(data["down"], a.thr, iso_key)
        if len(iv):
            import trimesh
            mesh = trimesh.Trimesh(iv, ifc, process=False)
            mesh.export(OUT / f"iso_{iso_key}_{a.thr:g}_down.stl")
            mesh.export(OUT / f"iso_{iso_key}_{a.thr:g}_down.glb")
            print(f"wrote iso-surface {iso_key} = {a.thr:g}, tool down: {len(iv)} vertices (robot base frame, mm)")
        print("wrote", write_json(data, lay, targets, (iv, ifc), a.thr, iso_key))


if __name__ == "__main__":
    main()
