"""Viewer only, for the real TM5-900: serves the audience page /demo (and the detailed view /) and reads the
robot's Ethernet Slave stream (5891) for joints and flange pose, read-only. It sends nothing to the robot: the
Listen node (5890) is talked to by the script alone, exactly as when it runs on its own.

From robot-cell/, shared venv. TMflow: HandE_Bridge_v1 running, Ethernet Slave on (as for demo_run.py).
Terminal 1, the viewer (Ctrl+C to stop), then open http://127.0.0.1:8090/demo:
    python tests/demo_viewer.py view --robot 10.0.12.101
Terminal 2, the script unchanged (robot IP and all); its step calls go to the page:
    python tests/demo_viewer.py run demo_run.py --step
    python tests/demo_viewer.py run hande_bridge.py pickplace --air
Against the mock instead of the robot: view --robot 127.0.0.1 --port 8092 while tmflow_mock.py serve runs,
and run --view 8092 ... (the mock's own run sends the steps to the mock's view).
"""
import argparse
import re
import socket
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import tmflow_mock as tm
from tmflow_mock import HERE, lt


class RobotView(tm.View):
    """tmflow_mock's live view, its state from the robot's Ethernet Slave stream instead of the mock robot."""

    def __init__(self, port, ip):
        super().__init__(port, HERE / "listen_loop_flow.html")
        self.flow = SimpleNamespace(name="hande", title=f"HandE_Bridge_v1 on the real robot {ip} (view only)")
        self.ip, self.live = ip, {"joints": [0] * 6, "flange": [0] * 6, "running": False, "error": 0, "link": False}
        threading.Thread(target=self._slave, daemon=True).start()

    def _slave(self):
        """Read 5891 for good: the controller streams to whoever connects, nothing is ever sent back."""
        while True:
            try:
                with socket.create_connection((self.ip, lt.SLAVE), timeout=3) as s:
                    tm.log(f"reading the Ethernet Slave stream on {self.ip}:{lt.SLAVE}")
                    buf = b""
                    while True:
                        data = s.recv(4096)
                        if not data:
                            break
                        pkt, buf = tm.take_packet(buf + data)
                        while pkt:
                            if pkt[0] == "TMSVR":
                                self._take(pkt[1])
                            pkt, buf = tm.take_packet(buf)
            except OSError as e:
                tm.log(f"no Ethernet Slave stream on {self.ip}:{lt.SLAVE} ({e}), retrying")
            self.live["link"] = False
            time.sleep(2)

    def _take(self, content):
        get = lambda key: re.search(key + r"=(\{[^}]*\}|[^\r\n]*)", content)   # noqa: E731
        for key, name in (("Joint_Angle", "joints"), ("Coord_Robot_Flange", "flange")):
            m = get(key)
            if m:
                self.live[name] = [float(v) for v in m.group(1).strip("{}").split(",")]
        run, err = get("Project_Run"), get("Robot_Error")
        self.live["running"] = bool(run) and run.group(1).strip().lower() == "true"
        self.live["error"] = int(err.group(1)) if err and err.group(1).strip().isdigit() else 0
        self.live["link"] = True

    def state(self):
        v = self.live
        return {"t": "state", "at": round(time.time() - tm.T0, 2), "joints": v["joints"], "flange": v["flange"],
                "busy": False, "queued": 0, "last": None, "error": "Robot_Error" if v["error"] else None,
                "node": None, "listening": False, "running": v["running"], "vars": {},
                "gripper": "?", "link": v["link"], "real": True}


def view(a):
    tm.VIEW = RobotView(a.port, a.robot)
    tm.log(f"view only, robot {a.robot}: http://{tm.HOST}:{a.port}/demo  (detailed: http://{tm.HOST}:{a.port}/)")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        tm.log("viewer stopped")


def run(a):
    """The script as from the command line, nothing redirected: only its step calls are posted to the viewer."""
    path = Path(a.script)
    path = (path if path.exists() else HERE / path.name).resolve()
    tm.run_traced(path, a.args, a.view)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("view", help="serve /demo and read the robot's state stream")
    v.add_argument("--robot", default=lt.IP, help=f"robot controller IP (default {lt.IP})")
    v.add_argument("--port", type=int, default=8090, help="page port (default 8090)")
    r = sub.add_parser("run", help="run a script against the real robot, its steps shown on the page")
    r.add_argument("--view", type=int, default=8090, help="the viewer's port (default 8090)")
    r.add_argument("script")
    r.add_argument("args", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    view(a) if a.cmd == "view" else run(a)
