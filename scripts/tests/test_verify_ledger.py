#!/usr/bin/env python3
"""Temp-repo tests for `scripts/verify-ledger.py` (Story 1 of
`2026-11-06-pr-ready-and-ledger`).

Every test builds its own git repository under a temp dir with `make_repo`:
`main` holds `app.py` (a Python function under twelve header lines and a
blank line after the changed line), `top.txt`, and `blob.bin` (binary); the
`feature` branch is checked out with head H, which changes one line of
`app.py` and one byte of `blob.bin`. Fixture git calls and the script run
with global and system git config switched off unless a test sets its own.

- `record` writes one row with every field, `check` reads it back as
  `verified_exact`, and recording the same PR and head again replaces the
  row and prints `reason: replaced` [AC-1.1].
- A non-zero evidence exit, a head that is not checked out, and a modified
  tracked file each refuse with `fail`, exit 1, and the ledger file left
  byte-identical; an `os.replace` failure leaves the file as it was and no
  temp file behind [AC-1.2].
- Each single-property mutation of H (one byte, whitespace-only re-indent,
  mode only, binary bytes only) and H's diff under another PR read NOT
  VERIFIED with `patch_id_mismatch`; H rebased unchanged onto a `main` that
  gained lines above the hunk reads `verified_patch_id` [AC-1.3].
- Hostile diff config (and `GIT_DIFF_OPTS`) leaves the ids unchanged, and a
  submodule pointer bump changes the id even when config or `.gitmodules`
  tells `git diff` to ignore submodules; a head missing from the repo, an
  unresolvable base, a `git` that rejects `patch-id --verbatim`, a failing
  `git diff`, an empty diff, unrelated histories, and no `git` on PATH all
  fail closed [AC-1.4].
- The Classification row, contract smoke, `--help`, a malformed ledger
  (exit 2, stdout empty), usage errors, and the plugin copy [AC-1.5].

Run: uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_verify_ledger.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Union
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify-ledger.py"
PLUGIN_COPY = REPO_ROOT / "plugins" / "writ" / "scripts" / "verify-ledger.py"
CONTRACT_DOC = REPO_ROOT / ".writ" / "docs" / "agent-cli-contract.md"
CONTRACT_TEST = REPO_ROOT / "scripts" / "tests" / "test_agent_cli_contract.py"
LEDGER_REL = Path(".writ") / "state" / "verify-ledger.json"
CALLERS = "none shipped yet; /ship --watch (spec 2026-11-06-ship-watch-and-merge)"
REAL_GIT = shutil.which("git") or "git"


def _clean_env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """The caller's env minus GIT_*, with global and system git config off."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    env.update(extra or {})
    return env


ENV = _clean_env()

HEADER = "".join("# header line %d\n" % i for i in range(12))
APP_BASE = HEADER + "\n\ndef add(a, b):\n    total = a - b\n\n    return total\n"
APP_H = APP_BASE.replace("    total = a - b", "    total = a + b")
APP_ONE_BYTE = APP_BASE.replace("    total = a - b", "    total = a * b")
APP_REINDENT = APP_BASE.replace("    total = a - b", "  total = a + b")
TOP = "top line one\ntop line two\n"
BLOB_BASE = bytes(range(256)) * 4
BLOB_H = BLOB_BASE[:100] + b"\xff" + BLOB_BASE[101:]
BLOB_MUTANT = BLOB_H[:200] + b"\x00" + BLOB_H[201:]

FileValue = Union[str, bytes, None]


def git(repo: Path, *args: str, env: Optional[Dict[str, str]] = None) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c",
                           "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
                          capture_output=True, encoding="utf-8", env=env or ENV)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout.strip()


def write_files(repo: Path, files: Dict[str, FileValue]) -> None:
    for rel, value in files.items():
        path = repo / rel
        if value is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            path.write_text(value, encoding="utf-8")


def commit(repo: Path, files: Dict[str, FileValue], message: str,
           executable: Optional[List[str]] = None) -> str:
    """Write each file (None deletes it), chmod +x the named ones, commit, return the SHA."""
    write_files(repo, files)
    for rel in executable or []:
        path = repo / rel
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def branch_commit(repo: Path, name: str, start: str, files: Dict[str, FileValue],
                  message: str, executable: Optional[List[str]] = None) -> str:
    """Commit on a new branch from `start`, then return to the branch checked out before."""
    before = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    git(repo, "checkout", "-q", "-b", name, start)
    sha = commit(repo, files, message, executable)
    git(repo, "checkout", "-q", before)
    return sha


