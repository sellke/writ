#!/usr/bin/env python3
"""Guard tests for Stories 1 and 2 of `2026-10-20-harness-cuts`.

The lean command siblings, the install/update logic that skipped them, and
every lean code path in `scripts/` are gone. These tests fail if any of it
comes back:

- no `commands/*.lean.md` file exists;
- the guard grep from spec.md Business Rule 2, with two sibling Phase 13
  specs also excluded, finds nothing in the repo;
- neither `scripts/install.sh` nor `scripts/update.sh` defines or calls
  `is_unshipped_lean_sibling`;
- the lean-only tests are gone, and no mixed test or eval check that used to
  read a lean file still names one;
- `lean-decision.py` and the Story 2 lean tests are gone;
- with the old lean variable exported, `story-context.py` and
  `measure-invocation.py` behave exactly as without it;
- `eval-leanness.py` and `eval.sh` `check_manifest` treat every
  `commands/*.md` as a command, whatever its name;
- the three `is_shippable_script` copies are identical and no longer name
  `lean-decision.py`.

This file and `test_install_update_harness_cuts.sh` are excluded from the
guard grep, so only they may name the old variable and the lean suffix.

Each test cites the acceptance criterion it covers (AC-1.1, AC-1.5, AC-2.1,
AC-2.2, AC-2.4, AC-2.5).
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
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[2]

GUARD_PATTERNS = ("-e", "WRIT_HARNESS_LEAN", "-e", r"\.lean\.md")

# Business Rule 2 exclusions: historical records, the Complete spec that
# names the lean files, this spec's own folder, and the two guard tests.
EXCLUDED = (
    ":!CHANGELOG.md",
    ":!.writ/decision-log.md",
    ":!.writ/specs/archive",
    ":!.writ/research",
    ":!.writ/product",
    ":!.writ/decision-records",
    ":!.writ/specs/2026-10-12-agent-cli-contract",
    ":!.writ/specs/2026-10-20-harness-cuts",
    ":!scripts/tests/test_harness_cuts.py",
    ":!scripts/tests/test_install_update_harness_cuts.sh",
    # Sibling Phase 13 specs written after this one; their contracts name the deleted lean files as history.
    ":!.writ/specs/2026-10-20-platform-neutral-names",
    ":!.writ/specs/2026-10-20-shipped-command-hygiene",
)

INSTALL_SCRIPTS = ("scripts/install.sh", "scripts/update.sh")
LEAN_SKIP_FUNCTION = "is_unshipped_lean_sibling"

# Tests that only read the real lean files. Story 1 deletes them.
LEAN_ONLY_TESTS = (
    "scripts/tests/test_lean_commands.py",
    "scripts/tests/test_lean_preamble.py",
    "scripts/tests/test_install_update_lean_siblings.sh",
)

# Tests that read a lean file beside their other assertions. Story 1 removes
# the lean reads and keeps the rest.
MIXED_TESTS = (
    "scripts/tests/test_agent_cli_contract.py",
    "scripts/tests/test_implement_story_default_path.py",
    "scripts/tests/test_panel_trial_outcome.py",
    "scripts/tests/test_product_check_direction.py",
    "scripts/tests/test_quality_gate_wiring.py",
    "scripts/tests/test_review_panel.py",
    "scripts/tests/test_jev_setup_hooks.sh",
    "scripts/tests/test_jev_shadow_hooks.sh",
    "scripts/tests/test_uat_plan_verification_hooks.sh",
    "scripts/tests/test_manifest_shipped_baselines.sh",
)

# eval.sh checks that pinned a lean file. Each now pins the default files only.
EVAL_CHECKS = ("check_review_panel", "check_product_check_direction")

# Files Story 2 deletes.
STORY2_DELETED = (
    "scripts/lean-decision.py",
    "scripts/tests/test_lean_decision.py",
    "scripts/tests/test_measure_invocation_lean.py",
    "scripts/tests/test_eval_manifest_lean.sh",
)

# The variable the lean code paths read. Nothing reads it now.
OLD_LEAN_VARIABLE = "WRIT_HARNESS_LEAN"

SHIP_FILTER_SCRIPTS = ("scripts/install.sh", "scripts/update.sh", "scripts/unlink.sh")
DECISION_SCRIPT = "lean-decision.py"
DOCS_NAMING_DEV_ONLY = (".writ/docs/agent-cli-contract.md", "commands/update-writ.md")
DEV_SCRIPTS_TEST = "scripts/tests/test_install_update_dev_scripts.sh"


def guard_grep(paths: tuple) -> List[str]:
    """Run the guard grep over `paths` and return the matching lines.

    `git grep` exits 1 when nothing matches. Any exit other than 0 or 1 is
    an error in the command itself, not a test result."""
    cmd = ["git", "grep", "-n", *GUARD_PATTERNS, "--", *paths, *EXCLUDED]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if proc.returncode == 1:
        return []
    if proc.returncode == 0:
        return proc.stdout.splitlines()
    raise RuntimeError("guard grep failed (exit %d): %s\n%s"
                       % (proc.returncode, " ".join(cmd), proc.stderr))


class LeanFilesGoneTest(unittest.TestCase):
    """AC-1.1, AC-2.1: the lean siblings no longer exist and nothing in the
    repo outside the excluded paths names them."""

    def test_ac_1_1_no_lean_command_files(self):
        lean = sorted(p.name for p in (REPO_ROOT / "commands").glob("*.lean.md"))
        self.assertEqual(lean, [], "lean command files still exist: %s" % ", ".join(lean))

    def test_ac_1_1_ac_2_1_guard_grep_is_empty_repo_wide(self):
        # Story 1 ran this over its own paths; Story 2 widens it to the repo.
        hits = guard_grep((".",))
        self.assertEqual(hits, [], "lean references remain:\n" + "\n".join(hits))

    def test_ac_2_1_lean_decision_and_story2_lean_tests_are_deleted(self):
        present = [rel for rel in STORY2_DELETED if (REPO_ROOT / rel).exists()]
        self.assertEqual(present, [], "files Story 2 deletes still exist: %s" % ", ".join(present))


class LeanSkipLogicGoneTest(unittest.TestCase):
    """AC-1.1: install.sh and update.sh carry no lean skip function."""

    def test_ac_1_1_install_and_update_do_not_define_the_lean_skip_function(self):
        definition = re.compile(r"^\s*%s\s*\(\)" % LEAN_SKIP_FUNCTION, re.MULTILINE)
        defined = [rel for rel in INSTALL_SCRIPTS
                   if definition.search((REPO_ROOT / rel).read_text(encoding="utf-8"))]
        self.assertEqual(defined, [], "%s is still defined in: %s"
                         % (LEAN_SKIP_FUNCTION, ", ".join(defined)))

    def test_ac_1_1_install_and_update_do_not_call_the_lean_skip_function(self):
        # A leftover call would not fail at run time: `name ... && continue`
        # just skips the `continue` when the command is not found.
        callers = [rel for rel in INSTALL_SCRIPTS
                   if LEAN_SKIP_FUNCTION in (REPO_ROOT / rel).read_text(encoding="utf-8")]
        self.assertEqual(callers, [], "%s is still referenced in: %s"
                         % (LEAN_SKIP_FUNCTION, ", ".join(callers)))


def shell_function_body(text: str, name: str) -> str:
    """The lines of a top-level bash function, from `name() {` to the first
    line that is exactly `}`."""
    match = re.search(r"^%s\(\) \{\n.*?^\}$" % re.escape(name), text, re.MULTILINE | re.DOTALL)
    if match is None:
        raise RuntimeError("scripts/eval.sh has no function %s" % name)
    return match.group(0)


class NoTestReadsALeanFileTest(unittest.TestCase):
    """AC-1.5: no test or eval check reads a lean file. The full suite and
    eval.sh run the rest; this pins that the lean reads are gone."""

    def test_ac_1_5_lean_only_tests_are_deleted(self):
        present = [rel for rel in LEAN_ONLY_TESTS if (REPO_ROOT / rel).exists()]
        self.assertEqual(present, [], "lean-only tests still exist: %s" % ", ".join(present))

    def test_ac_1_5_mixed_tests_name_no_lean_file(self):
        hits = guard_grep(MIXED_TESTS)
        self.assertEqual(hits, [], "mixed tests still read a lean file:\n" + "\n".join(hits))

    def test_ac_1_5_mixed_tests_still_exist(self):
        # The lean reads go; the tests that held them stay and keep running.
        missing = [rel for rel in MIXED_TESTS if not (REPO_ROOT / rel).is_file()]
        self.assertEqual(missing, [], "mixed tests were deleted: %s" % ", ".join(missing))

    def test_ac_1_5_eval_checks_pin_no_lean_file(self):
        text = (REPO_ROOT / "scripts" / "eval.sh").read_text(encoding="utf-8")
        for name in EVAL_CHECKS:
            with self.subTest(check=name):
                body = shell_function_body(text, name)
                lean_lines = [line.strip() for line in body.splitlines() if ".lean.md" in line]
                self.assertEqual(lean_lines, [], "%s still pins a lean file:\n%s"
                                 % (name, "\n".join(lean_lines)))
                self.assertIn("commands/", body, "%s no longer pins any command file" % name)


def env_with_old_variable(value: str = "1") -> dict:
    """os.environ without the Anthropic key (no network), with the old lean
    variable set to `value`."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env[OLD_LEAN_VARIABLE] = value
    return env


