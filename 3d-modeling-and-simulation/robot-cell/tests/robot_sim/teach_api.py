"""The 3D page's "Adjust step" panel (manip_layers.js), served by tmflow_mock.py / demo_viewer.py:

    POST /teach/preview  {"version": "v8", "move": "<move name>", "d": [dx, dy, dz, drx, dry, drz]}
        -> {"ok", "joints", "flange", "msg"}: the move's flange nudged by d - mm along the robot base axes, degrees
           about the base axes through the fingertips (as step_run.py's x/y/z and rx/ry/rz) - and the joints for it
    POST /teach/save     same body
        -> stores that pose as the move's taught pose (teach_overrides.record, with rotation - as teach.py / step_run's
           "save" do from the real robot), rebuilds the program (teach.py --rebuild) and refreshes the 3D page's path
           data (joints, durations, grips of manip_data.json; the mu1 values follow with manipulability.py all)

Only grips and their approach moves can be taught (teach_overrides events); others get a message saying so.
Nothing here talks to a robot.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CELL = HERE.parents[1]
for p in (str(CELL), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import teach_overrides as TO                              # noqa: E402
import tm5_kin as K                                       # noqa: E402

TIP = 160.0                                               # flange -> fingertips [mm]
JOINT_SPEED = 50.0                                        # deg/s, as v4_replay.py (durations for the timeline)


def _rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]), "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axis]


def nudged(flange, d):
    """The flange pose moved by d = [dx, dy, dz] mm (robot base axes) and turned by [drx, dry, drz] deg about the base
    axes through the fingertips (rx first, then ry, then rz)."""
    T = TO.pose_to_T(list(flange))
    p = T[:3, 3] + TIP * T[:3, 2]                         # the fingertips: they stay put when only turning
    R = _rot("z", d[5]) @ _rot("y", d[4]) @ _rot("x", d[3])
    out = np.eye(4)
    out[:3, :3] = R @ T[:3, :3]
    out[:3, 3] = R @ (T[:3, 3] - p) + p + np.asarray(d[:3], float)
    return TO.T_to_pose(out)


def nudged_ops(flange, ops):
    """The flange pose after a list of jog steps, in order, as the page's Adjust panel sends them:
    {"frame": "base" | "tool", "axis": "x" | "y" | "z" | "rx" | "ry" | "rz", "v": mm or deg}.
    base: along / about the robot base axes; tool: along / about the gripper's own axes (z along the gripper, x the
    fingers' closing direction). Turns are always about the fingertips (they stay put)."""
    T = TO.pose_to_T(list(flange))
    for op in ops or []:
        ax, v, fr = str(op.get("axis", "x")), float(op.get("v", 0)), str(op.get("frame", "base"))
        tipT = T[:3, 3] + TIP * T[:3, 2]
        if ax in ("x", "y", "z"):
            u = np.eye(3)["xyz".index(ax)]
            T[:3, 3] += (T[:3, :3] @ u if fr == "tool" else u) * v
        else:
            R = _rot(ax[1], v)
            R = T[:3, :3] @ R @ T[:3, :3].T if fr == "tool" else R     # about the tool's own axis, in base terms
            T[:3, :3] = R @ T[:3, :3]
            T[:3, 3] = R @ (T[:3, 3] - tipT) + tipT
    return TO.T_to_pose(T)


def _program(version):
    import teach                                          # tests/robot_sim/teach.py (program(), as the CLI uses)
    return teach.program(version)


def _step(steps, name):
    return next((s for s in steps if s.get("name") == name and "move" in s), None)


def _pose(flange, d, ops, start=None):
    """start: an absolute flange pose to begin from (the page's history), else the move's own pose."""
    base = list(start) if start else flange
    return nudged_ops(base, ops) if (ops or start) else nudged(flange, d)


def preview(version, name, d, ops=None, start=None):
    steps = json.loads((CELL / "tests" / f"{version}_moves.json").read_text(encoding="utf-8"))["steps"]
    s = _step(steps, name)
    if s is None:
        return 404, {"ok": False, "msg": f"no move '{name}' in {version}_moves.json"}
    f = _pose(s["flange"], d, ops, start)
    q = K.ik(f, s["joints"])
    if q is None:
        return 200, {"ok": False, "flange": f, "msg": "out of reach (or past a joint limit) at this offset"}
    return 200, {"ok": True, "joints": [round(v, 4) for v in q], "flange": [round(v, 4) for v in f], "msg": "ok"}


