#!/usr/bin/env python3
"""Unit tests for scripts/pipeline-baseline.py `select` (Story 3 of
2026-09-05-phase11-repair-and-baseline).

Every test builds a throwaway git repository shaped like yuss.app —
`.writ/specs/archive/<folder>/user-stories/story-N-<slug>.md` files with
`> **Status:**` / `> **Commit:**` headers, and commits that touch per-class
source + test file pairs — then runs `select` against it. The module filename
contains a hyphen, so it is imported by path (the `test_phase_state.py`
recipe). Business Rule 2 is enforced here by a `subprocess.run` spy: every
spawned process must be `git`, every git subcommand must be read-only, and
`git status --porcelain` inside the fixture must be byte-identical before and
after every run.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Union
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parent.parent / "pipeline-baseline.py"
_spec = importlib.util.spec_from_file_location("pipeline_baseline", MODULE_PATH)
pb = importlib.util.module_from_spec(_spec)
# Python 3.9's dataclasses resolve string annotations through sys.modules, so
# the module must be registered before it executes.
sys.modules["pipeline_baseline"] = pb
_spec.loader.exec_module(pb)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Fixture builder
# ---------------------------------------------------------------------------

CLEAN_TEST = 'import { foo } from "../foo";\ntest("x", () => expect(foo()).toBe(1));\n'
STRIPE_TEST = 'import Stripe from "stripe";\ntest("x", () => expect(1).toBe(1));\n'
PRISMA_TEST = (
    'import { PrismaClient } from "@prisma/client";\n'
    'jest.mock("@prisma/client");\n'
    'test("x", () => expect(1).toBe(1));\n'
)
PRISMA_LIVE_TEST = 'import { prisma } from "@/lib/prisma";\ntest("x", () => expect(1).toBe(1));\n'
NEXTAUTH_MOCKED_TEST = (
    'import { getServerSession } from "next-auth";\n'
    "jest.mock('next-auth');\n"
    'test("x", () => expect(1).toBe(1));\n'
)


class Repo:
    """A yuss-shaped fixture repository built one commit at a time."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.clock = 1_700_000_000
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        self.git("config", "commit.gpgsign", "false")
        self.commit({"README.md": "seed\n"}, "chore: seed")

    def git(self, *args: str, check: bool = True) -> str:
        env = dict(os.environ)
        stamp = "%d +0000" % self.clock
        env["GIT_AUTHOR_DATE"] = stamp
        env["GIT_COMMITTER_DATE"] = stamp
        proc = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, text=True, env=env, check=check,
        )
        return proc.stdout.strip()

    def write(self, rel: str, content: Union[str, bytes, None]) -> None:
        path = self.root / rel
        if content is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")

    def commit(self, files: dict, message: str, advance: int = 60) -> str:
        """Write `files` (path -> content, None deletes), commit, return SHA.
        Each commit is `advance` seconds later than the previous one so the
        most-recent tie-break is deterministic."""
        self.clock += advance
        for rel, content in files.items():
            self.write(rel, content)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def merge_commit(self, files: dict, message: str) -> str:
        """Commit `files` on a side branch and merge it back with --no-ff so
        the returned SHA has two parents."""
        base = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "-b", "side")
        self.commit(files, message + " (branch)")
        self.git("checkout", "-q", "main")
        self.clock += 60
        self.git("merge", "-q", "--no-ff", "-m", message, "side")
        self.git("branch", "-q", "-D", "side")
        assert self.git("rev-parse", "HEAD^1") == base
        return self.git("rev-parse", "HEAD")

    # -- story files -------------------------------------------------------

    def story(
        self,
        folder: str,
        number: int,
        slug: str,
        *,
        status: str = "Completed ✅",
        commit: Optional[str] = None,
        notes: str = "",
        archived: bool = True,
    ) -> str:
        """Write a story file to disk (uncommitted) and return its
        repo-relative path."""
        base = ".writ/specs/archive" if archived else ".writ/specs"
        rel = "%s/%s/user-stories/story-%d-%s.md" % (base, folder, number, slug)
        header = ["# Story %d: %s" % (number, slug), "", "> **Status:** %s  " % status]
        if commit is not None:
            header.append("> **Commit:** %s" % commit)
        header += ["> **Priority:** High", "> **Dependencies:** None", ""]
        body = ["## User Story", "", "As a user I want %s." % slug, ""]
        body += ["## Acceptance Criteria", "", "- [x] it works", ""]
        if notes:
            body += ["## Notes", "", notes, ""]
        body += ["## Definition of Done", "", "- [x] done", ""]
        self.write(rel, "\n".join(header + body))
        return rel

    def stage_stories(self) -> None:
        """Commit every uncommitted story file with a message the log-grep
        fallback cannot match, so the tree is clean before `select` runs."""
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "chore(archive): sweep")


def four_class_repo(root: Path) -> tuple:
    """The happy-path archive: one admissible story per surface class.

    Returns (repo, {class: story_rel_path}, {class: commit_sha}).
    """
    repo = Repo(root)
    folder = "2026-01-01-alpha"
    paths, shas = {}, {}

    shas["api_route"] = repo.commit(
        {"app/api/foo/route.ts": "export const GET = () => 1;\n",
         "app/api/foo/__tests__/route.test.ts": CLEAN_TEST},
        "feat(api): foo route",
    )
    paths["api_route"] = repo.story(folder, 1, "api-foo", commit=shas["api_route"])

    # Story 2 has no Commit: header; the closing commit names it in the
    # message and touches the (pre-archival) spec folder.
    paths["ui"] = repo.story(folder, 2, "ui-foo", archived=False)
    shas["ui"] = repo.commit(
        {"components/Foo.tsx": "export const Foo = () => null;\n",
         "components/__tests__/Foo.test.tsx": CLEAN_TEST},
        "feat(ui): Story 2 — Foo component",
    )
    # ...and is then swept into the archive (mirrors yuss history).
    repo.write(paths["ui"], None)
    paths["ui"] = repo.story(folder, 2, "ui-foo")
    repo.stage_stories()

    # Story 3: schema is the sole non-test touch and the test mocks the client.
    shas["data_model"] = repo.commit(
        {"prisma/schema.prisma": "model User { id Int @id }\n",
         "lib/__tests__/schema.test.ts": PRISMA_TEST},
        "feat(db): Story 3 schema",
    )
    paths["data_model"] = repo.story(folder, 3, "data-foo", commit=shas["data_model"])

    # Story 4: a refactor (deletions only, no new files) closed by a merge.
    repo.commit(
        {"lib/util.ts": "export const a = 1;\nexport const b = 2;\nexport const c = 3;\n",
         "lib/__tests__/util.test.ts": CLEAN_TEST + "test('b', () => 1);\ntest('c', () => 1);\n"},
        "chore: util pre-refactor",
    )
    shas["refactor"] = repo.merge_commit(
        {"lib/util.ts": "export const a = 1;\n",
         "lib/__tests__/util.test.ts": CLEAN_TEST},
        "refactor(util): Story 4 remove dead helpers",
    )
    paths["refactor"] = repo.story(folder, 4, "refactor-util", commit=shas["refactor"])
    return repo, paths, shas


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


# The git subcommands `select` is allowed to spawn — a literal, not the
# module's own allowlist, so widening READ_ONLY_GIT fails here.
ALLOWED_GIT_SUBCOMMANDS = {"rev-parse", "log", "show", "diff-tree"}


class Spy:
    """Wraps subprocess.run, recording argv while delegating to `real`
    (the genuine subprocess.run, or a test double)."""

    def __init__(self, real=None) -> None:
        self.calls: list = []
        self._real = real or subprocess.run

    def __call__(self, argv, *args, **kwargs):
        self.calls.append(list(argv))
        return self._real(argv, *args, **kwargs)


