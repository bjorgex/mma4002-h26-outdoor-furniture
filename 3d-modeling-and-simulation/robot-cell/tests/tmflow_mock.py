"""Fake TMflow + TM5-900 on this PC, so the Listen-node scripts run without the robot or the lab
network. Speaks the same protocol on the same ports, but on 127.0.0.1:
    5890  Listen node: $TMSTA status (00 = which Listen node, 01 = QueueTag done), $TMSCT scripts
    5891  Ethernet Slave stream: $TMSVR with Joint_Angle and Coord_Robot_Flange, 50 Hz
and plays one of the TMflow projects the scripts are written for (node by node, gripper nodes
included): Listen nodes accept Line/PTP/QueueTag/var_x = .../ScriptExit(), moves take as long as
their speed says, GRIP answers OK, FAIL or LOSS as told by --grip.

Terminal 1, the mock (Ctrl+C to stop; serve again to restart the "project"):
    python robot_cell/tests/tmflow_mock.py serve                    HandE_Bridge_v1 (hande_bridge.py)
    python robot_cell/tests/tmflow_mock.py serve --flow testjb2     listen_loop_test.py
    python robot_cell/tests/tmflow_mock.py serve --flow testproject listen_pick_place_test.py run
    python robot_cell/tests/tmflow_mock.py serve --robodk           + IK and the robot moving in RoboDK
    python robot_cell/tests/tmflow_mock.py serve --grip ok,loss     GRIP results, in turn (default ok)
    python robot_cell/tests/tmflow_mock.py serve --fast 5           everything 5x faster than real time
                                                                    (live: /all's Speed slider, POST /speed)
Live view (the TMflow diagram + Listen-node conversation from listen_loop_flow.html, lit up as it
happens): open http://127.0.0.1:8090 in a browser while serve runs (--view 0 turns it off).
For an audience: http://127.0.0.1:8090/demo, the step the script is in, in plain words (fed by run below).
Terminal 2, any test script unchanged, its robot IP pointed at the mock:
    python robot_cell/tests/tmflow_mock.py run hande_bridge.py pickplace --air
    python robot_cell/tests/tmflow_mock.py run robodk_mirror.py
--robodk uses the robot in RoboDK's open station (or adds Omron-TM5-900.robot to an empty one),
in simulation mode only. Second RoboDK instance: $env:ROBODK_API_PORT=20601 before serve.
--sim instead: our own TM5-900 kinematics (robot_sim/tm5_kin.py, no RoboDK). Either way the 3D cell view
(robot_sim/sim_view.html) is at http://127.0.0.1:8090/sim/, and everything on one page (flow, script side +
demo steps, 3D cell) at http://127.0.0.1:8090/all, all fed by the same /events ("j": joints 25 times a second with
the time they are for, which the 3D pane plays back a little behind, interpolated). With --robodk a scenario's
"station" (scenarios.json) is loaded first if another one is open (closed without saving, one station at a time).
Under run, the script's own time.sleep follows the speed slider too. Next to another mock: serve
and run both take --listen/--slave (ports) and --view, e.g. serve --listen 7890 --slave 7891 --view 8097.
"""
import argparse
import itertools
import json
import math
import os
import queue
import re
import runpy
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import listen_pick_place_test as lt                     # noqa: E402  packet(), ports, points file
ROBOT_PORTS = (lt.LISTEN, lt.SLAVE)                     # the real robot's ports, before --listen/--slave

HOST = "127.0.0.1"
DT = 0.02                                               # motion/animation step, wall clock [s]
MAX_STEP = 0.06                                         # a step that took longer (RoboDK busy) counts as this long:
                                                        # the motion slows down instead of jumping to catch up
JOINT_HZ = 25                                           # "j" joint samples to each /events client [Hz]
SLEEP_MIN = 0.05                                        # run: the script's waits scaled by the speed, down to this [s]
JOINT_SPEED = 180                                       # TM5-900 joint speed at PTP 100 % [deg/s]
HOME_SPEED = 20                                         # TMflow point nodes (Home, P3) [% PTP]
NODE_TIME = {"set": 3, "grip": 4, "release": 3, "leave": 0.5}   # gripper nodes, node switch [s]

# TMflow projects, as the scripts' docstrings describe them. Node: (kind, next) where next is a node
# name, for "grip" {result: node}, for "gateway" ({var_cmd value: node}, else node).
FLOWS = {
    "hande": ("HandE_Bridge_v1", "Home", {"var_cmd": 0}, {
        "Home": ("home", "SET1"),
        "SET1": ("set", "Listen1"),
        "Listen1": ("listen", "Gateway"),               # Bridge
        "Gateway": ("gateway", ({1: "GRIP1", 2: "RELEASE1", 3: "Home2"}, "Stop")),
        "GRIP1": ("grip", {"ok": "Listen1", "fail": "Listen2", "loss": "Listen2"}),
        "RELEASE1": ("release", "Listen1"),
        "Home2": ("home", "Listen1"),
        "Listen2": ("listen", "Listen1"),               # Lost
    }),
    "testjb2": ("testjb2", "P3", {}, {
        "P3": ("home", "SET1"),
        "SET1": ("set", "Listen1"),
        "Listen1": ("listen", "RELEASE1"),
        "RELEASE1": ("release", "Listen2"),
        "Listen2": ("listen", "GRIP1"),
        "GRIP1": ("grip", {"ok": "Listen1", "fail": "Listen1", "loss": "Listen3"}),
        "Listen3": ("listen", "Stop"),
    }),
    "testproject": ("TestProject", "SET1", {}, {
        "SET1": ("set", "RELEASE1"),
        "RELEASE1": ("release", "Listen1"),
        "Listen1": ("listen", "GRIP1"),
        "GRIP1": ("grip", {"ok": "Listen2", "fail": "Listen2", "loss": "Listen2"}),
        "Listen2": ("listen", "RELEASE2"),
        "RELEASE2": ("release", "Listen3"),
        "Listen3": ("listen", "Stop"),
    }),
}

T0 = time.time()
VIEW = None                                             # the live view, when serve runs with --view
LIVE = {}                                               # the robot and flow now (a scenario reset swaps them)
SCENARIOS = HERE / "scenarios.json"                     # what the page's Run button may start (whitelist)


def emit(t, **ev):
    if VIEW:
        VIEW.emit({"t": t, **ev})


class Clock:
    """The time scale (x real time), live: the page's speed slider (POST /speed) changes it mid-run, for the move in
    progress too (what is left of it runs at the new rate), the gripper/node waits and every scenario after."""
    LO, HI = 0.25, 50

    def __init__(self, fast=1):
        self.lock = threading.Lock()
        self.fast, self.user = min(max(fast, self.LO), self.HI), False

    def get(self):
        with self.lock:
            return self.fast

    def set(self, x, user=False):
        """user: set on the page; from then on a scenario's own 'fast' no longer overrides it (this server's life)."""
        x = float(min(max(float(x), self.LO), self.HI))
        with self.lock:
            self.fast, self.user = x, self.user or user
            user = self.user
        emit("speed", fast=x, user=user)
        return x

    def sleep(self, secs, stop=lambda: False):
        """Wait secs of simulated time; a speed change part-way re-scales what is left."""
        left = secs
        while left > 1e-6 and not stop():
            x = self.get()
            dt = min(left / x, 0.05)
            time.sleep(dt)
            left -= dt * x


