#!/usr/bin/env python3
"""Outcome tests for the design divergence trial (spec 2026-10-25-design-divergence, Story 5).

AC-5.5: once `trial-report.md` is committed, its first line (`keep`, `remove`,
or `unverifiable`) must match the repo state in technical-spec.md → Verdict
Execution. The live check skips while the report is absent. The verdict checks
are pure functions over a repo root, and the unit tests at the bottom run them
against small fake repos, so the logic is tested before any report exists.

AC-5.1, AC-5.2, AC-5.3, and AC-5.4 are verified by the orchestrator's run and
its check of `rating-handoff.md`. This file adds structural checks for them
(briefs, shared prompt template, trial file, raw arms, rating sheet, renders,
handoff), and each skips while its files are absent. It does not assert that
the drafts came from independent spawns at one tier; that part is run-verified.

Stdlib and pytest only. It never imports or loads `scripts/divergence-trial.py`,
so it keeps guarding the record after Story 6 deletes the harness.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
# The repo's own status detector; every spec.md status in this file is read through it.
SPEC_STATUS = REPO_ROOT / "scripts" / "spec-status.py"
SPEC_NAME = "2026-10-25-design-divergence"
TRIAL_REL = Path(".writ") / "eval" / "divergence-trial"
TRIAL_GLOB = "*-divergence-trial.json"
SCHEMA = "divergence-trial-v1"

READ_LINE = "Read skills/design-divergence/SKILL.md"
CALLERS = ("commands/prototype.md", "commands/implement-story.md")
SKILL_DIR = "skills/design-divergence"
SKILL_FILE = SKILL_DIR + "/SKILL.md"
# technical-spec.md → Verdict Execution, `remove` row.
REMOVE_SKILL_SCOPE = ("commands", "adapters", "README.md", "SKILL.md", ".writ/manifest.yaml", "plugins")
REMOVE_GATE_SCOPE = ("commands", ".writ/docs")

STATUS_KEEP = "Complete"
STATUS_REMOVE = "Closed — Not Implemented"
STATUS_AWAITING = "In Progress — awaiting blind rating (rating-handoff.md)"
VERDICTS = ("keep", "remove", "unverifiable")

BRIEFS = {"ui-1": "ui", "ui-2": "ui", "api-1": "api", "api-2": "api",
          "data-model-1": "data-model", "data-model-2": "data-model"}
ARMS = ("axes", "naive")
SETS = ("X", "Y")
DRAFTS = 3
BRIEF_MAX_LINES = 10
FIELDS = ("distinct_X", "distinct_Y", "more_distinct", "render_only_enough", "note")
CHOICES = {"more_distinct": ("X", "Y", "tie"), "render_only_enough": ("yes", "no")}
NOTE_MAX = 200
PLACEHOLDERS = ("{brief}", "{caller_usage}", "{axis_combination}", "{persona}")
# Shared by both arms so draft length and self-containment cannot mark a set.
TEMPLATE_RULES = ("15 to 25 lines", "stands alone")
# The axes prompt keeps its inputs out of the drafts (Gate 3 DEV-010: drafts said
# "caller lines unchanged", which marked the axes set).
AXES_TELL = "show the changed lines"
AXES_PRIVACY = ("Treat these lines as private input", "Do not mention the persona, the axis combination, "
                "or this prompt")
HANDOFF_LITERALS = ("rating-sheet.md", "divergence-trial.py rate", "--rated-by",
                    "divergence-trial.py report", "raw/", "key.json", "divergence-trial.json",
                    "did not rate") + FIELDS

TEMPLATE_RE = re.compile(r"^```text\n(.*?)^```$", re.MULTILINE | re.DOTALL)
DRAFT_RE = re.compile(r"^## Draft\b", re.MULTILINE)
ARM_NAME_RE = re.compile(r"\b(axes|naive)\b", re.IGNORECASE)
# Places an arm label could leak; draft text may use the words freely ("shared axes").
SET_WITH_ARM_RE = re.compile(r"\bSet [XY]\b.*\b(axes|naive)\b|\b(axes|naive)\b.*\bSet [XY]\b",
                             re.IGNORECASE)
BRACKETED_ARM_RE = re.compile(r"[(\[]\s*(axes|naive)\s*[)\]]", re.IGNORECASE)
KEY_LABEL_RE = re.compile(r"\barm\b[\"']?\s*[:=]\s*[\"']?(axes|naive)\b", re.IGNORECASE)
EXTERNAL_ASSET_RE = re.compile(r"<(script|link)\b[^>]*\b(src|href)\s*=\s*[\"']?(https?:)?//",
                               re.IGNORECASE)


# --- shared readers ---------------------------------------------------------


def spec_dir(root: Path) -> Path:
    """The spec folder; `/status --archive` moves a Complete spec under archive/."""
    specs = root / ".writ" / "specs"
    for candidate in (specs / SPEC_NAME, specs / "archive" / SPEC_NAME):
        if candidate.is_dir():
            return candidate
    return specs / SPEC_NAME


def read_status(spec_md: Path, script: Path = SPEC_STATUS) -> dict:
    """spec.md's status as `spec-status.py is-complete` reads it.

    Returns its JSON (`complete`, `matched_value`, `canonical_head`, ...), or {}
    when the detector reports a blocker such as a missing file.
    """
    result = subprocess.run([sys.executable, str(script), "is-complete", "--file", str(spec_md)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return {}
    try:
        status = json.loads(result.stdout)
    except ValueError:
        return {}
    return status if isinstance(status, dict) else {}


def spec_status(root: Path) -> dict:
    return read_status(spec_dir(root) / "spec.md")


def status_is(status: dict, head: str) -> bool:
    """True when the detector puts the status in the complete family under `head`."""
    return status.get("complete") is True and status.get("canonical_head") == head


def report_path(root: Path) -> Path:
    return spec_dir(root) / "trial-report.md"


def parse_report(text: str) -> Tuple[str, List[str]]:
    """(first line, distinct `reason:` codes in order). A code is the reason's first word."""
    lines = text.splitlines()
    verdict = lines[0].strip() if lines else ""
    codes: List[str] = []
    for line in lines:
        if line.startswith("reason:"):
            words = line[len("reason:"):].split()
            if words and words[0] not in codes:
                codes.append(words[0])
    return verdict, codes


