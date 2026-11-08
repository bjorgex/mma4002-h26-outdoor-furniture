"""Collision check of a whole robot program in our own cell model, no RoboDK (trimesh + python-fcl).

    python tests/robot_sim/collision.py bench_tmflow/v7/AssembleBench.zip --cell v7
    python tests/robot_sim/collision.py tests/robot_sim/ref/v6_program.json --cell v6 --parts
    python tests/robot_sim/collision.py <program> --cell v7 --shift "Base B:0,-30,0"     test: a fixture moved
    python tests/robot_sim/collision.py <program> --cell tests/robot_sim/cell_v8.glb      any cell .glb (+ its layout json)
    options: --parts (also the parts check), --step 5 (coarser, faster), --list (every colliding move)

From Python (e.g. a cell builder that never had RoboDK):
    from collision import check_program
    hits = check_program("tests/v8_moves.json", "v8.glb")      # or a program dict, a step list, "v7", a layout json
    for h in hits: print(h["move"], h["check"], h["pairs"], h["context"])
    -> [] when free. Each hit: {"move": 1-based move number, "name", "check": "fixtures" | "parts",
        "pairs": [(a, b), ...], "context": "after '<gripper event>', before '<gripper event>'"}

Cell (cell_layout argument):
    "v6" / "v7"      the objects and poses bench_cell_v6/7.py's build() puts into RoboDK (constants imported, build()
                     not called): table + AMR boxes, the jig STLs (jig_parts/), the bench parts (benchV1_parts/,
                     assembly.json), all under "Ground base" = bench_layout.json's work frame * GROUND_IN_WORK
    a .glb           one node per object in robot base coordinates (cell_layout.py's cell_vN.glb); kinds from the
                     cell_layout*.json next to it with the same suffix, else from the names
    a layout .json   cell_layout_vN.json: its .glb (cell_vN.glb) is loaded
    a dict           {name: (kind, trimesh.Trimesh in robot base)}, kind "fixture" or "part"
Robot: Techman's link meshes (tm5_links.glb) on tm5_kin.py's joint frames (RoboDK's link lengths), the EGP gripper
as the builds' three boxes in flange coordinates (bench_cell_v7.EGP).
Path: each move sampled every `step` mm / deg as the robot drives it: PTP linear in joint space from the joints the
arm has to the stored ones, Line with the TCP straight and the joints followed from the move before (kin_check.py).

Checks, as bench_cell_v7.py does them in RoboDK:
    fixtures  = check(): robot links + gripper against the fixtures; parts left out (they touch on purpose). The AMR's
              LD-250 model is not in the cell (v7 switches it off as well).
    parts     = check_parts(), over the whole program: robot links + gripper against every part not held, carried
              parts against the other parts and the fixtures. Contact on purpose is allowed: gripper/robot with the
              parts of the next grip from the gripper event before it on (going in) and with the parts just released
              until the next gripper event (backing out). Carried parts are also checked against the robot's
              links (not the gripper, which holds them): a part turned into the arm is a hit. In the first two
              moves after a grip and the last two before the release, carried parts may only touch what they
              already touch at the grip / release pose (sliding out of a slot, setting down); anything new is a
              hit (2026-11-06: the old blanket skip hid a bench lifted up through the guide).
    spawn       a step {"spawn": {part: pose, ...}} (v8x2's reload: bench 2's parts) - those parts are absent before it
              (not in the parts check at all) and stand at their start poses in the cell from it on.
Exit code 1 if anything collides.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
CELL = HERE.parents[1]
sys.path.insert(0, str(HERE))
import kin_check as KC                                      # noqa: E402
import tm5_kin as K                                         # noqa: E402
from tmflow_export import load_program                      # noqa: E402

EGP = [((-47, -45, 0), (47, 45, 123)), ((-9, -4, 123), (-6, 4, 160)), ((6, -4, 123), (9, 4, 160))]   # bench_cell_v7
KIND = {"table": "fixture", "plate": "fixture", "jig": "fixture", "amr": "fixture", "fixture": "fixture",
        "frame": "part", "piece": "part", "plank": "part", "guide": "part", "part": "part", "marker": None}
_ROBOT = None                                               # link meshes, loaded once


def npm(m):
    """robomath.Mat -> 4x4 numpy."""
    return np.array([[m[i, j] for j in range(4)] for i in range(4)], dtype=float)


def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)])
    b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)])
    return b


# ------------------------------------------------------------------ cells
def cell_from_station(version):
    """{name: (kind, mesh in robot base)} at the program start, from bench_cell_<version>.py's constants."""
    import importlib
    from robodk.robomath import Mat, eye, pi, rotx, rotz, transl
    sys.path.insert(0, str(CELL))
    m = importlib.import_module(f"bench_cell_{version}")
    asm = {p["name"]: Mat(p["pose"]) for p in json.loads((m.PARTS / "assembly.json").read_text())["parts"]}
    G = npm(Mat(m.LAYOUT["work_frame"]) * m.GROUND_IN_WORK)
    sx, sy, st = m.GROUND_SIZE
    out = {}

    def add(name, kind, mesh, pose=None):
        mesh = mesh.copy()
        mesh.apply_transform(G @ npm(pose if pose is not None else eye(4)))
        out[name] = (kind, mesh)

    stl = lambda folder, n: trimesh.load_mesh(folder / f"{n}.stl")
    if hasattr(m, "WORK_PLATE"):                             # v7: Jig V2 on the robot's work plate
        wx0, wy0, wx1, wy1 = m.WORK_PLATE
        add("Table", "fixture", box((-350, wy0, -m.TABLE_H), (wx1, wy1, -st)))
        add("Ground base plate", "fixture", stl(m.JIG, "ground_base_v7"))
        add("Base A", "fixture", stl(m.JIG, "base_a_v7"), m.BASE_A)
        add("Base B", "fixture", stl(m.JIG, "base_b_v7"), m.BASE_B)
        add("Plank jig", "fixture", stl(m.JIG, "plank_rack_v7"), m.PLANK_JIG)
        guide, floor = ("guide_inner_v7", "guide_outer_v7"), getattr(m, "PLANK_FLOOR", 0)
    else:                                                    # v6
        add("Table", "fixture", box((-350, -10, -m.TABLE_H), (sx + 10, sy + 60, -st)))
        add("Ground base plate", "fixture", stl(m.JIG, "ground_base_split"))
        for name, base, f, riser in (("Base A", m.BASE_A, "base_a", m.RISER_A), ("Base B", m.BASE_B, "base_b", m.RISER_B)):
            add(f"{name} riser", "fixture", box((-90, -90, -riser), (90, 90, 0)), base)
            add(name, "fixture", stl(m.JIG, f), base)
        add("Plank jig", "fixture", stl(m.JIG, "plank_jig"), m.PLANK_JIG)
        guide, floor = ("guide_inner", "guide_outer"), 0
    add("AMR plate", "fixture", box((0, 0, -10), (m.AMR_PLATE[0], m.AMR_PLATE[1], 0)), m.AMR_AT)
    add("AMR top module", "fixture",
        box((40, 40, 383 - m.TABLE_H - st), (m.AMR_PLATE[0] - 40, m.AMR_PLATE[1] - 40, -10)), m.AMR_AT)
    frame, piece, plank = stl(m.PARTS, "frame"), stl(m.PARTS, "interface_piece"), stl(m.PARTS, "plank_body")
    add("frame1", "part", frame, m.BASE_A * m.T_IN * asm["frame1"])
    add("frame2", "part", frame, m.BASE_B * m.FLIP * m.T_IN * asm["frame2"])
    for k in range(1, 7):
        P = m.T_IN * asm[f"plank{k}"]
        add(f"piece A{k}", "part", piece, m.BASE_A * P)
        add(f"piece B{k}", "part", piece, m.BASE_B * m.FLIP * P * rotz(pi))
        row, col = divmod(k - 1, 3)
        start = m.PLANK_JIG * transl(m.PITCH * (col + 0.5), m.PITCH * (row + 0.5) + 2.5, 125 + floor) * rotx(pi / 2)
        add(f"plank{k}", "part", plank, start)
    add("Guide inner", "part", stl(m.JIG, guide[0]), m.BASE_A * m.GUIDE_ON_A)
    add("Guide outer", "part", stl(m.JIG, guide[1]), m.BASE_A * m.GUIDE_ON_A)
    return out


