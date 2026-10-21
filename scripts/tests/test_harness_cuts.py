#!/usr/bin/env python3
"""Guard tests for Stories 1 to 4 of `2026-10-20-harness-cuts`.

The lean command siblings, the install/update logic that skipped them,
every lean code path in `scripts/`, and the ADR-025 no-op emit lines are
gone, and `/ship` says it opens a PR. These tests fail if any of it comes
back:

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
  `lean-decision.py`;
- `commands/` carries no `escalated(...)` no-op emit or its sink sentence,
  while both floor-tier sites keep escalate-once and `check_model_escalation`
  keeps their iteration pins;
- `commands/ship.md` says it opens a PR, did not grow, and the recorded
  overages of the files this story shrank fell.
- `recommend-state.py` and the recommended-delivery state doc are dev-only:
  drift-triage has no recommended-mode branch, shipped docs name the script
  only as dev-only, `SKILL.md` no longer says install manages the state doc,
  and the eval lifecycle scenarios assert absence, removal, and an untouched
  unlink symlink.

This file and `test_install_update_harness_cuts.sh` are excluded from the
guard grep, so only they may name the old variable and the lean suffix.

Each test cites the acceptance criterion it covers (AC-1.1, AC-1.5, AC-2.1,
AC-2.2, AC-2.4, AC-2.5, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-4.4, AC-4.5).
"""

from __future__ import annotations

import ast
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


# Story 3 of 2026-10-20-harness-cuts. ac-trace credits a test token to the
# spec folder named most recently above it, and EXCLUDED names other specs,
# so this line names this spec again before the Story 3 tokens.

CREATE_SPEC = "commands/create-spec.md"
IMPLEMENT_STORY = "commands/implement-story.md"
SHIP = "commands/ship.md"
GOVERNOR_TEST = "scripts/tests/test_governor_enforcement.py"

# The two greps AC-3.1 runs over commands/.
NOOP_GREPS = ("no-op until ADR-025", "The line has no sink today")

# spec.md Business Rule 5: both iteration sentences stay verbatim.
CREATE_SPEC_ITERATION = ("the floor attempt and its anchor re-run count as one attempt"
                         " \u2014 there is no second regeneration")
IMPLEMENT_STORY_ITERATION = ("the floor attempt and its anchor re-run count as one attempt"
                             " against `loop.max_iterations`")

# Wording that says /ship merges, compared in lower case.
MERGE_CLAIMS = ("merged pr", "branch to merged", "gets it merged")
OPENS_A_PR = re.compile(r"\ban open (?:PR|pull request)\b|\bopens (?:a|the) (?:PR|pull request)\b")

# ship.md frontmatter lines this story must not touch, as they read before it.
SHIP_KEPT_FRONTMATTER = (
    'problem: "The last mile from green branch to open PR is a manual chain \u2014 merge default,'
    ' split commits, write the body, push, open \u2014 and a skipped link yields a stale or'
    ' unreviewable PR."',
    'outcome: "The branch has the default branch merged into it and its commits grouped by'
    ' concern, and an open pull request states the change\'s spec, test and drift position."',
    'exit_criteria:\n'
    '  - "the current branch has an origin upstream and its local tip equals the pushed tip"\n'
    '  - "an open pull request exists whose head is the current branch and whose body carries'
    ' Summary, Changes, Spec Reference and Test Results sections"\n'
    '  - "the default branch tip is an ancestor of the branch tip, and the PR is marked draft'
    ' whenever tests failed or drift is unresolved"',
)

COMMAND_BYTE_BUDGET = 24960
SHIP_MAX_BYTES = 28990
# KNOWN_OVER_BUDGET before this story; each file sat exactly at its entry.
OVERAGE_BEFORE = {
    "commands/create-spec.md": 29304,
    "commands/implement-story.md": 12013,
    "commands/ship.md": 4030,
}
LEDGER_LINE = r"# 2026-10-20 \(2026-10-20-harness-cuts Story 3\): %d -> (\d+);"


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    """From the `start` heading up to, not including, the `end` heading."""
    i = text.index(start)
    return text[i:text.index(end, i)]


