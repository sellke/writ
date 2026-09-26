#!/usr/bin/env python3
"""Tests for scripts/drift-format.py (Story 5 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`). [AC-5.1, AC-5.2]

`summary` roll-up: Story 4 of `2026-09-26-drift-arch-guards`.
[AC-4.1, AC-4.2, AC-4.3, AC-4.4]
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


def _dev(num: str, title: str, severity: str) -> str:
    return (
        "#### [DEV-%s] %s\n"
        "- **Severity:** %s\n"
        "- **Spec said:** X\n"
        "- **Implementation did:** Y\n"
        "- **Reason:** Z\n"
        "- **Resolution:** R\n"
        "- **Spec amendment:** A\n" % (num, title, severity)
    )


ROLLUP_LOG = (
    "# Drift Log\n\n> Spec: .writ/specs/x/\n> Created: 2026-09-20\n\n---\n\n"
    "## Story 1: Old Story — Drift Report\n\n> Run: 2026-09-20\n"
    "> Overall Drift: Medium\n\n### Deviations\n\n"
    + _dev("001", "Old medium change", "Medium")
    + "\n---\n\n"
    "## Story 2: Retry Story — Drift Report\n\n> Run: 2026-09-26\n"
    "> Overall Drift: Medium\n\n### Deviations\n\n"
    + _dev("002", "Renamed helper", "Small")
    + "\n"
    + _dev("003", "Added retry wrapper", "Medium")
    + "\n---\n\n"
    "## Story 3: API Story — Drift Report\n\n> Run: 2026-09-27\n"
    "> Overall Drift: Large\n\n### Deviations\n\n"
    + _dev("004", "GraphQL instead of REST", "Large")
    + "\n"
    + _dev("005", "Second medium", "Medium")
)

UNDATED_LOG = (
    "# Drift Log\n\n---\n\n"
    "## Story 7: Undated — Drift Report\n\n> Overall Drift: Medium\n\n"
    "### Deviations\n\n" + _dev("001", "Undated medium", "Medium")
)


class DriftSummaryTests(unittest.TestCase):
    """`summary` roll-up (Story 4 of `2026-09-26-drift-arch-guards`).
    [AC-4.1, AC-4.2]"""

    def _summary(self, log_text: "str | None", *extra: str) -> tuple[int, str]:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "drift-log.md"
            if log_text is not None:
                log.write_text(log_text, encoding="utf-8")
            return _run(["summary", "--drift-log", str(log), *extra])

    def test_counts_and_headlines_in_file_order(self) -> None:
        code, out = self._summary(ROLLUP_LOG)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "pass",
            "medium: DEV-001 Old medium change (Story 1)",
            "medium: DEV-003 Added retry wrapper (Story 2)",
            "large: DEV-004 GraphQL instead of REST (Story 3)",
            "medium: DEV-005 Second medium (Story 3)",
            "drift-format summary: 1 small, 3 medium, 1 large",
        ])

    def test_since_keeps_sections_on_or_after_date(self) -> None:
        code, out = self._summary(ROLLUP_LOG, "--since", "2026-09-26")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "pass",
            "medium: DEV-003 Added retry wrapper (Story 2)",
            "large: DEV-004 GraphQL instead of REST (Story 3)",
            "medium: DEV-005 Second medium (Story 3)",
            "drift-format summary: 1 small, 2 medium, 1 large since 2026-09-26",
        ])

    def test_since_after_every_run_counts_zero(self) -> None:
        code, out = self._summary(ROLLUP_LOG, "--since", "2026-10-01")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "pass",
            "drift-format summary: 0 small, 0 medium, 0 large since 2026-10-01",
        ])

    def test_section_without_run_date_kept_without_since(self) -> None:
        code, out = self._summary(UNDATED_LOG)
        self.assertEqual(code, 0, out)
        self.assertIn("medium: DEV-001 Undated medium (Story 7)", out.splitlines())
        self.assertEqual(out.splitlines()[-1],
                         "drift-format summary: 0 small, 1 medium, 0 large")

    def test_section_without_run_date_dropped_with_since(self) -> None:
        code, out = self._summary(UNDATED_LOG, "--since", "2026-01-01")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "pass",
            "drift-format summary: 0 small, 0 medium, 0 large since 2026-01-01",
        ])

    def test_missing_log_passes_with_zero_counts(self) -> None:
        code, out = self._summary(None, "--since", "2026-09-26")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "pass",
            "drift-format summary: 0 small, 0 medium, 0 large since 2026-09-26",
        ])

    def test_unreadable_log_directory_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            code, out = _run(["summary", "--drift-log", tmp])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], "unverifiable")
        self.assertIn("drift_log_unreadable", _reasons(out))
        self.assertTrue(out.splitlines()[-1].startswith("drift-format summary:"))

    def test_undecodable_log_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "drift-log.md"
            log.write_bytes(b"\xff\xfe\x00bad")
            code, out = _run(["summary", "--drift-log", str(log)])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], "unverifiable")
        self.assertIn("drift_log_unreadable", _reasons(out))

    def test_malformed_since_is_exit_2(self) -> None:
        for bad in ("2026-9-26", "yesterday", "2026-13-01"):
            code, _out = self._summary(ROLLUP_LOG, "--since", bad)
            self.assertEqual(code, 2, bad)

    def test_summary_never_fails(self) -> None:
        code, out = self._summary(MALFORMED)
        self.assertEqual(code, 0, out)
        self.assertNotIn("fail", out.splitlines())


class DriftSummaryWiringTests(unittest.TestCase):
    """implement-spec Step 4.2 roll-up wiring. [AC-4.3, AC-4.4]"""

    def test_step_4_2_runs_summary_since_start_and_is_report_only(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-spec.md").read_text(encoding="utf-8")
        start = text.index("#### Step 4.2:")
        end = text.index("\n---\n", start)
        step = text[start:end]
        self.assertIn("scripts/drift-format.py summary --drift-log", step)
        self.assertIn("--since", step)
        self.assertIn("startedAt", step)
        self.assertGreaterEqual(step.count("Drift this run:"), 2,
                                "instruction and example report both carry the line")
        self.assertIn(
            "never changes the checker verdict, the banner, or any story status",
            step,
        )


if __name__ == "__main__":
    unittest.main()
