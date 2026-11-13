"""Find the jigs in a tool-camera photo and say how far each moved from its CAD position - three methods, same output.

Each method returns, per jig, its move from the CAD start as the pivot's offset x, y (mm, robot base) and rz (deg) -
the same numbers the sim's Jigs panel uses and writes into the photo's JSON under "objects" (the truth).

  aruco    the ArUco marker on the jig (needs markers on the jigs). Its 4 corners are found in the image, put on the
           marker's known height (ray from the camera), and fitted to the marker's CAD corners -> move.
  colour   the jig's colour (learned from the reference photo) inside a search area around its CAD place; the blob is
           put on the jig's top height and matched to the reference blob by turning (+-25 deg) and shifting -> move.
  features SIFT keypoints of the jig in the reference photo, each with its true 3D point from the reference's position
           pass (.xyz.f32); matched in the new photo, solvePnPRansac -> the jig's pose -> move. Works from another
           camera pose too, like TMflow's pattern matching after calibration.

colour and features need a reference photo: the jigs at their CAD places (Reset all), taken with xyz=True.

  python tests/vision_lab/jig_vision.py <photo.json> --ref <ref.json> [--methods aruco,colour,features] [--overlay]
"""
import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

JIGS = ["Base A", "Base B", "Plank rack", "Guide small", "Guide big"]
HALF = 0.5   # OpenCV puts a pixel's centre at whole numbers, the camera model (K, three.js) at +0.5: add HALF to OpenCV points


# ---- photo + camera ------------------------------------------------------------------------------------------
class Photo:
    def __init__(self, json_path):
        self.json = Path(json_path)
        self.meta = json.loads(self.json.read_text(encoding="utf-8"))
        self.img = cv2.imread(str(self.json.with_name(self.meta["image"])))
        self.K = np.array(self.meta["K"], float)
        T = np.array(self.meta["T_base_cam"], float)
        self.R, self.C = T[:3, :3], T[:3, 3]
        self.T = T
        self.model = (self.meta.get("jig_model") or {}).get("jigs", {})
        self.xyz = None
        if self.meta.get("xyz_file"):
            h, w, _ = self.meta["xyz_shape"]
            self.xyz = np.fromfile(self.json.with_name(self.meta["xyz_file"]), np.float32).reshape(h, w, 4)
            self.ids = {int(k): v for k, v in self.meta["xyz_ids"].items()}

    def ray_to_z(self, uv, z):
        """Pixels (N,2) -> points (N,3) on the plane z (robot base, mm)."""
        uv = np.asarray(uv, float).reshape(-1, 2)
        d = (self.R @ (np.linalg.inv(self.K) @ np.c_[uv, np.ones(len(uv))].T)).T
        t = (z - self.C[2]) / d[:, 2]
        return self.C + d * t[:, None]

    def project(self, P):
        """Points (N,3) robot base -> pixels (N,2)."""
        pc = (self.R.T @ (np.asarray(P, float).reshape(-1, 3) - self.C).T).T
        uv = (self.K @ pc.T).T
        return uv[:, :2] / uv[:, 2:3]

    def truth(self, name):
        o = self.meta.get("objects", {}).get(name)
        return {"x": o["x"], "y": o["y"], "rz": o["rz"]} if o else {"x": 0.0, "y": 0.0, "rz": 0.0}


def move_from_rigid2d(Rm, t, pivot):
    """x' = Rm x + t (plane, mm) -> the pivot's offset and rz."""
    p = np.asarray(pivot[:2], float)
    d = Rm @ p + t - p
    return {"x": float(d[0]), "y": float(d[1]), "rz": math.degrees(math.atan2(Rm[1, 0], Rm[0, 0]))}


def rigid2d_to_4x4(Rm, t):
    """The plane move as a 4x4 in the robot base (turn about z, shift in x y): new point = T_move @ taught point."""
    T = np.eye(4); T[:2, :2] = Rm; T[:2, 3] = t
    return T


