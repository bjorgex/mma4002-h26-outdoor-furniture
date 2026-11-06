"""Grip points taught on the real robot -> corrections the program builder applies (bench_cell_v8.py's Program.move).

    teach_v8.json (written by tests/robot_sim/teach.py, read here)

Each GRIP EVENT is the move just before a gripper grip/release ("plank2 pick", "guide small place", "bench down")
plus the moves that belong to it:
    approach  the moves straight above it, before it ("pick travel", "pick approach", "over place", "above guide")
    follow    the moves after it, up to the next event's approach or Home ("pick out", "pick up", "place out", "push",
              "lift off", the turn-over of the bench): they carry the part from where it really was
A taught grip is stored as a correction C in the grip's OWN TCP frame (tool x, y, z at the planned grip):
    T_taught = T_planned @ C
The grip pose is fixed to the part (base-local / rack-local / plank-local), so C is a part-local correction: it
stays right when a base is moved or turned on the plate. The approach and follow moves get the same physical shift
(their plate-frame offset to the grip is kept: "straight above" stays straight above), unless an approach was taught
itself (then its own C). Only translation by default; the rotation only if taught with --with-rotation.

    import teach_overrides
    T = teach_overrides.apply(name, T)          # plate-frame TCP pose in, corrected pose out (same object if none)
"""
import json
import math
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
ROT_SAME_DEG = 0.5          # an approach has the grip's orientation (within this)
LATERAL_MM = 1.0            # ... and lies on the vertical / the tool axis through the grip (within this)
_CACHE = {}


def path_for(version="v8"):
    """robot-cell/teach_<version>.json, or $TEACH_FILE (tests)."""
    return Path(os.environ["TEACH_FILE"]) if os.environ.get("TEACH_FILE") else HERE / f"teach_{version}.json"


