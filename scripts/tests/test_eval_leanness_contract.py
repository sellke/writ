#!/usr/bin/env python3
"""Tests for eval-leanness.py's contract instrumentation (spec:
2026-08-11-governor-instrumentation).

Two families live here:

  1. **The bound justification (Story 1).** The 16-row matrix from
     `sub-specs/technical-spec.md` -> "Test matrix for the bound
     justification". Rows 4, 5 and 7 are the acceptance bar (grow -> justify
     -> quiet; grow further -> warns again; down is free); row 8 proves the
     per-metric independence the old per-surface read lacked; row 10 is the
     direct regression test against the permanent mute.

  2. **The contract checks and the emission seam (Stories 3-7).** Fixture
     trees under a temp root, plus the flip test that sets
     `CONTRACT_CHECK_SEVERITY` in-process and asserts the identical finding
     dicts move from `warnings` to `structural`.

`eval-leanness.py` has a hyphen in its filename, so it is loaded by path via
`importlib.util.spec_from_file_location` — the established recipe in
`test_archive_sweep.py`, `test_spec_status.py` and `test_story_deps.py`.
Tests are `unittest.TestCase` classes (as in `test_story_context.py` and
`test_story_deps.py`) so the file runs under both `python3 -m unittest` and
`python3 -m pytest`.
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import inspect
import io
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "eval-leanness.py"
_spec = importlib.util.spec_from_file_location("eval_leanness", MODULE_PATH)
assert _spec is not None and _spec.loader is not None
lean = importlib.util.module_from_spec(_spec)
sys.modules["eval_leanness"] = lean
_spec.loader.exec_module(lean)


# ---------------------------------------------------------------------------
# Story 1 — the bound justification
# ---------------------------------------------------------------------------

BASELINE_PATH = "/tmp/leanness-baseline.json"


def make_baseline(surface_entry: dict, *, schema: int = 3) -> dict:
    return {"recorded": "2026-08-11", "schema": schema,
            "surfaces": {"commands": surface_entry}}


def make_metrics(**per_surface_values: int) -> dict:
    return {"per_surface": {"commands": dict(per_surface_values)}}


def growth_warnings(baseline: dict, metrics: dict) -> list[dict]:
    structural, warnings = lean.check_baseline(baseline, None, BASELINE_PATH, metrics)
    assert structural == [], f"unexpected structural findings: {structural}"
    return warnings


def j(value, date: str = "2026-08-11", text: str = "accepted increment") -> dict:
    return {"value": value, "date": date, "text": text}


class BoundJustificationTests(unittest.TestCase):
    """The 16-row matrix. Row numbers match sub-specs/technical-spec.md."""

    def test_row1_equal_is_not_growth(self):
        warnings = growth_warnings(make_baseline({"lines": 100}),
                                   make_metrics(lines=100))
        self.assertEqual(warnings, [])

    def test_row2_down_is_free(self):
        warnings = growth_warnings(make_baseline({"lines": 100}),
                                   make_metrics(lines=90))
        self.assertEqual(warnings, [])

    def test_row3_growth_with_no_justification_warns_naming_the_metric(self):
        warnings = growth_warnings(make_baseline({"lines": 100}),
                                   make_metrics(lines=120))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")
        self.assertIn("no justification recorded", warnings[0]["what"])
        self.assertIn("justifications.lines", warnings[0]["fix"])

    def test_row4_justified_exactly_is_silent(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j(120)}}),
            make_metrics(lines=120))
        self.assertEqual(warnings, [])

    def test_row5_one_past_the_ceiling_warns_naming_the_ceiling(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j(120)}}),
            make_metrics(lines=121))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")
        self.assertIn("justified ceiling of 120", warnings[0]["what"])
        self.assertIn("2026-08-11", warnings[0]["what"])

    def test_row6_ceiling_never_rearms_a_satisfied_floor(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j(120)}}),
            make_metrics(lines=100))
        self.assertEqual(warnings, [])

    def test_row7_down_is_free_even_with_a_justification_present(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j(120)}}),
            make_metrics(lines=90))
        self.assertEqual(warnings, [])

    def test_row8_a_justification_for_one_metric_never_silences_the_other(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "chars": 1000,
                           "justifications": {"lines": j(120)}}),
            make_metrics(lines=120, chars=5000))
        self.assertEqual([w["subject"] for w in warnings], ["commands.chars"])

    def test_row9_legacy_empty_string_behaves_exactly_as_today(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justification": ""}, schema=2),
            make_metrics(lines=120))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")
        self.assertIn("no justification recorded", warnings[0]["what"])

    def test_row10_legacy_non_empty_string_no_longer_mutes(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justification": "because"}, schema=2),
            make_metrics(lines=1_000_000))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")
        self.assertIn("legacy unbounded", warnings[0]["what"])
        self.assertIn("justifications.lines", warnings[0]["fix"])

    def test_row11_non_numeric_ceiling_never_silences(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j("120")}}),
            make_metrics(lines=120))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")

    def test_row12_a_bound_with_no_reason_is_not_a_justification(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j(120, text="")}}),
            make_metrics(lines=120))
        self.assertEqual(len(warnings), 1)

    def test_row13_stale_ceiling_below_the_floor_warns_without_crashing(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": {"lines": j(90)}}),
            make_metrics(lines=120))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")

    def test_row14_justifications_not_a_dict_warns_without_raising(self):
        warnings = growth_warnings(
            make_baseline({"lines": 100, "justifications": "yes"}),
            make_metrics(lines=120))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["subject"], "commands.lines")

    def test_row15_schema_2_is_read_normally_not_structurally_flagged(self):
        baseline = make_baseline({"lines": 100, "justification": ""}, schema=2)
        structural, _ = lean.check_baseline(baseline, None, BASELINE_PATH,
                                            make_metrics(lines=100))
        self.assertEqual(structural, [])

    def test_row15b_schema_3_is_read_normally(self):
        baseline = make_baseline({"lines": 100, "justifications": {}}, schema=3)
        structural, _ = lean.check_baseline(baseline, None, BASELINE_PATH,
                                            make_metrics(lines=100))
        self.assertEqual(structural, [])

    def test_row15c_schema_1_stays_structural(self):
        structural, _ = lean.check_baseline({"schema": 1}, None, BASELINE_PATH,
                                            make_metrics(lines=100))
        self.assertEqual(len(structural), 1)

    def test_row16_update_baseline_writes_schema_3_with_empty_justifications(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "commands").mkdir()
            (root / "commands" / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
            baseline_path = root / ".writ" / "leanness-baseline.json"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = lean.main(["--root", str(root), "--baseline", str(baseline_path),
                                "--update-baseline"])
            self.assertEqual(rc, 0)
            payload = json.loads(baseline_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], 3)
            for name, entry in payload["surfaces"].items():
                self.assertEqual(entry["justifications"], {}, name)
                self.assertNotIn("justification", entry, name)
            self.assertNotIn("justification", json.dumps(payload).replace(
                "justifications", ""))

    def test_the_fix_text_never_prescribes_a_self_erasing_sequence(self):
        """The old `fix` said: write a justification, then rerun
        --update-baseline (which erases it). The replacement must state the
        two dispositions separately."""
        warnings = growth_warnings(make_baseline({"lines": 100}),
                                   make_metrics(lines=120))
        fix = warnings[0]["fix"]
        self.assertNotIn("and rerun --update-baseline", fix)
        self.assertIn("moves EVERY surface's floor", fix)

    def test_docstring_no_longer_advertises_up_costs_a_sentence(self):
        doc = inspect.getdoc(lean.check_baseline) or ""
        self.assertNotIn("up costs a sentence", doc)


class JustifiedCeilingTests(unittest.TestCase):
    """`justified_ceiling()` in isolation — the reader the matrix exercises."""

    def test_valid_bound_returns_value_text_and_date(self):
        ceiling, text, date = lean.justified_ceiling(
            {"justifications": {"lines": j(120, "2026-08-11", "why")}}, "lines")
        self.assertEqual((ceiling, text, date), (120, "why", "2026-08-11"))

    def test_absent_key_returns_no_bound(self):
        self.assertEqual(lean.justified_ceiling({}, "lines"), (None, "", ""))

    def test_legacy_string_returns_its_text_but_no_bound(self):
        ceiling, text, _ = lean.justified_ceiling({"justification": "because"}, "lines")
        self.assertIsNone(ceiling)
        self.assertEqual(text, "because")

    def test_boolean_value_is_not_a_numeric_ceiling(self):
        self.assertEqual(
            lean.justified_ceiling({"justifications": {"lines": j(True)}}, "lines"),
            (None, "", ""))

    def test_other_metric_key_is_never_consulted(self):
        self.assertEqual(
            lean.justified_ceiling({"justifications": {"lines": j(120)}}, "chars"),
            (None, "", ""))


class RealRepoBaselineTests(unittest.TestCase):
    """Behaviour against the committed repo, stable across Story 1 and 2."""

    def test_no_structural_finding_and_every_growth_subject_names_a_metric(self):
        metrics, _ = lean.compute_metrics(str(REPO_ROOT))
        baseline_path = REPO_ROOT / ".writ" / "leanness-baseline.json"
        baseline, err = lean.load_baseline(str(baseline_path))
        structural, warnings = lean.check_baseline(baseline, err, str(baseline_path),
                                                   metrics)
        self.assertEqual(structural, [], "committed baseline must never be structural")
        for warning in warnings:
            self.assertIn(".", warning["subject"],
                          "growth subjects must be <surface>.<metric>")


# ---------------------------------------------------------------------------
# Stories 3-7 — fixture tree helpers
# ---------------------------------------------------------------------------

COMPLIANT_FRONTMATTER = """\
---
name: {name}
description: "a description"
problem: "the problem this command exists to solve"
outcome: "what the run leaves behind"
exit_criteria:
  - "the first falsifiable condition"
  - "the second falsifiable condition"
