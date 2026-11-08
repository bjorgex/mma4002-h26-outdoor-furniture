"""TMflow project zip (what RoboDK's Omron post writes, bench_tmflow/vN/AssembleBench.zip) without RoboDK:
read one into a program file, and write one from a program file (or a tests/vN_moves.json).

    python tests/robot_sim/tmflow_export.py import bench_tmflow/v7/AssembleBench.zip -o tests/robot_sim/ref/v7_program.json
    python tests/robot_sim/tmflow_export.py export tests/robot_sim/ref/v7_program.json -o out/AssembleBench.zip
    python tests/robot_sim/tmflow_export.py export tests/v4_moves.json --base-from bench_tmflow/v4/AssembleBench.zip -o out/v4.zip
    python tests/robot_sim/tmflow_export.py diff bench_tmflow/v7/AssembleBench.zip out/AssembleBench.zip
    python tests/robot_sim/tmflow_export.py selftest       v3/v4/v6/v7: import -> export -> diff, v4 also from v4_moves.json

The zip (reverse-engineered from bench_tmflow/v3, v4, v6, v7 and Omron_DAM.py's settings):
    ConfigData.xml                         the TCP "EGP" (flange -> TCP, here z 160)
    Projects/<prog>/<prog>.prog            fixed 58-byte XML stub
    Projects/<prog>/<prog>.dat             XML: <Point> per distinct target (coordinate = flange pose in the base
                                           "Groundbase", tool_mode = TCP pose, joint_angle = RoboDK's joints),
                                           <Base> RobotBase + Groundbase (its pose in the robot base, TM x,y,z,rx,ry,rz)
    Projects/<prog>/<prog>.flow            JSON: Start -> chain of nodes (Display, Point, SET, WaitFor), 8 per column
Encrypted with the traditional PKWARE cipher ("ZipCrypto"), password Omron_DAM.SET_PASSWORD = robodk1234, and a
192-character zip comment written by RoboDK's TMExportZip.exe (C:/RoboDK/Other/TMExportZip, a stand-alone .NET tool:
"TMExportZip /V:<vendor> /P:<password> <dir>"; the comment is its AES-encrypted vendor/password tag that TMflow's
import checks). Packing: --packer tmexportzip (that exe, if present: same as RoboDK's ZIP_TYPE 1) or --packer python
(pure Python ZipCrypto, no comment: what RoboDK's ZIP_TYPE 2 "without TMExportZip" would be; whether TMflow imports
a zip without the tag is untested) or --packer dir (just the folder).
Point nodes: PTP -> PSPercentage = joint speed / 185 deg/s (Omron_DAM.MAX_SPEED_DEGS), PSTTTS 150; Line ->
LSAVelocity = the linear speed (mm/s), LSTTTS 300, LineABS ON (values as in the v7 export).

Program file (a superset of tests/vN_moves.json; a moves file is a valid program file):
    {"program": "AssembleBench", "base": {"name": "Groundbase", "pose": [x,y,z,rx,ry,rz]},   base in robot base
     "tcp": {"name": "EGP", "pose": [0,0,160,0,0,0]}, "joint_speed": 50,
     "steps": [{"move": "ptp"|"line", "joints": [6 deg], "flange": [TM pose, robot base], "speed": mm/s, "name": ...},
               {"do0": 0|1, "gripper": "grip"|"release"|null, "parts": [...], "wait_ms": 500},
               {"message": "Simulation: parts to start"}, {"wait_ms": 300}]}
"""
import argparse
import binascii
import datetime
import io
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parents[1]
sys.path.insert(0, str(HERE))
import tm5_kin as K                                       # noqa: E402  pose_to_mat / mat_to_pose (TM convention)

PASSWORD = "robodk1234"                                   # Omron_DAM.SET_PASSWORD
TMEXPORTZIP = Path("C:/RoboDK/Other/TMExportZip/TMExportZip.exe")
VENDOR = "RoboDK"                                         # /V: for TMExportZip (see OWN_TOOL.md: not verifiable)
MAX_SPEED_DEGS = 185                                      # Omron_DAM.MAX_SPEED_DEGS
JOINT_SPEED = 50                                          # bench_cell_v*.py JOINT (deg/s)
VERTICAL_INS = 8                                          # Omron_DAM.VERTICAL_INS
ROBOT = "Omron TM5-900"
CRLF = "\r\n"
PROG_STUB = b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\r\n\r\n'
TCP_BASE_DEFAULT = {"name": "Groundbase", "pose": [-206.458, 219.983, 1.571, -0.0269, -0.0665, -179.9760]}  # v7
TCP_DEFAULT = {"name": "EGP", "pose": [0, 0, 160, 0, 0, 0]}


