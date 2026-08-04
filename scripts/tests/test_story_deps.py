#!/usr/bin/env python3
"""Unit tests for scripts/story-deps.py.

Each test builds a disposable spec folder with real `user-stories/story-*.md`
files in a temp directory so the validator runs against the same shape it
will see in production: absent headers (legacy), the five blocking error
classes (`malformed_dependencies`, `missing_reference`, `self_reference`,
`duplicate_reference`, `dependency_cycle`), deterministic batch ordering with
a numeric story-number tie-break, and byte-identical repeat runs. The module
filename contains a hyphen, so it is imported by path — the exact recipe
`test_revert_resolve.py` uses.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

MODULE_PATH = Path(__file__).resolve().parent.parent / "story-deps.py"
_spec = importlib.util.spec_from_file_location("story_deps", MODULE_PATH)
sd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sd)  # type: ignore[union-attr]


def make_story(root: Path, number: int, title: str, dependencies: str | None) -> Path:
    """Write one story file under root/user-stories/, mirroring the real
    story-file shape: an H1, an optional Dependencies header, and a body.
    Passing dependencies=None omits the header entirely (legacy)."""
    folder = root / "user-stories"
    folder.mkdir(parents=True, exist_ok=True)
    lines = [f"# Story {number}: {title}", ""]
    if dependencies is not None:
        lines.append(f"> **Dependencies:** {dependencies}")
    lines += ["", "## User Story", "", "Body."]
    slug = title.lower().replace(" ", "-")
    path = folder / f"story-{number}-{slug}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_cli(*args: str) -> tuple[int, dict]:
    buf = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(buf):
            sd.main(list(args))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    try:
        payload = json.loads(buf.getvalue())
    except json.JSONDecodeError:
        payload = {"_raw": buf.getvalue()}
    return code, payload


class ParseDependenciesTests(unittest.TestCase):
    def test_absent_header_is_legacy_empty(self) -> None:
        self.assertEqual(sd.parse_dependencies("# Story 1: X\n\nBody.\n", "story-1"), [])

    def test_none_case_insensitive_is_empty(self) -> None:
        text = "# Story 1: X\n\n> **Dependencies:** NoNe\n\nBody.\n"
        self.assertEqual(sd.parse_dependencies(text, "story-1"), [])

    def test_single_dependency_parsed(self) -> None:
        text = "> **Dependencies:** Story 2\n"
        self.assertEqual(sd.parse_dependencies(text, "story-1"), ["story-2"])

    def test_comma_separated_list_preserves_order(self) -> None:
        text = "> **Dependencies:** Story 3, Story 2\n"
        self.assertEqual(sd.parse_dependencies(text, "story-1"), ["story-3", "story-2"])

    def test_story_dash_number_form_accepted(self) -> None:
        text = "> **Dependencies:** story-2\n"
        self.assertEqual(sd.parse_dependencies(text, "story-1"), ["story-2"])

    def test_malformed_value_raises(self) -> None:
        text = "> **Dependencies:** Story ???\n"
        with self.assertRaises(sd.ContractError) as ctx:
            sd.parse_dependencies(text, "story-1")
        self.assertEqual(ctx.exception.code, "malformed_dependencies")
        self.assertIn("story-1", ctx.exception.summary)

    def test_malformed_trailing_comma_raises(self) -> None:
        text = "> **Dependencies:** Story 2,\n"
        with self.assertRaises(sd.ContractError) as ctx:
            sd.parse_dependencies(text, "story-1")
        self.assertEqual(ctx.exception.code, "malformed_dependencies")

    def test_prose_mentioning_dependencies_not_conflated(self) -> None:
        # A body sentence that merely mentions "Dependencies:" without the
        # exact `> **Dependencies:**` header form must not match.
        text = "# Story 1\n\nDependencies: Story 2 in prose, not the header.\n"
        self.assertEqual(sd.parse_dependencies(text, "story-1"), [])

    # Real-world prose observed dogfooding across .writ/specs/ — plural
    # prefixes, parenthetical annotations, "and" separators, dash ranges,
    # and annotated None all appear in existing story files and must parse,
    # not just the minimal "Story N" form.

    def test_plural_prefix_comma_list(self) -> None:
        text = "> **Dependencies:** Stories 2, 3, 4\n"
        self.assertEqual(
            sd.parse_dependencies(text, "story-1"), ["story-2", "story-3", "story-4"]
        )

    def test_single_token_with_parenthetical_annotation(self) -> None:
        text = "> **Dependencies:** Story 1 (manifest schema)\n"
        self.assertEqual(sd.parse_dependencies(text, "story-3"), ["story-1"])

    def test_multiple_tokens_each_with_annotation(self) -> None:
        text = "> **Dependencies:** Story 1 (manifest schema), Story 2 (install fanout)\n"
        self.assertEqual(sd.parse_dependencies(text, "story-3"), ["story-1", "story-2"])

    def test_and_separator(self) -> None:
        text = "> **Dependencies:** Stories 1 and 2\n"
        self.assertEqual(sd.parse_dependencies(text, "story-3"), ["story-1", "story-2"])

    def test_dash_range(self) -> None:
        text = "> **Dependencies:** Stories 1-3\n"
        self.assertEqual(
            sd.parse_dependencies(text, "story-4"), ["story-1", "story-2", "story-3"]
        )

    def test_en_dash_range(self) -> None:
        text = "> **Dependencies:** Stories 1\u20133\n"
        self.assertEqual(
            sd.parse_dependencies(text, "story-4"), ["story-1", "story-2", "story-3"]
        )

    def test_inverted_range_is_malformed(self) -> None:
        text = "> **Dependencies:** Stories 3-1\n"
        with self.assertRaises(sd.ContractError) as ctx:
            sd.parse_dependencies(text, "story-4")
        self.assertEqual(ctx.exception.code, "malformed_dependencies")

    def test_annotated_none_is_still_empty(self) -> None:
        text = "> **Dependencies:** None (independent of Stories 1, 3)\n"
        self.assertEqual(sd.parse_dependencies(text, "story-2"), [])

    def test_none_within_this_spec_annotation(self) -> None:
        text = "> **Dependencies:** None (within this spec)\n"
        self.assertEqual(sd.parse_dependencies(text, "story-1"), [])

    def test_bare_number_without_prior_story_prefix_is_malformed(self) -> None:
        text = "> **Dependencies:** 1, 2\n"
        with self.assertRaises(sd.ContractError) as ctx:
            sd.parse_dependencies(text, "story-3")
        self.assertEqual(ctx.exception.code, "malformed_dependencies")


class StoryIdentifierTests(unittest.TestCase):
    def test_story_number_rejects_unparseable_id(self) -> None:
        with self.assertRaises(sd.ContractError) as ctx:
            sd.story_number("not-a-story")
        self.assertEqual(ctx.exception.code, "malformed_dependencies")

    def test_story_id_from_path_rejects_non_numeric_filename(self) -> None:
        with self.assertRaises(sd.ContractError) as ctx:
            sd.story_id_from_path(Path("story-x-alpha.md"))
        self.assertEqual(ctx.exception.code, "malformed_dependencies")
        self.assertIn("story-x-alpha.md", ctx.exception.summary)


class BuildGraphTests(unittest.TestCase):
    def test_no_stories_found_blocks(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "user-stories").mkdir(parents=True)
            with self.assertRaises(sd.ContractError) as ctx:
                sd.build_graph(root)
            self.assertEqual(ctx.exception.code, "no_stories_found")

    def test_unreadable_story_file_is_missing_reference(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "user-stories"
            folder.mkdir(parents=True)
            # A directory named like a story file is unreadable as text.
            (folder / "story-1-bad.md").mkdir()
            with self.assertRaises(sd.ContractError) as ctx:
                sd.build_graph(root)
            self.assertEqual(ctx.exception.code, "missing_reference")
            self.assertIn("story-1", ctx.exception.summary)

    def test_legacy_stories_have_no_dependencies(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_story(root, 1, "Alpha", None)
            make_story(root, 2, "Beta", None)
            graph = sd.build_graph(root)
            self.assertEqual(graph, {"story-1": [], "story-2": []})

    def test_duplicate_story_number_across_two_files_blocks(self) -> None:
        # A renumbering leftover: two files both resolve to story-1 (glob
        # sorts "alpha" before "beta", so "beta" is the file that collides).
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_story(root, 1, "Alpha", None)
            make_story(root, 1, "Beta", None)
            with self.assertRaises(sd.ContractError) as ctx:
                sd.build_graph(root)
            self.assertEqual(ctx.exception.code, "malformed_dependencies")
            self.assertIn("story-1", ctx.exception.summary)
            self.assertIn("story-1-beta.md", ctx.exception.summary)


class ValidateGraphErrorClassTests(unittest.TestCase):
    def test_malformed_dependencies_blocks(self) -> None:
        with self.assertRaises(sd.ContractError) as ctx:
            sd.parse_dependencies("> **Dependencies:** garbage\n", "story-1")
        self.assertEqual(ctx.exception.code, "malformed_dependencies")

    def test_missing_reference_blocks(self) -> None:
        graph = {"story-1": [], "story-2": ["story-9"]}
        with self.assertRaises(sd.ContractError) as ctx:
            sd.validate_graph(graph)
        self.assertEqual(ctx.exception.code, "missing_reference")
        self.assertIn("story-2", ctx.exception.summary)
        self.assertIn("story-9", ctx.exception.summary)

    def test_self_reference_blocks(self) -> None:
        graph = {"story-1": [], "story-2": ["story-2"]}
        with self.assertRaises(sd.ContractError) as ctx:
            sd.validate_graph(graph)
        self.assertEqual(ctx.exception.code, "self_reference")
        self.assertIn("story-2", ctx.exception.summary)

    def test_duplicate_reference_blocks(self) -> None:
        graph = {"story-1": [], "story-2": ["story-1", "story-1"]}
        with self.assertRaises(sd.ContractError) as ctx:
            sd.validate_graph(graph)
        self.assertEqual(ctx.exception.code, "duplicate_reference")
        self.assertIn("story-2", ctx.exception.summary)

    def test_two_story_cycle_blocks_with_path(self) -> None:
        graph = {"story-1": ["story-2"], "story-2": ["story-1"]}
        with self.assertRaises(sd.ContractError) as ctx:
            sd.validate_graph(graph)
        self.assertEqual(ctx.exception.code, "dependency_cycle")
        self.assertIn("->", ctx.exception.summary)
        self.assertIn("story-1", ctx.exception.summary)
        self.assertIn("story-2", ctx.exception.summary)

    def test_four_story_cycle_names_full_path(self) -> None:
        graph = {
            "story-1": [],
            "story-2": ["story-4"],
            "story-3": ["story-2"],
            "story-4": ["story-3"],
        }
        with self.assertRaises(sd.ContractError) as ctx:
            sd.validate_graph(graph)
        self.assertEqual(ctx.exception.code, "dependency_cycle")
        for story in ("story-2", "story-3", "story-4"):
            self.assertIn(story, ctx.exception.summary)


class DeterministicBatchTests(unittest.TestCase):
    def test_happy_path_batches_respect_dependencies(self) -> None:
        graph = {
            "story-1": [],
            "story-2": ["story-1"],
            "story-3": [],
            "story-4": ["story-3"],
            "story-5": ["story-2", "story-4"],
        }
        result = sd.validate_graph(graph)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["schema"], sd.SCHEMA)
        batches = result["batches"]
        self.assertEqual(batches[0], ["story-1", "story-3"])
        self.assertEqual(batches[1], ["story-2", "story-4"])
        self.assertEqual(batches[2], ["story-5"])

    def test_legacy_all_stories_batch_together(self) -> None:
        graph = {"story-1": [], "story-2": [], "story-3": []}
        result = sd.validate_graph(graph)
        self.assertEqual(result["batches"], [["story-1", "story-2", "story-3"]])

    def test_numeric_tiebreak_not_lexicographic(self) -> None:
        # story-10 and story-11 must sort after story-2 and story-9 by
        # numeric value, not lexicographically ("story-10" < "story-2" as
        # strings, but must come after it here).
        graph = {f"story-{n}": [] for n in range(1, 12)}
        result = sd.validate_graph(graph)
        self.assertEqual(
            result["batches"][0],
            [f"story-{n}" for n in range(1, 12)],
        )

    def test_numeric_tiebreak_within_dependent_batch(self) -> None:
        graph = {
            "story-1": [],
            "story-2": [],
            "story-10": ["story-1"],
            "story-9": ["story-2"],
        }
        result = sd.validate_graph(graph)
        self.assertEqual(result["batches"][0], ["story-1", "story-2"])
        # story-9 must sort before story-10 numerically, not lexicographically.
        self.assertEqual(result["batches"][1], ["story-9", "story-10"])

    def test_repeated_runs_are_byte_identical(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_story(root, 1, "Alpha", None)
            make_story(root, 2, "Beta", "Story 1")
            make_story(root, 3, "Gamma", "Story 1")
            first = json.dumps(sd.validate(root))
            second = json.dumps(sd.validate(root))
            self.assertEqual(first, second)


class CliTests(unittest.TestCase):
    def test_validate_happy_path_exits_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_story(root, 1, "Alpha", None)
            make_story(root, 2, "Beta", "Story 1")
            code, payload = run_cli("validate", "--spec-dir", str(root))
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["schema"], "story-graph/v1")
            self.assertEqual(payload["batches"], [["story-1"], ["story-2"]])

    def test_validate_blocker_exits_one(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_story(root, 1, "Alpha", "Story 1")
            code, payload = run_cli("validate", "--spec-dir", str(root))
            self.assertEqual(code, 1)
            self.assertEqual(payload["blocker"]["code"], "self_reference")

    def test_no_json_flag_exists(self) -> None:
        # Precedent (spec-deps.py) has no --json flag and always prints JSON
        # unconditionally; story-deps.py follows the same contract, so
        # passing --json is an argparse usage error (exit code 2), not a
        # recognized flag.
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_story(root, 1, "Alpha", None)
            code, _ = run_cli("validate", "--spec-dir", str(root), "--json")
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
