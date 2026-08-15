#!/usr/bin/env python3
"""Tests for 2026-08-12-governor-enforcement.

Four families, one per mechanism this spec lands:

  1. **The METRIC bridge (Story 1).** `scripts/eval.sh`'s `check_leanness()`
     TSV bridge printed a fixed METRIC set with no branch for
     `contract_compliance` or `required_skills_declarations`, so both reached
     the JSON and never the report a maintainer reads. The bridge's heredoc is
     extracted from the committed script and run directly, so these assert the
     shipped renderer rather than a copy of it.

  2. **The absolute per-invocation byte cap (Story 2).** Boundary, infra
     exclusion, error paths, severity-independence, non-silenceability by a
     justification, and agreement with `scripts/measure-invocation.py`'s
     accounting.

  3. **The compliance gate (Story 4).** Real-repo assertions, one per half of
     the deliverable: the contract half (flipped blocking) must be saturated
     and silent; the byte half (measured, non-blocking) must not acquire a
     violator that was not already recorded.

  4. **`MAX_SKILLS`, the record, and inline-read resolution (Story 7).**

`eval-leanness.py` has a hyphen in its filename, so it is loaded by path via
`importlib.util.spec_from_file_location` — the recipe already used by
`test_eval_leanness_contract.py` and friends.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "eval-leanness.py"
EVAL_SH = REPO_ROOT / "scripts" / "eval.sh"
MEASURE_PATH = REPO_ROOT / "scripts" / "measure-invocation.py"

_spec = importlib.util.spec_from_file_location("eval_leanness_ge", MODULE_PATH)
assert _spec is not None and _spec.loader is not None
lean = importlib.util.module_from_spec(_spec)
sys.modules["eval_leanness_ge"] = lean
_spec.loader.exec_module(lean)


def load_measure():
    spec = importlib.util.spec_from_file_location("measure_invocation_ge", MEASURE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def function_code(name: str) -> str:
    """A function's executable source, with its docstring and comments stripped.

    These assertions are about what the CODE consults, not about what the prose
    around it is allowed to mention. A check whose docstring explains why it
    ignores justifications must not fail a test looking for the word.
    """
    source = MODULE_PATH.read_text(encoding="utf-8")
    _, _, tail = source.partition(f"def {name}(")
    body = tail.split("\ndef ", 1)[0]
    body = re.sub(r'"""(?:.|\n)*?"""', "", body)
    return "\n".join(line.split("#", 1)[0] for line in body.split("\n"))


def write_command(root: Path, name: str, body: str) -> Path:
    path = root / "commands" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def sized_command(byte_total: int) -> str:
    """A command body of exactly `byte_total` bytes (ASCII throughout)."""
    head = "---\nname: x\nproblem: \"p\"\noutcome: \"o\"\nexit_criteria:\n  - \"c\"\n---\n\n# X\n\n## Completion\n\n"
    assert len(head) <= byte_total, "requested size is smaller than the fixture header"
    return head + "x" * (byte_total - len(head))


# ---------------------------------------------------------------------------
# Story 1 — the METRIC bridge
# ---------------------------------------------------------------------------

class MetricBridgeTests(unittest.TestCase):
    """The bridge is extracted from the committed eval.sh, never re-typed.

    A copy of the renderer would pass while the shipped one stayed broken,
    which is the defect class this whole spec is about.
    """

    @classmethod
    def setUpClass(cls):
        source = EVAL_SH.read_text(encoding="utf-8")
        _, marker, tail = source.partition('python3 - "$json" > "$tsv" <<\'PY\'\n')
        assert marker, "the check_leanness TSV bridge heredoc moved or was renamed"
        cls.bridge = tail.split("\nPY\n", 1)[0]

    def render(self, payload: dict) -> list[str]:
        with TemporaryDirectory() as tmp:
            script = Path(tmp) / "bridge.py"
            script.write_text(self.bridge, encoding="utf-8")
            data = Path(tmp) / "data.json"
            data.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(script), str(data)],
                                    capture_output=True, text=True, check=True)
        return [line for line in result.stdout.split("\n") if line]

    def metric_lines(self, payload: dict) -> list[str]:
        return [line.split("\t", 1)[1] for line in self.render(payload)
                if line.startswith("METRIC\t")]

    def test_contract_compliance_reaches_the_report(self):
        lines = self.metric_lines({"metrics": {"contract_compliance": {
            "commands_checked": 31, "commands_with_contract": 31,
            "commands_with_completion": 31, "loop_commands_checked": 5,
            "loop_commands_bounded": 5, "agents_checked": 7,
            "agents_with_contract": 7}}})
        rendered = [line for line in lines if line.startswith("contract_compliance:")]
        self.assertEqual(len(rendered), 1, lines)
        for key in ("commands_checked=31", "commands_with_contract=31",
                    "commands_with_completion=31", "loop_commands_checked=5",
                    "loop_commands_bounded=5", "agents_checked=7",
                    "agents_with_contract=7"):
            self.assertIn(key, rendered[0])

    def test_required_skills_declarations_reaches_the_report_at_zero(self):
        lines = self.metric_lines({"metrics": {"required_skills_declarations": 0}})
        rendered = [line for line in lines
                    if line.startswith("required_skills_declarations=")]
        self.assertEqual(len(rendered), 1, lines)
        self.assertTrue(rendered[0].startswith("required_skills_declarations=0"),
                        "a permanent 0 is exactly the value the vacuous-pass "
                        "guard exists to publish")

    def test_inline_skill_reads_reaches_the_report(self):
        lines = self.metric_lines({"metrics": {"inline_skill_reads": 17}})
        self.assertEqual([line for line in lines
                          if line.startswith("inline_skill_reads=")][0].split(" ")[0],
                         "inline_skill_reads=17")

    def test_command_budget_names_every_over_budget_command(self):
        lines = self.metric_lines({"metrics": {"command_budget": {
            "budget": 24960, "checked": 31, "total_overage": 21463,
            "over_budget": [{"subject": "commands/create-spec.md",
                             "bytes": 46423, "over_by": 21463}]}}})
        rendered = [line for line in lines if line.startswith("command_budget:")][0]
        self.assertIn("budget=24960", rendered)
        self.assertIn("over_budget=1", rendered)
        self.assertIn("commands/create-spec.md +21463", rendered)

    def test_absent_keys_print_nothing_never_none(self):
        """A mismatched or older eval-leanness.py must not print `: None`."""
        lines = self.metric_lines({"metrics": {"commands": 3}})
        # The legacy first line is byte-frozen and has always rendered absent
        # aggregate keys as None; that behavior is not this story's to change.
        # Every line Story 1 adds must simply not exist.
        new_lines = lines[1:]
        joined = "\n".join(new_lines)
        for key in ("contract_compliance", "required_skills_declarations",
                    "inline_skill_reads", "command_budget",
                    "per_command_invocation"):
            self.assertNotIn(key, joined)
        self.assertNotIn("None", joined)

    def test_no_new_metric_line_carries_a_tab_or_newline(self):
        """`while IFS=$'\\t' read -r kind a b c` splits on tabs: a value with a
        tab in it silently shifts every field after it."""
        payload = {"metrics": {
            "contract_compliance": {"commands_checked": 31},
            "required_skills_declarations": 0,
            "inline_skill_reads": 17,
            "command_budget": {"budget": 24960, "checked": 31, "total_overage": 0,
                               "over_budget": []},
            "per_command_invocation": {"alpha": {"command_bytes": 1,
                                                 "floor_bytes": 2,
                                                 "ceiling_bytes": 3}},
        }}
        for line in self.render(payload):
            self.assertEqual(line.count("\t"), 1,
                             f"a METRIC line must carry exactly one tab: {line!r}")

    def test_the_legacy_first_metric_line_is_byte_identical_to_its_shipped_form(self):
        """Its own comment names the Tier B consumers that read only the first
        METRIC line. Story 1 adds branches; it does not restructure."""
        legacy = ('print("METRIC\\tcommands=%s agents=%s skills=%s '
                  'command_lines=%s command_chars=%s" % (\n'
                  '    m.get("commands"), m.get("agents"), m.get("skills"), '
                  'm.get("command_lines"), m.get("command_chars")))')
        self.assertIn(legacy, self.bridge)
        first = [line for line in self.metric_lines({"metrics": {
            "commands": 32, "agents": 7, "skills": 14,
            "command_lines": 1, "command_chars": 2,
            "contract_compliance": {"commands_checked": 31}}})][0]
        self.assertEqual(
            first, "commands=32 agents=7 skills=14 command_lines=1 command_chars=2")


# ---------------------------------------------------------------------------
# Story 2 — the absolute per-invocation byte cap
# ---------------------------------------------------------------------------

class CommandBudgetTests(unittest.TestCase):

    def test_the_budget_is_pinned_with_its_derivation_recorded(self):
        self.assertEqual(lean.COMMAND_BYTE_BUDGET, 24960)
        self.assertIn("system-instructions.md", lean.COMMAND_BYTE_BUDGET_DERIVED)
        self.assertIn("commands/_preamble.md", lean.COMMAND_BYTE_BUDGET_DERIVED)
        self.assertIn("2026-08-12", lean.COMMAND_BYTE_BUDGET_DERIVED)

    def test_one_byte_over_emits_one_finding(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "fat", sized_command(lean.COMMAND_BYTE_BUDGET + 1))
            findings = lean.check_command_budget(tmp)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["subject"], "commands/fat.md")
            self.assertIn(str(lean.COMMAND_BYTE_BUDGET + 1), findings[0]["what"])
            self.assertIn(str(lean.COMMAND_BYTE_BUDGET), findings[0]["what"])
            self.assertIn("by 1", findings[0]["what"])

    def test_exactly_at_budget_is_compliant(self):
        """`>` not `>=`, asserted rather than left to a reading of the code."""
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "edge", sized_command(lean.COMMAND_BYTE_BUDGET))
            self.assertEqual(lean.check_command_budget(tmp), [])

    def test_one_byte_under_budget_is_compliant(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "edge", sized_command(lean.COMMAND_BYTE_BUDGET - 1))
            self.assertEqual(lean.check_command_budget(tmp), [])

    def test_plan_product_the_tightest_near_miss_on_the_real_surface(self):
        """207 bytes of headroom on 2026-08-12. A false positive against a
        compliant file is the fastest way to teach a maintainer the gate is
        arbitrary, so it is asserted by name."""
        path = REPO_ROOT / "commands" / "plan-product.md"
        self.assertTrue(path.is_file())
        self.assertLessEqual(len(path.read_bytes()), lean.COMMAND_BYTE_BUDGET)
        subjects = {f["subject"] for f in lean.check_command_budget(str(REPO_ROOT))}
        self.assertNotIn("commands/plan-product.md", subjects)

    def test_infra_is_excluded_by_the_existing_rule_not_by_a_hardcoded_name(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "_preamble",
                          sized_command(lean.COMMAND_BYTE_BUDGET + 5000))
            self.assertEqual(lean.check_command_budget(tmp), [])
        body = function_code("check_command_budget")
        self.assertNotIn("_preamble", body,
                         "infra exclusion must reuse is_infra(), never a filename")
        self.assertIn("is_infra", body)

    def test_absent_commands_directory_yields_no_findings(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(lean.check_command_budget(tmp), [])

    def test_zero_byte_command_is_under_budget_with_no_division(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "empty", "")
            self.assertEqual(lean.check_command_budget(tmp), [])

    def test_unreadable_command_emits_a_naming_finding_and_never_raises(self):
        with TemporaryDirectory() as tmp:
            path = write_command(Path(tmp), "locked", sized_command(200))
            os.chmod(path, 0o000)
            try:
                findings = lean.check_command_budget(tmp)
            finally:
                os.chmod(path, 0o644)
            if os.geteuid() == 0:  # root ignores the mode; nothing to assert
                self.skipTest("running as root: an unreadable file cannot be staged")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["subject"], "commands/locked.md")
            self.assertIn("could not be read", findings[0]["what"])

    def test_the_finding_names_file_bytes_budget_overage_and_the_adr_remedy(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "fat", sized_command(30000))
            finding = lean.check_command_budget(tmp)[0]
            self.assertEqual(finding["subject"], "commands/fat.md")
            self.assertIn("30000 bytes", finding["what"])
            self.assertIn("24960", finding["what"])
            self.assertIn("5040", finding["what"])
            self.assertIn("ADR-021", finding["fix"])
            for prescription in ("add an exemption", "eval-exempt",
                                 "raise the budget"):
                self.assertNotIn(prescription, finding["fix"].lower(),
                                 "the remedy is extraction, never a silencer")

    def test_the_cap_never_reads_the_severity_constant_or_a_baseline(self):
        """Severity-independence, asserted across all three values of the seam
        plus a direct source read: the budget is not the flip's to disable."""
        shipped = lean.CONTRACT_CHECK_SEVERITY
        self.addCleanup(setattr, lean, "CONTRACT_CHECK_SEVERITY", shipped)
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "fat", sized_command(30000))
            baseline = [lean.check_command_budget(tmp)]
            for value in ("warnings", "structural", "blocking-typo"):
                lean.CONTRACT_CHECK_SEVERITY = value
                baseline.append(lean.check_command_budget(tmp))
            for produced in baseline[1:]:
                self.assertEqual(produced, baseline[0])
        body = function_code("check_command_budget")
        for forbidden in ("CONTRACT_CHECK_SEVERITY", "emit_contract_findings",
                          "justification", "baseline", ".writ"):
            self.assertNotIn(forbidden, body,
                             f"check_command_budget must not consult {forbidden}")

    def test_eval_leanness_has_no_exemption_reader_at_all(self):
        """Non-silenceability is structural, not documentary (Business Rule 1).

        The literal is allowed in prose that explains the absence; what may not
        exist is code that greps for it.
        """
        source = MODULE_PATH.read_text(encoding="utf-8")
        code = "\n".join(line.split("#", 1)[0] for line in source.split("\n"))
        self.assertNotIn("eval-exempt", code)
        self.assertNotIn("file_has_exemption", code)

    def test_a_bound_justification_cannot_quiet_the_cap(self):
        """A justification explains growth against a BASELINE. It has no
        meaning against an ABSOLUTE budget (Business Rule 3)."""
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "fat", sized_command(30000))
            clean = lean.check_command_budget(tmp)
            baseline_dir = Path(tmp) / ".writ"
            baseline_dir.mkdir(parents=True, exist_ok=True)
            (baseline_dir / "leanness-baseline.json").write_text(json.dumps({
                "recorded": "2026-08-12", "schema": 3,
                "surfaces": {"commands": {
                    "lines": 1, "chars": 1,
                    "justifications": {"chars": {"value": 10 ** 9,
                                                 "date": "2026-08-12",
                                                 "text": "planted to silence the cap"}}}},
            }), encoding="utf-8")
            self.assertEqual(lean.check_command_budget(tmp), clean)
            self.assertEqual(len(clean), 1)

    def test_command_bytes_agrees_with_measure_invocation_on_the_real_repo(self):
        """One accounting, two readers. Two implementations of "how big is this
        command" that can disagree is a defect waiting for its first file."""
        result = subprocess.run(
            [sys.executable, str(MEASURE_PATH), "--root", str(REPO_ROOT),
             "--format", "json"], capture_output=True, text=True, check=True)
        reported = json.loads(result.stdout)["commands"]
        mine = lean.command_byte_sizes(str(REPO_ROOT))
        self.assertGreater(len(mine), 0)
        for name, entry in reported.items():
            self.assertEqual(mine[name], entry["command_bytes"], name)
        self.assertEqual(set(mine), set(reported))

    def test_base_drift_is_reported_non_blocking_and_never_moves_the_budget(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "system-instructions.md").write_text("x" * 100,
                                                             encoding="utf-8")
            write_command(Path(tmp), "_preamble", "y" * 100)
            findings = lean.check_budget_derivation(tmp)
            self.assertEqual(len(findings), 1)
            self.assertIn("24960", findings[0]["what"])
            self.assertIn("200", findings[0]["what"])
            self.assertIn("unchanged", findings[0]["fix"].lower() + findings[0]["what"].lower())
            self.assertEqual(lean.COMMAND_BYTE_BUDGET, 24960)

    def test_a_base_that_still_equals_the_budget_is_silent(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "system-instructions.md").write_text(
                "x" * 20153, encoding="utf-8")
            write_command(Path(tmp), "_preamble", "y" * 4807)
            self.assertEqual(lean.check_budget_derivation(tmp), [])

    def test_the_cap_lands_in_warnings_and_main_still_exits_zero(self):
        """The 2026-08-12 (d) rescope: five commands stay over budget and
        nobody is converting them, so the cap ships MEASURED and NON-BLOCKING.
        A permanently-red gate is invisible — the exact failure ADR-021 reason
        2 diagnoses and this spec exists to prevent.
        """
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "fat", sized_command(30000))
            for surface in ("skills", "adapters", "scripts", "agents"):
                (Path(tmp) / surface).mkdir(parents=True, exist_ok=True)
            (Path(tmp) / "system-instructions.md").write_text("# S\n", encoding="utf-8")
            (Path(tmp) / "README.md").write_text(
                "# Demo\n\n## Commands\n\n| Command | Purpose |\n|---|---|\n"
                "| `/fat` | fixture |\n", encoding="utf-8")
            baseline_path = Path(tmp) / ".writ" / "leanness-baseline.json"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                lean.main(["--root", tmp, "--baseline", str(baseline_path),
                           "--update-baseline"])
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = lean.main(["--root", tmp, "--baseline", str(baseline_path)])
            payload = json.loads(out.getvalue())
        self.assertEqual(rc, 0)
        subjects = {f["subject"] for f in payload["warnings"]}
        self.assertIn("commands/fat.md", subjects)
        self.assertNotIn("commands/fat.md",
                         {f["subject"] for f in payload["structural"]})
        budget = payload["metrics"]["command_budget"]
        self.assertEqual(budget["budget"], 24960)
        self.assertEqual([entry["subject"] for entry in budget["over_budget"]],
                         ["commands/fat.md"])
        self.assertEqual(budget["over_budget"][0]["over_by"], 30000 - 24960)
        self.assertIn("fat", payload["metrics"]["per_command_invocation"])


