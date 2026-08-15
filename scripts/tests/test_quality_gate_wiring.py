#!/usr/bin/env python3
"""Wiring assertions for Stories 5 and 6 of
`2026-08-14-script-backed-quality-gates`.

Stories 5 and 6 change command and agent prose rather than code, so their
executable protection lives in `scripts/eval.sh`'s `require_literal` /
`forbid_literal` bindings. This file asserts the same properties from the unit
suite, for two reasons.

First, CI runs `scripts/eval.sh` and never `scripts/tests/` — but the reverse
gap also exists, and it bit this very spec: the per-command byte ratchet in
`test_governor_enforcement.py` is *not* wired into `eval.sh`, and caught a real
regression only because the full unit suite was run by hand. Properties worth
gating are worth gating from both directions.

Second, these are the citations that make Stories 5 and 6's acceptance criteria
traceable. `scripts/ac-trace.py` counts a bare `AC-<story>.<n>` token in a
test-shaped path as a test citation; a criterion whose only evidence is prose in
a command file has none, and reads as `untested_criterion` once its story
completes.

Run: python3 scripts/tests/test_quality_gate_wiring.py
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"
TESTING_AGENT = REPO_ROOT / "agents" / "testing-agent.md"
CODING_AGENT = REPO_ROOT / "agents" / "coding-agent.md"
WRIT_CODER = REPO_ROOT / "claude-code" / "agents" / "writ-coder.md"
TDD_SKILL = REPO_ROOT / "skills" / "tdd-cycle" / "SKILL.md"
INITIALIZE = REPO_ROOT / "commands" / "initialize.md"
STATUS = REPO_ROOT / "commands" / "status.md"
VISUAL_QA = REPO_ROOT / "agents" / "visual-qa-agent.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Gate4OverrideTests(unittest.TestCase):
    """AC-5.1 — the checker's verdict is authoritative over the agent's
    self-reported `Coverage threshold met` field."""

    def test_gate_4_runs_the_coverage_re_derivation(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertIn("scripts/test-integrity.py coverage", text)
        self.assertIn("scripts/test-integrity.py authenticity", text)

    def test_gate_4_states_the_checker_wins(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertIn("where they disagree the checker wins", text)

    def test_gate_4_shows_both_the_claim_and_the_measurement(self) -> None:
        self.assertIn(
            "Show both the claim and the measurement", read(IMPLEMENT_STORY)
        )

    def test_blocking_coverage_findings_stop_the_story_closing(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertIn("The story does not reach `Completed ✅`", text)

    def test_testing_agent_records_that_its_field_is_verified(self) -> None:
        text = read(TESTING_AGENT)
        self.assertIn("verified, not trusted", text)
        # The field itself must survive: Gate 4's BLOCKED handling and
        # subagent-result-completeness both key off the existing shape.
        self.assertIn("- **Coverage threshold met:** [YES/NO]", text)


class Gate2SmokeTests(unittest.TestCase):
    """AC-5.2 — Gate 2 boots the framework, routing a blocking finding through
    the existing shared BLOCKED escalation rather than new control flow."""

    def test_gate_2_runs_the_build_smoke_check(self) -> None:
        self.assertIn(
            "scripts/build-smoke.py check --project .", read(IMPLEMENT_STORY)
        )

    def test_source_failure_uses_the_existing_blocked_escalation(self) -> None:
        text = read(IMPLEMENT_STORY)
        smoke = text.split("**Build smoke.**", 1)[1].split("---", 1)[0]
        self.assertIn("build_failed_source", smoke)
        self.assertIn("#blocked-agent-escalation", smoke)

    def test_no_iteration_cap_was_added_to_gate_2(self) -> None:
        """eval-loop-bounds.py cross-reads `loop.nested` against prose like
        '2 fix iterations max'; a cap in one place and not the other drifts."""
        text = read(IMPLEMENT_STORY)
        smoke = text.split("**Build smoke.**", 1)[1].split("---", 1)[0]
        self.assertNotRegex(smoke, r"\d+\s+(fix\s+)?iterations?\s+max")
        self.assertIn("no iteration cap", smoke.lower())

    def test_coding_agents_describe_gate_2s_new_remit(self) -> None:
        for path in (CODING_AGENT, WRIT_CODER):
            self.assertIn("build smoke", read(path).lower(), path.name)


class UnverifiableIsNotDegradedTests(unittest.TestCase):
    """AC-5.3 — an unverifiable check is not a failed gate. DEGRADED means a
    gate could not be cleared; unverifiable means a check could not be run."""

    def test_both_gates_state_the_distinction(self) -> None:
        text = read(IMPLEMENT_STORY)
        smoke = text.split("**Build smoke.**", 1)[1].split("---", 1)[0]
        gate4 = text.split("**Verify the claim, don't trust it.**", 1)[1]

        for block, name in ((smoke, "Gate 2"), (gate4, "Gate 4")):
            self.assertIn("unverifiable", block, name)
            self.assertIn("DEGRADED", block, name)
            self.assertIn("not", block, name)

    def test_gate_2_names_the_distinction_explicitly(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertIn(
            "DEGRADED means a gate could not be cleared, `unverifiable` means a "
            "check could not be run here",
            text,
        )


class NoNewGateNumberTests(unittest.TestCase):
    """AC-5.4 and AC-5.5 — the gate set is unchanged from Gate 0 to Gate 5, and
    the five literal-pinned routing rows still exist."""

    EXPECTED_GATES = {
        "Gate 0", "Gate 0.5", "Gate 1", "Gate 2", "Gate 2.5",
        "Gate 3", "Gate 3.5", "Gate 4", "Gate 4.5", "Gate 5",
    }

    def test_pipeline_table_gate_set_is_unchanged(self) -> None:
        found = set(re.findall(r"^\| (Gate [0-9.]+)", read(IMPLEMENT_STORY), re.M))
        self.assertEqual(found, self.EXPECTED_GATES)

    def test_no_gate_2_6_or_4_6_was_introduced(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertNotIn("Gate 2.6", text)
        self.assertNotIn("Gate 4.6", text)

    def test_the_five_routing_rows_survive(self) -> None:
        text = read(IMPLEMENT_STORY)
        for row in (
            "| Architecture Check (Gate 0) |",
            "| Coding Agent (Gate 1) |",
            "| Review Agent (Gate 3) |",
            "| Testing Agent (Gate 4) |",
            "| Documentation Agent (Gate 5) |",
        ):
            self.assertIn(row, text, row)

    def test_visual_qa_diagram_needed_no_edit(self) -> None:
        self.assertIn("**Gate 4.5**", read(VISUAL_QA))

    def test_pipeline_table_and_quick_mode_agree_on_gate_2(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertIn("| Gate 2 | Lint, Typecheck, Format & Build Smoke |", text)
        self.assertIn("Gate 2 (lint + build smoke)", text)

    def test_tdd_skill_names_the_gate_that_actually_spawns_the_agent(self) -> None:
        text = read(TDD_SKILL)
        self.assertIn("Gate 1 spawns the coding agent", text)
        self.assertNotIn("Gate 2 spawns the coding agent", text)


class InitializeBaselineTests(unittest.TestCase):
    """AC-6.1, AC-6.2 and AC-6.3 — record existing debt, write the coverage
    floor at the measured value, and never re-baseline automatically."""

    def test_initialize_runs_the_audit_and_writes_the_baseline(self) -> None:
        text = read(INITIALIZE)
        self.assertIn("scripts/quality-config-audit.py check --project .", text)
        self.assertIn(".writ/quality-baseline.md", text)

    def test_baseline_entries_carry_a_date_and_a_rationale(self) -> None:
        text = read(INITIALIZE)
        self.assertIn("YYYY-MM-DD", text)
        self.assertIn("rationale", text)

    def test_re_baselining_is_prohibited(self) -> None:
        self.assertIn("Never re-baseline automatically", read(INITIALIZE))

    def test_coverage_floor_is_written_at_the_measured_value(self) -> None:
        text = read(INITIALIZE)
        self.assertIn("floor(measured)", text)
        self.assertIn("never 80%", text)

    def test_the_coverage_write_carries_a_confirmation(self) -> None:
        """Brownfield /initialize is otherwise read-only with respect to
        target-project config."""
        self.assertIn("same explicit confirmation", read(INITIALIZE))


class StatusSurfaceTests(unittest.TestCase):
    """AC-6.4 and AC-6.5 — pure file reads only, the existing health
    vocabulary, and omit-if-empty."""

    def test_status_surfaces_only_the_pure_file_read_checker(self) -> None:
        self.assertIn("scripts/quality-config-audit.py check --project .", read(STATUS))

    def test_status_never_invokes_the_tooling_executing_checkers(self) -> None:
        """/status's third exit criterion promises no build, test, or
        git-mutating command ran."""
        text = read(STATUS)
        self.assertNotIn("test-integrity.py coverage --project", text)
        self.assertNotIn("build-smoke.py check --project", text)

    def test_the_config_audit_cannot_run_a_subprocess_at_all(self) -> None:
        """The strongest form of the same guarantee: the checker /status calls
        has no subprocess capability, so the criterion cannot be breached by
        the call itself."""
        checker = read(REPO_ROOT / "scripts" / "quality-config-audit.py")
        self.assertNotIn("import subprocess", checker)

    def test_status_reuses_the_existing_health_vocabulary(self) -> None:
        text = read(STATUS)
        block = text.split("**Quality configuration:**", 1)[1].split("### Step 8", 1)[0]
        for word in ("Healthy", "Warning", "Attention"):
            self.assertIn(word, block, word)

    def test_status_omits_the_line_when_there_is_nothing_to_say(self) -> None:
        self.assertIn("Omit the line entirely", read(STATUS))

    def test_suggested_actions_use_only_allowlisted_commands(self) -> None:
        text = read(STATUS)
        allowlist_block = text.split("**Command allowlist", 1)[1].split("\n\n", 1)[0]
        allowed = set(re.findall(r"`(/[a-z-]+)`", allowlist_block))
        self.assertIn("/status", allowed, "the allowlist block failed to parse")

        rows = [
            line for line in text.splitlines()
            if line.startswith("| Quality-config findings")
            or line.startswith("| New quality-config findings")
        ]
        self.assertEqual(len(rows), 2, "both next-action rows must be present")
        for row in rows:
            for command in re.findall(r"`(/[a-z-]+)`", row):
                self.assertIn(command, allowed, f"{command} is not allowlisted")


class ClassificationDocBindingTests(unittest.TestCase):
    """AC-1.1 through AC-1.5 — the doc Stories 2-4 implement against."""

    DOC = REPO_ROOT / ".writ" / "docs" / "quality-signal-classification.md"

    def test_every_finding_code_is_defined(self) -> None:
        text = read(self.DOC)
        for code in (
            "build_gate_disabled", "coverage_threshold_absent", "coverage_scope_gap",
            "tests_excluded_from_typecheck", "duplicate_lockfile", "could_not_parse",
            "coverage_below_threshold", "coverage_regression", "coverage_report_absent",
            "test_imports_no_source", "build_failed_source", "build_failed_environment",
            "unsupported_stack",
        ):
            self.assertIn(code, text, code)

    def test_the_verdict_rules_are_specified(self) -> None:
        text = read(self.DOC)
        self.assertIn("never exits 2", text)
        self.assertIn("Unparseable is not absent", text)
        self.assertIn("No automatic re-baselining", text)

    def test_every_unverifiable_reason_is_registered(self) -> None:
        text = read(self.DOC)
        for reason in (
            "could_not_parse", "unsupported_stack", "no_coverage_report",
            "unknown_report_format", "truncated_report", "environment",
            "timeout", "nothing_inspected",
        ):
            self.assertIn(reason, text, reason)


if __name__ == "__main__":
    unittest.main()
