#!/usr/bin/env python3
"""Wiring assertions for spec `2026-10-25-design-divergence`.

The spec ships markdown, so these checks read the files directly. Sections:

- Story 1: `skills/design-divergence/SKILL.md` content (frontmatter, lint,
  sections, the eight rules, the axis catalog, examples, boundary) and its
  registration (manifest, root catalog, README, generated trees)
  [AC-1.1 .. AC-1.4]. AC-1.5 is the verification run (`uv run pytest`,
  `uv run --python 3.9 pytest`, the bash tests, `bash scripts/eval.sh`), not
  an assertion here.
- Story 2 (`commands/prototype.md` Step 2.5) and Story 3 (`/implement-story`
  Gate 0) append their own sections below.

Run: uv run pytest scripts/tests/test_design_divergence_wiring.py -q
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

SKILL_NAME = "design-divergence"
SKILL = REPO_ROOT / "skills" / SKILL_NAME / "SKILL.md"
MANIFEST = REPO_ROOT / ".writ" / "manifest.yaml"
ROOT_CATALOG = REPO_ROOT / "SKILL.md"
README = REPO_ROOT / "README.md"
LINT = REPO_ROOT / "scripts" / "lint-skill.sh"

GENERATED_SKILL_COPIES = (
    REPO_ROOT / "plugins" / "writ" / "skills" / SKILL_NAME / "SKILL.md",
    REPO_ROOT / "cursor" / "plugin" / "skills" / SKILL_NAME / "SKILL.md",
)
CODEX_TEMPLATE = REPO_ROOT / "codex" / "AGENTS.md.template"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(text: str) -> "tuple[str, str]":
    """Return (frontmatter, body). Frontmatter is the block between the first
    two `---` lines; body is everything after the closing one."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return "", text


