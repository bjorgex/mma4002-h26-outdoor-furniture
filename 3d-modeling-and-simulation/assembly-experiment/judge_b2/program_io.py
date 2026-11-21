"""Program files for the judge: load a program json, and the two 4x4 helpers kin_check uses.

A program json: {"base": {"name", "pose"}, "tcp": {"name", "pose": [x, y, z, rx, ry, rz]}, "joint_speed": deg/s,
"steps": [...]} with steps
    {"name", "move": "ptp" | "line", "joints": [6 deg], "flange": [x, y, z, rx, ry, rz] (robot base),
     "speed": mm/s (Line), "joint_speed": deg/s (PTP, optional), "pose_base": TCP in the base frame (info)}
    {"name", "do0": 0 | 1, "gripper": "grip" | "release" | null, "parts": [cell part names], "wait_ms": ms}
    {"message": "..."}                                                    (ignored)
Poses: TM convention (mm, deg, R = Rz Ry Rx). The joints are what a PTP drives to; a Line drives the TCP straight
from where the arm is to flange * tcp (the stored joints of a Line are only checked against where it ends).
"""
import json
from pathlib import Path

import tm5_kin as K


def mul(a, b):
    return K.matmul(a, b)


def inv(m):
    r = [[m[j][i] for j in range(3)] for i in range(3)]
    t = [-sum(r[i][k] * m[k][3] for k in range(3)) for i in range(3)]
    return [r[0] + [t[0]], r[1] + [t[1]], r[2] + [t[2]], [0, 0, 0, 1]]


def load_program(path):
    path = Path(path)
    if path.suffix != ".json":
        raise ValueError(f"{path}: the judge reads program json files only")
    return json.loads(path.read_text(encoding="utf-8"))