def trial_files(root: Path) -> List[Path]:
    return sorted((root / TRIAL_REL).glob(TRIAL_GLOB))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_under(root: Path, rels: Sequence[str]) -> List[Path]:
    """Every regular file at or below each relative path, in a stable order."""
    found: List[Path] = []
    for rel in rels:
        path = root / rel
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            for parent, dirs, names in os.walk(str(path)):
                dirs.sort()
                found += [Path(parent) / name for name in sorted(names)]
    return found


def mentions(root: Path, rels: Sequence[str], needle: str) -> List[str]:
    """`mention <needle> <path>` for each file under `rels` whose text contains needle."""
    hits = []
    for path in files_under(root, rels):
        text = path.read_bytes().decode("utf-8", errors="ignore")
        if needle in text:
            hits.append("mention %s %s" % (needle, path.relative_to(root).as_posix()))
    return hits


# --- verdict execution (AC-5.5) ----------------------------------------------


def wiring_problems(root: Path) -> List[str]:
    """The skill exists and both callers carry its Read line (keep and unverifiable)."""
    problems = []
    if not (root / SKILL_FILE).is_file():
        problems.append("skill_missing %s" % SKILL_FILE)
    for caller in CALLERS:
        path = root / caller
        if not path.is_file() or READ_LINE not in path.read_text(encoding="utf-8"):
            problems.append("read_line_missing %s" % caller)
    return problems


def rating_problems(trial: dict) -> List[str]:
    """`rated_by` is a name and every one of the six briefs has all five valid fields."""
    problems = []
    rater = trial.get("rated_by")
    if not isinstance(rater, str) or not rater.strip():
        problems.append("rated_by empty")
    ids = sorted(b.get("id") for b in trial.get("briefs", []) if isinstance(b, dict))
    if ids != sorted(BRIEFS):
        problems.append("briefs %s (need %s)" % (",".join(map(str, ids)), ",".join(sorted(BRIEFS))))
    ratings = trial.get("ratings")
    ratings = ratings if isinstance(ratings, dict) else {}
    for bid in sorted(BRIEFS):
        rating = ratings.get(bid)
        if not isinstance(rating, dict):
            problems.append("rating_missing %s" % bid)
            continue
        for field in FIELDS:
            value = rating.get(field)
            if field == "note":
                ok = isinstance(value, str) and bool(value.strip()) and len(value) <= NOTE_MAX \
                    and "\n" not in value
            elif field.startswith("distinct_"):
                ok = not isinstance(value, bool) and value in (1, 2, 3)
            else:
                ok = value in CHOICES[field]
            if not ok:
                problems.append("rating_invalid %s %s=%r" % (bid, field, value))
    return problems


def keep_problems(root: Path) -> List[str]:
    problems = wiring_problems(root)
    status = spec_status(root)
    if not status_is(status, STATUS_KEEP):
        problems.append("status %r (need %r)" % (status.get("matched_value"), STATUS_KEEP))
    files = trial_files(root)
    if len(files) != 1:
        problems.append("trial_files %d (need exactly one %s)" % (len(files), TRIAL_REL / TRIAL_GLOB))
        return problems
    try:
        trial = json.loads(files[0].read_text(encoding="utf-8"))
    except ValueError:
        return problems + ["trial_unreadable %s" % files[0].name]
    if not isinstance(trial, dict):
        return problems + ["trial_unreadable %s" % files[0].name]
    return problems + rating_problems(trial)


def remove_problems(root: Path) -> List[str]:
    problems = []
    if (root / SKILL_DIR).exists():
        problems.append("skill_present %s" % SKILL_DIR)
    problems += mentions(root, REMOVE_SKILL_SCOPE, "design-divergence")
    problems += mentions(root, REMOVE_GATE_SCOPE, "Gate 0 Divergence")
    status = spec_status(root)
    if not status_is(status, STATUS_REMOVE):
        problems.append("status %r (need %r)" % (status.get("matched_value"), STATUS_REMOVE))
    return problems


def unverifiable_problems(root: Path, codes: Sequence[str]) -> List[str]:
    """Nothing acted on: the wiring stays, and the status names a blocking reason."""
    problems = wiring_problems(root)
    status = spec_status(root)
    value = status.get("matched_value") or ""
    if not status:
        problems.append("status unreadable (spec-status.py found no status)")
    elif status.get("complete") is not False:
        problems.append("status %r (an unverifiable report is never acted on)" % value)
    if not codes:
        problems.append("report_reason_missing")
    elif not any(code in value for code in codes):
        problems.append("status_reason %r names none of %s" % (value, ", ".join(codes)))
    return problems


def verdict_problems(root: Path) -> List[str]:
    verdict, codes = parse_report(report_path(root).read_text(encoding="utf-8"))
    if verdict == "keep":
        return keep_problems(root)
    if verdict == "remove":
        return remove_problems(root)
    if verdict == "unverifiable":
        return unverifiable_problems(root, codes)
    return ["verdict_unknown %r" % verdict]


# --- trial inputs and run (AC-5.1 to AC-5.4, structural) --------------------


def brief_problems(root: Path) -> List[str]:
    """Exactly the six briefs, each headed `id:` / `medium:` and at most ten lines."""
    briefs_dir = root / TRIAL_REL / "briefs"
    problems = []
    for bid, medium in sorted(BRIEFS.items()):
        path = briefs_dir / ("%s.md" % bid)
        if not path.is_file():
            problems.append("brief_missing %s" % bid)
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > BRIEF_MAX_LINES:
            problems.append("brief_too_long %s %d lines (max %d)" % (bid, len(lines), BRIEF_MAX_LINES))
        if lines[:2] != ["id: %s" % bid, "medium: %s" % medium]:
            problems.append("brief_header %s (need 'id: %s' then 'medium: %s')" % (bid, bid, medium))
    expected = {"%s.md" % bid for bid in BRIEFS}
    for path in sorted(briefs_dir.glob("*.md")):
        if path.name not in expected:
            problems.append("brief_unexpected %s" % path.name)
    return problems


