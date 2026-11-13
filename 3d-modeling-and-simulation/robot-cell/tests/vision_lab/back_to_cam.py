"""Back to the camera pose safely: up to SAFE_Z, over, down."""
import socket, time, re
exec(open(__file__.replace("back_to_cam.py", "approach.py")).read().split("vb = ask(")[0].replace(
    "FINAL_Z = float(sys.argv[1]) if len(sys.argv) > 1 else 462.0", "FINAL_Z = 0"))
CAM = (-420.95, 0.78, 388.0, -175.2, -0.4, 93.7)
script('ChangeBase("RobotBase")')
import struct
m=socket.create_connection((H,502),timeout=3); m.sendall(struct.pack(">HHHBBHH",1,0,6,1,4,7001,12)); r=m.recv(64); m.close()
cx,cy,cz,crx,cry,crz=[struct.unpack(">f",r[9+i:13+i])[0] for i in range(0,24,4)]
print("current:", cx, cy, cz)
print("1 up");   move(f'Line("CAP",{cx:.2f},{cy:.2f},{SAFE_Z},{crx:.2f},{cry:.2f},{crz:.2f},40,300,0,false)', 1)
print("2 over"); move(f'Line("CAP",{CAM[0]},{CAM[1]},{SAFE_Z},{CAM[3]},{CAM[4]},{CAM[5]},40,300,0,false)', 2)
print("3 down"); move(f'Line("CAP",{CAM[0]},{CAM[1]},{CAM[2]},{CAM[3]},{CAM[4]},{CAM[5]},20,300,0,false)', 3)
print("done"); s.close()
