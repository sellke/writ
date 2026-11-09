#!/usr/bin/env python3
"""Outcome test for spec 2026-10-25-gate-upgrade-removal-measurement (Story 3, task 3.1).

Once Story 4 commits `trial-report.md`, every `upgrade: <name> verdict=<v>`
line must match the repo state in technical-spec.md → Verdict Execution →
"Repo state the outcome test asserts", and spec.md's status must match the set
of verdicts (spec.md Business Rule 13).

AC-3.1: the live test skips with a reason naming `trial-report.md` while the
report is absent. This file imports only the stdlib and pytest; it never
imports or loads the trial harness, so it keeps guarding the record after
Story 4 deletes the harness.

Story 6 (AC-6.3): Repro First's verdict comes from
`trial-report-repro-first.md` once that file exists, checked against the
substitute trial file `*-repro-first-substitute-trial.json`; the other three
verdicts come from `trial-report.md` and the first trial file (spec.md
Business Rule 13).

AC-3.2, AC-3.3, AC-3.4, and AC-3.5 are run-verified by the orchestrator during
Story 3 (init and presence probes, the arms, the sheet and handoff, the yuss
snapshot, and the awaiting-labels status line). This file does not re-check
that run.

The checks are private helpers over a repo root. Each raises
`AssertionError("upgrade: <name> verdict=<v>: <what>")` at its first failure.
The unit tests at the bottom run them against small fake repos, so the logic
is tested before any report exists.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
# The repo's own status detector; every spec.md status here is read through it.
SPEC_STATUS = REPO_ROOT / "scripts" / "spec-status.py"
SPEC_NAME = "2026-10-25-gate-upgrade-removal-measurement"
# spec.md Business Rule 12: the design-divergence blind trial may remove Gate 0.
BLIND_SPEC_NAME = "2026-10-25-design-divergence"
REPORT_NAME = "trial-report.md"
TRIAL_REL = Path(".writ") / "eval" / "gate-upgrade-trial"
TRIAL_GLOB = "*-gate-upgrade-trial.json"
# Story 6: the Repro First substitute trial (spec.md Business Rule 14).
SUBSTITUTE = "repro-first"
SUBSTITUTE_REPORT_NAME = "trial-report-repro-first.md"
SUBSTITUTE_TRIAL_GLOB = "*-repro-first-substitute-trial.json"
SCHEMA = "gate-upgrade-trial-v1"

UPGRADES = ("gate0-divergence", "safety-fact", "reviewer-filters", "repro-first")
LABELS = ("valid", "invalid")
DECIDED = ("keep", "remove", "absent")
STATUS_DONE = "Complete"
STATUS_OPEN = "In Progress —"
UPGRADE_LINE = re.compile(r"^upgrade: (\S+) verdict=(\S+)")

# technical-spec.md → Upgrades Under Test: (file, text it must contain or None).
GATE0_MARKER = "**Design divergence (boundary-crossing route).**"
PROBES: Dict[str, Tuple[str, Optional[str]]] = {
    "gate0-divergence": ("commands/implement-story.md", GATE0_MARKER),
    "safety-fact": ("skills/blast-radius/SKILL.md", None),
    "reviewer-filters": ("skills/review-judgment-filters/SKILL.md", None),
    "repro-first": ("scripts/repro-order.py", None),
}


class Removal(NamedTuple):
    gone: Tuple[str, ...]     # paths that must not exist
    needles: Tuple[str, ...]  # text no file under `scope` may contain
    scope: Tuple[str, ...]


# technical-spec.md → Verdict Execution → "Repo state the outcome test asserts", `remove` row.
REMOVALS: Dict[str, Removal] = {
    "gate0-divergence": Removal((), ("Gate 0 Divergence", "Design divergence (boundary-crossing route)"),
                                ("commands", ".writ/docs")),
    "safety-fact": Removal(("skills/blast-radius",), ("Safety Fact",),
                           ("commands", "agents", ".writ/docs")),
    "reviewer-filters": Removal(("skills/review-judgment-filters",), ("Reviewer Filters", "reviewer_filters"),
                                ("commands", "agents", ".writ/docs")),
    "repro-first": Removal(("scripts/repro-order.py",), ("Repro First",),
                           ("commands", "agents", "skills", ".writ/docs")),
}


# --- readers -----------------------------------------------------------------


def _fail(name: str, verdict: str, what: str) -> None:
    raise AssertionError("upgrade: %s verdict=%s: %s" % (name, verdict, what))


def _find_report(root: Path, spec_name: str, report_name: str = REPORT_NAME) -> Optional[Path]:
    """The spec's report file; `/status --archive` may have moved the spec."""
    specs = root / ".writ" / "specs"
    for folder in (specs / spec_name, specs / "archive" / spec_name):
        if (folder / report_name).is_file():
            return folder / report_name
    return None