def frontmatter_value(frontmatter: str, key: str) -> Optional[str]:
    match = re.search(r"(?m)^%s:[ \t]*(.*)$" % re.escape(key), frontmatter)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def section(text: str, heading: str) -> str:
    """Text under `heading` (exact line) up to the next heading of the same or
    higher level. Empty string when the heading is absent."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return ""
    out: List[str] = []
    for line in lines[start + 1 :]:
        m = re.match(r"^(#{1,6})\s", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def table_rows(block: str) -> List[str]:
    """Data rows of the first markdown table in `block` (header and separator
    rows excluded)."""
    rows: List[str] = []
    in_table = False
    for line in block.splitlines():
        if line.startswith("|"):
            in_table = True
            rows.append(line)
        elif in_table:
            break
    return [r for r in rows[2:] if not re.match(r"^\|[\s:|-]+\|$", r)]


def numbered_items(block: str) -> List[str]:
    """Top-level numbered list items, each joined with its wrapped lines."""
    items: List[str] = []
    for line in block.splitlines():
        if re.match(r"^\d+\.\s", line):
            items.append(line)
        elif items and line.startswith("   ") and line.strip():
            items[-1] += " " + line.strip()
    return items


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
            entries[-1][m.group(1)] = m.group(2).strip()
    return entries


def skill_text() -> str:
    if not SKILL.is_file():
        raise AssertionError("%s does not exist" % SKILL.relative_to(REPO_ROOT))
    return read(SKILL)


# ---------------------------------------------------------------------------
# Story 1: skill content [AC-1.1, AC-1.2]
# ---------------------------------------------------------------------------


class SkillFrontmatterTest(unittest.TestCase):
    """[AC-1.1]"""

    def setUp(self) -> None:
        self.frontmatter, _ = split_frontmatter(skill_text())

    def test_name(self) -> None:
        self.assertEqual(frontmatter_value(self.frontmatter, "name"), SKILL_NAME)

    def test_description_starts_with_generate(self) -> None:
        description = frontmatter_value(self.frontmatter, "description") or ""
        self.assertTrue(description.startswith("Generate "), description)
        for medium in ("UI", "API shape", "data model"):
            self.assertIn(medium, description)

    def test_model_invocation_disabled(self) -> None:
        self.assertEqual(
            frontmatter_value(self.frontmatter, "disable-model-invocation"), "true"
        )

    def test_status_candidate(self) -> None:
        self.assertEqual(frontmatter_value(self.frontmatter, "status"), "candidate")


class SkillLintTest(unittest.TestCase):
    """[AC-1.1]"""

    def test_lint_line_one_is_pass(self) -> None:
        skill_text()
        result = subprocess.run(
            ["bash", str(LINT), str(SKILL.relative_to(REPO_ROOT))],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        first = result.stdout.splitlines()[0] if result.stdout else ""
        self.assertEqual(first, "pass", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0)


class SkillSectionsTest(unittest.TestCase):
    """[AC-1.2]"""

    def setUp(self) -> None:
        _, self.body = split_frontmatter(skill_text())

    def test_required_sections_in_order(self) -> None:
        headings = [l for l in self.body.splitlines() if l.startswith("## ")]
        required = ["## Purpose", "## When to Use", "## How to Apply", "## Examples"]
        positions = []
        for heading in required:
            self.assertIn(heading, headings)
            positions.append(headings.index(heading))
        self.assertEqual(positions, sorted(positions))


class SkillRulesTest(unittest.TestCase):
    """The eight rules in `## How to Apply` [AC-1.2]."""

    # One pattern per rule, in the technical spec's order.
    RULES = (
        ("usage first", r"(?i)caller'?s usage"),
        ("axes first", r"(?i)declare the axes"),
        ("independent contexts", r"(?i)independent"),
        ("commit before drafting", r"(?i)commit before drafting"),
        ("ordinary personas", r"(?i)ordinary personas"),
        ("two or three drafts", r"(?i)two or three drafts"),
        ("anti-pattern", r"(?i)anti-pattern"),
        ("same model family", r"(?i)same (model )?family"),
    )

    def setUp(self) -> None:
        _, body = split_frontmatter(skill_text())
        self.how = section(body, "## How to Apply")
        self.items = numbered_items(self.how)

    def test_exactly_eight_rules(self) -> None:
        self.assertEqual(len(self.items), 8, "\n".join(self.items))

    def test_each_rule_in_order(self) -> None:
        self.assertEqual(len(self.items), 8)
        for item, (label, pattern) in zip(self.items, self.RULES):
            self.assertRegex(item, pattern, "rule '%s' missing or out of order" % label)

    def test_usage_rule_gives_line_range(self) -> None:
        self.assertRegex(self.items[0], r"3 to 10 lines")

    def test_anti_pattern_states_its_reason(self) -> None:
        rule = self.items[6]
        self.assertIn("give me three options", rule)
        self.assertRegex(rule, r"(?i)fixate")
        self.assertRegex(rule, r"(?i)converge")

    def test_same_family_rule_excludes_cross_vendor_routing(self) -> None:
        rule = self.items[7]
        self.assertRegex(rule, r"(?i)out of scope")
        self.assertIn("ADR-024", rule)


class SkillAxisCatalogTest(unittest.TestCase):
    """One axis table per medium: UI, API shape, data model [AC-1.2]."""

    MEDIA = ("#### UI", "#### API shape", "#### Data model")

    def setUp(self) -> None:
        _, body = split_frontmatter(skill_text())
        self.catalog = section(section(body, "## How to Apply"), "### Axis catalog")

    def test_each_medium_has_a_two_or_three_row_table(self) -> None:
        self.assertTrue(self.catalog, "### Axis catalog missing under ## How to Apply")
        for heading in self.MEDIA:
            block = section(self.catalog, heading)
            self.assertTrue(block, "%s heading missing under ### Axis catalog" % heading)
            rows = table_rows(block)
            self.assertTrue(2 <= len(rows) <= 3, "%s: %d rows" % (heading, len(rows)))

    def test_exactly_three_media(self) -> None:
        media = [l for l in self.catalog.splitlines() if l.startswith("#### ")]
        self.assertEqual(media, list(self.MEDIA))


class SkillExamplesTest(unittest.TestCase):
    """One API example and one data-model example [AC-1.2]."""

    def setUp(self) -> None:
        _, body = split_frontmatter(skill_text())
        self.examples = section(body, "## Examples")

    def _example(self, prefix: str) -> str:
        headings = [l for l in self.examples.splitlines() if l.startswith("### " + prefix)]
        self.assertEqual(len(headings), 1, "expected one '### %s' example" % prefix)
        return section(self.examples, headings[0])

    def _assert_shape(self, block: str) -> None:
        self.assertRegex(block, r"(?i)\*\*Axes")
        self.assertRegex(block, r"\*\*Draft A")
        self.assertRegex(block, r"\*\*Draft B")
        self.assertRegex(block, r"(?i)usage")

    def test_api_example(self) -> None:
        self._assert_shape(self._example("API"))

    def test_data_model_example(self) -> None:
        self._assert_shape(self._example("Data model"))


class SkillBoundaryTest(unittest.TestCase):
    """The body stays a procedure: no commands, skills, subagents, caller steps,
    or vendor routing [AC-1.2; spec Business Rule 9; D20]."""

    def setUp(self) -> None:
        _, self.body = split_frontmatter(skill_text())

    def test_no_line_starts_with_slash(self) -> None:
        offenders = [l for l in self.body.splitlines() if l.startswith("/")]
        self.assertEqual(offenders, [])

    def test_no_invocation_text(self) -> None:
        for literal in ("Read commands/", "Read skills/", "Task("):
            self.assertNotIn(literal, self.body)

    def test_no_caller_specific_steps(self) -> None:
        for literal in ("render table", "gate0-divergence", "exploration.md", "Gate 0"):
            self.assertNotIn(literal, self.body)

    def test_no_other_vendor_named(self) -> None:
        self.assertNotRegex(self.body, r"(?i)\b(openai|gpt|gemini|grok|mistral|llama)\b")


# ---------------------------------------------------------------------------
# Story 1: registration [AC-1.3, AC-1.4]
# ---------------------------------------------------------------------------


class ManifestEntryTest(unittest.TestCase):
    """[AC-1.3]"""

    def setUp(self) -> None:
        self.entries = manifest_skill_entries()
        self.names = [e["name"] for e in self.entries]

    def test_one_entry(self) -> None:
        self.assertEqual(self.names.count(SKILL_NAME), 1)

    def test_alphabetical_placement(self) -> None:
        self.assertIn(SKILL_NAME, self.names)
        i = self.names.index(SKILL_NAME)
        self.assertEqual(self.names[i - 1], "dependency-context-loading")
        self.assertEqual(self.names[i + 1], "drift-triage")

    def test_fields(self) -> None:
        self.assertIn(SKILL_NAME, self.names)
        entry = self.entries[self.names.index(SKILL_NAME)]
        self.assertEqual(entry.get("file"), "skills/%s/SKILL.md" % SKILL_NAME)
        self.assertEqual(entry.get("status"), "candidate")
        self.assertEqual(entry.get("tags"), "[design, divergence, exploration]")
        frontmatter, _ = split_frontmatter(skill_text())
        self.assertEqual(
            entry.get("description", "").strip('"'),
            frontmatter_value(frontmatter, "description"),
        )


class CatalogAndReadmeTest(unittest.TestCase):
    """[AC-1.3]"""

    def test_root_catalog_lists_skill(self) -> None:
        rows = [
            l
            for l in read(ROOT_CATALOG).splitlines()
            if l.startswith("| `%s` |" % SKILL_NAME)
        ]
        self.assertEqual(len(rows), 1)
        self.assertIn("`candidate`", rows[0])

    def test_readme_skills_table_has_one_row(self) -> None:
        skills = section(read(README), "## Skills")
        rows = [
            l
            for l in table_rows(skills)
            if l.startswith("| [`%s`](skills/%s/SKILL.md) |" % (SKILL_NAME, SKILL_NAME))
        ]
        self.assertEqual(len(rows), 1)


class GeneratedTreesTest(unittest.TestCase):
    """The skill reaches every generated tree [AC-1.4]. Byte parity with the
    source is `gen-platform-trees.py --check`'s job."""

    def test_generated_copies_exist(self) -> None:
        for path in GENERATED_SKILL_COPIES:
            self.assertTrue(path.is_file(), str(path.relative_to(REPO_ROOT)))

    def test_codex_template_lists_skill(self) -> None:
        self.assertIn("| `%s` |" % SKILL_NAME, read(CODEX_TEMPLATE))


if __name__ == "__main__":
    unittest.main()
