"""Work frame from the four corners logged on the real robot, and a layout of the fixtures inside it.

    python robot_cell/bench_layout.py        (shared venv: numpy, trimesh, matplotlib)

In:  real_points.json (log_points.py: flange poses with the gripper tip on the corners),
     benchV1_parts/frame.stl + assembly.json (frame outline, plank positions).
Out: bench_layout.json  work frame (robot base coordinates) + fixture poses in the work frame
     bench_layout.png   picture of the layout
Work frame: origin at the "right down" corner, x towards "right up" (away from the robot),
y towards "left down", z up. Parts and fingertips stay inside; only the finished bench leaves,
over the far edge (x = max) onto the AMR plate. The gripper body (Schunk EGP, 94 x 90 mm) may
hang over an edge (Bjørge, 2026-10-16: with the body kept inside no layout was found).
"""
import itertools
import json
from pathlib import Path

import numpy as np
import trimesh
from matplotlib.path import Path as MPath

HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
TIP = 160.0          # flange -> closed fingertips, mm: Schunk EGP-C 40 TM (123 mm) + fingers, ESTIMATE
MARGIN = 3           # mm from the plate edge
CL = 8               # mm between parts (finger room)
R = 2.0              # mm per grid cell
AMR_EDGE_GAP = 30    # the jig must reach within this of the far edge
BODY = (0, 0)        # gripper half sizes that must stay over the plate: (0, 0) = fingertips only;
                     # the whole EGP body would be (47, 45): along the jaw direction, across it
RACK = (90, 60, 30)  # plank rack: size x, y in its own frame, pitch (3 planks along x, 2 rows along y)

# grips and pushes (x, y, closing direction) in side coordinates, as in the v2 bench_cell.py (git history)
C, S = np.cos(np.arctan2(1.75, 10)), np.sin(np.arctan2(1.75, 10))   # leg tilt 9.9 deg
LEG = (57.4, -40, C, S)                                     # rear leg of a frame
FRAME2_PUSHES = [(-47, -2.5, 1, 0), (47, -2.5, 1, 0), (67.6, 92.8, np.cos(np.radians(80)), np.sin(np.radians(80)))]


def rot(a, b, c):
    """TM pose angles (deg): R = Rz(c) Ry(b) Rx(a)."""
    a, b, c = np.radians([a, b, c])
    Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def work_frame():
    pts = {p["label"]: np.array(p["flange"]) for p in json.loads((HERE / "real_points.json").read_text())}
    tip = {k: v[:3] + TIP * rot(*v[3:])[:, 2] for k, v in pts.items()}
    o = tip["right down"]
    x = tip["right up"] - o
    x /= np.linalg.norm(x)
    z = np.cross(x, tip["left down"] - o)
    z /= np.linalg.norm(z)
    y = np.cross(z, x)
    pose = np.eye(4)
    pose[:3, :3] = np.c_[x, y, z]
    pose[:3, 3] = o
    local = {k: np.linalg.inv(pose) @ np.r_[v, 1] for k, v in tip.items()}
    size_x = min(local["right up"][0], local["left up"][0])           # inside both opposite sides
    size_y = min(local["left down"][1], local["left up"][1])
    return pose, size_x, size_y, {k: v[:3].round(2).tolist() for k, v in local.items()}


def side_plank_grips():
    """Plank grip/push spots in the jig (side coordinates): position and closing direction."""
    side = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 125], [0, 0, 0, 1]], float)   # transl(0,0,125) rotx(90)
    grip = np.array([[0, -1, 0, 0], [0, 0, -1, 110], [1, 0, 0, 2.5], [0, 0, 0, 1]], float)
    parts = json.loads((HERE / "benchV1_parts" / "assembly.json").read_text())["parts"]
    return [(t[0, 3], t[1, 3], t[0, 0], t[1, 0]) for t in
            (side @ np.array(p["pose"]) @ grip for p in parts if p["type"] == "plank")]


JIG_GRIPS = [LEG] + FRAME2_PUSHES + side_plank_grips()
NEST_GRIPS = [LEG]
RACK_GRIPS = [(RACK[2] * (c + 0.5), RACK[2] * (r + 0.5) + 2.5, 0, 1) for r in range(2) for c in range(3)]


