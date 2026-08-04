#!/usr/bin/env python3
"""Unit tests for scripts/story-context.py.

Every test builds a disposable spec tree in a temp directory via
`make_spec_tree()` (this repo has no static `scripts/tests/fixtures/`
directory convention — `eval-spec-deps.py`'s `make_spec()` in-temp-dir
pattern is the established precedent) and exercises the assembler against
that tree, matching the shape it sees in production: `<spec>/spec.md`,
`<spec>/sub-specs/technical-spec.md`, `<spec>/user-stories/story-N-slug.md`.

The module filename contains a hyphen, so it is imported by path — the exact
recipe `test_story_deps.py` uses.

Coverage maps to `.writ/docs/context-hint-format.md`'s Error Handling table,
the technical-spec.md Error & Rescue Map rows for hint parsing/resolution,
and the Interaction Edge Cases this story touches (duplicate-Operation-name
concatenation, byte-identical repeats, Unicode headers, empty brackets,
duplicate category-line merging, both reference forms).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

MODULE_PATH = Path(__file__).resolve().parent.parent / "story-context.py"
_spec = importlib.util.spec_from_file_location("story_context", MODULE_PATH)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)  # type: ignore[union-attr]


def make_spec_tree(
    root: Path,
    spec_id: str = "s-spec",
    *,
    spec_md: str | None = "DEFAULT",
    technical_spec_md: str | None = None,
    hints: str | None = None,
    story_body: str = "## User Story\n\nBody.\n",
) -> Path:
    """Build one disposable spec folder and return the story file path.

    `spec_md=None` omits spec.md entirely (unreadable/missing fixture).
    `spec_md="DEFAULT"` writes a standard spec.md with Business Rules and
    Experience Design sections used across the happy-path tests.
    `technical_spec_md=None` (the default) omits technical-spec.md, matching
    the "no sub-specs dir" fallback fixture; pass content to include it.
    `hints=None` omits the `## Context for Agents` section (legacy story).
    """
    folder = root / spec_id
    folder.mkdir(parents=True, exist_ok=True)

    if spec_md == "DEFAULT":
        spec_md = (
            "# Spec: Example\n\n"
            "## \U0001F4CB Business Rules\n\n"
            "1. **One implementation per contract.** No duplicated parsers survive.\n"
            "2. **Determinism is a testable property.** Byte-identical repeat runs.\n\n"
            "## \U0001F3AF Experience Design\n\n"
            "### Entry Point\n\n"
            "No new user-invokable surface.\n\n"
            "### Happy Path\n\n"
            "1. Developer runs the command.\n"
            "2. Batches print.\n\n"
            "### Error Experience\n\n"
            "| Situation | Behavior |\n"
            "|---|---|\n"
            "| Bad graph | Blocking. |\n"
        )
    if spec_md is not None:
        (folder / "spec.md").write_text(spec_md, encoding="utf-8")

    if technical_spec_md is not None:
        sub = folder / "sub-specs"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "technical-spec.md").write_text(technical_spec_md, encoding="utf-8")

    stories = folder / "user-stories"
    stories.mkdir(parents=True, exist_ok=True)
    lines = ["# Story 1: Example", "", story_body]
    if hints is not None:
        lines += ["", "## Context for Agents", "", hints]
    story_path = stories / "story-1-example.md"
    story_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return story_path


DEFAULT_TECH_SPEC = (
    "# Technical Spec\n\n"
    "## Error & Rescue Map\n\n"
    "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
    "|---|---|---|---|\n"
    "| Create session | Redis unavailable | Retry once, then fail | Fixture |\n"
    "| Validate input | Missing field | 400 with field name | Fixture |\n\n"
    "## Shadow Paths\n\n"
    "| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |\n"
    "|---|---|---|---|---|\n"
    "| User registration flow | Account created | N/A | Rejected | Retry |\n"
)


class ExtractMarkdownSectionTests(unittest.TestCase):
    def test_exact_match_after_strip(self) -> None:
        text = "## Foo\n\nBody.\n\n## Bar\n\nOther.\n"
        section = sc.extract_markdown_section(text, "## Foo")
        self.assertIn("Body.", section)
        self.assertNotIn("Other.", section)

    def test_unicode_emoji_heading_resolves(self) -> None:
        text = "## \U0001F3AF Experience Design\n\nContent.\n\n## Next\n\nMore.\n"
        section = sc.extract_markdown_section(text, "## \U0001F3AF Experience Design")
        self.assertIsNotNone(section)
        self.assertIn("Content.", section)
        self.assertNotIn("More.", section)

    def test_missing_heading_returns_none(self) -> None:
        self.assertIsNone(sc.extract_markdown_section("## Foo\n\nBody.\n", "## Missing"))

    def test_subsection_search_scoped_to_slice(self) -> None:
        outer = "## Experience\n\n### A\n\nOne.\n\n### B\n\nTwo.\n"
        section = sc.extract_markdown_section(outer, "### B")
        self.assertIn("Two.", section)
        self.assertNotIn("One.", section)


class ParseCategoryValueTests(unittest.TestCase):
    def test_bracket_form_splits_and_trims(self) -> None:
        self.assertEqual(
            sc.parse_category_value("[Create session,  Validate input ]"),
            ("bracket", ["Create session", "Validate input"]),
        )

    def test_empty_brackets_is_valid_empty_signal(self) -> None:
        self.assertEqual(sc.parse_category_value("[]"), ("empty", []))

    def test_unclosed_bracket_is_none(self) -> None:
        self.assertIsNone(sc.parse_category_value("[Create session, Validate input"))

    def test_no_recognizable_form_is_none(self) -> None:
        self.assertIsNone(sc.parse_category_value("just prose, no markers"))

    def test_extended_form_single_arrow_span(self) -> None:
        self.assertEqual(
            sc.parse_category_value("`technical-spec.md \u2192 ## Error & Rescue Map`"),
            ("extended", ["technical-spec.md \u2192 ## Error & Rescue Map"]),
        )

    def test_double_arrow_not_supported(self) -> None:
        # Finding 3: only the single-character → arrow is canonical. A `>>`
        # arrow inside backticks with ".md" still has no → and is not an
        # extended reference at all — it falls through to bracket parsing
        # (which also fails, since there's no `[`), so the line is
        # unparseable, not silently accepted as a legacy-lenient extended ref.
        self.assertIsNone(sc.parse_category_value("`technical-spec.md >> ## Error & Rescue Map`"))

    def test_backtick_item_without_md_or_arrow_is_bracket_text(self) -> None:
        # `eval-leanness` calls assembler is a real Operation name containing
        # backticks but no ".md"/arrow — must be treated as ordinary bracket
        # text, not misdetected as an extended reference.
        self.assertEqual(
            sc.parse_category_value("[`eval-leanness` calls assembler]"),
            ("bracket", ["`eval-leanness` calls assembler"]),
        )


class ParseHintLinesTests(unittest.TestCase):
    def test_recognized_categories_parsed(self) -> None:
        section = (
            "## Context for Agents\n\n"
            "- **Error map rows:** [Create session]\n"
            "- **Shadow paths:** [User registration flow]\n"
            "- **Business rules:** [One implementation per contract]\n"
            "- **Experience:** [Entry Point]\n"
        )
        data, warnings = sc.parse_hint_lines(section)
        self.assertEqual(warnings, [])
        self.assertEqual(data["Error map rows"]["bracket_refs"], ["Create session"])
        self.assertEqual(data["Experience"]["bracket_refs"], ["Entry Point"])

    def test_category_prefix_typo_skips_and_warns(self) -> None:
        section = "- **Eror map rows:** [Create session]\n"
        data, warnings = sc.parse_hint_lines(section)
        self.assertEqual(data, {})
        self.assertEqual(len(warnings), 1)
        self.assertIn('Unrecognized context hint category: "Eror map rows"', warnings[0])

    def test_malformed_bracket_skips_and_warns(self) -> None:
        section = "- **Error map rows:** [Create session, Validate input\n"
        data, warnings = sc.parse_hint_lines(section)
        # The category entry exists (so later duplicate-line bookkeeping still
        # works) but carries no references — assemble() drops empty entries
        # before resolution, so this never surfaces as content.
        self.assertEqual(data["Error map rows"], {"bracket_refs": [], "extended_refs": []})
        self.assertEqual(len(warnings), 1)
        self.assertIn("Malformed context hint category", warnings[0])

    def test_empty_brackets_no_warning(self) -> None:
        section = "- **Error map rows:** []\n"
        data, warnings = sc.parse_hint_lines(section)
        self.assertEqual(warnings, [])
        self.assertEqual(data["Error map rows"]["bracket_refs"], [])

    def test_duplicate_category_lines_merge_and_warn_once(self) -> None:
        section = (
            "- **Business rules:** [Rule A]\n"
            "- **Business rules:** [Rule B]\n"
            "- **Business rules:** [Rule A, Rule C]\n"
        )
        data, warnings = sc.parse_hint_lines(section)
        self.assertEqual(data["Business rules"]["bracket_refs"], ["Rule A", "Rule B", "Rule C"])
        duplicate_warnings = [w for w in warnings if "Duplicate context hint category" in w]
        self.assertEqual(len(duplicate_warnings), 1)


class ResolveTableCategoryTests(unittest.TestCase):
    """Finding 1 (duplicate Operation names -> concatenate all, table order,
    deduplicated, no warning) and Finding 2 (exact match, backticks preserved)."""

    def test_single_match_resolves(self) -> None:
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Create session"], DEFAULT_TECH_SPEC, "## Error & Rescue Map", "", "### Error Experience", warnings
        )
        self.assertIn("Create session", content)
        self.assertIn("Redis unavailable", content)
        self.assertEqual(warnings, [])

    def test_duplicate_operation_names_concatenate_all_rows_in_table_order(self) -> None:
        tech = (
            "## Error & Rescue Map\n\n"
            "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
            "|---|---|---|---|\n"
            "| Parse hint category | Prefix typo | Skip line, warn | Fixture A |\n"
            "| Parse hint category | Malformed brackets | Skip category, warn | Fixture B |\n"
            "| Parse hint category | Empty brackets | Skip silently | Fixture C |\n"
        )
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Parse hint category"], tech, "## Error & Rescue Map", "", "### Error Experience", warnings
        )
        self.assertEqual(warnings, [])
        for expected in ("Prefix typo", "Malformed brackets", "Empty brackets"):
            self.assertIn(expected, content)
        # Table order preserved: Prefix typo's row appears before Malformed
        # brackets', which appears before Empty brackets'.
        self.assertLess(content.index("Prefix typo"), content.index("Malformed brackets"))
        self.assertLess(content.index("Malformed brackets"), content.index("Empty brackets"))

    def test_backtick_preserved_exact_match(self) -> None:
        tech = (
            "## Error & Rescue Map\n\n"
            "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
            "|---|---|---|---|\n"
            "| Parse `Dependencies` header | Header absent | Treat as None | Fixture |\n"
        )
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Parse `Dependencies` header"], tech, "## Error & Rescue Map", "", "### Error Experience", warnings
        )
        self.assertIn("Header absent", content)
        self.assertEqual(warnings, [])

    def test_backtick_stripped_reference_does_not_match(self) -> None:
        # Finding 2: matching is exact on the raw cell text — a reference
        # authored WITHOUT the table's backticks must not match.
        tech = (
            "## Error & Rescue Map\n\n"
            "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
            "|---|---|---|---|\n"
            "| Parse `Dependencies` header | Header absent | Treat as None | Fixture |\n"
        )
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Parse Dependencies header"], tech, "## Error & Rescue Map", "", "### Error Experience", warnings
        )
        self.assertEqual(content, "")
        self.assertEqual(len(warnings), 1)
        self.assertIn('missing content: "Parse Dependencies header"', warnings[0])

    def test_unmatched_reference_warns_and_is_skipped(self) -> None:
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Nonexistent Operation"], DEFAULT_TECH_SPEC, "## Error & Rescue Map", "", "### Error Experience", warnings
        )
        self.assertEqual(content, "")
        self.assertEqual(len(warnings), 1)
        self.assertIn('"Nonexistent Operation"', warnings[0])
        self.assertIn("technical-spec.md", warnings[0])

    def test_technical_spec_absent_falls_back_to_spec_md_subsection(self) -> None:
        spec_text = (
            "## \U0001F3AF Experience Design\n\n### Error Experience\n\n"
            "| Situation | Behavior |\n|---|---|\n| Bad graph | Blocking. |\n"
        )
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Create session"], None, "## Error & Rescue Map", spec_text, "### Error Experience", warnings
        )
        self.assertIn("Bad graph", content)
        self.assertEqual(warnings, [])  # silent fallback per the Error & Rescue Map row

    def test_technical_spec_absent_and_fallback_subsection_missing_warns(self) -> None:
        spec_text = "## Some Other Section\n\nNothing relevant.\n"
        warnings: list[str] = []
        content = sc.resolve_table_category(
            ["Create session"], None, "## Error & Rescue Map", spec_text, "### Error Experience", warnings
        )
        self.assertEqual(content, "")
        self.assertEqual(len(warnings), 1)


class ResolveBusinessRulesTests(unittest.TestCase):
    def test_matches_bold_phrase_ignoring_trailing_period(self) -> None:
        spec_text = (
            "## \U0001F4CB Business Rules\n\n"
            "1. **One implementation per contract.** No duplicated parsers survive.\n"
        )
        warnings: list[str] = []
        content = sc.resolve_business_rules(["One implementation per contract"], spec_text, warnings)
        self.assertIn("No duplicated parsers survive.", content)
        self.assertEqual(warnings, [])

    def test_unmatched_rule_warns(self) -> None:
        spec_text = "## \U0001F4CB Business Rules\n\n1. **Real rule.** Text.\n"
        warnings: list[str] = []
        content = sc.resolve_business_rules(["Fictional rule"], spec_text, warnings)
        self.assertEqual(content, "")
        self.assertEqual(len(warnings), 1)

    def test_missing_section_warns_for_each_ref(self) -> None:
        warnings: list[str] = []
        content = sc.resolve_business_rules(["A", "B"], "## Nothing Here\n", warnings)
        self.assertEqual(content, "")
        self.assertEqual(len(warnings), 2)


class ResolveExperienceTests(unittest.TestCase):
    def test_matches_subsection_by_exact_name(self) -> None:
        spec_text = "## \U0001F3AF Experience Design\n\n### Entry Point\n\nNo new surface.\n"
        warnings: list[str] = []
        content = sc.resolve_experience(["Entry Point"], spec_text, warnings)
        self.assertIn("No new surface.", content)
        self.assertEqual(warnings, [])

    def test_unmatched_subsection_warns(self) -> None:
        spec_text = "## \U0001F3AF Experience Design\n\n### Entry Point\n\nContent.\n"
        warnings: list[str] = []
        content = sc.resolve_experience(["Moment of Truth"], spec_text, warnings)
        self.assertEqual(content, "")
        self.assertEqual(len(warnings), 1)


class ResolveExtendedRefTests(unittest.TestCase):
    def test_resolves_nested_section_chain(self) -> None:
        with TemporaryDirectory() as tmp:
            spec_folder = Path(tmp)
            (spec_folder / "spec.md").write_text(
                "## \U0001F3AF Experience Design\n\n### Error Experience\n\nWarn and skip.\n", encoding="utf-8"
            )
            content = sc.resolve_extended_ref(
                spec_folder, "spec.md \u2192 ## \U0001F3AF Experience Design \u2192 ### Error Experience"
            )
            self.assertIsNotNone(content)
            self.assertIn("Warn and skip.", content)

    def test_missing_file_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            content = sc.resolve_extended_ref(Path(tmp), "missing.md \u2192 ## Section")
            self.assertIsNone(content)

    def test_missing_heading_returns_none(self) -> None:
        with TemporaryDirectory() as tmp:
            spec_folder = Path(tmp)
            (spec_folder / "spec.md").write_text("## Real Heading\n\nBody.\n", encoding="utf-8")
            content = sc.resolve_extended_ref(spec_folder, "spec.md \u2192 ## Missing Heading")
            self.assertIsNone(content)

    def test_resolves_via_sub_specs_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            spec_folder = Path(tmp)
            sub = spec_folder / "sub-specs"
            sub.mkdir()
            (sub / "technical-spec.md").write_text(
                "## Error & Rescue Map\n\nTable content.\n", encoding="utf-8"
            )
            content = sc.resolve_extended_ref(spec_folder, "technical-spec.md \u2192 ## Error & Rescue Map")
            self.assertIsNotNone(content)
            self.assertIn("Table content.", content)

    def test_relative_traversal_escapes_confinement_returns_none(self) -> None:
        # A `../` reference that resolves outside spec_folder must degrade
        # exactly like a missing file (None) — never disclose the escaped
        # file's content.
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "secret.md").write_text(
                "## Secret\n\nTop secret content that must never leak.\n", encoding="utf-8"
            )
            spec_folder = root / "spec"
            spec_folder.mkdir()
            content = sc.resolve_extended_ref(spec_folder, "../secret.md \u2192 ## Secret")
            self.assertIsNone(content)

    def test_absolute_path_reference_returns_none(self) -> None:
        # pathlib's `/` operator discards the left operand entirely when the
        # right-hand side is absolute (spec_folder / "/etc/passwd" ==
        # "/etc/passwd"). An absolute-path reference must be rejected the
        # same way a missing file is — never disclose arbitrary local files.
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside-secret.md"
            outside.write_text(
                "## Secret\n\nTop secret content that must never leak.\n", encoding="utf-8"
            )
            spec_folder = root / "spec"
            spec_folder.mkdir()
            content = sc.resolve_extended_ref(spec_folder, f"{outside.resolve()} \u2192 ## Secret")
            self.assertIsNone(content)


class AssembleTests(unittest.TestCase):
    def test_happy_path_both_reference_forms_all_categories(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = (
                "- **Error map rows:** [Create session, Validate input]\n"
                "- **Shadow paths:** [User registration flow]\n"
                "- **Business rules:** [One implementation per contract]\n"
                "- **Experience:** `spec.md \u2192 ## \U0001F3AF Experience Design "
                "\u2192 ### Entry Point`\n"
            )
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            self.assertEqual(payload["warnings"], [])
            self.assertIn("Create session", payload["fetched_context"]["error_map_rows"])
            self.assertIn("User registration flow", payload["fetched_context"]["shadow_paths"])
            self.assertIn("No duplicated parsers survive", payload["fetched_context"]["business_rules"])
            self.assertIn("No new user-invokable surface", payload["fetched_context"]["experience"])
            self.assertFalse(payload["truncated"])
            self.assertEqual(
                payload["bytes"]["total"],
                sum(v for k, v in payload["bytes"].items() if k != "total"),
            )

    def test_legacy_story_no_hints_section(self) -> None:
        with TemporaryDirectory() as tmp:
            story = make_spec_tree(Path(tmp), hints=None)
            payload = sc.assemble(story)
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(payload["bytes"], {"total": 0})
            self.assertFalse(payload["truncated"])
            self.assertEqual(len(payload["warnings"]), 1)
            self.assertIn("No \"## Context for Agents\" section", payload["warnings"][0])

    def test_story_file_missing_returns_empty_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.md"
            payload = sc.assemble(missing)
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(len(payload["warnings"]), 1)
            self.assertIn("unreadable or missing", payload["warnings"][0])

    def test_spec_md_absent_returns_empty_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            story = make_spec_tree(
                Path(tmp), spec_md=None, technical_spec_md=DEFAULT_TECH_SPEC,
                hints="- **Error map rows:** [Create session]\n",
            )
            payload = sc.assemble(story)
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(payload["bytes"], {"total": 0})
            self.assertEqual(len(payload["warnings"]), 1)
            self.assertIn("spec.md absent or unreadable", payload["warnings"][0])

    def test_technical_spec_absent_falls_back_end_to_end(self) -> None:
        with TemporaryDirectory() as tmp:
            story = make_spec_tree(
                Path(tmp), technical_spec_md=None,
                hints="- **Error map rows:** [Create session]\n",
            )
            payload = sc.assemble(story)
            self.assertIn("error_map_rows", payload["fetched_context"])
            self.assertIn("Bad graph", payload["fetched_context"]["error_map_rows"])
            self.assertEqual(payload["warnings"], [])

    def test_empty_brackets_skip_category_silently(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = "- **Error map rows:** []\n- **Business rules:** [One implementation per contract]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            self.assertNotIn("error_map_rows", payload["fetched_context"])
            self.assertIn("business_rules", payload["fetched_context"])
            self.assertEqual(payload["warnings"], [])

    def test_category_prefix_typo_warns_and_continues(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = "- **Eror map rows:** [Create session]\n- **Business rules:** [One implementation per contract]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            self.assertIn("business_rules", payload["fetched_context"])
            self.assertTrue(any("Unrecognized context hint category" in w for w in payload["warnings"]))

    def test_malformed_brackets_warns_and_continues(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = (
                "- **Error map rows:** [Create session, Validate input\n"
                "- **Business rules:** [One implementation per contract]\n"
            )
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            self.assertNotIn("error_map_rows", payload["fetched_context"])
            self.assertIn("business_rules", payload["fetched_context"])
            self.assertTrue(any("Malformed context hint category" in w for w in payload["warnings"]))

    def test_missing_referenced_row_warns_and_continues(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = (
                "- **Error map rows:** [Nonexistent Operation]\n"
                "- **Business rules:** [One implementation per contract]\n"
            )
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            self.assertNotIn("error_map_rows", payload["fetched_context"])
            self.assertIn("business_rules", payload["fetched_context"])
            self.assertTrue(
                any('"Nonexistent Operation"' in w for w in payload["warnings"])
            )

    def test_duplicate_category_lines_merge_end_to_end(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = (
                "- **Business rules:** [One implementation per contract]\n"
                "- **Business rules:** [Determinism is a testable property]\n"
            )
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            content = payload["fetched_context"]["business_rules"]
            self.assertIn("No duplicated parsers survive", content)
            self.assertIn("Byte-identical repeat runs", content)
            duplicate_warnings = [w for w in payload["warnings"] if "Duplicate context hint category" in w]
            self.assertEqual(len(duplicate_warnings), 1)

    def test_duplicate_operation_name_concatenation_fixture(self) -> None:
        """Architecture Check Finding 1, end-to-end: a bracketed reference
        matching multiple Error & Rescue Map rows under the same Operation
        name concatenates ALL of them in table order, deduplicated, with no
        warning — mirroring Story 2's own real hint ("Parse hint category",
        which genuinely has 3 rows in the live technical-spec.md)."""
        tech = (
            "## Error & Rescue Map\n\n"
            "| Operation | What Can Fail | Planned Handling | Test Strategy |\n"
            "|---|---|---|---|\n"
            "| Read source spec | `technical-spec.md` absent | Fall through to spec.md fallback | Fixture 1 |\n"
            "| Read source spec | `spec.md` absent or unreadable | Warn, return empty payload | Fixture 2 |\n"
        )
        with TemporaryDirectory() as tmp:
            hints = "- **Error map rows:** [Read source spec]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=tech, hints=hints)
            payload = sc.assemble(story)
            content = payload["fetched_context"]["error_map_rows"]
            self.assertIn("Fall through to spec.md fallback", content)
            self.assertIn("Warn, return empty payload", content)
            self.assertEqual(payload["warnings"], [])

    def test_unicode_section_header_resolves(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = "- **Experience:** [Entry Point]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story)
            self.assertIn("No new user-invokable surface", payload["fetched_context"]["experience"])

    def test_repeated_runs_are_byte_identical(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = (
                "- **Error map rows:** [Create session, Validate input]\n"
                "- **Shadow paths:** [User registration flow]\n"
                "- **Business rules:** [One implementation per contract, Determinism is a testable property]\n"
                "- **Experience:** [Entry Point, Happy Path]\n"
            )
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            first = json.dumps(sc.assemble(story))
            second = json.dumps(sc.assemble(story))
            self.assertEqual(first, second)

    def test_budget_bytes_of_one_truncates_to_a_single_byte(self) -> None:
        # Story 2's "budget-bytes is accepted and otherwise unused" contract
        # is retired by Story 3: a budget tighter than the resolved content
        # now truncates for real rather than being silently ignored.
        with TemporaryDirectory() as tmp:
            hints = "- **Business rules:** [One implementation per contract]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            payload = sc.assemble(story, budget_bytes=1)
            self.assertTrue(payload["truncated"])
            self.assertEqual(payload["bytes"]["total"], 1)
            self.assertEqual(len(payload["fetched_context"]["business_rules"].encode("utf-8")), 1)


class DerivedBudgetConstantTests(unittest.TestCase):
    def test_constant_is_a_positive_int_above_the_measured_max(self) -> None:
        """Sanity check on FETCHED_CONTEXT_BUDGET_BYTES's derivation comment
        (Business Rule 4): the committed constant must exceed the observed
        corpus max (10251 bytes at derivation time, 2026-08-03) — a cap at or
        below the biggest real story would fire on normal work, not just
        pathology. Re-run scripts/sweep-story-context-bytes.py periodically
        and update both the constant and this bound if the corpus shifts."""
        self.assertIsInstance(sc.FETCHED_CONTEXT_BUDGET_BYTES, int)
        self.assertGreater(sc.FETCHED_CONTEXT_BUDGET_BYTES, 10251)


class BudgetEnforcementTests(unittest.TestCase):
    """Story 3, AC2/AC3/AC5 + Architecture Check Findings 4 and 6.

    Every scenario first assembles WITHOUT a budget to learn the real,
    non-hardcoded byte sizes of the fixture's resolved categories, then
    derives budgets relative to those measured sizes — avoiding brittle
    hardcoded byte-count assertions that would silently drift if the
    fixture text or the assembler's whitespace handling ever changes.
    """

    def _four_category_story(self, tmp: str) -> Path:
        hints = (
            "- **Error map rows:** [Create session, Validate input]\n"
            "- **Shadow paths:** [User registration flow]\n"
            "- **Business rules:** [One implementation per contract]\n"
            "- **Experience:** [Entry Point]\n"
        )
        return make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)

    def test_exactly_at_budget_is_not_truncated(self) -> None:
        """Finding 6 — dedicated boundary test, isolated from the over-budget
        case: total == budget must NOT truncate (strictly-greater triggers)."""
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            unbudgeted = sc.assemble(story)
            exact_budget = unbudgeted["bytes"]["total"]

            payload = sc.assemble(story, budget_bytes=exact_budget)
            self.assertFalse(payload["truncated"])
            self.assertEqual(payload["fetched_context"], unbudgeted["fetched_context"])
            self.assertEqual(payload["bytes"], unbudgeted["bytes"])
            self.assertFalse(any("truncated" in w for w in payload["warnings"]))

    def test_one_byte_over_budget_truncates_with_warning(self) -> None:
        """AC2 — strictly exceeding the budget truncates, sets truncated:
        true, and warns naming actual and budget bytes."""
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            unbudgeted = sc.assemble(story)
            actual_total = unbudgeted["bytes"]["total"]
            budget = actual_total - 1

            payload = sc.assemble(story, budget_bytes=budget)
            self.assertTrue(payload["truncated"])
            self.assertEqual(payload["bytes"]["total"], budget)
            truncation_warnings = [w for w in payload["warnings"] if "fetched_context truncated" in w]
            self.assertEqual(len(truncation_warnings), 1)
            self.assertIn(str(actual_total), truncation_warnings[0])
            self.assertIn(str(budget), truncation_warnings[0])

    def test_relevance_ordered_retention_keeps_higher_relevance_categories_whole(self) -> None:
        """Finding 4 — CATEGORY_ORDER doubles as truncation priority: when the
        budget covers the first three categories exactly but not the fourth,
        error_map_rows/shadow_paths/business_rules survive whole and the
        lowest-relevance category (experience) is dropped entirely, not
        partially — because it never gets a turn at the remaining budget."""
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            unbudgeted = sc.assemble(story)
            fetched = unbudgeted["fetched_context"]
            budget = (
                unbudgeted["bytes"]["error_map_rows"]
                + unbudgeted["bytes"]["shadow_paths"]
                + unbudgeted["bytes"]["business_rules"]
            )

            payload = sc.assemble(story, budget_bytes=budget)
            self.assertTrue(payload["truncated"])
            self.assertEqual(payload["fetched_context"]["error_map_rows"], fetched["error_map_rows"])
            self.assertEqual(payload["fetched_context"]["shadow_paths"], fetched["shadow_paths"])
            self.assertEqual(payload["fetched_context"]["business_rules"], fetched["business_rules"])
            self.assertNotIn("experience", payload["fetched_context"])
            self.assertEqual(payload["bytes"]["total"], budget)

    def test_partial_retention_truncates_within_the_surviving_category(self) -> None:
        """AC2's "retains higher-relevance content first" applies within a
        single category too: a single-category payload truncated mid-content
        keeps exactly the leading bytes that fit, not a dropped category."""
        with TemporaryDirectory() as tmp:
            hints = "- **Error map rows:** [Create session, Validate input]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            unbudgeted = sc.assemble(story)
            full_content = unbudgeted["fetched_context"]["error_map_rows"]
            budget = unbudgeted["bytes"]["total"] - 10

            payload = sc.assemble(story, budget_bytes=budget)
            self.assertTrue(payload["truncated"])
            kept = payload["fetched_context"]["error_map_rows"]
            self.assertTrue(full_content.startswith(kept))
            self.assertLessEqual(len(kept.encode("utf-8")), budget)
            self.assertEqual(payload["bytes"]["error_map_rows"], len(kept.encode("utf-8")))

    def test_truncation_boundary_splitting_a_multibyte_char_drops_category_entirely(self) -> None:
        """`enforce_budget()`'s truncation branch decodes `encoded[:remaining]`
        with `errors="ignore"` (module docstring: "a trailing partial
        multi-byte character is dropped rather than emitting invalid UTF-8").
        When the *entire* remaining allowance falls inside one multi-byte
        character at the very start of a category's content, that decode
        yields "" — a distinct outcome from the `remaining <= 0` skip just
        above it in the loop: here `remaining` is genuinely positive (2) when
        the category is considered, but the category still contributes
        nothing to `kept_fetched`/`kept_bytes` because no whole character
        survives the cut. Exercised directly against `enforce_budget()`
        (like the other pure-function tests in this file) since crafting a
        real story/spec fixture that lands a markdown-derived byte offset
        exactly mid-emoji is needlessly fragile for what is a `enforce_budget`-
        local concern.
        """
        # U+1F386 (🎆) is 4 bytes in UTF-8; a 2-byte prefix is an incomplete
        # sequence with zero decodable characters.
        content = "\U0001F386fireworks"
        fetched = {"error_map_rows": content}
        byte_counts = {"error_map_rows": len(content.encode("utf-8"))}

        kept_fetched, kept_bytes, truncated = sc.enforce_budget(fetched, byte_counts, 2)

        self.assertTrue(truncated)
        self.assertNotIn("error_map_rows", kept_fetched)
        self.assertNotIn("error_map_rows", kept_bytes)
        self.assertEqual(kept_fetched, {})
        self.assertEqual(kept_bytes, {})

    def test_zero_budget_drops_all_categories(self) -> None:
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            payload = sc.assemble(story, budget_bytes=0)
            self.assertTrue(payload["truncated"])
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(payload["bytes"]["total"], 0)

    def test_repeated_runs_with_budget_are_byte_identical(self) -> None:
        """AC5 / Business Rule 5 — determinism holds under enforcement too."""
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            unbudgeted = sc.assemble(story)
            budget = unbudgeted["bytes"]["total"] // 2

            first = json.dumps(sc.assemble(story, budget_bytes=budget))
            second = json.dumps(sc.assemble(story, budget_bytes=budget))
            self.assertEqual(first, second)

    def test_under_budget_is_never_truncated(self) -> None:
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            unbudgeted = sc.assemble(story)
            payload = sc.assemble(story, budget_bytes=unbudgeted["bytes"]["total"] + 1000)
            self.assertFalse(payload["truncated"])
            self.assertEqual(payload["fetched_context"], unbudgeted["fetched_context"])

    def test_budget_bytes_argument_is_inert_on_every_early_return_path(self) -> None:
        """`assemble()`'s four early-return branches (story unreadable,
        no hints section, no category_data survives filtering, spec.md
        absent) each call `_payload()` without forwarding `budget_bytes` —
        `fetched`/`byte_counts` are always `{}` at those points, so
        `enforce_budget()` would be a no-op even if it were invoked
        (0 <= any non-negative budget). Pinned here so a future refactor
        that starts forwarding `budget_bytes` into these branches can't
        silently change behavior on an empty payload without a test
        noticing."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_hints_story = make_spec_tree(root, spec_id="s-no-hints", hints=None)
            payload = sc.assemble(no_hints_story, budget_bytes=5)
            self.assertFalse(payload["truncated"])
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(payload["bytes"], {"total": 0})

            no_spec_story = make_spec_tree(
                root, spec_id="s-no-spec", spec_md=None,
                hints="- **Error map rows:** [Create session]\n",
            )
            payload = sc.assemble(no_spec_story, budget_bytes=5)
            self.assertFalse(payload["truncated"])
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(payload["bytes"], {"total": 0})

    def test_no_budget_argument_never_truncates(self) -> None:
        """Backward-compatible default: omitting --budget-bytes entirely
        (budget_bytes=None) still means unbounded, matching Story 2 behavior
        for any caller that doesn't yet pass the flag (Story 4's job)."""
        with TemporaryDirectory() as tmp:
            story = self._four_category_story(tmp)
            payload = sc.assemble(story, budget_bytes=None)
            self.assertFalse(payload["truncated"])


