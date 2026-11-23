# Record the frame flip by hand (FreeBot): Enter = save position, d = delete last, l = list, q = save + quit.
Set-Location "C:\Users\bjoer\dev\studyDev\mma4002-h26-outdoor-furniture\3d-modeling-and-simulation\robot-cell"
$Host.UI.RawUI.WindowTitle = "Record-flip"
& "C:\Users\bjoer\dev\studyDev\MSc-MechAuto-NTNU\.venv\Scripts\python.exe" tests/record_flip.py
