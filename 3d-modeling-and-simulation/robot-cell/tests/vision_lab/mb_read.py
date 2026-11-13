import socket, struct
def read(fc, addr, n, unit=1, host="10.0.12.101"):
    s = socket.create_connection((host, 502), timeout=3)
    req = struct.pack(">HHHBBHH", 1, 0, 6, unit, fc, addr, n)
    s.sendall(req); r = s.recv(512); s.close()
    if r[7] & 0x80: return f"exception {r[8]}"
    data = r[9:9 + r[8]]
    return [struct.unpack(">f", data[i:i+4])[0] for i in range(0, len(data), 4)]
print("TCP pose (FC04 7001, 6 floats):", read(4, 7001, 12))
print("Joints   (FC04 7013, 6 floats):", read(4, 7013, 12))
