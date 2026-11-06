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
# 2026-11-06-lean-story-pipeline Story 2: gates with no recorded catch
# (gate-evidence.md) moved under this heading; the rest stay in Step 3.
FULL_PIPELINE_HEADING = "### Full-Pipeline Gates (`--full-pipeline` only)"
STEP3_HEADING = "### Step 3: Run Pipeline"
DEMOTED = frozenset({"gate0_arch", "gate4_5_behavior", "gate5_docs"})
HEADING_TO_ID = {
    "0": "gate0_arch", "0.5": "gate0_5_boundary", "1": "gate1_coding",
    "2": "gate2_build", "2.5": "gate2_5_surface", "3": "gate3_review",
    "3.5": "gate3_5_drift", "4": "gate4_tests", "4.5": "gate4_5_behavior",
    "5": "gate5_docs",
}


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


def _gate_paths(text: str) -> dict[str, str | None]:
    """`gates:` frontmatter id -> its `path:` value (None when absent)."""
    front = text.split("\n---\n", 1)[0]
    block = front.split("\ngates:\n", 1)[1]
    paths: dict[str, str | None] = {}
    current = None
    for line in block.splitlines():
        m = re.match(r"^  - id: (\S+)$", line)
        if m:
            current = m.group(1)
            paths[current] = None
            continue
        m = re.match(r"^    path: (\S+)$", line)
        if m and current:
            paths[current] = m.group(1)
    return paths


