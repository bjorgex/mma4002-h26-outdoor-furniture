"""Build the Part B sandbox (the blind run's whole world) and run the leak check.

    python make_sandbox.py [--root ~/dev/assembly-blind] [--force]       (server; shared venv)
    python make_sandbox.py --leak-check-only [--root ...]

What goes in (nothing else: no git history, no v4+ scripts, moves, cells or reports):
    AGENT.md, CLAUDE.md           the brief (sandbox_src/AGENT.md), CLAUDE.md points to it
    py                            the venv's python ($ASSEMBLY_PY, set by run_part_b.sh)
    judge/                        the frozen judge (judge/ here): read-only, SHA-256 list in judge/SHA256SUMS, a copy
                                  outside the sandbox (<root>.judge.sha256) for the runner's watchdog
    design/program.json           the v3 program (ref/v3_program.json without the exporter's header)
    design/build_cell.py          the v3 cell builder (constants of the v3 station, numpy, no RoboDK)
    design/meshes/jig, bench      the v3 jig STLs and the bench part meshes + assembly.json
    design/cad/                   jig_parts.py, jig_guide.py, bench_parts.py (paths adapted) + step/ (the 3 STEP inputs)
    toolbox/ (README), log/ (lessons.md, tool_changes.md), best/ (filled by the baseline), scratch/
    <root>.settings.json          (outside) permissions for the headless agent (run_part_b.sh --settings)
Checks: the built cell equals the Part A v3 cell (every object, vertices within 1e-6 mm), then the leak check:
every text file (and the names inside the binary ones) grepped for later design ideas, later version names,
RoboDK and the repo's paths. Exit code 1 if anything is found.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent / "robot-cell"
SIM = CELL / "tests" / "robot_sim"
SRC = HERE / "sandbox_src"
JUDGE_FILES = ["tm5_kin.py", "kin_check.py", "collision.py", "cycle_time.py", "manip.py", "program_io.py", "score.py",
               "shots.py", "iterate.py", "tm5_links.glb", "reference.json"]
JIG_STL = ["base_a", "base_b", "guide", "plank_jig", "ground_base", "vision_square"]
BENCH_STL = ["frame", "interface_piece", "plank_body", "plank", "block"]
STEPS = {"BenchInterfaceV1.STEP": "jig-cad/BenchInterfaceV1.STEP", "JigAssemDraft1.STEP": "jig-cad/JigAssemDraft1.STEP",
         "JigGuide_DoubleSided.STEP": "jig-cad/JigGuide_DoubleSided.STEP"}

# the leak check: later design ideas / names (v4 .. v10), RoboDK, paths into the repo
LEAKS = [r"\bv([4-9]|1\d)\b", r"bench_cell", r"robodk", r"robomath", r"tmflow", r"split[ _-]?guide", r"guide[ _-]?split",
         r"ground_base_split", r"\bhalves\b", r"cut in two", r"guide[ _-]?(inner|outer|big|small)",
         r"(inner|outer) half", r"parking", r"\bpad\b", r"t-?slot", r"hand-?e\b", r"hand-?over", r"hand over",
         r"take-?out", r"jig_moves", r"carrier", r"camera", r"\brack\b", r"two benches", r"\bx2\b",
         r"jig v[2-9]", r"guide arm", r"frame_jig", r"topflat", r"vision_lab", r"walkthrough", r"mma4002",
         r"outdoor-furniture", r"robot-cell", r"robot_sim", r"assembly-experiment", r"studydev", r"\.rdk\b",
         r"ld-?250", r"second bench", r"reload"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def build(root, force):
    if root.exists():
        if not force:
            raise SystemExit(f"{root} exists (use --force to rebuild it from scratch)")
        for p in root.rglob("*"):                                    # the judge is read-only
            try:
                os.chmod(p, stat.S_IWUSR | stat.S_IRUSR | (stat.S_IXUSR if p.is_dir() else 0))
            except OSError:
                pass
        shutil.rmtree(root)
    for d in ("judge", "design/meshes/jig", "design/meshes/bench", "design/cad/step", "toolbox", "log", "scratch"):
        (root / d).mkdir(parents=True, exist_ok=True)

    # judge (frozen)
    for f in JUDGE_FILES:
        shutil.copy2(HERE / "judge" / f, root / "judge" / f)
    sums = "".join(f"{sha(root / 'judge' / f)}  {f}\n" for f in JUDGE_FILES)
    write(root / "judge" / "SHA256SUMS", sums)
    Path(str(root) + ".judge.sha256").write_text(sums)

    # design: program, cell builder, meshes, CAD
    prog = json.loads((SIM / "ref" / "v3_program.json").read_text())
    prog.pop("tmflow", None)
    prog["source"] = "the v3 program (joints made with the 'station' link lengths, judge/tm5_kin.py)"
    prog["program"] = "AssembleBench"
    write(root / "design" / "program.json", json.dumps(prog, indent=1))
    shutil.copy2(SRC / "build_cell.py", root / "design" / "build_cell.py")
    for f in JIG_STL:
        shutil.copy2(CELL / "jig_parts" / f"{f}.stl", root / "design" / "meshes" / "jig" / f"{f}.stl")
    for f in BENCH_STL:
        shutil.copy2(CELL / "benchV1_parts" / f"{f}.stl", root / "design" / "meshes" / "bench" / f"{f}.stl")
    asm = json.loads((CELL / "benchV1_parts" / "assembly.json").read_text())
    write(root / "design" / "meshes" / "bench" / "assembly.json", json.dumps(asm, indent=1))
    for f in ("jig_parts.py", "jig_guide.py", "bench_parts.py"):
        shutil.copy2(SRC / "cad" / f, root / "design" / "cad" / f)
    for dst, src in STEPS.items():
        shutil.copy2(HERE.parent / src, root / "design" / "cad" / "step" / dst)

    # brief, helpers, logs
    shutil.copy2(SRC / "AGENT.md", root / "AGENT.md")
    write(root / "CLAUDE.md", "# Read AGENT.md first\n\nThis folder is an experiment sandbox. Your brief, the rules and "
                              "the loop are in `AGENT.md`. Follow it exactly.\n")
    write(root / "py", '#!/bin/sh\n# the venv python (numpy, trimesh, python-fcl, build123d, matplotlib, scipy)\n'
                       'exec "${ASSEMBLY_PY:?set ASSEMBLY_PY}" "$@"\n')
    os.chmod(root / "py", 0o755)
    write(root / "toolbox" / "README.md", "# toolbox\n\nYour own tools (program generator, planner, layout search, "
                                          "extra checks, ...). Log every change in `log/tool_changes.md`.\n")
    write(root / "log" / "lessons.md", "# Lessons (problems and fixes)\n\nOne block per problem, written at once "
                                       "(AGENT.md \"Self-learning rule\"). Read in full at the start of every "
                                       "iteration.\n")
    write(root / "log" / "tool_changes.md", "# Tool changes\n\nOne block per change to a tool in `toolbox/` "
                                            "(`## T<NN> (iter NN) <title>`: what, why, which iteration needed it, "
                                            "how it was tested), and any PROPOSED JUDGE FIX.\n")
    r, home = str(root), str(Path.home())
    settings = {"permissions": {                                     # outside the sandbox: run_part_b.sh --settings
        "deny": ["WebFetch", "WebSearch", "Bash(git:*)", "Bash(curl:*)", "Bash(wget:*)", "Bash(ssh:*)",
                 "Bash(sudo:*)", "Bash(chmod:*)", f"Edit(/{r}/judge/**)", f"Edit(/{r}/best/**)",
                 f"Edit(/{r}/log/iterations.csv)", f"Edit(/{r}/log/state.json)", f"Edit(/{r}/log/run.jsonl)",
                 f"Edit(/{r}/log/iter_*/score.json)", f"Edit(/{r}/log/iter_*/pending.json)",
                 f"Read(/{home}/dev/studyDev/**)", f"Read(/{home}/.claude/projects/**)"],
        "allow": ["Read", "Edit", "Write", "Glob", "Grep", "TodoWrite", "Bash(./py:*)", "Bash(ls:*)", "Bash(mkdir:*)",
                  "Bash(cp:*)", "Bash(mv:*)", "Bash(diff:*)", "Bash(wc:*)", "Bash(sha256sum:*)", "Bash(du:*)"]}}
    Path(r + ".settings.json").write_text(json.dumps(settings, indent=1))

    # build the cell and compare with the Part A v3 cell
    env = dict(os.environ, ASSEMBLY_PY=sys.executable)
    r = subprocess.run([str(root / "py"), "design/build_cell.py"], cwd=root, env=env, capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-500:])
    if r.returncode:
        raise SystemExit("build_cell.py failed")
    compare_cells(root / "design" / "cell.glb", SIM / "cell_v3.glb")

    # read-only judge
    for f in (root / "judge").iterdir():
        os.chmod(f, 0o444)
    os.chmod(root / "judge", 0o555)


def compare_cells(a, b):
    sys.path.insert(0, str(HERE / "judge"))
    import collision
    ca, cb = collision.load_cell(str(a)), collision.load_cell(str(b))
    assert set(ca) == set(cb), f"objects differ: {set(ca) ^ set(cb)}"
    import numpy as np
    worst = max(float(np.abs(ca[n][1].vertices - cb[n][1].vertices).max()) for n in ca)
    kinds = all(ca[n][0] == cb[n][0] for n in ca)
    print(f"cell check: {len(ca)} objects, same names, kinds {'same' if kinds else 'DIFFER'}, "
          f"max vertex difference to the Part A v3 cell {worst:.2e} mm")
    if worst > 1e-3 or not kinds:
        raise SystemExit("the sandbox cell is not the v3 cell")


def leak_check(root, skip_log=False):
    pat = re.compile("|".join(f"(?:{p})" for p in LEAKS), re.I)
    found = []
    for p in sorted(root.rglob("*")):
        if p.is_dir() or "__pycache__" in p.parts or (skip_log and p.relative_to(root).parts[0] == "log"):
            continue
        data = p.read_bytes()
        if p.suffix.lower() == ".glb":                                # only the JSON chunk (names), not the buffers
            import struct
            n = struct.unpack("<I", data[12:16])[0]
            text = data[20:20 + n].decode("utf-8", "replace")
        elif p.suffix.lower() in (".stl", ".step", ".png"):
            text = " ".join(m.decode("latin-1") for m in re.findall(rb"[ -~]{4,}", data[:2_000_000]))
            if p.suffix.lower() == ".stl" and data[:5] != b"solid":
                text = text[:200]                                     # binary STL: only the header is text
        else:
            text = data.decode("utf-8", "replace")
        rel = p.relative_to(root)
        for i, line in enumerate(text.splitlines() or [text], 1):
            for m in pat.finditer(line):
                found.append(f"{rel}:{i}: '{m.group(0)}' in: {line.strip()[:140]}")
    for d in (".git",):
        if (root / d).exists():
            found.append(f"{d} exists")
    print(f"leak check of {root}: {'PASS (nothing found)' if not found else f'FAIL, {len(found)} hits'}")
    for f in found[:60]:
        print("   ", f)
    return not found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(Path.home() / "dev" / "assembly-blind"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--leak-check-only", action="store_true")
    ap.add_argument("--skip-log", action="store_true", help="leave log/ out of the leak check (a restarted run)")
    a = ap.parse_args()
    root = Path(a.root).expanduser()
    if not a.leak_check_only:
        build(root, a.force)
    raise SystemExit(0 if leak_check(root, a.skip_log) else 1)


if __name__ == "__main__":
    main()
