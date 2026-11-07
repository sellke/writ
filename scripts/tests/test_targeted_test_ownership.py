#!/usr/bin/env python3
"""Targeted-test ownership (2026-11-06-lean-story-pipeline Story 4, Rule 6).

The coding agent runs only the story's targeted tests, the Gate 3 reviewers
read `recorded_test_results` and run no suite (one ADR-032 evidence repro
aside), and Gate 4 says where the full suite runs: once at `implement-spec`
Step 4.1, or in `/ship` for a standalone story. Pins key phrases, not whole
paragraphs, so later prose edits break only the rule they change.

Reads the source files and their generated copies as text, and runs
`gen-platform-trees.py --check`, which writes nothing.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CODING_AGENT = REPO_ROOT / "agents" / "coding-agent.md"
EVALUATOR_AGENT = REPO_ROOT / "agents" / "evaluator-agent.md"
REVIEW_AGENT = REPO_ROOT / "agents" / "review-agent.md"
IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"
IMPLEMENT_SPEC = REPO_ROOT / "commands" / "implement-spec.md"
GOVERNOR_TEST = REPO_ROOT / "scripts" / "tests" / "test_governor_enforcement.py"
GEN_TREES = REPO_ROOT / "scripts" / "gen-platform-trees.py"

COMMAND_BYTE_BUDGET = 24960  # pinned in test_governor_enforcement.py

# AC-4.1: the coder's self-verification test step.
CODER_TARGETED = (
    "Run only the story's test files and any test file that imports a "
    "changed source file."
)
CODER_NO_SUITE = "Never run the full suite, however fast"
CODER_RETIRED = (
    "Run the full suite if fast (<30s)",
    "if the full suite is slow",
)

# AC-4.2: the same rule in both Gate 3 agents.
REVIEWER_RULE = (
    "Read `recorded_test_results` for test evidence and never run the full "
    "suite. You may run one ADR-032 evidence repro, or re-run a test file the "
    "recorded run names; that is not a suite run."
)

# AC-4.3: Gate 4 names where the suite runs.
GATE4_TARGETED = "Gate 3's recorded run is targeted"
GATE4_FULL_SUITE = (
    "The full suite runs once, at `implement-spec` Step 4.1, or in `/ship` "
    "for a standalone story."
)
GATE4_HEADING = "#### Gate 4: Testing Agent"
FULL_PIPELINE_HEADING = "### Full-Pipeline Gates (`--full-pipeline` only)"

# AC-4.4: generated copies, keyed by the source they are rendered from.
GENERATED = {
    CODING_AGENT: (
        "claude-code/agents/writ-coder.md",
        "cursor/plugin/agents/coding-agent.md",
        "codex/agents/coding-agent.toml",
        "plugins/writ/agents/coding-agent.md",
        "plugins/writ/agents/writ-coder.md",
    ),
    EVALUATOR_AGENT: (
        "claude-code/agents/writ-evaluator.md",
        "cursor/plugin/agents/evaluator-agent.md",
        "codex/agents/evaluator-agent.toml",
        "plugins/writ/agents/evaluator-agent.md",
        "plugins/writ/agents/writ-evaluator.md",
    ),
    REVIEW_AGENT: (
        "claude-code/agents/writ-reviewer.md",
        "cursor/plugin/agents/review-agent.md",
        "codex/agents/review-agent.toml",
        "plugins/writ/agents/review-agent.md",
        "plugins/writ/agents/writ-reviewer.md",
    ),
    IMPLEMENT_STORY: (
        "cursor/plugin/commands/implement-story.md",
        "plugins/writ/commands/implement-story.md",
    ),
}
PINS = {
    CODING_AGENT: (CODER_TARGETED, CODER_NO_SUITE),
    EVALUATOR_AGENT: (REVIEWER_RULE,),
    REVIEW_AGENT: (REVIEWER_RULE,),
    IMPLEMENT_STORY: (GATE4_TARGETED, GATE4_FULL_SUITE),
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    return text[i : text.index(end, i)]


def self_verification(text: str) -> str:
    return section(text, "## Self-Verification", "## Tasks to Complete")


class CoderRunsTargetedTests(unittest.TestCase):
    """AC-4.1"""

    def test_ac41_self_verification_runs_only_targeted_tests(self) -> None:
        """AC-4.1: step 1 names the story's tests and importers of changed files."""
        step = self_verification(read(CODING_AGENT))
        self.assertIn(CODER_TARGETED, step)
        self.assertIn(CODER_NO_SUITE, step)

    def test_ac41_full_suite_under_30s_rule_is_gone(self) -> None:
        """AC-4.1: the run-the-suite-when-fast rule no longer appears."""
        text = read(CODING_AGENT)
        for phrase in CODER_RETIRED:
            self.assertNotIn(phrase, text)
        self.assertNotIn("<30s", self_verification(text))

    def test_ac41_coder_names_where_the_full_suite_runs(self) -> None:
        """AC-4.1: the coder is told the suite runs at Step 4.1 or in /ship."""
        step = self_verification(read(CODING_AGENT))
        self.assertIn("`implement-spec` Step 4.1", step)
        self.assertIn("`/ship`", step)


