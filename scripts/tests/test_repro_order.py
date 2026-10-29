#!/usr/bin/env python3
"""Fixture-history tests for `scripts/repro-order.py` (Story 1 of
`2026-10-25-repro-first-bug-fixing`).

Each test builds a throwaway git repository in a temp dir: `make_repo(tmp)`
runs `git init`, sets a local `user.name` and `user.email`, and commits
`src/app.py` and `tests/test_app.py`; `commit(repo, files, message)` writes
(or, for a `None` value, deletes) files and commits them. Fixture git calls
and the script run with the user's global and system git config switched off,
so a signing or default-branch setting on the machine cannot change a result.

- A repro commit (test files only, `Repro:` trailer) followed by a fix commit
  passes, with one `reason:` line per commit and the summary last [AC-1.1].
- Each of the six broken histories fails with its reason code, and every
  finding prints [AC-1.2].
- `- **Repro First:** off` prints `unverifiable` without calling git (the
  run has no `git` on PATH and no repository); a merge in the range is
  `unverifiable` with `merge_in_range` [AC-1.3].
- A missing `--base`, an unknown revision, a base that is not an ancestor of
  head, and a directory that is not a repository exit 2 with stdout empty
  [AC-1.4].
- The Classification table has a `repro-order.py` row and the contract test
  has a smoke entry for it [AC-1.5].

Run: uv run --python 3.9 pytest scripts/tests/test_repro_order.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "repro-order.py"
CONTRACT_DOC = REPO_ROOT / ".writ" / "docs" / "agent-cli-contract.md"
CONTRACT_TEST = REPO_ROOT / "scripts" / "tests" / "test_agent_cli_contract.py"


def _clean_env() -> Dict[str, str]:
    """The caller's env minus GIT_*, with global and system git config off."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    return env


ENV = _clean_env()

APP = "def add(a, b):\n    return a - b\n"
APP_FIXED = "def add(a, b):\n    return a + b\n"
TEST_APP = "from src.app import add\n\n\ndef test_add_zero():\n    assert add(0, 0) == 0\n"
TEST_SUM = "from src.app import add\n\n\ndef test_add_two():\n    assert add(2, 2) == 4\n"

REPRO_MSG = "test(app): reproduce wrong sum\n\nRepro: add(2, 2) returns 0"
FIX_MSG = "fix(app): add instead of subtract"


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          encoding="utf-8", env=ENV)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout.strip()


def commit(repo: Path, files: Dict[str, Optional[str]], message: str) -> str:
    """Write each file (None deletes it), commit everything, return the SHA."""
    for rel, text in files.items():
        path = repo / rel
        if text is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "-c", "init.defaultBranch=main", "init", "-q")
    git(repo, "config", "user.name", "Repro Test")
    git(repo, "config", "user.email", "repro@example.com")
    git(repo, "config", "commit.gpgsign", "false")
    commit(repo, {"src/app.py": APP, "tests/test_app.py": TEST_APP}, "chore: base")
    return repo


def run_script(args: List[str], cwd: Path,
               env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(cwd),
                          capture_output=True, encoding="utf-8", env=env or ENV,
                          timeout=60)


def short(sha: str) -> str:
    return sha[:7]


class ReproOrderCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = make_repo(self.tmp)
        self.base = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def check(self, *extra: str, base: Optional[str] = None,
              repo: Optional[Path] = None,
              env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        where = repo or self.repo
        return run_script(["check", "--repo", str(where), "--base", base or self.base,
                           *extra], self.tmp, env)

    def assertOutput(self, result: subprocess.CompletedProcess, code: int,
                     lines: List[str]) -> None:
        self.assertEqual(result.stdout.splitlines(), lines,
                         "stderr: %s" % result.stderr)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def assertReasons(self, result: subprocess.CompletedProcess, verdict: str,
                      reasons: List[str]) -> None:
        out = result.stdout.splitlines()
        self.assertTrue(out, "no stdout; stderr: %s" % result.stderr)
        self.assertEqual(out[0], verdict, result.stdout + result.stderr)
        self.assertEqual([line for line in out if line.startswith("reason: ")],
                         ["reason: %s" % r for r in reasons])
        self.assertTrue(out[-1].startswith("repro-order: %s (" % verdict), out[-1])
        self.assertEqual(result.returncode, {"pass": 0, "unverifiable": 0, "fail": 1}[verdict])

    def assertUsage(self, result: subprocess.CompletedProcess, cause: str) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn(cause, result.stderr)

    def write_config(self, where: Path, value: Optional[str]) -> None:
        lines = ["# Writ Project Config", "", "## Conventions", ""]
        if value is not None:
            lines.append("- **Repro First:** %s" % value)
        path = where / ".writ" / "config.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def repro_then_fix(self) -> List[str]:
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        fix = commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        return [repro, fix]

    def pass_lines(self, repro: str, fix: str) -> List[str]:
        return ["pass",
                "reason: repro %s test(app): reproduce wrong sum (1 test file)" % short(repro),
                "reason: fix %s fix(app): add instead of subtract (1 source file)" % short(fix),
                "repro-order: pass (1 repro, 1 fix commit(s))"]


class PassTests(ReproOrderCase):
    def test_pass_repro_then_fix(self) -> None:
        """Repro (tests, trailer) then fix (src): exact pass output, exit 0. [AC-1.1]"""
        repro, fix = self.repro_then_fix()
        result = self.check()
        self.assertOutput(result, 0, self.pass_lines(repro, fix))
        self.assertEqual(result.stderr, "")

    def test_default_repo_and_head(self) -> None:
        """`--repo` defaults to `.` and `--head` to `HEAD`. [AC-1.1]"""
        repro, fix = self.repro_then_fix()
        result = run_script(["check", "--base", self.base], self.repo)
        self.assertOutput(result, 0, self.pass_lines(repro, fix))

    def test_head_bounds_the_range(self) -> None:
        """`--head` stops the range: a later bad commit outside it is not read. [AC-1.1]"""
        repro, fix = self.repro_then_fix()
        commit(self.repo, {"tests/test_sum.py": TEST_SUM + "# edited\n"}, "test: edit repro")
        self.assertOutput(self.check("--head", fix), 0, self.pass_lines(repro, fix))

    def test_two_repros_each_with_a_fix(self) -> None:
        """A later repro may modify an earlier repro's test file; each repro has a fix. [AC-1.1]"""
        repro, fix = self.repro_then_fix()
        repro2 = commit(self.repo, {"tests/test_sum.py": TEST_SUM + "\n\ndef test_neg():\n"
                                    "    assert add(-1, -1) == -2\n"},
                        "test(app): reproduce negative sum\n\nRepro: add(-1, -1) is wrong")
        fix2 = commit(self.repo, {"src/app.py": APP_FIXED + "# negatives\n",
                                  "src/neg.py": "N = -1\n"}, "fix(app): negatives")
        lines = self.pass_lines(repro, fix)[:3] + [
            "reason: repro %s test(app): reproduce negative sum (1 test file)" % short(repro2),
            "reason: fix %s fix(app): negatives (2 source files)" % short(fix2),
            "repro-order: pass (2 repro, 2 fix commit(s))"]
        self.assertOutput(self.check(), 0, lines)

    def test_writ_only_commit_ignored(self) -> None:
        """A completion commit that touches only `.writ/` is ignored. [AC-1.1]"""
        repro, fix = self.repro_then_fix()
        commit(self.repo, {".writ/specs/s/user-stories/story-1.md": "# Story 1\n"},
               "docs(s): record story 1")
        self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))

    def test_fix_may_add_new_tests(self) -> None:
        """A fix commit that also adds new tests still passes. [AC-1.1]"""
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        fix = commit(self.repo, {"src/app.py": APP_FIXED, "tests/test_more.py": TEST_SUM},
                     FIX_MSG)
        self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))

    def test_repro_unskips_existing_test(self) -> None:
        """A repro that edits an existing test file is a valid repro. [AC-1.1]"""
        repro = commit(self.repo, {"tests/test_app.py": TEST_APP + TEST_SUM}, REPRO_MSG)
        fix = commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))

    def test_paths_with_spaces_and_non_ascii(self) -> None:
        """NUL-separated diff-tree output keeps spaced and non-ASCII paths whole. [AC-1.1, AC-1.2]"""
        spaced = "tests/test café sum.py"
        repro = commit(self.repo, {spaced: TEST_SUM}, REPRO_MSG)
        fix = commit(self.repo, {"src/my app.py": APP_FIXED}, FIX_MSG)
        self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))
        bad = commit(self.repo, {spaced: TEST_SUM + "# weakened\n"}, "fix(app): tweak test")
        self.assertReasons(self.check(), "fail",
                           ["repro_test_modified %s %s" % (short(bad), spaced)])

    def test_test_glob(self) -> None:
        """`--test-glob 'qa/*'` marks `qa/login_check.py` a test file. [AC-1.1, AC-1.2]"""
        repro = commit(self.repo, {"qa/login_check.py": TEST_SUM}, REPRO_MSG)
        fix = commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertOutput(self.check("--test-glob", "qa/*"), 0, self.pass_lines(repro, fix))
        self.assertReasons(self.check(), "fail", [
            "repro_empty %s" % short(repro),
            "repro_touches_source %s qa/login_check.py" % short(repro)])


