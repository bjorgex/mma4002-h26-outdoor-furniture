import os, sys
from PIL import Image, ImageChops
T = os.path.dirname(os.path.abspath(__file__))
REPO = sys.argv[1]
M = os.path.join(REPO, "assignment-5-industrial-review-board-presentation", "deck", "media")
os.makedirs(M, exist_ok=True)

def save(im, name, maxw=1800):
    im = im.convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(os.path.join(M, name), quality=88, optimize=True)
    print(name, im.size)

def autocrop(im, pad=40, thr=18):
    rgb = im.convert("RGB")
    bg = Image.new("RGB", rgb.size, rgb.getpixel((5, rgb.height // 2)))
    diff = ImageChops.difference(rgb, bg).convert("L").point(lambda v: 255 if v > thr else 0)
    l, t, r, b = diff.getbbox()
    return rgb.crop((max(0, l - pad), max(0, t - pad), min(rgb.width, r + pad), min(rgb.height, b + pad)))

def fit(im, ar, cx=0.5, cy=0.5):
    """crop to aspect ratio ar (w/h) around (cx, cy) fractions"""
    w, h = im.size
    if w / h > ar:
        nw = round(h * ar); x = min(max(0, round(cx * w - nw / 2)), w - nw); return im.crop((x, 0, x + nw, h))
    nh = round(w / ar); y = min(max(0, round(cy * h - nh / 2)), h - nh); return im.crop((0, y, w, y + nh))

# simulation action frames (1920x1080): drop header bar + status card
frames = {"sim_planks.jpg": 1, "sim_guide.jpg": 14, "sim_flip.jpg": 21, "sim_guide_out.jpg": 27}
for name, i in frames.items():
    im = Image.open(os.path.join(T, "shots", f"simclean_v8-full_{i:03d}.png"))
    save(fit(im.crop((300, 120, 1820, 1080)), 4 / 3, 0.5, 0.45), name, 1200)

# cell views (2400x1350 at 1.5x)
im = Image.open(os.path.join(T, "shots", "cell_iso.png")); save(im.crop((420, 180, im.width - 60, im.height - 40)), "cell_iso.jpg")
im = Image.open(os.path.join(T, "shots", "cell_overlays.png")); save(im.crop((0, 60, im.width, im.height)), "cell_overlays.jpg")
save(Image.open(os.path.join(T, "shots", "all_v8-full_003.png")), "dashboard_v8.jpg", 1920)
save(Image.open(os.path.join(T, "shots", "probe.png")), "dashboard_done.jpg", 1920)

# product shots from the configurator
for n in ["p_high_laser", "p_none_laser", "p_high_shield"]:
    save(autocrop(Image.open(os.path.join(T, "cfg2", n + ".png")), pad=60), n + ".jpg", 1400)
im = Image.open(os.path.join(T, "cfg2", "p_allee.png")); save(im, "p_allee.jpg")
im = Image.open(os.path.join(T, "cfg", "cfg_tool.png")); save(im.crop((60, 40, 1560, 1000)), "cfg_page.jpg")

# existing repo images
R = lambda *p: os.path.join(REPO, *p)
im = Image.open(R("3d-modeling-and-simulation", "jig-cad", "Jig V3", "Jig_V3_all.png")); save(autocrop(im.crop((im.width // 2 + 40, 40, im.width, im.height)), pad=30), "jig_v3_3d.jpg")
save(autocrop(Image.open(R("3d-modeling-and-simulation", "jig-cad", "Jig V3", "Guide_V3.png")), pad=20), "guide_split.jpg")
save(Image.open(R("3d-modeling-and-simulation", "robot-cell", "tests", "tmflow_demo_view.png")), "tmflow_demo.jpg")
im = Image.open(R("3d-modeling-and-simulation", "robot-cell", "tests", "robot_sim", "manipulability", "map_v8_best_mu3_vfix.png"))
save(im.crop((0, 80, im.width // 4 + 40, im.height)), "manip_map.jpg", 900)
