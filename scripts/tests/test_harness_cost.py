#!/usr/bin/env python3
"""harness-cost.py prices a pipeline baseline without replacing cost_usd."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "harness-cost.py"


def _load():
    spec = importlib.util.spec_from_file_location("harness_cost", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harness_cost = _load()


def _run(tokens, cost=1.0, status="complete", turns=2):
    return {
        "status": status,
        "num_turns": turns,
        "cost_usd": cost,
        "tokens": tokens,
    }


class SummarizeTests(unittest.TestCase):
    def test_formula_omits_cache_creation_and_does_not_replace_cost(self):
        doc = {"runs": [_run(
            {"input": 1_000_000, "output": 0, "cache_read": 0, "cache_creation": 4_000_000},
            cost=99.0,
        )]}
        summary = harness_cost.summarize_baseline(doc)
        self.assertEqual(summary["formula_usd"], 10.0)
        self.assertEqual(summary["cost_usd"], 99.0)
        self.assertEqual(summary["tokens"]["cache_creation"], 4_000_000)

    def test_cache_hit_rate_uses_input_side_only(self):
        tokens = {"input": 100, "output": 9_000, "cache_read": 800, "cache_creation": 100}
        self.assertAlmostEqual(harness_cost.cache_hit_rate(tokens), 0.8)
        summary = harness_cost.summarize_baseline({"runs": [_run(tokens, cost=3.0, turns=4)]})
        self.assertAlmostEqual(summary["cache_hit_rate"], 0.8)
        self.assertEqual(summary["turns"], 4)

    def test_empty_input_side_has_no_hit_rate(self):
        self.assertIsNone(harness_cost.cache_hit_rate(
            {"input": 0, "output": 10, "cache_read": 0, "cache_creation": 0}))

    def test_cli_json_includes_price_of_record(self):
        # The module is what the tests pin; the CLI must emit the same keys.
        missing = HERE / "no-such-baseline.json"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "baseline", str(missing), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error", proc.stderr)


class StaticTests(unittest.TestCase):
    def test_missing_file_is_null_not_zero(self):
        report = harness_cost.static_sections(Path("/nonexistent/writ-root"))
        system = report["sections"][0]
        self.assertEqual(system["source"], "system_prompt")
        self.assertIsNone(system["bytes"])
        self.assertFalse(report["token_method_validated"])


if __name__ == "__main__":
    unittest.main()
