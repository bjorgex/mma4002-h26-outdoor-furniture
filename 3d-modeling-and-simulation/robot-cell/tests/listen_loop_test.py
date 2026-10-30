"""Looping pick-and-place on the real TM5-900, driven through the TMflow project "testjb2".
Moves a box back and forth between two taught spots: pick at A, place at B, pick at B, place at A...

testjb2 flow (Manual mode), node names as below:
    Start -> P3 -> SET1 -> (OK|FAIL) -> Listen1
    Listen1 Pass -> RELEASE1 -> (OK|FAIL) -> Listen2
    Listen2 Pass -> GRIP1   -> (OK|FAIL) -> Listen1      LOSS -> Listen3
Listen1 = go to the place spot (RELEASE follows), Listen2 = go to the pick spot (GRIP follows).
The script asks the robot which Listen node it is in after every gripper node, so it follows
whichever exit GRIP took. Listen3 (no object in the fingers) retracts and stops.

Spots are the same ones listen_pick_place_test.py teaches (listen_test_points.json):
    python robot_cell/tests/listen_pick_place_test.py teach pick     where the box starts
    python robot_cell/tests/listen_pick_place_test.py teach place    the other spot
    python robot_cell/tests/listen_loop_test.py --above 50           dry run 50 mm above both spots
    python robot_cell/tests/listen_loop_test.py --cycles 4           4 moves of the box (2 round trips)
"""
import argparse
import json

import listen_pick_place_test as lt

PLACE_NODE, PICK_NODE, LOSS_NODE = "Listen1", "Listen2", "Listen3"


def where(r):
    """Name of the Listen node the flow waits in: $TMSTA,15,00,true,Listen1,*79"""
    return r.status("00").split(",")[4]


def go(r, target, above):
    """Up LIFT mm from here, across at that height, then straight down onto target."""
    here = lt.read_state()["flange"]
    r.move(lt.line(here, lt.LIFT), lt.line(target, above + lt.LIFT), lt.line(target, above))


def park(r, why):
    """Retract and leave the robot waiting in this Listen node (no ScriptExit)."""
    r.move(lt.line(lt.read_state()["flange"], lt.LIFT))
    r.s.close()
    print(f"{why}\nParked in a Listen node: stop the project in TMflow.")


def run(cycles, above):
    pts = json.loads(lt.POINTS.read_text())
    src, dst = pts["pick"]["flange"], pts["place"]["flange"]
    print(f"A ({src[0]:.0f}, {src[1]:.0f}) z {src[2] + above:.0f}   B ({dst[0]:.0f}, {dst[1]:.0f}) z {dst[2] + above:.0f}")
    print(f"{cycles} moves of the box, approach height +{lt.LIFT} mm")
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
                return park(r, "done")
            go(r, src, above)
            held = True
            print("at pick, gripping")
            r.exit()
        elif node == LOSS_NODE:
            return park(r, "GRIP reported LOSS: no object between the fingers.")
        else:
            raise RuntimeError(f"unexpected Listen node {node!r}: check the node names in testjb2")
        r = lt.Listen()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=2, help="moves of the box (2 = there and back)")
    ap.add_argument("--above", type=float, default=0, help="extra height on both spots [mm] (dry run)")
    a = ap.parse_args()
    run(a.cycles, a.above)