class ReviewersReadRecordedResults(unittest.TestCase):
    """AC-4.2"""

    def test_ac42_both_gate3_agents_carry_the_rule(self) -> None:
        """AC-4.2: evaluator and review agent read recorded results, run no suite."""
        for path in (EVALUATOR_AGENT, REVIEW_AGENT):
            self.assertIn(REVIEWER_RULE, read(path), path.name)

    def test_ac42_rule_sits_in_the_prompt_beside_the_recorded_results(self) -> None:
        """AC-4.2: the rule is in the spawn prompt, after `{recorded_test_results}`."""
        for path in (EVALUATOR_AGENT, REVIEW_AGENT):
            text = read(path)
            prompt = text.split("## Prompt Template", 1)[1]
            slot = prompt.index("{recorded_test_results}")
            rule = prompt.index(REVIEWER_RULE)
            self.assertLess(slot, rule, path.name)
            self.assertLess(rule - slot, 400, path.name)

    def test_ac42_no_other_line_bans_every_test_run(self) -> None:
        """AC-4.2: the repro allowance is the only run rule; no line forbids all runs."""
        for path in (EVALUATOR_AGENT, REVIEW_AGENT):
            text = read(path)
            self.assertEqual(text.count("never run the full suite"), 1, path.name)
            self.assertNotRegex(text, r"(?i)(do not|never) run (any )?tests\b",
                                path.name)


class Gate4StatesSuiteOwnership(unittest.TestCase):
    """AC-4.3"""

    def gate4(self) -> str:
        return section(read(IMPLEMENT_STORY), GATE4_HEADING, FULL_PIPELINE_HEADING)

    def test_ac43_recorded_run_is_targeted(self) -> None:
        """AC-4.3: Gate 4 says the orchestrator's recorded run is targeted."""
        self.assertIn(GATE4_TARGETED, self.gate4())

    def test_ac43_full_suite_runs_at_step_41_or_ship(self) -> None:
        """AC-4.3: the full suite runs once at implement-spec Step 4.1 or in /ship."""
        self.assertIn(GATE4_FULL_SUITE, self.gate4())

    def test_ac43_the_default_path_states_it(self) -> None:
        """AC-4.3: the statement is on the default path, before `--full-pipeline`."""
        default = self.gate4().split("**`--full-pipeline`:**", 1)[0]
        self.assertIn(GATE4_TARGETED, default)
        self.assertIn(GATE4_FULL_SUITE, default)

    def test_ac43_step_41_names_a_real_full_suite_step(self) -> None:
        """AC-4.3: the cited step exists and runs the full suite."""
        step = section(read(IMPLEMENT_SPEC), "#### Step 4.1:", "\n#### ")
        self.assertIn("Full test suite", step)


class GeneratedCopiesAndBudget(unittest.TestCase):
    """AC-4.4"""

    def test_ac44_generated_copies_carry_the_same_wording(self) -> None:
        """AC-4.4: every generated copy carries each pinned phrase of its source."""
        for source, copies in GENERATED.items():
            for rel in copies:
                text = read(REPO_ROOT / rel)
                for pin in PINS[source]:
                    if rel.startswith("plugins/writ/"):
                        # The Claude Code plugin namespaces slash commands.
                        pin = pin.replace("`/ship`", "`/writ:ship`")
                    self.assertIn(pin, text, rel)
                if source is CODING_AGENT:
                    self.assertNotIn(CODER_RETIRED[0], text, rel)

    def test_ac44_gen_platform_trees_check_is_clean(self) -> None:
        """AC-4.4: `gen-platform-trees.py --check` reports no stale copy."""
        proc = subprocess.run(
            [sys.executable, str(GEN_TREES), "--check"],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)

    def test_ac44_known_over_budget_records_the_new_size_with_a_date(self) -> None:
        """AC-4.4: KNOWN_OVER_BUDGET equals size - budget, with a dated Story 4 entry."""
        governor = read(GOVERNOR_TEST)
        size = len(IMPLEMENT_STORY.read_bytes())
        match = re.search(r'"commands/implement-story\.md":\s*(\d+)', governor)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), size - COMMAND_BYTE_BUDGET)
        entry = re.search(
            r"# 2026-\d\d-\d\d \(lean-story-pipeline Story 4\)[^\n]*\n"
            r"(?:\s*#[^\n]*\n)*",
            governor,
        )
        self.assertIsNotNone(entry, "no dated Story 4 entry")
        prose = " ".join(line.strip().lstrip("#").strip()
                         for line in entry.group(0).splitlines())
        self.assertIn(f"file 38542 -> {size}", prose)


if __name__ == "__main__":
    unittest.main()
