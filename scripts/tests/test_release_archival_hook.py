"""Fixture tests for `/release` Step 1.3c's post-merge archival hook (Story 3
of post-merge-archival-hook).

`commands/release.md` is a prose workflow document, not compiled code, so
there is no importable "hook" module to call directly. `run_archival_hook()`
models Step 1.3c's exact control-flow composition -- resolve via
`scripts/resolve-spec-reference.py resolve`, branch on its `result` field,
and (only when `matched`) invoke `scripts/archive-sweep.py archive-one`,
branching purely on its returned `status` field -- then drives that
composition against real fixture directories via subprocess, exactly the way
Step 1.3c's prose describes the two scripts being chained. This mirrors how
`test_archive_sweep.py` and `test_resolve_spec_reference.py` drive their own
CLIs via subprocess against fixture directories (hyphenated filenames,
invoked as subprocess CLIs here rather than imported by path, since the
point under test is the *composition* of the two CLI boundaries, not either
script's internals -- those are already covered by their own test files and
are Readable-only for this story).

`run_archival_hook()` and its fixture helpers live in the shared
`scripts/_archival_hook_model.py` module (extracted by Story 4 Task 4.0) so
this pytest suite and `scripts/eval-post-merge-archival.py`'s smoke scenarios
share one implementation rather than two drifting copies.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODEL_PATH = Path(__file__).resolve().parents[1] / "_archival_hook_model.py"
_SPEC = importlib.util.spec_from_file_location("archival_hook_model", _MODEL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_archival_hook_model = importlib.util.module_from_spec(_SPEC)
sys.modules["archival_hook_model"] = _archival_hook_model
_SPEC.loader.exec_module(_archival_hook_model)

RESOLVER_PATH = _archival_hook_model.RESOLVER_PATH
ARCHIVE_SWEEP_PATH = _archival_hook_model.ARCHIVE_SWEEP_PATH
run_archival_hook = _archival_hook_model.run_archival_hook
_run_git = _archival_hook_model._run_git
init_repo = _archival_hook_model.init_repo
make_spec = _archival_hook_model.make_spec
commit_all = _archival_hook_model.commit_all
empty_knowledge_dir = _archival_hook_model.empty_knowledge_dir
fixed_output_script = _archival_hook_model.fixed_output_script
fake_matched_resolver = _archival_hook_model.fake_matched_resolver


# --- (a) hook fires and archives (matched + eligible) ---


def test_hook_fires_and_archives_on_matched_and_eligible(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-03-15-auth-system", "> **Status:** Complete")
    commit_all(repo)

    result = run_archival_hook(
        branch="feature/auth-system",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=32,
    )

    assert result["archived"] is True
    assert result["spec"] == "2026-03-15-auth-system"
    assert result["status"] == "archived"
    assert "via PR #32" in result["ledger_line"]
    assert not (specs_dir / "2026-03-15-auth-system").exists()
    assert (specs_dir / "archive" / "2026-03-15-auth-system" / "spec.md").exists()

    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "via PR #32" in ledger


def test_hook_archived_unlogged_still_counts_as_archived_for_commit_purposes(
    tmp_path: Path,
) -> None:
    """Task 3.3: `archived_unlogged` is a successful move (the ledger write
    failed, not the `git mv`) -- the hook must still report it as an archive
    outcome, distinct from a genuine skip. `archive-sweep.py`'s own internal
    path to `archived_unlogged` (a `git mv` that succeeds followed by a
    ledger-append that raises) is already covered by
    `test_archive_sweep.py::test_archive_one_ledger_append_failure_returns_archived_unlogged`;
    this test only exercises this composition's own branching for that
    status, via a stand-in `archive-one` boundary."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-05-01-ledger-write-fails", "> **Status:** Complete")
    commit_all(repo)

    fake_archive_sweep = fixed_output_script(
        tmp_path,
        "fake_archive_sweep_unlogged.py",
        json.dumps(
            {
                "status": "archived_unlogged",
                "spec": "2026-05-01-ledger-write-fails",
                "ledger_line": None,
            }
        ),
    )

    result = run_archival_hook(
        branch="feature/ledger-write-fails",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=None,
        archive_sweep_path=fake_archive_sweep,
    )

    assert result["archived"] is True
    assert result["status"] == "archived_unlogged"
    assert result["ledger_line"] is None


# --- (b) resolver returns none/ambiguous -> no archive call made ---


