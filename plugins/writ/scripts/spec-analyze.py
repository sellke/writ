#!/usr/bin/env python3
"""Acceptance-criteria analysis (Story 1 of
`2026-09-08-phase11-stage3-spec-analysis`).

Deterministic structural findings plus schema-check of an optional
orchestrator `--findings` JSON. Does not call an LLM API. Does not
import ac-trace parsers. Does not decide accept / reject / modify-spec.

Subcommand:
  check --spec PATH [--findings FILE] [--repo .]

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` lines, then a summary line last.

Structural reasons: `under_min_criteria`, `empty_criterion`,
`unmeasurable_criterion`, and `planned_red_window` (a story plans a check
to fail or go stale until a later story).

Exit 0: ran, no blocking helper defect (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple


SEMANTIC_CODES = frozenset(("contradiction", "gap", "ambiguity"))
AC_ID = re.compile(r"^AC-\d+\.\d+$")
CRITERION = re.compile(r"^- \[[ xX]\]\s+(.*)$")
THEN_SPLIT = re.compile(r",\s*then\s+", re.IGNORECASE)
TAG_TAIL = re.compile(r"\s*`\[AC-\d+\.\d+(?:,\s*AC-\d+\.\d+)*\]`\s*$")
VAGUE_THEN = frozenset((
    "works correctly",
    "it works correctly",
    "as expected",
    "it works as expected",
    "looks good",
    "it looks good",
))

# planned_red_window: a story plans a check to fail or go stale until a
# later story, so the commits between them are red (Phase 15 retro F3). Only
# the plan is read; from `## What Was Built` on, the file records what ran.
STORY_NUMBER = re.compile(r"^story-(\d+)-")
RECORD_HEADING = re.compile(r"^##\s+What Was Built\b")
UNIT_START = re.compile(r"^\s*(?:[-*+>]|\d+\.|#)")
SENTENCE_END = re.compile(r"[.!?;]\**\s+")
RED_WORD = re.compile(r"\b(?<!not )(?<!never )(?<!n't )(?:fail\w*|stale)\b", re.IGNORECASE)
LATER_STORY = re.compile(r"\b(?:until|between this story and)\s+story\s+(\d+)\b", re.IGNORECASE)


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


def _story_files(spec: Path) -> Optional[List[Path]]:
    stories = spec / "user-stories"
    if not spec.is_dir() or not stories.is_dir():
        return None
    files = sorted(stories.glob("story-*.md"))
    if not files:
        return None
    return files


def _criteria(text: str) -> List[str]:
    out: List[str] = []
    for line in text.splitlines():
        match = CRITERION.match(line)
        if not match:
            continue
        body = match.group(1).strip()
        if body.lower().startswith("given"):
            out.append(body)
    return out


def _then_clause(body: str) -> str:
    stripped = TAG_TAIL.sub("", body).strip()
    parts = THEN_SPLIT.split(stripped, maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip().rstrip(".").strip().lower()


def _planned_red_window(path: Path, text: str) -> bool:
    """True when a sentence in the story's plan names a failing or stale
    check and a later story that clears it."""
    match = STORY_NUMBER.match(path.name)
    if not match:
        return False
    own = int(match.group(1))
    units: List[str] = []
    for line in text.splitlines():
        if RECORD_HEADING.match(line):
            break
        if not units or not line.strip() or UNIT_START.match(line):
            units.append(line.strip())
        else:
            units[-1] += " " + line.strip()
    for unit in units:
        for sentence in SENTENCE_END.split(unit):
            if not RED_WORD.search(sentence):
                continue
            if any(int(m.group(1)) > own for m in LATER_STORY.finditer(sentence)):
                return True
    return False


def _structural(spec: Path) -> Tuple[Optional[List[str]], Optional[str]]:
    files = _story_files(spec)
    if files is None:
        return None, "spec_unreadable"
    reasons: List[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None, "spec_unreadable"
        bodies = _criteria(text)
        if len(bodies) < 3:
            reasons.append("under_min_criteria")
        for body in bodies:
            rest = body[5:].strip() if body.lower().startswith("given") else body
            if rest == "":
                reasons.append("empty_criterion")
                continue
            then = _then_clause(body)
            if then in VAGUE_THEN:
                reasons.append("unmeasurable_criterion")
        if _planned_red_window(path, text):
            reasons.append("planned_red_window")
    # Stable unique order.
    seen = set()
    ordered: List[str] = []
    for code in reasons:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered, None


def _schema_check(raw: str) -> Optional[str]:
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return "malformed_findings"
    if not isinstance(data, list):
        return "malformed_findings"
    for item in data:
        if not isinstance(item, dict):
            return "malformed_findings"
        code = item.get("code")
        story = item.get("story")
        summary = item.get("summary")
        if code not in SEMANTIC_CODES:
            return "malformed_findings"
        if not isinstance(story, str) or not story.strip():
            return "malformed_findings"
        if not isinstance(summary, str) or not summary.strip():
            return "malformed_findings"
        ac_ids = item.get("ac_ids")
        if ac_ids is None:
            continue
        if not isinstance(ac_ids, list):
            return "malformed_findings"
        for ac_id in ac_ids:
            if not isinstance(ac_id, str) or not AC_ID.match(ac_id):
                return "malformed_findings"
    return None


def check(spec: Optional[Path], findings: Optional[Path]) -> int:
    if spec is None:
        return _emit("unverifiable", ["missing_spec"],
                     "spec-analyze: unverifiable (no --spec)")

    structural, unread = _structural(spec)
    if unread:
        return _emit("unverifiable", [unread],
                     "spec-analyze: unverifiable (spec unreadable)")

    reasons: List[str] = list(structural or [])

    if findings is not None:
        try:
            raw = findings.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            reasons.append("malformed_findings")
        else:
            schema = _schema_check(raw)
            if schema:
                reasons.append(schema)

    if reasons:
        return _emit("fail", reasons, "spec-analyze: fail (structural or schema)")

    if findings is None:
        return _emit(
            "unverifiable",
            ["no_findings"],
            "spec-analyze: unverifiable (no --findings and no structural hit)",
        )

    return _emit("pass", [], "spec-analyze: pass (no structural hit; findings well-formed)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="analyze story acceptance criteria")
    p.add_argument("--spec", type=Path, default=None)
    p.add_argument("--findings", type=Path, default=None)
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if getattr(args, "action", None) != "check":
        return 2
    return check(args.spec, args.findings)


if __name__ == "__main__":
    sys.exit(main())
