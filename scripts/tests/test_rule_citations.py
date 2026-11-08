#!/usr/bin/env python3
"""Story 4 of `2026-11-06-lean-story-tasks`: a business rule is stated once.

In a spec that `/create-spec` generates, the contract numbers its Business
Rules. Every later document cites a rule as `Business Rule N` and does not
restate it. These tests pin that wording:

- the contract template in `commands/create-spec.md` Step 1.4 numbers its
  rules, so `Business Rule N` resolves (AC-4.1);
- Step 2.4's business-rules bullet adds detail per rule number and does not
  restate the rule (AC-4.1);
- Step 2.8, the generator's Context for Agents business-rule hint, and
  `.writ/docs/context-hint-format.md` cite `Business Rule N` and carry no
  rule summaries (AC-4.2);
- the generator's task rules let a task cite a rule number and forbid
  paraphrasing the rule (AC-4.3);
- `commands/create-spec.md` stays net-zero in bytes, or a dated ledger line
  covers its growth (AC-4.4).

ac-trace credits the AC tokens below to `2026-11-06-lean-story-tasks`.
"""
from __future__ import annotations

import ast
import importlib.util
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CREATE_SPEC = "commands/create-spec.md"
CREATE_SPEC_COPIES = ("cursor/plugin/commands/create-spec.md",
                      "plugins/writ/commands/create-spec.md")
STORY_GENERATOR = "agents/user-story-generator.md"
STORY_GENERATOR_COPIES = ("claude-code/agents/writ-story-gen.md",
                          "cursor/plugin/agents/user-story-generator.md")
HINT_FORMAT = ".writ/docs/context-hint-format.md"
GOVERNOR_TEST = "scripts/tests/test_governor_enforcement.py"

# scripts/eval-leanness.py COMMAND_BYTE_BUDGET; the ledger records bytes over it.
COMMAND_BYTE_BUDGET = 24960
# create-spec.md when Story 4 started. Story 4 left it net-zero. Any later size
# change needs a dated ledger line that starts from this overage; its end value
# is free, since the governor test asserts the live total exactly.
CREATE_SPEC_SIZE_AT_STORY_4_START = 39081
DATED_LEDGER_LINE_FROM = r"(?m)^\s*# \d{4}-\d{2}-\d{2}\b.*: %d -> \d+\b"

CITATION = "`Business Rule N`"
HINT_LINE = re.compile(r"^- \*\*Business rules:\*\* \[(.*?)\]", re.MULTILINE)
NUMBER_REF = re.compile(r"^Business Rule (\d+|N|M)$")

_story_context_spec = importlib.util.spec_from_file_location(
    "story_context", REPO_ROOT / "scripts" / "story-context.py")
story_context = importlib.util.module_from_spec(_story_context_spec)
_story_context_spec.loader.exec_module(story_context)  # type: ignore[union-attr]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    """From `start` up to, not including, the next `end` after it."""
    i = text.index(start)
    return text[i:text.index(end, i)]