class FailTests(ReproOrderCase):
    def test_fail_no_repro(self) -> None:
        """A fix with no repro commit fails `no_repro_commit`. [AC-1.2]"""
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertOutput(self.check(), 1, [
            "fail", "reason: no_repro_commit",
            "repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))"])

    def test_fail_base_equals_head(self) -> None:
        """An empty range is a `fail` with `no_repro_commit`, not a usage error. [AC-1.2]"""
        self.assertOutput(self.check(), 1, [
            "fail", "reason: no_repro_commit",
            "repro-order: fail (0 repro, 0 fix commit(s), 1 finding(s))"])

    def test_fail_repro_touches_source(self) -> None:
        """A repro that also changes source fails, one line per source path. [AC-1.2]"""
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM, "src/app.py": APP_FIXED,
                                   "src/util.py": "X = 1\n"}, REPRO_MSG)
        commit(self.repo, {"src/util.py": "X = 2\n"}, FIX_MSG)
        self.assertReasons(self.check(), "fail", [
            "repro_touches_source %s src/app.py" % short(repro),
            "repro_touches_source %s src/util.py" % short(repro)])

    def test_fail_repro_empty(self) -> None:
        """A repro that changes only `.writ/` has no test file. [AC-1.2]"""
        repro = commit(self.repo, {".writ/notes.md": "bug\n"}, REPRO_MSG)
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertReasons(self.check(), "fail", ["repro_empty %s" % short(repro)])

    def test_fail_source_before_repro(self) -> None:
        """A source change before the first repro fails. [AC-1.2]"""
        early = commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        commit(self.repo, {"src/app.py": APP_FIXED + "# tidy\n"}, "fix(app): tidy")
        self.assertReasons(self.check(), "fail",
                           ["source_before_repro %s src/app.py" % short(early)])

    def test_fail_no_fix_after_repro(self) -> None:
        """A repro with no later source change fails. [AC-1.2]"""
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        self.assertOutput(self.check(), 1, [
            "fail", "reason: no_fix_after_repro %s" % short(repro),
            "repro-order: fail (1 repro, 0 fix commit(s), 1 finding(s))"])

    def test_fail_second_repro_without_fix(self) -> None:
        """With two repros, each needs its own later fix. [AC-1.2]"""
        commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        second = commit(self.repo, {"tests/test_neg.py": TEST_SUM},
                        "test(app): reproduce negatives\n\nRepro: negatives are wrong")
        self.assertReasons(self.check(), "fail", ["no_fix_after_repro %s" % short(second)])

    def test_fail_repro_test_modified(self) -> None:
        """A fix that edits the file the repro added fails. [AC-1.2]"""
        self.repro_then_fix()
        bad = commit(self.repo, {"tests/test_sum.py": TEST_SUM + "# weakened\n",
                                 "src/app.py": APP_FIXED + "# more\n"}, "fix(app): more")
        self.assertReasons(self.check(), "fail",
                           ["repro_test_modified %s tests/test_sum.py" % short(bad)])

    def test_fail_repro_test_renamed(self) -> None:
        """Renaming the repro's test file after the fix fails. [AC-1.2]"""
        self.repro_then_fix()
        moved = commit(self.repo, {"tests/test_sum.py": None, "tests/test_total.py": TEST_SUM},
                       "test: rename sum test")
        self.assertTrue(git(self.repo, "diff-tree", "--no-commit-id", "-r", "-M",
                            "--name-status", moved).startswith("R"))
        self.assertReasons(self.check(), "fail",
                           ["repro_test_modified %s tests/test_sum.py" % short(moved)])

    def test_fail_repro_test_deleted(self) -> None:
        """Deleting the repro's test file after the fix fails. [AC-1.2]"""
        self.repro_then_fix()
        deleted = commit(self.repo, {"tests/test_sum.py": None}, "test: delete sum test")
        self.assertReasons(self.check(), "fail",
                           ["repro_test_modified %s tests/test_sum.py" % short(deleted)])

    def test_rename_counts_both_sides(self) -> None:
        """A repro that moves a source file into tests/ still touches source. [AC-1.2]"""
        repro = commit(self.repo, {"src/app.py": None, "tests/fixtures/app_copy.py": APP},
                       REPRO_MSG)
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertReasons(self.check(), "fail",
                           ["repro_touches_source %s src/app.py" % short(repro)])

    def test_every_finding_prints(self) -> None:
        """All rules run: the spec's two-finding example prints both, rule order. [AC-1.2]"""
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM, "src/app.py": APP_FIXED},
                       REPRO_MSG)
        self.assertOutput(self.check(), 1, [
            "fail",
            "reason: repro_touches_source %s src/app.py" % short(repro),
            "reason: no_fix_after_repro %s" % short(repro),
            "repro-order: fail (1 repro, 0 fix commit(s), 2 finding(s))"])

    @unittest.skipIf(os.name == "nt", "newline in a file name needs a POSIX file system")
    def test_control_characters_escaped(self) -> None:
        """A newline in a path or ESC in a subject prints escaped and adds no line. [AC-1.2]"""
        evil = "src/evil\nreason: pass.py"
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM, evil: "X = 1\n",
                                   "src/café.py": "Y = 1\n"}, REPRO_MSG)
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertOutput(self.check(), 1, [
            "fail",
            "reason: repro_touches_source %s src/café.py" % short(repro),
            "reason: repro_touches_source %s src/evil\\nreason: pass.py" % short(repro),
            "repro-order: fail (1 repro, 1 fix commit(s), 2 finding(s))"])
        git(self.repo, "reset", "-q", "--hard", self.base)
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        fix = commit(self.repo, {"src/app.py": APP_FIXED}, "fix(app): add\x1b[31m now\tok")
        lines = self.pass_lines(repro, fix)
        lines[2] = "reason: fix %s fix(app): add\\x1b[31m now\\tok (1 source file)" % short(fix)
        self.assertOutput(self.check(), 0, lines)

    def test_combined_trailer_block(self) -> None:
        """`Repro:` in one final trailer block with `Ref:` and `Co-Authored-By:` is a repro. [AC-1.1]"""
        repro = commit(self.repo, {"tests/test_sum.py": TEST_SUM},
                       "test(app): reproduce wrong sum\n\n"
                       "The sum test enters through the public add() call.\n\n"
                       "Repro: add(2, 2) returns 0\n"
                       "Ref: .writ/specs/x/user-stories/story-1-x.md\n"
                       "Co-Authored-By: A <a@b.c>")
        fix = commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))

    def test_repro_paragraph_before_separate_trailer_paragraph(self) -> None:
        """`Repro:` in its own paragraph before a `Co-Authored-By:` paragraph is not a repro. [AC-1.2]"""
        commit(self.repo, {"tests/test_sum.py": TEST_SUM},
               "test(app): reproduce wrong sum\n\nRepro: add(2, 2) returns 0\n\n"
               "Co-Authored-By: A <a@b.c>")
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertReasons(self.check(), "fail", ["no_repro_commit"])

    def test_trailer_must_be_non_empty_in_final_paragraph(self) -> None:
        """`Repro:` counts only with a value and only in the last paragraph. [AC-1.2]"""
        commit(self.repo, {"tests/test_sum.py": TEST_SUM},
               "test(app): reproduce\n\nRepro: add is wrong\n\nMore notes after it.")
        commit(self.repo, {"tests/test_neg.py": TEST_SUM}, "test(app): another\n\nRepro:")
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        self.assertReasons(self.check(), "fail", ["no_repro_commit"])


