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
  switch --name safety-fact|reviewer-filters [--repo .]

`check` prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason: <code>` lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.

`switch` (Story 1 of `2026-10-25-review-route-rigor`) resolves one upgrade
switch from `<repo>/.writ/config.md`. The config lines are:
  - **Safety Fact:** off
  - **Reviewer Filters:** off
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
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


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
}


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
    return check(args.spec, args.repo, args.story, args.new_files, args.tests)


if __name__ == "__main__":
    sys.exit(main())
