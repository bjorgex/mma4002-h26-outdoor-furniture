"""Low-level click: move, settle, press, hold, release. usage: slow_click.py x y [hold]"""
import ctypes, sys, time
u = ctypes.windll.user32; ctypes.windll.shcore.SetProcessDpiAwareness(2)
x, y = int(sys.argv[1]), int(sys.argv[2]); hold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
u.SetCursorPos(x - 3, y - 3); time.sleep(0.15); u.SetCursorPos(x, y); time.sleep(0.25)
u.mouse_event(2, 0, 0, 0, 0); time.sleep(hold); u.mouse_event(4, 0, 0, 0, 0)
print("clicked", x, y)
