# Coordinator workflow

Adapted from the solo study-coordinator pattern in `MSc-MechAuto-NTNU/WORKFLOW.md` for this
repo: one project instead of several parallel courses, and a real teammate (see `git log`) also
pushing here — not just Bjørge working alone.

One **coordinator** session per work session, driving **work-stream** sessions in the background
(one per active area of work: configurator, CAD/RoboDK, a report write-up, ...). Bjørge only
talks to Claude between focus blocks if he's using his `focus` timer; otherwise he talks to the
coordinator whenever, and it queues background reports instead of interrupting.

```
Bjørge ── coordinator (this repo, one per session) ── work-stream sessions (background)
                                                          └─ their own subagents when useful
```

## Starting the coordinator
- **Terminal:** open Claude Code in this repo's root and type `coord`.
- **VS Code Claude side panel:** open a new chat with this repo (or a folder in it) as the
  workspace and type `coord`.

**Know your own name:** call `ListAgents` once at the start; its first line says "This session
is <name>". Work-stream sessions report to that name, so put it in every brief.

## Coordinator

### Start of session
0. **One coordinator at a time.** If today's diary (`diary/YYYY-MM-DD.md`) exists, read its
   `Coordinator:` line.
   - That session is still in `ListAgents` → don't start a second one: tell Bjørge "today's
     coordinator is <name>, switch to that chat/terminal" and stop.
   - It's gone → **take over**: write your own name on the `Coordinator:` line (old one moves to
     the Log), `SendMessage` every running work-stream session "From now on report to <your
     name>." Don't create a new diary — carry over its plan/queue/log.
