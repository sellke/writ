#!/usr/bin/env python3
"""Temp-repo tests for `scripts/ship-branch-cleanup.py` and `/ship` Step 6b
(Story 2 of `2026-11-09-delete-merged-branches`).

Every test builds a bare `origin` and a clone under a temp dir. `origin` has
`main` and `feat`; a second clone (`gh-side`) plays GitHub and lands `feat` on
`main` by merge commit or squash, so the clone's local `main` is behind
`origin/main` until the helper pulls. Git runs with global and system config
off, and the helper runs with no `gh` on PATH.

- A merged branch checked out clean is deleted with `-d`, and the checkout ends
  on the default branch, fast-forwarded [AC-2.1].
- A squash-merged branch whose tip is the PR head is deleted with `-D`; one
  extra local commit keeps it as `local_commits_not_in_pr` [AC-2.2].
- A dirty tree, another worktree, a failed fetch, and an unproven branch are
  kept with their reasons; dirty and unmerged reads `not_merged` (row 7 before
  row 8); a failed `git status`, a failed ff-only pull, and a refused
  `git branch -d` are kept [AC-2.3].
- The opt-out, the default branch, and an absent branch are skipped and change
  no ref [AC-2.4].
- ship.md Step 6b, merge item 7, the merged-PR re-entry in Step 2 and 7.1, the
  completion line, the kept merge ban, the contract row and smoke, and the
  plugin copy [AC-2.5].

Run: uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_ship_branch_cleanup.py
"""

from __future__ import annotations

import atexit
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ship-branch-cleanup.py"
PLUGIN_COPY = REPO_ROOT / "plugins" / "writ" / "scripts" / "ship-branch-cleanup.py"
SHIP = REPO_ROOT / "commands" / "ship.md"
CONTRACT_DOC = REPO_ROOT / ".writ" / "docs" / "agent-cli-contract.md"
CONTRACT_TEST = REPO_ROOT / "scripts" / "tests" / "test_agent_cli_contract.py"
SCHEMA = "ship-branch-cleanup-v1"
REAL_GIT = shutil.which("git") or "/usr/bin/git"


def _path_without_gh() -> str:
    """One private folder linking every executable from git's folder, /usr/bin and /bin
    except `gh`. Dropping whole folders fails where `gh` and `git` share one (CI runners
    install both in /usr/bin)."""
    bin_dir = tempfile.mkdtemp(prefix="ship-cleanup-bin-")
    atexit.register(shutil.rmtree, bin_dir, True)
    for d in (os.path.dirname(REAL_GIT), "/usr/bin", "/bin"):
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for name in names:
            src, dst = os.path.join(d, name), os.path.join(bin_dir, name)
            if name == "gh" or os.path.lexists(dst) or not os.access(src, os.X_OK):
                continue
            os.symlink(src, dst)
    return bin_dir


def _env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PATH": _path_without_gh(),
    })
    return env


ENV = _env()


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run([REAL_GIT, "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false", *args],
                          cwd=str(cwd), env=ENV, capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), done.stderr))
    return done.stdout.strip()


def run_script(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)] + args, cwd=str(cwd), env=ENV,
                          capture_output=True, text=True, timeout=120)