def env_without_old_variable() -> dict:
    return {k: v for k, v in os.environ.items()
            if k not in ("ANTHROPIC_API_KEY", OLD_LEAN_VARIABLE)}


def over_budget_story(root: Path) -> Path:
    """A spec folder whose one story resolves two business rules, more bytes
    than the budget the tests pass."""
    spec = root / "s-spec"
    (spec / "user-stories").mkdir(parents=True)
    (spec / "spec.md").write_text(
        "# Spec\n\n## \U0001F4CB Business Rules\n\n"
        "1. **First rule.** " + "a" * 200 + "\n"
        "2. **Second rule.** " + "b" * 200 + "\n", encoding="utf-8")
    story = spec / "user-stories" / "story-1-example.md"
    story.write_text(
        "# Story 1: Example\n\n## Context for Agents\n\n"
        "- **Business rules:** [First rule, Second rule]\n", encoding="utf-8")
    return story


def spill_files(state_dir: Path) -> set:
    return set(state_dir.glob("story-context-spill-*")) if state_dir.is_dir() else set()


def load_eval_leanness():
    spec = importlib.util.spec_from_file_location(
        "eval_leanness_harness_cuts", REPO_ROOT / "scripts" / "eval-leanness.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OldLeanVariableIsIgnoredTest(unittest.TestCase):
    """AC-2.2, AC-2.4: a maintainer who still exports the old lean variable
    sees no change. The scripts produce the same output as without it."""

    def setUp(self):
        self.real_state = REPO_ROOT / ".writ" / "state"
        self.state_before = spill_files(self.real_state)

    def tearDown(self):
        # Remove any spill file a failing run wrote into the real repo, so
        # the failure does not leave the tree dirty.
        for leaked in spill_files(self.real_state) - self.state_before:
            leaked.unlink()

    def assemble(self, story: Path, env: dict, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "story-context.py"), "assemble",
             "--story", str(story), "--budget-bytes", "120", *extra],
            capture_output=True, text=True, env=env)

    def test_ac_2_2_story_context_over_budget_ignores_the_variable_and_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            story = over_budget_story(Path(tmp))
            state_dir = Path(tmp) / "state"
            plain = self.assemble(story, env_without_old_variable())
            exported = self.assemble(story, env_with_old_variable())
            with_dir = self.assemble(story, env_with_old_variable(), "--state-dir", str(state_dir))

            for proc in (plain, exported, with_dir):
                self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(with_dir.stdout)
            self.assertEqual(sorted(payload), ["bytes", "fetched_context", "truncated", "warnings"])
            self.assertTrue(payload["truncated"])
            self.assertEqual(payload["bytes"]["total"], 120)
            self.assertEqual(exported.stdout, plain.stdout)
            self.assertEqual(with_dir.stdout, plain.stdout)
            self.assertFalse(state_dir.exists(), "story-context.py wrote under --state-dir")
            self.assertEqual(spill_files(self.real_state) - self.state_before, set(),
                             "story-context.py wrote a spill file under .writ/state/")

    def test_ac_2_4_measure_invocation_report_ignores_the_variable(self):
        script = str(REPO_ROOT / "scripts" / "measure-invocation.py")
        argv = [sys.executable, script, "--root", str(REPO_ROOT)]
        plain = subprocess.run(argv, capture_output=True, text=True, env=env_without_old_variable())
        exported = subprocess.run(argv, capture_output=True, text=True, env=env_with_old_variable())
        self.assertEqual(plain.returncode, 0, plain.stderr)
        self.assertEqual(exported.returncode, 0, exported.stderr)
        report = json.loads(exported.stdout)
        self.assertNotIn("harness_lean", report)
        sourced = sorted(name for name, row in report["commands"].items() if "source" in row)
        self.assertEqual(sourced, [], "per-command source key present for: %s" % ", ".join(sourced))
        self.assertEqual(exported.stdout, plain.stdout)


