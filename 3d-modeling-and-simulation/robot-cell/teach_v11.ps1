param([string]$First = '')
# Teach v11-1plank grip points on the real robot (teach.py, read-only towards the robot).
# Pick a point by number, jog the robot there, Enter = save. Empty = list again, q = quit.
$ErrorActionPreference = 'Continue'
Set-Location "C:\Users\bjoer\dev\studyDev\mma4002-h26-outdoor-furniture\3d-modeling-and-simulation\robot-cell"
$py = "C:\Users\bjoer\dev\studyDev\MSc-MechAuto-NTNU\.venv\Scripts\python.exe"
$Host.UI.RawUI.WindowTitle = "Teach v11-1plank"
while ($true) {
    & $py tests/robot_sim/teach.py v11_1plank --list
    $lines = & $py tests/robot_sim/teach.py v11_1plank --list | Select-Object -Skip 1
    if ($First) { $k = $First; $First = '' } else { $k = Read-Host "`nPoint number to teach (Enter = list again, s = show taught, r = rebuild program, q = quit)" }
    if ($k -eq 'q') { break }
    if ($k -eq 's') { & $py tests/robot_sim/teach.py v11_1plank --show; continue }
    if ($k -eq 'r') { & $py tests/robot_sim/teach.py v11_1plank --rebuild; continue }
    if ($k -notmatch '^\d+$') { continue }
    $line = $lines | Where-Object { $_ -match "^\s*$k\s" } | Select-Object -First 1
    if (-not $line) { Write-Host "no point $k"; continue }
    $name = ((($line -replace '^\s*\d+\s+(grip|release)\s+','') -split '->')[-1] -replace '\[.*$','' -replace '\*','').Trim().ToLower()
    Write-Host "`n== teaching '$name': jog the robot there, then Enter (q + Enter = cancel) ==" -ForegroundColor Yellow
    # --max-mm 80: the real cell is up to ~30 mm off the CAD (rack 28 mm in -Y, camera 2026-11-20), plus the grip itself
    & $py tests/robot_sim/teach.py v11_1plank $name --real --max-mm 300
}



