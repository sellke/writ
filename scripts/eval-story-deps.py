#!/usr/bin/env python3
"""Fixture scenarios for the story-dependency contract (Story 1).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_story_deps.
Every scenario builds disposable fixture spec folders in a temp directory and
exercises scripts/story-deps.py, asserting the authoritative contract:

  - absent header      -> legacy, treated as []
  - "None"              -> declared, no dependencies (case-insensitive)
  - ordered list        -> declared order preserved
  - malformed           -> blocking malformed_dependencies
  - missing ref         -> blocking missing_reference (names the reference)
  - self-reference      -> blocking self_reference
  - duplicate           -> blocking duplicate_reference
  - cycle                -> blocking dependency_cycle (names the path)
  - no stories found     -> blocking no_stories_found
  - deterministic topological batches
  - numeric story-number tie-break (not lexicographic)
  - byte-identical repeat runs
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("story-deps.py")
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


def make_story(root: Path, number: int, title: str, dependencies: str | None) -> Path:
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


def scenario_happy_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", "Story 1")
        make_story(root, 3, "Gamma", "None")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("happy-path-exits-zero", code == 0 and payload.get("status") == "ok", payload)
        emit("happy-path-schema", payload.get("schema") == "story-graph/v1", payload)
        batches = payload.get("batches", [])
        emit("happy-path-batch-order",
             batches == [["story-1", "story-3"], ["story-2"]], batches)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        first_code, first_payload = run("validate", "--spec-dir", str(root))
        second_code, second_payload = run("validate", "--spec-dir", str(root))
        emit("repeated-runs-byte-identical",
             first_code == second_code and json.dumps(first_payload) == json.dumps(second_payload),
             (first_payload, second_payload))


def scenario_legacy_and_declared_none() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        code, payload = run("validate", "--spec-dir", str(root))
        emit("legacy-absent-header-is-empty-deps",
             code == 0 and payload.get("graph", {}).get("story-1") == [], payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", "none")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("declared-none-case-insensitive-is-empty-deps",
             code == 0 and payload.get("graph", {}).get("story-1") == [], payload)


def scenario_real_world_prose_forms() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", None)
        make_story(root, 3, "Gamma", "Stories 1, 2")
        make_story(root, 4, "Delta", "Story 3 (needs the manifest schema)")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("plural-and-parenthetical-forms-parse",
             code == 0 and payload.get("graph", {}).get("story-3") == ["story-1", "story-2"]
             and payload.get("graph", {}).get("story-4") == ["story-3"],
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", "None (independent of Story 1)")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("annotated-none-is-empty",
             code == 0 and payload.get("graph", {}).get("story-2") == [], payload)


def scenario_malformed_dependencies() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", "Story ???")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("malformed-garbage-value-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "malformed_dependencies",
             payload)


def scenario_missing_reference() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", None)
        make_story(root, 3, "Gamma", "Story 9")
        code, payload = run("validate", "--spec-dir", str(root))
        blocker = payload.get("blocker", {})
        emit("missing-reference-blocks",
             code != 0 and blocker.get("code") == "missing_reference"
             and "story-3" in blocker.get("summary", "") and "story-9" in blocker.get("summary", ""),
             payload)


def scenario_self_reference() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", "Story 2")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("self-reference-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "self_reference", payload)


def scenario_duplicate_reference() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", "Story 1, Story 1")
        code, payload = run("validate", "--spec-dir", str(root))
        emit("duplicate-reference-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "duplicate_reference", payload)


def scenario_cycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", "Story 2")
        make_story(root, 2, "Beta", "Story 1")
        code, payload = run("validate", "--spec-dir", str(root))
        blocker = payload.get("blocker", {})
        emit("two-story-cycle-blocks-with-path",
             code != 0 and blocker.get("code") == "dependency_cycle" and "->" in blocker.get("summary", ""),
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_story(root, 1, "Alpha", None)
        make_story(root, 2, "Beta", "Story 4")
        make_story(root, 3, "Gamma", "Story 2")
        make_story(root, 4, "Delta", "Story 3")
        code, payload = run("validate", "--spec-dir", str(root))
        blocker = payload.get("blocker", {})
        summary = blocker.get("summary", "")
        emit("four-story-cycle-names-full-path",
             code != 0 and blocker.get("code") == "dependency_cycle"
             and all(story in summary for story in ("story-2", "story-3", "story-4")),
             payload)


def scenario_no_stories_found() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "user-stories").mkdir(parents=True)
        code, payload = run("validate", "--spec-dir", str(root))
        emit("no-stories-found-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "no_stories_found", payload)


def scenario_numeric_tiebreak() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for number in range(1, 12):
            make_story(root, number, f"Story{number}", None)
        code, payload = run("validate", "--spec-dir", str(root))
        expected = [f"story-{n}" for n in range(1, 12)]
        emit("numeric-tiebreak-not-lexicographic",
             code == 0 and payload.get("batches", [[]]) == [expected], payload)


def main() -> int:
    scenario_happy_path()
    scenario_legacy_and_declared_none()
    scenario_real_world_prose_forms()
    scenario_malformed_dependencies()
    scenario_missing_reference()
    scenario_self_reference()
    scenario_duplicate_reference()
    scenario_cycle()
    scenario_no_stories_found()
    scenario_numeric_tiebreak()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