def one_line(text: str, prefix: str) -> str:
    lines = [line for line in text.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise RuntimeError("expected one line starting %r, found %d" % (prefix, len(lines)))
    return lines[0]


def contract_rules(text: str) -> list:
    """The rule lines under the Step 1.4 template's Business Rules label."""
    step = section(text, "#### Step 1.4: Contract Proposal", "#### Step 1.4b")
    block = section(step, "**📋 Business Rules:**\n", "\n\n")
    return block.splitlines()[1:]


def step_2_4_rules_bullet(text: str) -> str:
    step = section(text, "#### Step 2.4:", "#### Step 2.4b:")
    return one_line(step, "- **Business rules** —")


def step_2_8(text: str) -> str:
    return section(text, "#### Step 2.8:", "#### Step 2.9:")


def generator_hint_line(text: str) -> str:
    return one_line(section(text, "## Context for Agents", "**Selection criteria:**"),
                    "- **Business rules:**")


def task_rules(text: str) -> str:
    return section(text, "Rules for tasks:\n", "\n## Notes")


def task_quality_guideline(text: str) -> str:
    return section(text, "### Implementation Tasks\n", "\n### Notes Section")


def known_over_budget() -> dict:
    tree = ast.parse(read(GOVERNOR_TEST))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "KNOWN_OVER_BUDGET"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("%s defines no KNOWN_OVER_BUDGET" % GOVERNOR_TEST)


class ContractRulesAreNumberedTest(unittest.TestCase):
    """AC-4.1: the generated contract numbers its rules and Step 2.4 expands
    each by number without restating it."""

    def test_ac_4_1_contract_template_numbers_business_rules(self):
        """AC-4.1: `Business Rule N` resolves only if the contract numbers its rules."""
        for rel in (CREATE_SPEC,) + CREATE_SPEC_COPIES:
            with self.subTest(file=rel):
                rules = contract_rules(read(rel))
                self.assertGreaterEqual(len(rules), 2, rules)
                for n, line in enumerate(rules, start=1):
                    self.assertTrue(line.startswith("%d. [" % n), line)

    def test_ac_4_1_step_2_4_adds_detail_per_rule_number(self):
        """AC-4.1"""
        for rel in (CREATE_SPEC,) + CREATE_SPEC_COPIES:
            with self.subTest(file=rel):
                bullet = step_2_4_rules_bullet(read(rel))
                self.assertIn("per contract rule", bullet)
                self.assertIn(CITATION, bullet)
                self.assertIn("never restate the rule", bullet)


class RulesAreCitedByNumberTest(unittest.TestCase):
    """AC-4.2: Step 2.8, the generator's hint, and the hint format doc cite
    `Business Rule N` and restate no rule."""

    def test_ac_4_2_step_2_8_cites_rule_numbers(self):
        """AC-4.2"""
        for rel in (CREATE_SPEC,) + CREATE_SPEC_COPIES:
            with self.subTest(file=rel):
                step = step_2_8(read(rel))
                self.assertIn(CITATION, step)
                self.assertIn("never restate", step)

    def test_ac_4_2_generator_hint_cites_rule_numbers(self):
        """AC-4.2"""
        for rel in (STORY_GENERATOR,) + STORY_GENERATOR_COPIES:
            with self.subTest(file=rel):
                line = generator_hint_line(read(rel))
                self.assertIn("[Business Rule 1, Business Rule 3]", line)
                self.assertNotIn("summary", line)
                self.assertNotIn("(", line)

    def test_ac_4_2_hint_format_doc_cites_rule_numbers(self):
        """AC-4.2: every bracketed business-rule hint in the doc is a list of
        rule numbers, so no example restates a rule."""
        text = read(HINT_FORMAT)
        hints = HINT_LINE.findall(text)
        self.assertGreaterEqual(len(hints), 4, hints)
        for inner in hints:
            for item in inner.split(","):
                with self.subTest(item=item):
                    self.assertRegex(item.strip(), NUMBER_REF)
        rules = section(text, "#### 3. Business Rules", "#### 4. Experience Elements")
        self.assertIn(CITATION, rules)
        self.assertNotIn("summar", rules.lower())

    def test_ac_4_2_hint_format_doc_drops_rule_summaries(self):
        """AC-4.2: the quality and validation rules no longer ask for rule summaries."""
        text = read(HINT_FORMAT)
        self.assertNotIn("rule summaries", text.lower())
        self.assertNotIn("Business rules are concise summaries", text)

    def test_ac_4_2_hint_format_doc_has_no_definition_of_done(self):
        """AC-4.2: the section sits at the end of the story file; new stories
        have no Definition of Done to sit after."""
        text = read(HINT_FORMAT)
        self.assertNotIn("Definition of Done", text)
        self.assertIn("`## Context for Agents` section at the end of the story file", text)

    def test_ac_4_2_story_context_parses_number_citations(self):
        """AC-4.2: `scripts/story-context.py` splits a number-citation hint
        into one ref per rule; a summary with a comma no longer splits a rule."""
        line = generator_hint_line(read(STORY_GENERATOR))
        rest = line.split(":**", 1)[1]
        kind, refs = story_context.parse_category_value(rest)
        self.assertEqual(kind, "bracket")
        self.assertEqual(refs, ["Business Rule 1", "Business Rule 3"])


class TasksCiteButDoNotParaphraseTest(unittest.TestCase):
    """AC-4.3: a task may cite a rule number and may not paraphrase the rule."""

    def test_ac_4_3_task_rules_allow_citing_and_forbid_paraphrase(self):
        """AC-4.3"""
        for rel in (STORY_GENERATOR,) + STORY_GENERATOR_COPIES:
            with self.subTest(file=rel):
                rules = task_rules(read(rel))
                self.assertIn("A task may cite a business rule by number (%s)" % CITATION, rules)
                self.assertIn("never paraphrases it", rules)

    def test_ac_4_3_quality_guideline_says_the_same(self):
        """AC-4.3"""
        guideline = task_quality_guideline(read(STORY_GENERATOR))
        self.assertIn("May cite a business rule by number; never paraphrase it", guideline)


class CreateSpecByteLedgerTest(unittest.TestCase):
    """AC-4.4: create-spec.md is net-zero, or a dated ledger line from its
    Story 4 start value covers the change."""

    def test_ac_4_4_create_spec_is_net_zero_or_in_the_ledger(self):
        """AC-4.4"""
        size = len((REPO_ROOT / CREATE_SPEC).read_bytes())
        self.assertEqual(known_over_budget()[CREATE_SPEC], size - COMMAND_BYTE_BUDGET)
        if size != CREATE_SPEC_SIZE_AT_STORY_4_START:
            start = CREATE_SPEC_SIZE_AT_STORY_4_START - COMMAND_BYTE_BUDGET
            self.assertRegex(read(GOVERNOR_TEST), DATED_LEDGER_LINE_FROM % start)


if __name__ == "__main__":
    unittest.main()
