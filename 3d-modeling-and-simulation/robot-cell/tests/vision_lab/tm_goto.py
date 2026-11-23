"""Drive the robot to a pose through TMflow's vision-editor Direct Move (Base tab): type X..Rz, hold Move (hold-to-run,
claude_cursor releases it if Bjørge touches the mouse), check the pose over Modbus, repeat the hold until there.
Stops on a robot error or if not there after 4 holds.   Usage: tm_goto.py X Y Z RX RY RZ"""
import socket, struct, subprocess, sys, os, time
CC = [r"C:\Python313\python.exe", os.path.expandvars(r"%USERPROFILE%\dev\dotfiles\windows\claude-cursor\claude_cursor.py"),
      "tmflow-vision"]
H = "10.0.12.101"


def mb(fc, addr, n):
    s = socket.create_connection((H, 502), timeout=3)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, fc, addr, n)); r = s.recv(512); s.close()
    return r[9:9 + r[8]]


def pose():
    return list(struct.unpack(">6f", mb(4, 7001, 12)))


def error():
    return mb(2, 7201, 1)[0] & 1


def cc(*a):
    r = subprocess.run(CC + list(a), capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"claude_cursor {a[0]} failed: {r.stdout}{r.stderr}")


target = [float(v) for v in sys.argv[1:7]]
for i, v in enumerate(target):
    cc("click-at", "1790", str(732 + 52 * i), "--allow-raw", "--hover", "--keep-focus")
    cc("keys", "ctrl+a", "--allow-raw", "--keep-focus")
    cc("type", f"{v:.1f}", "--allow-raw", "--keep-focus")
start = pose()
d0 = max(abs(start[i] - target[i]) for i in range(3))
for attempt in range(4):
    cc("hold", "DirectMove.Move", "8", "--allow-robot", "--keep-focus")
    if attempt == 0 and d0 > 2:                      # 2026-11-20: on the Tool tab "up" went DOWN - stop if not closer
        p = pose()
        if max(abs(p[i] - target[i]) for i in range(3)) >= d0 - 1:
            sys.exit(f"NOT GETTING CLOSER to the target - stopped (Direct Move on the Base tab?). pose {p}")
    time.sleep(0.5)
    if error():
        sys.exit(f"ROBOT ERROR after hold {attempt + 1} - stopped. pose {pose()}")
    p = pose()
    dp = max(abs(p[i] - target[i]) for i in range(3))
    da = max(abs(((p[i] - target[i] + 180) % 360) - 180) for i in range(3, 6))
    print(f"  hold {attempt + 1}: off by {dp:.2f} mm / {da:.2f} deg")
    if dp < 0.5 and da < 0.3:
        print("  reached", [round(x, 2) for x in p]); sys.exit(0)
sys.exit("NOT REACHED after 4 holds - stopped")
