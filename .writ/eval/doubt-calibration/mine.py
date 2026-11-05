#!/usr/bin/env python3
"""Dev-only. Mine labeled doubt examples from Claude Code transcripts.

Reads AskUserQuestion calls and their answers from the transcripts of ONE
project (default: this repository and its worktrees) and writes one JSONL row
per question that carried a `(Recommended)` option:

  {"id", "question", "options": [{"label", "description"}], "recommended",
   "evidence": [...], "outcome": "as_recommended" | "overridden",
   "source": "<transcript>:<line>"}

`evidence` holds what the assistant had when it asked: the person's last request
(its first REQUEST_CHARS characters) and the assistant's text since that request
(its last REASONING_CHARS characters). Nothing after the question is read, so no
row carries its own answer. `--no-evidence` writes the rows without it.

The rows are personal data about the maintainer's answers. They are written to
the gitignored `.writ/state/` by default and are never committed.

Usage: mine.py [--transcripts DIR] [--prefix NAME ...] [--out FILE] [--no-evidence]
Prints one summary line: `mine: rows=<n> as_recommended=<a> overridden=<o>`.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

SUFFIX = "(Recommended)"
REQUEST_CHARS = 1500
REASONING_CHARS = 2500
_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
_COMMAND = re.compile(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", re.S)
_TAG = re.compile(r"</?[a-z-]+>")
# User events the app writes, not the person: they never replace the request.
_NOT_A_REQUEST = ("<local-command-", "<task-notification>", "<side-sessions-event>",
                  "<ci-monitor-event>", "[Request interrupted")


def strip(label):
    label = label.rstrip()
    return label[: -len(SUFFIX)].rstrip() if label.endswith(SUFFIX) else label


def request_text(ev):
    """The person's words in a user event, or None when the event is not a request
    (a tool result, a meta or summary event, a local command's output)."""
    if ev.get("type") != "user" or ev.get("isMeta") or ev.get("isCompactSummary"):
        return None
    content = (ev.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(isinstance(p, dict) and p.get("type") == "tool_result" for p in content):
            return None
        content = " ".join(p.get("text", "") for p in content
                           if isinstance(p, dict) and p.get("type") == "text")
    if not isinstance(content, str):
        return None
    if any(marker in content for marker in _NOT_A_REQUEST):
        return None
    command = _COMMAND.search(content)
    if command:
        content = ("%s %s" % (command.group(1), command.group(2))).strip()
    text = _TAG.sub("", _REMINDER.sub("", content)).strip()
    return text or None


def evidence_from(request, reasoning):
    out = []
    if request:
        out.append("The person's request: " + request[:REQUEST_CHARS])
    said = " ".join(t.strip() for t in reasoning if t.strip())
    if said:
        out.append("What the assistant said before asking: " + said[-REASONING_CHARS:])
    return out


def rows_from(path):
    pending = {}
    request, reasoning = None, []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            asked = request_text(ev)
            if asked is not None:
                request, reasoning = asked, []
                continue
            content = (ev.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if ev.get("type") == "assistant" and part.get("type") == "text":
                    reasoning.append(part.get("text", ""))
                elif part.get("type") == "tool_use" and part.get("name") == "AskUserQuestion":
                    pending[part.get("id")] = (part.get("input") or {}, n,
                                               evidence_from(request, reasoning))
                elif part.get("type") == "tool_result" and part.get("tool_use_id") in pending:
                    inp, at, evidence = pending.pop(part.get("tool_use_id"))
                    res = part.get("content")
                    if isinstance(res, list):
                        res = " ".join(x.get("text", "") for x in res if isinstance(x, dict))
                    res = res or ""
                    for q in inp.get("questions") or []:
                        opts = q.get("options") or []
                        rec = [o.get("label", "") for o in opts
                               if o.get("label", "").rstrip().endswith(SUFFIX)]
                        text = q.get("question", "")
                        m = re.search(re.escape('"%s"' % text) + r'="([^"]*)"', res)
                        if len(rec) != 1 or not m or q.get("multiSelect"):
                            continue
                        answer = m.group(1).strip()
                        labels = [o.get("label", "").strip() for o in opts]
                        outcome = "as_recommended" if answer == rec[0].strip() else "overridden"
                        if outcome == "overridden" and answer not in labels:
                            outcome = "overridden"  # free-text "Other" answers count as overrides
                        row = {
                            "question": text,
                            "options": [{"label": strip(o.get("label", "")),
                                         "description": o.get("description", "")} for o in opts],
                            "recommended": strip(rec[0]),
                            "evidence": evidence,
                            "outcome": outcome,
                            "source": "%s:%d" % (os.path.basename(path), at),
                        }
                        row["id"] = hashlib.sha256(json.dumps(
                            [row["question"], row["options"], row["recommended"]],
                            sort_keys=True).encode()).hexdigest()[:16]
                        yield row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcripts", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--prefix", action="append",
                    default=None, help="project directory name prefix (repeatable)")
    ap.add_argument("--out", default=".writ/state/doubt-calibration/labeled.jsonl")
    ap.add_argument("--no-evidence", action="store_true",
                    help="write rows without the request and reasoning that preceded each question")
    args = ap.parse_args(argv)
    prefixes = args.prefix or ["-Users-asellke-Projects-writ"]
    seen, rows = set(), []
    for root in sorted(os.listdir(args.transcripts)):
        exact = root in prefixes
        worktree = any(root.startswith(p + "--claude-worktrees-") for p in prefixes)
        if not (exact or worktree):
            continue
        for path in sorted(glob.glob(os.path.join(args.transcripts, root, "**", "*.jsonl"),
                                     recursive=True)):
            for row in rows_from(path):
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                if args.no_evidence:
                    row.pop("evidence")
                rows.append(row)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    a = sum(1 for r in rows if r["outcome"] == "as_recommended")
    e = sum(1 for r in rows if r.get("evidence"))
    print("mine: rows=%d as_recommended=%d overridden=%d with_evidence=%d out=%s"
          % (len(rows), a, len(rows) - a, e, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
