"""Condense `claude -p --output-format stream-json --verbose` into run.jsonl lines as they happen.

    claude -p ... | python3 stream_filter.py --iter 3 --raw log/claude/iter_03.jsonl --out log/run.jsonl

Every input line is kept as is in --raw; one short line per event goes to --out: {"t", "src": "agent", "iter",
"event", "msg", ...}: session_start (model), text (the agent's words, cut), tool (name + command / file),
tool_error, leak_risk (a tool input that names the repo or paths outside the sandbox), session_end (turns, time,
cost, tokens). Standard library only.
"""
import argparse
import datetime
import json
import re
import sys

LEAK = re.compile(r"mma4002|outdoor-furniture|robot-cell|robot_sim|assembly-experiment|studyDev|\.claude/projects|"
                  r"\bgit\b|https?://", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", type=int, required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = open(a.raw, "a", encoding="utf-8")
    out = open(a.out, "a", encoding="utf-8")

    def emit(event, msg, **kw):
        out.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"), "src": "agent",
                              "iter": a.iter, "event": event, "msg": msg, **kw}) + "\n")
        out.flush()

    for line in sys.stdin:
        raw.write(line)
        raw.flush()
        try:
            m = json.loads(line)
        except ValueError:
            emit("stdout", line.strip()[:300])
            continue
        t = m.get("type")
        if t == "system" and m.get("subtype") == "init":
            emit("session_start", f"iter {a.iter:02d}: session start, model {m.get('model')}, "
                                  f"permission mode {m.get('permissionMode')}", model=m.get("model"))
        elif t == "assistant":
            for c in m.get("message", {}).get("content", []):
                if c.get("type") == "text" and c.get("text", "").strip():
                    emit("text", c["text"].strip().replace("\n", " ")[:400])
                elif c.get("type") == "tool_use":
                    inp = c.get("input", {})
                    what = inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("path") or \
                        json.dumps(inp)[:200]
                    emit("tool", f"{c.get('name')}: {str(what)[:300]}")
                    blob = json.dumps(inp)
                    if LEAK.search(blob):
                        emit("leak_risk", f"tool input names something outside the sandbox: {blob[:300]}")
        elif t == "user":
            for c in m.get("message", {}).get("content", []) if isinstance(m.get("message", {}).get("content"), list) else []:
                if c.get("type") == "tool_result" and c.get("is_error"):
                    body = c.get("content")
                    if isinstance(body, list):
                        body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                    emit("tool_error", str(body).replace("\n", " ")[:300])
        elif t == "result":
            u = m.get("usage", {}) or {}
            emit("session_end", f"iter {a.iter:02d}: session end ({m.get('subtype')}), {m.get('num_turns')} turns, "
                                f"{(m.get('duration_ms') or 0) / 60000:.1f} min, ${m.get('total_cost_usd') or 0:.2f}, "
                                f"tokens in {u.get('input_tokens')} (+cache read {u.get('cache_read_input_tokens')}, "
                                f"cache write {u.get('cache_creation_input_tokens')}) out {u.get('output_tokens')}",
                 turns=m.get("num_turns"), duration_ms=m.get("duration_ms"), cost_usd=m.get("total_cost_usd"),
                 usage=u, is_error=m.get("is_error"))


if __name__ == "__main__":
    main()
