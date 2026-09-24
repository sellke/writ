#!/usr/bin/env python3
"""Tests for the lean preamble sibling, `commands/_preamble.lean.md` (Story 2).

The lean file drops the Plan Mode Integrity and Narrow Recommended-Delivery
Exception restatements of `system-instructions.md` and keeps User Challenge,
Autonomy Gate Classes, File Organization, and Artifact Integrity. The default
`commands/_preamble.md` stays under the unchanged 95-line `check_length` cap,
and neither file tells the model to save tokens.

These tests read the real repository files, not fixtures: the contract is
about the text that ships.
"""

from __future__ import annotations

import importlib.util
import os
import re
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
ROOT = os.path.dirname(SCRIPTS)

DEFAULT = os.path.join(ROOT, "commands", "_preamble.md")
LEAN = os.path.join(ROOT, "commands", "_preamble.lean.md")
EVAL = os.path.join(SCRIPTS, "eval.sh")

LEAN_ENV = "WRIT_HARNESS_LEAN"
KEY_ENV = "ANTHROPIC_API_KEY"

# Phrases that would coach the model to spend fewer tokens (Business rule 1).
# Chosen so none false-matches the kept text ("cost_if_wrong", "cost less
# than the decision" in stakes triage are about decision cost, not tokens).
TOKEN_SAVING = re.compile(
    r"fewer tokens|save tokens|saving tokens|conserve|be brief|be concise|"
    r"keep it short|keep (your )?(answers|responses|output) short|"
    r"avoid waste|wasting tokens|token budget|minimi[sz]e tokens|"
    r"minimi[sz]e (output|verbosity)|terse",
    re.IGNORECASE,
)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _lines(path):
    return len(_read(path).splitlines())


def _load_measure():
    target = os.path.join(SCRIPTS, "measure-invocation.py")
    spec = importlib.util.spec_from_file_location("measure_invocation_preamble", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _env(value=None):
    env = {k: v for k, v in os.environ.items() if k not in (KEY_ENV, LEAN_ENV)}
    if value is not None:
        env[LEAN_ENV] = value
    return mock.patch.dict(os.environ, env, clear=True)


class LineCaps(unittest.TestCase):
    """AC-2.3: lean shorter than default; default <=95; cap not raised."""

    def test_lean_file_exists(self):
        self.assertTrue(os.path.isfile(LEAN), f"missing {LEAN}")

    def test_lean_is_shorter_than_default(self):
        self.assertLess(_lines(LEAN), _lines(DEFAULT))

    def test_default_within_95_lines(self):
        self.assertLessEqual(_lines(DEFAULT), 95)

    def test_check_length_cap_is_still_95(self):
        text = _read(EVAL)
        body = text[text.index("check_length() {"):]
        body = body[:body.index("\n}\n")]
        self.assertIn('file="$PROJECT_ROOT/commands/_preamble.md"', body)
        self.assertIn('if [ "$count" -gt 95 ]; then', body)
        self.assertIn("(limit 95)", body)


class DroppedSections(unittest.TestCase):
    """AC-2.1: Plan Mode / --recommend restatements are gone from the lean file."""

    def test_no_plan_mode_integrity(self):
        self.assertNotIn("## Plan Mode Integrity", _read(LEAN))

    def test_no_narrow_recommended_delivery_exception(self):
        self.assertNotIn("Narrow Recommended-Delivery Exception", _read(LEAN))

    def test_default_still_carries_both(self):
        text = _read(DEFAULT)
        self.assertIn("## Plan Mode Integrity", text)
        self.assertIn("### Narrow Recommended-Delivery Exception", text)

    def test_system_instructions_carry_the_dropped_rules(self):
        text = _read(os.path.join(ROOT, "system-instructions.md"))
        self.assertIn("Never let Plan Mode absorb a command's workflow.", text)
        self.assertIn("Planning commands create files and stop", text)
        self.assertIn("No `--recommend` command merges", text)
        self.assertIn("`--recommend` lives on exactly two commands.", text)


class KeptSections(unittest.TestCase):
    """AC-2.2: the standing sections survive in the lean file."""

    def setUp(self):
        self.text = _read(LEAN)

    def test_frontmatter_unchanged(self):
        self.assertTrue(self.text.startswith("---\nname: _preamble\n"))
        default_fm = _read(DEFAULT).split("---\n")[1]
        self.assertEqual(self.text.split("---\n")[1], default_fm)

    def test_user_challenge(self):
        for literal in (
            "## User Challenge",
            "scope_degradation",
            "exit_criteria_degradation",
            "four required parts",
            "roadmap_or_spec_said",
            "recommendation",
            "possibly_missing_context",
            "cost_if_wrong",
            "select-or-pause",
            "challenge_required",
            "contract error",
        ):
            self.assertIn(literal, self.text)

    def test_autonomy_gate_classes(self):
        for literal in (
            "## Autonomy Gate Classes",
            "| Production boundary (merge/PR/release/tag/publish) | **Human gate**",
            "| Product & spec direction | **Human gate**",
            "| Design & UX judgment | **Human gate**",
            "**Reversibility precondition.**",
            "**Stakes triage (ADR-023).**",
            "**Safety gates are never capped by count.**",
        ):
            self.assertIn(literal, self.text)

    def test_file_organization(self):
        self.assertIn("## File Organization", self.text)
        self.assertIn("All work is organized into `.writ/`", self.text)

    def test_artifact_integrity(self):
        for literal in (
            "## Artifact Integrity",
            "**Required missing** → HALT",
            "**Optional missing** → warn and continue",
        ):
            self.assertIn(literal, self.text)


class NoTokenCoaching(unittest.TestCase):
    """AC-2.4: no line tells the model to use fewer tokens or be brief."""

    def test_lean_has_no_token_saving_line(self):
        hits = [line for line in _read(LEAN).splitlines() if TOKEN_SAVING.search(line)]
        self.assertEqual(hits, [])

    def test_pattern_catches_coaching(self):
        # Guards the regex itself so a typo cannot make the scan vacuous.
        for bad in ("Be concise.", "Use fewer tokens.", "Conserve context.",
                    "Keep it short.", "Avoid waste.", "Minimize tokens."):
            self.assertIsNotNone(TOKEN_SAVING.search(bad), bad)


class LoaderSelection(unittest.TestCase):
    """AC-2.1 / task 2.5: the flag picks which preamble the base counts."""

    @classmethod
    def setUpClass(cls):
        cls.mi = _load_measure()

    def test_flag_unset_loads_default_preamble(self):
        with _env(None):
            report = self.mi.measure(ROOT, tokenizer="estimate")
        components = report["base"]["components"]
        self.assertEqual(components["commands/_preamble.md"], os.path.getsize(DEFAULT))
        self.assertNotIn("commands/_preamble.lean.md", components)

    def test_flag_on_loads_lean_preamble(self):
        with _env("1"):
            report = self.mi.measure(ROOT, tokenizer="estimate")
        components = report["base"]["components"]
        self.assertEqual(components["commands/_preamble.lean.md"], os.path.getsize(LEAN))
        self.assertNotIn("commands/_preamble.md", components)


if __name__ == "__main__":
    unittest.main()
