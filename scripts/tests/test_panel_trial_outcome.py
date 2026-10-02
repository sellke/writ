#!/usr/bin/env python3
"""Outcome tests for the cross-family review panel trial (spec 2026-10-01-cross-family-review-panel, Story 5).

Reads the committed trial record and report with stdlib JSON and regex only. It
never imports review-panel.py, so it keeps guarding the record after a `remove`
verdict deletes that script.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / ".writ" / "specs" / "2026-10-01-cross-family-review-panel"
TRIAL_DIR = REPO_ROOT / ".writ" / "eval" / "panel-trial"
REPORT = SPEC_DIR / "trial-report.md"
COMMAND_FILES = (
    REPO_ROOT / "commands" / "implement-story.md",
    REPO_ROOT / "commands" / "implement-story.lean.md",
)
PANEL_PARAGRAPH = "**Review panel (opt-in).**"
CAVEAT = "sample: 4 stories; one valid miss keeps the panel — a low bar, not a cost case"
STATUS_FOR_VERDICT = {"keep": "Complete", "remove": "Closed — Not Implemented"}
DIFF_MARKER = re.compile(r"^(@@|\+\+\+ |--- )", re.MULTILINE)
NOTE_LIMIT = 200


def _trial_files() -> List[Path]:
    return sorted(TRIAL_DIR.glob("*-panel-trial.json"))


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _verdict() -> str:
    return REPORT.read_text(encoding="utf-8").splitlines()[0].strip()


def _spec_status() -> str:
    match = re.search(r"^> \*\*Status:\*\* (.+)$", (SPEC_DIR / "spec.md").read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).strip() if match else ""


@unittest.skipUnless(_trial_files(), "no committed .writ/eval/panel-trial/*-panel-trial.json yet")
class TrialRecordTests(unittest.TestCase):
    """AC-5.1: the committed record is complete, labeled, and text-free."""

    def setUp(self):
        self.trial = json.loads(_trial_files()[-1].read_text(encoding="utf-8"))
        baseline = json.loads((REPO_ROOT / self.trial["baseline"]).read_text(encoding="utf-8"))
        self.selection = [entry["story_id"] for entry in baseline["selection"]]

    def test_schema_and_story_set_match_the_baseline_selection(self):
        self.assertEqual(self.trial["schema"], "panel-trial-v1")
        self.assertEqual(sorted(s["story_id"] for s in self.trial["stories"]), sorted(self.selection))
        self.assertEqual(len(self.trial["stories"]), 4)

    def test_every_story_has_both_arms(self):
        for story in self.trial["stories"]:
            self.assertEqual(sorted(story["arms"]), ["evaluator", "panel"], story["story_id"])

    def test_every_panel_only_finding_is_labeled_with_a_short_plain_note(self):
        for story in self.trial["stories"]:
            for finding in story["panel_only"]:
                where = "%s %s" % (story["story_id"], finding["key"])
                self.assertIn(finding["label"], ("valid", "invalid"), where)
                note = finding["note"] or ""
                self.assertTrue(note.strip(), where)
                self.assertLessEqual(len(note), NOTE_LIMIT, where)
                self.assertNotIn("\n", note, where)
                self.assertNotIn("```", note, where)

    def test_no_diff_or_multiline_text_is_committed(self):
        for text in _strings(self.trial):
            self.assertIsNone(DIFF_MARKER.search(text), text[:80])
            self.assertNotIn("\n", text, text[:80])


@unittest.skipUnless(REPORT.is_file(), "no committed trial-report.md yet")
class VerdictAgreementTests(unittest.TestCase):
    """AC-5.2, AC-5.3, AC-5.4, AC-5.5: the repo acts on the verdict the report printed."""

    def test_report_carries_the_small_sample_caveat(self):
        self.assertIn(CAVEAT, REPORT.read_text(encoding="utf-8"))

    def test_spec_status_matches_the_verdict(self):
        verdict = _verdict()
        status = _spec_status()
        if verdict in STATUS_FOR_VERDICT:
            self.assertEqual(status, STATUS_FOR_VERDICT[verdict])
        else:
            self.assertNotIn(status, STATUS_FOR_VERDICT.values())

    def test_panel_wiring_matches_the_verdict(self):
        verdict = _verdict()
        if verdict not in STATUS_FOR_VERDICT:
            self.skipTest("verdict %r is not acted on" % verdict)
        for command in COMMAND_FILES:
            present = PANEL_PARAGRAPH in command.read_text(encoding="utf-8")
            self.assertEqual(present, verdict == "keep", command.name)

    def test_adr_and_roadmap_record_the_verdict(self):
        if _verdict() not in STATUS_FOR_VERDICT:
            self.skipTest("an unverifiable trial records nothing")
        adr = (REPO_ROOT / ".writ" / "decision-records"
               / "adr-028-behavioral-verification-and-cross-family-panels.md").read_text(encoding="utf-8")
        self.assertIn("**Trial result", adr)
        self.assertIn("cross-family-review-panel/trial-report.md", adr)
        criterion = [line for line in (REPO_ROOT / ".writ" / "product" / "roadmap.md").read_text(encoding="utf-8").splitlines()
                     if line.startswith("- The cross-family panel raises at least one valid finding")]
        self.assertEqual(len(criterion), 1)
        self.assertIn("✅ met", criterion[0])
        self.assertIn("trial-report", criterion[0])

    def test_remove_keeps_the_tags_jev_judge_consumes(self):
        if _verdict() != "remove":
            self.skipTest("only a remove verdict touches the agent files")
        for agent in ("review-agent.md", "evaluator-agent.md"):
            text = (REPO_ROOT / "agents" / agent).read_text(encoding="utf-8")
            self.assertRegex(text, r"\[AC-N\.M\]", agent)
            self.assertIn("- **Category:**", text, agent)


if __name__ == "__main__":
    unittest.main()
