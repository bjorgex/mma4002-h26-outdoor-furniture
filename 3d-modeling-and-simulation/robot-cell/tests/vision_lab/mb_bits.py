import socket, struct, sys
def req(fc, addr, n, host="10.0.12.101"):
    s = socket.create_connection((host, 502), timeout=3)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, fc, addr, n)); r = s.recv(512); s.close()
    if r[7] & 0x80: return f"exception {r[8]}"
    data = r[9:9 + r[8]]
    return [(data[i // 8] >> (i % 8)) & 1 for i in range(n)]
names = ["7201 error", "7202 running", "7203 editing", "7204 paused", "7205 get control", "7206", "7207", "7208"]
bits = req(2, 7201, 8)
print("discrete inputs:", bits if isinstance(bits, str) else dict(zip(names, bits)))
print("coils 7101-7108 (read):", req(1, 7101, 8))
