#!/usr/bin/env python3
"""Tests for scripts/drift-format.py (Story 5 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`). [AC-5.1, AC-5.2]
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "drift-format.py"

WELL_FORMED = """# Drift Log

## Story 1: Fixture — Drift Report

> Run: 2026-09-08
> Overall Drift: Large

### Deviations

#### [DEV-001] Something large
- **Severity:** Large
- **Spec said:** Stay inside the contract
- **Implementation did:** Left the contract
- **Reason:** Test fixture
- **Resolution:** Pipeline paused — accepted by user
- **Spec amendment:** N/A — deviation accepted as-is
"""

MALFORMED = """# Drift Log

#### [DEV-001] Missing fields
- **Severity:** Small
- **Spec said:** X
"""

STORY = """# Story 1

> **Status:** In Progress

PAUSE
"""

STORY_NO_PAUSE = """# Story 1

> **Status:** In Progress
"""


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def _verdict(out: str) -> str:
    for line in out.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return out


def _reasons(out: str) -> list[str]:
    return [ln[8:] for ln in out.splitlines() if ln.startswith("reason: ")]


class DriftFormatTests(unittest.TestCase):
    def test_pass_well_formed_large_with_pause(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            log = root / "drift-log.md"
            story.write_text(STORY, encoding="utf-8")
            log.write_text(WELL_FORMED, encoding="utf-8")
            code, out = _run(["check", "--story", str(story), "--drift-log", str(log)])
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict(out), "pass")
            self.assertNotIn("accept", out.splitlines()[0])
            self.assertNotIn("reject", out)
            self.assertNotIn("modify-spec", out)

    def test_fail_malformed_entry(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            log = root / "drift-log.md"
            story.write_text(STORY, encoding="utf-8")
            log.write_text(MALFORMED, encoding="utf-8")
            code, out = _run(["check", "--story", str(story), "--drift-log", str(log)])
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict(out), "fail")
            self.assertIn("malformed_entry", _reasons(out))

    def test_fail_large_without_pause(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            log = root / "drift-log.md"
            story.write_text(STORY_NO_PAUSE, encoding="utf-8")
            log.write_text(WELL_FORMED, encoding="utf-8")
            code, out = _run(["check", "--story", str(story), "--drift-log", str(log)])
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict(out), "fail")
            self.assertIn("large_drift_without_pause", _reasons(out))

    def test_pass_large_pause_in_review_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            log = root / "drift-log.md"
            review = root / "review.txt"
            story.write_text(STORY_NO_PAUSE, encoding="utf-8")
            log.write_text(WELL_FORMED, encoding="utf-8")
            review.write_text("REVIEW_RESULT: PAUSE\n", encoding="utf-8")
            code, out = _run([
                "check", "--story", str(story),
                "--drift-log", str(log),
                "--review-output", str(review),
            ])
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict(out), "pass")

    def test_unverifiable_no_log_no_large(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(STORY_NO_PAUSE, encoding="utf-8")
            code, out = _run(["check", "--story", str(story)])
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertIn("no_drift_signal", _reasons(out))

    def test_usage_without_story_is_exit_2(self) -> None:
        code, _out = _run(["check"])
        self.assertEqual(code, 2)

    def test_gate_3_5_wiring(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 3.5:")
        end = text.index("#### Gate 4:", start)
        gate = text[start:end]
        self.assertIn("scripts/drift-format.py check", gate)
        self.assertIn("⚠️ DEGRADED", gate)
        self.assertIn("  - id: gate3_5_drift\n    script: scripts/drift-format.py", text)

    def test_visual_qa_has_no_percentage_thresholds(self) -> None:
        text = (REPO_ROOT / "agents" / "visual-qa-agent.md").read_text(encoding="utf-8")
        self.assertNotIn("85", text)
        self.assertNotIn("70", text)
        for word in ("PASS", "SOFT PASS", "FAIL"):
            self.assertIn(word, text)


if __name__ == "__main__":
    unittest.main()
