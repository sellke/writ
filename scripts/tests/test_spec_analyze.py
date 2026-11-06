#!/usr/bin/env python3
"""Tests for scripts/spec-analyze.py (Story 1 of
`2026-09-08-phase11-stage3-spec-analysis`). [AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "spec-analyze.py"

CLEAN_STORY = """# Story 1

## Acceptance Criteria

- [ ] Given a user, when they save, then `foo.py` exists `[AC-1.1]`
- [ ] Given a user, when they test, then 3 tests pass `[AC-1.2]`
- [ ] Given a user, when they ship, then the verdict is pass `[AC-1.3]`
"""


def _write_spec(root: Path, stories: dict[str, str]) -> Path:
    stories_dir = root / "user-stories"
    stories_dir.mkdir(parents=True)
    for name, text in stories.items():
        (stories_dir / name).write_text(text, encoding="utf-8")
    return root


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _verdict(out: str) -> str:
    for line in out.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return out.strip()


def _reasons(out: str) -> list[str]:
    return [ln[8:] for ln in out.splitlines() if ln.startswith("reason: ")]


def _banned_verdicts(out: str) -> None:
    for word in ("accept", "reject", "modify-spec"):
        assert word not in out.splitlines()[0] if out.splitlines() else True


class SpecAnalyzeTests(unittest.TestCase):
    def test_pass_clean_with_empty_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-clean.md": CLEAN_STORY})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            self.assertTrue(out.strip().splitlines()[-1].startswith("spec-analyze:"))
            for banned in ("accept", "reject", "modify-spec"):
                self.assertNotIn(banned, out)

    def test_fail_empty_criterion(self) -> None:
        text = CLEAN_STORY.replace(
            "- [ ] Given a user, when they save, then `foo.py` exists `[AC-1.1]`",
            "- [ ] Given",
        )
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-empty.md": text})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("empty_criterion", _reasons(out))

    def test_fail_unmeasurable_criterion(self) -> None:
        text = CLEAN_STORY.replace(
            "then `foo.py` exists `[AC-1.1]`",
            "then it works correctly `[AC-1.1]`",
        )
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-vague.md": text})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("unmeasurable_criterion", _reasons(out))

    def test_clean_fixture_does_not_trip_unmeasurable(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-clean.md": CLEAN_STORY})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            _code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertNotIn("unmeasurable_criterion", _reasons(out))
            self.assertEqual(_verdict(out), "pass")

    def test_fail_under_min_criteria(self) -> None:
        text = """# Story 1

## Acceptance Criteria