---

# {name}

## Completion

Done when the exit criteria hold.
"""


def write_command(root: Path, name: str, body: str) -> Path:
    path = root / "commands" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def write_agent(root: Path, name: str, body: str) -> Path:
    path = root / "agents" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def compliant_agent(heading: str = "## Agent Configuration", info: str = "") -> str:
    return (
        "# Agent\n\n"
        f"{heading}\n\n"
        f"```{info}\n"
        "name: sample\n"
        'problem: "the gap this agent closes"\n'
        'outcome: "what the agent hands back"\n'
        "exit_criteria:\n"
        '  - "the first condition"\n'
        "```\n"
    )


def subjects(findings: list[dict]) -> list[str]:
    return [f["subject"] for f in findings]


# ---------------------------------------------------------------------------
# Story 3 — component contract presence
# ---------------------------------------------------------------------------

class FrontmatterReaderTests(unittest.TestCase):

    def test_leading_fence_is_parsed_into_key_value_pairs(self):
        with TemporaryDirectory() as tmp:
            path = write_command(Path(tmp), "alpha",
                                 COMPLIANT_FRONTMATTER.format(name="alpha"))
            fm = lean.read_frontmatter(str(path))
            self.assertIsNotNone(fm)
            self.assertEqual(fm["name"], "alpha")
            self.assertIn("the first falsifiable condition", fm["exit_criteria"])

    def test_no_leading_fence_returns_none(self):
        with TemporaryDirectory() as tmp:
            path = write_command(Path(tmp), "alpha", "# Alpha\n\nbody\n")
            self.assertIsNone(lean.read_frontmatter(str(path)))

    def test_mid_document_horizontal_rule_is_not_frontmatter(self):
        with TemporaryDirectory() as tmp:
            path = write_command(Path(tmp), "alpha",
                                 "# Alpha\n\n---\n\nproblem: not really\n---\n")
            self.assertIsNone(lean.read_frontmatter(str(path)))

    def test_unterminated_fence_returns_none(self):
        with TemporaryDirectory() as tmp:
            path = write_command(Path(tmp), "alpha", "---\nproblem: x\n\n# Alpha\n")
            self.assertIsNone(lean.read_frontmatter(str(path)))

    def test_block_value_maps_to_its_joined_continuation_lines(self):
        with TemporaryDirectory() as tmp:
            path = write_command(
                Path(tmp), "alpha",
                '---\nname: alpha\nexit_criteria:\n  - "one"\n  - "two"\n---\n')
            fm = lean.read_frontmatter(str(path))
            self.assertIn("one", fm["exit_criteria"])
            self.assertIn("two", fm["exit_criteria"])

    def test_empty_block_value_maps_to_the_empty_string(self):
        with TemporaryDirectory() as tmp:
            path = write_command(Path(tmp), "alpha",
                                 "---\nname: alpha\nexit_criteria:\n---\n")
            fm = lean.read_frontmatter(str(path))
            self.assertEqual(fm["exit_criteria"], "")


class ComponentContractCheckTests(unittest.TestCase):

    def test_compliant_command_emits_nothing(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", COMPLIANT_FRONTMATTER.format(name="alpha"))
            self.assertEqual(lean.check_component_contract(tmp), [])

    def test_one_missing_field_emits_exactly_one_named_finding(self):
        with TemporaryDirectory() as tmp:
            body = COMPLIANT_FRONTMATTER.format(name="alpha").replace(
                'outcome: "what the run leaves behind"\n', "")
            write_command(Path(tmp), "alpha", body)
            findings = lean.check_component_contract(tmp)
            self.assertEqual(subjects(findings), ["commands/alpha.md → outcome:"])

    def test_empty_exit_criteria_is_a_finding(self):
        with TemporaryDirectory() as tmp:
            body = COMPLIANT_FRONTMATTER.format(name="alpha").replace(
                '  - "the first falsifiable condition"\n'
                '  - "the second falsifiable condition"\n', "")
            write_command(Path(tmp), "alpha", body)
            findings = lean.check_component_contract(tmp)
            self.assertEqual(subjects(findings), ["commands/alpha.md → exit_criteria:"])

    def test_empty_list_literal_is_a_finding(self):
        with TemporaryDirectory() as tmp:
            body = COMPLIANT_FRONTMATTER.format(name="alpha").replace(
                'exit_criteria:\n  - "the first falsifiable condition"\n'
                '  - "the second falsifiable condition"\n', "exit_criteria: []\n")
            write_command(Path(tmp), "alpha", body)
            findings = lean.check_component_contract(tmp)
            self.assertEqual(subjects(findings), ["commands/alpha.md → exit_criteria:"])

    def test_missing_frontmatter_emits_one_file_level_finding(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", "# Alpha\n\nno fence here\n")
            findings = lean.check_component_contract(tmp)
            self.assertEqual(len(findings), 1)
            self.assertIn("no frontmatter block", findings[0]["what"])

    def test_infra_commands_are_never_checked(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "_preamble", "# Preamble\n\nno frontmatter\n")
            self.assertEqual(lean.check_component_contract(tmp), [])

    def test_both_agent_carriers_are_recognised(self):
        with TemporaryDirectory() as tmp:
            write_agent(Path(tmp), "plain", compliant_agent())
            write_agent(Path(tmp), "yamlish",
                        compliant_agent("## Agent Specification", "yaml"))
            self.assertEqual(lean.check_component_contract(tmp), [])

    def test_agent_with_no_carrier_emits_one_carrier_level_finding(self):
        with TemporaryDirectory() as tmp:
            write_agent(Path(tmp), "bare", "# Agent\n\nno config block at all\n")
            findings = lean.check_component_contract(tmp)
            self.assertEqual(len(findings), 1)
            self.assertIn("Agent Configuration", findings[0]["subject"])

    def test_agent_heading_with_no_fence_emits_one_carrier_level_finding(self):
        with TemporaryDirectory() as tmp:
            write_agent(Path(tmp), "bare",
                        "# Agent\n\n## Agent Configuration\n\nprose, no fence\n")
            findings = lean.check_component_contract(tmp)
            self.assertEqual(len(findings), 1)

    def test_agent_missing_one_field_emits_one_field_finding(self):
        with TemporaryDirectory() as tmp:
            body = compliant_agent().replace('problem: "the gap this agent closes"\n', "")
            write_agent(Path(tmp), "plain", body)
            findings = lean.check_component_contract(tmp)
            self.assertEqual(subjects(findings), ["agents/plain.md → problem:"])

    def test_absent_directories_yield_no_findings(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(lean.check_component_contract(tmp), [])

    def test_real_repo_agents_produce_no_carrier_false_finding(self):
        findings = lean.check_component_contract(str(REPO_ROOT))
        offenders = [f for f in findings if "visual-qa-agent" in f["subject"]]
        self.assertEqual(offenders, [], "visual-qa-agent.md's ```yaml carrier must be read")



# ---------------------------------------------------------------------------
# Story 4 — `## Completion` presence
# ---------------------------------------------------------------------------

class CompletionSectionCheckTests(unittest.TestCase):

    def test_compliant_command_emits_nothing(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", COMPLIANT_FRONTMATTER.format(name="alpha"))
            self.assertEqual(lean.check_completion_sections(tmp), [])

    def test_missing_heading_emits_one_named_finding(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", "# Alpha\n\nbody\n")
            findings = lean.check_completion_sections(tmp)
            self.assertEqual(subjects(findings), ["commands/alpha.md → ## Completion"])

    def test_completion_criteria_near_miss_is_a_finding_with_the_exact_spelling(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", "# Alpha\n\n## Completion Criteria\n\nx\n")
            findings = lean.check_completion_sections(tmp)
            self.assertEqual(len(findings), 1)
            self.assertIn("exact H2 spelling", findings[0]["fix"])
            self.assertIn("## Completion Criteria", findings[0]["fix"])

    def test_h3_near_miss_is_a_finding(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", "# Alpha\n\n### Completion\n\nx\n")
            self.assertEqual(len(lean.check_completion_sections(tmp)), 1)

    def test_heading_with_empty_body_passes(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", "# Alpha\n\n## Completion\n")
            self.assertEqual(lean.check_completion_sections(tmp), [])

    def test_heading_only_inside_a_fence_does_not_satisfy_the_check(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha",
                          "# Alpha\n\n```markdown\n## Completion\n```\n")
            self.assertEqual(len(lean.check_completion_sections(tmp)), 1)

    def test_infra_commands_are_never_checked(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "_preamble", "# Preamble\n")
            self.assertEqual(lean.check_completion_sections(tmp), [])

    def test_absent_commands_directory_yields_no_findings(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(lean.check_completion_sections(tmp), [])



# ---------------------------------------------------------------------------
# Story 5 — loop-bound presence
# ---------------------------------------------------------------------------

LOOP_BLOCK = (
    "loop:\n"
    '  unit: "story"\n'
    "  max_iterations: 12\n"
    "  on_exhaustion: halt_reported\n"
    '  calibrated_against: "evidence"\n'
)


def loop_command_body(loop_block: str = LOOP_BLOCK) -> str:
    return ('---\nname: x\nproblem: "p"\noutcome: "o"\n'
            'exit_criteria:\n  - "c"\n' + loop_block + "---\n\n# X\n\n## Completion\n\nx\n")


class LoopBoundsCheckTests(unittest.TestCase):

    def _tree(self, tmp: str, bodies: dict[str, str]) -> None:
        for name in lean.LOOP_BEARING_COMMANDS:
            if name in bodies:
                write_command(Path(tmp), name, bodies[name])
            else:
                write_command(Path(tmp), name, loop_command_body())

    def test_all_five_declared_emits_nothing(self):
        with TemporaryDirectory() as tmp:
            self._tree(tmp, {})
            self.assertEqual(lean.check_loop_bounds(tmp), [])

    def test_one_missing_field_emits_exactly_one_named_finding(self):
        with TemporaryDirectory() as tmp:
            partial = LOOP_BLOCK.replace("  on_exhaustion: halt_reported\n", "")
            self._tree(tmp, {"refactor": loop_command_body(partial)})
            findings = lean.check_loop_bounds(tmp)
            self.assertEqual(subjects(findings),
                             ["commands/refactor.md → loop.on_exhaustion"])

    def test_childless_loop_key_emits_two_findings_not_one(self):
        with TemporaryDirectory() as tmp:
            self._tree(tmp, {"refactor": loop_command_body("loop:\n")})
            findings = lean.check_loop_bounds(tmp)
            self.assertEqual(sorted(subjects(findings)), [
                "commands/refactor.md → loop.max_iterations",
                "commands/refactor.md → loop.on_exhaustion",
            ])

    def test_flattened_keys_are_accepted(self):
        with TemporaryDirectory() as tmp:
            flat = "loop.max_iterations: 4\nloop.on_exhaustion: escalate\n"
            self._tree(tmp, {"refactor": loop_command_body(flat)})
            self.assertEqual(lean.check_loop_bounds(tmp), [])

    def test_unlisted_command_is_never_checked(self):
        with TemporaryDirectory() as tmp:
            self._tree(tmp, {})
            write_command(Path(tmp), "status", "# Status\n\nno loop, no frontmatter\n")
            self.assertEqual(lean.check_loop_bounds(tmp), [])

    def test_a_listed_command_missing_from_disk_is_a_finding(self):
        with TemporaryDirectory() as tmp:
            self._tree(tmp, {})
            (Path(tmp) / "commands" / "refactor.md").unlink()
            findings = lean.check_loop_bounds(tmp)
            self.assertEqual(subjects(findings), ["commands/refactor.md → missing"])

    def test_unparseable_frontmatter_emits_one_file_level_finding(self):
        with TemporaryDirectory() as tmp:
            self._tree(tmp, {})
            write_command(Path(tmp), "refactor", "# Refactor\n\nno fence\n")
            findings = lean.check_loop_bounds(tmp)
            self.assertEqual(len(findings), 1)
            self.assertIn("no frontmatter block", findings[0]["what"])

    def test_real_repo_five_commands_are_all_bounded(self):
        self.assertEqual(lean.check_loop_bounds(str(REPO_ROOT)), [])

    def test_the_constant_matches_the_correctness_checker_that_shares_it(self):
        """Check 3 (presence) and eval-loop-bounds.py (correctness) split one
        population. Two different lists would report the same file twice or
        skip it entirely — cross-read it, never restate it."""
        source = (REPO_ROOT / "scripts" / "eval-loop-bounds.py").read_text(
            encoding="utf-8")
        for name in lean.LOOP_BEARING_COMMANDS:
            self.assertIn(f'"{name}"', source)



# ---------------------------------------------------------------------------
# Story 6 — required_skills: resolution
# ---------------------------------------------------------------------------

def skill_command(names: str) -> str:
    return ('---\nname: x\nproblem: "p"\noutcome: "o"\n'
            f'exit_criteria:\n  - "c"\nrequired_skills: {names}\n---\n\n'
            "# X\n\n## Completion\n\nx\n")


class RequiredSkillsCheckTests(unittest.TestCase):

    def _skill(self, tmp: str, name: str) -> None:
        path = Path(tmp) / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"name: {name}\n", encoding="utf-8")

    def test_resolving_name_emits_nothing(self):
        with TemporaryDirectory() as tmp:
            self._skill(tmp, "tdd-cycle")
            write_command(Path(tmp), "alpha", skill_command("[tdd-cycle]"))
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual(findings, [])
            self.assertEqual(count, 1)

    def test_unknown_name_emits_one_finding_naming_file_and_name(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", skill_command("[no-such-skill]"))
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual(subjects(findings),
                             ["commands/alpha.md → required_skills: no-such-skill"])
            self.assertIn("skills/no-such-skill/SKILL.md", findings[0]["fix"])
            self.assertEqual(count, 1)

    def test_duplicates_are_deduplicated(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha",
                          skill_command("[no-such-skill, no-such-skill]"))
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual(len(findings), 1)
            self.assertEqual(count, 1)

    def test_block_list_form_is_read(self):
        with TemporaryDirectory() as tmp:
            body = ('---\nname: x\nproblem: "p"\noutcome: "o"\n'
                    'exit_criteria:\n  - "c"\n'
                    "required_skills:\n  - tdd-cycle\n  - ghost-skill\n---\n\n# X\n")
            self._skill(tmp, "tdd-cycle")
            write_command(Path(tmp), "alpha", body)
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual(subjects(findings),
                             ["commands/alpha.md → required_skills: ghost-skill"])
            self.assertEqual(count, 2)

    def test_agent_carrier_declarations_are_checked_identically(self):
        with TemporaryDirectory() as tmp:
            body = compliant_agent("## Agent Specification", "yaml").replace(
                "name: sample\n", "name: sample\nrequired_skills: [ghost-skill]\n")
            write_agent(Path(tmp), "plain", body)
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual(subjects(findings),
                             ["agents/plain.md → required_skills: ghost-skill"])
            self.assertEqual(count, 1)

    def test_empty_list_is_zero_pairs_and_zero_findings(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", skill_command("[]"))
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual((findings, count), ([], 0))

    def test_absent_skills_directory_warns_rather_than_raising(self):
        with TemporaryDirectory() as tmp:
            write_command(Path(tmp), "alpha", skill_command("[tdd-cycle]"))
            findings, count = lean.check_required_skills(tmp)
            self.assertEqual(len(findings), 1)
            self.assertEqual(count, 1)

    def test_real_repo_is_vacuous_and_says_so(self):
        findings, count = lean.check_required_skills(str(REPO_ROOT))
        self.assertEqual(findings, [])
        self.assertEqual(count, 0, "a vacuous pass must be visible as a declaration count")



# ---------------------------------------------------------------------------
# Story 7 — the warnings -> structural flip seam
# ---------------------------------------------------------------------------

CONTRACT_CHECKS = (
    "check_component_contract",
    "check_completion_sections",
    "check_loop_bounds",
    "check_required_skills",
)


def build_noncompliant_root(tmp: str) -> None:
    """One fixture tree that makes all four checks speak.

    Every OTHER check is kept quiet — the registry surfaces exist, and the
    README table names every command — so `structural` is empty for reasons
    that have nothing to do with the seam, and a finding appearing there after
    the flip can only have come through the router.
    """
    root = Path(tmp)
    write_command(root, "alpha", "# Alpha\n\nno frontmatter, no completion\n")
    for name in lean.LOOP_BEARING_COMMANDS:
        write_command(root, name, "---\nname: x\n---\n\n# X\n")
    write_agent(root, "bare", "# Agent\n\nno carrier\n")
    write_command(root, "skilled", skill_command("[ghost-skill]"))

    for surface in ("skills", "adapters", "scripts"):
        (root / surface).mkdir(parents=True, exist_ok=True)
    (root / "system-instructions.md").write_text("# System Instructions\n",
                                                 encoding="utf-8")
    names = ["alpha", "skilled", *lean.LOOP_BEARING_COMMANDS]
    rows = "\n".join(f"| `/{name}` | fixture command |" for name in names)
    (root / "README.md").write_text(
        "# Demo\n\n## Commands\n\n| Command | Purpose |\n|---|---|\n"
        + rows + "\n", encoding="utf-8")


class FlipSeamTests(unittest.TestCase):

    def setUp(self):
        self._shipped = lean.CONTRACT_CHECK_SEVERITY
        self.addCleanup(setattr, lean, "CONTRACT_CHECK_SEVERITY", self._shipped)

    def _collect(self, tmp: str) -> tuple[list[dict], list[dict]]:
        structural: list[dict] = []
        warnings: list[dict] = []
        lean.emit_contract_findings(lean.check_component_contract(tmp),
                                    structural, warnings)
        lean.emit_contract_findings(lean.check_completion_sections(tmp),
                                    structural, warnings)
        lean.emit_contract_findings(lean.check_loop_bounds(tmp), structural, warnings)
        skill_findings, _ = lean.check_required_skills(tmp)
        lean.emit_contract_findings(skill_findings, structural, warnings,
                                    severity="warnings")
        return structural, warnings

    def test_shipped_default_is_warnings(self):
        self.assertEqual(self._shipped, "warnings",
                         "the committed constant must ship non-blocking")

    def test_default_routes_everything_non_blocking(self):
        with TemporaryDirectory() as tmp:
            build_noncompliant_root(tmp)
            structural, warnings = self._collect(tmp)
            self.assertEqual(structural, [])
            self.assertGreater(len(warnings), 0)

    def test_flip_moves_the_identical_dicts_to_structural(self):
        with TemporaryDirectory() as tmp:
            build_noncompliant_root(tmp)
            _, before = self._collect(tmp)
            pinned, _ = lean.check_required_skills(tmp)
            self.assertGreater(len(pinned), 0, "the fixture must exercise the pin")
            expected_moved = copy.deepcopy([f for f in before if f not in pinned])

            lean.CONTRACT_CHECK_SEVERITY = "structural"
            structural, warnings = self._collect(tmp)

            self.assertEqual(structural, expected_moved)
            self.assertEqual(warnings, pinned)

    def test_pinned_required_skills_findings_survive_the_flip(self):
        with TemporaryDirectory() as tmp:
            build_noncompliant_root(tmp)
            pinned, _ = lean.check_required_skills(tmp)
            lean.CONTRACT_CHECK_SEVERITY = "structural"
            structural, warnings = self._collect(tmp)
            for finding in pinned:
                self.assertIn(finding, warnings)
                self.assertNotIn(finding, structural)

    def test_unrecognised_severity_falls_back_to_warnings(self):
        with TemporaryDirectory() as tmp:
            build_noncompliant_root(tmp)
            lean.CONTRACT_CHECK_SEVERITY = "blocking"
            structural, warnings = self._collect(tmp)
            self.assertEqual(structural, [])
            self.assertGreater(len(warnings), 0)

    def test_no_contract_check_touches_the_buckets_directly(self):
        for name in CONTRACT_CHECKS:
            source = inspect.getsource(getattr(lean, name))
            self.assertNotIn("structural", source, f"{name} must not name `structural`")
            self.assertNotIn("warnings.append", source,
                             f"{name} must not append to `warnings`")

    def test_the_constant_carries_its_handoff_comment(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        head, _, _ = source.partition('CONTRACT_CHECK_SEVERITY = "warnings"')
        preamble = head[-1400:]
        for token in ("governor-enforcement", "ADR-020", "Enforcement sequencing"):
            self.assertIn(token, preamble,
                          f"the flip handoff comment must name {token}")

    def test_main_exits_zero_and_stays_non_blocking_on_a_noncompliant_root(self):
        with TemporaryDirectory() as tmp:
            build_noncompliant_root(tmp)
            baseline_path = Path(tmp) / ".writ" / "leanness-baseline.json"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                lean.main(["--root", tmp, "--baseline", str(baseline_path),
                           "--update-baseline"])
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = lean.main(["--root", tmp, "--baseline", str(baseline_path)])
            self.assertEqual(rc, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["structural"], [])
            self.assertGreater(len(payload["warnings"]), 0)
            compliance = payload["metrics"]["contract_compliance"]
            for key in ("commands_checked", "commands_with_contract",
                        "commands_with_completion", "loop_commands_checked",
                        "loop_commands_bounded", "agents_checked",
                        "agents_with_contract"):
                self.assertIsInstance(compliance[key], int, key)
            self.assertEqual(payload["metrics"]["required_skills_declarations"], 1)

    def test_flipped_main_makes_the_same_findings_blocking(self):
        """The eval.sh boundary: check_leanness() maps `structural` -> FAIL, so
        proving the flip reaches a non-empty `structural` from main() is the
        same proof, without mutating the committed script."""
        with TemporaryDirectory() as tmp:
            build_noncompliant_root(tmp)
            baseline_path = Path(tmp) / ".writ" / "leanness-baseline.json"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                lean.main(["--root", tmp, "--baseline", str(baseline_path),
                           "--update-baseline"])
            lean.CONTRACT_CHECK_SEVERITY = "structural"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                lean.main(["--root", tmp, "--baseline", str(baseline_path)])
            payload = json.loads(out.getvalue())
            self.assertGreater(len(payload["structural"]), 0)


class EvalShBoundaryTests(unittest.TestCase):
    """The seam must reach the gate, not just the JSON.

    The committed script is never mutated. A temp project root gets a COPY of
    eval.sh and a COPY of eval-leanness.py with the constant flipped, and
    `eval.sh --check=leanness` runs against it for real.
    """

    def test_eval_sh_maps_structural_to_add_finding(self):
        source = (REPO_ROOT / "scripts" / "eval.sh").read_text(encoding="utf-8")
        _, _, tail = source.partition("check_leanness() {")
        body = tail.split("\ncheck_", 1)[0]
        self.assertIn("STRUCT)", body)
        self.assertIn('add_finding "$a" "$b" "$c"', body)
        self.assertIn("WARN)", body)
        self.assertIn("add_note", body)

    def _run_leanness_check(self, severity: str) -> tuple[subprocess.CompletedProcess, str]:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        report_dir = TemporaryDirectory()
        self.addCleanup(report_dir.cleanup)
        root = Path(self._tmp.name)
        build_noncompliant_root(str(root))

        scripts = root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "scripts" / "eval.sh", scripts / "eval.sh")
        helper_source = MODULE_PATH.read_text(encoding="utf-8")
        # Anchored on the newline so the `-CONTRACT_CHECK_SEVERITY = "warnings"`
        # line inside the handoff comment's diff preview is never the one
        # rewritten — the flip must land on the statement, not its
        # documentation.
        flipped = helper_source.replace(
            '\nCONTRACT_CHECK_SEVERITY = "warnings"',
            f'\nCONTRACT_CHECK_SEVERITY = "{severity}"', 1)
        self.assertIn(f'\nCONTRACT_CHECK_SEVERITY = "{severity}"', flipped)
        (scripts / "eval-leanness.py").write_text(flipped, encoding="utf-8")

        subprocess.run([sys.executable, str(scripts / "eval-leanness.py"),
                        "--root", str(root), "--baseline",
                        str(root / ".writ" / "leanness-baseline.json"),
                        "--update-baseline"], capture_output=True, check=True)

        report = Path(report_dir.name) / "report.md"
        result = subprocess.run(
            ["bash", str(scripts / "eval.sh"), "--check=leanness",
             f"--report={report}"],
            capture_output=True, text=True)
        return result, report.read_text(encoding="utf-8")

    def test_shipped_severity_passes_the_gate_on_the_same_tree(self):
        result, report = self._run_leanness_check("warnings")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", report)
        self.assertIn("WARNING [commands/alpha.md]", report)

    def test_flipped_severity_fails_the_gate(self):
        result, report = self._run_leanness_check("structural")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", report)
        self.assertIn("commands/alpha.md", report)
        # The pin holds all the way to the gate: required_skills: is still a
        # non-blocking note in the same flipped run.
        self.assertIn("WARNING [commands/skilled.md → required_skills: ghost-skill]",
                      report)


if __name__ == "__main__":
    unittest.main()