CLOCK = Clock()


def log(msg):
    print(f"[{time.time() - T0:7.1f}] {msg}", flush=True)
    emit("log", msg=msg)


def wrap(a):
    return (a + 180) % 360 - 180


def fmt(v):
    return "(" + ", ".join(f"{x:.1f}" for x in v) + ")"


class RoboDK:
    """Kinematics and live view from RoboDK's TM5-900. Flange poses as TM reports them (Rz*Ry*Rx)."""

    def __init__(self, station=None, robot=None):
        from robodk import robolink, robomath
        self.rm, self.rl = robomath, robolink
        self.RDK = robolink.Robolink()
        self.file = None                                # the .rdk the station came from, for reload()
        if station:                                     # --station: an open station by name, else an .rdk to open
            st = [s for s in self.RDK.getOpenStations() if s.Name() == station]
            if not st:                                  # a path, or a name: robot-cell/<name>.rdk
                named = HERE.parent / f"{station}.rdk"
                self.file = named.resolve() if not Path(station).is_file() and named.is_file() else Path(station).resolve()
                if not self.file.is_file():
                    raise SystemExit(f"no open station '{station}' and no file {self.file}")
                # one station at a time: close one the scenarios switch to (the mock never saves them), e.g. the
                # v5 cell a v5 run left open; any other open station is left alone
                ours = {s.get("station") for s in json.loads(SCENARIOS.read_text(encoding="utf-8"))} if SCENARIOS.exists() else set()
                for s in self.RDK.getOpenStations():
                    if s.Name() in ours:
                        log(f"RoboDK: closing station '{s.Name()}' without saving (one station at a time)")
                        self.RDK.setActiveStation(s)
                        self.RDK.CloseStation()
            self.RDK.setActiveStation(st[0] if st else self.RDK.AddFile(str(self.file)))
        self.file = self.file or self._station_file()
        self.robot_name, self.lock = robot, threading.RLock()
        self._attach()
        log(f"RoboDK: robot '{self.robot.Name()}' in station '{self.RDK.ActiveStation().Name()}'"
            f" (reload from: {self.file or 'unknown'})")

    def _station_file(self):
        """The active station's .rdk on disk: RoboDK's PATH/FILE_OPENSTATION, else robot-cell/<station name>.rdk."""
        name = self.RDK.ActiveStation().Name()
        try:
            folder, file = self.RDK.getParam("PATH_OPENSTATION"), self.RDK.getParam("FILE_OPENSTATION")
        except Exception:                               # an older RoboDK: the fallback below
            folder = file = ""
        tries = []
        if folder.lower().endswith(".rdk"):             # some builds give the full path here
            tries.append(Path(folder))
        if folder and file:
            tries.append(Path(folder) / (file if file.lower().endswith(".rdk") else file + ".rdk"))
        tries.append(HERE.parent / f"{name}.rdk")
        return next((t.resolve() for t in tries if t.is_file()), None)

    def _attach(self):
        """Item handles from the active station: the robot, its tool and the parts' start poses + parents."""
        robolink = self.rl
        self.station_name = self.RDK.ActiveStation().Name()
        self.RDK.setRunMode(robolink.RUNMODE_SIMULATE)  # never drive a real robot from here
        robots = self.RDK.ItemList(robolink.ITEM_TYPE_ROBOT)
        if self.robot_name:                             # --robot: by name (the v4 cell also has the AMR's robot)
            robots = [r for r in robots if r.Name() == self.robot_name]
            if not robots:
                raise SystemExit(f"no robot '{self.robot_name}' in station '{self.RDK.ActiveStation().Name()}'")
        self.robot = robots[0] if robots else self.RDK.AddFile(str(HERE.parent / "Omron-TM5-900.robot"))
        self.robot_name = self.robot_name or self.robot.Name()     # the same robot again after a reload
        # parts follow the gripper: names from the script's "carry" events (v4_replay.py), attached to the robot's
        # tool on GRIP OK, back to their parent on RELEASE, all back to the start on a scenario reset. Never saved.
        self.tool = self.robot.getLink(robolink.ITEM_TYPE_TOOL)
        self.start = {o.Name(): (o, o.Parent(), o.Pose()) for o in self.RDK.ItemList(robolink.ITEM_TYPE_OBJECT)}
        self.pending, self.held = [], []

    def station(self):
        """The loaded station's name (as of the last load: no RoboDK call, so it never waits on a reload)."""
        return self.station_name

    def reload(self, say, file=None):
        """The page's Reset RoboDK: close the station WITHOUT saving, open the same .rdk from disk, new item handles
        and a new start snapshot. file: another .rdk instead (a scenario's "station"); only one station is ever
        open. say(state, msg) reports progress. Never calls Save."""
        file = Path(file).resolve() if file else self.file
        if not file:
            raise RuntimeError("don't know which .rdk this station came from (serve with --station <file.rdk>)")
        if not file.is_file():                          # check before closing anything
            raise RuntimeError(f"no station file {file}")
        with self.lock:                                 # ik/fk/show wait until the new station is in
            name = self.RDK.ActiveStation().Name()
            say("closing", f"closing station '{name}' without saving")
            self.RDK.CloseStation()
            say("loading", f"opening {file.name} from disk")
            st = self.RDK.AddFile(str(file))
            if not st.Valid():
                raise RuntimeError(f"RoboDK could not open {file}")
            self.RDK.setActiveStation(st)
            self.file = file                            # Reset RoboDK reloads whichever station is loaded
            try:
                self._attach()
            except SystemExit as e:                     # --robot not in the reloaded file: not the server's end
                raise RuntimeError(str(e))
        log(f"RoboDK: station '{st.Name()}' loaded from {file}, {len(self.start)} parts")

    def carry(self, action, parts):
        if action == "grip":
            self.pending = list(parts)

    def grab(self):
        with self.lock:
            names, self.pending = self.pending, []
            if not self.tool.Valid() or self.held:
                return
            for n in names:
                if n in self.start:
                    o = self.start[n][0]
                    self.held.append((o, o.Parent()))
                    o.setParentStatic(self.tool)
                else:
                    log(f"RoboDK: no object '{n}' in the station, not attached")

    def drop(self):
        with self.lock:
            for o, parent in self.held:
                o.setParentStatic(parent)
            self.held = []

    def restore(self, cell="cell"):
        """Parts back to the start of the scenario's cell: robot_sim/cell_layout*.json (the .rdk's own start poses in
        the robot base frame, as the 3D pane's cell), so also right when this server started on a station a run had
        left the parts elsewhere in. Parts the snapshot found on the tool go back under 'Ground base'."""
        with self.lock:
            self.pending, self.held = [], []
            ground = self.RDK.Item("Ground base", self.rl.ITEM_TYPE_FRAME)
            for o, parent, pose in self.start.values():
                if parent.Type() == self.rl.ITEM_TYPE_TOOL and ground.Valid():
                    parent = ground
                o.setParent(parent)
                o.setPose(pose)
            f = HERE / "robot_sim" / f"cell_layout{cell[4:]}.json"
            if not f.exists():
                return
            try:
                parts = json.loads(f.read_text())["objects"]
            except (OSError, ValueError, KeyError) as e:    # keep the snapshot's poses
                return log(f"RoboDK: {f.name} not read ({e}): parts at the snapshot's poses")
            base = self.robot.Parent().PoseAbs()        # the robot base frame
            for part in parts:
                if part["name"] in self.start:
                    self.start[part["name"]][0].setPoseAbs(base * self.rm.Mat(part["pose"]))

    def ik(self, flange, near):
        with self.lock:
            j = self.robot.SolveIK(self.rm.Techman_2_Pose(flange), near).list()
        return j[:6] if len(j) >= 6 else None

    def fk(self, joints):
        with self.lock:
            return self.rm.Pose_2_Techman(self.robot.SolveFK(joints))

    def show(self, joints):
        with self.lock:
            self.robot.setJoints(joints)


