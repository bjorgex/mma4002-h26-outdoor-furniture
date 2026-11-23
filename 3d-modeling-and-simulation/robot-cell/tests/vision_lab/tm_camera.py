"""The TM5's own camera instead of a webcam: TMflow's External Detection sends the camera image over HTTP to this
script, which saves it the same way as real_capture.py (calib -> calib_shots/, photo -> real_shots/, with the pose).
It only READS the robot (Modbus pose); it never moves it.

  python tests/vision_lab/tm_camera.py calib  [--port 6189]   # every image -> calibration photo (raw + pose)
  python tests/vision_lab/tm_camera.py photo  [--port 6189]   # every image -> measuring photo (undistorted + T_base_cam)
  options as real_capture.py: --robot 10.0.12.101 | --pose x y z rx ry rz | --camera camera.json | --out | --jigs

TMflow side (check in the lab; the exact menu depends on the TMflow version): a Vision job on the eye-in-hand
camera with an "External Detection" step, server = http://<laptop IP>:6189 . Techman's ROS driver uses the
same route: POST /api/<method>?... with the image as a multipart file. The format is NOT verified on our robot,
so this server takes any POST with an image (multipart or raw body) and logs every request to tm_camera.log -
read that log after the first try. Firewall: allow Python on the private network, or the robot can't connect.
Keep the robot STILL while the vision node runs (the pose is read when the image arrives).
"""
import argparse
import email.parser
import email.policy
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from real_capture import measuring_photo, modbus_pose, write  # noqa: E402

LOG = HERE / "tm_camera.log"


def log(line):
    print(line)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + line + "\n")


def image_from(body, ctype):
    """The image in a request: the first multipart part that decodes as an image, else the raw body."""
    blobs = []
    if ctype.lower().startswith("multipart/"):
        msg = email.parser.BytesParser(policy=email.policy.default).parsebytes(
            b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + body)
        for part in msg.iter_parts():
            data = part.get_payload(decode=True) or b""
            blobs.append((part.get_param("name", header="content-disposition"), part.get_filename(), data))
    blobs.append(("<body>", None, body))
    for name, fname, data in blobs:
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) if data else None
        if img is not None:
            return img, f"{name} {fname or ''}".strip()
    return None, ", ".join(f"{n}:{len(d)} B" for n, _, d in blobs)


def make_handler(a, cam):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def answer(self, obj, code=200):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            log(f"GET {self.path} from {self.client_address[0]}")
            self.answer({"message": "success", "result": None})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n)
            ctype = self.headers.get("Content-Type", "")
            log(f"POST {self.path} from {self.client_address[0]}: {n} B, {ctype}")
            img, where = image_from(body, ctype)
            if img is None:
                log(f"  no image found ({where})")
                return self.answer({"message": "no image", "result": None}, 400)
            try:
                p = list(a.pose) if a.pose else modbus_pose(a.robot)
                if a.cmd == "calib":
                    j = write(Path(a.out or HERE / "calib_shots"), img, {"pose": p, "source": "tm"})
                else:
                    und, meta = measuring_photo(img, p, cam, jigs_file=a.jigs)
                    meta["source"] = "tm"
                    j = write(Path(a.out or HERE / "real_shots"), und, meta)
            except (Exception, SystemExit) as e:          # measuring_photo exits on a missing calibration
                log(f"  failed: {e}")
                return self.answer({"message": str(e), "result": None}, 500)
            log(f"  image {img.shape[1]}x{img.shape[0]} ({where}), pose {p} -> {j}")
            # TMflow's External Detection needs at least one object back, or the job fails ("make sure your object
            # is detectable") and can't be saved. Answer with the OMRON/TM landmark(s) found in the raw image
            # (landmark.py), in the box format of Techman's external-detection examples. Format not confirmed on
            # TMflow 1.88: the answer is logged, so check TMflow's result against it.
            ann = []
            try:
                from landmark import find_landmarks
                for m in find_landmarks(img):
                    c = m["corners"]
                    up = c[0] - c[3]
                    ann.append({"box_cx": round(float(m["centre"][0]), 1), "box_cy": round(float(m["centre"][1]), 1),
                                "box_w": round(float(np.linalg.norm(c[1] - c[0])), 1),
                                "box_h": round(float(np.linalg.norm(c[3] - c[0])), 1),
                                "label": "landmark", "score": round(min(1.0, 0.5 + m["turn_score"]), 3),
                                "rotation": round(float(np.degrees(np.arctan2(up[0], -up[1]))), 2)})
            except Exception as e:
                log(f"  landmark reader failed: {e}")
            reply = {"message": "success", "result": None, "annotations": ann}
            log(f"  answer: {json.dumps(reply)}")
            self.answer(reply)
    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["calib", "photo"])
    ap.add_argument("--port", type=int, default=6189)
    ap.add_argument("--robot", default="10.0.12.101")
    ap.add_argument("--pose", nargs=6, type=float)
    ap.add_argument("--camera", default=str(HERE / "camera.json"))
    ap.add_argument("--out")
    ap.add_argument("--jigs")
    a = ap.parse_args()
    cam = json.loads(Path(a.camera).read_text()) if Path(a.camera).exists() else {}
    if a.cmd == "photo" and "K" not in cam:
        sys.exit("no camera.json yet: calibrate first (calibrate.py intrinsics, then handeye)")
    srv = ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(a, cam))
    log(f"waiting for TMflow images on port {a.port} ({a.cmd}); Ctrl+C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
