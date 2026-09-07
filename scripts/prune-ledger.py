#!/usr/bin/env python3
"""Ledger check for lines pruned from Writ's shared base (Story 1 of
2026-09-07-phase11-stage2-prune-the-base, ADR-026).

`check` diffs the two base files (`system-instructions.md`,
`commands/_preamble.md`) in the working tree against a pinned base commit and
requires every removed line to have a row in
`.writ/decision-records/pruned-instructions-ledger.md` with identical text and
file. It also flags a ledger row whose text is back in the file it was cut
from — the stall signal the Goal Card counts — and reports the base byte
total against a cap.

Removed lines come only from `git diff --no-color -U0 <base-commit> --
<file>`; this module never re-implements diff. Line texts are compared byte
for byte with no whitespace normalization: a kept line that gets reflowed
reads as a removal without a row, which is the intended failure (Business
Rule 5). Two counting rules keep the check satisfiable:

  * A pure move within one file is not a removal: removed and added texts are
    compared as multisets per file, and matching pairs cancel. A line moved
    between the two base files is a removal in one and an addition in the
    other.
  * Whitespace-only lines need no row: a blank line carries no instruction,
    and a row for one would read as re-added wherever another blank line
    exists.

A ledger row has "reappeared" when its text is a whole line in its file at
the working tree *and* is not among that file's net removals — so a row for
one of two identical lines is honored while the other copy stays.

`measure` prints bytes per `##` / `###` section of both base files so the
maintainer can see where the bytes are before cutting.

Findings print one per line to stdout as `<code>: <detail>`; notes print as
`note: <code>: <detail>`; the summary line is always last:
`base: <bytes> bytes (cap <cap>), ledger: <rows> rows, removed: <n>,
re-added: <n>`.

Exit codes: 0 no findings · 1 findings · 2 usage or git failure (git's own
stderr is relayed; nothing is fabricated).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BASE_FILES = ("system-instructions.md", "commands/_preamble.md")
LEDGER = ".writ/decision-records/pruned-instructions-ledger.md"
DEFAULT_BASE_COMMIT = "cf84742"
DEFAULT_CAP = 10000
# Story 3 appends this line to the ledger when the cap is reached; eval.sh
# passes --cap-blocking when it is present.
CAP_BLOCKING_MARKER = "<!-- cap: blocking -->"
CLASSES = ("moved", "behavior-request", "duplicate")

ROW_RE = re.compile(
    r"^\| (\d{4}-\d{2}-\d{2}) \| ([^|]+) \| (moved|behavior-request|duplicate) \| ([^|]*) \| (.*) \|$"
)
HEADER_ROW = "| Date | File | Class | Reason | Text |"
SEPARATOR_RE = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")
HEADING_RE = re.compile(r"^#{2,3} ")


class GitError(Exception):
    """`git diff` failed; `stderr` carries git's own message."""

    def __init__(self, stderr: str) -> None:
        super().__init__(stderr)
        self.stderr = stderr


@dataclass
class Row:
    line_no: int
    date: str
    file: str
    cls: str
    reason: str
    text: str


@dataclass
class CheckResult:
    findings: list
    notes: list
    summary: str

    @property
    def exit_code(self) -> int:
        return 1 if self.findings else 0


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


def escape_pipes(text: str) -> str:
    return text.replace("|", "\\|")


def unescape_pipes(text: str) -> str:
    return text.replace("\\|", "|")


def parse_ledger(text: str, path: str = LEDGER):
    """Return (rows, malformed_findings). Header and separator rows are
    skipped; any other line starting with `|` that fails ROW_RE is a
    `malformed_row` finding naming the ledger line number."""
    rows = []
    findings = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        if not line.startswith("|"):
            continue
        if line == HEADER_ROW or SEPARATOR_RE.match(line):
            continue
        match = ROW_RE.match(line)
        if match is None:
            findings.append("malformed_row: %s:%d: %s" % (path, line_no, line))
            continue
        date, file, cls, reason, raw_text = match.groups()
        rows.append(Row(line_no, date, file.strip(), cls, reason.strip(), unescape_pipes(raw_text)))
    return rows, findings


def load_ledger(repo: Path):
    """Return (rows, malformed_findings, present)."""
    path = repo / LEDGER
    if not path.is_file():
        return [], [], False
    rows, findings = parse_ledger(path.read_text(encoding="utf-8"))
    return rows, findings, True


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------


def parse_diff(diff: str):
    """Multisets of removed and added line texts from a `-U0` unified diff.

    Prefix classification starts only after the first `@@` hunk header, so a
    removed `---` line (rendered `----`) is not confused with the `--- a/…`
    file header."""
    removed: Counter = Counter()
    added: Counter = Counter()
    in_hunk = False
    for line in diff.split("\n"):
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("diff --git"):
            in_hunk = False
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("-"):
            removed[line[1:]] += 1
        elif line.startswith("+"):
            added[line[1:]] += 1
    return removed, added


def git_diff(repo: Path, base_commit: str, rel: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "diff", "--no-color", "-U0", base_commit, "--", rel],
        capture_output=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise GitError(proc.stderr)
    return proc.stdout


