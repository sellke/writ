#!/usr/bin/env python3
"""Unit tests for scripts/exit-criteria.py.

Covers: the classification-doc parser (against the real doc on disk, so
drift between it and the checker is caught by the suite itself), the rollup
precedence table, each of the four `impossible` pre-pass triggers, every
predicate (evaluable-now, needs-run-record, structurally-unobservable), the
pre-Story-2 `unknown` path, and the shadow paths (empty spec set / zero
stories). The module filename contains a hyphen, so it is imported by path.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parent.parent / "exit-criteria.py"
_spec = importlib.util.spec_from_file_location("exit_criteria", MODULE_PATH)
ec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ec)  # type: ignore[union-attr]

REPO_ROOT = MODULE_PATH.parent.parent
REAL_CLASSIFICATION_PATH = REPO_ROOT / ".writ" / "docs" / "exit-criteria-classification.md"

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, env=_GIT_ENV,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit_all(repo: Path, message: str, *, at: str | None = None) -> str:
    """`at` (e.g. "2026-01-01T00:01:00") pins author/committer date so
    ordering-sensitive tests don't depend on same-second wall-clock timing."""
    git(repo, "add", "-A")
    env_override = dict(_GIT_ENV)
    if at is not None:
        env_override["GIT_AUTHOR_DATE"] = at
        env_override["GIT_COMMITTER_DATE"] = at
    proc = subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", "commit", "-m", message],
        capture_output=True, text=True, env=env_override,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git commit failed: {proc.stderr}")
    return git(repo, "rev-parse", "HEAD")


def run_cli(*args: str) -> tuple[int, dict]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = ec.main(list(args))
    return code, json.loads(buf.getvalue())


MINIMAL_PLAN_CLASSIFICATION = """\
# Exit Criteria Classification

## Bucket Table

| Criterion ID | Command | Bucket | One-line reason |
|---|---|---|---|
| `implement-phase.c1` | implement-phase | evaluable-now | a |
| `implement-phase.c2` | implement-phase | evaluable-now (split: presence + ordering) | b |
| `implement-phase.c3` | implement-phase | needs-run-record | c |
| `implement-phase.c4` | implement-phase | structurally-unobservable (report-only) | d |
| `implement-spec.c1` | implement-spec | needs-run-record | e |
| `implement-spec.c2` | implement-spec | evaluable-now | f |
| `implement-spec.c3` | implement-spec | needs-run-record | g |
| `implement-story.c1` | implement-story | Scope: excluded | h |
| `implement-story.c2` | implement-story | Scope: excluded | i |
| `implement-story.c3` | implement-story | Scope: excluded | j |
"""


class ClassificationParserTests(unittest.TestCase):
    def test_parses_the_real_classification_doc_on_disk(self) -> None:
        """Parses the actual committed doc -- drift between the doc and the
        checker's expectations is caught here, not just in a fixture copy."""
        registry = ec.load_classification(REAL_CLASSIFICATION_PATH)
        expected = {
            "implement-phase.c1": "evaluable-now",
            "implement-phase.c2": "evaluable-now",
            "implement-phase.c3": "needs-run-record",
            "implement-phase.c4": "structurally-unobservable",
            "implement-spec.c1": "needs-run-record",
            "implement-spec.c2": "evaluable-now",
            "implement-spec.c3": "needs-run-record",
            "implement-story.c1": "excluded",
            "implement-story.c2": "excluded",
            "implement-story.c3": "excluded",
        }
        self.assertEqual(registry, expected)

    def test_bucket_counts_match_the_docs_own_summary(self) -> None:
        registry = ec.load_classification(REAL_CLASSIFICATION_PATH)
        counts: dict[str, int] = {}
        for bucket in registry.values():
            counts[bucket] = counts.get(bucket, 0) + 1
        self.assertEqual(counts["evaluable-now"], 3)
        self.assertEqual(counts["needs-run-record"], 3)
        self.assertEqual(counts["structurally-unobservable"], 1)
        self.assertEqual(counts["excluded"], 3)

    def test_missing_doc_is_impossible(self) -> None:
        with self.assertRaises(ec.Impossible):
            ec.load_classification(Path("/nonexistent/classification.md"))

    def test_doc_with_no_rows_is_impossible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "classification.md"
            write(path, "# Nothing here\n\nNo table.\n")
            with self.assertRaises(ec.Impossible):
                ec.load_classification(path)

    def test_summary_line_backticked_ids_are_not_mistaken_for_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "classification.md"
            write(path, MINIMAL_PLAN_CLASSIFICATION + (
                "\nBucket counts: **evaluable-now: 3** "
                "(`implement-phase.c1`, `implement-phase.c2`, `implement-spec.c2`)\n"
            ))
            registry = ec.load_classification(path)
            self.assertEqual(len(registry), 10)


