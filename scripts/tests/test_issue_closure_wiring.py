#!/usr/bin/env python3
"""Wiring assertions for Story 2 of `2026-09-26-arch-lint-and-follow-ups`:
the issue-closure convention.

An issue file is closed exactly when it has a line that is exactly
`## Resolution`. The rule lives in command and skill prose, not code, so these
tests pin the prose where each surface applies it:

- `commands/status.md` Step 5 skips a closed issue before the age and
  `spec_ref` checks, so it never reaches NEEDS TRIAGE `[AC-2.1]`.
- `status.md` Step 8 and `skills/project-context-snapshot/SKILL.md` count
  open issues only, in the same words as Step 5 `[AC-2.2]`.
- `commands/create-issue.md` says how to close an issue `[AC-2.3]`.
- `status.md` pays for the edit inside its byte budget `[AC-2.4]`.

Run: python3 scripts/tests/test_issue_closure_wiring.py
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

STATUS = REPO_ROOT / "commands" / "status.md"
SNAPSHOT_SKILL = REPO_ROOT / "skills" / "project-context-snapshot" / "SKILL.md"
CREATE_ISSUE = REPO_ROOT / "commands" / "create-issue.md"
GOVERNOR_TEST = REPO_ROOT / "scripts" / "tests" / "test_governor_enforcement.py"
ISSUES = REPO_ROOT / ".writ" / "issues"
FIXTURE_SCAN_ISSUE = ISSUES / "bugs" / "2026-09-26-ac-trace-scans-fixture-ac-tokens.md"

RULE = "a line exactly `## Resolution`"
STATUS_BYTE_CEILING = 24211 + 300


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def is_closed(text: str) -> bool:
    """The rule the prose states, in the form `grep -x` applies it."""
    return any(line == "## Resolution" for line in text.splitlines())


class ClosedMeansResolutionTests(unittest.TestCase):
    """[AC-2.1] Only a whole line closes an issue."""

    def test_the_whole_line_closes(self) -> None:
        self.assertTrue(is_closed("# Bug\n\n## Resolution\n\nFixed on main.\n"))

    def test_a_dated_heading_does_not_close(self) -> None:
        self.assertFalse(is_closed("## Resolution (2026-09-25)\n"))

    def test_the_heading_inside_a_longer_line_does_not_close(self) -> None:
        self.assertFalse(is_closed("Append `## Resolution` when fixed.\n"))
        self.assertFalse(is_closed("```markdown ## Resolution\n"))

    def test_the_fixture_scan_issue_is_closed(self) -> None:
        self.assertTrue(is_closed(read(FIXTURE_SCAN_ISSUE)))


class StatusStep5Tests(unittest.TestCase):
    """[AC-2.1] Step 5 skips closed issues before the age check."""

    def setUp(self) -> None:
        self.step5 = section(read(STATUS), "### Step 5", "### Step 6")

    def test_step_5_states_the_rule(self) -> None:
        self.assertIn(RULE, self.step5)

    def test_the_skip_precedes_the_age_and_spec_ref_checks(self) -> None:
        skip = self.step5.index(RULE)
        self.assertLess(skip, self.step5.index("**Check age**"))
        self.assertLess(skip, self.step5.index("**Check spec_ref**"))

    def test_the_skip_is_in_the_per_file_list(self) -> None:
        per_file = section(self.step5, "For each issue file found:", "**Report format:**")
        self.assertIn(RULE, per_file)
        self.assertIn("skip", per_file.split(RULE, 1)[1].split("\n", 1)[0])


class OpenIssueCountTests(unittest.TestCase):
    """[AC-2.2] Both Open Issues renderers count open issues only."""

    def test_status_step_8_counts_open_issues_only(self) -> None:
        step8 = section(read(STATUS), "### Step 8", "### Step 9")
        line = next(l for l in step8.splitlines() if l.startswith("- **Open Issues**"))
        self.assertIn(f"without {RULE}", line)
        self.assertIn("omit if absent", line)

    def test_the_snapshot_skill_counts_open_issues_only(self) -> None:
        schema = section(read(SNAPSHOT_SKILL), "## Open Issues", "```")
        self.assertIn(f"without {RULE}", schema)
        self.assertIn("omit section if `.writ/issues/` absent", schema)

    def test_the_absent_folder_fallback_is_unchanged(self) -> None:
        self.assertIn('`.writ/issues/` absent → omit the "Open Issues" section.',
                      read(SNAPSHOT_SKILL))


class CreateIssueClosingNoteTests(unittest.TestCase):
    """[AC-2.3] /create-issue documents how to close an issue."""

    def setUp(self) -> None:
        self.text = read(CREATE_ISSUE)

    def test_the_note_exists(self) -> None:
        self.assertIn("**Closing an issue:**", self.text)

    def test_the_note_names_the_heading_date_and_change(self) -> None:
        note = self.text.split("**Closing an issue:**", 1)[1].split("\n\n", 1)[0]
        self.assertIn("`## Resolution`", note)
        self.assertIn("date", note)
        self.assertIn("commit or branch", note)
        self.assertIn("never delete or move", note.lower())


class StatusBudgetTests(unittest.TestCase):
    """[AC-2.4] The edit fits inside status.md's byte budget."""

    def test_status_grew_by_at_most_300_bytes(self) -> None:
        self.assertLessEqual(len(STATUS.read_bytes()), STATUS_BYTE_CEILING)

    def test_status_has_no_over_budget_entry(self) -> None:
        tree = ast.parse(read(GOVERNOR_TEST))
        known = next(
            ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign)
            and any(getattr(t, "id", None) == "KNOWN_OVER_BUDGET" for t in node.targets)
        )
        self.assertNotIn("commands/status.md", known)


if __name__ == "__main__":
    unittest.main()
