"""Fixture tests for the status-alone archive sweep (Story 2, amended 2026-08-04).

Knowledge evidence is enrichment on the ledger line, not an eligibility gate
— see `archive-sweep.py`'s module docstring and `spec.md` Technical Concerns
→ Amendment for the full rationale.

Every test builds a disposable git repo in a temp directory (git mv requires
tracked files) mirroring `.writ/specs/` and `.writ/knowledge/` shape, then
exercises scripts/archive-sweep.py directly as a module (hyphenated filename,
imported by path — same recipe as test_spec_status.py / test_story_deps.py).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
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


def test_status_alone_eligibility_matrix(tmp_path: Path) -> None:
    """Amendment 2026-08-04: eligibility is complete-family status alone.
    Evidence is still computed and reported, but never gates `eligible`."""
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
    assert by_id["2026-01-01-both-signals"]["evidence"] == ["lessons/cites-both.md"]
    assert by_id["2026-01-02-complete-only"]["eligible"] is True  # complete alone is now sufficient
    assert by_id["2026-01-02-complete-only"]["evidence"] == []
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


def test_complete_no_evidence_is_archived_with_enrichment_marker(tmp_path: Path) -> None:
    """Amendment 2026-08-04: a Complete spec with zero knowledge evidence is
    archived anyway; the ledger records 'no knowledge evidence yet' instead
    of blocking the move."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-lonely-complete", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert len(result["archived"]) == 1
    assert result["archived"][0]["spec"] == "2026-01-01-lonely-complete"
    assert result["archived"][0]["evidence"] == []
    assert not (specs_dir / "2026-01-01-lonely-complete").exists()
    assert (specs_dir / "archive" / "2026-01-01-lonely-complete" / "spec.md").exists()

    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "no knowledge evidence yet" in ledger


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
    assert result["collisions"] == []
    assert result["move_failures"] == []


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


# --- Story 2 (post-merge-archival-hook): single-spec archive entry point ---