def move_point(T_move, p):
    """A taught point (x, y, z) of a jig -> where it is now."""
    return (np.asarray(T_move) @ np.r_[np.asarray(p, float)[:3], 1.0])[:3]


def fit_rigid2d(A, B):
    """Least-squares rotation + translation with B ~ R A + t (Kabsch, 2D)."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    ca, cb = A.mean(0), B.mean(0)
    U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
    Rm = Vt.T @ U.T
    if np.linalg.det(Rm) < 0:
        Vt[-1] *= -1
        Rm = Vt.T @ U.T
    return Rm, cb - Rm @ ca


# ---- 1. ArUco markers --------------------------------------------------------------------------------------
def aruco_params():
    prm = cv2.aruco.DetectorParameters()
    prm.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    return prm


def aruco(photo, ref=None, **_):
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    corners, ids, _ = cv2.aruco.ArucoDetector(d, aruco_params()).detectMarkers(cv2.cvtColor(photo.img, cv2.COLOR_BGR2GRAY))
    found = {int(i): c.reshape(4, 2) + HALF for i, c in zip(ids.ravel(), corners)} if ids is not None else {}
    out = {}
    for name in JIGS:
        if name not in photo.model:
            out[name] = {"ok": False, "why": "not in the jig model (real_setup.py)"}
            continue
        mk = photo.model.get(name, {}).get("marker")
        if not mk:
            out[name] = {"ok": False, "why": "no marker on this jig"}
            continue
        if mk["id"] not in found:
            out[name] = {"ok": False, "why": f"marker {mk['id']} ({mk['size']} mm) not detected"}
            continue
        cad = np.array(mk["corners"], float)
        now = photo.ray_to_z(found[mk["id"]], cad[0, 2])            # same height as at the CAD start (dz = 0)
        Rm, t = fit_rigid2d(cad[:, :2], now[:, :2])
        res = move_from_rigid2d(Rm, t, photo.model[name]["pivot"])
        res.update(ok=True, px=found[mk["id"]].tolist(), fit_mm=float(np.abs((Rm @ cad[:, :2].T).T + t - now[:, :2]).max()),
                   T_move=rigid2d_to_4x4(Rm, t).tolist(),
                   off_centre=float(np.linalg.norm(found[mk["id"]].mean(0) - photo.K[:2, 2]) / photo.K[0, 0]))
        out[name] = res
    return out


# ---- 2. colour -----------------------------------------------------------------------------------------------
def _hsv(photo):
    """The photo's HSV (int16), computed once per photo/image."""
    if getattr(photo, "_hsv_of", None) is not photo.img:
        photo._hsv, photo._hsv_of = cv2.cvtColor(photo.img, cv2.COLOR_BGR2HSV).astype(np.int16), photo.img
    return photo._hsv


def _learn_colour(ref, name):
    """The jig's colour in the reference photo: H, S, V centre + spread of its own pixels (from the position pass)."""
    hsv = _hsv(ref)
    oid = [k for k, v in ref.ids.items() if v == name][0]
    m = np.repeat(np.repeat(np.round(ref.xyz[..., 3]).astype(int) == oid, 2, 0), 2, 1)
    px = hsv[m]
    if len(px) < 50:
        return None
    h, s, v = np.median(px[:, 0]), np.median(px[:, 1]), np.median(px[:, 2])
    return {"h": float(h), "s": float(s), "v": float(v),
            "dh": float(max(4, np.percentile(np.abs(px[:, 0] - h), 80))),
            "ds": float(max(25, np.percentile(np.abs(px[:, 1] - s), 80)))}


