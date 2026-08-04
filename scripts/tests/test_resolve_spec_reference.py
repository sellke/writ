"""Fixture tests for the shared Spec Reference resolver (Story 1 of
post-merge-archival-hook).

Covers the resolver's three outcomes -- `matched` / `none` / `ambiguous` --
across exact folder-name match, fuzzy/partial branch-name match (common
prefixes stripped), story-file-reference match, a deliberately
conflicting-signal case, cross-signal dedup, and graceful degradation
(missing specs dir, absent branch name). Imported by path, same recipe as
test_archive_sweep.py / test_spec_status.py (hyphenated filename).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "resolve-spec-reference.py"
SPEC = importlib.util.spec_from_file_location("resolve_spec_reference", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
resolve_spec_reference_mod = importlib.util.module_from_spec(SPEC)
sys.modules["resolve_spec_reference"] = resolve_spec_reference_mod
SPEC.loader.exec_module(resolve_spec_reference_mod)

resolve_spec_reference = resolve_spec_reference_mod.resolve_spec_reference


def make_spec(specs_dir: Path, spec_id: str, stories: list[str] | None = None) -> None:
    folder = specs_dir / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "spec.md").write_text(f"# Spec: {spec_id}\n", encoding="utf-8")
    if stories:
        stories_dir = folder / "user-stories"
        stories_dir.mkdir(parents=True, exist_ok=True)
        for name in stories:
            (stories_dir / name).write_text(f"# {name}\n", encoding="utf-8")


def test_exact_folder_name_substring_in_branch_matches(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference("2026-03-15-auth-system", [], specs_dir)

    assert result["result"] == "matched"
    assert result["spec"] == "2026-03-15-auth-system"


def test_fuzzy_partial_branch_name_match_ignores_common_prefix(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-07-11-leanness-guardian")

    result = resolve_spec_reference("feat/leanness-guardian", [], specs_dir)

    assert result["result"] == "matched"
    assert result["spec"] == "2026-07-11-leanness-guardian"


def test_story_file_reference_in_commit_message_matches(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(
        specs_dir,
        "2026-04-12-session-management",
        stories=["story-3-session-management.md"],
    )

    result = resolve_spec_reference(
        None,
        ["feat(auth): implement story-3-session-management.md timeout logic"],
        specs_dir,
    )

    assert result["result"] == "matched"
    assert result["spec"] == "2026-04-12-session-management"


def test_zero_matches_returns_none(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference("totally-unrelated-branch", ["chore: bump deps"], specs_dir)

    assert result["result"] == "none"
    assert result["spec"] is None
    assert result["candidates"] == []


def test_conflicting_signals_across_two_specs_is_ambiguous(tmp_path: Path) -> None:
    """Branch name suggests spec A; a commit references spec B's story file."""
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")
    make_spec(
        specs_dir,
        "2026-04-12-billing-refactor",
        stories=["story-1-invoice-totals.md"],
    )

    result = resolve_spec_reference(
        "feature/auth-system",
        ["fix: correct rounding in story-1-invoice-totals.md"],
        specs_dir,
    )

    assert result["result"] == "ambiguous"
    assert result["spec"] is None
    assert set(result["candidates"]) == {"2026-03-15-auth-system", "2026-04-12-billing-refactor"}


def test_same_spec_from_both_signals_dedupes_to_matched(tmp_path: Path) -> None:
    """Arch-check finding: branch-name signal and commit-message signal both
    resolving to the SAME spec folder must dedupe to `matched`, not
    `ambiguous`, even though two independent signals fired."""
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference(
        "feature/auth-system",
        ["feat(auth): wire up .writ/specs/2026-03-15-auth-system/spec.md changes"],
        specs_dir,
    )

    assert result["result"] == "matched"
    assert result["spec"] == "2026-03-15-auth-system"
    assert result["candidates"] == []