def make_repo(tmp: Path) -> Path:
    """`main` with the base files; `feature` checked out at head H."""
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    # The ledger lives in the work tree; keep it out of `git add -A`.
    (repo / ".git" / "info").mkdir(parents=True, exist_ok=True)
    (repo / ".git" / "info" / "exclude").write_text(".writ/\n", encoding="utf-8")
    commit(repo, {"app.py": APP_BASE, "top.txt": TOP, "blob.bin": BLOB_BASE}, "chore: base")
    git(repo, "checkout", "-q", "-b", "feature")
    commit(repo, {"app.py": APP_H, "blob.bin": BLOB_H}, "feat: add instead of subtract")
    return repo


def run_script(args: List[str], cwd: Path, env: Optional[Dict[str, str]] = None,
               script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=str(cwd),
                          capture_output=True, encoding="utf-8", env=env or ENV, timeout=60)


def short(sha: str) -> str:
    return sha[:7]


def load_module():
    spec = importlib.util.spec_from_file_location("verify_ledger_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class LedgerCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = make_repo(self.tmp)
        self.base = git(self.repo, "rev-parse", "main")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @property
    def ledger(self) -> Path:
        return self.repo / LEDGER_REL

    def ledger_bytes(self) -> Optional[bytes]:
        return self.ledger.read_bytes() if self.ledger.exists() else None

    def rows(self) -> List[dict]:
        return json.loads(self.ledger.read_text(encoding="utf-8"))["rows"]

    def record(self, pr: int, head: Optional[str] = None, base: str = "main",
               evidence: Optional[List[List[str]]] = None,
               env: Optional[Dict[str, str]] = None,
               repo: Optional[Path] = None) -> subprocess.CompletedProcess:
        args = ["record", "--pr", str(pr), "--head", head or self.head, "--base", base,
                "--repo", str(repo or self.repo)]
        for exit_code, command in evidence or [["0", "pytest"], ["0", "bash scripts/eval.sh"]]:
            args += ["--evidence", exit_code, command]
        return run_script(args, self.tmp, env)

    def check(self, pr: int, head: str, base: Optional[str] = None,
              env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        args = ["check", "--pr", str(pr), "--head", head, "--repo", str(self.repo)]
        if base is not None:
            args += ["--base", base]
        return run_script(args, self.tmp, env)

    def assertVerdict(self, result: subprocess.CompletedProcess, verdict: str,
                      first_reason: str) -> List[str]:
        """Line 1 is `verdict`, the first `reason:` line starts with `first_reason`,
        the summary is last, and the exit code matches the verdict."""
        out = result.stdout.splitlines()
        self.assertTrue(out, "no stdout; stderr: %s" % result.stderr)
        self.assertEqual(out[0], verdict, result.stdout + result.stderr)
        reasons = [line[len("reason: "):] for line in out if line.startswith("reason: ")]
        self.assertTrue(reasons, result.stdout)
        self.assertTrue(reasons[0].startswith(first_reason), (reasons, first_reason))
        self.assertTrue(out[-1].startswith("verify-ledger: %s (" % verdict), out[-1])
        self.assertEqual(result.returncode, {"pass": 0, "fail": 1}[verdict],
                         result.stdout + result.stderr)
        return reasons

    def assertUsage(self, result: subprocess.CompletedProcess, cause: str = "") -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn(cause, result.stderr)

    def patch_id_of(self, head: str, env: Optional[Dict[str, str]] = None,
                    pinned: bool = True) -> str:
        """The verbatim id of main...head, computed outside the script."""
        flags = ["--no-color", "--no-ext-diff", "--no-textconv", "--binary", "--full-index",
                 "--no-renames", "--src-prefix=a/", "--dst-prefix=b/", "--diff-algorithm=myers",
                 "-U3", "--no-relative"] if pinned else []
        mb = git(self.repo, "merge-base", "main", head, env=env)
        diff = subprocess.run(["git", "-C", str(self.repo), "diff", *flags, mb, head],
                              capture_output=True, env=env or ENV, check=True).stdout
        out = subprocess.run(["git", "-C", str(self.repo), "patch-id", "--verbatim"],
                             input=diff, capture_output=True, env=env or ENV, check=True).stdout
        fields = out.decode("ascii").split()
        return fields[0] if fields else ""


# ---------------------------------------------------------------------------
# AC-1.1 record and check
# ---------------------------------------------------------------------------

class RecordTests(LedgerCase):
    def test_record_writes_one_row_and_check_reads_exact(self) -> None:
        """record writes schema verify-ledger/1 and one full row; check prints verified_exact. [AC-1.1]"""
        result = self.record(7, evidence=[["0", "pytest -q"], ["0", "bash scripts/eval.sh"]])
        pid = self.patch_id_of(self.head)
        self.assertEqual(result.stdout.splitlines(), [
            "pass",
            "reason: recorded PR 7 head %s patch-id %s" % (short(self.head), short(pid)),
            "verify-ledger: pass (recorded PR 7 head %s, 2 command(s))" % short(self.head),
        ], result.stderr)
        self.assertEqual(result.returncode, 0)
        data = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "verify-ledger/1")
        self.assertEqual(len(data["rows"]), 1)
        row = data["rows"][0]
        self.assertEqual(sorted(row), ["base_ref", "evidence", "head", "merge_base", "patch_id",
                                       "pr", "recorded_at"])
        self.assertEqual((row["pr"], row["head"], row["patch_id"], row["base_ref"],
                          row["merge_base"]), (7, self.head, pid, "main", self.base))
        self.assertRegex(row["recorded_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(row["evidence"], [{"command": "pytest -q", "exit": 0},
                                           {"command": "bash scripts/eval.sh", "exit": 0}])
        check = self.check(7, self.head)
        reasons = self.assertVerdict(check, "pass", "verified_exact %s" % short(self.head))
        self.assertEqual(reasons, ["verified_exact %s (recorded %s)"
                                   % (short(self.head), row["recorded_at"])])
        self.assertEqual(check.stdout.splitlines()[-1],
                         "verify-ledger: pass (PR 7 head %s VERIFIED, exact)" % short(self.head))

    def test_record_same_head_replaces_row(self) -> None:
        """Recording the same PR and head again keeps one row, with the new evidence and `reason: replaced`. [AC-1.1]"""
        self.assertEqual(self.record(7).returncode, 0)
        other = branch_commit(self.repo, "other", "main", {"top.txt": TOP + "x\n"}, "feat: other")
        git(self.repo, "checkout", "-q", "other")
        self.assertEqual(self.record(8, head=other).returncode, 0)
        git(self.repo, "checkout", "-q", "feature")
        again = self.record(7, evidence=[["0", "make test"]])
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn("reason: replaced", again.stdout.splitlines())
        self.assertTrue(again.stdout.splitlines()[-1].endswith(", 1 command(s))"))
        rows = self.rows()
        self.assertEqual([(r["pr"], r["head"]) for r in rows], [(7, self.head), (8, other)])
        self.assertEqual(rows[0]["evidence"], [{"command": "make test", "exit": 0}])

    def test_record_creates_state_dir_and_accepts_untracked_files(self) -> None:
        """Untracked files do not refuse a record; `.writ/state/` is created. [AC-1.1]"""
        (self.repo / "scratch.log").write_text("untracked\n", encoding="utf-8")
        self.assertFalse((self.repo / ".writ").exists())
        result = self.record(7)
        self.assertEqual(result.stdout.splitlines()[0], "pass", result.stdout + result.stderr)
        self.assertTrue(self.ledger.is_file())

    def test_check_resolves_a_ref_to_the_exact_row(self) -> None:
        """A non-hex `--head` resolves through git and matches the exact row. [AC-1.1]"""
        self.record(7)
        self.assertVerdict(self.check(7, "feature"), "pass", "verified_exact")

    def test_check_no_rows(self) -> None:
        """No ledger file and no row for the PR both read `no_rows`. [AC-1.1]"""
        result = self.check(7, self.head)
        self.assertEqual(self.assertVerdict(result, "fail", "no_rows"), ["no_rows PR 7"])
        self.assertEqual(result.stdout.splitlines()[-1],
                         "verify-ledger: fail (PR 7 head %s NOT VERIFIED, no_rows)" % short(self.head))
        self.record(7)
        self.assertEqual(self.assertVerdict(self.check(9, self.head), "fail", "no_rows"),
                         ["no_rows PR 9"])


# ---------------------------------------------------------------------------
# AC-1.2 refusals and failed writes
# ---------------------------------------------------------------------------

class RefusalTests(LedgerCase):
    def assertRefused(self, result: subprocess.CompletedProcess, code: str,
                      before: Optional[bytes]) -> None:
        out = result.stdout.splitlines()
        self.assertEqual(out[0], "fail", result.stdout + result.stderr)
        self.assertTrue(any(line.startswith("reason: %s" % code) for line in out), out)
        self.assertEqual(out[-1], "verify-ledger: fail (record refused for PR 7 head %s)"
                         % short(self.head))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.ledger_bytes(), before)

    def test_each_refusal_leaves_the_ledger_unchanged(self) -> None:
        """A non-zero evidence exit, another checked-out HEAD, or a tracked change refuses; the file is byte-identical. [AC-1.2]"""
        for prior in (False, True):
            with self.subTest(ledger_exists=prior):
                if prior:
                    self.assertEqual(self.record(7).returncode, 0)
                before = self.ledger_bytes()
                self.assertRefused(self.record(7, evidence=[["0", "pytest"], ["1", "eval"]]),
                                   "evidence_failed 1 eval", before)
                git(self.repo, "checkout", "-q", "main")
                self.assertRefused(self.record(7), "head_not_checked_out %s (HEAD is %s)"
                                   % (short(self.head), short(self.base)), before)
                git(self.repo, "checkout", "-q", "feature")
                (self.repo / "top.txt").write_text("edited\n", encoding="utf-8")
                self.assertRefused(self.record(7), "dirty_tree 1 path(s)", before)
                git(self.repo, "add", "top.txt")
                self.assertRefused(self.record(7), "dirty_tree 1 path(s)", before)
                git(self.repo, "checkout", "-q", "HEAD", "--", "top.txt")

    def test_every_refusal_prints(self) -> None:
        """All refusals that hold print, in order. [AC-1.2]"""
        (self.repo / "app.py").write_text("changed\n", encoding="utf-8")
        result = self.record(7, head=self.base, evidence=[["2", "a"], ["0", "b"], ["3", "c"]])
        self.assertEqual(result.stdout.splitlines()[:-1], [
            "fail",
            "reason: evidence_failed 2 a",
            "reason: evidence_failed 3 c",
            "reason: head_not_checked_out %s (HEAD is %s)" % (short(self.base), short(self.head)),
            "reason: dirty_tree 1 path(s)",
        ])
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(self.ledger_bytes())

    def test_failed_replace_leaves_file_and_no_temp(self) -> None:
        """When os.replace raises during an accepted record, the file is unchanged and no *.tmp remains. [AC-1.2]"""
        self.assertEqual(self.record(7).returncode, 0)
        before = self.ledger_bytes()
        module = load_module()
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, ENV, clear=True), \
                mock.patch("os.replace", side_effect=OSError(28, "No space left on device")), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(["record", "--pr", "7", "--head", self.head, "--base", "main",
                                "--repo", str(self.repo), "--evidence", "0", "pytest"])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("verify-ledger: ", err.getvalue())
        self.assertEqual(self.ledger_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.ledger.parent.iterdir()),
                         ["verify-ledger.json"])


