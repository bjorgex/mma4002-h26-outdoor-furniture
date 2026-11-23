"""Find Techman's OMRON / TM Landmark sticker in a photo - the black-framed white square with "OMRON" text above a
blue curve pattern - and give its 4 corners in a fixed order, so it can be used like an ArUco marker.

  python tests/vision_lab/landmark.py <image.png> [--size MM] [--camera camera.json] [--pose x y z rx ry rz]
                                                  [--z MM] [--overlay out.png]

How it works:
  1. find  - dark, convex 4-corner outlines whose inside is bright and holds blue pixels (the curves)
  2. turn  - the square looks the same in 4 turns; the text is always above the blue pattern, so the warped
             square is tried in all 4 turns and the one with the blue in the bottom half and the dark text in the
             top half wins. Corners come out as TL, TR, BR, BL of the sticker as you read it.
  3. pose  - with --size (OUTER side of the black frame, mm: 50 on our sticker; the white square is 40) and a calibrated camera (camera.json from
             calibrate.py) it solves the sticker's pose like jig_vision's aruco method: corners + known size ->
             cv2.solvePnP(IPPE_SQUARE) -> T_cam_landmark; with the robot pose (--pose, or the photo's JSON) ->
             T_base_landmark: x, y, z (mm) and rz (deg) in the robot base.

Limits vs ArUco: every landmark looks the same (no id - one per scene, or tell them apart by where they are), and
the 4-turn choice depends on the print (text over curves). Without camera.json it still finds the sticker and
its turn in pixels (useful for a first look).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

WARP = 200  # px side of the rectified square


def _blue_mask(bgr):
    """Pixels clearly bluer than this patch's own white. Relative, because the TM camera tints white (white came
    out lavender, hue ~145, on 2026-11-20) and the printed curves are a pale blue."""
    b, g, r = [x.astype(np.int16) for x in cv2.split(bgr)]
    blueness = b - (r + g) // 2
    bright = (b + g + r) // 3 > 60
    ref = np.median(blueness[bright]) if bright.any() else 0
    return (((blueness - ref) > 12) & bright).astype(np.uint8) * 255


def _order(pts):
    """Corners in image order TL, TR, BR, BL (by angle around the centre)."""
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]  # from -pi: TL first for an upright square (y down)
    s = pts.sum(axis=1)
    return np.roll(pts, -int(np.argmin(s)), axis=0)


def _turn_score(w_bgr):
    """How well this warped square reads as 'text on top, blue curves below' (higher = better)."""
    h = w_bgr.shape[0]
    inner = w_bgr[int(h * .18):int(h * .82), int(h * .18):int(h * .82)]
    blue = _blue_mask(inner) > 0
    grey = cv2.cvtColor(inner, cv2.COLOR_BGR2GRAY)
    dark = (grey < 0.55 * np.median(grey)) & ~blue
    half = inner.shape[0] // 2
    return (blue[half:].mean() - blue[:half].mean()) + (dark[:half].mean() - dark[half:].mean())


def find_landmarks(bgr, min_area=400):
    """Returns a list of dicts: corners (4x2 float, TL TR BR BL of the sticker), score, centre."""
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thr = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 51, 15)
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    blue_all = _blue_mask(bgr)
    found = []
    for mask in (thr, otsu):
        cnts, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if area < min_area:
                continue
            approx = cv2.approxPolyDP(c, 0.04 * cv2.arcLength(c, True), True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue
            pts = _order(approx.reshape(4, 2).astype(np.float32))
            sides = [np.linalg.norm(pts[i] - pts[(i + 1) % 4]) for i in range(4)]
            if min(sides) / max(sides) < 0.5:
                continue
            dst = np.float32([[0, 0], [WARP, 0], [WARP, WARP], [0, WARP]])
            H = cv2.getPerspectiveTransform(pts, dst)
            w = cv2.warpPerspective(bgr, H, (WARP, WARP))
            g = cv2.cvtColor(w, cv2.COLOR_BGR2GRAY)
            centre = g[40:160, 40:160]
            blue = (_blue_mask(w[40:160, 40:160]) > 0).mean()
            dark = (centre < 0.55 * np.median(centre)).mean()  # the OMRON letters
            # a bright square holding dark letters and pale-blue curves: the landmark (the outline found may be
            # the outer edge of the black frame or its inner edge; the frame itself is not needed)
            if not (np.median(centre) > 120 and 0.01 < dark < 0.35 and blue > 0.01):
                continue
            scores = []
            for k in range(4):
                scores.append(_turn_score(np.rot90(w, -k).copy()))
            k = int(np.argmax(scores))
            # k clockwise quarter turns read it upright: each turn brings the previous corner to the top-left,
            # so the sticker's TL is image corner -k
            corners = np.roll(pts, k, axis=0)
            found.append({"corners": corners, "turn_score": float(scores[k]), "area": float(area),
                          "centre": corners.mean(axis=0), "blue": float(blue)})
    # duplicates (two masks, outer + inner frame edge): keep the biggest per place
    found.sort(key=lambda f: -f["area"])
    keep = []
    for f in found:
        if all(np.linalg.norm(f["centre"] - k["centre"]) > 0.5 * math.sqrt(k["area"]) for k in keep):
            keep.append(f)
    return keep


def tm_pose_to_T(p):
    """TM pose (mm, deg; Rx Ry Rz fixed-axis XYZ) -> 4x4."""
    x, y, z, rx, ry, rz = p
    a, b, c = np.radians([rx, ry, rz])
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    T = np.eye(4)
    T[:3, :3] = Rz @ Ry @ Rx
    T[:3, 3] = [x, y, z]
    return T


def landmark_pose(corners, size, K, dist):
    """T_cam_landmark (4x4, mm) from the 4 corners (TL TR BR BL) and the outer side length."""
    h = size / 2
    obj = np.float32([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]])  # x right, y up, z out of the sticker
    ok, rvec, tvec = cv2.solvePnP(obj, corners.astype(np.float32) + 0.5, K, dist,  # +0.5: our K convention (calibrate.HALF)
                                  flags=cv2.SOLVEPNP_IPPE_SQUARE)
    if not ok:
        return None
    T = np.eye(4)
    T[:3, :3] = cv2.Rodrigues(rvec)[0]
    T[:3, 3] = tvec.ravel()
    return T


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image")
    p.add_argument("--size", type=float, help="OUTER side of the black frame, mm (the outline found); our sticker: 50 (white square 40)")
    p.add_argument("--camera", help="camera.json from calibrate.py (K, dist, T_tool_cam)")
    p.add_argument("--pose", type=float, nargs=6, help="robot TCP pose when the photo was taken (TM, mm/deg)")
    p.add_argument("--overlay", help="write a picture with the corners drawn")
    a = p.parse_args(argv)

    bgr = cv2.imread(a.image)
    if bgr is None:
        sys.exit(f"can't read {a.image}")
    marks = find_landmarks(bgr)
    print(f"{len(marks)} landmark(s) in {Path(a.image).name}")
    for i, m in enumerate(marks):
        c = m["corners"]
        up = c[0] - c[3]  # BL -> TL: the sticker's 'up' in the image
        ang = math.degrees(math.atan2(up[0], -up[1]))  # 0 = text up in the image, + = turned clockwise
        print(f"  #{i}: centre px ({m['centre'][0]:.1f}, {m['centre'][1]:.1f}), turned {ang:+.1f} deg in the image, "
              f"side ~{math.sqrt(m['area']):.0f} px, turn certainty {m['turn_score']:.2f}")
        if a.size and a.camera:
            cam = json.loads(Path(a.camera).read_text())
            K, dist = np.array(cam["K"]), np.array(cam.get("dist", [0, 0, 0, 0, 0]))
            T_cl = landmark_pose(c, a.size, K, dist)
            print(f"     camera -> landmark: {np.round(T_cl[:3, 3], 1)} mm")
            if a.pose and "T_tool_cam" in cam:
                T_bl = tm_pose_to_T(a.pose) @ np.array(cam["T_tool_cam"]) @ T_cl
                rz = math.degrees(math.atan2(T_bl[1, 0], T_bl[0, 0]))
                print(f"     robot base: x {T_bl[0, 3]:.1f}  y {T_bl[1, 3]:.1f}  z {T_bl[2, 3]:.1f} mm, rz {rz:.1f} deg")
    if a.overlay:
        out = bgr.copy()
        for m in marks:
            c = m["corners"].astype(int)
            cv2.polylines(out, [c], True, (0, 255, 0), 2)
            for j, name in enumerate(("TL", "TR", "BR", "BL")):
                cv2.circle(out, tuple(c[j]), 4, (0, 0, 255), -1)
                cv2.putText(out, name, tuple(c[j] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        cv2.imwrite(a.overlay, out)
        print(f"overlay -> {a.overlay}")


if __name__ == "__main__":
    main()