class UnverifiableTests(ReproOrderCase):
    def test_unverifiable_merge(self) -> None:
        """A merge commit in the range is `unverifiable` with `merge_in_range`. [AC-1.3]"""
        git(self.repo, "checkout", "-q", "-b", "side")
        commit(self.repo, {"tests/test_sum.py": TEST_SUM}, REPRO_MSG)
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        git(self.repo, "merge", "-q", "--no-ff", "--no-edit", "side")
        self.assertOutput(self.check(), 0, [
            "unverifiable", "reason: merge_in_range",
            "repro-order: unverifiable (0 repro, 0 fix commit(s))"])

    def test_switch_off(self) -> None:
        """`off` in any case: `unverifiable`, no git call, works outside a repository. [AC-1.3]"""
        plain = self.tmp / "plain"
        no_git = self.tmp / "empty-path"
        no_git.mkdir()
        env = dict(ENV, PATH=str(no_git))
        for value in ("off", "OFF", "Off  "):
            with self.subTest(value=value):
                self.write_config(plain, value)
                result = self.check(base="no-such-rev", repo=plain, env=env)
                self.assertOutput(result, 0, [
                    "unverifiable", "reason: repro-first off",
                    "repro-order: unverifiable (0 repro, 0 fix commit(s))"])
                self.assertEqual(result.stderr, "")

    def test_switch_off_wins_over_history(self) -> None:
        """The switch is read before git: a passing history still reads `unverifiable`. [AC-1.3]"""
        self.repro_then_fix()
        self.write_config(self.repo, "off")
        self.assertReasons(self.check(), "unverifiable", ["repro-first off"])

    def test_switch_unknown_value(self) -> None:
        """`yes` reads as on and adds an informational reason line. [AC-1.3]"""
        repro, fix = self.repro_then_fix()
        self.write_config(self.repo, "yes")
        expected = self.pass_lines(repro, fix)
        expected.insert(1, "reason: repro-first value yes read as on")
        self.assertOutput(self.check(), 0, expected)

    def test_switch_on_values(self) -> None:
        """No file, no line, an empty value, or `on` in any case: on, no extra line. [AC-1.3]"""
        repro, fix = self.repro_then_fix()
        self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))
        for value in (None, "", "on", "ON"):
            with self.subTest(value=value):
                self.write_config(self.repo, value)
                self.assertOutput(self.check(), 0, self.pass_lines(repro, fix))