class RollupTests(unittest.TestCase):
    def test_all_met_is_met(self) -> None:
        criteria = [ec._entry("a", "met", evidence="x"), ec._entry("b", "met", evidence="y")]
        self.assertEqual(ec._rollup(criteria), "met")

    def test_met_and_unknown_is_met(self) -> None:
        criteria = [ec._entry("a", "met", evidence="x"), ec._entry("b", "unknown", reason="n/a")]
        self.assertEqual(ec._rollup(criteria), "met")

    def test_any_unmet_wins_over_met(self) -> None:
        criteria = [ec._entry("a", "met", evidence="x"), ec._entry("b", "unmet", reason="no")]
        self.assertEqual(ec._rollup(criteria), "unmet")

    def test_any_impossible_wins_over_unmet(self) -> None:
        criteria = [
            ec._entry("a", "unmet", reason="no"),
            ec._entry("b", "impossible", reason="boom"),
        ]
        self.assertEqual(ec._rollup(criteria), "impossible")

    def test_all_unknown_is_met(self) -> None:
        criteria = [ec._entry("a", "unknown", reason="x"), ec._entry("b", "unknown", reason="y")]
        self.assertEqual(ec._rollup(criteria), "met")

    def test_exit_code_mapping(self) -> None:
        self.assertEqual(ec.EXIT_CODES["met"], 0)
        self.assertEqual(ec.EXIT_CODES["unmet"], 1)
        self.assertEqual(ec.EXIT_CODES["impossible"], 2)


def write_phase_state(path: Path, **overrides: Any) -> None:
    state = {
        "schemaVersion": 2,
        "phase": "6",
        "phaseBranch": "main",
        "startedAt": "2026-08-12T00:00:00Z",
        "updatedAt": "2026-08-12T00:00:00Z",
        "status": "executing",
        "specOrder": ["spec-a"],
        "specs": {
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                # reconcile requires a truthy mergeCommit for any "integrated"
                # spec (phase-state.py cmd_reconcile); a placeholder sha is
                # fine since reconcile only checks presence, not git validity.
                "worktreePath": None, "agentRunId": None,
                "mergeCommit": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "integrated",
            }
        },
        "challenges": [],
        "knowledgeWritten": [],
    }
    state.update(overrides)
    write(path, json.dumps(state, indent=2))