def shared_template(text: str) -> Optional[str]:
    """The body of the first ```text fence: the output template both prompts share."""
    match = TEMPLATE_RE.search(text)
    return match.group(1) if match else None


def prompt_problems(root: Path) -> List[str]:
    prompts = root / TRIAL_REL / "prompts"
    texts = {}
    problems = []
    for arm in ("naive", "axes"):
        path = prompts / ("%s.md" % arm)
        if path.is_file():
            texts[arm] = path.read_text(encoding="utf-8")
        else:
            problems.append("prompt_missing %s" % arm)
    if problems:
        return problems
    templates = {arm: shared_template(text) for arm, text in texts.items()}
    for arm, template in templates.items():
        if template is None:
            problems.append("template_missing %s" % arm)
    if problems:
        return problems
    if templates["naive"] != templates["axes"]:
        problems.append("template_differs")
    for field in ("## Draft", "Title:", "Structure:", "Trade-off:"):
        if field not in templates["axes"]:
            problems.append("template_field_missing %s" % field)
    if "Commitment:" in templates["axes"]:
        problems.append("template_commitment (the shared template is the naive arm's too)")
    for rule in TEMPLATE_RULES:
        if rule not in templates["axes"]:
            problems.append("template_rule_missing %r" % rule)
    if AXES_TELL in texts["axes"]:
        problems.append("axes_tell %r" % AXES_TELL)
    for sentence in AXES_PRIVACY:
        if sentence not in texts["axes"]:
            problems.append("axes_privacy_missing %r" % sentence)
    if "Give me three options for" not in texts["naive"]:
        problems.append("naive_opening_missing")
    if "Commitment:" in texts["naive"]:
        problems.append("naive_commitment")
    for placeholder in PLACEHOLDERS:
        if placeholder not in texts["axes"]:
            problems.append("axes_placeholder_missing %s" % placeholder)
    if "Commitment:" not in texts["axes"]:
        problems.append("axes_commitment_missing")
    return problems


def trial_problems(root: Path) -> List[str]:
    """One init-shaped trial file whose briefs and hashes match the brief files."""
    files = trial_files(root)
    if len(files) != 1:
        return ["trial_files %d (need exactly one)" % len(files)]
    try:
        trial = json.loads(files[0].read_text(encoding="utf-8"))
    except ValueError:
        return ["trial_unreadable %s" % files[0].name]
    if not isinstance(trial, dict) or trial.get("schema") != SCHEMA:
        return ["trial_schema %s (need %s)" % (files[0].name, SCHEMA)]
    problems = []
    briefs = {b.get("id"): b for b in trial.get("briefs", []) if isinstance(b, dict)}
    if sorted(map(str, briefs)) != sorted(BRIEFS):
        problems.append("trial_briefs %s" % ",".join(sorted(map(str, briefs))))
    for bid, medium in sorted(BRIEFS.items()):
        brief = briefs.get(bid)
        if brief is None:
            continue
        if brief.get("medium") != medium:
            problems.append("trial_medium %s %r" % (bid, brief.get("medium")))
        path = root / TRIAL_REL / "briefs" / ("%s.md" % bid)
        if not path.is_file() or sha256_file(path) != brief.get("brief_sha256"):
            problems.append("brief_changed %s" % bid)
    return problems


def commitment_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("Commitment:"))


def raw_problems(trial_dir: Path, trial: dict) -> List[str]:
    """Each recorded arm has its raw drafts; once blinded, all twelve arms are recorded."""
    problems = []
    for brief in trial.get("briefs", []):
        bid = brief.get("id")
        arms = brief.get("arms") or {}
        for arm in ARMS:
            record = arms.get(arm)
            if not isinstance(record, dict):
                if trial.get("blind"):
                    problems.append("arm_missing %s %s" % (bid, arm))
                continue
            raw = trial_dir / "raw" / str(bid) / ("%s.md" % arm)
            if not raw.is_file():
                problems.append("raw_missing %s %s" % (bid, arm))
                continue
            if sha256_file(raw) != record.get("sha256"):
                problems.append("raw_changed %s %s" % (bid, arm))
                continue
            text = raw.read_text(encoding="utf-8")
            count = len(DRAFT_RE.findall(text))
            if count != DRAFTS:
                problems.append("raw_draft_count %s %s %d" % (bid, arm, count))
            want = DRAFTS if arm == "axes" else 0
            if commitment_lines(text) != want:
                problems.append("raw_commitment %s %s %d (need %d)" % (
                    bid, arm, commitment_lines(text), want))
    return problems


def arm_label_leak(line: str, unrated: bool) -> bool:
    """An arm name where a label could sit: a heading, a rating line, beside a set
    label, in brackets, or as key.json writes it. Rating lines count only while
    unrated; after rating, the note is the rater's own text."""
    if line.startswith(tuple(f + ":" for f in FIELDS)):
        return unrated and bool(ARM_NAME_RE.search(line))
    if line.startswith("#"):
        return bool(ARM_NAME_RE.search(line))
    return bool(SET_WITH_ARM_RE.search(line) or BRACKETED_ARM_RE.search(line)
                or KEY_LABEL_RE.search(line))


