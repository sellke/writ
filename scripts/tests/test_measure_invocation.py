#!/usr/bin/env python3
"""Tests for measure-invocation.py — per-invocation load measurement.

The tool exists because Phase 10's token success criterion reads
"measured **per-invocation load**, not just file size" and nothing measured
that. `eval-leanness.py` weighs the whole `commands/` directory; a command
invocation loads the root contract, the shared preamble, one command file,
and (only if declared) its `required_skills:`. Those are different numbers
and progressive disclosure only moves one of them.

Two families live here:

  1. **Byte accounting** — floor/ceiling/base arithmetic on fixture trees
     with known sizes, including the shared-base insight that disclosure
     cannot reduce, and the ghost-skill case where a declared skill has no
     file (counted as unresolved, never silently zero).

  2. **Labeling discipline (ADR-019)** — bytes are a measurement, tokens are
     an estimate unless a real tokenizer is present, and the output must say
     which it did. This is the half that settles roadmap caveat 1: chars/4
     was never validated against a tokenizer, and the tool must not launder
     an assumption into a number that reads like a measurement.

`measure-invocation.py` has a hyphen in its filename, so it is loaded by path
via `importlib.util.spec_from_file_location` — the established recipe in
`test_archive_sweep.py`, `test_spec_status.py`, `test_story_deps.py` and
`test_eval_leanness_contract.py`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
TARGET = os.path.join(SCRIPTS, "measure-invocation.py")


def _load():
    spec = importlib.util.spec_from_file_location("measure_invocation", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mi = _load()


def build_root(tmp, *, commands, skills=None, system_instructions="S" * 100,
               preamble="P" * 50):
    """A minimal product tree. `commands` maps stem -> file body."""
    os.makedirs(os.path.join(tmp, "commands"), exist_ok=True)
    if system_instructions is not None:
        with open(os.path.join(tmp, "system-instructions.md"), "w") as fh:
            fh.write(system_instructions)
    if preamble is not None:
        with open(os.path.join(tmp, "commands", "_preamble.md"), "w") as fh:
            fh.write(preamble)
    for stem, body in commands.items():
        with open(os.path.join(tmp, "commands", f"{stem}.md"), "w") as fh:
            fh.write(body)
    for name, body in (skills or {}).items():
        d = os.path.join(tmp, "skills", name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w") as fh:
            fh.write(body)
    return tmp


def fm(**fields):
    """A frontmatter block followed by body filler."""
    lines = ["---", "name: x", 'description: "d"']
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


class ByteAccounting(unittest.TestCase):

    def test_floor_is_base_plus_command(self):
        """Per-invocation floor = root contract + preamble + the command."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm() + "x" * 400
            build_root(tmp, commands={"alpha": body},
                       system_instructions="S" * 100, preamble="P" * 50)
            report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(report["base"]["bytes"], 150)
            self.assertEqual(alpha["command_bytes"], len(body))
            self.assertEqual(alpha["floor_bytes"], 150 + len(body))

    def test_no_skills_at_all_means_ceiling_equals_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["conditional_bytes"], 0)
            self.assertEqual(alpha["eager_bytes"], 0)
            self.assertEqual(alpha["ceiling_bytes"], alpha["floor_bytes"])

    def test_required_skills_is_EAGER_and_lands_in_the_floor(self):
        """`required_skills:` pre-loads before phase 1 — it is not conditional.

        system-instructions.md: "the harness loads skills/foo/SKILL.md ... and
        makes it accessible to the agent before any phase work begins."
        adapters/claude-code.md:396 says the same. A declared skill is paid on
        every invocation, so it belongs in the floor. An earlier version of
        this module put it in `conditional_bytes`, which understated the floor
        and would have let progressive disclosure self-certify on a number
        nobody pays.
        """
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp,
                       commands={"alpha": fm(required_skills="[tdd-cycle]")},
                       skills={"tdd-cycle": "K" * 300})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 300)
            self.assertIn(300, [alpha["floor_bytes"] - alpha["base_bytes"]
                                - alpha["command_bytes"]])
            self.assertEqual(alpha["conditional_bytes"], 0)

    def test_inline_read_is_CONDITIONAL_and_lands_above_the_floor(self):
        """`Read skills/<n>/SKILL.md` in the body loads only if reached."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm() + "\nGate 3 runs via `Read skills/tdd-cycle/SKILL.md` here.\n"
            build_root(tmp, commands={"alpha": body},
                       skills={"tdd-cycle": "K" * 300})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["conditional_bytes"], 300)
            self.assertEqual(alpha["eager_bytes"], 0)
            self.assertEqual(alpha["ceiling_bytes"], alpha["floor_bytes"] + 300)
            self.assertEqual(alpha["conditional_skills"], ["tdd-cycle"])

    def test_both_mechanisms_are_reported_separately(self):
        """A misclassified skill must be visible, never silently absorbed."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm(required_skills="[eagerly]") + "\n`Read skills/lazily/SKILL.md`\n"
            build_root(tmp, commands={"alpha": body},
                       skills={"eagerly": "E" * 200, "lazily": "L" * 500})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 200)
            self.assertEqual(alpha["conditional_bytes"], 500)
            self.assertEqual(alpha["eager_skills"], ["eagerly"])
            self.assertEqual(alpha["conditional_skills"], ["lazily"])

    def test_skill_both_declared_and_inline_read_warns(self):
        """Declaring what you also inline-read pays for it unconditionally."""
        with tempfile.TemporaryDirectory() as tmp:
            body = fm(required_skills="[dup]") + "\n`Read skills/dup/SKILL.md`\n"
            build_root(tmp, commands={"alpha": body}, skills={"dup": "D" * 400})
            report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["eager_bytes"], 400)
            self.assertEqual(alpha["conditional_bytes"], 0)  # not double-counted
            self.assertTrue(any("dup" in w and "both" in w.lower()
                                for w in report["warnings"]))

    def test_ghost_skill_is_unresolved_not_silently_zero(self):
        """A declared skill with no file must be visible, not absorbed."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp,
                       commands={"alpha": fm(required_skills="[ghost, real]")},
                       skills={"real": "R" * 120})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["unresolved_skills"], ["ghost"])
            self.assertEqual(alpha["eager_bytes"], 120)
            self.assertEqual(alpha["resolved_skills"], ["real"])

    def test_preamble_is_base_never_a_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            report = mi.measure(tmp)
            self.assertNotIn("_preamble", report["commands"])
            self.assertEqual(report["base"]["components"]["commands/_preamble.md"], 50)

    def test_missing_root_contract_degrades_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()}, system_instructions=None)
            report = mi.measure(tmp)
            self.assertEqual(report["base"]["components"]["system-instructions.md"], 0)
            self.assertIn("system-instructions.md", report["warnings"][0])

    def test_shared_base_is_the_floor_disclosure_cannot_reduce(self):
        """Reported explicitly: the irreducible cost of any invocation."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"a": fm() + "x" * 900, "b": fm()},
                       system_instructions="S" * 200, preamble="P" * 100)
            report = mi.measure(tmp)
            self.assertEqual(report["base"]["bytes"], 300)
            self.assertEqual(report["corpus"]["irreducible_base_bytes"], 300)
            self.assertLess(report["corpus"]["min_floor_bytes"],
                            report["corpus"]["max_floor_bytes"])