class CleanupCase(unittest.TestCase):
    """A bare origin, a clone `repo` on `feat` (pushed), and a GitHub stand-in."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(os.path.realpath(self._tmp.name))
        self.origin = self.tmp / "origin.git"
        git(self.tmp, "init", "-q", "--bare", str(self.origin))
        git(self.origin, "symbolic-ref", "HEAD", "refs/heads/main")
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "symbolic-ref", "HEAD", "refs/heads/main")
        git(self.repo, "remote", "add", "origin", str(self.origin))
        self.write("app.txt", "one\n")
        git(self.repo, "add", "app.txt")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "push", "-q", "-u", "origin", "main")
        git(self.repo, "checkout", "-q", "-b", "feat")
        self.write("feat.txt", "feature\n")
        git(self.repo, "add", "feat.txt")
        git(self.repo, "commit", "-q", "-m", "feature")
        self.tip = git(self.repo, "rev-parse", "feat")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- fixture helpers ---------------------------------------------------

    def write(self, rel: str, text: str, repo: Optional[Path] = None) -> None:
        (repo or self.repo).joinpath(rel).write_text(text, encoding="utf-8")

    def push_feat(self, upstream: bool = True) -> None:
        git(self.repo, "push", "-q", *(["-u"] if upstream else []), "origin", "feat")

    def land(self, how: str) -> None:
        """Land origin/feat on origin/main from a second clone, as GitHub would."""
        side = self.tmp / "gh-side"
        if not side.exists():
            git(self.tmp, "clone", "-q", str(self.origin), str(side))
        git(side, "fetch", "-q", "origin")
        git(side, "checkout", "-q", "main")
        git(side, "reset", "-q", "--hard", "origin/main")
        if how == "merge":
            git(side, "merge", "-q", "--no-ff", "-m", "Merge feat", "origin/feat")
        else:
            git(side, "merge", "-q", "--squash", "origin/feat")
            git(side, "commit", "-q", "-m", "feat (squash)")
        git(side, "push", "-q", "origin", "main")

    def refs(self) -> str:
        return git(self.repo, "for-each-ref", "--format=%(refname) %(objectname)") + \
            "\nHEAD " + git(self.repo, "symbolic-ref", "-q", "HEAD")

    def branch_exists(self, name: str) -> bool:
        return subprocess.run([REAL_GIT, "show-ref", "--verify", "--quiet", "refs/heads/" + name],
                              cwd=str(self.repo), env=ENV).returncode == 0

    def head_ref(self) -> str:
        return git(self.repo, "symbolic-ref", "-q", "HEAD")

    def delete(self, *extra: str, branch: str = "feat", default: str = "main",
               repo: Optional[Path] = None) -> dict:
        args = ["delete", "--branch", branch, "--default", default,
                "--repo", str(repo or self.repo)] + list(extra)
        result = run_script(args, self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1, result.stdout)
        record = json.loads(lines[0])
        self.assertEqual(set(record), {"schema", "status", "reason", "method", "branch",
                                       "default"})
        self.assertEqual(record["schema"], SCHEMA)
        self.assertEqual((record["branch"], record["default"]), (branch, default))
        return record

    def assertOutcome(self, record: dict, status: str, reason: str,
                      method: Optional[str] = None) -> None:
        self.assertEqual((record["status"], record["reason"], record["method"]),
                         (status, reason, method), record)


# ---------------------------------------------------------------------------
# AC-2.1: merged branch, checked out clean, deleted with -d
# ---------------------------------------------------------------------------

class MergedAncestorTests(CleanupCase):
    def test_ac_2_1_merged_checked_out_clean_is_deleted_with_d(self) -> None:
        """A merge-commit land: switch to main, ff-only pull, `-d`, `deleted`, exit 0. [AC-2.1]"""
        self.push_feat()
        self.land("merge")
        record = self.delete("--pr-state", "MERGED", "--pr-head", self.tip)
        self.assertOutcome(record, "deleted", "merged", "-d")
        self.assertFalse(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/main")
        self.assertEqual(git(self.repo, "rev-parse", "main"),
                         git(self.repo, "rev-parse", "origin/main"))

    def test_ac_2_1_merged_without_pr_flags_uses_the_merged_proof(self) -> None:
        """No `--pr-state` or `--pr-head` (the nil-input path): `--merged` alone deletes with `-d`. [AC-2.1]"""
        self.push_feat()
        self.land("merge")
        self.assertOutcome(self.delete(), "deleted", "merged", "-d")
        self.assertFalse(self.branch_exists("feat"))

    def test_ac_2_1_merged_branch_not_checked_out_is_deleted_without_a_switch(self) -> None:
        """On main already, after a pull, `-d` deletes feat and HEAD stays on main. [AC-2.1]"""
        self.push_feat()
        self.land("merge")
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "pull", "-q", "--ff-only", "origin", "main")
        self.assertOutcome(self.delete(), "deleted", "merged", "-d")
        self.assertFalse(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/main")

    def test_ac_2_1_unreadable_opt_out_value_reads_as_true(self) -> None:
        """A `writ.deleteMergedBranches` value git cannot read as a boolean means true. [AC-2.1]"""
        self.push_feat()
        self.land("merge")
        git(self.repo, "config", "writ.deleteMergedBranches", "maybe")
        self.assertOutcome(self.delete(), "deleted", "merged", "-d")


# ---------------------------------------------------------------------------
# AC-2.2: squash merge, PR proof
# ---------------------------------------------------------------------------

class SquashTests(CleanupCase):
    def test_ac_2_2_squash_with_matching_pr_head_is_deleted_with_capital_d(self) -> None:
        """Squash land, `--pr-state MERGED`, `--pr-head` = local tip: `-D`, `deleted`. [AC-2.2]"""
        self.push_feat()
        self.land("squash")
        record = self.delete("--pr-state", "MERGED", "--pr-head", self.tip)
        self.assertOutcome(record, "deleted", "pr_merged", "-D")
        self.assertFalse(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/main")

    def test_ac_2_2_squash_with_an_extra_local_commit_is_kept(self) -> None:
        """One local commit after the PR head: kept, `local_commits_not_in_pr`, branch and tip intact. [AC-2.2]"""
        self.push_feat()
        self.land("squash")
        self.write("feat.txt", "feature\nmore\n")
        git(self.repo, "commit", "-q", "-am", "unpushed")
        tip = git(self.repo, "rev-parse", "feat")
        git(self.repo, "fetch", "-q", "origin")
        before = self.refs()
        record = self.delete("--pr-state", "MERGED", "--pr-head", self.tip)
        self.assertOutcome(record, "kept", "local_commits_not_in_pr")
        self.assertEqual(git(self.repo, "rev-parse", "feat"), tip)
        self.assertEqual(self.refs(), before)

    def test_ac_2_2_squash_without_pr_head_is_not_merged(self) -> None:
        """Squash land with no `--pr-head`: only the `--merged` proof applies, so kept `not_merged`. [AC-2.2]"""
        self.push_feat()
        self.land("squash")
        self.assertOutcome(self.delete("--pr-state", "MERGED"), "kept", "not_merged")
        self.assertTrue(self.branch_exists("feat"))

    def test_ac_2_2_matching_head_on_an_open_pr_is_not_merged(self) -> None:
        """`--pr-head` equal but `--pr-state OPEN`: no PR proof, kept `not_merged`. [AC-2.2]"""
        self.push_feat()
        self.assertOutcome(self.delete("--pr-state", "OPEN", "--pr-head", self.tip),
                           "kept", "not_merged")
        self.assertTrue(self.branch_exists("feat"))


# ---------------------------------------------------------------------------
# AC-2.3: kept outcomes
# ---------------------------------------------------------------------------

class KeptTests(CleanupCase):
    def test_ac_2_3_dirty_tree_keeps_branch_and_checkout(self) -> None:
        """Merged, checked out, a modified tracked file: kept `dirty_tree`, no switch, the edit stays. [AC-2.3]"""
        self.push_feat()
        self.land("merge")
        self.write("feat.txt", "edited\n")
        self.assertOutcome(self.delete(), "kept", "dirty_tree")
        self.assertTrue(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/feat")
        self.assertEqual((self.repo / "feat.txt").read_text(encoding="utf-8"), "edited\n")

    def test_ac_2_3_unreadable_status_is_kept_as_dirty_tree(self) -> None:
        """Merged, checked out, `git status` fails: kept `dirty_tree`, never read as clean. [AC-2.3]"""
        self.push_feat()
        self.land("merge")
        shim = self.tmp / "bin"
        shim.mkdir()
        (shim / "git").write_text(
            '#!/bin/sh\nfor a in "$@"; do [ "$a" = status ] && exit 128; done\n'
            'exec "%s" "$@"\n' % REAL_GIT, encoding="utf-8")
        (shim / "git").chmod(0o755)
        env = dict(ENV, PATH=str(shim) + os.pathsep + ENV["PATH"])
        result = subprocess.run([sys.executable, str(SCRIPT), "delete", "--branch", "feat",
                                 "--default", "main", "--repo", str(self.repo)],
                                cwd=str(self.tmp), env=env, capture_output=True, text=True,
                                timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertOutcome(json.loads(result.stdout.splitlines()[-1]), "kept", "dirty_tree")
        self.assertTrue(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/feat")

    def test_ac_2_3_dirty_and_unmerged_reads_not_merged(self) -> None:
        """Row 7 precedes row 8: unmerged and dirty reads `not_merged`. [AC-2.3]"""
        self.push_feat()
        self.write("feat.txt", "edited\n")
        self.assertOutcome(self.delete(), "kept", "not_merged")
        self.assertEqual(self.head_ref(), "refs/heads/feat")

    def test_ac_2_3_branch_checked_out_in_another_worktree_is_kept(self) -> None:
        """feat checked out in a linked worktree: kept `checked_out_elsewhere:<path>`. [AC-2.3]"""
        self.push_feat()
        self.land("merge")
        git(self.repo, "checkout", "-q", "main")
        other = self.tmp / "wt"
        git(self.repo, "worktree", "add", "-q", str(other), "feat")
        record = self.delete()
        self.assertEqual(record["status"], "kept")
        prefix = "checked_out_elsewhere:"
        self.assertTrue(record["reason"].startswith(prefix), record)
        self.assertEqual(os.path.realpath(record["reason"][len(prefix):]),
                         os.path.realpath(str(other)))
        self.assertIsNone(record["method"])
        self.assertTrue(self.branch_exists("feat"))

    def test_ac_2_3_run_from_the_worktree_holding_the_branch_is_not_elsewhere(self) -> None:
        """`--repo` is the linked worktree that has feat: not `checked_out_elsewhere`; main is
        checked out in the main worktree, so the switch fails and feat is kept. [AC-2.3]"""
        self.push_feat()
        self.land("merge")
        git(self.repo, "checkout", "-q", "main")
        other = self.tmp / "wt"
        git(self.repo, "worktree", "add", "-q", str(other), "feat")
        self.assertOutcome(self.delete(repo=other), "kept", "switch_failed")
        self.assertTrue(self.branch_exists("feat"))

    def test_ac_2_3_failed_fetch_keeps_the_branch(self) -> None:
        """An unreachable origin: kept `fetch_failed`, no ref changed. [AC-2.3]"""
        self.push_feat()
        self.land("merge")
        git(self.repo, "remote", "set-url", "origin", str(self.tmp / "missing.git"))
        before = self.refs()
        self.assertOutcome(self.delete(), "kept", "fetch_failed")
        self.assertEqual(self.refs(), before)

    def test_ac_2_3_unmerged_branch_is_kept(self) -> None:
        """Neither merged nor PR-proven: kept `not_merged`, exit 0. [AC-2.3]"""
        self.push_feat()
        self.assertOutcome(self.delete(), "kept", "not_merged")
        self.assertTrue(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/feat")

    def test_ac_2_3_failed_ff_only_pull_keeps_branch_and_leaves_default_checked_out(self) -> None:
        """Local main diverged from origin/main: the ff-only pull fails, kept `switch_failed`,
        checkout left on main. [AC-2.3]"""
        self.push_feat()
        git(self.repo, "checkout", "-q", "main")
        self.write("local.txt", "local only\n")
        git(self.repo, "add", "local.txt")
        git(self.repo, "commit", "-q", "-m", "local main commit")
        git(self.repo, "checkout", "-q", "feat")
        self.land("merge")
        self.assertOutcome(self.delete(), "kept", "switch_failed")
        self.assertTrue(self.branch_exists("feat"))
        self.assertEqual(self.head_ref(), "refs/heads/main")

    def test_ac_2_3_refused_d_is_kept_with_gits_message(self) -> None:
        """Merged into origin/main, no upstream, HEAD on a branch without it: `git branch -d`
        refuses, kept `delete_failed:<message>`. [AC-2.3]"""
        self.push_feat(upstream=False)
        self.land("merge")
        git(self.repo, "checkout", "-q", "-b", "other", "main")
        record = self.delete()
        self.assertEqual((record["status"], record["method"]), ("kept", "-d"), record)
        self.assertTrue(record["reason"].startswith("delete_failed:"), record)
        self.assertIn("not fully merged", record["reason"])
        self.assertNotIn("\n", record["reason"])
        self.assertTrue(self.branch_exists("feat"))


# ---------------------------------------------------------------------------
# AC-2.4: skipped outcomes change no ref
# ---------------------------------------------------------------------------

class SkippedTests(CleanupCase):
    def assertSkipped(self, reason: str, **kw: str) -> None:
        self.push_feat()
        self.land("merge")
        before = self.refs()
        self.assertOutcome(self.delete(**kw), "skipped", reason)
        self.assertEqual(self.refs(), before)

    def test_ac_2_4_opt_out_is_skipped(self) -> None:
        """`writ.deleteMergedBranches=false`: skipped `opted_out`, no ref changed, no fetch. [AC-2.4]"""
        git(self.repo, "config", "--bool", "writ.deleteMergedBranches", "false")
        self.assertSkipped("opted_out")
        self.assertTrue(self.branch_exists("feat"))

    def test_ac_2_4_default_branch_is_skipped(self) -> None:
        """`--branch` equal to `--default`: skipped `default_branch`. [AC-2.4]"""
        self.assertSkipped("default_branch", branch="main")
        self.assertTrue(self.branch_exists("main"))

    def test_ac_2_4_absent_branch_is_skipped(self) -> None:
        """A branch that does not exist locally: skipped `no_branch`. [AC-2.4]"""
        self.assertSkipped("no_branch", branch="gone")


# ---------------------------------------------------------------------------
# Usage errors and --help
# ---------------------------------------------------------------------------

class UsageTests(CleanupCase):
    def test_ac_2_4_usage_errors_exit_2_with_stdout_empty(self) -> None:
        """Missing `--branch`, an option-like name, and a non-repo exit 2 and print nothing on stdout. [AC-2.4]"""
        empty = self.tmp / "empty"
        empty.mkdir()
        cases = [
            ["delete", "--default", "main", "--repo", str(self.repo)],
            ["delete", "--branch=-D", "--default", "main", "--repo", str(self.repo)],
            ["delete", "--branch", "feat", "--default", "main", "--repo", str(empty)],
            ["--zz-bad-flag"],
        ]
        for args in cases:
            with self.subTest(args=args):
                result = run_script(args, self.tmp)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())
        self.assertTrue(self.branch_exists("feat"))

    def test_ac_2_4_help_names_the_schema_and_every_reason(self) -> None:
        """`--help` exits 0 and documents the record and its reasons. [AC-2.4]"""
        result = run_script(["--help"], self.tmp)
        self.assertEqual(result.returncode, 0)
        for needle in (SCHEMA, "delete", "opted_out", "default_branch", "no_branch",
                       "checked_out_elsewhere", "fetch_failed", "local_commits_not_in_pr",
                       "not_merged", "dirty_tree", "switch_failed", "delete_failed"):
            self.assertIn(needle, result.stdout)


# ---------------------------------------------------------------------------
# AC-2.5: text pins, contract registration, plugin copy
# ---------------------------------------------------------------------------

def _ship() -> str:
    return SHIP.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """From the line starting with `heading` to the next heading of the same or a
    higher level (fenced code skipped)."""
    lines = text.splitlines(keepends=True)
    level = len(heading) - len(heading.lstrip("#"))
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    out = [lines[start]]
    fenced = False
    for line in lines[start + 1:]:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced:
            m = re.match(r"^(#{1,6}) ", line)
            if m and len(m.group(1)) <= level:
                break
        out.append(line)
    return "".join(out)


def _flat(text: str) -> str:
    return " ".join(text.split())


STEP_6B = "### Step 6b: Branch Cleanup (post-land)"
COMMAND_PREFIX = "python3 scripts/ship-branch-cleanup.py delete"


class ShipTextTests(CleanupCase):
    def test_ac_2_5_step_6b_sits_between_step_6_and_step_7(self) -> None:
        """Step 6b's heading follows Step 6 and precedes Step 7. [AC-2.5]"""
        text = _ship()
        self.assertEqual(text.count(STEP_6B), 1)
        self.assertLess(text.index("### Step 6: Audit Note (post-land)"), text.index(STEP_6B))
        self.assertLess(text.index(STEP_6B), text.index("### Step 7: Watch Pass"))

    def test_ac_2_5_step_6b_has_its_own_gate_and_runs_when_audit_notes_are_off(self) -> None:
        """Step 6b runs when `writ.auditNotes=false`, reads its own opt-out, prints the 🧹 lines,
        and makes no gh call of its own. [AC-2.5]"""
        step = _flat(_section(_ship(), STEP_6B))
        self.assertIn("`writ.auditNotes=false`", step)
        self.assertIn("writ.deleteMergedBranches", step)
        self.assertIn("🧹 deleted local branch <b> (merged into <d>)", step)
        self.assertIn("🧹 kept <b> — <reason>", step)
        self.assertIn("`skipped`", step)
        self.assertIn("non-blocking", step.lower())
        self.assertNotIn("gh pr view <n> --json state,headRefOid", step)
        step6 = _flat(_section(_ship(), "### Step 6: Audit Note"))
        self.assertNotIn("ship-branch-cleanup", step6)

    def test_ac_2_5_step_6b_command_runs_as_written(self) -> None:
        """The Step 6b command line, filled in, runs the helper and deletes a merged branch. [AC-2.5]"""
        lines = [line.strip() for line in _section(_ship(), STEP_6B).splitlines()
                 if line.strip().startswith(COMMAND_PREFIX)]
        self.assertEqual(len(lines), 1, lines)
        self.push_feat()
        self.land("merge")
        filled = (lines[0].replace("<branch>", "feat").replace("<default-branch>", "main")
                  .replace("<state>", "MERGED").replace("<headRefOid>", self.tip))
        self.assertNotRegex(filled, r"<[^>]+>")
        argv = shlex.split(filled)
        self.assertEqual(argv[:2], ["python3", "scripts/ship-branch-cleanup.py"])
        result = subprocess.run([sys.executable, str(SCRIPT)] + argv[2:], cwd=str(self.repo),
                                env=ENV, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "deleted")

    def test_ac_2_5_merge_item_7_runs_steps_6_and_6b(self) -> None:
        """Merge step item 7 runs Step 6 then Step 6b; "Never `--delete-branch`" stays. [AC-2.5]"""
        text = _ship()
        start = text.index("**Merge step.**")
        step = text[start:text.index("\n**7.7", start)]
        line = next(l for l in step.splitlines() if l.startswith("7. "))
        self.assertIn("Step 6 in this pass", line)
        self.assertIn("Step 6b", line)
        self.assertLess(line.index("Step 6 in this pass"), line.index("Step 6b"))
        self.assertIn("Never `--delete-branch`, `--admin`, or `--auto`", _flat(step))

    def test_ac_2_5_plain_ship_on_a_merged_pr_runs_steps_6_and_6b_before_step_2_merges(self) -> None:
        """Plain `/ship`: before Step 2's merge, a `MERGED` PR from
        `gh pr view --json state,headRefOid,mergeCommit` runs Steps 6 and 6b with `mergeCommit.oid`
        as the landed SHA and stops, ahead of "No changes to ship". [AC-2.5]"""
        step2 = _section(_ship(), "### Step 2: Merge Default Branch")
        call = "`gh pr view --json state,headRefOid,mergeCommit`"
        self.assertIn(call, step2)
        line = _flat(step2[:step2.index("```")])
        self.assertIn("`MERGED`", line)
        self.assertIn("Steps 6 and 6b", line)
        self.assertIn("`mergeCommit.oid` as the landed SHA", line)
        self.assertIn("stop", line)
        self.assertIn('"No changes to ship"', line)
        self.assertLess(line.index('"No changes to ship"'), line.index("`MERGED`"))
        self.assertLess(step2.index(call), step2.index("git merge origin/"))

    def test_ac_2_5_step_2_every_non_merged_result_falls_through_to_the_merge(self) -> None:
        """Only `MERGED` stops; an `OPEN` or `CLOSED` PR, no PR, and a failing gh call all take
        the "Otherwise" path to `git merge`. [AC-2.5]"""
        step2 = _section(_ship(), "### Step 2: Merge Default Branch")
        line = _flat(step2[:step2.index("```")])
        self.assertNotIn("No PR or no `gh`", line)
        rest = line[line.index("stop"):]
        self.assertIn("Otherwise", rest)
        fallthrough = rest[rest.index("Otherwise"):]
        self.assertIn("bring the branch up to date", fallthrough)
        self.assertIn("`OPEN`", fallthrough)
        self.assertIn("`CLOSED`", fallthrough)
        self.assertNotIn("`OPEN`", line[:line.index("Otherwise")])

    def test_ac_2_5_watch_7_1_passes_the_merged_head_to_step_6b(self) -> None:
        """7.1 reads `headRefOid` and `mergeCommit`; `MERGED` runs Steps 6 and 6b with them; Step 6b
        names both head sources. [AC-2.5]"""
        text = _ship()
        line = next(l for l in text.splitlines() if l.startswith("**7.1 Resolve the PR.**"))
        self.assertIn("`gh pr view --json number,state,headRefOid,mergeCommit`", line)
        self.assertIn("`MERGED` → Steps 6 and 6b (`--pr-state MERGED --pr-head <headRefOid>`), "
                      "report `merged`", line)
        merged = line[line.index("`MERGED` →"):line.index("`CLOSED`")]
        self.assertIn("`mergeCommit.oid` as the landed SHA", merged)
        step = _flat(_section(text, STEP_6B))
        self.assertIn("Step 2 or 7.1", step)
        self.assertIn("`view.headRefOid`", step)

    def test_ac_2_5_completion_output_has_the_cleanup_line(self) -> None:
        """Step 5's completion output block carries a 🧹 line. [AC-2.5]"""
        step5 = _section(_ship(), "### Step 5")
        block = step5[step5.index("**Completion output:**"):]
        block = block[:block.index("```", block.index("```") + 3)]
        self.assertRegex(block, r"(?m)^\s+🧹 deleted local branch \S+ \(merged into \S+\)")

    def test_ac_2_5_helper_is_registered_and_copied(self) -> None:
        """A data row in the Classification table, a smoke entry, and a byte-identical plugin copy. [AC-2.5]"""
        doc = CONTRACT_DOC.read_text(encoding="utf-8")
        row = re.search(r"^\| `ship-branch-cleanup\.py` \| (\w+) \| ([^|]*) \| (.*) \|$", doc,
                        re.MULTILINE)
        self.assertIsNotNone(row, "no ship-branch-cleanup.py row in %s" % CONTRACT_DOC)
        self.assertEqual(row.group(1), "data")
        self.assertIn("commands/ship.md", row.group(3))
        self.assertIn("- `ship-branch-cleanup.py` — data.", doc)
        self.assertIn('Smoke("ship-branch-cleanup.py"', CONTRACT_TEST.read_text(encoding="utf-8"))
        self.assertEqual(PLUGIN_COPY.read_bytes(), SCRIPT.read_bytes())

    def test_ac_2_5_helper_source_never_calls_gh(self) -> None:
        """The helper names no `gh` command; the caller passes the PR facts. [AC-2.5]"""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"""["']gh["']""")
        self.assertIsNone(shutil.which("gh", path=ENV["PATH"]))


if __name__ == "__main__":
    unittest.main()
