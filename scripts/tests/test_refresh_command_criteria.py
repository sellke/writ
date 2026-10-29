#!/usr/bin/env python3
"""Static checks for spec `2026-10-25-retro-fix-ladder`, Story 4.

`commands/refresh-command.md` is read as text. These tests pin the two
criteria the story adds and the four rejection reason tokens:

- § Phase 3 carries `**Covered already?**` before the five required fields
  and `**Skill targets**`; a covered signal is logged as `execution failure`
  with the covering section, and an unused skill target is rejected with
  `skill not used`. The Evidence block's affected section may name a skill
  section (AC-4.1).
- § Step 4.1a runs `bash scripts/lint-skill.sh skills/<name>/SKILL.md` on a
  skill amendment, and line 1 `fail` rejects with `eval failed`. § Step 4.2's
  rejected examples carry all four tokens, and its Target file line names
  the command and any skill (AC-4.2).
- The frontmatter `exit_criteria` names all four tokens and covers skill
  amendments, `description` is unchanged, and `## Completion` carries the
  sentence the spec gives (AC-4.3).
- `scripts/eval-refresh-evidence.py` prints `PASS` for the three new
  scenarios, accepts exactly the four tokens, and its missing-token message
  lists them (AC-4.4).
- The file stays under the 24,960-byte command budget, and every literal
  `check_refresh_evidence` in `scripts/eval.sh` pins is still present
  (AC-4.5).

Run: uv run --python 3.9 pytest scripts/tests/test_refresh_command_criteria.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND = REPO_ROOT / "commands" / "refresh-command.md"
LOG_FORMAT = REPO_ROOT / ".writ" / "docs" / "refresh-log-format.md"
EVAL_SCRIPT = REPO_ROOT / "scripts" / "eval-refresh-evidence.py"

BYTE_CEILING = 24960  # COMMAND_BYTE_BUDGET in scripts/eval-leanness.py

TOKENS = ("no evidence", "eval failed", "execution failure", "skill not used")

DESCRIPTION_LINE = (
    'description: "Turn your experience running a Writ command into concrete '
    'improvements to that command file."'
)

COMPLETION_SENTENCE = "improves one command file, and the skills that run read, from evidence."

SKILL_LINT = "bash scripts/lint-skill.sh skills/<name>/SKILL.md"

NEW_SCENARIOS = (
    "rejected-execution-failure-is-valid-record",
    "rejected-skill-not-used-is-valid-record",
    "rejected-unknown-token-fails",
)

# Literals scripts/eval.sh check_refresh_evidence pins with require_literal.
COMMAND_PINS = (
    "**Evidence:**",
    "**Rejected:**",
    "no evidence",
    "eval failed",
    "verbatim private transcript bodies",
    "high-traffic allowlist — `create-spec`, `implement-story`, `ship`, `refactor`",
    "structural only — not an LLM-as-judge",
)
LOG_FORMAT_PINS = ("**Evidence:**", "LEARNING_CONTRACT_SINCE", "no evidence", "eval failed")


def command_text() -> str:
    return COMMAND.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """Return `heading` and its body up to the next heading of the same or a
    higher level. Lines inside code fences are never headings: Step 4.2's
    example log carries `## [DATE] ...` inside a fence."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    out = []  # type: List[str]
    in_fence = False
    capturing = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence and not line.startswith("```") and line.startswith("#"):
            hashes = len(line) - len(line.lstrip("#"))
            if capturing and hashes <= level:
                break
            if line.strip() == heading:
                capturing = True
        if capturing:
            out.append(line)
    assert out, "heading %r not found in %s" % (heading, COMMAND.name)
    return "\n".join(out)


def frontmatter_lines(text: str) -> List[str]:
    lines = text.splitlines()
    assert lines[0] == "---", "no frontmatter"
    end = lines.index("---", 1)
    return lines[1:end]


def exit_criteria(text: str) -> List[str]:
    lines = frontmatter_lines(text)
    start = lines.index("exit_criteria:")
    items = []  # type: List[str]
    for line in lines[start + 1:]:
        if not line.startswith("  - "):
            break
        items.append(line[4:])
    return items


