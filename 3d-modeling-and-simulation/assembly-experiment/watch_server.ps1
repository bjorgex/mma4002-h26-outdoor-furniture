# Live log of the assembly experiment on bj-hserver (Part A log; Part B run.jsonl + iterations.csv once it runs).
# Windows OpenSSH, not WSL. Ctrl+C to stop.
$exp = '~/dev/studyDev/mma4002-h26-outdoor-furniture/3d-modeling-and-simulation/assembly-experiment'
$remote = @"
echo '== bj-hserver: assembly experiment =='; uptime
pgrep -af 'score_run|run_part_b|claude -p' | grep -v pgrep | cut -c1-160 || echo 'nothing running right now'
echo; tail -n 30 -F $exp/results/part_a.log ~/dev/assembly-blind/log/run.jsonl ~/dev/assembly-blind/log/iterations.csv 2>&1 | grep --line-buffered -v 'cannot open'
"@
& "$env:SystemRoot\System32\OpenSSH\ssh.exe" -t bj-hserver $remote
