import socket, struct, time, sys
H = "10.0.12.101"
def coil(addr, on):
    s = socket.create_connection((H, 502), timeout=3)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 5, addr, 0xFF00 if on else 0)); r = s.recv(64); s.close()
    return "exception %d" % r[8] if r[7] & 0x80 else "ok"
def bits():
    s = socket.create_connection((H, 502), timeout=3)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 2, 7201, 5)); r = s.recv(64); s.close()
    b = r[9]; return {"error": b & 1, "running": b >> 1 & 1, "editing": b >> 2 & 1, "paused": b >> 3 & 1}
addr = int(sys.argv[1]) if len(sys.argv) > 1 else 7104
print("press", addr, coil(addr, True)); time.sleep(0.5); print("release", coil(addr, False))
for i in range(6):
    time.sleep(1); print(i + 1, "s:", bits())