def test_missing_specs_dir_is_none_not_an_error(tmp_path: Path) -> None:
    specs_dir = tmp_path / "does-not-exist"

    result = resolve_spec_reference("feature/anything", ["chore: whatever"], specs_dir)

    assert result["result"] == "none"
    assert result["spec"] is None


def test_empty_branch_name_skips_signal_one_falls_back_to_commits(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference(
        "",
        ["feat: touches .writ/specs/2026-03-15-auth-system/spec.md"],
        specs_dir,
    )

    assert result["result"] == "matched"
    assert result["spec"] == "2026-03-15-auth-system"


def test_none_branch_name_skips_signal_one_falls_back_to_commits(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference(
        None,
        ["feat: touches .writ/specs/2026-03-15-auth-system/spec.md"],
        specs_dir,
    )

    assert result["result"] == "matched"
    assert result["spec"] == "2026-03-15-auth-system"


def test_no_commits_provided_uses_branch_signal_only(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference("2026-03-15-auth-system", None, specs_dir)

    assert result["result"] == "matched"


def test_signals_are_reported_for_caller_diagnostics(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    result = resolve_spec_reference("feature/auth-system", [], specs_dir)

    assert result["signals"]["branch_matches"] == ["2026-03-15-auth-system"]
    assert result["signals"]["commit_matches"] == []


def test_generic_readme_story_file_never_causes_a_false_positive(tmp_path: Path) -> None:
    """Every spec's user-stories/ folder has a generic README.md index file
    (Writ convention). A commit merely mentioning the word "README.md" --
    extremely common, e.g. a docs commit about swapping README.md content --
    must not false-positive-match every spec that happens to have one
    (discovered via Task 1.6 dogfooding against this repo's real history)."""
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-01-01-unrelated-spec", stories=["README.md", "story-1-something.md"])
    make_spec(specs_dir, "2026-01-02-another-spec", stories=["README.md", "story-1-else.md"])

    result = resolve_spec_reference(
        None,
        ["docs(release): swap in a temporary README.md for npm publish, then restore README.md"],
        specs_dir,
    )

    assert result["result"] == "none"
    assert result["candidates"] == []


def test_dogfood_real_branch_resolves_only_via_commit_message_signal(tmp_path: Path) -> None:
    """Real repo history: `chore/spec-lifecycle-status-alone-eligibility` does
    NOT substring-match `2026-08-04-spec-lifecycle-archival` by branch name
    alone -- it only resolves via the commit-message `Ref:` line signal
    (see architecture-check finding 4)."""
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-08-04-spec-lifecycle-archival")

    branch_only = resolve_spec_reference(
        "chore/spec-lifecycle-status-alone-eligibility", [], specs_dir
    )
    assert branch_only["result"] == "none"

    with_commits = resolve_spec_reference(
        "chore/spec-lifecycle-status-alone-eligibility",
        [
            "feat(spec-lifecycle): make archive eligibility status-alone\n\n"
            "Ref: .writ/specs/2026-08-04-spec-lifecycle-archival/spec.md\n"
            "Ref: .writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/"
            "story-2-archive-sweep-mechanism.md\n"
        ],
        specs_dir,
    )
    assert with_commits["result"] == "matched"
    assert with_commits["spec"] == "2026-08-04-spec-lifecycle-archival"


def test_cli_resolve_help_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, str(MODULE_PATH), "resolve", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--branch" in proc.stdout
    assert "--specs-dir" in proc.stdout


def test_cli_resolve_smoke_invocation_prints_json_and_exits_zero(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    make_spec(specs_dir, "2026-03-15-auth-system")

    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "resolve",
            "--branch",
            "feature/auth-system",
            "--specs-dir",
            str(specs_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert '"result": "matched"' in proc.stdout


def test_cli_resolve_never_raises_on_nonexistent_specs_dir(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "resolve",
            "--branch",
            "feature/anything",
            "--specs-dir",
            str(tmp_path / "nope"),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert '"result": "none"' in proc.stdout
