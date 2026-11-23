# Teach the v11 one-plank grip points by hand (FreeBot): live pose, Enter = save, s = skip, b = back, q = quit.
Set-Location "C:\Users\bjoer\dev\studyDev\mma4002-h26-outdoor-furniture\3d-modeling-and-simulation\robot-cell"
$Host.UI.RawUI.WindowTitle = "Teach-by-hand-v11"
& "C:\Users\bjoer\dev\studyDev\MSc-MechAuto-NTNU\.venv\Scripts\python.exe" tests/teach_walk.py v11_1plank @args
