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

REVIEW_RESULT: PAUSE
"""

# Documented format (.writ/docs/drift-report-format.md): plain `> Overall
# Drift:` line, `- **Severity:** Large`, and a title without the word.
DOCUMENTED_LARGE = """# Drift Log

## Story 1: Fixture — Drift Report

> Run: 2026-09-08
> Overall Drift: Large

### Deviations

#### [DEV-001] Replaced the payment provider
- **Severity:** Large
- **Spec said:** Use Stripe
- **Implementation did:** Used a different provider
- **Reason:** Test fixture
- **Resolution:** Pipeline paused — accepted by user
- **Spec amendment:** N/A — deviation accepted as-is
"""

# Title mentions "large" but the entry is Small: not a Large drift.
SMALL_TITLED_LARGE = """# Drift Log

## Story 1: Fixture — Drift Report

> Run: 2026-09-08
> Overall Drift: Small

### Deviations

#### [DEV-001] Large-file handling renamed
- **Severity:** Small
- **Spec said:** readLarge
- **Implementation did:** readBig
- **Reason:** Naming
- **Resolution:** Auto-amended
- **Spec amendment:** Rename readLarge to readBig
"""

# Story prose that mentions PAUSE without carrying a verdict token.
STORY_PAUSE_PROSE = """# Story 1

> **Status:** In Progress

## Acceptance Criteria

- [ ] Given Large drift, when Gate 3 runs, then it emits PAUSE rather than FAIL.
- [ ] The PAUSE is owned by Gate 3.5.

### REVIEW_RESULT: [PASS/FAIL/PAUSE]
"""

STORY_EVAL_PAUSE = """# Story 1

> **Status:** In Progress

### EVALUATION_RESULT: PAUSE
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

    def _check(self, story_text: str, log_text: "str | None" = None,
               review_text: "str | None" = None) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(story_text, encoding="utf-8")
            args = ["check", "--story", str(story)]
            if log_text is not None:
                log = root / "drift-log.md"
                log.write_text(log_text, encoding="utf-8")
                args += ["--drift-log", str(log)]
            if review_text is not None:
                review = root / "review.txt"
                review.write_text(review_text, encoding="utf-8")
                args += ["--review-output", str(review)]
            return _run(args)

    def test_fail_documented_large_format_without_pause(self) -> None:
        code, out = self._check(STORY_NO_PAUSE, DOCUMENTED_LARGE)
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

    def test_fail_severity_large_alone_without_pause(self) -> None:
        log = DOCUMENTED_LARGE.replace("> Overall Drift: Large\n", "")
        code, out = self._check(STORY_NO_PAUSE, log)
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

    def test_fail_bold_overall_drift_large_without_pause(self) -> None:
        log = DOCUMENTED_LARGE.replace(
            "> Overall Drift: Large", "> **Overall Drift:** Large")
        code, out = self._check(STORY_NO_PAUSE, log)
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

    def test_fail_large_in_review_output_without_pause(self) -> None:
        review = "### Drift Analysis\n\n**Overall Drift:** Large\n"
        code, out = self._check(STORY_NO_PAUSE, None, review)
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

    def test_pass_small_entry_with_large_in_title(self) -> None:
        code, out = self._check(STORY_NO_PAUSE, SMALL_TITLED_LARGE)
        self.assertEqual(code, 0, out)
        self.assertEqual(_verdict(out), "pass")

    def test_fail_pause_in_prose_is_not_a_verdict(self) -> None:
        code, out = self._check(STORY_PAUSE_PROSE, DOCUMENTED_LARGE)
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

    def test_fail_pause_in_prose_review_output(self) -> None:
        code, out = self._check(STORY_NO_PAUSE, DOCUMENTED_LARGE,
                                "The pipeline will PAUSE for human decision.\n")
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

    def test_pass_evaluation_result_pause_heading(self) -> None:
        code, out = self._check(STORY_EVAL_PAUSE, DOCUMENTED_LARGE)
        self.assertEqual(code, 0, out)
        self.assertEqual(_verdict(out), "pass")

    def test_pass_bold_review_result_pause(self) -> None:
        code, out = self._check(STORY_NO_PAUSE, DOCUMENTED_LARGE,
                                "**REVIEW_RESULT:** PAUSE\n")
        self.assertEqual(code, 0, out)
        self.assertEqual(_verdict(out), "pass")

    def test_fail_against_real_story_prose(self) -> None:
        story = (REPO_ROOT / ".writ" / "specs" / "archive"
                 / "2026-09-08-phase11-stage2b-mechanize-the-gates"
                 / "user-stories" / "story-1-gate3-review-override.md")
        code, out = self._check(story.read_text(encoding="utf-8"), DOCUMENTED_LARGE)
        self.assertEqual(code, 1, out)
        self.assertIn("large_drift_without_pause", _reasons(out))

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
