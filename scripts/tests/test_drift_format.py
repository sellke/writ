#!/usr/bin/env python3
"""Tests for scripts/drift-format.py (Story 5 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`). [AC-5.1, AC-5.2]

`summary` roll-up: Story 4 of `2026-09-26-drift-arch-guards`.
[AC-4.1, AC-4.2, AC-4.3, AC-4.4]
"""

from __future__ import annotations

import os
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
        # No Large signal fired. The fixture sits outside a git work tree, so
        # its Auto-amended entry is the one thing left unchecked.
        self.assertEqual(_reasons(out), ["auto_amend_unverifiable"])

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


# --- Phase 15 retro F1: an `Auto-amended` entry must amend spec-lite.md ------

_GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="t@example.com",
                GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="t@example.com")


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
                          capture_output=True, text=True, env=_GIT_ENV)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _story_section(story: int, *entries: str) -> str:
    return ("\n---\n\n## Story %d: Fixture — Drift Report\n\n> Run: 2026-10-30\n"
            "> Overall Drift: Small\n\n### Deviations\n\n%s" % (story, "\n".join(entries)))


def _entry(num: str, resolution: str, severity: str = "Small") -> str:
    return (
        "#### [DEV-%s] Renamed a helper\n"
        "- **Severity:** %s\n"
        "- **Spec said:** validateInput\n"
        "- **Implementation did:** validateRegistrationData\n"
        "- **Reason:** Naming only\n"
        "- **Resolution:** %s\n"
        "- **Spec amendment:** Rename validateInput in spec-lite.md\n" % (num, severity, resolution)
    )


AUTO = "Auto-amended (Small)."
LOG_HEADER = "# Drift Log\n\n> Spec: .writ/specs/x/\n> Created: 2026-10-30\n"