# --- small pose helpers (4x4 numpy, TM [x, y, z, rx, ry, rz] with R = Rz Ry Rx, degrees)
def rpy_to_R(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def R_to_rpy(R):
    sy = math.hypot(R[0, 0], R[1, 0])
    if sy > 1e-9:
        v = (math.atan2(R[2, 1], R[2, 2]), math.atan2(-R[2, 0], sy), math.atan2(R[1, 0], R[0, 0]))
    else:
        v = (math.atan2(-R[1, 2], R[1, 1]), math.atan2(-R[2, 0], sy), 0.0)
    return [math.degrees(x) for x in v]


def pose_to_T(p):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = rpy_to_R(*p[3:6]), p[:3]
    return T


def T_to_pose(T):
    return [float(v) for v in T[:3, 3]] + R_to_rpy(T[:3, :3])


def rot_deg(R):
    """Rotation angle of R (atan2: exact for small angles too, where acos of the trace is not)."""
    s = np.linalg.norm([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / 2
    return math.degrees(math.atan2(s, (np.trace(R) - 1) / 2))


# --- the overrides file
def load(version="v8", path=None):
    """The overrides (empty if no file), re-read when the file changed."""
    p = Path(path) if path else path_for(version)
    if not p.exists():
        return {"version": version, "events": {}}
    key = (str(p), p.stat().st_mtime_ns)
    if key not in _CACHE:
        _CACHE.clear()
        _CACHE[key] = json.loads(p.read_text(encoding="utf-8"))
    return _CACHE[key]


def save(data, version="v8", path=None):
    p = Path(path) if path else path_for(version)
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    _CACHE.clear()


def _index(data):
    """move name -> (event, role, entry) for every move an event covers."""
    idx = {}
    for ev, e in data.get("events", {}).items():
        idx[e["grip"]] = (ev, "grip", e)
        for n in e.get("approach", []):
            idx.setdefault(n, (ev, "approach", e))
        for n in e.get("follow", []):
            idx.setdefault(n, (ev, "follow", e))
    return idx


def correction_T(c):
    """A stored correction {"xyz": [..] mm, "rpy": [..] deg (tool frame)} -> 4x4."""
    T = np.eye(4)
    T[:3, 3] = c["xyz"]
    if c.get("rpy"):
        T[:3, :3] = rpy_to_R(*c["rpy"])
    return T


def apply(name, T, version="v8", path=None):
    """Plate-frame TCP pose of move `name` with the taught correction (T itself if there is none)."""
    data = load(version, path)
    hit = _index(data).get(name)
    if hit is None:
        return T
    ev, role, e = hit
    own = e.get("taught", {}).get(name)                    # this very move taught (the grip, or an approach)
    if own:
        return T @ correction_T(own["correction"])
    grip = e.get("taught", {}).get(e["grip"])
    if grip is None:                                       # only the approach was taught: the rest as planned
        return T
    C = correction_T(grip["correction"])
    # the planned grip's orientation from this move's: R_g = R_move @ rel^T (rel = R_g^T R_move, stored per move)
    rel = np.array(e["rel"][name], float).reshape(3, 3)
    Rg = T[:3, :3] @ rel.T
    out = T.copy()
    out[:3, :3] = Rg @ C[:3, :3] @ Rg.T @ T[:3, :3]       # the grip's rotation correction, about this move's TCP
    out[:3, 3] = T[:3, 3] + Rg @ C[:3, 3]                  # the grip's shift, in plate coordinates
    return out


# --- what teach.py uses
def events_from_steps(steps, plate_T):
    """Grip events of a moves file. plate_T(step) -> the step's planned plate-frame TCP pose (4x4).
    -> {event name: {"grip", "kind" (grip|release), "approach": [...], "follow": [...], "rel": {name: 3x3}}}"""
    moves = [(i, s) for i, s in enumerate(steps) if "move" in s]
    pos = {i: k for k, (i, _) in enumerate(moves)}
    grips = []
    for i, s in enumerate(steps):
        if s.get("gripper") in ("grip", "release"):
            prev = [j for j, _ in moves if j < i]
            if prev:
                grips.append((prev[-1], s["gripper"]))
    out, claimed = {}, set()
    for gi, kind in grips:
        Tg = plate_T(steps[gi])
        k, appr = pos[gi] - 1, []
        while k >= 0:                                      # straight above, back to the first move that isn't
            j, s = moves[k]
            T = plate_T(s)
            d = T[:3, 3] - Tg[:3, 3]
            lat_z = math.hypot(d[0], d[1])
            lat_tool = np.linalg.norm(d - (d @ Tg[:3, 2]) * Tg[:3, 2])
            if s["name"] in claimed or rot_deg(Tg[:3, :3].T @ T[:3, :3]) > ROT_SAME_DEG or \
                    min(lat_z, lat_tool) > LATERAL_MM or np.linalg.norm(d) < 1e-6:
                break
            appr.insert(0, s["name"])
            k -= 1
        name = steps[gi]["name"]
        out[name] = {"grip": name, "kind": kind, "approach": appr, "follow": [], "rel": {}}
        claimed.update(appr + [name])
    grip_names = {e["grip"] for e in out.values()}
    approach_names = {n for e in out.values() for n in e["approach"]}
    for ev, e in out.items():                              # after it, up to the next event's moves (or Home)
        k = pos[[i for i, s in moves if s["name"] == e["grip"]][0]] + 1
        while k < len(moves):
            s = moves[k][1]
            if s["name"] in grip_names or s["name"] in approach_names or s["name"].lower().startswith("home"):
                break
            e["follow"].append(s["name"])
            k += 1
    for e in out.values():
        Rg = plate_T(steps[[i for i, s in moves if s["name"] == e["grip"]][0]])[:3, :3]
        for n in e["approach"] + e["follow"]:
            s = next(s for _, s in moves if s["name"] == n)
            e["rel"][n] = [round(float(v), 9) for v in (Rg.T @ plate_T(s)[:3, :3]).ravel()]
    return out


def correction_from(T_plan, T_taught, with_rotation=False):
    """Tool-frame correction C (T_taught = T_plan @ C); translation only unless with_rotation."""
    C = np.linalg.inv(T_plan) @ T_taught
    out = {"xyz": [round(float(v), 4) for v in C[:3, 3]]}
    if with_rotation:
        out["rpy"] = [round(v, 4) for v in R_to_rpy(C[:3, :3])]
    return out


def record(data, events, name, T_plan, T_taught, flange, joints, with_rotation=False):
    """Store a taught pose for move `name` (a grip or an approach); refreshes every event's move lists."""
    ev = next((k for k, e in events.items() if name == e["grip"] or name in e["approach"]), None)
    if ev is None:
        raise KeyError(f"'{name}' is not a grip or approach move (see --list)")
    old = data.get("events", {})
    data["events"] = {}
    for k, e in events.items():                            # move lists from the current program, taught kept
        data["events"][k] = dict(e, taught=old.get(k, {}).get("taught", {}))
    C = correction_from(T_plan, T_taught, with_rotation)
    d_plate = (T_taught[:3, 3] - T_plan[:3, 3]).round(3).tolist()
    data["events"][ev]["taught"][name] = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"), "correction": C, "plate_delta_mm": d_plate,
        "rot_change_deg": round(rot_deg(T_plan[:3, :3].T @ T_taught[:3, :3]), 3), "with_rotation": with_rotation,
        "planned_tcp_plate": [round(v, 4) for v in T_to_pose(T_plan)],
        "taught_tcp_plate": [round(v, 4) for v in T_to_pose(T_taught)],
        "robot_flange": [round(v, 4) for v in flange], "robot_joints": [round(v, 4) for v in joints]}
    return ev, C, d_plate
