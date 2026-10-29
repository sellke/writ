#!/usr/bin/env python3
"""Wiring assertions for Story 2 of `2026-10-25-review-route-rigor`.
[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]

The story ships markdown, so these checks read the files directly:

- `skills/review-judgment-filters/SKILL.md`: frontmatter, lint, the three
  filters with filter 3 applied before filter 2, and its registration
  (manifest, README, root catalog, generated copies) [AC-2.1].
- `agents/review-agent.md` and `agents/evaluator-agent.md` take a
  `reviewer_filters` input and carry one conditional `Read` line before the
  verdict; the generated Claude Code agents carry the same line [AC-2.2].
- Gate 3 of `commands/implement-story.md` resolves the `reviewer-filters`
  switch, passes `reviewer_filters` to every spawn, and prints the report line;
  the off arm reads no skill because every `Read` of it is conditional [AC-2.3].
- `commands/review.md` Step 3 resolves the switch and reads the skill before
  severities; the Step 4 header records `> Reviewer filters:` [AC-2.4].
- The distinctive filter sentences live only in the skill: none of
  `agents/`, `commands/`, `claude-code/agents/`, or the plugin and codex
  agent/command trees carry them [AC-2.5]. `gen-platform-trees.py --check` is
  part of the verification run, not an assertion here.

Run: uv run --python 3.9 pytest scripts/tests/test_review_route_rigor.py -q
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

SKILL_NAME = "review-judgment-filters"
SKILL_REL = "skills/review-judgment-filters/SKILL.md"
SKILL = REPO_ROOT / "skills" / SKILL_NAME / "SKILL.md"
LINT = REPO_ROOT / "scripts" / "lint-skill.sh"
MANIFEST = REPO_ROOT / ".writ" / "manifest.yaml"
README = REPO_ROOT / "README.md"
ROOT_CATALOG = REPO_ROOT / "SKILL.md"

REVIEW_AGENT = REPO_ROOT / "agents" / "review-agent.md"
EVALUATOR_AGENT = REPO_ROOT / "agents" / "evaluator-agent.md"
NATIVE_REVIEWER = REPO_ROOT / "claude-code" / "agents" / "writ-reviewer.md"
NATIVE_EVALUATOR = REPO_ROOT / "claude-code" / "agents" / "writ-evaluator.md"
REVIEW_COMMAND = REPO_ROOT / "commands" / "review.md"
IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"

DESCRIPTION = (
    "Separate findings that change a verdict from nits and untraced "
    "hypotheticals, without dismissing security findings."
)
STATUS_EVIDENCE = (
    "Phase 15 (2026-10-25). 3 consumers: agents/review-agent.md, "
    "agents/evaluator-agent.md, commands/review.md."
)

SWITCH_COMMAND = "python3 scripts/review-override.py switch --name reviewer-filters"
REVIEW_LINE = (
    "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` "
    "and apply it before you set REVIEW_RESULT."
)
EVALUATOR_LINE = (
    "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` "
    "and apply it before you set EVALUATION_RESULT."
)

FILTER_HEADINGS = (
    "### Filter 1: All nits means the code is fine",
    "### Filter 2: Trace the call site before accepting a hypothetical",
    "### Filter 3: Be slow to dismiss security findings",
)

# Sentences only the skill may carry. Compared lowercased with whitespace
# collapsed, so markdown line wrapping cannot hide or fake a match.
FILTER_SENTENCES = (
    "all nits means the code is fine",
    "trace the call site before accepting a hypothetical",
    "be slow to dismiss security findings",
    "a security finding is dismissed only by citing the guard",
    "do not raise a nit's severity to justify a fail",
    "input that crosses a trust boundary",
    "filter 3 is applied before filter 2",
)

# Agent and command trees: the canonical sources and every generated copy.
SCANNED_GLOBS = (
    ("agents", "*.md"),
    ("commands", "*.md"),
    ("claude-code/agents", "*.md"),
    ("plugins/writ/agents", "*.md"),
    ("plugins/writ/commands", "*.md"),
    ("cursor/plugin/agents", "*.md"),
    ("cursor/plugin/commands", "*.md"),
    ("codex/agents", "*.toml"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def skill_text() -> str:
    if not SKILL.is_file():
        raise AssertionError("%s does not exist" % SKILL_REL)
    return read(SKILL)


def split_frontmatter(text: str) -> Tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return "", text


def frontmatter_value(frontmatter: str, key: str) -> Optional[str]:
    match = re.search(r"(?m)^%s:[ \t]*(.*)$" % re.escape(key), frontmatter)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def slice_between(text: str, start: str, end: str) -> str:
    """Text from the line starting with `start` up to the line starting with
    `end`. Empty when `start` is absent; to the end of text when `end` is."""
    lines = text.splitlines()
    begin = next((i for i, l in enumerate(lines) if l.startswith(start)), None)
    if begin is None:
        return ""
    stop = next(
        (i for i in range(begin + 1, len(lines)) if lines[i].startswith(end)),
        len(lines),
    )
    return "\n".join(lines[begin:stop])


def table_rows(block: str) -> List[str]:
    rows: List[str] = []
    in_table = False
    for line in block.splitlines():
        if line.startswith("|"):
            in_table = True
            rows.append(line)
        elif in_table:
            break
    return [r for r in rows[2:] if not re.match(r"^\|[\s:|-]+\|$", r)]


def manifest_skill_entries() -> List[dict]:
    entries: List[dict] = []
    in_skills = False
    for line in read(MANIFEST).splitlines():
        if re.match(r"^skills:", line):
            in_skills = True
            continue
        if in_skills and re.match(r"^\S", line):
            break
        if not in_skills:
            continue
        m = re.match(r"^  - name:\s*(\S+)", line)
        if m:
            entries.append({"name": m.group(1)})
            continue
        m = re.match(r"^    (\w+):\s*(.*)$", line)
        if m and entries:
            entries[-1][m.group(1)] = m.group(2).strip().strip('"')
    return entries


def scanned_files() -> List[Path]:
    files: List[Path] = []
    for folder, pattern in SCANNED_GLOBS:
        base = REPO_ROOT / folder
        if base.is_dir():
            files.extend(sorted(base.glob(pattern)))
    return files


# ---------------------------------------------------------------------------
# AC-2.1: the skill and its registration
# ---------------------------------------------------------------------------


class SkillFrontmatterTest(unittest.TestCase):
    """[AC-2.1]"""

    def setUp(self) -> None:
        self.frontmatter, _ = split_frontmatter(skill_text())

    def test_name(self) -> None:
        self.assertEqual(frontmatter_value(self.frontmatter, "name"), SKILL_NAME)

    def test_description(self) -> None:
        self.assertEqual(frontmatter_value(self.frontmatter, "description"), DESCRIPTION)

    def test_model_invocation_disabled(self) -> None:
        self.assertEqual(
            frontmatter_value(self.frontmatter, "disable-model-invocation"), "true"
        )

    def test_status_candidate_with_three_consumers(self) -> None:
        self.assertEqual(frontmatter_value(self.frontmatter, "status"), "candidate")
        self.assertEqual(
            frontmatter_value(self.frontmatter, "status_evidence"), STATUS_EVIDENCE
        )


class SkillLintTest(unittest.TestCase):
    """`bash scripts/lint-skill.sh` passes the skill. [AC-2.1]"""

    def test_lint_line_one_is_pass_and_exit_zero(self) -> None:
        skill_text()
        result = subprocess.run(
            ["bash", str(LINT), SKILL_REL],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertEqual(first, "pass", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class SkillBodyTest(unittest.TestCase):
    """Purpose, When to Use, How to Apply; the three filters in order, filter 3
    applied before filter 2, one example each, the `/review` mapping. [AC-2.1]"""

    def setUp(self) -> None:
        _, self.body = split_frontmatter(skill_text())
        self.how = slice_between(self.body, "## How to Apply", "## ")

    def test_sections_in_order(self) -> None:
        headings = [l for l in self.body.splitlines() if l.startswith("## ")]
        required = ["## Purpose", "## When to Use", "## How to Apply"]
        for heading in required:
            self.assertIn(heading, headings)
        self.assertEqual(
            [headings.index(h) for h in required],
            sorted(headings.index(h) for h in required),
        )

    def test_when_to_use_names_verdict_and_ship_recommendation(self) -> None:
        when = normalized(slice_between(self.body, "## When to Use", "## How to Apply"))
        self.assertIn("verdict", when)
        self.assertIn("ship recommendation", when)

    def test_three_filters_in_order_under_how_to_apply(self) -> None:
        lines = self.how.splitlines()
        positions = []
        for heading in FILTER_HEADINGS:
            self.assertIn(heading, lines, "missing filter heading: %s" % heading)
            positions.append(lines.index(heading))
        self.assertEqual(positions, sorted(positions))

    def test_filter_3_applied_before_filter_2(self) -> None:
        how = normalized(self.how)
        self.assertIn("filter 3 is applied before filter 2", how)
        self.assertIn("filter 2 does not apply to security", how)

    def test_each_filter_carries_one_example(self) -> None:
        for i, heading in enumerate(FILTER_HEADINGS):
            end = FILTER_HEADINGS[i + 1] if i + 1 < len(FILTER_HEADINGS) else "### "
            block = slice_between(self.how, heading, end)
            examples = [l for l in block.splitlines() if l.startswith("Example:")]
            self.assertEqual(len(examples), 1, "%s: %r" % (heading, examples))

    def test_filter_rules_carry_the_spec_terms(self) -> None:
        how = normalized(self.how)
        for phrase in (
            "the verdict is pass",
            "recommendations",
            "do not raise a nit's severity to justify a fail",
            "`path:line`",
            "input that crosses a trust boundary",
            "a security finding is dismissed only by citing the guard",
            "major or above",
        ):
            self.assertIn(phrase, how)

    def test_review_severity_mapping(self) -> None:
        how = normalized(self.how)
        self.assertIn("a nit is low", how)
        self.assertIn("high or above", how)


class SkillRegistrationTest(unittest.TestCase):
    """Manifest entry, README row and count, root catalog row, generated copies.
    [AC-2.1]"""

    def test_manifest_entry(self) -> None:
        entries = {e["name"]: e for e in manifest_skill_entries()}
        self.assertIn(SKILL_NAME, entries)
        entry = entries[SKILL_NAME]
        self.assertEqual(entry.get("file"), SKILL_REL)
        self.assertEqual(entry.get("description"), DESCRIPTION)
        self.assertEqual(entry.get("status"), "candidate")
        self.assertTrue(entry.get("tags", "").startswith("["), entry)

    def test_readme_row_and_live_count(self) -> None:
        text = read(README)
        rows = table_rows(slice_between(text, "## Skills", "## Platform"))
        self.assertTrue(
            any("[`%s`](%s)" % (SKILL_NAME, SKILL_REL) in r for r in rows), rows
        )
        count = re.search(r"(\d+) skills are live today", text)
        self.assertIsNotNone(count)
        self.assertEqual(int(count.group(1)), len(rows))

    def test_root_catalog_row(self) -> None:
        self.assertIn(
            "| `%s` | `candidate` | `%s` |" % (SKILL_NAME, SKILL_REL), read(ROOT_CATALOG)
        )

    def test_generated_skill_copies_exist(self) -> None:
        for base in ("plugins/writ/skills", "cursor/plugin/skills"):
            if (REPO_ROOT / base).is_dir():
                copy = REPO_ROOT / base / SKILL_NAME / "SKILL.md"
                self.assertTrue(copy.is_file(), "%s missing" % copy.relative_to(REPO_ROOT))


# ---------------------------------------------------------------------------
# AC-2.2 / AC-2.3: the agents
# ---------------------------------------------------------------------------


class AgentWiringTest(unittest.TestCase):
    """Each agent takes `reviewer_filters` and reads the skill only when it is
    `on`, inside its prompt, before its output format. [AC-2.2, AC-2.3]"""

    CASES = (
        (REVIEW_AGENT, REVIEW_LINE),
        (EVALUATOR_AGENT, EVALUATOR_LINE),
    )

    def test_input_row(self) -> None:
        for path, _ in self.CASES:
            inputs = slice_between(read(path), "## Input Requirements", "## ")
            rows = [r for r in table_rows(inputs) if r.startswith("| `reviewer_filters` |")]
            self.assertEqual(len(rows), 1, path.name)
            self.assertIn("`on`", rows[0])
            self.assertIn("`off`", rows[0])
            self.assertIn("Gate 3", rows[0])

    def test_conditional_line_inside_prompt_before_output_format(self) -> None:
        for path, line in self.CASES:
            lines = read(path).splitlines()
            self.assertIn(line, lines, path.name)
            at = lines.index(line)
            prompt = lines.index("## Prompt Template")
            output = next(
                i for i in range(prompt, len(lines)) if lines[i].startswith("## Output Format")
            )
            self.assertLess(prompt, at, path.name)
            self.assertLess(at, output, path.name)

    def test_every_read_of_the_skill_is_conditional(self) -> None:
        """The off arm reads nothing: no unconditional `Read` of the skill."""
        for path, line in self.CASES:
            reads = [l for l in read(path).splitlines() if SKILL_REL in l]
            self.assertEqual(reads, [line], path.name)

    def test_generated_native_agents_carry_the_line(self) -> None:
        for path, line in ((NATIVE_REVIEWER, REVIEW_LINE), (NATIVE_EVALUATOR, EVALUATOR_LINE)):
            text = read(path)
            self.assertIn(line, text.splitlines(), path.name)
            self.assertIn("| `reviewer_filters` |", text, path.name)


# ---------------------------------------------------------------------------
# AC-2.2 / AC-2.3: Gate 3 of /implement-story
# ---------------------------------------------------------------------------


class Gate3WiringTest(unittest.TestCase):
    """Gate 3 resolves the switch once, passes `reviewer_filters` to every
    spawn (panel reviewers and re-reviews included), and prints the report
    line. Gate 0 and Step 4 stay untouched. [AC-2.2, AC-2.3]"""

    def setUp(self) -> None:
        self.text = read(IMPLEMENT_STORY)
        self.gate3 = slice_between(self.text, "#### Gate 3: Review Agent", "#### Gate 3.5:")
        self.assertTrue(self.gate3, "Gate 3 section not found")

    def _switch_paragraph(self) -> str:
        paragraphs = [p for p in self.gate3.split("\n\n") if SWITCH_COMMAND in p]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        return paragraphs[0]

    def test_gate3_resolves_switch_and_passes_input(self) -> None:
        paragraph = self._switch_paragraph()
        self.assertIn("`reviewer_filters`", paragraph)
        self.assertIn("every Gate 3 spawn", paragraph)
        self.assertIn("panel reviewers", paragraph)
        self.assertIn("re-review", paragraph)

    def test_gate3_prints_report_line(self) -> None:
        self.assertIn("`reviewer-filters: <on|off>`", self._switch_paragraph())

    def test_switch_only_in_gate3(self) -> None:
        self.assertEqual(self.text.count(SWITCH_COMMAND), 1)
        gate0 = slice_between(self.text, "#### Gate 0: Architecture Check", "#### Gate 0.5:")
        step4 = slice_between(self.text, "### Step 4: Story Completion", "## Error Handling")
        self.assertTrue(gate0 and step4)
        for name, block in (("Gate 0", gate0), ("Step 4", step4)):
            self.assertNotIn("reviewer-filters", block, name)
            self.assertNotIn("reviewer_filters", block, name)

    def test_gate3_carries_no_filter_text(self) -> None:
        self.assertNotIn(SKILL_REL, self.gate3)


# ---------------------------------------------------------------------------
# AC-2.4: /review
# ---------------------------------------------------------------------------


class ReviewCommandWiringTest(unittest.TestCase):
    """Step 3 resolves the switch and reads the skill before Technique 1;
    Step 4's report header records the switch. [AC-2.4]"""

    def setUp(self) -> None:
        self.text = read(REVIEW_COMMAND)
        self.step3 = slice_between(self.text, "### Step 3:", "### Step 4:")
        self.step4 = slice_between(self.text, "### Step 4:", "### Step 5:")

    def test_step3_opens_with_switch_and_conditional_read(self) -> None:
        opening = self.step3.split("#### Technique 1")[0]
        self.assertIn(SWITCH_COMMAND, opening)
        self.assertIn("`Read %s`" % SKILL_REL, opening)
        self.assertRegex(normalized(opening), r"on `on`")
        self.assertIn("Technique 4", opening)
        self.assertIn("Recommendation", opening)

    def test_step4_header_records_reviewer_filters(self) -> None:
        lines = self.step4.splitlines()
        self.assertIn("> Reviewer filters: on|off", lines)
        at = lines.index("> Reviewer filters: on|off")
        reviewed = next(i for i, l in enumerate(lines) if l.startswith("> Reviewed:"))
        self.assertLess(abs(at - reviewed), 5)

    def test_review_reads_the_skill_only_when_on(self) -> None:
        reads = [l for l in self.text.splitlines() if SKILL_REL in l]
        self.assertEqual(len(reads), 1, reads)
        self.assertIn("`on`", reads[0])


