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
import json
import os
import re
import socket
import subprocess
import sys
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
        # the page's "j" stream (3D pane) asks self.robot.sample() for (at, joints): the real joints, as of now
        self.robot = SimpleNamespace(sample=lambda: (time.time() - tm.T0, list(self.live["joints"])))
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


class RealScenarios:
    """The page's Run / Stop (/all) on the REAL robot: the chosen preset from scenarios.json runs as
    "demo_viewer.py run <script> <args>", so it talks to the robot's Listen node (lt.IP) and its steps come to this
    page. Only HandE_Bridge_v1 presets (flow "hande"); the mock's grip/fast settings mean nothing here. The script's
    Enter prompts are answered (Run is the go-ahead). Stop kills the script: moves the robot already queued still
    run, so the E-stop is the real stop."""

    def __init__(self, a):
        self.a, self.proc, self.name, self.state, self.code, self.stopped = a, None, None, "idle", None, False
        self.lines, self.err = [], None
        self.lock = threading.Lock()

    def list(self):
        return [s for s in json.loads(tm.SCENARIOS.read_text(encoding="utf-8")) if s.get("flow", "hande") == "hande"]

    def status(self):
        return {"t": "scenario", "name": self.name, "state": self.state, "code": self.code, "fast": 1,
                "fast_user": False, "robodk": False, "rdk_busy": False, "station": None,
                "error": self.err if self.state == "failed" else None, "env": "real", "robot": self.a.robot}

    def _set(self, state, code=None):
        if state == "running" and self.state != "running":
            self.t0 = time.time()                       # wall clock: the real assembly time
        if state == "finished" and self.state == "running" and self.name:
            tm.save_run_time(self.name, "real", time.time() - self.t0)
        self.state, self.code = state, code
        self.err = tm.error_line(self.lines) if state == "failed" else None
        if state != "running":                          # a script that ended can't be on hold any more
            tm.VIEW.hold = None
        tm.emit(**self.status())

    def preflight(self):
        """None if the robot is ready for a run (Listen node open and TMflow in it), else why not - in plain words."""
        ip = self.a.robot
        try:
            s = socket.create_connection((ip, lt.LISTEN), timeout=2)
        except OSError:
            if not tm.VIEW.live.get("link"):
                return f"No robot: {ip} does not answer (cable / network / controller off?)"
            return (f"Robot {ip} is on, but TMflow is not in a Listen node (port {lt.LISTEN} closed): "
                    "start HandE_Bridge_v1 and wait for the Bridge node")
        try:
            s.settimeout(3)
            s.sendall(lt.packet("TMSTA", "00"))
            buf = b""
            while b"\r\n" not in buf:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
            reply = buf.decode(errors="replace")
        except OSError as e:
            return f"Robot {ip}: no answer from the Listen node ({e}) - is another script connected?"
        finally:
            s.close()
        if ",true," not in reply:
            return f"Robot {ip}: TMflow is not in a Listen node right now ({reply.strip()[:60]})"
        return None

    def run(self, name):
        sc = {s["name"]: s for s in self.list()}.get(name)
        if not sc:
            return 404, f"no scenario {name!r}"
        why = self.preflight()
        if why:
            self.name, self.lines = name, [why]
            self._set("failed")
            return 503, why
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return 409, f"{self.name} is still running: stop it first"
            self.name, self.stopped = name, False
            tm.VIEW.reset()                                 # pages opened from now on don't replay the run before
            tm.emit("reset", flow="hande", title=tm.VIEW.flow.title, cell=sc.get("cell", "cell"))
            cmd = [sys.executable, str(Path(__file__).resolve()), "run", "--view", str(self.a.port), sc["script"]] \
                + [str(x) for x in sc.get("args", [])]
            tm.log(f"REAL ROBOT {self.a.robot}: scenario {name}: {sc['script']} {' '.join(map(str, sc.get('args', [])))}")
            self.proc = subprocess.Popen(cmd, cwd=HERE.parent, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                         env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
            self._set("running")
            threading.Thread(target=self._watch, args=(self.proc,), daemon=True).start()
        return 200, "started on the real robot"

    def _watch(self, proc):
        try:
            proc.stdin.write("\n" * 200)
            proc.stdin.close()
        except OSError:
            pass
        self.lines = []
        for line in proc.stdout:
            line = line.rstrip("\r\n")
            tm.emit("out", line=line)
            self.lines = (self.lines + [line])[-60:]
            print(line, flush=True)
        code = proc.wait()
        if proc is self.proc:
            self._set("stopped" if self.stopped else "finished" if code == 0 else "failed", code)

    def stop(self):
        with self.lock:
            if not (self.proc and self.proc.poll() is None):
                return 409, "nothing is running"
            self.stopped = True
            self.proc.kill()
            self.proc.wait()
        return 200, "script stopped (queued robot moves may still run: E-stop)"

    def reset_all(self):
        """The page's Reset on the REAL robot: stops the script if one runs and puts the 3D view's parts back at the
        start. The robot itself is not moved (Home is TMflow's job)."""
        with self.lock:
            if self.proc and self.proc.poll() is None:
                self.stopped = True
                self.proc.kill()
                self.proc.wait()
            cell = next((s.get("cell", "cell") for s in self.list() if s.get("default")), "cell_v8")
            tm.VIEW.reset()
            tm.emit("reset", flow="hande", title=tm.VIEW.flow.title, cell=cell)
            self.name, self.lines, self.err = None, [], None
            self._set("idle")
        return 200, "reset: 3D parts at the start (the real robot is not moved)"

    def robodk_reset(self):
        return 404, "no RoboDK on the real-robot viewer"


def view(a):
    tm.VIEW = RobotView(a.port, a.robot)
    tm.VIEW.scenarios = RealScenarios(a)
    if a.cell != "cell":                                # the 3D pane's cell (robot_sim/<cell>.glb), e.g. cell_v8
        tm.emit("reset", flow="hande", title=tm.VIEW.flow.title, cell=a.cell)   # in the backlog: every page gets it
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
    v.add_argument("--cell", default="cell", help="3D cell: cell (v4, default), cell_v5, cell_v8")
    r = sub.add_parser("run", help="run a script against the real robot, its steps shown on the page")
    r.add_argument("--view", type=int, default=8090, help="the viewer's port (default 8090)")
    r.add_argument("script")
    r.add_argument("args", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    view(a) if a.cmd == "view" else run(a)
