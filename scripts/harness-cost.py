#!/usr/bin/env python3
"""Price-weighted cost of a Writ pipeline run, and the static prefix that every
command invocation pays.

`pipeline-baseline.py` already stores per-run `tokens` (the transcript result
event: input, output, cache_read, cache_creation) and driver `cost_usd`. It
does not turn those into a cache hit rate or a billing-type cost share, and
it does not say how much of a request is the always-loaded prefix.

Two numbers must not be mixed:

- `tokens` is one usage object on the result event. It is what the published
  formula below is applied to. It is not a sum of turns.
- `tokens_main_thread` is the sum of per-turn usage on the parent thread
  (subagent events that carry `parent_tool_use_id` are excluded). Summing
  cache reads across turns counts the same prefix once per turn. Do not
  subtract it from `tokens` to estimate worker spend.

`cost_usd` is the price of record. The formula ($10 input / $50 output /
$0.25 cache read per million tokens, cache creation omitted) is the one
Phase 11 Story 5 recorded, and that story showed it understates the driver.
This script prints both and never replaces `cost_usd` with the formula.

Static sections are bytes. Tokens are `bytes / chars_per_token` and are
labeled as an estimate. This script does not call a tokenizer.

Usage:
  harness-cost.py baseline PATH [--format text|json]
  harness-cost.py static [--root .] [--chars-per-token 4] [--format text|json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Phase 11 Story 5 rate card. Cache creation is intentionally absent: the
# story's formula did not price it, and inventing a rate here would launder
# the gap the story already measured.
RATE_INPUT_PER_MTOK = 10.0
RATE_OUTPUT_PER_MTOK = 50.0
RATE_CACHE_READ_PER_MTOK = 0.25

TOKEN_KEYS = ("input", "output", "cache_read", "cache_creation")

STATIC_FILES = (
    ("system_prompt", "system-instructions.md"),
    ("preamble", "commands/_preamble.md"),
    ("claude_md", "CLAUDE.md"),
    ("agents_md", "AGENTS.md"),
)


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return value


def _tokens_of(run):
    raw = run.get("tokens") if isinstance(run, dict) else None
    if not isinstance(raw, dict):
        raw = {}
    return {key: _num(raw.get(key)) for key in TOKEN_KEYS}


def formula_usd(tokens):
    """Lower-bound dollar estimate. Omits cache creation on purpose."""
    return (
        tokens["input"] * RATE_INPUT_PER_MTOK
        + tokens["output"] * RATE_OUTPUT_PER_MTOK
        + tokens["cache_read"] * RATE_CACHE_READ_PER_MTOK
    ) / 1_000_000.0


def cache_hit_rate(tokens):
    """Share of input-side tokens served from cache.

    Denominator is uncached input + cache read + cache creation. Output is
    not an input-side token and is excluded. Zero when nothing was read.
    """
    denom = tokens["input"] + tokens["cache_read"] + tokens["cache_creation"]
    if denom <= 0:
        return None
    return tokens["cache_read"] / denom


def summarize_baseline(doc):
    runs = doc.get("runs") if isinstance(doc, dict) else None
    if not isinstance(runs, list):
        runs = []
    totals = {key: 0 for key in TOKEN_KEYS}
    cost = 0.0
    turns = 0
    complete = 0
    priced = 0
    for run in runs:
        if not isinstance(run, dict):
            continue
        tokens = _tokens_of(run)
        for key in TOKEN_KEYS:
            totals[key] += tokens[key]
        if run.get("cost_usd") is not None:
            cost += _num(run.get("cost_usd"))
            priced += 1
        turns += int(_num(run.get("num_turns")))
        if run.get("status") == "complete":
            complete += 1
    formula = formula_usd(totals)
    hit = cache_hit_rate(totals)
    input_side = totals["input"] + totals["cache_read"] + totals["cache_creation"]
    return {
        "runs": len([r for r in runs if isinstance(r, dict)]),
        "complete": complete,
        "priced_runs": priced,
        "turns": turns,
        "tokens": totals,
        "cost_usd": cost,
        "formula_usd": formula,
        "formula_note": (
            "Lower bound: $10/MTok uncached input, $50/MTok output, "
            "$0.25/MTok cache read. Cache creation is not priced. "
            "cost_usd is the price of record."
        ),
        "cache_hit_rate": hit,
        "input_side_tokens": input_side,
        "billing_share_of_formula": _formula_shares(totals, formula),
    }


def _formula_shares(tokens, formula):
    if formula <= 0:
        return {key: None for key in ("input", "output", "cache_read")}
    return {
        "input": (tokens["input"] * RATE_INPUT_PER_MTOK / 1_000_000.0) / formula,
        "output": (tokens["output"] * RATE_OUTPUT_PER_MTOK / 1_000_000.0) / formula,
        "cache_read": (tokens["cache_read"] * RATE_CACHE_READ_PER_MTOK / 1_000_000.0) / formula,
    }


def _file_bytes(root: Path, rel: str):
    path = root / rel
    if not path.is_file():
        return None
    return len(path.read_bytes())


def static_sections(root: Path, chars_per_token: float = 4.0):
    sections = []
    for name, rel in STATIC_FILES:
        size = _file_bytes(root, rel)
        sections.append({
            "source": name,
            "path": rel,
            "bytes": size,
            "tokens_estimate": None if size is None else size / chars_per_token,
        })
    commands = sorted((root / "commands").glob("*.md"))
    command_bytes = 0
    largest = None
    for path in commands:
        if path.name == "_preamble.md":
            continue
        size = len(path.read_bytes())
        command_bytes += size
        if largest is None or size > largest[1]:
            largest = (path.name, size)
    sections.append({
        "source": "commands_except_preamble",
        "path": "commands/*.md",
        "bytes": command_bytes,
        "tokens_estimate": command_bytes / chars_per_token,
        "files": len(commands) - (1 if (root / "commands" / "_preamble.md").is_file() else 0),
        "largest": None if largest is None else {"name": largest[0], "bytes": largest[1]},
    })
    return {
        "chars_per_token": chars_per_token,
        "token_method": "estimate",
        "token_method_validated": False,
        "sections": sections,
    }


def _fmt_rate(value):
    if value is None:
        return "n/a"
    return "%.1f%%" % (value * 100.0)


def _fmt_usd(value):
    return "$%.2f" % value


def format_baseline(summary):
    tokens = summary["tokens"]
    lines = [
        "runs: %d complete, %d priced, %d turns" % (
            summary["complete"], summary["priced_runs"], summary["turns"]),
        "tokens: input=%d output=%d cache_read=%d cache_creation=%d" % (
            tokens["input"], tokens["output"], tokens["cache_read"], tokens["cache_creation"]),
        "cache_hit_rate: %s (cache_read / input-side)" % _fmt_rate(summary["cache_hit_rate"]),
        "cost_usd: %s (price of record)" % _fmt_usd(summary["cost_usd"]),
        "formula_usd: %s (lower bound, cache creation omitted)" % _fmt_usd(summary["formula_usd"]),
    ]
    shares = summary["billing_share_of_formula"]
    lines.append(
        "formula share: input %s, output %s, cache_read %s"
        % (_fmt_rate(shares["input"]), _fmt_rate(shares["output"]), _fmt_rate(shares["cache_read"]))
    )
    return "\n".join(lines)


def format_static(report):
    lines = [
        "token_method: estimate (bytes / %s), not validated" % report["chars_per_token"],
    ]
    for section in report["sections"]:
        size = section["bytes"]
        est = section["tokens_estimate"]
        if size is None:
            lines.append("%s: missing (%s)" % (section["source"], section["path"]))
            continue
        lines.append("%s: %d bytes, ~%.0f tokens (%s)" % (
            section["source"], size, est, section["path"]))
        largest = section.get("largest")
        if largest:
            lines.append("  largest command: %s, %d bytes" % (largest["name"], largest["bytes"]))
    return "\n".join(lines)


def _load_json(path: Path):
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("harness-cost: error: %s" % exc, file=sys.stderr)
        return None
    if not isinstance(doc, dict):
        print("harness-cost: error: %s is not a JSON object" % path, file=sys.stderr)
        return None
    return doc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    baseline = sub.add_parser("baseline", help="summarize a pipeline-baseline JSON file")
    baseline.add_argument("path")
    baseline.add_argument("--format", choices=("text", "json"), default="text")

    static = sub.add_parser("static", help="measure the always-loaded prefix in bytes")
    static.add_argument("--root", default=".")
    static.add_argument("--chars-per-token", type=float, default=4.0)
    static.add_argument("--format", choices=("text", "json"), default="text")

    args = parser.parse_args(argv)
    if args.cmd == "baseline":
        doc = _load_json(Path(args.path))
        if doc is None:
            return 2
        summary = summarize_baseline(doc)
        if args.format == "json":
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(format_baseline(summary))
        return 0
    report = static_sections(Path(args.root), args.chars_per_token)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_static(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
