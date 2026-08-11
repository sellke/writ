#!/usr/bin/env python3
"""Tests for eval-leanness.py's contract instrumentation (spec:
2026-08-11-governor-instrumentation).

**The bound justification (Story 1).** The 16-row matrix from
`sub-specs/technical-spec.md` -> "Test matrix for the bound justification".
Rows 4, 5 and 7 are the acceptance bar (grow -> justify -> quiet; grow
further -> warns again; down is free); row 8 proves the per-metric
independence the old per-surface read lacked; row 10 is the direct
regression test against the permanent mute.

`eval-leanness.py` has a hyphen in its filename, so it is loaded by path via
`importlib.util.spec_from_file_location` — the established recipe in
`test_archive_sweep.py`, `test_spec_status.py` and `test_story_deps.py`.
Tests are `unittest.TestCase` classes (as in `test_story_context.py` and
`test_story_deps.py`) so the file runs under both `python3 -m unittest` and
`python3 -m pytest`.
"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import io
import json
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


if __name__ == "__main__":
    unittest.main()
