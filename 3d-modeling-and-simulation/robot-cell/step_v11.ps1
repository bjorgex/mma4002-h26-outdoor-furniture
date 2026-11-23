# Step through the v11 one-plank test on the real robot (tests/step_run.py), Listen mode via HandE_Bridge_v1.
# Enter = next step, z 50 = up 50 mm, save = store where the robot is now as the last move's taught pose, q = stop.
Set-Location "C:\Users\bjoer\dev\studyDev\mma4002-h26-outdoor-furniture\3d-modeling-and-simulation\robot-cell"
$Host.UI.RawUI.WindowTitle = "Step-v11-1plank"
& "C:\Users\bjoer\dev\studyDev\MSc-MechAuto-NTNU\.venv\Scripts\python.exe" tests/step_run.py --cell v11_1plank @args
