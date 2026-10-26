#!/usr/bin/env python3
"""Wiring assertions for spec `2026-10-25-design-divergence`.

The spec ships markdown, so these checks read the files directly. Sections:

- Story 1: `skills/design-divergence/SKILL.md` content (frontmatter, lint,
  sections, the eight rules, the axis catalog, examples, boundary) and its
  registration (manifest, root catalog, README, generated trees)
  [AC-1.1 .. AC-1.4]. AC-1.5 is the verification run (`uv run pytest`,
  `uv run --python 3.9 pytest`, the bash tests, `bash scripts/eval.sh`), not
  an assertion here.
- Story 2: `commands/prototype.md` Step 2.5 reads the skill instead of
  carrying the rules inline, keeps its render-table pins, and links the skill
  under `## References` [AC-2.1, AC-2.2, AC-2.3]. AC-2.2's full pin set lives
  in `test_platform_neutral_names.py`; AC-2.3's byte-identity of the untouched
  sections and the shrink are checked against the pre-change file at
  verification time, since HEAD moves. AC-2.4 is the verification run
  (`gen-platform-trees.py --check`, `uv run pytest`,
  `uv run --python 3.9 pytest`, `bash scripts/eval.sh`), not an assertion here.
- Story 3: `commands/implement-story.md` Gate 0 carries the
  boundary-crossing divergence block: every text-contract literal, the three
  route-predictor commands, the switch, the seven report states, and the
  never-blocking rule; `.writ/docs/config-format.md` documents the switch; the
  Pipeline Gate 0 row, Overview clause, and References line name the skill
  [AC-3.1, AC-3.2, AC-3.3, AC-3.4]. AC-3.4's byte-identity of Gate 0.5
  through Gate 5, the routing table, and the completeness and worktree notes
  is checked against `git show HEAD:commands/implement-story.md` at
  verification time, since HEAD moves. AC-3.5 is the verification run (the
  ratchet re-pin in `test_governor_enforcement.py`,
  `gen-platform-trees.py --check`, `uv run pytest`,
  `uv run --python 3.9 pytest`, the bash tests, `bash scripts/eval.sh`), not
  an assertion here.

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


# ---------------------------------------------------------------------------
# Story 2: /prototype Step 2.5 loads the skill [AC-2.1, AC-2.2, AC-2.3]
# ---------------------------------------------------------------------------

PROTOTYPE = REPO_ROOT / "commands" / "prototype.md"
PLUGIN_PROTOTYPE = REPO_ROOT / "plugins" / "writ" / "commands" / "prototype.md"
STEP_25 = "### Step 2.5: Diverge & Choose"
DIFFER = "#### Getting drafts that actually differ"
READ_LINE = "Read skills/design-divergence/SKILL.md"
REFERENCE_LINK = "[design-divergence](../skills/design-divergence/SKILL.md)"


class PrototypeReadsSkillTest(unittest.TestCase):
    """[AC-2.1]"""

    def setUp(self) -> None:
        self.text = read(PROTOTYPE)
        self.differ = section(section(self.text, STEP_25), DIFFER)

    def test_subsection_present(self) -> None:
        self.assertTrue(self.differ.strip(), "%s missing under Step 2.5" % DIFFER)

    def test_subsection_reads_skill(self) -> None:
        self.assertIn(READ_LINE, self.differ)

    def test_subsection_states_what_the_step_owns(self) -> None:
        flat = " ".join(self.differ.split())
        self.assertRegex(flat, r"(?i)this step owns")
        for owned in ("when drafts are made", "what a draft is", "how they render", "the record"):
            self.assertIn(owned, flat)

    def test_inline_rules_removed(self) -> None:
        for removed in (
            "Declare the axes first.",
            "Use ordinary personas, not visionary ones.",
        ):
            self.assertNotIn(removed, self.text)

    def test_no_numbered_rules_left_in_subsection(self) -> None:
        self.assertEqual(numbered_items(self.differ), [])


class PrototypeRenderPinsTest(unittest.TestCase):
    """Step 2.5 keeps its heading order and render table [AC-2.2]."""

    def setUp(self) -> None:
        self.step = section(read(PROTOTYPE), STEP_25)

    def test_render_table_three_rows_in_order(self) -> None:
        block = section(self.step, "#### Render through the platform")
        rows = table_rows(block)
        self.assertEqual(len(rows), 3, "\n".join(rows))
        self.assertTrue(rows[0].startswith("| Native artboard/design surface |"))
        self.assertTrue(rows[1].startswith("| `canvas-preview` (the adapter maps it) |"))
        self.assertTrue(rows[2].startswith("| Neither |"))
        self.assertIn("Never degrade silently.", block)


class PrototypeReferencesTest(unittest.TestCase):
    """[AC-2.3]"""

    def test_references_link_skill_once(self) -> None:
        refs = section(read(PROTOTYPE), "## References")
        self.assertEqual(refs.count(REFERENCE_LINK), 1, refs)

    def test_plugin_copy_regenerated(self) -> None:
        """The generator rewrites paths, so the plugin copy is not a byte copy;
        parity is `gen-platform-trees.py --check`'s job. This only catches a
        stale plugin copy of the replaced subsection [AC-2.4]."""
        plugin = read(PLUGIN_PROTOTYPE)
        differ = section(section(plugin, STEP_25), DIFFER)
        self.assertIn("skills/design-divergence/SKILL.md", differ)
        self.assertNotIn("Declare the axes first.", plugin)


# ---------------------------------------------------------------------------
# Story 3: /implement-story Gate 0 divergence [AC-3.1, AC-3.2, AC-3.3, AC-3.4]
# ---------------------------------------------------------------------------

IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"
PLUGIN_IMPLEMENT_STORY = REPO_ROOT / "plugins" / "writ" / "commands" / "implement-story.md"
CONFIG_FORMAT = REPO_ROOT / ".writ" / "docs" / "config-format.md"
GATE_0 = "#### Gate 0: Architecture Check"
GATE_05 = "#### Gate 0.5"
BLOCK_LEAD = "**Design divergence (boundary-crossing route).**"
SWITCH_LITERAL = "- **Gate 0 Divergence:** off"
MALFORMED_LINE = "gate0-divergence: on (malformed: <value>)"

PREDICTOR_COMMANDS = (
    "python3 scripts/boundary-map.py compute --story <story-file> --repo . "
    "[--overlap <check-5-overlap>] > .writ/state/boundary-<story-stem>.json",
    "python3 scripts/change-surface.py classify --changed <planned files>",
    "python3 scripts/boundary-map.py crossings --map "
    ".writ/state/boundary-<story-stem>.json --changed <planned files> "
    "--story <story-file> --surface <class>",
)

# spec.md -> Experience Design -> State Catalog, in order.
REPORT_STATES = (
    "gate0-divergence: off (config)",
    MALFORMED_LINE,
    "gate0-divergence: skip (route evaluator-agent)",
    "gate0-divergence: skip (unverifiable: <reason>)",
    "gate0-divergence: skip (arch-check abort)",
    "gate0-divergence: skip (sketch incomplete: <A|B>)",
    "gate0-divergence: chose <A|B> (<axis combination>) — <why the other lost>",
)


def gate0_section(text: str) -> str:
    """`#### Gate 0: Architecture Check` up to `#### Gate 0.5`."""
    start = text.index(GATE_0)
    return text[start : text.index(GATE_05, start)]


def divergence_block(text: str) -> str:
    """From the block's bold lead to the `---` that precedes Gate 0.5."""
    gate0 = gate0_section(text)
    if BLOCK_LEAD not in gate0:
        raise AssertionError("%s missing from Gate 0" % BLOCK_LEAD)
    start = gate0.index(BLOCK_LEAD)
    end = gate0.rindex("\n---")
    if end < start:
        raise AssertionError("no `---` after the block inside Gate 0")
    return gate0[start:end]