def cell_from_glb(glb, layout=None):
    """{name: (kind, mesh)} from a cell .glb (nodes in robot base coordinates, as cell_layout.py writes them)."""
    glb = Path(glb)
    if layout is None:                                       # cell_v5.glb -> cell_layout_v5.json, cell.glb -> cell_layout.json
        cand = glb.with_name(glb.name.replace("cell", "cell_layout", 1).replace(".glb", ".json"))
        layout = cand if cand.exists() else None
    kinds = {}
    if layout:
        kinds = {o["name"]: o.get("kind", "") for o in json.loads(Path(layout).read_text())["objects"]}
    scene = trimesh.load(glb)
    out = {}
    for node in scene.graph.nodes_geometry:
        T, g = scene.graph[node]
        kind = KIND.get(kinds.get(node, ""), None) if node in kinds else _guess_kind(node)
        if kind is None:
            continue
        mesh = scene.geometry[g].copy()
        mesh.apply_transform(T)
        out[node] = (kind, mesh)
    return out


def _guess_kind(name):
    n = name.lower()
    if "vision" in n or "marker" in n:
        return None
    return "part" if any(w in n for w in ("frame", "piece", "plank", "guide")) and "jig" not in n else "fixture"


def load_cell(cell_layout):
    if isinstance(cell_layout, dict):
        return cell_layout
    s = str(cell_layout)
    if s.endswith(".glb"):
        return cell_from_glb(s)
    if s.endswith(".json"):
        p = Path(s)
        return cell_from_glb(p.with_name(p.name.replace("cell_layout", "cell", 1).replace(".json", ".glb")), p)
    return cell_from_station(s)


