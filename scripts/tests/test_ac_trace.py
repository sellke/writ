#!/usr/bin/env python3
"""Unit tests for scripts/ac-trace.py (Story 2 of
`2026-08-13-acceptance-criteria-traceability-ids`).

Each test builds a disposable spec folder — and, where the citation scan is
under test, a disposable repo root — in a temp directory, exercising the
checker against the same shape it sees in production: one test per finding
code with severity asserted alongside detection, the two non-tag hazards
(a marker must not satisfy its own ID; an ID-shaped token quoted in
criterion prose must not be misread as a definition — Story 4's own
criteria are the regression fixture), the bare-token boundary decision,
determinism, and all three exit codes. The module filename contains a
hyphen, so it is imported by path — the recipe `test_story_deps.py` uses.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

MODULE_PATH = Path(__file__).resolve().parent.parent / "ac-trace.py"
_spec = importlib.util.spec_from_file_location("ac_trace", MODULE_PATH)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)  # type: ignore[union-attr]


# --- Fixture builders --------------------------------------------------------

def write_story(root: Path, number: int, *, status: str = "Not Started",
                 marker_lines: list[str] | None = None,
                 ac_lines: tuple[str, ...] = (),
                 task_lines: tuple[str, ...] = ()) -> Path:
    """Write one disposable `story-N-*.md` under `root/user-stories/`,
    mirroring the real shape: status header, marker line(s) (or none),
    checkbox criterion lines, checkbox task lines."""
    lines = [
        f"# Story {number}: Fixture",
        "",
        f"> **Status:** {status}",
        "> **Priority:** High",
        "> **Dependencies:** None",
        "",
        "## User Story",
        "",
        "Fixture body.",
        "",
        "## Acceptance Criteria",
        "",
    ]
    if marker_lines:
        lines.extend(marker_lines)
        lines.append("")
    lines.extend(ac_lines)
    lines.append("")
    lines.append("## Implementation Tasks")
    lines.append("")
    lines.extend(task_lines)
    lines.append("")

    folder = root / "user-stories"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"story-{number}-fixture.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def make_spec(repo: Path, name: str = "demo-spec") -> Path:
    spec_dir = repo / ".writ" / "specs" / name
    spec_dir.mkdir(parents=True, exist_ok=True)
    return spec_dir


def run_cli(*args: str) -> tuple[int, dict]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = ac.main(list(args))
    raw = buf.getvalue()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {"_raw": raw}
    return code, payload


def run_check(spec_dir: Path, repo: Path) -> tuple[int, dict]:
    return ac.check(spec_dir, repo)


def codes(result: dict) -> list[str]:
    return [f["code"] for f in result.get("findings", [])]


def findings_for(result: dict, code: str) -> list[dict]:
    return [f for f in result.get("findings", []) if f["code"] == code]


# --- One test per finding code, severity asserted alongside detection -----

class FindingCodeTests(unittest.TestCase):
    def test_untasked_criterion_blocking(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Given a criterion no task cites. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Unrelated task with no citation.",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "untasked_criterion")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["id"], "AC-3.1")
            self.assertEqual(found[0]["severity"], "blocking")
            self.assertEqual(found[0]["story"], 3)

    def test_untested_criterion_blocking_only_when_completed(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3, status="Completed ✅",
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Given a tasked, untested criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "untested_criterion")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["id"], "AC-3.1")
            self.assertEqual(found[0]["severity"], "blocking")

    def test_untested_criterion_absent_before_completed(self) -> None:
        """Tests do not exist before the work does -- absence is expected,
        not blocking, until the story reads Completed."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3, status="Not Started",
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Given a tasked, untested criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0)
            self.assertEqual(findings_for(result, "untested_criterion"), [])

    def test_dangling_reference_from_task_citation(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=(
                    "- [ ] 3.1 Implement it. `[AC-3.1]`",
                    "- [ ] 3.2 Cites a deleted criterion. `[AC-3.9]`",
                ),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "dangling_reference")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["id"], "AC-3.9")
            self.assertEqual(found[0]["severity"], "blocking")
            self.assertEqual(found[0]["story"], 3)

    def test_dangling_reference_from_test_citation(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            tests_dir = repo / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_thing.py").write_text(
                '"""AC-3.9 -- names a criterion that was deleted."""\n', encoding="utf-8",
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "dangling_reference")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["id"], "AC-3.9")

    def test_duplicate_id_blocking(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=(
                    "- [ ] First criterion. `[AC-3.1]`",
                    "- [ ] Second criterion sharing an ID. `[AC-3.1]`",
                ),
                task_lines=("- [ ] 3.1 Implement both. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "duplicate_id")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["id"], "AC-3.1")
            self.assertEqual(found[0]["severity"], "blocking")

    def test_marker_violation_id_exceeds_marker(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Exceeds the marker. `[AC-3.6]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.6]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "marker_violation")
            self.assertTrue(any(f["id"] == "AC-3.6" for f in found))
            self.assertEqual(found[0]["severity"], "blocking")

    def test_marker_violation_missing_while_ids_present(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=None,
                ac_lines=("- [ ] Tagged, but no marker exists. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "marker_violation")
            self.assertEqual(len(found), 1)
            self.assertIsNone(found[0]["id"])

    def test_marker_violation_malformed_value(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** not-an-id"],
                ac_lines=("- [ ] Tagged criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "marker_violation")
            self.assertTrue(any("malformed marker value" in f["detail"] for f in found))

    def test_marker_violation_two_marker_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=[
                    "> **AC IDs assigned through:** AC-3.1",
                    "> **AC IDs assigned through:** AC-3.2",
                ],
                ac_lines=("- [ ] Tagged criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "marker_violation")
            self.assertTrue(any("marker lines found" in f["detail"] for f in found))

    def test_marker_violation_cross_story_definition(self) -> None:
        """A definition tag whose story number differs from the file's own
        number is reported, never silently re-homed to the story it lands
        in — and is excluded from that ID's definition set entirely."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 4,
                marker_lines=["> **AC IDs assigned through:** AC-4.1"],
                ac_lines=(
                    "- [ ] Wrongly tagged with story 2's id. `[AC-2.1]`",
                    "- [ ] A real story-4 criterion. `[AC-4.1]`",
                ),
                task_lines=("- [ ] 4.1 Implement it. `[AC-4.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            violations = findings_for(result, "marker_violation")
            self.assertTrue(any(f["id"] == "AC-2.1" for f in violations))
            # AC-2.1 must not have entered the definition set: a task citing
            # it would be a dangling_reference, not silently satisfied.
            dangling = findings_for(result, "dangling_reference")
            self.assertEqual(dangling, [])  # nothing cites AC-2.1 here

    def test_marker_violation_malformed_criterion_tag(self) -> None:
        """A tag-shaped but grammatically invalid ID (`AC-3`, no ordinal) is
        reported, not silently treated as an untagged line."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Malformed id, missing the ordinal. `[AC-3]`",),
                task_lines=("- [ ] 3.1 Implement it.",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "marker_violation")
            self.assertTrue(any("malformed criterion tag" in f["detail"] for f in found))

    def test_partial_adoption_blocking(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=(
                    "- [ ] Tagged criterion. `[AC-3.1]`",
                    "- [ ] Untagged criterion.",
                ),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "partial_adoption")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["severity"], "blocking")

    def test_legacy_story_informational_not_blocking(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=None,
                ac_lines=(
                    "- [ ] Untagged criterion one.",
                    "- [ ] Untagged criterion two.",
                ),
                task_lines=("- [ ] 3.1 Implement both.",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0)
            found = findings_for(result, "legacy_story")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["severity"], "informational")

    def test_clean_spec_exits_zero_no_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Fully covered criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0)
            self.assertEqual(result["findings"], [])


# --- Non-tag hazards ---------------------------------------------------------

class NonTagHazardTests(unittest.TestCase):
    def test_marker_line_does_not_satisfy_its_own_id(self) -> None:
        """A marker mentioning AC-3.1 must not itself count as a definition
        of AC-3.1 -- without exclusion, every marker would satisfy its own
        ID and mask a spec with zero real coverage."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] An untagged criterion.",),
                task_lines=("- [ ] 3.1 Cites the marker's own id. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1)
            found = findings_for(result, "dangling_reference")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["id"], "AC-3.1")

    def test_story_4_regression_fixture_prose_ids_are_inert(self) -> None:
        """Story 4's own criteria quote AC-2.1..AC-2.4 as a worked example
        inside criterion prose. A naive unanchored scan reads that as three
        extra definitions and reports them untasked/cross-story -- the
        exact failure recorded in spec.md. This pins the fix: reading
        Story 4's real file yields exactly its own four AC-4.* definitions,
        nothing from the quoted prose."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            story4_line = (
                "- [ ] Given a story with criteria `AC-2.1` through `AC-2.4` and a marker "
                "reading `AC-2.4`, when `/edit-spec` inserts a criterion anywhere in the "
                "list, then the new criterion is `AC-2.5`, the marker advances to "
                "`AC-2.5`, and all four existing ID tags are byte-identical to their "
                "pre-edit state. `[AC-4.1]`"
            )
            write_story(
                spec, 4,
                marker_lines=["> **AC IDs assigned through:** AC-4.4"],
                ac_lines=(
                    story4_line,
                    "- [ ] Second criterion. `[AC-4.2]`",
                    "- [ ] Third criterion. `[AC-4.3]`",
                    "- [ ] Fourth criterion. `[AC-4.4]`",
                ),
                task_lines=(
                    "- [ ] 4.1 Task one. `[AC-4.1]`",
                    "- [ ] 4.2 Task two. `[AC-4.2]`",
                    "- [ ] 4.3 Task three. `[AC-4.3]`",
                    "- [ ] 4.4 Task four. `[AC-4.4]`",
                ),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)
            self.assertEqual(result["findings"], [])

    def test_real_story_4_file_yields_exactly_four_definitions(self) -> None:
        """Same regression, against the actual repo file rather than a
        copy, so drift in the real spec is caught by the suite."""
        real_story_4 = (
            Path(__file__).resolve().parents[2]
            / ".writ" / "specs" / "2026-08-13-acceptance-criteria-traceability-ids"
            / "user-stories" / "story-4-edit-spec-stability-guard.md"
        )
        if not real_story_4.is_file():
            self.skipTest("real story-4 fixture file not present in this checkout")
        story = ac.parse_story_file(real_story_4)
        findings: list = []
        defs = ac._analyze_story(story, findings)
        self.assertEqual(sorted(defs), ["AC-4.1", "AC-4.2", "AC-4.3", "AC-4.4"])
        self.assertEqual([f for f in findings if f["severity"] == "blocking"], [])


# --- Bare-token boundary (task 2.1's fixture) --------------------------------

class BareTokenBoundaryTests(unittest.TestCase):
    def test_standalone_bare_id_matches(self) -> None:
        self.assertTrue(ac.BARE_ID.search("see AC-3.1 for detail"))

    def test_bare_id_with_trailing_non_whitespace_does_not_match(self) -> None:
        self.assertIsNone(ac.BARE_ID.search("AC-3.1x"))

    def test_bare_id_with_leading_non_whitespace_does_not_match(self) -> None:
        self.assertIsNone(ac.BARE_ID.search("xAC-3.1"))

    def test_bare_id_followed_by_punctuation_still_matches(self) -> None:
        self.assertTrue(ac.BARE_ID.search("covers AC-3.1."))


# --- Determinism -------------------------------------------------------------

class DeterminismTests(unittest.TestCase):
    def test_two_runs_byte_identical(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.3"],
                ac_lines=(
                    "- [ ] One. `[AC-3.1]`",
                    "- [ ] Two, exceeds marker. `[AC-3.9]`",
                    "- [ ] Three. `[AC-3.3]`",
                ),
                task_lines=(
                    "- [ ] 3.1 Implement one. `[AC-3.1]`",
                    "- [ ] 3.3 Implement three, and cite a ghost. `[AC-3.3, AC-3.7]`",
                ),
            )
            code1, result1 = run_check(spec, repo)
            code2, result2 = run_check(spec, repo)
            self.assertEqual(code1, code2)
            self.assertEqual(
                json.dumps(result1, sort_keys=True), json.dumps(result2, sort_keys=True),
            )

    def test_cli_two_runs_stdout_byte_identical(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Clean. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            first = subprocess.run(
                [sys.executable, str(MODULE_PATH), "check", "--spec", str(spec), "--repo", str(repo)],
                capture_output=True, text=True,
            )
            second = subprocess.run(
                [sys.executable, str(MODULE_PATH), "check", "--spec", str(spec), "--repo", str(repo)],
                capture_output=True, text=True,
            )
            self.assertEqual(first.returncode, second.returncode)
            self.assertEqual(first.stdout, second.stdout)


# --- Exit codes (0 / 1 / 2) --------------------------------------------------

class ExitCodeTests(unittest.TestCase):
    def test_exit_0_clean(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Clean. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, _ = run_check(spec, repo)
            self.assertEqual(exit_code, 0)

    def test_exit_1_blocking_findings(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Untasked. `[AC-3.1]`",),
                task_lines=(),
            )
            exit_code, _ = run_check(spec, repo)
            self.assertEqual(exit_code, 1)

    def test_exit_2_missing_spec_path(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            missing = repo / "does-not-exist"
            with self.assertRaises(ac.UsageError):
                run_check(missing, repo)

    def test_exit_2_spec_is_a_file_not_a_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            file_path = repo / "not-a-folder"
            file_path.write_text("x", encoding="utf-8")
            with self.assertRaises(ac.UsageError):
                run_check(file_path, repo)

    def test_exit_2_no_user_stories_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / ".writ" / "specs" / "demo"
            spec.mkdir(parents=True)
            with self.assertRaises(ac.UsageError):
                run_check(spec, repo)

    def test_exit_2_user_stories_directory_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            (spec / "user-stories").mkdir(parents=True)
            with self.assertRaises(ac.UsageError):
                run_check(spec, repo)

    def test_exit_2_unreadable_story_file(self) -> None:
        if os.name != "posix" or os.geteuid() == 0:
            self.skipTest("permission-denied fixture requires a non-root POSIX user")
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            path = write_story(spec, 3, ac_lines=("- [ ] X.",), task_lines=())
            path.chmod(0)
            try:
                with self.assertRaises(ac.UsageError):
                    run_check(spec, repo)
            finally:
                path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_exit_2_invalid_utf8_story_file(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            folder = spec / "user-stories"
            folder.mkdir(parents=True)
            path = folder / "story-3-fixture.md"
            path.write_bytes(b"# Story 3\n\xff\xfe not valid utf-8\n")
            with self.assertRaises(ac.UsageError):
                run_check(spec, repo)

    def test_cli_exit_2_prints_error_not_a_finding_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            missing = repo / "does-not-exist"
            code, payload = run_cli("check", "--spec", str(missing), "--repo", str(repo))
            self.assertEqual(code, 2)
            self.assertIn("error", payload)

    def test_cli_exit_0_prints_findings_payload(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Clean. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            code, payload = run_cli("check", "--spec", str(spec), "--repo", str(repo))
            self.assertEqual(code, 0)
            self.assertEqual(payload["schema"], ac.SCHEMA)
            self.assertEqual(payload["findings"], [])


# --- Citation-scan scoping and bounds ----------------------------------------

class CitationScanTests(unittest.TestCase):
    def test_test_shaped_path_satisfies_coverage(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3, status="Completed ✅",
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Tested via a real test file. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            tests_dir = repo / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_thing.py").write_text(
                'def test_x():\n    """AC-3.1 -- covered."""\n', encoding="utf-8",
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)
            self.assertEqual(findings_for(result, "untested_criterion"), [])

    def test_source_shaped_path_does_not_satisfy_coverage(self) -> None:
        """The tempting shortcut this spec exists to close: a non-test
        mention outside .writ/ must not launder untested_criterion."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3, status="Completed ✅",
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Only mentioned in a changelog. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            docs_dir = repo / "docs"
            docs_dir.mkdir()
            (docs_dir / "CHANGELOG.md").write_text("AC-3.1 was implemented.\n", encoding="utf-8")
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1, result)
            self.assertEqual(len(findings_for(result, "untested_criterion")), 1)

    def test_writ_directory_excluded_from_repo_scan(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3, status="Completed ✅",
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] Only mentioned inside .writ/. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            decoy = repo / ".writ" / "decoy.md"
            decoy.write_text("AC-3.1 mentioned here, inside .writ/.\n", encoding="utf-8")
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1, result)
            self.assertEqual(len(findings_for(result, "untested_criterion")), 1)

    def test_binary_files_are_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            (repo / "blob.bin").write_bytes(b"AC-9.9 decoy \x00 binary")
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)
            self.assertEqual(findings_for(result, "dangling_reference"), [])

    def test_symlink_leaving_repo_is_not_followed(self) -> None:
        with TemporaryDirectory() as outer_tmp:
            outer = Path(outer_tmp)
            external = outer / "external.py"
            external.write_text("AC-9.9 decoy outside the repo\n", encoding="utf-8")
            with TemporaryDirectory() as tmp:
                repo = Path(tmp)
                spec = make_spec(repo)
                write_story(
                    spec, 3,
                    marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                    ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                    task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
                )
                link = repo / "escape.py"
                try:
                    link.symlink_to(external)
                except OSError:
                    self.skipTest("symlinks unsupported in this environment")
                exit_code, result = run_check(spec, repo)
                self.assertEqual(exit_code, 0, result)
                self.assertEqual(findings_for(result, "dangling_reference"), [])

    def test_git_ignored_directory_excluded_and_disclosed(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init = subprocess.run(["git", "init", "-q", str(repo)], capture_output=True, text=True)
            if init.returncode != 0:
                self.skipTest("git unavailable in this environment")
            (repo / ".gitignore").write_text("vendor/\n", encoding="utf-8")
            vendor = repo / "vendor"
            vendor.mkdir()
            (vendor / "decoy.py").write_text("AC-9.9 decoy inside a git-ignored dir\n", encoding="utf-8")

            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)
            self.assertEqual(findings_for(result, "dangling_reference"), [])
            self.assertTrue(result["ignore_filter"])

    def test_non_git_repo_falls_back_and_discloses(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)
            self.assertFalse(result["ignore_filter"])

    def test_nested_worktree_boundary_not_descended(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            nested = repo / "nested-worktree"
            nested.mkdir()
            # A worktree's .git entry is a FILE containing a gitdir pointer,
            # never a directory -- that is the recognizable boundary.
            (nested / ".git").write_text("gitdir: /elsewhere/.git/worktrees/nested\n", encoding="utf-8")
            (nested / "decoy.py").write_text("AC-9.9 decoy inside a nested worktree\n", encoding="utf-8")
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)
            self.assertEqual(findings_for(result, "dangling_reference"), [])

    def test_directory_symlink_leaving_repo_is_not_descended(self) -> None:
        with TemporaryDirectory() as outer_tmp:
            outer = Path(outer_tmp)
            external_dir = outer / "external"
            external_dir.mkdir()
            (external_dir / "decoy.py").write_text("AC-9.9 decoy outside the repo\n", encoding="utf-8")
            with TemporaryDirectory() as tmp:
                repo = Path(tmp)
                spec = make_spec(repo)
                write_story(
                    spec, 3,
                    marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                    ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                    task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
                )
                link = repo / "escape-dir"
                try:
                    link.symlink_to(external_dir, target_is_directory=True)
                except OSError:
                    self.skipTest("symlinks unsupported in this environment")
                exit_code, result = run_check(spec, repo)
                self.assertEqual(exit_code, 0, result)
                self.assertEqual(findings_for(result, "dangling_reference"), [])

    def test_symlink_loop_does_not_crash_the_scan(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            loop = repo / "loop"
            try:
                loop.symlink_to(loop)
            except OSError:
                self.skipTest("symlinks unsupported in this environment")
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 0, result)

    def test_cross_file_duplicate_id_detected(self) -> None:
        """Two story files that both validly claim the same story number
        (a malformed spec) must not silently let the second overwrite the
        first's definition."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] First file's criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            # A second file that also claims to be story 3.
            folder = spec / "user-stories"
            (folder / "story-3-duplicate.md").write_text(
                "\n".join([
                    "# Story 3: Duplicate",
                    "",
                    "> **Status:** Not Started",
                    "",
                    "## Acceptance Criteria",
                    "",
                    "> **AC IDs assigned through:** AC-3.1",
                    "",
                    "- [ ] Second file's criterion, same id. `[AC-3.1]`",
                    "",
                    "## Implementation Tasks",
                    "",
                    "- [ ] 3.1 Implement it. `[AC-3.1]`",
                    "",
                ]) + "\n",
                encoding="utf-8",
            )
            exit_code, result = run_check(spec, repo)
            self.assertEqual(exit_code, 1, result)
            self.assertTrue(any(f["code"] == "duplicate_id" for f in result["findings"]))

    def test_scanned_files_count_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = make_spec(repo)
            write_story(
                spec, 3,
                marker_lines=["> **AC IDs assigned through:** AC-3.1"],
                ac_lines=("- [ ] A real criterion. `[AC-3.1]`",),
                task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
            )
            (repo / "one.py").write_text("nothing relevant\n", encoding="utf-8")
            (repo / "two.py").write_text("nothing relevant either\n", encoding="utf-8")
            _, result = run_check(spec, repo)
            self.assertGreaterEqual(result["scanned_files"], 2)


# --- Story-file parsing edge cases -------------------------------------------

class StoryFileParsingEdgeCaseTests(unittest.TestCase):
    def test_unparseable_story_filename_is_usage_error(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-a-story-file.md"
            path.write_text("# Not a story\n", encoding="utf-8")
            with self.assertRaises(ac.UsageError):
                ac.parse_story_file(path)

    def test_missing_section_heading_yields_none_bounds(self) -> None:
        self.assertIsNone(ac._section_bounds(["# Story 1", "", "Body only."], "Acceptance Criteria"))

    def test_story_with_no_acceptance_criteria_section_parses_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "story-3-no-sections.md"
            path.write_text("# Story 3: No Sections\n\n> **Status:** Not Started\n\nBody.\n", encoding="utf-8")
            story = ac.parse_story_file(path)
            self.assertEqual(story["ac_lines"], [])
            self.assertEqual(story["task_lines"], [])
            self.assertEqual(story["status"], "Not Started")

    def test_story_with_no_status_line_has_none_status(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "story-3-no-status.md"
            path.write_text(
                "# Story 3: No Status\n\n## Acceptance Criteria\n\n- [ ] X. `[AC-3.1]`\n"
                "\n## Implementation Tasks\n\n- [ ] 3.1 Y. `[AC-3.1]`\n",
                encoding="utf-8",
            )
            story = ac.parse_story_file(path)
            self.assertIsNone(story["status"])


if __name__ == "__main__":
    unittest.main()