def sheet_problems(trial_dir: Path, trial: dict) -> List[str]:
    """The sheet hides the arms; its rating lines stay blank until a human rates."""
    problems = []
    if not (trial_dir / "key.json").is_file():
        problems.append("key_missing")
    lines = (trial_dir / "rating-sheet.md").read_text(encoding="utf-8").splitlines()
    for heading, want in [("### Set %s" % label, len(BRIEFS)) for label in SETS] + \
            [("#### Draft %d" % n, len(BRIEFS) * len(SETS)) for n in range(1, DRAFTS + 1)]:
        if lines.count(heading) != want:
            problems.append("sheet_heading_count %r %d (need %d)" % (heading, lines.count(heading), want))
    unrated = trial.get("rated_by") is None
    for n, line in enumerate(lines, 1):
        if line.startswith("Commitment:"):
            problems.append("sheet_commitment line %d" % n)
        if line.startswith("Title:"):  # blinding drops the title; indented Title: is draft text
            problems.append("sheet_title line %d" % n)
        if arm_label_leak(line, unrated):
            problems.append("sheet_arm_name line %d" % n)
    for bid, medium in sorted(BRIEFS.items()):
        if "## Brief %s (medium: %s)" % (bid, medium) not in lines:
            problems.append("sheet_brief_missing %s" % bid)
        heading = "### Rating: %s" % bid
        if heading not in lines:
            problems.append("sheet_rating_missing %s" % bid)
            continue
        if trial.get("rated_by") is not None:
            continue
        start = lines.index(heading) + 2
        for offset, field in enumerate(FIELDS):
            line = lines[start + offset] if start + offset < len(lines) else ""
            if line.rstrip() != field + ":":
                problems.append("sheet_rating_filled %s %s" % (bid, field))
    return problems


def render_problems(trial_dir: Path, trial: dict) -> List[str]:
    """Every UI draft in both sets has a self-contained HTML page."""
    problems = []
    for brief in trial.get("briefs", []):
        if brief.get("medium") != "ui":
            continue
        for label in SETS:
            for n in range(1, DRAFTS + 1):
                name = "%s-%d" % (label, n)
                path = trial_dir / "render" / str(brief.get("id")) / ("%s.html" % name)
                if not path.is_file():
                    problems.append("render_missing %s %s" % (brief.get("id"), name))
                    continue
                text = path.read_text(encoding="utf-8")
                if "<html" not in text.lower():
                    problems.append("render_not_html %s %s" % (brief.get("id"), name))
                if EXTERNAL_ASSET_RE.search(text):
                    problems.append("render_external %s %s" % (brief.get("id"), name))
    return problems


def handoff_problems(root: Path) -> List[str]:
    """The handoff names every required item; until a report exists the spec awaits rating."""
    text = (spec_dir(root) / "rating-handoff.md").read_text(encoding="utf-8").lower()
    problems = ["handoff_missing %r" % literal for literal in HANDOFF_LITERALS
                if literal.lower() not in text]
    if not report_path(root).is_file():
        value = spec_status(root).get("matched_value")
        if value != STATUS_AWAITING:
            problems.append("status %r (need %r until trial-report.md exists)" % (
                value, STATUS_AWAITING))
    return problems


# --- live checks -------------------------------------------------------------


@pytest.mark.skipif(not (REPO_ROOT / ".writ" / "specs" / SPEC_NAME / "trial-report.md").is_file()
                    and not (REPO_ROOT / ".writ" / "specs" / "archive" / SPEC_NAME
                             / "trial-report.md").is_file(),
                    reason="trial-report.md is absent: the blind rating has not happened yet, "
                           "so there is no verdict to check (Story 6 writes the report)")
def test_repo_matches_the_committed_verdict():
    assert verdict_problems(REPO_ROOT) == []


TRIAL_DIR = REPO_ROOT / TRIAL_REL


def live_trial() -> Optional[dict]:
    files = trial_files(REPO_ROOT)
    return json.loads(files[0].read_text(encoding="utf-8")) if len(files) == 1 else None


def arms_recorded(trial: Optional[dict]) -> int:
    return sum(len(b.get("arms") or {}) for b in (trial or {}).get("briefs", []))


@pytest.mark.skipif(not (TRIAL_DIR / "briefs").is_dir(), reason="no trial briefs yet")
def test_six_briefs_are_short_and_headed():
    assert brief_problems(REPO_ROOT) == []


@pytest.mark.skipif(not (TRIAL_DIR / "prompts").is_dir(), reason="no trial prompts yet")
def test_both_prompts_share_one_output_template():
    assert prompt_problems(REPO_ROOT) == []


@pytest.mark.skipif(not trial_files(REPO_ROOT), reason="init has not written the trial file yet")
def test_trial_file_matches_the_briefs():
    assert trial_problems(REPO_ROOT) == []


@pytest.mark.skipif(arms_recorded(live_trial()) == 0, reason="no arms recorded yet")
def test_recorded_arms_have_matching_raw_drafts():
    assert raw_problems(TRIAL_DIR, live_trial()) == []


@pytest.mark.skipif(not (TRIAL_DIR / "rating-sheet.md").is_file() or live_trial() is None,
                    reason="blind has not written rating-sheet.md yet")
def test_rating_sheet_is_blind():
    assert sheet_problems(TRIAL_DIR, live_trial()) == []


@pytest.mark.skipif(not (TRIAL_DIR / "render").is_dir() or live_trial() is None,
                    reason="no UI drafts rendered yet")
def test_every_ui_draft_has_a_self_contained_render():
    assert render_problems(TRIAL_DIR, live_trial()) == []


@pytest.mark.skipif(not (spec_dir(REPO_ROOT) / "rating-handoff.md").is_file(),
                    reason="rating-handoff.md is absent: the lane has not reached the handoff")
def test_rating_handoff_names_every_required_item():
    assert handoff_problems(REPO_ROOT) == []


# --- unit tests on fake repos ------------------------------------------------


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def full_ratings() -> Dict[str, dict]:
    return {bid: {"distinct_X": 3, "distinct_Y": 1, "more_distinct": "X",
                  "render_only_enough": "yes", "note": "set X splits the data differently"}
            for bid in BRIEFS}


