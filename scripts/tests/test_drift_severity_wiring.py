#!/usr/bin/env python3
"""Wiring assertions for Story 3 of `2026-09-26-drift-arch-guards`
(contract-anchored drift and architecture-class severity).

The story changes command and agent prose, not code, so these checks read the
prose directly:

- `contract_content` (the locked `## Specification Contract` section of
  spec.md) is routed to both Gate 3 agents and named in their input tables,
  their Claude Code peers, and the regenerated Codex TOMLs [AC-3.1, AC-3.2].
- The three architecture-class cases (new runtime dependency, changed
  interface at an integration point, changed architectural approach) sit under
  Large and never under Medium, in every severity rubric [AC-3.3, AC-3.4].

A "tier block" is either a table row whose first cell names the tier, or the
prose that follows a heading / bold lead naming the tier, up to the next
heading, bold lead, numbered step, or table row. A code fence opened inside a
block never ends it, so a `### Medium Deviation` example is judged as a whole;
a block that starts inside a fence (a prompt template) ends with that fence.

Run: python3 scripts/tests/test_drift_severity_wiring.py
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]

IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"
EVALUATOR = REPO_ROOT / "agents" / "evaluator-agent.md"
REVIEWER = REPO_ROOT / "agents" / "review-agent.md"
CLAUDE_EVALUATOR = REPO_ROOT / "claude-code" / "agents" / "writ-evaluator.md"
CLAUDE_REVIEWER = REPO_ROOT / "claude-code" / "agents" / "writ-reviewer.md"
FORMAT_DOC = REPO_ROOT / ".writ" / "docs" / "drift-report-format.md"
TRIAGE_SKILL = REPO_ROOT / "skills" / "drift-triage" / "SKILL.md"
CODEX_EVALUATOR = REPO_ROOT / "codex" / "agents" / "evaluator-agent.toml"
CODEX_REVIEWER = REPO_ROOT / "codex" / "agents" / "review-agent.toml"

RUBRIC_FILES = (
    EVALUATOR,
    REVIEWER,
    CLAUDE_EVALUATOR,
    CLAUDE_REVIEWER,
    FORMAT_DOC,
    TRIAGE_SKILL,
)

# What each architecture-class case must say under Large, and the broader stem
# that must not appear anywhere under Medium.
LARGE_ANCHORS = {
    "dependency": re.compile(r"(?i)runtime\s+dependenc"),
    "integration": re.compile(r"(?i)integration\s+point"),
    "approach": re.compile(r"(?i)architectural\s+approach"),
}
MEDIUM_FORBIDDEN = {
    "dependency": re.compile(r"(?i)dependenc"),
    "integration": re.compile(r"(?i)integration"),
    "approach": re.compile(r"(?i)architectur"),
}

CONTRACT_SECTION = "Locked Contract (drift reference)"
FENCE = re.compile(r"^\s*```")
TIER_ROW = re.compile(r"^\|\s*[*`]*(Small|Medium|Large)[*`]*\s*\|")
TIER_LEAD = re.compile(r"^(?:#{2,6}\s+|\*\*)(Small|Medium|Large)\b")
BLOCK_END = re.compile(r"^(?:#{1,6}\s|\*\*|\d+\.\s|\|)")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def tier_blocks(text: str) -> Dict[str, List[str]]:
    blocks: Dict[str, List[str]] = {"Small": [], "Medium": [], "Large": []}
    current = None
    buf: List[str] = []
    in_fence = False
    started_in_fence = False

    def flush() -> None:
        if current is not None:
            blocks[current].append("\n".join(buf))

    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            if current is not None and started_in_fence and not in_fence:
                flush()
                current, buf = None, []
            elif current is not None:
                buf.append(line)
            continue
        if current is not None and in_fence and not started_in_fence:
            buf.append(line)
            continue
        row = TIER_ROW.match(line)
        if row:
            flush()
            current, buf = None, []
            blocks[row.group(1)].append(line)
            continue
        lead = TIER_LEAD.match(line)
        if lead:
            flush()
            current, buf = lead.group(1), [line]
            started_in_fence = in_fence
            continue
        if current is not None and BLOCK_END.match(line):
            flush()
            current, buf = None, []
            continue
        if current is not None:
            buf.append(line)
    flush()
    return blocks


def section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    stop = text.index(end, begin + len(start))
    return text[begin:stop]


class GateThreeRoutesContract(unittest.TestCase):
    """AC-3.1: both Gate 3 routing rows carry `contract_content`."""

    def test_routing_rows_carry_contract_content(self) -> None:
        text = read(IMPLEMENT_STORY)
        for label in ("| Evaluator Agent (Gate 3, default) |", "| Review Agent (Gate 3) |"):
            with self.subTest(row=label):
                rows = [ln for ln in text.splitlines() if ln.startswith(label)]
                self.assertEqual(len(rows), 1, f"expected one routing row {label}")
                self.assertIn("`contract_content`", rows[0])
                self.assertIn("`spec_lite_for_review`", rows[0])


class AgentsNameContractAsDriftReference(unittest.TestCase):
    """AC-3.2: each agent surface names `contract_content` and says it
    outranks spec-lite."""

    def test_input_tables_have_contract_row(self) -> None:
        for path in (EVALUATOR, REVIEWER):
            with self.subTest(agent=path.name):
                table = section(read(path), "## Input Requirements", "## Prompt Template")
                rows = [ln for ln in table.splitlines() if ln.startswith("| `contract_content` |")]
                self.assertEqual(len(rows), 1)
                self.assertIn("## Specification Contract", rows[0])
                self.assertIn("empty string", rows[0].lower())

    def test_prompt_templates_have_locked_contract_section(self) -> None:
        for path in (EVALUATOR, REVIEWER):
            with self.subTest(agent=path.name):
                prompt = section(read(path), "## Prompt Template", "## Severity Definitions")
                self.assertIn(f"## {CONTRACT_SECTION}", prompt)
                self.assertIn("{contract_content}", prompt)
                self.assertIn("{spec_lite_content}", prompt)

    def test_every_surface_says_contract_outranks_spec_lite(self) -> None:
        for path in (EVALUATOR, REVIEWER, CLAUDE_EVALUATOR, CLAUDE_REVIEWER,
                     CODEX_EVALUATOR, CODEX_REVIEWER):
            with self.subTest(surface=path.name):
                text = read(path)
                self.assertIn("contract_content", text)
                self.assertIn(CONTRACT_SECTION, text)
                self.assertRegex(text, r"outranks `?spec-lite(\.md)?`?")

    def test_codex_bodies_match_agent_sources(self) -> None:
        gen_path = REPO_ROOT / "scripts" / "gen-codex-agent-tomls.py"
        spec = importlib.util.spec_from_file_location("gen_codex_agent_tomls", gen_path)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)  # type: ignore[union-attr]
        for md, toml in ((EVALUATOR, CODEX_EVALUATOR), (REVIEWER, CODEX_REVIEWER)):
            with self.subTest(toml=toml.name):
                body = gen.strip_optional_yaml_frontmatter(read(md))
                want = gen.toml_long_string(gen.strip_retired_fast_lines(body))
                self.assertIn("developer_instructions = " + want, read(toml))


class ArchitectureClassIsLarge(unittest.TestCase):
    """AC-3.3, AC-3.4: the three cases are Large in every rubric and absent
    from every Medium block."""

    def test_cases_sit_under_large(self) -> None:
        for path in RUBRIC_FILES:
            large = "\n".join(tier_blocks(read(path))["Large"])
            for case, pattern in LARGE_ANCHORS.items():
                with self.subTest(file=path.name, case=case):
                    self.assertRegex(large, pattern)

    def test_cases_absent_from_medium(self) -> None:
        for path in RUBRIC_FILES:
            blocks = tier_blocks(read(path))["Medium"]
            self.assertTrue(blocks or path in (CLAUDE_EVALUATOR, CLAUDE_REVIEWER),
                            f"{path.name}: no Medium block found")
            medium = "\n".join(blocks)
            for case, pattern in MEDIUM_FORBIDDEN.items():
                with self.subTest(file=path.name, case=case):
                    self.assertNotRegex(medium, pattern)

    def test_ambiguity_default_stays_medium(self) -> None:
        for path in (EVALUATOR, REVIEWER):
            with self.subTest(agent=path.name):
                self.assertIn("When severity is ambiguous → default to Medium", read(path))

    def test_review_agent_drops_at_least_medium_rule(self) -> None:
        self.assertNotIn("that's at least Medium", read(REVIEWER))


class FormatDocMediumExample(unittest.TestCase):
    """AC-3.4: the Medium example is a scope-expansion case, still DEV-003 with
    all six fields."""

    def test_medium_example_is_scope_expansion(self) -> None:
        example = section(read(FORMAT_DOC), "### Medium Deviation", "### Large Deviation")
        self.assertIn("#### [DEV-003]", example)
        self.assertIn("- **Severity:** Medium", example)
        self.assertIn("Scope expansion", example)
        self.assertNotRegex(example, r"(?i)dependenc|zod")
        for field in ("Severity", "Spec said", "Implementation did", "Reason",
                      "Resolution", "Spec amendment"):
            self.assertIn(f"- **{field}:**", example)


if __name__ == "__main__":
    unittest.main()
