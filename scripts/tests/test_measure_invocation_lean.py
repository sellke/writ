#!/usr/bin/env python3
"""Tests for the WRIT_HARNESS_LEAN flag substrate in measure-invocation.py.

With the flag unset, `measure()` must report exactly what it reported before
the flag existed, even with `commands/*.lean.md` siblings on disk. With the
flag at `1`, the preamble and each command resolve to their lean sibling when
one exists. Any other value is treated as unset and warned about once. A
missing sibling for a command this spec requires falls back to the default
file and names the missing path.

Every test pins WRIT_HARNESS_LEAN and removes ANTHROPIC_API_KEY, so a stray
variable in the developer's shell cannot poison a default-path assertion.
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), "measure-invocation.py")

LEAN_ENV = "WRIT_HARNESS_LEAN"
KEY_ENV = "ANTHROPIC_API_KEY"


def _load():
    spec = importlib.util.spec_from_file_location("measure_invocation_lean", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mi = _load()


def lean_env(value=None):
    """os.environ without the API key, with WRIT_HARNESS_LEAN set to `value`
    (or removed when `value` is None)."""
    env = {k: v for k, v in os.environ.items() if k not in (KEY_ENV, LEAN_ENV)}
    if value is not None:
        env[LEAN_ENV] = value
    return mock.patch.dict(os.environ, env, clear=True)


def write(root, rel, body):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(body)


def fm(**fields):
    lines = ["---", "name: x", 'description: "d"']
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


SYSTEM = "S" * 100
PREAMBLE = "P" * 50
PREAMBLE_LEAN = "p" * 20
SPEC_BODY = fm(required_skills="[big]") + "x" * 400
SPEC_LEAN = fm(required_skills="[small]") + "y" * 30
OTHER_BODY = fm() + "z" * 200


def build_default(root):
    write(root, "system-instructions.md", SYSTEM)
    write(root, "commands/_preamble.md", PREAMBLE)
    write(root, "commands/create-spec.md", SPEC_BODY)
    write(root, "commands/status.md", OTHER_BODY)
    write(root, "skills/big/SKILL.md", "B" * 300)
    write(root, "skills/small/SKILL.md", "s" * 10)
    return root


def add_lean(root):
    write(root, "commands/_preamble.lean.md", PREAMBLE_LEAN)
    write(root, "commands/create-spec.lean.md", SPEC_LEAN)
    return root


def run(root, **kwargs):
    kwargs.setdefault("tokenizer", "estimate")
    return mi.measure(root, **kwargs)


class FlagUnset(unittest.TestCase):
    """AC-1.1: unset flag, lean siblings on disk, output unchanged."""

    def test_report_is_identical_with_and_without_lean_files(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env(None):
            build_default(tmp)
            before = json.dumps(run(tmp), indent=2)
            add_lean(tmp)
            after = json.dumps(run(tmp), indent=2)
            self.assertEqual(before, after)

    def test_lean_files_are_never_measured_as_commands(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env(None):
            add_lean(build_default(tmp))
            report = run(tmp)
            self.assertEqual(sorted(report["commands"]), ["create-spec", "status"])
            self.assertFalse(any(".lean" in k for k in report["commands"]))

    def test_lean_bytes_absent_from_every_floor(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env(None):
            add_lean(build_default(tmp))
            report = run(tmp)
            base = len(SYSTEM) + len(PREAMBLE)
            self.assertEqual(report["base"]["bytes"], base)
            self.assertEqual(report["commands"]["create-spec"]["floor_bytes"],
                             base + len(SPEC_BODY) + 300)
            self.assertEqual(report["commands"]["status"]["floor_bytes"],
                             base + len(OTHER_BODY))
            self.assertNotIn("harness_lean", report)
            for data in report["commands"].values():
                self.assertNotIn("source", data)

    def test_lean_files_ignored_when_flag_off_even_for_single_command(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env(None):
            add_lean(build_default(tmp))
            report = run(tmp, command="create-spec.lean")
            self.assertEqual(report["commands"], {})


class FlagOn(unittest.TestCase):
    """AC-1.2: flag `1` loads the lean sibling in place of the default."""

    def test_preamble_and_command_use_lean_bytes(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            add_lean(build_default(tmp))
            report = run(tmp)
            base = len(SYSTEM) + len(PREAMBLE_LEAN)
            self.assertEqual(report["base"]["bytes"], base)
            self.assertEqual(report["base"]["components"], {
                "system-instructions.md": len(SYSTEM),
                "commands/_preamble.lean.md": len(PREAMBLE_LEAN),
            })
            spec = report["commands"]["create-spec"]
            self.assertEqual(spec["command_bytes"], len(SPEC_LEAN))
            self.assertEqual(spec["floor_bytes"], base + len(SPEC_LEAN) + 10)

    def test_frontmatter_is_parsed_from_the_lean_file(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            add_lean(build_default(tmp))
            spec = run(tmp)["commands"]["create-spec"]
            self.assertEqual(spec["eager_skills"], ["small"])
            self.assertEqual(spec["eager_bytes"], 10)

    def test_inline_reads_are_parsed_from_the_lean_file(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            add_lean(build_default(tmp))
            write(tmp, "skills/cond/SKILL.md", "c" * 7)
            write(tmp, "commands/create-spec.lean.md",
                  SPEC_LEAN + "\n## Step 1\nRead skills/cond/SKILL.md\n")
            spec = run(tmp)["commands"]["create-spec"]
            self.assertEqual(spec["conditional_skills"], ["cond"])

    def test_report_marks_lean_mode_and_sources(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            add_lean(build_default(tmp))
            report = run(tmp)
            self.assertIs(report["harness_lean"], True)
            self.assertEqual(report["commands"]["create-spec"]["source"],
                             "commands/create-spec.lean.md")
            self.assertEqual(report["commands"]["status"]["source"],
                             "commands/status.md")
            self.assertEqual(sorted(report["commands"]), ["create-spec", "status"])

    def test_lean_mode_emits_no_warnings_when_siblings_present(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            add_lean(build_default(tmp))
            self.assertEqual(run(tmp, command="create-spec")["warnings"], [])


class FlagInvalid(unittest.TestCase):
    """AC-1.3: any value but `1` is treated as unset, with one warning."""

    def _check(self, value):
        with tempfile.TemporaryDirectory() as tmp:
            add_lean(build_default(tmp))
            with lean_env(None):
                default = run(tmp)
            with lean_env(value):
                report = run(tmp)
            flagged = [w for w in report["warnings"] if LEAN_ENV in w]
            self.assertEqual(len(flagged), 1, report["warnings"])
            self.assertIn(repr(value), flagged[0])
            self.assertIn("1", flagged[0])
            self.assertEqual(report["warnings"], flagged + default["warnings"])
            self.assertNotIn("harness_lean", report)
            report["warnings"] = default["warnings"]
            self.assertEqual(json.dumps(report), json.dumps(default))

    def test_yes_is_treated_as_unset(self):
        self._check("yes")

    def test_empty_string_is_treated_as_unset(self):
        self._check("")

    def test_true_is_treated_as_unset(self):
        self._check("true")


class MissingSibling(unittest.TestCase):
    """AC-1.4: flag `1`, required sibling absent, default loads with a warning."""

    def test_missing_command_and_preamble_siblings_fall_back_and_warn(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            build_default(tmp)
            report = run(tmp)
            self.assertEqual(report["base"]["components"], {
                "system-instructions.md": len(SYSTEM),
                "commands/_preamble.md": len(PREAMBLE),
            })
            spec = report["commands"]["create-spec"]
            self.assertEqual(spec["command_bytes"], len(SPEC_BODY))
            self.assertEqual(spec["source"], "commands/create-spec.md")
            warnings = report["warnings"]
            self.assertEqual(
                sum("commands/_preamble.lean.md" in w for w in warnings), 1)
            self.assertEqual(
                sum("commands/create-spec.lean.md" in w for w in warnings), 1)

    def test_command_outside_lean_siblings_does_not_warn(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            build_default(tmp)
            report = run(tmp)
            self.assertFalse(any("status.lean.md" in w for w in report["warnings"]))
            self.assertEqual(report["commands"]["status"]["source"],
                             "commands/status.md")

    def test_single_command_warns_only_about_its_own_sibling(self):
        with tempfile.TemporaryDirectory() as tmp, lean_env("1"):
            build_default(tmp)
            write(tmp, "commands/verify-spec.md", OTHER_BODY)
            report = run(tmp, command="create-spec")
            warnings = report["warnings"]
            self.assertTrue(any("commands/create-spec.lean.md" in w for w in warnings))
            self.assertTrue(any("commands/_preamble.lean.md" in w for w in warnings))
            self.assertFalse(any("verify-spec.lean.md" in w for w in warnings))

    def test_lean_siblings_constant_names_the_required_set(self):
        self.assertEqual(mi.LEAN_SIBLINGS, ("_preamble", "create-spec", "verify-spec",
                                            "implement-phase", "implement-story"))
        self.assertEqual(mi.LEAN_ENV, LEAN_ENV)
        self.assertEqual(mi.LEAN_SUFFIX, ".lean.md")


if __name__ == "__main__":
    unittest.main()
