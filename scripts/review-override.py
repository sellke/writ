#!/usr/bin/env python3
"""Gate 3 review override (Story 1 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Re-derives a mechanical PASS/FAIL from `ac-trace.py` and (when path flags
are present) `test-integrity.py`. Does not judge architecture, security, or
taste — those stay with `review-agent`. A mechanical pass never washes out
an agent FAIL or PAUSE; this script only reports the measurement.

Subcommand:
  check --spec PATH --repo . [--story PATH] [--new-files FILE …] [--tests FILE …]
  `--project` is accepted as an alias of `--repo`.

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason: <code>` lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple


STORY_FILENAME = re.compile(r"story-(\d+)-")
COMPLETED = re.compile(r"Completed", re.IGNORECASE)

BLOCKING_AC = frozenset({
    "untasked_criterion",
    "untested_criterion",
    "dangling_reference",
    "duplicate_id",
})
BLOCKING_INTEGRITY = frozenset({
    "coverage_below_threshold",
    "coverage_regression",
    "test_imports_no_source",
})

HELPER_DIR = Path(__file__).resolve().parent


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


def _story_number(story: Path) -> Optional[int]:
    match = STORY_FILENAME.search(story.name)
    if match:
        return int(match.group(1))
    return None


def _story_completed(story: Path) -> bool:
    try:
        text = story.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    for line in text.splitlines()[:15]:
        if line.startswith("> **Status:**") and COMPLETED.search(line):
            return True
    return False


def _run_helper(script: Path, argv: List[str]) -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *argv],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def _load_json(stdout: str) -> Optional[dict]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _ac_reasons(payload: dict, story_number: int, story_complete: bool) -> List[str]:
    reasons: List[str] = []
    for finding in payload.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        if finding.get("story") != story_number:
            continue
        code = finding.get("code")
        if code not in BLOCKING_AC:
            continue
        if finding.get("severity") and finding.get("severity") != "blocking":
            continue
        if code == "untested_criterion" and not story_complete:
            continue
        reasons.append(str(code))
    return reasons


def _integrity_codes(payload: dict) -> Tuple[str, List[str]]:
    verdict = str(payload.get("verdict") or "")
    codes: List[str] = []
    for finding in payload.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        code = finding.get("code")
        if code in BLOCKING_INTEGRITY:
            codes.append(str(code))
    if verdict == "unverifiable" or payload.get("unverifiable"):
        extra: List[str] = []
        for item in payload.get("unverifiable") or []:
            if isinstance(item, dict) and item.get("reason"):
                extra.append(str(item["reason"]))
        return "unverifiable", extra or ["helper_unverifiable"]
    if codes or verdict == "fail":
        return "fail", codes or ["integrity_fail"]
    return "pass", []


def check(spec: Optional[Path], repo: Path, story: Optional[Path],
          new_files: Optional[List[str]], tests: Optional[List[str]]) -> int:
    if spec is None:
        return _emit("unverifiable", ["missing_spec"],
                     "review-override: unverifiable (missing --spec)")
    if story is None:
        return _emit("unverifiable", ["missing_story"],
                     "review-override: unverifiable (missing --story)")

    story_number = _story_number(story)
    if story_number is None:
        return _emit("unverifiable", ["unparseable_story"],
                     "review-override: unverifiable (story filename has no number)")

    ac_script = HELPER_DIR / "ac-trace.py"
    if not ac_script.is_file():
        return _emit("unverifiable", ["helper_missing"],
                     "review-override: unverifiable (ac-trace.py missing)")

    rc, stdout = _run_helper(ac_script, [
        "check", "--spec", str(spec), "--repo", str(repo),
    ])
    payload = _load_json(stdout)
    if payload is None or rc == 2 or payload.get("error"):
        return _emit("unverifiable", ["helper_unverifiable"],
                     "review-override: unverifiable (ac-trace.py could not answer)")

    ac_fail = _ac_reasons(payload, story_number, _story_completed(story))
    if ac_fail:
        return _emit("fail", ac_fail,
                     "review-override: fail (ac-trace blocking finding on story %d)"
                     % story_number)

    if new_files or tests:
        integrity = HELPER_DIR / "test-integrity.py"
        if not integrity.is_file():
            return _emit("unverifiable", ["helper_missing"],
                         "review-override: unverifiable (test-integrity.py missing)")
        if new_files:
            argv = ["coverage", "--project", str(repo), "--new-files", *new_files]
            rc, stdout = _run_helper(integrity, argv)
            payload = _load_json(stdout)
            if payload is None or rc == 2 or payload.get("error"):
                return _emit("unverifiable", ["helper_unverifiable"],
                             "review-override: unverifiable (test-integrity coverage)")
            kind, codes = _integrity_codes(payload)
            if kind == "fail":
                return _emit("fail", codes,
                             "review-override: fail (test-integrity coverage)")
            if kind == "unverifiable":
                return _emit("unverifiable", codes,
                             "review-override: unverifiable (test-integrity coverage)")
        if tests:
            argv = ["authenticity", "--project", str(repo), "--tests", *tests]
            rc, stdout = _run_helper(integrity, argv)
            payload = _load_json(stdout)
            if payload is None or rc == 2 or payload.get("error"):
                return _emit("unverifiable", ["helper_unverifiable"],
                             "review-override: unverifiable (test-integrity authenticity)")
            kind, codes = _integrity_codes(payload)
            if kind == "fail":
                return _emit("fail", codes,
                             "review-override: fail (test-integrity authenticity)")
            if kind == "unverifiable":
                return _emit("unverifiable", codes,
                             "review-override: unverifiable (test-integrity authenticity)")

    return _emit("pass", [], "review-override: pass (no blocking helper finding)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="re-derive Gate 3 from ac-trace + test-integrity")
    p.add_argument("--spec", type=Path, default=None)
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--story", type=Path, default=None)
    p.add_argument("--new-files", nargs="+", default=None)
    p.add_argument("--tests", nargs="+", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    return check(args.spec, args.repo, args.story, args.new_files, args.tests)


if __name__ == "__main__":
    sys.exit(main())
