"""/vision/* for the mock's view server (tmflow_mock.py): the 3D page's tool camera and jig mover (vision_layer.js).

POST /vision/snap     {png: data URL, meta: {...}, id?}  -> saves tests/vision_lab/sim_shots/<stamp>.png + .json
POST /vision/request  {renderer?}                                -> {id}; the page takes the photo (SSE "snap_request")
GET  /vision/result?id=<id>                               -> {path, json} once that photo is saved, 404 before
POST /vision/jigs     {cell, offsets, locks, truth}       -> tests/vision_lab/sim_jig_offsets.json (per cell)
POST /vision/jigs/set {offsets: {name: {x,y,z,rz}}, along?, reset?} -> the page moves those jigs (SSE "jig_set")
POST /vision/board    {on, pose: [x y z rz]}              -> the ChArUco calibration board on / off (SSE "board")
POST /vision/mode     {name, step, empty}                 -> a named mode on the page (banner; empty: jigs + parts hidden)
GET  /vision/mode                                           -> the current mode and board (a page loaded later applies them)
POST /vision/markers  {on}                                 -> ArUco markers on the jigs on / off (SSE "markers")
GET  /vision/pose                                         -> {flange, joints}: the mock's pose (Ethernet Slave 5891)
POST /vision/jog      {d: [dx dy dz drx dry drz], frame: "tool"|"base"} | {to: [x y z rx ry rz]}, speed?
      frame "tool": d along / about the tool's own axes (flange frame); "base" (default): robot base axes.
      Free move: one Line("CAP") through the mock's Listen node (5890), like tests/vision_lab/sim_camera.py.
      Only the arm moves - the program, the taught points and the sim's files are not touched.
POST /vision/history  {title, body, result: "ok"|"issue"}  -> appends one entry to config_history.md
GET  /vision/history                                       -> {md: the whole file's text}
      Written by the Spotlight Guide's "Review" step (tests/tmflow_all_view.html); a plain markdown log,
      newest entry first, so it reads like Next steps.md - not a database, just append + read the whole file.
"""
import base64
import json
import threading
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "vision_lab"
SHOTS = LAB / "sim_shots"
JIGS = LAB / "sim_jig_offsets.json"
HISTORY = LAB / "config_history.md"
_history_lock = threading.Lock()
_done, _lock = {}, threading.Lock()                     # request id -> saved paths
_jog = threading.Lock()
_state = {"mode": None, "board": {"on": False}}          # what a page loaded later must show
_want_renderer = set()                                  # request ids only the renderer page (/all?renderer) may answer