def _colour_mask(photo, c):
    hsv = _hsv(photo)
    dh = np.abs(hsv[..., 0] - c["h"]); dh = np.minimum(dh, 180 - dh)
    # hue + saturation only, brightness just above black: light level and shadows change V, not the colour
    m = (dh <= c["dh"]) & (np.abs(hsv[..., 1] - c["s"]) <= c["ds"]) & (hsv[..., 2] >= 30)
    m = m.astype(np.uint8) * 255
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def _blob_mm(photo, mask, area_poly, z, grid):
    """Mask pixels inside the search area -> a 1 mm grid image on the plane z (grid = (x0, y0, W, H))."""
    roi = np.zeros(mask.shape, np.uint8)
    cv2.fillPoly(roi, [np.round(photo.project(area_poly)).astype(np.int32)], 255)
    vs, us = np.nonzero(mask & roi)
    if len(us) < 50:
        return None
    P = photo.ray_to_z(np.c_[us + 0.5, vs + 0.5], z)
    x0, y0, W, H = grid
    g = np.zeros((H, W), np.uint8)
    xi, yi = np.round(P[:, 0] - x0).astype(int), np.round(P[:, 1] - y0).astype(int)
    k = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
    g[yi[k], xi[k]] = 255
    return cv2.morphologyEx(g, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))


_refblobs = {}


def colour(photo, ref, margin=60, **_):
    out = {}
    for name in JIGS:
        jm = photo.model[name]
        c = _learn_colour(ref, name)
        if not c or c["s"] < 40:
            out[name] = {"ok": False, "why": "grey/unsaturated: colour doesn't separate it" if c else "not seen in the reference"}
            continue
        z = jm["box_max"][2]
        bx0, by0, bx1, by1 = jm["box_min"][0] - margin, jm["box_min"][1] - margin, jm["box_max"][0] + margin, jm["box_max"][1] + margin
        area = [[bx0, by0, z], [bx1, by0, z], [bx1, by1, z], [bx0, by1, z]]
        grid = (int(bx0), int(by0), int(bx1 - bx0) + 1, int(by1 - by0) + 1)
        key = (str(ref.json), name, margin)
        if key not in _refblobs:                    # the reference blob never changes: once per reference photo
            _refblobs[key] = _blob_mm(ref, _colour_mask(ref, c), area, z, grid)
        a = _refblobs[key]
        b = _blob_mm(photo, _colour_mask(photo, c), area, z, grid)
        if a is None or b is None:
            out[name] = {"ok": False, "why": "no colour blob found"}
            continue
        ma, mb = cv2.moments(a, True), cv2.moments(b, True)
        ca = np.array([ma["m10"] / ma["m00"], ma["m01"] / ma["m00"]]); cb = np.array([mb["m10"] / mb["m00"], mb["m01"] / mb["m00"]])
        af, bf = a.astype(np.float32) / 255, b.astype(np.float32) / 255

        def score(ang):                             # turn the reference blob, shift it onto the new one, overlap
            r = math.radians(ang)
            Rm = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
            t = cb - Rm @ ca
            w = cv2.warpAffine(af, np.c_[Rm, t].astype(np.float32), (b.shape[1], b.shape[0]))
            (sx, sy), _ = cv2.phaseCorrelate(w, bf)           # fine shift
            t2 = t + [sx, sy]
            w = cv2.warpAffine(af, np.c_[Rm, t2].astype(np.float32), (b.shape[1], b.shape[0]))
            return float(np.minimum(w, bf).sum() / max(1e-6, np.maximum(w, bf).sum())), Rm, t2

        best = max((score(g) for g in np.arange(-24, 24.1, 3)), key=lambda x: x[0])      # coarse: every 3 deg
        a0 = math.degrees(math.atan2(best[1][1, 0], best[1][0, 0]))
        for step in (0.75, 0.2):                                                     # then finer around the best
            best = max([best] + [score(a0 + k * step) for k in range(-4, 5) if k], key=lambda x: x[0])
            a0 = math.degrees(math.atan2(best[1][1, 0], best[1][0, 0]))
        iou, Rm, t = best
        t_mm = t + np.array(grid[:2]) - Rm @ np.array(grid[:2])            # grid coords -> robot mm
        res = move_from_rigid2d(Rm, t_mm, jm["pivot"])
        res.update(ok=True, iou=round(iou, 3), area_ref_mm2=int(a.sum() / 255), area_now_mm2=int(b.sum() / 255))
        out[name] = res
    return out


# ---- 3. features (SIFT + PnP) -------------------------------------------------------------------------------
_sift, _refcache = None, {}


