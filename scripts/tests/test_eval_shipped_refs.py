#!/usr/bin/env python3
"""Tests for `scripts/eval-shipped-refs.py` and eval.sh's `shipped-refs` check.

Spec `2026-10-20-shipped-command-hygiene`, Story 1. A shipped command must not
link to Writ's own development history: ADR files, archived specs, research
documents, or calibration records under `.writ/state/`. Runtime paths and
placeholders for the user's own files stay. The helper runs against temp roots
through `--root`; the eval-level test copies `eval.sh` and the helper into a
temp `scripts/` the way `test_review_panel.py` does.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "eval-shipped-refs.py"
EVAL_SH = REPO_ROOT / "scripts" / "eval.sh"
KINDS = ("archived-spec", "research", "adr", "calibration-state")

ADR_LINK = "See [ADR-017](../.writ/decision-records/adr-017-git-notes-audit-channel.md)."


def run_helper(root: Path) -> Tuple[int, List[List[str]]]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), "--root", str(root)],
        capture_output=True, text=True, check=False)
    rows = [line.split("\t") for line in proc.stdout.splitlines() if line]
    return proc.returncode, rows


def fails(rows: List[List[str]]) -> List[List[str]]:
    return [row for row in rows if row[0] == "FAIL"]


def make_root(tmp: str, lines: List[str], archived: Tuple[str, ...] = ()) -> Path:
    root = Path(tmp)
    (root / "commands").mkdir()
    (root / "commands" / "x.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name in archived:
        (root / ".writ" / "specs" / "archive" / name).mkdir(parents=True)
    return root


def load_helper_module():
    spec = importlib.util.spec_from_file_location("eval_shipped_refs", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HelperPositiveTests(unittest.TestCase):
    """AC-1.1: one FAIL line per internal reference, naming file:line, kind, token."""

    LINES = [
        "# x",
        "Rationale: [ADR-013](../.writ/decision-records/adr-013-recommended-autonomous-delivery.md).",
        "Boundary: [ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md).",
        "See .writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md for why.",
        "Technical spec: `.writ/specs/2026-07-18-logical-unit-revert/sub-specs/technical-spec.md`",
        "Research (`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`) found it.",
        '  calibrated_against: "Observed run: .writ/state/phase-execution-20260719-121255.json."',
    ]
    EXPECTED = [
        ("commands/x.md:2", "adr", "decision-records/adr-013-recommended-autonomous-delivery.md"),
        ("commands/x.md:3", "adr", "decision-records/adr-009-command-agent-skill-boundary.md"),
        ("commands/x.md:4", "archived-spec",
         ".writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria"),
        ("commands/x.md:5", "archived-spec", ".writ/specs/2026-07-18-logical-unit-revert"),
        ("commands/x.md:6", "research",
         ".writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md"),
        ("commands/x.md:7", "calibration-state",
         ".writ/state/phase-execution-20260719-121255.json"),
    ]

    def test_each_kind_fails_once_with_file_line_kind_and_token(self):
        with TemporaryDirectory() as tmp:
            root = make_root(tmp, self.LINES, archived=("2026-07-18-logical-unit-revert",))
            code, rows = run_helper(root)
        got = [(row[1], row[2]) for row in fails(rows)]
        want = [(f"shipped-refs:{where}", f"{kind}: {token}")
                for where, kind, token in self.EXPECTED]
        self.assertEqual(got, want)
        self.assertEqual(code, 1)
        self.assertNotIn(["PASS", "shipped-refs-tree"], rows)

    def test_old_spec_path_fires_only_when_the_folder_is_archived(self):
        line = "Technical spec: `.writ/specs/2026-07-18-logical-unit-revert/spec.md`"
        with TemporaryDirectory() as tmp:
            _, rows = run_helper(make_root(tmp, [line]))
        self.assertEqual(fails(rows), [])
        self.assertIn(["PASS", "shipped-refs-tree"], rows)

    def test_two_links_on_one_line_are_two_findings(self):
        line = ("[ADR-009](../.writ/decision-records/adr-009-command-agent-skill-boundary.md) "
                "and [ADR-014](../.writ/decision-records/adr-014-skill-lifecycle.md)")
        with TemporaryDirectory() as tmp:
            _, rows = run_helper(make_root(tmp, [line]))
        self.assertEqual([row[2] for row in fails(rows)], [
            "adr: decision-records/adr-009-command-agent-skill-boundary.md",
            "adr: decision-records/adr-014-skill-lifecycle.md",
        ])


class HelperNegativeTests(unittest.TestCase):
    """Spec 2026-10-20-shipped-command-hygiene, AC-1.2: runtime paths and
    placeholders produce no finding."""

    LINES = [
        "State lives in `.writ/state/` and is gitignored.",
        '  calibrated_against: "Recalibrate against .writ/state/phase-execution-*.json records."',
        '  calibrated_against: "scripts/phase-state.py cmd_classify; agents/coding-agent.md."',
        "Each spec lives in `.writ/specs/<name>/`.",
        "Archived specs move to `.writ/specs/archive/<name>/`.",
        "The sweep appends to `.writ/specs/archive/LEDGER.md`.",
        "Exclude `.writ/specs/archive/**` from indexing.",
        "**File path:** `.writ/research/[DATE]-[topic-name]-research.md`",
        "A file matching .writ/research/<YYYY-MM-DD>-<topic>-research.md exists.",
        "| `.writ/decision-records/adr-*.md` | Reference targets |",
        "Does .writ/decision-records/adr-{NN}-*.md exist?",
        "At minimum `ADR-000-product-posture.md` and `ADR-001-market-focus.md`.",
        "See [`.writ/docs/spec-lifecycle.md`](../.writ/docs/spec-lifecycle.md).",
        "- Spec: .writ/specs/2026-03-15-auth-system/spec.md",
        "Design principle (ADR-001): bare labels are not links.",
    ]

    def test_runtime_paths_produce_no_fail_and_the_tree_passes(self):
        with TemporaryDirectory() as tmp:
            # An unrelated archived spec, so the old-path rule has a folder to
            # look in and still does not fire on the example ID.
            root = make_root(tmp, self.LINES, archived=("2026-01-01-unrelated-spec",))
            code, rows = run_helper(root)
        self.assertEqual(fails(rows), [])
        self.assertIn(["PASS", "shipped-refs-tree"], rows)
        self.assertEqual(code, 0)

    def test_every_rule_self_test_prints_pass_before_the_tree_verdict(self):
        with TemporaryDirectory() as tmp:
            _, rows = run_helper(make_root(tmp, ["# clean"]))
        names = [row[1] for row in rows]
        self.assertEqual(names[:len(KINDS)], [f"shipped-refs-rule-{k}" for k in KINDS])
        self.assertEqual([row[0] for row in rows[:len(KINDS)]], ["PASS"] * len(KINDS))
        self.assertEqual(names[-1], "shipped-refs-tree")

    def test_other_directories_are_not_scanned(self):
        with TemporaryDirectory() as tmp:
            root = make_root(tmp, ["# clean"])
            (root / "agents").mkdir()
            (root / "agents" / "a.md").write_text(ADR_LINK + "\n", encoding="utf-8")
            _, rows = run_helper(root)
        self.assertEqual(fails(rows), [])
        self.assertIn(["PASS", "shipped-refs-tree"], rows)

    def test_preamble_is_a_shipped_command_and_is_scanned(self):
        """Business Rule 1: every commands/*.md, _preamble.md included."""
        with TemporaryDirectory() as tmp:
            root = make_root(tmp, ["# clean"])
            (root / "commands" / "_preamble.md").write_text(ADR_LINK + "\n", encoding="utf-8")
            _, rows = run_helper(root)
        self.assertEqual([row[1] for row in fails(rows)], ["shipped-refs:commands/_preamble.md:1"])

    def test_scanned_directories_live_in_one_constant(self):
        self.assertEqual(load_helper_module().SCANNED_DIRS, ("commands",))

    def test_missing_commands_directory_is_a_run_error_not_a_pass(self):
        with TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(HELPER), "--root", tmp],
                capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("PASS\tshipped-refs-tree", proc.stdout)
        self.assertIn("no shipped command files", proc.stderr)


class SelfTestTests(unittest.TestCase):
    """A rule regex that silently matches nothing must fail its self-test."""

    def test_a_dead_rule_fails_its_own_scenario(self):
        module = load_helper_module()
        never = re.compile(r"(?!)")
        for kind in KINDS:
            with self.subTest(kind=kind):
                saved = dict(module.PATTERNS)
                try:
                    for key in module.PATTERNS:
                        if key.startswith(kind):
                            module.PATTERNS[key] = never
                    results = {name: ok for name, ok, _ in module.self_test()}
                finally:
                    module.PATTERNS.clear()
                    module.PATTERNS.update(saved)
                self.assertFalse(results[f"shipped-refs-rule-{kind}"])
                others = [k for k in KINDS if k != kind]
                self.assertTrue(all(results[f"shipped-refs-rule-{k}"] for k in others))


def run_eval(root: Path) -> Tuple[int, str]:
    report = root / "report.md"
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "eval.sh"), "--check=shipped-refs",
         f"--report={report}"],
        capture_output=True, text=True, check=False)
    return proc.returncode, report.read_text(encoding="utf-8") if report.exists() else ""


class EvalMutationTests(unittest.TestCase):
    """Spec 2026-10-20-shipped-command-hygiene, AC-1.3: clean -> link added ->
    link removed -> helper missing."""

    CLEAN = [
        "# Example",
        "",
        "State lives in `.writ/state/`; specs in `.writ/specs/<name>/`.",
        "See [`.writ/docs/spec-lifecycle.md`](../.writ/docs/spec-lifecycle.md).",
    ]

    def test_check_passes_bites_recovers_and_errors_without_the_helper(self):
        with TemporaryDirectory() as tmp:
            root = make_root(tmp, self.CLEAN)
            (root / "scripts").mkdir()
            shutil.copy(EVAL_SH, root / "scripts" / "eval.sh")
            shutil.copy(HELPER, root / "scripts" / "eval-shipped-refs.py")
            command = root / "commands" / "x.md"
            clean = command.read_text(encoding="utf-8")

            code, report = run_eval(root)
            self.assertEqual(code, 0, report)

            command.write_text(clean + ADR_LINK + "\n", encoding="utf-8")
            code, report = run_eval(root)
            self.assertEqual(code, 1, report)
            line = len(self.CLEAN) + 1
            self.assertIn(f"shipped-refs:commands/x.md:{line}", report)
            self.assertIn("adr: decision-records/adr-017-git-notes-audit-channel.md", report)
            self.assertIn("Remove the link to Writ's development history.", report)

            command.write_text(clean, encoding="utf-8")
            code, report = run_eval(root)
            self.assertEqual(code, 0, report)

            (root / "scripts" / "eval-shipped-refs.py").unlink()
            code, report = run_eval(root)
            self.assertEqual(code, 2, report)
            self.assertIn("scripts/eval-shipped-refs.py", report)

    def test_shipped_refs_is_registered_right_after_referenced_paths(self):
        text = EVAL_SH.read_text(encoding="utf-8")
        block = text[text.index("CHECKS=(\n"):]
        block = block[:block.index("\n)\n")]
        names = [line.strip() for line in block.splitlines()[1:]]
        self.assertIn("shipped-refs", names)
        self.assertEqual(names[names.index("referenced-paths") + 1], "shipped-refs")


class RealTreeTests(unittest.TestCase):
    """Spec 2026-10-20-shipped-command-hygiene, AC-1.4: the shipped commands
    carry no internal reference."""

    def test_real_tree_is_clean(self):
        code, rows = run_helper(REPO_ROOT)
        self.assertEqual(fails(rows), [])
        self.assertIn(["PASS", "shipped-refs-tree"], rows)
        self.assertEqual(code, 0)


LOOP_BOUNDS = REPO_ROOT / "scripts" / "eval-loop-bounds.py"
# The five rewritten values: (command, unit).
REWRITTEN_UNITS = (
    ("implement-phase", "spec"),
    ("implement-spec", "story"),
    ("implement-story", "review_cycle"),
    ("implement-story", "testing_cycle"),
    ("refactor", "change"),
)
# A `.writ/state/` or `.writ/specs/archive/` path is allowed only as a glob.
INTERNAL_RECORD = re.compile(r"\.writ/(?:state|specs/archive)/[\w./*-]*")


def load_loop_bounds_module():
    spec = importlib.util.spec_from_file_location("eval_loop_bounds", LOOP_BOUNDS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calibrated_against(module, command: str, unit: str) -> str:
    """Read one unit's value with eval-loop-bounds.py's own frontmatter parser."""
    text = (REPO_ROOT / "commands" / f"{command}.md").read_text(encoding="utf-8")
    parsed, err = module.frontmatter(text)
    if err:
        raise AssertionError(f"commands/{command}.md: {err}")
    loop = parsed.get("loop")
    entries = ([loop] + list(loop.get("nested") or [])) if isinstance(loop, dict) else []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("unit") == unit:
            return str(entry.get("calibrated_against") or "")
    raise AssertionError(f"commands/{command}.md declares no loop unit {unit!r}")


class CalibrationValueTests(unittest.TestCase):
    """Spec 2026-10-20-shipped-command-hygiene, AC-1.5: the rewritten
    calibrated_against values cite shipped paths or `no recorded run`, name no
    Writ record except as a glob, and loop-bounds still passes."""

    def setUp(self):
        self.module = load_loop_bounds_module()

    def test_each_value_cites_a_shipped_path_or_no_recorded_run(self):
        for command, unit in REWRITTEN_UNITS:
            with self.subTest(command=command, unit=unit):
                value = calibrated_against(self.module, command, unit)
                self.assertTrue(
                    self.module.PATH_TOKEN.search(value)
                    or self.module.NO_RECORDED_RUN in value.lower(), value)

    def test_refactor_value_keeps_no_recorded_run(self):
        value = calibrated_against(self.module, "refactor", "change")
        self.assertIn("no recorded run", value.lower())

    def test_no_value_names_a_writ_record_except_as_a_glob(self):
        for command, unit in REWRITTEN_UNITS:
            with self.subTest(command=command, unit=unit):
                value = calibrated_against(self.module, command, unit)
                records = [m.group(0) for m in INTERNAL_RECORD.finditer(value)
                           if "*" not in m.group(0)]
                self.assertEqual(records, [], value)

    def test_loop_bounds_reports_no_fail_for_these_commands(self):
        proc = subprocess.run([sys.executable, str(LOOP_BOUNDS)], cwd=REPO_ROOT,
                              capture_output=True, text=True, check=False)
        rows = {line.split("\t")[1]: line.split("\t")[0]
                for line in proc.stdout.splitlines() if line.count("\t") >= 1}
        names = sorted({f"schema-{command}" for command, _ in REWRITTEN_UNITS}
                       | {"refactor-no-recorded-run-literal"})
        self.assertEqual({name: rows.get(name) for name in names},
                         {name: "PASS" for name in names}, proc.stdout)


if __name__ == "__main__":
    unittest.main()
