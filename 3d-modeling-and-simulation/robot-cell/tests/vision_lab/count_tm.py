"""Count the Techman-plate corners in calibration photos (calibrate.py --board tm). Usage: count_tm.py <png>..."""
import sys
import cv2
import calibrate as C
C.KIND = "tm"
for f in sys.argv[1:]:
    r = C.detect(cv2.imread(f))
    print(f"{f}: {'NOT FOUND' if r is None else str(len(r[0])) + ' corners'}")
