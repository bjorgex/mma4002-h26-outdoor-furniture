"""Safe approach to the vision-found plank guide via Listen node: up, over at safe height, down.
usage: approach.py [final_z]"""
import socket, time, re, sys

H = "10.0.12.101"
SAFE_Z = 497.6
FINAL_Z = float(sys.argv[1]) if len(sys.argv) > 1 else 462.0


def packet(header, data):
    body = f"{header},{len(data.encode())},{data},"; cs = 0
    for b in body.encode(): cs ^= b
    return f"${body}*{cs:02X}\r\n".encode()


s = socket.create_connection((H, 5890), timeout=5)
buf = b""


def reply(prefix):
    global buf
    while True:
        while b"\r\n" not in buf:
            buf += s.recv(4096)
        line, buf = buf.split(b"\r\n", 1)
        line = line.decode(errors="replace")
        if line.startswith(prefix):
            return line


n = 0


def script(code):
    global n
    n += 1
    s.sendall(packet("TMSCT", f"{n},{code}"))
    r = reply("$TMSCT")
    if ",OK" not in r:
        raise RuntimeError(f"{code!r}: {r}")


def ask(code, tag):
    s.sendall(packet("TMSCT", f"99,{code}"))
    while True:
        line = reply("$TMSTA")
        if f",{tag}," in line:
            reply("$TMSCT")
            return line


def move(cmd, tag):
    script(cmd + f"\r\nQueueTag({tag},0)")
    while True:
        s.sendall(packet("TMSTA", f"01,{tag}"))
        f = reply("$TMSTA").split(",")
        if f[3] == str(tag) and f[4] == "true":
            return
        time.sleep(0.3)


vb = ask('float[] vb = Base["vision_FindPlank"].Value\r\nListenSend(93, vb[0] + "," + vb[1] + "," + vb[2] + "," + vb[3] + "," + vb[4] + "," + vb[5])', 93)
x, y, z, rx, ry, rz = [float(v) for v in re.search(r",93,([^*]*),\*", vb).group(1).split(",")]
print("vision base:", x, y, z, rx, ry, rz)
grip_rz = rz + 180 if rz < 0 else rz - 180
script('ChangeBase("RobotBase")')
cur = ask('float[] p = Robot[0].CoordRobot\r\nListenSend(94, p[0] + "," + p[1] + "," + p[2] + "," + p[3] + "," + p[4] + "," + p[5])', 94)
cx, cy, cz, crx, cry, crz = [float(v) for v in re.search(r",94,([^*]*),\*", cur).group(1).split(",")]
print("current:", cx, cy, cz)
SPEED = 40  # mm/s
print("1 up");   move(f'Line("CAP",{cx:.2f},{cy:.2f},{SAFE_Z},{crx:.2f},{cry:.2f},{crz:.2f},{SPEED},300,0,false)', 1)
print("2 over"); move(f'Line("CAP",{x:.2f},{y:.2f},{SAFE_Z},-180,0,{grip_rz:.2f},{SPEED},300,0,false)', 2)
print("3 down"); move(f'Line("CAP",{x:.2f},{y:.2f},{FINAL_Z},-180,0,{grip_rz:.2f},20,300,0,false)', 3)
print("done")
s.close()
