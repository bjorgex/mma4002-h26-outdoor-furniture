"""Screenshots of the cell for one scored run (headless, matplotlib): what the judge's numbers can't show.

    called by score.py: render(cell, snaps, tcp_pts, moves, out_dir)

Out: out_dir/shots/NN_<event>_after_move_MMM_<parts>.png, one per snapshot (start, after every release, end): the
cell with the parts where they are at that moment and the robot in its pose, left iso view, right top view (robot
base frame: x, y in mm; the robot stands at 0, 0). Colours: jigs blue, plate grey, frames steel blue, planks wood,
interface pieces red, guide yellow, robot dark grey (link shapes as convex hulls), gripper black.
out_dir/topview.png: plate, jigs and parts at the start (outlines) + the TCP path of the whole program, PTP moves
dashed, Lines solid; colour = time along the program (light -> dark); gripper events marked.
Look at every shot: a part floating, crooked in its pocket, into another part, a jig in an odd place, the arm
folded oddly - things a collision count does not tell you.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                      # noqa: E402
import numpy as np                                                   # noqa: E402
import trimesh                                                       # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection              # noqa: E402

HERE = Path(__file__).resolve().parent
_HULLS = None
LIGHT = np.array([0.3, -0.4, 0.85]) / np.linalg.norm([0.3, -0.4, 0.85])


def colour(name, kind):
    n = name.lower()
    if "plank" in n and "jig" not in n:
        return (0.75, 0.55, 0.3)
    if "piece" in n:
        return (0.85, 0.1, 0.1)
    if "frame" in n:
        return (0.45, 0.55, 0.75)
    if "guide" in n:
        return (0.95, 0.75, 0.2)
    if "plate" in n:
        return (0.82, 0.8, 0.74)
    if "amr" in n:
        return (0.4, 0.75, 0.45)
    if "riser" in n:
        return (0.6, 0.6, 0.62)
    return (0.35, 0.55, 0.85) if kind == "fixture" else (0.7, 0.7, 0.7)


def robot_hulls():
    global _HULLS
    if _HULLS is None:
        import collision
        _HULLS = [m.convex_hull for m in collision.robot_meshes()]
    return _HULLS


def robot_parts(q):
    import collision
    P = collision.robot_poses(q)
    out = []
    for i, m in enumerate(robot_hulls()):
        mm = m.copy()
        mm.apply_transform(P[f"link_{i}"])
        out.append((mm, (0.3, 0.3, 0.33)))
    g = trimesh.util.concatenate([collision.box(lo, hi) for lo, hi in collision.EGP])
    g.apply_transform(P["EGP"])
    out.append((g, (0.1, 0.1, 0.1)))
    return out


def scene_at(cell, snap, lim=None):
    objs = []
    for n, (k, m) in cell.items():
        if n.lower() == "table" or "amr top" in n.lower():
            continue
        if lim is not None and (m.bounds[1][0] < lim[0][0] or m.bounds[0][0] > lim[0][1]
                                or m.bounds[1][1] < lim[1][0] or m.bounds[0][1] > lim[1][1]):
            continue                                                 # outside the view (the AMR)
        mm = m
        if k == "part" and snap and n in snap["poses"]:
            mm = m.copy()
            mm.apply_transform(np.asarray(snap["poses"][n]))
        objs.append((mm, colour(n, k)))
    return objs


def draw(ax, objs, elev, azim, lim):
    tris, cols = [], []
    for m, c in objs:
        t = m.triangles
        n = m.face_normals
        shade = 0.45 + 0.55 * np.abs(n @ LIGHT)
        tris.append(t)
        cols.append(np.clip(np.array(c)[None, :] * shade[:, None], 0, 1))
    pc = Poly3DCollection(np.vstack(tris), facecolors=np.vstack(cols), edgecolors="none", linewidths=0)
    ax.add_collection3d(pc)
    (x0, x1), (y0, y1), (z0, z1) = lim
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_zlim(z0, z1)
    ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0))
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.tick_params(labelsize=6)


def limits(cell):
    plate = next((m for n, (k, m) in cell.items() if "plate" in n.lower() and "amr" not in n.lower()), None)
    if plate is None:
        lo, hi = np.array([-900, -400, -20]), np.array([200, 400, 600])
    else:
        lo, hi = plate.bounds
    return ((lo[0] - 60, max(hi[0] + 60, 150)), (lo[1] - 60, hi[1] + 60), (-20, 620))


def render(cell, snaps, tcp_pts, moves, out_dir, label=""):
    out_dir = Path(out_dir)
    shots = out_dir / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    for f in shots.glob("*.png"):
        f.unlink()
    lim = limits(cell)
    keep = [s for s in snaps if s["event"] in ("start", "release", "end")]
    for i, s in enumerate(keep):
        objs = scene_at(cell, s, lim) + robot_parts(s["q"])
        fig = plt.figure(figsize=(13, 6.2), dpi=90)
        a1 = fig.add_subplot(1, 2, 1, projection="3d")
        draw(a1, objs, 28, -150, lim)
        a2 = fig.add_subplot(1, 2, 2, projection="3d")
        draw(a2, objs, 89.9, -90, lim)
        a2.set_proj_type("ortho")
        parts = ", ".join(s["parts"][:4]) + (f" +{len(s['parts']) - 4}" if len(s["parts"]) > 4 else "")
        title = {"start": "start", "end": "end of the program"}.get(s["event"], f"after the release of {parts}")
        fig.suptitle(f"{label}: {title} (after move #{s['move']})   left: iso, right: top (x, y mm)", fontsize=10)
        fig.tight_layout()
        tag = "_".join(p.replace(" ", "") for p in s["parts"][:2])
        fig.savefig(shots / f"{i:02d}_{s['event']}_after_move_{s['move']:03d}{'_' + tag if tag else ''}.png")
        plt.close(fig)
    topview(cell, snaps, tcp_pts, moves, out_dir / "topview.png", label, lim)


def topview(cell, snaps, tcp_pts, moves, path, label, lim):
    fig, ax = plt.subplots(figsize=(9, 7.5), dpi=90)
    start = snaps[0] if snaps else None
    for m, c in scene_at(cell, start):
        xy = m.vertices[:, :2]
        try:
            from scipy.spatial import ConvexHull
            h = ConvexHull(xy)
            x, y = xy[h.vertices, 0], xy[h.vertices, 1]
        except Exception:
            (x0, y0), (x1, y1) = xy.min(0), xy.max(0)
            x, y = [x0, x1, x1, x0], [y0, y0, y1, y1]
        ax.fill(x, y, color=c, alpha=0.35, lw=0.6, ec=tuple(v * 0.6 for v in c))
    n = len(tcp_pts)
    cmap = plt.get_cmap("plasma_r")
    for k, p in enumerate(tcp_pts):
        if len(p) < 2 and k == 0:
            continue
        pts = np.vstack([tcp_pts[k - 1][-1:], p]) if k else p
        ax.plot(pts[:, 0], pts[:, 1], ls="--" if moves[k]["move"] == "ptp" else "-", lw=1.0,
                color=cmap(0.15 + 0.8 * k / max(1, n - 1)))
    ax.plot([0], [0], "k+", ms=12)
    ax.text(5, 5, "robot", fontsize=7)
    ax.set_xlim(*lim[0])
    ax.set_ylim(*lim[1])
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm] (robot base)")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"{label}: start layout + TCP path (PTP dashed, light -> dark = time)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