class EveryCommandFileIsACommandTest(unittest.TestCase):
    """AC-2.4: `eval-leanness.py` and `eval.sh` `check_manifest` count a
    `commands/<stem>.lean.md` beside `commands/<stem>.md` as a command like
    any other file."""

    def test_ac_2_4_eval_leanness_counts_a_lean_named_file_as_a_command(self):
        leanness = load_eval_leanness()
        with tempfile.TemporaryDirectory() as tmp:
            commands = Path(tmp) / "commands"
            commands.mkdir()
            for name in ("x.md", "x.lean.md"):
                (commands / name).write_text("# %s\n" % name, encoding="utf-8")
            files = [Path(p).name for p in leanness.all_command_files(tmp)]
            metrics, _ = leanness.compute_metrics(tmp)
        self.assertEqual(files, ["x.lean.md", "x.md"])
        self.assertEqual(metrics["commands"], 2)

    def test_ac_2_4_check_manifest_reports_an_unlisted_lean_named_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("scripts", "commands", "agents", ".writ/state"):
                (root / rel).mkdir(parents=True)
            shutil.copy(REPO_ROOT / "scripts" / "eval.sh", root / "scripts" / "eval.sh")
            for name in ("listed", "listed.lean"):
                (root / "commands" / ("%s.md" % name)).write_text(
                    '---\nname: %s\ndescription: "d"\n---\n\n## Overview\n' % name, encoding="utf-8")
            (root / ".writ" / "manifest.yaml").write_text(
                "commands:\n  - name: listed\n    file: commands/listed.md\nagents:\n", encoding="utf-8")
            subprocess.run(["bash", "scripts/eval.sh", "--check=manifest", "--report=eval-report.md"],
                           cwd=str(root), capture_output=True, text=True)
            report_path = root / "eval-report.md"
            self.assertTrue(report_path.is_file(), "eval.sh wrote no report")
            report = report_path.read_text(encoding="utf-8")
        self.assertIn("`commands/listed.lean.md`: command file exists but is not listed", report)
        self.assertNotIn("`commands/listed.md`: command file exists but is not listed", report)