def _source(root: Path, name: str) -> Tuple[Optional[Path], str]:
    """(report, trial-file glob) for one upgrade. Repro First reads the substitute
    pair once trial-report-repro-first.md exists; every other upgrade, and Repro
    First before then, reads trial-report.md and the first trial file."""
    if name == SUBSTITUTE:
        report = _find_report(root, SPEC_NAME, SUBSTITUTE_REPORT_NAME)
        if report is not None:
            return report, SUBSTITUTE_TRIAL_GLOB
    return _find_report(root, SPEC_NAME), TRIAL_GLOB


def _spec_md(root: Path) -> Path:
    specs = root / ".writ" / "specs"
    for folder in (specs / SPEC_NAME, specs / "archive" / SPEC_NAME):
        if folder.is_dir():
            return folder / "spec.md"
    return specs / SPEC_NAME / "spec.md"


def _verdicts(text: str) -> Dict[str, str]:
    """{upgrade: verdict} from the report's `upgrade:` lines; the first line per name wins."""
    found: Dict[str, str] = {}
    for line in text.splitlines():
        match = UPGRADE_LINE.match(line.strip())
        if match:
            found.setdefault(match.group(1), match.group(2))
    return found


def _all_verdicts(root: Path) -> Dict[str, str]:
    """{upgrade: verdict}, each read from its own report (see `_source`)."""
    found: Dict[str, str] = {}
    for name in UPGRADES:
        report = _source(root, name)[0]
        verdict = _verdicts(report.read_text(encoding="utf-8")).get(name) if report else None
        if verdict is not None:
            found[name] = verdict
    return found


