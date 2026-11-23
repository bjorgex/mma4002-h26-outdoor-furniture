"""How far a jig moved since its reference photo, from the OMRON/TM landmark sticker on it -> v10's moves file.

  python tests/vision_lab/landmark_move.py <reference.png> <now.png> [--jig "Base B"] [--save moves.json]
  then: python bench_cell_v10.py moves.json   (or bench_cell_v10_1plank.py moves.json)

The reference photo is taken with the jig in its place (where the program expects it; 2026-11-20: Base B, photo
reference/20261120-155755-912.png). Each photo's JSON holds the robot pose; camera_tm.json the calibration (TM wrist
camera, Techman plate, 0.25 px / 0.34 mm). The sticker's 4 corners are followed along their line of sight down to
the sticker's height (fixed, from the reference: the most stable way, see the 10 mm test in tests/vision_lab/README),
then a 2D rigid fit of now vs reference gives the jig's move: x, y (mm, robot base) and rz (deg), and
T_move (4x4: new point = T_move @ taught point), the format bench_cell_v10.py reads.
"""
import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

from landmark import find_landmarks, landmark_pose, tm_pose_to_T

HERE = Path(__file__).resolve().parent


def corners_on_plane(png, cam, z=None, size=50.0):
    """The sticker's 4 outer-frame corners (TL TR BR BL) in the robot base on the plane z (default: PnP height)."""
    K, d, Ttc = np.array(cam["K"]), np.array(cam["dist"]), np.array(cam["T_tool_cam"])
    marks = find_landmarks(cv2.imread(str(png)))
    if len(marks) != 1:
        raise SystemExit(f"{png}: {len(marks)} landmarks found, need exactly 1")
    c = marks[0]["corners"]
    T = tm_pose_to_T(json.loads(Path(png).with_suffix(".json").read_text())["pose"]) @ Ttc
    if z is None:
        z = float((T @ landmark_pose(c, size, K, d))[2, 3])
    rays = cv2.undistortPoints((c + 0.5).reshape(-1, 1, 2).astype(np.float64), K, d).reshape(-1, 2)
    out = []
    for u, v in rays:
        r = T[:3, :3] @ np.array([u, v, 1.0])
        out.append(T[:3, 3] + (z - T[2, 3]) / r[2] * r)
    return np.array(out), z


def rigid2d(a, b):
    """R, t with b ~ R a + t (2D, least squares)."""
    ca, cb = a.mean(0), b.mean(0)
    U, _, Vt = np.linalg.svd((a - ca).T @ (b - cb))
    R = (U @ Vt).T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = (U @ Vt).T
    return R, cb - R @ ca


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("now")
    ap.add_argument("--jig", default="Base B")
    ap.add_argument("--camera", default=str(HERE / "camera_tm.json"))
    ap.add_argument("--size", type=float, default=50.0, help="OUTER side of the black frame, mm: 50 on our sticker (the outline found)")
    ap.add_argument("--save")
    a = ap.parse_args()
    cam = json.loads(Path(a.camera).read_text())
    ref, z = corners_on_plane(a.reference, cam, size=a.size)
    now, _ = corners_on_plane(a.now, cam, z=z, size=a.size)
    R, t = rigid2d(ref[:, :2], now[:, :2])
    T = np.eye(4)
    T[:2, :2], T[:2, 3] = R, t
    rz = math.degrees(math.atan2(R[1, 0], R[0, 0]))
    fit = np.abs((R @ ref[:, :2].T).T + t - now[:, :2]).max()
    c0, c1 = ref.mean(0), now.mean(0)
    print(f"sticker height {z:.1f} mm; sticker centre ({c0[0]:.1f}, {c0[1]:.1f}) -> ({c1[0]:.1f}, {c1[1]:.1f}): "
          f"moved {c1[0] - c0[0]:+.1f}, {c1[1] - c0[1]:+.1f} mm, turned {rz:+.2f} deg (corner fit {fit:.2f} mm)")
    if a.save:
        out = {"source": f"landmark_move.py {Path(a.reference).name} -> {Path(a.now).name}",
               "moves": {a.jig: {"x": round(float(T[0, 3]), 3), "y": round(float(T[1, 3]), 3),
                                 "rz_deg": round(rz, 3), "T_move": T.round(6).tolist()}}}
        Path(a.save).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("written:", a.save)


if __name__ == "__main__":
    main()