# ---------------------------------------------------------------------------
# AC-2.5: filter text lives only in the skill
# ---------------------------------------------------------------------------


class FilterTextIsolationTest(unittest.TestCase):
    """The off arm carries none of the filter text. [AC-2.5]"""

    def test_sentences_are_in_the_skill(self) -> None:
        text = normalized(skill_text())
        for sentence in FILTER_SENTENCES:
            self.assertIn(sentence, text)

    def test_sentences_absent_from_agents_commands_and_generated_trees(self) -> None:
        files = scanned_files()
        self.assertGreater(len(files), 0)
        hits = []
        for path in files:
            text = normalized(read(path))
            for sentence in FILTER_SENTENCES:
                if sentence in text:
                    hits.append("%s: %s" % (path.relative_to(REPO_ROOT), sentence))
        self.assertEqual(hits, [], "\n".join(hits))


# ---------------------------------------------------------------------------
# Story 4 of `2026-10-25-review-route-rigor`: the safety fact at Gate 3.
# [AC-4.4, AC-4.5]
#
# - `skills/blast-radius/SKILL.md`: frontmatter, lint, the ladder table, the
#   section format, and its registration (manifest, README, root catalog,
#   generated copies).
# - The ladder's rung definitions live only in the skill: none of the agent
#   or command trees carry them, so the switch-off arm carries no ladder text.
# - `agents/review-agent.md` takes `recorded_test_results`, `safety_fact`, and
#   `blast_radius`, reads the skill only when `safety_fact` is `on`, and has a
#   one-line output slot; the generated reviewer carries the same.
# - Gate 3 of `commands/implement-story.md` saves the review output and the
#   recorded run, runs `review-override.py safety-fact`, routes each reason,
#   counts the re-review as the same attempt, and prints the report lines;
#   nothing outside Gate 3 runs the verifier.
# - `agents/evaluator-agent.md` takes no `safety_fact`: the evaluator never
#   runs on the risk route.
# ---------------------------------------------------------------------------