def _read_status(spec_md: Path) -> dict:
    """`spec-status.py is-complete --file` JSON, or {} when it reports a blocker."""
    result = subprocess.run([sys.executable, str(SPEC_STATUS), "is-complete", "--file", str(spec_md)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return {}
    try:
        status = json.loads(result.stdout)
    except ValueError:
        return {}
    return status if isinstance(status, dict) else {}


def _probe(root: Path, name: str) -> bool:
    rel, marker = PROBES[name]
    path = root / rel
    if not path.is_file():
        return False
    return marker is None or marker in path.read_bytes().decode("utf-8", errors="ignore")


def _mentions(root: Path, scope: Sequence[str], needle: str) -> List[str]:
    """Repo-relative paths of files at or under `scope` whose text contains needle."""
    hits: List[str] = []
    for rel in scope:
        top = root / rel
        paths: List[Path] = [top] if top.is_file() else []
        for parent, dirs, names in os.walk(str(top)):
            dirs.sort()
            paths += [Path(parent) / name for name in sorted(names)]
        for path in paths:
            try:
                text = path.read_bytes().decode("utf-8", errors="ignore")
            except OSError:
                continue
            if needle in text:
                hits.append(path.relative_to(root).as_posix())
    return hits


def _blind_trial_removed(root: Path) -> bool:
    report = _find_report(root, BLIND_SPEC_NAME)
    if report is None:
        return False
    lines = report.read_text(encoding="utf-8").splitlines()
    return bool(lines) and lines[0].strip() == "remove"


# --- checks ------------------------------------------------------------------


def _trial(root: Path, name: str, verdict: str, glob: str = TRIAL_GLOB) -> dict:
    """The one committed trial file matching `glob`: right schema and a human `labeled_by`."""
    files = sorted((root / TRIAL_REL).glob(glob))
    if len(files) != 1:
        _fail(name, verdict, "%d trial files (need exactly one %s)" % (len(files), (TRIAL_REL / glob).as_posix()))
    try:
        trial = json.loads(files[0].read_text(encoding="utf-8"))
    except ValueError:
        trial = None
    if not isinstance(trial, dict) or trial.get("schema") != SCHEMA:
        _fail(name, verdict, "%s is not a %s trial file" % (files[0].name, SCHEMA))
    labeled_by = trial.get("labeled_by")
    if not isinstance(labeled_by, str) or not labeled_by.strip():
        _fail(name, verdict, "labeled_by is %r (need the labeler's name)" % (labeled_by,))
    return trial


def _check_labels(trial: dict, name: str, verdict: str) -> None:
    for story in trial.get("stories") or []:
        for entry in (story.get("upgrade_only") or []) if isinstance(story, dict) else []:
            if isinstance(entry, dict) and entry.get("upgrade") == name and entry.get("label") not in LABELS:
                _fail(name, verdict, "upgrade-only finding %s %s has label %r"
                      % (entry.get("id"), entry.get("key"), entry.get("label")))


def _check_present(root: Path, trial: dict, name: str, verdict: str) -> None:
    """keep, unverifiable, absent: the presence probe reads as it did at init."""
    upgrade = (trial.get("upgrades") or {}).get(name)
    at_init = upgrade.get("present") if isinstance(upgrade, dict) else None
    if not isinstance(at_init, bool):
        _fail(name, verdict, "trial file has no upgrades.%s.present" % name)
    now = _probe(root, name)
    if now == at_init:
        return
    if name == "gate0-divergence" and at_init and _blind_trial_removed(root):
        return
    _fail(name, verdict, "presence probe %s reads %s, init recorded %s"
          % (PROBES[name][0], str(now).lower(), str(at_init).lower()))


def _check_removed(root: Path, trial: dict, name: str, verdict: str) -> None:
    """remove: the technical-spec removal assertions, by a text scan of the repo."""
    removal = REMOVALS[name]
    for rel in removal.gone:
        if (root / rel).exists():
            _fail(name, verdict, "%s still exists" % rel)
    for needle in removal.needles:
        hits = _mentions(root, removal.scope, needle)
        if hits:
            _fail(name, verdict, "mention %r in %s" % (needle, ", ".join(hits)))


EXPECTED: Dict[str, Callable[[Path, dict, str, str], None]] = {
    "keep": _check_present,
    "unverifiable": _check_present,
    "absent": _check_present,
    "remove": _check_removed,
}


def _check_status(root: Path, name: str, verdict: str, verdicts: Dict[str, str]) -> None:
    """Business Rule 13: Complete when every verdict is decided, else `In Progress — <reason>`."""
    status = _read_status(_spec_md(root))
    value = status.get("matched_value")
    if not status:
        _fail(name, verdict, "spec.md status unreadable (spec-status.py found no status)")
    if all(verdicts.get(upgrade) in DECIDED for upgrade in UPGRADES):
        if status.get("complete") is not True or status.get("canonical_head") != STATUS_DONE:
            _fail(name, verdict, "spec.md status %r (every verdict is decided; need %r)" % (value, STATUS_DONE))
    elif not str(value or "").startswith(STATUS_OPEN):
        _fail(name, verdict, "spec.md status %r (a verdict is unverifiable; need %r...)" % (value, STATUS_OPEN))


def _check_upgrade(root: Path, name: str) -> None:
    report, glob = _source(root, name)
    if report is None:
        _fail(name, "missing", "no %s" % REPORT_NAME)
    verdict = _verdicts(report.read_text(encoding="utf-8")).get(name)
    if verdict is None:
        _fail(name, "missing", "no `upgrade: %s` line in %s" % (name, report.name))
    if verdict not in EXPECTED:
        _fail(name, verdict, "unknown verdict")
    trial = _trial(root, name, verdict, glob)
    _check_labels(trial, name, verdict)
    EXPECTED[verdict](root, trial, name, verdict)
    _check_status(root, name, verdict, _all_verdicts(root))


# --- live check ----------------------------------------------------------------


@pytest.mark.skipif(_find_report(REPO_ROOT, SPEC_NAME) is None,
                    reason="trial-report.md is absent: the human has not labeled the trial yet, "
                           "so there is no verdict to check (Story 4 writes the report)")
@pytest.mark.parametrize("name", UPGRADES, ids=list(UPGRADES))
def test_upgrade_verdict_matches_repo(name):
    _check_upgrade(REPO_ROOT, name)


# --- unit tests on fake repos ---------------------------------------------------


# Files each upgrade's wiring adds in a fake repo: (path, text).
WIRING: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "gate0-divergence": (("commands/implement-story.md", GATE0_MARKER + "\n"),
                         (".writ/docs/config-format.md", "- **Gate 0 Divergence:** off\n")),
    "safety-fact": (("skills/blast-radius/SKILL.md", "---\nname: blast-radius\n---\n"),
                    ("agents/review-agent.md", "### Safety Fact\n")),
    "reviewer-filters": (("skills/review-judgment-filters/SKILL.md", "---\nname: filters\n---\n"),
                         ("agents/review-agent.md", "reviewer_filters: on\n")),
    "repro-first": (("scripts/repro-order.py", "print('pass')\n"),
                    ("agents/coding-agent.md", "- **Repro First:** off\n")),
}
BASE_FILES = ("commands/implement-story.md", "agents/review-agent.md", "agents/coding-agent.md",
              ".writ/docs/config-format.md", "skills/tdd-cycle/SKILL.md")
ALL_KEEP = {name: "keep" for name in UPGRADES}


def _append(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def _report_text(verdicts: Dict[str, str]) -> str:
    open_ = [n for n in UPGRADES if verdicts.get(n) not in DECIDED]
    lines = ["unverifiable" if open_ else "pass"]
    lines += ["reason: %s unlabeled 1" % n for n in open_]
    lines += ["upgrade: %s verdict=%s" % (n, v) for n, v in verdicts.items()]
    return "\n".join(lines + ["gate-upgrade-trial: summary"]) + "\n"


def _make_repo(root: Path, verdicts: Dict[str, str], status: str,
               present: Optional[Dict[str, bool]] = None, labeled_by: Optional[str] = "Adam",
               label: Optional[str] = "valid") -> Path:
    """A fake repo in the state technical-spec.md → Verdict Execution names for each verdict."""
    present = present or {n: verdicts.get(n) != "absent" for n in UPGRADES}
    for rel in BASE_FILES:
        _append(root, rel, "# %s\n" % rel)
    for name in UPGRADES:
        if present[name] and verdicts.get(name) != "remove":
            for rel, text in WIRING[name]:
                _append(root, rel, text)
    spec = root / ".writ" / "specs" / SPEC_NAME
    _append(root, (spec / "spec.md").relative_to(root).as_posix(), "# Spec\n\n> **Status:** %s\n" % status)
    _append(root, (spec / REPORT_NAME).relative_to(root).as_posix(), _report_text(verdicts))
    findings = [{"id": "F%02d" % (i + 1), "upgrade": n, "key": "security:app/%s.ts" % n,
                 "severity": "Major", "label": label, "note": None} for i, n in enumerate(UPGRADES)]
    trial = {"schema": SCHEMA, "upgrades": {n: {"present": present[n]} for n in UPGRADES},
             "stories": [{"story_id": "s/story-1", "upgrade_only": findings}], "labeled_by": labeled_by}
    _append(root, (TRIAL_REL / "2026-10-30-gate-upgrade-trial.json").as_posix(), json.dumps(trial))
    return root


def _check_all(root: Path) -> None:
    for name in UPGRADES:
        _check_upgrade(root, name)


def test_verdicts_read_each_upgrade_line():
    text = ("unverifiable\nreason: repro-first not_exercised_unacknowledged\n"
            "upgrade: gate0-divergence verdict=keep exercised=3/4 upgrade_only=2 valid=1 invalid=1 off_only=0\n"
            "upgrade: repro-first verdict=unverifiable exercised=0/4 reason=not_exercised_unacknowledged\n"
            "gate-upgrade-trial: keep 1\n")
    assert _verdicts(text) == {"gate0-divergence": "keep", "repro-first": "unverifiable"}


@pytest.mark.parametrize("verdicts", [
    ALL_KEEP,
    {"gate0-divergence": "remove", "safety-fact": "remove", "reviewer-filters": "remove", "repro-first": "remove"},
    {"gate0-divergence": "absent", "safety-fact": "keep", "reviewer-filters": "remove", "repro-first": "remove"},
], ids=["all-keep", "all-remove", "mixed"])
def test_decided_repo_with_complete_status_passes(tmp_path, verdicts):
    _check_all(_make_repo(tmp_path, verdicts, "Complete"))


def test_unverifiable_keeps_its_wiring_and_the_spec_stays_in_progress(tmp_path):
    verdicts = dict(ALL_KEEP, **{"repro-first": "unverifiable"})
    _check_all(_make_repo(tmp_path, verdicts, "In Progress — repro-first unlabeled 1"))


@pytest.mark.parametrize("name,rel,needle", [
    ("gate0-divergence", ".writ/docs/config-format.md", "Gate 0 Divergence"),
    ("gate0-divergence", "commands/prototype.md", "Design divergence (boundary-crossing route)"),
    ("safety-fact", "agents/review-agent.md", "Safety Fact"),
    ("reviewer-filters", "commands/implement-story.md", "reviewer_filters"),
    ("repro-first", "skills/tdd-cycle/SKILL.md", "Repro First"),
])
def test_remove_catches_a_leftover_mention(tmp_path, name, rel, needle):
    _make_repo(tmp_path, dict(ALL_KEEP, **{name: "remove"}), "Complete")
    _append(tmp_path, rel, "%s\n" % needle)
    with pytest.raises(AssertionError, match=r"^upgrade: %s verdict=remove: mention .*%s"
                       % (name, re.escape(rel))):
        _check_upgrade(tmp_path, name)


@pytest.mark.parametrize("name,rel", [("safety-fact", "skills/blast-radius/README.md"),
                                      ("reviewer-filters", "skills/review-judgment-filters/SKILL.md"),
                                      ("repro-first", "scripts/repro-order.py")])
def test_remove_catches_a_leftover_path(tmp_path, name, rel):
    _make_repo(tmp_path, dict(ALL_KEEP, **{name: "remove"}), "Complete")
    _append(tmp_path, rel, "x\n")
    with pytest.raises(AssertionError, match=r"^upgrade: %s verdict=remove: .* still exists" % name):
        _check_upgrade(tmp_path, name)


def test_remove_ignores_mentions_outside_its_scope(tmp_path):
    _make_repo(tmp_path, dict(ALL_KEEP, **{"safety-fact": "remove"}), "Complete")
    _append(tmp_path, "README.md", "Safety Fact was removed.\n")
    _append(tmp_path, ".writ/specs/%s/notes.md" % SPEC_NAME, "Safety Fact\n")
    _check_upgrade(tmp_path, "safety-fact")


@pytest.mark.parametrize("name", UPGRADES)
def test_keep_catches_wiring_that_is_gone(tmp_path, name):
    _make_repo(tmp_path, ALL_KEEP, "Complete")
    rel, marker = PROBES[name]
    if marker:
        (tmp_path / rel).write_text("# %s\n" % rel, encoding="utf-8")
    else:
        (tmp_path / rel).unlink()
    with pytest.raises(AssertionError, match=r"^upgrade: %s verdict=keep: presence probe .* reads false, "
                       r"init recorded true" % name):
        _check_upgrade(tmp_path, name)


def test_absent_catches_wiring_that_appeared(tmp_path):
    _make_repo(tmp_path, dict(ALL_KEEP, **{"repro-first": "absent"}), "Complete")
    _append(tmp_path, "scripts/repro-order.py", "x\n")
    with pytest.raises(AssertionError, match=r"^upgrade: repro-first verdict=absent: presence probe"):
        _check_upgrade(tmp_path, "repro-first")


@pytest.mark.parametrize("blind,where,passes", [
    ("remove", "", True),
    ("remove", "archive/", True),
    ("keep", "", False),
    (None, "", False),
])
def test_gate0_may_be_gone_only_when_the_blind_trial_removed_it(tmp_path, blind, where, passes):
    _make_repo(tmp_path, ALL_KEEP, "Complete")
    (tmp_path / "commands" / "implement-story.md").write_text("# Implement story\n", encoding="utf-8")
    if blind is not None:
        _append(tmp_path, ".writ/specs/%s%s/%s" % (where, BLIND_SPEC_NAME, REPORT_NAME),
                "%s\ndivergence-trial: %s\n" % (blind, blind))
    if passes:
        _check_upgrade(tmp_path, "gate0-divergence")
    else:
        with pytest.raises(AssertionError, match=r"^upgrade: gate0-divergence verdict=keep: presence probe"):
            _check_upgrade(tmp_path, "gate0-divergence")


@pytest.mark.parametrize("verdicts,status,passes", [
    (ALL_KEEP, "Complete ✅", True),
    (ALL_KEEP, "In Progress — awaiting human labels (rating-handoff.md)", False),
    (dict(ALL_KEEP, **{"safety-fact": "unverifiable"}), "Complete", False),
    (dict(ALL_KEEP, **{"safety-fact": "unverifiable"}), "In Progress", False),
    (dict(ALL_KEEP, **{"safety-fact": "unverifiable"}), "In Progress — safety-fact unlabeled 1", True),
], ids=["decided-complete", "decided-in-progress", "open-complete", "open-no-reason", "open-in-progress"])
def test_status_follows_the_verdict_set(tmp_path, verdicts, status, passes):
    _make_repo(tmp_path, verdicts, status)
    if passes:
        _check_upgrade(tmp_path, "gate0-divergence")
    else:
        with pytest.raises(AssertionError, match=r"^upgrade: gate0-divergence verdict=keep: spec\.md status"):
            _check_upgrade(tmp_path, "gate0-divergence")


@pytest.mark.parametrize("kwargs,what", [
    ({"labeled_by": None}, "labeled_by is None"),
    ({"labeled_by": "  "}, "labeled_by is '  '"),
    ({"label": None}, "upgrade-only finding F01 security:app/gate0-divergence.ts has label None"),
    ({"label": "maybe"}, "has label 'maybe'"),
])
def test_labels_must_be_complete(tmp_path, kwargs, what):
    _make_repo(tmp_path, ALL_KEEP, "Complete", **kwargs)
    with pytest.raises(AssertionError, match=re.escape(what)):
        _check_upgrade(tmp_path, "gate0-divergence")


def test_trial_file_must_be_exactly_one_with_the_schema(tmp_path):
    _make_repo(tmp_path, ALL_KEEP, "Complete")
    extra = tmp_path / TRIAL_REL / "2026-10-31-gate-upgrade-trial.json"
    extra.write_text("{}", encoding="utf-8")
    with pytest.raises(AssertionError, match="2 trial files"):
        _check_upgrade(tmp_path, "safety-fact")
    extra.unlink()
    (tmp_path / TRIAL_REL / "2026-10-30-gate-upgrade-trial.json").write_text('{"schema": "panel-trial-v1"}',
                                                                            encoding="utf-8")
    with pytest.raises(AssertionError, match="is not a %s trial file" % SCHEMA):
        _check_upgrade(tmp_path, "safety-fact")


def test_a_missing_upgrade_line_fails(tmp_path):
    verdicts = {n: "keep" for n in UPGRADES if n != "reviewer-filters"}
    _make_repo(tmp_path, verdicts, "In Progress — reviewer-filters missing",
               present={n: True for n in UPGRADES})
    with pytest.raises(AssertionError, match=r"^upgrade: reviewer-filters verdict=missing: no `upgrade: "):
        _check_upgrade(tmp_path, "reviewer-filters")


def test_an_archived_spec_is_followed(tmp_path):
    _make_repo(tmp_path, ALL_KEEP, "Complete")
    specs = tmp_path / ".writ" / "specs"
    (specs / "archive").mkdir()
    (specs / SPEC_NAME).rename(specs / "archive" / SPEC_NAME)
    assert _find_report(tmp_path, SPEC_NAME) == specs / "archive" / SPEC_NAME / REPORT_NAME
    _check_all(tmp_path)


# --- Story 6: Repro First reads the substitute report ---------------------------

SUBSTITUTE_TRIAL_NAME = "2026-11-09-repro-first-substitute-trial.json"


def _unwire(root: Path, name: str) -> None:
    """Strip an upgrade's fake wiring, leaving the repo as its removal would."""
    for rel, text in WIRING[name]:
        path = root / rel
        rest = path.read_text(encoding="utf-8").replace(text, "")
        if rel == PROBES[name][0] and PROBES[name][1] is None:
            path.unlink()
        else:
            path.write_text(rest, encoding="utf-8")


def _add_substitute(root: Path, verdict: str, labeled_by: Optional[str] = "Adam (delegated)",
                    label: Optional[str] = "valid", extra: str = "", copies: int = 1) -> Path:
    """The substitute pair Story 5 and Story 6 commit: report plus scoped trial file."""
    spec = (Path(".writ") / "specs" / SPEC_NAME).as_posix()
    report = ["remove" if verdict in DECIDED else "unverifiable",
              "scope: repro-first", "upgrade: repro-first verdict=%s exercised=3/3" % verdict]
    _append(root, "%s/trial-report-repro-first.md" % spec, "\n".join(report) + "\n" + extra)
    findings = [{"id": "F01", "upgrade": "repro-first", "key": "repro:AC-1.1", "severity": "Major",
                 "label": label, "note": None}]
    trial = {"schema": SCHEMA, "scope": ["repro-first"], "upgrades": {"repro-first": {"present": True}},
             "stories": [{"story_id": "s/story-1", "upgrade_only": findings}], "labeled_by": labeled_by}
    for i in range(copies):
        name = SUBSTITUTE_TRIAL_NAME if i == 0 else "2026-11-1%d-repro-first-substitute-trial.json" % i
        _append(root, (TRIAL_REL / name).as_posix(), json.dumps(trial))
    return root


def _substitute_repo(root: Path, verdict: str, status: str, **kwargs) -> Path:
    """First trial: three keeps and Repro First unverifiable; substitute trial: `verdict`."""
    _make_repo(root, dict(ALL_KEEP, **{"repro-first": "unverifiable"}), status)
    if verdict == "remove":
        _unwire(root, "repro-first")
    return _add_substitute(root, verdict, **kwargs)


def test_repro_first_reads_the_substitute_report_when_it_exists(tmp_path):
    """[AC-6.3] spec 2026-10-25-gate-upgrade-removal-measurement Story 6: Repro First's
    `remove` comes from trial-report-repro-first.md, not the first report's `unverifiable`."""
    _check_all(_substitute_repo(tmp_path, "remove", "Complete"))


def test_repro_first_falls_back_to_the_first_report_without_a_substitute(tmp_path):
    """[AC-6.3] Story 6: with no trial-report-repro-first.md, Repro First reads trial-report.md."""
    _make_repo(tmp_path, dict(ALL_KEEP, **{"repro-first": "unverifiable"}), "In Progress — repro-first amendment_requested")
    _unwire(tmp_path, "repro-first")
    with pytest.raises(AssertionError, match=r"^upgrade: repro-first verdict=unverifiable: presence probe"):
        _check_upgrade(tmp_path, "repro-first")


def test_other_upgrades_ignore_the_substitute_report(tmp_path):
    """[AC-6.3] Story 6: the other three verdicts come from trial-report.md even when the
    substitute report carries a line for them."""
    _substitute_repo(tmp_path, "remove", "Complete", extra="upgrade: safety-fact verdict=remove\n")
    _check_upgrade(tmp_path, "safety-fact")


def test_substitute_keep_still_wants_the_wiring(tmp_path):
    """[AC-6.3] Story 6: a substitute `keep` checks the probe against the substitute trial file."""
    _substitute_repo(tmp_path, "keep", "Complete")
    _check_upgrade(tmp_path, "repro-first")
    (tmp_path / "scripts" / "repro-order.py").unlink()
    with pytest.raises(AssertionError, match=r"^upgrade: repro-first verdict=keep: presence probe"):
        _check_upgrade(tmp_path, "repro-first")


@pytest.mark.parametrize("kwargs,what", [
    ({"labeled_by": None}, "labeled_by is None"),
    ({"label": None}, "upgrade-only finding F01 repro:AC-1.1 has label None"),
])
def test_repro_first_labels_come_from_the_substitute_trial(tmp_path, kwargs, what):
    """[AC-6.3] Story 6: the labels check reads the substitute trial file for Repro First."""
    _substitute_repo(tmp_path, "remove", "Complete", **kwargs)
    with pytest.raises(AssertionError, match=r"^upgrade: repro-first verdict=remove: .*" + re.escape(what)):
        _check_upgrade(tmp_path, "repro-first")


def test_substitute_trial_file_must_be_exactly_one(tmp_path):
    """[AC-6.3] Story 6: two substitute trial files fail, as two first-trial files do."""
    _substitute_repo(tmp_path, "remove", "Complete", copies=2)
    with pytest.raises(AssertionError, match=r"2 trial files .*repro-first-substitute-trial\.json"):
        _check_upgrade(tmp_path, "repro-first")


@pytest.mark.parametrize("verdict,status,passes", [
    ("remove", "Complete", True),
    ("remove", "In Progress — repro-first amendment_requested", False),
    ("unverifiable", "In Progress — repro-first unlabeled 1", True),
    ("unverifiable", "Complete", False),
], ids=["sub-remove-complete", "sub-remove-open", "sub-open-open", "sub-open-complete"])
def test_status_uses_the_substitute_verdict(tmp_path, verdict, status, passes):
    """[AC-6.3] Story 6: Business Rule 13 counts Repro First's substitute verdict."""
    _substitute_repo(tmp_path, verdict, status)
    if passes:
        _check_upgrade(tmp_path, "gate0-divergence")
    else:
        with pytest.raises(AssertionError, match=r"^upgrade: gate0-divergence verdict=keep: spec\.md status"):
            _check_upgrade(tmp_path, "gate0-divergence")


def test_live_test_skip_reason_names_the_report():
    marks = [m for m in getattr(test_upgrade_verdict_matches_repo, "pytestmark", []) if m.name == "skipif"]
    assert len(marks) == 1
    assert REPORT_NAME in marks[0].kwargs["reason"]


def test_this_file_imports_only_the_stdlib_and_pytest():
    """[AC-3.1, AC-6.3] stdlib and pytest only; never the trial harness."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add((node.module or "").split(".")[0])
    allowed = {"__future__", "ast", "json", "os", "re", "subprocess", "sys", "pathlib", "typing", "pytest"}
    assert modules <= allowed, sorted(modules - allowed)