def test_archive_one_eligible_and_complete_archives(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = make_knowledge_entry(
        repo, "decisions", "cites-it.md", ["2026-01-01-eligible-spec"]
    )
    commit_all(repo)

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-eligible-spec")

    assert result["status"] == "archived"
    assert result["ledger_line"] is not None
    assert not (specs_dir / "2026-01-01-eligible-spec").exists()
    assert (specs_dir / "archive" / "2026-01-01-eligible-spec" / "spec.md").exists()

    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "2026-01-01-eligible-spec" in ledger
    assert "decisions/cites-it.md" in ledger


def test_archive_one_not_yet_complete_skips_even_when_named(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-in-progress", "> **Status:** In Progress")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-in-progress")

    assert result["status"] == "not_eligible"
    assert (specs_dir / "2026-01-01-in-progress").exists()


def test_archive_one_already_archived_is_idempotent_no_op(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    first = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-eligible-spec")
    assert first["status"] == "archived"

    ledger_before = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")

    second = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-eligible-spec")
    assert second["status"] == "already_archived"
    assert second["ledger_line"] is None

    ledger_after = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert ledger_before == ledger_after  # no duplicate ledger line


def test_archive_one_destination_collision_hard_stops(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-collides", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    collision_dest = specs_dir / "archive" / "2026-01-01-collides"
    collision_dest.mkdir(parents=True)
    (collision_dest / "spec.md").write_text("# already here\n", encoding="utf-8")
    commit_all(repo)

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-collides")

    assert result["status"] == "collision"
    assert (specs_dir / "2026-01-01-collides").exists()  # untouched — collision, not moved
    assert (specs_dir / "archive" / "2026-01-01-collides" / "spec.md").exists()


def test_archive_one_nonexistent_spec_name_is_not_eligible_not_a_crash(tmp_path: Path) -> None:
    """Absent from both specs_dir and archive_dir falls through naturally to
    not_eligible — never raises (arch-check CAUTION item 3)."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-some-other-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-does-not-exist")

    assert result["status"] == "not_eligible"


def test_archive_one_pr_number_annotates_ledger_line(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.archive_one(
        repo, specs_dir, knowledge_dir, "2026-01-01-eligible-spec", pr_number=32
    )

    assert result["status"] == "archived"
    assert "via PR #32" in result["ledger_line"]
    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "via PR #32" in ledger


def test_archive_one_without_pr_number_ledger_stays_unannotated(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-eligible-spec")

    assert result["status"] == "archived"
    assert "via PR" not in result["ledger_line"]
    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "via PR" not in ledger


def test_append_ledger_pr_number_none_output_byte_for_byte_unchanged(tmp_path: Path) -> None:
    """`_append_ledger()`'s new trailing `pr_number` parameter must be a
    no-op when omitted — every existing (sweep-originated) call site output
    stays byte-for-byte identical (arch-check CAUTION item 5)."""
    ledger_a = tmp_path / "a" / "LEDGER.md"
    ledger_b = tmp_path / "b" / "LEDGER.md"

    archive_sweep._append_ledger(ledger_a, "2026-01-01-spec", [], "2026-08-04T15:32:00Z")
    archive_sweep._append_ledger(ledger_b, "2026-01-01-spec", [], "2026-08-04T15:32:00Z", None)

    assert ledger_a.read_text(encoding="utf-8") == ledger_b.read_text(encoding="utf-8")


def test_ledger_with_mixed_annotated_and_unannotated_lines_stays_readable(tmp_path: Path) -> None:
    """An existing LEDGER.md containing only pre-existing sweep-originated
    (unannotated) lines still parses/reads correctly once a PR-annotated
    line is appended alongside — old lines untouched, not rewritten."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-swept", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    sweep_result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)
    assert len(sweep_result["archived"]) == 1
    ledger_after_sweep = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")

    make_spec(repo, "2026-01-02-hooked", "> **Status:** Complete")
    commit_all(repo)
    hook_result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-02-hooked", pr_number=32)
    assert hook_result["status"] == "archived"

    ledger_final = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert ledger_final.startswith(ledger_after_sweep)  # old lines untouched, only appended to
    assert "2026-01-01-swept" in ledger_final and "via PR" not in ledger_final.split("2026-01-01-swept")[1].split("\n")[0]
    assert "2026-01-02-hooked" in ledger_final
    assert "via PR #32" in ledger_final


def test_archive_one_git_mv_failure_reports_not_raises(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-untracked", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    # Never committed — `git mv` fails ("not under version control").

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-untracked")

    assert result["status"] == "git_mv_failed"
    assert (specs_dir / "2026-01-01-untracked").exists()  # move failed — left in place


def test_archive_one_ledger_append_failure_returns_archived_unlogged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When `git mv` succeeds but the ledger append raises, the move is not
    rolled back (accepted rare risk per arch-check CAUTION item 2) — the
    result must be distinguishable from both a clean `archived` and a
    `git_mv_failed` that never moved anything."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(archive_sweep, "_append_ledger", _boom)

    result = archive_sweep.archive_one(repo, specs_dir, knowledge_dir, "2026-01-01-eligible-spec")

    assert result["status"] == "archived_unlogged"
    assert not (specs_dir / "2026-01-01-eligible-spec").exists()  # move happened
    assert (specs_dir / "archive" / "2026-01-01-eligible-spec" / "spec.md").exists()


def test_archive_one_cli_subcommand_happy_path(tmp_path: Path) -> None:
    """Task 2.7: exercise `archive_one()` via the `archive-one` CLI
    subcommand, not just the direct function call."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    proc = subprocess.run(
        [
            sys.executable, str(MODULE_PATH), "archive-one",
            "--specs-dir", str(specs_dir),
            "--knowledge-dir", str(knowledge_dir),
            "--repo-root", str(repo),
            "--spec-name", "2026-01-01-eligible-spec",
            "--pr-number", "32",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "archived"
    assert "via PR #32" in payload["ledger_line"]
    assert not (specs_dir / "2026-01-01-eligible-spec").exists()


def test_archive_one_cli_subcommand_via_main_in_process(tmp_path: Path) -> None:
    """Same `archive-one` CLI subcommand as the subprocess test above, but
    invoked in-process via `main()` directly (same recipe as
    test_revert_resolve.py's `main([...])` calls) so the CLI subcommand's
    argument wiring and dispatch branch in `main()` — not just `archive_one()`
    itself — is exercised under coverage instrumentation. The subprocess
    variant above stays as the real-CLI-boundary/exit-code check; this one
    exists purely so the new `archive-one` parser/dispatch lines in `main()`
    aren't invisible to line-coverage tooling."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-eligible-spec", "> **Status:** Complete")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = archive_sweep.main(
            [
                "archive-one",
                "--specs-dir", str(specs_dir),
                "--knowledge-dir", str(knowledge_dir),
                "--repo-root", str(repo),
                "--spec-name", "2026-01-01-eligible-spec",
                "--pr-number", "32",
            ]
        )

    assert exit_code == 0
    payload = json.loads(buf.getvalue())
    assert payload["status"] == "archived"
    assert "via PR #32" in payload["ledger_line"]
    assert not (specs_dir / "2026-01-01-eligible-spec").exists()


def test_closed_spec_ledger_line_records_that_it_was_never_built(tmp_path: Path) -> None:
    """A terminal-but-unbuilt spec archives, and its ledger line says so.

    `spec-status.py`'s COMPLETE_FAMILY_PREFIXES deliberately admits `Closed`,
    so "Closed — Not Implemented" is complete-family: the spec is done being
    worked on. But `LEDGER.md` is the one place a future reader scans without
    opening 13 spec files, and an unannotated line there reports a spec that
    was deliberately never built exactly like one that shipped.
    """
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-shipped", "> **Status:** Complete")
    make_spec(
        repo,
        "2026-01-01-never-built",
        "> **Status:** Closed — Not Implemented (measured evidence, 2026-01-01)",
    )
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    result = archive_sweep.sweep(repo, specs_dir, knowledge_dir)

    assert len(result["archived"]) == 2
    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    shipped_line = next(l for l in ledger.splitlines() if "2026-01-01-shipped" in l)
    closed_line = next(l for l in ledger.splitlines() if "2026-01-01-never-built" in l)

    # The closed spec carries its terminal status; the shipped one is unchanged.
    assert "Closed — Not Implemented (measured evidence, 2026-01-01)" in closed_line
    assert "Closed" not in shipped_line
    assert shipped_line.endswith("archived (evidence: no knowledge evidence yet)")


def test_complete_family_note_is_absent_for_plain_complete(tmp_path: Path) -> None:
    """The annotation is trailing and optional — the 41 pre-existing ledger
    lines and every `Complete` spec keep their exact current format."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-01-01-plain", "> **Status:** Completed ✅ (2026-01-01)")
    knowledge_dir = repo / ".writ" / "knowledge"
    commit_all(repo)

    archive_sweep.sweep(repo, specs_dir, knowledge_dir)
    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    line = next(l for l in ledger.splitlines() if "2026-01-01-plain" in l)
    assert line.endswith("archived (evidence: no knowledge evidence yet)")