def make_repo(root: Path, verdict: str, status: str, reasons: Sequence[str] = (),
              skill: bool = True, rated_by: Optional[str] = "Adam",
              ratings: Optional[dict] = None) -> Path:
    """A fake repo in the state technical-spec.md → Verdict Execution names for `verdict`."""
    spec = ".writ/specs/%s" % SPEC_NAME
    write(root, spec + "/spec.md", "# Spec\n\n> **Status:** %s\n" % status)
    report = [verdict] + ["reason: %s" % r for r in reasons] + ["divergence-trial: %s" % verdict]
    write(root, spec + "/trial-report.md", "\n".join(report) + "\n")
    if skill:
        write(root, SKILL_FILE, "---\nname: design-divergence\n---\n")
        for caller in CALLERS:
            write(root, caller, "# cmd\n\n`%s` for drafts.\n" % READ_LINE)
        write(root, "README.md", "| design-divergence | skill |\n")
        write(root, ".writ/docs/config-format.md", "## Gate 0 Divergence\n")
    else:
        for caller in CALLERS:
            write(root, caller, "# cmd\n\nAsk for up to three drafts.\n")
        write(root, "README.md", "# Writ\n")
        write(root, ".writ/docs/config-format.md", "# Config\n")
    trial = {"schema": SCHEMA,
             "briefs": [{"id": bid, "medium": m, "brief_sha256": "0" * 64, "arms": {}}
                        for bid, m in sorted(BRIEFS.items())],
             "blind": None, "rated_by": rated_by,
             "ratings": full_ratings() if ratings is None else ratings}
    write(root, str(TRIAL_REL / "2026-10-26-divergence-trial.json"), json.dumps(trial))
    return root


def test_parse_report_reads_the_verdict_line_and_reason_codes():
    verdict, codes = parse_report("unverifiable\nreason: unrated\nreason: missing_arm ui-1 axes\n"
                                  "reason: unrated ui-2\ndivergence-trial: unverifiable\n")
    assert verdict == "unverifiable"
    assert codes == ["unrated", "missing_arm"]


def test_keep_passes_when_the_skill_callers_status_and_ratings_hold(tmp_path):
    make_repo(tmp_path, "keep", STATUS_KEEP)
    assert verdict_problems(tmp_path) == []


def test_keep_fails_without_the_skill_or_a_caller_read_line(tmp_path):
    make_repo(tmp_path, "keep", STATUS_KEEP)
    (tmp_path / SKILL_FILE).unlink()
    write(tmp_path, CALLERS[1], "# cmd\n")
    problems = verdict_problems(tmp_path)
    assert any("skill_missing" in p for p in problems)
    assert any("read_line_missing %s" % CALLERS[1] in p for p in problems)


def test_keep_fails_on_wrong_status(tmp_path):
    make_repo(tmp_path, "keep", "In Progress")
    assert any(p.startswith("status") for p in verdict_problems(tmp_path))


def test_keep_fails_without_a_rater(tmp_path):
    make_repo(tmp_path, "keep", STATUS_KEEP, rated_by="  ")
    assert any(p.startswith("rated_by") for p in verdict_problems(tmp_path))


def test_keep_fails_on_incomplete_ratings(tmp_path):
    ratings = full_ratings()
    del ratings["api-2"]
    ratings["ui-1"]["distinct_Y"] = 4
    ratings["ui-2"]["note"] = ""
    make_repo(tmp_path, "keep", STATUS_KEEP, ratings=ratings)
    problems = verdict_problems(tmp_path)
    assert any("api-2" in p for p in problems)
    assert any("ui-1 distinct_Y" in p for p in problems)
    assert any("ui-2 note" in p for p in problems)


def test_keep_requires_exactly_one_trial_file(tmp_path):
    make_repo(tmp_path, "keep", STATUS_KEEP)
    write(tmp_path, str(TRIAL_REL / "2026-10-27-divergence-trial.json"), "{}")
    assert any(p.startswith("trial_files 2") for p in verdict_problems(tmp_path))


def test_remove_passes_when_everything_is_gone(tmp_path):
    make_repo(tmp_path, "remove", STATUS_REMOVE, skill=False)
    assert verdict_problems(tmp_path) == []


def test_remove_fails_on_a_leftover_skill_folder(tmp_path):
    make_repo(tmp_path, "remove", STATUS_REMOVE, skill=False)
    write(tmp_path, SKILL_DIR + "/notes.txt", "x\n")
    assert any(p.startswith("skill_present") for p in verdict_problems(tmp_path))


@pytest.mark.parametrize("rel", ["commands/ship.md", "adapters/claude-code.md", "README.md",
                                 "SKILL.md", ".writ/manifest.yaml",
                                 "plugins/writ/skills/x/SKILL.md"])
def test_remove_fails_on_a_leftover_skill_mention(tmp_path, rel):
    make_repo(tmp_path, "remove", STATUS_REMOVE, skill=False)
    write(tmp_path, rel, "see design-divergence\n")
    assert "mention design-divergence %s" % rel in verdict_problems(tmp_path)


@pytest.mark.parametrize("rel", ["commands/implement-story.md", ".writ/docs/config-format.md"])
def test_remove_fails_on_a_leftover_gate_switch(tmp_path, rel):
    make_repo(tmp_path, "remove", STATUS_REMOVE, skill=False)
    write(tmp_path, rel, "- **Gate 0 Divergence:** off\n")
    assert "mention Gate 0 Divergence %s" % rel in verdict_problems(tmp_path)


def test_remove_ignores_mentions_outside_its_scope(tmp_path):
    make_repo(tmp_path, "remove", STATUS_REMOVE, skill=False)
    write(tmp_path, ".writ/specs/%s/notes.md" % SPEC_NAME, "design-divergence Gate 0 Divergence\n")
    write(tmp_path, "scripts/tests/test_x.py", "design-divergence\n")
    assert verdict_problems(tmp_path) == []