# ------------------------------------------------------------------ robot + path
def robot_meshes():
    global _ROBOT
    if _ROBOT is None:
        scene = trimesh.load(HERE / "tm5_links.glb")
        links = []
        for i in range(7):
            T, g = scene.graph[f"link_{i}"]
            mesh = scene.geometry[g].copy()
            mesh.apply_transform(T)
            links.append(mesh)
        _ROBOT = links
    return _ROBOT


def robot_poses(q):
    fr = [np.array(f) for f in K.frames(q)]
    out = {"link_0": np.eye(4)}
    out.update({f"link_{i}": f for i, f in enumerate(fr, 1)})
    out["EGP"] = fr[-1]
    return out


def program_samples(program, step=2.0):
    """Per move (0-based): its joint samples as the robot drives it. Plus gripper events {move index: [steps]}
    (the events after that move; -1 = before the first)."""
    T = K.pose_to_mat(program.get("tcp", {}).get("pose", [0, 0, 160, 0, 0, 0]))
    per, events, qa, mi = [], {}, None, -1
    for s in program["steps"]:
        if "move" not in s:
            if s.get("gripper"):
                events.setdefault(mi, []).append(s)
            continue
        mi += 1
        q = list(s["joints"])
        if qa is None:
            path = [q]
        elif s["move"] == "ptp":
            path = KC.joint_path(qa, q, step)
        else:
            poses, _, _ = KC.line_poses(K.pose_to_mat(K.fk(qa)), K.pose_to_mat(s["flange"]), T, step, step)
            path, fail = KC.follow_line(qa, poses)
            if fail is not None:                             # kin_check reports it; carry on with the stored joints
                path = path + KC.joint_path(path[-1] if path else qa, q, step)
        per.append(path)
        qa = list(path[-1])
    return per, events


def _context(events, mi):
    flat = sorted((k, s) for k, v in events.items() for s in v)
    before = [s for k, s in flat if k < mi]
    after = [s for k, s in flat if k >= mi]
    f = lambda s: f"{'attach' if s['gripper'] == 'grip' else 'release'} {', '.join(s['parts'][:2])}" + \
        (f" +{len(s['parts']) - 2}" if len(s["parts"]) > 2 else "")
    return f"after '{f(before[-1]) if before else 'start'}', before '{f(after[0]) if after else 'end'}'"


def _manager(objs):
    m = trimesh.collision.CollisionManager()
    for name, mesh in objs.items():
        m.add_object(name, mesh)
    return m


def egp_at_gap(gap, egp=EGP):
    """The gripper boxes with the two fingers (egp[1], egp[2]: same size, mirrored about tool x = 0) moved so their
    inner faces are `gap` mm apart (body unchanged)."""
    body, (lo1, hi1), (lo2, hi2) = egp[0], egp[1], egp[2]
    t = hi1[0] - lo1[0]                                     # finger thickness along the closing direction
    h = gap / 2
    return [body, ((-h - t, lo1[1], lo1[2]), (-h, hi1[1], hi1[2])), ((h, lo2[1], lo2[2]), (h + t, hi2[1], hi2[2]))]