# ------------------------------------------------------------------ number formats (as RoboDK's post writes them)
def fmt_pose(p):
    """x,y,z with 3 decimals, angles with 4 ("-0.0000" kept)."""
    return ",".join([f"{v:.3f}" for v in p[:3]] + [f"{v:.4f}" for v in p[3:6]])


def fmt_joints(q):
    """6 significant digits, J1-J5 printed with 5 decimals, J6 with 4 (that is what the exports contain)."""
    q = [float(f"{v:.6g}") for v in q]
    return ",".join([f"{v:.5f}" for v in q[:5]] + [f"{q[5]:.4f}"])


def fmt_base(p):
    return ",".join([f"{v:.3f}" for v in p[:3]] + [f"{v:.4f}" for v in p[3:6]])


def num(v):
    """'100' for 100.0, '12.5' otherwise."""
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def tool_mode(coord, T):
    """TCP pose string of a point: the flange pose `coord` (base frame) times the TCP T; the angles are the
    coordinate's (RoboDK writes them so, "-0.0000" as "0.0000"). From the rounded coordinate this matches RoboDK's
    string in 441 of the 450 points of v3-v7; the rest are 0.001 mm off (RoboDK uses the unrounded pose)."""
    m = mul(K.pose_to_mat(coord), T)
    a = [f"{v:.4f}" for v in coord[3:6]]
    return ",".join([f"{m[i][3]:.3f}" for i in range(3)] + ["0.0000" if x == "-0.0000" else x for x in a])


def parse_csv(s):
    return [float(x) for x in s.split(",")]


def mul(a, b):
    return K.matmul(a, b)


def inv(m):
    r = [[m[j][i] for j in range(3)] for i in range(3)]
    t = [-sum(r[i][k] * m[k][3] for k in range(3)) for i in range(3)]
    return [r[0] + [t[0]], r[1] + [t[1]], r[2] + [t[2]], [0, 0, 0, 1]]


# ------------------------------------------------------------------ zip: read (password) and write (ZipCrypto)
def read_zip(path, password=PASSWORD):
    """{name: bytes} of every file in the export, plus the zip comment under key None."""
    import zipfile
    with zipfile.ZipFile(path) as z:
        out = {i.filename: z.read(i, pwd=password.encode()) for i in z.infolist() if not i.is_dir()}
        out[None] = z.comment
    return out


class _ZipCrypto:
    def __init__(self, password):
        self.k = [0x12345678, 0x23456789, 0x34567890]
        for c in password:
            self._update(c)

    @staticmethod
    def _crc(c, b):
        return binascii.crc32(bytes([b]), c ^ 0xFFFFFFFF) ^ 0xFFFFFFFF

    def _update(self, b):
        k0 = self._crc(self.k[0], b)
        k1 = ((self.k[1] + (k0 & 0xFF)) * 134775813 + 1) & 0xFFFFFFFF
        k2 = self._crc(self.k[2], k1 >> 24)
        self.k = [k0, k1, k2]

    def encrypt(self, data):
        out = bytearray()
        for b in data:
            t = (self.k[2] | 2) & 0xFFFF
            out.append(b ^ (((t * (t ^ 1)) >> 8) & 0xFF))
            self._update(b)
        return bytes(out)


def write_zip(files, path, password=PASSWORD, comment=b"", when=None):
    """Zip like the exports (UTF-8 names, directories as entries, deflate except the .prog stub, ZipCrypto),
    without TMExportZip's comment tag unless one is given."""
    when = when or datetime.datetime.now()
    dostime = (when.hour << 11) | (when.minute << 5) | (when.second // 2)
    dosdate = ((when.year - 1980) << 9) | (when.month << 5) | when.day
    names = []
    for n in files:                                        # parent folders first, as in the exports
        parts = n.split("/")
        for i in range(1, len(parts)):
            d = "/".join(parts[:i]) + "/"
            if d not in names:
                names.append(d)
        names.append(n)
    local, central, off = io.BytesIO(), io.BytesIO(), 0
    import random
    rnd = random.Random(4002)                              # the 11 random header bytes: fixed (reproducible zips)
    for n in names:
        data = b"" if n.endswith("/") else files[n]
        crc = binascii.crc32(data) & 0xFFFFFFFF
        method = 8 if data and not n.endswith(".prog") else 0
        body = data
        if method == 8:
            c = zlib.compressobj(9, zlib.DEFLATED, -15)
            body = c.compress(data) + c.flush()
        flags, attr = 0x800, (16 if n.endswith("/") else 32)
        if not n.endswith("/") and password:
            flags |= 1
            zc = _ZipCrypto(password.encode())
            head = bytes(rnd.randrange(256) for _ in range(11)) + bytes([crc >> 24])
            body = zc.encrypt(head + body)
        fn = n.encode("utf-8")
        hdr = struct.pack("<4sHHHHHIIIHH", b"PK\x03\x04", 20, flags, method, dostime, dosdate, crc, len(body),
                          len(data), len(fn), 0)
        local.write(hdr + fn + body)
        central.write(struct.pack("<4sHHHHHHIIIHHHHHII", b"PK\x01\x02", 45, 20, flags, method, dostime, dosdate, crc,
                                  len(body), len(data), len(fn), 0, 0, 0, 0, attr, off) + fn)
        off += len(hdr) + len(fn) + len(body)
    cd = central.getvalue()
    end = struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, len(names), len(names), len(cd), off, len(comment))
    Path(path).write_bytes(local.getvalue() + cd + end + comment)