# ---------------------------------------------------------------------------
# AC-1.3 mutations
# ---------------------------------------------------------------------------

class MutationTests(LedgerCase):
    def setUp(self) -> None:
        super().setUp()
        self.other = branch_commit(self.repo, "pr8", "main", {"top.txt": TOP + "pr 8\n"},
                                   "feat: pr 8")
        git(self.repo, "checkout", "-q", "pr8")
        self.assertEqual(self.record(8, head=self.other).returncode, 0)
        git(self.repo, "checkout", "-q", "feature")
        self.assertEqual(self.record(7).returncode, 0)
        self.h_id = self.rows()[1]["patch_id"]
        self.assertIsNotNone(self.h_id)

    def test_single_property_mutations_read_not_verified(self) -> None:
        """One byte, a re-indent, chmod +x, binary bytes, or H's diff under PR 8: fail patch_id_mismatch, exit 1. [AC-1.3]"""
        mutants = {
            "one_byte": ({"app.py": APP_ONE_BYTE, "blob.bin": BLOB_H}, None, 7),
            "reindent": ({"app.py": APP_REINDENT, "blob.bin": BLOB_H}, None, 7),
            "mode_only": ({"app.py": APP_H, "blob.bin": BLOB_H}, ["app.py"], 7),
            "binary_only": ({"app.py": APP_H, "blob.bin": BLOB_MUTANT}, None, 7),
            "other_pr": ({"app.py": APP_H, "blob.bin": BLOB_H}, None, 8),
        }
        for name, (files, executable, pr) in mutants.items():
            with self.subTest(mutation=name):
                sha = branch_commit(self.repo, "m-" + name, self.base, files,
                                    "feat: mutant %s" % name, executable)
                self.assertNotEqual(sha, self.head)
                result = self.check(pr, sha)
                reasons = self.assertVerdict(result, "fail", "patch_id_mismatch %s" % short(sha))
                self.assertRegex(reasons[0], r"^patch_id_mismatch %s patch-id [0-9a-f]{7} matches "
                                 r"no verified row for PR %d$" % (short(sha), pr))
                if name != "other_pr":
                    self.assertNotIn(short(self.h_id), reasons[0])

    def test_same_diff_new_sha_reads_verified_under_same_pr(self) -> None:
        """H's diff on a new SHA reads verified_patch_id under PR 7 (the other_pr control). [AC-1.3]"""
        sha = branch_commit(self.repo, "same", self.base, {"app.py": APP_H, "blob.bin": BLOB_H},
                            "feat: same diff, new message")
        reasons = self.assertVerdict(self.check(7, sha), "pass", "verified_patch_id")
        self.assertEqual(reasons, ["verified_patch_id %s matches %s" % (short(sha),
                                                                         short(self.head))])

    def test_rebase_with_unchanged_diff_reads_verified(self) -> None:
        """H rebased onto a main that gained lines above the hunk reads verified_patch_id. [AC-1.3]"""
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, {"app.py": "# new top one\n# new top two\n" + APP_BASE}, "chore: top")
        git(self.repo, "checkout", "-q", "feature")
        git(self.repo, "rebase", "-q", "main")
        rebased = git(self.repo, "rev-parse", "HEAD")
        self.assertNotEqual(rebased, self.head)
        result = self.check(7, rebased)
        self.assertEqual(self.assertVerdict(result, "pass", "verified_patch_id"),
                         ["verified_patch_id %s matches %s" % (short(rebased), short(self.head))])
        self.assertEqual(result.stdout.splitlines()[-1],
                         "verify-ledger: pass (PR 7 head %s VERIFIED, patch-id)" % short(rebased))