class CliTests(unittest.TestCase):
    def _run(self, *args: str) -> tuple[int, dict]:
        proc = subprocess.run(
            [sys.executable, str(MODULE_PATH), *args],
            capture_output=True,
            text=True,
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {"_raw": proc.stdout, "_err": proc.stderr}
        return proc.returncode, payload

    def test_assemble_happy_path_exits_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = "- **Business rules:** [One implementation per contract]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            code, payload = self._run("assemble", "--story", str(story))
            self.assertEqual(code, 0)
            self.assertIn("business_rules", payload["fetched_context"])
            self.assertFalse(payload["truncated"])

    def test_assemble_missing_story_exits_zero_with_empty_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            code, payload = self._run("assemble", "--story", str(Path(tmp) / "ghost.md"))
            self.assertEqual(code, 0)
            self.assertEqual(payload["fetched_context"], {})

    def test_budget_bytes_flag_accepted(self) -> None:
        with TemporaryDirectory() as tmp:
            story = make_spec_tree(Path(tmp), hints=None)
            code, _payload = self._run("assemble", "--story", str(story), "--budget-bytes", "500")
            self.assertEqual(code, 0)

    def test_budget_bytes_flag_enforces_truncation_end_to_end(self) -> None:
        with TemporaryDirectory() as tmp:
            hints = "- **Business rules:** [One implementation per contract]\n"
            story = make_spec_tree(Path(tmp), technical_spec_md=DEFAULT_TECH_SPEC, hints=hints)
            code, payload = self._run("assemble", "--story", str(story), "--budget-bytes", "1")
            self.assertEqual(code, 0)
            self.assertTrue(payload["truncated"])
            self.assertEqual(payload["bytes"]["total"], 1)

    def test_missing_required_story_flag_is_usage_error(self) -> None:
        code, _payload = self._run("assemble")
        self.assertEqual(code, 2)

    def test_undecodable_bytes_never_raise_and_degrade_via_internal_error_branch(self) -> None:
        # Invalid UTF-8 raises UnicodeDecodeError from Path.read_text() *inside*
        # assemble() — a distinct failure from the OSError assemble() itself
        # catches (missing/unreadable file). It propagates out of assemble()
        # and must be caught by main()'s outer `except Exception`, which is a
        # separate degrade path from assemble()'s own — never letting the
        # process exit non-zero (Business Rule 1: never raise).
        with TemporaryDirectory() as tmp:
            story = Path(tmp) / "binary.md"
            story.write_bytes(b"\xff\xfe\x00\x01## Context for Agents\n[broken\x80")
            code, payload = self._run("assemble", "--story", str(story))
            self.assertEqual(code, 0)
            self.assertEqual(payload["fetched_context"], {})
            self.assertEqual(payload["bytes"], {"total": 0})
            self.assertFalse(payload["truncated"])
            self.assertEqual(len(payload["warnings"]), 1)
            self.assertIn("story-context.py internal error", payload["warnings"][0])


if __name__ == "__main__":
    unittest.main()
