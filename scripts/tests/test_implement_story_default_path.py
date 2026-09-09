#!/usr/bin/env python3
"""Contract tests for commands/implement-story.md default path (Stage 4b Story 2).

Reads the command as text. Asserts AC-2.1–2.5 plus pin-sensitive literals
that keep existing wiring / governor tests green.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Authenticity pin: test-integrity.py extracts JS-style from '…' specifiers,
# not Python imports. This test's unit under test is the command it reads.
# from "../../commands/implement-story.md"
COMMAND_PATH = REPO_ROOT / "commands" / "implement-story.md"

ALLOWED_DEFAULT_STEMS = frozenset({"coding-agent", "evaluator-agent"})
FULL_PIPELINE_STEMS = (
    "architecture-check",
    "review",
    "testing",
    "visual-qa",
    "documentation",
)
ROUTING_PREFIXES = (
    "| Architecture Check (Gate 0) |",
    "| Coding Agent (Gate 1) |",
    "| Review Agent (Gate 3) |",
    "| Testing Agent (Gate 4) |",
    "| Documentation Agent (Gate 5) |",
)
PAIR_COUNTS_ONCE = (
    "the floor attempt and its anchor re-run count as one attempt "
    "against `loop.max_iterations`"
)


def _section(text: str, start: str, end: str | None = None) -> str:
    i = text.index(start)
    if end is None:
        return text[i:]
    return text[i : text.index(end, i)]


def _default_agent_markers(text: str) -> list[str]:
    """`> **Agent:**` lines not immediately guarded by `--full-pipeline`."""
    last_nonempty = ""
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith("> **Agent:**"):
            guarded = (
                "--full-pipeline" in last_nonempty or "--full-pipeline" in line
            )
            if not guarded:
                out.append(line)
        if line.strip():
            last_nonempty = line
    return out


def _stems_in(line: str) -> set[str]:
    found = set()
    for m in re.finditer(r"([a-z0-9-]+-agent)", line):
        found.add(m.group(1))
    return found


class ImplementStoryDefaultPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(COMMAND_PATH.is_file(), "commands/implement-story.md is missing")
        self.text = COMMAND_PATH.read_text(encoding="utf-8")

    def test_authenticity_pin_resolves_to_command_file(self) -> None:
        pinned = (
            Path(__file__).resolve().parent / "../../commands/implement-story.md"
        ).resolve()
        self.assertEqual(pinned, COMMAND_PATH.resolve())

    def test_ac21_no_default_token_and_invocation_matrix(self) -> None:
        self.assertNotIn("--default", self.text)
        inv = _section(self.text, "## Invocation", "## Pipeline")
        self.assertIn("--full-pipeline", inv)
        self.assertIn("`coding-agent`", inv)
        self.assertIn("`evaluator-agent`", inv)
        story_row = next(
            ln for ln in inv.splitlines()
            if ln.startswith("| `/implement-story story-") and "--" not in ln.split("|")[1]
        )
        self.assertIn("coding-agent", story_row)
        self.assertIn("evaluator-agent", story_row)
        self.assertNotIn("architecture-check", story_row)
        full_row = next(ln for ln in inv.splitlines() if "--full-pipeline" in ln)
        for name in FULL_PIPELINE_STEMS:
            self.assertIn(name, full_row, name)
        self.assertIn("coding", full_row)
        quick_row = next(ln for ln in inv.splitlines() if "--quick" in ln)
        self.assertIn("coding-agent", quick_row)
        self.assertNotIn("evaluator-agent", quick_row)
        review_row = next(ln for ln in inv.splitlines() if "--review-only" in ln)
        self.assertIn("evaluator-agent", review_row)
        self.assertNotIn("coding-agent", review_row)

    def test_ac22_default_spawns_and_pipeline_runs_as(self) -> None:
        for line in _default_agent_markers(self.text):
            extra = _stems_in(line) - ALLOWED_DEFAULT_STEMS
            self.assertFalse(extra, f"default-path Agent marker names {extra}: {line}")
        default_stems = set()
        for line in _default_agent_markers(self.text):
            default_stems |= _stems_in(line) & ALLOWED_DEFAULT_STEMS
        self.assertEqual(default_stems, ALLOWED_DEFAULT_STEMS)

        pipe = _section(self.text, "## Pipeline", "## Command Process")
        g0 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 0 |"))
        self.assertIn("arch-check.py", g0)
        self.assertIn("architecture-check-agent", g0)
        self.assertIn("--full-pipeline", g0)
        self.assertIn("--quick", g0)
        self.assertIn("--review-only", g0)
        g3 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 3 |"))
        self.assertIn("evaluator-agent", g3)
        self.assertIn("review-agent", g3)
        self.assertIn("--full-pipeline", g3)
        g4 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 4 |"))
        self.assertIn("test-integrity.py", g4)
        self.assertIn("testing-agent", g4)
        self.assertIn("--full-pipeline", g4)
        g45 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 4.5 |"))
        self.assertIn("--full-pipeline", g45)
        self.assertIn("visual-qa", g45)
        self.assertIn("default", g45.lower())
        g5 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 5 |"))
        self.assertIn("docs-check.py", g5)
        self.assertIn("documentation-agent", g5)
        self.assertIn("--full-pipeline", g5)

        for note_start in (
            "**Sub-agent completeness:**",
            "**Sub-agent worktree integration:**",
        ):
            note = _section(self.text, note_start, "---")
            self.assertIn("Gate 1", note)
            self.assertIn("Gate 3", note)
            for gate in ("Gate 0", "Gate 4", "Gate 4.5"):
                for ln in note.splitlines():
                    if gate in ln and "--full-pipeline" not in ln:
                        self.fail(f"{note_start} lists {gate} on default: {ln}")

        desc = _section(self.text, "description:", "problem:")
        overview = _section(self.text, "## Overview", "## Required Artifacts")
        for block in (desc, overview):
            self.assertNotRegex(
                block,
                r"(?i)full SDLC pipeline",
                "no-flag must not be described as the full SDLC pipeline",
            )
        self.assertIn("--full-pipeline", overview)
        self.assertIn("evaluator-agent", overview)

        exit3 = next(
            ln for ln in self.text.splitlines()
            if "80 percent line coverage" in ln or "80 percent line coverage" in ln
        )
        self.assertTrue(
            "designed" in exit3.lower() or "default-path" in exit3.lower()
            or "agent skip" in exit3.lower() or "agent-only" in exit3.lower(),
            "third exit_criterion must exempt designed default agent-skips",
        )

    def test_ac23_two_fail_escalation(self) -> None:
        self.assertIn("evaluator_fail_count", self.text)
        self.assertRegex(self.text, r"evaluator_fail_count.*0|starts at 0")
        self.assertIn("consecutive", self.text.lower())
        self.assertIn("remainder", self.text.lower())
        self.assertIn("--full-pipeline", self.text)
        self.assertIn("do not AskQuestion", self.text)
        self.assertIn("do not restart Gate 0", self.text)
        self.assertRegex(self.text, r"(?i)reset.*evaluator_fail_count|evaluator_fail_count.*reset|Reset .*counter")
        self.assertIn("--quick` never escalates", self.text)
        self.assertIn("no silent", self.text.lower())
        review_only = [ln for ln in self.text.splitlines() if "--review-only" in ln]
        self.assertTrue(
            any("FAIL" in ln or "fail" in ln for ln in review_only),
            "--review-only FAIL must be described",
        )
        self.assertTrue(
            any("recode" in ln.lower() or "no recode" in ln.lower() for ln in review_only),
            "--review-only must say there is no recode",
        )

    def test_ac24_override_and_gate4_fail(self) -> None:
        gate3 = _section(self.text, "#### Gate 3: Review Agent", "#### Gate 3.5:")
        self.assertIn("Verify the claim, don't trust it.", gate3)
        self.assertIn("scripts/review-override.py check", gate3)
        self.assertIn("FAIL-only", gate3)
        self.assertIn("does not force PASS", gate3)
        self.assertIn("⚠️ DEGRADED", gate3)
        self.assertIn("evaluator-agent", gate3)
        self.assertIn("review-agent", gate3)
        self.assertIn("does not wash", gate3.lower())
        self.assertIn("EVALUATION_RESULT", gate3)
        self.assertIn("REVIEW_RESULT", gate3)
        self.assertIn("`--quick`", gate3)
        self.assertIn("`--review-only`", gate3)
        self.assertIn("`--full-pipeline`", gate3)

        gate4 = _section(self.text, "#### Gate 4: Testing Agent", "#### Gate 4.5:")
        self.assertIn("coding-agent", gate4)
        self.assertIn("restarting **Gate 1**", gate4)
        self.assertIn("testing-agent", gate4)
        self.assertIn("restarting **Gate 4**", gate4)
        self.assertIn("test-integrity.py", gate4)
        self.assertNotIn("> **Agent:** `agents/testing-agent.md`", gate4.split("`--full-pipeline`")[0])

    def test_ac25_gate0_45_5_and_frontmatter(self) -> None:
        self.assertIn("  - id: gate3_review\n    script: scripts/review-override.py", self.text)
        self.assertEqual(self.text.count("#### Gate 3: Review Agent"), 1)

        gate0 = _section(self.text, "#### Gate 0: Architecture Check", "#### Gate 0.5:")
        self.assertIn("scripts/arch-check.py check", gate0)
        self.assertIn("--planned", gate0)
        self.assertIn("never on ABORT", gate0)
        self.assertIn("ADR-024", gate0)
        self.assertIn("⚠️ DEGRADED", gate0)
        self.assertIn("escalated(agent=architecture-check-agent, site=implement-story.gate0, origin=", gate0)
        self.assertIn("(no-op until ADR-025 Story 1)", gate0)
        self.assertIn("The line has no sink today", gate0)
        self.assertIn(PAIR_COUNTS_ONCE, gate0)
        default_agents = _default_agent_markers(gate0)
        self.assertEqual(default_agents, [], default_agents)
        self.assertIn("`--full-pipeline`", gate0)
        self.assertIn("planned", gate0)

        gate45 = _section(self.text, "#### Gate 4.5: Visual QA (Optional)", "#### Gate 5:")
        self.assertNotIn("%", gate45)
        self.assertNotIn(" percent", gate45)
        for word in ("PASS", "SOFT PASS", "FAIL"):
            self.assertIn(word, gate45)
        self.assertIn("`--full-pipeline`", gate45)
        self.assertTrue(
            "default" in gate45.lower() and "skip" in gate45.lower(),
            "Gate 4.5 must skip on default even with visual refs",
        )
        self.assertEqual(_default_agent_markers(gate45), [])

        gate5 = _section(self.text, "#### Gate 5: Documentation Agent")
        self.assertIn("scripts/docs-check.py check", gate5)
        self.assertIn("documentation-agent", gate5)
        self.assertIn("⚠️ DEGRADED", gate5)
        self.assertIn("`--full-pipeline`", gate5)
        self.assertEqual(_default_agent_markers(gate5.split("## Error Handling")[0]), [])

        control = _section(self.text, "**Control flow:**", "## Command Process")
        self.assertIn("--full-pipeline", control)
        self.assertIn("ABORT", control)

    def test_pin_literals_and_forbidden_gate_numbers(self) -> None:
        for row in ROUTING_PREFIXES:
            self.assertIn(row, self.text)
        self.assertIn("| Gate 2 | Lint, Typecheck, Format & Build Smoke |", self.text)
        self.assertIn("Gate 2 (lint + build smoke)", self.text)
        self.assertNotIn("Gate 2.6", self.text)
        self.assertNotIn("Gate 4.6", self.text)
        self.assertIn("problem:", self.text)
        self.assertIn("outcome:", self.text)
        self.assertIn("exit_criteria:", self.text)

    def test_quick_mode_hatch_is_full_pipeline(self) -> None:
        quick = _section(self.text, "## Quick Mode", "## Completion")
        self.assertIn("Gate 2 (lint + build smoke)", quick)
        self.assertIn("--full-pipeline", quick)
        self.assertIn("coding-agent", quick)
        before_hatch = quick.split("--full-pipeline")[0]
        self.assertNotIn("evaluator-agent", before_hatch)
        self.assertNotRegex(
            quick,
            r"full pipeline later:\s*\n```\s*\n/implement-story story-3 --review-only",
        )

    def test_yaml_description_is_not_full_sdlc(self) -> None:
        desc = self.text.split("description:", 1)[1].split("\n", 1)[0]
        self.assertNotIn("full SDLC pipeline", desc)


if __name__ == "__main__":
    unittest.main()