def test_resolver_none_makes_no_archive_call(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-03-15-auth-system", "> **Status:** Complete")
    commit_all(repo)

    result = run_archival_hook(
        branch="totally-unrelated-branch",
        commits="chore: bump deps",
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
    )

    assert result["archived"] is False
    assert result["reason"] == "none"
    assert (specs_dir / "2026-03-15-auth-system").exists()  # untouched


def test_resolver_ambiguous_makes_no_archive_call(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-03-15-auth-system", "> **Status:** Complete")
    make_spec(repo, "2026-04-12-billing-refactor", "> **Status:** Complete")
    commit_all(repo)

    result = run_archival_hook(
        branch="feature/auth-system",
        commits="fix: correct rounding in .writ/specs/2026-04-12-billing-refactor/spec.md",
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
    )

    assert result["archived"] is False
    assert result["reason"] == "ambiguous"
    assert (specs_dir / "2026-03-15-auth-system").exists()
    assert (specs_dir / "2026-04-12-billing-refactor").exists()


# --- (c) resolver matches but archive-one returns a non-archiving status ---


def test_resolver_matches_but_not_eligible_no_further_action(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-01-in-progress-spec", "> **Status:** In Progress")
    commit_all(repo)

    result = run_archival_hook(
        branch="feature/in-progress-spec",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
    )

    assert result["archived"] is False
    assert result["reason"] == "not_eligible"
    assert (specs_dir / "2026-06-01-in-progress-spec").exists()


def test_resolver_matches_but_already_archived_no_further_action(tmp_path: Path) -> None:
    """A live resolver naturally cannot resolve `matched` for an
    already-archived spec (Story 1's folder scan excludes `archive/`
    entirely -- there is nothing left in `specs_dir` to substring-match).
    This scenario only arises from a race between resolve-time and
    archive-call-time, so it's exercised here with a stand-in resolver that
    forces `matched` against a spec fixture-archived up front, letting
    `archive-one`'s own real `already_archived` branch fire."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-02-already-archived", "> **Status:** Complete")
    commit_all(repo)

    first = run_archival_hook(
        branch="feature/already-archived",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=1,
    )
    assert first["archived"] is True

    forced_resolver = fake_matched_resolver(tmp_path, "2026-06-02-already-archived")
    second = run_archival_hook(
        branch="feature/already-archived",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=2,
        resolver_path=forced_resolver,
    )

    assert second["archived"] is False
    assert second["reason"] == "already_archived"
    ledger = (specs_dir / "archive" / "LEDGER.md").read_text(encoding="utf-8")
    assert "via PR #2" not in ledger  # second call produced no new ledger line


def test_resolver_matches_but_collision_no_further_action(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-03-collides", "> **Status:** Complete")
    collision_dest = specs_dir / "archive" / "2026-06-03-collides"
    collision_dest.mkdir(parents=True)
    (collision_dest / "spec.md").write_text("# already here\n", encoding="utf-8")
    commit_all(repo)

    result = run_archival_hook(
        branch="feature/collides",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
    )

    assert result["archived"] is False
    assert result["reason"] == "collision"
    assert (specs_dir / "2026-06-03-collides").exists()  # untouched -- collision, not moved


def test_resolver_matches_but_git_mv_failed_no_further_action(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-04-untracked-spec", "> **Status:** Complete")
    # Never committed -- `git mv` fails ("not under version control").

    result = run_archival_hook(
        branch="feature/untracked-spec",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
    )

    assert result["archived"] is False
    assert result["reason"] == "git_mv_failed"
    assert (specs_dir / "2026-06-04-untracked-spec").exists()  # left in place


# --- (d) a forced/simulated exception anywhere in the chain is caught ---


def test_malformed_resolver_output_is_caught_not_propagated(tmp_path: Path) -> None:
    """Simulates a corrupted/non-JSON resolver stdout (e.g. a future
    regression, or the resolver crashing before it can print its own
    best-effort JSON fallback) -- the hook's guard must swallow the
    `json.JSONDecodeError` rather than let it escape."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-05-whatever", "> **Status:** Complete")
    commit_all(repo)

    broken_resolver = tmp_path / "broken_resolver.py"
    broken_resolver.write_text(
        "import sys\nsys.stdout.write('not json at all')\nsys.exit(0)\n", encoding="utf-8"
    )

    result = run_archival_hook(
        branch="feature/whatever",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
        resolver_path=broken_resolver,
    )

    assert result["archived"] is False
    assert result["reason"] == "exception"
    assert (specs_dir / "2026-06-05-whatever").exists()  # untouched -- never got to archive step


def test_resolver_script_not_found_is_caught_not_propagated(tmp_path: Path) -> None:
    """A missing/renamed resolver script (e.g. a bad path in a future
    `release.md` edit) must degrade to a swallowed no-op, not a crash that
    blocks the release."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-06-whatever-else", "> **Status:** Complete")
    commit_all(repo)

    result = run_archival_hook(
        branch="feature/whatever-else",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
        resolver_path=tmp_path / "does-not-exist.py",
    )

    assert result["archived"] is False
    assert result["reason"] == "exception"
    assert (specs_dir / "2026-06-06-whatever-else").exists()


def test_malformed_archive_sweep_output_is_caught_not_propagated(tmp_path: Path) -> None:
    """Same guard, but the fault is on the second CLI boundary (`archive-one`)
    rather than the resolver -- confirms the try/except wraps the *entire*
    resolve -> archive-call chain, not just the first call."""
    repo = init_repo(tmp_path)
    specs_dir = make_spec(repo, "2026-06-07-second-boundary", "> **Status:** Complete")
    commit_all(repo)

    broken_archive_sweep = tmp_path / "broken_archive_sweep.py"
    broken_archive_sweep.write_text(
        "import sys\nsys.stdout.write('{not: valid json')\nsys.exit(0)\n", encoding="utf-8"
    )

    result = run_archival_hook(
        branch="feature/second-boundary",
        commits=None,
        specs_dir=specs_dir,
        knowledge_dir=empty_knowledge_dir(repo),
        repo_root=repo,
        pr_number=99,
        archive_sweep_path=broken_archive_sweep,
    )

    assert result["archived"] is False
    assert result["reason"] == "exception"
    assert (specs_dir / "2026-06-07-second-boundary").exists()  # untouched


# --- SHA-comparison / --skip-gate structural properties (AC 3-4) are

# release.md prose-structure properties, not testable via this fixture per
# Task 3.1's revised scope -- verified instead via the trace-through
# documented in the coding agent's Story 3 output (Task 3.6).
