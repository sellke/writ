#!/usr/bin/env python3
"""Contract tests for agents/evaluator-agent.md (Phase 11 Stage 4b Story 1).

Asserts Agent Configuration, AC + recorded-test rubric language, residual
scope, no how-to-fix / apply-patch instruction, and that review-agent.md is
not in this story's edited file set. Does not import review-agent.md.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Authenticity pin: test-integrity.py extracts JS-style from '…' specifiers,
# not Python imports. This test's unit under test is the agent file it reads.
# from "../../agents/evaluator-agent.md"
AGENT_PATH = REPO_ROOT / "agents" / "evaluator-agent.md"

PROBLEM = (
    "A story that satisfies its task list can still miss an acceptance "
    "criterion or quietly redefine the spec, and self-critique in the same "
    "context as the coder does not catch it."
)
OUTCOME = (
    "An EVALUATION_RESULT against the story's acceptance criteria and test "
    "results, with residual architecture / security / taste named, and no "
    "applied patch."
)
EXIT_CRITERIA = (
    "the number of criteria adjudicated equals the number supplied; none "
    "left unaddressed",
    "Overall Drift reads None, Small, Medium, or Large, and Large produces "
    "PAUSE rather than FAIL",
    "every FAIL issue carries Location and Severity; Suggested Fix is "
    "optional and is never applied",
)

REVIEW_AGENT_REL = "agents/review-agent.md"


def _git_story_paths() -> set[str]:
    cmds = (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: set[str] = set()
    for cmd in cmds:
        out = subprocess.check_output(cmd, cwd=REPO_ROOT, text=True)
        for line in out.splitlines():
            name = line.strip()
            if name:
                paths.add(name)
    return paths


class EvaluatorAgentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            AGENT_PATH.is_file(),
            "agents/evaluator-agent.md is missing",
        )
        self.text = AGENT_PATH.read_text(encoding="utf-8")

    def test_authenticity_pin_resolves_to_agent_file(self) -> None:
        pinned = (Path(__file__).resolve().parent / "../../agents/evaluator-agent.md").resolve()
        self.assertEqual(pinned, AGENT_PATH.resolve())

    def test_unindented_model_tier_anchor_once(self) -> None:
        hits = [ln for ln in self.text.splitlines() if ln == "model_tier: anchor"]
        self.assertEqual(
            hits,
            ["model_tier: anchor"],
            "model_tier: anchor must appear exactly once as an unindented line",
        )

    def test_readonly_true(self) -> None:
        self.assertRegex(self.text, r"(?m)^readonly: true")

    def test_problem_outcome_exit_criteria_verbatim(self) -> None:
        self.assertIn(PROBLEM, self.text)
        self.assertIn(OUTCOME, self.text)
        for criterion in EXIT_CRITERIA:
            self.assertIn(criterion, self.text)

    def test_rubric_is_acceptance_criteria_and_test_results(self) -> None:
        lower = self.text.lower()
        self.assertIn("acceptance criteria", lower)
        self.assertTrue(
            "recorded test results" in lower or "test results" in lower,
            "prompt must name recorded/test results as part of the rubric",
        )
        self.assertRegex(
            self.text,
            r'(?i)do not .{0,20}["“]?find problems["”]?',
            "prompt must forbid finding problems beyond the rubric",
        )

    def test_residual_architecture_security_taste(self) -> None:
        lower = self.text.lower()
        self.assertIn("architecture", lower)
        self.assertIn("security", lower)
        self.assertIn("taste", lower)
        self.assertIn("residual", lower)

    def test_no_how_to_fix_or_apply_patch(self) -> None:
        lower = self.text.lower()
        self.assertIn("do not tell the coder how to fix", lower)
        self.assertIn("do not apply a patch", lower)
        self.assertNotIn("rewrite this function", lower)
        self.assertNotIn("be actionable", lower)
        self.assertNotIn("every issue gets a suggested fix", lower)

    def test_suggested_fix_optional_never_applied(self) -> None:
        lower = self.text.lower()
        self.assertIn("suggested fix", lower)
        self.assertIn("optional", lower)
        self.assertIn("never applied", lower)

    def test_evaluation_result_heading(self) -> None:
        self.assertIn("EVALUATION_RESULT", self.text)

    def test_review_agent_not_in_story_edit_set(self) -> None:
        paths = _git_story_paths()
        self.assertNotIn(
            REVIEW_AGENT_REL,
            paths,
            "agents/review-agent.md must not appear in git diff --name-only, "
            "--cached, or untracked files",
        )


if __name__ == "__main__":
    unittest.main()
