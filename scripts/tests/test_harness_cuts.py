#!/usr/bin/env python3
"""Guard tests for Story 1 of `2026-10-20-harness-cuts`.

The lean command siblings and the install/update logic that skipped them are
gone. These tests fail if any of it comes back:

- no `commands/*.lean.md` file exists;
- the guard grep from spec.md Business Rule 2 finds nothing in the paths
  Story 1 cleans (Story 2 widens the path list to the whole repo);
- neither `scripts/install.sh` nor `scripts/update.sh` defines or calls
  `is_unshipped_lean_sibling`;
- the lean-only tests are gone, and no mixed test or eval check that used to
  read a lean file still names one.

Each test cites the acceptance criterion it covers (AC-1.1, AC-1.5).
"""

from __future__ import annotations

import re
import subprocess
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
)

# The paths Story 1 of 2026-10-20-harness-cuts cleans.
STORY1_PATHS = (
    "commands",
    "README.md",
    "scripts/install.sh",
    "scripts/update.sh",
    ".writ/docs",
    ".writ/issues",
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
    """AC-1.1: the lean siblings no longer exist and nothing in the Story 1
    paths names them."""

    def test_ac_1_1_no_lean_command_files(self):
        lean = sorted(p.name for p in (REPO_ROOT / "commands").glob("*.lean.md"))
        self.assertEqual(lean, [], "lean command files still exist: %s" % ", ".join(lean))

    def test_ac_1_1_guard_grep_is_empty_in_story1_paths(self):
        hits = guard_grep(STORY1_PATHS)
        self.assertEqual(hits, [], "lean references remain:\n" + "\n".join(hits))


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


if __name__ == "__main__":
    unittest.main()
