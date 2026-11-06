#!/usr/bin/env python3
"""Retrospective-trial helper for the cross-family review panel (spec
`2026-10-01-cross-family-review-panel`, Story 4).

ADR-032 removed the panel from Gate 3; only the trial subcommands and the
Gate 3 output parser stay. `.writ/eval/gate-upgrade-trial/gate-upgrade-trial.py`
loads this file by path for `_prepare_run`, `PrepareError`, `parse_output`,
`trial_key`, and `_key_order`. This script never spawns a model and never
touches the network.

Subcommands (the trial file holds keys, vendors, severities, and labels,
never reviewer, diff, or story text):
  trial-init    --baseline FILE --out FILE [--force]
  trial-prepare --trial FILE --yuss PATH --story ID [--tmp-root DIR]
                      Fresh `git init` + `fetch --depth 2` under the tmp root;
                      writes diff.patch, story.md, contract.md. yuss is only
                      read (`rev-parse`) and fetched from.
  trial-record  --trial FILE --story ID --arm evaluator|panel --origin "<model>"
                --primary FILE [--reviewer <slug>=FILE …]
                      Keys each output's findings (`ac:AC-N.M` from unchecked
                      tagged checklist lines; `<security|architecture>:<path>`
                      from Critical/Major Issues Found entries). Raw outputs go
                      to .writ/state/panel-trial/<story>/.
  trial-label   --trial FILE --story ID --key KEY --label valid|invalid --note TEXT
  trial-report  --trial FILE [--json]
                      `pass` with `reason: keep` or `reason: remove`, or
                      `unverifiable`; always exit 0.

`trial-init`, `trial-prepare`, `trial-record`, and `trial-label` print `pass`
first when they did their job, then their detail lines and summary.
`trial-report` prints its verdict line first; a trial word that is not a
verdict (`keep`, `remove`) is the first `reason:` line. `--json` prints one
object instead, with that word as its `verdict`.

Exit 0: ran. Exit 2: usage (unreadable or malformed trial or baseline file,
unknown story, unreachable commit, malformed `--reviewer`, primary output
missing or without a verdict line); a refusal writes nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple


# The only vendor knowledge Writ holds; `trial-record` resolves the session
# and reviewer vendors through it. Slug prefixes are matched literally,
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


# --------------------------------------------------------------------------
# Output parser (Story 2)
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


def _key_order(key: str) -> Tuple[int, Tuple[int, ...], str]:
    kind, _, rest = key.partition(":")
    if kind == "ac":
        return (0, tuple(int(n) for n in rest[3:].split(".")), "")
    return (1, (), key)


class Source(NamedTuple):
    name: str     # "primary" or the reviewer slug
    vendor: str
    parsed: Parsed


def _read_output(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return text if text.strip() else None


def _parse_reviewer_arg(value: str) -> Tuple[str, Path]:
    slug, sep, path = value.partition("=")
    if not sep or not slug.strip() or not path.strip():
        raise UsageError("--reviewer expects <slug>=<file>, got %r" % value)
    return slug.strip(), Path(path.strip())


# The check-shape line 1 for a trial word that is not itself a verdict; the
# word follows as the first `reason:` line.
PANEL_WORD_VERDICT = {"keep": "pass", "remove": "pass"}


def _print_verdict(word: str) -> None:
    verdict = PANEL_WORD_VERDICT.get(word, word)
    print(verdict)
    if verdict != word:
        print("reason: %s" % word)


# --- Retrospective trial (Story 4) ------------------------------------------
#
# The committed trial file holds story identity, finding keys, vendors,
# severities, and labels — never reviewer, diff, source, or story text
# (Business Rule 11). Raw outputs stay under gitignored `.writ/state/`.

TRIAL_SCHEMA = "panel-trial-v1"
TRIAL_STORIES = 4
IDENTITY_FIELDS = ("story_id", "story_path", "spec_folder", "story_commit", "parent_sha")
ARMS = ("evaluator", "panel")
LABELS = ("valid", "invalid")
NOTE_MAX = 200
SHA = re.compile(r"^[0-9a-f]{7,40}$")
SAFE_REL = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]*$")
RAW_ROOT = Path(".writ/state/panel-trial")
PATH_SHAPED = re.compile(r"^[A-Za-z0-9._@+/\[\]()-]+$")
CONTRACT_HEADING = re.compile(r"^## Specification Contract\b.*$", re.MULTILINE)
# Specs written before the heading was renamed (e.g. the 2026-07-24 baseline spec).
LEGACY_CONTRACT_HEADING = re.compile(r"^## Contract Summary\b.*$", re.MULTILINE)
NEXT_H2 = re.compile(r"^## ", re.MULTILINE)
TRIAL_CAVEAT = "sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case"
# Inherited repository redirects would point `git -C` somewhere else.
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR")


def _safe_rel(value: str) -> bool:
    return bool(SAFE_REL.match(value)) and ".." not in value.split("/")


def _story_slug(story_id: str) -> str:
    return story_id.replace("/", "--")


def _plural(count: int, word: str) -> str:
    if count == 1:
        return "1 %s" % word
    consonant_y = word.endswith("y") and word[-2:-1] not in ("a", "e", "i", "o", "u")
    return "%d %s" % (count, word[:-1] + "ies" if consonant_y else word + "s")


def _write_json_atomic(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.tmp" % path.name)
    tmp.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def _load_json(path: Path, what: str) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise UsageError("%s unreadable: %s (%s)" % (what, path, exc.__class__.__name__))
    if not isinstance(doc, dict):
        raise UsageError("%s is not a JSON object: %s" % (what, path))
    return doc


def _load_trial(path: Path) -> dict:
    doc = _load_json(path, "trial file")
    stories = doc.get("stories")
    if doc.get("schema") != TRIAL_SCHEMA or not isinstance(stories, list):
        raise UsageError("not a %s file: %s" % (TRIAL_SCHEMA, path))
    if len(stories) != TRIAL_STORIES:
        raise UsageError("trial file must hold %d stories, has %d" % (TRIAL_STORIES, len(stories)))
    return doc


def _trial_story(doc: dict, story_id: str) -> dict:
    for story in doc["stories"]:
        if isinstance(story, dict) and story.get("story_id") == story_id:
            return story
    raise UsageError("story not in trial: %s" % story_id)


def trial_skeleton(baseline: dict, baseline_path: str) -> dict:
    selection = baseline.get("selection")
    if not isinstance(selection, list) or len(selection) != TRIAL_STORIES:
        raise UsageError("baseline selection must list %d stories" % TRIAL_STORIES)
    stories = []
    for entry in selection:
        if not isinstance(entry, dict):
            raise UsageError("baseline selection entry is not an object")
        identity = {}
        for field in IDENTITY_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value:
                raise UsageError("baseline selection entry lacks %s" % field)
            identity[field] = value
        for field in ("story_commit", "parent_sha"):
            if not SHA.match(identity[field]):
                raise UsageError("%s is not a commit SHA: %r" % (field, identity[field]))
        for field in ("story_id", "story_path", "spec_folder"):
            if not _safe_rel(identity[field]):
                raise UsageError("%s is not a safe relative path: %r" % (field, identity[field]))
        identity.update(arms={}, panel_only=[])
        stories.append(identity)
    if len({s["story_id"] for s in stories}) != len(stories):
        raise UsageError("baseline selection repeats a story_id")
    return {"schema": TRIAL_SCHEMA, "baseline": baseline_path, "stories": stories}


def cmd_trial_init(args: argparse.Namespace) -> int:
    out = Path(args.out)
    if out.exists() and not args.force:
        raise UsageError("refusing to overwrite %s without --force" % out)
    doc = trial_skeleton(_load_json(Path(args.baseline), "baseline"), args.baseline)
    _write_json_atomic(out, doc)
    print("pass")
    for story in doc["stories"]:
        print("story: %s %s" % (story["story_id"], story["story_commit"][:12]))
    print("review-panel: trial initialized — %s, no arms recorded" %
          _plural(len(doc["stories"]), "story"))
    return 0


def _git_env() -> Dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in GIT_REDIRECTS}


def _git(cwd: Path, *args: str) -> Optional[str]:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                          encoding="utf-8", errors="replace", env=_git_env())
    return proc.stdout if proc.returncode == 0 else None


def _reachable(yuss: Path, sha: str) -> bool:
    return _git(yuss, "rev-parse", "--verify", "--quiet", "%s^{commit}" % sha) is not None


def _show_first(checkout: Path, commit: str, paths: Sequence[str]) -> Optional[str]:
    for rel in paths:
        text = _git(checkout, "show", "%s:%s" % (commit, rel))
        if text is not None:
            return text
    return None


def extract_contract(spec_text: str) -> Optional[str]:
    match = CONTRACT_HEADING.search(spec_text) or LEGACY_CONTRACT_HEADING.search(spec_text)
    if match is None:
        return None
    rest = spec_text[match.end():]
    end = NEXT_H2.search(rest)
    return spec_text[match.start():match.end() + (end.start() if end else len(rest))].rstrip() + "\n"


class PrepareError(Exception):
    """A trial-prepare failure; the run directory is removed."""


def _prepare_run(yuss: Path, story: dict, run: Path) -> Dict[str, Path]:
    checkout = run / "checkout"
    checkout.mkdir(parents=True)
    commit, parent = story["story_commit"], story["parent_sha"]
    if _git(checkout, "init", "-q") is None:
        raise PrepareError("git init failed")
    if _git(checkout, "fetch", "-q", "--depth", "2", "--", str(yuss), commit) is None:
        raise PrepareError("fetch of %s failed" % commit[:12])
    if _git(checkout, "checkout", "-q", "FETCH_HEAD") is None:
        raise PrepareError("checkout of %s failed" % commit[:12])
    fetch_head = checkout / ".git" / "FETCH_HEAD"
    if fetch_head.exists():
        fetch_head.unlink()
    head = (_git(checkout, "rev-parse", "HEAD") or "").strip()
    if not head.startswith(commit) and head != commit:
        raise PrepareError("checked-out %s is not story_commit %s" % (head[:12], commit[:12]))
    if _git(checkout, "cat-file", "-e", "%s^{commit}" % parent) is None:
        raise PrepareError("parent %s not reachable at depth 2" % parent[:12])
    diff = _git(checkout, "diff", "--no-color", "--no-ext-diff", parent, commit)
    if diff is None:
        raise PrepareError("git diff %s..%s failed" % (parent[:12], commit[:12]))
    active = ".writ/specs/%s" % story["spec_folder"]
    archived = str(Path(story["story_path"]).parent.parent)
    stem = Path(story["story_path"]).name
    story_text = _show_first(checkout, commit, ("%s/user-stories/%s" % (active, stem),
                                                story["story_path"]))
    if story_text is None:
        raise PrepareError("story file not found at %s" % commit[:12])
    spec_text = _show_first(checkout, commit, ("%s/spec.md" % active, "%s/spec.md" % archived))
    contract = extract_contract(spec_text) if spec_text is not None else None
    if contract is None:
        raise PrepareError("no ## Specification Contract (or ## Contract Summary) in the spec at %s"
                           % commit[:12])
    paths = {"checkout": checkout, "diff": run / "diff.patch",
             "story": run / "story.md", "contract": run / "contract.md"}
    paths["diff"].write_text(diff, encoding="utf-8")
    paths["story"].write_text(story_text, encoding="utf-8")
    paths["contract"].write_text(contract, encoding="utf-8")
    return paths


def cmd_trial_prepare(args: argparse.Namespace) -> int:
    doc = _load_trial(Path(args.trial))
    story = _trial_story(doc, args.story)
    sid = story["story_id"]
    yuss = Path(args.yuss).resolve()
    if not yuss.is_dir():
        raise UsageError("%s: yuss path missing: %s" % (sid, yuss))
    for field in ("story_commit", "parent_sha"):
        if not SHA.match(story.get(field, "")) or not _reachable(yuss, story[field]):
            raise UsageError("%s: %s %s unreachable in %s" % (sid, field, story.get(field), yuss))
    tmp_root = Path(args.tmp_root or os.environ.get("TMPDIR") or "/tmp")
    run = tmp_root / ("writ-panel-trial-%s" % _story_slug(sid))
    if run.exists():
        shutil.rmtree(str(run))
    try:
        paths = _prepare_run(yuss, story, run)
    except (PrepareError, OSError) as exc:
        shutil.rmtree(str(run), ignore_errors=True)
        raise UsageError("%s: %s" % (sid, exc))
    print("pass")
    print("checkout: %s" % paths["checkout"])
    print("diff: %s" % paths["diff"])
    print("story: %s" % paths["story"])
    print("contract: %s" % paths["contract"])
    print("review-panel: prepared %s at %s" % (sid, story["story_commit"][:12]))
    return 0


def trial_key(key: str) -> str:
    """The key as stored in the trial file. A Location that is not path-shaped
    may be prose or source a reviewer typed; it is stored as a digest, which
    still matches the same Location across arms."""
    category, _, rest = key.partition(":")
    if category == "ac" or PATH_SHAPED.match(rest):
        return key
    return "%s:#%s" % (category, hashlib.sha256(rest.encode("utf-8")).hexdigest()[:12])


def _arm_keys(sources: Sequence[Source]) -> List[Dict[str, object]]:
    keys = sorted({k for s in sources for k in s.parsed.findings}, key=_key_order)
    out = []
    for key in keys:
        raisers = [s for s in sources if key in s.parsed.findings]
        vendors: List[str] = []
        for source in raisers:
            if source.vendor not in vendors:
                vendors.append(source.vendor)
        severity = min((s.parsed.findings[key].severity for s in raisers),
                       key=lambda sev: SEVERITY_RANK.get(sev, 9))
        out.append({"key": trial_key(key), "vendors": vendors, "severity": severity})
    return out


def panel_only_findings(story: dict) -> List[Dict[str, object]]:
    """Keys a panel vendor raised in the `panel` arm that the `evaluator` arm
    did not raise. Labels survive for keys that stay panel-only."""
    panel = story.get("arms", {}).get("panel")
    if not panel:
        return []
    evaluator = story["arms"].get("evaluator") or {"keys": []}
    seen = {k["key"] for k in evaluator["keys"]}
    previous = {f["key"]: f for f in story.get("panel_only", [])}
    found = []
    for entry in panel["keys"]:
        panel_vendors = [v for v in entry["vendors"] if v != panel["session_vendor"]]
        if not panel_vendors or entry["key"] in seen:
            continue
        old = previous.get(entry["key"], {})
        found.append({"key": entry["key"], "vendors": panel_vendors,
                      "severity": entry["severity"],
                      "label": old.get("label"), "note": old.get("note")})
    return found


def cmd_trial_record(args: argparse.Namespace) -> int:
    if not Path(".writ").is_dir():
        raise UsageError("run trial-record from the repo root (no .writ/ here); raw outputs "
                         "belong under the gitignored .writ/state/")
    trial_path = Path(args.trial)
    doc = _load_trial(trial_path)
    story = _trial_story(doc, args.story)
    reviewers = [_parse_reviewer_arg(value) for value in args.reviewer or []]
    if args.arm == "evaluator" and reviewers:
        raise UsageError("the evaluator arm takes no --reviewer")
    if args.arm == "panel" and not reviewers:
        raise UsageError("the panel arm needs at least one --reviewer")
    session = origin_vendor(args.origin)
    if session is None:
        raise UsageError("unknown session vendor for origin %r" % args.origin)
    primary_text = _read_output(Path(args.primary))
    if primary_text is None:
        raise UsageError("primary output unreadable or empty: %s" % args.primary)
    primary = parse_output(primary_text)
    if primary.verdict is None:
        raise UsageError("primary output has no EVALUATION_RESULT / REVIEW_RESULT line")

    sources = [Source("primary", session, primary)]
    raw = {"primary": primary_text}
    dropped: List[Dict[str, str]] = []
    for slug, path in reviewers:
        text = _read_output(path)
        vendor = slug_vendor(slug)
        if text is not None:
            raw[slug] = text
        if vendor is None:
            dropped.append({"slug": slug, "reason": "unknown_vendor"})
        elif text is None:
            dropped.append({"slug": slug, "reason": "no_output"})
        else:
            parsed = parse_output(text)
            if parsed.verdict is None:
                dropped.append({"slug": slug, "reason": "malformed_output"})
            else:
                sources.append(Source(slug, vendor, parsed))

    raw_dir = RAW_ROOT / _story_slug(story["story_id"])
    for name in raw:
        if not _safe_rel(name) or "/" in name:
            raise UsageError("reviewer slug is not a safe file name: %r" % name)
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, text in raw.items():
        (raw_dir / ("%s-%s.md" % (args.arm, name))).write_text(text, encoding="utf-8")

    story["arms"][args.arm] = {"origin": args.origin, "session_vendor": session,
                               "primary_verdict": primary.verdict,
                               "reviewers": [s for s, _ in reviewers],
                               "dropped": dropped, "keys": _arm_keys(sources)}
    story["panel_only"] = panel_only_findings(story)
    _write_json_atomic(trial_path, doc)

    print("pass")
    for entry in dropped:
        print("review-panel: dropped %s — %s" % (entry["slug"], entry["reason"]))
    print("review-panel: recorded %s %s — %s, %s" % (
        story["story_id"], args.arm, _plural(len(story["arms"][args.arm]["keys"]), "key"),
        _plural(len(story["panel_only"]), "panel-only finding")))
    return 0


def cmd_trial_label(args: argparse.Namespace) -> int:
    trial_path = Path(args.trial)
    doc = _load_trial(trial_path)
    story = _trial_story(doc, args.story)
    if args.label not in LABELS:
        raise UsageError("--label must be valid or invalid")
    note = args.note
    if len(note) > NOTE_MAX or "\n" in note or "\r" in note or "```" in note:
        raise UsageError("--note must be one line of at most %d characters, no code block" %
                         NOTE_MAX)
    finding = next((f for f in story["panel_only"] if f["key"] == args.key), None)
    if finding is None:
        raise UsageError("%s is not a panel-only finding for %s" % (args.key, args.story))
    finding["label"], finding["note"] = args.label, note
    _write_json_atomic(trial_path, doc)
    print("pass")
    print("review-panel: labeled %s %s %s" % (args.story, args.key, args.label))
    return 0


def trial_verdict(doc: dict) -> Dict[str, object]:
    reasons: List[str] = []
    rows = []
    missing_stories = unlabeled = valid = total = 0
    for story in doc["stories"]:
        arms = [arm for arm in ARMS if arm in story.get("arms", {})]
        absent = [arm for arm in ARMS if arm not in arms]
        if absent:
            missing_stories += 1
            reasons.extend("missing_arm %s %s" % (story["story_id"], arm) for arm in absent)
        findings = story.get("panel_only", [])
        counts = {label: sum(1 for f in findings if f.get("label") == label) for label in LABELS}
        open_keys = [f["key"] for f in findings if f.get("label") not in LABELS]
        reasons.extend("unlabeled %s %s" % (story["story_id"], key) for key in open_keys)
        unlabeled += len(open_keys)
        valid += counts["valid"]
        total += len(findings)
        rows.append({"story_id": story["story_id"], "arms": arms, "panel_only": len(findings),
                     "valid": counts["valid"], "invalid": counts["invalid"],
                     "unlabeled": len(open_keys)})
    if unlabeled or missing_stories:
        verdict = "unverifiable"
        parts = []
        if unlabeled:
            parts.append("%d unlabeled" % unlabeled)
        if missing_stories:
            parts.append("%s missing an arm" % _plural(missing_stories, "story"))
        summary = "review-panel: unverifiable — %s" % "; ".join(parts)
    else:
        verdict = "keep" if valid else "remove"
        summary = "review-panel: %s — %d valid of %s, %s" % (
            verdict, valid, _plural(total, "panel-only finding"),
            _plural(len(doc["stories"]), "story"))
    return {"verdict": verdict, "reasons": reasons if verdict == "unverifiable" else [],
            "stories": rows, "caveat": TRIAL_CAVEAT, "summary": summary}


def cmd_trial_report(args: argparse.Namespace) -> int:
    report = trial_verdict(_load_trial(Path(args.trial)))
    if args.json:
        print(json.dumps(report, sort_keys=True))
        return 0
    _print_verdict(report["verdict"])
    for reason in report["reasons"]:
        print("reason: %s" % reason)
    for row in report["stories"]:
        print("story: %s arms=%s panel_only=%d valid=%d invalid=%d unlabeled=%d" % (
            row["story_id"], ",".join(row["arms"]) or "none", row["panel_only"],
            row["valid"], row["invalid"], row["unlabeled"]))
    print(report["caveat"])
    print(report["summary"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("trial-init", help="start a panel-trial-v1 file from a baseline")
    p.add_argument("--baseline", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_trial_init)

    p = sub.add_parser("trial-prepare", help="build one story's read-only trial inputs")
    p.add_argument("--trial", required=True)
    p.add_argument("--yuss", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--tmp-root", default=None)
    p.set_defaults(func=cmd_trial_prepare)

    p = sub.add_parser("trial-record", help="record one arm's finding keys")
    p.add_argument("--trial", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--origin", required=True)
    p.add_argument("--primary", required=True)
    p.add_argument("--reviewer", action="append", metavar="SLUG=FILE")
    p.set_defaults(func=cmd_trial_record)

    p = sub.add_parser("trial-label", help="label one panel-only finding")
    p.add_argument("--trial", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--note", required=True)
    p.set_defaults(func=cmd_trial_label)

    p = sub.add_parser("trial-report", help="score the trial (pass with keep or remove, "
                                            "or unverifiable)")
    p.add_argument("--trial", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_trial_report)
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
