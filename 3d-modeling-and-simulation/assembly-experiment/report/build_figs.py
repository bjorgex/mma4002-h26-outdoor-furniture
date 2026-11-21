"""Figures + LaTeX tables for the Part B / B2 reports, read only from the run logs (re-runnable, no hand-typed numbers).

    python report/build_figs.py part_b      -> report/part_b/ (fig_*.png, iter_table.tex, numbers.tex)
    python report/build_figs.py part_b2

Reads results/<run>/log/: iterations.csv, run.jsonl (session cost + minutes), iter_NN/notes.md (title, Reason),
and report/reasons_<run>.json if it exists (one-line reasons written after the run; Part B had no Reason section,
its reasons are condensed from each iteration's Hypothesis).
"""
import csv
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

HERE = Path(__file__).resolve().parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "part_b"
LOG = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "results" / RUN / "log"   # argv[2]: a live copy
OUT = HERE / RUN
OUT.mkdir(exist_ok=True)
TYPE_COL = {"program": "#E07B39", "layout": "#2F6FB5", "jig_cad": "#3F7D58", "tool": "#8E5BB5", "mixed": "#B5A42F",
            "baseline": "#888888", "": "#888888"}
PHASE_COL = {"guide": "#B5A42F", "planks": "#E07B39", "frame 1 + planks": "#2F6FB5", "home": "#888888"}

rows = list(csv.DictReader((LOG / "iterations.csv").open(encoding="utf-8")))
for r in rows:
    r["it"] = int(r["iteration"])
    r["cyc"] = float(r["cycle_s"]) if r["cycle_s"] else None
    r["viol"] = int(float(r["rule_violations"])) if r["rule_violations"] else None
    r["keep"] = r["kept"] == "True"