def body_inside(grips, pose, sx, sy):
    """True if the gripper body fits on the plate at every grip of a fixture at pose (tx, ty, rot)."""
    tx, ty, rot_deg = pose
    c, s = np.cos(np.radians(rot_deg)), np.sin(np.radians(rot_deg))
    for x, y, dx, dy in grips:
        px, py = c * x - s * y + tx, s * x + c * y + ty
        ux, uy = c * dx - s * dy, s * dx + c * dy                      # closing direction
        vx, vy = -uy, ux
        for a in (-1, 1):
            for b in (-1, 1):
                qx, qy = px + a * BODY[0] * ux + b * BODY[1] * vx, py + a * BODY[0] * uy + b * BODY[1] * vy
                if not (0 <= qx <= sx and 0 <= qy <= sy):
                    return False
    return True


def frame_mask():
    a = {p["name"]: p for p in json.loads((HERE / "benchV1_parts" / "assembly.json").read_text())["parts"]}
    m = trimesh.load(HERE / "benchV1_parts" / "frame.stl")
    m.apply_transform(np.array(a["frame1"]["pose"]))
    sec = m.section(plane_origin=[0, -120, 0], plane_normal=[0, 1, 0])
    loops = [np.c_[sec.vertices[e.points][:, 0], -sec.vertices[e.points][:, 2]] for e in sec.entities]
    outer = max(loops, key=lambda p: np.ptp(p[:, 0]) * np.ptp(p[:, 1]))   # side coordinates (bench on its side)
    lo = outer.min(0)
    n = np.ceil(np.ptp(outer, 0) / R).astype(int) + 1
    gx, gy = np.meshgrid(lo[0] + np.arange(n[0]) * R, lo[1] + np.arange(n[1]) * R, indexing="ij")
    return MPath(outer).contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(n), lo


def pose_of(shape, lo, r, ij):
    """(x, y, rot) of the part frame for a mask of `shape` whose unrotated min corner is `lo`,
    rotated r deg CCW and placed with its min corner at grid cell ij."""
    nx, ny = shape
    c, s = np.cos(np.radians(r)), np.sin(np.radians(r))
    corners = np.array([[0, 0], [nx - 1, 0], [0, ny - 1], [nx - 1, ny - 1]]) * R + lo
    rc = corners @ np.array([[c, s], [-s, c]])                       # rotated CCW (row vectors)
    t = np.array(ij) * R + MARGIN - rc.min(0)
    return (round(float(t[0]), 2), round(float(t[1]), 2), r)