def test_remove_fails_on_wrong_status(tmp_path):
    make_repo(tmp_path, "remove", STATUS_KEEP, skill=False)
    assert any(p.startswith("status") for p in verdict_problems(tmp_path))


def test_unverifiable_passes_when_status_names_the_reason(tmp_path):
    make_repo(tmp_path, "unverifiable", "In Progress — trial unverifiable (key_changed)",
              reasons=["key_changed"], rated_by=None, ratings={})
    assert verdict_problems(tmp_path) == []


def test_unverifiable_fails_when_status_omits_the_reason(tmp_path):
    make_repo(tmp_path, "unverifiable", STATUS_AWAITING, reasons=["key_changed"])
    assert any(p.startswith("status_reason") for p in verdict_problems(tmp_path))


def test_unverifiable_fails_when_the_report_names_no_reason(tmp_path):
    make_repo(tmp_path, "unverifiable", "In Progress — unrated")
    assert "report_reason_missing" in verdict_problems(tmp_path)


def test_unverifiable_fails_when_the_status_reads_as_acted_on(tmp_path):
    make_repo(tmp_path, "unverifiable", STATUS_REMOVE, reasons=["unrated"])
    assert any(p.startswith("status") for p in verdict_problems(tmp_path))


def test_unverifiable_fails_when_something_was_removed(tmp_path):
    make_repo(tmp_path, "unverifiable", "In Progress — unrated", reasons=["unrated"])
    (tmp_path / SKILL_FILE).unlink()
    write(tmp_path, CALLERS[0], "# cmd\n")
    problems = verdict_problems(tmp_path)
    assert any("skill_missing" in p for p in problems)
    assert any("read_line_missing %s" % CALLERS[0] in p for p in problems)


def test_unknown_verdict_line_is_a_problem(tmp_path):
    make_repo(tmp_path, "maybe", STATUS_KEEP)
    assert verdict_problems(tmp_path) == ["verdict_unknown 'maybe'"]


def test_archived_spec_is_followed(tmp_path):
    make_repo(tmp_path, "keep", STATUS_KEEP)
    specs = tmp_path / ".writ" / "specs"
    (specs / "archive").mkdir()
    (specs / SPEC_NAME).rename(specs / "archive" / SPEC_NAME)
    assert verdict_problems(tmp_path) == []


# --- unit tests: structural checks --------------------------------------------

TEMPLATE = ("```text\n## Draft <n>\nTitle: <name>\nStructure:\n"
            "<15 to 25 lines. The draft stands alone: define every part; refer to no other draft>\n"
            "Trade-off: <one line>\n```\n")


def make_inputs(root: Path) -> Path:
    """Six briefs, both prompts, and an init-shaped trial file with no arms."""
    trial_dir = root / TRIAL_REL
    briefs = []
    for bid, medium in sorted(BRIEFS.items()):
        path = write(trial_dir, "briefs/%s.md" % bid, "id: %s\nmedium: %s\n\nA page.\n" % (bid, medium))
        briefs.append({"id": bid, "medium": medium, "brief_sha256": sha256_file(path), "arms": {}})
    write(trial_dir, "prompts/naive.md", "Give me three options for {brief}\n\n" + TEMPLATE)
    write(trial_dir, "prompts/axes.md", " ".join(PLACEHOLDERS) + "\n\n" + "\n".join(AXES_PRIVACY) + "\n\n"
          + TEMPLATE + "\nCommitment: {axis_combination} — <trade-off>\n")
    trial = {"schema": SCHEMA, "briefs": briefs, "blind": None, "rated_by": None, "ratings": None}
    write(trial_dir, "2026-10-26-divergence-trial.json", json.dumps(trial))
    return trial_dir


def drafts_text(arm: str) -> str:
    blocks = []
    for n in range(1, DRAFTS + 1):
        commitment = "Commitment: one call — slower\n" if arm == "axes" else ""
        blocks.append("## Draft %d\nTitle: T%d\n%sStructure:\n  a\nTrade-off: t\n" % (n, n, commitment))
    return "\n".join(blocks)


def record_all(trial_dir: Path) -> dict:
    path = next(trial_dir.glob(TRIAL_GLOB))
    trial = json.loads(path.read_text(encoding="utf-8"))
    for brief in trial["briefs"]:
        for arm in ARMS:
            raw = write(trial_dir, "raw/%s/%s.md" % (brief["id"], arm), drafts_text(arm))
            brief["arms"][arm] = {"sha256": sha256_file(raw), "drafts": DRAFTS}
    path.write_text(json.dumps(trial), encoding="utf-8")
    return trial


def sheet_text(rated: bool = False) -> str:
    out = ["# Divergence trial rating sheet", "", "Rate from this file alone."]
    for bid, medium in sorted(BRIEFS.items()):
        out += ["", "## Brief %s (medium: %s)" % (bid, medium)]
        for label in SETS:
            out += ["", "### Set %s" % label]
            for n in range(1, DRAFTS + 1):
                out += ["", "#### Draft %d" % n, "", "Structure:", "  a", "Trade-off: t"]
        out += ["", "### Rating: %s" % bid, ""]
        out += [f + (": 2" if rated else ":") for f in FIELDS]
    return "\n".join(out) + "\n"


def test_inputs_pass_when_well_formed(tmp_path):
    make_inputs(tmp_path)
    assert brief_problems(tmp_path) == []
    assert prompt_problems(tmp_path) == []
    assert trial_problems(tmp_path) == []


def test_brief_problems_catch_length_header_and_count(tmp_path):
    trial_dir = make_inputs(tmp_path)
    write(trial_dir, "briefs/ui-1.md", "id: ui-1\nmedium: ui\n" + "x\n" * 9)
    write(trial_dir, "briefs/api-2.md", "id: api-9\nmedium: api\n")
    write(trial_dir, "briefs/extra.md", "id: extra\nmedium: ui\n")
    problems = brief_problems(tmp_path)
    assert any(p.startswith("brief_too_long ui-1") for p in problems)
    assert any(p.startswith("brief_header api-2") for p in problems)
    assert any(p.startswith("brief_unexpected extra.md") for p in problems)