def notes(it):
    p = LOG / f"iter_{it:02d}" / "notes.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def section(text, title):
    m = re.search(r"^## " + title + r"[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def title(it):
    m = re.match(r"#\s*iter\s*\d+\s*:\s*(.*)", notes(it).splitlines()[0] if notes(it) else "")
    return m.group(1).strip() if m else ""


# session cost / minutes per iteration from run.jsonl
cost, mins = {}, {}
for ln in (LOG / "run.jsonl").open(encoding="utf-8"):
    e = json.loads(ln)
    if e.get("event") == "session_end" and "iter" in e:
        cost[e["iter"]] = cost.get(e["iter"], 0) + (e.get("cost_usd") or 0)
        mins[e["iter"]] = mins.get(e["iter"], 0) + (e.get("duration_ms") or 0) / 60000
    if e.get("event") in ("run_start", "run_end"):
        pass
events = [json.loads(ln) for ln in (LOG / "run.jsonl").open(encoding="utf-8")]
reasons_file = HERE / f"reasons_{RUN}.json"
reasons = json.loads(reasons_file.read_text(encoding="utf-8")) if reasons_file.exists() else {}

# ---------------------------------------------------------------- progress
base = rows[0]
best_rank, best_cyc, steps = None, [], []
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
cur = None
for r in rows:
    if r["keep"]:
        cur = r
    steps.append(cur["cyc"])
    if r["cyc"] is not None:
        col = TYPE_COL.get(r["change_type"], "#888")
        ax.scatter(r["it"], r["cyc"], s=36, zorder=3, facecolor=col if r["keep"] else "white", edgecolor=col, lw=1.5)
        ax2.bar(r["it"], r["viol"], color=col if r["keep"] else "white", edgecolor=col, lw=1.2)
ax.step([r["it"] for r in rows], steps, where="post", color="#333", lw=1.2, label="best so far")
ax.set_ylabel("cycle time [s]")
ax.grid(alpha=.3)
for t, c in TYPE_COL.items():
    if t and t != "baseline" and any(r["change_type"] == t for r in rows):
        ax.scatter([], [], color=c, label=t)
ax.scatter([], [], facecolor="white", edgecolor="#333", label="rejected (hollow)")
ax.legend(fontsize=7, ncol=3, loc="upper right")
ax2.set_ylabel("rule\nviolations")
ax2.set_xlabel("iteration")
ax2.grid(alpha=.3)
fig.tight_layout()
fig.savefig(OUT / "fig_progress.png", dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- waterfall of kept changes
kept = [r for r in rows if r["keep"]]
fig, ax = plt.subplots(figsize=(8, 3.6))
level = kept[0]["cyc"]
ax.bar(0, level, color="#888", width=.7)
xs, labels = [0], ["start"]
for i, r in enumerate(kept[1:], 1):
    d = r["cyc"] - level
    ax.bar(i, d, bottom=level, color=TYPE_COL.get(r["change_type"], "#888"), width=.7)
    if abs(d) >= 1.5:
        ax.text(i, max(level, r["cyc"]) + 1.5, f"{d:+.1f}", ha="center", fontsize=6, rotation=90)
    level = r["cyc"]
    xs.append(i)
    labels.append(str(r["it"]))
ax.bar(len(kept), level, color="#333", width=.7)
xs.append(len(kept))
labels.append("best")
ax.set_xticks(xs)
ax.set_xticklabels(labels, fontsize=7)
ax.set_xlabel("kept iteration")
ax.set_ylabel("cycle time [s]")
lo = min(r["cyc"] for r in kept)
ax.set_ylim(lo * 0.85 if RUN == "part_b2" else 0, max(r["cyc"] for r in kept) * 1.08)
ax.grid(alpha=.3, axis="y")
fig.tight_layout()
fig.savefig(OUT / "fig_waterfall.png", dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- phases start vs best
best = min((r for r in rows if r["keep"]), key=lambda r: (r["viol"] > 0, r["viol"], r["cyc"]))
fig, ax = plt.subplots(figsize=(6, 2.6))
for y, (lab, r) in enumerate([("start (iter 00)", base), (f"best (iter {best['it']:02d})", best)]):
    ph, left = json.loads(r["phases_s"]), 0
    for k, v in ph.items():
        ax.barh(y, v, left=left, color=PHASE_COL.get(k, "#aaa"), edgecolor="white", label=k if y == 0 or k not in json.loads(base["phases_s"]) else None)
        if v > 6:
            ax.text(left + v / 2, y, f"{v:.0f}", ha="center", va="center", fontsize=7, color="white")
        left += v
    ax.text(left + 2, y, f"{left:.1f} s", va="center", fontsize=8)
ax.set_yticks([0, 1])
ax.set_yticklabels(["start (iter 00)", f"best (iter {best['it']:02d})"], fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("time per phase [s]")
ax.set_xlim(0, float(base["cycle_s"]) * 1.15)
h, l = ax.get_legend_handles_labels()
ax.legend(h, l, fontsize=7, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
fig.tight_layout()
fig.savefig(OUT / "fig_phases.png", dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- change types
types = [t for t in TYPE_COL if t and t != "baseline" and any(r["change_type"] == t for r in rows[1:])]
tries = [sum(r["change_type"] == t for r in rows[1:]) for t in types]
keeps = [sum(r["change_type"] == t and r["keep"] for r in rows[1:]) for t in types]
gain = []
prev = base
for t in types:
    gain.append(0.0)
lvl = base["cyc"]
gmap = {t: 0.0 for t in types}
for r in rows[1:]:
    if r["keep"]:
        gmap[r["change_type"]] += lvl - r["cyc"]
        lvl = r["cyc"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7, 2.4))
x = range(len(types))
a1.bar([i - .2 for i in x], tries, .4, color="#ccc", label="tried")
a1.bar([i + .2 for i in x], keeps, .4, color=[TYPE_COL[t] for t in types], label="kept")
a1.set_xticks(list(x))
a1.set_xticklabels(types, fontsize=7)
a1.set_ylabel("iterations")
a1.legend(fontsize=7)
a2.bar(list(x), [gmap[t] for t in types], color=[TYPE_COL[t] for t in types])
a2.set_xticks(list(x))
a2.set_xticklabels(types, fontsize=7)
a2.set_ylabel("cycle time saved [s]")
for a in (a1, a2):
    a.grid(alpha=.3, axis="y")
fig.tight_layout()
fig.savefig(OUT / "fig_types.png", dpi=170)
plt.close(fig)


# ---------------------------------------------------------------- LaTeX
def tex(s):
    s = s.replace("\\", "/")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"$\sim$"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    for a, b in [("->", r"$\to$"), ("→", r"$\to$"), ("≥", r"$\ge$"), (">=", r"$\ge$"), ("≤", r"$\le$"),
                 ("<=", r"$\le$"), ("Δ", r"$\Delta$"), ("°", r"$^\circ$"), ("×", r"$\times$"), ("±", r"$\pm$"),
                 ("+-", r"$\pm$"), ("μ", r"$\mu$"), ("–", "--"), ("—", "---"), ("’", "'"), ("“", "``"), ("”", "''"),
                 ("<", r"$<$"), (">", r"$>$")]:
        s = s.replace(a, b)
    return "".join(c if ord(c) < 256 else "?" for c in s)


def first_sentences(s, n=230):
    if len(s) <= n:
        return s
    cut = s[:n]
    k = cut.rfind(". ")
    return (cut[:k + 1] if k > 80 else cut.rstrip() + " ...")


lines = []
lvl = base["cyc"]
for r in rows[1:]:
    d = r["cyc"] - lvl if r["cyc"] is not None else None
    why = reasons.get(str(r["it"])) or first_sentences(r.get("reason") or section(notes(r["it"]), "Reason"), 330)
    res = ("kept" if r["keep"] else "rejected")
    rej = ""
    if not r["keep"] and r.get("reject_reason") and not reasons.get(str(r["it"])):
        rej = "\\newline \\textit{Rejected: " + tex(first_sentences(r["reject_reason"], 200)) + "}"
    lines.append(f"{r['it']} & {tex(r['change_type'])} & \\textbf{{{tex(title(r['it']))}}}\\newline {tex(why)}{rej} & "
                 f"{r['cyc'] if r['cyc'] is not None else '--'} & {f'{d:+.1f}' if d is not None else '--'} & "
                 f"{r['viol'] if r['viol'] is not None else '--'} & {tex(res)} \\\\")
    if r["keep"]:
        lvl = r["cyc"]
HEAD = (r"{\small" "\n" r"\rowcolors{2}{rowlt}{white}" "\n"
        r"\begin{longtable}{>{\raggedleft}p{5mm} p{12mm} >{\raggedright}p{85mm} r r r p{14mm}}" "\n"
        r"\toprule" "\n"
        r"\rowcolor{hdrblue}\hdr{It} & \hdr{Type} & \hdr{Change and reason} & \hdr{Cycle} & \hdr{$\Delta$s} & "
        r"\hdr{Viol.} & \hdr{Result}\\" "\n" r"\midrule" "\n" r"\endhead" "\n")
(OUT / "iter_table.tex").write_text(HEAD + "\n".join(lines) + "\n" + r"\bottomrule" + "\n" + r"\end{longtable}"
                                    + "\n}\n", encoding="utf-8")

t0 = next((e["t"] for e in events if e.get("event") == "run_start"), "")
t1 = next((e["t"] for e in reversed(events) if e.get("event") in ("run_end", "decided")), "")
les = (LOG / "lessons.md").read_text(encoding="utf-8")
if RUN == "part_b2" and "# Run B2" in les:
    les = les.split("# Run B2", 1)[1]                     # only this run's lessons
n_les = len(re.findall(r"^## L\d+", les, re.M))
n_again = len(re.findall(r"^## L\d+[^\n]*\bL\d+ again", les, re.M))
lasts = [r for r in rows if r["keep"]]
num = {
    "startcycle": base["cycle_s"], "startviol": base["rule_violations"], "startjoints": base["joint_travel_deg"],
    "startpath": base["tcp_path_m"], "startmoves": base["n_moves"],
    "bestcycle": best["cycle_s"], "bestviol": best["rule_violations"], "bestjoints": best["joint_travel_deg"],
    "bestpath": best["tcp_path_m"], "bestmoves": best["n_moves"], "bestit": f"{best['it']:02d}",
    "niter": len(rows) - 1, "nkept": sum(r["keep"] for r in rows[1:]), "nrej": sum(not r["keep"] for r in rows[1:]),
    "cost": f"{sum(cost.values()):.0f}", "agentmin": f"{sum(mins.values()):.0f}",
    "tstart": t0.replace("T", " "), "tend": t1.replace("T", " "),
    "nlessons": n_les, "nagain": n_again,
    "firstlegal": next((r["it"] for r in rows if r["keep"] and r["viol"] == 0), "--"),
    "gainpct": f"{100 * (1 - float(best['cycle_s']) / float(base['cycle_s'])):.0f}",
}
PFX = {"part_b": "pb", "part_b2": "pbtwo"}[RUN]                # LaTeX macro names: letters only
(OUT / "numbers.tex").write_text("".join(f"\\newcommand{{\\{PFX}{k}}}{{{tex(str(v))}}}\n"
                                         for k, v in num.items()), encoding="utf-8")
print(json.dumps(num, indent=1))
print("cost per iter:", {k: round(v, 2) for k, v in cost.items()})

# ---------------------------------------------------------------- B2 only: the whole path v3 -> B -> B2
if RUN == "part_b2":
    rb = list(csv.DictReader((HERE.parent / "results" / "part_b" / "log" / "iterations.csv").open(encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for k, (rr, col, lab, off) in enumerate([(rb, "#E07B39", "run B (judge B)", 0),
                                              (rows, "#2F6FB5", "run B2 (judge B2: + Line rotation time)",
                                               len(rb) - 1)]):
        cur, xs, ys = None, [], []
        for r in rr:
            c = float(r["cycle_s"]) if r["cycle_s"] else None
            if r["kept"] == "True":
                cur = c
            xs.append(int(r["iteration"]) + off)
            ys.append(cur)
            if c is not None:
                ax.scatter(int(r["iteration"]) + off, c, s=14, color=col if r["kept"] == "True" else "white",
                           edgecolor=col, zorder=3)
        ax.step(xs, ys, where="post", color=col, lw=1.4, label=lab)
    ax.axvline(len(rb) - 1, color="#999", ls=":", lw=1)
    ax.set_xlabel("iteration (B2 continues after B's iter 30)")
    ax.set_ylabel("cycle time [s]")
    ax.legend(fontsize=7)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig_combined.png", dpi=170)
    plt.close(fig)
    # zoom on B2 only, the y range of B2
    print("combined figure written")