def _features(img):
    global _sift
    _sift = _sift or cv2.SIFT_create(nfeatures=6000)
    return _sift.detectAndCompute(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), None)


def _ref_features(ref):
    """The reference's keypoints with their 3D points and object ids (position pass), once per reference photo."""
    key = str(ref.json)
    if key not in _refcache:
        kr, dr = _features(ref.img)
        h, w = ref.xyz.shape[:2]
        pts = np.array([k.pt for k in kr]) + HALF
        # half-res pixel (c, r) covers full-res [2c, 2c+2); keep keypoints whose neighbours are the same object
        ci = np.clip(np.floor(pts[:, 0] / 2).astype(int), 0, w - 1)
        ri = np.clip(np.floor(pts[:, 1] / 2).astype(int), 0, h - 1)
        P3 = ref.xyz[ri, ci, :3].astype(float); oid = np.round(ref.xyz[ri, ci, 3]).astype(int)
        c2, r2 = np.clip(ci + 1, 0, w - 1), np.clip(ri + 1, 0, h - 1)
        same = (np.round(ref.xyz[r2, ci, 3]) == oid) & (np.round(ref.xyz[ri, c2, 3]) == oid)
        oid[~same] = -9                             # on an edge between objects: its 3D point is unreliable
        _refcache[key] = (kr, dr, P3, oid)
    return _refcache[key]


def features(photo, ref, **_):
    kr, dr, P3, oid = _ref_features(ref)
    kn, dn = _features(photo.img)
    if dr is None or dn is None:
        return {n: {"ok": False, "why": "no keypoints"} for n in JIGS}
    matches = cv2.BFMatcher(cv2.NORM_L2).knnMatch(dr, dn, k=2)
    good = [m for m, n2 in (p for p in matches if len(p) == 2) if m.distance < 0.75 * n2.distance]
    out = {}
    for name in JIGS:
        jid = [k for k, v in ref.ids.items() if v == name][0]
        g = [m for m in good if oid[m.queryIdx] == jid]
        if len(g) < 6:
            out[name] = {"ok": False, "why": f"only {len(g)} matched keypoints"}
            continue
        obj = P3[[m.queryIdx for m in g]]
        img = np.array([kn[m.trainIdx].pt for m in g]) + HALF
        ok, rvec, tvec, inl = cv2.solvePnPRansac(obj, img, photo.K, None, reprojectionError=3.0, iterationsCount=1000,
                                                 flags=cv2.SOLVEPNP_EPNP)
        if not ok or inl is None or len(inl) < 6:
            out[name] = {"ok": False, "why": f"PnP failed ({len(g)} matches)"}
            continue
        inl = inl.ravel()
        rvec, tvec = cv2.solvePnPRefineLM(obj[inl], img[inl], photo.K, None, rvec, tvec)
        Rc, _ = cv2.Rodrigues(rvec)
        M = photo.T @ np.r_[np.c_[Rc, tvec], [[0, 0, 0, 1]]]           # CAD start -> now, robot base
        p = np.r_[photo.model[name]["pivot"], 1.0]
        d = M @ p - p
        out[name] = {"ok": True, "x": float(d[0]), "y": float(d[1]), "z": float(d[2]),
                     "rz": math.degrees(math.atan2(M[1, 0], M[0, 0])), "matches": len(g), "inliers": int(len(inl))}
    return out


METHODS = {"aruco": aruco, "colour": colour, "features": features}


def errors(photo, res):
    out = {}
    for name, r in res.items():
        t = photo.truth(name)
        if not r.get("ok"):
            out[name] = None
            continue
        da = (r["rz"] - t["rz"] + 180) % 360 - 180
        out[name] = {"pos_mm": math.hypot(r["x"] - t["x"], r["y"] - t["y"]), "rz_deg": abs(da)}
    return out