def handle(method, path, query, body, emit):
    """(code, json) for one /vision/ request. emit(t, **ev) sends an SSE event to the pages."""
    if method == "POST" and path == "/vision/snap":
        png = str(body.get("png", ""))
        if not png.startswith("data:image/png;base64,"):
            return 400, {"ok": False, "msg": "png must be a PNG data URL"}
        rid = body.get("id")
        with _lock:
            if rid and rid in _done:                    # another page already answered this request
                return 409, {"ok": False, "msg": "already taken by another page", **_done[rid]}
            if rid in _want_renderer and not body.get("renderer"):
                return 409, {"ok": False, "msg": "already taken: this request wants the renderer page (/all?renderer)"}
        SHOTS.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 1000:03d}"
        f = SHOTS / f"{stamp}.png"
        f.write_bytes(base64.b64decode(png.split(",", 1)[1]))
        meta = {**(body.get("meta") or {}), "image": f.name}
        if body.get("xyz"):                             # position pass: Float32 [x y z id] per pixel (half resolution)
            f.with_suffix(".xyz.f32").write_bytes(base64.b64decode(body["xyz"]))
            meta["xyz_file"] = f.with_suffix(".xyz.f32").name
        f.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        out = {"ok": True, "path": str(f), "json": str(f.with_suffix(".json"))}
        if rid:
            with _lock:
                _done.setdefault(rid, out)              # several pages open: the first photo counts
        return 200, out
    if method == "POST" and path == "/vision/request":
        rid = uuid.uuid4().hex[:12]
        if body.get("renderer"):
            _want_renderer.add(rid)
        emit("snap_request", id=rid, renderer=bool(body.get("renderer")), xyz=bool(body.get("xyz")))
        return 200, {"ok": True, "id": rid}
    if method == "GET" and path == "/vision/result":
        rid = (query.get("id") or [""])[0]
        with _lock:
            out = _done.get(rid)
        return (200, out) if out else (404, {"ok": False, "msg": "not yet (is the /all page open?)"})
    if method == "POST" and path == "/vision/jigs/set":    # a script moves jigs: the page applies it (SSE "jig_set")
        emit("jig_set", offsets=body.get("offsets") or {}, along=body.get("along", True), reset=bool(body.get("reset")))
        return 200, {"ok": True}
    if method == "POST" and path == "/vision/board":       # the ChArUco board on/off at a pose [x y z rz] (SSE "board")
        _state["board"] = {"on": bool(body.get("on")), "pose": body.get("pose")}
        emit("board", **_state["board"])
        return 200, {"ok": True}
    if method == "POST" and path == "/vision/mode":        # e.g. {"name": "Camera calibration", "step": "...", "empty": true}
        old, now = _state["mode"] or {}, time.time()
        _state["mode"] = ({"name": str(body["name"]), "step": str(body.get("step") or ""), "empty": bool(body.get("empty")),
                           "phase": body.get("phase"),
                           "t0": old["t0"] if old.get("name") == body["name"] else now,      # the mode's timer
                           "pt0": old["pt0"] if old and old.get("phase") == body.get("phase") else now}   # the step's
                          if body.get("name") else None)
        emit("mode", mode=_state["mode"])
        return 200, {"ok": True}
    if method == "GET" and path == "/vision/mode":
        return 200, _state
    if method == "POST" and path == "/vision/markers":
        emit("markers", on=bool(body.get("on")))
        return 200, {"ok": True}
    if method == "POST" and path == "/vision/jigs":
        cell = str(body.get("cell") or "cell")
        LAB.mkdir(parents=True, exist_ok=True)
        allc = json.loads(JIGS.read_text(encoding="utf-8")) if JIGS.exists() else {}
        allc[cell] = {"offsets": body.get("offsets") or {}, "locks": body.get("locks") or [], "truth": body.get("truth") or {},
                      "saved": time.strftime("%Y-%m-%d %H:%M:%S")}
        JIGS.write_text(json.dumps(allc, indent=1), encoding="utf-8")
        return 200, {"ok": True, "path": str(JIGS)}
    if path in ("/vision/pose", "/vision/jog"):
        import sys
        sys.path.insert(0, str(LAB))
        import sim_camera
        cur = sim_camera.current()
        if not cur:
            return 503, {"ok": False, "msg": "no pose from the mock (Ethernet Slave 5891)"}
        if path == "/vision/pose":
            return 200, {"ok": True, "joints": cur[0], "flange": cur[1]}
        if method != "POST":
            return 405, {"ok": False, "msg": "POST /vision/jog"}
        if body.get("to"):
            target = [float(v) for v in body["to"]]
        else:
            d = [float(v) for v in (body.get("d") or [0] * 6)]
            if body.get("frame") == "tool":             # along / about the tool's own axes: T_new = T x D
                import tm5_kin
                target = tm5_kin.mat_to_pose(tm5_kin.matmul(tm5_kin.pose_to_mat(cur[1]), tm5_kin.pose_to_mat(d)))
            else:                                       # robot base axes (rx ry rz added as angles)
                target = [a + b for a, b in zip(cur[1], d)]
        if len(target) != 6:
            return 400, {"ok": False, "msg": "6 values: x y z rx ry rz"}
        with _jog:                                      # one free move at a time
            try:
                L = sim_camera.Listen(5890)
                L.s.settimeout(30)
                L.move(target, float(body.get("speed", 50)), 15)
                L.s.close()
            except (OSError, RuntimeError) as e:        # not in the Listen node (a run going on?), unreachable, IK ...
                return 409, {"ok": False, "msg": f"move refused: {e}"}
        cur = sim_camera.current()
        return 200, {"ok": True, "joints": cur[0] if cur else None, "flange": cur[1] if cur else target}
    if method == "GET" and path == "/vision/history":
        return 200, {"ok": True, "md": HISTORY.read_text(encoding="utf-8") if HISTORY.exists() else ""}
    if method == "POST" and path == "/vision/history":
        title = str(body.get("title") or "Configuration attempt").strip()
        entry_body = str(body.get("body") or "").strip()
        result = "✅ ok" if body.get("result") != "issue" else "⚠️ issue"
        stamp = time.strftime("%Y-%m-%d %H:%M")
        entry = f"### {title}  ({stamp})\n**Result:** {result}\n\n{entry_body}\n\n---\n"
        with _history_lock:
            text = HISTORY.read_text(encoding="utf-8") if HISTORY.exists() else "# Vision/assembly configuration history\n\n---\n"
            marker = "---\n"
            i = text.find(marker)
            text = (text[:i + len(marker)] + "\n" + entry + text[i + len(marker):]) if i != -1 else text + "\n" + entry
            HISTORY.write_text(text, encoding="utf-8")
        return 200, {"ok": True}
    return 404, {"ok": False, "msg": f"no {method} {path}"}
