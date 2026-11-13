"""Photos on the real cell: a webcam frame + the robot's pose -> a photo in the sim's format (PNG + JSON with K and
T_base_cam), so jig_vision.py measures real and sim photos the same way. It only READS the robot (Modbus); it never
moves it - you jog the robot yourself.

  python tests/vision_lab/real_capture.py calib  [--cam 0]        # calibration photo -> calib_shots/ (raw frame + pose)
  python tests/vision_lab/real_capture.py photo  [--cam 0]        # measuring photo -> real_shots/<stamp>.png + .json
  python tests/vision_lab/real_capture.py live   [--cam 0]        # a window with the camera and the markers it sees
options: --robot 10.0.12.101 (Modbus) | --pose x y z rx ry rz (typed) | --no-robot (fixed camera: no pose needed)
         --image file.png instead of a webcam (e.g. a saved frame), --res 1920x1080, --camera camera.json

The pose is Modbus input registers 7001-7012: the current TCP pose in the robot base (mm, deg) - the same TCP must be
active as when calibrate.py handeye ran. For a camera on the tool, keep the robot STILL while the photo is taken.
"""
import argparse
import json
import socket
import struct
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from calibrate import pose_mat  # noqa: E402

REAL_JIGS = HERE / "real_jigs.json"                 # real_setup.py: the markers' places in the taught layout


def modbus_pose(host, port=502):
    """TCP pose (x y z mm, rx ry rz deg) from input registers 7001.. (12 registers = 6 floats, big-endian)."""
    s = socket.create_connection((host, port), timeout=3)
    try:
        s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 4, 7001, 12))
        r = b""
        while len(r) < 9 + 24:
            chunk = s.recv(64)
            if not chunk:
                break
            r += chunk
    finally:
        s.close()
    if len(r) < 33 or r[7] != 4:
        raise RuntimeError(f"Modbus answer not understood: {r!r}")
    return [struct.unpack(">f", r[9 + i:13 + i])[0] for i in range(0, 24, 4)]


def frame(a):
    if a.image:
        img = cv2.imread(a.image)
        if img is None:
            sys.exit(f"can't read {a.image}")
        return img
    cap = cv2.VideoCapture(a.cam, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(a.cam)
    if a.res:
        w, h = (int(v) for v in a.res.lower().split("x"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    img = None
    for _ in range(15):                              # let exposure / white balance settle
        ok, f = cap.read()
        if ok:
            img = f
    cap.release()
    if img is None:
        sys.exit(f"no frame from camera {a.cam}")
    return img


def pose(a):
    if a.pose:
        return list(a.pose)
    if a.no_robot:
        return None
    return modbus_pose(a.robot)


def write(folder, img, meta):
    folder.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 1000:03d}"   # ms: two photos in a second
    f = folder / f"{stamp}.png"
    cv2.imwrite(str(f), img)
    meta["image"] = f.name
    f.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return f.with_suffix(".json")


def measuring_photo(img, p, cam, jig_model="file", jigs_file=None):
    """Undistort (new K, no distortion left) and work out T_base_cam -> (image, meta) in jig_vision's format."""
    K, dist = np.array(cam["K"]), np.array(cam["dist"])
    h, w = img.shape[:2]
    newK, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 0)
    und = cv2.undistort(img, K, dist, None, newK)
    if cam.get("mount") == "tool":
        if p is None:
            sys.exit("camera on the tool: needs the robot pose (--robot or --pose)")
        T = pose_mat(p) @ np.array(cam["T_tool_cam"])
    elif cam.get("mount") == "fixed":
        T = np.array(cam["T_base_cam"])
    else:
        sys.exit("camera.json has no mount yet: run calibrate.py handeye (camera on the tool) or fixed")
    meta = {"source": "real", "w": w, "h": h, "K": newK.tolist(), "T_base_cam": T.tolist(), "pose": p,
            "camera": cam.get("updated"), "objects": {},
            "jig_model": (json.loads(Path(jigs_file or REAL_JIGS).read_text(encoding="utf-8"))
                          if Path(jigs_file or REAL_JIGS).exists() else None) if jig_model == "file" else jig_model}
    return und, meta


def live(a, cam):
    """A window: the camera with the jig markers it sees (q / Esc to close)."""
    cap = cv2.VideoCapture(a.cam, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(a.cam)
    det = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters())
    while True:
        ok, f = cap.read()
        if not ok:
            break
        c, ids, _ = det.detectMarkers(f)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(f, c, ids)
        cv2.putText(f, f"{0 if ids is None else len(ids)} jig markers  (q = quit)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("camera", f)
        if cv2.waitKey(30) & 0xFF in (ord("q"), 27):
            break
    cap.release(); cv2.destroyAllWindows()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["calib", "photo", "live"])
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--image")
    ap.add_argument("--robot", default="10.0.12.101")
    ap.add_argument("--pose", nargs=6, type=float)
    ap.add_argument("--no-robot", action="store_true")
    ap.add_argument("--camera", default=str(HERE / "camera.json"))
    ap.add_argument("--out", help="folder (default calib_shots/ or real_shots/)")
    ap.add_argument("--jigs", help="the set-up file (default tests/vision_lab/real_jigs.json from real_setup.py)")
    a = ap.parse_args()
    cam = json.loads(Path(a.camera).read_text()) if Path(a.camera).exists() else {}
    if a.cmd == "live":
        return live(a, cam)
    img, p = frame(a), pose(a)
    if a.cmd == "calib":
        j = write(Path(a.out or HERE / "calib_shots"), img, {"pose": p, "source": "real"})
    else:
        if "K" not in cam:
            sys.exit("no camera.json yet: calibrate first (calibrate.py intrinsics, then handeye or fixed)")
        und, meta = measuring_photo(img, p, cam, jigs_file=a.jigs)
        j = write(Path(a.out or HERE / "real_shots"), und, meta)
    print(j)


if __name__ == "__main__":
    main()