def load_eval_module():
    spec = importlib.util.spec_from_file_location("eval_refresh_evidence", str(EVAL_SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejected_entry(bullet: str) -> str:
    return (
        "## 2026-10-25 — /create-spec refreshed\n\n"
        "**Signals found:** 2 total, 1 actionable\n"
        "**Amendments applied:** 0 of 1 proposed\n\n"
        "**Rejected:**\n"
        "- %s\n\n"
        "**Scope:** Local only\n"
        "**Target file:** commands/create-spec.md\n" % bullet
    )


# -- AC-4.1: Phase 3 criteria ----------------------------------------------


def test_phase3_has_both_labels():
    """AC-4.1 — § Phase 3 carries `**Covered already?**` and `**Skill targets**`."""
    phase3 = section(command_text(), "## Phase 3: Propose Amendments")
    assert "**Covered already?**" in phase3
    assert "**Skill targets**" in phase3


def test_covered_check_comes_before_the_five_fields():
    """AC-4.1 — the covered check runs before the five required fields are written."""
    phase3 = section(command_text(), "## Phase 3: Propose Amendments")
    assert "**Covered already?**" in phase3
    fields = phase3.index("five required fields")
    assert phase3.index("**Covered already?**") < fields


def test_covered_signal_is_logged_as_execution_failure():
    """AC-4.1 — a covered signal is logged under `execution failure` with the covering section."""
    phase3 = section(command_text(), "## Phase 3: Propose Amendments")
    assert "**Covered already?**" in phase3 and "**Skill targets**" in phase3
    covered = phase3[phase3.index("**Covered already?**"):phase3.index("**Skill targets**")]
    assert "`execution failure`" in covered
    assert "covering section" in covered
    assert "skills/<name>/SKILL.md" in covered


def test_unused_skill_target_is_rejected():
    """AC-4.1 — a skill target the transcript does not show in use is rejected with `skill not used`."""
    phase3 = section(command_text(), "## Phase 3: Propose Amendments")
    assert "**Skill targets**" in phase3
    rule = phase3[phase3.index("**Skill targets**"):]
    assert "`skill not used`" in rule
    assert "transcript" in rule


def test_evidence_block_may_name_a_skill_section():
    """AC-4.1 — the Evidence block's affected section may name a skill section."""
    phase3 = section(command_text(), "## Phase 3: Propose Amendments")
    assert 'skills/<name>/SKILL.md → "' in phase3


# -- AC-4.2: Step 4.1a lint and Step 4.2 log -------------------------------


def test_step_41a_lints_skill_amendments():
    """AC-4.2 — Step 4.1a runs lint-skill.sh on a skill amendment; line 1 `fail` → `eval failed`."""
    step = section(command_text(), "### Step 4.1a: Pre-Merge Eval Gate")
    assert SKILL_LINT in step
    tail = step[step.index(SKILL_LINT):]
    assert "line 1 `fail`" in tail
    assert "`eval failed`" in tail


@pytest.mark.parametrize("token", TOKENS)
def test_step_42_rejected_examples_carry_each_token(token):
    """AC-4.2 — Step 4.2's rejected examples show all four reason tokens."""
    step = section(command_text(), "### Step 4.2: Write Refresh Log")
    rejected = step[step.index("**Rejected:**"):step.index("**Scope:**")]
    assert "— reason: %s" % token in rejected


def test_step_42_target_file_names_skills():
    """AC-4.2 — Step 4.2's Target file line lists the command and any skill edited."""
    step = section(command_text(), "### Step 4.2: Write Refresh Log")
    target = [ln for ln in step.splitlines() if ln.startswith("**Target file:**")]
    assert len(target) == 1, target
    assert "commands/[command].md" in target[0]
    assert "skills/<name>/SKILL.md" in target[0]


# -- AC-4.3: frontmatter and Completion ------------------------------------


def test_description_unchanged():
    """AC-4.3 — `description` equals its value before the edit."""
    assert DESCRIPTION_LINE in frontmatter_lines(command_text())


@pytest.mark.parametrize("token", TOKENS)
def test_exit_criteria_name_each_token(token):
    """AC-4.3 — `exit_criteria` names all four reason tokens."""
    assert token in " ".join(exit_criteria(command_text()))


def test_exit_criteria_cover_skill_amendments():
    """AC-4.3 — the first exit criterion covers amendments written to a skill the run read."""
    first = exit_criteria(command_text())[0]
    assert "every amendment written to commands/<name>.md or to a skill it read" in first


def test_completion_sentence():
    """AC-4.3 — `## Completion` carries the terminal sentence."""
    completion = section(command_text(), "## Completion")
    assert COMPLETION_SENTENCE in completion
    assert "improves one command file from evidence." not in completion


@pytest.mark.parametrize("token", TOKENS)
def test_completion_names_each_token(token):
    """AC-4.3 — `## Completion` lists the four reasons a candidate can be rejected for."""
    assert token in section(command_text(), "## Completion")


# -- AC-4.4: eval-refresh-evidence.py --------------------------------------


def test_eval_script_prints_pass_for_new_scenarios():
    """AC-4.4 — the script prints PASS for the three new scenarios and no FAIL row."""
    proc = subprocess.run([sys.executable, str(EVAL_SCRIPT)], cwd=str(REPO_ROOT),
                          capture_output=True, text=True, timeout=60)
    rows = [ln.split("\t") for ln in proc.stdout.splitlines() if ln]
    status = {row[1]: row[0] for row in rows if len(row) >= 2}
    for name in NEW_SCENARIOS:
        assert status.get(name) == "PASS", "%s: %r" % (name, status.get(name))
    failing = [row for row in rows if row[0] == "FAIL"]
    assert failing == [], failing
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("token", TOKENS)
def test_validator_accepts_each_token(token):
    """AC-4.4 — a rejected record with any of the four tokens is valid."""
    module = load_eval_module()
    ok, reason = module.validate_entry(rejected_entry("Some change — reason: %s" % token))
    assert ok, reason


def test_validator_rejects_unknown_token():
    """AC-4.4 — a rejected record with any other token fails."""
    module = load_eval_module()
    ok, reason = module.validate_entry(rejected_entry("Some change — reason: not convinced"))
    assert not ok
    assert reason.startswith("rejected:")


def test_missing_token_message_lists_all_four():
    """AC-4.4 — the missing-token message names all four tokens."""
    module = load_eval_module()
    ok, reason = module.validate_entry(rejected_entry("Some change, no reason given"))
    assert not ok
    for token in TOKENS:
        assert token in reason, reason


# -- AC-4.5: budget and pinned literals ------------------------------------


def test_command_under_byte_ceiling():
    """AC-4.5 — commands/refresh-command.md stays under the 24,960-byte command budget."""
    size = len(COMMAND.read_bytes())
    assert size < BYTE_CEILING, "%d bytes" % size


@pytest.mark.parametrize("literal", COMMAND_PINS)
def test_check_refresh_evidence_command_pins(literal):
    """AC-4.5 — every literal check_refresh_evidence pins in the command is present."""
    assert literal in command_text()


@pytest.mark.parametrize("literal", LOG_FORMAT_PINS + TOKENS)
def test_log_format_pins_and_tokens(literal):
    """AC-4.5 — the log-format doc keeps its pinned literals and documents all four tokens."""
    assert literal in LOG_FORMAT.read_text(encoding="utf-8")
