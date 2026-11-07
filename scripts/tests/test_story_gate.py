#!/usr/bin/env python3
"""Tests for scripts/story-gate.py (2026-11-06-lean-story-pipeline Story 3).

Every run happens in a temp git repo. story-gate.py is copied into the temp
repo's `scripts/` folder beside stub checkers, because it resolves each checker
as a sibling of itself. `--state-dir` always points into the temp repo, so no
test writes under the real `.writ/state/`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "story-gate.py"
COMMAND = REPO_ROOT / "commands" / "implement-story.md"
CLI_DOC = REPO_ROOT / ".writ" / "docs" / "agent-cli-contract.md"
ADR_DIR = REPO_ROOT / ".writ" / "decision-records"

PRE_ORDER = ["gate2_build_smoke", "gate2_arch_lint", "gate2_5_change_surface",
             "gate0_5_crossings", "gate2_5_blast_radius"]
POST_ORDER = ["gate3_override", "gate3_safety_fact", "gate3_evidence", "gate3_verdict",
              "gate3_5_drift_format", "gate4_coverage", "gate4_authenticity",
              "gate1_repro_order", "gate3_jev_shadow"]

JSON_PASS = json.dumps({"verdict": "pass", "findings": [], "unverifiable": []})
JSON_FAIL_COVERAGE = json.dumps({"verdict": "fail", "findings": [
    {"code": "coverage_below_threshold", "severity": "blocking", "file": "src/a.py"}],
    "unverifiable": []})
SWITCH_ON = "on\nreason: no_config_line\nreview-override switch: x on (.writ/config.md)\n"

# One entry per stub script: {subcommand key: [stdout, exit]}. The key is the
# first argument, or `switch:<name>` for review-override.py switch.
DEFAULT_STUBS: Dict[str, Dict[str, List]] = {
    "build-smoke.py": {"check": [JSON_PASS, 0]},
    "arch-lint.py": {"detect": ["pass\narch-lint detect: 0 ruleset(s), 0 runnable\n", 0]},
    "change-surface.py": {
        "classify": [json.dumps({"class": "single-component"}), 0],
        "blast-radius": [json.dumps({"verdict": "pass", "consumers": {}, "tests": {},
                                     "truncated": [], "reasons": []}), 0],
    },
    "boundary-map.py": {"crossings": [json.dumps({
        "verdict": "pass", "route": "evaluator-agent", "reasons": [],
        "summary": "boundary-map crossings: pass"}), 0]},
    "review-override.py": {
        "switch:safety-fact": [SWITCH_ON, 0],
        "switch:reviewer-filters": [SWITCH_ON, 0],
        "switch:evidence-gate": [SWITCH_ON, 0],
        "check": ["pass\nreview-override: pass (0 findings)\n", 0],
        "safety-fact": ["pass\nrung: claimed=tested measured=tested\nfact: f holds\n"
                        "review-override safety-fact: pass (measured tested, floor tested)\n", 0],
        "evidence": ["pass\nreview-override evidence: pass (0 confirmed, 0 advisory, 0 unverifiable)\n", 0],
    },
    "drift-format.py": {"check": ["pass\ndrift-format: pass (0 entries)\n", 0]},
    "test-integrity.py": {"coverage": [JSON_PASS, 0], "authenticity": [JSON_PASS, 0]},
    "repro-order.py": {"check": ["pass\nrepro-order: pass (1 repro, 1 fix commit(s))\n", 0]},
    "jev-judge.py": {
        "status": ["fail\nreason: no_provider\njev-judge: fail (no_provider)\n", 0],
        "ac-shadow": ["pass\njev-judge ac-shadow: pass\n", 0],
    },
}

STUB_TEMPLATE = '''import json, os, sys
SPEC = json.loads(%r)
NAME = %r
args = sys.argv[1:]
key = args[0] if args else ""
if key == "switch" and "--name" in args:
    key = "switch:" + args[args.index("--name") + 1]
log = os.environ.get("STUB_LOG")
if log:
    with open(log, "a") as fh:
        fh.write(json.dumps([NAME, args]) + "\\n")
out, code = SPEC.get(key, ["", 0])
sys.stdout.write(out)
sys.exit(code)
'''

# The heading form the evaluator and review agents emit.
REVIEW_PASS = "### EVALUATION_RESULT: PASS\n\n### Summary\nok\n"
REVIEW_FAIL = "### REVIEW_RESULT: FAIL\n\n### Summary\nF1\n"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True,
                            text=True, check=True)
    return result.stdout.strip()


def load_module():
    spec = importlib.util.spec_from_file_location("story_gate", str(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Repo:
    """A temp git repo with story-gate.py and stub checkers under scripts/."""

    def __init__(self, git_init: bool = True) -> None:
        self.tmp = tempfile.mkdtemp(prefix="story-gate-")
        self.root = Path(self.tmp)
        self.scripts = self.root / "scripts"
        self.scripts.mkdir()
        shutil.copy2(str(SCRIPT), str(self.scripts / "story-gate.py"))
        self.state = self.root / ".writ" / "state"
        self.log = self.root / "calls.log"
        self.stubs = json.loads(json.dumps(DEFAULT_STUBS))
        self.write_stubs()
        spec = self.root / ".writ" / "specs" / "s"
        (spec / "user-stories").mkdir(parents=True)
        self.story = spec / "user-stories" / "story-1-thing.md"
        self.story.write_text("# Story 1: thing\n", encoding="utf-8")
        self.spec = spec
        (self.root / ".gitignore").write_text(".writ/state/\ncalls.log\nscripts/\n", encoding="utf-8")
        self.base = None
        if git_init:
            git(self.root, "init", "-q")
            git(self.root, "config", "user.email", "t@example.com")
            git(self.root, "config", "user.name", "t")
            git(self.root, "add", "-A")
            git(self.root, "commit", "-q", "-m", "base")
            self.base = git(self.root, "rev-parse", "HEAD")
            (self.root / "src").mkdir()
            (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
            (self.root / "tests").mkdir()
            (self.root / "tests" / "test_a.py").write_text("import src.a\n", encoding="utf-8")
            git(self.root, "add", "-A")
            git(self.root, "commit", "-q", "-m", "story code")

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_stubs(self) -> None:
        for name, spec in self.stubs.items():
            (self.scripts / name).write_text(STUB_TEMPLATE % (json.dumps(spec), name),
                                             encoding="utf-8")

    def stub(self, name: str, key: str, out: str, code: int = 0) -> None:
        self.stubs[name][key] = [out, code]
        self.write_stubs()

    def remove(self, name: str) -> None:
        (self.scripts / name).unlink()

    def write_map(self) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "boundary-story-1-thing.json").write_text(
            json.dumps({"owned": ["src/a.py"], "readable": [], "out_of_scope": []}),
            encoding="utf-8")

    def review(self, text: str) -> Path:
        # Under the gitignored state dir, as Gate 3 saves `<review>`.
        self.state.mkdir(parents=True, exist_ok=True)
        path = self.state / "review.md"
        path.write_text(text, encoding="utf-8")
        return path

    def run(self, *args: str, phase: Optional[str] = None,
            env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(self.scripts / "story-gate.py")]
        if phase:
            argv += ["run", "--phase", phase, "--story", str(self.story), "--spec", str(self.spec),
                     "--base", self.base or "HEAD", "--repo", str(self.root),
                     "--state-dir", str(self.state)]
        argv += list(args)
        full_env = dict(os.environ)
        full_env["STUB_LOG"] = str(self.log)
        full_env.pop("STORY_GATE_TIMEOUT", None)
        if env:
            full_env.update(env)
        return subprocess.run(argv, cwd=str(self.root), capture_output=True, text=True,
                              env=full_env, timeout=120)

    def calls(self) -> List[Tuple[str, List[str]]]:
        if not self.log.is_file():
            return []
        return [tuple(json.loads(ln)) for ln in self.log.read_text().splitlines() if ln]


def check_lines(stdout: str) -> List[str]:
    return [ln for ln in stdout.splitlines() if ln.startswith("check: ")]


def check_ids(stdout: str) -> List[str]:
    return [ln.split()[1] for ln in check_lines(stdout)]


def record_of(stdout: str) -> dict:
    return json.loads(stdout.rstrip("\n").splitlines()[-1])


def line_for(stdout: str, check_id: str) -> str:
    return next(ln for ln in check_lines(stdout) if ln.split()[1] == check_id)


class GateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(self.repo.close)


class CliShapeTests(GateTestCase):
    """AC-3.1: check shape, record last, exit codes 0/1/2."""

    def test_help_documents_both_subcommands(self) -> None:
        """AC-3.1: --help exits 0 and names run and tally."""
        result = self.repo.run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run", result.stdout)
        self.assertIn("tally", result.stdout)
        for sub in ("run", "tally"):
            sub_help = self.repo.run(sub, "--help")
            self.assertEqual(sub_help.returncode, 0, sub_help.stderr)

    def test_usage_error_exits_2_with_empty_stdout(self) -> None:
        """AC-3.1: an unknown flag or a missing --phase is a usage error."""
        for argv in (("run", "--bogus"), ("run", "--phase", "pre-review"), ("nope",)):
            result = self.repo.run(*argv)
            self.assertEqual(result.returncode, 2, argv)
            self.assertEqual(result.stdout, "", argv)

    def test_base_that_is_not_a_commit_is_a_usage_error(self) -> None:
        """AC-3.1 / Error map: `--base` not a commit exits 2, stdout empty."""
        self.repo.base = "0" * 40
        result = self.repo.run(phase="pre-review")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("base", result.stderr)

    def test_pre_review_pass_prints_check_shape_then_record(self) -> None:
        """AC-3.1: line 1 verdict, one check line per check, summary, JSON last."""
        self.repo.write_map()
        result = self.repo.run(phase="pre-review")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = result.stdout.rstrip("\n").splitlines()
        self.assertEqual(lines[0], "pass")
        self.assertEqual(check_ids(result.stdout), PRE_ORDER)
        self.assertRegex(lines[-2], r"^story-gate: pass \(phase pre-review, 5 checks, 0 fail, "
                                    r"\d+ unverifiable\)$")
        record = record_of(result.stdout)
        self.assertEqual(record["schema"], "story-gate-v1")
        self.assertEqual(record["phase"], "pre-review")
        self.assertIn("route: evaluator-agent", result.stdout)
        self.assertIn("change_surface: single-component", result.stdout)
        for name in ("reviewer_filters: on", "evidence_gate: on", "blast_radius: (none)",
                     "safety_fact: not on route"):
            self.assertIn(name, result.stdout)
        on_disk = json.loads((self.repo.state / "story-gate-story-1-thing-pre-review.json")
                             .read_text())
        self.assertEqual(on_disk, record)

    def test_arch_lint_commands_run_and_a_failure_is_advisory(self) -> None:
        """Gate 2: each `command:` line runs; a failing one is flagged, not counted."""
        fail_cmd = "%s -c \"import sys; sys.exit(3)\"" % sys.executable
        self.repo.stub("arch-lint.py", "detect",
                       "pass\ntool: import-linter run setup.cfg\ncommand: %s\n"
                       "tool: archunit via-tests pom.xml\n"
                       "arch-lint detect: 2 ruleset(s), 1 runnable\n" % fail_cmd, 0)
        result = self.repo.run(phase="pre-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        line = line_for(result.stdout, "gate2_arch_lint")
        self.assertIn("gate2_arch_lint fail (command_failed", line)
        self.assertIn("(exit 3)", line)
        self.assertIn("arch-lint: import-linter, archunit (via tests)", result.stdout)
        self.assertNotIn("restart:", result.stdout)

    def test_fail_exits_1(self) -> None:
        """AC-3.1: an overall fail exits 1 with line 1 `fail`."""
        self.repo.stub("build-smoke.py", "check", json.dumps({
            "verdict": "fail", "unverifiable": [],
            "findings": [{"code": "build_failed_source", "severity": "blocking"}]}), 1)
        (self.repo.root / "src" / "b.py").write_text("y = 2\n", encoding="utf-8")
        result = self.repo.run(phase="pre-review")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.splitlines()[0], "fail")
        self.assertIn("restart: gate2", result.stdout)
        self.assertIn("build_failed_source", line_for(result.stdout, "gate2_build_smoke"))


class PostReviewRecordTests(GateTestCase):
    """AC-3.2: fixed order, atomic record with head_sha and dirty, restart."""

    def test_order_record_and_first_failing_restart(self) -> None:
        """AC-3.2: one failing and one passing stub; every check runs in order."""
        review = self.repo.review(REVIEW_PASS)
        tests_out = self.repo.state / "tests.txt"
        tests_out.write_text("command: pytest\nexit code: 0\n", encoding="utf-8")
        self.repo.stub("drift-format.py", "check",
                       "fail\nreason: missing_field DEV-001 Severity\ndrift-format: fail\n", 1)
        self.repo.stub("test-integrity.py", "coverage", JSON_FAIL_COVERAGE, 1)
        result = self.repo.run("--review-output", str(review), "--tests-output", str(tests_out),
                               phase="post-review")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(check_ids(result.stdout), POST_ORDER)
        # drift-format is the first failing check, so its target wins.
        self.assertIn("restart: gate3-blocked", result.stdout)
        self.assertIn("gate4_coverage fail (coverage_below_threshold", result.stdout)
        path = self.repo.state / "story-gate-story-1-thing-post-review.json"
        record = json.loads(path.read_text())
        self.assertEqual(record, record_of(result.stdout))
        self.assertEqual(record["head_sha"], git(self.repo.root, "rev-parse", "HEAD"))
        self.assertIs(record["dirty"], False)
        self.assertEqual(record["base"], self.repo.base)
        self.assertEqual(record["restart"], "gate3-blocked")
        self.assertEqual([c["id"] for c in record["checks"]], POST_ORDER)
        drift = next(c for c in record["checks"] if c["id"] == "gate3_5_drift_format")
        self.assertEqual(drift["exit"], 1)
        self.assertEqual(drift["reasons"], ["missing_field DEV-001 Severity"])
        self.assertTrue(drift["command"][-1].endswith("review.md"))
        # The checkers ran in the table's order.
        ran = [name for name, _ in self.repo.calls()]
        self.assertLess(ran.index("drift-format.py"), ran.index("test-integrity.py"))
        self.assertLess(ran.index("test-integrity.py"), ran.index("jev-judge.py"))
        # Atomic write leaves no temp file; history keeps this run.
        leftovers = [p.name for p in self.repo.state.iterdir() if p.name.startswith(".")]
        self.assertEqual(leftovers, [])
        history = list((self.repo.state / "story-gate-history").glob(
            "story-1-thing-post-review-*.json"))
        self.assertEqual(len(history), 1)

    def test_rerun_replaces_record_and_adds_history(self) -> None:
        """AC-3.2: the record is replaced, never appended; history grows."""
        review = self.repo.review(REVIEW_PASS)
        for _ in range(2):
            self.assertEqual(self.repo.run("--review-output", str(review),
                                           phase="post-review").returncode, 0)
        record = json.loads((self.repo.state / "story-gate-story-1-thing-post-review.json")
                            .read_text())
        self.assertEqual(record["verdict"], "pass")
        self.assertEqual(len(list((self.repo.state / "story-gate-history").iterdir())), 2)

    def test_dirty_tree_outside_the_spec_folder_is_recorded(self) -> None:
        """Business Rule 5: only edits under the `--spec` folder (Gate 3.5 § A's
        drift-log.md and spec-lite.md) leave dirty false; any other uncommitted
        path, `.writ/` included, sets it."""
        review = self.repo.review(REVIEW_PASS)
        (self.repo.spec / "drift-log.md").write_text("# log\n", encoding="utf-8")
        (self.repo.spec / "spec-lite.md").write_text("# lite\n", encoding="utf-8")
        clean = record_of(self.repo.run("--review-output", str(review),
                                        phase="post-review").stdout)
        self.assertIs(clean["dirty"], False)
        for path in (self.repo.root / ".writ" / "config.md",
                     self.repo.root / ".writ" / "docs" / "shipped.md",
                     self.repo.root / ".writ" / "specs" / "other" / "spec-lite.md",
                     self.repo.root / "src" / "a.py"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("changed\n", encoding="utf-8")
            dirty = record_of(self.repo.run("--review-output", str(review),
                                            phase="post-review").stdout)
            self.assertIs(dirty["dirty"], True, path)
            git(self.repo.root, "add", "-A")
            git(self.repo.root, "commit", "-q", "-m", "commit %s" % path.name)

    def test_worktree_only_modification_keeps_porcelain_columns(self) -> None:
        """Business Rule 5: a ` M` entry (tracked file, modified in the worktree
        only) is parsed with its leading status column intact. Stripping git's
        output turned the first ` M .writ/specs/...` into `M .writ/...`, whose
        path read `writ/specs/...` and set dirty on a clean spec-folder edit."""
        review = self.repo.review(REVIEW_PASS)
        for name in ("drift-log.md", "spec-lite.md"):
            (self.repo.spec / name).write_text("# v1\n", encoding="utf-8")
        git(self.repo.root, "add", "-A")
        git(self.repo.root, "commit", "-q", "-m", "spec files")
        for name in ("drift-log.md", "spec-lite.md"):
            (self.repo.spec / name).write_text("# v2\n", encoding="utf-8")
        status = subprocess.run(["git", "-C", str(self.repo.root), "status", "--porcelain"],
                                capture_output=True, text=True, check=True).stdout
        self.assertTrue(status.startswith(" M .writ/specs/s/"), status)
        clean = record_of(self.repo.run("--review-output", str(review),
                                        phase="post-review").stdout)
        self.assertIs(clean["dirty"], False)
        git(self.repo.root, "add", "-A")
        git(self.repo.root, "commit", "-q", "-m", "spec files v2")
        (self.repo.root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        dirty = record_of(self.repo.run("--review-output", str(review),
                                        phase="post-review").stdout)
        self.assertIs(dirty["dirty"], True)

    def test_git_lists_keep_leading_spaces(self) -> None:
        """`_git_list` never strips: NUL-separated entries keep their own spaces."""
        module = load_module()
        name = " lead.py"  # sorts first, so it opens git's output
        (self.repo.root / name).write_text("y = 1\n", encoding="utf-8")
        self.assertEqual(module._git_list(
            self.repo.root, "ls-files", "--others", "--exclude-standard", "-z"), [name])
        git(self.repo.root, "add", "-A")
        self.assertEqual(module._git_list(
            self.repo.root, "diff", "--name-only", "-z", "--cached"), [name])

    def test_changed_new_and_test_files_come_from_base(self) -> None:
        """The runner computes the file lists from `--base`, plus untracked files."""
        (self.repo.root / "src" / "new.py").write_text("z = 1\n", encoding="utf-8")
        review = self.repo.review(REVIEW_PASS)
        self.repo.run("--review-output", str(review), phase="post-review")
        calls = self.repo.calls()
        coverage = next(a for n, a in calls if n == "test-integrity.py" and a[0] == "coverage")
        self.assertIn("src/a.py", coverage)
        self.assertIn("src/new.py", coverage)
        self.assertNotIn("tests/test_a.py", coverage)
        auth = next(a for n, a in calls if n == "test-integrity.py" and a[0] == "authenticity")
        self.assertIn("tests/test_a.py", auth)
        self.assertNotIn("src/a.py", auth)

    def test_parallel_stories_write_separate_records(self) -> None:
        """Interaction edge case: two stories in one batch never share a file."""
        review = self.repo.review(REVIEW_PASS)
        other = self.repo.spec / "user-stories" / "story-2-other.md"
        other.write_text("# Story 2: other\n", encoding="utf-8")
        self.repo.run("--review-output", str(review), phase="post-review")
        self.repo.story = other
        self.repo.run("--review-output", str(review), phase="post-review")
        names = sorted(p.name for p in self.repo.state.glob("story-gate-*.json"))
        self.assertEqual(names, ["story-gate-story-1-thing-post-review.json",
                                 "story-gate-story-2-other-post-review.json"])


class UnverifiableTests(GateTestCase):
    """AC-3.3 and the Error & Rescue Map / Shadow Paths rows."""

    def test_missing_script_is_helper_error_and_run_continues(self) -> None:
        """AC-3.3: a missing checker reads unverifiable (helper_error: missing ...)."""
        self.repo.remove("drift-format.py")
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.splitlines()[0], "pass")
        line = line_for(result.stdout, "gate3_5_drift_format")
        self.assertRegex(line, r"unverifiable \(helper_error: missing .*drift-format\.py\)")
        self.assertEqual(check_ids(result.stdout), POST_ORDER)
        self.assertTrue(any(n == "test-integrity.py" for n, _ in self.repo.calls()))

    def test_exit_outside_0_1_2_is_helper_error(self) -> None:
        """AC-3.3: an exit outside 0/1/2 never sets the overall verdict to fail."""
        self.repo.stub("drift-format.py", "check", "fail\nreason: boom\n", 3)
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("unverifiable (helper_error: exit 3)",
                      line_for(result.stdout, "gate3_5_drift_format"))

    def test_empty_stdout_is_helper_error(self) -> None:
        """Error map: empty stdout is helper_error."""
        self.repo.stub("drift-format.py", "check", "", 0)
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertIn("helper_error: exit 0, empty stdout",
                      line_for(result.stdout, "gate3_5_drift_format"))

    def test_checker_exit_2_is_helper_error_and_the_agent_fail_stands(self) -> None:
        """Evidence table row 8: an evidence checker that exits 2 reads
        unverifiable (helper_error: exit 2 ...), and the agent FAIL stands."""
        self.repo.stub("review-override.py", "evidence", "unverifiable\nreason: bad_args\n", 2)
        review = self.repo.review(REVIEW_FAIL)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("gate3_evidence unverifiable (helper_error: exit 2",
                      line_for(result.stdout, "gate3_evidence"))
        gate3 = record_of(result.stdout)["gate3"]
        self.assertEqual((gate3["verdict"], gate3["row"]), ("FAIL", "8"))
        self.assertIn("restart: gate1", result.stdout)
        self.assertIn("evidence-gate: unverifiable (helper_error: exit 2", result.stdout)

    def test_missing_review_output_path_is_unreadable(self) -> None:
        """Error map: a `--review-output` path that does not exist marks every
        review check unverifiable (review_output_unreadable); no Gate 3 decision."""
        missing = self.repo.state / "no-such-review.md"
        result = self.repo.run("--review-output", str(missing), phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.splitlines()[0], "pass")
        for cid in ("gate3_override", "gate3_safety_fact", "gate3_evidence", "gate3_verdict",
                    "gate3_5_drift_format", "gate3_jev_shadow"):
            self.assertIn("unverifiable (review_output_unreadable)",
                          line_for(result.stdout, cid), cid)
        self.assertNotIn("gate3", record_of(result.stdout))
        self.assertNotIn("gate3:", result.stdout)

    def test_timeout_is_unverifiable(self) -> None:
        """Error map: a check over its time limit reads unverifiable (timeout)."""
        stub = self.repo.scripts / "drift-format.py"
        stub.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review",
                               env={"STORY_GATE_TIMEOUT": "1"})
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("unverifiable (timeout)", line_for(result.stdout, "gate3_5_drift_format"))

    def test_no_review_output_marks_review_checks(self) -> None:
        """Shadow path Nil (`--quick`): review checks unverifiable, record still written."""
        result = self.repo.run(phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        for cid in ("gate3_override", "gate3_safety_fact", "gate3_evidence", "gate3_verdict",
                    "gate3_5_drift_format", "gate3_jev_shadow"):
            self.assertIn("unverifiable (no_review_output)", line_for(result.stdout, cid), cid)
        self.assertIn("gate4_coverage pass", result.stdout)
        self.assertTrue((self.repo.state / "story-gate-story-1-thing-post-review.json").is_file())

    def test_empty_change_set_passes(self) -> None:
        """Shadow path Empty: no changed files; file-needing checks unverifiable; pass."""
        self.repo.base = git(self.repo.root, "rev-parse", "HEAD")
        self.repo.write_map()
        result = self.repo.run(phase="pre-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.splitlines()[0], "pass")
        self.assertIn("unverifiable (no_changed_files)",
                      line_for(result.stdout, "gate2_5_change_surface"))
        self.assertIn("route: review-agent (unverifiable: no_changed_files)", result.stdout)

    def test_not_a_git_repo_marks_git_checks_no_git(self) -> None:
        """Error map: not a git repo -> git-dependent checks unverifiable (no_git)."""
        plain = Repo(git_init=False)
        self.addCleanup(plain.close)
        plain.write_map()
        result = plain.run(phase="pre-review")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unverifiable (no_git)", line_for(result.stdout, "gate2_5_change_surface"))
        record = record_of(result.stdout)
        self.assertIsNone(record["head_sha"])
        self.assertIsNone(record["dirty"])

    def test_record_write_failure_keeps_line_1(self) -> None:
        """Error map: an unwritable state dir adds reason: record_write_failed."""
        self.repo.state.parent.mkdir(parents=True, exist_ok=True)
        self.repo.state.write_text("not a directory", encoding="utf-8")
        review = self.repo.spec / "review.md"  # the state dir is a file here
        review.write_text(REVIEW_PASS, encoding="utf-8")
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.splitlines()[0], "pass")
        self.assertIn("reason: record_write_failed", result.stdout)
        self.assertEqual(record_of(result.stdout)["schema"], "story-gate-v1")

    def test_jev_shadow_is_never_counted(self) -> None:
        """Technical spec: the Jev shadow runs last, only after status pass, uncounted."""
        self.repo.stub("jev-judge.py", "status", "pass\nreason: enabled\njev-judge: pass\n", 0)
        self.repo.stub("jev-judge.py", "ac-shadow", "fail\nreason: disagree\njev: fail\n", 1)
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        jev = next(c for c in record_of(result.stdout)["checks"] if c["id"] == "gate3_jev_shadow")
        self.assertEqual(jev["verdict"], "fail")
        self.assertIs(jev["counted"], False)
        self.assertTrue(any(p.suffix == ".patch" for p in self.repo.state.iterdir()))


class RouteAndGate3Tests(GateTestCase):
    """The Gate 2.5 route reaches Gate 3, and the evidence table is first-match."""

    def test_risk_route_runs_blast_radius_and_turns_safety_fact_on(self) -> None:
        """Business Rule 3: route review-agent + switch on -> blast radius file."""
        self.repo.write_map()
        self.repo.stub("boundary-map.py", "crossings", json.dumps({
            "verdict": "pass", "route": "review-agent",
            "reasons": ["outside_boundary src/x.py"], "summary": "s"}), 0)
        pre = self.repo.run(phase="pre-review")
        self.assertIn("route: review-agent (outside_boundary src/x.py)", pre.stdout)
        blast = (self.repo.state / "blast-radius-story-1-thing.json").resolve()
        self.assertTrue(blast.is_file())
        self.assertIn("blast_radius: %s" % blast, pre.stdout)
        self.assertIn("safety_fact: on", pre.stdout)
        crossings = next(a for n, a in self.repo.calls() if n == "boundary-map.py")
        self.assertEqual(crossings[crossings.index("--surface") + 1], "single-component")
        self.assertTrue(crossings[crossings.index("--map") + 1].endswith(
            ".writ/state/boundary-story-1-thing.json"))
        review = self.repo.review(REVIEW_PASS)
        self.repo.run("--review-output", str(review), phase="post-review")
        fact = next(a for n, a in self.repo.calls() if n == "review-override.py"
                    and a[0] == "safety-fact")
        self.assertIn(str(blast), fact)

    def test_safety_fact_switch_off_skips_blast_radius(self) -> None:
        """Gate 2.5: on the risk route, blast radius runs only with the switch on."""
        self.repo.write_map()
        self.repo.stub("boundary-map.py", "crossings", json.dumps({
            "verdict": "pass", "route": "review-agent", "reasons": ["r"], "summary": "s"}), 0)
        self.repo.stub("review-override.py", "switch:safety-fact",
                       "off\nreason: config_off\nreview-override switch: safety-fact off\n", 0)
        pre = self.repo.run(phase="pre-review")
        self.assertIn("skip (safety_fact_off)", line_for(pre.stdout, "gate2_5_blast_radius"))
        self.assertIn("blast_radius: (none)", pre.stdout)
        self.assertIn("safety_fact: off", pre.stdout)
        self.assertFalse((self.repo.state / "blast-radius-story-1-thing.json").exists())
        names = [(n, a[0]) for n, a in self.repo.calls()]
        self.assertIn(("review-override.py", "switch"), names)
        self.assertNotIn(("change-surface.py", "blast-radius"), names)

    def test_no_boundary_map_routes_evaluator(self) -> None:
        """Gate 0.5 skipped (no map): crossings skip, evaluator route."""
        result = self.repo.run(phase="pre-review")
        self.assertIn("skip (no_boundary_map)", line_for(result.stdout, "gate0_5_crossings"))
        self.assertIn("route: evaluator-agent (no_boundary_map)", result.stdout)

    def test_unverifiable_crossings_route_review_agent(self) -> None:
        """Gate 2.5: an unverifiable crossings check routes review-agent."""
        self.repo.write_map()
        self.repo.remove("boundary-map.py")
        result = self.repo.run(phase="pre-review")
        self.assertIn("route: review-agent (unverifiable: helper_error", result.stdout)

    def test_agent_fail_washed_by_evidence_pass(self) -> None:
        """Evidence table row 9: an agent FAIL whose evidence passes becomes PASS."""
        review = self.repo.review(REVIEW_FAIL)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("gate3: PASS", result.stdout)

    def test_agent_fail_stands_when_evidence_unverifiable(self) -> None:
        """Evidence table row 8: unverifiable evidence leaves the FAIL standing."""
        self.repo.stub("review-override.py", "evidence",
                       "unverifiable\nreason: no_test_runner\nreview-override evidence: "
                       "unverifiable (no_test_runner)\n", 0)
        review = self.repo.review(REVIEW_FAIL)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("gate3: FAIL", result.stdout)
        self.assertIn("restart: gate1", result.stdout)

    def test_tree_mutation_outranks_a_check_fail(self) -> None:
        """Evidence table row 1 before row 2: BLOCKED, not recode."""
        self.repo.stub("review-override.py", "check",
                       "fail\nreason: untested_criterion AC-1.1\nreview-override: fail\n", 1)
        self.repo.stub("review-override.py", "evidence",
                       "fail\nreason: repro_mutated_tree src/a.py\nreview-override evidence: "
                       "fail (0 confirmed, 0 advisory, 0 unverifiable)\n", 1)
        review = self.repo.review(REVIEW_FAIL)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertIn("restart: gate3-blocked", result.stdout)

    def test_safety_fact_missing_restarts_gate3(self) -> None:
        """Evidence table row 4: a missing safety fact re-spawns Gate 3."""
        self.repo.write_map()
        self.repo.stub("boundary-map.py", "crossings", json.dumps({
            "verdict": "pass", "route": "review-agent", "reasons": ["r"], "summary": "s"}), 0)
        self.repo.run(phase="pre-review")
        self.repo.stub("review-override.py", "safety-fact",
                       "fail\nrung: claimed=none measured=none\nfact: \n"
                       "reason: safety_fact_missing section\nreview-override safety-fact: fail\n", 1)
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertIn("restart: gate3\n", result.stdout)

    def test_verdict_line_agrees_with_the_gate3_result(self) -> None:
        """No `gate3_verdict` line reads `pass` beside `gate3: FAIL`: a row 1-4a
        decision reads `skip` with that row, so the deciding check's catch is
        counted once; rows 5-9 read the decision."""
        self.repo.stub("review-override.py", "check",
                       "fail\nreason: untested_criterion AC-1.1\nreview-override: fail\n", 1)
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        record = record_of(result.stdout)
        self.assertEqual((record["gate3"]["verdict"], record["gate3"]["row"]), ("FAIL", "2"))
        self.assertIn("gate3_verdict skip (FAIL (row 2: check fail: untested_criterion",
                      line_for(result.stdout, "gate3_verdict"))
        counted = [c["id"] for c in record["checks"] if c["counted"] and c["verdict"] == "fail"]
        self.assertEqual(counted, ["gate3_override"])
        self.repo.stub("review-override.py", "check", "pass\nreview-override: pass\n", 0)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertIn("gate3_verdict pass (PASS (row 5))", line_for(result.stdout, "gate3_verdict"))
        self.assertIn("gate3: PASS (row 5", result.stdout)

    def test_prior_manifest_runs_evidence_on_pass(self) -> None:
        """Row 4a: once the manifest exists, evidence runs on any verdict with --prior."""
        self.repo.state.mkdir(parents=True, exist_ok=True)
        (self.repo.state / "evidence-story-1-thing.json").write_text("{}", encoding="utf-8")
        self.repo.stub("review-override.py", "evidence",
                       "fail\nreason: repro_removed tests/test_r.py\nreview-override evidence: "
                       "fail (repro_removed tests/test_r.py)\n", 1)
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertIn("restart: gate1", result.stdout)
        evidence = next(a for n, a in self.repo.calls() if n == "review-override.py"
                        and a[0] == "evidence")
        self.assertIn("--prior", evidence)

    def test_repro_order_runs_only_with_a_repro_commit(self) -> None:
        """Gate 1 bug path: repro-order runs when a commit since base has `Repro:`."""
        review = self.repo.review(REVIEW_PASS)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertIn("skip (no_repro_commit)", line_for(result.stdout, "gate1_repro_order"))
        (self.repo.root / "tests" / "test_b.py").write_text("import src.a\n", encoding="utf-8")
        git(self.repo.root, "add", "-A")
        git(self.repo.root, "commit", "-q", "-m", "test: repro\n\nRepro: crash on empty")
        self.repo.stub("repro-order.py", "check",
                       "fail\nreason: no_fix_after_repro abc\nrepro-order: fail\n", 1)
        result = self.repo.run("--review-output", str(review), phase="post-review")
        self.assertEqual(result.returncode, 1)
        record = record_of(result.stdout)
        self.assertIsNone(record["restart"])
        self.assertNotIn("restart:", result.stdout)


class TallyTests(GateTestCase):
    """AC-3.4: runs, fails, sole_catches per check id; writes nothing."""

    def test_tally_counts_and_writes_nothing(self) -> None:
        """AC-3.4: one fail-alone record and one passing record."""
        review = self.repo.review(REVIEW_PASS)
        self.repo.run("--review-output", str(review), phase="post-review")
        self.repo.stub("drift-format.py", "check", "fail\nreason: x\ndrift-format: fail\n", 1)
        self.repo.run("--review-output", str(review), phase="post-review")
        before = sorted(str(p) for p in self.repo.state.rglob("*"))
        result = self.repo.run("tally", "--state-dir", str(self.repo.state))
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "pass")
        self.assertIn("tally: gate3_5_drift_format runs=2 fails=1 sole_catches=1", lines)
        self.assertIn("tally: gate4_coverage runs=2 fails=0 sole_catches=0", lines)
        self.assertTrue(lines[-1].startswith("story-gate tally: pass (2 records"))
        self.assertEqual(sorted(str(p) for p in self.repo.state.rglob("*")), before)

    def test_tally_without_history_is_unverifiable(self) -> None:
        """AC-3.4: no history prints unverifiable and reason: no_records."""
        result = self.repo.run("tally", "--state-dir", str(self.repo.state))
        self.assertEqual(result.returncode, 0)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "unverifiable")
        self.assertIn("reason: no_records", lines)
        self.assertFalse(self.repo.state.exists())


def _gates_by_path(text: str) -> Dict[str, Optional[str]]:
    front = text.split("\n---\n", 1)[0]
    block = front.split("\ngates:\n", 1)[1]
    paths: Dict[str, Optional[str]] = {}
    current = None
    for line in block.splitlines():
        m = re.match(r"^  - id: (\S+)$", line)
        if m:
            current = m.group(1)
            paths[current] = None
            continue
        m = re.match(r"^    path: (\S+)$", line)
        if m and current:
            paths[current] = m.group(1)
    return paths


class CommandWiringTests(unittest.TestCase):
    """AC-3.5: the procedure, the check table, and the docs agree."""

    def setUp(self) -> None:
        self.text = COMMAND.read_text(encoding="utf-8")

    def test_default_check_table_equals_default_gates(self) -> None:
        """AC-3.5: the runner's gate ids equal the `path: default` gates entries."""
        module = load_module()
        table_gates = {row.gate for rows in module.CHECKS.values() for row in rows}
        default = {gid for gid, path in _gates_by_path(self.text).items()
                   if path in (None, "default")}
        self.assertEqual(table_gates, default)
        ids = [row.id for rows in module.CHECKS.values() for row in rows]
        self.assertEqual(ids, PRE_ORDER + POST_ORDER)

    def test_default_path_names_two_runner_calls_and_four_invocations(self) -> None:
        """AC-3.5: exactly two story-gate calls; at most four script invocations."""
        body = self.text.split("\n---\n", 1)[1]
        start = body.index("## Command Process")
        full = body.index("### Full-Pipeline Gates")
        step4 = body.index("### Step 4: Story Completion")
        default = body[start:full] + body[step4:body.index("## Error Handling")]
        runs = re.findall(r"python3 scripts/story-gate\.py run --phase (\S+)", default)
        self.assertEqual(runs, ["pre-review", "post-review"])
        invocations = set(re.findall(r"python3 scripts/([\w.-]+ \w[\w-]*)", default))
        self.assertLessEqual(len(invocations), 4, sorted(invocations))
        self.assertEqual(invocations, {"story-context.py assemble", "boundary-map.py compute",
                                       "story-gate.py run"})
        self.assertLess(default.index("--phase pre-review"), default.index("#### Gate 3:"))
        self.assertGreater(default.index("--phase post-review"), default.index("#### Gate 3:"))

    # AC-3.5's byte shrink is pinned in one place only: the implement-story.md
    # entry of KNOWN_OVER_BUDGET in test_governor_enforcement.py (eval size-pins).

    def test_cli_doc_row_and_adr_note(self) -> None:
        """AC-3.5: agent-cli-contract row and the dated ADR-029 runner note."""
        doc = CLI_DOC.read_text(encoding="utf-8")
        row = next(ln for ln in doc.splitlines() if ln.startswith("| `story-gate.py` |"))
        self.assertIn("| check |", row)
        self.assertIn("commands/implement-story.md", row)
        adr = next(ADR_DIR.glob("adr-029-*.md")).read_text(encoding="utf-8")
        self.assertRegex(adr, r"\*Amended 2026-11-06[^\n]*story-gate")
        self.assertIn("not a dispatcher", adr)


if __name__ == "__main__":
    unittest.main()