class Robot:
    """Flange pose + joints, the motion queue and QueueTag states. Moves run on their own thread."""

    def __init__(self, flange, joints, kin, known, speed):
        self.flange, self.joints, self.kin, self.known = list(flange), list(joints), kin, known
        self.speed = speed / 100                        # project speed (the time scale: CLOCK)
        self.queue, self.tags, self.busy, self.error, self.last = [], {}, False, None, ""
        self.stamp = time.time() - T0                   # when self.joints was last set (T0 clock, as events' "at")
        self.cv = threading.Condition()
        self.warned = set()
        threading.Thread(target=self._run, daemon=True).start()

    def push(self, items):
        with self.cv:
            for it in items:
                if it[0] == "tag":
                    self.tags[it[1]] = "false"
            self.queue += items
            self.cv.notify_all()

    def clear(self):
        with self.cv:
            self.queue.clear()

    def tag(self, n):
        with self.cv:
            return self.tags.get(n, "none")

    def wait_idle(self):
        with self.cv:
            self.cv.wait_for(lambda: self.error or not (self.queue or self.busy))

    def state(self):
        with self.cv:
            return self.joints[:], self.flange[:]

    def sample(self):
        """(at, joints): during a move the time the joints were computed, else now (they hold still)."""
        with self.cv:
            return (self.stamp if self.busy else time.time() - T0), self.joints[:]

    def _run(self):
        while True:
            with self.cv:
                self.cv.wait_for(lambda: self.queue)
                item, self.busy = self.queue.pop(0), True
            if item[0] == "tag":
                with self.cv:
                    self.tags[item[1]] = "true"
                emit("tag", n=item[1])
            elif not self.error:
                try:
                    self._move(*item)
                except RuntimeError as e:
                    with self.cv:
                        self.error = str(e)
                        self.queue.clear()
                    log(f"ROBOT ERROR: {e}")
            with self.cv:
                self.busy = False
                self.cv.notify_all()

    def _warn(self, key, msg):
        if key not in self.warned:
            self.warned.add(key)
            log(f"note: {msg}")

    def _snap(self, flange=None, joints=None):
        """Without RoboDK, a taught pose (points file) gives the other half of the state."""
        for f, j in self.known:
            if flange and max(abs(a - b) for a, b in zip(f[:3], flange[:3])) < 0.5:
                return j
            if joints and max(abs(wrap(a - b)) for a, b in zip(j, joints)) < 0.5:
                return f
        return None

    def _move(self, kind, target, speed, acc):
        f0, j0 = self.flange[:], self.joints[:]
        if kind == "cptp" and self.kin:                 # PTP to a Cartesian pose: joints are the path
            j1 = self.kin.ik(target, j0)
            if j1 is None:
                raise RuntimeError(f"PTP target out of reach: {fmt(target)}")
            target, kind = j1, "jptp"
        if kind == "jptp":
            j1 = list(target)
            f1 = self.kin.fk(j1) if self.kin else self._snap(joints=j1)
            if f1 is None:
                f1 = f0
                self._warn("ptp", "no RoboDK: a PTP to joints the points file doesn't know keeps the flange pose")
            t = max(abs(b - a) for a, b in zip(j0, j1)) / (JOINT_SPEED * speed / 100 * self.speed)
        else:                                           # Line, or PTP "CPP" without RoboDK
            f1 = list(target)
            d = math.dist(f0[:3], f1[:3])
            rot = max(abs(wrap(b - a)) for a, b in zip(f0[3:], f1[3:]))
            v = speed * self.speed if kind == "line" else 250 * speed / 100 * self.speed
            t = max(d / v, rot / (90 * self.speed))
            if not self.kin:
                self._warn("line", "no RoboDK: joint angles in the stream only change at taught poses")
        t += acc / 1000
        self.last = f"{kind} {fmt(f0[:3])} -> {fmt(f1[:3])}  {t:.1f} s"
        log(f"  {self.last}")
        emit("move", kind=kind, frm=f0[:3], to=f1[:3], secs=round(t, 2))
        done, last = 0.0, time.monotonic()              # simulated seconds of this move so far
        due = last
        while done < t:
            if getattr(self, "stop", False):            # a scenario reset: a new Robot takes over
                return
            due += DT                                   # a steady DT grid, whatever the IK/RoboDK calls took
            time.sleep(max(0.0, due - time.monotonic()))
            now = time.monotonic()
            if now - due > DT:                          # fell behind: start a new grid, no burst of short steps
                due = now
            # live time scale (the slider); a stalled step counts as MAX_STEP so nothing jumps to catch up
            done, last = min(t, done + min(now - last, MAX_STEP) * CLOCK.get()), now
            s = done / t
            s = s * s * (3 - 2 * s)                     # ease in/out
            if kind == "jptp":
                j = [a + (b - a) * s for a, b in zip(j0, j1)]   # PTP JPP: to the joints as given, no +-360 short cut
                f = self.kin.fk(j) if self.kin else [a + (b - a) * s for a, b in zip(f0, f1)]
            else:
                f = [a + (b - a) * s for a, b in zip(f0[:3], f1[:3])] + \
                    [wrap(a + wrap(b - a) * s) for a, b in zip(f0[3:], f1[3:])]
                j = self.kin.ik(f, self.joints) if self.kin else self.joints
                if j is None:
                    raise RuntimeError(f"Line through an unreachable pose at {fmt(f[:3])}")
            with self.cv:
                self.flange, self.joints, self.stamp = list(f), list(j), time.time() - T0
            if self.kin:
                self.kin.show(j)
        if not self.kin:
            with self.cv:
                self.stamp = time.time() - T0
                self.flange = list(f1)
                if kind == "jptp":
                    self.joints = j1
                else:
                    self.joints = self._snap(flange=f1) or self.joints


