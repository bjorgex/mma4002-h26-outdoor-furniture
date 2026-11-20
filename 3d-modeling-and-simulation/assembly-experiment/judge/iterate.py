"""The iteration loop's bookkeeping (part of the frozen judge): score a candidate, then keep or reject it.

    ./py judge/iterate.py status                         best so far, budget left, the no-improvement streak
    ./py judge/iterate.py score NN --type program|layout|jig_cad|tool|mixed
        rebuilds the cell (design/build_cell.py), scores design/program.json in design/cell.glb at 2 mm (the only
        score that counts), writes log/iter_NN/: score.json, shots/*.png, topview.png, diff.patch (against best/),
        copies of the program, the cell layout and the scripts; prints the summary and the verdict against the best.
        Needs log/iter_NN/notes.md with a "## Hypothesis" section first. May be run again for the same NN (a fix)
        until it is decided.
    ./py judge/iterate.py decide NN keep|reject --reason "..."
        keep: only if the verdict was "better" and notes.md has a "## Screenshots" section (what you saw in every
        shot) and a "## Result" section. design/ is copied to best/.
        reject: design/ is restored from best/ (your toolbox/ stays as it is).
        Appends the row to log/iterations.csv and a line to log/run.jsonl.
    ./py judge/iterate.py baseline                       (the runner, once) iteration 0 = the start design, kept

Keep rule (AGENT.md): rank = (fails a hard rule?, rule_violations, cycle_s, joint_travel_deg), lower is better;
a candidate is "better" if its rank is lower than the best's. So: first legal, then fewer violations, then faster,
ties broken by less joint travel.
Budget: iterations 1..MAX_ITER; the run stops after MAX_ITER or after STREAK decided iterations in a row without a
keep.
"""
import argparse
import csv
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN, BEST, LOG = ROOT / "design", ROOT / "best", ROOT / "log"
STATE = LOG / "state.json"
MAX_ITER, STREAK = 30, 5
TYPES = ("program", "layout", "jig_cad", "tool", "mixed")
sys.path.insert(0, str(HERE))
import score as J                                           # noqa: E402

ID_COLUMNS = ["label", "iteration", "parent", "timestamp", "wall_s", "change_type", "kept", "reject_reason"]
ITER_COLUMNS = ID_COLUMNS + [c for c in J.COLUMNS if c not in ID_COLUMNS] + J.RULE_COLUMNS


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def log_event(event, msg, **kw):
    LOG.mkdir(exist_ok=True)
    with (LOG / "run.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": now(), "src": "judge", "event": event, "msg": msg, **kw}) + "\n")


def state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"best_iter": None, "best_rank": None, "decided": [], "streak": 0, "last_decide": time.time(),
            "started": time.time()}


def save_state(s):
    STATE.write_text(json.dumps(s, indent=1))


def rank(row):
    v = int(row["rule_violations"])
    return [int(v > 0), v, float(row["cycle_s"]), float(row["joint_travel_deg"])]


def verify_judge():
    """The judge files against judge/SHA256SUMS (also checked from outside the sandbox by the runner)."""
    bad = []
    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        h, name = line.split(None, 1)
        p = HERE / name.strip()
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
            bad.append(name.strip())
    if bad:
        log_event("judge_tampered", f"judge files changed: {bad}", files=bad)
        raise SystemExit(f"JUDGE FILES CHANGED: {bad}. The judge is frozen - restore them; propose a fix in "
                         f"log/tool_changes.md instead.")


def section(text, title):
    """Text of a '## title' section (up to the next '## ')."""
    lines, on = [], False
    for ln in text.splitlines():
        if ln.startswith("## "):
            on = ln[3:].strip().lower().startswith(title.lower())
            continue
        if on:
            lines.append(ln)
    return "\n".join(lines).strip()


def snapshot(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "scratch"))


def tool_changes(nn):
    p = LOG / "tool_changes.md"
    if not p.exists():
        return 0
    return sum(1 for ln in p.read_text(encoding="utf-8").splitlines()
               if ln.startswith("## ") and f"(iter {nn:02d})" in ln)


