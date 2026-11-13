"""Set up the real jig markers: where each marker is when the jigs stand in the TAUGHT layout (the layout the robot
program was taught in). jig_vision.py then measures every later photo against this: "Base A moved 3.2 mm in x and
turned 0.8 deg since teaching" - exactly the correction the taught points need.

  1. markers on the jigs (print_markers.py; ids 1-5 = Base A, Base B, Plank rack, Guide small, Guide big)
  2. the jigs in the taught layout; photo(s) with real_capture.py photo (overview + one straight above the rack)
  3. python tests/vision_lab/real_setup.py real_shots/<a>.json [real_shots/<b>.json] --size 30 \
         --z "Base A=36" --z "Base B=36" --z "Plank rack=97" --z "Guide small=57" --z "Guide big=57"
     -> real_jigs.json (real_capture.py puts it into every new photo)

--z: each marker's height (mm, robot base z of the marker's surface). Measure it: jog the TCP tip onto the marker's
centre and read Z (TMflow or `real_capture.py` prints the pose), or take the CAD height + tab thickness. Without --z
the height is estimated from the marker's size in the image (PnP) - quick, but a few mm off, and every mm of height
error moves the result by up to ~0.4 mm at the image edge. So measure it.
--pivot "Base A=x,y,z": the point whose move is reported (default: the marker's centre). Any point of the jig moves
with the same 4x4 (T_move in the output), so the pivot only changes which numbers are printed.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jig_vision as jv  # noqa: E402
from print_markers import JIG_IDS  # noqa: E402


def parse_kv(items, n):
    out = {}
    for s in items or []:
        k, v = s.split("=", 1)
        vals = [float(x) for x in v.split(",")]
        out[k.strip()] = vals[0] if n == 1 else vals
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", nargs="+")
    ap.add_argument("--size", type=float, default=30, help="black square of the printed markers, mm")
    ap.add_argument("--z", action="append", help='"<jig>=<marker height mm>"')
    ap.add_argument("--pivot", action="append", help='"<jig>=x,y,z"')
    ap.add_argument("--out", default=str(HERE / "real_jigs.json"))
    a = ap.parse_args()
    zs, pivots = parse_kv(a.z, 1), parse_kv(a.pivot, 3)
    s = a.size / 2
    local = np.array([[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]], np.float32)   # OpenCV's marker corner order
    jigs = {}
    for pj in a.photos:
        ph = jv.Photo(pj)
        det = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), jv.aruco_params())
        corners, ids, _ = det.detectMarkers(cv2.cvtColor(ph.img, cv2.COLOR_BGR2GRAY))
        if ids is None:
            continue
        for mid, c in zip(ids.ravel(), corners):
            name = JIG_IDS.get(int(mid))
            if not name or name in jigs:
                continue                                  # unknown id, or already found in an earlier photo
            px = c.reshape(4, 2) + jv.HALF
            if name in zs:
                z, src = zs[name], "given"
            else:                                         # PnP: the marker's pose from its known size
                ok, rvec, tvec = cv2.solvePnP(local, px.astype(np.float32), ph.K, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                z, src = float((ph.T @ np.r_[tvec.ravel(), 1.0])[2]), "estimated (PnP) - measure it and pass --z"
            cor = ph.ray_to_z(px, z)
            ctr = cor.mean(0)
            piv = pivots.get(name, ctr.tolist())
            jigs[name] = {"pivot": [float(v) for v in piv],
                          "box_min": [float(ctr[0] - 50), float(ctr[1] - 50), float(z - 40)],
                          "box_max": [float(ctr[0] + 50), float(ctr[1] + 50), float(z)],
                          "marker": {"id": int(mid), "size": a.size, "corners": cor.tolist(), "centre": ctr.tolist(),
                                     "z_source": src}, "photo": Path(pj).name}
            print(f"{name:12s} marker {mid} at x {ctr[0]:8.2f} y {ctr[1]:8.2f} z {z:7.2f}  ({src})")
    missing = [n for n in JIG_IDS.values() if n not in jigs]
    if missing:
        print("NOT seen:", ", ".join(missing), "- take another photo where they are visible and add it")
    out = {"jigs": jigs, "markers_visible": True, "marker_dict": "DICT_4X4_50", "set_up": time.strftime("%Y-%m-%d %H:%M"),
           "photos": [Path(p).name for p in a.photos]}
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("written:", a.out)


if __name__ == "__main__":
    main()