1. `git pull --rebase`.
2. Skim `git log --oneline -20` for anything a teammate (anyone who isn't Bjørge) pushed since
   the last session — note it in the diary's Plan so it isn't silently overwritten.
3. Read the newest file in `diary/`: open questions, unfinished tasks, tomorrow's plan.
4. `claude agents --json` → which work-stream sessions are already running on this machine.
5. Create today's diary file (format below) with your name on the `Coordinator:` line, and ask
   Bjørge for the first tasks.
6. Hand them out, then start the focus timer if he uses it (below). From here the session runs
   itself: he doesn't have to type `coord` again.

### The focus timer (optional, Bjørge's own habit)
`powershell -Command focus` (profile function from the dotfiles repo). 25 min focus (Do Not
Disturb, his Spotify playlist) → chime, 5 min break → chime → READY. Running it again while open
starts the next block. State in `%APPDATA%\focus\state.json`: `phase` = `focus` | `break` |
`ready` | `stopped`, plus `endsAt`. If he isn't using it, skip this and just treat every message
from him as a check-in (go to the break routine).

### While work streams are running — queue, don't interrupt
When a work-stream session reports, add it to the diary's **Queue** section and say nothing
unless he's actively mid-message to you. One queue item = one result to review and/or one
decision.

### Any message from Bjørge
- If the focus timer is running and in `focus` phase: answer briefly, don't show the agenda,
  don't touch the timer.
- Otherwise (break, ready, stopped, or no timer in use): run the break routine below. A question
  gets answered first, then the agenda.

### Break routine
1. **Agenda:** a numbered list, one line per queue item plus what's still running:
   ```
   Agenda (2 items)
   1. cad-robodk — jig V2 clearance check done, 1 question
   2. configurator — decoration toggle built, review only
   Still running: writeup-A3
   ```
2. **One item at a time:** open its result files (`code -r "<path>"`; CAD → see "CAD results"
   below), a 2–3 line recap, **one** question. Wait.
3. His answer → `SendMessage` it to that work-stream session and log it in the diary. Then the
   next item. `skip` → stays queued for next time.
4. Queue empty → hand out new tasks, checkpoint commit (below), restart the focus timer if in
   use. Nothing to hand out → say so in one line, unless he's done for the session.

### CAD results
The work-stream session builds the model **before** reporting — building can take minutes,
showing must not. It exports a STEP to `_preview/<name>.step` next to the script (gitignored). At
review, the coordinator only loads that file:
```
.venv/Scripts/python.exe -c "from build123d import import_step; from ocp_vscode import show; show(import_step(r'<path>'))"
```
(Adjust the venv path to whichever one is current for this repo.) Only one model in the viewer at
a time: the item being reviewed.

### Work streams
Not a fixed table — name one for whatever's actually being worked on, e.g.:
- `configurator` — `index.html`
- `cad-robodk` — `3d-modeling-and-simulation/` (CAD, RoboDK cell)
- `writeup-<N>` — the active `assignment-<N>-.../` report

Start one only when there's a task for it; don't keep an idle one running.
- **No session for the stream yet:**
  ```
  claude --bg -n "<stream>" --permission-mode auto "<brief>"
  ```
  Then `SendMessage` to that name with `notify_when_idle: true` (no message) so you hear when it
  stops.
- **Already running:** `SendMessage` the new brief to `"<stream>"` with `notify_when_idle: true`.
- Session goes idle but no report arrived → `claude logs "<stream>"` to see why.

**Brief template** (every brief starts with this, then the task):
```
You are the background work-stream session for <stream> on this repo. Bjørge is busy and can't
answer until his next check-in — work without stopping to ask.
- Task: <one task, sized to finish in one go>. Done means: <concrete deliverable>.
- If something is unclear, make a reasonable assumption, note it, and continue. If you truly
  cannot continue, stop and say what you need.
- Follow the repo CLAUDE.md. This is a group project — a teammate may have touched files you
  didn't expect; don't assume you have the only eyes on this repo.
- Stay inside your area. Do not git commit or push. Suggest changes to shared files
  (root CLAUDE.md, index.html if another stream owns it) in your report instead.
- Don't open viewers or call show(); save files (plots, PDF, screenshots) and list them. CAD:
  build the model and export to `_preview/<name>.step` next to the script before reporting.
- Use subagents for independent parallel parts if it speeds things up.
- When done, SendMessage your report to "<coordinator's own name>":
  Done: <2–4 lines> | Files: <changed/created paths> | Assumptions | Questions (numbered) |
  Suggested commit message.
```

### Shared single-user tools
- **RoboDK main station** (port 20500, licensed — saves stations, exports to TMflow): only one
  session drives it. A second work stream that needs RoboDK builds/tests against an unlicensed
  instance instead: `$env:ROBODK_API_PORT=20601` before it runs.
- **OCP CAD Viewer:** only the coordinator opens it, during review.

### Checkpoint commit (each check-in, local + push)
- `git pull --rebase` **immediately before pushing** — a teammate may have pushed since you
  started. Stop only on a real conflict and flag it to Bjørge.
- Commit **per task**, adding only that task's paths (from its report): `git add -- <paths>` →
  `git commit -m "<stream>: <suggested message>"`. Write messages a teammate skimming `git log`
  would understand — not shorthand only you'd recognize.
- Generated exports (STL, 3MF, STEP previews) go in a gitignored folder next to the script, not
  into the commit — commit the script, not its output. `simulations-html/*.html` is the
  exception: tracked via Git LFS (see `.gitattributes`).
- **Never commit a file over 50 MB** (GitHub warns at 50 MB, rejects at 100 MB) unless it's going
  through LFS: list it under "Not committed" in the diary and let Bjørge decide.
- `git push`. Report the commit hash and that `main` matches `origin/main`.

### End of session
1. Write the diary's "Summary" and "Tomorrow".
2. Last checkpoint commit (diary included) and push.
3. Leave work-stream sessions running unless Bjørge says stop (`claude stop "<stream>"`).

### Keep the coordinator's context small
Summaries and paths, not file contents. Work-stream sessions do the reading. The diary is the
memory between sessions — and, since this is shared, a quick way for a teammate to see what's
been done without reading the whole chat history.

## Diary — `diary/YYYY-MM-DD.md`
```
# YYYY-MM-DD
Coordinator: <name from ListAgents>

## Plan
- <stream>: <goal for this session>
- (note here if a teammate pushed something since last time)

## Queue
- [ ] <stream> — <result / decision> → <files>   (ticked off when reviewed)

## Log
### HH:MM check-in
- <stream> — <task given / result> → <file links>
- Q1 (<stream>): <question> → <his answer>

## Not committed
- <path> (<size>, why)

## Summary
<3–6 lines: what got done, per stream>

## Tomorrow
- <open task / question>
```

## For Bjørge — moving between sessions
| Want to | Do |
|---|---|
| See all sessions | `claude agents` |
| Jump into a work-stream session (read history, talk directly) | `claude attach "<stream>"` — detach and you're back |
| Peek at its output | `claude logs "<stream>"` |
| Stop one | `claude stop "<stream>"` |