def net_removals(repo: Path, base_commit: str, rel: str) -> Counter:
    """Removed-line multiset for one file after cancelling in-file moves and
    dropping whitespace-only lines."""
    removed, added = parse_diff(git_diff(repo, base_commit, rel))
    net = removed - added
    return Counter({text: n for text, n in net.items() if text.strip()})


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def run_check(repo: Path, base_commit: str, cap: int, cap_blocking: bool) -> CheckResult:
    findings = []
    notes = []

    rows, malformed, present = load_ledger(repo)
    findings.extend(malformed)

    removed_by_file = {}
    total_removed = 0
    for rel in BASE_FILES:
        removed_by_file[rel] = net_removals(repo, base_commit, rel)
        total_removed += sum(removed_by_file[rel].values())

    ledgered = {(r.file, r.text) for r in rows}
    for rel in BASE_FILES:
        for text in sorted(removed_by_file[rel]):
            if (rel, text) not in ledgered:
                findings.append("removed_not_in_ledger: %s: %s" % (rel, text))

    current_lines = {
        rel: set((repo / rel).read_text(encoding="utf-8").split("\n")) for rel in BASE_FILES
    }
    reappeared = 0
    for r in rows:
        if r.file not in current_lines or not r.text.strip():
            continue
        if r.text in current_lines[r.file] and r.text not in removed_by_file[r.file]:
            findings.append("ledger_text_reappeared: %s %s: %s" % (r.date, r.file, r.text))
            reappeared += 1

    total_bytes = sum(os.path.getsize(repo / rel) for rel in BASE_FILES)
    if total_bytes > cap:
        line = "over_cap: %d bytes > cap %d" % (total_bytes, cap)
        if cap_blocking:
            findings.append(line)
        else:
            notes.append("note: " + line)

    if not rows:
        what = "no rows yet" if present else "no ledger file yet"
        notes.append("note: ledger_missing: %s (%s)" % (what, LEDGER))

    summary = "base: %d bytes (cap %d), ledger: %d rows, removed: %d, re-added: %d" % (
        total_bytes, cap, len(rows), total_removed, reappeared,
    )
    return CheckResult(findings, notes, summary)


def _refuse(command: str, message: str, code: int = 2) -> None:
    print("%s: error: %s" % (command, message), file=sys.stderr)
    sys.exit(code)


def _resolve_repo(command: str, arg: str) -> Path:
    repo = Path(arg).expanduser().resolve()
    if not repo.is_dir():
        _refuse(command, "--repo %s is not a directory" % repo)
    for rel in BASE_FILES:
        if not (repo / rel).is_file():
            _refuse(command, "%s is missing under --repo %s" % (rel, repo))
    return repo


def cmd_check(args: argparse.Namespace) -> None:
    repo = _resolve_repo("check", args.repo)
    if args.cap < 0:
        _refuse("check", "--cap must be non-negative")
    try:
        result = run_check(repo, args.base_commit, args.cap, args.cap_blocking)
    except GitError as exc:
        sys.stderr.write(exc.stderr)
        sys.exit(2)
    for line in result.findings:
        print(line)
    for line in result.notes:
        print(line)
    print(result.summary)
    sys.exit(result.exit_code)


# ---------------------------------------------------------------------------
# measure
# ---------------------------------------------------------------------------


def measure_sections(text: str):
    """[(heading, bytes)] for one file; a `##` or `###` heading starts a new
    section, and bytes before the first heading are their own entry."""
    sections = []
    heading = "(before first heading)"
    buf: list = []

    def flush() -> None:
        sections.append((heading, len("".join(buf).encode("utf-8"))))

    for line in text.splitlines(keepends=True):
        if HEADING_RE.match(line):
            flush()
            heading = line.rstrip("\n")
            buf = [line]
        else:
            buf.append(line)
    flush()
    if sections[0] == ("(before first heading)", 0):
        sections.pop(0)
    return sections


def cmd_measure(args: argparse.Namespace) -> None:
    repo = _resolve_repo("measure", args.repo)
    total = 0
    for rel in BASE_FILES:
        text = (repo / rel).read_text(encoding="utf-8")
        size = len(text.encode("utf-8"))
        total += size
        print("%s  %d bytes" % (rel, size))
        for heading, nbytes in measure_sections(text):
            print("%6d  %s" % (nbytes, heading))
        print()
    print("total: %d bytes" % total)
    sys.exit(0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prune-ledger.py",
        description="Account for every line pruned from Writ's shared base (ADR-026).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    chk = sub.add_parser("check", help="every removed base line has a ledger row; no row's text is back")
    chk.add_argument("--repo", required=True, help="repository root holding the base files and the ledger")
    chk.add_argument("--base-commit", default=DEFAULT_BASE_COMMIT,
                     help="commit the base files are diffed against (default: %(default)s)")
    chk.add_argument("--cap", type=int, default=DEFAULT_CAP,
                     help="byte cap for both base files together (default: %(default)s)")
    chk.add_argument("--cap-blocking", action="store_true",
                     help="report over_cap as a finding instead of a note")
    chk.set_defaults(func=cmd_check)

    mea = sub.add_parser("measure", help="print bytes per ## / ### section of both base files")
    mea.add_argument("--repo", required=True, help="repository root holding the base files")
    mea.set_defaults(func=cmd_measure)
    return parser


def main(argv: Optional[list] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
