"""Story 6 of 2026-11-06-lean-story-pipeline: the trial report's verdict.

AC-6.4: the report carries exactly one verdict line, and it is one of
`lean-pipeline: keep`, `lean-pipeline: regress (<what>)`, or
`lean-pipeline: inconclusive`. More escaped Major+ defects in `arm-after`
than in `arm-before` must read `regress`.

The live test reads the spec's `trial-report.md` and skips while it is absent
(the report is written by the trial run). The parser is also tested against
synthetic reports, so the rule is pinned before the report exists.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIRS = (
    REPO_ROOT / ".writ" / "specs" / "2026-11-06-lean-story-pipeline",
    REPO_ROOT / ".writ" / "specs" / "archive" / "2026-11-06-lean-story-pipeline",
)

VERDICT_RE = re.compile(
    r"^lean-pipeline: (keep|inconclusive|regress \((?P<what>[^)]+)\))\s*$"
)
ESCAPED_ROW = "escaped major+ defects"


def verdict_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines()
            if line.strip().startswith("lean-pipeline:")]


def arm_columns(text: str) -> Optional[Tuple[int, int]]:
    """Return the column indexes of arm-before and arm-after in the measures table."""
    for line in text.splitlines():
        cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if "arm-before" in cells and "arm-after" in cells:
            return cells.index("arm-before"), cells.index("arm-after")
    return None


def measure_row(text: str, label: str) -> Optional[Dict[str, str]]:
    cols = arm_columns(text)
    if cols is None:
        return None
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower().startswith(label):
            return {"arm-before": cells[cols[0]], "arm-after": cells[cols[1]]}
    return None


def leading_int(cell: str) -> Optional[int]:
    match = re.match(r"\s*(\d+)", cell)
    return int(match.group(1)) if match else None


def check_report(text: str) -> List[str]:
    """Return the problems with a trial report; empty means it satisfies AC-6.4."""
    problems: List[str] = []
    lines = verdict_lines(text)
    if len(lines) != 1:
        return [f"expected one verdict line, found {len(lines)}"]
    match = VERDICT_RE.match(lines[0])
    if not match:
        return [f"verdict line not an allowed value: {lines[0]!r}"]
    row = measure_row(text, ESCAPED_ROW)
    if row is None:
        return ["no 'Escaped Major+ defects' row with arm-before/arm-after columns"]
    before, after = leading_int(row["arm-before"]), leading_int(row["arm-after"])
    if before is not None and after is not None and after > before:
        if not lines[0].startswith("lean-pipeline: regress ("):
            problems.append(
                f"arm-after has more escaped Major+ defects ({after} > {before}) "
                f"but the verdict is {lines[0]!r}")
    return problems


def _report(before: str, after: str, verdict: str) -> str:
    return (
        "## Results\n\n"
        "| Measure | arm-before | arm-after |\n|---|---|---|\n"
        f"| Escaped Major+ defects | {before} | {after} |\n"
        "| Review iterations | 2 | 1 |\n\n"
        f"## Verdict\n\n{verdict}\n"
    )


class ParserTests(unittest.TestCase):
    def test_keep_with_equal_escapes_passes(self) -> None:
        self.assertEqual(check_report(_report("1", "1", "lean-pipeline: keep")), [])

    def test_regress_value_with_reason_passes(self) -> None:
        text = _report("0", "1", "lean-pipeline: regress (escaped data-loss defect)")
        self.assertEqual(check_report(text), [])

    def test_inconclusive_passes(self) -> None:
        self.assertEqual(check_report(_report("0", "0", "lean-pipeline: inconclusive")), [])

    def test_more_escapes_after_must_read_regress(self) -> None:
        problems = check_report(_report("0", "1 (data loss)", "lean-pipeline: keep"))
        self.assertTrue(any("more escaped" in p for p in problems), problems)

    def test_unknown_verdict_value_fails(self) -> None:
        problems = check_report(_report("0", "0", "lean-pipeline: improve"))
        self.assertTrue(any("not an allowed value" in p for p in problems), problems)

    def test_two_verdict_lines_fail(self) -> None:
        text = _report("0", "0", "lean-pipeline: keep") + "\nlean-pipeline: inconclusive\n"
        self.assertEqual(check_report(text), ["expected one verdict line, found 2"])

    def test_missing_escaped_row_fails(self) -> None:
        text = "| Measure | arm-before | arm-after |\n|---|---|---|\n\nlean-pipeline: keep\n"
        self.assertTrue(check_report(text))

    def test_regress_needs_a_reason(self) -> None:
        problems = check_report(_report("0", "0", "lean-pipeline: regress"))
        self.assertTrue(any("not an allowed value" in p for p in problems), problems)


class LiveReportTests(unittest.TestCase):
    def test_trial_report_verdict(self) -> None:
        report = next((d / "trial-report.md" for d in SPEC_DIRS
                       if (d / "trial-report.md").is_file()), None)
        if report is None:
            self.skipTest("trial-report.md not written yet")
        self.assertEqual(check_report(report.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
