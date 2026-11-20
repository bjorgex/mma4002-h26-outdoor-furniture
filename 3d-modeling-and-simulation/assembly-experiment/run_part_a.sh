#!/usr/bin/env bash
# Part A on bj-hserver: score every version, then commit + push the results.
#   cd ~/dev/studyDev/mma4002-h26-outdoor-furniture/3d-modeling-and-simulation/assembly-experiment
#   nohup nice -n 10 bash run_part_a.sh > results/part_a.log 2>&1 &
set -u
cd "$(dirname "$0")"
PY=${PY:-$HOME/dev/studyDev/MSc-MechAuto-NTNU/.venv/bin/python}
mkdir -p results
rm -f results/versions.csv                      # one clean table per Part A run (git keeps the old one)
"$PY" score_run.py --all --jobs "${JOBS:-10}"
status=$?
git add results/versions.csv results/runs results/part_a.log 2>/dev/null
git commit -m "assembly-experiment Part A: every version scored on bj-hserver (exit $status)" || true
git pull --rebase && git push
echo "DONE exit $status"