# ---- overlay: what each method found, on the photo -----------------------------------------------------------
def outline(photo, name, mv):
    """The jig's CAD box top, moved by mv (x y rz about the pivot), as image points."""
    jm = photo.model[name]
    (x0, y0, _), (x1, y1, z) = jm["box_min"], jm["box_max"]
    p = np.array(jm["pivot"][:2]); r = math.radians(mv["rz"])
    Rm = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
    Q = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    Q = (Rm @ (Q - p).T).T + p + [mv["x"], mv["y"]]
    return photo.project(np.c_[Q, np.full(4, z)])


def overlay(photo, res, method, path):
    img = photo.img.copy()
    err = errors(photo, res)
    for k, name in enumerate(JIGS):
        t = photo.truth(name)
        cv2.polylines(img, [np.round(outline(photo, name, t) - HALF).astype(np.int32)], True, (60, 60, 230), 2)        # truth: red
        r = res.get(name, {})
        if r.get("ok"):
            cv2.polylines(img, [np.round(outline(photo, name, r) - HALF).astype(np.int32)], True, (40, 200, 40), 2)   # found: green
            if r.get("px"):
                cv2.polylines(img, [np.round(np.array(r["px"]) - HALF).astype(np.int32)], True, (255, 160, 0), 2)
            e = err[name]
            txt = f"{name}: {e['pos_mm']:.1f} mm, {e['rz_deg']:.2f} deg"
        else:
            txt = f"{name}: - ({r.get('why', '?')})"
        cv2.putText(img, txt, (12, 28 + 26 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(img, txt, (12, 28 + 26 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 1, cv2.LINE_AA)
    cv2.putText(img, f"{method}  (green = found, red = truth)", (12, img.shape[0] - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (20, 20, 20), 2, cv2.LINE_AA)
    cv2.imwrite(str(path), img)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo", nargs="+", help="one or more photos (e.g. overview + above the rack): each jig is taken "
                    "from the photo where its marker is nearest the image centre")
    ap.add_argument("--save", help="write the moves (x y rz + T_move per jig) to this json, for the robot program")
    ap.add_argument("--ref", help="reference photo json (jigs at CAD, taken with xyz)")
    ap.add_argument("--methods", default="aruco,colour,features")
    ap.add_argument("--overlay", action="store_true", help="write <photo>_<method>.png with what was found")
    a = ap.parse_args()
    photos = [Photo(p) for p in a.photo]
    ref = Photo(a.ref) if a.ref else None
    saved = {}
    for m in a.methods.split(","):
        if m != "aruco" and not ref:
            print(f"{m}: needs --ref"); continue
        best = {}
        for ph in photos:
            res = METHODS[m](ph, ref)
            err = errors(ph, res)
            for n in JIGS:
                r = res[n]
                if r.get("ok") and (n not in best or r.get("off_centre", 0) < best[n][0].get("off_centre", 0)):
                    best[n] = (r, err[n], ph.json.name)
                elif n not in best:
                    best.setdefault(n + "#miss", (r, None, ph.json.name))
            if a.overlay:
                overlay(ph, res, m, ph.json.with_name(ph.json.stem + f"_{m}.png"))
        truth = any(ph.meta.get("objects") for ph in photos)
        print(f"== {m}")
        for n in JIGS:
            if n in best:
                r, e, src = best[n]
                print(f"  {n:12s} x {r['x']:7.2f} y {r['y']:7.2f} rz {r['rz']:6.2f}" +
                      (f"   error {e['pos_mm']:5.2f} mm {e['rz_deg']:5.2f} deg" if truth and e else "") + f"   ({src})")
                saved[n] = {k: r[k] for k in ("x", "y", "rz", "T_move") if k in r} | {"photo": src, "method": m}
            else:
                r = best.get(n + "#miss", ({"why": "?"},))[0]
                print(f"  {n:12s} -  ({r.get('why')})")
    if a.save:
        Path(a.save).write_text(json.dumps({"moves": saved, "photos": [p.json.name for p in photos],
                                            "note": "x y = the pivot's move (mm), rz deg; new point = T_move @ taught point"},
                                           indent=1), encoding="utf-8")
        print("written:", a.save)


if __name__ == "__main__":
    main()
