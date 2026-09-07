#!/usr/bin/env python3
"""Verdict provenance check for a Writ command's Step 3 gates (Story 4 of
2026-09-07-phase11-stage2-prune-the-base).

Every `#### Gate N` heading in `commands/implement-story.md` must have an
entry in the frontmatter `gates:` list naming where its verdict comes from —
a `script:` path that re-derives it, or `verification: prose-only` when the
gate still runs on the agent's own say-so. This script reads both sides and
reports where they drift apart, so the count of honor-system gates is a
checked number rather than an impression.

Subcommand:
  check --command PATH [--repo .] [--max-prose-only 2] [--prose-only-blocking]

Output, one line each: findings as `<code>: <detail>`; the prose-only count
as `note: prose_only_count: <n> (cap <max>)`, or as the finding
`prose_only_count: <n> (cap <max>)` when `--prose-only-blocking` is passed
and the count exceeds the cap; then the summary line, always last.

Finding codes: heading_without_entry, entry_without_heading,
entry_without_source, entry_both_sources, script_missing,
unknown_verification_value.

Exit codes: 0 no findings · 1 findings · 2 usage (missing file, no
frontmatter fence, a `gates:` entry with no `id`).

No YAML library: the frontmatter reader is a minimal stdlib line parser that
understands only the `gates:` list's fixed shape (`- id:` plus `script:` or
`verification:`), not general YAML. Python 3.9 floor.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Fixed heading -> id table. The ids for 0, 2, 3, 4, 5 match
# pipeline-baseline.py's GATE_NAMES so a later join is free.
HEADING_TO_ID: Dict[str, str] = {
    "0": "gate0_arch",
    "0.5": "gate0_5_boundary",
    "1": "gate1_coding",
    "2": "gate2_build",
    "2.5": "gate2_5_surface",
    "3": "gate3_review",
    "3.5": "gate3_5_drift",
    "4": "gate4_tests",
    "4.5": "gate4_5_visual",
    "5": "gate5_docs",
}

PROSE_ONLY = "prose-only"
DEFAULT_MAX_PROSE_ONLY = 2

FINDING_CODES = (
    "heading_without_entry",
    "entry_without_heading",
    "entry_without_source",
    "entry_both_sources",
    "script_missing",
    "unknown_verification_value",
)

_HEADING = re.compile(r"^#### Gate (\d+(?:\.\d+)?)\b")
_LIST_ITEM = re.compile(r"^(\s*)- (.*)$")
_KEY_VALUE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


class ParseError(Exception):
    """A usage-class defect in the command file (exit 2)."""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def split_frontmatter(text: str) -> Tuple[List[str], str]:
    """Return (frontmatter lines, body text). Raises ParseError without a fence."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ParseError("file does not open with a --- frontmatter fence")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    raise ParseError("frontmatter fence is never closed")


