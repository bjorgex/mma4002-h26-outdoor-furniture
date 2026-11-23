#!/usr/bin/env bash
# One TM wrist-camera photo from the CURRENT robot pose: in TMflow's vision editor, Save makes the job test itself,
# which sends the image to tm_camera.py (External Detection, setting laptop_jig); then Cancel the "Save Job" dialog
# (or OK a "not detectable" warning). Prints the new photo and its plate-corner count.  Usage: tm_photo.sh [folder]
cd "$(dirname "$0")"
PY=../../../../../MSc-MechAuto-NTNU/.venv/Scripts/python.exe; CC="$USERPROFILE/dev/dotfiles/windows/claude-cursor/claude_cursor.py"
OUT=${1:-calib_tm}; n0=$(ls "$OUT"/*.png 2>/dev/null | wc -l)
C:/Python313/python.exe "$CC" tmflow-vision click-at 148 192 --allow-raw --hover --keep-focus >/dev/null
for i in $(seq 1 15); do sleep 1; [ "$(ls "$OUT"/*.png 2>/dev/null | wc -l)" -gt "$n0" ] && break; done
sleep 2
for w in "Save Job" "Dialog"; do      # close whatever TMflow shows: Save Job -> Cancel, warning -> OK
  XY=$(C:/Python313/python.exe -c "
import ctypes, ctypes.wintypes as w, sys
u=ctypes.windll.user32; ctypes.windll.shcore.SetProcessDpiAwareness(2)
h=u.FindWindowW(None,'$w')
if not h or not u.IsWindowVisible(h): sys.exit()
p=w.POINT(0,0); u.ClientToScreen(h,ctypes.byref(p)); print(*((1064-p.x, 896-p.y) if '$w'=='Save Job' else (960-p.x, 751-p.y)))" | tr -d '\r')
  [ -n "$XY" ] && C:/Python313/python.exe "$CC" tmflow-vision click-at $XY --allow-raw --hover --keep-focus --window "^$w\$" >/dev/null && sleep 1
done
new=$(ls -t "$OUT"/*.png 2>/dev/null | head -$(( $(ls "$OUT"/*.png 2>/dev/null | wc -l) - n0 )))
[ -z "$new" ] && { echo "NO NEW PHOTO"; exit 1; }
$PY count_tm.py $new
