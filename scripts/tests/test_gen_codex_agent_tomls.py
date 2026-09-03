#!/usr/bin/env python3
"""Unit tests for scripts/gen-codex-agent-tomls.py (Story 3 of
`2026-09-03-model-delegation`, AC-3.5).

The generator turns `agents/*.md` into `codex/agents/*.toml`. Under ADR-024
the Codex floor is effort-only: the two `floor` stems get
`model_reasoning_effort = "low"` and no `model =` line (the parent's model is
used, so the floor never crosses vendors or exceeds the origin); the five
`anchor` stems get neither line. Any historical `model: "fast"` line inside an
embedded agent body is stripped defensively, and the retired `FAST_MODEL`
constant must not exist. The module filename contains a hyphen, so it is
imported by path — the recipe `test_ac_trace.py` uses.

Assertions run against the TOML HEADER only (everything before the
`developer_instructions = ` key), so text inside the embedded agent body can
never satisfy — or falsely violate — a header expectation.
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "gen-codex-agent-tomls.py"
_spec = importlib.util.spec_from_file_location("gen_codex_agent_tomls", MODULE_PATH)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)  # type: ignore[union-attr]

FLOOR_STEMS = ("architecture-check-agent", "user-story-generator")
ANCHOR_STEMS = (
    "coding-agent",
    "documentation-agent",
    "review-agent",
    "testing-agent",
    "visual-qa-agent",
)
ALL_STEMS = FLOOR_STEMS + ANCHOR_STEMS

EFFORT_LOW = re.compile(r'^model_reasoning_effort = "low"$', re.MULTILINE)
EFFORT_KEY = re.compile(r"^model_reasoning_effort\s*=", re.MULTILINE)
MODEL_KEY = re.compile(r"^model\s*=", re.MULTILINE)
BODY_SPLIT = "\ndeveloper_instructions = "

BODY = "# Fixture Agent\n\nSome body text.\n"


def split_toml(output: str) -> tuple[str, str]:
    """Return (header, body) — the generator's header ends where the
    `developer_instructions` key begins."""
    assert BODY_SPLIT in output, "emit_toml() output lacks developer_instructions"
    header, body = output.split(BODY_SPLIT, 1)
    return header, body


class FloorStemsEmitEffortOnly(unittest.TestCase):
    """AC-3.5: floor stems carry `model_reasoning_effort = "low"` and no `model =`."""

    def test_floor_stems_emit_low_effort(self) -> None:
        for stem in FLOOR_STEMS:
            with self.subTest(stem=stem):
                header, _ = split_toml(gen.emit_toml(stem, BODY))
                self.assertRegex(header, EFFORT_LOW)

    def test_anchor_stems_emit_no_effort(self) -> None:
        # Any effort key — not just "low" — would pin the anchor below the
        # origin, so anchor stems must emit no model_reasoning_effort at all.
        for stem in ANCHOR_STEMS:
            with self.subTest(stem=stem):
                header, _ = split_toml(gen.emit_toml(stem, BODY))
                self.assertNotRegex(header, EFFORT_KEY)


class NoStemEmitsAModelKey(unittest.TestCase):
    """AC-3.5: `model =` is never emitted — the parent's model is always used."""

    def test_no_model_key_for_any_stem(self) -> None:
        for stem in ALL_STEMS:
            with self.subTest(stem=stem):
                header, _ = split_toml(gen.emit_toml(stem, BODY))
                self.assertNotRegex(header, MODEL_KEY)


class BodyFilterStripsRetiredFastLines(unittest.TestCase):
    """AC-3.5: any `model: "fast"` line — bare or the historical
    comma-terminated template form — is dropped from the embedded body, while
    unrelated `model:` lines survive."""

    FIXTURE_BODY = (
        "# Fixture Agent\n"
        "\n"
        "```\n"
        "model: \"fast\"\n"
        "model: default (inherits from parent)\n"
        "```\n"
        "\n"
        "Task({\n"
        "  subagent_type: \"generalPurpose\",\n"
        "  model: \"fast\",\n"
        "  model: inherit\n"
        "})\n"
    )

    def test_fast_lines_are_stripped_and_others_survive(self) -> None:
        _, body = split_toml(gen.emit_toml("coding-agent", self.FIXTURE_BODY))
        self.assertNotRegex(body, re.compile(r'^\s*model:\s*"fast",?\s*$', re.MULTILINE))
        self.assertIn("model: default (inherits from parent)\n", body)
        self.assertIn("model: inherit\n", body)


class FastModelConstantIsGone(unittest.TestCase):
    """AC-3.5: the generator contains no `FAST_MODEL`."""

    def test_no_fast_model_attribute(self) -> None:
        self.assertFalse(hasattr(gen, "FAST_MODEL"))


if __name__ == "__main__":
    unittest.main()