class PhaseGitFixture(unittest.TestCase):
    """A minimal real git repo standing in for `--repo`, with a `main`
    branch that is also the phase branch, so `_require_git_repo` and
    `reconcile`'s branch-existence checks pass without extra setup."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "commit.gpgsign", "false")
        write(self.repo / "README.md", "root\n")
        commit_all(self.repo, "chore: root commit")
        self.state_path = self.repo / "state.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()


class ImpossibleTriggerTests(PhaseGitFixture):
    def test_missing_state_file_is_impossible(self) -> None:
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.repo / "nope.json"), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "impossible")
        self.assertIn("nope.json", payload["reason"])

    def test_malformed_json_is_impossible(self) -> None:
        write(self.state_path, "{not json")
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "impossible")

    def test_wrong_schema_version_is_impossible(self) -> None:
        write_phase_state(self.state_path, schemaVersion=9)
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertIn("schema", payload["reason"])

    def test_classification_doc_missing_is_impossible(self) -> None:
        write_phase_state(self.state_path)
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(self.repo / "nonexistent.md"),
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "impossible")

    def test_unregistered_criterion_id_is_impossible(self) -> None:
        write_phase_state(self.state_path)
        # A classification doc missing implement-phase.c1's row entirely.
        trimmed = MINIMAL_PLAN_CLASSIFICATION.replace(
            "| `implement-phase.c1` | implement-phase | evaluable-now | a |\n", ""
        )
        classification_path = self.repo / "classification.md"
        write(classification_path, trimmed)
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(classification_path),
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "impossible")
        self.assertIn("implement-phase.c1", payload["reason"])

    def test_not_a_git_repo_is_impossible(self) -> None:
        with tempfile.TemporaryDirectory() as not_a_repo:
            write_phase_state(self.state_path)
            code, payload = run_cli(
                "check", "--command", "implement-phase",
                "--state", str(self.state_path), "--repo", not_a_repo,
                "--classification", str(REAL_CLASSIFICATION_PATH),
            )
            self.assertEqual(code, 2)
            self.assertIn("not a git repository", payload["reason"])

    def test_halt_reported_is_impossible(self) -> None:
        write_phase_state(self.state_path, haltReported={
            "unit": "spec", "bound": 12, "reached": 12, "lastIntegrated": "spec-a",
        })
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertIn("Loop bound tripped", payload["reason"])

    def test_unresolved_challenge_is_impossible(self) -> None:
        write_phase_state(self.state_path, challenges=[
            {"id": "CHAL-1", "spec": "spec-a", "status": "unresolved", "challenge": {}}
        ])
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertIn("Unresolved escalation", payload["reason"])

    def test_resolved_challenge_does_not_trip_the_trigger(self) -> None:
        write_phase_state(self.state_path, challenges=[
            {"id": "CHAL-1", "spec": "spec-a", "status": "resolved", "challenge": {}}
        ])
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        # A *resolved* challenge must never trip the pre-pass trigger -- the
        # run reaches the normal per-criterion evaluation (criteria[] present,
        # no top-level "reason", regardless of what those criteria conclude).
        self.assertIn("criteria", payload)
        self.assertNotIn("reason", payload)

    def test_criterion_recorded_unachievable_is_impossible(self) -> None:
        write_phase_state(self.state_path, exitCriteria=[
            {"id": "roadmap-x", "source": "roadmap", "class": "machine",
             "verdict": "unachievable", "evidence": "measured and withdrawn"}
        ])
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertIn("Criterion recorded unachievable", payload["reason"])

    def test_reconcile_mismatch_is_impossible(self) -> None:
        # phaseBranch names a branch that doesn't exist in this repo.
        write_phase_state(self.state_path, phaseBranch="phase/does-not-exist")
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertIn("State/git mismatch", payload["reason"])


class PhaseC1Tests(PhaseGitFixture):
    def test_empty_spec_set_is_unmet_not_vacuously_met(self) -> None:
        write_phase_state(self.state_path, specOrder=[], specs={})
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c1")
        self.assertEqual(c1["verdict"], "unmet")
        self.assertIn("no spec resolved", c1["reason"])

    def test_non_terminal_spec_is_unmet(self) -> None:
        write_phase_state(self.state_path, specs={
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "implementing",
            }
        })
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c1")
        self.assertEqual(c1["verdict"], "unmet")

    def test_terminal_specs_with_no_quarantine_is_met(self) -> None:
        write_phase_state(self.state_path)  # default fixture: spec-a integrated
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c1")
        self.assertEqual(c1["verdict"], "met")

    def test_quarantine_branch_leaked_into_phase_branch_is_unmet(self) -> None:
        # Build a quarantine branch, then merge it into main (the phase
        # branch) -- the exact violation c1's confinement half must catch.
        git(self.repo, "checkout", "-b", "writ/quarantine/spec-a")
        write(self.repo / "leak.txt", "leaked\n")
        commit_all(self.repo, "feat: leaked quarantine work")
        git(self.repo, "checkout", "main")
        git(self.repo, "merge", "--no-ff", "writ/quarantine/spec-a", "-m", "merge leak")

        write_phase_state(self.state_path, specs={
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": "writ/quarantine/spec-a", "blockedBy": [],
                "uatPlan": None, "evidence": [], "status": "quarantined",
            }
        })
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c1")
        self.assertEqual(c1["verdict"], "unmet")
        self.assertIn("reachable from the phase branch", c1["reason"])

    def test_quarantine_branch_confined_is_met(self) -> None:
        git(self.repo, "branch", "writ/quarantine/spec-a")
        git(self.repo, "checkout", "writ/quarantine/spec-a")
        write(self.repo / "quarantined.txt", "quarantined\n")
        commit_all(self.repo, "feat: quarantined work, never merged")
        git(self.repo, "checkout", "main")

        write_phase_state(self.state_path, specs={
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": "writ/quarantine/spec-a", "blockedBy": [],
                "uatPlan": None, "evidence": [],
                "status": "quarantined", "failure": {"summary": "x", "attempts": 1},
            }
        })
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c1")
        self.assertEqual(c1["verdict"], "met")


def uat_plan_populated(title: str) -> str:
    return (
        f"# UAT Plan: {title}\n\n"
        "## How to Use This Plan\n\n"
        "1. Work through scenarios in order.\n"
        "2. Mark Pass or Fail.\n\n"
        "## Scenario 1\n\nRun the thing. Expect green.\n"
    )


class PhaseC2Tests(PhaseGitFixture):
    def _make_merged_spec(self, spec_id: str, *, plan_text: str | None,
                           plan_commit_first: bool) -> str:
        """Creates a spec folder with spec.md (Complete) and, optionally, a
        uat-plan.md, in a controlled commit order. Returns the merge commit
        SHA to record as the spec's `mergeCommit`."""
        # Pinned, well-separated author/committer dates so ordering is
        # deterministic regardless of how fast the test actually runs (git
        # commit timestamps carry only 1-second resolution).
        spec_dir = self.repo / ".writ" / "specs" / spec_id
        write(spec_dir / "spec.md", "# Spec\n\n> **Status:** Complete\n")
        commit_all(self.repo, f"chore({spec_id}): scaffold", at="2026-01-01T00:00:00")

        if plan_commit_first and plan_text is not None:
            write(spec_dir / "uat-plan.md", plan_text)
            commit_all(self.repo, f"docs({spec_id}): uat plan", at="2026-01-01T00:01:00")

        write(self.repo / "src" / f"{spec_id}.txt", "impl\n")
        completion_sha = commit_all(self.repo, f"feat({spec_id}): implement", at="2026-01-01T00:02:00")

        if not plan_commit_first and plan_text is not None:
            write(spec_dir / "uat-plan.md", plan_text)
            commit_all(self.repo, f"docs({spec_id}): uat plan", at="2026-01-01T00:03:00")

        return completion_sha

    def _spec_record(self, merge_commit: str) -> dict:
        return {
            "dependencies": [], "attempts": 1, "laneBranch": None,
            "worktreePath": None, "agentRunId": None, "mergeCommit": merge_commit,
            "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
            "evidence": [], "status": "integrated",
        }

    def test_no_merged_specs_is_met(self) -> None:
        write_phase_state(self.state_path, specs={
            "spec-a": {
                "dependencies": [], "attempts": 0, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "closed_not_implemented",
                "closure": {"reason": "n/a", "closedAt": "2026-08-12T00:00:00Z"},
            }
        })
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c2")
        self.assertEqual(c2["verdict"], "met")

    def test_missing_uat_plan_is_unmet(self) -> None:
        sha = self._make_merged_spec("spec-a", plan_text=None, plan_commit_first=False)
        write_phase_state(self.state_path, specs={"spec-a": self._spec_record(sha)})
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c2")
        self.assertEqual(c2["verdict"], "unmet")
        self.assertIn("lacks a populated uat-plan.md", c2["reason"])

    def test_stub_uat_plan_is_unmet(self) -> None:
        stub = "# UAT Plan: spec-a\n\n> **Generated:** 2026-08-12\n"
        sha = self._make_merged_spec("spec-a", plan_text=stub, plan_commit_first=False)
        write_phase_state(self.state_path, specs={"spec-a": self._spec_record(sha)})
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c2")
        self.assertEqual(c2["verdict"], "unmet")
        self.assertIn("is a stub", c2["reason"])

    def test_populated_plan_generated_after_completion_is_met(self) -> None:
        sha = self._make_merged_spec(
            "spec-a", plan_text=uat_plan_populated("spec-a"), plan_commit_first=False,
        )
        write_phase_state(self.state_path, specs={"spec-a": self._spec_record(sha)})
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c2")
        self.assertEqual(c2["verdict"], "met")

    def test_populated_plan_generated_before_completion_is_unmet(self) -> None:
        sha = self._make_merged_spec(
            "spec-a", plan_text=uat_plan_populated("spec-a"), plan_commit_first=True,
        )
        write_phase_state(self.state_path, specs={"spec-a": self._spec_record(sha)})
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c2")
        self.assertEqual(c2["verdict"], "unmet")
        self.assertIn("ordering violation", c2["reason"])