def step_2_6a() -> str:
    return section(read(CREATE_SPEC), "#### Step 2.6a: Validate Generated Stories", "#### Step 2.6b:")


def anchor_confirmation() -> str:
    gate0 = section(read(IMPLEMENT_STORY), "#### Gate 0: Architecture Check", "#### Gate 0.5:")
    lines = [line for line in gate0.splitlines()
             if line.startswith("**Anchor confirmation (ADR-024):**")]
    if len(lines) != 1:
        raise RuntimeError("Gate 0 has %d anchor confirmation paragraphs" % len(lines))
    return lines[0]


def ship_frontmatter_and_overview() -> tuple:
    text = read(SHIP)
    if not text.startswith("---\n"):
        raise RuntimeError("%s has no frontmatter" % SHIP)
    frontmatter = text[len("---\n"):text.index("\n---\n")]
    overview = section(text, "## Overview\n", "\n## ")
    return frontmatter, overview


def run_model_escalation(create_spec_text: str, implement_story_text: str) -> str:
    """Run `eval.sh --check=model-escalation` in a temp tree holding only the
    two command files, and return the report."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in ("scripts", "commands", "agents", ".writ/state"):
            (root / rel).mkdir(parents=True)
        shutil.copy(REPO_ROOT / "scripts" / "eval.sh", root / "scripts" / "eval.sh")
        (root / CREATE_SPEC).write_text(create_spec_text, encoding="utf-8")
        (root / IMPLEMENT_STORY).write_text(implement_story_text, encoding="utf-8")
        subprocess.run(["bash", "scripts/eval.sh", "--check=model-escalation",
                        "--report=eval-report.md"],
                       cwd=str(root), capture_output=True, text=True)
        report_path = root / "eval-report.md"
        if not report_path.is_file():
            raise RuntimeError("eval.sh wrote no report")
        return report_path.read_text(encoding="utf-8")


def findings_count(report: str) -> int:
    match = re.search(r"^- Findings: (\d+)$", report, re.MULTILINE)
    if match is None:
        raise RuntimeError("report has no Findings line:\n" + report)
    return int(match.group(1))


def known_over_budget() -> dict:
    tree = ast.parse(read(GOVERNOR_TEST))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "KNOWN_OVER_BUDGET"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("%s defines no KNOWN_OVER_BUDGET" % GOVERNOR_TEST)


class NoOpEmitLinesGoneTest(unittest.TestCase):
    """AC-3.1: no command tells an agent to print an `escalated(...)` line
    that nothing reads."""

    def test_ac_3_1_noop_greps_over_commands_print_nothing(self):
        for pattern in NOOP_GREPS:
            with self.subTest(pattern=pattern):
                proc = subprocess.run(["grep", "-rn", pattern, "commands"],
                                      cwd=REPO_ROOT, capture_output=True, text=True)
                self.assertIn(proc.returncode, (0, 1), proc.stderr)
                self.assertEqual(proc.stdout, "", "grep -rn %r commands printed:\n%s"
                                 % (pattern, proc.stdout))

    def test_ac_3_1_create_spec_step_2_6a_has_items_1_to_3_only(self):
        items = re.findall(r"^(\d+)\. ", step_2_6a(), re.MULTILINE)
        self.assertEqual(items, ["1", "2", "3"])

    def test_ac_3_1_gate0_anchor_confirmation_has_no_escalated_emit(self):
        paragraph = anchor_confirmation()
        self.assertNotIn("escalated(", paragraph)
        self.assertNotIn("On the re-run emit", paragraph)


class EscalateOnceUnchangedTest(unittest.TestCase):
    """AC-3.2: both floor-tier sites still re-run a failing floor result once
    at `anchor` and state the iteration accounting verbatim, and
    `check_model_escalation` pins exactly that, with no emit pin left."""

    def test_ac_3_2_create_spec_still_reruns_once_at_anchor(self):
        text = step_2_6a()
        self.assertIn("spawn one regeneration with the identical prompt at `anchor`", text)
        self.assertIn("re-check once", text)
        self.assertIn("A passing story is never regenerated.", text)
        self.assertIn("Escalation fires only on a *returned* file that fails the check", text)
        self.assertIn("Iteration accounting: " + CREATE_SPEC_ITERATION, text)

    def test_ac_3_2_implement_story_gate0_still_reruns_once_at_anchor(self):
        paragraph = anchor_confirmation()
        self.assertIn("re-run `architecture-check-agent` once at `anchor`", paragraph)
        self.assertIn("A floor PROCEED/CAUTION is never re-run", paragraph)
        self.assertIn("escalation fires only on a returned verdict", paragraph)
        self.assertIn("Iteration accounting: " + IMPLEMENT_STORY_ITERATION, paragraph)

    def test_ac_3_2_check_keeps_the_iteration_pins_and_drops_the_emit_pins(self):
        body = shell_function_body(read("scripts/eval.sh"), "check_model_escalation")
        self.assertIn("local create_spec_iteration_sentence='%s'" % CREATE_SPEC_ITERATION, body)
        self.assertIn("local implement_story_iteration_sentence='%s'" % IMPLEMENT_STORY_ITERATION, body)
        self.assertIn('require_literal "$create_spec" "$create_spec_iteration_sentence"', body)
        self.assertIn('require_literal "$implement_story" "$implement_story_iteration_sentence"', body)
        self.assertIn('forbid_literal "$create_spec" \'loop.max_iterations\'', body)
        for gone in ("noop_prefix", "missing_sink", "escalated(agent="):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, body)

    def test_ac_3_2_check_passes_on_the_sentences_without_an_emit_line(self):
        report = run_model_escalation("x\n%s\n" % CREATE_SPEC_ITERATION,
                                      "x\n%s\n" % IMPLEMENT_STORY_ITERATION)
        self.assertEqual(findings_count(report), 0, report)

    def test_ac_3_2_check_still_requires_each_iteration_sentence(self):
        for missing, create_spec, implement_story in (
                (CREATE_SPEC, "x\n", "x\n%s\n" % IMPLEMENT_STORY_ITERATION),
                (IMPLEMENT_STORY, "x\n%s\n" % CREATE_SPEC_ITERATION, "x\n")):
            with self.subTest(missing=missing):
                report = run_model_escalation(create_spec, implement_story)
                self.assertEqual(findings_count(report), 1, report)
                self.assertIn(missing, report)

    def test_ac_3_2_check_still_forbids_loop_max_iterations_in_create_spec(self):
        report = run_model_escalation(
            "x\n%s\nbounded by `loop.max_iterations`\n" % CREATE_SPEC_ITERATION,
            "x\n%s\n" % IMPLEMENT_STORY_ITERATION)
        self.assertEqual(findings_count(report), 1, report)
        self.assertIn(CREATE_SPEC, report)


class ShipSaysItOpensAPRTest(unittest.TestCase):
    """AC-3.3: `/ship` is described as opening a pull request, never as
    merging one, and its contract frontmatter is untouched."""

    def test_ac_3_3_description_and_overview_make_no_merge_claim(self):
        frontmatter, overview = ship_frontmatter_and_overview()
        description = re.search(r'^description: "(.*)"$', frontmatter, re.MULTILINE)
        self.assertIsNotNone(description, "ship.md has no description")
        for name, text in (("description", description.group(1)), ("Overview", overview)):
            for claim in MERGE_CLAIMS:
                with self.subTest(part=name, claim=claim):
                    self.assertNotIn(claim, text.lower())

    def test_ac_3_3_description_and_overview_say_it_opens_a_pr(self):
        frontmatter, overview = ship_frontmatter_and_overview()
        description = re.search(r'^description: "(.*)"$', frontmatter, re.MULTILINE).group(1)
        self.assertRegex(description, OPENS_A_PR)
        self.assertRegex(overview, OPENS_A_PR)

    def test_ac_3_3_problem_outcome_and_exit_criteria_are_unchanged(self):
        frontmatter, _ = ship_frontmatter_and_overview()
        lines = "\n" + frontmatter + "\n"
        for kept in SHIP_KEPT_FRONTMATTER:
            with self.subTest(key=kept.split(":", 1)[0]):
                self.assertIn("\n" + kept + "\n", lines)


class OverageLedgerFellTest(unittest.TestCase):
    """AC-3.4: ship.md did not grow, and the recorded overages of the files
    this story shrank equal their new overage, each with a dated line."""

    def size(self, rel: str) -> int:
        return len((REPO_ROOT / rel).read_bytes())

    def test_ac_3_4_ship_md_did_not_grow(self):
        self.assertLessEqual(self.size(SHIP), SHIP_MAX_BYTES)

    def test_ac_3_4_lowered_entries_equal_the_new_overage(self):
        recorded = known_over_budget()
        for rel in (CREATE_SPEC, IMPLEMENT_STORY):
            with self.subTest(file=rel):
                self.assertEqual(recorded[rel], self.size(rel) - COMMAND_BYTE_BUDGET)
                self.assertLess(recorded[rel], OVERAGE_BEFORE[rel])
        self.assertEqual(recorded[SHIP], self.size(SHIP) - COMMAND_BYTE_BUDGET)
        self.assertLessEqual(recorded[SHIP], OVERAGE_BEFORE[SHIP])

    def comments_above_entry(self, rel: str) -> str:
        """The comment lines directly above `rel`'s KNOWN_OVER_BUDGET entry."""
        lines = read(GOVERNOR_TEST).splitlines()
        entry = re.compile(r'^\s*"%s": \d+,$' % re.escape(rel))
        index = next(i for i, line in enumerate(lines) if entry.match(line))
        comments = []
        while index > 0 and lines[index - 1].lstrip().startswith("#"):
            index -= 1
            comments.insert(0, lines[index].strip())
        return "\n".join(comments)

    def test_ac_3_4_each_lowered_entry_has_a_dated_ledger_line(self):
        recorded = known_over_budget()
        lowered = [rel for rel in OVERAGE_BEFORE if recorded[rel] != OVERAGE_BEFORE[rel]]
        self.assertIn(CREATE_SPEC, lowered)
        self.assertIn(IMPLEMENT_STORY, lowered)
        for rel in lowered:
            with self.subTest(file=rel):
                match = re.search(LEDGER_LINE % OVERAGE_BEFORE[rel], self.comments_above_entry(rel))
                self.assertIsNotNone(match, "no dated ledger line above %s" % rel)
                self.assertLess(int(match.group(1)), OVERAGE_BEFORE[rel])