BLAST_NAME = "blast-radius"
BLAST_REL = "skills/blast-radius/SKILL.md"
BLAST_SKILL = REPO_ROOT / "skills" / BLAST_NAME / "SKILL.md"
BLAST_DESCRIPTION = (
    "Name the one fact a change is safe because of and push its evidence up a "
    "five-rung ladder."
)
BLAST_STATUS_EVIDENCE = (
    "Phase 15 (2026-10-25). 1 consumer: agents/review-agent.md; kept as a skill "
    "so the safety-fact switch can remove it cleanly."
)
SAFETY_LINE = (
    "When `{safety_fact}` is `on`, `Read skills/blast-radius/SKILL.md` and write its "
    "`### Safety Fact` section, starting from `{blast_radius}`."
)
SAFETY_SLOT = "### Safety Fact (only when safety_fact is on; format in the skill)"
IMPLEMENT_STORY_CAP = 40234
RUNG_ORDER = ("claimed", "read", "traced", "tested", "reproduced")

# Rung definitions only the skill may carry, compared normalized.
LADDER_SENTENCES = (
    "someone said so: the coding agent's report, a commit message, a comment, the spec",
    "the reviewer read the code that makes the fact true",
    "the reviewer followed the changed code to its callers",
    "a test exercises the fact and passed in the orchestrator's recorded run",
    "the fact was observed in the running app",
    "the ladder is not cumulative",
)


