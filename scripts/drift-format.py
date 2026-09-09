#!/usr/bin/env python3
"""Gate 3.5 drift-log format check (Story 5 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Checks that every `DEV-NNN` entry matches
`.writ/docs/drift-report-format.md` required fields, and that a
Large-drift heading implies a PAUSE token in the story or
`--review-output`. Does not decide accept / reject / modify-spec.

Subcommand:
  check --story PATH [--drift-log PATH] [--review-output PATH]

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


DEV_HEADING = re.compile(r"^#### \[DEV-(\d{3})\]\s+\S", re.MULTILINE)
REQUIRED_FIELDS = (
    "Severity",
    "Spec said",
    "Implementation did",
    "Reason",
    "Resolution",
    "Spec amendment",
)
FIELD_LINE = re.compile(
    r"^- \*\*(%s):\*\* .+\S" % "|".join(re.escape(f) for f in REQUIRED_FIELDS),
    re.MULTILINE,
)
LARGE_HEADING = re.compile(
    r"(?im)^(> \*\*Overall Drift:\*\* Large|\*\*Severity:\*\* Large|#### \[DEV-\d{3}\].*Large)"
)
PAUSE_TOKEN = re.compile(r"\bPAUSE\b")


class UsageError(Exception):
    """Exit-2 conditions."""


def _emit(verdict: str, reasons: Sequence[str], summary: str) -> int:
    print(verdict)
    for reason in reasons:
        print("reason: %s" % reason)
    print(summary)
    if verdict == "fail":
        return 1
    return 0


def _read(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _entries(text: str) -> List[Tuple[str, str]]:
    matches = list(DEV_HEADING.finditer(text))
    out: List[Tuple[str, str]] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((match.group(1), text[start:end]))
    return out


def _missing_fields(block: str) -> List[str]:
    present = {m.group(1) for m in FIELD_LINE.finditer(block)}
    return [name for name in REQUIRED_FIELDS if name not in present]


def check(story: Optional[Path], drift_log: Optional[Path],
          review_output: Optional[Path]) -> int:
    if story is None:
        return 2

    story_text = _read(story)
    if story_text is None:
        return _emit("unverifiable", ["story_unreadable"],
                     "drift-format: unverifiable (story unreadable)")

    log_text = _read(drift_log) if drift_log is not None else None
    if drift_log is not None and log_text is None:
        return _emit("unverifiable", ["drift_log_unreadable"],
                     "drift-format: unverifiable (drift log unreadable)")

    review_text = _read(review_output) if review_output is not None else ""
    pause_haystack = "%s\n%s" % (story_text, review_text or "")

    large = False
    if log_text:
        large = bool(LARGE_HEADING.search(log_text))
    large = large or bool(re.search(r"(?im)^> \*\*Overall Drift:\*\* Large", story_text))
    large = large or bool(re.search(r"(?im)^### Drift Analysis[\s\S]*Large", story_text))

    if not log_text and not large:
        return _emit(
            "unverifiable",
            ["no_drift_signal"],
            "drift-format: unverifiable (no drift log and no Large-drift heading)",
        )

    reasons: List[str] = []
    if log_text:
        entries = _entries(log_text)
        if not entries and "DEV-" in log_text:
            reasons.append("malformed_entry")
        for _num, block in entries:
            missing = _missing_fields(block)
            if missing:
                reasons.append("malformed_entry")
                break

    if large and not PAUSE_TOKEN.search(pause_haystack):
        reasons.append("large_drift_without_pause")

    if reasons:
        return _emit("fail", reasons, "drift-format: fail (format or PAUSE)")

    return _emit("pass", [], "drift-format: pass (entries well-formed)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="format-check a drift log / Large-drift PAUSE")
    p.add_argument("--story", type=Path, required=True)
    p.add_argument("--drift-log", type=Path, default=None)
    p.add_argument("--review-output", type=Path, default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if args.action != "check":
        return 2
    rc = check(args.story, args.drift_log, args.review_output)
    if rc == 2:
        print("error: --story is required and must be readable", file=sys.stderr)
    # Never print accept / reject / modify-spec as a verdict.
    return rc


if __name__ == "__main__":
    sys.exit(main())