class UsageErrorTests(ReproOrderCase):
    def test_usage_errors(self) -> None:
        """Missing --base, bad rev, base not an ancestor, not a repo: exit 2, stdout empty. [AC-1.4]"""
        git(self.repo, "checkout", "-q", "-b", "side")
        side = commit(self.repo, {"tests/test_side.py": TEST_SUM}, "test: side")
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, {"src/app.py": APP_FIXED}, FIX_MSG)
        plain = self.tmp / "plain"
        plain.mkdir()
        cases = [
            ("missing --base", ["check", "--repo", str(self.repo)], "--base"),
            ("bad rev", ["check", "--repo", str(self.repo), "--base", "no-such-rev"],
             "repro-order: cannot resolve no-such-rev"),
            ("bad head", ["check", "--repo", str(self.repo), "--base", self.base,
                          "--head", "no-such-head"], "repro-order: cannot resolve no-such-head"),
            ("option-like rev", ["check", "--repo", str(self.repo), "--base=--all"],
             "repro-order: cannot resolve --all"),
            ("not an ancestor", ["check", "--repo", str(self.repo), "--base", side],
             "repro-order: %s is not an ancestor of HEAD" % side),
            ("not a repository", ["check", "--repo", str(plain), "--base", "HEAD"],
             "repro-order: not a git repository"),
            ("no subcommand", [], "usage:"),
            ("unknown flag", ["check", "--base", "HEAD", "--zz-probe"], "usage:"),
        ]
        for name, args, cause in cases:
            with self.subTest(case=name):
                self.assertUsage(run_script(args, self.tmp), cause)

    def test_git_not_found(self) -> None:
        """No `git` on PATH with the switch on: exit 2, `git not found`. [AC-1.4]"""
        no_git = self.tmp / "empty-path"
        no_git.mkdir()
        self.assertUsage(self.check(env=dict(ENV, PATH=str(no_git))),
                         "repro-order: git not found")

    def test_unreadable_config(self) -> None:
        """A config that is not UTF-8 is exit 2 with `cannot read .writ/config.md`. [AC-1.4]"""
        self.repro_then_fix()
        config = self.repo / ".writ" / "config.md"
        config.parent.mkdir(parents=True)
        config.write_bytes(b"- **Repro First:** \xff\xfe off\n")
        self.assertUsage(self.check(), "repro-order: cannot read .writ/config.md (")

    @unittest.skipIf(not hasattr(os, "geteuid") or os.geteuid() == 0,
                     "needs POSIX permissions and a non-root user")
    def test_unsearchable_writ_dir(self) -> None:
        """A `.writ/` that cannot be searched is exit 2 with `cannot read`, no traceback. [AC-1.4]"""
        writ = self.repo / ".writ"
        self.write_config(self.repo, "on")
        os.chmod(str(writ), 0)
        try:
            result = self.check()
        finally:
            os.chmod(str(writ), 0o755)
        self.assertUsage(result, "repro-order: cannot read .writ/config.md (")
        self.assertNotIn("Traceback", result.stderr)

    def test_help(self) -> None:
        """`--help` exits 0 and names the `check` subcommand. [AC-1.4]"""
        result = run_script(["--help"], self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check", result.stdout)


class ContractTests(unittest.TestCase):
    def test_contract_row_and_smoke_entry(self) -> None:
        """The Classification table has a `repro-order.py` check row; the contract test smokes it. [AC-1.5]"""
        doc = CONTRACT_DOC.read_text(encoding="utf-8")
        row = re.search(r"^\| `repro-order\.py` \| (\w+) \|", doc, re.MULTILINE)
        self.assertIsNotNone(row, "no repro-order.py row in %s" % CONTRACT_DOC)
        self.assertEqual(row.group(1), "check")
        self.assertIn('Smoke("repro-order.py"', CONTRACT_TEST.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
