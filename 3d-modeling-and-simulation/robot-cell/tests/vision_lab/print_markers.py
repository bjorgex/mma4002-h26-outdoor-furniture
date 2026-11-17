"""Printable A4 sheets (1:1) for the real cell: the jig markers and the ChArUco calibration board.

  python tests/vision_lab/print_markers.py [--size 30]     -> print/jig_markers_<size>mm.pdf, print/charuco_board.pdf

Print at 100 % ("actual size", no "fit to page"), then measure the 100 mm scale bar: it must be 100 mm (+-0.5).
Glue the board on something flat and stiff (a bent board ruins the calibration).

Jig markers: ArUco DICT_4X4_50, ids 1-3 = Base A, Base B, Guide (as in the sim, 3 only - 2026-11-17: not
Plank rack, not a second one for Guide big), 4-10 spare. The size is the black square; keep the white
margin around it when cutting.
Board: ChArUco 7 x 5 squares of 30 mm, markers 22 mm, DICT_5X5_100 (a different dictionary, so it is never taken
for a jig marker). These numbers are in BOARD below and used by calibrate.py - change both or neither.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "print"
PX = 10                                                  # px per mm (254 dpi)
A4 = (210 * PX, 297 * PX)
JIG_IDS = {1: "Base A", 2: "Base B", 3: "Guide"}
BOARD = {"squares": (7, 5), "square_mm": 30.0, "marker_mm": 22.0, "dict": "DICT_5X5_100"}


def font(size):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def scale_bar(d, x, y):
    d.rectangle([x, y, x + 100 * PX, y + 3 * PX], fill=0)
    for k in range(11):
        d.line([x + k * 10 * PX, y - 2 * PX, x + k * 10 * PX, y], fill=0, width=3)
    d.text((x, y + 4 * PX), "100 mm - measure this after printing (must be 100 mm)", fill=0, font=font(28))


def jig_sheet(size_mm):
    img = Image.new("L", A4, 255); d = ImageDraw.Draw(img)
    d.text((15 * PX, 10 * PX), f"Jig markers - ArUco 4x4_50, black square {size_mm:g} mm. Keep the white border.", fill=0, font=font(40))
    dic = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    cell = size_mm * PX
    ids = list(range(1, 11))
    for k, i in enumerate(ids):
        col, row = k % 2, k // 2
        x0, y0 = int(20 * PX + col * 95 * PX), int(30 * PX + row * 50 * PX)
        m = cv2.aruco.generateImageMarker(dic, i, int(round(cell)))
        img.paste(Image.fromarray(m), (x0 + int(cell / 6), y0 + int(cell / 6)))
        w = int(cell + cell / 3)
        d.rectangle([x0, y0, x0 + w, y0 + w], outline=180, width=2)            # cut line (white margin = 1 cell)
        d.text((x0 + w + 4 * PX, y0 + 2 * PX), f"id {i}", fill=0, font=font(44))
        d.text((x0 + w + 4 * PX, y0 + 9 * PX), JIG_IDS.get(i, "spare"), fill=0, font=font(34))
        d.text((x0 + w + 4 * PX, y0 + 15 * PX), f"{size_mm:g} mm", fill=0, font=font(30))
    scale_bar(d, 20 * PX, 280 * PX)
    return img


def board_sheet():
    img = Image.new("L", A4, 255); d = ImageDraw.Draw(img)
    sx, sy = BOARD["squares"]; sq = BOARD["square_mm"]
    b = cv2.aruco.CharucoBoard((sx, sy), sq, BOARD["marker_mm"], cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, BOARD["dict"])))
    im = b.generateImage((int(sx * sq * PX), int(sy * sq * PX)), marginSize=0)
    x0, y0 = int((210 - sx * sq) / 2 * PX), int(40 * PX)
    img.paste(Image.fromarray(im), (x0, y0))
    d.text((15 * PX, 10 * PX), f"ChArUco calibration board: {sx} x {sy} squares of {sq:g} mm, markers {BOARD['marker_mm']:g} mm, {BOARD['dict']}",
           fill=0, font=font(36))
    d.text((15 * PX, 18 * PX), "Glue flat on a stiff plate. The board's origin is the top-left corner of the chessboard (marked O).",
           fill=0, font=font(30))
    d.text((x0 - 8 * PX, y0 - 7 * PX), "O", fill=0, font=font(50))
    d.text((x0 + 4 * PX, y0 + int(sy * sq * PX) + 3 * PX), "x ->   (y runs down the page, z into the board)", fill=0, font=font(30))
    scale_bar(d, 20 * PX, 280 * PX)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=float, default=30, help="jig marker black square, mm")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    bw = lambda im: im.point(lambda v: 255 if v > 127 else 0, "1")     # pure black/white: sharp edges, no JPEG
    bw(jig_sheet(a.size)).save(OUT / f"jig_markers_{a.size:g}mm.pdf", resolution=25.4 * PX)
    bw(board_sheet()).save(OUT / "charuco_board.pdf", resolution=25.4 * PX)
    b = cv2.aruco.CharucoBoard(BOARD["squares"], BOARD["square_mm"], BOARD["marker_mm"],
                               cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, BOARD["dict"])))
    cv2.imwrite(str(HERE.parent / "robot_sim" / "markers" / "charuco_board.png"),
                cv2.copyMakeBorder(b.generateImage((7 * 30 * 4, 5 * 30 * 4), marginSize=0), 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255))
    print("written:", *sorted(p.name for p in OUT.glob("*.pdf")))


if __name__ == "__main__":
    main()