def save(version, name, d, ops=None, start=None):
    B, steps, flange_to_plate, plate_T, moves_file = _program(version)
    events = TO.events_from_steps(steps, plate_T)
    s = _step(steps, name)
    if s is None:
        return 404, {"ok": False, "msg": f"no move '{name}'"}
    if not any(name == e["grip"] or name in e["approach"] for e in events.values()):
        teachable = sorted({n for e in events.values() for n in [e["grip"], *e["approach"]]})
        return 400, {"ok": False, "msg": f"'{name}' can't be saved on its own: only a grip / place or the moves just "
                                         f"before one (approach) can. Go to the grip of this part and adjust there.",
                     "teachable": teachable}
    f = _pose(s["flange"], d, ops, start)
    q = K.ik(f, s["joints"])
    if q is None:
        return 200, {"ok": False, "msg": "out of reach at this offset: not saved"}
    data = TO.load(version)
    ev, C, dp = TO.record(data, events, name, plate_T(s), flange_to_plate(f), f, q, with_rotation=True)
    TO.save(data, version)
    r = subprocess.run([sys.executable, str(HERE / "teach.py"), version, "--rebuild"], cwd=CELL,
                       capture_output=True, text=True)
    if r.returncode:
        return 500, {"ok": False, "msg": "saved, but the rebuild failed: " + (r.stdout + r.stderr)[-400:]}
    n = refresh_path_data(version)
    return 200, {"ok": True, "msg": f"saved '{name}': plate shift {[round(v, 1) for v in dp]} mm, "
                                    f"program rebuilt, {n} path points refreshed", "event": ev}


def refresh_path_data(version):
    """manip_data.json's program points for this version: joints, durations, grips from the rebuilt moves file (fast;
    the mu1 numbers stay until manipulability.py all runs again)."""
    p = HERE / "manipulability" / "manip_data.json"
    if not p.exists():
        return 0
    D = json.loads(p.read_text(encoding="utf-8"))
    steps = json.loads((CELL / "tests" / f"{version}_moves.json").read_text(encoding="utf-8"))["steps"]
    key = next((k for k in D["programs"] if k.endswith(" " + version)), None)
    if not key:
        return 0
    by_name = {}
    for k, s in enumerate(steps):
        if "joints" in s:
            by_name.setdefault(s["name"], []).append(k)
    n, prev = 0, None
    seen = {}
    for t in D["programs"][key]:
        ks = by_name.get(t["name"], [])
        i = seen.get(t["name"], 0)
        if i >= len(ks):
            continue
        seen[t["name"]] = i + 1
        k = ks[i]
        s = steps[k]
        t["i"], t["q"] = k, [round(float(v), 3) for v in s["joints"]]
        if prev is None:
            t["dur"] = 0.0
        elif s.get("move") == "ptp":
            t["dur"] = round(max(abs(a - b) for a, b in zip(s["joints"], prev["joints"])) / JOINT_SPEED, 3)
        else:
            t["dur"] = round(math.dist(s["flange"][:3], prev["flange"][:3]) / max(float(s.get("speed", 100)), 1), 3)
        t.pop("grip", None); t.pop("grip_parts", None)
        for nxt in steps[k + 1:]:                         # the gripper acts here if it does before the next move
            if "joints" in nxt:
                break
            if nxt.get("gripper") in ("grip", "release"):
                t["grip"], t["grip_parts"] = nxt["gripper"], nxt.get("parts", [])
        prev, n = s, n + 1
    p.write_text(json.dumps(D, separators=(",", ":")), encoding="utf-8")
    return n


def handle(path, body):
    version = str(body.get("version", "v8"))
    name = str(body.get("move", ""))
    d = [float(x) for x in (body.get("d") or [0] * 6)][:6] + [0.0] * max(0, 6 - len(body.get("d") or []))
    ops = body.get("ops") or None
    start = body.get("flange") or None                    # an absolute pose from the page's history
    if path == "/teach/preview":
        return preview(version, name, d, ops, start)
    if path == "/teach/save":
        return save(version, name, d, ops, start)
    return 404, {"ok": False, "msg": "unknown /teach/ call"}
