"""Looping pick-and-place on the real TM5-900, driven through the TMflow project "testjb2".
Moves a box back and forth between two taught spots: pick at A, place at B, pick at B, place at A...

testjb2 flow (Manual mode), node names as below:
    Start -> P3 -> SET1 -> (OK|FAIL) -> Listen1
    Listen1 Pass -> RELEASE1 -> (OK|FAIL) -> Listen2
    Listen2 Pass -> GRIP1   -> (OK|FAIL) -> Listen1      LOSS -> Listen3
Listen1 = go to the place spot (RELEASE follows), Listen2 = go to the pick spot (GRIP follows).
The script asks the robot which Listen node it is in after every gripper node, so it follows
whichever exit GRIP took. Listen3 (no object in the fingers) retracts and stops.

A finished run goes home and stays in Listen2, the node the next run starts from, so the script
can run again without restarting the project. An even --cycles leaves the box where it started.

Spots are the ones listen_pick_place_test.py teaches (listen_test_points.json), plus home:
    python robot_cell/tests/listen_pick_place_test.py teach pick     where the box starts
    python robot_cell/tests/listen_pick_place_test.py teach place    the other spot
    python robot_cell/tests/listen_loop_test.py teach-home           where every run ends (e.g. P3)
    python robot_cell/tests/listen_loop_test.py --above 50           dry run 50 mm above both spots
    python robot_cell/tests/listen_loop_test.py --cycles 4           4 moves of the box (2 round trips)
"""
import argparse
import json

import listen_pick_place_test as lt

PLACE_NODE, PICK_NODE, LOSS_NODE = "Listen1", "Listen2", "Listen3"
HOME_SPEED = 20                                         # joint move home [% of max speed]


def where(r):
    """Name of the Listen node the flow waits in: $TMSTA,15,00,true,Listen1,*79"""
    return r.status("00").split(",")[4]


def ptp(joints):
    """Joint move. JPP = joint angles, speed in %, blend in %."""
    j = ",".join(f"{v:.3f}" for v in joints)
    return f'PTP("JPP",{j},{HOME_SPEED},{lt.ACC},0,false)'


def go(r, target, above):
    """Up LIFT mm from here, across at that height, then straight down onto target."""
    here = lt.read_state()["flange"]
    r.move(lt.line(here, lt.LIFT), lt.line(target, above + lt.LIFT), lt.line(target, above))


def park(r, why, home=None):
    """Lift (then go home, if given) and leave the robot waiting in this Listen node (no ScriptExit)."""
    moves = [lt.line(lt.read_state()["flange"], lt.LIFT)]
    if home:
        moves.append(ptp(home))
    r.move(*moves)
    r.s.close()
    print(why)


def teach_home():
    pts = json.loads(lt.POINTS.read_text()) if lt.POINTS.exists() else {}
    pts["home"] = lt.read_state()
    lt.POINTS.write_text(json.dumps(pts, indent=2))
    print("home: joints", pts["home"]["joints"])


def run(cycles, above):
    pts = json.loads(lt.POINTS.read_text())
    if "home" not in pts:
        raise SystemExit("no home pose yet: python robot_cell/tests/listen_loop_test.py teach-home")
    src, dst, home = pts["pick"]["flange"], pts["place"]["flange"], pts["home"]["joints"]
    print(f"A ({src[0]:.0f}, {src[1]:.0f}) z {src[2] + above:.0f}   B ({dst[0]:.0f}, {dst[1]:.0f}) z {dst[2] + above:.0f}")
    print(f"{cycles} moves of the box, approach height +{lt.LIFT} mm, then home")
    input("Manual mode, low project speed, hand on the E-stop, testjb2 running. Enter to start ")

    held, moved = False, 0
    r = lt.Listen()
    while True:
        node = where(r)
        print("in", node)
        if node == PLACE_NODE:
            if held:
                go(r, dst, above)
                held, moved = False, moved + 1
                src, dst = dst, src
                print(f"move {moved}/{cycles}: placed, releasing")
            r.exit()
        elif node == PICK_NODE:
            if moved >= cycles:
                return park(r, "Done and home. Waiting in Listen2: run again, or stop the project.", home)
            go(r, src, above)
            held = True
            print("at pick, gripping")
            r.exit()
        elif node == LOSS_NODE:
            return park(r, "GRIP reported LOSS: no object between the fingers. Stop the project in TMflow.")
        else:
            raise RuntimeError(f"unexpected Listen node {node!r}: check the node names in testjb2")
        r = lt.Listen()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="run", choices=["run", "teach-home"])
    ap.add_argument("--cycles", type=int, default=2, help="moves of the box (even = it ends where it started)")
    ap.add_argument("--above", type=float, default=0, help="extra height on both spots [mm] (dry run)")
    a = ap.parse_args()
    teach_home() if a.cmd == "teach-home" else run(a.cycles, a.above)