def flat(text: str) -> str:
    return " ".join(text.split())


class Gate0DivergenceLiteralsTest(unittest.TestCase):
    """Every Gate 0 literal in technical-spec.md's text contract [AC-3.1]."""

    def setUp(self) -> None:
        self.text = read(IMPLEMENT_STORY)
        self.gate0 = gate0_section(self.text)
        self.block = divergence_block(self.text)

    def test_lead_and_read_line(self) -> None:
        self.assertEqual(self.gate0.count(BLOCK_LEAD), 1)
        self.assertIn(READ_LINE, self.block)

    def test_block_sits_after_anchor_confirmation(self) -> None:
        anchor = self.gate0.index("**Anchor confirmation (ADR-024):**")
        self.assertLess(anchor, self.gate0.index(BLOCK_LEAD))

    def test_predictor_commands_verbatim_in_bash_fence(self) -> None:
        fences = re.findall(r"```bash\n(.*?)```", self.block, re.S)
        lines = [l for fence in fences for l in fence.splitlines()]
        for command in PREDICTOR_COMMANDS:
            self.assertIn(command, lines)

    def test_triggers(self) -> None:
        for trigger in ("`--full-pipeline`", "`--panel`", "`route: review-agent`"):
            self.assertIn(trigger, self.block)

    def test_runs_after_proceed_or_caution_or_resolved_abort(self) -> None:
        block = flat(self.block)
        self.assertIn(
            "Run on PROCEED, CAUTION, `unverifiable`, or an ABORT resolved as proceed", block
        )

    def test_order_switch_abort_route_then_read(self) -> None:
        """BR2: switch off first, then an unresolved ABORT, then the route; the
        skill is read only on the route, inside the Sketches paragraph."""
        block = self.block
        positions = [
            block.index("`%s`" % SWITCH_LITERAL),
            block.index("`gate0-divergence: skip (arch-check abort)`"),
            block.index("`--panel`"),
            block.index("Otherwise run:"),
            block.index("```bash"),
            block.index("`gate0-divergence: skip (route evaluator-agent)`"),
            block.index("**Sketches.** `%s`" % READ_LINE),
            block.index("**Choice.**"),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(block.count(READ_LINE), 1)

    def test_predictor_runs_only_off_the_forced_triggers(self) -> None:
        self.assertIn("`--full-pipeline` or `--panel` qualifies. Otherwise run:", flat(self.block))

    def test_usage_written_before_axes(self) -> None:
        block = flat(self.block)
        path = "`.writ/state/divergence-<story-stem>.md`"
        self.assertIn(path, block)
        self.assertRegex(block, r"3 to 10 lines")
        self.assertLess(block.index(path), block.index("axes"))
        self.assertRegex(block, r"before (declaring|picking|any) ")

    def test_two_readonly_anchor_spawns_in_one_message(self) -> None:
        block = flat(self.block)
        self.assertRegex(block, r"(?i)two `readonly` .*at `anchor`")
        self.assertIn("one message", block)
        for item in ("the story", "`spec_lite_for_coding`", "persona"):
            self.assertIn(item, block)
        self.assertRegex(block, r"neither sees the other")

    def test_sketch_fields(self) -> None:
        block = flat(self.block)
        for field in ("`COMMITMENT:`", "`SKETCH:`", "`USAGE FIT:`"):
            self.assertIn(field, block)
        self.assertRegex(block, r"`SKETCH:` \(≤40 lines\)")
        self.assertLess(block.index("`COMMITMENT:`"), block.index("`SKETCH:`"))
        self.assertLess(block.index("`SKETCH:`"), block.index("`USAGE FIT:`"))

    def test_axes_from_skill_catalog(self) -> None:
        self.assertRegex(flat(self.block), r"two axes from the skill's catalog")

    def test_choice_rule_and_handoff(self) -> None:
        block = flat(self.block)
        self.assertRegex(block, r"unchanged usage|usage unchanged")
        self.assertRegex(block, r"fewer new public names")
        self.assertIn("`sketches converged`", block)
        self.assertIn("`design sketch (Gate 0 divergence)`", block)
        self.assertIn("Gate 0 warnings", block)

    def test_no_new_gate_heading_or_agent_marker(self) -> None:
        self.assertNotRegex(self.block, r"(?m)^#{1,6} ")
        self.assertNotIn("> **Agent:**", self.block)

    def test_block_under_2000_bytes(self) -> None:
        size = len(self.block.encode("utf-8"))
        self.assertLess(size, 2000, "block is %d bytes" % size)

    def test_plugin_copy_regenerated(self) -> None:
        """Parity is `gen-platform-trees.py --check`'s job; this catches a stale
        plugin copy of Gate 0 [AC-3.5]."""
        plugin = gate0_section(read(PLUGIN_IMPLEMENT_STORY))
        self.assertIn(BLOCK_LEAD, plugin)


class Gate0DivergenceSwitchTest(unittest.TestCase):
    """The switch in Gate 0 and config-format.md, and the report states [AC-3.2]."""

    def setUp(self) -> None:
        self.block = flat(divergence_block(read(IMPLEMENT_STORY)))
        self.config = read(CONFIG_FORMAT)

    def test_switch_literal_in_gate0(self) -> None:
        self.assertIn("`%s`" % SWITCH_LITERAL, self.block)

    def test_gate0_absent_means_on_and_malformed_means_on(self) -> None:
        self.assertRegex(self.block, r"(?i)absent( line)? or `on` means on")
        self.assertRegex(self.block, r"(another|any other) value (means|is) on")
        self.assertIn("`%s`" % MALFORMED_LINE, self.block)

    def test_report_states_each_start_with_prefix(self) -> None:
        for state in REPORT_STATES:
            self.assertIn("`%s`" % state, self.block, state)
        spans = re.findall(r"`(gate0-divergence: [^`]+)`", self.block)
        self.assertEqual(sorted(set(spans)), sorted(REPORT_STATES))

    def test_every_run_prints_a_line(self) -> None:
        self.assertRegex(self.block, r"Each run prints a `gate0-divergence:` line")

    def test_config_key_table_row(self) -> None:
        rows = [
            r
            for r in table_rows(section(self.config, "## Supported Keys"))
            if r.startswith("| `Gate 0 Divergence` |")
        ]
        self.assertEqual(len(rows), 1)
        self.assertIn("implement-story (Gate 0)", rows[0])
        self.assertIn("`off`", rows[0])

    def test_config_section(self) -> None:
        body = section(self.config, "## Gate 0 Divergence")
        self.assertTrue(body.strip(), "## Gate 0 Divergence section missing")
        self.assertIn(SWITCH_LITERAL, body)
        text = flat(body)
        self.assertRegex(text, r"(?i)no line.*means on|absent.*means on")
        self.assertIn("`%s`" % MALFORMED_LINE, text)
        self.assertRegex(text, r"(?i)only Gate 0 reads")
        self.assertIn("`/prototype`", text)


class Gate0DivergenceNeverBlocksTest(unittest.TestCase):
    """No divergence outcome blocks the story [AC-3.3]."""

    def setUp(self) -> None:
        self.block = flat(divergence_block(read(IMPLEMENT_STORY)))

    def test_never_blocking_statements(self) -> None:
        self.assertRegex(self.block, r"(?i)never blocks")
        self.assertIn("DEGRADED", self.block)
        self.assertIn("AskQuestion", self.block)
        self.assertIn("`review_cycle`", self.block)
        self.assertRegex(self.block, r"(?i)\bretr(y|ies)\b")

    def test_sketch_failure_skips_without_retry(self) -> None:
        self.assertRegex(self.block, r"(?i)spawn error or (a )?missing field")


class Gate0DivergenceOtherEditsTest(unittest.TestCase):
    """Overview clause, Pipeline Gate 0 row, References line [AC-3.4]."""

    def setUp(self) -> None:
        self.text = read(IMPLEMENT_STORY)

    def test_overview_clause(self) -> None:
        overview = section(self.text, "## Overview")
        self.assertIn("and two Gate 0 sketch spawns on the boundary-crossing route", overview)

    def test_pipeline_gate0_row(self) -> None:
        pipeline = section(self.text, "## Pipeline")
        rows = [r for r in pipeline.splitlines() if r.startswith("| Gate 0 |")]
        self.assertEqual(len(rows), 1)
        cells = [c.strip() for c in rows[0].strip("|").split("|")]
        self.assertEqual(len(cells), 5, rows[0])
        self.assertIn("two sketch spawns on the boundary-crossing route", cells[2])
        self.assertEqual(cells[4].replace("`", ""), "design-divergence (boundary-crossing route)")

    def test_references_link_once(self) -> None:
        refs = section(self.text, "## References")
        self.assertEqual(refs.count(REFERENCE_LINK), 1, refs)


if __name__ == "__main__":
    unittest.main()