# ------------------------------------------------------------------ the check
def check_program(moves, cell_layout="v7", step=2.0, parts=False, shift=None, egp=EGP, clearance=None):
    """Collisions of a program (program dict, step list, or a path: zip / program json / moves json) in a cell
    (see the module docstring). Returns a list of hits (empty = free). `shift` {object: (dx, dy, dz)} moves objects
    (robot base axes) first; `clearance` (a dict) gets the smallest robot/gripper-fixture distance per free move."""
    if isinstance(moves, (str, Path)):
        moves = load_program(moves)
    elif isinstance(moves, list):
        moves = {"steps": moves}
    cell = dict(load_cell(cell_layout))
    for name, d in (shift or {}).items():
        kind, mesh = cell[name]
        mesh = mesh.copy()
        mesh.apply_translation(d)
        cell[name] = (kind, mesh)
    names = [s.get("name", "") for s in moves["steps"] if "move" in s]
    # optional per-move finger gap (a moves file's "egp_gap", mm between the fingers' inner faces; v8: Hand-E
    # 0-50 mm stroke): the gripper's fingers are rebuilt at that gap for the move; missing = `egp` as given
    gaps = [s.get("egp_gap") for s in moves["steps"] if "move" in s]
    per, events = program_samples(moves, step)
    fixtures = _manager({n: m for n, (k, m) in cell.items() if k == "fixture"})
    rob = _manager({**{f"link_{i}": l for i, l in enumerate(robot_meshes())},
                    "EGP": trimesh.util.concatenate([box(lo, hi) for lo, hi in egp])})
    part_mesh = {n: m for n, (k, m) in cell.items() if k == "part"}
    world = _manager(part_mesh) if parts else None
    spawn_at, k_ = {}, -1                                    # parts that appear after move k (a reload step)
    for s in moves["steps"]:
        if "move" in s:
            k_ += 1
        elif s.get("spawn"):
            spawn_at.setdefault(k_, []).extend(n for n in s["spawn"] if n in part_mesh)
    absent = {n for v in spawn_at.values() for n in v}

    def spawn(k):
        for n in spawn_at.get(k, []):
            if n in absent:
                absent.discard(n)
                if world is not None:
                    world.add_object(n, part_mesh[n], transform=pose[n])
    if world is not None:
        for n in absent:
            world.remove_object(n)
    arm = _manager({**{f"link_{i}": l for i, l in enumerate(robot_meshes()) if i >= 3},     # for the clearance:
                    "EGP": trimesh.util.concatenate([box(lo, hi) for lo, hi in egp])})     # the base stays put
    pose = {n: np.eye(4) for n in part_mesh}             # part transform (applied to its start mesh)
    held, rel, held_mgr = [], {}, None
    flat = sorted((k, s) for k, v in events.items() for s in v)
    grips = [k for k, s in flat if s["gripper"] == "grip"]
    releases = [k for k, s in flat if s["gripper"] == "release"]
    last_released = set()
    hits = []
    gap_now = None
    anchor_after = set()                                     # held-part contacts at the last grip pose
    rel_cache = {}
    spawn(-1)

    def contacts(F):
        """(held part, other) contact pairs with the held parts at gripper pose F."""
        m = trimesh.collision.CollisionManager()
        for n in held:
            m.add_object(n, part_mesh[n], transform=F @ rel[n])
        out = set()
        for other in (world, fixtures):
            hit, pairs = m.in_collision_other(other, return_names=True)
            if hit:
                out |= {tuple(sorted(p)) for p in pairs if not set(p) <= set(held)}
        return out

    def release_contacts(r):
        if r not in rel_cache:
            rel_cache[r] = contacts(robot_poses(per[r][-1])["EGP"])
        return rel_cache[r]
    for mi, path in enumerate(per):
        if gaps[mi] is not None and gaps[mi] != gap_now:     # fingers at this move's gap (see egp_at_gap)
            gap_now = gaps[mi]
            g = trimesh.util.concatenate([box(lo, hi) for lo, hi in egp_at_gap(gap_now, egp)])
            for m in (rob, arm):
                m.remove_object("EGP")
                m.add_object("EGP", g)
        nxt = next((s for k, s in flat if k >= mi), None)
        going_in = set(nxt["parts"]) if nxt and nxt["gripper"] == "grip" else set()
        quiet = any(0 < mi - g <= 2 for g in grips) or any(0 <= r - mi < 2 for r in releases)
        fx, pt = set(), set()
        for k, q in enumerate(path):
            P = robot_poses(q)
            for n, T in P.items():
                rob.set_transform(n, T)
            hit, pairs = fixtures.in_collision_other(rob, return_names=True)
            if hit:
                fx |= {tuple(sorted(p)) for p in pairs}
            elif clearance is not None and k % 5 == 0:
                for n in ("link_3", "link_4", "link_5", "link_6", "EGP"):
                    arm.set_transform(n, P[n])
                clearance[mi + 1] = min(clearance.get(mi + 1, 1e9), arm.min_distance_other(fixtures))
            if parts:
                F = P["EGP"]
                for n in held:
                    pose[n] = F @ rel[n]
                    world.set_transform(n, pose[n])
                    held_mgr.set_transform(n, pose[n])
                ok = going_in | last_released | set(held)
                hit, pairs = world.in_collision_other(rob, return_names=True)
                if hit:
                    pt |= {tuple(sorted(p)) for p in pairs if not set(p) & ok}
                if held:
                    allowed = set()
                    if quiet:                                # only the contacts of the grip / release pose
                        allowed = anchor_after if any(0 < mi - g <= 2 for g in grips) else set()
                        r = next((r for r in releases if 0 <= r - mi < 2), None)
                        if r is not None:
                            allowed = allowed | release_contacts(r)
                    for other in (world, fixtures):
                        hit, pairs = held_mgr.in_collision_other(other, return_names=True)
                        if hit:
                            pt |= {tuple(sorted(p)) for p in pairs
                                   if not set(p) <= set(held) and tuple(sorted(p)) not in allowed}
                    hit, pairs = held_mgr.in_collision_other(rob, return_names=True)
                    if hit:                                  # carried parts into the arm
                        pt |= {tuple(sorted(p)) for p in pairs if "EGP" not in p}
        if fx:
            hits.append({"move": mi + 1, "name": names[mi], "check": "fixtures", "pairs": sorted(fx),
                         "context": _context(events, mi)})
        if pt:
            hits.append({"move": mi + 1, "name": names[mi], "check": "parts", "pairs": sorted(pt),
                         "context": _context(events, mi)})
        if parts:                                           # gripper events after this move
            F = robot_poses(path[-1])["EGP"]
            for s in events.get(mi, []):
                if s["gripper"] == "grip":
                    for n in s["parts"]:
                        if n in pose and n not in held:
                            held.append(n)
                            rel[n] = np.linalg.inv(F) @ pose[n]
                    held_mgr = trimesh.collision.CollisionManager()
                    for n in held:
                        held_mgr.add_object(n, part_mesh[n], transform=pose[n])
                    anchor_after = contacts(F)
                    last_released = set()
                elif s["gripper"] == "release":
                    last_released = set(held)
                    held, rel, held_mgr = [], {}, None
        spawn(mi)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("program", help="TMflow zip, program json or tests/vN_moves.json")
    ap.add_argument("--cell", required=True, help='"v6", "v7", a cell .glb or a cell_layout json')
    ap.add_argument("--step", type=float, default=2.0, help="sampling, mm (Line) / deg (PTP), default 2")
    ap.add_argument("--parts", action="store_true", help="also check against the parts")
    ap.add_argument("--shift", action="append", default=[], help='"<object>:dx,dy,dz" (mm, robot base axes)')
    ap.add_argument("--list", action="store_true", help="every colliding move, not the first 20")
    ap.add_argument("--geometry", choices=list(K.GEOMETRY), default="robodk")
    a = ap.parse_args()
    K.use(a.geometry)
    shift = {s.split(":")[0]: [float(v) for v in s.split(":")[1].split(",")] for s in a.shift}
    for n, d in shift.items():
        print(f"{n} shifted by {d} mm (robot base axes)")
    clear = {}
    hits = check_program(a.program, a.cell, a.step, a.parts, shift, clearance=clear)
    for check in ("fixtures",) + (("parts",) if a.parts else ()):
        h = [x for x in hits if x["check"] == check]
        print(f"{check}: {'free' if not h else f'{len(h)} moves collide'}")
        for x in h[: None if a.list else 20]:
            pairs = sorted({f"{p}/{q}" for p, q in x["pairs"]})
            print(f"    move #{x['move']} ({x['name']}, {x['context']}): {', '.join(pairs[:6])}"
                  f"{' ...' if len(pairs) > 6 else ''}")
    if clear:
        print("closest moves to the fixtures (forearm, wrist, gripper; every 5th sample): " +
              ", ".join(f"#{k} {d:.1f} mm" for k, d in sorted(clear.items(), key=lambda kv: kv[1])[:5]))
    raise SystemExit(1 if hits else 0)


if __name__ == "__main__":
    main()