def _scalar(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def parse_gates(text: str) -> List[Dict[str, str]]:
    """Read the frontmatter `gates:` list of {id, script?, verification?}.

    Returns [] when the key is absent. Raises ParseError when an entry has no
    `id` — that is a malformed block, not a drift finding.
    """
    fm, _ = split_frontmatter(text)
    gates: List[Dict[str, str]] = []
    in_block = False
    current: Optional[Dict[str, str]] = None
    for line in fm:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if not in_block:
            if indent == 0 and re.match(r"^gates:\s*$", line):
                in_block = True
            continue
        if indent == 0:
            break  # next top-level key
        item = _LIST_ITEM.match(line)
        if item:
            if current is not None:
                gates.append(current)
            current = {}
            rest = item.group(2).strip()
            if rest:
                kv = _KEY_VALUE.match(rest)
                if kv is None:
                    raise ParseError("gates: entry %r is not a key: value pair" % rest)
                current[kv.group(2)] = _scalar(kv.group(3))
            continue
        kv = _KEY_VALUE.match(line)
        if kv is None or current is None:
            raise ParseError("gates: line %r is not a key: value pair inside an entry" % line.strip())
        current[kv.group(2)] = _scalar(kv.group(3))
    if current is not None:
        gates.append(current)
    for i, gate in enumerate(gates):
        if not gate.get("id"):
            raise ParseError("gates: entry %d has no id" % (i + 1))
    return gates


def parse_headings(text: str) -> List[str]:
    """Map each body `#### Gate N` heading to its id, in document order.

    A heading whose number is not in HEADING_TO_ID is returned as
    `gate?<N>` so the caller can report it as heading_without_entry.
    """
    _, body = split_frontmatter(text)
    ids: List[str] = []
    for line in body.split("\n"):
        m = _HEADING.match(line)
        if m:
            ids.append(HEADING_TO_ID.get(m.group(1), "gate?%s" % m.group(1)))
    return ids


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def _fail(message: str, code: int = 2) -> None:
    print("check: error: %s" % message, file=sys.stderr)
    sys.exit(code)


def run_check(command: Path, repo: Path, max_prose_only: int,
              prose_only_blocking: bool, label: str) -> Tuple[List[str], List[str], str]:
    """Return (finding lines, note lines, summary line)."""
    text = command.read_text(encoding="utf-8")
    gates = parse_gates(text)
    headings = parse_headings(text)

    findings: List[str] = []
    notes: List[str] = []
    entry_ids = [g["id"] for g in gates]
    heading_set = set(headings)
    entry_set = set(entry_ids)

    for hid in headings:
        if hid not in entry_set:
            findings.append("heading_without_entry: %s %s (#### Gate heading has no gates: entry)"
                            % (label, hid))
    for gate in gates:
        gid = gate["id"]
        if gid not in heading_set:
            findings.append("entry_without_heading: %s %s (gates: entry has no #### Gate heading)"
                            % (label, gid))
        has_script = "script" in gate
        has_verification = "verification" in gate
        if not has_script and not has_verification:
            findings.append("entry_without_source: %s %s (neither script nor verification)"
                            % (label, gid))
        if has_script and has_verification:
            findings.append("entry_both_sources: %s %s (both script and verification)"
                            % (label, gid))
        if has_script:
            path = repo / gate["script"]
            if not path.is_file():
                findings.append("script_missing: %s %s (%s not found under %s)"
                                % (label, gid, gate["script"], repo))
        if has_verification and gate["verification"] != PROSE_ONLY:
            findings.append("unknown_verification_value: %s %s (%r is not %r)"
                            % (label, gid, gate["verification"], PROSE_ONLY))

    script_count = sum(1 for g in gates if "script" in g)
    prose_count = sum(1 for g in gates if g.get("verification") == PROSE_ONLY)
    count_line = "prose_only_count: %d (cap %d)" % (prose_count, max_prose_only)
    if prose_only_blocking and prose_count > max_prose_only:
        findings.append(count_line)
    else:
        notes.append("note: " + count_line)

    summary = ("gates: %d entries, headings: %d, script: %d, prose-only: %d, findings: %d"
               % (len(gates), len(headings), script_count, prose_count, len(findings)))
    return findings, notes, summary


def cmd_check(args: argparse.Namespace) -> None:
    command = Path(args.command).expanduser()
    repo = Path(args.repo).expanduser()
    if not command.is_file():
        _fail("--command %s does not exist" % command)
    if not repo.is_dir():
        _fail("--repo %s is not a directory" % repo)
    try:
        label = str(command.resolve().relative_to(repo.resolve()))
    except ValueError:
        label = str(command)
    try:
        findings, notes, summary = run_check(command, repo, args.max_prose_only,
                                             args.prose_only_blocking, label)
    except ParseError as exc:
        _fail("%s: %s" % (label, exc))
        return
    for line in findings:
        print(line)
    for line in notes:
        print(line)
    print(summary)
    sys.exit(1 if findings else 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verdict-provenance.py",
        description="Check that every #### Gate heading declares its verdict source in frontmatter.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    chk = sub.add_parser("check", help="compare gates: frontmatter entries with #### Gate headings")
    chk.add_argument("--command", required=True, help="command file to check (commands/implement-story.md)")
    chk.add_argument("--repo", default=".", help="repository root that script: paths resolve against (default: .)")
    chk.add_argument("--max-prose-only", type=int, default=DEFAULT_MAX_PROSE_ONLY,
                     help="cap on verification: prose-only entries (default: %(default)s)")
    chk.add_argument("--prose-only-blocking", action="store_true",
                     help="make a prose-only count over the cap a finding instead of a note")
    chk.set_defaults(func=cmd_check)
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