class PhaseC3Tests(PhaseGitFixture):
    def test_missing_exit_criteria_is_unknown_pre_story_2(self) -> None:
        # No exitCriteria key at all, and a spec status (closed_not_implemented)
        # that keeps c1/c2 trivially met so c3's own unknown-vs-unmet behavior
        # is isolated rather than drowned out by an unrelated missing uat-plan.
        write_phase_state(self.state_path, specs={
            "spec-a": {
                "dependencies": [], "attempts": 0, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "closed_not_implemented",
                "closure": {"reason": "n/a", "closedAt": "2026-08-12T00:00:00Z"},
            }
        })
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c3 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c3")
        self.assertEqual(c3["verdict"], "unknown")
        self.assertEqual(c3["reason"], ec.PRE_STORY_2_REASON)
        # An unknown pre-Story-2 criterion must not make the whole run unmet.
        self.assertNotEqual(payload["verdict"], "unmet")

    def test_properly_recorded_machine_and_human_criteria_is_met(self) -> None:
        write_phase_state(self.state_path, exitCriteria=[
            {"id": "r1", "source": "roadmap", "class": "machine",
             "verdict": "pass", "evidence": "measured"},
            {"id": "r2", "source": "roadmap", "class": "human",
             "verdict": "handed_off", "evidence": "handed to maintainer"},
        ])
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c3 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c3")
        self.assertEqual(c3["verdict"], "met")

    def test_human_criterion_self_certified_is_unmet(self) -> None:
        write_phase_state(self.state_path, exitCriteria=[
            {"id": "r1", "source": "roadmap", "class": "human",
             "verdict": "pass", "evidence": "self-certified, not handed off"},
        ])
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c3 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c3")
        self.assertEqual(c3["verdict"], "unmet")