def test_shared_template_reads_the_first_text_fence():
    assert shared_template("x\n```text\nA\nB\n```\n```text\nC\n```\n") == "A\nB\n"
    assert shared_template("no fence\n") is None


def test_prompt_problems_catch_a_drifted_template_and_a_naive_commitment(tmp_path):
    trial_dir = make_inputs(tmp_path)
    write(trial_dir, "prompts/naive.md", "Give me three options for {brief}\n\n"
          + TEMPLATE.replace("Trade-off", "Tradeoff") + "Commitment: x\n")
    problems = prompt_problems(tmp_path)
    assert "template_differs" in problems
    assert "naive_commitment" in problems


def test_prompt_problems_catch_a_missing_placeholder(tmp_path):
    trial_dir = make_inputs(tmp_path)
    text = (trial_dir / "prompts/axes.md").read_text(encoding="utf-8")
    write(trial_dir, "prompts/axes.md", text.replace("{persona}", "a user"))
    assert "axes_placeholder_missing {persona}" in prompt_problems(tmp_path)


def test_trial_problems_catch_a_changed_brief(tmp_path):
    trial_dir = make_inputs(tmp_path)
    write(trial_dir, "briefs/ui-2.md", "id: ui-2\nmedium: ui\n\nEdited.\n")
    assert "brief_changed ui-2" in trial_problems(tmp_path)


def test_raw_problems_pass_for_twelve_recorded_arms(tmp_path):
    trial = record_all(make_inputs(tmp_path))
    trial["blind"] = {"sheet": "rating-sheet.md"}
    assert raw_problems(tmp_path / TRIAL_REL, trial) == []


def test_raw_problems_catch_missing_changed_and_wrong_commitments(tmp_path):
    trial_dir = make_inputs(tmp_path)
    trial = record_all(trial_dir)
    (trial_dir / "raw/ui-1/axes.md").unlink()
    write(trial_dir, "raw/api-1/naive.md", drafts_text("axes"))
    del trial["briefs"][-1]["arms"]["naive"]
    trial["blind"] = {"sheet": "rating-sheet.md"}
    problems = raw_problems(trial_dir, trial)
    assert "raw_missing ui-1 axes" in problems
    assert "raw_changed api-1 naive" in problems
    assert "arm_missing %s naive" % trial["briefs"][-1]["id"] in problems


def test_raw_problems_allow_a_partial_run_before_blind(tmp_path):
    trial_dir = make_inputs(tmp_path)
    trial = record_all(trial_dir)
    del trial["briefs"][0]["arms"]["naive"]
    assert raw_problems(trial_dir, trial) == []


def test_sheet_passes_when_blind_and_blank(tmp_path):
    trial_dir = make_inputs(tmp_path)
    write(trial_dir, "rating-sheet.md", sheet_text())
    write(trial_dir, "key.json", "{}")
    trial = json.loads(next(trial_dir.glob(TRIAL_GLOB)).read_text(encoding="utf-8"))
    assert sheet_problems(trial_dir, trial) == []


def test_sheet_problems_catch_leaks_and_filled_fields_before_rating(tmp_path):
    trial_dir = make_inputs(tmp_path)
    text = sheet_text(rated=True).replace("  a\n", "Commitment: x\nSet X is the naive set\n", 1)
    write(trial_dir, "rating-sheet.md", text)
    trial = json.loads(next(trial_dir.glob(TRIAL_GLOB)).read_text(encoding="utf-8"))
    problems = sheet_problems(trial_dir, trial)
    assert "key_missing" in problems
    assert any(p.startswith("sheet_commitment") for p in problems)
    assert any(p.startswith("sheet_arm_name") for p in problems)
    assert any(p.startswith("sheet_rating_filled") for p in problems)


def test_sheet_may_be_filled_once_rated(tmp_path):
    trial_dir = make_inputs(tmp_path)
    write(trial_dir, "rating-sheet.md", sheet_text(rated=True))
    write(trial_dir, "key.json", "{}")
    trial = json.loads(next(trial_dir.glob(TRIAL_GLOB)).read_text(encoding="utf-8"))
    trial["rated_by"] = "Adam"
    assert sheet_problems(trial_dir, trial) == []


def test_render_problems(tmp_path):
    trial_dir = make_inputs(tmp_path)
    trial = json.loads(next(trial_dir.glob(TRIAL_GLOB)).read_text(encoding="utf-8"))
    for bid in ("ui-1", "ui-2"):
        for label in SETS:
            for n in range(1, DRAFTS + 1):
                write(trial_dir, "render/%s/%s-%d.html" % (bid, label, n),
                      "<!doctype html><html><body>x</body></html>\n")
    assert render_problems(trial_dir, trial) == []
    (trial_dir / "render/ui-2/Y-3.html").unlink()
    write(trial_dir, "render/ui-1/X-1.html",
          '<html><script src="https://cdn.example/x.js"></script></html>')
    problems = render_problems(trial_dir, trial)
    assert "render_missing ui-2 Y-3" in problems
    assert "render_external ui-1 X-1" in problems


def handoff_text() -> str:
    return " ".join(HANDOFF_LITERALS) + "\n"


def test_handoff_passes_and_requires_the_awaiting_status_before_a_report(tmp_path):
    write(tmp_path, ".writ/specs/%s/spec.md" % SPEC_NAME, "> **Status:** %s\n" % STATUS_AWAITING)
    write(tmp_path, ".writ/specs/%s/rating-handoff.md" % SPEC_NAME, handoff_text())
    assert handoff_problems(tmp_path) == []
    write(tmp_path, ".writ/specs/%s/spec.md" % SPEC_NAME, "> **Status:** In Progress\n")
    assert any(p.startswith("status") for p in handoff_problems(tmp_path))
    write(tmp_path, ".writ/specs/%s/trial-report.md" % SPEC_NAME, "keep\n")
    assert handoff_problems(tmp_path) == []