def build_cell():
    r = subprocess.run([sys.executable, str(DESIGN / "build_cell.py")], capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit(f"design/build_cell.py failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def do_score(nn, ctype, label=None, need_notes=True):
    verify_judge()
    s = state()
    if nn in s["decided"]:
        raise SystemExit(f"iteration {nn} is already decided; the next one is {max(s['decided']) + 1}")
    if nn != 0 and (nn > MAX_ITER or s["streak"] >= STREAK):
        raise SystemExit("budget used up (AGENT.md): no more iterations")
    if nn != 0 and nn != (max(s["decided"]) + 1 if s["decided"] else 1):
        raise SystemExit(f"the next iteration is {max(s['decided']) + 1 if s['decided'] else 1}, not {nn}")
    d = LOG / f"iter_{nn:02d}"
    d.mkdir(parents=True, exist_ok=True)
    notes = d / "notes.md"
    if need_notes:
        if not notes.exists() or len(section(notes.read_text(encoding="utf-8"), "Hypothesis").split()) < 10:
            raise SystemExit(f"write {notes} with a '## Hypothesis' section first (what you change, why, the expected "
                             f"delta in s), then score")
    if ctype not in TYPES:
        raise SystemExit(f"--type must be one of {TYPES}")
    t0 = time.time()
    log_event("score_start", f"iter {nn:02d}: scoring ({ctype})", iteration=nn)
    built = build_cell()
    for f in ("program.json", "cell_layout.json"):
        shutil.copy2(DESIGN / f, d / f)
    scripts = d / "scripts"
    if scripts.exists():
        shutil.rmtree(scripts)
    for p in list(DESIGN.glob("*.py")) + list((DESIGN / "cad").glob("*.py")):
        (scripts / p.parent.relative_to(DESIGN)).mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, scripts / p.relative_to(DESIGN))
    if BEST.exists():
        r = subprocess.run(["diff", "-ruN", "-x", "__pycache__", "-x", "*.glb", "best", "design"], capture_output=True,
                           text=True, cwd=ROOT)
        (d / "diff.patch").write_text(r.stdout, encoding="utf-8")
    row, details = J.score(DESIGN / "program.json", DESIGN / "cell.glb", "station", label=label or f"iter_{nn:02d}",
                           out_dir=d, layout_path=DESIGN / "cell_layout.json")
    best_row = None
    if s["best_iter"] is not None:
        best_row = json.loads((LOG / f"iter_{s['best_iter']:02d}" / "score.json").read_text())["row"]
    better = best_row is None or rank(row) < rank(best_row)
    pend = {"iteration": nn, "type": ctype, "row": row, "better": better, "parent": s["best_iter"],
            "scored_at": now(), "score_wall_s": round(time.time() - t0, 1)}
    (d / "pending.json").write_text(json.dumps(pend, indent=1, default=str))
    print(built)
    print(J.summary(row, details))
    if best_row is not None:
        print(f"best so far: iter {s['best_iter']:02d}: violations {best_row['rule_violations']}, cycle "
              f"{best_row['cycle_s']} s, joints {best_row['joint_travel_deg']} deg")
    verdict = "BETTER than the best (may be kept)" if better else "NOT better than the best (reject it)"
    print(f"VERDICT iter {nn:02d}: {verdict}")
    if nn:
        print(f"Next: look at every image in log/iter_{nn:02d}/shots/ and topview.png, write '## Screenshots' (what "
              f"you see in each) and '## Result' in notes.md, then: ./py judge/iterate.py decide {nn} keep|reject "
              f"--reason ...")
    log_event("scored", f"iter {nn:02d} ({ctype}): violations {row['rule_violations']}, cycle {row['cycle_s']} s, "
              f"joints {row['joint_travel_deg']} deg -> {'better' if better else 'not better'}", iteration=nn,
              rule_violations=row["rule_violations"], cycle_s=row["cycle_s"], better=better)
    return row, better


def do_decide(nn, action, reason, force=False):
    verify_judge()
    s = state()
    d = LOG / f"iter_{nn:02d}"
    pf = d / "pending.json"
    if nn in s["decided"]:
        raise SystemExit(f"iteration {nn} is already decided")
    if not pf.exists():
        if not force:
            raise SystemExit(f"score iteration {nn} first")
        pend = None
    else:
        pend = json.loads(pf.read_text())
    if action == "keep":
        if pend is None or not pend["better"]:
            raise SystemExit("keep is only allowed for a candidate the judge found better than the best")
        text = (d / "notes.md").read_text(encoding="utf-8") if (d / "notes.md").exists() else ""
        if len(section(text, "Screenshots").split()) < 40:
            raise SystemExit("hard rule: write what you see in the screenshots under '## Screenshots' in notes.md "
                             "(every shot, at least a line each) before keeping")
        if not section(text, "Result"):
            raise SystemExit("write the '## Result' section in notes.md (expected vs got, why kept) first")
        snapshot(DESIGN, BEST)
        s["best_iter"], s["best_rank"], s["streak"] = nn, rank(pend["row"]), 0
    else:
        if BEST.exists():
            snapshot(BEST, DESIGN)
        if nn != 0:
            s["streak"] += 1
    if pend is not None:
        row = dict(pend["row"])
    else:
        row = {c: "" for c in ITER_COLUMNS}
        row["label"] = f"iter_{nn:02d}"
    wall = round(time.time() - s["last_decide"], 1)
    row.update(iteration=nn, parent="" if pend is None or pend["parent"] is None else pend["parent"], timestamp=now(),
               wall_s=wall, wall_time_s=wall, change_type=pend["type"] if pend else "", kept=action == "keep",
               reject_reason="" if action == "keep" else reason, tool_changes=tool_changes(nn))
    out = LOG / "iterations.csv"
    new = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ITER_COLUMNS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
    s["decided"].append(nn)
    s["last_decide"] = time.time()
    save_state(s)
    if pf.exists():
        pf.rename(d / "decided.json")
    left = MAX_ITER - max([x for x in s["decided"]] or [0])
    msg = (f"iter {nn:02d} {'KEPT' if action == 'keep' else 'rejected'}: violations {row.get('rule_violations')}, "
           f"cycle {row.get('cycle_s')} s" + (f" ({reason})" if reason else "") +
           f"; best = iter {s['best_iter']:02d}; budget left {left}, no-improvement streak {s['streak']}/{STREAK}")
    log_event("decided", msg, iteration=nn, kept=action == "keep", streak=s["streak"])
    print(msg)
    if s["streak"] >= STREAK or left <= 0:
        print("BUDGET USED UP: the run ends here (write log/summary.md if you have not).")


def do_status():
    s = state()
    best = None
    if s["best_iter"] is not None:
        best = json.loads((LOG / f"iter_{s['best_iter']:02d}" / "score.json").read_text())["row"]
    nxt = max(s["decided"]) + 1 if s["decided"] else 1
    print(f"decided: {s['decided']}; next iteration: {nxt}; budget: up to {MAX_ITER}, stop after {STREAK} in a row "
          f"without a keep (streak now {s['streak']})")
    if best:
        print(f"best: iter {s['best_iter']:02d}: violations {best['rule_violations']} "
              + ", ".join(f"{c} {best[c]}" for c in J.RULE_COLUMNS[1:10])
              + f"; cycle {best['cycle_s']} s, joints {best['joint_travel_deg']} deg, phases {best['phases_s']}")
    lessons = LOG / "lessons.md"
    n = sum(ln.startswith("## L") for ln in lessons.read_text(encoding="utf-8").splitlines()) if lessons.exists() else 0
    print(f"lessons logged: {n} (log/lessons.md - read them all before you start an iteration)")
    pend = sorted(LOG.glob("iter_*/pending.json"))
    for p in pend:
        print(f"PENDING (scored, not decided): {p.parent.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("baseline")
    a1 = sub.add_parser("score")
    a1.add_argument("nn", type=int)
    a1.add_argument("--type", required=True, choices=TYPES)
    a2 = sub.add_parser("decide")
    a2.add_argument("nn", type=int)
    a2.add_argument("action", choices=["keep", "reject"])
    a2.add_argument("--reason", default="")
    a2.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.cmd == "status":
        do_status()
    elif a.cmd == "baseline":
        d = LOG / "iter_00"
        d.mkdir(parents=True, exist_ok=True)
        (d / "notes.md").write_text("# iter 00: baseline\n\n## Hypothesis\nThe v3 design as given, scored by the "
                                    "frozen judge: the start point every change is measured against.\n",
                                    encoding="utf-8")
        row, _ = do_score(0, "program", label="iter_00", need_notes=False)
        snapshot(DESIGN, BEST)
        s = state()
        s["best_iter"], s["best_rank"], s["decided"], s["last_decide"] = 0, rank(row), [0], time.time()
        save_state(s)
        pf = d / "pending.json"
        pend = json.loads(pf.read_text())
        r = dict(pend["row"])
        r.update(iteration=0, parent="", timestamp=now(), wall_s=0, wall_time_s=0, change_type="baseline", kept=True,
                 reject_reason="", tool_changes=0)
        with (LOG / "iterations.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ITER_COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerow(r)
        pf.rename(d / "decided.json")
        log_event("baseline", f"iter 00 baseline (v3): violations {row['rule_violations']}, cycle {row['cycle_s']} s")
    elif a.cmd == "score":
        do_score(a.nn, a.type)
    else:
        do_decide(a.nn, a.action, a.reason, a.force)


if __name__ == "__main__":
    main()
