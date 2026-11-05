"""tmflow_mock.py with our own kinematics (tm5_kin.py) and the 3D view (sim_view.html at /sim/), no RoboDK,
without changing tmflow_mock.py - until its --sim option (sim_option.patch) is in, and for running a
second mock on other ports next to the one on 5890/5891/8090.

    python robot_cell/tests/robot_sim/mock_sim.py serve --flow testjb2 --view 8092 --listen 5990 --slave 5991
        then open http://127.0.0.1:8092/sim/
    python robot_cell/tests/robot_sim/mock_sim.py serve --geometry robodk     link lengths of RoboDK's robot

serve takes tmflow_mock's own options (--flow, --grip, --fast, --project-speed, --rate, --points, --view,
--diagram, -v) plus --listen/--slave (ports; lt.LISTEN/lt.SLAVE) and --geometry; --robodk is implied
(tmflow_mock's RoboDK class is swapped for tm5_kin.TM5Kin). --mock-dir: where tmflow_mock.py is (default ..).
"""
import argparse
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tm5_kin                                          # noqa: E402
from sim_http import sim_get                            # noqa: E402

class Options(argparse.Namespace):
    """tmflow_mock options this file doesn't know (the mock keeps growing) read as None."""

    def __getattr__(self, name):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mock-dir", default=str(HERE.parent), help="folder with tmflow_mock.py (default ..)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--listen", type=int, default=5890, help="Listen node port (default 5890)")
    s.add_argument("--slave", type=int, default=5891, help="Ethernet Slave port (default 5891)")
    s.add_argument("--geometry", choices=tm5_kin.GEOMETRY, default="techman", help="link lengths (default techman)")
    # tmflow_mock serve's own options, same defaults
    s.add_argument("--flow", default="hande")
    s.add_argument("--grip", default="ok")
    s.add_argument("--fast", type=float, default=1)
    s.add_argument("--project-speed", type=float, default=100)
    s.add_argument("--rate", type=float, default=50)
    s.add_argument("--points")
    s.add_argument("--view", type=int, default=8092, help="live view port (default 8092, not the mock's 8090)")
    s.add_argument("--diagram")
    s.add_argument("-v", "--verbose", action="store_true")
    a = Options(**vars(ap.parse_args()))

    sys.path.insert(0, str(Path(a.mock_dir).resolve()))
    import tmflow_mock as tm
    if a.flow not in tm.FLOWS:
        raise SystemExit(f"--flow: one of {', '.join(tm.FLOWS)}")
    for port in (a.listen, a.slave, a.view):           # another mock may be on them: stop before it gets packets
        try:
            socket.create_server((tm.HOST, port)).close()
        except OSError:
            raise SystemExit(f"port {port} is in use (another mock?) - pick others with --listen/--slave/--view")
    tm.lt.LISTEN, tm.lt.SLAVE = a.listen, a.slave
    tm5_kin.use(a.geometry)

    class Kin(tm5_kin.TM5Kin):
        def __init__(self, *_, **__):                  # RoboDK(station, robot): not used here
            tm.log(f"kinematics: tm5_kin.py ({a.geometry} geometry), 3D view on /sim/")

    tm.RoboDK = Kin
    Server = tm.ThreadingHTTPServer

    class SimServer(Server):                            # the mock's view server, plus /sim/
        def __init__(self, addr, handler):
            class H(handler):
                def do_GET(self):
                    if not sim_get(self):
                        super().do_GET()
            super().__init__(addr, H)

    tm.ThreadingHTTPServer = SimServer
    a.robodk = True
    a.diagram = a.diagram or str(Path(a.mock_dir) / "listen_loop_flow.html")
    tm.serve(a)


if __name__ == "__main__":
    main()