# ---------------------------------------------------------------------------
# AC-1.4 hostile config and failing closed
# ---------------------------------------------------------------------------

HOSTILE_CONFIG = """[diff]
\tnoprefix = true
\talgorithm = patience
\trenames = copies
\tsuppressBlankEmpty = true
\tinterHunkContext = 10
\tindentHeuristic = false
\tignoreSubmodules = all
\tsubmodule = log
[color]
\tui = always
"""


class HostileConfigTests(LedgerCase):
    def test_hostile_diff_config_gives_the_same_ids(self) -> None:
        """noprefix, patience, renames=copies, color.ui=always (and more) leave record and check ids unchanged. [AC-1.4]"""
        config = self.tmp / "hostile.gitconfig"
        config.write_text(HOSTILE_CONFIG, encoding="utf-8")
        hostile = _clean_env({"GIT_CONFIG_GLOBAL": str(config)})
        # The config would change an unpinned id, so the test is not vacuous.
        self.assertNotEqual(self.patch_id_of(self.head, pinned=False),
                            self.patch_id_of(self.head, env=hostile, pinned=False))
        self.assertEqual(self.record(7).returncode, 0)
        plain = self.rows()[0]["patch_id"]
        result = self.record(7, env=hostile)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.rows()[0]["patch_id"], plain)
        same = branch_commit(self.repo, "same", self.base, {"app.py": APP_H, "blob.bin": BLOB_H},
                             "feat: same diff")
        self.assertVerdict(self.check(7, same, env=hostile), "pass", "verified_patch_id")

    def test_git_diff_opts_does_not_change_the_id(self) -> None:
        """GIT_DIFF_OPTS=-u0 in the environment leaves record and check ids unchanged. [AC-1.4]"""
        self.assertEqual(self.record(7).returncode, 0)
        plain = self.rows()[0]["patch_id"]
        env = _clean_env({"GIT_DIFF_OPTS": "-u0"})
        self.assertEqual(self.record(7, env=env).returncode, 0)
        self.assertEqual(self.rows()[0]["patch_id"], plain)
        same = branch_commit(self.repo, "same", self.base, {"app.py": APP_H, "blob.bin": BLOB_H},
                             "feat: same diff")
        self.assertVerdict(self.check(7, same, env=env), "pass", "verified_patch_id")


