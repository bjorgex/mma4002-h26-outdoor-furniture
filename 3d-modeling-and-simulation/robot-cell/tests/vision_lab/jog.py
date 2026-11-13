"""Direct Move in the vision editor's Base tab: type the 6 fields, hold Move until reached.
usage: jog.py x y z rx ry rz [min_z]   (Line move; aborts if Z < min_z)"""
import ctypes, sys, time, socket, struct
u = ctypes.windll.user32
ctypes.windll.shcore.SetProcessDpiAwareness(2)
FX = 4656
FY = [1344, 1448, 1552, 1656, 1760, 1864]
MOVE = (4656, 2080)
vals = [float(v) for v in sys.argv[1:7]]
min_z = float(sys.argv[7]) if len(sys.argv) > 7 else -1e9


def click(x, y):
    u.SetCursorPos(x, y); time.sleep(0.1)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0); time.sleep(0.15)


def key(vk, up=False):
    u.keybd_event(vk, 0, 2 if up else 0, 0)


def type_text(t):
    key(0x11); key(0x41); key(0x41, True); key(0x11, True); time.sleep(0.05)  # ctrl+a
    key(0x2E); key(0x2E, True)  # delete
    for ch in t:
        vk = {"-": 0xBD, ".": 0xBE}.get(ch, ord(ch))
        key(vk); key(vk, True); time.sleep(0.02)


def pose():
    s = socket.create_connection(("10.0.12.101", 502), timeout=3)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 4, 7001, 12)); r = s.recv(64); s.close()
    return [struct.unpack(">f", r[9 + i:13 + i])[0] for i in range(0, 24, 4)]


for y, v in zip(FY, vals):
    click(FX, y); type_text(f"{v:.2f}")
click(FX - 300, 1200)  # unfocus
t0 = time.time()
while time.time() - t0 < 60:
    u.SetCursorPos(*MOVE); time.sleep(0.2)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.6); u.mouse_event(4, 0, 0, 0, 0)
    p = pose()
    print(" ".join(f"{a:.1f}" for a in p))
    if p[2] < min_z:
        print("ABORT: Z below", min_z); break
    if all(abs(a - b) < 0.3 for a, b in zip(p[:3], vals[:3])) and all(abs(((a - b + 180) % 360) - 180) < 0.3 for a, b in zip(p[3:], vals[3:])):
        print("reached"); break
