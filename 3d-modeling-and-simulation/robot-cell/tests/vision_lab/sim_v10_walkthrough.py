"""The lab procedure, step by step, on the simulated robot - and the result as program v10.

  1 board flat on the EMPTY plate (jigs out, as for TMflow's calibration)   2 15 calibration photos (the robot jogs to each pose)   3 lens + hand-eye -> camera.json
  4 taught layout: 2 photos -> real_jigs.json          5 the jigs are moved (as if re-bolted in the T-slots)
  6 2 photos -> jig_vision.py -> moves.json            7 bench_cell_v10.py -> tests/v10_moves.json
  8 v9 vs v10 against the moved jigs: tool-tip error at every grip and place, collision.py with the jigs shifted
Pictures of every step (robot overview + what the camera saw) -> results/walkthrough_<stamp>/pics/, used by the report.

Needs the mock (tests/tmflow_mock.py serve --sim). Starts the headless renderer and a second headless tab for the
overview pictures. Leaves the jigs MOVED, so "v10-full" (and "v9-full", for comparison) can be run on the page.
  python tests/vision_lab/sim_v10_walkthrough.py [--reset]      --reset: the jigs back to CAD at the end
"""
import argparse
import base64
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
CELL_DIR = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "robot_sim")); sys.path.insert(0, str(CELL_DIR))
import calibrate  # noqa: E402
import jig_vision as jv  # noqa: E402
import real_capture  # noqa: E402
import real_setup  # noqa: E402
import renderer  # noqa: E402
import tm5_kin  # noqa: E402
from calibrate_test import aim, go, post, snap  # noqa: E402
from jig_vision_test import POSES, follow  # noqa: E402

# the test layout: jigs re-bolted a few mm off (translations only: the T-slots keep them square)
LAYOUT = {"Base A": (10, 8), "Base B": (-12, -9), "Plank rack": (8, 10)}
ON_B = ["Guide small", "Guide big"]
BOARD_C = [-365, 7, -1.4]                             # centre of the EMPTY T-slot plate (top z -4.4), board 3 mm thick
TILTS = [(0, 0, 0), (15, 0, 0), (-15, 0, 0), (0, 15, 0), (0, -15, 0), (10, 10, 30), (-10, 10, -30), (10, -10, -30),
         (-10, -10, 30), (20, 0, 20), (-20, 0, -20), (0, 20, -40), (0, -20, 40), (12, -12, 0), (-12, 12, 0)]
PY = sys.executable
# the steps on the page (its step list + progress bar), as a preset run shows them; the same /step events v4_replay sends
PHASES = [("calibration_board", "Calibration: jigs out, board flat on the empty plate"),
          ("calibration_photos", "Calibration: 15 photos, board still, robot tilted"),
          ("lens_and_hand_eye", "Calibration: lens + hand-eye -> camera.json"),
          ("taught_layout", "Jigs back in: taught-layout photos -> real_jigs.json"),
          ("move_jigs", "Jigs moved a few mm (as if re-bolted)"),
          ("measure_jigs", "Measure: 2 photos -> jig moves (moves.json)"),
          ("build_v10", "Build V10 from the measured moves"),
          ("v9_vs_v10", "V9 vs V10 at the same grips"),
          ("v10_stages", "V10: one pose per stage")]
PH = {"k": 0}


