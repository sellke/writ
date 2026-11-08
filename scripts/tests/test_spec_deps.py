#!/usr/bin/env python3
"""Tests for scripts/spec-deps.py archive resolution.

Spec `2026-11-06-archived-dependencies-resolve`, Story 1: a declared
dependency whose folder sits under `.writ/specs/archive/<id>/spec.md` is
satisfied, reported under `archived_dependencies`, and never parsed or
ordered. An id in neither place still blocks with `missing_reference`, and
every other blocker keeps its code and exit.

Each test builds disposable spec folders under `tmp_path` and runs the script
by subprocess, the way `/implement-phase` and `/verify-spec` call it. The
module filename contains a hyphen, so it is also imported by path, the recipe
`test_story_deps.py` uses.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "spec-deps.py"
_spec = importlib.util.spec_from_file_location("spec_deps", MODULE_PATH)
sd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sd)  # type: ignore[union-attr]


def make_spec(root: Path, spec_id: str, header: str | None, archived: bool = False) -> Path:
    """Write root/<id>/spec.md, or root/archive/<id>/spec.md when archived.

    header=None omits the Dependencies line entirely (legacy absence).
    """
    base = root / "archive" if archived else root
    folder = base / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    lines = [f"# {spec_id}", ""]
    if header is not None:
        lines.append(header)
    lines += ["", "Body.", ""]
    path = folder / "spec.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_validate(root: Path) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(MODULE_PATH), "validate", "--specs-dir", str(root)],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def test_archived_dependency_is_satisfied(tmp_path: Path) -> None:
    """[AC-1.1] An archived dependency validates ok and is reported, not ordered."""
    make_spec(tmp_path, "consumer", "> **Dependencies:** [done]")
    make_spec(tmp_path, "done", "> **Dependencies:** []", archived=True)

    code, payload = run_validate(tmp_path)

    assert code == 0, payload
    assert payload["status"] == "ok"
    assert payload["schema"] == "spec-deps-graph-v1"
    assert payload["order"] == ["consumer"]
    assert payload["graph"]["consumer"] == ["done"]
    assert payload["archived_dependencies"] == {"consumer": ["done"]}
    assert "blocker" not in payload


def test_archived_specs_are_never_parsed(tmp_path: Path) -> None:
    """[AC-1.2] A malformed archived header and an archived chain raise nothing."""
    make_spec(tmp_path, "done", "> **Dependencies:** not a list", archived=True)
    make_spec(tmp_path, "loop", "> **Dependencies:** [done]", archived=True)
    make_spec(tmp_path, "consumer", "> **Dependencies:** [done, loop]")

    code, payload = run_validate(tmp_path)

    assert code == 0, payload
    assert "blocker" not in payload
    assert payload["status"] == "ok"
    assert payload["order"] == ["consumer"]
    assert payload["archived_dependencies"]["consumer"] == ["done", "loop"]


def test_unknown_id_still_blocks_and_names_both_paths(tmp_path: Path) -> None:
    """[AC-1.3] An id in neither place blocks, and the summary names both paths."""
    make_spec(tmp_path, "consumer", "> **Dependencies:** [ghost]")
    make_spec(tmp_path, "done", "> **Dependencies:** []", archived=True)

    code, payload = run_validate(tmp_path)

    assert code == 1, payload
    blocker = payload["blocker"]
    assert blocker["code"] == "missing_reference"
    assert ".writ/specs/ghost/" in blocker["summary"]
    assert ".writ/specs/archive/ghost/" in blocker["summary"]


def test_active_folder_wins_over_archive(tmp_path: Path) -> None:
    """[AC-1.2] An id both active and archived keeps its ordering edge."""
    make_spec(tmp_path, "done", "> **Dependencies:** []")
    make_spec(tmp_path, "done", "> **Dependencies:** []", archived=True)
    make_spec(tmp_path, "consumer", "> **Dependencies:** [done]")

    code, payload = run_validate(tmp_path)

    assert code == 0, payload
    assert payload["order"] == ["done", "consumer"]
    assert payload["archived_dependencies"] == {}


@pytest.mark.parametrize("archive_folder", ["absent", "empty"])
def test_no_archive_folder_is_unchanged(tmp_path: Path, archive_folder: str) -> None:
    """[AC-1.1] No archive (or an empty one) gives today's result plus an empty map."""
    if archive_folder == "empty":
        (tmp_path / "archive").mkdir()
    make_spec(tmp_path, "done", "> **Dependencies:** []")
    make_spec(tmp_path, "consumer", "> **Dependencies:** [done]")

    code, payload = run_validate(tmp_path)

    assert code == 0, payload
    for key in ("schema", "status", "order", "graph", "archived_dependencies"):
        assert key in payload, key
    assert payload["order"] == ["done", "consumer"]
    assert payload["graph"] == {"consumer": ["done"], "done": []}
    assert payload["archived_dependencies"] == {}
    # The in-process call agrees with the CLI.
    assert sd.validate_graph(tmp_path, []) == payload


BLOCKER_FIXTURES = {
    "self_reference": [("loner", "> **Dependencies:** [loner]")],
    # `done` is archived; a duplicate is still caught before resolution.
    "duplicate_reference": [("dup", "> **Dependencies:** [done, done]")],
    "dependency_cycle": [
        ("left", "> **Dependencies:** [right]"),
        ("right", "> **Dependencies:** [left]"),
    ],
    "malformed_dependencies": [("bad", "> **Dependencies:** not a list")],
}


@pytest.mark.parametrize("code_name", sorted(BLOCKER_FIXTURES))
def test_existing_blockers_unchanged(tmp_path: Path, code_name: str) -> None:
    """[AC-1.3] Every existing blocker keeps its code and exit with an archive present."""
    make_spec(tmp_path, "done", "> **Dependencies:** []", archived=True)
    for spec_id, header in BLOCKER_FIXTURES[code_name]:
        make_spec(tmp_path, spec_id, header)

    code, payload = run_validate(tmp_path)

    assert code == 1, payload
    assert payload["blocker"]["code"] == code_name
