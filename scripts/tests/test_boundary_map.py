#!/usr/bin/env python3
"""Tests for scripts/boundary-map.py (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Overlap-present vs overlap-absent JSON maps; malformed story → exit 1;
usage → exit 2. [AC-4.1, AC-4.2, AC-4.4, AC-4.5]

`crossings` (Story 1 of `2026-09-26-drift-arch-guards`): owned-only pass,
crossing classes in input order, pipeline-output exclusion, full-stack
routing, unreadable map, usage. [AC-1.1, AC-1.2, AC-1.3, AC-1.4]
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "boundary-map.py"

WELL_FORMED_STORY = """# Story 1: Fixture

> **Status:** Not Started

## User Story

Fixture.

## Acceptance Criteria

- [ ] Given `AC-4.1`, when it runs, then it passes

## Implementation Tasks

- [ ] 1.1 Create `src/auth/login.ts`
- [ ] 1.2 Modify `src/auth/session.ts`
- [ ] 1.3 Add to `src/lib/utils.ts`
- [ ] 1.4 Update `src/auth/login.test.ts`

## Notes

Ignore `src/other/out-of-scope.ts` here.
"""

OVERLAP_TABLE = """## Check 5 — File overlap

| File / area | Stories sharing | Severity (note / warn) |
|-------------|-----------------|-------------------------|
| `src/lib/utils.ts` | 1, 2, 3 | warn |
| `src/shared/types.ts` | 1, 2 | note |
"""


def _run(args, cwd=None):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _payload(stdout):
    return json.loads(stdout)


class BoundaryMapTests(unittest.TestCase):
    def test_overlap_absent_owned_only(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            code, out, err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0, err)
            payload = _payload(out)
            self.assertEqual(
                set(payload.keys()),
                {"owned", "readable", "out_of_scope"},
            )
            self.assertEqual(
                payload["owned"],
                [
                    "src/auth/login.ts",
                    "src/auth/session.ts",
                    "src/lib/utils.ts",
                    "src/auth/login.test.ts",
                ],
            )
            self.assertEqual(payload["readable"], [])
            self.assertEqual(payload["out_of_scope"], [])
            self.assertNotIn("src/other/out-of-scope.ts", payload["owned"])

    def test_overlap_present_merges_shared_unread_paths(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            overlap = root / "assessment-report.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            overlap.write_text(OVERLAP_TABLE, encoding="utf-8")
            code, out, err = _run(
                [
                    "compute",
                    "--story",
                    str(story),
                    "--repo",
                    str(root),
                    "--overlap",
                    str(overlap),
                ],
            )
            self.assertEqual(code, 0, err)
            payload = _payload(out)
            self.assertIn("src/lib/utils.ts", payload["owned"])
            self.assertNotIn("src/lib/utils.ts", payload["readable"])
            self.assertEqual(payload["readable"], ["src/shared/types.ts"])
            self.assertEqual(payload["out_of_scope"], [])

    def test_malformed_story_missing_tasks_exits_1(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text("# Story\n\nNo tasks.\n", encoding="utf-8")
            code, out, _err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 1)
            self.assertEqual(out.strip(), "")

    def test_malformed_empty_story_exits_1(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text("", encoding="utf-8")
            code, _out, _err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 1)

    def test_missing_story_file_exits_1(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, _out, _err = _run(
                [
                    "compute",
                    "--story",
                    str(root / "missing.md"),
                    "--repo",
                    str(root),
                ],
            )
            self.assertEqual(code, 1)

    def test_usage_missing_flags_exits_2(self):
        code, _out, _err = _run(["compute"])
        self.assertEqual(code, 2)

    def test_usage_missing_subcommand_exits_2(self):
        code, _out, _err = _run([])
        self.assertEqual(code, 2)

    def test_missing_overlap_file_exits_2_with_error_naming_path(self):
        """UAT Scenario 22: a bad --overlap is a usage error, not silent."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            missing = root / "no-such-overlap.md"
            code, out, err = _run(
                [
                    "compute", "--story", str(story), "--repo", str(root),
                    "--overlap", str(missing),
                ],
            )
            self.assertEqual(code, 2)
            self.assertEqual(out, "")
            self.assertIn("error: overlap file is not readable", err)
            self.assertIn(str(missing), err)

    def test_writes_nothing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            before = {p.relative_to(root) for p in root.rglob("*")}
            code, _out, _err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0)
            after = {p.relative_to(root) for p in root.rglob("*")}
            self.assertEqual(before, after)


