"""Mirror the real TM5-900 in RoboDK: reads the joints from the Ethernet Slave stream (port 5891,
read-only) and sets the robot in RoboDK's open station to match. Sends nothing to the robot, so it
runs next to any Listen-node script (hande_bridge.py, listen_loop_test.py).

    python robot_cell/tests/robodk_mirror.py        Ctrl+C to stop
"""
import re
import socket
import time

from robodk import robolink

import listen_pick_place_test as lt

RATE = 0.05                                             # RoboDK update interval [s]
JOINTS = re.compile(rb"Joint_Angle=\{([^}]*)\}")

RDK = robolink.Robolink()
robot = RDK.Item("", robolink.ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit("no robot in the open RoboDK station")
RDK.setRunMode(robolink.RUNMODE_SIMULATE)               # this script must never drive the real robot
print(f"mirroring {lt.IP}:{lt.SLAVE} onto RoboDK robot '{robot.Name()}', Ctrl+C to stop")

try:
    with socket.create_connection((lt.IP, lt.SLAVE), timeout=3) as s:
        buf, last = b"", 0.0
        while True:
            chunk = s.recv(4096)
            if not chunk:
                raise SystemExit("Ethernet Slave stream closed")
            buf += chunk
            m = None
            for m in JOINTS.finditer(buf):              # keep only the newest complete reading
                pass
            if m:
                buf = buf[m.end():]
                if time.time() - last > RATE:
                    robot.setJoints([float(v) for v in m.group(1).split(b",")])
                    last = time.time()
            else:
                buf = buf[-8192:]
except KeyboardInterrupt:
    print("stopped")