def invoke(argv: list, repo: Optional[Repo] = None, fake_run=None) -> tuple:
    """Run `pb.main(argv)` with the subprocess spy installed. Returns
    (exit_code, stdout, stderr, spy).

    Every spawned process must be `git` with an allowed read-only subcommand.
    When `repo` is given, every call must also target that repo and its
    `git status --porcelain` and HEAD must be byte-identical afterwards —
    Business Rule 2, asserted on success, refusal, and error paths alike."""
    before = head_before = None
    if repo is not None:
        before = repo.git("status", "--porcelain")
        head_before = repo.git("rev-parse", "HEAD")
    spy = Spy(fake_run)
    out_buf, err_buf = io.StringIO(), io.StringIO()
    code = 0
    original = pb.subprocess.run
    pb.subprocess.run = spy
    try:
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            pb.main(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    finally:
        pb.subprocess.run = original
    for call in spy.calls:
        assert call[0] == "git", call
        assert call[1] == "-C", call
        assert call[3] in ALLOWED_GIT_SUBCOMMANDS, call
        if repo is not None:
            assert call[2] == str(repo.root.resolve()), call
    if repo is not None:
        assert repo.git("status", "--porcelain") == before
        assert repo.git("rev-parse", "HEAD") == head_before
    return code, out_buf.getvalue(), err_buf.getvalue(), spy


def run_select(repo: Repo, out: Path, *extra: str) -> tuple:
    """Run `select` against the fixture repo through `invoke`."""
    return invoke(["select", "--yuss", str(repo.root), "--out", str(out), *extra], repo=repo)


def load(out: Path) -> dict:
    return json.loads(out.read_text(encoding="utf-8"))


def by_class(doc: dict) -> dict:
    return {e["surface_class"]: e for e in doc["selection"]}


def excluded_reasons(doc: dict) -> dict:
    return {e["story_path"]: e["reason"] for e in doc["excluded"]}


def walk_strings(value, path: str = "$"):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk_strings(v, "%s[%d]" % (path, i))
    elif isinstance(value, str):
        yield path, value


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class HappyPathTest(unittest.TestCase):
    def test_four_classes_selected_with_contract_keys(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, paths, shas = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = Path(tmp) / "out" / "2026-09-06-claude-fable-5-1.json"
            code, stdout, stderr, spy = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)

            # Literal key lists: Story 4 reads these names verbatim and Story
            # 5 validates them, so a rename in the module must fail here.
            self.assertEqual(list(doc.keys()), [
                "schema", "model", "generated_at", "yuss_head", "runs_per_story",
                "criteria", "selection", "excluded", "rejection_tally", "runs",
            ])
            self.assertEqual(doc["schema"], "pipeline-baseline-v1")
            self.assertEqual(doc["model"], "claude-fable-5-1")
            self.assertEqual(doc["yuss_head"], repo.git("rev-parse", "HEAD"))
            self.assertIsNone(doc["runs_per_story"])
            self.assertEqual(doc["runs"], [])
            self.assertTrue(doc["generated_at"].endswith("Z"))

            crit = doc["criteria"]
            self.assertEqual(list(crit.keys()), [
                "status_required", "status_pattern", "commit_resolution", "requires_test_file",
                "test_file_globs", "test_file_extensions", "test_files_exclude_deleted",
                "deny_list", "deny_list_scan", "deny_list_match", "live_test_scope",
                "live_test_dirs", "schema_only_relaxation", "surface_classes",
                "class_paths_exclude_test_files", "migration_note_pattern", "migration_note_scope",
                "tie_break", "class_fill_order", "exclusion_cap", "detail_max_chars", "reason_codes",
            ])
            self.assertEqual(crit["live_test_scope"], "story")
            self.assertEqual(crit["live_test_dirs"], [])
            self.assertEqual(crit["exclusion_cap"], 10)
            self.assertEqual(crit["deny_list"], ["prisma", "stripe", "@neondatabase", "next-auth"])
            self.assertIn("transitive imports are not followed", crit["deny_list_scan"])
            self.assertIn("substring", crit["deny_list_match"])
            self.assertEqual(crit["reason_codes"], [
                "status_not_completed", "commit_unresolved", "git_error", "no_test_files",
                "live_service_import", "migration_prerequisite", "no_surface_class", "class_filled",
            ])
            self.assertEqual(crit["surface_classes"]["refactor"],
                             "no new files and net negative lines (renames counted as delete+add)")
            self.assertIn("log_grep_regex", crit["commit_resolution"])
            self.assertNotIn("\\b", crit["commit_resolution"]["log_grep_regex"])
            self.assertEqual(len(crit["commit_resolution"]["log_grep_pathspecs"]), 2)

            sel = by_class(doc)
            self.assertEqual(sorted(sel), ["api_route", "data_model", "refactor", "ui"])
            self.assertEqual(len(doc["selection"]), 4)
            for cls, entry in sel.items():
                self.assertEqual(list(entry.keys()), [
                    "story_path", "spec_folder", "story_id", "story_commit", "parent_sha",
                    "parent_is_merge", "surface_class", "eligible_classes", "test_files",
                    "criteria_values",
                ])
                self.assertEqual(entry["story_path"], paths[cls])
                self.assertEqual(entry["spec_folder"], "2026-01-01-alpha")
                self.assertEqual(entry["story_commit"], shas[cls])
                self.assertEqual(len(entry["parent_sha"]), 40)
                self.assertEqual(entry["parent_sha"], repo.git("rev-parse", shas[cls] + "^1"))
                self.assertEqual(entry["criteria_values"]["deny_list_hits"], 0)
                self.assertFalse(entry["criteria_values"]["migration_note"])
                self.assertGreaterEqual(entry["criteria_values"]["test_file_count"], 1)
                self.assertIn(cls, entry["eligible_classes"])

            self.assertEqual(sel["api_route"]["story_id"], "2026-01-01-alpha/story-1-api-foo")
            self.assertEqual(sel["api_route"]["criteria_values"]["commit_source"], "header")
            self.assertEqual(sel["ui"]["criteria_values"]["commit_source"], "log_grep")
            self.assertEqual(sel["data_model"]["criteria_values"]["deny_list_mocked"], 1)
            self.assertEqual(sel["refactor"]["criteria_values"]["new_files"], 0)
            self.assertLess(sel["refactor"]["criteria_values"]["net_lines"], 0)
            self.assertTrue(sel["refactor"]["parent_is_merge"])
            self.assertFalse(sel["api_route"]["parent_is_merge"])
            self.assertEqual(sel["api_route"]["test_files"],
                             ["app/api/foo/__tests__/route.test.ts"])
            self.assertEqual(doc["excluded"], [])
            self.assertEqual(doc["rejection_tally"], {})
            self.assertTrue(spy.calls)
            # Story 5's validator blocks on any string > 200 chars or with a
            # newline; the criteria block must respect that too.
            for path, value in walk_strings(doc):
                self.assertLessEqual(len(value), 200, path)
                self.assertNotIn("\n", value, path)

    def test_model_override_and_basename_warning(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = Path(tmp) / "baseline.json"
            code, _, stderr, _ = run_select(repo, out, "--model", "claude-x")
            self.assertEqual(code, 0)
            self.assertEqual(load(out)["model"], "claude-x")
            self.assertIn("-claude-x.json", stderr)


class RejectionTest(unittest.TestCase):
    """Each candidate fails exactly one admission rule."""

    def _repo_with_rejects(self, tmp: Path):
        repo, paths, shas = four_class_repo(tmp / "yuss")
        folder = "2026-02-02-beta"
        rejects = {}

        rejects["status_not_completed"] = repo.story(
            folder, 1, "wip", status="In Progress", commit=shas["api_route"])

        rejects["commit_unresolved"] = repo.story(folder, 2, "orphan")

        sha = repo.commit({"app/api/bar/route.ts": "export const GET = () => 2;\n"},
                          "feat(api): bar route, no tests")
        rejects["no_test_files"] = repo.story(folder, 3, "untested", commit=sha)

        sha = repo.commit({"app/api/pay/route.ts": "export const POST = () => 3;\n",
                           "app/api/pay/__tests__/route.test.ts": STRIPE_TEST},
                          "feat(api): pay route")
        rejects["live_service_import"] = repo.story(folder, 4, "stripe", commit=sha)

        sha = repo.commit({"app/api/mig/route.ts": "export const GET = () => 4;\n",
                           "app/api/mig/__tests__/route.test.ts": CLEAN_TEST},
                          "feat(api): mig route")
        rejects["migration_prerequisite"] = repo.story(
            folder, 5, "needs-migration", commit=sha,
            notes="Run the database migration `20260101_add_col` before deploying; it is a prerequisite.")

        sha = repo.commit({"app/api/old/route.ts": "export const GET = () => 5;\n",
                           "app/api/old/__tests__/route.test.ts": CLEAN_TEST},
                          "feat(api): old route", advance=-100_000)
        rejects["class_filled"] = repo.story(folder, 6, "older-api", commit=sha)

        sha = repo.commit({"docs/readme.md": "hello\n", "docs/__tests__/x.test.ts": CLEAN_TEST},
                          "docs: nothing classifiable")
        rejects["no_surface_class"] = repo.story(folder, 7, "docs-only", commit=sha)

        repo.stage_stories()
        return repo, rejects

    def test_each_rejection_reason(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, rejects = self._repo_with_rejects(Path(tmp))
            out = Path(tmp) / "out.json"
            code, stdout, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)
            self.assertEqual(len(doc["selection"]), 4)
            reasons = excluded_reasons(doc)
            for reason, path in rejects.items():
                self.assertEqual(reasons.get(path), reason, (path, reasons))
                self.assertIn(reason, pb.REASONS)
            self.assertEqual(doc["rejection_tally"],
                             {r: 1 for r in rejects})
            for entry in doc["excluded"]:
                self.assertEqual(sorted(entry), ["detail", "reason", "story_path"])
                self.assertLessEqual(len(entry["detail"]), 200)
                self.assertNotIn("import", entry["detail"])
                self.assertNotIn("\n", entry["detail"])
            details = {e["story_path"]: e["detail"] for e in doc["excluded"]}
            self.assertIn("app/api/pay/__tests__/route.test.ts", details[rejects["live_service_import"]])
            self.assertIn("stripe", details[rejects["live_service_import"]])
            self.assertIn("api_route", details[rejects["class_filled"]])

    def test_excluded_cap_is_ten_most_recent_and_tally_counts_all(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            folder = "2026-03-03-gamma"
            paths = [repo.story(folder, n, "wip-%d" % n, status="Not Started") for n in range(1, 13)]
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out)
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(len(doc["excluded"]), 10)
            # Scan order is sorted path order; the ten most recent are the tail.
            expected = sorted(paths)[2:]
            self.assertEqual([e["story_path"] for e in doc["excluded"]], expected)
            self.assertEqual(doc["rejection_tally"], {"status_not_completed": 12})
            self.assertEqual(doc["criteria"]["exclusion_cap"], 10)

    def test_detail_is_truncated_to_200_chars(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            long_path = "app/api/%s/%s/__tests__/route.test.ts" % ("a" * 120, "b" * 120)
            sha = repo.commit({"app/api/long/route.ts": "x\n", long_path: STRIPE_TEST}, "long path")
            p_long = repo.story("2026-03-03-gamma", 1, "long", commit=sha)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out)
            self.assertEqual(code, 0)
            entry = [e for e in load(out)["excluded"] if e["story_path"] == p_long][0]
            full_detail = "%s: stripe" % long_path
            self.assertGreater(len(full_detail), 200)
            self.assertEqual(entry["reason"], "live_service_import")
            self.assertEqual(len(entry["detail"]), 200)
            self.assertEqual(entry["detail"], full_detail[:200])

    def test_excluded_cap_override(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            for n in range(1, 6):
                repo.story("2026-03-03-gamma", n, "wip", status="Blocked")
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out, "--excluded-cap", "2")
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(len(doc["excluded"]), 2)
            self.assertEqual(doc["criteria"]["exclusion_cap"], 2)

    def test_story_30_commit_does_not_resolve_story_3(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            folder = "2026-04-04-delta"
            repo.story(folder, 30, "thirty", archived=False)
            repo.commit({"app/api/t/route.ts": "x\n", "app/api/t/__tests__/t.test.ts": CLEAN_TEST},
                        "feat: Story 30 done")
            path3 = repo.story(folder, 3, "three")
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, _, _ = run_select(repo, out)
            self.assertEqual(code, 1)
            self.assertIn("commit_unresolved=1", stdout)
            self.assertFalse(out.exists())
            # Direct check of the resolver too.
            analysis = pb.resolve_commit(pb.Git(repo.root.resolve()), folder, 3, None)
            self.assertIsNone(analysis[0])
            self.assertEqual(analysis[1], "commit_unresolved")
            del path3

    def test_log_grep_matches_pre_archival_and_archive_pathspecs(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            folder = "2026-04-04-delta"
            # Closing commit touches the *archive* path directly.
            repo.story(folder, 7, "seven")
            sha = repo.commit({"app/api/s/route.ts": "x\n", "app/api/s/__tests__/s.test.ts": CLEAN_TEST},
                              "feat: stories 7-8 closed")
            git = pb.Git(repo.root.resolve())
            self.assertEqual(pb.resolve_commit(git, folder, 7, None), (sha, "log_grep"))
            # A commit that mentions the story but touches neither pathspec is ignored.
            repo.commit({"lib/x.ts": "y\n"}, "feat: Story 9 elsewhere")
            self.assertEqual(pb.resolve_commit(git, folder, 9, None)[1], "commit_unresolved")

    def test_header_commit_bad_sha_falls_back_then_unresolves(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            git = pb.Git(repo.root.resolve())
            self.assertEqual(pb.resolve_commit(git, "f", 1, "deadbeefdeadbeef")[1], "commit_unresolved")

    def test_root_commit_is_commit_unresolved(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            root = repo.git("rev-list", "--max-parents=0", "HEAD")
            repo.story("2026-05-05-eps", 1, "root", commit=root)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, _, _ = run_select(repo, out)
            self.assertEqual(code, 1)
            self.assertIn("commit_unresolved=1", stdout)

    def test_migration_mention_outside_notes_does_not_reject(self) -> None:
        """AC-3.2: the migration-prerequisite rule reads `## Notes` only. A
        story whose Acceptance Criteria name a required migration, with a
        clean Notes section, is admitted."""
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            sha = repo.commit({"app/api/mig2/route.ts": "x\n",
                               "app/api/mig2/__tests__/mig2.test.ts": CLEAN_TEST}, "feat(api): mig2")
            rel = repo.story("2026-02-02-beta", 8, "ac-migration", commit=sha,
                             notes="Ships behind a feature flag.")
            path = repo.root / rel
            text = path.read_text(encoding="utf-8")
            self.assertIn("- [x] it works", text)
            path.write_text(text.replace(
                "- [x] it works",
                "- [x] the database migration `20260101_add_col` must be applied before this ships"),
                encoding="utf-8")
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)
            self.assertNotIn("migration_prerequisite", doc["rejection_tally"])
            entry = by_class(doc)["api_route"]
            self.assertEqual(entry["story_path"], rel)
            self.assertFalse(entry["criteria_values"]["migration_note"])


class TieBreakAndAssignmentTest(unittest.TestCase):
    def test_most_recent_commit_wins_class(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, paths, _ = four_class_repo(Path(tmp) / "yuss")
            folder = "2026-06-06-zeta"
            # Story 9 is newer than the alpha api story but has a *lower*
            # number than story 10, which is older still.
            newer = repo.commit({"app/api/n/route.ts": "x\n", "app/api/n/__tests__/n.test.ts": CLEAN_TEST},
                                "feat(api): newer")
            p9 = repo.story(folder, 9, "newer", commit=newer)
            older = repo.commit({"app/api/o/route.ts": "x\n", "app/api/o/__tests__/o.test.ts": CLEAN_TEST},
                                "feat(api): older", advance=-500_000)
            p10 = repo.story(folder, 10, "older", commit=older)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out)
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(by_class(doc)["api_route"]["story_path"], p9)
            reasons = excluded_reasons(doc)
            self.assertEqual(reasons[p10], "class_filled")
            self.assertEqual(reasons[paths["api_route"]], "class_filled")

    def test_same_commit_tie_goes_to_higher_story_number(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            folder = "2026-06-06-zeta"
            # Build the other three classes first so only api_route is contested.
            ui = repo.commit({"components/A.tsx": "x\n", "components/__tests__/A.test.tsx": CLEAN_TEST}, "ui")
            repo.story(folder, 1, "ui", commit=ui)
            repo.stage_stories()
            dm = repo.commit({"prisma/schema.prisma": "x\n", "lib/__tests__/s.test.ts": PRISMA_TEST}, "dm")
            repo.story(folder, 2, "dm", commit=dm)
            repo.stage_stories()
            repo.commit({"lib/u.ts": "a\nb\nc\n", "lib/__tests__/u.test.ts": CLEAN_TEST + "// x\n"}, "pre")
            rf = repo.commit({"lib/u.ts": "a\n", "lib/__tests__/u.test.ts": CLEAN_TEST}, "refactor")
            repo.story(folder, 3, "rf", commit=rf)
            repo.stage_stories()
            shared = repo.commit({"app/api/x/route.ts": "x\n", "app/api/x/__tests__/x.test.ts": CLEAN_TEST},
                                 "feat: stories 4 and 5")
            p4 = repo.story(folder, 4, "four", commit=shared)
            p5 = repo.story(folder, 5, "five", commit=shared)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)
            self.assertEqual(by_class(doc)["api_route"]["story_path"], p5)
            self.assertEqual(excluded_reasons(doc)[p4], "class_filled")

    def test_sort_key_falls_through_to_lexical_path(self) -> None:
        a = pb.SelectionSortKey(commit_time=5, story_number=2, story_path="b")
        b = pb.SelectionSortKey(commit_time=5, story_number=2, story_path="a")
        self.assertEqual(sorted([a, b], key=pb.preference)[0].story_path, "a")

    def test_same_commit_same_number_tie_goes_to_lexical_path(self) -> None:
        """AC-3.3: one commit closes story 9 in two spec folders. Commit date
        and story number tie, so the lexically smaller `story_path` wins."""
        with TemporaryDirectory() as tmp:
            repo, paths, _ = four_class_repo(Path(tmp) / "yuss")
            shared = repo.commit({"app/api/w/route.ts": "x\n", "app/api/w/__tests__/w.test.ts": CLEAN_TEST},
                                 "feat: closes two spec folders")
            p_zeta = repo.story("2026-06-06-zeta", 9, "nine", commit=shared)
            p_eta = repo.story("2026-06-06-eta", 9, "nine", commit=shared)
            self.assertLess(p_eta, p_zeta)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)
            self.assertEqual(by_class(doc)["api_route"]["story_path"], p_eta)
            reasons = excluded_reasons(doc)
            self.assertEqual(reasons[p_zeta], "class_filled")
            self.assertEqual(reasons[paths["api_route"]], "class_filled")
            self.assertEqual(doc["rejection_tally"], {"class_filled": 2})

    def test_multi_class_story_goes_to_scarcer_class(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, paths, _ = four_class_repo(Path(tmp) / "yuss")
            folder = "2026-07-07-eta"
            # Newest story touches both an API route and a component. ui
            # already has a candidate (alpha story 2); api_route's only
            # candidate besides this one is alpha story 1. Both classes have
            # two eligible candidates -> tie on count, class order breaks it,
            # so add a third ui candidate to make api_route strictly scarcer.
            extra_ui = repo.commit({"components/B.tsx": "x\n", "components/__tests__/B.test.tsx": CLEAN_TEST},
                                   "ui extra")
            repo.story(folder, 1, "ui-extra", commit=extra_ui)
            both = repo.commit({"app/api/z/route.ts": "x\n", "components/Z.tsx": "x\n",
                                "components/__tests__/Z.test.tsx": CLEAN_TEST}, "both")
            p_both = repo.story(folder, 2, "both", commit=both)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out)
            self.assertEqual(code, 0)
            sel = by_class(load(out))
            self.assertEqual(sel["api_route"]["story_path"], p_both)
            self.assertEqual(sel["api_route"]["eligible_classes"], ["api_route", "ui"])
            self.assertEqual(sel["ui"]["story_path"],
                             ".writ/specs/archive/2026-07-07-eta/user-stories/story-1-ui-extra.md")


class ShortClassTest(unittest.TestCase):
    def test_short_class_exits_1_and_does_not_touch_out(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            folder = "2026-08-08-theta"
            api = repo.commit({"app/api/a/route.ts": "x\n", "app/api/a/__tests__/a.test.ts": CLEAN_TEST}, "a")
            repo.story(folder, 1, "a", commit=api)
            repo.story(folder, 2, "wip", status="In Progress", commit=api)
            repo.story(folder, 3, "orphan")
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            out.write_text("KEEP", encoding="utf-8")
            # --force lets the pre-existing file past the early refusal, so
            # what is proved here is that a short class never reaches the writer.
            code, stdout, _, _ = run_select(repo, out, "--force")
            self.assertEqual(code, 1)
            self.assertEqual(out.read_text(encoding="utf-8"), "KEEP")
            lines = [l for l in stdout.splitlines() if l.startswith("select: no admissible story")]
            self.assertEqual(len(lines), 3)
            for cls in ("ui", "data_model", "refactor"):
                self.assertTrue(any("for class %s (" % cls in l for l in lines), lines)
            self.assertIn("2 candidates rejected", lines[0])
            self.assertIn("status_not_completed=1", lines[0])
            self.assertIn("commit_unresolved=1", lines[0])

    def test_short_class_tally_counts_displaced_admissible_stories(self) -> None:
        """AC-3.4: the printed tally accounts for every candidate that could
        have filled a class — including admissible stories another story
        displaced (`class_filled`), not only rule rejections."""
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            folder = "2026-08-08-theta"
            older = repo.commit({"app/api/a/route.ts": "x\n", "app/api/a/__tests__/a.test.ts": CLEAN_TEST}, "a")
            repo.story(folder, 1, "a", commit=older)
            newer = repo.commit({"app/api/b/route.ts": "x\n", "app/api/b/__tests__/b.test.ts": CLEAN_TEST}, "b")
            repo.story(folder, 2, "b", commit=newer)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, _, _ = run_select(repo, out)
            self.assertEqual(code, 1)
            self.assertFalse(out.exists())
            lines = [l for l in stdout.splitlines() if l.startswith("select: no admissible story")]
            self.assertEqual(len(lines), 3)
            for cls, line in zip(("ui", "data_model", "refactor"), lines):
                self.assertEqual(
                    line, "select: no admissible story for class %s (1 candidates rejected: class_filled=1)" % cls)

    def test_empty_archive_exits_2_no_candidates(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            (repo.root / ".writ/specs/archive/2026-01-01-x/user-stories").mkdir(parents=True)
            out = Path(tmp) / "out.json"
            code, _, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 2)
            self.assertIn("no candidates", stderr)
            self.assertFalse(out.exists())


class RefusalTest(unittest.TestCase):
    """Every refusal path runs through `invoke`, so the read-only argv and
    unchanged-porcelain assertions cover invalid `--yuss` too (AC-3.5)."""

    def _run(self, yuss: str, out: Path, *extra: str, repo: Optional[Repo] = None) -> tuple:
        code, stdout, stderr, _ = invoke(
            ["select", "--yuss", yuss, "--out", str(out), *extra], repo=repo)
        return code, stdout, stderr

    def test_missing_yuss(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            code, _, err = self._run(str(Path(tmp) / "nope"), out)
            self.assertEqual(code, 2)
            self.assertIn("nope", err)
            self.assertFalse(out.exists())

    def test_not_a_git_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            plain = Path(tmp) / "plain"
            (plain / ".writ/specs/archive").mkdir(parents=True)
            code, _, err = self._run(str(plain), Path(tmp) / "out.json")
            self.assertEqual(code, 2)
            self.assertIn("not a git repository", err)

    def test_no_archive_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            code, _, err = self._run(str(repo.root), Path(tmp) / "out.json", repo=repo)
            self.assertEqual(code, 2)
            self.assertIn(".writ/specs/archive", err)

    def test_out_inside_yuss_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = repo.root / "baseline.json"
            code, _, err = self._run(str(repo.root), out, repo=repo)
            self.assertEqual(code, 2)
            self.assertIn("inside", err)
            self.assertFalse(out.exists())
            self.assertEqual(repo.git("status", "--porcelain"), "")

    def test_existing_out_requires_force(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            out.write_text('{"runs": [1]}', encoding="utf-8")
            code, _, err = self._run(str(repo.root), out, repo=repo)
            self.assertEqual(code, 2)
            self.assertIn("--force", err)
            self.assertEqual(out.read_text(encoding="utf-8"), '{"runs": [1]}')
            code, _, _ = self._run(str(repo.root), out, "--force", repo=repo)
            self.assertEqual(code, 0)
            self.assertEqual(load(out)["runs"], [])
            self.assertFalse(list(out.parent.glob(".*tmp*")))

    def test_existing_out_is_refused_before_the_archive_scan(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            out.write_text("{}", encoding="utf-8")
            code, _, _, spy = invoke(["select", "--yuss", str(repo.root), "--out", str(out)], repo=repo)
            self.assertEqual(code, 2)
            # Only the repo check ran; no per-candidate log/show/diff-tree calls.
            self.assertEqual([c[3] for c in spy.calls], ["rev-parse"])

    def test_written_file_is_world_readable(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = Path(tmp) / "2026-09-06-claude-fable-5-1.json"
            old_umask = os.umask(0o022)
            try:
                code, _, _, _ = run_select(repo, out)
            finally:
                os.umask(old_umask)
            self.assertEqual(code, 0)
            self.assertEqual(stat.S_IMODE(out.stat().st_mode), 0o644)

    def test_write_json_removes_temp_file_when_replace_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "baselines" / "o.json"
            with mock.patch.object(pb.os, "replace", side_effect=OSError("simulated")):
                with self.assertRaises(OSError):
                    pb.write_json(out, {"schema": pb.SCHEMA})
            self.assertFalse(out.exists())
            # The parent was created, but the sibling temp file was cleaned up.
            self.assertEqual(list(out.parent.iterdir()), [])

    def test_compare_without_paths_is_usage(self) -> None:
        err = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stderr(err):
            pb.main(["compare"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertNotIn("not implemented", err.getvalue())

    def test_tilde_expansion(self) -> None:
        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"HOME": tmp}):
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            repo.stage_stories()
            out = Path(tmp) / "o.json"
            code, _, _ = self._run("~/yuss", out, repo=repo)
            self.assertEqual(code, 0)


class ChangeAnalysisTest(unittest.TestCase):
    def test_rename_counts_as_new_file_and_binary_numstat_is_ignored(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            repo.commit({"lib/a.ts": "1\n2\n3\n4\n", "lib/__tests__/a.test.ts": CLEAN_TEST}, "pre")
            repo.write("lib/a.ts", None)
            repo.write("lib/b.ts", "1\n2\n")
            repo.write("img.png", None)
            (repo.root / "img.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x01")
            repo.write("lib/__tests__/a.test.ts", CLEAN_TEST + "// moved\n")
            repo.git("add", "-A")
            repo.git("commit", "-q", "-m", "refactor: rename a to b")
            sha = repo.git("rev-parse", "HEAD")
            git = pb.Git(repo.root.resolve())
            change = pb.analyze_commit(git, sha)
            self.assertEqual(change.new_files, ["img.png", "lib/b.ts"])
            self.assertIn("lib/a.ts", change.paths)
            self.assertIn("lib/b.ts", change.paths)
            self.assertFalse(pb.is_refactor(change))
            # binary `-\t-` rows contribute nothing to net lines
            self.assertEqual(change.net_lines, 2 - 4 + 1)

    def test_class_predicates_ignore_test_files(self) -> None:
        classes = pb.eligible_classes(
            ["app/api/user/__tests__/x.test.ts", "components/__tests__/y.test.tsx", "lib/z.ts"],
            new_files=["lib/z.ts"], net_lines=3)
        self.assertEqual(classes, [])
        self.assertEqual(pb.eligible_classes(["app/api/u/route.ts", "app/x/page.tsx", "lib/db/q.ts"],
                                             new_files=[], net_lines=-1),
                         ["api_route", "ui", "data_model", "refactor"])

    def test_deleted_test_file_is_not_a_test_file_of_the_commit(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            folder = "2026-11-11-lambda"
            repo.commit({"components/Old.tsx": "x\n", "components/__tests__/Old.test.tsx": CLEAN_TEST}, "pre")
            # Story commit deletes one test file and edits another; the
            # deleted one cannot be read via `git show <commit>:<path>` and
            # cannot be run, so it is neither scanned nor recorded.
            sha = repo.commit({"components/Old.tsx": None, "components/__tests__/Old.test.tsx": None,
                               "components/New.tsx": "y\n", "components/__tests__/New.test.tsx": CLEAN_TEST},
                              "swap")
            repo.story(folder, 1, "swap", commit=sha)
            # A story whose only test touch is a deletion has no test files.
            repo.commit({"lib/gone.ts": "x\n", "lib/__tests__/gone.test.ts": CLEAN_TEST}, "pre2")
            sha2 = repo.commit({"lib/__tests__/gone.test.ts": None}, "drop test")
            p_gone = repo.story(folder, 2, "gone", commit=sha2)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)
            self.assertEqual(doc["rejection_tally"].get("git_error"), None)
            self.assertEqual(by_class(doc)["ui"]["test_files"], ["components/__tests__/New.test.tsx"])
            self.assertEqual(excluded_reasons(doc)[p_gone], "no_test_files")

    def test_test_file_globs(self) -> None:
        yes = ["a.test.ts", "src/b.spec.tsx", "components/__tests__/c.tsx", "tests/e2e/d.ts",
               "tests/integration/fixtures/db-helpers.ts", "x.test.mjs", "y.spec.jsx"]
        no = ["app/api/route.ts", "testsuite/x.ts", "lib/tester.ts",
              "tests/integration/README.md", "tests/fixtures/data.json", "components/__tests__/snap.png"]
        for p in yes:
            self.assertTrue(pb.is_test_file(p), p)
        for p in no:
            self.assertFalse(pb.is_test_file(p), p)


class HeaderParsingTest(unittest.TestCase):
    def test_status_normalization(self) -> None:
        for raw in ("Completed ✅", "Complete", "✅ Completed", "Completed ✅ (2026-07-27)",
                    "Complete ✅", "✅ COMPLETED (100% passing - 18/18 tests)", "  Completed  "):
            self.assertTrue(pb.is_completed(raw), raw)
        for raw in ("Not Started", "In Progress", "Implementation Complete", "Blocked ⚠️", ""):
            self.assertFalse(pb.is_completed(raw), raw)

    def test_commit_header_token(self) -> None:
        full = "db7cef560b46c8cf63352c8adbd7d7f65d029073"
        self.assertEqual(pb.commit_from_header(full), full)
        self.assertEqual(pb.commit_from_header("`%s`" % full), full)
        self.assertEqual(pb.commit_from_header("8d97930"), "8d97930")
        self.assertEqual(pb.commit_from_header("%s (hotfix DEV-004: %s)" % (full, "b" * 40)), full)
        self.assertIsNone(pb.commit_from_header("pending"))
        self.assertIsNone(pb.commit_from_header("abc"))

    def test_parse_story_file(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Repo(Path(tmp) / "yuss")
            rel = repo.story("2026-01-01-f", 12, "twelve", commit="abcdef1", notes="Needs a migration first.")
            cand = pb.parse_story(repo.root.resolve(), repo.root.resolve() / rel)
            self.assertEqual(cand.story_number, 12)
            self.assertEqual(cand.spec_folder, "2026-01-01-f")
            self.assertEqual(cand.story_id, "2026-01-01-f/story-12-twelve")
            self.assertEqual(cand.commit_header, "abcdef1")
            self.assertIn("migration", cand.notes)
            self.assertNotIn("Acceptance", cand.notes)
            self.assertTrue(pb.mentions_migration_prerequisite(cand.notes))
            self.assertFalse(pb.mentions_migration_prerequisite("We added a migration in this story."))


class LiveTestScopeTest(unittest.TestCase):
    def _repo(self, tmp: Path):
        repo, paths, _ = four_class_repo(tmp / "yuss")
        folder = "2026-09-09-iota"
        # Integration test imports the prisma client; sibling unit test is clean.
        sha = repo.commit({"app/api/int/route.ts": "x\n",
                           "tests/integration/int.test.ts": PRISMA_LIVE_TEST,
                           "app/api/int/__tests__/int.test.ts": CLEAN_TEST}, "int")
        p_int = repo.story(folder, 1, "integration", commit=sha)
        # Unit test imports next-auth and mocks it.
        sha = repo.commit({"app/api/auth/route.ts": "x\n",
                           "app/api/auth/__tests__/auth.test.ts": NEXTAUTH_MOCKED_TEST}, "auth")
        p_auth = repo.story(folder, 2, "auth-mocked", commit=sha)
        # A story whose only test lives under tests/e2e and is otherwise clean.
        sha = repo.commit({"app/api/e2e/route.ts": "x\n", "tests/e2e/flow.spec.ts": CLEAN_TEST}, "e2e")
        p_e2e = repo.story(folder, 3, "e2e-only", commit=sha)
        repo.stage_stories()
        return repo, p_int, p_auth, p_e2e

    def test_story_scope_is_strict(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, p_int, p_auth, p_e2e = self._repo(Path(tmp))
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out)
            self.assertEqual(code, 0)
            doc = load(out)
            reasons = excluded_reasons(doc)
            self.assertEqual(reasons[p_int], "live_service_import")
            self.assertEqual(reasons[p_auth], "live_service_import")
            # e2e story is clean by imports, so under story scope it competes
            # for api_route and is the most recent -> wins.
            self.assertEqual(by_class(doc)["api_route"]["story_path"], p_e2e)

    def test_file_scope_drops_live_files(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, p_int, p_auth, p_e2e = self._repo(Path(tmp))
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out, "--live-test-scope", "file")
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(doc["criteria"]["live_test_scope"], "file")
            reasons = excluded_reasons(doc)
            # e2e-only story: its sole test file is live -> rejected.
            self.assertEqual(reasons[p_e2e], "live_service_import")
            # auth story (newest remaining) wins api_route; its mocked import is clean.
            sel = by_class(doc)
            self.assertEqual(sel["api_route"]["story_path"], p_auth)
            self.assertEqual(sel["api_route"]["criteria_values"]["deny_list_mocked"], 1)
            # integration story is admissible but displaced; check its analysis directly.
            self.assertEqual(reasons[p_int], "class_filled")
            git = pb.Git(repo.root.resolve())
            cand = pb.parse_story(repo.root.resolve(), repo.root.resolve() / p_int)
            verdict = pb.admit(git, cand, pb.Rules(live_test_scope="file"))
            self.assertIsNone(verdict.rejection)
            self.assertEqual(verdict.test_files, ["app/api/int/__tests__/int.test.ts"])
            self.assertEqual(verdict.criteria_values["live_test_files_dropped"], 1)
            self.assertEqual(doc["criteria"]["live_test_dirs"], ["tests/integration/", "tests/e2e/"])

    def test_file_scope_drops_unmocked_deny_import_outside_live_dirs(self) -> None:
        """Scope addition: under `file` scope an un-mocked deny import makes
        *that file* live even outside tests/integration|e2e. The story is
        admitted iff a clean sibling remains; a story whose only test file is
        live is rejected with a count-bearing detail. Under the default
        `story` scope both are rejected."""
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            folder = "2026-09-09-iota"
            sha = repo.commit({"app/api/pay/route.ts": "x\n",
                               "app/api/pay/__tests__/pay-live.test.ts": STRIPE_TEST,
                               "app/api/pay/__tests__/pay-unit.test.ts": CLEAN_TEST}, "pay")
            p_mixed = repo.story(folder, 1, "mixed", commit=sha)
            sha = repo.commit({"app/api/only/route.ts": "x\n",
                               "app/api/only/__tests__/only.test.ts": STRIPE_TEST}, "only", advance=-1000)
            p_only = repo.story(folder, 2, "only-live", commit=sha)
            repo.stage_stories()

            out_file = Path(tmp) / "file.json"
            code, stdout, stderr, _ = run_select(repo, out_file, "--live-test-scope", "file")
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out_file)
            entry = by_class(doc)["api_route"]
            self.assertEqual(entry["story_path"], p_mixed)
            self.assertEqual(entry["test_files"], ["app/api/pay/__tests__/pay-unit.test.ts"])
            self.assertEqual(entry["criteria_values"]["test_file_count"], 1)
            self.assertEqual(entry["criteria_values"]["live_test_files_dropped"], 1)
            self.assertEqual(entry["criteria_values"]["deny_list_mocked"], 0)
            only = [e for e in doc["excluded"] if e["story_path"] == p_only][0]
            self.assertEqual(only["reason"], "live_service_import")
            self.assertEqual(only["detail"],
                             "app/api/only/__tests__/only.test.ts: stripe; 0 clean test files of 1")

            out_story = Path(tmp) / "story.json"
            code, _, _, _ = run_select(repo, out_story)
            self.assertEqual(code, 0)
            reasons = excluded_reasons(load(out_story))
            self.assertEqual(reasons[p_mixed], "live_service_import")
            self.assertEqual(reasons[p_only], "live_service_import")

    def test_deny_list_override(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, p_int, _, _ = self._repo(Path(tmp))
            out = Path(tmp) / "out.json"
            code, _, _, _ = run_select(repo, out, "--deny-list", "stripe,@neondatabase")
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(doc["criteria"]["deny_list"], ["stripe", "@neondatabase"])
            self.assertNotEqual(excluded_reasons(doc).get(p_int), "live_service_import")


class GitErrorTest(unittest.TestCase):
    def test_git_failure_maps_to_git_error(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            sha = repo.commit({"lib/k.ts": "x\n", "lib/__tests__/k.test.ts": CLEAN_TEST}, "k")
            repo.story("2026-10-10-kappa", 1, "boom", commit=sha)
            repo.stage_stories()

            real = subprocess.run  # bound before invoke() installs the spy

            def flaky(argv, *a, **kw):
                if "--numstat" in argv and sha in argv:
                    return subprocess.CompletedProcess(argv, 128, "", "fatal: simulated")
                return real(argv, *a, **kw)

            out = Path(tmp) / "out.json"
            code, _, _, _ = invoke(["select", "--yuss", str(repo.root), "--out", str(out)],
                                   repo=repo, fake_run=flaky)
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(doc["rejection_tally"].get("git_error"), 1)
            entry = [e for e in doc["excluded"] if e["reason"] == "git_error"][0]
            self.assertNotIn("simulated", entry["detail"])  # no stderr text leaks
            self.assertLessEqual(len(entry["detail"]), 200)

    def test_git_show_without_header_maps_to_git_error(self) -> None:
        """A `show` that exits 0 with no header lines (truncated output) is a
        `git_error` rejection, not a crash."""
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            sha = repo.commit({"lib/h.ts": "x\n", "lib/__tests__/h.test.ts": CLEAN_TEST}, "h")
            p_h = repo.story("2026-10-10-kappa", 1, "headless", commit=sha)
            repo.stage_stories()
            real = subprocess.run

            def truncated(argv, *a, **kw):
                if "--numstat" in argv and sha in argv:
                    return subprocess.CompletedProcess(argv, 0, "", "")
                return real(argv, *a, **kw)

            out = Path(tmp) / "out.json"
            code, _, _, _ = invoke(["select", "--yuss", str(repo.root), "--out", str(out)],
                                   repo=repo, fake_run=truncated)
            self.assertEqual(code, 0)
            doc = load(out)
            self.assertEqual(excluded_reasons(doc)[p_h], "git_error")
            self.assertEqual(doc["rejection_tally"], {"git_error": 1})
            entry = [e for e in doc["excluded"] if e["reason"] == "git_error"][0]
            self.assertIn("no header", entry["detail"])
            self.assertLessEqual(len(entry["detail"]), 200)

    def test_git_helper_refuses_write_subcommands(self) -> None:
        with TemporaryDirectory() as tmp:
            git = pb.Git(Path(tmp))
            with self.assertRaises(pb.GitError):
                git.run("checkout", "main")

    def test_non_utf8_test_file_does_not_abort_the_run(self) -> None:
        with TemporaryDirectory() as tmp:
            repo, _, _ = four_class_repo(Path(tmp) / "yuss")
            latin1 = b'import { foo } from "../foo";\n// caf\xe9 \xff\xfe\ntest("x", () => 1);\n'
            sha = repo.commit({"app/api/l1/route.ts": "x\n",
                               "app/api/l1/__tests__/l1.test.ts": latin1}, "latin-1 test")
            p_l1 = repo.story("2026-12-12-mu", 1, "latin1", commit=sha)
            repo.stage_stories()
            out = Path(tmp) / "out.json"
            code, stdout, stderr, _ = run_select(repo, out)
            self.assertEqual(code, 0, stdout + stderr)
            doc = load(out)
            # Newest api_route candidate; its undecodable bytes were replaced, not fatal.
            self.assertEqual(by_class(doc)["api_route"]["story_path"], p_l1)
            self.assertNotIn("git_error", doc["rejection_tally"])


# ---------------------------------------------------------------------------
# Story 5: validate / compare fixtures (eight-record docs, never the committed
# select skeleton under .writ/eval/baselines/)
# ---------------------------------------------------------------------------


def _hex(n: int) -> str:
    return "%040x" % n


def _selection_entry(i: int) -> dict:
    return {
        "story_path": "s%d.md" % i,
        "spec_folder": "f%d" % i,
        "story_id": "f%d/story-%d" % (i, i),
        "story_commit": _hex(i),
        "parent_sha": _hex(100 + i),
        "parent_is_merge": False,
        "surface_class": pb.SURFACE_CLASSES[i],
        "eligible_classes": [pb.SURFACE_CLASSES[i]],
        "test_files": ["t%d.test.ts" % i],
        "criteria_values": {"status": "Completed"},
    }


def _filled_run(story_id: str, run: int, **metrics) -> dict:
    rec = pb._null_record(story_id, run, "2026-09-06T00:00:00Z")
    rec["status"] = "complete"
    rec["gates"]["gate4_tests"]["integrity"] = None
    rec["wall_clock_s"] = metrics.get("wall_clock_s", 10.0 + run)
    rec["num_turns"] = metrics.get("num_turns", 4)
    rec["tokens"] = {
        "input": metrics.get("tin", 100), "output": metrics.get("tout", 50),
        "cache_read": metrics.get("tread", 10), "cache_creation": metrics.get("tcreate", 1),
    }
    rec["tokens_main_thread"] = dict(rec["tokens"])
    rec["cost_usd"] = metrics.get("cost_usd", 0.5)
    rec["interrupts"] = {
        "ask_user_question": metrics.get("ask", 0),
        "status_blocked": metrics.get("blocked", 0),
    }
    rec["review_iterations"] = metrics.get("review_iterations", 1)
    rec["exit_criteria"]["rederived"] = metrics.get("rederived", "met")
    rec["invocation"]["argv"] = ["claude", "-p", "go"]
    rec["invocation"]["model"] = "claude-fable-5-1"
    rec["invocation"]["permission_mode"] = "bypass"
    return rec


def clean_baseline(*, model: str = "claude-fable-5-1", runs_per_story: int = 2,
                   metric_fn=None, cost_usd=0.5) -> dict:
    selection = [_selection_entry(i) for i in range(4)]
    runs = []
    for entry in selection:
        for n in range(1, runs_per_story + 1):
            extra = metric_fn(entry["story_id"], n) if metric_fn else {}
            extra.setdefault("cost_usd", cost_usd)
            runs.append(_filled_run(entry["story_id"], n, **extra))
    return {
        "schema": pb.SCHEMA,
        "model": model,
        "generated_at": "2026-09-06T00:00:00Z",
        "yuss_head": _hex(1),
        "runs_per_story": runs_per_story,
        "criteria": {"status_required": "Completed"},
        "selection": selection,
        "excluded": [],
        "rejection_tally": {},
        "runs": runs,
    }


def write_baseline(directory: Path, doc: dict, name: str = "2026-09-06-claude-fable-5-1.json") -> Path:
    path = directory / name
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return path


def invoke_cmd(argv: list) -> tuple:
    """Like `invoke`, but validate/compare never spawn git."""
    return invoke(argv)


class ValidateTest(unittest.TestCase):
    def _validate(self, tmp: Path, doc: dict, name: str = "2026-09-06-claude-fable-5-1.json") -> tuple:
        path = write_baseline(Path(tmp), doc, name)
        return invoke_cmd(["validate", str(path)]) + (path,)

    def test_clean_eight_record_fixture_exits_0(self) -> None:
        with TemporaryDirectory() as tmp:
            code, stdout, stderr, _, _ = self._validate(tmp, clean_baseline())
            self.assertEqual(code, 0, stdout + stderr)
            self.assertEqual(stdout.strip(), "")

    def test_astra_filename_segment_is_not_tied_to_default_model(self) -> None:
        with TemporaryDirectory() as tmp:
            doc = clean_baseline(model="claude-opus-4-1")
            code, stdout, stderr, _, _ = self._validate(
                tmp, doc, "2026-09-06-claude-opus-4-1.json")
            self.assertEqual(code, 0, stdout + stderr)

    def _assert_finding(self, doc: dict, needle: str, name: str = "2026-09-06-claude-fable-5-1.json") -> str:
        with TemporaryDirectory() as tmp:
            code, stdout, stderr, _, _ = self._validate(tmp, doc, name)
            self.assertEqual(code, 1, stdout + stderr)
            self.assertTrue(stdout.strip(), "expected path: reason lines")
            self.assertIn(needle, stdout)
            for line in stdout.splitlines():
                self.assertIn(": ", line)
            return stdout

    def test_wrong_schema(self) -> None:
        doc = clean_baseline()
        doc["schema"] = "pipeline-baseline-v0"
        self._assert_finding(doc, "$.schema")

    def test_missing_schema(self) -> None:
        doc = clean_baseline()
        del doc["schema"]
        self._assert_finding(doc, "$.schema")

    def test_missing_model(self) -> None:
        doc = clean_baseline()
        del doc["model"]
        self._assert_finding(doc, "$.model")

    def test_model_does_not_match_filename_segment(self) -> None:
        doc = clean_baseline(model="claude-fable-5-1")
        self._assert_finding(doc, "$.model", "2026-09-06-claude-opus-4-1.json")

    def test_missing_criteria(self) -> None:
        doc = clean_baseline()
        del doc["criteria"]
        self._assert_finding(doc, "$.criteria")

    def test_selection_count_not_four(self) -> None:
        doc = clean_baseline()
        doc["selection"] = doc["selection"][:3]
        doc["runs"] = [r for r in doc["runs"] if r["story_id"] != "f3/story-3"]
        self._assert_finding(doc, "$.selection")

    def test_selection_not_a_list(self) -> None:
        doc = clean_baseline()
        doc["selection"] = {"stories": doc["selection"]}
        self._assert_finding(doc, "$.selection")

    def test_runs_count_not_runs_per_story_times_four(self) -> None:
        doc = clean_baseline()
        doc["runs"] = doc["runs"][:7]
        self._assert_finding(doc, "$.runs")

    def test_runs_per_story_null(self) -> None:
        doc = clean_baseline()
        doc["runs_per_story"] = None
        out = self._assert_finding(doc, "$.runs_per_story")
        self.assertNotIn("NoneType", out)

    def test_run_missing_run_keys_field(self) -> None:
        doc = clean_baseline()
        del doc["runs"][0]["wall_clock_s"]
        out = self._assert_finding(doc, "$.runs[0]")
        self.assertIn("wall_clock_s", out)

    def test_string_over_200_chars(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "x" * 201
        self._assert_finding(doc, "$.runs[0].reason")

    def test_sk_ant_leak(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "sk-ant-api03-short"
        self._assert_finding(doc, "sk-ant-")

    def test_line_start_import(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "import os"
        self._assert_finding(doc, "$.runs[0].reason")

    def test_line_start_def(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "def helper():"
        self._assert_finding(doc, "$.runs[0].reason")

    def test_line_start_function(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "function helper() {"
        self._assert_finding(doc, "$.runs[0].reason")

    def test_human_assistant_turn_markers(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "Human: hello"
        self._assert_finding(doc, "$.runs[0].reason")
        doc["runs"][0]["reason"] = "Assistant: hi"
        self._assert_finding(doc, "$.runs[0].reason")

    def test_import_not_at_line_start_is_not_a_leak(self) -> None:
        doc = clean_baseline()
        doc["runs"][0]["reason"] = "did not import secret"
        with TemporaryDirectory() as tmp:
            code, stdout, stderr, _, _ = self._validate(tmp, doc)
            self.assertEqual(code, 0, stdout + stderr)


class CompareTest(unittest.TestCase):
    def test_identical_selections_equal_runs_per_story_exits_0(self) -> None:
        with TemporaryDirectory() as tmp:
            a = write_baseline(Path(tmp), clean_baseline(), "2026-09-06-claude-fable-5-1.json")
            bdoc = clean_baseline(metric_fn=lambda sid, n: {"wall_clock_s": 20.0 + n})
            b = write_baseline(Path(tmp), bdoc, "2026-09-07-claude-fable-5-1.json")
            code, stdout, stderr, _ = invoke_cmd(["compare", str(a), str(b)])
            self.assertEqual(code, 0, stdout + stderr)
            self.assertIn("wall_clock_s", stdout)
            self.assertIn("delta", stdout.lower())
            self.assertIn("f0/story-0", stdout)

    def test_unequal_runs_per_story_uses_median(self) -> None:
        with TemporaryDirectory() as tmp:
            def a_fn(sid, n):
                return {"wall_clock_s": 10.0 if n == 1 else 20.0}

            def b_fn(sid, n):
                return {"wall_clock_s": float(10 * n)}

            a = write_baseline(Path(tmp), clean_baseline(runs_per_story=2, metric_fn=a_fn),
                               "2026-09-06-claude-fable-5-1.json")
            b = write_baseline(Path(tmp), clean_baseline(runs_per_story=3, metric_fn=b_fn),
                               "2026-09-07-claude-fable-5-1.json")
            code, stdout, stderr, _ = invoke_cmd(["compare", str(a), str(b)])
            self.assertEqual(code, 0, stdout + stderr)
            # A median(10, 20)=15; B median(10, 20, 30)=20; delta 5
            self.assertRegex(stdout, r"wall_clock_s\s+15\S*\s+20\S*\s+5")

    def test_mismatched_selection_exits_2_names_first_story_no_table(self) -> None:
        with TemporaryDirectory() as tmp:
            adoc = clean_baseline()
            bdoc = clean_baseline()
            bdoc["selection"][1]["story_path"] = "other.md"
            a = write_baseline(Path(tmp), adoc, "2026-09-06-claude-fable-5-1.json")
            b = write_baseline(Path(tmp), bdoc, "2026-09-07-claude-fable-5-1.json")
            code, stdout, stderr, _ = invoke_cmd(["compare", str(a), str(b)])
            self.assertEqual(code, 2)
            combined = stdout + stderr
            self.assertIn("s1.md", combined)
            self.assertNotIn("wall_clock_s", combined)
            self.assertNotRegex(combined, r"(?i)\bdelta\b")

    def test_mismatched_parent_sha_exits_2(self) -> None:
        with TemporaryDirectory() as tmp:
            adoc = clean_baseline()
            bdoc = clean_baseline()
            bdoc["selection"][0]["parent_sha"] = _hex(999)
            a = write_baseline(Path(tmp), adoc, "2026-09-06-claude-fable-5-1.json")
            b = write_baseline(Path(tmp), bdoc, "2026-09-07-claude-fable-5-1.json")
            code, stdout, stderr, _ = invoke_cmd(["compare", str(a), str(b)])
            self.assertEqual(code, 2)
            self.assertIn("s0.md", stdout + stderr)
            self.assertNotIn("wall_clock_s", stdout + stderr)

    def test_compare_file_with_itself_all_zero_deltas(self) -> None:
        with TemporaryDirectory() as tmp:
            path = write_baseline(Path(tmp), clean_baseline())
            code, stdout, stderr, _ = invoke_cmd(["compare", str(path), str(path)])
            self.assertEqual(code, 0, stdout + stderr)
            deltas = re.findall(r"\s(0(?:\.0+)?|—)\s*$", stdout, flags=re.M)
            self.assertTrue(stdout.strip())
            self.assertNotIn("+", stdout.split("delta")[-1] if "delta" in stdout.lower() else stdout)
            for line in stdout.splitlines():
                if "exit_criteria" in line:
                    continue
                if any(m in line for m in ("wall_clock_s", "num_turns", "cost_usd", "tokens.")):
                    self.assertRegex(line, r"\b0(?:\.0+)?\b")

    def test_cost_usd_all_null_stays_null_not_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            adoc = clean_baseline(cost_usd=None)
            bdoc = clean_baseline(cost_usd=None)
            a = write_baseline(Path(tmp), adoc, "2026-09-06-claude-fable-5-1.json")
            b = write_baseline(Path(tmp), bdoc, "2026-09-07-claude-fable-5-1.json")
            code, stdout, stderr, _ = invoke_cmd(["compare", str(a), str(b)])
            self.assertEqual(code, 0, stdout + stderr)
            cost_lines = [l for l in stdout.splitlines() if "cost_usd" in l]
            self.assertTrue(cost_lines)
            for line in cost_lines:
                self.assertNotRegex(line, r"\b0\.0\b")
                self.assertRegex(line, r"(—|null)")

    def test_empty_runs_prints_nothing_to_compare(self) -> None:
        with TemporaryDirectory() as tmp:
            adoc = clean_baseline()
            adoc["runs"] = []
            adoc["runs_per_story"] = 2
            bdoc = clean_baseline()
            bdoc["runs"] = []
            a = write_baseline(Path(tmp), adoc, "2026-09-06-claude-fable-5-1.json")
            b = write_baseline(Path(tmp), bdoc, "2026-09-07-claude-fable-5-1.json")
            code, stdout, stderr, _ = invoke_cmd(["compare", str(a), str(b)])
            self.assertEqual(code, 0, stdout + stderr)
            self.assertIn("nothing to compare", stdout + stderr)
            self.assertNotIn("wall_clock_s", stdout)

    def test_one_path_is_usage_exit_2(self) -> None:
        err = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stderr(err):
            pb.main(["compare", "only-one.json"])
        self.assertEqual(ctx.exception.code, 2)


class StdlibOnlyTest(unittest.TestCase):
    def test_imports_are_stdlib_only(self) -> None:
        import ast
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        stdlib = getattr(sys, "stdlib_module_names", None)
        if stdlib is None:  # Python 3.9 has no sys.stdlib_module_names
            stdlib = {"argparse", "collections", "dataclasses", "datetime", "fnmatch", "json",
                      "os", "re", "subprocess", "sys", "tempfile", "pathlib", "typing",
                      "statistics", "__future__"}
        self.assertTrue(names <= set(stdlib) | {"__future__"}, names - set(stdlib))


if __name__ == "__main__":
    unittest.main()
