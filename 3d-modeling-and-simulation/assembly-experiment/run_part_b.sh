#!/usr/bin/env bash
# Part B on bj-hserver: the blind run in ~/dev/assembly-blind (AGENT.md), one headless claude session per iteration.
#   cd ~/dev/studyDev/mma4002-h26-outdoor-furniture/3d-modeling-and-simulation/assembly-experiment
#   $PY make_sandbox.py --force                      fresh sandbox + leak check (must pass)
#   nohup nice -n 10 bash run_part_b.sh > results/part_b.log 2>&1 &
# Watch: tail -F ~/dev/assembly-blind/log/run.jsonl ~/dev/assembly-blind/log/iterations.csv (watch_server.ps1)
# Stop:  kill $(cat ~/dev/assembly-blind/log/runner.pid)   the runner stops claude, then still copies + commits the logs
# Env:   MAXN (30) ITER_TIMEOUT (s per session, 7200) MODEL (claude-opus-5-5) DRY=1 (no commit/push)
#        SMOKE=1 (one harness-test iteration with a scripted prompt, implies DRY=1 and MAXN=1)
# At the end: log/ (raw claude streams gzipped, shots of kept iterations only), best/ and AGENT.md are copied to
# results/part_b/, committed and pushed from here.
set -u
EXP=$(cd "$(dirname "$0")" && pwd)
BOX=${BOX:-$HOME/dev/assembly-blind}
export ASSEMBLY_PY=${PY:-$HOME/dev/studyDev/MSc-MechAuto-NTNU/.venv/bin/python}
CLAUDE=${CLAUDE:-$HOME/.local/bin/claude}
MODEL=${MODEL:-claude-opus-5-5}
MAXN=${MAXN:-30}
ITER_TIMEOUT=${ITER_TIMEOUT:-7200}
SMOKE=${SMOKE:-0}
DRY=${DRY:-$SMOKE}
[ "$SMOKE" = 1 ] && MAXN=1
LOG=$BOX/log
SUMS=$BOX.judge.sha256
mkdir -p "$LOG/claude"
echo $$ > "$LOG/runner.pid"
T0=$(date +%s)

jlog() {   # event, msg [, extra json]
  local extra=${3:-}
  [ -z "$extra" ] && extra='{}'
  python3 - "$1" "$2" "$extra" >> "$LOG/run.jsonl" <<'EOF'
import datetime, json, sys
ev, msg, extra = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
print(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"), "src": "runner", "event": ev,
                  "msg": msg, **extra}), flush=True)
EOF
}
st() { python3 -c "import json; s = json.load(open('$LOG/state.json')); print($1)"; }
judge_ok() { (cd "$BOX/judge" && sha256sum -c --quiet "$SUMS") >/dev/null 2>&1; }

CPID=""
STOP=0
on_term() { STOP=1; jlog stop_requested "runner got a stop signal: stopping claude, then copying the logs"; \
            [ -n "$CPID" ] && kill -TERM -- -"$CPID" 2>/dev/null; }
trap on_term TERM INT

