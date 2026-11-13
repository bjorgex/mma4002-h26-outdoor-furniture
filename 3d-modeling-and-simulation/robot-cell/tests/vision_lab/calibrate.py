"""Camera calibration for the real cell, with the printed ChArUco board (print_markers.py). Writes camera.json, which
real_capture.py uses to turn a webcam frame + the robot pose into a photo jig_vision.py can measure.

1. intrinsics - the lens (K, distortion), from 10-20 photos of the board (tilted, in all corners of the image):
     python tests/vision_lab/calibrate.py intrinsics calib_shots/            -> camera.json (K, dist)
2a. camera on the tool (eye-in-hand) - where the camera sits on the tool: the board lies still on the table, the robot
    looks at it from 10-15 different poses (tilt 10-25 deg each way, turn the wrist), each saved with its pose:
     python tests/vision_lab/calibrate.py handeye calib_shots/               -> camera.json + T_tool_cam
2b. camera fixed above the table (eye-to-hand) - where the camera is: the board on the table, one photo, and the robot
    tip touched on three board points (origin O, a point on the +x edge, a point on the +y edge; mm, robot base):
     python tests/vision_lab/calibrate.py fixed board.png --O x y z --X x y z --Y x y z   -> camera.json + T_base_cam
   check the printed origin O and the x / y arrows on the board sheet; y runs DOWN the page.

calib_shots/: <name>.png + <name>.json with {"pose": [x, y, z, rx, ry, rz]} (TM pose of the tool, mm / deg) - made by
`real_capture.py calib` (webcam + Modbus), or by the sim test (calibrate_test.py). The pose must be the same TCP that
real_capture.py reads later (Modbus 7001 = the current TCP): don't change the TCP in TMflow between the two.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "robot_sim"))
from print_markers import BOARD  # noqa: E402
import tm5_kin  # noqa: E402

HALF = 0.5                                       # OpenCV pixel centres at whole numbers, our K at +0.5 (see jig_vision)


def board():
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, BOARD["dict"]))
    return cv2.aruco.CharucoBoard(BOARD["squares"], BOARD["square_mm"], BOARD["marker_mm"], d)


def detect(img):
    """-> (object points Nx3 mm in the board frame, image points Nx2 px) of the visible chessboard corners, or None."""
    b = board()
    cc, ci, _, _ = cv2.aruco.CharucoDetector(b).detectBoard(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img)
    if ci is None or len(ci) < 6:
        return None
    obj, imgp = b.matchImagePoints(cc, ci)
    return obj.reshape(-1, 3), imgp.reshape(-1, 2)


def board_pose(img, K, dist):
    """T_cam_board (4x4, mm) from one photo, or None. Pixel coords in our +0.5 convention."""
    d = detect(img)
    if d is None:
        return None
    obj, imgp = d
    ok, rvec, tvec = cv2.solvePnP(obj, imgp + HALF, K, dist, flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return None
    R, _ = cv2.Rodrigues(rvec)
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = tvec.ravel()
    err = cv2.projectPoints(obj, rvec, tvec, K, dist)[0].reshape(-1, 2) - (imgp + HALF)
    return T, float(np.sqrt((err ** 2).sum(1).mean())), len(obj)


def pose_mat(p):
    return np.array(tm5_kin.pose_to_mat(list(p)), float)


def shots(folder):
    out = []
    for j in sorted(Path(folder).glob("*.json")):
        meta = json.loads(j.read_text(encoding="utf-8"))
        img = cv2.imread(str(j.with_suffix(".png")))
        if img is not None:
            out.append((j.stem, img, meta))
    return out


def intrinsics(folder, fix_k3=True):
    obj_all, img_all, size, used = [], [], None, []
    for name, img, _ in shots(folder):
        d = detect(img)
        size = (img.shape[1], img.shape[0])
        if d is None or len(d[0]) < 10:
            print(f"  {name}: board not found (or < 10 corners) - skipped"); continue
        obj_all.append(d[0].astype(np.float32)); img_all.append((d[1] + HALF).astype(np.float32)); used.append(name)
    if len(used) < 6:
        sys.exit(f"only {len(used)} usable photos - take 10-20 of the board, tilted, all over the image")
    flags = cv2.CALIB_FIX_K3 if fix_k3 else 0
    rms, K, dist, _, _ = cv2.calibrateCamera(obj_all, img_all, size, None, None, flags=flags)
    print(f"intrinsics from {len(used)} photos: reprojection RMS {rms:.3f} px")
    return {"K": K.tolist(), "dist": dist.ravel().tolist(), "size": list(size), "rms_px": rms, "photos": used}


def handeye(folder, cam):
    K, dist = np.array(cam["K"]), np.array(cam["dist"])
    Rg, tg, Rt, tt, Tbt, Tcb, names = [], [], [], [], [], [], []
    for name, img, meta in shots(folder):
        r = board_pose(img, K, dist)
        if r is None:
            print(f"  {name}: board not found - skipped"); continue
        T_cb, rms, n = r
        T_bt = pose_mat(meta["pose"])
        Rg.append(T_bt[:3, :3]); tg.append(T_bt[:3, 3]); Rt.append(T_cb[:3, :3]); tt.append(T_cb[:3, 3])
        Tbt.append(T_bt); Tcb.append(T_cb); names.append(name)
    if len(names) < 5:
        sys.exit(f"only {len(names)} usable poses - take 10-15, with the wrist tilted and turned differently each time")
    best = None
    for meth in (cv2.CALIB_HAND_EYE_PARK, cv2.CALIB_HAND_EYE_TSAI, cv2.CALIB_HAND_EYE_DANIILIDIS):
        R, t = cv2.calibrateHandEye(Rg, tg, Rt, tt, method=meth)
        T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t.ravel()
        # check: the board is still, so T_base_tool T_tool_cam T_cam_board must be the same board pose every time
        B = np.array([Tb @ T @ Tc for Tb, Tc in zip(Tbt, Tcb)])
        spread = float(np.linalg.norm(B[:, :3, 3] - np.median(B[:, :3, 3], 0), axis=1).max())
        if not best or spread < best[1]:
            best = (T, spread, meth)
    T, spread, meth = best
    print(f"hand-eye from {len(names)} poses: board position agrees within {spread:.2f} mm across the poses")
    return {"mount": "tool", "T_tool_cam": T.tolist(), "handeye_spread_mm": spread, "handeye_poses": names}


def fixed(img_path, cam, O, X, Y):
    K, dist = np.array(cam["K"]), np.array(cam["dist"])
    r = board_pose(cv2.imread(str(img_path)), K, dist)
    if r is None:
        sys.exit("board not found in the photo")
    T_cb, rms, n = r
    O, X, Y = (np.array(v, float) for v in (O, X, Y))
    x = (X - O) / np.linalg.norm(X - O)
    y = (Y - O) - np.dot(Y - O, x) * x; y /= np.linalg.norm(y)
    T_bb = np.eye(4); T_bb[:3, 0] = x; T_bb[:3, 1] = y; T_bb[:3, 2] = np.cross(x, y); T_bb[:3, 3] = O
    T = T_bb @ np.linalg.inv(T_cb)
    print(f"fixed camera at {np.round(T[:3, 3], 1)} mm (board seen with {n} corners, {rms:.2f} px)")
    return {"mount": "fixed", "T_base_cam": T.tolist()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["intrinsics", "handeye", "fixed"])
    ap.add_argument("path", help="calib_shots folder (intrinsics, handeye) or the board photo (fixed)")
    ap.add_argument("--camera", default=str(HERE / "camera.json"))
    ap.add_argument("--O", nargs=3, type=float); ap.add_argument("--X", nargs=3, type=float); ap.add_argument("--Y", nargs=3, type=float)
    a = ap.parse_args()
    cam = json.loads(Path(a.camera).read_text()) if Path(a.camera).exists() else {}
    if a.cmd == "intrinsics":
        cam.update(intrinsics(a.path))
    else:
        if "K" not in cam:
            sys.exit("run intrinsics first")
        cam.update(handeye(a.path, cam) if a.cmd == "handeye" else fixed(a.path, cam, a.O, a.X, a.Y))
    cam["updated"] = time.strftime("%Y-%m-%d %H:%M")
    Path(a.camera).write_text(json.dumps(cam, indent=1), encoding="utf-8")
    print("written:", a.camera)


if __name__ == "__main__":
    main()