def pack(sx, sy):
    frame, lo = frame_mask()
    rack = np.ones((int(RACK[0] / R), int(RACK[1] / R)), bool)
    gw, gh = int((sx - 2 * MARGIN) / R), int((sy - 2 * MARGIN) / R)
    k = int(np.ceil(CL / R))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    disk = np.argwhere(xx ** 2 + yy ** 2 <= k * k) - k

    def dilate(mask):
        out = np.zeros_like(mask)
        for dx, dy in disk:
            out |= np.roll(np.roll(mask, dx, 0), dy, 1)
        return out

    def free(occ, part):
        pw, ph = part.shape
        if pw > gw or ph > gh:
            return np.empty((0, 2), int)
        s = (gw + pw, gh + ph)
        ov = np.fft.irfft2(np.fft.rfft2(occ.astype(float), s=s) * np.fft.rfft2(part[::-1, ::-1].astype(float), s=s), s=s)
        return np.argwhere(ov[pw - 1:gw, ph - 1:gh] < 0.5)

    def put(occ, part, ij):
        o = occ.copy()
        o[ij[0]:ij[0] + part.shape[0], ij[1]:ij[1] + part.shape[1]] |= part
        return o

    def grip_ok(mask, mlo, r, grips):
        """map of grid offsets where the gripper body fits at every grip (computed once)"""
        m = np.rot90(mask, r // 90)
        out = np.zeros((max(gw - m.shape[0] + 1, 0), max(gh - m.shape[1] + 1, 0)), bool)
        for i, j in np.ndindex(out.shape):
            out[i, j] = body_inside(grips, pose_of(mask.shape, mlo, r, (i, j)), sx, sy)
        return out

    def spots(occ, mask, r, okmap):
        f = np.zeros_like(okmap)
        for i, j in free(occ, np.rot90(mask, r // 90)):
            f[i, j] = okmap[i, j]
        return np.argwhere(f)

    rots = (0, 90, 180, 270)
    ok_jig = {r: grip_ok(frame, lo, r, JIG_GRIPS) for r in rots}
    ok_nest = {r: grip_ok(frame, lo, r, NEST_GRIPS) for r in rots}
    ok_rack = {r: grip_ok(rack, np.zeros(2), r, RACK_GRIPS) for r in (0, 90)}
    zero = np.zeros((gw, gh), bool)
    for rj in rots:
        jm = np.rot90(frame, rj // 90)
        for ij in spots(zero, frame, rj, ok_jig[rj]):
            if (ij[0] + jm.shape[0]) * R + MARGIN < sx - AMR_EDGE_GAP:  # jig at the far edge (AMR)
                continue
            occ1 = put(zero, jm, ij)
            d1 = dilate(occ1)
            for ra, rb in itertools.product(rots, repeat=2):
                for ia in spots(d1, frame, ra, ok_nest[ra])[::2]:
                    occ2 = put(occ1, np.rot90(frame, ra // 90), ia)
                    d2 = dilate(occ2)
                    for ib in spots(d2, frame, rb, ok_nest[rb])[::3]:
                        occ3 = put(occ2, np.rot90(frame, rb // 90), ib)
                        d3 = dilate(occ3)
                        for rr in (0, 90):
                            sr = spots(d3, rack, rr, ok_rack[rr])
                            if len(sr):
                                occ4 = put(occ3, np.rot90(rack, rr // 90), sr[0])
                                return ({"jig": pose_of(frame.shape, lo, rj, ij), "nest A": pose_of(frame.shape, lo, ra, ia),
                                         "nest B": pose_of(frame.shape, lo, rb, ib),
                                         "rack": pose_of(rack.shape, np.zeros(2), rr, sr[0])}, occ1, occ2, occ3, occ4)
    return None


def main():
    pose, sx, sy, corners = work_frame()
    print(f"work frame origin (robot base, mm): {pose[:3, 3].round(1)}, usable {sx:.0f} x {sy:.0f} mm")
    res = pack(sx, sy)
    if res is None:
        raise SystemExit("no layout fits with the gripper body inside the plate")
    layout, o1, o2, o3, o4 = res
    out = {"tip_mm": TIP, "work_frame": pose.round(5).tolist(), "size": [round(sx, 1), round(sy, 1)],
           "corners_in_work_frame": corners, "gap": CL, "gripper_body": BODY,
           "rack": {"size": RACK[:2], "pitch": RACK[2]},
           "note": "[x, y, rot_deg] in the work frame: for jig and nests the frame's side-coordinate "
                   "origin, for the rack its own origin (planks 3 along its x, 2 rows along its y)",
           "layout": {k: list(v) for k, v in layout.items()}}
    (HERE / "bench_layout.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k, v in layout.items():
        print(f"  {k:7s} {v}")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    img = o1 * 1.0 + (o2 & ~o1) * 2 + (o3 & ~o2) * 3 + (o4 & ~o3) * 4
    plt.figure(figsize=(6, 6.6))
    plt.imshow(img.T, origin="lower", extent=[MARGIN, MARGIN + img.shape[0] * R, MARGIN, MARGIN + img.shape[1] * R],
               cmap="tab10", vmax=9)
    plt.gca().add_patch(plt.Rectangle((0, 0), sx, sy, fill=False, lw=2))
    plt.xlabel("x [mm]  robot side -> far edge (AMR)"); plt.ylabel("y [mm]  right -> left")
    plt.title("1 jig   2 nest A (frame 1)   3 nest B (frame 2)   4 plank rack")
    plt.savefig(HERE / "bench_layout.png", dpi=90, bbox_inches="tight")


if __name__ == "__main__":
    main()