finish() {
  kill "$WATCH" 2>/dev/null
  local wall=$(( $(date +%s) - T0 ))
  jlog run_end "run ended after $((wall / 60)) min: $(st "'decided ' + str(len(s['decided']) - 1) + ' iterations, best iter %02d' % s['best_iter'] + ', streak ' + str(s['streak'])" 2>/dev/null)" "{\"wall_s\": $wall}"
  if [ "$SMOKE" = 1 ]; then echo "SMOKE: logs stay in $LOG"; return; fi
  local DEST=$EXP/results/part_b
  rm -rf "$DEST"; mkdir -p "$DEST/log/claude"
  rsync -a --exclude 'shots/' --exclude 'claude/' --exclude 'runner.pid' "$LOG/" "$DEST/log/"
  for f in "$LOG"/claude/*.jsonl; do [ -f "$f" ] && gzip -c "$f" > "$DEST/log/claude/$(basename "$f").gz"; done
  python3 - "$LOG" "$DEST/log" <<'EOF'
import csv, shutil, sys
from pathlib import Path
log, dest = Path(sys.argv[1]), Path(sys.argv[2])
for r in csv.DictReader((log / "iterations.csv").open()) if (log / "iterations.csv").exists() else []:
    src = log / f"iter_{int(r['iteration']):02d}" / "shots"
    if r["kept"] == "True" and src.exists():
        shutil.copytree(src, dest / src.parent.name / "shots", dirs_exist_ok=True)
EOF
  rsync -a --exclude '__pycache__' "$BOX/best/" "$DEST/best/" 2>/dev/null
  cp "$BOX/AGENT.md" "$DEST/AGENT.md"
  if [ "$DRY" = 1 ]; then echo "DRY: no commit"; return; fi
  cd "$EXP" || return
  git add results/part_b results/part_b.log 2>/dev/null
  git commit -q -m "assembly-experiment Part B: blind run logs from bj-hserver ($(st "len(s['decided']) - 1" 2>/dev/null) iterations)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || true
  git pull -q --rebase --autostash && git push -q && jlog pushed "logs committed and pushed: $(git rev-parse --short HEAD)"
}

# ---------------------------------------------------------------- checks before the start
[ -d "$BOX/judge" ] || { echo "no sandbox at $BOX: run make_sandbox.py first"; exit 1; }
judge_ok || { jlog abort "judge files do not match $SUMS"; exit 1; }
"$ASSEMBLY_PY" "$EXP/make_sandbox.py" --leak-check-only --skip-log --root "$BOX" || { jlog abort "leak check failed"; exit 1; }
jlog run_start "Part B start: model $MODEL, up to $MAXN iterations, $ITER_TIMEOUT s per session$([ "$SMOKE" = 1 ] && echo ', SMOKE TEST')"

# judge watchdog: every minute; a changed file is logged and put back
( while sleep 60; do
    if ! judge_ok; then
      bad=$(cd "$BOX/judge" && sha256sum -c "$SUMS" 2>/dev/null | grep -v ': OK$' | cut -d: -f1 | tr '\n' ' ')
      jlog judge_tampered "judge files changed: $bad - restored from the repo copy"
      chmod u+w "$BOX/judge"; for f in $bad; do chmod u+w "$BOX/judge/$f" 2>/dev/null; cp "$EXP/judge/$f" "$BOX/judge/$f"; chmod 444 "$BOX/judge/$f"; done
      chmod 555 "$BOX/judge"
    fi
  done ) &
WATCH=$!

if [ ! -f "$LOG/state.json" ]; then
  jlog baseline_start "scoring the v3 baseline (iter 00)"
  (cd "$BOX" && ./py judge/iterate.py baseline) || { jlog abort "baseline failed"; finish; exit 1; }
fi

session() {   # iteration, prompt, timeout
  local n=$1 nn; nn=$(printf %02d "$1")
  setsid bash -c "cd '$BOX' && timeout --kill-after=60 $3 '$CLAUDE' -p \"\$0\" --model '$MODEL' \
      --permission-mode dontAsk --setting-sources project --settings '$BOX.settings.json' --strict-mcp-config \
      --disallowedTools WebFetch WebSearch --output-format stream-json --verbose < /dev/null \
      | python3 '$EXP/stream_filter.py' --iter $n --raw '$LOG/claude/iter_$nn.jsonl' --out '$LOG/run.jsonl'" "$2" &
  CPID=$!
  wait "$CPID"
  CPID=""
}
decided() { python3 -c "import json, sys; sys.exit(0 if $1 in json.load(open('$LOG/state.json'))['decided'] else 1)"; }

# ---------------------------------------------------------------- the loop
while [ "$STOP" = 0 ]; do
  N=$(st "max(s['decided']) + 1"); STREAK=$(st "s['streak']")
  if [ "$N" -gt "$MAXN" ] || [ "$STREAK" -ge 5 ]; then
    jlog budget_done "budget used up: next would be iter $N, no-improvement streak $STREAK"
    break
  fi
  NN=$(printf %02d "$N"); t1=$(date +%s)
  if [ "$SMOKE" = 1 ]; then
    P="HARNESS SMOKE TEST (not a real iteration). Read AGENT.md. Then: 1) ./py judge/iterate.py status. 2) Try once to append a line to judge/score.py and once to read ../ (expect both to be refused) and say what happened. 3) Write log/iter_$NN/notes.md: '# iter $NN: harness test', '## Hypothesis' 'No change to the design; this only tests the scoring harness end to end; expected delta 0 s and the same violations as the baseline.' 4) ./py judge/iterate.py score $N --type program. 5) Look at two of the shots and topview.png, write '## Screenshots' (a line each) and '## Result' in the notes. 6) ./py judge/iterate.py decide $N reject --reason 'harness smoke test'. 7) Add one lesson block to log/lessons.md about anything that went wrong (or 'L01 (iter $NN) smoke test: nothing went wrong'). Then stop."
  else
    P="You are the agent in this experiment sandbox. Run iteration $N now, exactly as AGENT.md says: read AGENT.md and log/lessons.md first, run ./py judge/iterate.py status, then hypothesis -> change -> score -> screenshots -> decide. End the session right after ./py judge/iterate.py decide $N ... (and the log updates). Do not start iteration $((N + 1)). If decide reports the budget is used up, write log/summary.md first."
  fi
  jlog iter_start "iter $NN: session starts (streak $STREAK/5)" "{\"iter\": $N}"
  session "$N" "$P" "$ITER_TIMEOUT"
  [ "$STOP" = 1 ] && break
  if ! decided "$N"; then
    jlog iter_retry "iter $NN: session ended without a decision; one more session to finish it" "{\"iter\": $N}"
    session "$N" "Finish iteration $N of AGENT.md now: if it is not scored, score it (./py judge/iterate.py score $N --type ...) or, if the change is not ready, write why in log/iter_$NN/notes.md and run ./py judge/iterate.py decide $N reject --reason 'not finished'. If it is scored, look at the shots, complete notes.md and decide. Log any problem in log/lessons.md. Then stop." 1800
    [ "$STOP" = 1 ] && break
    if ! decided "$N"; then
      (cd "$BOX" && ./py judge/iterate.py decide "$N" reject --reason "session ended without a decision" --force)
      jlog iter_forced "iter $NN: rejected by the runner (no decision)" "{\"iter\": $N}"
    fi
  fi
  jlog iter_end "iter $NN: done in $(( ($(date +%s) - t1) / 60 )) min" "{\"iter\": $N, \"wall_s\": $(( $(date +%s) - t1 ))}"
done
finish
echo "DONE"