# ------------------------------------------------------------------ project -> program
def parse_project(files):
    """The program in a TMflow export (files from read_zip) as a program dict (see the module docstring)."""
    flow_name = next(n for n in files if n and n.endswith(".flow"))
    prog = flow_name.split("/")[-1][:-5]
    flow = json.loads(files[flow_name].decode("utf-8-sig"))
    dat = files[flow_name[:-5] + ".dat"].decode("utf-8-sig")
    points = {m.group(1): m.groupdict() for m in re.finditer(
        r'<Point name="(?P<name>[^"]+)" coordinate="(?P<coordinate>[^"]+)" joint_angle="(?P<joint_angle>[^"]+)" '
        r'tool_mode="(?P<tool_mode>[^"]+)" base="(?P<base>[^"]+)" tcp="(?P<tcp>[^"]+)" type="(?P<type>[^"]+)" />', dat)}
    bases = {m.group(1): parse_csv(m.group(2)) for m in re.finditer(r'<Base name="([^"]+)" basedata="([^"]+)"', dat)}
    cfg = files.get("ConfigData.xml", b"").decode("utf-8-sig")
    tcp_name = re.search(r"<Name>(.*?)</Name>", cfg).group(1) if cfg else "EGP"
    g = re.search(r"<GPTFF>(.*?)</GPTFF>", cfg, re.S)
    tcp_pose = [float(re.search(f"<{a}>(.*?)</{a}>", g.group(1)).group(1)) for a in "XYZWVU"] if g else [0] * 6
    tcp_pose = tcp_pose[:3] + [tcp_pose[5], tcp_pose[4], tcp_pose[3]]       # W,V,U = rz,ry,rx? (all 0 here)
    nodes = {n["Name"]: n for n in flow["BaseObjectSingle"]}
    order, name = [], flow["BaseStart"]["ChildNode"]
    while name:
        order.append(nodes[name])
        name = nodes[name]["ChildNode"]
    base_name = next((n["ObjectNode"]["BaseName"] for n in order if n["NodeType"] == "Point"), "Groundbase")
    B = K.pose_to_mat(bases.get(base_name, [0] * 6))
    steps, speed, header, last_do = [], 100.0, None, None
    for n in order:
        t, o = n["NodeType"], n["ObjectNode"]
        if t == "Display":
            if n["ReplaceName"] == "RoboDK" and header is None and not steps:
                header = o["LogText"]
                continue
            m = re.match(r"Simulation: (attach|release) (.*)", o["LogText"])
            if m and last_do is not None and (last_do["gripper"] in (None, "grip" if m.group(1) == "attach" else "release")):
                last_do["gripper"] = "grip" if m.group(1) == "attach" else "release"
                last_do["parts"].append(m.group(2))
                continue
            steps.append({"message": o["LogText"]})
            last_do = None
        elif t == "SET":
            d = o["DIOData"][0]
            last_do = {"name": f"Set IO_{d['Chan']}={1 if d['HL'] == 'H' else 0}", "do0": 1 if d["HL"] == "H" else 0,
                       "gripper": None, "parts": []}
            steps.append(last_do)
        elif t == "WaitFor":
            ms = int(o["TimeData"])
            if last_do is not None and "wait_ms" not in last_do:
                last_do["wait_ms"] = ms
            else:
                steps.append({"wait_ms": ms})
                last_do = None
        elif t == "Point":
            p = points[n["ReplaceName"]]
            coord = parse_csv(p["coordinate"])
            line = o["MotionCMD"] == "Line"
            if line:
                speed = float(o["LSAVelocity"])
            step = {"name": n["ReplaceName"], "move": "line" if line else "ptp",
                    "joints": parse_csv(p["joint_angle"]),
                    "flange": [round(v, 4) for v in K.mat_to_pose(mul(B, K.pose_to_mat(coord)))],
                    "pose_base": coord, "tool_base": p["tool_mode"], "speed": speed}
            if not line:
                step["joint_speed"] = round(float(o["PSPercentage"]) * MAX_SPEED_DEGS / 100, 2)
            steps.append(step)
            last_do = None
        else:
            raise ValueError(f"node type {t} not handled ({n['Name']})")
    custom = re.search(r'<Custom max="(\d+)"', dat)
    return {"program": prog, "source": "TMflow export", "base": {"name": base_name, "pose": bases.get(base_name)},
            "tcp": {"name": tcp_name, "pose": tcp_pose}, "joint_speed": JOINT_SPEED, "steps": steps,
            "tmflow": {"header": header, "custom_max": int(custom.group(1)) if custom else 113,
                       "point_names": True}}