class AutoAmendTests(unittest.TestCase):
    """`auto_amend_unapplied`: a story whose drift entries say `Auto-amended`
    must change spec-lite.md, in its own commits or uncommitted at Gate 3.5."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _git(self.repo, "init", "-q")
        self.spec = self.repo / ".writ" / "specs" / "2026-10-30-x"
        self.stories = self.spec / "user-stories"
        self.stories.mkdir(parents=True)
        self.spec_lite = self.spec / "spec-lite.md"
        self.spec_lite.write_text("# Spec Lite\n\nUse validateInput.\n", encoding="utf-8")
        self.log = self.spec / "drift-log.md"
        self.log.write_text(LOG_HEADER, encoding="utf-8")
        self.story1 = self._story(1)
        self.story2 = self._story(2)
        _commit(self.repo, "docs(specs): author the spec")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _story(self, num: int) -> Path:
        path = self.stories / ("story-%d-fixture.md" % num)
        path.write_text("# Story %d: Fixture\n\n> **Status:** Not Started\n" % num,
                        encoding="utf-8")
        return path

    def _log(self, *sections: str) -> None:
        self.log.write_text(LOG_HEADER + "".join(sections), encoding="utf-8")

    def _work(self, story: Path, *, amend: bool) -> None:
        """What /implement-story does by Gate 3.5: code, story file, and,
        when `amend`, the spec-lite.md amendment."""
        (self.repo / "app.py").write_text("x = %r\n" % story.name, encoding="utf-8")
        with story.open("a", encoding="utf-8") as fh:
            fh.write("\n## What Was Built\n")
        if amend:
            with self.spec_lite.open("a", encoding="utf-8") as fh:
                fh.write("Use validateRegistrationData.\n")

    def _check(self, story: Path) -> "tuple[int, str]":
        return _run(["check", "--story", str(story), "--drift-log", str(self.log)])

    def test_fail_when_story_commit_leaves_spec_lite_unchanged(self) -> None:
        self._log(_story_section(1, _entry("001", AUTO)))
        self._work(self.story1, amend=False)
        _commit(self.repo, "feat: story 1 (Story 1)")
        code, out = self._check(self.story1)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.splitlines()[0], "fail")
        self.assertEqual(_reasons(out), ["auto_amend_unapplied"])
        self.assertIn("DEV-001", out.splitlines()[-1])

    def test_pass_when_story_commit_changes_spec_lite(self) -> None:
        self._log(_story_section(1, _entry("001", AUTO)))
        self._work(self.story1, amend=True)
        _commit(self.repo, "feat: story 1 (Story 1)")
        code, out = self._check(self.story1)
        self.assertEqual((code, out.splitlines()[0]), (0, "pass"), out)

    def test_mutation_reverting_the_amendment_flips_pass_to_fail(self) -> None:
        """Gate 3.5 runs before the story commit: the amendment is uncommitted.
        Undo it and the same check must fail."""
        self._log(_story_section(1, _entry("001", AUTO), _entry("002", AUTO)))
        self._work(self.story1, amend=True)
        code, out = self._check(self.story1)
        self.assertEqual((code, out.splitlines()[0]), (0, "pass"), out)
        _git(self.repo, "checkout", "--", str(self.spec_lite))
        code, out = self._check(self.story1)
        self.assertEqual(code, 1, out)
        self.assertIn("auto_amend_unapplied", _reasons(out))
        self.assertIn("DEV-001, DEV-002", out.splitlines()[-1])

    def test_spec_scaffold_commit_does_not_count_as_the_amendment(self) -> None:
        """spec-lite.md was added with the story file; that is create-spec's
        commit, not the story's."""
        self._log(_story_section(1, _entry("001", AUTO)))
        _commit(self.repo, "docs: log drift")
        code, out = self._check(self.story1)
        self.assertEqual(code, 1, out)
        self.assertIn("auto_amend_unapplied", _reasons(out))

    def test_other_storys_amendment_does_not_count(self) -> None:
        self._log(_story_section(1, _entry("001", AUTO)))
        self._work(self.story2, amend=True)
        _commit(self.repo, "feat: story 2 (Story 2)")
        self._work(self.story1, amend=False)
        _commit(self.repo, "feat: story 1 (Story 1)")
        code, out = self._check(self.story1)
        self.assertEqual(code, 1, out)
        self.assertIn("auto_amend_unapplied", _reasons(out))

    def test_only_this_storys_entries_are_checked(self) -> None:
        self._log(_story_section(1, _entry("001", AUTO)))
        self._work(self.story2, amend=False)
        _commit(self.repo, "feat: story 2 (Story 2)")
        code, out = self._check(self.story2)
        self.assertEqual((code, out.splitlines()[0]), (0, "pass"), out)

    def test_flagged_for_review_needs_no_amendment(self) -> None:
        self._log(_story_section(1, _entry("001", "Flagged for review", "Medium")))
        self._work(self.story1, amend=False)
        _commit(self.repo, "feat: story 1 (Story 1)")
        code, out = self._check(self.story1)
        self.assertEqual((code, out.splitlines()[0]), (0, "pass"), out)

    def test_format_failure_and_unapplied_amendment_are_both_reported(self) -> None:
        broken = _entry("002", AUTO).replace("- **Reason:** Naming only\n", "")
        self._log(_story_section(1, _entry("001", AUTO), broken))
        code, out = self._check(self.story1)
        self.assertEqual(code, 1, out)
        self.assertEqual(_reasons(out), ["malformed_entry", "auto_amend_unapplied"])

    def test_outside_a_git_work_tree_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            story = Path(tmp) / "story-1-fixture.md"
            log = Path(tmp) / "drift-log.md"
            story.write_text("# Story 1: Fixture\n", encoding="utf-8")
            log.write_text(LOG_HEADER + _story_section(1, _entry("001", AUTO)),
                           encoding="utf-8")
            code, out = _run(["check", "--story", str(story), "--drift-log", str(log)])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], "unverifiable")
        self.assertEqual(_reasons(out), ["auto_amend_unverifiable"])

    def test_retro_proof_why_command_story_1(self) -> None:
        """The Phase 15 retro's F1 proof: Story 1 logged two Auto-amended
        entries and its commit left spec-lite.md unchanged."""
        rel = Path("2026-10-25-why-command")
        for root in (REPO_ROOT / ".writ" / "specs", REPO_ROOT / ".writ" / "specs" / "archive"):
            if (root / rel / "drift-log.md").is_file():
                spec = root / rel
                break
        else:
            self.skipTest("why-command spec not in this checkout")
        code, out = _run(["check", "--story",
                          str(spec / "user-stories" / "story-1-why-command-file.md"),
                          "--drift-log", str(spec / "drift-log.md")])
        self.assertEqual(code, 1, out)
        self.assertIn("auto_amend_unapplied", _reasons(out))


if __name__ == "__main__":
    unittest.main()
