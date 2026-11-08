#!/usr/bin/env python3
"""Unit tests for scripts/verdict-provenance.py `check` (Story 4 of
2026-09-07-phase11-stage2-prune-the-base).

Each test writes a fixture command file — frontmatter with a `gates:` list and
a body with `#### Gate N` headings — into a temp repo, runs `check` against
it, and asserts on the finding lines, the `prose_only_count` note-vs-finding
split, and the exit code. The module filename contains a hyphen, so it is
imported by path (the `test_pipeline_baseline.py` recipe). The last test
runs `check` against the real `commands/implement-story.md` (AC-4.1).

Updated 2026-11-06 (spec 2026-11-06-lean-story-pipeline, Story 1): every
fixture entry now carries `catches:`, `evidence:`, and `kill_when:`, and
`GateEvidenceFieldTests` covers the four new finding codes (`missing_catches`,
`missing_evidence`, `missing_kill_when`, `unknown_path_value`) and the
optional `path:` key [AC-1.1, AC-1.2, AC-1.3].
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

MODULE_PATH = Path(__file__).resolve().parent.parent / "verdict-provenance.py"
_spec = importlib.util.spec_from_file_location("verdict_provenance", MODULE_PATH)
vp = importlib.util.module_from_spec(_spec)
sys.modules["verdict_provenance"] = vp
_spec.loader.exec_module(vp)  # type: ignore[union-attr]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ALL_IDS = (
    "gate0_arch", "gate0_5_boundary", "gate1_coding", "gate2_build",
    "gate2_5_surface", "gate3_review", "gate3_5_drift", "gate4_tests",
    "gate4_5_behavior", "gate5_docs",
)
HEADINGS = (
    "#### Gate 0: Architecture Check (Pre-Implementation)",
    "#### Gate 0.5: Boundary Computation (File Ownership Map)",
    "#### Gate 1: Coding Agent (TDD Implementation)",
    "#### Gate 2: Lint, Typecheck, Format & Build Smoke",
    "#### Gate 2.5: Change Surface Classification",
    "#### Gate 3: Review Agent",
    "#### Gate 3.5: Drift Response Handling & \"What Was Built\" Extraction",
    "#### Gate 4: Testing Agent (with Coverage Enforcement)",
    "#### Gate 4.5: Behavioral Verification",
    "#### Gate 5: Documentation Agent",
)
SCRIPTS = {"gate2_build": "scripts/build-smoke.py", "gate4_tests": "scripts/test-integrity.py"}


# The three fields every entry must declare (spec Business Rule 1). The
# values hold `:`, `==`, `.`, and `;` so every fixture also proves the line
# parser reads them as plain scalars.
EVIDENCE_FIELDS = {
    "catches": '"A broken build reaches review; cost: a red main branch"',
    "evidence": '"Phase 15 retro (2026-10-30) F26: one catch"',
    "kill_when": '"sole_catches == 0 over 20 default-path records"',
}


def entry_lines(gate_id: str, script: Optional[str] = None,
                verification: Optional[str] = None,
                omit: Tuple[str, ...] = (), path: Optional[str] = None) -> List[str]:
    lines = ["  - id: %s" % gate_id]
    if script is not None:
        lines.append("    script: %s" % script)
    if verification is not None:
        lines.append("    verification: %s" % verification)
    if path is not None:
        lines.append("    path: %s" % path)
    for key, value in EVIDENCE_FIELDS.items():
        if key not in omit:
            lines.append("    %s: %s" % (key, value))
    return lines


def complete_entries() -> List[str]:
    out: List[str] = []
    for gate_id in ALL_IDS:
        if gate_id in SCRIPTS:
            out.extend(entry_lines(gate_id, script=SCRIPTS[gate_id]))
        else:
            out.extend(entry_lines(gate_id, verification="prose-only"))
    return out


def command_text(entries: List[str], headings: Tuple[str, ...] = HEADINGS,
                 gates_key: bool = True) -> str:
    fm = ["---", "name: implement-story", 'description: "fixture"',
          "exit_criteria:", '  - "one criterion"']
    if gates_key:
        fm.append("gates:")
        fm.extend(entries)
    fm.extend(["loop:", "  unit: review_cycle", "  max_iterations: 3", "---", ""])
    body = ["# Fixture", "", "## Overview", "", "### Step 3: Run Pipeline", ""]
    for h in headings:
        body.extend([h, "", "Some prose.", ""])
    return "\n".join(fm + body)


class Fixture:
    """A temp repo holding commands/implement-story.md plus the two real script paths."""

    def __init__(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "scripts").mkdir()
        for rel in SCRIPTS.values():
            (self.root / rel).write_text("# stub\n", encoding="utf-8")
        (self.root / "commands").mkdir()
        self.command = self.root / "commands" / "implement-story.md"

    def write(self, text: str) -> None:
        self.command.write_text(text, encoding="utf-8")

    def cleanup(self) -> None:
        self._tmp.cleanup()


def run_check(fx: Fixture, *extra: str) -> Tuple[int, str, str]:
    argv = ["check", "--command", str(fx.command), "--repo", str(fx.root)] + list(extra)
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            vp.main(argv)
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, out.getvalue(), err.getvalue()


def finding_lines(stdout: str) -> List[str]:
    """Every line between the verdict line and the trailing summary that is not a note."""
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    return [ln for ln in lines[1:-1] if not ln.startswith("note:")]


class ParserTests(unittest.TestCase):
    def test_heading_table_is_the_fixed_ten(self) -> None:
        self.assertEqual(tuple(vp.HEADING_TO_ID.values()), ALL_IDS)
        self.assertEqual(vp.HEADING_TO_ID["0.5"], "gate0_5_boundary")
        self.assertEqual(vp.HEADING_TO_ID["4.5"], "gate4_5_behavior")

    def test_default_prose_only_cap_is_one(self) -> None:
        """AC-4.3 (2026-10-01-behavioral-verification): Gate 4.5 left prose-only."""
        self.assertEqual(vp.DEFAULT_MAX_PROSE_ONLY, 1)

    def test_ids_shared_with_pipeline_baseline_gate_names(self) -> None:
        for shared in ("gate0_arch", "gate2_build", "gate3_review", "gate4_tests", "gate5_docs"):
            self.assertIn(shared, vp.HEADING_TO_ID.values())

    def test_parse_gates_reads_id_script_verification(self) -> None:
        text = command_text(complete_entries())
        gates = vp.parse_gates(text)
        self.assertEqual([g["id"] for g in gates], list(ALL_IDS))
        by_id = {g["id"]: g for g in gates}
        self.assertEqual(by_id["gate2_build"].get("script"), "scripts/build-smoke.py")
        self.assertNotIn("verification", by_id["gate2_build"])
        self.assertEqual(by_id["gate0_arch"].get("verification"), "prose-only")

    def test_parse_gates_strips_quotes(self) -> None:
        text = command_text(['  - id: "gate0_arch"', "    verification: 'prose-only'"])
        self.assertEqual(vp.parse_gates(text), [{"id": "gate0_arch", "verification": "prose-only"}])

    def test_parse_gates_reads_evidence_fields_as_plain_scalars(self) -> None:
        """Quoted values holding `:`, `==`, `.` and `;` keep every character."""
        text = command_text(entry_lines("gate2_build", script="scripts/build-smoke.py",
                                        path="full-pipeline"))
        gate = vp.parse_gates(text)[0]
        self.assertEqual(gate["path"], "full-pipeline")
        self.assertEqual(gate["catches"], "A broken build reaches review; cost: a red main branch")
        self.assertEqual(gate["evidence"], "Phase 15 retro (2026-10-30) F26: one catch")
        self.assertEqual(gate["kill_when"], "sole_catches == 0 over 20 default-path records")

    def test_parse_gates_absent_key_is_empty(self) -> None:
        self.assertEqual(vp.parse_gates(command_text([], gates_key=False)), [])

    def test_parse_headings_maps_to_ids(self) -> None:
        self.assertEqual(vp.parse_headings(command_text([])), list(ALL_IDS))

    def test_parse_headings_ignores_frontmatter_and_other_levels(self) -> None:
        text = command_text([], headings=("### Gate 1: Not a gate heading", "#### Gate 3: Review Agent"))
        self.assertEqual(vp.parse_headings(text), ["gate3_review"])


class CheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    # AC-4.1 shape: complete block
    def test_complete_block_exits_zero_with_note(self) -> None:
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 0, out)
        self.assertEqual(finding_lines(out), [])
        self.assertIn("note: prose_only_count: 8 (cap 1)", out)

    # AC-4.2
    def test_heading_without_entry(self) -> None:
        entries = [ln for ln in complete_entries()]
        # drop gate2_5_surface's whole entry: id, source, and the three evidence fields
        idx = entries.index("  - id: gate2_5_surface")
        del entries[idx:idx + 5]
        self.fx.write(command_text(entries))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("heading_without_entry:")]
        self.assertEqual(len(found), 1, out)
        self.assertIn("gate2_5_surface", found[0])
        self.assertIn("implement-story.md", found[0])

    def test_entry_without_heading(self) -> None:
        headings = tuple(h for h in HEADINGS if not h.startswith("#### Gate 3.5"))
        self.fx.write(command_text(complete_entries(), headings=headings))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("entry_without_heading:")]
        self.assertEqual(len(found), 1, out)
        self.assertIn("gate3_5_drift", found[0])
        self.assertIn("implement-story.md", found[0])

    def test_entry_without_source(self) -> None:
        entries = complete_entries()
        idx = entries.index("  - id: gate1_coding")
        del entries[idx + 1]
        self.fx.write(command_text(entries))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("entry_without_source:")]
        self.assertEqual(len(found), 1, out)
        self.assertIn("gate1_coding", found[0])
        self.assertIn("implement-story.md", found[0])

    def test_entry_both_sources(self) -> None:
        entries = complete_entries()
        idx = entries.index("  - id: gate2_build")
        entries.insert(idx + 2, "    verification: prose-only")
        self.fx.write(command_text(entries))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("entry_both_sources:")]
        self.assertEqual(len(found), 1, out)
        self.assertIn("gate2_build", found[0])
        self.assertIn("implement-story.md", found[0])

    def test_script_missing_relative_to_repo(self) -> None:
        entries = complete_entries()
        idx = entries.index("    script: scripts/test-integrity.py")
        entries[idx] = "    script: scripts/does-not-exist.py"
        self.fx.write(command_text(entries))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("script_missing:")]
        self.assertEqual(len(found), 1, out)
        self.assertIn("gate4_tests", found[0])
        self.assertIn("scripts/does-not-exist.py", found[0])
        self.assertIn("implement-story.md", found[0])

    def test_script_resolves_against_repo_not_cwd(self) -> None:
        # The stub scripts exist only under the fixture root; --repo must be
        # what resolves them, not the process cwd (the Writ repo).
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 0, out)
        argv = ["check", "--command", str(self.fx.command), "--repo", str(self.fx.root / "commands")]
        out2 = io.StringIO()
        with contextlib.redirect_stdout(out2), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                vp.main(argv)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(out2.getvalue().count("script_missing:"), 2)

    def test_unknown_verification_value(self) -> None:
        entries = complete_entries()
        idx = entries.index("  - id: gate5_docs")
        entries[idx + 1] = "    verification: manual"
        self.fx.write(command_text(entries))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("unknown_verification_value:")]
        self.assertEqual(len(found), 1, out)
        self.assertIn("gate5_docs", found[0])
        self.assertIn("manual", found[0])
        self.assertIn("implement-story.md", found[0])

    def test_one_finding_per_drift_and_summary_last(self) -> None:
        entries = complete_entries()
        idx = entries.index("  - id: gate5_docs")
        entries[idx + 1] = "    verification: manual"
        headings = tuple(h for h in HEADINGS if not h.startswith("#### Gate 0.5"))
        self.fx.write(command_text(entries, headings=headings))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        codes = sorted(ln.split(":")[0] for ln in finding_lines(out))
        self.assertEqual(codes, ["entry_without_heading", "unknown_verification_value"])
        self.assertEqual(out.splitlines()[0], "fail", out)
        self.assertTrue(out.splitlines()[-1].startswith("verdict-provenance: fail (gates: "),
                        out)

    def test_clean_run_prints_pass_first_and_summary_last(self) -> None:
        """Agent CLI contract (check shape): verdict alone on line 1, summary last."""
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertEqual(lines[0], "pass", out)
        self.assertEqual(lines[1], "note: prose_only_count: 8 (cap 1)", out)
        self.assertRegex(lines[-1], r"^verdict-provenance: pass \(gates: \d+ entries, "
                                    r"headings: \d+, script: \d+, prose-only: 8, findings: 0\)$")
        self.assertEqual(len(lines), 3, out)

    # AC-4.3
    def test_prose_only_over_cap_is_note_by_default(self) -> None:
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 0, out)
        self.assertIn("note: prose_only_count: 8 (cap 1)", out)
        self.assertEqual(finding_lines(out), [])

    def test_prose_only_over_cap_is_finding_when_blocking(self) -> None:
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx, "--prose-only-blocking")
        self.assertEqual(code, 1, out)
        self.assertNotIn("note: prose_only_count", out)
        self.assertEqual(finding_lines(out), ["prose_only_count: 8 (cap 1)"])

    def test_prose_only_at_or_under_cap_is_never_a_finding(self) -> None:
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx, "--prose-only-blocking", "--max-prose-only", "8")
        self.assertEqual(code, 0, out)
        self.assertIn("note: prose_only_count: 8 (cap 8)", out)

    def test_max_prose_only_changes_cap_in_line(self) -> None:
        self.fx.write(command_text(complete_entries()))
        code, out, _ = run_check(self.fx, "--max-prose-only", "5")
        self.assertEqual(code, 0, out)
        self.assertIn("note: prose_only_count: 8 (cap 5)", out)

    # exit 2
    def test_missing_command_file_is_exit_2(self) -> None:
        code, out, err = run_check(self.fx)
        self.assertEqual(code, 2)
        self.assertIn("check: error:", err)

    def test_missing_frontmatter_is_exit_2(self) -> None:
        self.fx.write("# No frontmatter\n\n#### Gate 0: X\n")
        code, out, err = run_check(self.fx)
        self.assertEqual(code, 2)
        self.assertIn("frontmatter", err)

    def test_entry_without_id_is_exit_2(self) -> None:
        self.fx.write(command_text(["  - script: scripts/build-smoke.py"], headings=()))
        code, out, err = run_check(self.fx)
        self.assertEqual(code, 2)
        self.assertIn("id", err)

    def test_no_gates_key_reports_every_heading(self) -> None:
        self.fx.write(command_text([], gates_key=False))
        code, out, _ = run_check(self.fx)
        self.assertEqual(code, 1, out)
        found = [ln for ln in finding_lines(out) if ln.startswith("heading_without_entry:")]
        self.assertEqual(len(found), 10, out)


class GateEvidenceFieldTests(unittest.TestCase):
    """2026-11-06-lean-story-pipeline Story 1: catches / evidence / kill_when / path."""

    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def _entries_with(self, gate_id: str, **kwargs: object) -> List[str]:
        out: List[str] = []
        for gid in ALL_IDS:
            source = {"script": SCRIPTS[gid]} if gid in SCRIPTS else {"verification": "prose-only"}
            extra = kwargs if gid == gate_id else {}
            out.extend(entry_lines(gid, **source, **extra))  # type: ignore[arg-type]
        return out

    def _single_finding(self, entries: List[str], code: str, gate_id: str) -> str:
        self.fx.write(command_text(entries))
        rc, out, _ = run_check(self.fx)
        self.assertEqual(rc, 1, out)
        self.assertEqual(out.splitlines()[0], "fail", out)
        findings = finding_lines(out)
        self.assertEqual(len(findings), 1, out)
        self.assertTrue(findings[0].startswith(code + ":"), out)
        self.assertIn(gate_id, findings[0])
        self.assertIn("implement-story.md", findings[0])
        return findings[0]

    def test_finding_codes_extend_the_existing_six(self) -> None:
        """AC-1.3: existing codes keep their names and order; four are appended."""
        self.assertEqual(vp.FINDING_CODES[:6], (
            "heading_without_entry", "entry_without_heading", "entry_without_source",
            "entry_both_sources", "script_missing", "unknown_verification_value"))
        self.assertEqual(vp.FINDING_CODES[6:], (
            "missing_catches", "missing_evidence", "missing_kill_when", "unknown_path_value"))
        self.assertEqual(vp.PATH_VALUES, ("default", "full-pipeline"))

    # AC-1.1
    def test_missing_catches(self) -> None:
        line = self._single_finding(self._entries_with("gate2_build", omit=("catches",)),
                                    "missing_catches", "gate2_build")
        self.assertIn("catches", line)

    def test_missing_evidence(self) -> None:
        line = self._single_finding(self._entries_with("gate1_coding", omit=("evidence",)),
                                    "missing_evidence", "gate1_coding")
        self.assertIn("evidence", line)

    def test_missing_kill_when(self) -> None:
        line = self._single_finding(self._entries_with("gate5_docs", omit=("kill_when",)),
                                    "missing_kill_when", "gate5_docs")
        self.assertIn("kill_when", line)

    def test_empty_value_counts_as_missing(self) -> None:
        entries = self._entries_with("gate4_tests")
        idx = entries.index("  - id: gate4_tests")
        k = next(i for i in range(idx, len(entries)) if entries[i].startswith("    evidence:"))
        entries[k] = '    evidence: ""'
        self._single_finding(entries, "missing_evidence", "gate4_tests")

    def test_all_three_missing_is_three_findings_in_field_order(self) -> None:
        entries = self._entries_with("gate0_arch", omit=("catches", "evidence", "kill_when"))
        self.fx.write(command_text(entries))
        rc, out, _ = run_check(self.fx)
        self.assertEqual(rc, 1, out)
        self.assertEqual([ln.split(":")[0] for ln in finding_lines(out)],
                         ["missing_catches", "missing_evidence", "missing_kill_when"])

    # AC-1.2
    def test_unknown_path_value(self) -> None:
        line = self._single_finding(self._entries_with("gate3_5_drift", path="optional"),
                                    "unknown_path_value", "gate3_5_drift")
        self.assertIn("optional", line)

    def test_absent_path_is_no_finding(self) -> None:
        self.fx.write(command_text(complete_entries()))
        rc, out, _ = run_check(self.fx)
        self.assertEqual(rc, 0, out)
        self.assertEqual(finding_lines(out), [])

    def test_both_path_values_are_accepted(self) -> None:
        for value in vp.PATH_VALUES:
            with self.subTest(path=value):
                self.fx.write(command_text(self._entries_with("gate4_5_behavior", path=value)))
                rc, out, _ = run_check(self.fx)
                self.assertEqual(rc, 0, out)
                self.assertEqual(finding_lines(out), [])

    # AC-1.3
    def test_complete_entries_keep_the_three_line_clean_output(self) -> None:
        entries = self._entries_with("gate2_5_surface", path="default")
        self.fx.write(command_text(entries))
        rc, out, _ = run_check(self.fx)
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(out.splitlines()), 3, out)
        self.assertRegex(out.splitlines()[-1], r"^verdict-provenance: pass \(gates: 10 entries, "
                                               r"headings: 10, script: 2, prose-only: 8, findings: 0\)$")

    def test_new_codes_do_not_mask_existing_ones(self) -> None:
        """An entry with no source and no evidence fields reports both kinds."""
        entries = ["  - id: gate1_coding"]
        self.fx.write(command_text(entries, headings=("#### Gate 1: Coding Agent",)))
        rc, out, _ = run_check(self.fx)
        self.assertEqual(rc, 1, out)
        self.assertEqual([ln.split(":")[0] for ln in finding_lines(out)],
                         ["entry_without_source", "missing_catches", "missing_evidence",
                          "missing_kill_when"])

    def test_usage_errors_still_exit_2(self) -> None:
        self.fx.write(command_text(["  - path: default"], headings=()))
        rc, _, err = run_check(self.fx)
        self.assertEqual(rc, 2)
        self.assertIn("id", err)


class RealCommandTests(unittest.TestCase):
    """AC-4.1 against the shipped commands/implement-story.md."""

    def test_real_command_is_clean_with_current_prose_only(self) -> None:
        argv = ["check", "--command", str(REPO_ROOT / "commands" / "implement-story.md"),
                "--repo", str(REPO_ROOT)]
        out = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                vp.main(argv)
            except SystemExit as exc:
                code = int(exc.code or 0)
        text = out.getvalue()
        self.assertEqual(code, 0, text)
        self.assertEqual(finding_lines(text), [])
        # 2026-10-01-behavioral-verification AC-4.3: only Gate 1 stays prose-only.
        self.assertIn("note: prose_only_count: 1 (cap 1)", text)

    def test_real_command_gates_block_names_all_ten_truthfully(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        # Compare only the verdict-source keys; the evidence fields are pinned
        # by test_real_command_declares_evidence_on_every_gate.
        source_keys = ("id", "script", "verification")
        by_id = {g["id"]: {k: v for k, v in g.items() if k in source_keys}
                 for g in vp.parse_gates(text)}
        self.assertEqual(tuple(by_id), ALL_IDS)
        self.assertEqual(by_id["gate2_build"], {"id": "gate2_build", "script": "scripts/build-smoke.py"})
        self.assertEqual(by_id["gate4_tests"], {"id": "gate4_tests", "script": "scripts/test-integrity.py"})
        self.assertEqual(by_id["gate0_arch"], {"id": "gate0_arch", "script": "scripts/arch-check.py"})
        self.assertEqual(by_id["gate0_5_boundary"], {"id": "gate0_5_boundary", "script": "scripts/boundary-map.py"})
        self.assertEqual(by_id["gate2_5_surface"], {"id": "gate2_5_surface", "script": "scripts/change-surface.py"})
        self.assertEqual(by_id["gate3_review"], {"id": "gate3_review", "script": "scripts/review-override.py"})
        self.assertEqual(by_id["gate5_docs"], {"id": "gate5_docs", "script": "scripts/docs-check.py"})
        shipped_scripts = set(SCRIPTS) | {
            "gate0_arch", "gate0_5_boundary", "gate2_5_surface",
            "gate3_review", "gate3_5_drift", "gate5_docs", "gate4_5_behavior",
        }
        self.assertEqual(by_id["gate4_5_behavior"],
                         {"id": "gate4_5_behavior", "script": "scripts/app-verify.py"})
        self.assertEqual(by_id["gate3_5_drift"], {"id": "gate3_5_drift", "script": "scripts/drift-format.py"})
        for gate_id in ALL_IDS:
            if gate_id in shipped_scripts:
                continue
            self.assertEqual(by_id[gate_id], {"id": gate_id, "verification": "prose-only"})

    def test_real_command_declares_evidence_on_every_gate(self) -> None:
        """Business Rules 1-3 on the shipped file [AC-1.3, AC-1.4]."""
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        gates = vp.parse_gates(text)
        self.assertEqual(len(gates), 10)
        for gate in gates:
            for field in vp.EVIDENCE_FIELDS:
                self.assertTrue(gate.get(field), "%s lacks %s" % (gate["id"], field))
            self.assertIn(gate.get("path", "default"), vp.PATH_VALUES, gate["id"])
            # Rule 2: only a gate with no recorded catch leaves the default path.
            if gate.get("path") == "full-pipeline":
                self.assertEqual(gate["evidence"], "none recorded", gate["id"])
        by_id = {g["id"]: g for g in gates}
        # Rule 3: the gate holding Safety Fact, Reviewer Filters and the
        # evidence gate stays, and so do the producers they read: the boundary
        # map and change surface (risk route, blast radius), Gate 2's saved
        # checks, and the code itself.
        for kept in ("gate3_review", "gate2_5_surface", "gate0_5_boundary",
                     "gate2_build", "gate1_coding"):
            self.assertEqual(by_id[kept].get("path"), "default", kept)

    def test_real_gate_4_5_body_has_no_percentage(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 4.5: Behavioral Verification")
        end = text.index("#### Gate 5:", start)
        section = text[start:end]
        self.assertNotIn("%", section)
        self.assertNotIn(" percent", section)
        self.assertIn("scripts/app-verify.py run", section)


if __name__ == "__main__":
    unittest.main()