CALL = re.compile(r"^\s*(\w+)\s*\((.*)\)\s*$")
ASSIGN = re.compile(r"^\s*(var_\w+)\s*=\s*(.+?)\s*$")


def args_of(s):
    return [a.strip().strip('"') for a in s.split(",")] if s.strip() else []


def value_of(s):
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return {"true": True, "false": False}.get(s, s.strip('"'))


class Flow:
    """The TMflow project: walks the nodes, owns the Listen server on 5890."""

    def __init__(self, name, robot, home, grips, verbose):
        self.title, self.start, variables, self.nodes = FLOWS[name]
        self.vars = dict(variables)
        self.robot, self.home, self.grips, self.verbose = robot, home, itertools.cycle(grips), verbose
        self.grips_given = list(grips)
        self.name, self.node, self.listening, self.running, self.gripper = name, None, False, True, "?"
        self.exit_req = threading.Event()
        self.lock = threading.Lock()
        self.server, self.sessions, self.sids = None, [], itertools.count(1)
        self.abort = False                              # a scenario reset: stop quietly, a new Flow takes over
        self.leaving = None                             # sessions to close at the Listen node's Pass (ScriptExit)

    # --- the flow
    def run(self):
        log(f"project {self.title} started")
        node, prev = self.start, "Start"
        while node not in ("Stop", "Error"):
            kind, nxt = self.nodes[node]
            with self.lock:
                self.node = node
            emit("node", node=node, prev=prev, kind=kind)
            node, prev = getattr(self, "_" + kind)(node, nxt), node
            if self.robot.error or self.abort:
                node = "Error"
        if self.abort:
            self.running = False
            self._close_server()
            return
        with self.lock:
            self.node = node
        emit("node", node=node, prev=prev, kind="stop")
        self.running = False
        self._close_server()
        log(f"project {self.title} {'stopped (Stop node)' if node == 'Stop' else 'stopped on a robot error'}"
            " - Ctrl+C and serve again to restart")

    def _home(self, node, nxt):
        log(f"{node}: PTP to the home pose")
        self.robot.push([("jptp", self.home["joints"], HOME_SPEED, 500)])
        self.robot.wait_idle()
        return nxt

    def _gripper(self, node, what, secs):
        log(f"{node}: Hand-E {what}")
        CLOCK.sleep(secs, lambda: self.abort)

    def _set(self, node, nxt):
        self._gripper(node, "initialize", NODE_TIME["set"])
        self.gripper = "activated"
        return nxt

    def _release(self, node, nxt):
        getattr(self.robot.kin, "drop", lambda: None)()     # RoboDK: parts back to their parent
        self._gripper(node, "open", NODE_TIME["release"])
        self.gripper = "open"
        return nxt

    def _grip(self, node, exits):
        self._gripper(node, "close", NODE_TIME["grip"])
        result = next(self.grips)
        self.gripper = {"ok": "closed on the object", "fail": "closed, FAIL", "loss": "closed on air (LOSS)"}[result]
        log(f"{node}: {result.upper()} -> {exits[result]}")
        emit("grip", node=node, result=result, next=exits[result])
        if result == "ok":
            getattr(self.robot.kin, "grab", lambda: None)()     # RoboDK: the carry event's parts onto the tool
        return exits[result]

    def _gateway(self, node, spec):
        cases, other = spec
        nxt = cases.get(self.vars.get("var_cmd"), other)
        log(f"{node}: var_cmd = {self.vars.get('var_cmd')} -> {nxt}")
        return nxt

    def _listen(self, node, nxt):
        self.exit_req.clear()
        self._open_server()
        with self.lock:
            self.listening = True
        log(f"{node}: Listen node waiting on {HOST}:{lt.LISTEN}")
        while not self.exit_req.wait(0.1):
            if self.robot.error or self.abort:
                return "Error"
        with self.lock:                                 # (ScriptExit already did this; a reset's exit_req didn't)
            self.listening = False
            ours = self.leaving if self.leaving is not None else list(self.sessions)
            self.leaving = None
        self.robot.wait_idle()                          # assumption: queued moves finish before Pass
        self._drop_sessions(ours)
        CLOCK.sleep(NODE_TIME["leave"], lambda: self.abort)
        log(f"{node}: Pass -> {nxt}")
        return nxt

    # --- the Listen server: open from the first Listen node until the project stops
    def _open_server(self):
        if self.server:
            return
        self.server = socket.create_server((HOST, lt.LISTEN))
        threading.Thread(target=self._accept, args=(self.server,), daemon=True).start()

    def _close_server(self):
        if self.server:
            self.server.close()
        self._drop_sessions()

    def _drop_sessions(self, which=None):
        """Close these sessions (default: all)."""
        with self.lock:
            for c in list(self.sessions if which is None else which):
                try:
                    c.shutdown(socket.SHUT_RDWR)
                    c.close()
                except OSError:
                    pass
                if c in self.sessions:
                    self.sessions.remove(c)

    def _accept(self, server):
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            with self.lock:
                self.sessions.append(conn)
            threading.Thread(target=self._session, args=(conn,), daemon=True).start()

    def _session(self, conn):
        buf, sid = b"", next(self.sids)
        emit("conn", sid=sid, listening=self.listening, node=self.node)
        try:
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                buf += chunk
                while True:
                    pkt, buf = take_packet(buf)
                    if pkt is None:
                        break
                    if self.verbose:
                        log(f"    <- {pkt!r}")
                    emit("rx", sid=sid, header=pkt[0], data=pkt[1])
                    reply, then = self._handle(*pkt) if pkt[0] != "bad" else (lt.packet("CPERR", pkt[1]), None)
                    if self.verbose:
                        log(f"    -> {reply!r}")
                    conn.sendall(reply)
                    emit("tx", sid=sid, data=reply.decode().strip())
                    if then:
                        then()
        except OSError:
            pass
        finally:
            conn.close()
            emit("disc", sid=sid)

    def _handle(self, header, data):
        if header == "TMSTA":
            with self.lock:
                listening, node = self.listening, self.node
            f = data.split(",")
            if f[0] == "00":
                return lt.packet("TMSTA", f"00,{'true' if listening else 'false'},{node if listening else ''}"), None
            if f[0] == "01" and len(f) > 1 and f[1].isdigit():
                return lt.packet("TMSTA", f"01,{int(f[1]):02d},{self.robot.tag(int(f[1]))}"), None
            return lt.packet("CPERR", "04"), None       # data not supported
        if header != "TMSCT":
            return lt.packet("CPERR", "03"), None       # header not supported
        if not self.listening:
            return lt.packet("CPERR", "F1"), None       # not in a Listen node
        sid, _, code = data.partition(",")
        moves, sets, leave = [], {}, False
        for no, ln in enumerate(code.split("\r\n"), 1):
            ok, item = self._parse(ln)
            if not ok:
                log(f"  script {sid} line {no} rejected: {ln!r}")
                return lt.packet("TMSCT", f"{sid},ERROR;{no}"), None
            if item and item[0] == "set":
                sets[item[1]] = item[2]
            elif item == ("exit",):
                leave = True
            elif item == ("clear",):
                self.robot.clear()
            elif item:
                moves.append(item)

        def then():
            self.vars.update(sets)
            for k, v in sets.items():
                log(f"  {k} = {v}")
                emit("var", name=k, value=v)
            if moves:
                self.robot.push(moves)
            if leave:
                log("  ScriptExit()")
                with self.lock:                         # at once, before the script can reconnect: the node stops
                    self.listening = False              # listening, and only the sessions open now are closed at
                    self.leaving = list(self.sessions)  # Pass (a new one is told "not listening" and retries)
                self.exit_req.set()
        return lt.packet("TMSCT", f"{sid},OK"), then

    def _parse(self, ln):
        """-> (accepted, queue item or None). Only what the test scripts send; the rest is an ERROR."""
        if not ln.strip():
            return True, None
        m = ASSIGN.match(ln)
        if m:
            return m.group(1) in self.vars, ("set", m.group(1), value_of(m.group(2)))
        m = CALL.match(ln)
        if not m:
            return False, None
        fn, a = m.group(1), args_of(m.group(2))
        try:
            if fn == "Line" and a[0] == "CAP" and len(a) == 11:
                return True, ("line", [float(v) for v in a[1:7]], float(a[7]), float(a[8]))
            if fn == "PTP" and a[0] in ("JPP", "CPP") and len(a) == 11:
                kind = "jptp" if a[0] == "JPP" else "cptp"
                return True, (kind, [float(v) for v in a[1:7]], float(a[7]), float(a[8]))
            if fn == "QueueTag" and 1 <= int(a[0]) <= 15:
                return True, ("tag", int(a[0]))
            if fn == "ChangeTCP":
                if any(float(v) for v in a):
                    log(f"  note: ChangeTCP({a}) - the mock always moves the flange")
                return True, None
        except (ValueError, IndexError):
            return False, None
        if fn == "ChangeBase":
            if a != ["RobotBase"]:
                log(f"  note: ChangeBase({a}) - the mock always works in RobotBase")
            return True, None
        if fn == "ScriptExit" and not a:
            return True, ("exit",)
        if fn == "StopAndClearBuffer":
            return True, ("clear",)
        return False, None


