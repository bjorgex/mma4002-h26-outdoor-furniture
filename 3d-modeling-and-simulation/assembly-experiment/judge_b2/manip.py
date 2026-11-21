"""Manipulability (velocity ellipsoids) of the TM5-900 with the gripper at the program's targets.

Theory: Modern Robotics 5.4 (pp. 195-197). For a Jacobian J (here the BODY Jacobian J_b of the TCP, MR row
order [omega; v]) A = J J^T; principal axes = eigenvectors of A, semi-axes sqrt(lambda_i). Measures:
    mu1 = sqrt(lmax/lmin)  isotropy (1 = round, -> inf at a singularity)
    mu2 = lmax/lmin        condition number of A (= mu1^2)
    mu3 = sqrt(det A)      volume (-> 0 at a singularity)
vfix = linear TCP velocity with the orientation held, A_fix = (C^T C)^-1, C = last 3 columns of J^-1: what a
straight tool-down move sees. The judge reports max mu1_vfix and min mu3_vfix over the move targets, and the
targets with mu1_vfix > MU1_THR (near-singular).
TCP = flange * transl(0, 0, TIP).
"""
import math

import numpy as np

import tm5_kin as K

TIP = 160.0                          # mm, flange -> closed fingertips
L_CHAR = 0.5                         # m: length scale for the 6x6 measure (v / L next to omega)
MU1_THR = 3.0                        # flag: semi-axis ratio > 3 (mu2 > 9) counts as near-singular


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
