#!/usr/bin/env python3
"""Fixture scenarios for the acceptance-criterion traceability checker
(Story 2 of `2026-08-13-acceptance-criteria-traceability-ids`).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh's check_ac_trace.
Every scenario builds a disposable spec folder (and, where the citation
scan is under test, a disposable repo root) in a temp directory and
exercises scripts/ac-trace.py via its CLI, following
scripts/eval-story-deps.py's exact shape:

  - clean spec                      -> exit 0, no findings
  - untasked_criterion              -> blocking, exit 1
  - untested_criterion              -> blocking only once Completed
  - dangling_reference              -> blocking (task and test citation)
  - duplicate_id                    -> blocking
  - marker_violation                -> blocking (exceeds / missing / cross-story)
  - partial_adoption                -> blocking
  - legacy_story                    -> informational, exit 0
  - marker does not satisfy its own id (non-tag hazard)
  - Story 4's own criteria: prose-quoted ids are inert (non-tag hazard)
  - test-shaped path satisfies coverage; source-shaped does not
  - missing --spec / no user-stories/ -> exit 2
  - byte-identical repeat runs
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("ac-trace.py")
passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def write_story(root: Path, number: int, *, status: str = "Not Started",
                 marker_lines: list[str] | None = None,
                 ac_lines: tuple[str, ...] = (),
                 task_lines: tuple[str, ...] = ()) -> Path:
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


def codes(payload: dict) -> list[str]:
    return [f["code"] for f in payload.get("findings", [])]


def scenario_clean_spec_exits_zero() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Fully covered criterion. `[AC-3.1]`",),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("clean-spec-exits-zero", code == 0 and payload.get("findings") == [], payload)
        emit("clean-spec-schema", payload.get("schema") == "ac-trace-check-v1", payload)


def scenario_untasked_criterion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] No task cites this. `[AC-3.1]`",),
            task_lines=("- [ ] 3.1 Unrelated, no citation.",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("untasked-criterion-blocks", code == 1 and "untasked_criterion" in codes(payload), payload)


def scenario_untested_criterion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3, status="Completed ✅",
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Tasked but never tested. `[AC-3.1]`",),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("untested-criterion-blocks-when-completed",
             code == 1 and "untested_criterion" in codes(payload), payload)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3, status="Not Started",
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Tasked but never tested. `[AC-3.1]`",),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("untested-criterion-absent-before-completed",
             code == 0 and "untested_criterion" not in codes(payload), payload)


def scenario_dangling_reference() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Real criterion. `[AC-3.1]`",),
            task_lines=(
                "- [ ] 3.1 Implement it. `[AC-3.1]`",
                "- [ ] 3.2 Cites a deleted criterion. `[AC-3.9]`",
            ),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("dangling-reference-from-task",
             code == 1 and "dangling_reference" in codes(payload), payload)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Real criterion. `[AC-3.1]`",),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
        )
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_thing.py").write_text(
            '"""AC-3.9 -- names a criterion that was deleted."""\n', encoding="utf-8",
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("dangling-reference-from-test",
             code == 1 and "dangling_reference" in codes(payload), payload)


def scenario_duplicate_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=(
                "- [ ] First. `[AC-3.1]`",
                "- [ ] Second, same id. `[AC-3.1]`",
            ),
            task_lines=("- [ ] 3.1 Implement both. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("duplicate-id-blocks", code == 1 and "duplicate_id" in codes(payload), payload)


def scenario_marker_violation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Exceeds the marker. `[AC-3.6]`",),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.6]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("marker-violation-exceeds", code == 1 and "marker_violation" in codes(payload), payload)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=None,
            ac_lines=("- [ ] Tagged with no marker at all. `[AC-3.1]`",),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("marker-violation-missing", code == 1 and "marker_violation" in codes(payload), payload)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 4,
            marker_lines=["> **AC IDs assigned through:** AC-4.1"],
            ac_lines=(
                "- [ ] Wrongly tagged with story 2's id. `[AC-2.1]`",
                "- [ ] Real story-4 criterion. `[AC-4.1]`",
            ),
            task_lines=("- [ ] 4.1 Implement it. `[AC-4.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        found_ids = {f.get("id") for f in payload.get("findings", []) if f["code"] == "marker_violation"}
        emit("marker-violation-cross-story", code == 1 and "AC-2.1" in found_ids, payload)


def scenario_partial_adoption() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=(
                "- [ ] Tagged. `[AC-3.1]`",
                "- [ ] Untagged.",
            ),
            task_lines=("- [ ] 3.1 Implement it. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("partial-adoption-blocks", code == 1 and "partial_adoption" in codes(payload), payload)


def scenario_legacy_story() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=None,
            ac_lines=("- [ ] Untagged one.", "- [ ] Untagged two."),
            task_lines=("- [ ] 3.1 Implement both.",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        codes_found = codes(payload)
        emit("legacy-story-informational-exits-zero",
             code == 0 and "legacy_story" in codes_found, payload)


def scenario_non_tag_hazards() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        write_story(
            spec, 3,
            marker_lines=["> **AC IDs assigned through:** AC-3.1"],
            ac_lines=("- [ ] Untagged criterion.",),
            task_lines=("- [ ] 3.1 Cites the marker's own id. `[AC-3.1]`",),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        found_ids = {f.get("id") for f in payload.get("findings", []) if f["code"] == "dangling_reference"}
        emit("marker-does-not-satisfy-its-own-id", code == 1 and "AC-3.1" in found_ids, payload)

    with tempfile.TemporaryDirectory() as tmp:
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
                "- [ ] Second. `[AC-4.2]`",
                "- [ ] Third. `[AC-4.3]`",
                "- [ ] Fourth. `[AC-4.4]`",
            ),
            task_lines=(
                "- [ ] 4.1 Task one. `[AC-4.1]`",
                "- [ ] 4.2 Task two. `[AC-4.2]`",
                "- [ ] 4.3 Task three. `[AC-4.3]`",
                "- [ ] 4.4 Task four. `[AC-4.4]`",
            ),
        )
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("story-4-prose-quoted-ids-are-inert", code == 0 and payload.get("findings") == [], payload)


def scenario_citation_scan_scoping() -> None:
    with tempfile.TemporaryDirectory() as tmp:
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
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("test-shaped-path-satisfies-coverage",
             code == 0 and "untested_criterion" not in codes(payload), payload)

    with tempfile.TemporaryDirectory() as tmp:
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
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("source-shaped-path-does-not-satisfy-coverage",
             code == 1 and "untested_criterion" in codes(payload), payload)


def scenario_usage_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        missing = repo / "does-not-exist"
        code, payload = run("check", "--spec", str(missing), "--repo", str(repo))
        emit("missing-spec-path-exits-two", code == 2 and "error" in payload, payload)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        spec = make_spec(repo)
        code, payload = run("check", "--spec", str(spec), "--repo", str(repo))
        emit("no-user-stories-directory-exits-two", code == 2 and "error" in payload, payload)


def scenario_determinism() -> None:
    with tempfile.TemporaryDirectory() as tmp:
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
                "- [ ] 3.3 Implement three, cite a ghost. `[AC-3.3, AC-3.7]`",
            ),
        )
        first = subprocess.run(
            [sys.executable, str(HELPER), "check", "--spec", str(spec), "--repo", str(repo)],
            capture_output=True, text=True,
        )
        second = subprocess.run(
            [sys.executable, str(HELPER), "check", "--spec", str(spec), "--repo", str(repo)],
            capture_output=True, text=True,
        )
        emit("repeated-runs-byte-identical",
             first.returncode == second.returncode and first.stdout == second.stdout,
             (first.stdout, second.stdout))


def main() -> int:
    scenario_clean_spec_exits_zero()
    scenario_untasked_criterion()
    scenario_untested_criterion()
    scenario_dangling_reference()
    scenario_duplicate_id()
    scenario_marker_violation()
    scenario_partial_adoption()
    scenario_legacy_story()
    scenario_non_tag_hazards()
    scenario_citation_scan_scoping()
    scenario_usage_errors()
    scenario_determinism()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
