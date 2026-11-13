"""Send script lines to the running Listen node and print every raw reply. usage: listen_try.py 'line1' 'line2' ..."""
import socket, sys, time
def packet(header, data):
    body = f"{header},{len(data.encode())},{data},"; cs = 0
    for b in body.encode(): cs ^= b
    return f"${body}*{cs:02X}\r\n".encode()
s = socket.create_connection(("10.0.12.101", 5890), timeout=3)
def ask(header, data, wait=1.5):
    s.sendall(packet(header, data)); time.sleep(wait); out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c: break
            out += c
    except socket.timeout: pass
    return out.decode(errors="replace").strip()
print("STA 00 ->", ask("TMSTA", "00"))
for i, line in enumerate(sys.argv[1:], 1):
    print(f"SCT {line!r} ->", ask("TMSCT", f"{i},{line}"))
s.close()