def blast_text() -> str:
    if not BLAST_SKILL.is_file():
        raise AssertionError("%s does not exist" % BLAST_REL)
    return read(BLAST_SKILL)


class BlastSkillTest(unittest.TestCase):
    """Frontmatter, lint, sections, ladder table, section format. [AC-4.5]"""

    def setUp(self) -> None:
        self.frontmatter, self.body = split_frontmatter(blast_text())
        self.how = slice_between(self.body, "## How to Apply", "## ")

    def test_frontmatter(self) -> None:
        fm = self.frontmatter
        self.assertEqual(frontmatter_value(fm, "name"), BLAST_NAME)
        self.assertEqual(frontmatter_value(fm, "description"), BLAST_DESCRIPTION)
        self.assertEqual(frontmatter_value(fm, "disable-model-invocation"), "true")
        self.assertEqual(frontmatter_value(fm, "status"), "candidate")
        self.assertEqual(frontmatter_value(fm, "status_evidence"), BLAST_STATUS_EVIDENCE)

    def test_lint_passes(self) -> None:
        result = subprocess.run(
            ["bash", str(LINT), BLAST_REL],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertEqual(first, "pass", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sections_in_order(self) -> None:
        headings = [l for l in self.body.splitlines() if l.startswith("## ")]
        required = ["## Purpose", "## When to Use", "## How to Apply"]
        for heading in required:
            self.assertIn(heading, headings)
        self.assertEqual([headings.index(h) for h in required],
                         sorted(headings.index(h) for h in required))

    def test_ladder_table_lists_five_rungs_in_order(self) -> None:
        rows = table_rows(slice_between(self.how, "### Evidence Ladder", "### "))
        rungs = [re.search(r"`(\w+)`", r.split("|")[2]).group(1) for r in rows]
        self.assertEqual(rungs, list(RUNG_ORDER))
        for row in rows:
            self.assertEqual(len([c for c in row.strip("|").split("|")]), 4, row)

    def test_section_format(self) -> None:
        # The format block itself holds a `### Safety Fact` line, so the slice
        # runs to the next named subsection rather than the next `### `.
        block = slice_between(self.how, "### Safety Fact section", "### Rules")
        for line in ("### Safety Fact", "**Fact:**", "**Holds:** yes | no",
                     "**Rung:** claimed | read | traced | tested | reproduced",
                     "**Evidence:**", "- read:", "- traced:", "- tested:"):
            self.assertIn(line, block)
        self.assertIn("### Security Assessment", block)

    def test_rules(self) -> None:
        how = normalized(self.how)
        for phrase in (
            "one fact",
            "name the weaker one",
            "a fact about the code, not about the process",
            "push the fact up the ladder",
            "**holds:** no",
            "`architecture`",
            "`security`",
            "`blast_radius`",
            "`consumers`",
            "`tests`",
            "search for callers yourself",
            "`app-verify-result-v1`",
            "recode iteration",
            "did not change since",
            "`rung:`",
            "`reason:`",
        ):
            self.assertIn(phrase, how)


class BlastSkillRegistrationTest(unittest.TestCase):
    """Manifest entry, README row, root catalog row, generated copies. [AC-4.5]"""

    def test_manifest_entry(self) -> None:
        entries = manifest_skill_entries()
        by_name = {e["name"]: e for e in entries}
        self.assertIn(BLAST_NAME, by_name)
        entry = by_name[BLAST_NAME]
        self.assertEqual(entry.get("file"), BLAST_REL)
        self.assertEqual(entry.get("description"), BLAST_DESCRIPTION)
        self.assertEqual(entry.get("status"), "candidate")
        self.assertTrue(entry.get("tags", "").startswith("["), entry)
        names = [e["name"] for e in entries]
        self.assertEqual(names.index(BLAST_NAME) + 1,
                         names.index("boundary-map-computation"))

    def test_readme_row(self) -> None:
        rows = table_rows(slice_between(read(README), "## Skills", "## Platform"))
        self.assertTrue(any("[`%s`](%s)" % (BLAST_NAME, BLAST_REL) in r for r in rows), rows)
        self.assertIn(BLAST_NAME, rows[-1])

    def test_root_catalog_row(self) -> None:
        self.assertIn("| `%s` | `candidate` | `%s` |" % (BLAST_NAME, BLAST_REL),
                      read(ROOT_CATALOG))

    def test_generated_skill_copies_exist(self) -> None:
        for base in ("plugins/writ/skills", "cursor/plugin/skills"):
            if (REPO_ROOT / base).is_dir():
                copy = REPO_ROOT / base / BLAST_NAME / "SKILL.md"
                self.assertTrue(copy.is_file(), "%s missing" % copy.relative_to(REPO_ROOT))

    def test_example_citations_stay_repo_relative_in_every_copy(self) -> None:
        """The plugin generator rewrites `scripts/` paths; the format example must
        not turn into a citation the skill's own repo-relative rule rejects."""
        for base in ("skills", "plugins/writ/skills", "cursor/plugin/skills"):
            copy = REPO_ROOT / base / BLAST_NAME / "SKILL.md"
            if not copy.is_file():
                continue
            block = slice_between(read(copy), "### Safety Fact section", "### Rules")
            cites = [l for l in block.splitlines()
                     if re.match(r"^- (read|traced|tested|reproduced): ", l)]
            self.assertTrue(cites, base)
            for line in cites:
                self.assertNotIn("${", line, "%s: %s" % (base, line))
                self.assertNotRegex(line, r"`(/|scripts/)", "%s: %s" % (base, line))


class LadderTextIsolationTest(unittest.TestCase):
    """The rung definitions live only in the skill. [AC-4.5]"""

    def test_sentences_are_in_the_skill(self) -> None:
        text = normalized(blast_text())
        for sentence in LADDER_SENTENCES:
            self.assertIn(sentence, text)

    def test_sentences_absent_from_agents_commands_and_generated_trees(self) -> None:
        files = scanned_files()
        self.assertGreater(len(files), 0)
        hits = []
        for path in files:
            text = normalized(read(path))
            for sentence in LADDER_SENTENCES:
                if sentence in text:
                    hits.append("%s: %s" % (path.relative_to(REPO_ROOT), sentence))
        self.assertEqual(hits, [], "\n".join(hits))


class ReviewAgentSafetyFactTest(unittest.TestCase):
    """Input rows, one conditional `Read` line, one output slot. [AC-4.4, AC-4.5]"""

    def setUp(self) -> None:
        self.text = read(REVIEW_AGENT)
        self.lines = self.text.splitlines()

    def _row(self, name: str) -> str:
        inputs = slice_between(self.text, "## Input Requirements", "## ")
        rows = [r for r in table_rows(inputs) if r.startswith("| `%s` |" % name)]
        self.assertEqual(len(rows), 1, name)
        return rows[0]

    def test_input_rows(self) -> None:
        self.assertIn("exit code", self._row("recorded_test_results"))
        safety = self._row("safety_fact")
        self.assertIn("`on`", safety)
        self.assertIn("`off`", safety)
        self.assertIn("`(none)`", self._row("blast_radius"))

    def test_recorded_test_results_reach_the_prompt(self) -> None:
        prompt = slice_between(self.text, "## Prompt Template", "## Severity Definitions")
        self.assertIn("{recorded_test_results}", prompt)

    def test_conditional_line_follows_filters_line(self) -> None:
        self.assertIn(SAFETY_LINE, self.lines)
        at = self.lines.index(SAFETY_LINE)
        self.assertEqual(self.lines[at - 2], REVIEW_LINE)
        output = self.lines.index("## Output Format")
        self.assertLess(at, output)

    def test_every_read_of_the_skill_is_conditional(self) -> None:
        reads = [l for l in self.lines if BLAST_REL in l]
        self.assertEqual(reads, [SAFETY_LINE])

    def test_output_slot_after_security_assessment(self) -> None:
        self.assertIn(SAFETY_SLOT, self.lines)
        at = self.lines.index(SAFETY_SLOT)
        security = self.lines.index("### Security Assessment")
        issues = self.lines.index("### Issues Found (if FAIL)")
        self.assertLess(security, at)
        self.assertLess(at, issues)

    def test_no_ladder_or_format_text_in_agent(self) -> None:
        text = normalized(self.text)
        self.assertNotIn("**holds:**", text)
        self.assertNotIn("- traced:", text)
        self.assertNotIn("app-verify-result-v1", text)

    def test_generated_reviewer_carries_the_wiring(self) -> None:
        text = read(NATIVE_REVIEWER)
        self.assertIn(SAFETY_LINE, text.splitlines())
        self.assertIn(SAFETY_SLOT, text.splitlines())
        for name in ("recorded_test_results", "safety_fact", "blast_radius"):
            self.assertIn("| `%s` |" % name, text)


class EvaluatorHasNoSafetyFactTest(unittest.TestCase):
    """The evaluator never runs on the risk route. [AC-4.5]"""

    def test_no_safety_fact_input_or_read(self) -> None:
        for path in (EVALUATOR_AGENT, NATIVE_EVALUATOR):
            text = read(path)
            self.assertNotIn("safety_fact", text, path.name)
            self.assertNotIn("blast_radius", text, path.name)
            self.assertNotIn(BLAST_REL, text, path.name)


class Gate3SafetyFactTest(unittest.TestCase):
    """Gate 3 runs the verifier, routes its reasons, and prints the report
    lines; only Gate 3 runs it; the file stays under its byte cap.
    [AC-4.4, AC-4.5]"""

    def setUp(self) -> None:
        self.text = read(IMPLEMENT_STORY)
        self.gate3 = slice_between(self.text, "#### Gate 3: Review Agent", "#### Gate 3.5:")
        self.assertTrue(self.gate3, "Gate 3 section not found")

    def test_gate3_carries_the_wiring(self) -> None:
        for literal in (
            "python3 scripts/review-override.py safety-fact",
            ".writ/state/gate3-review-<story-stem>.md",
            "gate3-tests-<story-stem>.txt",
            "`recorded_test_results`",
            "`blast_radius`",
            "`safety_fact`",
            "safety_fact_missing",
            "safety_fact_below_floor",
            "safety_fact_contradicts_verdict",
            "same Gate 3 attempt",
            "review_cycle",
            "BLOCKED",
            "unverifiable",
            "a test that exercises the fact",
            "safety-fact: off",
            "safety-fact: not on route",
            "safety-fact: <measured> (claimed <claimed>) — <fact>",
        ):
            self.assertIn(literal, self.gate3)

    def test_gate_condition_is_pinned(self) -> None:
        """The paragraph runs only when `safety_fact` is on, and `safety_fact` is
        on exactly when Gate 2.5 wrote a blast radius."""
        self.assertIn("**Safety fact (`safety_fact` on).**", self.gate3)
        same_inputs = [l for l in self.gate3.splitlines()
                       if l.startswith("Spawn `review-agent` instead. Same inputs:")]
        self.assertEqual(len(same_inputs), 1, same_inputs)
        self.assertIn("`safety_fact` (`on` unless `blast_radius` is `(none)`)", same_inputs[0])

    def test_unverifiable_is_not_degraded(self) -> None:
        paragraph = slice_between(self.gate3, "**Safety fact", "**Jev shadow")
        self.assertIn("never `⚠️ DEGRADED`", paragraph)

    def test_contradicts_routes_before_re_review(self) -> None:
        paragraph = slice_between(self.gate3, "**Safety fact", "**Jev shadow")
        self.assertLess(paragraph.index("safety_fact_contradicts_verdict"),
                        paragraph.index("safety_fact_missing"))

    def test_verifier_runs_only_in_gate3(self) -> None:
        self.assertEqual(self.text.count("review-override.py safety-fact"), 1)
        self.assertEqual(self.gate3.count("review-override.py safety-fact"), 1)
        for start, end in (("#### Gate 0: Architecture Check", "#### Gate 0.5:"),
                           ("#### Gate 2.5:", "#### Gate 3: Review Agent"),
                           ("### Step 4: Story Completion", "## Error Handling")):
            block = slice_between(self.text, start, end)
            self.assertTrue(block, start)
            self.assertNotIn("safety_fact", block, start)
            self.assertNotIn("gate3-review-", block, start)

    def test_gate3_carries_no_ladder_text(self) -> None:
        self.assertNotIn(BLAST_REL, self.gate3)
        self.assertNotIn("app-verify-result-v1", self.gate3)

    def test_implement_story_byte_cap(self) -> None:
        size = len(IMPLEMENT_STORY.read_bytes())
        self.assertLessEqual(size, IMPLEMENT_STORY_CAP)


if __name__ == "__main__":
    unittest.main()