SUB_OLD = "1" * 40
SUB_NEW = "2" * 40
GITMODULES = '[submodule "sub"]\n\tpath = sub\n\turl = ./nowhere\n'


class SubmoduleTests(unittest.TestCase):
    def bump_check(self, gitmodules: str, global_config: str) -> subprocess.CompletedProcess:
        """Record H (an app.py change over a base with gitlink `sub`), bump the
        gitlink in a new commit, and check that commit under PR 7."""
        with tempfile.TemporaryDirectory() as name:
            tmp = Path(name)
            config = tmp / "global.gitconfig"
            config.write_text(global_config, encoding="utf-8")
            env = _clean_env({"GIT_CONFIG_GLOBAL": str(config)})
            repo = tmp / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            (repo / ".git" / "info" / "exclude").write_text(".writ/\n", encoding="utf-8")
            (repo / "sub").mkdir()
            write_files(repo, {"app.py": APP_BASE, ".gitmodules": gitmodules})
            git(repo, "add", "app.py", ".gitmodules")
            git(repo, "update-index", "--add", "--cacheinfo", "160000,%s,sub" % SUB_OLD)
            git(repo, "commit", "-q", "-m", "chore: base")
            git(repo, "checkout", "-q", "-b", "feature")
            head = commit(repo, {"app.py": APP_H}, "feat: H")
            recorded = run_script(["record", "--pr", "7", "--head", head, "--base", "main",
                                   "--evidence", "0", "pytest", "--repo", str(repo)], tmp, env)
            self.assertEqual(recorded.stdout.splitlines()[:1], ["pass"],
                             recorded.stdout + recorded.stderr)
            git(repo, "update-index", "--add", "--cacheinfo", "160000,%s,sub" % SUB_NEW)
            git(repo, "commit", "-q", "-m", "chore: bump the submodule")
            bumped = git(repo, "rev-parse", "HEAD")
            return run_script(["check", "--pr", "7", "--head", bumped, "--repo", str(repo)],
                              tmp, env)

    def test_submodule_bump_reads_not_verified(self) -> None:
        """A submodule pointer bump after verification reads patch_id_mismatch, even under ignore config. [AC-1.4]"""
        cases = {
            "plain": (GITMODULES, ""),
            "gitmodules_ignore_all": (GITMODULES + "\tignore = all\n", ""),
            "diff_ignore_submodules_all": (GITMODULES, "[diff]\n\tignoreSubmodules = all\n"),
            "diff_submodule_log": (GITMODULES, "[diff]\n\tsubmodule = log\n"),
        }
        for name, (gitmodules, config) in cases.items():
            with self.subTest(case=name):
                result = self.bump_check(gitmodules, config)
                out = result.stdout.splitlines()
                self.assertEqual(out[:1], ["fail"], result.stdout + result.stderr)
                self.assertTrue(out[1].startswith("reason: patch_id_mismatch "), out)
                self.assertEqual(result.returncode, 1)


