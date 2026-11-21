"""Build the Part B2 sandbox from the finished Part B sandbox, then run the leak check.

    python make_sandbox_b2.py [--src ~/dev/assembly-blind] [--root ~/dev/assembly-blind-b2] [--force]   (server)

Why a second run: Part B stopped at its 30-iteration cap while still improving (streak 0, iter 30 kept), so the
question "how far can it go" was not answered. B2 starts where B ended and keeps what B learned:
    design/, best/     Part B's best (iter 30), the start of B2 (design = best)
    toolbox/, scratch/ Part B's own tools and probe scripts (its lessons point at them)
    judge/             judge_b2/: Part B's judge + the judge fix Part B proposed (Line time includes tool rotation),
                       + B2 bookkeeping (a '## Reason' section is required, a 'reason' column, a time budget)
    AGENT.md           sandbox_src/AGENT_B2.md (Part B's brief + "where run B ended", the reason rule, 3 h budget)
    log/lessons.md, log/tool_changes.md   Part B's, headings re-tagged "(B iter NN)" so the per-iteration counters
                       of B2 do not count them; B2's blocks follow under a "Run B2" header
    <root>.settings.json, <root>.judge.sha256   (outside) as for Part B, paths changed to <root>
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_sandbox import JUDGE_FILES, leak_check, write    # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def retag(text):
    return re.sub(r"^(## [LT]\d+ )\(iter (\d+)\)", r"\1(B iter \2)", text, flags=re.M)


def build(src, root, force):
    if root.exists():
        if not force:
            raise SystemExit(f"{root} exists (use --force)")
        for p in root.rglob("*"):
            os.chmod(p, stat.S_IRWXU) if p.is_dir() else os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
        os.chmod(root, stat.S_IRWXU)
        shutil.rmtree(root)
    ign = shutil.ignore_patterns("__pycache__")
    root.mkdir(parents=True)
    for d in ("best", "toolbox", "scratch"):
        if (src / d).exists():
            shutil.copytree(src / d, root / d, ignore=ign)
    shutil.copytree(src / "best", root / "design", ignore=ign)       # design = best (Part B iter 30)
    for f in ("py", "CLAUDE.md"):
        shutil.copy2(src / f, root / f)
    os.chmod(root / "py", 0o755)
    shutil.copy2(HERE / "sandbox_src" / "AGENT_B2.md", root / "AGENT.md")
    # the judge
    (root / "judge").mkdir()
    for f in JUDGE_FILES:
        shutil.copy2(HERE / "judge_b2" / f, root / "judge" / f)
    sums = "".join(f"{sha(root / 'judge' / f)}  {f}\n" for f in JUDGE_FILES)
    write(root / "judge" / "SHA256SUMS", sums)
    Path(str(root) + ".judge.sha256").write_text(sums)
    # logs carried over
    (root / "log").mkdir()
    les = retag((src / "log" / "lessons.md").read_text(encoding="utf-8"))
    les = les.replace("# Lessons (problems and fixes)",
                      "# Lessons (problems and fixes)\n\nL01-L30 are from run B (headings tagged \"B iter NN\"); "
                      "run B2's lessons follow under \"Run B2\" and continue the numbering (L31, ...).", 1)
    write(root / "log" / "lessons.md", les.rstrip() + "\n\n# Run B2\n")
    tc = retag((src / "log" / "tool_changes.md").read_text(encoding="utf-8"))
    tc = re.sub(r"^## PROPOSED JUDGE FIX \((noted )?iter (\d+)\)", r"## PROPOSED JUDGE FIX (B iter \2)", tc, flags=re.M)
    tc = tc.rstrip() + ("\n\nThe Line-rotation judge fix above is APPLIED in run B2's judge (judge/cycle_time.py, "
                        "ROT_SPEED).\n\n# Run B2\n")
    write(root / "log" / "tool_changes.md", tc)
    # permissions for the headless agent (outside the sandbox)
    s = Path(str(src) + ".settings.json").read_text().replace(str(src) + "/", str(root) + "/")
    Path(str(root) + ".settings.json").write_text(s)
    for f in (root / "judge").iterdir():
        os.chmod(f, 0o444)
    os.chmod(root / "judge", 0o555)
    print(f"built {root} from {src}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", default=str(Path.home() / "dev" / "assembly-blind"))
    ap.add_argument("--root", default=str(Path.home() / "dev" / "assembly-blind-b2"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--leak-check-only", action="store_true")
    ap.add_argument("--skip-log", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).expanduser()
    if not a.leak_check_only:
        build(Path(a.src).expanduser(), root, a.force)
    raise SystemExit(0 if leak_check(root, a.skip_log) else 1)


if __name__ == "__main__":
    main()