# Story 4 of 2026-10-20-harness-cuts: recommended-delivery staging is dev-only.
# The ship filters and install/update behavior are tested in
# test_install_update_harness_cuts.sh; these tests cover the prose and the
# eval check.

DRIFT_TRIAGE = "skills/drift-triage/SKILL.md"
AGENT_CLI_CONTRACT = ".writ/docs/agent-cli-contract.md"
AC_IDS_DOC = ".writ/docs/acceptance-criteria-ids.md"
UPDATE_WRIT = "commands/update-writ.md"
ROOT_SKILL = "SKILL.md"
GEN_SKILL = "scripts/gen-skill.sh"
STAGING_HELPER = "recommend-state.py"
STATE_DOC_NAME = "recommended-delivery-state-format.md"

SMALL_ROUTE_AMEND = ("Auto-amend **only** `spec-lite.md` and append **one unique `DEV-NNN`"
                     " entry** to `drift-log.md`.")
# Text the drift-triage skill carried only for recommended mode, lower case.
RECOMMENDED_BRANCH_TEXT = ("recommended mode", "sha-256", "recommend-state",
                           "recommend-spec-lite-review", "never batch")

# Lifecycle scenario names in check_recommended_spec_implementation, as the
# f-strings in its three-platform loop spell them.
LIFECYCLE_NOW = (
    "install-{platform}-dry-run-names-neither",
    "install-{platform}-omits-helper",
    "install-{platform}-omits-state-doc",
    "update-{platform}-dry-run-lists-stale",
    "update-{platform}-removes-helper",
    "update-{platform}-removes-state-doc",
    "unlink-{platform}-skips-helper",
)
LIFECYCLE_BEFORE = (
    "install-{platform}-dry-run-helper",
    "install-{platform}-dry-run-state-doc",
    "install-{platform}-helper-executable",
    "install-{platform}-state-doc",
    "update-{platform}-dry-run-helper",
    "update-{platform}-dry-run-state-doc",
    "update-{platform}-restores-helper",
    "update-{platform}-restores-state-doc",
    "unlink-{platform}-dry-run-helper",
    "unlink-{platform}-dry-run-state-doc",
    "unlink-{platform}-copies-helper",
    "unlink-{platform}-copies-state-doc",
)
# A sample of the reducer and static scenario names the check emitted before
# Story 4. The full before/after name comparison is in the story record.
REDUCER_SAMPLE = ("complete-package-validates", "append-only-log-advances",
                  "parallel-worktrees-reserved-adopted-integrated",
                  "operational-exception-is-blocked-json")
