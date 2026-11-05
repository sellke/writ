#!/usr/bin/env python3
"""Dev-only. Mine labeled doubt examples from Claude Code transcripts.

Reads AskUserQuestion calls and their answers from the transcripts of ONE
project (default: this repository and its worktrees) and writes one JSONL row
per question that carried a `(Recommended)` option:

  {"id", "question", "options": [{"label", "description"}], "recommended",
   "outcome": "as_recommended" | "overridden", "source": "<transcript>:<line>"}

The rows are personal data about the maintainer's answers. They are written to
the gitignored `.writ/state/` by default and are never committed.

Usage: mine.py [--transcripts DIR] [--prefix NAME ...] [--out FILE]
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


def strip(label):
    label = label.rstrip()
    return label[: -len(SUFFIX)].rstrip() if label.endswith(SUFFIX) else label


def rows_from(path):
    pending = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            content = (ev.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "tool_use" and part.get("name") == "AskUserQuestion":
                    pending[part.get("id")] = (part.get("input") or {}, n)
                elif part.get("type") == "tool_result" and part.get("tool_use_id") in pending:
                    inp, at = pending.pop(part.get("tool_use_id"))
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
                rows.append(row)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    a = sum(1 for r in rows if r["outcome"] == "as_recommended")
    print("mine: rows=%d as_recommended=%d overridden=%d out=%s" % (len(rows), a, len(rows) - a, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