def _gate_parents(text: str) -> dict[str, str]:
    """Each `#### Gate N` heading's id -> the `###` heading it sits under."""
    parents: dict[str, str] = {}
    parent = ""
    in_fence = False
    for line in text.split("\n---\n", 1)[1].splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        if line.startswith("### ") or line.startswith("## "):
            parent = line
        m = re.match(r"^#### Gate (\d+(?:\.\d+)?)\b", line)
        if m:
            parents[HEADING_TO_ID[m.group(1)]] = parent
    return parents


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
        # Story 2 (2026-11-06-lean-story-pipeline): Gates 0, 4.5 and 5 are
        # skipped on every path but --full-pipeline, where agent and script run.
        g0 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 0 |"))
        self.assertIn("arch-check.py", g0)
        self.assertIn("architecture-check-agent", g0)
        self.assertIn("| all but `--full-pipeline` |", g0)
        g3 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 3 |"))
        self.assertIn("evaluator-agent", g3)
        self.assertIn("review-agent", g3)
        self.assertIn("--full-pipeline", g3)
        g4 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 4 |"))
        self.assertIn("test-integrity.py", g4)
        self.assertIn("testing-agent", g4)
        self.assertIn("--full-pipeline", g4)
        g45 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 4.5 |"))
        self.assertIn("app-verify.py", g45)
        self.assertIn("visual-qa", g45)
        self.assertIn("| all but `--full-pipeline` |", g45)
        g5 = next(ln for ln in pipe.splitlines() if ln.startswith("| Gate 5 |"))
        self.assertIn("docs-check.py", g5)
        self.assertIn("documentation-agent", g5)
        self.assertIn("| all but `--full-pipeline` |", g5)
        for row in (pipe.splitlines()):
            if row.startswith("| Gate ") and row not in (g0, g45, g5):
                self.assertNotIn("all but `--full-pipeline`", row)

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
        # 2026-11-04 (2026-11-04-evidence-gated-review Story 3): the FAIL-only
        # sentence went; a check pass is "no override", and the decision table
        # (row 9) can now wash an agent FAIL.
        self.assertIn("→ no override", gate3)
        override = next(line for line in gate3.splitlines() if "→ no override" in line)
        self.assertIn("never `⚠️ DEGRADED`", override)
        self.assertIn("⚠️ DEGRADED", gate3)
        self.assertIn("evaluator-agent", gate3)
        self.assertIn("review-agent", gate3)
        self.assertIn("EVALUATION_RESULT", gate3)
        self.assertIn("REVIEW_RESULT", gate3)
        self.assertIn("`--quick`", gate3)
        self.assertIn("`--review-only`", gate3)
        self.assertIn("`--full-pipeline`", gate3)

        gate4 = _section(self.text, "#### Gate 4: Testing Agent", FULL_PIPELINE_HEADING)
        self.assertIn("coding-agent", gate4)
        self.assertIn("restarting **Gate 1**", gate4)
        self.assertIn("testing-agent", gate4)
        self.assertIn("restarting **Gate 4**", gate4)
        self.assertIn("test-integrity.py", gate4)
        self.assertNotIn("> **Agent:** `agents/testing-agent.md`", gate4.split("`--full-pipeline`")[0])

    def test_ac25_gate0_45_5_and_frontmatter(self) -> None:
        self.assertIn("  - id: gate3_review\n    script: scripts/review-override.py", self.text)
        self.assertEqual(self.text.count("#### Gate 3: Review Agent"), 1)

        gate0 = _section(self.text, "#### Gate 0: Architecture Check", "#### Gate 4.5:")
        self.assertIn("scripts/arch-check.py check", gate0)
        self.assertIn("--planned", gate0)
        self.assertIn("never on ABORT", gate0)
        self.assertIn("ADR-024", gate0)
        self.assertIn("⚠️ DEGRADED", gate0)
        # 2026-10-20-harness-cuts Story 3 (AC-3.1): the no-op emit and its
        # sink sentence are gone; the iteration accounting stays.
        self.assertNotIn("(no-op until ADR-025 Story 1)", gate0)
        self.assertNotIn("The line has no sink today", gate0)
        self.assertNotIn("escalated(agent=architecture-check-agent", gate0)
        self.assertIn(PAIR_COUNTS_ONCE, gate0)
        default_agents = _default_agent_markers(gate0)
        self.assertEqual(default_agents, [], default_agents)
        self.assertIn("`--full-pipeline`", gate0)
        self.assertIn("planned", gate0)

        # 2026-10-01-behavioral-verification Story 4 (AC-4.1, AC-4.2): a
        # script decides Gate 4.5; visual-qa is notes-only under --full-pipeline.
        gate45 = _section(self.text, "#### Gate 4.5: Behavioral Verification", "#### Gate 5:")
        self.assertNotIn("%", gate45)
        self.assertNotIn(" percent", gate45)
        self.assertIn("python3 scripts/app-verify.py touched", gate45)
        self.assertIn("run --recipe .writ/docs/app-verification.md", gate45)
        self.assertIn("--run-label story-N", gate45)
        self.assertIn("Gate 1", gate45)
        self.assertIn("shared review-loop cap", gate45)
        self.assertIn("**not** marked `⚠️ DEGRADED`", gate45)
        self.assertIn("no mapped features", gate45)
        self.assertIn("never asks a question", gate45)
        self.assertNotIn("Task(", gate45)
        self.assertEqual(_default_agent_markers(gate45), [])
        full = _section(gate45, "**`--full-pipeline`:**")
        self.assertIn("agents/visual-qa-agent.md", full)
        self.assertIn("notes", full)
        self.assertIn("never fail", full)
        self.assertIn("count toward the review loop", full)
        self.assertIn("--features <touched ids, comma-joined>", gate45)
        # Story 2: Gate 4.5 runs only under --full-pipeline, so its old
        # --quick skip and --review-only clauses are gone; a script still
        # decides and a fail still recodes on the shared cap (asserted above).
        self.assertNotIn("Skip in", gate45)
        self.assertNotIn("`--review-only`", gate45)
        flow = _section(self.text, "**Control flow:**", "## Command Process")
        self.assertNotIn("visual QA", flow)
        loop = _section(self.text, "**Review loop:**", "**Verify the claim")
        self.assertNotIn("visual QA", loop)
        self.assertIn("Gate 4.5 script fail", loop)

        gate5 = _section(self.text, "#### Gate 5: Documentation Agent", "### Step 4:")
        self.assertIn("scripts/docs-check.py check", gate5)
        self.assertIn("documentation-agent", gate5)
        self.assertIn("⚠️ DEGRADED", gate5)
        self.assertIn("`--full-pipeline`", gate5)
        self.assertEqual(_default_agent_markers(gate5), [])

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


