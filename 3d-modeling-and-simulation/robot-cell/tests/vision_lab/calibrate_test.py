"""The real-robot procedure, run in the sim with known answers: calibrate.py (intrinsics, hand-eye, fixed camera),
real_capture.py (measuring photos from a frame + pose), real_setup.py (taught layout) and jig_vision.py (ArUco), each
checked against the sim's truth. If this passes, the same scripts are ready for the webcam on the real cell.

Needs the mock (tests/tmflow_mock.py serve --sim); starts its own renderer.
  python tests/vision_lab/calibrate_test.py [--layouts 5]       -> results/calib_<stamp>/report.json + printed summary
"""
import argparse
import json
import math
import random
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "robot_sim"))
import calibrate  # noqa: E402
import jig_vision as jv  # noqa: E402
import real_capture  # noqa: E402
import real_setup  # noqa: E402
import renderer  # noqa: E402
import sim_camera  # noqa: E402
import tm5_kin  # noqa: E402
from jig_vision_test import POSES, ON_B, MOVED, follow  # noqa: E402

CAM_OFF = np.array([0, 75, 53.0])                       # only to aim the camera at the board when picking poses


def post(path, body):
    code, r = sim_camera.http("POST", path, body)
    if code != 200:
        raise RuntimeError(f"{path}: {code} {r}")
    return r


def snap():
    time.sleep(0.6)
    j = Path(sim_camera.snap(timeout=120, renderer=True)["json"])
    return j, json.loads(j.read_text())


def go(pose):
    code, r = sim_camera.http("POST", "/vision/jog", {"to": [float(v) for v in pose], "speed": 100})
    time.sleep(1.0)
    return code == 200


def aim(target, rx, ry, rz, d):
    """The flange pose that puts the camera d mm from target, looking at it, with that wrist orientation."""
    R = np.array(tm5_kin.pose_to_mat([0, 0, 0, rx, ry, rz]))[:3, :3]
    p = np.asarray(target) - d * R[:, 2] - R @ CAM_OFF
    return [*p, rx, ry, rz]


def table_err(T_est, T_true, K, w=1280, h=960, z=30.0):
    """What a camera-pose error does on the table: the same pixels' rays cut with the plane z (mm), worst difference."""
    us, vs = np.meshgrid(np.linspace(0, w, 9), np.linspace(0, h, 7))
    uv = np.c_[us.ravel(), vs.ravel(), np.ones(us.size)]
    out = []
    for T in (T_est, T_true):
        d = (T[:3, :3] @ (np.linalg.inv(K) @ uv.T)).T
        t = (z - T[2, 3]) / d[:, 2]
        out.append(T[:3, 3] + d * t[:, None])
    return float(np.linalg.norm(out[0] - out[1], axis=1).max())


