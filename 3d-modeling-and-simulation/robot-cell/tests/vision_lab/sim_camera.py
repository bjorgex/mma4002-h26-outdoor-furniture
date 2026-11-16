"""Tool camera in the simulator, from the command line (the same as the 3D page's Photo button, for scripts / Claude).

Needs: python tests/tmflow_mock.py serve --sim   and   http://127.0.0.1:8090/all open in a browser (the page renders).

  python tests/vision_lab/sim_camera.py snap                      # photo -> tests/vision_lab/sim_shots/<stamp>.png + .json
  python tests/vision_lab/sim_camera.py pose                      # the mock's flange pose (x y z rx ry rz) and joints
  python tests/vision_lab/sim_camera.py move X Y Z RX RY RZ [--speed 50]
        # Line to that flange pose (robot base, mm/deg) through the mock's Listen node - the same packets the real
        # robot takes. Goes UP to --safe-z first, over, then down (feedback-robot-motion-safety), unless --direct.
"""
import argparse
import json
import socket
import sys
import time
import urllib.request
from pathlib import Path

HOST = "127.0.0.1"


def http(method, path, body=None, port=8090, timeout=10):
    req = urllib.request.Request(f"http://{HOST}:{port}{path}", method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def snap(port=8090, timeout=15, renderer=False, xyz=False):
    """Photo from the tool camera -> {path, json}. renderer: only the page at /all?renderer may take it (tests)."""
    code, r = http("POST", "/vision/request", {"renderer": renderer, "xyz": xyz}, port)
    if code != 200:
        sys.exit(f"request failed ({code}): {r}")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            code, out = http("GET", f"/vision/result?id={r['id']}", port=port)
        except (TimeoutError, urllib.error.URLError):     # server busy (e.g. a page loading the cell): ask again
            code = None
        if code == 200:
            return out
        time.sleep(0.3)
    sys.exit("no photo: is http://127.0.0.1:8090/all open in a browser (and the 3D pane loaded)?")


# ---- Listen node (same framing as the real robot: tests/vision_lab/approach.py) --------------------------------
def packet(header, data):
    body = f"{header},{len(data.encode())},{data},"
    cs = 0
    for b in body.encode():
        cs ^= b
    return f"${body}*{cs:02X}\r\n".encode()


class Listen:
    def __init__(self, port=5890):
        self.s = socket.create_connection((HOST, port), timeout=10)
        self.buf, self.n = b"", 0

    def reply(self, prefix):
        while True:
            while b"\r\n" not in self.buf:
                self.buf += self.s.recv(4096)
            line, self.buf = self.buf.split(b"\r\n", 1)
            line = line.decode(errors="replace")
            if line.startswith(prefix):
                return line

    def script(self, code):
        self.n += 1
        self.s.sendall(packet("TMSCT", f"{self.n},{code}"))
        r = self.reply("$TMSCT")
        if ",OK" not in r:
            raise RuntimeError(f"{code!r}: {r}")

    def move(self, pose, speed, tag):
        x, y, z, rx, ry, rz = pose
        self.script(f'Line("CAP",{x:.2f},{y:.2f},{z:.2f},{rx:.2f},{ry:.2f},{rz:.2f},{speed:g},300,0,false)\r\n'
                    f"QueueTag({tag},0)")
        while True:
            self.s.sendall(packet("TMSTA", f"01,{tag:02d}"))
            f = self.reply("$TMSTA").split(",")
            if len(f) > 4 and f[3].isdigit() and int(f[3]) == tag and f[4] == "true":
                return
            time.sleep(0.2)


def current(slave=5891):
    """(joints, flange pose) from the mock's Ethernet Slave stream (teach.py's reader), or None."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "robot_sim"))
        import teach
        st = teach.Stream(HOST, slave)
        try:
            joints, flange = st.read()[-1]
        finally:
            st.close()
        return joints, flange
    except (Exception, SystemExit):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["snap", "pose", "move"])
    ap.add_argument("pose", nargs="*", type=float)
    ap.add_argument("--speed", type=float, default=50)
    ap.add_argument("--safe-z", type=float, default=450, help="travel height for move (flange z, mm)")
    ap.add_argument("--direct", action="store_true", help="one straight Line, no up-over-down")
    ap.add_argument("--port", type=int, default=8090, help="the mock's view port")
    ap.add_argument("--listen", type=int, default=5890)
    a = ap.parse_args()
    if a.cmd == "snap":
        out = snap(a.port)
        print(out["path"])
        print(out["json"])
        return
    if a.cmd == "pose":
        c = current()
        if not c:
            sys.exit("no pose: is the mock running (Ethernet Slave on 5891)?")
        print("flange:", " ".join(f"{v:.2f}" for v in c[1]))
        print("joints:", " ".join(f"{v:.2f}" for v in c[0]))
        return
    if len(a.pose) != 6:
        sys.exit("move takes X Y Z RX RY RZ")
    L = Listen(a.listen)
    if a.direct:
        L.move(a.pose, a.speed, 1)
    else:
        x, y, z, rx, ry, rz = a.pose
        c = current()
        if c:
            cur = c[1]
            L.move([cur[0], cur[1], max(a.safe_z, cur[2]), *cur[3:]], a.speed, 1)
        L.move([x, y, max(a.safe_z, z), rx, ry, rz], a.speed, 2)
        L.move(a.pose, a.speed, 3)
    print("done")


if __name__ == "__main__":
    main()
