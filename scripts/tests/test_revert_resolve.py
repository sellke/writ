#!/usr/bin/env python3
"""Unit tests for scripts/revert-resolve.py.

Each test builds a disposable git repository so the resolver runs against real
`git` history — recorded SHAs, `/ship` `Ref:` footers, phase-state JSON, ghost
(rewritten) SHAs, spec unions, ordering, base computation, and read-only
guarantees. The module filename contains a hyphen, so it is imported by path.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "revert-resolve.py"
_spec = importlib.util.spec_from_file_location("revert_resolve", MODULE_PATH)
rr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rr)  # type: ignore[union-attr]


SPEC_ID = "2026-07-18-sample-spec"

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


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def story_file(spec_id: str, num: int, title: str, commit: str | None) -> str:
    header = [f"# Story {num}: {title}", "", "> **Status:** Complete"]
    if commit is not None:
        header.append(f"> **Commit:** {commit}")
    header += ["", "## User Story", "", "Body."]
    return "\n".join(header) + "\n"


class ResolverFixture(unittest.TestCase):
    """Builds a repo with a spec-scaffold commit + two story commits."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "commit.gpgsign", "false")

        self.spec_dir = self.repo / ".writ" / "specs" / SPEC_ID
        self.stories_dir = self.spec_dir / "user-stories"

        # Commit 0: root/scaffold — first add of spec.md.
        write(self.spec_dir / "spec.md", "# Spec\n\n> **Status:** In Progress\n")
        self.sha_scaffold = commit_all(self.repo, "chore(spec): scaffold sample spec")
        self.default_branch = git(self.repo, "rev-parse", "--abbrev-ref", "HEAD")

        # Commit 1: story 1 implementation.
        write(self.repo / "src" / "one.txt", "one\n")
        self.sha_s1 = commit_all(self.repo, "feat(sample): implement widget one")

        # Commit 2: story 2 implementation.
        write(self.repo / "src" / "two.txt", "two\n")
        self.sha_s2 = commit_all(self.repo, "feat(sample): implement widget two")

        # Story files on disk (working tree) with recorded SHAs.
        write(self.stories_dir / "story-1-one.md",
              story_file(SPEC_ID, 1, "Widget One", self.sha_s1))
        write(self.stories_dir / "story-2-two.md",
              story_file(SPEC_ID, 2, "Widget Two", self.sha_s2))

    def tearDown(self) -> None:
        self._tmp.cleanup()


class RecordedLayerTests(ResolverFixture):
    def test_recorded_present_in_history(self) -> None:
        result = rr.resolve_story(self.repo, "story-1", SPEC_ID)
        self.assertEqual(len(result["commits"]), 1)
        c = result["commits"][0]
        self.assertEqual(c["sha"], self.sha_s1)
        self.assertEqual(c["source"], "recorded")
        self.assertEqual(c["confidence"], "exact")
        self.assertEqual(result["ghost"], [])

    def test_recorded_normalizes_short_sha(self) -> None:
        short = self.sha_s1[:8]
        write(self.stories_dir / "story-1-one.md",
              story_file(SPEC_ID, 1, "Widget One", short))
        result = rr.resolve_story(self.repo, "1", SPEC_ID)
        self.assertEqual(result["commits"][0]["sha"], self.sha_s1)

    def test_base_is_parent_of_earliest(self) -> None:
        result = rr.resolve_story(self.repo, "story-2", SPEC_ID)
        self.assertEqual(result["base"], self.sha_s1)  # parent of s2 is s1


class RefFooterLayerTests(ResolverFixture):
    def test_ref_footer_found_without_recorded(self) -> None:
        # Story 3 has no recorded SHA but a /ship Ref: footer commit.
        write(self.repo / "src" / "three.txt", "three\n")
        sha3 = commit_all(
            self.repo,
            "feat(sample): widget three\n\n"
            f"Ref: .writ/specs/{SPEC_ID}/user-stories/story-3-three.md",
        )
        write(self.stories_dir / "story-3-three.md",
              story_file(SPEC_ID, 3, "Widget Three", None))
        result = rr.resolve_story(self.repo, "story-3", SPEC_ID)
        shas = [c["sha"] for c in result["commits"]]
        self.assertIn(sha3, shas)
        self.assertEqual(
            next(c for c in result["commits"] if c["sha"] == sha3)["source"],
            "ref-footer",
        )

    def test_recorded_and_footer_dedup(self) -> None:
        # Recorded SHA also carries a Ref: footer for the same story -> one entry.
        write(self.repo / "src" / "four.txt", "four\n")
        sha4 = commit_all(
            self.repo,
            "feat(sample): widget four\n\n"
            f"Ref: .writ/specs/{SPEC_ID}/user-stories/story-4-four.md",
        )
        write(self.stories_dir / "story-4-four.md",
              story_file(SPEC_ID, 4, "Widget Four", sha4))
        result = rr.resolve_story(self.repo, "story-4", SPEC_ID)
        self.assertEqual([c["sha"] for c in result["commits"]].count(sha4), 1)
        # recorded wins the source (resolved first).
        self.assertEqual(result["commits"][0]["source"], "recorded")