DOTTED_STORY = """# Story 1: Dots

> **Status:** Not Started

## Implementation Tasks

- [ ] 1.1 Append to `.writ/decision-log.md`
- [ ] 1.2 Edit `scripts/eval.sh` lines `70/219/231`
- [ ] 1.3 Update `.github/workflows/ci.yml`
- [ ] 1.4 Do not change how `/implement-story` or `/revert` spawn agents
- [ ] 1.5 Drop the lines at `adapters/cursor.md:50\u201355` and `agents/x.md:12`
- [ ] 1.6 Write `scripts/tests/test_gate_replay.py`; run `test_gate_replay.py` later
- [ ] 1.7 Ignore `85/70`, `{date} stage-2b: x`, `/abs/tool`, and `a/b|c`
- [ ] 1.8 Also `./src/app.py` and a lone `README.md`
"""


class PathPlausibilityTests(unittest.TestCase):
    """UAT Scenario 26 / Honest Note 4: the map names real-looking repo paths."""

    def _owned(self, text):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(text, encoding="utf-8")
            code, out, err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0, err)
            return _payload(out)["owned"]

    def test_leading_dots_are_kept(self):
        owned = self._owned(DOTTED_STORY)
        self.assertIn(".writ/decision-log.md", owned)
        self.assertIn(".github/workflows/ci.yml", owned)
        self.assertNotIn("writ/decision-log.md", owned)
        self.assertNotIn("github/workflows/ci.yml", owned)

    def test_non_path_tokens_are_dropped(self):
        owned = self._owned(DOTTED_STORY)
        for bad in ("70/219/231", "85/70", "/implement-story", "/revert", "/abs/tool", "a/b|c"):
            self.assertNotIn(bad, owned)
        self.assertFalse(any("{" in p or " " in p for p in owned), owned)

    def test_line_suffixes_are_stripped(self):
        owned = self._owned(DOTTED_STORY)
        self.assertIn("adapters/cursor.md", owned)
        self.assertIn("agents/x.md", owned)
        self.assertFalse(any(":" in p for p in owned), owned)

    def test_bare_filename_duplicating_a_full_path_is_dropped(self):
        owned = self._owned(DOTTED_STORY)
        self.assertIn("scripts/tests/test_gate_replay.py", owned)
        self.assertNotIn("test_gate_replay.py", owned)
        self.assertIn("README.md", owned)

    def test_dot_slash_prefix_is_normalized(self):
        owned = self._owned(DOTTED_STORY)
        self.assertIn("src/app.py", owned)
        self.assertNotIn("./src/app.py", owned)

    def test_spec_relative_path_resolves_to_repo_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / ".writ" / "specs" / "demo"
            (spec / "sub-specs").mkdir(parents=True)
            (spec / "user-stories").mkdir()
            (spec / "sub-specs" / "technical-spec.md").write_text("x", encoding="utf-8")
            story = spec / "user-stories" / "story-1.md"
            story.write_text(
                "# Story 1\n\n## Implementation Tasks\n\n"
                "- [ ] 1.1 Follow `sub-specs/technical-spec.md` and edit `src/new.py`\n",
                encoding="utf-8",
            )
            code, out, err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                _payload(out)["owned"],
                [".writ/specs/demo/sub-specs/technical-spec.md", "src/new.py"],
            )

    def test_symbol_suffix_and_unique_bare_filename_resolve(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / ".writ" / "specs" / "demo"
            (spec / "user-stories").mkdir(parents=True)
            (root / "scripts" / "tests").mkdir(parents=True)
            for rel in ("scripts/phase-state.py", "scripts/tests/test_eval_x.sh",
                        "a/dup.md", "b/dup.md"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("x", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            story = spec / "user-stories" / "story-1.md"
            story.write_text(
                "# Story 1\n\n## Implementation Tasks\n\n"
                "- [ ] 1.1 Edit `scripts/phase-state.py::knowledge_writeback`, "
                "mirror `test_eval_x.sh`, read `dup.md`, create `brand_new.py`\n",
                encoding="utf-8",
            )
            code, out, err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                _payload(out)["owned"],
                ["scripts/phase-state.py", "scripts/tests/test_eval_x.sh",
                 "dup.md", "brand_new.py"],
            )

    def test_exact_owned_list(self):
        self.assertEqual(
            self._owned(DOTTED_STORY),
            [
                ".writ/decision-log.md",
                "scripts/eval.sh",
                ".github/workflows/ci.yml",
                "adapters/cursor.md",
                "agents/x.md",
                "scripts/tests/test_gate_replay.py",
                "src/app.py",
                "README.md",
            ],
        )


MAP = {
    "owned": ["scripts/boundary-map.py", "src/auth/", "src/lib"],
    "readable": ["src/shared/types.ts"],
    "out_of_scope": ["src/legacy/"],
}


def _lines(stdout):
    return stdout.strip().splitlines()


def _reasons(stdout):
    return [line[len("reason: "):] for line in _lines(stdout) if line.startswith("reason: ")]


class CrossingsTests(unittest.TestCase):
    """Story 1 of `2026-09-26-drift-arch-guards` — `crossings` routing signal."""

    def _crossings(self, changed, payload=MAP, extra=(), map_text=None):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            boundary = root / "boundary.json"
            boundary.write_text(
                map_text if map_text is not None else json.dumps(payload),
                encoding="utf-8",
            )
            args = ["crossings", "--map", str(boundary), "--repo", str(root)]
            if changed is not None:
                args += ["--changed", *[c.replace("{root}", str(root)) for c in changed]]
            args += [e.replace("{root}", str(root)) for e in extra]
            return _run(args)

    # AC-1.1

    def test_owned_only_passes_and_routes_evaluator(self):
        code, out, err = self._crossings(
            ["scripts/boundary-map.py", "src/auth/login.ts", "src/lib/utils.ts"],
        )
        self.assertEqual(code, 0, err)
        lines = _lines(out)
        self.assertEqual(lines[0], "pass")
        self.assertEqual(lines[1], "route: evaluator-agent")
        self.assertEqual(_reasons(out), [])
        self.assertTrue(lines[-1].startswith("boundary-map crossings: 0 crossing(s)"), lines[-1])
        self.assertIn("(route evaluator-agent)", lines[-1])

    def test_directory_entry_covers_nested_but_not_sibling_prefix(self):
        code, out, _err = self._crossings(["src/lib/deep/x.py", "src/library.py"])
        self.assertEqual(code, 0)
        self.assertEqual(_reasons(out), ["outside_boundary src/library.py"])

    # AC-1.2

    def test_each_crossing_class_in_input_order(self):
        code, out, err = self._crossings(
            [
                "scripts/x.py",
                "src/shared/types.ts",
                "src/auth/login.ts",
                "src/legacy/old.py",
            ],
        )
        self.assertEqual(code, 0, err)
        lines = _lines(out)
        self.assertEqual(lines[0], "pass")
        self.assertEqual(lines[1], "route: review-agent")
        self.assertEqual(
            _reasons(out),
            [
                "outside_boundary scripts/x.py",
                "readable_modified src/shared/types.ts",
                "out_of_scope src/legacy/old.py",
            ],
        )
        self.assertTrue(lines[-1].startswith("boundary-map crossings: 3 crossing(s)"), lines[-1])
        self.assertIn("(route review-agent)", lines[-1])

    def test_out_of_scope_outranks_readable(self):
        payload = {"owned": [], "readable": ["src/"], "out_of_scope": ["src/legacy"]}
        code, out, _err = self._crossings(["src/legacy/a.py", "src/b.py"], payload=payload)
        self.assertEqual(code, 0)
        self.assertEqual(
            _reasons(out),
            ["out_of_scope src/legacy/a.py", "readable_modified src/b.py"],
        )

    def test_paths_normalize_repo_relative(self):
        code, out, err = self._crossings(
            [
                "{root}/src/auth/login.ts",
                "./src/lib/utils.ts",
                "{root}/scripts/new.py",
                "./.github/workflows/ci.yml",
                ".writ/decision-log.md",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(
            _reasons(out),
            [
                "outside_boundary scripts/new.py",
                "outside_boundary .github/workflows/ci.yml",
                "outside_boundary .writ/decision-log.md",
            ],
        )

    def test_empty_map_lists_make_every_file_a_crossing(self):
        payload = {"owned": [], "readable": [], "out_of_scope": []}
        code, out, _err = self._crossings(["a.py", "b/c.py"], payload=payload)
        self.assertEqual(code, 0)
        self.assertEqual(_reasons(out), ["outside_boundary a.py", "outside_boundary b/c.py"])

    # AC-1.3

    def test_pipeline_outputs_excluded_without_story(self):
        code, out, _err = self._crossings(
            [".writ/context.md", ".writ/state/boundary-story-1.json", ".writ/contextual.md"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(_reasons(out), ["outside_boundary .writ/contextual.md"])

    def test_story_spec_folder_excluded_with_story(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / ".writ" / "specs" / "demo"
            (spec / "user-stories").mkdir(parents=True)
            story = spec / "user-stories" / "story-1.md"
            story.write_text("# Story 1\n", encoding="utf-8")
            boundary = root / "boundary.json"
            boundary.write_text(json.dumps(MAP), encoding="utf-8")
            code, out, err = _run(
                [
                    "crossings", "--map", str(boundary), "--repo", str(root),
                    "--story", str(story),
                    "--changed",
                    ".writ/specs/demo/user-stories/story-1.md",
                    ".writ/specs/demo/drift-log.md",
                    ".writ/specs/other/spec.md",
                    ".writ/state/x.json",
                ],
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(_reasons(out), ["outside_boundary .writ/specs/other/spec.md"])

    def test_spec_folder_not_excluded_without_story(self):
        code, out, _err = self._crossings([".writ/specs/demo/drift-log.md"])
        self.assertEqual(code, 0)
        self.assertEqual(_reasons(out), ["outside_boundary .writ/specs/demo/drift-log.md"])

    def test_full_stack_routes_review_with_reason_last(self):
        code, out, err = self._crossings(
            ["scripts/x.py", "src/auth/login.ts"], extra=["--surface", "full-stack"],
        )
        self.assertEqual(code, 0, err)
        lines = _lines(out)
        self.assertEqual(lines[0], "pass")
        self.assertEqual(lines[1], "route: review-agent")
        self.assertEqual(_reasons(out), ["outside_boundary scripts/x.py", "full_stack_surface"])
        self.assertEqual(
            lines[-1],
            "boundary-map crossings: 1 crossing(s), surface full-stack (route review-agent)",
        )

    def test_full_stack_alone_routes_review(self):
        code, out, _err = self._crossings(
            ["src/auth/login.ts"], extra=["--surface", "full-stack"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(_lines(out)[1], "route: review-agent")
        self.assertEqual(_reasons(out), ["full_stack_surface"])

    def test_other_surface_does_not_route_review(self):
        code, out, _err = self._crossings(
            ["src/auth/login.ts"], extra=["--surface", "cross-component"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(_lines(out)[1], "route: evaluator-agent")
        self.assertEqual(
            _lines(out)[-1],
            "boundary-map crossings: 0 crossing(s), surface cross-component (route evaluator-agent)",
        )

    # AC-1.4

    def _assert_unverifiable(self, code, out, err):
        self.assertEqual(code, 0, err)
        lines = _lines(out)
        self.assertEqual(lines[0], "unverifiable")
        self.assertEqual(lines[1], "route: review-agent")
        self.assertEqual(_reasons(out), ["map_unreadable"])
        self.assertTrue(lines[-1].startswith("boundary-map crossings:"), lines[-1])

    def test_missing_map_is_unverifiable(self):
        with TemporaryDirectory() as tmp:
            code, out, err = _run(
                ["crossings", "--map", str(Path(tmp) / "none.json"), "--repo", tmp,
                 "--changed", "a.py"],
            )
            self._assert_unverifiable(code, out, err)

    def test_map_directory_is_unverifiable(self):
        with TemporaryDirectory() as tmp:
            code, out, err = _run(
                ["crossings", "--map", tmp, "--repo", tmp, "--changed", "a.py"],
            )
            self._assert_unverifiable(code, out, err)

    def test_invalid_json_map_is_unverifiable(self):
        self._assert_unverifiable(*self._crossings(["a.py"], map_text="{not json"))

    def test_non_object_map_is_unverifiable(self):
        self._assert_unverifiable(*self._crossings(["a.py"], map_text='["a.py"]'))

    def test_non_list_entry_is_unverifiable(self):
        self._assert_unverifiable(*self._crossings(["a.py"], map_text='{"owned": "a.py"}'))

    def test_changed_omitted_exits_2(self):
        code, out, _err = self._crossings(None)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_changed_empty_exits_2(self):
        code, out, _err = self._crossings([])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_changed_blank_values_exit_2(self):
        code, out, _err = self._crossings(["", "  "])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_compute_unchanged_by_crossings(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            code, out, err = _run(["compute", "--story", str(story), "--repo", str(root)])
            self.assertEqual(code, 0, err)
            self.assertEqual(
                set(_payload(out)), {"owned", "readable", "out_of_scope"},
            )


class Gate05WiringTests(unittest.TestCase):
    """AC-4.4 / AC-4.5 — Gate 0.5 runs the script; maps stay advisory."""

    def test_gate_0_5_invokes_compute_and_stays_advisory(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 0.5: Boundary Computation")
        end = text.index("#### Gate 1:", start)
        gate = text[start:end]
        self.assertIn("scripts/boundary-map.py compute", gate)
        self.assertIn("advisory", gate.lower())
        self.assertIn("no hard file locking", gate)

    def test_frontmatter_names_boundary_map(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate0_5_boundary\n    script: scripts/boundary-map.py", text)


if __name__ == "__main__":
    unittest.main()