def rot_deg(Ra, Rb):
    return math.degrees(math.acos(np.clip((np.trace(Ra.T @ Rb) - 1) / 2, -1, 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layouts", type=int, default=5)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = HERE / "results" / ("calib_" + time.strftime("%Y%m%d-%H%M%S")); out.mkdir(parents=True)
    shots = out / "calib_shots"; shots.mkdir()
    rep = {}
    renderer.start()
    post("/vision/markers", {"on": False}); post("/vision/jigs/set", {"reset": True})
    board_c = [-365, 7, 60]
    post("/vision/board", {"on": True, "pose": board_c + [12]})

    # 1. calibration photos: the board from 15 wrist poses (as you would jog the real robot)
    tilts = [(0, 0, 0), (15, 0, 0), (-15, 0, 0), (0, 15, 0), (0, -15, 0), (10, 10, 30), (-10, 10, -30), (10, -10, -30),
             (-10, -10, 30), (20, 0, 20), (-20, 0, -20), (0, 20, -40), (0, -20, 40), (12, -12, 0), (-12, 12, 0)]
    n = 0
    for k, (ax, ay, az) in enumerate(tilts):
        if not go(aim(board_c, 180 + ax, ay, -180 + az, 380 + 15 * (k % 5))):
            print(f"  pose {k}: not reachable - skipped"); continue
        j, meta = snap()
        T_bf = np.array(meta["T_base_flange"])
        tm = tm5_kin.mat_to_pose(T_bf.tolist())
        shutil.copy(j.with_suffix(".png"), shots / f"{k:02d}.png")
        (shots / f"{k:02d}.json").write_text(json.dumps({"pose": tm, "truth": meta}), encoding="utf-8")
        n += 1
    print(f"calibration photos: {n}")
    truth = json.loads((shots / "00.json").read_text())["truth"]
    K_true = np.array(truth["K"]); T_fc_true = np.linalg.inv(np.array(truth["T_base_flange"])) @ np.array(truth["T_base_cam"])

    # 2. intrinsics
    cam = calibrate.intrinsics(shots)
    K = np.array(cam["K"])
    rep["intrinsics"] = {"rms_px": cam["rms_px"], "fx_err_pct": 100 * (K[0, 0] / K_true[0, 0] - 1),
                         "fy_err_pct": 100 * (K[1, 1] / K_true[1, 1] - 1), "cx_err_px": K[0, 2] - K_true[0, 2],
                         "cy_err_px": K[1, 2] - K_true[1, 2], "dist": cam["dist"]}
    # 3. hand-eye (camera on the tool)
    cam.update(calibrate.handeye(shots, cam))
    T = np.array(cam["T_tool_cam"])
    rep["handeye"] = {"pos_err_mm": float(np.linalg.norm(T[:3, 3] - T_fc_true[:3, 3])), "rot_err_deg": rot_deg(T[:3, :3], T_fc_true[:3, :3]),
                      "found_offset_mm": T[:3, 3].round(2).tolist(), "true_offset_mm": T_fc_true[:3, 3].round(2).tolist(),
                      "spread_mm": cam["handeye_spread_mm"]}
    # 4. fixed camera: touch three board points (with 0.3 mm touch noise), one photo
    Tbb = np.array(truth["board"]["T_base_board"])
    nz = np.random.default_rng(a.seed)
    O, X, Y = Tbb[:3, 3], Tbb[:3, 3] + 150 * Tbb[:3, 0], Tbb[:3, 3] + 100 * Tbb[:3, 1]
    O, X, Y = (v + nz.normal(0, 0.3, 3) for v in (O, X, Y))
    fx = calibrate.fixed(shots / "00.png", cam, O, X, Y)
    Tf = np.array(fx["T_base_cam"]); Tt = np.array(truth["T_base_cam"])
    rep["fixed"] = {"pos_err_mm": float(np.linalg.norm(Tf[:3, 3] - Tt[:3, 3])), "rot_err_deg": rot_deg(Tf[:3, :3], Tt[:3, :3]),
                    "table_err_mm": table_err(Tf, Tt, K_true)}
    T_he = np.array(truth["T_base_flange"]) @ np.array(cam["T_tool_cam"])
    rep["handeye"]["table_err_mm"] = table_err(T_he, np.array(truth["T_base_cam"]), K_true)
    (out / "camera.json").write_text(json.dumps(cam, indent=1))
    post("/vision/board", {"on": False})

    # 5. the jig procedure with the calibrated camera: taught layout -> real_setup, then moved layouts -> jig_vision
    post("/vision/markers", {"on": True}); post("/vision/jigs/set", {"reset": True})
    real = out / "real_shots"; real.mkdir()

    def measuring(pose_name):
        go(POSES[pose_name])
        j, meta = snap()
        img = cv2.imread(str(j.with_suffix(".png")))
        pose = tm5_kin.mat_to_pose(meta["T_base_flange"])          # = what Modbus would give for the flange TCP
        und, m = real_capture.measuring_photo(img, pose, cam, jig_model=jig_model)
        m["objects"] = meta.get("objects", {})                  # sim truth, only for scoring
        return real_capture.write(real, und, m), meta

    jig_model = None
    setup = [measuring("top")[0], measuring("rack")[0]]
    ref_meta = snap()[1]                                   # markers' true heights from the sim's model
    zs = [f"{n}={m['marker']['centre'][2]:.2f}" for n, m in ref_meta["jig_model"]["jigs"].items() if m.get("marker")]
    sys.argv = ["real_setup", *map(str, setup), "--size", "22", "--out", str(out / "real_jigs.json")] + sum((["--z", z] for z in zs), [])
    real_setup.main()
    jig_model = json.loads((out / "real_jigs.json").read_text())

    errs = []
    model = ref_meta["jig_model"]["jigs"]
    for i in range(a.layouts):
        offs = {n: {"x": rng.uniform(-30, 30), "y": rng.uniform(-30, 30), "z": 0, "rz": rng.uniform(-10, 10)} for n in MOVED}
        for g in ON_B:
            offs[g] = follow(offs["Base B"], model["Base B"]["pivot"], model[g]["pivot"])
        post("/vision/jigs/set", {"reset": True, "offsets": offs})
        photos = [jv.Photo(measuring(p)[0]) for p in ("top", "rack")]
        best = {}
        for ph in photos:
            for n, r in jv.aruco(ph).items():
                if r.get("ok") and (n not in best or r["off_centre"] < best[n][0]["off_centre"]):
                    best[n] = (r, ph)
        for n in jv.JIGS:
            if n not in best:
                errs.append({"layout": i, "jig": n, "found": False}); continue
            r, ph = best[n]
            T_est = np.array(r["T_move"])
            T_true = np.array(ph.meta["objects"][n]["T_move"]) if n in ph.meta["objects"] else np.eye(4)
            c = np.array(jig_model["jigs"][n]["marker"]["centre"])
            far = c + [80, 60, 0]                                   # a point 100 mm from the marker (a grip point)
            e_c = np.linalg.norm(jv.move_point(T_est, c) - jv.move_point(T_true, c))
            e_f = np.linalg.norm(jv.move_point(T_est, far) - jv.move_point(T_true, far))
            a_est = math.degrees(math.atan2(T_est[1, 0], T_est[0, 0]))
            a_true = math.degrees(math.atan2(T_true[1, 0], T_true[0, 0]))
            da = abs((a_est - a_true + 180) % 360 - 180)
            errs.append({"layout": i, "jig": n, "found": True, "err_marker_mm": e_c, "err_100mm_away_mm": e_f, "rz_err_deg": da})
        print(f"layout {i + 1}/{a.layouts}")
    post("/vision/jigs/set", {"reset": True})
    f = [e for e in errs if e["found"]]
    rep["jigs"] = {"found": f"{len(f)}/{len(errs)}",
                   "err_marker_mm_median": float(np.median([e["err_marker_mm"] for e in f])),
                   "err_marker_mm_max": float(np.max([e["err_marker_mm"] for e in f])),
                   "err_100mm_away_mm_median": float(np.median([e["err_100mm_away_mm"] for e in f])),
                   "err_100mm_away_mm_max": float(np.max([e["err_100mm_away_mm"] for e in f])),
                   "rz_err_deg_median": float(np.median([e["rz_err_deg"] for e in f])),
                   "rz_err_deg_max": float(np.max([e["rz_err_deg"] for e in f])),
                   "per_jig": {n: f"{sum(1 for e in f if e['jig'] == n)}/{sum(1 for e in errs if e['jig'] == n)}" for n in jv.JIGS},
                   "rows": errs}
    (out / "report.json").write_text(json.dumps(rep, indent=1, default=float))
    print(json.dumps({k: v for k, v in rep.items() if k != "jigs"} | {"jigs": {k: v for k, v in rep["jigs"].items() if k != "rows"}}, indent=1, default=float))
    print("results:", out)


if __name__ == "__main__":
    main()