def test_handoff_problems_name_each_missing_item(tmp_path):
    write(tmp_path, ".writ/specs/%s/spec.md" % SPEC_NAME, "> **Status:** %s\n" % STATUS_AWAITING)
    write(tmp_path, ".writ/specs/%s/rating-handoff.md" % SPEC_NAME,
          handoff_text().replace("did not rate", "").replace("key.json", ""))
    problems = handoff_problems(tmp_path)
    assert "handoff_missing 'did not rate'" in problems
    assert "handoff_missing 'key.json'" in problems


def blinded_sheet(trial_dir: Path, body: str = "  a", rated: bool = False) -> dict:
    """A sheet whose first draft body is `body`; returns the trial it belongs to."""
    write(trial_dir, "rating-sheet.md", sheet_text(rated).replace("  a\n", body + "\n", 1))
    write(trial_dir, "key.json", "{}")
    return json.loads(next(trial_dir.glob(TRIAL_GLOB)).read_text(encoding="utf-8"))


@pytest.mark.parametrize("body", ["  axes: Axis[]  // shared axes", "  naive diff of drafts",
                                  "  CommitmentList(chosen)", "  Commitment: indented draft text",
                                  "Uses the naive and the axes views"])
def test_sheet_allows_arm_words_inside_draft_text(tmp_path, body):
    trial_dir = make_inputs(tmp_path)
    assert sheet_problems(trial_dir, blinded_sheet(trial_dir, body)) == []


@pytest.mark.parametrize("old,new", [("### Set X", "### Set X (axes)"),
                                     ("#### Draft 1", "#### Draft 1 naive"),
                                     ("\n\n### Rating: api-1", "\n\nSet Y: naive\n\n### Rating: api-1"),
                                     ("\n\n### Rating: api-1", '\n\n"arm": "axes"\n\n### Rating: api-1'),
                                     ("distinct_X:", "distinct_X: (axes)")])
def test_sheet_flags_an_arm_word_in_a_label_position(tmp_path, old, new):
    trial_dir = make_inputs(tmp_path)
    trial = blinded_sheet(trial_dir)
    path = trial_dir / "rating-sheet.md"
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    assert any(p.startswith("sheet_arm_name") for p in sheet_problems(trial_dir, trial))


def test_sheet_flags_a_commitment_line_at_column_zero(tmp_path):
    trial_dir = make_inputs(tmp_path)
    trial = blinded_sheet(trial_dir, "Commitment: one call — slower")
    assert any(p.startswith("sheet_commitment") for p in sheet_problems(trial_dir, trial))


def test_prompt_problems_require_the_shared_length_and_standalone_rules(tmp_path):
    trial_dir = make_inputs(tmp_path)
    for arm in ("naive", "axes"):
        path = trial_dir / "prompts" / ("%s.md" % arm)
        path.write_text(path.read_text(encoding="utf-8").replace("15 to 25 lines", "some lines")
                        .replace("stands alone", "is a draft"), encoding="utf-8")
    problems = prompt_problems(tmp_path)
    assert "template_rule_missing '15 to 25 lines'" in problems
    assert "template_rule_missing 'stands alone'" in problems


def test_prompt_problems_keep_caller_usage_private_in_the_axes_prompt(tmp_path):
    trial_dir = make_inputs(tmp_path)
    path = trial_dir / "prompts/axes.md"
    path.write_text(path.read_text(encoding="utf-8").replace("\n".join(AXES_PRIVACY), AXES_TELL), encoding="utf-8")
    problems = prompt_problems(tmp_path)
    assert "axes_tell %r" % AXES_TELL in problems
    assert any(p.startswith("axes_privacy_missing") for p in problems)


def test_sheet_skips_arm_checks_on_rating_lines_once_rated(tmp_path):
    trial_dir = make_inputs(tmp_path)
    trial = blinded_sheet(trial_dir, rated=True)
    path = trial_dir / "rating-sheet.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("note: 2", "note: Set X looked naive", 1), encoding="utf-8")
    trial["rated_by"] = "Adam"
    assert sheet_problems(trial_dir, trial) == []


def test_sheet_flags_a_title_line_at_column_zero(tmp_path):
    trial_dir = make_inputs(tmp_path)
    trial = blinded_sheet(trial_dir, "Title: Ledger by patch-id")
    assert any(p.startswith("sheet_title line") for p in sheet_problems(trial_dir, trial))


def test_sheet_allows_an_indented_title_line(tmp_path):
    trial_dir = make_inputs(tmp_path)
    assert sheet_problems(trial_dir, blinded_sheet(trial_dir, "  Title: page header text")) == []


def test_read_status_returns_the_detector_fields(tmp_path):
    spec = write(tmp_path, "spec.md", "# Spec\n\n> **Status:** In Progress — trial unverifiable (unrated)\n")
    status = read_status(spec)
    assert status["complete"] is False
    assert status["canonical_head"] == "In Progress"
    assert status["matched_value"] == "In Progress — trial unverifiable (unrated)"


def test_read_status_of_a_missing_spec_is_empty(tmp_path):
    assert read_status(tmp_path / "absent.md") == {}


def test_keep_accepts_the_unbold_status_form_the_detector_reads(tmp_path):
    make_repo(tmp_path, "keep", STATUS_KEEP)
    write(tmp_path, ".writ/specs/%s/spec.md" % SPEC_NAME, "# Spec\n\n> Status: Complete\n")
    assert verdict_problems(tmp_path) == []


def test_remove_accepts_the_unbold_status_form_the_detector_reads(tmp_path):
    make_repo(tmp_path, "remove", STATUS_REMOVE, skill=False)
    write(tmp_path, ".writ/specs/%s/spec.md" % SPEC_NAME, "# Spec\n\n> Status: %s\n" % STATUS_REMOVE)
    assert verdict_problems(tmp_path) == []
