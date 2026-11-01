#!/usr/bin/env python3
"""Gate 3.5 drift-log format check (Story 5 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Checks that every `DEV-NNN` entry matches
`.writ/docs/drift-report-format.md` required fields, and that a
Large-drift signal (`Overall Drift: Large` or `- **Severity:** Large`)
implies a PAUSE verdict line (`REVIEW_RESULT: PAUSE` /
`EVALUATION_RESULT: PAUSE`) in the story or `--review-output`. Does not decide accept / reject / modify-spec.

`summary` (Story 4 of `2026-09-26-drift-arch-guards`) rolls a drift log up
for the `/implement-spec` Step 4.2 report: it counts DEV entries by
`- **Severity:**` across `## Story N:` sections (with `--since`, only
sections whose `> Run:` date is on or after the date; undated sections are
then dropped), lists each Medium / Large entry as
`medium:` / `large: DEV-NNN <title> (Story N)` in file order, and never
emits `fail` — the roll-up is report-only.

Subcommands:
  check --story PATH [--drift-log PATH] [--review-output PATH]
  summary --drift-log PATH [--since YYYY-MM-DD]

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` (or `summary` headline) lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail` (`check` only).
Exit 2: usage, including a `--since` that is not a YYYY-MM-DD date.
"""

from __future__ import annotations

import argparse
import datetime
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
# Large drift, per `.writ/docs/drift-report-format.md` and the
# review/evaluator `### Drift Analysis` block: an `Overall Drift:` line
# (plain `> Overall Drift: Large` or bold `**Overall Drift:** Large`, with or
# without the `> ` quote) or a per-entry `- **Severity:** Large` field.
# A DEV heading title is free text and is not a severity signal.
LARGE_SIGNAL = re.compile(
    r"(?m)^(?:> )?(?:\*\*Overall Drift:\*\*|Overall Drift:)[ \t]*Large\b"
    r"|^- \*\*Severity:\*\*[ \t]*Large\b"
)
# A PAUSE verdict is the gate-decision line the review / evaluator agent
# emits (`agents/review-agent.md` `### REVIEW_RESULT: PAUSE`,
# `agents/evaluator-agent.md` `### EVALUATION_RESULT: PAUSE`), optionally
# bolded or without the heading marks. The word PAUSE in prose, or the
# `[PASS/FAIL/PAUSE]` template, is not a verdict.
PAUSE_VERDICT = re.compile(
    r"(?m)^(?:#{1,6}[ \t]+)?(?:\*\*)?(?:REVIEW_RESULT|EVALUATION_RESULT)"
    r"(?::\*\*|\*\*:|:)[ \t]*(?:\*\*)?PAUSE(?:\*\*)?[ \t]*$"
)
STORY_HEADING = re.compile(r"^## Story (\d+):", re.MULTILINE)
RUN_DATE = re.compile(r"^> Run:[ \t]*(\d{4}-\d{2}-\d{2})\b", re.MULTILINE)
DEV_TITLE = re.compile(r"^#### \[DEV-\d{3}\][ \t]+(.+?)[ \t]*$", re.MULTILINE)
SEVERITY = re.compile(r"^- \*\*Severity:\*\*[ \t]*(Small|Medium|Large)\b",
                      re.MULTILINE)
SINCE_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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

    large = any(
        LARGE_SIGNAL.search(text)
        for text in (log_text or "", story_text, review_text or "")
    )

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

    if large and not PAUSE_VERDICT.search(pause_haystack):
        reasons.append("large_drift_without_pause")

    if reasons:
        return _emit("fail", reasons, "drift-format: fail (format or PAUSE)")

    return _emit("pass", [], "drift-format: pass (entries well-formed)")


def _story_sections(text: str) -> List[Tuple[str, str]]:
    """(story number, section text) per `## Story N:` heading, each section
    ending at the next story heading or `---` rule."""
    matches = list(STORY_HEADING.finditer(text))
    out: List[Tuple[str, str]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = re.split(r"(?m)^---[ \t]*$", text[match.start():end], maxsplit=1)[0]
        out.append((match.group(1), section))
    return out


def summary(drift_log: Path, since: Optional[str]) -> int:
    suffix = " since %s" % since if since else ""
    if not drift_log.exists():
        text = ""
    else:
        text = _read(drift_log)
        if text is None:
            return _emit("unverifiable", ["drift_log_unreadable"],
                         "drift-format summary: unverifiable (drift log unreadable)")

    counts = {"Small": 0, "Medium": 0, "Large": 0}
    headlines: List[str] = []
    for story, section in _story_sections(text):
        run = RUN_DATE.search(section)
        if since and (run is None or run.group(1) < since):
            continue
        for num, block in _entries(section):
            severity = SEVERITY.search(block)
            if severity is None:
                continue
            level = severity.group(1)
            counts[level] += 1
            if level != "Small":
                title = DEV_TITLE.search(block)
                headlines.append("%s: DEV-%s %s (Story %s)" % (
                    level.lower(), num, title.group(1) if title else "", story))

    print("pass")
    for line in headlines:
        print(line)
    print("drift-format summary: %d small, %d medium, %d large%s" % (
        counts["Small"], counts["Medium"], counts["Large"], suffix))
    return 0


def _valid_since(value: Optional[str]) -> bool:
    if value is None:
        return True
    if not SINCE_FORMAT.match(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="format-check a drift log / Large-drift PAUSE")
    p.add_argument("--story", type=Path, required=True)
    p.add_argument("--drift-log", type=Path, default=None)
    p.add_argument("--review-output", type=Path, default=None)
    s = sub.add_parser("summary", help="roll up drift counts and Medium/Large headlines")
    s.add_argument("--drift-log", type=Path, required=True)
    s.add_argument("--since", default=None, metavar="YYYY-MM-DD")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if args.action == "summary":
        if not _valid_since(args.since):
            print("error: --since must be a YYYY-MM-DD date", file=sys.stderr)
            return 2
        return summary(args.drift_log, args.since)
    if args.action != "check":
        return 2
    rc = check(args.story, args.drift_log, args.review_output)
    if rc == 2:
        print("error: --story is required and must be readable", file=sys.stderr)
    # Never print accept / reject / modify-spec as a verdict.
    return rc


if __name__ == "__main__":
    sys.exit(main())