class GateDemotionTests(unittest.TestCase):
    """2026-11-06-lean-story-pipeline Story 2: gates whose gate-evidence.md row
    reads `none recorded` with no kept dependent run only under --full-pipeline."""

    def setUp(self) -> None:
        self.text = COMMAND_PATH.read_text(encoding="utf-8")
        self.paths = _gate_paths(self.text)
        self.parents = _gate_parents(self.text)

    def test_ac21_demoted_sections_sit_under_the_full_pipeline_heading(self) -> None:
        """AC-2.1: section under the heading and `path: full-pipeline`."""
        self.assertEqual(self.text.count(FULL_PIPELINE_HEADING + "\n"), 1)
        demoted = {gid for gid, path in self.paths.items() if path == "full-pipeline"}
        self.assertEqual(demoted, DEMOTED)
        for gid in DEMOTED:
            self.assertEqual(self.parents[gid], FULL_PIPELINE_HEADING, gid)
        under = {gid for gid, parent in self.parents.items()
                 if parent == FULL_PIPELINE_HEADING}
        self.assertEqual(under, DEMOTED)

    def test_ac22_kept_gates_stay_in_step_3_on_the_default_path(self) -> None:
        """AC-2.2: kept sections stay in Step 3; their entry is not full-pipeline."""
        self.assertEqual(set(self.paths), set(HEADING_TO_ID.values()))
        for gid in set(self.paths) - DEMOTED:
            self.assertIn(self.paths[gid], (None, "default"), gid)
            self.assertEqual(self.parents[gid], STEP3_HEADING, gid)
        # Gate 3's PAUSE lands in Gate 3.5 § A, and Step 4 reads its § B
        # extraction, so Gate 3.5 must follow Gate 3 on the default path.
        step3 = _section(self.text, STEP3_HEADING, FULL_PIPELINE_HEADING)
        self.assertIn("##### A. Drift Response", step3)
        self.assertIn('##### B. "What Was Built" Data Extraction', step3)
        self.assertLess(step3.index("#### Gate 3: Review Agent"),
                        step3.index("#### Gate 3.5:"))

    def test_ac21_full_pipeline_section_says_default_runs_none_of_it(self) -> None:
        """AC-2.1: the heading's lead states the skip and that it is not DEGRADED."""
        section = _section(self.text, FULL_PIPELINE_HEADING, "### Step 4:")
        lead = section.split("#### Gate 0:", 1)[0]
        for phrase in ("default path", "`--quick`", "`--review-only`",
                       "not `⚠️ DEGRADED`", "Gate 0 before Gate 0.5",
                       "after Gate 4"):
            self.assertIn(phrase, lead, phrase)
        self.assertLess(section.index("#### Gate 0:"), section.index("#### Gate 4.5:"))
        self.assertLess(section.index("#### Gate 4.5:"), section.index("#### Gate 5:"))

    def test_ac23_default_path_wording_is_gone_from_demoted_gates(self) -> None:
        """AC-2.3: no sentence still runs a demoted gate's script on default."""
        section = _section(self.text, FULL_PIPELINE_HEADING, "### Step 4:")
        for gone in ("**Default:**", "Default is script-only", "always on default",
                     "immediately on default", "> **Skip in:**"):
            self.assertNotIn(gone, section, gone)
        self.assertNotIn("Default Gate 0 is script-only", self.text)
        quick = _section(self.text, "## Quick Mode", "## Completion")
        keeps = next(ln for ln in quick.splitlines() if ln.startswith("**Keeps:**"))
        skips = next(ln for ln in quick.splitlines() if ln.startswith("**Skips:**"))
        self.assertNotIn("Gate 0", keeps)
        self.assertNotIn("Gate 5", keeps)
        self.assertIn("Gates 0, 4.5 and 5", skips)
        flow = _section(self.text, "**Control flow:**", "## Command Process")
        self.assertIn("Gates 0, 4.5 and 5 run only under `--full-pipeline`", flow)
        exit3 = next(ln for ln in self.text.splitlines() if "80 percent line coverage" in ln)
        self.assertNotIn("scripts still run", exit3)
        self.assertIn("Gates 0, 4.5 and 5", exit3)

    def test_ac23_full_pipeline_behavior_is_unchanged(self) -> None:
        """AC-2.3: agent plus script, ABORT, anchor re-run, and every verdict
        branch survive the move."""
        gate0 = _section(self.text, "#### Gate 0:", "#### Gate 4.5:")
        self.assertLess(gate0.index("agents/architecture-check-agent.md"),
                        gate0.index("python3 scripts/arch-check.py check"))
        for phrase in ("**ABORT** → present findings", "never on ABORT",
                       "**Anchor confirmation (ADR-024):**", "`rederived: caution`",
                       "script `fail`", "`rederived: proceed`", "any `unverifiable` verdict"):
            self.assertIn(phrase, gate0, phrase)
        gate5 = _section(self.text, "#### Gate 5:", "### Step 4:")
        self.assertLess(gate5.index("agents/documentation-agent.md"),
                        gate5.index("python3 scripts/docs-check.py check"))
        self.assertIn("restarting **Gate 5**", gate5)
        gate45 = _section(self.text, "#### Gate 4.5:", "#### Gate 5:")
        self.assertLess(gate45.index("python3 scripts/app-verify.py run"),
                        gate45.index("agents/visual-qa-agent.md"))



class BehavioralVerificationContractTests(unittest.TestCase):
    """2026-10-01-behavioral-verification Story 4."""

    def test_coding_agent_writes_checks_it_never_grades(self) -> None:
        """AC-4.4: one rule; the check's exit code is the verdict."""
        text = (REPO_ROOT / "agents" / "coding-agent.md").read_text(encoding="utf-8")
        rules = [ln for ln in text.splitlines() if ".writ/docs/app-verification.md" in ln]
        self.assertEqual(len(rules), 1, rules)
        rule = rules[0]
        for phrase in ("Feature Map row", "(ID, feature, paths, check)",
                       "test harness", "exit code is the verdict", "never grade"):
            self.assertIn(phrase, rule)

if __name__ == "__main__":
    unittest.main()
