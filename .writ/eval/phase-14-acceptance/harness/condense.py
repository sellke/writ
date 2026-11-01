"""condense.py <run.jsonl> -> readable transcript on stdout (tool calls, results, text, final)."""
import json, sys
def short(x, n=600):
    s = x if isinstance(x, str) else json.dumps(x)
    return s if len(s) <= n else s[:n] + " …[%d chars]" % len(s)
lines = []
for raw in open(sys.argv[1], errors="ignore"):
    try: e = json.loads(raw)
    except Exception: continue
    t = e.get("type")
    if t == "turn_marker":
        lines.append("===== TURN %s =====" % e.get("turn")); continue
    # Claude Code stream-json
    if t == "system" and e.get("subtype") == "init":
        lines.append("[init] model=%s output_style=%s slash_commands=%d agents=%s" % (
            e.get("model"), e.get("output_style"), len(e.get("slash_commands", [])), e.get("agents")))
    elif t == "assistant":
        for b in e["message"].get("content", []):
            if b.get("type") == "text": lines.append("ASSISTANT: " + b["text"])
            elif b.get("type") == "tool_use": lines.append("TOOL_CALL %s: %s" % (b["name"], short(b.get("input"), 1500)))
    elif t == "user":
        c = e.get("message", {}).get("content")
        if isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_result":
                    cc = b.get("content"); cc = " ".join(x.get("text", "") for x in cc if isinstance(x, dict)) if isinstance(cc, list) else cc
                    lines.append("TOOL_RESULT%s: %s" % (" (error)" if b.get("is_error") else "", short(cc)))
    elif t == "result":
        lines.append("[result] %s turns=%s cost=%s" % (e.get("subtype"), e.get("num_turns"), e.get("total_cost_usd")))
    # Codex exec --json
    elif t in ("item.completed", "item.started") and t == "item.completed":
        it = e.get("item", {}); k = it.get("type")
        if k == "agent_message": lines.append("ASSISTANT: " + it.get("text", ""))
        elif k == "command_execution": lines.append("TOOL_CALL shell: %s\nTOOL_RESULT: %s" % (it.get("command"), short(it.get("aggregated_output", ""))))
        elif k == "file_change": lines.append("TOOL_CALL file_change: %s" % short(it.get("changes")))
        elif k == "reasoning": pass
        else: lines.append("ITEM %s: %s" % (k, short(it)))
    elif t == "thread.started":
        lines.append("[codex thread] %s" % e.get("thread_id"))
    elif t == "turn.completed":
        lines.append("[turn.completed] usage=%s" % short(e.get("usage"), 200))
print("\n".join(lines))