class PopulatedSubmoduleTests(LedgerCase):
    def test_submodule_state_binds_the_record(self) -> None:
        """Under `ignore = all`, a submodule at another commit refuses record; untracked files inside it do not. [AC-1.2]"""
        source = self.tmp / "subsrc"
        source.mkdir()
        git(source, "init", "-q", "-b", "main")
        first = commit(source, {"lib.py": "X = 1\n"}, "feat: lib one")
        commit(source, {"lib.py": "X = 2\n"}, "feat: lib two")
        git(self.repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
            str(source), "sub")
        git(self.repo, "config", "-f", ".gitmodules", "submodule.sub.ignore", "all")
        head = commit(self.repo, {}, "chore: add the submodule")
        sub = self.repo / "sub"
        (sub / "scratch.log").write_text("untracked\n", encoding="utf-8")
        accepted = self.record(7, head=head)
        self.assertEqual(accepted.stdout.splitlines()[0], "pass",
                         accepted.stdout + accepted.stderr)
        before = self.ledger_bytes()
        git(sub, "checkout", "-q", first)
        refused = self.record(7, head=head)
        self.assertEqual(refused.stdout.splitlines()[:2], ["fail", "reason: dirty_tree 1 path(s)"],
                         refused.stdout + refused.stderr)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(self.ledger_bytes(), before)


def shim_dir(tmp: Path, pattern: str = '*" patch-id "*"--verbatim"*') -> Path:
    """A `git` that exits 129 when its arguments match `pattern` (default
    `patch-id --verbatim`) and runs the real git otherwise."""
    folder = tmp / ("shim-%d" % len(list(tmp.glob("shim-*"))))
    folder.mkdir()
    shim = folder / "git"
    shim.write_text("#!/bin/sh\n"
                    'case " $* " in\n'
                    '  %s) echo "error: unknown option" >&2; exit 129;;\n'
                    "esac\n"
                    'exec "%s" "$@"\n' % (pattern, REAL_GIT), encoding="utf-8")
    shim.chmod(0o755)
    return folder