class ShipFilterDropsLeanDecisionTest(unittest.TestCase):
    """AC-2.5: the dev-only arm no longer names `lean-decision.py`, the three
    ship filters stay byte-identical, and no doc or test still names it."""

    def filter_body(self, rel: str) -> str:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        match = re.search(r"^is_shippable_script\(\) \{\n.*?^\}$", text, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "%s has no is_shippable_script" % rel)
        return match.group(0)

    def test_ac_2_5_ship_filters_are_identical_and_do_not_name_lean_decision(self):
        bodies = {rel: self.filter_body(rel) for rel in SHIP_FILTER_SCRIPTS}
        naming = [rel for rel, body in bodies.items() if DECISION_SCRIPT in body]
        self.assertEqual(naming, [], "dev-only arm still names %s in: %s"
                         % (DECISION_SCRIPT, ", ".join(naming)))
        self.assertEqual(len(set(bodies.values())), 1, "is_shippable_script bodies differ")

    def test_ac_2_5_docs_do_not_name_lean_decision(self):
        naming = [rel for rel in DOCS_NAMING_DEV_ONLY
                  if DECISION_SCRIPT in (REPO_ROOT / rel).read_text(encoding="utf-8")]
        self.assertEqual(naming, [], "%s still named in: %s" % (DECISION_SCRIPT, ", ".join(naming)))

    def test_ac_2_5_dev_scripts_test_keeps_prune_ledger_as_the_modified_fixture(self):
        text = (REPO_ROOT / DEV_SCRIPTS_TEST).read_text(encoding="utf-8")
        self.assertFalse(DECISION_SCRIPT in text, "%s still names %s" % (DEV_SCRIPTS_TEST, DECISION_SCRIPT))
        self.assertTrue("locally modified \u2014 kept): scripts/prune-ledger.py" in text,
                        "%s does not warn on a kept prune-ledger.py" % DEV_SCRIPTS_TEST)


if __name__ == "__main__":
    unittest.main()
