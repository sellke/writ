#!/usr/bin/env python3
"""Precision of spec-analyze.py against committed gold labels (Story 3).
[AC-3.4, AC-3.5]

Semantic gold is the labeled JSON, not a live LLM. Structural check plus
schema-check must match expected_verdict / expected_reasons. A clean
fixture must not trip unmeasurable_criterion.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "spec-analyze.py"
FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "spec-analyze"
REQUIRED = ("contradiction", "gap", "ambiguity", "clean")


def _run(spec: Path, findings_path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "check", "--spec", str(spec),
         "--findings", str(findings_path)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def _verdict(out: str) -> str:
    for line in out.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return out.strip()


def _reasons(out: str) -> list[str]:
    return [ln[8:] for ln in out.splitlines() if ln.startswith("reason: ")]


class PrecisionTests(unittest.TestCase):
    def test_four_labeled_classes_exist(self) -> None:
        labels = set()
        for gold_path in FIXTURES.glob("*/gold.json"):
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            labels.add(gold["label"])
        self.assertEqual(labels, set(REQUIRED))

    def test_score_against_gold(self) -> None:
        counts = {label: {"tp": 0, "fp": 0} for label in REQUIRED}
        for gold_path in sorted(FIXTURES.glob("*/gold.json")):
            spec = gold_path.parent
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            label = gold["label"]
            with NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
                json.dump(gold["findings"], handle)
                handle.flush()
                findings_file = Path(handle.name)
            try:
                code, out = _run(spec, findings_file)
            finally:
                findings_file.unlink(missing_ok=True)
            verdict = _verdict(out)
            reasons = _reasons(out)
            if label == "clean":
                self.assertNotIn("unmeasurable_criterion", reasons)
            expected_v = gold["expected_verdict"]
            expected_r = gold["expected_reasons"]
            if verdict == expected_v and reasons == expected_r:
                counts[label]["tp"] += 1
            else:
                counts[label]["fp"] += 1
                self.fail("%s: verdict=%s reasons=%s code=%s\n%s" % (
                    label, verdict, reasons, code, out))
        # Expose totals for What Was Built.
        bits = ["%s %d/%d" % (k, counts[k]["tp"], counts[k]["fp"]) for k in REQUIRED]
        print("PRECISION " + " ".join(bits))
        overall_tp = sum(c["tp"] for c in counts.values())
        overall_fp = sum(c["fp"] for c in counts.values())
        print("PRECISION_OVERALL %d/%d" % (overall_tp, overall_fp))


if __name__ == "__main__":
    unittest.main()