class FailClosedTests(LedgerCase):
    def test_head_missing_from_repo(self) -> None:
        """A full SHA that is not in the repo reads head_unavailable. [AC-1.4]"""
        self.record(7)
        (self.tmp / "elsewhere").mkdir()
        elsewhere = make_repo(self.tmp / "elsewhere")
        missing = commit(elsewhere, {"only-elsewhere.txt": "elsewhere\n"}, "feat: elsewhere")
        self.assertEqual(self.assertVerdict(self.check(7, missing), "fail", "head_unavailable"),
                         ["head_unavailable %s" % missing])

    def test_base_unresolvable(self) -> None:
        """An explicit `--base` or a deleted row base_ref that does not resolve reads base_unavailable. [AC-1.4]"""
        git(self.repo, "branch", "topic-base", "main")
        self.assertEqual(self.record(7, base="topic-base").returncode, 0)
        same = branch_commit(self.repo, "same", self.base, {"app.py": APP_H, "blob.bin": BLOB_H},
                             "feat: same diff")
        self.assertEqual(self.assertVerdict(self.check(7, same, base="no-such-ref"), "fail",
                                            "base_unavailable"),
                         ["base_unavailable no-such-ref"])
        git(self.repo, "branch", "-D", "topic-base")
        self.assertEqual(self.assertVerdict(self.check(7, same), "fail", "base_unavailable"),
                         ["base_unavailable topic-base"])

    def test_verbatim_unsupported(self) -> None:
        """Under a git without `patch-id --verbatim`, record stores null and only the exact head passes. [AC-1.4]"""
        env = _clean_env({"PATH": str(shim_dir(self.tmp)) + os.pathsep + ENV.get("PATH", "")})
        result = self.record(7, env=env)
        self.assertEqual(result.stdout.splitlines(), [
            "pass",
            "reason: recorded PR 7 head %s patch-id null" % short(self.head),
            "reason: patch_id_unavailable (verbatim_unsupported)",
            "verify-ledger: pass (recorded PR 7 head %s, 2 command(s))" % short(self.head),
        ], result.stderr)
        self.assertIsNone(self.rows()[0]["patch_id"])
        self.assertVerdict(self.check(7, self.head, env=env), "pass", "verified_exact")
        same = branch_commit(self.repo, "same", self.base, {"app.py": APP_H, "blob.bin": BLOB_H},
                             "feat: same diff")
        self.assertEqual(self.assertVerdict(self.check(7, same, env=env), "fail",
                                            "patch_id_unavailable"),
                         ["patch_id_unavailable (verbatim_unsupported)"])
        # A null row never matches by id, even once git supports --verbatim again.
        self.assertVerdict(self.check(7, same), "fail", "patch_id_mismatch")

    def test_failing_git_diff(self) -> None:
        """A `git diff` that fails stores a null id (git_failed); another head fails closed. [AC-1.4]"""
        env = _clean_env({"PATH": str(shim_dir(self.tmp, '*" diff "*')) + os.pathsep
                          + ENV.get("PATH", "")})
        result = self.record(7, env=env)
        self.assertIn("reason: patch_id_unavailable (git_failed)", result.stdout.splitlines(),
                      result.stdout + result.stderr)
        self.assertIsNone(self.rows()[0]["patch_id"])
        self.assertVerdict(self.check(7, self.head, env=env), "pass", "verified_exact")
        self.assertEqual(self.assertVerdict(self.check(7, self.base, env=env), "fail",
                                            "patch_id_unavailable"),
                         ["patch_id_unavailable (git_failed)"])

    def test_git_not_runnable(self) -> None:
        """A `git` on PATH that cannot be executed: record exits 2, check fails closed with git_failed. [AC-1.4]"""
        self.record(7)
        folder = self.tmp / "noexec"
        folder.mkdir()
        (folder / "git").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (folder / "git").chmod(0o644)
        env = _clean_env({"PATH": str(folder)})
        self.assertUsage(self.record(7, env=env), "cannot run git")
        self.assertVerdict(self.check(7, self.head, env=env), "pass", "verified_exact")
        self.assertEqual(self.assertVerdict(self.check(7, self.base, env=env), "fail",
                                            "patch_id_unavailable"),
                         ["patch_id_unavailable (git_failed)"])

    def test_empty_diff_and_no_merge_base(self) -> None:
        """An empty diff and unrelated histories store a null id with the reason; other heads fail closed. [AC-1.4]"""
        git(self.repo, "checkout", "-q", "main")
        result = self.record(7, head=self.base)
        self.assertIn("reason: patch_id_unavailable (empty_diff)", result.stdout.splitlines())
        row = self.rows()[0]
        self.assertEqual((row["patch_id"], row["merge_base"]), (None, self.base))
        self.assertEqual(self.assertVerdict(self.check(7, self.head), "fail",
                                            "patch_id_mismatch")[0][:17], "patch_id_mismatch")
        self.assertEqual(self.assertVerdict(self.check(7, self.base, base=self.base), "pass",
                                            "verified_exact")[0][:14], "verified_exact")
        git(self.repo, "checkout", "-q", "--orphan", "lonely")
        git(self.repo, "rm", "-rfq", ".")
        orphan = commit(self.repo, {"solo.txt": "solo\n"}, "feat: unrelated")
        result = self.record(9, head=orphan)
        self.assertIn("reason: patch_id_unavailable (no_merge_base)", result.stdout.splitlines())
        row = [r for r in self.rows() if r["pr"] == 9][0]
        self.assertEqual((row["patch_id"], row["merge_base"]), (None, None))
        self.assertEqual(self.assertVerdict(self.check(7, orphan), "fail", "patch_id_unavailable"),
                         ["patch_id_unavailable (no_merge_base)"])

    def test_git_not_on_path(self) -> None:
        """No git: record exits 2; check still answers an exact head and fails closed otherwise. [AC-1.4]"""
        self.record(7)
        empty = self.tmp / "nogit"
        empty.mkdir()
        env = _clean_env({"PATH": str(empty)})
        self.assertUsage(self.record(7, env=env), "git not found")
        self.assertVerdict(self.check(7, self.head, env=env), "pass", "verified_exact")
        self.assertEqual(self.assertVerdict(self.check(7, self.base, env=env), "fail",
                                            "patch_id_unavailable"),
                         ["patch_id_unavailable (git_not_found)"])


# ---------------------------------------------------------------------------
# AC-1.5 contract, malformed ledgers, usage errors
# ---------------------------------------------------------------------------

