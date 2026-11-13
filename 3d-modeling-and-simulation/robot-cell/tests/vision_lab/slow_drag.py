"""Slow, WPF-friendly drag: press, wiggle past the drag threshold, glide, hold, release.
usage: python slow_drag.py x0 y0 x1 y1   (physical virtual-desktop pixels)"""
import ctypes, sys, time

u = ctypes.windll.user32
ctypes.windll.shcore.SetProcessDpiAwareness(2)
DOWN, UP = 0x0002, 0x0004
x0, y0, x1, y1 = map(int, sys.argv[1:5])
HOLD = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3


def at(x, y):
    u.SetCursorPos(int(x), int(y))


at(x0, y0); time.sleep(0.3)
u.mouse_event(DOWN, 0, 0, 0, 0); time.sleep(HOLD)
for i in range(1, 11):            # small moves first so WPF starts the drag
    at(x0 + i, y0 + i); time.sleep(0.03)
steps = 60
for i in range(1, steps + 1):
    t = i / steps
    at(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t); time.sleep(0.02)
time.sleep(0.4)
u.mouse_event(UP, 0, 0, 0, 0)
print("dragged", x0, y0, "->", x1, y1)