# ---------------------------------------------------------------------------
# Story 4 — the compliance gate, one half at a time
# ---------------------------------------------------------------------------

# The byte half of the deliverable does NOT comply and is not being converted:
# the five sibling disclosure specs were closed unimplemented after the pilot
# measured ~1,017 bytes of overhead per extracted skill and a +9.7% worst-path
# regression (spec.md -> Approved Scope Changes, 2026-08-12 (d)). These five
# are therefore the RECORDED violators. The gate is a one-way ratchet over
# them: a new name, or a larger overage on a recorded one, fails. Shrinking is
# free, and a file leaving the list never fails a build.
#
# Updated 2026-08-13 (v0.31.0 dogfooding): three deliberate, disclosed
# increases, none silencing this gate — each is a real overage acknowledged
# here, not exempted from eval.sh's own leanness warning (which separately
# still reports each as non-blocking). implement-phase.md 4176 -> 11090 and
# implement-story.md (NEW, 735) both came from the machine-evaluable-exit-
# criteria and recalibrate-implement-loop specs (v0.31.0). release.md 3629 ->
# 7167 came from the same release's roadmap-sync Step 3.1b addition. This
# test caught all three only because it was run by hand -- it is not wired
# into eval.sh or CI today, unlike the leanness WARNING it parallels.
#
# Updated 2026-08-13 (acceptance-criteria-traceability-ids, Story 1):
# create-spec.md 21463 -> 24036, a disclosed increase from Step 2.6's
# criterion-ID-grammar note, the Step 2.4 note deferring ID tags on
# spec-lite.md's Review-agent bullets, and the new Step 2.6b that appends
# those tags once story files exist.
#
# Updated 2026-08-13 (acceptance-criteria-traceability-ids, Story 3):
# verify-spec.md 7150 -> 10298, a disclosed increase from wiring Check 3e
# (criterion coverage) and Check 3f (dangling/malformed references) into
# Check 3 Completion Integrity, plus the auto-fix-boundary and status-rollup
# prose that names them. Sub-checks of Check 3, not a ninth top-level check
# — the eight-row check table promise is unchanged (see check_ac_trace in
# scripts/eval.sh, which asserts the row count directly).
#
# Updated 2026-08-14 (script-backed-quality-gates, Story 5):
# implement-story.md 735 -> 2730, a disclosed increase from wiring the two
# script-backed checks into gates that already existed. Gate 2 gains the
# build-smoke step; Gate 4 gains the coverage/authenticity re-derivation whose
# verdict overrides the testing agent's self-reported "Coverage threshold met"
# field. Both blocks also state the unverifiable-is-not-DEGRADED rule
# explicitly, which is the bulk of the prose and is deliberate: conflating the
# two either floods DEGRADED until it stops meaning anything or hides real gate
# failures. This is the cheaper of the two available edits by construction --
# inserting Gate 2.6 and Gate 4.6 instead would have cost five literal-pinned
# rows in eval.sh, eval-leanness.py's GATE_AGENT_FILES, the gate->verdict table
# in skills/subagent-result-completeness/SKILL.md, an ASCII diagram in
# agents/visual-qa-agent.md, and a --quick policy decision, for two checks that
# are the missing halves of existing stages rather than new ones. Acknowledged
# here, not exempted: eval.sh's leanness warning still reports the overage.
KNOWN_OVER_BUDGET = {
    "commands/create-spec.md": 24036,
    "commands/verify-spec.md": 10298,
    "commands/implement-phase.md": 11090,
    "commands/release.md": 7167,
    "commands/ship.md": 3411,
    "commands/implement-story.md": 2730,
}