class ContractTests(LedgerCase):
    def test_contract_row_and_smoke_entry(self) -> None:
        """The Classification table has a verify-ledger.py check row with the shared Callers text; the contract test smokes it. [AC-1.5]"""
        doc = CONTRACT_DOC.read_text(encoding="utf-8")
        row = re.search(r"^\| `verify-ledger\.py` \| (\w+) \|  \| (.*) \|$", doc, re.MULTILINE)
        self.assertIsNotNone(row, "no verify-ledger.py row in %s" % CONTRACT_DOC)
        self.assertEqual((row.group(1), row.group(2)), ("check", CALLERS))
        self.assertIn("- `verify-ledger.py` — check.", doc)
        self.assertIn('Smoke("verify-ledger.py"', CONTRACT_TEST.read_text(encoding="utf-8"))

    def test_smoke_shape_in_empty_dir(self) -> None:
        """check in an empty temp dir prints fail with no_rows and exits 1; --help exits 0. [AC-1.5]"""
        empty = self.tmp / "empty"
        empty.mkdir()
        result = run_script(["check", "--pr", "1", "--head", "a" * 40, "--repo", str(empty)],
                            empty)
        self.assertEqual(result.stdout.splitlines(), [
            "fail", "reason: no_rows PR 1",
            "verify-ledger: fail (PR 1 head aaaaaaa NOT VERIFIED, no_rows)"])
        self.assertEqual(result.returncode, 1)
        help_run = run_script(["--help"], self.tmp)
        self.assertEqual(help_run.returncode, 0)
        for needle in ("record", "check", "verify-ledger/1", "--verbatim", "evidence_failed",
                       "patch_id_mismatch"):
            self.assertIn(needle, help_run.stdout)

    def test_malformed_ledger_exits_2(self) -> None:
        """A malformed ledger makes check exit 2 with stdout empty, and record exit 2 without rewriting it. [AC-1.5]"""
        bad_rows = [
            "not json",
            json.dumps({"schema": "x"}),
            json.dumps({"schema": "verify-ledger/1", "rows": {}}),
            json.dumps({"schema": "verify-ledger/1", "rows": [{"pr": 7}]}),
            json.dumps({"schema": "verify-ledger/1", "rows": [{
                "pr": "7", "head": "a" * 40, "patch_id": None, "base_ref": "main",
                "merge_base": None, "recorded_at": "x", "evidence": []}]}),
        ]
        self.ledger.parent.mkdir(parents=True)
        for text in bad_rows:
            with self.subTest(ledger=text[:40]):
                self.ledger.write_text(text, encoding="utf-8")
                self.assertUsage(self.check(7, self.head), "verify-ledger: ")
                self.assertUsage(self.record(7), "verify-ledger: ")
                self.assertEqual(self.ledger.read_text(encoding="utf-8"), text)

    def test_usage_errors(self) -> None:
        """Unresolvable revs, a bad evidence exit, an empty command, PR < 1, and a non-repo exit 2. [AC-1.5]"""
        ev = ["--evidence", "0", "pytest"]
        record = ["record", "--pr", "7", "--head", self.head, "--base", "main"]
        cases = [
            (["record", "--pr", "7", "--head", "nope", "--base", "main"] + ev, "cannot resolve nope"),
            (["record", "--pr", "7", "--head", self.head, "--base", "nope"] + ev,
             "cannot resolve nope"),
            (["record", "--pr", "7", "--head=-x", "--base", "main"] + ev, "cannot resolve -x"),
            (record + ["--evidence", "x", "pytest"], "evidence exit x is not an integer"),
            (record + ["--evidence", "0", " "], "evidence command is empty"),
            (["record", "--pr", "0", "--head", self.head, "--base", "main"] + ev, "--pr"),
            (["check", "--pr", "0", "--head", self.head], "--pr"),
            (record, "--evidence"),
        ]
        for args, cause in cases:
            with self.subTest(args=args):
                self.assertUsage(run_script(args + ["--repo", str(self.repo)], self.tmp), cause)
        not_repo = self.tmp / "plain"
        not_repo.mkdir()
        self.assertUsage(run_script(["record", "--pr", "7", "--head", "HEAD", "--base", "main",
                                     "--evidence", "0", "pytest", "--repo", str(not_repo)],
                                    self.tmp), "not a git work tree")
        self.assertUsage(run_script(["check", "--pr", "7", "--head", "a" * 40, "--repo",
                                     str(self.tmp / "missing")], self.tmp), "not a directory")
        self.assertIsNone(self.ledger_bytes())

    def test_hostile_head_is_escaped(self) -> None:
        """A `--head` with control characters prints on one line. [AC-1.5]"""
        self.record(7)
        result = self.check(7, "bad\nhead\x1b")
        reasons = self.assertVerdict(result, "fail", "head_unavailable")
        self.assertEqual(reasons, ["head_unavailable bad\\nhead\\x1b"])
        self.assertEqual(len(result.stdout.splitlines()), 3)

    def test_plugin_copy_matches(self) -> None:
        """plugins/writ/scripts/verify-ledger.py is the generated byte copy. [AC-1.5]"""
        self.assertEqual(PLUGIN_COPY.read_bytes(), SCRIPT.read_bytes())


if __name__ == "__main__":
    unittest.main()