- [ ] Given a user, when they save, then `foo.py` exists `[AC-1.1]`
- [ ] Given a user, when they test, then 3 tests pass `[AC-1.2]`
"""
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-short.md": text})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("under_min_criteria", _reasons(out))

    def test_fail_malformed_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-clean.md": CLEAN_STORY})
            findings = spec / "findings.json"
            findings.write_text(json.dumps([{"code": "nope", "story": "spec", "summary": "x"}]),
                                encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("malformed_findings", _reasons(out))

    def test_empty_findings_array_is_well_formed(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-clean.md": CLEAN_STORY})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)

    def test_unverifiable_missing_spec(self) -> None:
        code, out, _err = _run(["check"])
        self.assertEqual(_verdict(out), "unverifiable")
        self.assertEqual(code, 0)

    def test_unverifiable_unreadable_spec(self) -> None:
        code, out, _err = _run(["check", "--spec", "/no/such/spec-folder"])
        self.assertEqual(_verdict(out), "unverifiable")
        self.assertEqual(code, 0)

    def test_unverifiable_no_findings_no_structural(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-clean.md": CLEAN_STORY})
            code, out, _err = _run(["check", "--spec", str(spec)])
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertEqual(code, 0)

    def test_usage_unknown_subcommand_exits_2(self) -> None:
        code, _out, err = _run(["nope"])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_project_alias_of_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {"story-1-clean.md": CLEAN_STORY})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(
                ["check", "--spec", str(spec), "--findings", str(findings), "--project", str(tmp)]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)

    def test_no_ac_trace_or_llm_import(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        joined = " ".join(imported)
        self.assertNotIn("ac-trace", joined)
        self.assertNotIn("ac_trace", joined)
        self.assertNotIn("anthropic", joined)
        self.assertNotIn("openai", joined)

    def test_create_spec_not_edited_by_story_1_contract(self) -> None:
        # Story 1 must not be the story that adds Step 2.6c — that's Story 2.
        # This test only documents the exclusive file; it does not grep the
        # live command (Story 2 will add the step).
        self.assertTrue(SCRIPT.exists())


def _planned_story(tasks: str = "", notes: str = "", built: str = "") -> str:
    """CLEAN_STORY plus Implementation Tasks, Notes, and an optional What Was
    Built record."""
    text = CLEAN_STORY + "\n## Implementation Tasks\n\n- [ ] 1.1 Write the tests `[AC-1.1]`\n"
    text += tasks + "\n## Notes\n\n- **Scope.** One command file.\n" + notes
    if built:
        text += "\n## What Was Built\n\n" + built
    return text


class PlannedRedWindowTests(unittest.TestCase):
    """Phase 15 retro F3: the why-command spec planned two commits that
    failed `gen-platform-trees.py --check` until Story 2. A story that plans
    a check to fail or go stale until a later story fails the analysis."""

    WINDOWS = (
        ("story-1-x.md", _planned_story(tasks=(
            "- [ ] 1.7 Verify. Expect `check_manifest` to report `commands/why.md` "
            "unregistered and `gen-platform-trees.py --check` to report the plugin "
            "trees stale until Story 2; every other check passes `[AC-1.1]`\n"))),
        ("story-1-x.md", _planned_story(notes=(
            "- **Known window.** Between this story and Story 2, `check_manifest` "
            "and the generated-tree check fail. Story 2 clears both.\n"))),
        ("story-2-x.md", _planned_story(notes=(
            "- Against the committed tree, `--check` fails for the seven files\n"
            "  until Story 3 runs.\n"))),
    )

    def _check(self, name: str, text: str) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            spec = _write_spec(Path(tmp), {name: text})
            findings = spec / "findings.json"
            findings.write_text("[]", encoding="utf-8")
            code, out, _err = _run(["check", "--spec", str(spec), "--findings", str(findings)])
            return code, out

    def test_planned_red_window_fails(self) -> None:
        """Mutation: each window fails; the same story with the window
        sentence replaced by an all-green plan passes."""
        for name, text in self.WINDOWS:
            with self.subTest(name=name, text=text):
                code, out = self._check(name, text)
                self.assertEqual(_verdict(out), "fail", out)
                self.assertEqual(code, 1)
                self.assertEqual(_reasons(out), ["planned_red_window"])
                self.assertTrue(out.strip().splitlines()[-1].startswith("spec-analyze: fail"))
        code, out = self._check("story-1-x.md", _planned_story(tasks=(
            "- [ ] 1.7 Verify. Register the command in this story; every check "
            "passes `[AC-1.1]`\n")))
        self.assertEqual(_verdict(out), "pass", out)
        self.assertEqual(code, 0)

    def test_ordinary_story_references_pass(self) -> None:
        """Not a window: a later story named without a failing check, a
        failing check that waits on an earlier story (a dependency), an
        ordering note, and a record of what happened."""
        cases = (
            ("story-1-x.md", _planned_story(notes=(
                "- **Stale Claude Code row.** Until Story 2 changes the row, Step 4 "
                "takes the file-write branch.\n"))),
            ("story-2-x.md", _planned_story(notes=(
                "- **Story 1 must exist first.** `eval.sh` fails until Story 1 "
                "lands the script.\n"))),
            ("story-1-x.md", _planned_story(notes=(
                "- **Order matters.** Delete the files before Story 2, or the "
                "governor test would fail.\n"))),
            ("story-1-x.md", _planned_story(notes=(
                "- Until Story 2 lands, the lint must warn, not fail, or the gate "
                "breaks between stories.\n"))),
            ("story-1-x.md", _planned_story(built=(
                "- Bash tests: 1 FAIL, same orphan finding, stale until Story 2.\n"))),
        )
        for name, text in cases:
            with self.subTest(name=name, text=text):
                code, out = self._check(name, text)
                self.assertEqual(_verdict(out), "pass", out)
                self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