class ComplianceGateTests(unittest.TestCase):
    """Against the REAL repo, not a fixture. Committed, so it keeps guarding.

    "We checked before flipping" is a hope. This is the gate, and it stays in
    the suite after the flip as the regression guard for the state the flip
    depends on.
    """

    def setUp(self):
        self._shipped = lean.CONTRACT_CHECK_SEVERITY
        self.addCleanup(setattr, lean, "CONTRACT_CHECK_SEVERITY", self._shipped)

    def run_main(self) -> dict:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = lean.main(["--root", str(REPO_ROOT), "--baseline",
                            str(REPO_ROOT / ".writ" / "leanness-baseline.json")])
        self.assertEqual(rc, 0)
        return json.loads(out.getvalue())

    def test_the_tree_is_measurable_at_all(self):
        """`all_command_files()` on an absent commands/ returns [], and "every
        element of an empty list is under budget" is True. A gate that passes
        vacuously would green-light a flip against a tree nobody measured."""
        commands = lean.all_command_files(str(REPO_ROOT))
        self.assertGreater(len(commands), 0, "commands/ is absent or unreadable")
        self.assertGreater(len(lean.all_agent_files(str(REPO_ROOT))), 0)

    def test_no_command_acquires_a_new_or_larger_budget_violation(self):
        sizes = lean.command_byte_sizes(str(REPO_ROOT))
        self.assertGreater(len(sizes), 0)
        over = {f"commands/{name}.md": size - lean.COMMAND_BYTE_BUDGET
                for name, size in sizes.items()
                if size > lean.COMMAND_BYTE_BUDGET}
        regressions = []
        for subject, overage in sorted(over.items()):
            recorded = KNOWN_OVER_BUDGET.get(subject)
            if recorded is None:
                regressions.append(
                    f"{subject}: NEW violator, {sizes[Path(subject).stem]} bytes, "
                    f"{overage} over the {lean.COMMAND_BYTE_BUDGET}-byte budget")
            elif overage > recorded:
                regressions.append(
                    f"{subject}: grew past its recorded overage — {overage} over, "
                    f"was {recorded}")
        self.assertEqual(regressions, [], "\n".join(regressions))

    def test_the_four_contract_checks_are_silent_on_the_real_tree(self):
        """The precondition the flip rests on, measured at its source.

        Read from the check functions themselves rather than from a bucket, so
        the assertion cannot be satisfied by a routing change: whatever
        CONTRACT_CHECK_SEVERITY says, these four lists must be empty.
        """
        root = str(REPO_ROOT)
        offenders = (lean.check_component_contract(root)
                     + lean.check_completion_sections(root)
                     + lean.check_loop_bounds(root))
        self.assertEqual([f["subject"] for f in offenders], [])
        skill_findings = lean.check_required_skills(root)[0]
        self.assertEqual([f["subject"] for f in skill_findings], [])

    def test_structural_is_empty_under_the_shipped_severity_and_a_structural_pin(self):
        """The load-bearing assertion, and the one that makes this a gate.

        Asserting `structural: []` under a `"warnings"` pin proves nothing
        about the post-flip world — the contract findings would sit in
        `warnings` either way. Pinning `"structural"` in-process and asserting
        the list is STILL empty is what proves the flip is safe. Both pins are
        run, and the shipped constant is restored by addCleanup so a failure
        cannot leak a flipped module into a later test in the same process.
        """
        for severity in (self._shipped, "structural", "warnings"):
            lean.CONTRACT_CHECK_SEVERITY = severity
            payload = self.run_main()
            blocking = [f["subject"] for f in payload["structural"]]
            self.assertEqual(blocking, [], f"under {severity!r}: {blocking}")

    def test_the_byte_cap_is_the_half_that_does_not_comply_and_is_not_blocking(self):
        """The other half of the same precondition, gated on its own evidence.

        Five commands are over budget and the specs that owned them were closed
        unimplemented, so the cap is reported rather than blocking. Landing it
        blocking would make every run red for files with no owner — the exact
        ADR-021 reason 2 failure this spec exists to prevent. Business Rule 1's
        "no exemption to make the flip possible" is upheld by not flipping this
        half, never by silencing it, so the finding must still be PRESENT.
        """
        self.assertEqual(lean.COMMAND_BUDGET_SEVERITY, "warnings")
        payload = self.run_main()
        reported = {f["subject"] for f in payload["warnings"]}
        blocking = {f["subject"] for f in payload["structural"]}
        for subject in KNOWN_OVER_BUDGET:
            self.assertIn(subject, reported,
                          "an over-budget command must still be named — the cap "
                          "is non-blocking, not silent")
            self.assertNotIn(subject, blocking)
        budget = payload["metrics"]["command_budget"]
        self.assertEqual({entry["subject"] for entry in budget["over_budget"]},
                         set(KNOWN_OVER_BUDGET))
        self.assertEqual(budget["total_overage"], sum(KNOWN_OVER_BUDGET.values()))

    def test_contract_compliance_is_saturated_on_all_four_pairs(self):
        compliance = self.run_main()["metrics"]["contract_compliance"]
        unsaturated = [
            f"{have}={compliance[have]} of {total}={compliance[total]}"
            for have, total in (
                ("commands_with_contract", "commands_checked"),
                ("commands_with_completion", "commands_checked"),
                ("loop_commands_bounded", "loop_commands_checked"),
                ("agents_with_contract", "agents_checked"))
            if compliance[have] != compliance[total]
        ]
        self.assertEqual(unsaturated, [], "; ".join(unsaturated))
        self.assertGreater(compliance["commands_checked"], 0)
        self.assertGreater(compliance["agents_checked"], 0)

    def test_no_command_or_agent_declares_required_skills(self):
        """A declaration is an EAGER pre-load: it moves skill bytes into the
        floor, where every invocation pays them, WITHOUT changing any command's
        own byte count — so the budget assertion structurally cannot see it.
        Cross-checked by a direct grep so a future parse_skill_names() change
        cannot turn a green assertion into a vacuous one.
        """
        self.assertEqual(self.run_main()["metrics"]["required_skills_declarations"], 0)
        declared = []
        for path in (lean.all_command_files(str(REPO_ROOT))
                     + lean.all_agent_files(str(REPO_ROOT))):
            text = Path(path).read_text(encoding="utf-8")
            for match in re.finditer(r"^required_skills:(.*)$", text, re.M):
                declared.append(f"{Path(path).name} -> required_skills:{match.group(1)}")
        self.assertEqual(declared, [], "; ".join(declared))


