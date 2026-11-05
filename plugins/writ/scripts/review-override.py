#!/usr/bin/env python3
"""Gate 3 review override (Story 1 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Re-derives a mechanical PASS/FAIL from `ac-trace.py` and (when path flags
are present) `test-integrity.py`. Does not judge architecture, security, or
taste — those stay with `review-agent`. A mechanical pass never washes out
an agent FAIL or PAUSE; this script only reports the measurement.

Subcommands:
  check --spec PATH --repo . [--story PATH] [--new-files FILE …] [--tests FILE …]
  `--project` is accepted as an alias of `--repo`.
  switch --name safety-fact|reviewer-filters|evidence-gate [--repo .]

`check` prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason: <code>` lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.

`switch` (Story 1 of `2026-10-25-review-route-rigor`) resolves one upgrade
switch from `<repo>/.writ/config.md`. The config lines are:
  - **Safety Fact:** off
  - **Reviewer Filters:** off
  - **Evidence Gate:** off
The first matching line anywhere in the file wins. A switch is on by default;
only the value `off` (any case, surrounding whitespace ignored) turns it off.
Line 1 is the state word `on` or `off`, then one `reason:` line, then the
summary `review-override switch: <name> <state> (.writ/config.md)`.
Reasons: `no_config` (file missing or unreadable), `no_config_line`,
`config_off`, `config_on` (value `on` or empty), `malformed_value <value>`
(any other value; the switch stays on). Always exit 0, except usage (2) for
an unknown or missing `--name`.

`safety-fact` (Story 4 of `2026-10-25-review-route-rigor`):
  safety-fact --review-output FILE [--repo .] [--blast-radius FILE] [--tests-output FILE]
reads the review agent's `### Safety Fact` section (heading `##`-`######`
to the next heading; fields Fact, Holds, Rung, Evidence, case-insensitive,
bold optional) and re-derives the measured evidence rung. A rung counts when
it has at least one `- <rung>: <value>` line and every such line checks out
(`claimed` needs only a non-empty Fact). Cited paths resolve against `--repo`;
absolute paths and paths resolving outside it are rejected. The ladder is not
cumulative; measured is the highest accepted rung (`none` if none). Floor:
`traced`. Prints line 1 `pass`/`fail`/`unverifiable`,
`rung: claimed=<c> measured=<m>`, `fact: <fact>`, `reason:` lines in order
(`safety_fact_missing <section|fact|holds|rung>`,
`safety_fact_below_floor <measured>`, `safety_fact_contradicts_verdict`),
then `review-override safety-fact: <verdict> (measured <m>, floor traced)`.
An unreadable review output is `unverifiable` with
`review_output_unreadable`. Exit 0 pass/unverifiable, 1 fail, 2 usage.

`evidence` (Story 2 of `2026-11-04-evidence-gated-review`):
  evidence --review-output FILE [--repo .] [--changed FILE …]
           [--surface gate3|review] [--tests-output FILE] [--checks FILE]
           [--prior MANIFEST] [--manifest-out FILE] [--timeout SECONDS]
decides which Gate 3 FAIL findings carry executed evidence
(skills/evidence-gated-findings/SKILL.md). Issues under `### Issues Found` are
keyed F1..Fn in output order. A Critical or Major issue whose Location is in
`--changed` and that cites an AC ID (or is Category security/architecture) is
evaluated by the kind of its first `**Evidence:**` field: `test` (the fenced
file, run with the config `Test Runner` scoped to it), `recorded` (a failed
`path::test` in `--tests-output`), `check` (a `--checks` command plus
arguments), or `security-path` (two `path:line` citations). Every other issue
is advisory. At most five `test`/`check` runs per call, each under
`--timeout` (default 120) in its own process group. The scoped command is the
`Test Runner` tokens through the runner word (`go test`, `cargo test`,
`vitest run`), then the scoped argument; later flags are dropped. Each run is
bracketed by a git snapshot (status, `diff HEAD` hash, file hashes, HEAD); a change
outside the repro prints `reason: repro_mutated_tree <paths>` first, makes
line 1 `fail`, stops later runs, and restores nothing. Prints line 1
`pass`/`fail`/`unverifiable`, one `finding F<n>: confirmed (...)` /
`advisory (<reason>)` / `advisory (unverifiable <reason>)` line per issue,
`reason:` lines, then `review-override evidence: <verdict> (<c> confirmed,
<a> advisory, <u> unverifiable)`. A run-level `unverifiable` (`switch_off`,
`no_review_output`, `verdict_not_fail <verdict>`, `no_git`,
`runner_not_found`, `no_test_runner`) prints no finding lines. Git runs are
read-only. `--prior` and `--manifest-out` are accepted and do nothing yet.
Exit 0 pass/unverifiable, 1 fail, 2 usage.

`--surface review` (Story 5) reads a `/review` report instead: the Failure
Modes Registry rows, keyed by FM ID, each bound to its `#### FM-NNN` block
under `## Evidence`. Critical and High rows are evaluated; any Category can
confirm; there is no verdict check; `recorded` and `check` are `unverifiable
kind_unavailable`. Line 2 is `evidence-gate: on|off|unverifiable (<reason>)`
for the report header. Each finding line ends `; severity <mapped>`: an
unconfirmed Critical or High row maps to `Medium (unconfirmed)`. A run-level
`unverifiable`, a tree mutation included, prints no finding lines, so every
severity stays as written. A registry row that repeats an FM ID is dropped
with `reason: duplicate_row FM-NNN`.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Set, Tuple


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

CONFIG_REL = ".writ/config.md"
SWITCH_LINES = {
    "safety-fact": re.compile(r"^- \*\*Safety Fact:\*\*[ \t]*(.*)$", re.MULTILINE),
    "reviewer-filters": re.compile(r"^- \*\*Reviewer Filters:\*\*[ \t]*(.*)$", re.MULTILINE),
    # The technical spec's `\s*` would cross a newline and read the next line
    # as the value; `[ \t]*` keeps the match on one line.
    "evidence-gate": re.compile(r"^[ \t]*-[ \t]*\*\*Evidence Gate:\*\*[ \t]*(.*)$", re.MULTILINE),
}


class UsageError(Exception):
    """Exit-2 conditions."""


def _emit(verdict: str, reasons: Sequence[str], summary: str,
          details: Sequence[str] = ()) -> int:
    """Check shape: verdict, detail lines, `reason:` lines, summary last."""
    print(verdict)
    for line in details:
        print(line)
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


def _resolve_switch(name: str, repo: Path) -> Tuple[str, str]:
    """(state, reason) for one switch; never raises on a bad config."""
    try:
        text = (repo / CONFIG_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "on", "no_config"
    match = SWITCH_LINES[name].search(text)
    if match is None:
        return "on", "no_config_line"
    value = match.group(1).strip()
    if value.lower() == "off":
        return "off", "config_off"
    if value == "" or value.lower() == "on":
        return "on", "config_on"
    return "on", "malformed_value %s" % value


def switch(name: str, repo: Path) -> int:
    state, reason = _resolve_switch(name, repo)
    return _emit(state, [reason],
                 "review-override switch: %s %s (%s)" % (name, state, CONFIG_REL))


# ---------------------------------------------------------------------------
# safety-fact (Story 4 of `2026-10-25-review-route-rigor`)
# ---------------------------------------------------------------------------

RUNGS = ("claimed", "read", "traced", "tested", "reproduced")
FLOOR = "traced"
APP_VERIFY_SCHEMA = "app-verify-result-v1"

SAFETY_HEADING = re.compile(r"^#{2,6}\s*Safety Fact\s*$")
ANY_HEADING = re.compile(r"^#{1,6}\s")
# Same pattern review-panel.py uses for the verdict line; first match wins.
VERDICT_LINE = re.compile(r"^#{1,6}\s*(?:EVALUATION_RESULT|REVIEW_RESULT):\s*\**\s*([A-Za-z]+)",
                          re.MULTILINE)
SAFETY_FIELD = re.compile(
    r"^\s*(?:[-*]\s+)?\*{0,2}\s*(fact|holds|rung|evidence)\s*\*{0,2}\s*:\s*\*{0,2}\s*(.*?)\s*$",
    re.IGNORECASE)
EVIDENCE_LINE = re.compile(
    r"^\s*[-*]\s+\*{0,2}`?(read|traced|tested|reproduced)`?\*{0,2}\s*:\s*\*{0,2}\s*(.*?)\s*$",
    re.IGNORECASE)
CITE_LINE = re.compile(r"^(.+):(\d+)(?:-(\d+))?$")
PARAM_ID = re.compile(r"\[[^\]]*\]$")


class SafetySection:
    """Parsed `### Safety Fact` fields; `evidence` maps rung -> first tokens."""

    def __init__(self) -> None:
        self.fields: Dict[str, str] = {}
        self.evidence: Dict[str, List[str]] = {r: [] for r in RUNGS[1:]}


def _parse_safety_section(text: str) -> Optional[SafetySection]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if SAFETY_HEADING.match(line)), None)
    if start is None:
        return None
    section = SafetySection()
    for line in lines[start + 1:]:
        if ANY_HEADING.match(line):
            break
        evidence = EVIDENCE_LINE.match(line)
        if evidence:
            value = evidence.group(2).replace("`", "").strip()
            token = value.split()[0].rstrip(",;") if value else ""
            section.evidence[evidence.group(1).lower()].append(token)
            continue
        field = SAFETY_FIELD.match(line)
        if field:
            section.fields.setdefault(field.group(1).lower(), field.group(2))
    return section


def _word(value: Optional[str]) -> str:
    """Field value without markdown emphasis, lowercased (`Holds`, `Rung`)."""
    return re.sub(r"[`*_]", "", value or "").strip().rstrip(".").strip().lower()


def _inside(repo: Path, cited: str) -> Optional[Path]:
    """The resolved path for a repo-relative citation, or None when it is
    absolute or resolves (through `..` or a symlink) outside `repo`."""
    if not cited or Path(cited).is_absolute():
        return None
    try:
        target = (repo / cited).resolve()
    except (OSError, RuntimeError):
        return None
    if target != repo and repo not in target.parents:
        return None
    return target


def _line_count(path: Path) -> Optional[int]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    count = data.count(b"\n")
    if data and not data.endswith(b"\n"):
        count += 1
    return count


def _read_text(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _cite_ok(repo: Path, token: str) -> Optional[str]:
    """The cited path, normalized, when `path:line` (or `path:start-end`) names
    an existing file inside `repo` and the start line is within it; else None."""
    match = CITE_LINE.match(token)
    if not match:
        return None
    target = _inside(repo, match.group(1))
    if target is None or not target.is_file():
        return None
    try:
        start = int(match.group(2))
    except ValueError:  # 3.11+ int-conversion digit limit: the line is past any EOF
        return None
    count = _line_count(target)
    if count is None or start < 1 or start > count:
        return None
    return posixpath.normpath(match.group(1))


def _consumer_union(blast_radius: Optional[Path]) -> Optional[Set[str]]:
    """Union of `consumers` from a readable `pass` blast radius; None when the
    file is absent, unreadable, malformed, or not `pass`."""
    text = _read_text(blast_radius)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except (ValueError, RecursionError):  # malformed, or nested past the recursion limit
        return None
    if not isinstance(payload, dict) or payload.get("verdict") != "pass":
        return None
    consumers = payload.get("consumers")
    if not isinstance(consumers, dict):
        return None
    union: Set[str] = set()
    for paths in consumers.values():
        if not isinstance(paths, list):
            return None
        union.update(posixpath.normpath(str(p)) for p in paths)
    return union


def _traced_ok(repo: Path, tokens: List[str], union: Optional[Set[str]]) -> bool:
    cites = [t for t in tokens if t.lower().strip(",;:") != "none"]
    if cites:
        found = [_cite_ok(repo, t) for t in cites]
        if any(rel is None for rel in found):
            return False
        if union:
            return any(rel in union for rel in found)
        return True
    if tokens:
        return union is not None and not union
    return False


def _tested_ok(repo: Path, token: str, tests_text: Optional[str]) -> bool:
    if tests_text is None or "::" not in token:
        return False
    if not any(line.strip() == "exit code: 0" for line in tests_text.splitlines()):
        return False
    cited, _, names = token.partition("::")
    target = _inside(repo, cited)
    if target is None or not target.is_file():
        return False
    body = _read_text(target)
    if body is None:
        return False
    for name in names.split("::"):
        name = PARAM_ID.sub("", name)
        if not name or name not in body:
            return False
    return cited in tests_text or posixpath.normpath(cited) in tests_text


def _reproduced_ok(repo: Path, token: str) -> bool:
    target = _inside(repo, token)
    if target is None or not target.is_file():
        return False
    text = _read_text(target)
    if text is None:
        return False
    try:
        payload = json.loads(text)
    except (ValueError, RecursionError):  # malformed, or nested past the recursion limit
        return False
    return (isinstance(payload, dict) and payload.get("schema") == APP_VERIFY_SCHEMA
            and payload.get("verdict") == "pass")


def _measured_rung(section: SafetySection, fact: str, repo: Path,
                   blast_radius: Optional[Path], tests_output: Optional[Path]) -> str:
    """Highest rung whose evidence is accepted, or `none`. Each rung stands on
    its own lines (not cumulative); every line for a rung must check out."""
    union = _consumer_union(blast_radius)
    tests_text = _read_text(tests_output)
    ev = section.evidence
    accepted = {
        "claimed": bool(fact),
        "read": bool(ev["read"]) and all(_cite_ok(repo, t) for t in ev["read"]),
        "traced": _traced_ok(repo, ev["traced"], union),
        "tested": bool(ev["tested"]) and all(_tested_ok(repo, t, tests_text)
                                             for t in ev["tested"]),
        "reproduced": bool(ev["reproduced"]) and all(_reproduced_ok(repo, t)
                                                     for t in ev["reproduced"]),
    }
    best = "none"
    for rung in RUNGS:
        if accepted[rung]:
            best = rung
    return best


def safety_fact(review_output: Path, repo: Path, blast_radius: Optional[Path],
                tests_output: Optional[Path]) -> int:
    text = _read_text(review_output)
    if text is None:
        return _emit("unverifiable", ["review_output_unreadable"],
                     "review-override safety-fact: unverifiable (review_output_unreadable)")
    repo = repo.resolve()
    section = _parse_safety_section(text)
    match = VERDICT_LINE.search(text)
    verdict = match.group(1).upper() if match else ""

    reasons: List[str] = []
    fact, holds, claimed = "", "", "none"
    if section is None:
        reasons.append("safety_fact_missing section")
        measured = "none"
    else:
        fact = section.fields.get("fact", "").strip()
        holds = _word(section.fields.get("holds"))
        rung = _word(section.fields.get("rung"))
        if rung in RUNGS:
            claimed = rung
        if not fact:
            reasons.append("safety_fact_missing fact")
        if holds not in ("yes", "no"):
            reasons.append("safety_fact_missing holds")
        if claimed == "none":
            reasons.append("safety_fact_missing rung")
        measured = _measured_rung(section, fact, repo, blast_radius, tests_output)
    if measured == "none" or RUNGS.index(measured) < RUNGS.index(FLOOR):
        reasons.append("safety_fact_below_floor %s" % measured)
    # A fact that does not hold agrees only with FAIL or PAUSE; PASS, or no
    # verdict line at all, leaves the unsafe change unblocked.
    if holds == "no" and verdict not in ("FAIL", "PAUSE"):
        reasons.append("safety_fact_contradicts_verdict")

    state = "fail" if reasons else "pass"
    print(state)
    print("rung: claimed=%s measured=%s" % (claimed, measured))
    print("fact: %s" % (fact or "(none)"))
    for reason in reasons:
        print("reason: %s" % reason)
    print("review-override safety-fact: %s (measured %s, floor %s)" % (state, measured, FLOOR))
    return 1 if reasons else 0


# ---------------------------------------------------------------------------
# evidence (Story 2 of `2026-11-04-evidence-gated-review`)
# ---------------------------------------------------------------------------

BLOCKING_SEVERITIES = ("Critical", "Major")
CLAIM_CATEGORIES = ("security", "architecture")
RUN_CAP = 5
DEFAULT_TIMEOUT = 120
GIT_TIMEOUT = 60
KILL_GRACE = 5
DIFF_KEY = "\0diff"  # snapshot key for the `git diff HEAD` hash; never a path
HEAD_KEY = "\0head"  # snapshot key for HEAD's commit and branch; never a path

# Issue parsing copies the `_issue_entries` / `normalize_location` patterns
# from review-panel.py rather than importing them (that file is being trimmed).
# Field names match in any case, with or without bold, as SAFETY_FIELD does.
ISSUES_HEADING = re.compile(r"^(#{2,6})\s*Issues Found\b", re.IGNORECASE)
HEADING_LEVEL = re.compile(r"^(#{1,6})\s")
ISSUE_START = re.compile(
    r"^\s*(?:[-*]|\d+\.)\s+\*{0,2}\s*issue\s*\*{0,2}\s*:\s*\*{0,2}\s*(.*?)\s*$", re.IGNORECASE)
ISSUE_FIELD = re.compile(
    r"^\s*(?:[-*]\s+)?\*{0,2}\s*(location|severity|category|evidence)\s*\*{0,2}\s*:"
    r"\s*\*{0,2}\s*(.*?)\s*$", re.IGNORECASE)
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
AC_ID = re.compile(r"AC-\d+\.\d+")
PLACEHOLDER_LOCATIONS = frozenset({"n/a", "na", "none", "-", "—", "–", "not applicable"})
TRAILING_LINE_NO = re.compile(r":\d+(?:-\d+)?$")

# `--surface review`: severities from the Failure Modes Registry table,
# evidence from `#### FM-NNN` blocks under `## Evidence` (spec § /review).
REVIEW_SEVERITIES = ("Critical", "High")  # no Major in /review; High counts as Major+
REVIEW_UNAVAILABLE = ("recorded", "check")  # /review has no recorded run and no Gate 2
UNCONFIRMED = "Medium (unconfirmed)"
REGISTRY_HEADING = re.compile(r"^(#{1,6})\s*Failure Modes Registry\b", re.IGNORECASE)
EVIDENCE_HEADING = re.compile(r"^(#{1,6})\s*Evidence\s*$", re.IGNORECASE)
FM_HEADING = re.compile(r"^#{1,6}\s*(FM-\d+)\b", re.IGNORECASE)
FM_ID = re.compile(r"^FM-\d+$", re.IGNORECASE)
TABLE_RULE = re.compile(r"^\|?[\s:|-]+\|?$")

TEST_RUNNER_LINE = re.compile(r"^[ \t]*-[ \t]*\*\*Test Runner:\*\*[ \t]*(.*)$", re.MULTILINE)
RUNNER_NOTE = re.compile(r"\s+\(.*$")  # `jest (detected: package.json scripts.test)`
RUNNER_WORDS = {"pytest": "pytest", "py.test": "pytest", "jest": "jest",
                "vitest": "vitest", "rspec": "rspec"}
PREFIX_PAIRS = (("uv", "run"), ("poetry", "run"), ("bundle", "exec"))
PREFIX_WORDS = ("npx", "pnpm", "yarn")

PYTEST_FAILED = re.compile(r"\b[1-9]\d* failed\b")
JEST_FAILED = re.compile(r"^\s*Tests:.*?\b[1-9]\d* failed", re.MULTILINE)
VITEST_FAILED = re.compile(r"^\s*Tests\s+[1-9]\d* failed", re.MULTILINE)
VITEST_RESULT = re.compile(r"^\s*(?:[✓✔×✗❯↓]|FAIL\b|PASS\b|Tests\s)", re.MULTILINE)
VITEST_ERROR = re.compile(r"^\s*Error:", re.MULTILINE)
GO_FAILED = re.compile(r"^\s*--- FAIL:", re.MULTILINE)
CARGO_BROKEN = re.compile(r"could not compile|error\[E\d+")
RSPEC_FAILED = re.compile(r"\b\d+ examples?, [1-9]\d* failures?")
RSPEC_OUTSIDE = re.compile(r"errors? occurred outside of examples")

RECORDED_EXIT = re.compile(r"^\s*exit code:\s*(-?\d+)\s*$", re.MULTILINE)
FAILED_WORD = re.compile(r"\b(?:FAILED|FAIL|ERROR)\b")
PASSED_WORD = re.compile(r"\b(?:PASSED|PASS)\b")
OUTPUT_TOKEN = re.compile(r"[\s:(),'\"\[\]<>]+")

# Inherited repository redirects would point `git -C` somewhere else.
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")
# No index refresh, no fsmonitor hook: the snapshot never writes.
GIT_READ_ONLY = ("--no-optional-locks", "-c", "core.fsmonitor=false")


class Finding:
    """One `### Issues Found` entry, keyed F<n> in output order."""

    def __init__(self, key: str) -> None:
        self.key = key
        self.fields: Dict[str, str] = {}
        self.block: Optional[str] = None   # the fenced file after a `test` Evidence field
        self.wants_block = False
        self.extra_evidence = False
        self.bound = False  # /review: the registry row has an `#### FM-NNN` block


class Outcome(NamedTuple):
    state: str   # confirmed | advisory | unverifiable | abort (the whole call)
    detail: str  # what confirmed it, or the reason


class Runner(NamedTuple):
    kind: str          # pytest | jest | vitest | go | cargo | rspec
    base: List[str]    # Test Runner tokens through the runner word
    has_run: bool      # vitest: `run` is already in `base`
    npm: bool          # `npm test`: scoped arguments follow `--`


def _dedent(line: str, width: int) -> str:
    """`line` without up to `width` leading spaces (an indented fence's body)."""
    lead = len(line) - len(line.lstrip(" "))
    return line[min(lead, width):]


def _evidence_parts(value: str) -> Tuple[str, str]:
    """(kind, rest) of an Evidence value, with backticks dropped."""
    parts = value.replace("`", " ").split(None, 1)
    if not parts:
        return "", ""
    return parts[0].strip("*").lower(), (parts[1].strip() if len(parts) > 1 else "")


def _evidence_findings(lines: Sequence[str], surface: str = "gate3") -> List[Finding]:
    """Issues under `### Issues Found` (on `review`, `#### FM-NNN` blocks under
    `## Evidence`) with their first Evidence field and, for `test`, the first
    fenced block after it. Lines inside any fence are never read as headings
    or fields, so a `# comment` in a repro is code."""
    review = surface == "review"
    section = EVIDENCE_HEADING if review else ISSUES_HEADING
    findings: List[Finding] = []
    issues_level = 0  # heading depth of the open section; 0 = outside
    current: Optional[Finding] = None
    fence: Optional[Tuple[str, int, int]] = None  # (char, length, indent) of the open fence
    block: Optional[List[str]] = None
    for line in lines:
        if fence is not None:
            close = FENCE.match(line)
            if (close and close.group(2)[0] == fence[0] and len(close.group(2)) >= fence[1]
                    and not close.group(3).strip()):
                if block is not None and current is not None:
                    current.block = "\n".join(block) + "\n"
                fence, block = None, None
            elif block is not None:
                block.append(_dedent(line, fence[2]))
            continue
        opening = FENCE.match(line)
        if opening:
            fence = (opening.group(2)[0], len(opening.group(2)), len(opening.group(1)))
            if current is not None and current.wants_block:
                current.wants_block = False
                block = []
            continue
        heading = HEADING_LEVEL.match(line)
        if heading:
            issues = section.match(line)
            if issues:
                issues_level = len(issues.group(1))
            elif issues_level and len(heading.group(1)) <= issues_level:
                issues_level = 0
            block_id = FM_HEADING.match(line) if review and issues_level else None
            current = Finding(block_id.group(1).upper()) if block_id else None
            if current is not None:
                findings.append(current)
            continue
        if not issues_level:
            continue
        start = None if review else ISSUE_START.match(line)
        if start:
            current = Finding("F%d" % (len(findings) + 1))
            current.fields["issue"] = start.group(1)
            findings.append(current)
            continue
        field = ISSUE_FIELD.match(line)
        if field is None or current is None:
            continue
        name = field.group(1).lower()
        if name in current.fields:
            current.extra_evidence = current.extra_evidence or name == "evidence"
            continue
        current.fields[name] = field.group(2)
        if name == "evidence" and _evidence_parts(field.group(2))[0] == "test":
            current.wants_block = True
    if fence is not None and block is not None and current is not None:
        current.block = "\n".join(block) + "\n"  # an unclosed fence runs to the end
    return findings


def _normalize_location(raw: str) -> Optional[str]:
    """Path from a `**Location:**` value: the first backticked span (else the
    first word), without leading `./`, trailing `:line[-line]`, or whitespace."""
    raw = raw.strip()
    if not raw or raw.strip("*_[]").lower() in PLACEHOLDER_LOCATIONS:
        return None
    span = re.search(r"`([^`]+)`", raw)
    path = span.group(1) if span else raw.split()[0]
    path = path.strip().rstrip(",;")
    while path.startswith("./"):
        path = path[2:]
    path = TRAILING_LINE_NO.sub("", path).strip()
    if not path or path.lower() in PLACEHOLDER_LOCATIONS:
        return None
    return posixpath.normpath(path)


def _registry_rows(lines: Sequence[str]) -> List[Tuple[str, str, str]]:
    """(ID, Category, Severity) of each `FM-NNN` row in the Failure Modes
    Registry table. Columns are found by header name, else taken as the first
    three. Fenced lines are skipped."""
    rows: List[Tuple[str, str, str]] = []
    level = 0  # heading depth of the open registry section; 0 = outside
    columns: Optional[Tuple[int, ...]] = None
    fence = ""
    for line in lines:
        mark = FENCE.match(line)
        if fence:
            if (mark and mark.group(2)[0] == fence[0] and len(mark.group(2)) >= len(fence)
                    and not mark.group(3).strip()):
                fence = ""
            continue
        if mark:
            fence = mark.group(2)
            continue
        heading = HEADING_LEVEL.match(line)
        if heading:
            opened = REGISTRY_HEADING.match(line)
            if opened:
                level, columns = len(opened.group(1)), None
            elif level and len(heading.group(1)) <= level:
                level = 0
            continue
        if not level or not line.lstrip().startswith("|") or TABLE_RULE.match(line.strip()):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if columns is None:  # the header row
            names = [_word(cell) for cell in cells]
            columns = tuple(names.index(name) if name in names else i
                            for i, name in enumerate(("id", "category", "severity")))
            continue
        if len(cells) <= max(columns):
            continue
        key = re.sub(r"[`*_]", "", cells[columns[0]]).strip().upper()
        if FM_ID.match(key):
            rows.append((key, cells[columns[1]], cells[columns[2]]))
    return rows


def _review_findings(lines: Sequence[str]) -> Tuple[List[Finding], List[str]]:
    """Registry rows in table order, each bound to the first `#### FM-NNN`
    block with its ID, and the IDs of later rows that repeat an ID (dropped).
    The registry gives the Severity; the block gives the Location and
    Evidence, and its Category, when it has one, wins."""
    blocks: Dict[str, Finding] = {}
    for block in _evidence_findings(lines, surface="review"):
        if block.key in blocks:
            blocks[block.key].extra_evidence = True  # a second block for a row is ignored
        else:
            blocks[block.key] = block
    findings: List[Finding] = []
    duplicates: List[str] = []
    for key, category, severity in _registry_rows(lines):
        if any(f.key == key for f in findings):
            duplicates.append(key)
            continue
        finding = Finding(key)
        block = blocks.get(key)
        if block is not None:
            finding.fields.update(block.fields)
            finding.block, finding.extra_evidence = block.block, block.extra_evidence
            finding.bound = True
        finding.fields["severity"] = severity
        finding.fields.setdefault("category", category)
        findings.append(finding)
    return findings, duplicates


def _rel(repo: Path, raw: str) -> Optional[str]:
    """A changed-file or output token as a normalized repo-relative path; an
    absolute path counts only when it resolves inside `repo`."""
    raw = raw.strip()
    while raw.startswith("./"):
        raw = raw[2:]
    if not raw:
        return None
    if os.path.isabs(raw):
        try:
            return Path(raw).resolve().relative_to(repo).as_posix()
        except (OSError, RuntimeError, ValueError):
            return None
    return posixpath.normpath(raw)


def _first_word(value: str) -> str:
    words = value.split()
    return words[0].strip("*[](),.;:") if words else ""


def _has_claim(finding: Finding) -> bool:
    text = " ".join(finding.fields.get(k, "") for k in ("category", "issue", "location"))
    category = _first_word(finding.fields.get("category", "")).lower()
    return bool(AC_ID.search(text)) or category in CLAIM_CATEGORIES


def _npm_test_script(repo: Path) -> Optional[str]:
    text = _read_text(repo / "package.json")
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except (ValueError, RecursionError):
        return None
    scripts = payload.get("scripts") if isinstance(payload, dict) else None
    script = scripts.get("test") if isinstance(scripts, dict) else None
    return script if isinstance(script, str) and script.strip() else None


def _skip_prefixes(tokens: Sequence[str]) -> int:
    """Index of the runner word after `uv run`, `poetry run`, `bundle exec`,
    `npx`, `pnpm`, `yarn`, and `python* -m` (any interpreter basename)."""
    i = 0
    while i < len(tokens):
        name = posixpath.basename(tokens[i])
        following = tokens[i + 1] if i + 1 < len(tokens) else ""
        if (name, following) in PREFIX_PAIRS or (name.startswith("python") and following == "-m"):
            i += 2
        elif name in PREFIX_WORDS:
            i += 1
        else:
            break
    return i


def _detect_runner(value: str, repo: Path, npm_ok: bool = True) -> Tuple[Optional[Runner], str]:
    """The runner a `Test Runner` value names, or (None, `unknown_runner <token>`).
    `npm test` and `npm run test` resolve through package.json `scripts.test`."""
    text = RUNNER_NOTE.sub("", value).strip()
    try:
        tokens = shlex.split(text)
    except ValueError:
        return None, "unknown_runner %s" % (text.split() or ["none"])[0]
    if not tokens:
        return None, "unknown_runner none"
    i = _skip_prefixes(tokens)
    if i >= len(tokens):
        return None, "unknown_runner %s" % posixpath.basename(tokens[0])
    word = posixpath.basename(tokens[i])
    head, rest = tokens[:i + 1], tokens[i + 1:]
    if word in RUNNER_WORDS:
        kind = RUNNER_WORDS[word]
        if kind == "vitest" and "run" in rest:
            return Runner(kind, head + rest[:rest.index("run") + 1], True, False), ""
        return Runner(kind, head, False, False), ""
    if word in ("go", "cargo") and rest[:1] == ["test"]:
        return Runner(word, head + ["test"], False, False), ""
    if word == "npm" and npm_ok:
        sub = rest[:1] if rest[:1] == ["test"] else rest[:2] if rest[:2] == ["run", "test"] else []
        script = _npm_test_script(repo) if sub else None
        inner = _detect_runner(script, repo, npm_ok=False)[0] if script else None
        if inner is not None:
            return Runner(inner.kind, head + sub, inner.has_run, True), ""
    return None, "unknown_runner %s" % word


def _scoped_command(runner: Runner, path: str) -> List[str]:
    if runner.kind == "go":
        args = ["./" + (posixpath.dirname(path) or ".")]
    elif runner.kind == "cargo":
        args = ["--test", posixpath.splitext(posixpath.basename(path))[0]]
    elif runner.kind == "vitest" and not runner.has_run:
        args = ["run", path]
    else:
        args = [path]
    return runner.base + (["--"] if runner.npm else []) + args


def _test_path_ok(kind: str, rel: str) -> bool:
    """The runner's own test-file pattern (technical spec § Repro Paths)."""
    parts = rel.split("/")
    name = parts[-1]
    if kind == "pytest":
        return fnmatch.fnmatchcase(name, "test_*.py") or fnmatch.fnmatchcase(name, "?*_test.py")
    if kind in ("jest", "vitest"):
        return (fnmatch.fnmatchcase(name, "*.test.*") or fnmatch.fnmatchcase(name, "*.spec.*")
                or "__tests__" in parts[:-1])
    if kind == "go":
        return fnmatch.fnmatchcase(name, "?*_test.go") and not name.startswith(("_", "."))
    if kind == "cargo":
        return len(parts) >= 2 and parts[-2] == "tests" and fnmatch.fnmatchcase(name, "?*.rs")
    if kind == "rspec":
        return fnmatch.fnmatchcase(name, "?*_spec.rb")
    return False


def _vitest_error_first(output: str) -> bool:
    error = VITEST_ERROR.search(output)
    if error is None:
        return False
    result = VITEST_RESULT.search(output)
    return result is None or error.start() < result.start()


def _classify(kind: str, code: int, output: str) -> Tuple[str, str]:
    """(state, reason) for a finished scoped run: `confirmed` only in the
    runner's test-failed class, `advisory` on exit 0, else `collection_error`."""
    broken = ("unverifiable", "collection_error")
    if kind == "go" and ("[build failed]" in output or "[setup failed]" in output):
        return broken
    if kind == "cargo" and CARGO_BROKEN.search(output):
        return broken
    if code == 0:
        return "advisory", "repro_passed"
    if kind == "pytest":
        # Exit 1 alone is not enough: a setup error (`1 error`) and an
        # interpreter without pytest exit 1 too.
        failed = code == 1 and bool(PYTEST_FAILED.search(output))
    elif kind == "jest":
        failed = (code == 1 and bool(JEST_FAILED.search(output))
                  and "Test suite failed to run" not in output)
    elif kind == "vitest":
        failed = (code == 1 and bool(VITEST_FAILED.search(output))
                  and "no tests" not in output.lower() and not _vitest_error_first(output))
    elif kind == "go":
        failed = code == 1 and bool(GO_FAILED.search(output))
    elif kind == "cargo":
        failed = code == 101 and "test result: FAILED" in output
    else:
        failed = (code == 1 and bool(RSPEC_FAILED.search(output))
                  and not RSPEC_OUTSIDE.search(output))
    return ("confirmed", "") if failed else broken


def _git_bytes(cwd: Path, *args: str) -> Optional[bytes]:
    """stdout of a read-only git command, or None when git is missing or fails."""
    env = {k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}
    try:
        proc = subprocess.run(["git", *GIT_READ_ONLY, "-C", str(cwd), *args], input=b"",
                              capture_output=True, env=env, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _git_root(repo: Path) -> Optional[Path]:
    out = _git_bytes(repo, "rev-parse", "--show-toplevel")
    if out is None or not out.strip():
        return None
    return Path(os.fsdecode(out.strip()))


def _file_state(path: Path) -> str:
    try:
        if path.is_symlink():
            return "link " + os.readlink(str(path))
        if path.is_dir():
            return "dir"
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "missing"


def _snapshot(top: Path) -> Optional[Dict[str, str]]:
    """Each `git status` path with its status code and content hash, plus the
    SHA-256 of `git diff HEAD --binary` and HEAD's commit and branch. Ignored
    files never appear."""
    status = _git_bytes(top, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if status is None:
        return None
    diff_args = ("--binary", "--no-ext-diff", "--no-textconv")
    diff = _git_bytes(top, "diff", "HEAD", *diff_args)
    if diff is None:  # no commit yet: diff against the empty tree
        empty = _git_bytes(top, "hash-object", "-t", "tree", "--stdin")
        diff = _git_bytes(top, "diff", os.fsdecode(empty.strip()), *diff_args) if empty else None
        if diff is None:
            return None
    # A commit or checkout on a clean tree changes neither status nor diff.
    head = (_git_bytes(top, "rev-parse", "--verify", "-q", "HEAD") or b"") + b"\0" + \
        (_git_bytes(top, "symbolic-ref", "-q", "HEAD") or b"")
    state = {DIFF_KEY: hashlib.sha256(diff).hexdigest(), HEAD_KEY: os.fsdecode(head)}
    items = status.split(b"\0")
    i = 0
    while i < len(items):
        item = items[i]
        i += 1
        if len(item) < 4:
            continue
        code = item[:2].decode("ascii", "replace")
        if code[0] in "RC":
            i += 1  # -z prints the rename or copy source as the next item
        rel = os.fsdecode(item[3:])
        state[rel] = "%s %s" % (code, _file_state(top / rel))
    return state


def _tree_changes(before: Dict[str, str], after: Optional[Dict[str, str]]) -> List[str]:
    if after is None:
        return ["(git status failed)"]
    paths = sorted(k for k in set(before) | set(after)
                   if k not in (DIFF_KEY, HEAD_KEY) and before.get(k) != after.get(k))
    if paths:
        return paths
    if before.get(HEAD_KEY) != after.get(HEAD_KEY):
        return ["(HEAD)"]
    if before.get(DIFF_KEY) != after.get(DIFF_KEY):
        return ["(git diff HEAD)"]
    return []


def _executable(command: str, repo: Path) -> bool:
    if "/" in command or os.sep in command:
        path = Path(command) if os.path.isabs(command) else repo / command
        return path.is_file() and os.access(str(path), os.X_OK)
    return shutil.which(command) is not None


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (AttributeError, OSError):  # no process groups here, or the group is gone
        proc.kill()


def _run_bounded(command: List[str], cwd: Path, timeout: int) -> Tuple[Optional[int], str]:
    """(exit code, output) of one run in its own session; (None, "") on timeout,
    after the whole process group is killed. Raises OSError when it cannot start."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # no __pycache__ beside the repro
    proc = subprocess.Popen(command, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        try:
            proc.communicate(timeout=KILL_GRACE)
        except subprocess.TimeoutExpired:  # a child left the group and holds the pipe
            proc.stdout.close()
            proc.wait(timeout=KILL_GRACE)
        return None, ""
    except BaseException:  # an interrupt never reaches the run's own session
        _kill_group(proc)
        raise
    return proc.returncode, out.decode("utf-8", "replace")


def _recorded_outcome(rest: str, tests_text: Optional[str]) -> Outcome:
    """`recorded <path>::<test>` against the recorded run (`exit code: N`)."""
    test_id = rest.split()[0] if rest.split() else ""
    exit_line = RECORDED_EXIT.search(tests_text) if tests_text is not None else None
    if exit_line is None:
        return Outcome("unverifiable", "no_recorded_run")
    if "::" not in test_id:
        return Outcome("unverifiable", "test_not_in_run")
    code = int(exit_line.group(1))
    named = re.compile(r"(?<![\w./-])(?:\./)?%s(?:\[[^\]]*\])?(?![\w:\[.-])" % re.escape(test_id))
    hits = [line for line in tests_text.splitlines() if named.search(line)]
    if code != 0 and any(FAILED_WORD.search(line) for line in hits):
        return Outcome("confirmed", "recorded %s, exit %d" % (test_id, code))
    if any(PASSED_WORD.search(line) for line in hits):
        return Outcome("advisory", "recorded_passed")
    path = re.compile(r"(?<![\w./-])(?:\./)?%s(?![\w/-])" % re.escape(test_id.partition("::")[0]))
    if code == 0 and (hits or path.search(tests_text)):
        return Outcome("advisory", "recorded_passed")
    return Outcome("unverifiable", "test_not_in_run")


def _security_outcome(finding: Finding, rest: str, repo: Path, change_set: Set[str]) -> Outcome:
    """`security-path source <path:line> sink <path:line>`: both citations
    resolve as `read` lines do, and the sink is in the change set."""
    if _first_word(finding.fields.get("category", "")).lower() != "security":
        return Outcome("unverifiable", "not_security")
    cites: Dict[str, str] = {}
    tokens = [t.rstrip(",;") for t in rest.split()]
    for i, token in enumerate(tokens):
        word, colon, inline = token.partition(":")
        word = word.lower()
        if word in ("source", "sink") and word not in cites:
            if colon and inline:
                cites[word] = inline
            else:
                cites[word] = tokens[i + 1] if i + 1 < len(tokens) else ""
    for word in ("source", "sink"):
        token = cites.get(word, "")
        if not token or _cite_ok(repo, token) is None:
            return Outcome("unverifiable", "bad_citation %s" % (token or word))
    if _cite_ok(repo, cites["sink"]) not in change_set:
        return Outcome("advisory", "location_outside_change_set")
    return Outcome("confirmed", "security-path source %s sink %s" % (cites["source"], cites["sink"]))


def _remove_repro(target: Path) -> bool:
    """Delete the repro; False when it is still there."""
    try:
        target.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        return False
    return True


class EvidenceRun:
    """State shared across one call's `test` and `check` runs."""

    def __init__(self, repo: Path, top: Optional[Path], change_set: Set[str],
                 runner: Optional[Runner], runner_reason: str,
                 checks: Optional[List[List[str]]], timeout: int) -> None:
        self.repo = repo
        self.top = top
        self.change_set = change_set
        self.runner = runner
        self.runner_reason = runner_reason
        self.checks = checks
        self.timeout = timeout
        self.runs = 0
        self.declared: Set[str] = set()
        self.mutated: List[str] = []

    def test(self, finding: Finding, rest: str) -> Outcome:
        """Write the fenced repro at its path, run it scoped, delete it, and
        compare snapshots taken before the write and after the delete."""
        if finding.block is None:
            return Outcome("unverifiable", "missing_test_block")
        if self.runner is None:
            return Outcome("unverifiable", self.runner_reason)
        words = rest.split()
        target = _inside(self.repo, words[0]) if words else None
        if target is None:
            return Outcome("unverifiable", "path_outside_repo")
        rel = target.relative_to(self.repo).as_posix()
        if rel in self.declared or os.path.lexists(str(target)):
            self.declared.add(rel)
            return Outcome("unverifiable", "path_exists")
        self.declared.add(rel)
        if not _test_path_ok(self.runner.kind, rel):
            return Outcome("unverifiable", "not_a_test_path")
        if self.runs >= RUN_CAP:
            return Outcome("unverifiable", "repro_cap")
        before = _snapshot(self.top)
        if before is None:
            return Outcome("abort", "no_git")
        created: List[Path] = []  # missing parents, outermost first
        parent = target.parent
        while not parent.exists():
            created.insert(0, parent)
            parent = parent.parent
        opened = False  # set once `open(..., "x")` has created the repro
        try:
            try:
                for folder in created:
                    folder.mkdir()
                with open(str(target), "x", encoding="utf-8", newline="") as handle:
                    opened = True
                    handle.write(finding.block)
            except OSError:
                if opened:
                    _remove_repro(target)
                for folder in reversed(created):
                    try:
                        folder.rmdir()
                    except OSError:
                        pass
                return Outcome("unverifiable", "repro_write_failed")
            self.runs += 1
            try:
                code, output = _run_bounded(_scoped_command(self.runner, rel), self.repo,
                                            self.timeout)
                missing = False
            except OSError:
                code, output, missing = None, "", True
        finally:
            # Any exit from the block, an interrupt included, deletes the repro.
            removed = _remove_repro(target) if opened else True
        if not removed:
            self.mutated = [rel]
            return Outcome("unverifiable", "repro_mutated_tree")
        changes = _tree_changes(before, _snapshot(self.top))
        if changes:
            self.mutated = changes
            return Outcome("unverifiable", "repro_mutated_tree")
        if created:  # the snapshot matched, so only ignored files are left in it
            shutil.rmtree(str(created[0]), ignore_errors=True)
        if missing:
            return Outcome("abort", "runner_not_found")
        if code is None:
            return Outcome("unverifiable", "timeout %d" % self.timeout)
        state, reason = _classify(self.runner.kind, code, output)
        if state == "confirmed":
            return Outcome(state, "test %s, exit %d" % (rel, code))
        return Outcome(state, reason)

    def check(self, rest: str) -> Outcome:
        """Run a Gate 2 recorded command with the reviewer's arguments."""
        if self.checks is None:
            return Outcome("unverifiable", "no_gate2_record")
        try:
            command = shlex.split(rest)
        except ValueError:
            command = []
        if not command or not any(rec and command[:len(rec)] == rec for rec in self.checks):
            return Outcome("unverifiable", "command_not_recorded")
        if not _executable(command[0], self.repo):
            return Outcome("unverifiable", "command_not_found")
        if self.runs >= RUN_CAP:
            return Outcome("unverifiable", "repro_cap")
        before = _snapshot(self.top)
        if before is None:
            return Outcome("abort", "no_git")
        self.runs += 1
        try:
            code, output = _run_bounded(command, self.repo, self.timeout)
            missing = False
        except OSError:
            code, output, missing = None, "", True
        changes = _tree_changes(before, _snapshot(self.top))
        if changes:
            self.mutated = changes
            return Outcome("unverifiable", "repro_mutated_tree")
        if missing:
            return Outcome("unverifiable", "command_not_found")
        if code is None:
            return Outcome("unverifiable", "timeout %d" % self.timeout)
        if code == 0:
            return Outcome("advisory", "check_passed")
        if any(_rel(self.repo, token) in self.change_set for token in OUTPUT_TOKEN.split(output)):
            return Outcome("confirmed", "check %s, exit %d" % (" ".join(command), code))
        return Outcome("advisory", "no_changed_file_named")


def _read_checks(path: Optional[Path]) -> Optional[List[List[str]]]:
    """Gate 2 recorded commands, one per line, each split with shlex."""
    text = _read_text(path)
    if text is None:
        return None
    commands: List[List[str]] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            commands.append(shlex.split(line))
        except ValueError:
            continue
    return commands


def _evidence_unverifiable(reason: str, review: bool = False) -> int:
    # On `--surface review`, line 2 is the `/review` header's evidence-gate value.
    header: List[str] = []
    if review:
        state = "off" if reason == "switch_off" else "unverifiable (%s)" % reason
        header = ["evidence-gate: %s" % state]
    return _emit("unverifiable", [reason], "review-override evidence: unverifiable (%s)" % reason,
                 details=header)


def evidence(review_output: Path, repo: Path, changed: Sequence[str],
             tests_output: Optional[Path], checks: Optional[Path], timeout: int,
             surface: str = "gate3") -> int:
    repo = repo.resolve()
    review = surface == "review"
    if _resolve_switch("evidence-gate", repo)[0] == "off":
        return _evidence_unverifiable("switch_off", review)
    text = _read_text(review_output)
    if text is None or not text.strip():
        return _evidence_unverifiable("no_review_output", review)
    duplicates: List[str] = []  # /review registry rows that repeat an FM ID
    if review:  # /review writes no verdict
        findings, duplicates = _review_findings(text.splitlines())
    else:
        match = VERDICT_LINE.search(text)
        verdict = match.group(1).upper() if match else "none"
        if verdict != "FAIL":
            return _evidence_unverifiable("verdict_not_fail %s" % verdict)
        findings = _evidence_findings(text.splitlines())

    change_set = {rel for rel in (_rel(repo, p) for p in changed) if rel}
    blocking = REVIEW_SEVERITIES if review else BLOCKING_SEVERITIES
    outcomes: Dict[str, Outcome] = {}
    kinds: Dict[str, str] = {}  # evidence kind of each finding that passed selection
    for finding in findings:
        severity = _first_word(finding.fields.get("severity", "")).capitalize()
        location = _normalize_location(finding.fields.get("location", ""))
        if severity not in blocking:
            outcomes[finding.key] = Outcome("advisory", "low_severity %s" % (severity or "none"))
        elif review and not finding.bound and change_set:
            # A row with no block has no Location to test. With diff files it is
            # just unevidenced; with none, nothing can be inside the diff.
            kinds[finding.key] = ""
        elif location is None or location not in change_set:
            outcomes[finding.key] = Outcome("advisory", "location_outside_change_set")
        elif not review and not _has_claim(finding):  # on /review the evidence is the claim
            outcomes[finding.key] = Outcome("advisory", "no_claim")
        else:
            kinds[finding.key] = _evidence_parts(finding.fields.get("evidence", ""))[0]

    config = _read_text(repo / CONFIG_REL) or ""
    line = TEST_RUNNER_LINE.search(config)
    runner_value = line.group(1).strip() if line else ""
    runner, runner_reason = (_detect_runner(runner_value, repo) if runner_value
                             else (None, "no_test_runner"))
    # Project-level checks run before anything is written.
    needs_runner = runner is not None and "test" in kinds.values()
    top = None
    if needs_runner or (not review and "check" in kinds.values()):
        top = _git_root(repo)
        if top is None:
            return _evidence_unverifiable("no_git", review)
    if needs_runner and not _executable(runner.base[0], repo):
        return _evidence_unverifiable("runner_not_found", review)

    run = EvidenceRun(repo, top, change_set, runner, runner_reason, _read_checks(checks), timeout)
    tests_text = _read_text(tests_output)
    for finding in findings:
        if finding.key not in kinds:
            continue
        kind = kinds[finding.key]
        rest = _evidence_parts(finding.fields.get("evidence", ""))[1]
        if kind == "":
            outcome = Outcome("advisory", "no_evidence")
        elif review and kind in REVIEW_UNAVAILABLE:
            outcome = Outcome("unverifiable", "kind_unavailable")
        elif kind == "recorded":
            outcome = _recorded_outcome(rest, tests_text)
        elif kind == "security-path":
            outcome = _security_outcome(finding, rest, repo, change_set)
        elif kind in ("test", "check") and run.mutated:
            outcome = Outcome("unverifiable", "stopped_after_mutation")
        elif kind == "test":
            outcome = run.test(finding, rest)
        elif kind == "check":
            outcome = run.check(rest)
        else:
            outcome = Outcome("unverifiable", "unknown_kind %s" % kind)
        if outcome.state == "abort":
            return _evidence_unverifiable(outcome.detail, review)
        outcomes[finding.key] = outcome
    if review and run.mutated:
        # No row's evidence can be trusted after the tree changed, so every
        # severity stays as written, as on any run-level unverifiable.
        return _evidence_unverifiable("repro_mutated_tree %s" % " ".join(run.mutated), review)

    counts = {"confirmed": 0, "advisory": 0, "unverifiable": 0}
    lines: List[str] = ["evidence-gate: on"] if review else []
    reasons: List[str] = []
    for finding in findings:
        outcome = outcomes[finding.key]
        counts[outcome.state] += 1
        word = "unverifiable " if outcome.state == "unverifiable" else ""
        shown = ("confirmed (%s)" % outcome.detail if outcome.state == "confirmed"
                 else "advisory (%s%s)" % (word, outcome.detail))
        location = _normalize_location(finding.fields.get("location", ""))
        at = " at %s" % location if location else ""
        mapped = ""
        if review:  # spec § /review: unconfirmed Critical and High become Medium (unconfirmed)
            severity = _first_word(finding.fields.get("severity", "")).capitalize() or "none"
            if severity in REVIEW_SEVERITIES and outcome.state != "confirmed":
                severity = UNCONFIRMED
            mapped = "; severity %s" % severity
        lines.append("finding %s: %s%s%s" % (finding.key, shown, at, mapped))
        if finding.extra_evidence:
            reasons.append("extra_evidence %s" % finding.key)
        if outcome.state == "confirmed":
            reasons.append("confirmed %s" % finding.key)
    reasons.extend("duplicate_row %s" % key for key in duplicates)
    if run.mutated:
        reasons.insert(0, "repro_mutated_tree %s" % " ".join(run.mutated))
    decided = any(kinds[key] in ("recorded", "check", "security-path")
                  and outcomes[key].state != "unverifiable" for key in kinds)
    if run.mutated or counts["confirmed"]:
        verdict = "fail"
    elif not runner_value and kinds and not decided:
        # No Test Runner and nothing decided by another kind: the agent FAIL stands.
        return _evidence_unverifiable("no_test_runner", review)
    else:
        verdict = "pass"
    summary = ("review-override evidence: %s (%d confirmed, %d advisory, %d unverifiable)"
               % (verdict, counts["confirmed"], counts["advisory"], counts["unverifiable"]))
    return _emit(verdict, reasons, summary, details=lines)


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a whole number of seconds: %r" % value)
    if number < 1:
        raise argparse.ArgumentTypeError("timeout must be at least 1 second")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="re-derive Gate 3 from ac-trace + test-integrity")
    p.add_argument("--spec", type=Path, default=None)
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--story", type=Path, default=None)
    p.add_argument("--new-files", nargs="+", default=None)
    p.add_argument("--tests", nargs="+", default=None)
    s = sub.add_parser("switch", help="resolve an upgrade switch from .writ/config.md")
    s.add_argument("--name", required=True, choices=sorted(SWITCH_LINES))
    s.add_argument("--repo", type=Path, default=Path("."))
    f = sub.add_parser("safety-fact",
                       help="re-derive the Gate 3 safety fact's evidence rung")
    f.add_argument("--review-output", required=True, type=Path)
    f.add_argument("--repo", type=Path, default=Path("."))
    f.add_argument("--blast-radius", type=Path, default=None)
    f.add_argument("--tests-output", type=Path, default=None)
    e = sub.add_parser("evidence",
                       help="run or check the evidence on a Gate 3 FAIL's findings")
    e.add_argument("--review-output", required=True, type=Path)
    e.add_argument("--repo", type=Path, default=Path("."))
    e.add_argument("--changed", nargs="*", default=[])
    e.add_argument("--surface", choices=("gate3", "review"), default="gate3",
                   help="`review` reads a /review report (registry rows and FM-NNN blocks)")
    e.add_argument("--tests-output", type=Path, default=None)
    e.add_argument("--checks", type=Path, default=None)
    e.add_argument("--prior", type=Path, default=None, help="accepted; does nothing yet")
    e.add_argument("--manifest-out", type=Path, default=None, help="accepted; does nothing yet")
    e.add_argument("--timeout", type=_positive_int, default=DEFAULT_TIMEOUT,
                   help="seconds per run (default %d)" % DEFAULT_TIMEOUT)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if args.action == "switch":
        return switch(args.name, args.repo)
    if args.action == "safety-fact":
        return safety_fact(args.review_output, args.repo, args.blast_radius,
                           args.tests_output)
    if args.action == "evidence":
        return evidence(args.review_output, args.repo, args.changed, args.tests_output,
                        args.checks, args.timeout, args.surface)
    return check(args.spec, args.repo, args.story, args.new_files, args.tests)


if __name__ == "__main__":
    sys.exit(main())
