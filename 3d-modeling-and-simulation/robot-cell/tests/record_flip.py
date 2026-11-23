"""Record the frame flip by hand: move the arm with FreeBot, Enter at each good position -> its joints + pose are
saved as a waypoint. bench_cell_v11_1plank.py then drives them as joint moves ('frame flip hand 1..n') between
'frame flip turn 15' and 'frame flip above guide', instead of the calculated flip.

    python tests/record_flip.py            (read-only towards the robot: Modbus 7001 pose, 7013 joints)

Keys:  Enter = save this position as the next waypoint   d = delete the last one   l = list
       q = save the file and quit  (tests/v11_1plank_flip_waypoints.json; then rebuild: bench_cell_v11_1plank.py)
"""
import json
import msvcrt
import socket
import struct
import sys
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent / "v11_1plank_flip_waypoints.json"
IP = "10.0.12.101"


def read(addr):
    s = socket.create_connection((IP, 502), timeout=2)
    s.sendall(struct.pack(">HHHBBHH", 1, 0, 6, 1, 4, addr, 12))
    r = s.recv(64)
    s.close()
    return [round(v, 3) for v in struct.unpack(">6f", r[9:33])]


def main():
    wps = json.loads(OUT.read_text())["waypoints"] if OUT.exists() else []
    if wps:
        print(f"{len(wps)} waypoint(s) already in {OUT.name} - new ones are added after them (d deletes the last).")
    print("Move the arm by hand (FreeBot). Enter = save position, d = delete last, l = list, q = save + quit.\n")
    while True:
        try:
            p, q = read(7001), read(7013)
            sys.stdout.write(f"\r  pose {' '.join(f'{v:8.2f}' for v in p)}   J {' '.join(f'{v:7.1f}' for v in q)}  ")
            sys.stdout.flush()
        except OSError:
            sys.stdout.write("\r  (no answer from the robot)                                                       ")
        if msvcrt.kbhit():
            k = msvcrt.getwch().lower()
            if k in "\r\n":
                wps.append({"pose": p, "joints": q, "time": time.strftime("%H:%M:%S")})
                print(f"\n  saved waypoint {len(wps)}: J {[round(v, 1) for v in q]}")
                lims = [(-270, 270), (-180, 180), (-155, 155), (-180, 180), (-180, 180), (-270, 270)]
                near = [f"J{j + 1} {q[j]:.0f} (limit {lims[j][0] if q[j] < 0 else lims[j][1]})"
                        for j in range(6) if min(q[j] - lims[j][0], lims[j][1] - q[j]) < 8]
                if near:
                    print("    !! close to a limit: " + ", ".join(near) + " - move a bit away, d, then Enter again")
                if len(wps) > 1:
                    jj = max(range(6), key=lambda j: abs(q[j] - wps[-2]["joints"][j]))
                    jump = abs(q[jj] - wps[-2]["joints"][jj])
                    print(f"    biggest joint change from the last point: J{jj + 1} {jump:.0f} deg"
                          + ("  !! big - add a point in between (d, go back half way, Enter, then here again)"
                             if jump > 45 else ""))
            elif k == "d" and wps:
                wps.pop()
                print(f"\n  deleted the last one - {len(wps)} left")
            elif k == "l":
                print()
                for n, w in enumerate(wps, 1):
                    print(f"  {n}: J {[round(v, 1) for v in w['joints']]}  xyz {[round(v) for v in w['pose'][:3]]}")
            elif k == "q":
                OUT.write_text(json.dumps({"note": "frame flip waypoints recorded by hand (record_flip.py)",
                                           "waypoints": wps}, indent=1), encoding="utf-8")
                print(f"\n{len(wps)} waypoint(s) saved in {OUT}")
                return
        time.sleep(0.25)


if __name__ == "__main__":
    main()