class GhostLayerTests(ResolverFixture):
    def test_ghost_candidate_for_missing_sha(self) -> None:
        fake = "0" * 40
        write(self.stories_dir / "story-1-one.md",
              story_file(SPEC_ID, 1, "implement widget one", fake))
        result = rr.resolve_story(self.repo, "story-1", SPEC_ID)
        # Missing SHA must NOT appear in commits (never auto-selected).
        self.assertNotIn(fake, [c["sha"] for c in result["commits"]])
        self.assertEqual(len(result["ghost"]), 1)
        ghost = result["ghost"][0]
        self.assertEqual(ghost["recorded"], fake)
        self.assertEqual(ghost["candidate"], self.sha_s1)  # best subject match
        self.assertGreater(ghost["similarity"], 0.5)
        self.assertTrue(any("ghost candidate" in w for w in result["warnings"]))

    def test_no_similar_commit_warns_without_candidate(self) -> None:
        # Empty repo-ish: point at a repo whose only commits are unrelated and
        # title is gibberish below the similarity floor.
        fake = "0" * 40
        write(self.stories_dir / "story-1-one.md",
              story_file(SPEC_ID, 1, "zzzzzzzzzzqqqqqqwwww", fake))
        result = rr.resolve_story(self.repo, "story-1", SPEC_ID)
        # Either a low-similarity candidate below floor (no ghost) — assert no
        # crash and the missing-SHA warning is present.
        self.assertTrue(any(fake in w for w in result["warnings"]))


class SpecUnionTests(ResolverFixture):
    def test_spec_union_includes_stories_and_scaffold(self) -> None:
        result = rr.resolve_spec(self.repo, SPEC_ID)
        shas = [c["sha"] for c in result["commits"]]
        self.assertIn(self.sha_s1, shas)
        self.assertIn(self.sha_s2, shas)
        self.assertIn(self.sha_scaffold, shas)

    def test_spec_ordering_newest_first(self) -> None:
        result = rr.resolve_spec(self.repo, SPEC_ID)
        shas = [c["sha"] for c in result["commits"]]
        # s2 (newest) before s1 before scaffold (oldest).
        self.assertLess(shas.index(self.sha_s2), shas.index(self.sha_s1))
        self.assertLess(shas.index(self.sha_s1), shas.index(self.sha_scaffold))

    def test_spec_base_is_before_scaffold(self) -> None:
        result = rr.resolve_spec(self.repo, SPEC_ID)
        # scaffold is the root commit -> no parent -> base is None + warning.
        self.assertIsNone(result["base"])
        self.assertTrue(any("root commit" in w for w in result["warnings"]))

    def test_spec_dedup(self) -> None:
        result = rr.resolve_spec(self.repo, SPEC_ID)
        shas = [c["sha"] for c in result["commits"]]
        self.assertEqual(len(shas), len(set(shas)))


OTHER_SPEC = "2026-07-19-other-spec"