# ------------------------------------------------------------------ program -> project
def _point_obj(line, speed, joint_pct, base, tcp):
    o = {"Speed": "100", "MotionCMD": "Line" if line else "PTP", "Blend": "YES", "BlendValue": 1,
         "PSPercentage": "50" if line else num(joint_pct), "PSTTTS": "500" if line else "150", "PSTTTSOF": "ON",
         "PTPType": 1, "LineABS": "ON" if line else "OFF", "LSPercentage": "100",
         "LSAVelocity": num(speed) if line else "250", "LSTTTS": "300" if line else "500", "BaseName": base,
         "TCPName": tcp, "EnableLoad": True, "LoadValue": "0", "WayPointHP": "50", "WayPointSpeed": "-1",
         "IsKeepPose": True, "DisablePrecisePositioning": "true", "DisableStickSpeedLink": False,
         "SmartPTPConfig": False, "IsBaseShifting": False, "IsToolShifting": False, "WayPointMode": 0,
         "WayPointHeight": "0", "WayPointMotion": 0, "WayPointLineABS": "OFF", "WayPointLSPercentage": "100",
         "WayPointLSAVelocity": "250", "WayPointLSTTTS": "500"}
    return o


def build_project(program, when=None):
    """{zip path: bytes} of the TMflow project for a program dict."""
    when = when or datetime.datetime.now()
    prog = program.get("program", "AssembleBench")
    base = program.get("base") or TCP_BASE_DEFAULT
    tcp = program.get("tcp") or TCP_DEFAULT
    extra = program.get("tmflow", {})
    jspeed = program.get("joint_speed", JOINT_SPEED)
    B, T = K.pose_to_mat(base["pose"]), K.pose_to_mat(tcp["pose"])
    Binv = inv(B)
    header = extra.get("header") or (f"Program generated by tmflow_export.py (MMA4002 own tool) for {ROBOT} on "
                                     f"{when:%d/%m/%Y %H:%M:%S}\nUsing nominal kinematics.\nRobot program running")
    nodes, cnt = [], {}

    def add(kind, prefix, replace, obj):
        cnt[prefix] = cnt.get(prefix, 0) + 1
        nodes.append({"Name": f"{prefix}{cnt[prefix]}", "kind": kind, "ReplaceName": replace(cnt[prefix]), "obj": obj})

    def display(text, title="RoboDK Message", bg="White", replace=None):
        rn = replace or (text.split(":")[0] if ":" in text else "Message")
        add("Display", "Display", lambda k: rn, {"FGColor": "Black", "BGColor": bg, "TitleText": title, "LogText": text})

    display(header, "RoboDK Program", "Blue", "RoboDK")
    pts, point_lines = {}, []
    for s in program["steps"]:
        if "move" in s:
            coord = s.get("pose_base") or K.mat_to_pose(mul(Binv, K.pose_to_mat(s["flange"])))
            ckey, jkey = fmt_pose(coord), fmt_joints(s["joints"])
            key = (ckey, jkey)                            # one <Point> per distinct pose + joints
            if key not in pts:
                pts[key] = f"Point{len(pts) + 1}"
                point_lines.append(f'  <Point name="{pts[key]}" coordinate="{ckey}" joint_angle="{jkey}" '
                                   f'tool_mode="{s.get("tool_base") or tool_mode(coord, T)}" base="{base["name"]}" '
                                   f'tcp="{tcp["name"]}" type="R" />')
            pct = round(s.get("joint_speed", jspeed) / MAX_SPEED_DEGS * 100)
            add("Point", "P", lambda k, n=pts[key]: n,
                _point_obj(s["move"] == "line", s.get("speed", 100), pct, base["name"], tcp["name"]))
        elif "do0" in s:
            hl = "H" if s["do0"] else "L"
            add("SET", "SET", lambda k: f"Set_DO0{hl}",
                {"DIOData": [{"DeviceType": 16, "Slot": "0", "HL": hl, "Chan": 0, "DIOType": "DO"}],
                 "CameraLightOnOff": None, "AIOData": [], "MathData": []})
            ms = s.get("wait_ms", 500 if s.get("gripper") else 300)   # bench_cell_v*.py: gripper() 500, pre-sets 300
            add("WaitFor", "WaitFor", lambda k: f"Wait{ms}ms{k}", _wait(ms))
            if s.get("gripper") == "grip":
                for p in s.get("parts", []):
                    display(f"Simulation: attach {p}")
            elif s.get("gripper") == "release":
                for p in s.get("parts", []):
                    display(f"Simulation: release {p}")
        elif "message" in s:
            display(s["message"])
        elif "reload" in s:                               # bench_cell_v8 Program.reload (v8x2): people reload the jig
            # TMflow on its own: a Display node (the message) + a RELOAD_WAIT_MS WaitFor at Home; more time: Pause on
            # the robot stick. (Driven from v4_replay.py the robot stays in the Listen node until Resume on the page.)
            display(f"Reload: {s.get('name', 'reload the jig')} ({s['reload']}) - {RELOAD_WAIT_MS // 1000} s", "Reload", "White",
                    "Reload")
            add("WaitFor", "WaitFor", lambda k: f"WaitReload{k}", _wait(RELOAD_WAIT_MS))
        elif "wait_ms" in s:
            add("WaitFor", "WaitFor", lambda k, ms=s["wait_ms"]: f"Wait{ms}ms{k}", _wait(s["wait_ms"]))
    objs = []
    for i, n in enumerate(nodes):
        objs.append({"Name": n["Name"], "NodeID": i + 1, "ParentNode": nodes[i - 1]["Name"] if i else "",
                     "ChildNode": nodes[i + 1]["Name"] if i + 1 < len(nodes) else "", "ReplaceName": n["ReplaceName"],
                     "HMIFlowPoint": [100.0 + 200 * (i // VERTICAL_INS), 200.0 + 100 * (i % VERTICAL_INS)],
                     "NodeType": n["kind"], "NodeIcon": "", "GroupName": None, "ThreadName": "", "SubFlowName": "",
                     "InitValue": "YES", "UpdateFlag": "", "ObjectNode": n["obj"], "Attribute": 0})
    flow = {"FlowFile": {"Version": "-1.11"}, "BaseMathDefine": None,
            "BaseStart": {"Name": "Start", "ParentNode": "", "ChildNode": objs[0]["Name"], "ReplaceName": "Start",
                          "InitValue": "YES", "NodeType": "Start", "StickSpeed": "100", "Trialed": "False",
                          "UpdateFlag": "", "ObjectNode": {"ProfileName": "All Full Speed Operation Space",
                                                           "BindingSpace": "", "BindingBase": "RobotBase"},
                          "SubFlowName": "", "ThreadName": "", "CompileOption": None, "Version": "1.72.3800.29688",
                          "NonPauseFlag": False, "NoIOInitial": False, "Tag": "", "Attribute": 0,
                          "EnableBlendingSetCmd": True, "EnableBusyLoopOptimization": False},
            "BaseObjectSingle": objs, "BaseObjectMulti": [], "SubFlowStart": [], "MultiThreadStart": [],
            "ChildNode": objs[0]["Name"]}
    flow_text = json.dumps(flow, indent=2, ensure_ascii=False).replace("\n", CRLF)
    dat = CRLF.join(['<?xml version="1.0" encoding="UTF-8" standalone="no"?>', "<Root>", "  <RobotPoints>"]
                    + point_lines + ["  </RobotPoints>", "  <RobotBases>",
                                     '    <Base name="RobotBase" basedata="0,0,0,0,0,0" type="R" number="0" />',
                                     f'    <Base name="{base["name"]}" basedata="{fmt_base(base["pose"])}" type="C" number="1" />',
                                     "  </RobotBases>", "  <VirtualTCP>", "  </VirtualTCP>", "  <Network>", "  </Network>",
                                     "  <FTSensor>", "  </FTSensor>", "  <FineTuneVariable>", "  </FineTuneVariable>",
                                     "  <Conveyor>", "  </Conveyor>", "  <DisplayMgr>", '    <Pwd pwd="" />',
                                     "  </DisplayMgr>", "  <SafetySpace>", "  </SafetySpace>", "  <MaxBaseNumber>",
                                     f'    <Custom max="{extra.get("custom_max", 113)}" />', '    <Vision max="0" />',
                                     "  </MaxBaseNumber>", "  <ModbusDevice>",
                                     '    <Device DeviceName="localhost" Type="TCP" IP="127.0.0.1" Port="502" ID="1" Timeout="10000" />',
                                     "  </ModbusDevice>", '  <DisableSmartSafetySpeed value="false" />',
                                     '  <RefreshDILPeriod value="300" />', "  <RunStopSetting />", "  <RunErrorSetting />",
                                     "</Root>"])
    x, y, z, rx, ry, rz = tcp["pose"]
    f3 = lambda v: f"{v:.3f}"
    cfg = CRLF.join(["<Configuration>", "  <TCPConfig> ", '    <EndEffector order="1" default="false">',
                     f"      <Name>{tcp['name']}</Name>", "      <Description />", "      <GPTFF>",
                     f"        <X>{f3(x)}</X>", f"        <Y>{f3(y)}</Y>", f"        <Z>{f3(z)}</Z>",
                     f"        <W>{f3(rz)}</W>", f"        <V>{f3(ry)}</V>", f"        <U>{f3(rx)}</U>", "      </GPTFF>",
                     "      <Mass>0.0</Mass>", "      <MassCenter>"] + [f"        <{a}>0</{a}>" for a in "XYZWVU"]
                    + ["      </MassCenter>", "      <Inertia>", "        <Ixx>0</Ixx>", "        <Iyy>0</Iyy>",
                       "        <Izz>0</Izz>", "      </Inertia>", "      <GPTCF>"]
                    + [f"        <{a}>0</{a}>" for a in "XYZWVU"]
                    + ["      </GPTCF>", "    </EndEffector> ", "  </TCPConfig>", "</Configuration>", ""])
    return {"ConfigData.xml": cfg.encode("utf-8"),
            f"Projects/{prog}/{prog}.dat": dat.encode("utf-8"),
            f"Projects/{prog}/{prog}.flow": flow_text.encode("utf-8"),
            f"Projects/{prog}/{prog}.prog": PROG_STUB}


RELOAD_WAIT_MS = 120000                                    # a reload step's WaitFor in the TMflow export (2 min)


def _wait(ms):
    return {"DIOData": [], "DIOThan": "or", "CameraLightOnOff": None, "AIOData": [], "AIOThan": "or", "MathData": [],
            "MathThan": "or", "ComplianceData": [], "ComplianceThan": "or", "TimeData": str(ms), "Condition": "&&"}


def pack(files, out, packer="auto", password=PASSWORD, vendor=VENDOR):
    """Write the project: 'tmexportzip' (RoboDK's stand-alone packer, adds TMflow's comment tag), 'python'
    (ZipCrypto, no tag), 'dir' (unzipped folder), 'auto' = tmexportzip if present else python. Returns the packer used."""
    out = Path(out)
    if packer == "auto":                                   # TMExportZip first (TMflow's tag), else pure Python
        if TMEXPORTZIP.exists():
            try:
                return pack(files, out, "tmexportzip", password, vendor)
            except (RuntimeError, OSError, subprocess.SubprocessError) as e:
                print(f"TMExportZip failed ({str(e).strip().splitlines()[-1]}): packed in Python, without its tag")
        packer = "python"
    if packer == "dir":
        for n, b in files.items():
            (out / n).parent.mkdir(parents=True, exist_ok=True)
            (out / n).write_bytes(b)
        return packer
    out.parent.mkdir(parents=True, exist_ok=True)
    if packer == "python":
        write_zip(files, out, password)
        return packer
    # TMExportZip zips the *contents* of each directory given into <dir>.zip next to it
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / out.stem
        for n, b in files.items():
            (src / n).parent.mkdir(parents=True, exist_ok=True)
            (src / n).write_bytes(b)
        r = subprocess.run([str(TMEXPORTZIP), f"/V:{vendor}", f"/P:{password}", str(src)], capture_output=True,
                           text=True, cwd=tmp, timeout=120)
        made = Path(tmp) / f"{out.stem}.zip"
        for junk in Path(tmp).glob("DotNetZip-*.tmp"):
            junk.unlink()
        if not made.exists():
            raise RuntimeError(f"TMExportZip made no zip: {r.stdout} {r.stderr}")
        shutil.copy(made, out)
    return packer


# ------------------------------------------------------------------ diff
def diff(a, b, la="A", lb="B"):
    """Readable differences between two exports ({name: bytes} from read_zip / build_project). Returns lines."""
    out = []
    names = sorted({n for n in a if n} | {n for n in b if n})
    for n in names:
        if n not in a or n not in b:
            out.append(f"{n}: only in {la if n in a else lb}")
            continue
        if a[n] == b[n]:
            out.append(f"{n}: identical ({len(a[n])} bytes)")
            continue
        if n.endswith(".flow"):
            fa, fb = (json.loads(x[n].decode("utf-8-sig")) for x in (a, b))
            na, nb = fa["BaseObjectSingle"], fb["BaseObjectSingle"]
            out.append(f"{n}: {len(na)} vs {len(nb)} nodes")
            fields = {}
            for x, y in zip(na, nb):
                for k in set(x) | set(y):
                    if k == "ObjectNode":
                        for kk in set(x[k]) | set(y[k]):
                            if x[k].get(kk) != y[k].get(kk):
                                fields.setdefault(f"ObjectNode.{kk}", []).append((x["Name"], x[k].get(kk), y[k].get(kk)))
                    elif x.get(k) != y.get(k):
                        fields.setdefault(k, []).append((x["Name"], x.get(k), y.get(k)))
            for k, v in fields.items():
                ex = v[0]
                out.append(f"    {k}: {len(v)} nodes differ, e.g. {ex[0]}: {str(ex[1])[:70]!r} vs {str(ex[2])[:70]!r}")
            if not fields and len(na) == len(nb):
                out.append("    nodes identical (bytes differ in layout only)")
        elif n.endswith(".dat"):
            la_, lb_ = a[n].decode().split(CRLF), b[n].decode().split(CRLF)
            pa = [l for l in la_ if "<Point " in l]
            pb = [l for l in lb_ if "<Point " in l]
            out.append(f"{n}: {len(pa)} vs {len(pb)} points" + ("" if len(pa) == len(pb) else
                       " (different de-duplication: the point lists below are compared by position, not aligned)"))
            attrs = {}
            worst = {}
            for x, y in zip(pa, pb):
                ax, ay = dict(re.findall(r'(\w+)="([^"]*)"', x)), dict(re.findall(r'(\w+)="([^"]*)"', y))
                for k in ax:
                    if ax[k] != ay.get(k):
                        attrs[k] = attrs.get(k, 0) + 1
                        try:
                            d = max(abs(u - v) for u, v in zip(parse_csv(ax[k]), parse_csv(ay[k])))
                            worst[k] = max(worst.get(k, 0), d)
                        except ValueError:
                            pass
            for k, c in attrs.items():
                out.append(f"    {k}: {c} points differ" + (f", max {worst[k]:.4g}" if k in worst else ""))
            rest_a = [l for l in la_ if "<Point " not in l]
            rest_b = [l for l in lb_ if "<Point " not in l]
            for x, y in zip(rest_a, rest_b):
                if x != y:
                    out.append(f"    {x.strip()} vs {y.strip()}")
        else:
            out.append(f"{n}: differs ({len(a[n])} vs {len(b[n])} bytes)")
    try:
        out += compare_moves(parse_project(a), parse_project(b))
    except Exception as e:                                  # noqa: BLE001
        out.append(f"move-by-move comparison not possible: {e}")
    ca, cb = a.get(None), b.get(None)
    if ca is not None or cb is not None:
        out.append(f"zip comment: {len(ca or b'')} vs {len(cb or b'')} bytes, "
                   f"{'identical' if ca == cb else 'different'} (TMExportZip's tag, includes a timestamp)")
    return out


def compare_moves(pa, pb):
    """What the robot would do differently: move by move (type, speed, flange pose in the base, joints) and the
    gripper/wait/message steps in between."""
    ma = [s for s in pa["steps"] if "move" in s]
    mb = [s for s in pb["steps"] if "move" in s]
    out = [f"program: {len(ma)} vs {len(mb)} moves"]
    kind = sum(x["move"] != y["move"] for x, y in zip(ma, mb))
    spd = sum(x["move"] == "line" and x["speed"] != y["speed"] for x, y in zip(ma, mb))
    err = [K.pose_error(x["pose_base"], y["pose_base"]) for x, y in zip(ma, mb)]   # (mm, deg), Euler-proof
    dp, da = max((e[0] for e in err), default=0), max((e[1] for e in err), default=0)
    dj = max((max(abs(u - v) for u, v in zip(x["joints"], y["joints"])) for x, y in zip(ma, mb)), default=0)
    dj_ptp = max((max(abs(u - v) for u, v in zip(x["joints"], y["joints"])) for x, y in zip(ma, mb)
                  if x["move"] == "ptp"), default=0)
    out.append(f"    move type differs: {kind}, line speed differs: {spd}, flange pose max diff {dp:.4f} mm / "
               f"{da:.4f} deg, joints max diff {dj:.4f} deg (PTP targets: {dj_ptp:.4f} deg)")
    other = lambda p: [(k, s[k]) for s in p["steps"] if "move" not in s for k in ("do0", "gripper", "wait_ms", "message")
                       if k in s] + [("parts", tuple(s["parts"])) for s in p["steps"] if s.get("parts")]
    oa, ob = other(pa), other(pb)
    out.append(f"    I/O, waits, messages: {'identical' if oa == ob else f'{sum(x != y for x, y in zip(oa, ob))} differ'}"
               f" ({len(oa)} vs {len(ob)} items)")
    return out


def load_program(path, base_from=None):
    path = Path(path)
    if path.suffix == ".zip":
        return parse_project(read_zip(path))
    prog = json.loads(path.read_text(encoding="utf-8"))
    if base_from:
        ref = parse_project(read_zip(base_from))
        prog.setdefault("base", ref["base"])
        prog.setdefault("tcp", ref["tcp"])
    return prog


def selftest(out_dir):
    """Every export in bench_tmflow: zip -> program -> project, compared with the original; v4 also from the
    station's own data (tests/v4_moves.json) with v4's base."""
    out_dir = Path(out_dir)
    ok = True
    for v in ("v3", "v4", "v6", "v7"):
        z = CELL / "bench_tmflow" / v / "AssembleBench.zip"
        if not z.exists():
            continue
        ref = read_zip(z)
        prog = parse_project(ref)
        (out_dir / f"{v}_program.json").parent.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{v}_program.json").write_text(json.dumps(prog, indent=1))
        mine = build_project(prog)
        same = [n for n in mine if ref.get(n) == mine[n]]
        print(f"{v}: {sum('move' in s for s in prog['steps'])} moves, {len(same)}/{len(mine)} files byte-identical "
              f"after import -> export")
        for line in diff(ref, mine, "RoboDK", "ours"):
            if "identical" not in line or "nodes" in line:
                print("   ", line)
        ok &= len(same) == len(mine)
    mv = CELL / "tests" / "v4_moves.json"
    if mv.exists():
        prog = load_program(mv, base_from=CELL / "bench_tmflow" / "v4" / "AssembleBench.zip")
        prog["steps"].insert(0, {"message": "Simulation: parts to start"})   # not in the moves file
        ref = read_zip(CELL / "bench_tmflow" / "v4" / "AssembleBench.zip")
        mine = build_project(prog)
        print("v4 from tests/v4_moves.json (the station's own moves, no zip data except the base):")
        for line in diff(ref, mine, "RoboDK", "ours"):
            print("   ", line)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import", help="TMflow zip -> program json")
    s.add_argument("zip")
    s.add_argument("-o", "--out")
    s = sub.add_parser("export", help="program json / moves json / zip -> TMflow zip")
    s.add_argument("program")
    s.add_argument("-o", "--out", required=True)
    s.add_argument("--packer", choices=["auto", "tmexportzip", "python", "dir"], default="auto")
    s.add_argument("--vendor", default=VENDOR)
    s.add_argument("--base-from", help="take base + TCP from this export (a moves file has none)")
    s.add_argument("--fresh", action="store_true", help="drop the imported RoboDK header / Custom max (tmflow block)")
    s = sub.add_parser("diff", help="compare two exports (zip or folder)")
    s.add_argument("a")
    s.add_argument("b")
    s = sub.add_parser("selftest")
    s.add_argument("--out", default=str(HERE / "ref"))
    a = ap.parse_args()
    if a.cmd == "import":
        prog = parse_project(read_zip(a.zip))
        text = json.dumps(prog, indent=1)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(text)
            print(f"{a.out}: {sum('move' in x for x in prog['steps'])} moves, {len(prog['steps'])} steps")
        else:
            print(text)
    elif a.cmd == "export":
        prog = load_program(a.program, a.base_from)
        if a.fresh:
            prog.pop("tmflow", None)
        used = pack(build_project(prog), a.out, a.packer, vendor=a.vendor)
        print(f"{a.out}: {sum('move' in x for x in prog['steps'])} moves, packed with {used}")
    elif a.cmd == "diff":
        def get(p):
            p = Path(p)
            if p.is_dir():
                return {str(f.relative_to(p)).replace("\\", "/"): f.read_bytes() for f in p.rglob("*") if f.is_file()}
            return read_zip(p)
        print("\n".join(diff(get(a.a), get(a.b), a.a, a.b)))
    elif a.cmd == "selftest":
        raise SystemExit(0 if selftest(a.out) else 1)


if __name__ == "__main__":
    main()