class PhaseC4Tests(PhaseGitFixture):
    def test_always_unknown_report_only(self) -> None:
        write_phase_state(self.state_path)
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c4 = next(c for c in payload["criteria"] if c["id"] == "implement-phase.c4")
        self.assertEqual(c4["verdict"], "unknown")
        self.assertEqual(c4["reason"], "declared unobservable: report is transcript-only")


def write_spec_state(path: Path, **overrides: Any) -> None:
    state = {
        "spec": "2026-01-01-example",
        "startedAt": "2026-01-01T00:00:00Z",
        "plan": {"batches": [{"parallel": False, "stories": ["story-1-x"]}]},
        "stories": {"story-1-x": {"status": "complete", "phase": "done"}},
    }
    state.update(overrides)
    write(path, json.dumps(state, indent=2))


class SpecCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.spec_dir = self.repo / "spec-folder"
        self.spec_dir.mkdir(parents=True)
        self.state_path = self.repo / "execution.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_spec_dir_is_impossible(self) -> None:
        write_spec_state(self.state_path)
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.repo / "nonexistent"), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "impossible")

    def test_missing_state_is_impossible(self) -> None:
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.repo / "nope.json"),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "impossible")

    def test_zero_stories_in_batch_is_unmet_not_vacuously_met(self) -> None:
        write_spec_state(self.state_path, stories={})
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c2")
        self.assertEqual(c2["verdict"], "unmet")

    def test_pending_story_is_unmet(self) -> None:
        write_spec_state(self.state_path, stories={
            "story-1-x": {"status": "pending", "phase": None},
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c2")
        self.assertEqual(c2["verdict"], "unmet")
        self.assertIn("story-1-x", c2["reason"])

    def test_complete_skipped_and_failed_stories_are_met(self) -> None:
        write_spec_state(self.state_path, stories={
            "story-1-x": {"status": "complete"},
            "story-2-y": {"status": "skipped", "blockedBy": ["story-1-x"]},
            "story-3-z": {"status": "failed", "reason": "flaky infra, accepted"},
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c2")
        self.assertEqual(c2["verdict"], "met")

    def test_skipped_without_blocking_chain_is_unmet(self) -> None:
        write_spec_state(self.state_path, stories={
            "story-1-x": {"status": "skipped"},
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c2")
        self.assertEqual(c2["verdict"], "unmet")

    def test_failed_without_reason_is_unmet(self) -> None:
        write_spec_state(self.state_path, stories={
            "story-1-x": {"status": "failed"},
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c2 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c2")
        self.assertEqual(c2["verdict"], "unmet")

    def test_c1_missing_preflight_is_unknown_pre_story_2(self) -> None:
        write_spec_state(self.state_path)  # no preflight key
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c1")
        self.assertEqual(c1["verdict"], "unknown")
        self.assertEqual(c1["reason"], ec.PRE_STORY_2_REASON)

    def test_c1_recorded_validated_is_met(self) -> None:
        write_spec_state(self.state_path, preflight={
            "storyDepsValidated": True, "at": "2026-01-01T00:00:00Z",
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c1")
        self.assertEqual(c1["verdict"], "met")

    def test_c1_recorded_invalid_is_unmet(self) -> None:
        write_spec_state(self.state_path, preflight={
            "storyDepsValidated": False, "at": "2026-01-01T00:00:00Z",
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c1 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c1")
        self.assertEqual(c1["verdict"], "unmet")

    def test_c3_missing_post_run_is_unknown_pre_story_2(self) -> None:
        write_spec_state(self.state_path)  # no postRun key
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c3 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c3")
        self.assertEqual(c3["verdict"], "unknown")
        self.assertEqual(c3["reason"], ec.PRE_STORY_2_REASON)

    def test_c3_recorded_passing_is_met(self) -> None:
        write_spec_state(self.state_path, postRun={
            "typecheck": "pass", "testSuite": "pass",
            "contextRewritten": True, "at": "2026-01-01T01:00:00Z",
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c3 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c3")
        self.assertEqual(c3["verdict"], "met")

    def test_c3_recorded_failing_testsuite_is_unmet(self) -> None:
        write_spec_state(self.state_path, postRun={
            "typecheck": "pass", "testSuite": "fail",
            "contextRewritten": True, "at": "2026-01-01T01:00:00Z",
        })
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        c3 = next(c for c in payload["criteria"] if c["id"] == "implement-spec.c3")
        self.assertEqual(c3["verdict"], "unmet")

    def test_all_three_criteria_met_gives_overall_met_and_exit_0(self) -> None:
        write_spec_state(
            self.state_path,
            preflight={"storyDepsValidated": True, "at": "2026-01-01T00:00:00Z"},
            postRun={"typecheck": "pass", "testSuite": "pass",
                     "contextRewritten": True, "at": "2026-01-01T01:00:00Z"},
        )
        code, payload = run_cli(
            "check", "--command", "implement-spec",
            "--spec", str(self.spec_dir), "--state", str(self.state_path),
            "--repo", str(self.repo), "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "met")


class PredicateFaultInjectionTests(PhaseGitFixture):
    def test_predicate_raising_becomes_impossible_naming_exception_type(self) -> None:
        write_phase_state(self.state_path)

        def boom() -> dict:
            raise ValueError("synthetic failure")

        result = ec._safe_eval("implement-phase.c1", boom)
        self.assertEqual(result["verdict"], "impossible")
        self.assertIn("ValueError", result["reason"])
        self.assertIn("implement-phase.c1", result["id"])


class OutputShapeTests(PhaseGitFixture):
    def test_criteria_array_has_one_entry_per_classified_criterion(self) -> None:
        write_phase_state(self.state_path)
        code, payload = run_cli(
            "check", "--command", "implement-phase",
            "--state", str(self.state_path), "--repo", str(self.repo),
            "--classification", str(REAL_CLASSIFICATION_PATH),
        )
        self.assertEqual(payload["command"], "implement-phase")
        ids = [c["id"] for c in payload["criteria"]]
        self.assertEqual(ids, [
            "implement-phase.c1", "implement-phase.c2",
            "implement-phase.c3", "implement-phase.c4",
        ])
        for c in payload["criteria"]:
            self.assertIn(c["verdict"], {"met", "unmet", "unknown", "impossible"})
            if c["verdict"] == "met":
                self.assertIn("evidence", c)
            if c["verdict"] in {"unmet", "unknown"}:
                self.assertIn("reason", c)


if __name__ == "__main__":
    unittest.main()
