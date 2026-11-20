"""Judge re-check: score v3 and v10 with the Part B judge (judge/score.py) and compare every Part A metric column
with results/versions.csv. The extended judge must not change the old numbers.

    python rescore_check.py [--versions v3 v10]       (server; ~1-2 min per version)
Out: results/judge_check.csv (one row per version, Part A columns + the rule columns), and a printout of every
column that differs (phases_s is compared by its total: the judge names phases by grips, not by move names).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "judge"))
import score as J                                           # noqa: E402  (the judge, not robot_sim's tools)
import score_run as A                                       # noqa: E402  (Part A: VERSIONS, v10's shift)

GEO = {"robodk": "station", "techman": "techman"}
SAME = ["cycle_s", "cycle_ramps_s", "tcp_path_m", "line_path_m", "joint_travel_deg", "j1_travel_deg", "j2_travel_deg",
        "j3_travel_deg", "j4_travel_deg", "j5_travel_deg", "j6_travel_deg", "n_moves", "n_ptp", "n_line", "wrist_flips",
        "collisions_fixtures", "collisions_parts", "min_clearance_mm", "ptp_near_parts", "low_traverses", "ik_failures",
        "line_failures", "limit_hits", "max_mu1_vfix", "min_mu3_vfix", "near_singular", "grips", "regrasps",
        "part_flips", "jig_parts", "jig_volume_l"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--versions", nargs="+", default=["v3", "v10"])
    a = ap.parse_args()
    old = {r["label"]: r for r in csv.DictReader((HERE / "results" / "versions.csv").open(encoding="utf-8"))}
    rows, ok = [], True
    for v in a.versions:
        prog, cell, geo, note = A.VERSIONS[v]
        prog_p, cell_p = A.CELL / prog, A.CELL / cell
        import collision
        shift = A.expand_shift(A.v10_shift(json.loads(prog_p.read_text())) if v == "v10" else {},
                               dict(collision.load_cell(str(cell_p))))
        row, det = J.score(prog_p, cell_p, GEO[geo], label=v, version=v, note=note, shift=shift,
                           out_dir=HERE / "results" / "judge_check" / v)
        rows.append(row)
        diffs = []
        for c in SAME:
            x, y = str(old[v][c]), str(row[c])
            try:
                same = abs(float(x) - float(y)) < 1e-9
            except ValueError:
                same = x == y
            if not same:
                diffs.append(f"{c}: Part A {x} -> judge {y}")
        pa = sum(json.loads(old[v]["phases_s"]).values())
        pj = sum(json.loads(row["phases_s"]).values())
        if abs(pa - pj) > 0.15:
            diffs.append(f"phases_s total: Part A {pa:.1f} -> judge {pj:.1f}")
        ok &= not diffs
        print(f"{v}: {'all Part A columns unchanged' if not diffs else 'DIFFERS: ' + '; '.join(diffs)}")
        print(f"    rules: " + ", ".join(f"{c} {row[c]}" for c in J.RULE_COLUMNS))
    out = HERE / "results" / "judge_check.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=J.COLUMNS + J.RULE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{'OK' if ok else 'NOT OK'}: {out}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
