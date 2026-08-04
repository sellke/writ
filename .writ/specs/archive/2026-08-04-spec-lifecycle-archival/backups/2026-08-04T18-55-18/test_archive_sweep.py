"""Fixture tests for the evidence-gated archive sweep (Story 2).

Every test builds a disposable git repo in a temp directory (git mv requires
tracked files) mirroring `.writ/specs/` and `.writ/knowledge/` shape, then
exercises scripts/archive-sweep.py directly as a module (hyphenated filename,
imported by path — same recipe as test_spec_status.py / test_story_deps.py).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "archive-sweep.py"
SPEC = importlib.util.spec_from_file_location("archive_sweep", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
archive_sweep = importlib.util.module_from_spec(SPEC)
sys.modules["archive_sweep"] = archive_sweep
SPEC.loader.exec_module(archive_sweep)


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test")
    return repo


def make_spec(repo: Path, spec_id: str, header: str) -> Path:
    specs_dir = repo / ".writ" / "specs"
    folder = specs_dir / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "spec.md").write_text(f"# Spec: {spec_id}\n\n{header}\n", encoding="utf-8")
    return specs_dir


def make_knowledge_entry(repo: Path, category: str, name: str, related: list[str]) -> Path:
    knowledge_dir = repo / ".writ" / "knowledge"
    cat_dir = knowledge_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    items = "\n".join(f"  - {r}" for r in related)
    (cat_dir / name).write_text(
        f"---\nrelated_artifacts:\n{items}\n---\n\n# {name}\n", encoding="utf-8"
    )
    return knowledge_dir


def commit_all(repo: Path) -> None:
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "fixture commit")


def test_two_signal_eligibility_matrix(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-both-signals", "> **Status:** Complete")
    make_spec(repo, "2026-01-02-complete-only", "> **Status:** Complete")
    make_spec(repo, "2026-01-03-evidence-only", "> **Status:** Not Started")
    make_spec(repo, "2026-01-04-neither", "> **Status:** Not Started")
    knowledge_dir = make_knowledge_entry(
        repo, "lessons", "cites-both.md",
        ["2026-01-01-both-signals", "2026-01-03-evidence-only"],
    )
    commit_all(repo)

    result = archive_sweep.scan(specs_dir, knowledge_dir)
    by_id = {r["spec"]: r for r in result["results"]}

    assert by_id["2026-01-01-both-signals"]["eligible"] is True
    assert by_id["2026-01-02-complete-only"]["eligible"] is False
    assert by_id["2026-01-03-evidence-only"]["eligible"] is False  # not complete — status gate absolute
    assert by_id["2026-01-04-neither"]["eligible"] is False


def test_happy_path_git_mv_and_ledger_append(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = make_knowledge_entry(
        repo, "decisions", "cites-it.md", ["2026-01-01-eligible-spec"]
    )
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert len(result["archived"]) == 1
    assert result["archived"][0]["spec"] == "2026-01-01-eligible-spec"
    assert not (specs_dir / "2026-01-01-eligible-spec").exists()
    assert (specs_dir / "archive" / "2026-01-01-eligible-spec" / "spec.md").exists()

    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "2026-01-01-eligible-spec" in ledger
    assert "decisions/cites-it.md" in ledger

    # git recognizes the move as a rename once staged, not a delete+add pair.
    _run_git(repo, "add", "-A")
    status = _run_git(repo, "status", "--porcelain")
    assert "R  " in status.stdout


def test_complete_no_evidence_is_skipped_not_failed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-lonely-complete", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert result["archived"] == []
    assert result["skipped_no_evidence"] == ["2026-01-01-lonely-complete"]
    assert (specs_dir / "2026-01-01-lonely-complete").exists()


def test_evidence_without_complete_is_never_moved(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-in-progress", "> **Status:** In Progress")
    knowledge_dir = make_knowledge_entry(
        repo, "conventions", "cites-it.md", ["2026-01-01-in-progress"]
    )
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert result["archived"] == []
    assert (specs_dir / "2026-01-01-in-progress").exists()


def test_destination_collision_skips_one_continues_sweep(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-collides", "> **Status:** Complete")
    make_spec(repo, "2026-01-02-clean", "> **Status:** Complete")
    knowledge_dir = make_knowledge_entry(
        repo, "glossary", "cites-both.md",
        ["2026-01-01-collides", "2026-01-02-clean"],
    )
    # Pre-create the collision at the destination.
    collision_dest = specs_dir / "archive" / "2026-01-01-collides"
    collision_dest.mkdir(parents=True)
    (collision_dest / "spec.md").write_text("# already here\n", encoding="utf-8")
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert result["collisions"] == ["2026-01-01-collides"]
    assert any(a["spec"] == "2026-01-02-clean" for a in result["archived"])
    assert (specs_dir / "2026-01-01-collides").exists()  # untouched — collision, not moved


def test_git_mv_failure_skips_one_continues_sweep(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-untracked", "> **Status:** Complete")
    make_spec(repo, "2026-01-02-tracked", "> **Status:** Complete")
    knowledge_dir = make_knowledge_entry(
        repo, "lessons", "cites-both.md",
        ["2026-01-01-untracked", "2026-01-02-tracked"],
    )
    # Commit only the second spec — the first stays untracked, so `git mv`
    # fails for it ("not under version control") while the second succeeds.
    _run_git(repo, "add", str(specs_dir / "2026-01-02-tracked"))
    _run_git(repo, "add", str(knowledge_dir))
    _run_git(repo, "commit", "-q", "-m", "partial fixture commit")

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert len(result["move_failures"]) == 1
    assert result["move_failures"][0]["spec"] == "2026-01-01-untracked"
    assert any(a["spec"] == "2026-01-02-tracked" for a in result["archived"])
    assert (specs_dir / "2026-01-01-untracked").exists()  # move failed — left in place


def test_zero_eligible_specs_is_a_clean_no_op(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-not-started", "> **Status:** Not Started")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert result["archived"] == []
    assert "0 specs archived" in result["summary"]


def test_nil_input_no_specs_directory_no_ops_cleanly(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = repo / ".writ" / "specs"  # never created
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert result["archived"] == []
    assert result["skipped_no_evidence"] == []


def test_second_run_is_idempotent(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = make_knowledge_entry(
        repo, "decisions", "cites-it.md", ["2026-01-01-eligible-spec"]
    )
    commit_all(repo)

    first = archive_sweep.sweep(repo, specs_dir, knowledge_dir)
    assert len(first["archived"]) == 1

    second = archive_sweep.sweep(repo, specs_dir, knowledge_dir)
    assert second["archived"] == []  # already moved — no longer in the single-level glob
    assert second["skipped_no_evidence"] == []
    assert second["collisions"] == []

    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert ledger.count("2026-01-01-eligible-spec") == 1  # no duplicate entry


def test_folder_name_substring_match_not_exact_path(tmp_path: Path) -> None:
    """related_artifacts may cite `.writ/specs/<name>/spec.md` (full path) —
    the folder-name substring heuristic must still find it (spec.md's
    Technical Concerns)."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-full-path-cited", "> **Status:** Complete")
    knowledge_dir = make_knowledge_entry(
        repo, "decisions", "cites-full-path.md",
        [".writ/specs/2026-01-01-full-path-cited/spec.md"],
    )
    commit_all(repo)

    result = archive_sweep.scan(specs_dir, knowledge_dir)
    assert result["results"][0]["eligible"] is True