# ---------------------------------------------------------------------------
# Story 7 — MAX_SKILLS, inline-read resolution, and the mechanism record
# ---------------------------------------------------------------------------

class MaxSkillsDerivationTests(unittest.TestCase):

    def test_max_skills_is_the_derivation_not_the_roster(self):
        self.assertEqual(lean.MAX_SKILLS, lean.MAX_COMMANDS + lean.MAX_AGENTS)
        self.assertEqual(lean.MAX_SKILLS, 45)

    def test_the_derivation_is_recorded_at_the_constant(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        head, marker, _ = source.partition("\nMAX_SKILLS = ")
        self.assertTrue(marker)
        preamble = head[-3600:]
        for token in ("MAX_COMMANDS + MAX_AGENTS", "2026-08-12", "warn-only",
                      "governor-enforcement"):
            self.assertIn(token, preamble,
                          f"the MAX_SKILLS derivation comment must name {token}")

    def test_the_cap_can_still_fire(self):
        """A cap that clears its content by construction has no state in which
        it speaks — ADR-021 reason 1 rebuilt in the skills surface."""
        warnings = lean.check_ceilings({"commands": 1, "agents": 1,
                                        "skills": lean.MAX_SKILLS + 1})
        self.assertEqual([w["subject"] for w in warnings], ["skills"])
        self.assertIn(str(lean.MAX_SKILLS), warnings[0]["what"])

    def test_the_real_roster_is_under_the_cap_with_headroom(self):
        metrics, _ = lean.compute_metrics(str(REPO_ROOT))
        self.assertLessEqual(metrics["skills"], lean.MAX_SKILLS)
        self.assertEqual(lean.check_ceilings(metrics), [])

    def test_max_skills_stays_warn_only(self):
        body = function_code("check_ceilings")
        self.assertIn("warnings", body)
        self.assertNotIn("structural", body)

    def test_the_sibling_ceilings_did_not_move(self):
        self.assertEqual((lean.MAX_COMMANDS, lean.MAX_AGENTS), (35, 10))


class InlineSkillReadTests(unittest.TestCase):
    """The phase's real loading mechanism, which had no resolution check.

    `check_required_skills()` resolved `required_skills:` frontmatter only, and
    the phase retired that field in favour of inline reads. A mistyped
    `Read skills/tdd-cyle/SKILL.md` was a silent no-op: the gate passed, the
    skill never loaded, and the command quietly lost a capability.
    """

    def _skill(self, tmp: str, name: str) -> None:
        path = Path(tmp) / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"name: {name}\n", encoding="utf-8")

    def test_a_resolving_inline_read_is_counted_and_silent(self):
        with TemporaryDirectory() as tmp:
            self._skill(tmp, "tdd-cycle")
            write_command(Path(tmp), "alpha",
                          "# Alpha\n\nRead skills/tdd-cycle/SKILL.md\n")
            findings, declarations, inline = lean.check_required_skills(tmp)
            self.assertEqual(findings, [])
            self.assertEqual(declarations, 0)
            self.assertEqual(inline, 1)

    def test_a_mistyped_inline_read_emits_one_finding_naming_file_and_skill(self):
        with TemporaryDirectory() as tmp:
            self._skill(tmp, "tdd-cycle")
            write_command(Path(tmp), "alpha",
                          "# Alpha\n\nRead skills/tdd-cyle/SKILL.md\n")
            findings, _, inline = lean.check_required_skills(tmp)
            self.assertEqual([f["subject"] for f in findings],
                             ["commands/alpha.md → Read skills/tdd-cyle/SKILL.md"])
            self.assertIn("tdd-cyle", findings[0]["what"])
            self.assertIn("silent no-op", findings[0]["what"])
            self.assertEqual(inline, 1)

    def test_agent_bodies_are_resolved_identically(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "agents" / "coder.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Coder\n\nRead skills/ghost/SKILL.md\n", encoding="utf-8")
            findings, _, inline = lean.check_required_skills(tmp)
            self.assertEqual([f["subject"] for f in findings],
                             ["agents/coder.md → Read skills/ghost/SKILL.md"])
            self.assertEqual(inline, 1)

    def test_a_documentation_placeholder_is_never_resolved(self):
        """`commands/new-skill.md` teaches the form with a literal
        `<name>` placeholder. Flagging it would be a false finding against the
        one command whose job is to document the convention."""
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "new-skill",
                          "# New skill\n\n      Read skills/<name>/SKILL.md\n")
            findings, _, inline = lean.check_required_skills(tmp)
            self.assertEqual(findings, [])
            self.assertEqual(inline, 0)

    def test_repeats_of_one_name_in_one_file_count_once(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha",
                          "Read skills/ghost/SKILL.md\nRead skills/ghost/SKILL.md\n")
            findings, _, inline = lean.check_required_skills(tmp)
            self.assertEqual(len(findings), 1)
            self.assertEqual(inline, 1)

    def test_the_pattern_matches_measure_invocation_byte_for_byte(self):
        """One accounting, two readers — the same rule Story 2 applies to
        command_bytes, applied to the inline-read parser."""
        measure = load_measure()
        self.assertEqual(lean.INLINE_SKILL_READ.pattern, measure.INLINE_READ.pattern)

    def test_the_real_repo_resolves_every_inline_read(self):
        findings, declarations, inline = lean.check_required_skills(str(REPO_ROOT))
        self.assertEqual(findings, [], f"unresolvable inline reads: {findings}")
        self.assertEqual(declarations, 0)
        self.assertGreater(inline, 0,
                           "the phase's loading mechanism must be visible to the check")

    def test_inline_findings_stay_non_blocking_after_the_flip(self):
        """system-instructions.md's graceful-degradation contract: an unknown
        skill name warns at load time, never hard-fails. The pin outlives the
        flip, and it must cover the mechanism the phase actually uses."""
        shipped = lean.CONTRACT_CHECK_SEVERITY
        self.addCleanup(setattr, lean, "CONTRACT_CHECK_SEVERITY", shipped)
        lean.CONTRACT_CHECK_SEVERITY = "structural"
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", "Read skills/ghost/SKILL.md\n")
            findings, _, _ = lean.check_required_skills(tmp)
            structural: list[dict] = []
            warnings: list[dict] = []
            lean.emit_contract_findings(findings, structural, warnings,
                                        severity="warnings")
            self.assertEqual(structural, [])
            self.assertEqual(len(warnings), 1)