class CorpusSummary(unittest.TestCase):

    def test_distribution_reports_min_median_max(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={
                "a": fm() + "x" * 100,
                "b": fm() + "x" * 200,
                "c": fm() + "x" * 300,
            }, system_instructions="", preamble="")
            corpus = mi.measure(tmp)["corpus"]
            self.assertEqual(corpus["commands_measured"], 3)
            floors = sorted(
                mi.measure(tmp)["commands"][k]["floor_bytes"] for k in "abc")
            self.assertEqual(corpus["min_floor_bytes"], floors[0])
            self.assertEqual(corpus["median_floor_bytes"], floors[1])
            self.assertEqual(corpus["max_floor_bytes"], floors[2])

    def test_worst_offender_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"small": fm(), "huge": fm() + "x" * 5000})
            self.assertEqual(mi.measure(tmp)["corpus"]["max_floor_command"], "huge")


class LabelingDiscipline(unittest.TestCase):
    """ADR-019: never report an estimate as a measurement."""

    def test_bytes_and_tokens_are_separately_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertIn("floor_bytes", alpha)
            self.assertIn("floor_tokens_estimated", alpha)
            self.assertNotIn("floor_tokens", alpha)

    def test_method_records_estimate_and_divisor(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            report = mi.measure(tmp, chars_per_token=4.0)
            self.assertEqual(report["token_method"], "estimate:chars/4.0")
            self.assertEqual(report["chars_per_token"], 4.0)

    def test_divisor_is_overridable(self):
        """chars/4 is an assumption; the tool must let it be calibrated."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm() + "x" * 800})
            four = mi.measure(tmp, chars_per_token=4.0)
            three = mi.measure(tmp, chars_per_token=3.0)
            self.assertEqual(four["commands"]["alpha"]["floor_bytes"],
                             three["commands"]["alpha"]["floor_bytes"])
            self.assertGreater(three["commands"]["alpha"]["floor_tokens_estimated"],
                               four["commands"]["alpha"]["floor_tokens_estimated"])

    def test_estimate_carries_an_honest_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            note = mi.measure(tmp)["token_note"]
            self.assertIn("not", note.lower())
            self.assertIn("tokeniz", note.lower())

    def test_unvalidated_divisor_is_flagged_as_unvalidated(self):
        """The roadmap's chars/4 was never checked against a tokenizer."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            self.assertFalse(mi.measure(tmp)["token_method_validated"])


class LineCounts(unittest.TestCase):
    """The 400-line cap was derived from a distribution, not an impact."""

    def test_lines_reported_alongside_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = fm() + "\n".join("line" for _ in range(40)) + "\n"
            build_root(tmp, commands={"alpha": body})
            alpha = mi.measure(tmp)["commands"]["alpha"]
            self.assertEqual(alpha["command_lines"], body.count("\n"))

    def test_bytes_per_line_enables_cap_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm() + "y" * 100 + "\n"})
            corpus = mi.measure(tmp)["corpus"]
            self.assertIn("mean_bytes_per_command_line", corpus)
            self.assertGreater(corpus["mean_bytes_per_command_line"], 0)