STATIC_SAMPLE = ("create-fail-before-mutation", "state-json-parses",
                 "worktree-state-identity")


def flat(text: str) -> str:
    """`text` with every run of whitespace collapsed to one space."""
    return " ".join(text.split())


def between(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


class DriftTriageHasNoRecommendedBranchTest(unittest.TestCase):
    """AC-4.4: the Small route amends spec-lite.md and logs one DEV entry,
    with no recommended-mode branch and no pre-edit SHA-256 capture."""

    def test_ac_4_4_small_route_amends_spec_lite_and_logs_one_entry(self):
        small = flat(between(read(DRIFT_TRIAGE), "### Small", "### Medium"))
        self.assertIn(SMALL_ROUTE_AMEND, small)
        self.assertIn("Continue **PASS**.", small)
        self.assertIn("**Always** include the spec-lite changes in the run summary.", small)

    def test_ac_4_4_skill_has_no_recommended_mode_text(self):
        text = read(DRIFT_TRIAGE).lower()
        found = [needle for needle in RECOMMENDED_BRANCH_TEXT if needle in text]
        self.assertEqual(found, [], "%s still carries: %s" % (DRIFT_TRIAGE, found))


class StagingIsNamedDevOnlyTest(unittest.TestCase):
    """AC-4.4: shipped docs name recommend-state.py only as a dev-only,
    source-repo script, and SKILL.md says the state doc is not installed."""

    def test_ac_4_4_agent_cli_contract_names_it_only_in_the_dev_only_note(self):
        lines = [line for line in read(AGENT_CLI_CONTRACT).splitlines() if STAGING_HELPER in line]
        self.assertEqual(len(lines), 1, "%s names %s outside the dev-only note: %s"
                         % (AGENT_CLI_CONTRACT, STAGING_HELPER, lines))
        self.assertTrue(lines[0].startswith("**Not in the table.**"), lines[0])
        self.assertIn("Six dev-only scripts", lines[0])
        self.assertIn("ADR-013", lines[0])

    def test_ac_4_4_acceptance_criteria_ids_names_a_dev_only_parser(self):
        text = read(AC_IDS_DOC)
        self.assertNotIn("scripts/" + STAGING_HELPER, text)
        why = flat(between(text, "### Why suffix, not prefix", "## The Tag Is End-Anchored"))
        self.assertIn(STAGING_HELPER, why)
        self.assertIn("dev-only", why)
        self.assertIn("not installed", why)
        self.assertIn("| `recommend-state.py:378` |", why)

    def test_ac_4_4_update_writ_step3_names_both_exclusions(self):
        text = read(UPDATE_WRIT)
        scripts = between(text, "**Apply same logic to runtime scripts**",
                          "**Apply same logic to Writ reference docs**")
        self.assertIn("`%s`" % STAGING_HELPER, scripts)
        docs = between(text, "**Apply same logic to Writ reference docs**",
                       "**Apply same logic to platform-specific files:**")
        self.assertIn("`%s`" % STATE_DOC_NAME, docs)
        stale = next(line for line in text.splitlines() if line.startswith("**Detect stale files:**"))
        self.assertIn("docs the docs filter excludes", stale)

    def test_ac_4_4_skill_md_says_the_state_doc_is_not_installed(self):
        for rel in (ROOT_SKILL, GEN_SKILL):
            with self.subTest(file=rel):
                section = flat(between(read(rel), "## Runtime Contract", "## Available Commands"))
                self.assertNotIn("manage this file", section)
                self.assertNotRegex(section, r"(?i)install, update, and unlink")
                self.assertIn("ADR-013", section)
                self.assertIn("not installed", section)

    def test_ac_4_4_gen_skill_check_passes(self):
        proc = subprocess.run(["bash", GEN_SKILL, "--check"], cwd=REPO_ROOT,
                              capture_output=True, text=True)
        self.assertEqual(proc.stdout.splitlines()[:1], ["pass"], proc.stdout + proc.stderr)
        self.assertEqual(proc.returncode, 0)


class EvalLifecycleScenariosInvertedTest(unittest.TestCase):
    """AC-4.5: check_recommended_spec_implementation keeps its reducer and
    static scenarios and its three-platform loop, and its lifecycle scenarios
    now assert absence on install, removal on update, and an untouched helper
    symlink on unlink. `bash scripts/eval.sh` runs them."""

    def body(self) -> str:
        # Its embedded Python has lines that are exactly `}`, so
        # shell_function_body would stop early; cut at the next function.
        return between(read("scripts/eval.sh"), "\ncheck_recommended_spec_implementation() {\n",
                       "\ncheck_recommended_staging() {\n")

    def test_ac_4_5_lifecycle_scenarios_run_on_three_platforms(self):
        body = self.body()
        self.assertTrue('for platform in ("cursor", "claude", "codex"):' in body,
                        "the lifecycle loop no longer covers cursor, claude, and codex")
        for name in LIFECYCLE_NOW:
            with self.subTest(scenario=name):
                self.assertTrue('f"%s"' % name in body, "no %s scenario" % name)

    def test_ac_4_5_shipping_scenarios_are_gone(self):
        body = self.body()
        for name in LIFECYCLE_BEFORE:
            with self.subTest(scenario=name):
                self.assertFalse('f"%s"' % name in body, "%s still emitted" % name)

    def test_ac_4_5_lifecycle_reads_each_platform_manifest(self):
        body = self.body()
        self.assertTrue('manifest = target / f".{platform}/.writ-manifest"' in body,
                        "the lifecycle scenarios do not read the platform manifest")
        self.assertFalse("helper_dest.unlink()" in body,
                         "the lifecycle scenarios still delete an installed helper")

    def test_ac_4_5_reducer_static_and_adversarial_scenarios_still_run(self):
        body = self.body()
        for name in REDUCER_SAMPLE + STATIC_SAMPLE:
            with self.subTest(scenario=name):
                self.assertTrue('"%s"' % name in body, "no %s scenario" % name)
        self.assertTrue("scripts/eval-recommend-state-adversarial.py" in body,
                        "the adversarial scenarios no longer run")
        staging = shell_function_body(read("scripts/eval.sh"), "check_recommended_staging")
        self.assertTrue("scripts/eval-recommend-stage.py" in staging,
                        "check_recommended_staging no longer runs eval-recommend-stage.py")
        checks = read("scripts/eval.sh")
        for name in ("recommended-spec-implementation", "recommended-staging"):
            self.assertRegex(checks, r"(?m)^  %s$" % re.escape(name))


if __name__ == "__main__":
    unittest.main()