class MechanismRecordTests(unittest.TestCase):
    """The false first-consumer claim lived in four files, not one."""

    CLAIM_FILES = (
        "system-instructions.md",
        "adapters/cursor.md",
        "adapters/claude-code.md",
        "adapters/openclaw.md",
    )

    def test_no_file_still_names_phase_10_as_the_first_consumer(self):
        offenders = []
        for rel in self.CLAIM_FILES:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            for line_no, line in enumerate(text.split("\n"), 1):
                if "first consumer" in line and "progressive disclosure" in line:
                    offenders.append(f"{rel}:{line_no}")
        self.assertEqual(offenders, [], "; ".join(offenders))

    def test_every_file_records_the_convention_has_no_consumer(self):
        for rel in self.CLAIM_FILES:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("no consumer", text, rel)
            self.assertIn("2026-11-11", text, f"{rel} must carry the review trigger")

    def test_the_schema_and_the_graceful_degradation_rule_are_unchanged(self):
        text = (REPO_ROOT / "system-instructions.md").read_text(encoding="utf-8")
        for clause in (
            "`required_skills` is an **optional** array of strings.",
            "Order is **preserved** — downstream tooling may use it for load priority.",
            "Duplicates are **silently deduplicated**.",
            "Unknown skill names produce a **warning** at consumer load time, "
            "not a hard failure",
        ):
            self.assertIn(clause, text)

    def test_the_adapters_keep_their_accurate_description_of_the_mechanism(self):
        """Only the trailing consumer sentence was false. The harness genuinely
        does pre-load declared skills before the consumer's first phase — that
        fact is what the escalation rested on and it must survive."""
        for rel in ("adapters/cursor.md", "adapters/claude-code.md",
                    "adapters/openclaw.md"):
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("required_skills:", text, rel)
            self.assertIn("before", text, rel)


if __name__ == "__main__":
    unittest.main()