class CommandLineInterface(unittest.TestCase):

    def _run(self, *args):
        return subprocess.run([sys.executable, TARGET, *args],
                              capture_output=True, text=True)

    def test_emits_one_json_object_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            proc = self._run("--root", tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn("commands", payload)

    def test_single_command_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm(), "beta": fm()})
            payload = json.loads(self._run("--root", tmp, "--command", "alpha").stdout)
            self.assertEqual(list(payload["commands"]), ["alpha"])

    def test_absent_root_exits_zero_with_a_warning(self):
        """Read-only measurement never blocks a caller."""
        proc = self._run("--root", "/nonexistent-root-xyz")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(json.loads(proc.stdout)["warnings"])

    def test_table_mode_is_human_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            proc = self._run("--root", tmp, "--format", "table")
            self.assertEqual(proc.returncode, 0)
            self.assertIn("alpha", proc.stdout)
            self.assertIn("floor", proc.stdout.lower())


if __name__ == "__main__":
    unittest.main()


class PlacementEnforcement(unittest.TestCase):
    """The conditional mechanism's benefit IS placement, so placement must be
    checkable. A `Read` hoisted above the first step runs on every invocation
    — eager behaviour in conditional syntax — and without this check it
    reports an identical ceiling and passes every gate.
    """

    def _cmd(self, read_before_steps: bool):
        head = "---\nname: x\ndescription: \"d\"\n---\n\n## Overview\n\nText.\n"
        hoisted = "\n`Read skills/tdd-cycle/SKILL.md`\n" if read_before_steps else ""
        steps = "\n## Command Process\n\n### Step 1: Go\n"
        tail = "" if read_before_steps else "\n`Read skills/tdd-cycle/SKILL.md`\n"
        return head + hoisted + steps + tail

    def test_hoisted_read_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": self._cmd(True)},
                       skills={"tdd-cycle": "K" * 100})
            report = mi.measure(tmp)
            alpha = report["commands"]["alpha"]
            self.assertEqual(alpha["hoisted_skills"], ["tdd-cycle"])
            self.assertTrue(any("hoisted" in w.lower() for w in report["warnings"]))

    def test_read_at_point_of_need_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": self._cmd(False)},
                       skills={"tdd-cycle": "K" * 100})
            report = mi.measure(tmp)
            self.assertEqual(report["commands"]["alpha"]["hoisted_skills"], [])
            self.assertFalse(any("hoisted" in w.lower() for w in report["warnings"]))

    def test_no_step_heading_means_no_verdict(self):
        """Undetectable structure must not produce a false accusation."""
        with tempfile.TemporaryDirectory() as tmp:
            body = "---\nname: x\n---\n\n`Read skills/tdd-cycle/SKILL.md`\n"
            build_root(tmp, commands={"alpha": body},
                       skills={"tdd-cycle": "K" * 100})
            self.assertEqual(mi.measure(tmp)["commands"]["alpha"]["hoisted_skills"], [])


class CeilingIsAnEnvelope(unittest.TestCase):
    def test_ceiling_is_labelled_an_envelope_not_a_path(self):
        """Mutually exclusive branches are summed; no invocation may reach all."""
        with tempfile.TemporaryDirectory() as tmp:
            build_root(tmp, commands={"alpha": fm()})
            self.assertIn("envelope", mi.measure(tmp)["ceiling_note"].lower())
