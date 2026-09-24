#!/usr/bin/env python3
"""Fixture tests for scripts/lean-decision.py (Story 5 of
2026-09-24-flagged-harness-cuts, task 5.1).

`decide` reads a control and a lean `pipeline-baseline-v1` file and prints one
verdict: keep, null, quality_miss, or compare_error. Only a full sample (four
stories x 2 runs per arm) with every exit-criteria row N/N and a strictly
lower lean `cost_usd` is a keep. Nothing here spawns a subprocess or calls a
model; the run record is a trimmed copy of a real one from
.writ/eval/baselines/2026-09-07-claude-fable-5-1.json.
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "lean-decision.py"
_spec = importlib.util.spec_from_file_location("lean_decision", SCRIPT)
ld = importlib.util.module_from_spec(_spec)
sys.modules["lean_decision"] = ld
_spec.loader.exec_module(ld)  # type: ignore[union-attr]

MODEL = "claude-opus-5-5"

# Trimmed from runs[0] of the 2026-09-07 Fable 5.1 baseline: same keys and
# nesting, argv/rederivation/test-file detail dropped.
REAL_RECORD = {
    "story_id": "2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow",
    "run": 1,
    "status": "complete",
    "reason": None,
    "started_at": "2026-09-07T22:19:34Z",
    "isolation": {"reachable_commits": 1, "expected": 1, "asserted": True, "answer_scrub_asserted": True},
    "writ": {"source": "overlay", "commit": "e5792ceec48c57c11709053b5b72186f1a2d8081", "dirty": True,
             "checkout_manifest_version": "e1a3fd1", "manifest_diff_count": 156},
    "inputs": "parent",
    "deps": {"seconds": 5.724, "exit": 0},
    "invocation": {"driver": "claude", "argv": ["claude", "-p", "/implement-story <story>"],
                   "model": "claude-fable-5-1", "model_resolved": "claude-fable-5-1",
                   "claude_version": "2.1.260", "permission_mode": "bypass", "api_key_source": "none"},
    "wall_clock_s": 3376.767,
    "num_turns": 91,
    "tokens": {"input": 182, "output": 84678, "cache_read": 13583644, "cache_creation": 232751},
    "tokens_main_thread": {"input": 350, "output": 1481, "cache_read": 25828655, "cache_creation": 495345},
    "cost_usd": 26.385244000000007,
    "interrupts": {"ask_user_question": 0, "status_blocked": 4},
    "review_iterations": 0,
    "tests": {"suite": {"passed": 3055, "total": 3055, "reason": None},
              "original": {"passed": 0, "total": 0, "reason": "suite failed to run (2 failed suites)", "files": []}},
    "gates": {"gate4_tests": {"verdict": "PASS", "source": "tool_result", "rederived": "pass",
                              "integrity": "unverifiable"}},
    "rederivation": {},
    "exit_criteria": {"reported": "COMPLETE", "rederived": "met",
                      "rederived_by": "implement-story success predicates"},
    "yuss_head_unchanged": True,
}

STORY_IDS = (
    "2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow",
    "2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link",
    "2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption",
    "2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard",
)


def selection_entry(i: int, story_id: str) -> dict:
    folder, stem = story_id.split("/")
    return {"story_path": ".writ/specs/archive/%s/user-stories/%s.md" % (folder, stem),
            "spec_folder": folder, "story_id": story_id, "story_commit": "%040x" % (i + 1),
            "parent_sha": "%040x" % (i + 100), "parent_is_merge": False, "surface_class": "ui",
            "eligible_classes": ["ui"], "test_files": [], "criteria_values": {}}


def record(story_id: str, run: int, cost: float, lean, met: bool = True) -> dict:
    rec = copy.deepcopy(REAL_RECORD)
    rec["story_id"], rec["run"], rec["cost_usd"] = story_id, run, cost
    rec["invocation"]["model"] = rec["invocation"]["model_resolved"] = MODEL
    rec["writ"]["dirty"] = False
    if lean is not None:
        rec["writ"]["harness_lean"] = lean
    if not met:
        rec["exit_criteria"]["rederived"] = "not_met"
    return rec


def baseline(stories: int = 4, runs: int = 2, cost: float = 20.0, lean=False, model: str = MODEL) -> dict:
    ids = STORY_IDS[:stories]
    return {
        "schema": "pipeline-baseline-v1", "model": model, "generated_at": "2026-09-25T00:00:00Z",
        "yuss_head": "7c2d0430c12fd5f2a6ebe11eb6ece5f03ee41029", "runs_per_story": runs,
        "criteria": {"status_required": "Completed"},
        "selection": [selection_entry(i, sid) for i, sid in enumerate(STORY_IDS)],
        "excluded": [], "rejection_tally": {},
        "runs": [record(sid, n, cost, lean) for sid in ids for n in range(1, runs + 1)],
    }


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "control").mkdir()
        (self.root / "lean").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, arm: str, doc) -> Path:
        path = self.root / arm / ("2026-09-25-%s.json" % MODEL)
        path.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
        return path

    def decide(self, control: dict, lean: dict, fmt: str = "json") -> tuple:
        c, l = self.write("control", control), self.write("lean", lean)
        return self.run_main(["decide", "--control", str(c), "--lean", str(l), "--format", fmt])

    @staticmethod
    def run_main(argv: list) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = ld.main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
        return code, out.getvalue(), err.getvalue()

    def assert_error(self, control, lean, needle: str) -> dict:
        code, out, err = self.decide(control, lean)
        self.assertEqual(code, 0, err)
        doc = json.loads(out)
        self.assertEqual(doc["verdict"], "compare_error")
        self.assertTrue(any(needle in r for r in doc["reasons"]), doc["reasons"])
        return doc

    def verdict(self, control: dict, lean: dict) -> dict:
        code, out, err = self.decide(control, lean)
        self.assertEqual(code, 0, err)
        return json.loads(out)


class ConstantsTest(unittest.TestCase):
    def test_full_sample_is_four_stories_by_two(self) -> None:
        self.assertEqual(ld.FULL_SAMPLE_STORIES, 4)
        self.assertEqual(ld.FULL_SAMPLE_RUNS, 2)
        self.assertEqual(ld.VERDICTS, ("keep", "null", "quality_miss", "compare_error"))


class KeepTest(Case):
    def test_full_sample_all_met_and_cheaper_is_keep(self) -> None:
        doc = self.verdict(baseline(cost=20.0), baseline(cost=19.0, lean=True))
        self.assertEqual(doc["verdict"], "keep")
        self.assertEqual(doc["model"], MODEL)
        self.assertEqual(doc["sample"], {"stories": 4, "runs_per_story": 2, "full": True})
        self.assertAlmostEqual(doc["cost_usd"]["control"], 160.0)
        self.assertAlmostEqual(doc["cost_usd"]["lean"], 152.0)
        self.assertAlmostEqual(doc["cost_usd"]["delta"], -8.0)
        self.assertTrue(all(r["control"] == "2/2" and r["lean"] == "2/2" for r in doc["exit_criteria"]))


class NullTest(Case):
    def test_full_sample_not_cheaper_is_null(self) -> None:
        for lean_cost in (20.0, 21.0):
            doc = self.verdict(baseline(cost=20.0), baseline(cost=lean_cost, lean=True))
            self.assertEqual(doc["verdict"], "null")
            self.assertTrue(any("not cheaper" in r for r in doc["reasons"]), doc["reasons"])

    def test_reduced_sample_cheaper_is_still_null(self) -> None:
        doc = self.verdict(baseline(stories=1, cost=20.0), baseline(stories=1, cost=5.0, lean=True))
        self.assertEqual(doc["verdict"], "null")
        self.assertIn("reduced sample: keep requires 4 stories × 2", doc["reasons"][0])
        self.assertEqual(doc["sample"], {"stories": 1, "runs_per_story": 2, "full": False})

    def test_three_stories_or_one_run_each_is_reduced(self) -> None:
        for stories, runs in ((3, 2), (4, 1)):
            doc = self.verdict(baseline(stories=stories, runs=runs, cost=20.0),
                               baseline(stories=stories, runs=runs, cost=1.0, lean=True))
            self.assertEqual(doc["verdict"], "null", (stories, runs))
            self.assertFalse(doc["sample"]["full"])

    def test_text_output_names_price_of_record_and_formula_as_not_deciding(self) -> None:
        code, out, err = self.decide(baseline(stories=1), baseline(stories=1, cost=19.0, lean=True), fmt="text")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("verdict: null\n"), out)
        self.assertIn("reduced sample: keep requires 4 stories × 2", out)
        self.assertIn("cost_usd (price of record)", out)
        self.assertIn("does not decide", out)
        self.assertIn("2/2", out)


class QualityMissTest(Case):
    def test_a_lean_row_under_n_of_n_is_quality_miss_even_when_cheaper(self) -> None:
        lean = baseline(cost=1.0, lean=True)
        lean["runs"][3]["exit_criteria"]["rederived"] = "not_met"
        doc = self.verdict(baseline(), lean)
        self.assertEqual(doc["verdict"], "quality_miss")
        row = next(r for r in doc["exit_criteria"] if r["story_id"] == STORY_IDS[1])
        self.assertEqual((row["control"], row["lean"]), ("2/2", "1/2"))

    def test_a_control_row_under_n_of_n_is_quality_miss(self) -> None:
        control = baseline(stories=1)
        control["runs"][0]["exit_criteria"]["rederived"] = "not_met"
        doc = self.verdict(control, baseline(stories=1, lean=True))
        self.assertEqual(doc["verdict"], "quality_miss")

    def test_quality_miss_still_reports_both_arms_cost(self) -> None:
        lean = baseline(stories=1, cost=5.0, lean=True)
        lean["runs"][0]["exit_criteria"]["rederived"] = "not_met"
        doc = self.verdict(baseline(stories=1, cost=20.0), lean)
        self.assertEqual(doc["verdict"], "quality_miss")
        self.assertAlmostEqual(doc["cost_usd"]["control"], 40.0)
        self.assertAlmostEqual(doc["cost_usd"]["lean"], 10.0)
        code, out, err = self.decide(baseline(stories=1, cost=20.0), lean, fmt="text")
        self.assertIn("verdict: quality_miss", out)
        self.assertIn("cost_usd (price of record, informational)", out)

    def test_attempted_runs_that_stopped_early_are_quality(self) -> None:
        # The model ran the story and stopped: an execution error, max turns,
        # or the dollar budget. That is the arm's quality, not the harness.
        for status, reason in (("error", "error_during_execution"), ("error", "error_max_turns"),
                               ("budget", "error_max_budget_usd")):
            lean = baseline(stories=1, lean=True)
            rec = lean["runs"][1]
            rec["status"], rec["reason"] = status, reason
            rec["exit_criteria"]["rederived"] = "not_met"
            doc = self.verdict(baseline(stories=1), lean)
            self.assertEqual(doc["verdict"], "quality_miss", (status, reason))


class CompareErrorTest(Case):
    def test_mismatched_story_id(self) -> None:
        lean = baseline(stories=1, cost=1.0, lean=True)
        for rec in lean["runs"]:
            rec["story_id"] = STORY_IDS[2]
        self.assert_error(baseline(stories=1), lean, "story selection")

    def test_mismatched_run_counts(self) -> None:
        self.assert_error(baseline(stories=1, runs=2), baseline(stories=1, runs=1, cost=1.0, lean=True),
                          "story selection")

    def test_mismatched_parent_for_the_same_story(self) -> None:
        lean = baseline(stories=1, lean=True)
        lean["selection"][0]["parent_sha"] = "f" * 40
        self.assert_error(baseline(stories=1), lean, "parent_sha")

    def test_missing_file(self) -> None:
        c = self.write("control", baseline())
        code, out, err = self.run_main(["decide", "--control", str(c), "--lean",
                                        str(self.root / "nope.json"), "--format", "json"])
        self.assertEqual(code, 0, err)
        doc = json.loads(out)
        self.assertEqual(doc["verdict"], "compare_error")
        self.assertTrue(any("nope.json" in r for r in doc["reasons"]), doc["reasons"])

    def test_unreadable_json(self) -> None:
        self.assert_error(baseline(), "{not json", "not valid JSON")

    def test_wrong_schema(self) -> None:
        lean = baseline(lean=True)
        lean["schema"] = "something-else"
        self.assert_error(baseline(), lean, "pipeline-baseline-v1")

    def test_empty_runs(self) -> None:
        lean = baseline(lean=True)
        lean["runs"] = []
        self.assert_error(baseline(), lean, "empty runs")

    def test_model_mismatch(self) -> None:
        self.assert_error(baseline(model="claude-fable-5-1"), baseline(cost=1.0, lean=True), "model")

    def test_lean_file_holding_control_runs(self) -> None:
        # Arguments swapped, or `run` without --lean into the lean file.
        self.assert_error(baseline(), baseline(cost=1.0, lean=False), "harness_lean")
        self.assert_error(baseline(lean=True), baseline(cost=1.0, lean=True), "harness_lean")

    def test_lean_file_records_must_carry_the_arm(self) -> None:
        # A record written before the lean arm existed is a control run.
        self.assert_error(baseline(), baseline(cost=1.0, lean=None), "harness_lean")

    def test_unpriced_run_with_every_row_met(self) -> None:
        lean = baseline(cost=1.0, lean=True)
        lean["runs"][0]["cost_usd"] = None
        self.assert_error(baseline(), lean, "cost_usd")


class SetupFailureTest(Case):
    def _fail(self, arm: str, **fields) -> dict:
        control, lean = baseline(stories=1), baseline(stories=1, cost=1.0, lean=True)
        rec = (control if arm == "control" else lean)["runs"][1]
        rec["exit_criteria"]["rederived"] = None
        rec.update(fields)
        return self.assert_error(control, lean, "setup failure: %s run 2" % STORY_IDS[0])

    def test_record_without_a_writ_block(self) -> None:
        self._fail("lean", status="error", reason="fetch_failed", writ=None)
        self._fail("control", status="error", reason=None, writ=None)

    def test_pre_model_reasons(self) -> None:
        for reason in ("fetch_failed", "isolation_failed", "inputs_missing", "answer_leak",
                       "overlay_failed", "lean_overlay_failed"):
            doc = self._fail("lean", status="error", reason=reason)
            self.assertTrue(any(reason in r for r in doc["reasons"]), doc["reasons"])

    def test_timeout_and_missing_result_event(self) -> None:
        self._fail("control", status="timeout", reason=None)
        self._fail("lean", status="error", reason="no_result_event")

    def test_unrecognized_error_is_not_counted_as_quality(self) -> None:
        self._fail("lean", status="error", reason="something_new")


class ProvenanceTest(Case):
    def test_arms_on_different_writ_commits(self) -> None:
        lean = baseline(cost=1.0, lean=True)
        for rec in lean["runs"]:
            rec["writ"]["commit"] = "f" * 40
        doc = self.assert_error(baseline(), lean, "writ.commit")
        self.assertTrue(any("f" * 40 in r and REAL_RECORD["writ"]["commit"] in r for r in doc["reasons"]))

    def test_dirty_overlay_in_either_arm(self) -> None:
        for arm in ("control", "lean"):
            control, lean = baseline(), baseline(cost=1.0, lean=True)
            (control if arm == "control" else lean)["runs"][0]["writ"]["dirty"] = True
            self.assert_error(control, lean, "dirty")


class UsageTest(Case):
    def test_missing_argument_is_exit_2(self) -> None:
        code, _, _ = self.run_main(["decide", "--control", "x.json"])
        self.assertEqual(code, 2)

    def test_no_subcommand_is_exit_2(self) -> None:
        code, _, _ = self.run_main([])
        self.assertEqual(code, 2)


class StdlibOnlyTest(unittest.TestCase):
    def test_imports_are_stdlib(self) -> None:
        import ast
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        allowed = {"__future__", "argparse", "collections", "importlib", "json", "sys", "pathlib", "typing"}
        self.assertLessEqual(names, allowed)


if __name__ == "__main__":
    unittest.main()