class SpecScopingTests(unittest.TestCase):
    """Footer and subject matching must stay inside the requested spec.

    Reproduces the stage2-prune-the-base defect: `story 2 --spec X` pulled in
    commits whose `Ref:` footer named Story 2 of *other* specs, and missed the
    `Story 2 (2.N): ...` task commits that implemented X's Story 2.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "commit.gpgsign", "false")
        stories = self.repo / ".writ" / "specs" / SPEC_ID / "user-stories"
        other = self.repo / ".writ" / "specs" / OTHER_SPEC / "user-stories"

        write(self.repo / "README", "root\n")
        commit_all(self.repo, "chore: root")

        # Before the spec exists: a same-numbered task subject (other work).
        write(self.repo / "src" / "early.txt", "early\n")
        self.sha_pre = commit_all(self.repo, "Story 2 (2.1): unrelated earlier work")

        write(self.repo / ".writ" / "specs" / SPEC_ID / "spec.md", "# Spec\n")
        self.sha_scaffold = commit_all(self.repo, "spec: scaffold sample spec")

        # Foreign-spec Ref footer for story-2 (must be excluded).
        write(self.repo / "src" / "foreign.txt", "foreign\n")
        self.sha_foreign_ref = commit_all(
            self.repo,
            "feat(other): foreign story two\n\n"
            f"Ref: .writ/specs/{OTHER_SPEC}/user-stories/story-2-foreign.md",
        )
        # Ref footer naming no spec at all (must be excluded).
        write(self.repo / "src" / "bare.txt", "bare\n")
        self.sha_bare_ref = commit_all(
            self.repo, "feat: bare footer\n\nRef: story-2-something.md")
        # story-20 of the same spec (must not match story-2).
        write(self.repo / "src" / "twenty.txt", "twenty\n")
        self.sha_story20 = commit_all(
            self.repo,
            "feat(sample): story twenty\n\n"
            f"Ref: .writ/specs/{SPEC_ID}/user-stories/story-20-twenty.md",
        )

        # The spec's own task commits for Story 2.
        write(self.repo / "src" / "t22.txt", "t22\n")
        self.sha_t22 = commit_all(self.repo, "Story 2 (2.2): move section A")
        # Interleaved task commit from another spec's Story 2 (touches only
        # the other spec's folder) — must be excluded.
        write(other / "story-2-foreign.md", "# Story 2: Foreign\n")
        self.sha_other_task = commit_all(self.repo, "Story 2 (2.1): other spec task")
        write(self.repo / "src" / "t23.txt", "t23\n")
        self.sha_t23 = commit_all(self.repo, "Story 2 (2.3): move section B")
        # Same-spec Ref footer for story-2 (must be included).
        write(self.repo / "src" / "own.txt", "own\n")
        self.sha_own_ref = commit_all(
            self.repo,
            "fix(sample): follow-up\n\n"
            f"Ref: .writ/specs/{SPEC_ID}/user-stories/story-2-two.md",
        )
        # Story 3 task commit (different story, must be excluded from story 2).
        write(self.repo / "src" / "t31.txt", "t31\n")
        self.sha_t31 = commit_all(self.repo, "Story 3 (3.1): cut section C")

        # Story 2 completion commit, recorded in the story file.
        write(stories / "story-2-two.md", story_file(SPEC_ID, 2, "Two", None))
        self.sha_done = commit_all(self.repo, "Story 2: Two — complete")
        write(stories / "story-2-two.md", story_file(SPEC_ID, 2, "Two", self.sha_done))
        commit_all(self.repo, "Story 2: record completion commit SHA")

        # After completion: a later task subject with the same number.
        write(self.repo / "src" / "late.txt", "late\n")
        self.sha_late = commit_all(self.repo, "Story 2 (2.9): later unrelated work")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _shas(self, result: dict) -> list:
        return [c["sha"] for c in result["commits"]]

    def test_foreign_spec_ref_footer_excluded(self) -> None:
        shas = self._shas(rr.resolve_story(self.repo, "story-2", SPEC_ID))
        self.assertNotIn(self.sha_foreign_ref, shas)
        self.assertNotIn(self.sha_bare_ref, shas)
        self.assertNotIn(self.sha_story20, shas)

    def test_same_spec_ref_footer_included(self) -> None:
        result = rr.resolve_story(self.repo, "story-2", SPEC_ID)
        own = [c for c in result["commits"] if c["sha"] == self.sha_own_ref]
        self.assertEqual(len(own), 1)
        self.assertEqual(own[0]["source"], "ref-footer")

    def test_task_subjects_in_spec_range_included(self) -> None:
        result = rr.resolve_story(self.repo, "story-2", SPEC_ID)
        by_sha = {c["sha"]: c for c in result["commits"]}
        for sha in (self.sha_t22, self.sha_t23):
            self.assertIn(sha, by_sha)
            self.assertEqual(by_sha[sha]["source"], "task-subject")

    def test_task_subjects_outside_spec_excluded(self) -> None:
        shas = self._shas(rr.resolve_story(self.repo, "story-2", SPEC_ID))
        self.assertNotIn(self.sha_pre, shas)         # before the scaffold
        self.assertNotIn(self.sha_late, shas)        # after the completion
        self.assertNotIn(self.sha_other_task, shas)  # another spec's folder
        self.assertNotIn(self.sha_t31, shas)         # another story number

    def test_story_resolves_exactly_its_commits(self) -> None:
        result = rr.resolve_story(self.repo, "story-2", SPEC_ID)
        self.assertEqual(
            self._shas(result),
            [self.sha_done, self.sha_own_ref, self.sha_t23, self.sha_t22],
        )
        # Base is the parent of the earliest task commit.
        self.assertEqual(result["base"], self.sha_story20)

    def test_spec_ref_footer_scoped_to_spec(self) -> None:
        shas = self._shas(rr.resolve_spec(self.repo, SPEC_ID))
        self.assertNotIn(self.sha_foreign_ref, shas)
        self.assertIn(self.sha_story20, shas)
        self.assertIn(self.sha_t22, shas)
        self.assertIn(self.sha_t23, shas)


class PhaseStateLayerTests(ResolverFixture):
    def test_phase_state_commit_resolved(self) -> None:
        state = {
            "schemaVersion": "phase-execution-v2",
            "specs": {SPEC_ID: {"commit": self.sha_s2, "mergeCommit": self.sha_s1}},
        }
        write(self.repo / ".writ" / "state" / "phase-execution-20260718.json",
              json.dumps(state))
        # A fresh spec with no recorded story SHAs still resolves via phase-state.
        (self.stories_dir / "story-1-one.md").write_text(
            story_file(SPEC_ID, 1, "Widget One", None), encoding="utf-8")
        (self.stories_dir / "story-2-two.md").write_text(
            story_file(SPEC_ID, 2, "Widget Two", None), encoding="utf-8")
        result = rr.resolve_spec(self.repo, SPEC_ID)
        sources = {c["source"] for c in result["commits"]}
        self.assertIn("phase-state", sources)

    def test_malformed_phase_state_ignored(self) -> None:
        write(self.repo / ".writ" / "state" / "phase-execution-bad.json",
              "{ not json")
        result = rr.resolve_spec(self.repo, SPEC_ID)  # must not crash
        self.assertTrue(result["commits"])


class MergeWarningTests(ResolverFixture):
    def test_merge_commit_warns(self) -> None:
        git(self.repo, "checkout", "-q", "-b", "feature")
        write(self.repo / "src" / "feat.txt", "feat\n")
        commit_all(self.repo, "feat(sample): branch work")
        git(self.repo, "checkout", "-q", self.default_branch)
        git(self.repo, "-c", "commit.gpgsign=false", "merge", "--no-ff",
            "--no-edit", "feature")
        merge_sha = git(self.repo, "rev-parse", "HEAD")
        write(self.stories_dir / "story-5-merge.md",
              story_file(SPEC_ID, 5, "Merge Story", merge_sha))
        result = rr.resolve_story(self.repo, "story-5", SPEC_ID)
        self.assertTrue(any("merge commit" in w for w in result["warnings"]))


class ReadOnlyTests(ResolverFixture):
    def test_resolver_does_not_mutate_repo(self) -> None:
        before_head = git(self.repo, "rev-parse", "HEAD")
        before_status = git(self.repo, "status", "--porcelain")
        rr.resolve_spec(self.repo, SPEC_ID)
        rr.resolve_story(self.repo, "story-1", SPEC_ID)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), before_head)
        self.assertEqual(git(self.repo, "status", "--porcelain"), before_status)


class ErrorPathTests(ResolverFixture):
    def test_bad_unit(self) -> None:
        with self.assertRaises(rr.ContractError) as ctx:
            rr.resolve(self.repo, "phase", "x")
        self.assertEqual(ctx.exception.code, "bad_unit")

    def test_story_not_found(self) -> None:
        with self.assertRaises(rr.ContractError) as ctx:
            rr.resolve_story(self.repo, "story-99", SPEC_ID)
        self.assertEqual(ctx.exception.code, "story_not_found")

    def test_spec_not_found(self) -> None:
        with self.assertRaises(rr.ContractError) as ctx:
            rr.resolve_spec(self.repo, "no-such-spec")
        self.assertEqual(ctx.exception.code, "spec_not_found")

    def test_bad_story_id(self) -> None:
        with self.assertRaises(rr.ContractError) as ctx:
            rr.resolve_story(self.repo, "storyX", SPEC_ID)
        self.assertEqual(ctx.exception.code, "bad_story_id")

    def test_ambiguous_story_without_spec(self) -> None:
        other = self.repo / ".writ" / "specs" / "2026-01-01-other" / "user-stories"
        write(other / "story-1-x.md", story_file("2026-01-01-other", 1, "X", None))
        with self.assertRaises(rr.ContractError) as ctx:
            rr.resolve_story(self.repo, "story-1", None)
        self.assertEqual(ctx.exception.code, "ambiguous_story")


class CliTests(ResolverFixture):
    def test_main_json_output(self) -> None:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = rr.main(["story", "story-1", "--repo", str(self.repo),
                            "--spec", SPEC_ID, "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["unit"], "story")
        self.assertEqual(payload["schema"], rr.RESULT_SCHEMA)

    def test_main_human_output(self) -> None:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = rr.main(["spec", SPEC_ID, "--repo", str(self.repo)])
        self.assertEqual(code, 0)
        self.assertIn("Revert plan", buf.getvalue())

    def test_main_contract_error_exits_nonzero(self) -> None:
        import contextlib
        import io
        buf = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stdout(buf):
                rr.main(["spec", "missing-spec", "--repo", str(self.repo)])
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("blocker", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
