import shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
STL = HERE / "jig_parts" / "guide_1_v5.stl"
BACKUP = HERE / "jig_parts" / "guide_1_v5.stl.orig"
if BACKUP.exists():
    shutil.move(str(BACKUP), str(STL))
    print("restored", STL)
else:
    print("no backup found - nothing to restore")
