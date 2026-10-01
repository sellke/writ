#!/usr/bin/env python3
"""Cross-family review panel helper (spec `2026-10-01-cross-family-review-panel`).

The panel is additive: the session's Gate 3 agent and `review-override.py`
decide exactly as before, and a finding raised by two or more vendors adds a
block. This script never spawns a model and never touches the network; the
orchestrator spawns, this script owns the config contract, the vendor table,
the matching rule, and the verdict.

Subcommands:
  status --repo . --origin "<model>" [--platform cursor|claude-code|codex|openclaw] [--json]
                      Resolve `- **Review Panel:** <slug>[, <slug>…]` in
                      `.writ/config.md` against the session vendor and the
                      platform: which reviewers are kept, which are dropped
                      (`same_vendor`, `unknown_vendor`, `duplicate_slug`,
                      `over_cap`) and why the panel is off or skipped.

  tally --origin "<model>" --primary FILE --reviewer <slug>=FILE [--reviewer …] [--json]
                      Key each output's findings (`ac:AC-N.M` from unchecked
                      tagged checklist lines; `<security|architecture>:<path>`
                      from Critical/Major Issues Found entries) and count
                      distinct vendors per key, the primary counted as one.
                      ≥2 vendors → `block`; one panel vendor → advisory note;
                      primary-only keys are not reprinted.

Prints one verdict line first (`pass` / `block` / `unverifiable`), then
`reason:` lines (`status` adds `reviewer:` and `dropped:` lines; `tally` adds
`review-panel: dropped|advisory|block` lines), and a `review-panel:` summary
line last. `--json` prints one object instead.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `tally` found a consensus finding (`block`).
Exit 2: usage (missing `--origin`, unreadable repo or config, unknown
        platform, malformed `--reviewer`, primary output missing or without a
        verdict line).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple


CONFIG_LINE = re.compile(r"^- \*\*Review Panel:\*\*[ \t]*(.*)$",
                         re.MULTILINE | re.IGNORECASE)
DISABLED_VALUE = "none"
MAX_REVIEWERS = 3  # Cursor runs 4 concurrent Tasks, one of them the primary.

# The only vendor knowledge Writ holds. Slug prefixes are matched literally,
# longest first; adding a vendor is one entry here plus a test.
SLUG_PREFIXES: Tuple[Tuple[str, str], ...] = (
    ("cursor-grok-", "xai"),
    ("composer-", "cursor"),
    ("claude-", "anthropic"),
    ("gemini-", "google"),
    ("grok-", "xai"),
    ("muse-", "meta"),
    ("gpt-", "openai"),
)
O_SERIES = re.compile(r"^o[1-9]\d*(?:-|$)")
ORIGIN_WORDS: Dict[str, str] = {
    "claude": "anthropic",
    "gpt": "openai",
    "grok": "xai",
    "gemini": "google",
    "composer": "cursor",
    "muse": "meta",
}
O_SERIES_WORD = re.compile(r"^o[1-9]\d*$")

PLATFORMS = ("cursor", "claude-code", "codex", "openclaw")
NO_CROSS_VENDOR_PLATFORMS = frozenset({"claude-code", "codex"})


class UsageError(Exception):
    """Exit-2 conditions."""


def slug_vendor(slug: str) -> Optional[str]:
    """Vendor for a Cursor model slug, or None when no table row matches."""
    for prefix, vendor in sorted(SLUG_PREFIXES, key=lambda row: -len(row[0])):
        if slug.startswith(prefix):
            return vendor
    if O_SERIES.match(slug):
        return "openai"
    return None


def origin_vendor(origin: str) -> Optional[str]:
    """Vendor for the harness-reported origin model name, by case-insensitive
    word match. None when no word matches or words name two vendors."""
    found = set()
    for word in re.split(r"[^a-z0-9]+", origin.lower()):
        if word in ORIGIN_WORDS:
            found.add(ORIGIN_WORDS[word])
        elif O_SERIES_WORD.match(word):
            found.add("openai")
    if len(found) == 1:
        return next(iter(found))
    return None


def config_value(repo: Path) -> Optional[str]:
    """The raw Review Panel value (first matching line); None when the file
    or the line is absent. An existing but unreadable file is a usage error."""
    config = repo / ".writ" / "config.md"
    if not config.exists():
        return None
    try:
        text = config.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError("cannot read %s (%s)" % (config, exc))
    match = CONFIG_LINE.search(text)
    if not match:
        return None
    return match.group(1).strip()


class Panel(NamedTuple):
    verdict: str
    reasons: List[str]
    reviewers: List[Tuple[str, str]]  # (slug, vendor), config order
    dropped: List[Tuple[str, str]]    # (slug, reason), config order
    session_vendor: Optional[str]
    summary: str


def _drop_list(dropped: Sequence[Tuple[str, str]]) -> str:
    return ", ".join("%s %s" % pair for pair in dropped)


def resolve(repo: Path, origin: str, platform: Optional[str]) -> Panel:
    """Apply the config line, platform, and vendor table, in that order."""
    session = origin_vendor(origin)

    def off(reason: str, kind: str, summary: Optional[str] = None,
            dropped: Sequence[Tuple[str, str]] = ()) -> Panel:
        return Panel("unverifiable", [reason], [], list(dropped), session,
                     summary or "review-panel: %s — %s" % (kind, reason))

    value = config_value(repo)
    if value is None:
        return off("no_config_line", "off")
    if value.lower() == DISABLED_VALUE:
        return off("panel_disabled", "off")
    slugs = [s.strip() for s in value.split(",") if s.strip()]
    if not slugs:
        return off("malformed_config", "skipped")
    if platform in NO_CROSS_VENDOR_PLATFORMS:
        return off("platform_cannot_spawn_other_vendors", "skipped",
                   "review-panel: skipped — platform cannot spawn other vendors")
    if session is None:
        return off("unknown_session_vendor", "skipped")

    kept: List[Tuple[str, str]] = []
    dropped: List[Tuple[str, str]] = []
    seen = set()
    for slug in slugs:
        vendor = slug_vendor(slug)
        if slug in seen:
            dropped.append((slug, "duplicate_slug"))
        elif vendor is None:
            dropped.append((slug, "unknown_vendor"))
        elif vendor == session:
            dropped.append((slug, "same_vendor"))
        elif len(kept) >= MAX_REVIEWERS:
            dropped.append((slug, "over_cap"))
        else:
            kept.append((slug, vendor))
        seen.add(slug)

    if not kept:
        return off("no_other_vendor", "skipped",
                   "review-panel: skipped — no_other_vendor (dropped: %s)"
                   % _drop_list(dropped), dropped)
    reasons = ["unverified_platform"] if platform == "openclaw" else []
    noun = "reviewer" if len(kept) == 1 else "reviewers"
    summary = "review-panel: pass — %d %s (%s)" % (
        len(kept), noun, ", ".join("%s %s" % pair for pair in kept))
    return Panel("pass", reasons, kept, dropped, session, summary)


# --------------------------------------------------------------------------
# Output parser and tally (Story 2)
# --------------------------------------------------------------------------

VERDICT_LINE = re.compile(r"^#{1,6}\s*(?:EVALUATION_RESULT|REVIEW_RESULT):\s*\**\s*([A-Za-z]+)",
                          re.MULTILINE)
# Accepts every line jev-judge.py EVALUATOR_LINE accepts, plus comma-separated
# multi-ID tags such as `[AC-2.2, AC-2.3]`.
CHECKLIST_LINE = re.compile(
    r"^\s*[-*]\s+\[([ xX])\]\s+.*?`?\[(AC-\d+\.\d+(?:\s*,\s*AC-\d+\.\d+)*)\]`?\s*$")
AC_ID = re.compile(r"AC-\d+\.\d+")
ISSUES_HEADING = re.compile(r"^(#{2,6})\s*Issues Found\b", re.IGNORECASE)
ANY_HEADING = re.compile(r"^(#{1,6})\s")
PLACEHOLDER_LOCATIONS = frozenset({"n/a", "na", "none", "-", "—", "–", "not applicable"})
ISSUE_START = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\*\*Issue:\*\*\s*(.*)$")
ISSUE_FIELD = re.compile(r"^\s*(?:[-*]\s+)?\*\*(Location|Severity|Category):\*\*\s*(.*)$",
                         re.IGNORECASE)
TRAILING_LINE_NO = re.compile(r":\d+(?:-\d+)?$")
KEYED_SEVERITIES = ("Critical", "Major")
KEYED_CATEGORIES = ("security", "architecture")
# Both agents' Severity Definitions rate an unmet acceptance criterion Critical.
AC_SEVERITY = "Critical"
SEVERITY_RANK = {"Critical": 0, "Major": 1}


class Finding(NamedTuple):
    severity: str
    text: str


class Parsed(NamedTuple):
    verdict: Optional[str]
    findings: Dict[str, Finding]  # finding key -> first occurrence


def normalize_location(raw: str) -> Optional[str]:
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
    if path.lower() in PLACEHOLDER_LOCATIONS:
        return None
    return path or None


def _issue_entries(lines: Sequence[str]) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    issues_level = 0  # heading depth of the open Issues Found section; 0 = outside
    current: Optional[Dict[str, str]] = None
    for line in lines:
        heading = ANY_HEADING.match(line)
        if heading:
            issues = ISSUES_HEADING.match(line)
            if issues:
                issues_level = len(issues.group(1))
            elif issues_level and len(heading.group(1)) <= issues_level:
                issues_level = 0
            current = None
            continue
        in_issues = issues_level > 0
        if not in_issues:
            continue
        start = ISSUE_START.match(line)
        if start:
            current = {"issue": start.group(1).strip()}
            entries.append(current)
            continue
        field = ISSUE_FIELD.match(line)
        if field and current is not None:
            current.setdefault(field.group(1).lower(), field.group(2).strip())
    return entries


def parse_output(text: str) -> Parsed:
    """Verdict and finding keys from one Gate 3 agent output."""
    verdict_match = VERDICT_LINE.search(text)
    verdict = verdict_match.group(1).upper() if verdict_match else None
    findings: Dict[str, Finding] = {}
    lines = text.splitlines()
    for line in lines:
        match = CHECKLIST_LINE.match(line)
        if match and match.group(1) == " ":
            for ac in AC_ID.findall(match.group(2)):
                findings.setdefault("ac:%s" % ac, Finding(AC_SEVERITY, line.strip()))
    for entry in _issue_entries(lines):
        severity_word = entry.get("severity", "").split()
        severity = severity_word[0].strip("*[]").capitalize() if severity_word else ""
        category_word = entry.get("category", "").split()
        category = category_word[0].strip("*[]").lower() if category_word else ""
        path = normalize_location(entry.get("location", ""))
        if severity in KEYED_SEVERITIES and category in KEYED_CATEGORIES and path:
            findings.setdefault("%s:%s" % (category, path),
                                Finding(severity, entry.get("issue", "")))
    return Parsed(verdict, findings)


def key_display(key: str) -> str:
    kind, _, rest = key.partition(":")
    if kind == "ac":
        return "%s unmet" % rest
    return "%s %s" % (kind, rest)


def _key_order(key: str) -> Tuple[int, Tuple[int, ...], str]:
    kind, _, rest = key.partition(":")
    if kind == "ac":
        return (0, tuple(int(n) for n in rest[3:].split(".")), "")
    return (1, (), key)


class Source(NamedTuple):
    name: str     # "primary" or the reviewer slug
    vendor: str
    parsed: Parsed


class TallyFinding(NamedTuple):
    key: str
    classification: str  # consensus | advisory | primary-only
    vendors: List[str]   # distinct, primary first, then reviewer order
    severity: str
    texts: List[Dict[str, str]]


class TallyResult(NamedTuple):
    verdict: str          # block | pass | unverifiable
    reasons: List[str]
    primary_verdict: Optional[str]
    vendors: List[str]
    dropped: List[Tuple[str, str]]
    findings: List[TallyFinding]
    summary: str


def _read_output(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return text if text.strip() else None


def tally(origin: str, primary_text: str,
          reviewers: Sequence[Tuple[str, Optional[str]]]) -> TallyResult:
    """Count finding keys across vendors. `reviewers` holds (slug, output text
    or None when the reviewer returned nothing). Raises UsageError when the
    primary output has no verdict line."""
    primary = parse_output(primary_text)
    if primary.verdict is None:
        raise UsageError("primary output has no EVALUATION_RESULT / REVIEW_RESULT line")
    session = origin_vendor(origin)
    if session is None:
        return TallyResult("unverifiable", ["unknown_session_vendor"], primary.verdict,
                           [], [], [], "review-panel: unverifiable — unknown_session_vendor")

    sources = [Source("primary", session, primary)]
    dropped: List[Tuple[str, str]] = []
    for slug, text in reviewers:
        vendor = slug_vendor(slug)
        if vendor is None:
            dropped.append((slug, "unknown_vendor"))
            continue
        if text is None:
            dropped.append((slug, "no_output"))
            continue
        parsed = parse_output(text)
        if parsed.verdict is None:
            dropped.append((slug, "malformed_output"))
            continue
        sources.append(Source(slug, vendor, parsed))

    vendors: List[str] = []
    for source in sources:
        if source.vendor not in vendors:
            vendors.append(source.vendor)
    if len(vendors) == 1:
        return TallyResult("unverifiable", ["no_usable_reviewer"], primary.verdict, vendors,
                           dropped, [], "review-panel: unverifiable — no_usable_reviewer")

    keys = sorted({k for s in sources for k in s.parsed.findings}, key=_key_order)
    findings: List[TallyFinding] = []
    for key in keys:
        raisers = [s for s in sources if key in s.parsed.findings]
        key_vendors = [v for v in vendors if any(s.vendor == v for s in raisers)]
        if len(key_vendors) >= 2:
            classification = "consensus"
        elif key_vendors[0] == session:
            classification = "primary-only"
        else:
            classification = "advisory"
        severity = min((s.parsed.findings[key].severity for s in raisers),
                       key=lambda sev: SEVERITY_RANK.get(sev, 9))
        texts = [{"source": s.name, "vendor": s.vendor, "text": s.parsed.findings[key].text}
                 for s in raisers]
        findings.append(TallyFinding(key, classification, key_vendors, severity, texts))

    consensus = [f for f in findings if f.classification == "consensus"]
    count = "%d vendors, %d consensus finding%s" % (
        len(vendors), len(consensus), "" if len(consensus) == 1 else "s")
    if consensus:
        return TallyResult("block", ["consensus %s" % f.key for f in consensus],
                           primary.verdict, vendors, dropped, findings,
                           "review-panel: block — %s" % count)
    return TallyResult("pass", [], primary.verdict, vendors, dropped, findings,
                       "review-panel: pass — %s" % count)


def _parse_reviewer_arg(value: str) -> Tuple[str, Path]:
    slug, sep, path = value.partition("=")
    if not sep or not slug.strip() or not path.strip():
        raise UsageError("--reviewer expects <slug>=<file>, got %r" % value)
    return slug.strip(), Path(path.strip())


def load_tally(origin: str, primary: Path, reviewer_args: Sequence[str]) -> TallyResult:
    reviewers = [_parse_reviewer_arg(value) for value in reviewer_args]
    primary_text = _read_output(primary)
    if primary_text is None:
        raise UsageError("primary output unreadable or empty: %s" % primary)
    return tally(origin, primary_text, [(slug, _read_output(path)) for slug, path in reviewers])


def cmd_tally(args: argparse.Namespace) -> int:
    result = load_tally(args.origin, Path(args.primary), args.reviewer or [])
    code = 1 if result.verdict == "block" else 0
    if args.json:
        print(json.dumps({
            "verdict": result.verdict,
            "reasons": result.reasons,
            "primary_verdict": result.primary_verdict,
            "vendors": result.vendors,
            "dropped": [{"slug": s, "reason": r} for s, r in result.dropped],
            "findings": [{
                "key": f.key, "display": key_display(f.key),
                "classification": f.classification, "vendors": f.vendors,
                "severity": f.severity, "texts": f.texts,
            } for f in result.findings],
            "summary": result.summary,
        }, sort_keys=True))
        return code
    print(result.verdict)
    for reason in result.reasons:
        print("reason: %s" % reason)
    for slug, reason in result.dropped:
        print("review-panel: dropped %s — %s" % (slug, reason))
    for f in result.findings:
        if f.classification == "advisory":
            print("review-panel: advisory — %s (%s)" % (key_display(f.key), f.vendors[0]))
    for f in result.findings:
        if f.classification == "consensus":
            print("review-panel: block — %s (%s)" % (key_display(f.key), ", ".join(f.vendors)))
    print(result.summary)
    return code


def cmd_status(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    if not repo.is_dir() or not os.access(str(repo), os.R_OK | os.X_OK):
        raise UsageError("repo is not a readable directory: %s" % repo)
    panel = resolve(repo, args.origin, args.platform)
    if args.json:
        print(json.dumps({
            "verdict": panel.verdict,
            "reasons": panel.reasons,
            "reviewers": [{"slug": s, "vendor": v} for s, v in panel.reviewers],
            "dropped": [{"slug": s, "reason": r} for s, r in panel.dropped],
            "session_vendor": panel.session_vendor,
            "platform": args.platform,
            "summary": panel.summary,
        }, sort_keys=True))
        return 0
    print(panel.verdict)
    for reason in panel.reasons:
        print("reason: %s" % reason)
    for slug, vendor in panel.reviewers:
        print("reviewer: %s %s" % (slug, vendor))
    for slug, reason in panel.dropped:
        print("dropped: %s %s" % (slug, reason))
    print(panel.summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("status", help="resolve the Review Panel config line")
    p.add_argument("--repo", default=".")
    p.add_argument("--origin", required=True,
                   help="origin model name captured at command entry")
    p.add_argument("--platform", choices=PLATFORMS, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    t = sub.add_parser("tally", help="count Gate 3 findings across vendors")
    t.add_argument("--origin", required=True)
    t.add_argument("--primary", required=True, help="the Gate 3 agent's output file")
    t.add_argument("--reviewer", action="append", metavar="SLUG=FILE",
                   help="one panel reviewer's output (repeatable)")
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_tally)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    try:
        return args.func(args)
    except UsageError as exc:
        print("review-panel: usage — %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