def step_event(ev):
    try:
        req = urllib.request.Request("http://127.0.0.1:8090/step", json.dumps(ev).encode(), {"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3).close()
    except OSError:
        pass


def phase(k):
    if PH["k"]:
        step_event({"t": "done", "n": PH["k"], "fn": PHASES[PH["k"] - 1][0]})
    PH["k"] = k
    if k:
        fn, what = PHASES[k - 1]
        step_event({"t": "step", "n": k, "fn": fn, "args": [], "what": what})
        print(f"step {k}/{len(PHASES)}: {what}", flush=True)


# ---- a second headless tab for overview pictures (the renderer tab only renders photos) ------------------------
class Overview:
    def __init__(self):
        req = urllib.request.Request(f"http://127.0.0.1:{renderer.PORT}/json/new?http://127.0.0.1:8090/all", method="PUT")
        self.p = json.loads(urllib.request.urlopen(req, timeout=10).read())
        self.id = 0
        t0 = time.time()
        while time.time() - t0 < 60:
            try:
                if self.js("!!(window.__sim && window.__sim.camera && window.__sim.jigs && window.__sim.jigs.model())"):
                    break
            except Exception:
                pass
            time.sleep(1)
        self.hide()

    def hide(self):                                    # panels drawn over the 3D view: not in the pictures
        self.js("(()=>{const s=window.__sim, c=s.canvas, el=c.parentElement;"
                "[...el.children].forEach(e=>{if(e!==c)e.style.visibility='hidden'});"
                "document.querySelectorAll('.vis-panel,.jig-panel,.vis-pip-label').forEach(e=>e.style.visibility='hidden');"
                "s.manip?.videoLayers?.('hide');"                       # manipulability map, path + labels off
                "el.style.cssText+=';position:fixed;left:0;top:0;width:1200px;height:900px;z-index:99999;background:#fff';"
                "window.dispatchEvent(new Event('resize')); return 1})()")

    def call(self, method, params, timeout=60):
        import websocket
        ws = websocket.create_connection(self.p["webSocketDebuggerUrl"], timeout=timeout)
        try:
            self.id += 1
            ws.send(json.dumps({"id": self.id, "method": method, "params": params}))
            while True:
                m = json.loads(ws.recv())
                if m.get("id") == self.id:
                    return m.get("result", {})
        finally:
            ws.close()

    def js(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        return r.get("result", {}).get("value")

    def shot(self, path, eye, target, wait=1.5):
        """The 3D canvas only, seen from eye looking at target (robot base mm)."""
        self.js(f"(()=>{{const s=window.__sim; s.camera.position.set({eye[0]},{eye[1]},{eye[2]}); "
                f"s.controls.target.set({target[0]},{target[1]},{target[2]}); s.controls.update(); return 1}})()")
        time.sleep(wait)
        r = self.js("(()=>{const b=window.__sim.canvas.getBoundingClientRect(); return [b.x,b.y,b.width,b.height]})()")
        img = self.call("Page.captureScreenshot", {"format": "png", "clip": {"x": r[0], "y": r[1], "width": r[2],
                                                                              "height": r[3], "scale": 1}})
        Path(path).write_bytes(base64.b64decode(img["data"]))
        return path

    def close(self):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{renderer.PORT}/json/close/{self.p['id']}", timeout=5)
        except OSError:
            pass


ISO = ([60, -780, 640], [-390, 0, 120])               # whole cell, from the front right
TOPV = ([-380, 5, 900], [-380, 6, 0])                 # straight down on the plate
CLOSE = lambda c: ([c[0] + 170, c[1] - 280, c[2] + 210], c)      # noqa: E731  a close-up of point c


def label(img, text, sub=None):
    img = img.copy()
    cv2.rectangle(img, (0, 0), (img.shape[1], 44 if not sub else 74), (255, 255, 255), -1)
    cv2.putText(img, text, (14, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (30, 30, 30), 2, cv2.LINE_AA)
    if sub:
        cv2.putText(img, sub, (14, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90, 90, 90), 1, cv2.LINE_AA)
    return img


def grid(paths, out, cols, w=640):
    ims = []
    for p in paths:
        im = cv2.imread(str(p)) if not isinstance(p, np.ndarray) else p
        ims.append(cv2.resize(im, (w, int(im.shape[0] * w / im.shape[1]))))
    h = max(i.shape[0] for i in ims)
    ims = [cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims]
    while len(ims) % cols:
        ims.append(np.full_like(ims[0], 255))
    rows = [cv2.hconcat([cv2.copyMakeBorder(i, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                         for i in ims[r:r + cols]]) for r in range(0, len(ims), cols)]
    cv2.imwrite(str(out), cv2.vconcat(rows))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--collision", action="store_true", help="also collision.py for v9 and v10 (about 20 min each)")
    a = ap.parse_args()
    out = HERE / "results" / ("walkthrough_" + time.strftime("%Y%m%d-%H%M%S"))
    pics, shots, real = out / "pics", out / "he_shots", out / "real_shots"
    for d in (pics, shots, real):
        d.mkdir(parents=True)
    log = {"layout": LAYOUT}
    renderer.start()
    ov = Overview()
    try:
        # 1 board on the table, markers off, jigs where taught
        mode = lambda name, step, empty=False: post("/vision/mode", {"name": name, "step": step, "empty": empty,  # noqa: E731
                                                                      "phase": PH["k"]})
        step_event({"t": "plan", "steps": [{"fn": f, "args": [], "what": w} for f, w in PHASES]})
        phase(1)
        mode("Camera calibration", "1 &nbsp;Empty plate, board flat on it", True)
        post("/vision/markers", {"on": False}); post("/vision/jigs/set", {"reset": True})
        post("/vision/board", {"on": True, "pose": BOARD_C + [12]})
        go(POSES["top"])
        cv2.imwrite(str(pics / "s1_board.png"), label(cv2.imread(str(ov.shot(pics / "_s1.png", *ISO))),
                                                      "1  Jigs out, calibration board flat on the empty plate"))

        # 2 calibration photos from 15 wrist poses
        phase(2)
        cams, robots, n = [], [], 0
        for k, (ax, ay, az) in enumerate(TILTS):
            mode("Camera calibration", f"2 &nbsp;Photo {k + 1} of {len(TILTS)}: board still, robot tilted", True)
            if not go(aim(BOARD_C, 180 + ax, ay, -180 + az, 380 + 15 * (k % 5))):
                continue
            j, meta = snap()
            pose = tm5_kin.mat_to_pose(meta["T_base_flange"])
            shutil.copy(j.with_suffix(".png"), shots / f"{k:02d}.png")
            (shots / f"{k:02d}.json").write_text(json.dumps({"pose": pose, "truth": meta}), encoding="utf-8")
            n += 1
            if k in (0, 1, 5, 9, 12, 14):
                img = cv2.imread(str(j.with_suffix(".png")))
                d = calibrate.detect(img)
                if d is not None:
                    for u, v in d[1]:
                        cv2.circle(img, (int(round(u)), int(round(v))), 7, (0, 200, 0), 2)
                txt = f"pose {k + 1}: rx {ax:+d}  ry {ay:+d}  rz {az:+d} deg"
                cams.append(label(img, txt, f"{0 if d is None else len(d[1])} board corners found"))
                c = BOARD_C
                robots.append(label(cv2.imread(str(ov.shot(pics / f"_r{k}.png", [c[0] + 380, c[1] - 560, c[2] + 420],
                                                           [c[0], c[1], c[2] + 200], 1.0))), txt))
        grid(robots, pics / "s2_poses_robot.png", 3)
        grid(cams, pics / "s2_poses_camera.png", 3)
        log["calib_photos"] = n

        # 3 lens + hand-eye
        phase(3)
        mode("Camera calibration", "3 &nbsp;Lens + hand-eye calibration", True)
        cam = calibrate.intrinsics(shots)
        cam.update(calibrate.handeye(shots, cam))
        truth = json.loads((shots / "00.json").read_text())["truth"]
        T_true = np.linalg.inv(np.array(truth["T_base_flange"])) @ np.array(truth["T_base_cam"])
        T = np.array(cam["T_tool_cam"])
        log["calib"] = {"rms_px": cam["rms_px"], "spread_mm": cam["handeye_spread_mm"],
                        "found_offset_mm": T[:3, 3].round(2).tolist(), "true_offset_mm": T_true[:3, 3].round(2).tolist(),
                        "pos_err_mm": float(np.linalg.norm(T[:3, 3] - T_true[:3, 3]))}
        (out / "camera.json").write_text(json.dumps(cam, indent=1))
        post("/vision/board", {"on": False})
        print("calibrated:", log["calib"])

        # 4 taught layout: markers on, overview + above-the-rack photos -> real_jigs.json
        phase(4)
        mode("Jig set-up", "4 &nbsp;Jigs back in, where the program was taught: taught-layout photos")
        post("/vision/markers", {"on": True}); post("/vision/jigs/set", {"reset": True})

        def measuring(name, jig_model):
            go(POSES[name])
            j, meta = snap()
            img = cv2.imread(str(j.with_suffix(".png")))
            und, m = real_capture.measuring_photo(img, tm5_kin.mat_to_pose(meta["T_base_flange"]), cam, jig_model=jig_model)
            m["objects"] = meta.get("objects", {})                       # sim truth, only for scoring and pictures
            return real_capture.write(real, und, m), meta

        taught = [measuring("top", None), measuring("rack", None)]
        ref_meta = taught[0][1]
        zs = [f"{n}={m['marker']['centre'][2]:.2f}" for n, m in ref_meta["jig_model"]["jigs"].items() if m.get("marker")]
        sys.argv = ["real_setup", *(str(t[0]) for t in taught), "--size", "22", "--out", str(out / "real_jigs.json")] \
            + sum((["--z", z] for z in zs), [])
        real_setup.main()
        jig_model = json.loads((out / "real_jigs.json").read_text())
        for t in taught:                                                 # the photos now with the marker model in them
            m = json.loads(t[0].read_text()); m["jig_model"] = jig_model; t[0].write_text(json.dumps(m, indent=1))
        tp = []
        for t, name in zip(taught, ("overview photo", "photo above the rack")):
            ph = jv.Photo(t[0])
            img = ph.img.copy()
            for n, r in jv.aruco(ph).items():
                if r.get("ok") and r.get("px"):
                    cv2.polylines(img, [np.round(np.array(r["px"]) - jv.HALF).astype(np.int32)], True, (0, 200, 0), 3)
                    cv2.putText(img, n, tuple(int(v) for v in np.array(r["px"]).mean(0) + [-40, -30]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 160, 0), 2, cv2.LINE_AA)
            tp.append(label(img, f"4  Taught layout: {name}", "markers found (green) -> where each jig was taught"))
        grid(tp, pics / "s4_taught.png", 2)
        go(POSES["top"])
        before = ov.shot(pics / "_before.png", *TOPV)

        # 5 move the jigs
        phase(5)
        mode("Jig measuring", "5 &nbsp;Jigs moved (as if re-bolted a few mm off)")
        model = ref_meta["jig_model"]["jigs"]
        offs = {n: {"x": x, "y": y, "z": 0, "rz": 0} for n, (x, y) in LAYOUT.items()}
        for g in ON_B:
            offs[g] = follow(offs["Base B"], model["Base B"]["pivot"], model[g]["pivot"])
        post("/vision/jigs/set", {"reset": True, "offsets": offs})
        time.sleep(1.5)
        after = ov.shot(pics / "_after.png", *TOPV)
        grid([label(cv2.imread(str(before)), "Taught layout"),
              label(cv2.imread(str(after)), "5  Jigs moved", "  ".join(f"{n} {x:+d}/{y:+d} mm" for n, (x, y) in LAYOUT.items()))],
             pics / "s5_moved.png", 2)

        phase(6)
        mode("Jig measuring", "6 &nbsp;Measuring photos: overview + above the rack")
        # 6 measure: two photos -> jig_vision.py -> moves.json
        meas = [measuring("top", jig_model)[0], measuring("rack", jig_model)[0]]
        moves = out / "moves.json"
        r = subprocess.run([PY, str(HERE / "jig_vision.py"), *map(str, meas), "--methods", "aruco", "--save", str(moves),
                            "--overlay"], capture_output=True, text=True)
        print(r.stdout[-1500:], r.stderr[-800:])
        ovl = [p.with_name(p.stem + "_aruco.png") for p in meas]
        grid([label(cv2.imread(str(p)), "6  Measured: " + w, "red = true place, green = found")
              for p, w in zip(ovl, ("overview", "above the rack")) if p.exists()], pics / "s6_measured.png", 2)
        found = json.loads(moves.read_text())["moves"]
        log["measured"] = {n: {"x": round(v["x"], 2), "y": round(v["y"], 2), "rz": round(v["rz"], 3)} for n, v in found.items()}
        log["measure_err_mm"] = {n: round(float(np.hypot(found[n]["x"] - LAYOUT[n][0], found[n]["y"] - LAYOUT[n][1])), 3)
                                 for n in LAYOUT if n in found}
        print("measured:", log["measured"], "error:", log["measure_err_mm"])

        # 7 v10
        phase(7)
        mode("V10", "7 &nbsp;Build V10 from the measured jig moves")
        import bench_cell_v10
        v10 = bench_cell_v10.build(moves)
        shutil.copy(moves, out / "moves_used_for_v10.json")

        phase(8)
        mode("V9 vs V10", "8 &nbsp;Same grips: V9 (taught points) vs V10 (moved with the jigs)")
        # 8 v9 vs v10 against the moved jigs: where the tool tip ends at each grip/place, relative to where it should
        v9 = json.loads(bench_cell_v10.SRC.read_text())["steps"]
        tip = bench_cell_v10.TIP
        rows = []
        for s9, s10 in zip(v9, v10["steps"]):
            if "move" not in s9 or not s10.get("jig"):
                continue
            want = np.array([*LAYOUT[s10["jig"]], 0])
            F9, F10 = (np.array(tm5_kin.pose_to_mat(s["flange"])) for s in (s9, s10))
            p9, p10 = ((F @ [0, 0, tip, 1])[:3] for F in (F9, F10))
            rows.append({"name": s9["name"], "jig": s10["jig"], "v9_err_mm": float(np.linalg.norm(want)),   # v9 stays put
                         "v10_err_mm": float(np.linalg.norm(p10 - (p9 + want)))})
        log["tip_err"] = {"moves": len(rows), "v9_max_mm": max(r["v9_err_mm"] for r in rows),
                          "v10_max_mm": max(r["v10_err_mm"] for r in rows),
                          "v10_median_mm": float(np.median([r["v10_err_mm"] for r in rows]))}
        print("tip error:", log["tip_err"])
        shift = []
        for n, o in json.loads(snap()[0].read_text())["objects"].items():   # every moved object, parts included
            T_m = np.array(o["T_move"])
            if np.linalg.norm(T_m[:3, 3]) > 0.01:
                shift += ["--shift", f"{n}:{T_m[0, 3]:.2f},{T_m[1, 3]:.2f},{T_m[2, 3]:.2f}"]
        log["collisions"] = {}
        for v in (("v9", "v10") if a.collision else ()):
            r = subprocess.run([PY, str(HERE.parent / "robot_sim" / "collision.py"), str(HERE.parent / f"{v}_moves.json"),
                                "--cell", str(HERE.parent / "robot_sim" / "cell_v9.glb"), "--parts", *shift],
                               capture_output=True, text=True, cwd=CELL_DIR)
            (out / f"collision_{v}.txt").write_text(r.stdout + r.stderr)
            log["collisions"][v] = (r.stdout.strip().splitlines() or ["?"])[-1]
            print(v, "collision.py:", log["collisions"][v])

        # pictures: the first plank pick, v9 vs v10, with the jigs moved
        names = [s["name"] for s in v10["steps"] if "move" in s]
        pick = next(n for n in names if n.endswith("pick") and n.startswith("plank"))
        place = next(n for n in names if n.startswith("plank") and n.endswith("place"))
        cmp_ = []
        for nm in (pick, place):
            for v, steps in (("v9", v9), ("v10", v10["steps"])):
                st = next(s for s in steps if s.get("name") == nm)
                above = list(st["flange"]); above[2] += 150
                go(above); go(st["flange"])
                F = np.array(tm5_kin.pose_to_mat(st["flange"]))
                c = (F @ [0, 0, tip, 1])[:3]
                jig = next(s for s in v10["steps"] if s.get("name") == nm)["jig"]
                ok = "on target" if v == "v10" else f"{np.linalg.norm(LAYOUT[jig]):.0f} mm off ({jig} was moved)"
                cmp_.append(label(cv2.imread(str(ov.shot(pics / f"_{v}_{nm}.png", *CLOSE(c)))), f"{v.upper()}  {nm}", ok))
                go(above)
        grid(cmp_, pics / "s8_v9_vs_v10.png", 2)

        phase(9)
        mode("V10", "9 &nbsp;One pose per stage")
        # robot movements of v10: one picture per stage (its first grip), whole cell
        stage_pics = []
        for stage in sorted({s["stage"] for s in v10["steps"] if "move" in s}):
            sts = [s for s in v10["steps"] if s.get("stage") == stage and "move" in s]
            st = next((s for s in sts if s["name"].endswith(("pick", "grip"))), sts[len(sts) // 2])
            go(st["flange"])
            stage_pics.append(label(cv2.imread(str(ov.shot(pics / f"_stage{stage}.png", *ISO))), f"Stage {stage}: {st['name']}"))
        grid(stage_pics, pics / "s9_v10_stages.png", 3)
        go(POSES["top"])
        phase(0)
    finally:
        try:
            post("/vision/mode", {"name": None}); post("/vision/board", {"on": False})
        except Exception:
            pass
        ov.close()
        renderer.stop()
        if a.reset:
            post("/vision/jigs/set", {"reset": True})
        for p in pics.glob("_*.png"):
            p.unlink()
    (out / "walkthrough.json").write_text(json.dumps(log, indent=1, default=float))
    print("results:", out)


if __name__ == "__main__":
    main()