PKT = re.compile(rb"\$(\w+),(\d+),")


def take_packet(buf):
    """-> ((header, data) | ("bad", CPERR code) | None, rest of buf). Length-framed: data may hold \\r\\n."""
    start = buf.find(b"$")
    if start < 0:
        return None, b""
    m = PKT.match(buf, start)
    if not m:
        return (None, buf[start:]) if len(buf) - start < 32 else (("bad", "01"), buf[start + 1:])
    end = m.end() + int(m.group(2))
    if len(buf) < end + 6:
        return None, buf[start:]
    tail, rest = buf[end:end + 6], buf[end + 6:]
    if not (tail.startswith(b",*") and tail.endswith(b"\r\n")):
        return ("bad", "01"), rest
    cs = 0
    for b in buf[start + 1:end + 1]:
        cs ^= b
    if f"{cs:02X}".encode() != tail[2:4].upper():
        return ("bad", "02"), rest
    return (m.group(1).decode(), buf[m.end():end].decode(errors="replace")), rest


class View:
    """Live view: serves tmflow_mock_view.html and the group's diagram, pushes events as Server-Sent Events."""

    def __init__(self, port, diagram):
        self.clients, self.recent, self.lock = [], deque(maxlen=400), threading.Lock()
        self.robot = self.flow = None
        view = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/events":
                    return view._sse(self)
                if path == "/scenarios" and view.scenarios:     # the page's dropdown + the run state
                    return view._json(self, 200, {"scenarios": view.scenarios.list(), **view.scenarios.status()})
                if path == "/sim" or path.startswith("/sim/"):  # 3D view + meshes (robot_sim/), also for /all
                    sys.path.insert(0, str(HERE / "robot_sim"))
                    from sim_http import sim_get
                    return sim_get(self)
                f = {"/": HERE / "tmflow_mock_view.html", "/diagram": diagram,
                     "/demo": HERE / "tmflow_demo_view.html", "/all": HERE / "tmflow_all_view.html"}.get(path)
                if not f or not f.exists():
                    return self.send_error(404)
                body = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):                          # step events from "run" (another process)
                path = self.path.split("?")[0]
                if path == "/speed":                    # the page's speed slider: {"fast": x}, x 0.25..50
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        return self.send_error(415)     # JSON only, like /scenario/*
                    try:
                        x = float(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")["fast"])
                        if not math.isfinite(x):
                            raise ValueError
                    except (ValueError, KeyError, TypeError):   # JSONDecodeError is a ValueError
                        return view._json(self, 400, {"msg": 'POST /speed takes {"fast": <number>}'})
                    x = CLOCK.set(x, user=True)
                    log(f"speed: x{x:g} time (set on the page)")
                    return view._json(self, 200, {"fast": x, "user": True})
                if path == "/robodk/reset" and view.scenarios:     # the page's Reset RoboDK (--robodk only)
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        return self.send_error(415)
                    code, msg = view.scenarios.robodk_reset()
                    return view._json(self, code, {"msg": msg})
                if path in ("/scenario/run", "/scenario/stop") and view.scenarios:
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        return self.send_error(415)     # JSON only: other sites' plain form posts can't start runs
                    body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                    sc = view.scenarios
                    code, msg = sc.run(str(body.get("name", ""))) if path == "/scenario/run" else sc.stop()
                    return view._json(self, code, {"msg": msg, **sc.status()})
                if path != "/step":
                    return self.send_error(404)
                view.step(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}"))
                self.send_response(204)
                self.end_headers()

        ThreadingHTTPServer.daemon_threads = True
        self.demo = []                                  # this run's step events, for a /demo page opened mid-run
        self.scenarios = None                           # Scenarios, set by serve
        self.httpd = ThreadingHTTPServer((HOST, port), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def _json(self, h, code, obj):
        body = json.dumps(obj).encode()
        h.send_response(code)
        h.send_header("Content-Type", "application/json")
        h.send_header("Content-Length", str(len(body)))
        h.end_headers()
        h.wfile.write(body)

    def reset(self):
        """A scenario reset: pages opened from now on don't replay the run before."""
        with self.lock:
            self.recent.clear()
            self.demo = []

    def emit(self, ev):
        ev["at"] = round(time.time() - T0, 2)
        with self.lock:
            self.recent.append(ev)
            for q in self.clients:
                q.put(ev)

    def step(self, ev):
        """A step event from run (t = run | step | done | end), kept apart from the backlog so it can't scroll out."""
        ev["at"] = round(time.time() - T0, 2)
        with self.lock:
            if ev.get("t") == "run":
                self.demo = []
            if ev.get("t") == "carry" and LIVE:                 # RoboDK: what the next GRIP takes along
                getattr(LIVE["robot"].kin, "carry", lambda *a: None)(ev.get("action"), ev.get("parts", []))
            self.demo.append(ev)
            for q in self.clients:
                q.put(ev)

    def state(self):
        joints, flange = self.robot.state()
        f = self.flow
        return {"t": "state", "at": round(time.time() - T0, 2), "joints": joints, "flange": flange,
                "busy": self.robot.busy, "queued": len(self.robot.queue), "last": self.robot.last,
                "error": self.robot.error, "node": f.node, "listening": f.listening, "running": f.running,
                "vars": f.vars, "gripper": f.gripper, "fast": CLOCK.get()}

    def _sse(self, h):
        while self.flow is None:                        # a page reconnecting while serve still starts (RoboDK)
            time.sleep(0.1)
        h.send_response(200)
        h.send_header("Content-Type", "text/event-stream")
        h.send_header("Cache-Control", "no-cache")
        h.end_headers()
        q = queue.Queue()
        with self.lock:
            backlog = list(self.recent) + self.demo
            self.clients.append(q)

        def send(ev):
            h.wfile.write(f"data: {json.dumps(ev)}\n\n".encode())
            h.wfile.flush()
        try:
            send({"t": "hello", "flow": self.flow.name, "title": self.flow.title, "host": HOST, "fast": CLOCK.get()})
            for ev in backlog:                          # a page opened mid-run catches up
                send(ev)
            # "j" (joints + the time they are for) JOINT_HZ times a second for the 3D pane, which plays them back a
            # little behind, interpolated; "state" (everything else) 5 times a second. Both also while events queue.
            due_j = due_s = time.time()
            while True:
                now = time.time()
                if now >= due_j:
                    at, q6 = self.robot.sample()
                    send({"t": "j", "at": round(at, 3), "q": [round(x, 3) for x in q6]})
                    due_j = max(due_j + 1 / JOINT_HZ, now)
                if now >= due_s:
                    send(self.state())
                    due_s = now + 0.2
                try:
                    send(q.get(timeout=max(0, min(due_j, due_s) - time.time())))
                except queue.Empty:
                    pass
        except OSError:
            pass
        finally:
            with self.lock:
                self.clients.remove(q)


def stream(robot, flow, rate):
    """Ethernet Slave on 5891: a $TMSVR packet (STRING mode) every 1/rate s to every client."""
    server = socket.create_server((HOST, lt.SLAVE))
    vals = lambda v: ",".join(f"{x:.4f}" for x in v)   # noqa: E731

    def client(conn):
        with conn:
            try:
                while True:
                    robot, flow = LIVE["robot"], LIVE["flow"]   # a scenario reset swaps them
                    joints, flange = robot.state()
                    content = "\r\n".join([
                        "Robot_Link=1", f"Robot_Error={int(bool(robot.error))}",
                        f"Project_Run={'true' if flow.running else 'false'}",
                        f"Project_Speed={round(robot.speed * 100)}",
                        f"Joint_Angle={{{vals(joints)}}}", f"Coord_Robot_Flange={{{vals(flange)}}}",
                        f"Coord_Robot_Tool={{{vals(flange)}}}"])
                    conn.sendall(lt.packet("TMSVR", f"0,3,{content}"))
                    time.sleep(1 / rate)
            except OSError:
                pass

    while True:
        conn, _ = server.accept()
        threading.Thread(target=client, args=(conn,), daemon=True).start()


def serve(a):
    global VIEW
    if a.view:
        VIEW = View(a.view, Path(a.diagram).resolve())
    if a.points:
        lt.POINTS = Path(a.points).resolve()
    pts = json.loads(lt.POINTS.read_text()) if lt.POINTS.exists() else {}
    if getattr(a, "sim", None):                        # our own kinematics, no RoboDK (robot_sim/)
        sys.path.insert(0, str(HERE / "robot_sim"))
        import tm5_kin
        tm5_kin.use(a.sim)
        kin = tm5_kin.TM5Kin()
        log(f"kinematics: robot_sim/tm5_kin.py ({a.sim} geometry)")
    else:
        kin = RoboDK(a.station, a.robot) if a.robodk else None
    if "home" in pts:
        home = pts["home"]
    else:                                               # no taught home: 150 mm above the pick spot
        p = pts.get("pick", {"flange": [-297.5, -104.4, 227.7, -175.1, -1.9, -111.8],
                             "joints": [-4.5, 24.7, -142.5, 26.3, -87.2, 18.3]})
        f = p["flange"][:2] + [p["flange"][2] + 150] + p["flange"][3:]
        j = (kin.ik(f, p["joints"]) if kin else None) or p["joints"]
        home = {"flange": f, "joints": j}
        log(f"no 'home' in {lt.POINTS.name}: home = 150 mm above pick")
    known = [(home["flange"], home["joints"])] + [(v["flange"], v["joints"]) for v in pts.values()]
    flange = kin.fk(home["joints"]) if kin else home["flange"]
    CLOCK.set(a.fast)
    robot = Robot(flange, home["joints"], kin, known, a.project_speed)
    if kin:
        kin.show(home["joints"])
    grips = [g.strip().lower() for g in a.grip.split(",")]
    if not set(grips) <= {"ok", "fail", "loss"}:
        raise SystemExit("--grip takes ok, fail, loss (comma list = in turn)")
    flow = Flow(a.flow, robot, home, grips, a.verbose)
    LIVE.update(robot=robot, flow=flow)
    if VIEW:
        VIEW.robot, VIEW.flow = robot, flow
        VIEW.scenarios = Scenarios(a, kin, home, known, flange)
        log(f"live view: http://{HOST}:{a.view}  (3D: /sim/, everything on one page: /all)")
    threading.Thread(target=stream, args=(robot, flow, a.rate), daemon=True).start()
    log(f"mock TM5-900 on {HOST}: Listen {lt.LISTEN}, Ethernet Slave {lt.SLAVE}; "
        f"GRIP -> {', '.join(grips)}; x{CLOCK.get():g} time; project speed {a.project_speed:g} %")
    threading.Thread(target=flow.run, daemon=True).start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("mock stopped")


class Scenarios:
    """The page's Run / Stop: whitelisted runs from scenarios.json, one at a time. Run resets the mock in place (the
    scenario's flow, GRIP results and time scale - unless the page's speed slider was used - robot at home), then starts "tmflow_mock.py run <script> <args>" on
    this server's ports; the script's output goes to the page as "out" events, the run state as "scenario" events."""

    def __init__(self, a, kin, home, known, flange):
        self.a, self.kin, self.home, self.known, self.flange = a, kin, home, known, flange
        self.proc, self.name, self.state, self.code, self.stopped = None, None, "idle", None, False
        self.cell = "cell"                                  # the 3D cell of the last scenario (robot_sim/<cell>.glb)
        self.lock = threading.Lock()
        self.rdk_busy = False                               # a Reset RoboDK in progress

    def list(self):
        return json.loads(SCENARIOS.read_text(encoding="utf-8")) if SCENARIOS.exists() else []

    def status(self):
        return {"t": "scenario", "name": self.name, "state": self.state, "code": self.code, "fast": CLOCK.get(),
                "fast_user": CLOCK.user, "robodk": isinstance(self.kin, RoboDK), "rdk_busy": self.rdk_busy,
                "station": self.kin.station() if isinstance(self.kin, RoboDK) else None}

    def _set(self, state, code=None):
        self.state, self.code = state, code
        emit(**self.status())

    def run(self, name):
        sc = {s["name"]: s for s in self.list()}.get(name)
        if not sc:
            return 404, f"no scenario {name!r}"
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return 409, f"{self.name} is still running: stop it first"
            if self.rdk_busy:
                return 409, "RoboDK is reloading: wait for it"
            grips = [g.strip().lower() for g in sc.get("grip", "ok").split(",")]
            if sc.get("flow", "hande") not in FLOWS or not set(grips) <= {"ok", "fail", "loss"}:
                return 400, f"scenario {name!r}: bad flow or grip"
            self.name, self.stopped = name, False
            want = sc.get("station") if isinstance(self.kin, RoboDK) else None
            if want and want != self.kin.station():     # --robodk: the scenario's station first (its own thread)
                self.rdk_busy = True
                self._set("starting")
                threading.Thread(target=self._switch, args=(sc, grips, want), daemon=True).start()
                return 200, f"loading station {want}"
            return self._start(sc, grips)

    def _switch(self, sc, grips, want):
        """Close RoboDK's station without saving, open <want>.rdk (robot-cell/), then start the scenario. Any failure
        fails the run: never runs in the wrong station."""
        say = lambda state, msg: emit("rdk", state=state, msg=msg)     # noqa: E731
        try:
            say("switching", f"loading station '{want}'")
            self.kin.reload(say, HERE.parent / f"{want}.rdk")
            if self.kin.station() != want:
                raise RuntimeError(f"{want}.rdk opened as station '{self.kin.station()}'")
            say("ready", f"station '{want}' loaded")
        except Exception as e:
            log(f"scenario {sc['name']}: station switch failed: {e}")
            say("failed", f"station '{want}': {e}")
            emit("out", line=f"not started: RoboDK could not load station '{want}': {e}")
            self.rdk_busy = False
            with self.lock:
                self._set("failed")
            return
        self.rdk_busy = False
        with self.lock:
            self._start(sc, grips)

    def _start(self, sc, grips):
        """Reset the mock for this scenario and start its script (self.lock held)."""
        if not CLOCK.user:                              # the page's slider, once used, wins over the scenario's 'fast'
            CLOCK.set(float(sc.get("fast", self.a.fast)))
        self.reset(sc.get("flow", "hande"), grips, sc.get("cell", "cell"))
        script = (HERE.parent / sc["script"]).resolve()
        cmd = [sys.executable, str(HERE / "tmflow_mock.py"), "run", "--listen", str(lt.LISTEN), "--slave",
               str(lt.SLAVE), "--view", str(self.a.view), "--points",
               str((HERE / sc["points"]).resolve() if sc.get("points") else Path(lt.POINTS).resolve()), str(script)] + [str(x) for x in sc.get("args", [])]
        log(f"scenario {sc['name']}: {script.name} {' '.join(map(str, sc.get('args', [])))}")
        self.proc = subprocess.Popen(cmd, cwd=HERE.parent, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                     env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
        self._set("running")
        threading.Thread(target=self._watch, args=(self.proc,), daemon=True).start()
        return 200, "started"

    def _watch(self, proc):
        try:
            proc.stdin.write("\n" * 200)               # every "Enter to …" prompt (the scripts' safety stops)
            proc.stdin.close()
        except OSError:
            pass
        for line in proc.stdout:
            emit("out", line=line.rstrip("\r\n"))
        code = proc.wait()
        if proc is self.proc:
            self._set("stopped" if self.stopped else "finished" if code == 0 else "failed", code)

    def robodk_reset(self):
        """Close RoboDK's station without saving, reload its .rdk, new handles + start snapshot, mock robot at home."""
        if not isinstance(self.kin, RoboDK):
            return 404, "no RoboDK: serve runs without --robodk"
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return 409, f"{self.name} is running: stop it first"
            if self.rdk_busy:
                return 409, "a RoboDK reset is already running"
            self.rdk_busy = True
        threading.Thread(target=self._robodk_reset, daemon=True).start()
        return 202, "started"

    def _robodk_reset(self):
        say = lambda state, msg: emit("rdk", state=state, msg=msg)     # noqa: E731
        try:
            self.kin.reload(say)
            say("homing", "mock robot to home")
            with self.lock:
                flow = LIVE["flow"]
                self.reset(flow.name, flow.grips_given, self.cell)     # new Robot + Flow at home, parts at the start
            say("ready", f"RoboDK reloaded from {self.kin.file.name}, robot at home")
        except Exception as e:                          # RoboDK closed, file gone, ...: the page shows it
            log(f"RoboDK reset failed: {e}")
            say("failed", str(e))
        finally:
            self.rdk_busy = False

    def stop(self):
        with self.lock:
            if not (self.proc and self.proc.poll() is None):
                return 409, "nothing is running"
            self.stopped = True
            self.proc.kill()
            self.proc.wait()
            flow = LIVE["flow"]
            self.reset(flow.name, flow.grips_given, self.cell)   # back to idle: home, in the flow
        return 200, "stopped"

    def reset(self, name, grips, cell="cell"):
        """The mock as if serve had just started with this flow and GRIP results (no process restart; the time scale
        is CLOCK's, set by run before this).
        cell: the 3D pane's start state (robot_sim/<cell>.glb: cell = v4's, cell_v5 = guide on base A)."""
        self.cell = cell
        old = LIVE["flow"]
        old.abort, old.robot.stop = True, True
        old.robot.clear()
        old.exit_req.set()
        until = time.time() + 15
        while old.running and time.time() < until:
            time.sleep(0.05)
        old._close_server()
        VIEW.reset()
        getattr(self.kin, "restore", lambda c: None)(cell)  # RoboDK: parts at the cell's start, as the 3D pane
        robot = Robot(self.flange, self.home["joints"], self.kin, self.known, self.a.project_speed)
        if self.kin:
            self.kin.show(self.home["joints"])
        flow = Flow(name, robot, self.home, grips, self.a.verbose)
        LIVE.update(robot=robot, flow=flow)
        VIEW.robot, VIEW.flow = robot, flow
        emit("reset", flow=name, title=flow.title, cell=cell)
        log(f"reset: project {flow.title}; GRIP -> {', '.join(grips)}; x{CLOCK.get():g} time")
        threading.Thread(target=flow.run, daemon=True).start()


# What the /demo page shows: calls a driver function of the script makes to its step functions (both in the
# script's own file), as the plain-word step list. demo_run's plan is whatever its steps() returns.
STEPS = {
    "demo_run.py": ({"run"}, {"home", "open_gripper", "grab_plank", "move_to_jig", "place_in_jig", "release"}),
    "hande_bridge.py": ({"check", "demo", "pickplace"}, {"move", "lift", "grip", "release", "home", "finish",
                                                         "<lambda>"}),
    "v4_replay.py": ({"run"}, {"guide_to_base_a", "planks_into_frame1", "guide_back_to_base_b", "frame1_into_frame2",
                               "inner_half_to_pad", "outer_half_to_pad", "bench_to_amr"}),
}


def short(v):
    """A step argument for the page: plank numbers as they are, a pose as its (x, y, z)."""
    if isinstance(v, (list, tuple)) and len(v) == 6 and all(isinstance(x, (int, float)) for x in v):
        return "(" + ", ".join(f"{x:.0f}" for x in v[:3]) + ")"
    return v if isinstance(v, (int, float, str)) else repr(v)[:40]


NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # 127.0.0.1, never via a proxy


class Steps:
    """sys.setprofile on the script run by "run": posts its step calls to the live view's /step (serve's process)."""

    def __init__(self, path, port):
        self.file = str(path)
        self.drivers, self.names = STEPS.get(path.name, (set(), set()))
        self.url, self.q, self.k, self.active = f"http://{HOST}:{port}/step", queue.Queue(), 0, None
        threading.Thread(target=self._post, daemon=True).start()

    def send(self, t, **ev):
        self.q.put({"t": t, **ev})

    def _post(self):
        while True:
            ev = self.q.get()
            try:
                req = urllib.request.Request(self.url, json.dumps(ev).encode(), {"Content-Type": "application/json"})
                NO_PROXY.open(req, timeout=1).close()
            except OSError:                             # no serve with a view, or one older than /step
                pass
            self.q.task_done()

    def profile(self, frame, event, arg):
        code = frame.f_code
        if code.co_filename != self.file or event not in ("call", "return"):
            return
        if code.co_name == "steps" and event == "return" and arg:
            self.send("plan", steps=[{"fn": f.__name__, "args": [short(x) for x in xs]} for f, xs in arg])
        elif event == "return" and frame is self.active:
            self.active = None
            self.send("done", n=self.k, fn=code.co_name)
        elif event == "call" and code.co_name in self.names and self.active is None:
            up = frame.f_back
            if up and up.f_code.co_filename == self.file and up.f_code.co_name in self.drivers:
                names = [n for n in code.co_varnames[:code.co_argcount] if n != "self"]
                self.active, self.k = frame, self.k + 1
                self.send("step", n=self.k, fn=code.co_name, args=[short(frame.f_locals[n]) for n in names],
                          what=up.f_locals.get("what"))


def run_script(a):
    """Run a test script as if from the command line, every connection to the robot's IP sent to the mock."""
    robot_ip, connect = lt.IP, socket.create_connection

    def to_mock(address, *args, **kw):
        host, port = address
        if host == robot_ip:                            # a script run as __main__ keeps its own 5890/5891
            host, port = HOST, {ROBOT_PORTS[0]: lt.LISTEN, ROBOT_PORTS[1]: lt.SLAVE}.get(port, port)
        return connect((host, port), *args, **kw)
    socket.create_connection = to_mock                  # also covers a script run as __main__ (own IP)
    lt.IP = HOST
    if a.points:
        lt.POINTS = Path(a.points).resolve()
    path = Path(a.script)
    path = (path if path.exists() else HERE / path.name).resolve()
    if a.view:
        scale_sleep(a.view)
    run_traced(path, a.args, a.view)


def scale_sleep(port):
    """The script's own waits (QueueTag polls, the pause after ScriptExit, reconnect retries) at serve's live speed,
    like the robot's moves: else at x20 the arm stands still for those real seconds and then rushes through a move.
    Never shorter than SLEEP_MIN (the polls would flood the page). Speed read from serve's /scenarios."""
    real, fast = time.sleep, [1.0]

    def poll():
        while True:
            try:
                with NO_PROXY.open(f"http://{HOST}:{port}/scenarios", timeout=2) as r:
                    fast[0] = float(json.loads(r.read()).get("fast", 1)) or 1.0
            except (OSError, ValueError):
                pass
            real(0.5)
    threading.Thread(target=poll, daemon=True).start()
    time.sleep = lambda s: real(max(s / fast[0], min(s, SLEEP_MIN)))


def run_traced(path, args, view):
    """Run a script as __main__ with sys.argv = path + args; its steps go to the live view on port view (0 = off)."""
    sys.argv = [str(path)] + args
    if not view:
        return runpy.run_path(str(path), run_name="__main__")
    steps, result = Steps(path, view), "error"
    steps.send("run", script=path.name, args=args)
    sys.setprofile(steps.profile)
    try:
        runpy.run_path(str(path), run_name="__main__")
        result = "done"
    except SystemExit as e:
        result = "done" if e.code in (None, 0) else str(e.code)
        raise
    except KeyboardInterrupt:
        result = "stopped"
        raise
    finally:
        sys.setprofile(None)
        steps.send("end", result=result)
        steps.q.join()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="start the fake TMflow + robot")
    s.add_argument("--flow", choices=FLOWS, default="hande", help="TMflow project to play (default hande)")
    s.add_argument("--grip", default="ok", help="GRIP results in turn: ok, fail, loss (e.g. ok,loss)")
    s.add_argument("--fast", type=float, default=1, help="time scale (5 = five times faster than real)")
    s.add_argument("--project-speed", type=float, default=100, help="TMflow project speed [%%]")
    k = s.add_mutually_exclusive_group()
    k.add_argument("--robodk", action="store_true", help="IK/FK from RoboDK and show the robot moving there")
    k.add_argument("--sim", nargs="?", const="techman", choices=["techman", "robodk"],
                   help="IK/FK from robot_sim/tm5_kin.py, no RoboDK (link lengths: techman = Techman's nominal, "
                        "default; robodk = RoboDK's robot file). The 3D view (/sim/, /all) works with either")
    s.add_argument("--station", help="with --robodk: an open station's name, or an .rdk to open (default: active)")
    s.add_argument("--robot", help="with --robodk: the robot's name (default: the station's first robot)")
    s.add_argument("--rate", type=float, default=50, help="Ethernet Slave rate [Hz]")
    s.add_argument("--points", help="points file instead of listen_test_points.json")
    s.add_argument("--view", type=int, default=8090, help="live view port, 0 = off (default 8090)")
    s.add_argument("--diagram", default=str(HERE / "listen_loop_flow.html"), help="the group's flow diagram page")
    s.add_argument("-v", "--verbose", action="store_true", help="print every packet")
    r = sub.add_parser("run", help="run a test script against the mock")
    r.add_argument("--points", help="points file instead of listen_test_points.json")
    r.add_argument("--view", type=int, default=8090, help="serve's live view port, for the /demo steps; 0 = off")
    r.add_argument("script")
    r.add_argument("args", nargs=argparse.REMAINDER)
    for p in (s, r):                                    # ports, to run next to another mock
        p.add_argument("--listen", type=int, default=lt.LISTEN, help=f"Listen node port (default {lt.LISTEN})")
        p.add_argument("--slave", type=int, default=lt.SLAVE, help=f"Ethernet Slave port (default {lt.SLAVE})")
    a = ap.parse_args()
    lt.LISTEN, lt.SLAVE = a.listen, a.slave
    serve(a) if a.cmd == "serve" else run_script(a)
