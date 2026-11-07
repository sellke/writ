#!/usr/bin/env python3
"""Tests for scripts/review-override.py (Story 1 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Fixtures cover pass, fail-from-ac-trace, fail-from-integrity,
unverifiable-helper, and missing --spec / --story. Helpers are invoked as
subprocesses — stubs record argv so the tests prove the script did not
re-derive findings itself. [AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "review-override.py"

STUB_AC_TRACE = r'''
import json, sys
from pathlib import Path
Path(__file__).with_name("ac-trace.calls").write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
payload = json.loads(Path(__file__).with_name("ac-trace.out.json").read_text(encoding="utf-8"))
print(json.dumps(payload, sort_keys=True))
raise SystemExit(int(payload.get("exit", 0)))
'''

STUB_INTEGRITY = r'''
import json, sys
from pathlib import Path
Path(__file__).with_name("test-integrity.calls").write_text(
    json.dumps(sys.argv[1:]), encoding="utf-8"
)
payload = json.loads(Path(__file__).with_name("test-integrity.out.json").read_text(encoding="utf-8"))
print(json.dumps(payload, sort_keys=True))
raise SystemExit(int(payload.get("exit", 0)))
'''


def _write_story(spec: Path, number: int, *, status: str, ac: str, task: str) -> Path:
    stories = spec / "user-stories"
    stories.mkdir(parents=True, exist_ok=True)
    path = stories / ("story-%d-fixture.md" % number)
    path.write_text(
        "\n".join([
            "# Story %d: Fixture" % number,
            "",
            "> **Status:** %s" % status,
            "> **Priority:** High",
            "> **Dependencies:** None",
            "",
            "## User Story",
            "",
            "Fixture.",
            "",
            "## Acceptance Criteria",
            "",
            "> **AC IDs assigned through:** AC-%d.1" % number,
            "",
            ac,
            "",
            "## Implementation Tasks",
            "",
            task,
            "",
        ]) + "\n",
        encoding="utf-8",
    )
    return path


def _stub_tree(tmp: Path, ac_payload: dict, integrity_payload: dict | None = None) -> Path:
    scripts = tmp / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts / "review-override.py")
    (scripts / "ac-trace.py").write_text(STUB_AC_TRACE, encoding="utf-8")
    (scripts / "test-integrity.py").write_text(STUB_INTEGRITY, encoding="utf-8")
    (scripts / "ac-trace.out.json").write_text(
        json.dumps(ac_payload, sort_keys=True), encoding="utf-8"
    )
    if integrity_payload is not None:
        (scripts / "test-integrity.out.json").write_text(
            json.dumps(integrity_payload, sort_keys=True), encoding="utf-8"
        )
    return scripts / "review-override.py"


def _run(script: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(script.parent.parent),
    )
    return proc.returncode, proc.stdout


def _verdict_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return stdout


def _reasons(stdout: str) -> list[str]:
    return [ln[8:] for ln in stdout.splitlines() if ln.startswith("reason: ")]


class ReviewOverrideCliTests(unittest.TestCase):
    def test_missing_spec_is_unverifiable(self) -> None:
        code, out = _run(SCRIPT, ["check", "--repo", str(REPO_ROOT)])
        self.assertEqual(code, 0, out)
        self.assertEqual(_verdict_line(out), "unverifiable")
        self.assertIn("missing_spec", _reasons(out))

    def test_missing_story_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "spec"
            spec.mkdir()
            code, out = _run(
                SCRIPT,
                ["check", "--spec", str(spec), "--repo", str(repo)],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("missing_story", _reasons(out))

    def test_usage_without_subcommand_is_exit_2(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_pass_invokes_ac_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(
                spec,
                1,
                status="Completed ✅",
                ac="- [x] Done. `[AC-1.1]`",
                task="- [x] 1.1 Implement it `[AC-1.1]`",
            )
            script = _stub_tree(
                repo,
                {
                    "schema": "ac-trace-check-v1",
                    "findings": [],
                    "exit": 0,
                },
            )
            code, out = _run(
                script,
                ["check", "--spec", str(spec), "--repo", str(repo), "--story", str(story)],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")
            calls = json.loads(
                (repo / "scripts" / "ac-trace.calls").read_text(encoding="utf-8")
            )
            self.assertEqual(calls[0], "check")
            self.assertIn("--spec", calls)
            self.assertFalse((repo / "scripts" / "test-integrity.calls").exists())

    def test_fail_from_ac_trace_untasked(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(
                spec,
                1,
                status="In Progress",
                ac="- [ ] Untasked. `[AC-1.1]`",
                task="- [ ] 1.1 No citation.",
            )
            script = _stub_tree(
                repo,
                {
                    "schema": "ac-trace-check-v1",
                    "exit": 1,
                    "findings": [
                        {
                            "code": "untasked_criterion",
                            "severity": "blocking",
                            "story": 1,
                            "id": "AC-1.1",
                        }
                    ],
                },
            )
            code, out = _run(
                script,
                ["check", "--spec", str(spec), "--repo", str(repo), "--story", str(story)],
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict_line(out), "fail")
            self.assertIn("untasked_criterion", _reasons(out))
            self.assertTrue((repo / "scripts" / "ac-trace.calls").exists())

    def test_untested_on_incomplete_story_is_not_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(
                spec,
                1,
                status="Not Started",
                ac="- [ ] Pending. `[AC-1.1]`",
                task="- [ ] 1.1 Task `[AC-1.1]`",
            )
            script = _stub_tree(
                repo,
                {
                    "schema": "ac-trace-check-v1",
                    "exit": 0,
                    "findings": [
                        {
                            "code": "untested_criterion",
                            "severity": "blocking",
                            "story": 1,
                            "id": "AC-1.1",
                        }
                    ],
                },
            )
            code, out = _run(
                script,
                ["check", "--spec", str(spec), "--repo", str(repo), "--story", str(story)],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")

    def test_fail_from_integrity_coverage(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(
                spec,
                1,
                status="Completed ✅",
                ac="- [x] Done. `[AC-1.1]`",
                task="- [x] 1.1 Implement `[AC-1.1]`",
            )
            script = _stub_tree(
                repo,
                {"schema": "ac-trace-check-v1", "findings": [], "exit": 0},
                {
                    "schema": "test-integrity-v1",
                    "verdict": "fail",
                    "exit": 1,
                    "findings": [
                        {
                            "code": "coverage_below_threshold",
                            "severity": "blocking",
                        }
                    ],
                },
            )
            code, out = _run(
                script,
                [
                    "check",
                    "--spec",
                    str(spec),
                    "--repo",
                    str(repo),
                    "--story",
                    str(story),
                    "--new-files",
                    "src/app.py",
                    "--tests",
                    "tests/test_app.py",
                ],
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict_line(out), "fail")
            self.assertIn("coverage_below_threshold", _reasons(out))
            integrity_calls = json.loads(
                (repo / "scripts" / "test-integrity.calls").read_text(encoding="utf-8")
            )
            self.assertIn(integrity_calls[0], ("coverage", "authenticity"))

    def test_unverifiable_helper(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(
                spec,
                1,
                status="In Progress",
                ac="- [ ] Pending. `[AC-1.1]`",
                task="- [ ] 1.1 Task `[AC-1.1]`",
            )
            script = _stub_tree(
                repo,
                {"schema": "ac-trace-check-v1", "findings": [], "exit": 0},
                {
                    "schema": "test-integrity-v1",
                    "verdict": "unverifiable",
                    "exit": 0,
                    "findings": [],
                    "unverifiable": [{"reason": "nothing_inspected"}],
                },
            )
            code, out = _run(
                script,
                [
                    "check",
                    "--spec",
                    str(spec),
                    "--repo",
                    str(repo),
                    "--story",
                    str(story),
                    "--new-files",
                    "src/app.py",
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertTrue(
                any("unverifiable" in r or "nothing_inspected" in r for r in _reasons(out)),
                out,
            )

    def test_real_ac_trace_fail_untasked(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / ".writ" / "specs" / "demo"
            story = _write_story(
                spec,
                3,
                status="In Progress",
                ac="- [ ] Given a criterion no task cites. `[AC-3.1]`",
                task="- [ ] 3.1 Unrelated task with no citation.",
            )
            code, out = _run(
                SCRIPT,
                ["check", "--spec", str(spec), "--repo", str(repo), "--story", str(story)],
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict_line(out), "fail")
            self.assertIn("untasked_criterion", _reasons(out))


class Gate3WiringTests(unittest.TestCase):
    def test_implement_story_has_fail_only_verify_block(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 3: Review Agent")
        end = text.index("#### Gate 3.5:", start)
        gate3 = text[start:end]
        self.assertIn("Verify the claim, don't trust it.", gate3)
        # 2026-11-06 (lean-story-pipeline Story 3): `story-gate.py`
        # post-review runs `review-override.py check` first in its table.
        self.assertIn("python3 scripts/story-gate.py run --phase post-review", gate3)
        self.assertIn("`review-override.py` checks", gate3)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "story_gate", str(REPO_ROOT / "scripts" / "story-gate.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        first = module.CHECKS["post-review"][0]
        self.assertEqual((first.id, first.script), ("gate3_override", "review-override.py"))
        # 2026-11-04 (2026-11-04-evidence-gated-review Story 3): "FAIL-only" and
        # "does not force PASS" went with the sentence; the bullet says "no override".
        self.assertIn("→ no override", gate3)
        self.assertIn("⚠️ DEGRADED", gate3)
        self.assertIn("not", gate3.lower())

    def test_frontmatter_names_the_script(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate3_review\n    script: scripts/review-override.py", text)


# ---------------------------------------------------------------------------
# Story 1 of `2026-10-25-review-route-rigor`: the `switch` subcommand.
# Every resolver row runs for both switch names; usage errors exit 2 with
# empty stdout; `check` output is unchanged. [AC-1.1, AC-1.2, AC-1.3, AC-1.4]
# ---------------------------------------------------------------------------

SWITCH_KEYS = {"safety-fact": "Safety Fact", "reviewer-filters": "Reviewer Filters",
               "evidence-gate": "Evidence Gate"}


def _switch_config(*lines: str) -> str:
    return "\n".join([
        "# Writ Project Config",
        "",
        "## Conventions",
        "",
        "- **Default Branch:** main",
        *lines,
        "",
        "## Paths",
        "",
        "- **Changelog:** CHANGELOG.md",
    ]) + "\n"


def _write_config(repo: Path, text: str) -> None:
    (repo / ".writ").mkdir(parents=True, exist_ok=True)
    (repo / ".writ" / "config.md").write_text(text, encoding="utf-8")


def _switch(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "switch", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd is not None else None,
    )


def _switch_expected(name: str, state: str, reason: str) -> list[str]:
    return [
        state,
        "reason: %s" % reason,
        "review-override switch: %s %s (.writ/config.md)" % (name, state),
    ]


class SwitchSubcommandTests(unittest.TestCase):
    """Story 1 of `2026-10-25-review-route-rigor` — resolver rows, both names.
    [AC-1.1, AC-1.2, AC-1.3, AC-1.4]"""

    def assert_switch(self, config: str | None, name: str, state: str, reason: str) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            if config is not None:
                _write_config(repo, config)
            proc = _switch(["--name", name, "--repo", str(repo)])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(proc.stdout.splitlines(), _switch_expected(name, state, reason))

    def test_value_off_turns_switch_off(self) -> None:
        """AC-1.1 — `off` prints `off` and `reason: config_off`, exit 0."""
        for name, key in SWITCH_KEYS.items():
            with self.subTest(name=name):
                self.assert_switch(_switch_config("- **%s:** off" % key),
                                   name, "off", "config_off")

    def test_value_off_any_case_turns_switch_off(self) -> None:
        """AC-1.1 — `OFF` and `oFf` also turn the switch off."""
        for name, key in SWITCH_KEYS.items():
            for value in ("OFF", "oFf"):
                with self.subTest(name=name, value=value):
                    self.assert_switch(_switch_config("- **%s:** %s" % (key, value)),
                                       name, "off", "config_off")

    def test_value_off_surrounding_whitespace_ignored(self) -> None:
        """AC-1.1 — spaces and tabs around `Off` are ignored."""
        for name, key in SWITCH_KEYS.items():
            with self.subTest(name=name):
                self.assert_switch(_switch_config("- **%s:**  \tOff  \t" % key),
                                   name, "off", "config_off")

    def test_no_config_file_is_on(self) -> None:
        """AC-1.2 — no `.writ/config.md` prints `on` and `reason: no_config`."""
        for name in SWITCH_KEYS:
            with self.subTest(name=name):
                self.assert_switch(None, name, "on", "no_config")

    def test_config_without_line_is_on(self) -> None:
        """AC-1.2 — a config with no line for the switch prints `reason: no_config_line`."""
        for name in SWITCH_KEYS:
            with self.subTest(name=name):
                self.assert_switch(_switch_config(), name, "on", "no_config_line")

    def test_other_switch_line_does_not_count(self) -> None:
        """AC-1.2 — the other switch's `off` line leaves this switch at `no_config_line`."""
        for name, key in SWITCH_KEYS.items():
            other = next(k for n, k in SWITCH_KEYS.items() if n != name)
            with self.subTest(name=name):
                self.assert_switch(_switch_config("- **%s:** off" % other),
                                   name, "on", "no_config_line")

    def test_value_on_is_on(self) -> None:
        """AC-1.2 — `on` (any case) prints `on` and `reason: config_on`."""
        for name, key in SWITCH_KEYS.items():
            for value in ("on", "ON"):
                with self.subTest(name=name, value=value):
                    self.assert_switch(_switch_config("- **%s:** %s" % (key, value)),
                                       name, "on", "config_on")

    def test_empty_value_is_on(self) -> None:
        """AC-1.2 — a line with no value prints `on` and `reason: config_on`."""
        for name, key in SWITCH_KEYS.items():
            for line in ("- **%s:**" % key, "- **%s:**   " % key):
                with self.subTest(name=name, line=line):
                    self.assert_switch(_switch_config(line), name, "on", "config_on")

    def test_unreadable_config_is_on(self) -> None:
        """AC-1.2 — a config that is a directory or not UTF-8 reads as `no_config`."""
        for name, key in SWITCH_KEYS.items():
            with self.subTest(name=name, case="directory"), TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".writ" / "config.md").mkdir(parents=True)
                proc = _switch(["--name", name, "--repo", str(repo)])
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(proc.stdout.splitlines(),
                                 _switch_expected(name, "on", "no_config"))
            with self.subTest(name=name, case="non-utf8"), TemporaryDirectory() as tmp:
                repo = Path(tmp)
                (repo / ".writ").mkdir()
                (repo / ".writ" / "config.md").write_bytes(
                    ("- **%s:** off\n" % key).encode("utf-8") + b"\xff\xfe\x80\n")
                proc = _switch(["--name", name, "--repo", str(repo)])
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(proc.stdout.splitlines(),
                                 _switch_expected(name, "on", "no_config"))

    def test_malformed_value_is_on_with_reason(self) -> None:
        """AC-1.3 — `of` prints `on` and `reason: malformed_value of`, exit 0."""
        for name, key in SWITCH_KEYS.items():
            with self.subTest(name=name):
                self.assert_switch(_switch_config("- **%s:** of" % key),
                                   name, "on", "malformed_value of")

    def test_malformed_value_reason_is_stripped(self) -> None:
        """AC-1.3 — the malformed value is reported without surrounding whitespace."""
        self.assert_switch(_switch_config("- **Reviewer Filters:**   disabled now  "),
                           "reviewer-filters", "on", "malformed_value disabled now")

    def test_first_match_wins(self) -> None:
        """AC-1.1, AC-1.2 — the first line anywhere in the file decides; later lines are ignored."""
        for name, key in SWITCH_KEYS.items():
            with self.subTest(name=name, first="off"):
                config = _switch_config("- **%s:** off" % key) + "- **%s:** on\n" % key
                self.assert_switch(config, name, "off", "config_off")
            with self.subTest(name=name, first="on"):
                config = _switch_config("- **%s:** on" % key) + "- **%s:** off\n" % key
                self.assert_switch(config, name, "on", "config_on")
            with self.subTest(name=name, where="under ## Paths"):
                config = _switch_config() + "- **%s:** off\n" % key
                self.assert_switch(config, name, "off", "config_off")

    def test_repo_defaults_to_cwd(self) -> None:
        """AC-1.1 — without `--repo`, the switch reads `./.writ/config.md`."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write_config(repo, _switch_config("- **Safety Fact:** off"))
            proc = _switch(["--name", "safety-fact"], cwd=repo)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(proc.stdout.splitlines(),
                             _switch_expected("safety-fact", "off", "config_off"))

    def test_unknown_name_is_usage_error(self) -> None:
        """AC-1.4 — an unknown `--name` leaves stdout empty, prints usage on stderr, exits 2."""
        for value in ("safety", "Safety-Fact", "gate0-divergence"):
            with self.subTest(value=value), TemporaryDirectory() as tmp:
                proc = _switch(["--name", value, "--repo", tmp])
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(proc.stdout, "")
                self.assertIn("usage:", proc.stderr)

    def test_missing_name_is_usage_error(self) -> None:
        """AC-1.4 — `switch` without `--name` leaves stdout empty, prints usage on stderr, exits 2."""
        with TemporaryDirectory() as tmp:
            proc = _switch(["--repo", tmp])
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(proc.stdout, "")
            self.assertIn("usage:", proc.stderr)


class CheckUnchangedBySwitchTests(unittest.TestCase):
    """Story 1 of `2026-10-25-review-route-rigor` — `check` prints the same
    output and exit codes as before the `switch` subcommand. [AC-1.4]"""

    def test_check_missing_spec_output_is_byte_identical(self) -> None:
        """AC-1.4 — `check` with no `--spec` prints the same three lines, exit 0."""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--repo", str(REPO_ROOT)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "unverifiable\nreason: missing_spec\n"
                                      "review-override: unverifiable (missing --spec)\n")

    def test_check_missing_story_output_is_byte_identical(self) -> None:
        """AC-1.4 — `check` with no `--story` prints the same three lines, exit 0."""
        with TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "check", "--spec", tmp, "--project", tmp],
                capture_output=True, text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "unverifiable\nreason: missing_story\n"
                                      "review-override: unverifiable (missing --story)\n")

    def test_check_pass_output_is_byte_identical(self) -> None:
        """AC-1.4 — a stubbed clean ac-trace still prints `pass` and the same summary, exit 0."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1, status="Completed ✅",
                                 ac="- [x] Done. `[AC-1.1]`",
                                 task="- [x] 1.1 Implement it `[AC-1.1]`")
            script = _stub_tree(repo, {"schema": "ac-trace-check-v1", "findings": [], "exit": 0})
            code, out = _run(script, ["check", "--spec", str(spec), "--repo", str(repo),
                                      "--story", str(story)])
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "pass\nreview-override: pass (no blocking helper finding)\n")

    def test_check_rejects_switch_flags(self) -> None:
        """AC-1.4 — `check` still refuses an unknown flag with exit 2 and empty stdout."""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--name", "safety-fact"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)


# ---------------------------------------------------------------------------
# Story 4 of `2026-10-25-review-route-rigor`: the `safety-fact` subcommand.
# Each ladder rung is accepted on its own evidence and rejected when the
# evidence does not check out; cited paths outside `--repo` never count; the
# `traced` consumers rule follows the blast-radius file; every fail reason
# fires on its own condition and prints in table order; an unreadable review
# output is `unverifiable`. [AC-4.1, AC-4.2, AC-4.3]
# ---------------------------------------------------------------------------

SF_FACT = "no caller passes an empty list to parse()"
SF_TESTS_OK = "\n".join([
    "command: python3 -m pytest tests/test_lib.py -q",
    "exit code: 0",
    "tests/test_lib.py::LibTests::test_rejects_empty PASSED",
    "1 passed in 0.01s",
]) + "\n"
SF_RESULT = "evidence/app-verify/parse/result.json"
# Measures `tested` against SF_TESTS_OK; the floor since Story 6 of
# `2026-11-04-evidence-gated-review`.
SF_TESTED = ("- tested: tests/test_lib.py::test_rejects_empty",)


def _sf_repo(root: Path) -> Path:
    """A small repo: a library, one caller, one unrelated file, a test, and an
    app-verify result. `outside.py` sits next to the repo, not inside it."""
    repo = root / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "lib.py").write_text(
        "def parse(items):\n"
        "    if not items:\n"
        "        raise ValueError('empty')\n"
        "    return items[0]\n",
        encoding="utf-8",
    )
    (repo / "src" / "caller.py").write_text(
        "from src.lib import parse\n\nparse([1, 2])\n", encoding="utf-8")
    (repo / "src" / "other.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_lib.py").write_text(
        "class LibTests:\n"
        "    def test_rejects_empty(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    result = repo / SF_RESULT
    result.parent.mkdir(parents=True)
    result.write_text(json.dumps({"schema": "app-verify-result-v1", "verdict": "pass"}),
                      encoding="utf-8")
    (root / "outside.py").write_text("secret = 1\nsecret = 2\n", encoding="utf-8")
    return repo


def _sf_review(*, fact: str | None = SF_FACT, holds: str | None = "yes",
               rung: str | None = "traced", evidence: tuple = (),
               verdict: str | None = "PASS", heading: str | None = "### Safety Fact",
               after: tuple = ()) -> str:
    """A review-agent output. `None` drops that line; `heading=None` drops the
    whole section. `after` lines follow the next heading."""
    lines: list = []
    if verdict is not None:
        lines += ["### REVIEW_RESULT: %s" % verdict, ""]
    lines += ["### Summary", "Fixture review.", "",
              "### Security Assessment", "**Risk Level:** Clean", ""]
    if heading is not None:
        lines.append(heading)
        if fact is not None:
            lines.append(("**Fact:** %s" % fact).rstrip())
        if holds is not None:
            lines.append("**Holds:** %s" % holds)
        if rung is not None:
            lines.append("**Rung:** %s" % rung)
        lines.append("**Evidence:**")
        lines.extend(evidence)
        lines.append("")
    lines += ["### Recommendations (optional)", "None.", *after]
    return "\n".join(lines) + "\n"


def _sf_run(root: Path, repo: Path | None, review: str | None, *, blast=None,
            tests: str | None = None, extra: list | None = None,
            cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run `safety-fact`. `blast` is a dict (written as JSON) or raw text;
    `None` omits the flag. `review=None` points at a file that does not exist."""
    review_path = root / "review.md"
    if review is not None:
        review_path.write_text(review, encoding="utf-8")
    args = ["safety-fact", "--review-output", str(review_path)]
    if repo is not None:
        args += ["--repo", str(repo)]
    if blast is not None:
        blast_path = root / "blast.json"
        blast_path.write_text(blast if isinstance(blast, str) else json.dumps(blast),
                              encoding="utf-8")
        args += ["--blast-radius", str(blast_path)]
    if tests is not None:
        tests_path = root / "tests-output.txt"
        tests_path.write_text(tests, encoding="utf-8")
        args += ["--tests-output", str(tests_path)]
    args += extra or []
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
        cwd=str(cwd) if cwd is not None else None,
    )


def _sf_measured(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("rung: "):
            return line.split("measured=", 1)[1]
    raise AssertionError("no rung: line in %r" % stdout)


def _sf_expected(verdict: str, claimed: str, measured: str, fact: str,
                 reasons: list) -> list:
    return [
        verdict,
        "rung: claimed=%s measured=%s" % (claimed, measured),
        "fact: %s" % fact,
        *["reason: %s" % r for r in reasons],
        "review-override safety-fact: %s (measured %s, floor tested)" % (verdict, measured),
    ]


def _blast(*consumers: str, verdict: str = "pass") -> dict:
    return {"verdict": verdict, "consumers": {"src/lib.py": list(consumers)},
            "tests": {"src/lib.py": ["tests/test_lib.py"]}, "truncated": [], "reasons": []}


class SafetyFactRungTests(unittest.TestCase):
    """Story 4 of `2026-10-25-review-route-rigor` — each rung accepted on its
    own evidence and rejected when it does not check out. [AC-4.1]"""

    def measure(self, evidence: tuple, *, blast=None, tests: str | None = None,
                rung: str = "traced", setup=None) -> str:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            if setup is not None:
                evidence = setup(root, repo, evidence)
            proc = _sf_run(root, repo, _sf_review(rung=rung, evidence=evidence),
                           blast=blast, tests=tests)
            self.assertIn(proc.returncode, (0, 1), proc.stdout + proc.stderr)
            return _sf_measured(proc.stdout)

    def test_claimed_is_a_non_empty_fact(self) -> None:
        """AC-4.1 — a fact with no evidence measures `claimed`."""
        self.assertEqual(self.measure(()), "claimed")

    def test_claimed_evidence_line_adds_nothing(self) -> None:
        """AC-4.1 — `claimed` has no evidence line; one written anyway changes nothing."""
        self.assertEqual(self.measure(("- claimed: the coder said so",)), "claimed")

    def test_read_accepted(self) -> None:
        """AC-4.1 — `path:line` inside the repo within the file's lines is `read`."""
        for cite in ("`src/lib.py:2`", "src/lib.py:4", "`src/lib.py:2-3`", "src/lib.py:4-99"):
            with self.subTest(cite=cite):
                self.assertEqual(self.measure(("- read: %s" % cite,)), "read")

    def test_read_rejected(self) -> None:
        """AC-4.1 — a missing path, a line past EOF, line 0, or no line number does not count."""
        for cite in ("src/nope.py:1", "src/lib.py:5", "src/lib.py:0", "src/lib.py",
                     "src:1", "src/lib.py:99-100"):
            with self.subTest(cite=cite):
                self.assertEqual(self.measure(("- read: %s" % cite,)), "claimed")

    def test_read_rejects_dotdot_escape(self) -> None:
        """AC-4.1 — `../outside.py:1` resolves outside `--repo` and is rejected."""
        self.assertEqual(self.measure(("- read: ../outside.py:1",)), "claimed")
        self.assertEqual(self.measure(("- read: src/../../outside.py:1",)), "claimed")

    def test_read_allows_dotdot_that_stays_inside(self) -> None:
        """AC-4.1 — `..` that resolves back inside `--repo` is a normal citation."""
        self.assertEqual(self.measure(("- read: src/../src/lib.py:1",)), "read")

    def test_read_rejects_absolute_path(self) -> None:
        """AC-4.1 — an absolute path to a file outside `--repo` is rejected."""
        def absolute(root: Path, repo: Path, evidence: tuple) -> tuple:
            return ("- read: %s:1" % (root / "outside.py").resolve(),)
        self.assertEqual(self.measure((), setup=absolute), "claimed")

    def test_read_rejects_symlink_escape(self) -> None:
        """AC-4.1 — a symlink inside `--repo` that points outside it is rejected."""
        def link(root: Path, repo: Path, evidence: tuple) -> tuple:
            os.symlink(str(root / "outside.py"), str(repo / "src" / "escape.py"))
            return ("- read: src/escape.py:1",)
        self.assertEqual(self.measure((), setup=link), "claimed")

    def test_read_needs_every_line_valid(self) -> None:
        """AC-4.1 — one bad `read` citation beside a good one rejects the rung."""
        self.assertEqual(
            self.measure(("- read: src/lib.py:2", "- read: src/nope.py:1")), "claimed")

    def test_traced_accepted_without_blast_radius(self) -> None:
        """AC-4.1, AC-4.2 — with no blast-radius file, an existing caller citation is `traced`."""
        self.assertEqual(
            self.measure(("- traced: `src/caller.py:3` — passes [1, 2]",)), "traced")

    def test_traced_rejected_when_cite_is_invalid(self) -> None:
        """AC-4.1 — a missing caller, a line past EOF, or an escaping path is not `traced`."""
        for cite in ("src/nope.py:1", "src/caller.py:9", "../outside.py:1", "the callers"):
            with self.subTest(cite=cite):
                self.assertEqual(self.measure(("- traced: %s — note" % cite,)), "claimed")

    def test_traced_needs_every_cite_valid(self) -> None:
        """AC-4.1 — every cited `path:line` must be valid, not just one."""
        self.assertEqual(self.measure(("- traced: src/caller.py:3 — ok",
                                       "- traced: src/nope.py:1 — missing")), "claimed")

    def test_traced_cite_in_consumer_union_accepted(self) -> None:
        """AC-4.2 — blast radius `pass` with consumers: a cited caller in the union is `traced`."""
        self.assertEqual(
            self.measure(("- traced: src/caller.py:3 — passes [1, 2]",),
                         blast=_blast("src/caller.py")),
            "traced")
        self.assertEqual(
            self.measure(("- traced: src/caller.py:3 — passes [1, 2]",
                          "- traced: src/other.py:1 — unrelated"),
                         blast=_blast("src/caller.py")),
            "traced")

    def test_traced_cite_outside_consumer_union_rejected(self) -> None:
        """AC-4.2 — blast radius `pass` with consumers: no cited path in the union is not `traced`."""
        self.assertEqual(
            self.measure(("- read: src/lib.py:2", "- traced: src/other.py:1 — x"),
                         blast=_blast("src/caller.py")),
            "read")

    def test_traced_existence_only_when_blast_unusable(self) -> None:
        """AC-4.2 — blast radius `unverifiable`, malformed, or unreadable: existence is enough."""
        evidence = ("- traced: src/other.py:1 — x",)
        for label, blast in (("unverifiable", _blast("src/caller.py", verdict="unverifiable")),
                             ("malformed", "{not json"),
                             ("not an object", "[1, 2]"),
                             ("bad consumers", json.dumps({"verdict": "pass",
                                                           "consumers": ["src/caller.py"]}))):
            with self.subTest(blast=label):
                self.assertEqual(self.measure(evidence, blast=blast), "traced")

    def test_traced_existence_only_when_blast_path_missing(self) -> None:
        """AC-4.2 — a `--blast-radius` path that does not exist is unreadable, not unverifiable.
        The measured `traced` sits under the `tested` floor (AC-6.5)."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            proc = _sf_run(root, repo, _sf_review(evidence=("- traced: src/other.py:1 — x",)),
                           extra=["--blast-radius", str(root / "missing.json")])
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(proc.stdout.splitlines()[0], "fail", proc.stdout)
            self.assertIn("reason: safety_fact_below_floor traced", proc.stdout.splitlines())
            self.assertEqual(_sf_measured(proc.stdout), "traced")

    def test_traced_none_accepted_only_with_pass_and_empty_union(self) -> None:
        """AC-4.2 — `- traced: none` counts only when the blast radius is `pass` with no consumers."""
        none = ("- traced: none — searched for parse( across the repo",)
        self.assertEqual(self.measure(none, blast=_blast()), "traced")
        self.assertEqual(self.measure(("- traced: `none` — searched",),
                                      blast={"verdict": "pass", "consumers": {}}), "traced")

    def test_traced_none_rejected_otherwise(self) -> None:
        """AC-4.2 — `none` with consumers, an unverifiable or unreadable blast radius, or none given."""
        none = ("- traced: none — searched",)
        for label, blast in (("consumers", _blast("src/caller.py")),
                             ("unverifiable", _blast(verdict="unverifiable")),
                             ("malformed", "{not json"),
                             ("absent", None)):
            with self.subTest(blast=label):
                self.assertEqual(self.measure(none, blast=blast), "claimed")

    def test_tested_accepted(self) -> None:
        """AC-4.1 — `path::test_name` in a passing recorded run is `tested`."""
        for cite in ("`tests/test_lib.py::test_rejects_empty`",
                     "tests/test_lib.py::LibTests::test_rejects_empty",
                     "tests/test_lib.py::test_rejects_empty[case-1]"):
            with self.subTest(cite=cite):
                self.assertEqual(
                    self.measure(("- tested: %s" % cite,), tests=SF_TESTS_OK), "tested")

    def test_tested_rejected(self) -> None:
        """AC-4.1 — absent test name, missing file, path outside the repo, or no `::`."""
        for cite in ("tests/test_lib.py::test_accepts_empty",
                     "tests/test_nope.py::test_rejects_empty",
                     "../outside.py::secret",
                     "tests/test_lib.py"):
            with self.subTest(cite=cite):
                self.assertEqual(
                    self.measure(("- tested: %s" % cite,), tests=SF_TESTS_OK), "claimed")

    def test_tested_rejected_without_exit_code_zero(self) -> None:
        """AC-4.1 — the recorded run must have the line `exit code: 0`."""
        cite = ("- tested: tests/test_lib.py::test_rejects_empty",)
        for label, tests in (
            ("exit 1", SF_TESTS_OK.replace("exit code: 0", "exit code: 1")),
            ("exit 10", SF_TESTS_OK.replace("exit code: 0", "exit code: 10")),
            ("no line", SF_TESTS_OK.replace("exit code: 0\n", "")),
            ("not its own line", SF_TESTS_OK.replace("exit code: 0", "note exit code: 0 x")),
        ):
            with self.subTest(tests=label):
                self.assertEqual(self.measure(cite, tests=tests), "claimed")

    def test_tested_rejected_when_path_not_in_tests_output(self) -> None:
        """AC-4.1 — the cited test file must appear in the recorded run."""
        tests = "command: python3 -m pytest tests/test_other.py\nexit code: 0\n1 passed\n"
        self.assertEqual(
            self.measure(("- tested: tests/test_lib.py::test_rejects_empty",), tests=tests),
            "claimed")

    def test_tested_rejected_without_tests_output(self) -> None:
        """AC-4.1 — no `--tests-output`, or an unreadable one, makes `tested` unacceptable."""
        cite = ("- tested: tests/test_lib.py::test_rejects_empty",)
        self.assertEqual(self.measure(cite), "claimed")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            proc = _sf_run(root, repo, _sf_review(evidence=cite),
                           extra=["--tests-output", str(root / "missing.txt")])
            self.assertEqual(_sf_measured(proc.stdout), "claimed")

    def test_reproduced_accepted(self) -> None:
        """AC-4.1 — a passing `app-verify-result-v1` file inside the repo is `reproduced`."""
        self.assertEqual(self.measure(("- reproduced: `%s`" % SF_RESULT,)), "reproduced")

    def test_reproduced_rejected(self) -> None:
        """AC-4.1 — wrong schema, wrong verdict, not JSON, missing, or outside the repo."""
        cases = (
            ("wrong schema", json.dumps({"schema": "app-verify-v0", "verdict": "pass"})),
            ("wrong verdict", json.dumps({"schema": "app-verify-result-v1", "verdict": "fail"})),
            ("not json", "{"),
            ("not an object", json.dumps(["app-verify-result-v1", "pass"])),
        )
        for label, body in cases:
            def write(root: Path, repo: Path, evidence: tuple, body: str = body) -> tuple:
                (repo / SF_RESULT).write_text(body, encoding="utf-8")
                return ("- reproduced: %s" % SF_RESULT,)
            with self.subTest(result=label):
                self.assertEqual(self.measure((), setup=write), "claimed")
        with self.subTest(result="missing"):
            self.assertEqual(self.measure(("- reproduced: evidence/none/result.json",)),
                             "claimed")

        def outside(root: Path, repo: Path, evidence: tuple) -> tuple:
            (root / "result.json").write_text(
                json.dumps({"schema": "app-verify-result-v1", "verdict": "pass"}),
                encoding="utf-8")
            return ("- reproduced: ../result.json",)
        with self.subTest(result="outside repo"):
            self.assertEqual(self.measure((), setup=outside), "claimed")

    def assert_rejected_without_crash(self, evidence: tuple, *, blast=None, setup=None,
                                      rung: str = "traced") -> None:
        """The verifier prints its contract lines (no traceback, no empty
        stdout) and the citation does not count."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            if setup is not None:
                evidence = setup(root, repo, evidence)
            proc = _sf_run(root, repo, _sf_review(rung=rung, evidence=evidence), blast=blast)
            self.assertNotIn("Traceback", proc.stderr)
            lines = proc.stdout.splitlines()
            self.assertTrue(lines, proc.stderr)
            self.assertEqual(lines[0], "fail", proc.stdout + proc.stderr)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(_sf_measured(proc.stdout), "claimed")

    def test_huge_line_number_is_rejected_not_a_crash(self) -> None:
        """AC-4.1 — a 5,000-digit line number is a rejected citation on every Python:
        past EOF on 3.9, and an int-conversion limit error caught on 3.11+."""
        huge = "9" * 5000
        for line in ("- read: src/lib.py:%s" % huge,
                     "- traced: src/caller.py:%s — note" % huge):
            with self.subTest(line=line[:20]):
                self.assert_rejected_without_crash((line,))

    def test_deeply_nested_result_json_is_rejected_not_a_crash(self) -> None:
        """AC-4.1 — a `reproduced` file nested past the recursion limit does not count."""
        def deep(root: Path, repo: Path, evidence: tuple) -> tuple:
            (repo / SF_RESULT).write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
            return ("- reproduced: %s" % SF_RESULT,)
        self.assert_rejected_without_crash((), setup=deep, rung="reproduced")

    def test_deeply_nested_blast_radius_is_unreadable_not_a_crash(self) -> None:
        """AC-4.2 — a blast radius nested past the recursion limit reads as unusable:
        `none` is rejected and a cited caller needs only to exist."""
        deep = "[" * 100000 + "]" * 100000
        self.assert_rejected_without_crash(("- traced: none — searched",), blast=deep)
        self.assertEqual(self.measure(("- traced: src/other.py:1 — x",), blast=deep), "traced")

    def test_measured_is_highest_accepted_and_not_cumulative(self) -> None:
        """AC-4.1 — the ladder is not cumulative: `tested` stands without `read` or `traced`."""
        self.assertEqual(
            self.measure(("- tested: tests/test_lib.py::test_rejects_empty",),
                         tests=SF_TESTS_OK), "tested")
        self.assertEqual(
            self.measure(("- read: src/nope.py:1",
                          "- tested: tests/test_lib.py::test_rejects_empty"),
                         tests=SF_TESTS_OK), "tested")
        self.assertEqual(
            self.measure(("- read: src/lib.py:2",
                          "- traced: src/caller.py:3 — passes [1, 2]",
                          "- tested: tests/test_lib.py::test_absent"),
                         tests=SF_TESTS_OK), "traced")
        self.assertEqual(
            self.measure(("- read: src/lib.py:2",
                          "- tested: tests/test_lib.py::test_rejects_empty",
                          "- reproduced: %s" % SF_RESULT),
                         tests=SF_TESTS_OK), "reproduced")


class SafetyFactVerdictTests(unittest.TestCase):
    """Story 4 of `2026-10-25-review-route-rigor` — pass, each fail reason on
    its own, table order, the overclaim line, unreadable input, usage.
    [AC-4.1, AC-4.3]

    Story 6 of `2026-11-04-evidence-gated-review` raised the floor to `tested`:
    a case that passed at measured `traced` now cites `TESTED` evidence, or
    keeps `TRACED` and expects `safety_fact_below_floor traced`. [AC-6.5]"""

    TRACED = ("- read: src/lib.py:2", "- traced: src/caller.py:3 — passes [1, 2]")
    TESTED = SF_TESTED

    def run_review(self, review: str | None, **kwargs) -> subprocess.CompletedProcess:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            return _sf_run(root, repo, review, **kwargs)

    def assert_output(self, proc: subprocess.CompletedProcess, expected: list) -> None:
        self.assertEqual(proc.stdout.splitlines(), expected, proc.stderr)
        self.assertEqual(proc.returncode, 0 if expected[0] == "pass" else 1)

    def test_pass_prints_contract_lines(self) -> None:
        """AC-4.3 — section present, measured `tested`, `Holds: yes` → pass, exit 0."""
        proc = self.run_review(_sf_review(rung="tested", evidence=self.TESTED), tests=SF_TESTS_OK)
        self.assert_output(proc, _sf_expected("pass", "tested", "tested", SF_FACT, []))

    def test_holds_no_with_fail_or_pause_passes(self) -> None:
        """AC-4.3 — `Holds: no` agrees with a FAIL or PAUSE verdict."""
        for verdict in ("FAIL", "PAUSE", "**FAIL**"):
            with self.subTest(verdict=verdict):
                proc = self.run_review(_sf_review(holds="no", verdict=verdict, rung="tested",
                                                  evidence=self.TESTED), tests=SF_TESTS_OK)
                self.assert_output(proc, _sf_expected("pass", "tested", "tested", SF_FACT, []))

    def test_missing_section(self) -> None:
        """AC-4.3 — no `Safety Fact` heading: missing section, and nothing is measured."""
        proc = self.run_review(_sf_review(heading=None))
        self.assert_output(proc, _sf_expected(
            "fail", "none", "none", "(none)",
            ["safety_fact_missing section", "safety_fact_below_floor none"]))

    def test_heading_levels(self) -> None:
        """AC-4.3 — `##` to `######` open the section; `#` and trailing words do not."""
        for heading in ("## Safety Fact", "###### Safety Fact", "### Safety Fact  "):
            with self.subTest(heading=heading):
                proc = self.run_review(_sf_review(heading=heading, rung="tested",
                                                  evidence=self.TESTED), tests=SF_TESTS_OK)
                self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)
        for heading in ("# Safety Fact", "### Safety Facts", "### Safety Fact (draft)"):
            with self.subTest(heading=heading):
                proc = self.run_review(_sf_review(heading=heading, rung="tested",
                                                  evidence=self.TESTED), tests=SF_TESTS_OK)
                self.assertIn("reason: safety_fact_missing section", proc.stdout.splitlines())

    def test_section_ends_at_next_heading(self) -> None:
        """AC-4.3 — evidence after the next heading is not part of the section."""
        proc = self.run_review(_sf_review(after=("- traced: src/caller.py:3 — late",)))
        self.assert_output(proc, _sf_expected("fail", "traced", "claimed", SF_FACT,
                                              ["safety_fact_below_floor claimed"]))

    def test_missing_fact_alone(self) -> None:
        """AC-4.3 — an empty Fact is `safety_fact_missing fact`; evidence still measures."""
        for fact in ("", None):
            with self.subTest(fact=fact):
                proc = self.run_review(_sf_review(fact=fact, rung="tested",
                                                  evidence=self.TESTED), tests=SF_TESTS_OK)
                self.assert_output(proc, _sf_expected("fail", "tested", "tested", "(none)",
                                                      ["safety_fact_missing fact"]))

    def test_missing_holds_alone(self) -> None:
        """AC-4.3 — Holds not `yes`/`no` is `safety_fact_missing holds`."""
        for holds in ("maybe", "yes | no", "", None):
            with self.subTest(holds=holds):
                proc = self.run_review(_sf_review(holds=holds, rung="tested",
                                                  evidence=self.TESTED), tests=SF_TESTS_OK)
                self.assert_output(proc, _sf_expected("fail", "tested", "tested", SF_FACT,
                                                      ["safety_fact_missing holds"]))

    def test_missing_rung_alone(self) -> None:
        """AC-4.3 — Rung not one of the five is `safety_fact_missing rung`; claimed prints `none`."""
        for rung in ("solid", "", None):
            with self.subTest(rung=rung):
                proc = self.run_review(_sf_review(rung=rung, evidence=self.TESTED),
                                       tests=SF_TESTS_OK)
                self.assert_output(proc, _sf_expected("fail", "none", "tested", SF_FACT,
                                                      ["safety_fact_missing rung"]))

    def test_missing_items_one_line_each_in_order(self) -> None:
        """AC-4.3 — every missing item gets its own line: fact, holds, rung."""
        proc = self.run_review(_sf_review(fact="", holds=None, rung="?", evidence=self.TESTED),
                               tests=SF_TESTS_OK)
        self.assert_output(proc, _sf_expected(
            "fail", "none", "tested", "(none)",
            ["safety_fact_missing fact", "safety_fact_missing holds",
             "safety_fact_missing rung"]))

    def test_below_floor_alone(self) -> None:
        """AC-4.3 — measured `read` under the `tested` floor."""
        proc = self.run_review(_sf_review(rung="read", evidence=("- read: src/lib.py:2",)))
        self.assert_output(proc, _sf_expected("fail", "read", "read", SF_FACT,
                                              ["safety_fact_below_floor read"]))

    def test_below_floor_none_when_nothing_accepted(self) -> None:
        """AC-4.3 — an empty Fact and no accepted evidence measure `none`."""
        proc = self.run_review(_sf_review(fact="", rung="claimed"))
        self.assert_output(proc, _sf_expected(
            "fail", "claimed", "none", "(none)",
            ["safety_fact_missing fact", "safety_fact_below_floor none"]))

    def test_contradicts_verdict_alone(self) -> None:
        """AC-4.3 — `Holds: no` with a PASS verdict contradicts it."""
        for verdict in ("PASS", "pass"):
            with self.subTest(verdict=verdict):
                proc = self.run_review(_sf_review(holds="no", verdict=verdict, rung="tested",
                                                  evidence=self.TESTED), tests=SF_TESTS_OK)
                self.assert_output(proc, _sf_expected("fail", "tested", "tested", SF_FACT,
                                                      ["safety_fact_contradicts_verdict"]))

    def test_contradicts_when_no_verdict_line(self) -> None:
        """AC-4.3 — `Holds: no` with no FAIL or PAUSE verdict found is treated as a contradiction."""
        proc = self.run_review(_sf_review(holds="no", verdict=None, rung="tested",
                                          evidence=self.TESTED), tests=SF_TESTS_OK)
        self.assert_output(proc, _sf_expected("fail", "tested", "tested", SF_FACT,
                                              ["safety_fact_contradicts_verdict"]))

    def test_evaluation_result_verdict_is_read(self) -> None:
        """AC-4.3 — the verdict comes from the first REVIEW_RESULT or EVALUATION_RESULT heading."""
        review = _sf_review(holds="no", verdict=None, rung="tested", evidence=self.TESTED)
        proc = self.run_review("### EVALUATION_RESULT: FAIL\n\n" + review, tests=SF_TESTS_OK)
        self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)
        proc = self.run_review("## REVIEW_RESULT: PASS\n\n### REVIEW_RESULT: FAIL\n\n" + review,
                               tests=SF_TESTS_OK)
        self.assertIn("reason: safety_fact_contradicts_verdict", proc.stdout.splitlines())

    def test_every_reason_in_table_order(self) -> None:
        """AC-4.3 — missing, then below floor, then contradicts."""
        proc = self.run_review(_sf_review(holds="no", rung="high", verdict="PASS",
                                          evidence=("- read: src/lib.py:2",)))
        self.assert_output(proc, _sf_expected(
            "fail", "none", "read", SF_FACT,
            ["safety_fact_missing rung", "safety_fact_below_floor read",
             "safety_fact_contradicts_verdict"]))

    def test_overclaim_alone_is_not_a_reason(self) -> None:
        """AC-4.3 — claimed `reproduced`, measured `tested`: the rung line shows both, verdict pass."""
        proc = self.run_review(_sf_review(rung="reproduced", evidence=self.TESTED),
                               tests=SF_TESTS_OK)
        self.assert_output(proc, _sf_expected("pass", "reproduced", "tested", SF_FACT, []))

    def test_underclaim_prints_measured(self) -> None:
        """AC-4.3 — claimed `read` with `tested` evidence measures `tested` and passes."""
        proc = self.run_review(_sf_review(rung="read", evidence=self.TESTED), tests=SF_TESTS_OK)
        self.assert_output(proc, _sf_expected("pass", "read", "tested", SF_FACT, []))

    def test_fields_case_insensitive_bold_optional(self) -> None:
        """AC-4.3 — `Fact:`, `**holds:**`, `RUNG:`, `**Rung**:` and `- Traced:` all parse.
        The measured `traced` sits under the `tested` floor (AC-6.5)."""
        review = "\n".join([
            "### REVIEW_RESULT: PASS", "", "### Safety Fact",
            "fact: %s" % SF_FACT,
            "**holds:** Yes",
            "**Rung**: `Traced`",
            "EVIDENCE:",
            "- Read: `src/lib.py:2`",
            "* **traced:** `src/caller.py:3` — passes [1, 2]",
            "",
        ]) + "\n"
        proc = self.run_review(review)
        self.assert_output(proc, _sf_expected("fail", "traced", "traced", SF_FACT,
                                              ["safety_fact_below_floor traced"]))

    def test_first_field_occurrence_wins(self) -> None:
        """AC-4.3 — a second `Holds:` line in the section is ignored."""
        review = _sf_review(rung="tested", evidence=self.TESTED + ("**Holds:** no",))
        proc = self.run_review(review, tests=SF_TESTS_OK)
        self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)

    def test_unreadable_review_output_is_unverifiable(self) -> None:
        """AC-4.3 — a missing, directory, or non-UTF-8 review output is `unverifiable`, exit 0."""
        expected = ["unverifiable", "reason: review_output_unreadable",
                    "review-override safety-fact: unverifiable (review_output_unreadable)"]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            with self.subTest(case="missing"):
                proc = _sf_run(root, repo, None)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.splitlines(), expected)
            with self.subTest(case="directory"):
                (root / "review.md").mkdir()
                proc = _sf_run(root, repo, None)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.splitlines(), expected)
                (root / "review.md").rmdir()
            with self.subTest(case="non-utf8"):
                (root / "review.md").write_bytes(b"### Safety Fact\n\xff\xfe\x80\n")
                proc = _sf_run(root, repo, None)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.splitlines(), expected)

    def test_missing_review_output_flag_is_usage_error(self) -> None:
        """AC-4.3 — no `--review-output`: stdout empty, usage on stderr, exit 2."""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "safety-fact", "--repo", "."],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_repo_defaults_to_cwd(self) -> None:
        """AC-4.1 — without `--repo`, cited paths resolve against the working directory."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            proc = _sf_run(root, None, _sf_review(evidence=self.TRACED), cwd=repo)
            self.assert_output(proc, _sf_expected("fail", "traced", "traced", SF_FACT,
                                                  ["safety_fact_below_floor traced"]))
            proc = _sf_run(root, None, _sf_review(evidence=self.TRACED), cwd=root)
            self.assertEqual(_sf_measured(proc.stdout), "claimed")


class SafetyFactLeavesOtherSubcommandsTests(unittest.TestCase):
    """Story 4 of `2026-10-25-review-route-rigor` — `check` and `switch`
    print what they printed before `safety-fact` existed. [AC-4.3]"""

    def test_check_unchanged(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--repo", str(REPO_ROOT)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "unverifiable\nreason: missing_spec\n"
                                      "review-override: unverifiable (missing --spec)\n")

    def test_switch_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            proc = _switch(["--name", "safety-fact", "--repo", tmp])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.splitlines(),
                         _switch_expected("safety-fact", "on", "no_config"))


# ---------------------------------------------------------------------------
# Story 6 of `2026-11-04-evidence-gated-review`: the Safety Fact floor moves
# from `traced` to `tested`. A section measured `traced` now falls below the
# floor; a section measured `tested` keeps exactly the reasons it had. The
# floor wording in the script, the skill, and their generated copies names
# `tested`. [AC-6.1, AC-6.2, AC-6.3, AC-6.4]
# ---------------------------------------------------------------------------

class SafetyFactTestedFloorTests(unittest.TestCase):
    """Story 6 of `2026-11-04-evidence-gated-review` — `safety-fact` measures
    against the `tested` floor. [AC-6.3, AC-6.4]"""

    def run_lines(self, review: str) -> tuple:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            proc = _sf_run(root, repo, review, tests=SF_TESTS_OK)
        return proc.returncode, proc.stdout.splitlines()

    def test_traced_section_is_below_the_floor(self) -> None:
        """AC-6.3 — highest accepted rung `traced` prints `safety_fact_below_floor traced`."""
        for evidence in (("- traced: src/caller.py:3 — passes [1, 2]",),
                         ("- read: src/lib.py:2", "- traced: src/caller.py:3 — passes [1, 2]")):
            with self.subTest(evidence=evidence):
                code, lines = self.run_lines(_sf_review(evidence=evidence))
                self.assertEqual(lines[:2], ["fail", "rung: claimed=traced measured=traced"])
                self.assertIn("reason: safety_fact_below_floor traced", lines)
                self.assertEqual(code, 1)

    def test_tested_section_keeps_every_other_reason(self) -> None:
        """AC-6.4 — measured `tested`: no `safety_fact_below_floor` line, and the
        other reason lines are unchanged from before the floor moved."""
        cases = (
            ({}, []),
            ({"holds": "no", "verdict": "FAIL"}, []),
            ({"holds": "no", "verdict": "PASS"}, ["safety_fact_contradicts_verdict"]),
            ({"fact": ""}, ["safety_fact_missing fact"]),
            ({"holds": None}, ["safety_fact_missing holds"]),
            ({"rung": "high"}, ["safety_fact_missing rung"]),
            ({"fact": "", "holds": "maybe", "rung": None},
             ["safety_fact_missing fact", "safety_fact_missing holds",
              "safety_fact_missing rung"]),
            ({"holds": "no", "rung": "high", "verdict": None},
             ["safety_fact_missing rung", "safety_fact_contradicts_verdict"]),
        )
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                kwargs = dict({"rung": "tested", "evidence": SF_TESTED}, **overrides)
                code, lines = self.run_lines(_sf_review(**kwargs))
                self.assertIn("measured=tested", lines[1])
                self.assertEqual([l for l in lines if l.startswith("reason: ")],
                                 ["reason: %s" % r for r in expected])
                self.assertEqual(lines[0], "fail" if expected else "pass")
                self.assertEqual(code, 1 if expected else 0)


class SafetyFactFloorWordingTests(unittest.TestCase):
    """Story 6 of `2026-11-04-evidence-gated-review` — the shipped floor
    wording names `tested`, in the source and in its generated copies.
    [AC-6.1, AC-6.2]"""

    SCRIPTS = ("scripts/review-override.py", "plugins/writ/scripts/review-override.py")
    SKILLS = ("skills/blast-radius/SKILL.md", "cursor/plugin/skills/blast-radius/SKILL.md",
              "plugins/writ/skills/blast-radius/SKILL.md")
    # `traced` named as the floor, in either order: `FLOOR = "traced"`, "Floor: `traced`",
    # "floor traced)", "The floor is `traced`", "`traced` is the floor".
    TRACED_FLOOR = re.compile(
        r"floor\W{0,4}(?:is\s+)?`?traced\b|\btraced`?\W{0,4}(?:is\s+)?(?:the\s+)?floor",
        re.IGNORECASE)

    @staticmethod
    def flat(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def bullet(text: str, prefix: str) -> str:
        """The bullet starting with `prefix`, joined with its indented continuation lines."""
        lines = text.splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
        body = [lines[start]]
        for line in lines[start + 1:]:
            if not line.startswith("  "):
                break
            body.append(line)
        return " ".join(part.strip() for part in body)

    def test_script_floor_is_tested(self) -> None:
        """AC-6.1, AC-6.2 — `FLOOR = "tested"`, the docstring `Floor:` line, and the
        output example name `tested`, in the script and its plugin copy."""
        for rel in self.SCRIPTS:
            with self.subTest(path=rel):
                raw = (REPO_ROOT / rel).read_text(encoding="utf-8")
                self.assertRegex(raw, re.compile(r'^FLOOR = "tested"$', re.MULTILINE))
                doc = self.flat(ast.get_docstring(ast.parse(raw)) or "")
                self.assertIn("Floor: `tested`.", doc)
                self.assertIn("(measured <m>, floor tested)", doc)
                self.assertIsNone(self.TRACED_FLOOR.search(self.flat(raw)))

    def test_skill_floor_is_tested(self) -> None:
        """AC-6.1, AC-6.2 — the Evidence Ladder floor sentence and the re-review
        `safety_fact_below_floor` advice name `tested`, in the skill and both copies."""
        for rel in self.SKILLS:
            with self.subTest(path=rel):
                raw = (REPO_ROOT / rel).read_text(encoding="utf-8")
                self.assertIn("The floor is `tested`.", self.flat(raw))
                self.assertIsNone(self.TRACED_FLOOR.search(self.flat(raw)))
                advice = self.bullet(raw, "- `safety_fact_below_floor")
                self.assertIn("the measured rung is under `tested`. Cite a test from the "
                              "recorded run; only the coder can add one.", self.flat(advice))
                self.assertNotRegex(advice.lower(), r"\btrac")


# ---------------------------------------------------------------------------
# Story 2 of `2026-11-04-evidence-gated-review`: the `evidence` subcommand and
# the `evidence-gated-findings` skill. One test per Error & Rescue row and per
# Evidence outcomes cell, plus the skill's registration. Each test copies the
# fixture project into a temp git repo and writes its own `.writ/config.md`;
# no test runs `evidence` against the Writ working tree.
# [AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]
# ---------------------------------------------------------------------------

EV_FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "review-override" / "evidence"
EV_PROJECT = EV_FIXTURES / "pytest-project"
EV_STUBS = EV_FIXTURES / "stubs"
EV_PYTEST = "%s -m pytest" % shlex.quote(sys.executable)
EV_LOCATION = "`src/limits.py:3`"
EV_AT = " at src/limits.py"
EV_REPRO = "tests/test_limits_repro.py"
EV_REPRO_FAIL = (
    "from src.limits import parse_limit\n"
    "\n"
    "\n"
    "def test_negative_limit_rejected():\n"
    "    assert parse_limit(\"-1\") is None\n"
)
EV_REPRO_PASS = (
    "from src.limits import parse_limit\n"
    "\n"
    "\n"
    "def test_positive_limit():\n"
    "    assert parse_limit(\"5\") == 5\n"
)
EV_REPRO_BROKEN = "def test_broken(:\n    pass\n"

EV_SKILL_NAME = "evidence-gated-findings"
EV_SKILL_REL = "skills/evidence-gated-findings/SKILL.md"
# Cited by name, as shipped skills cite ADRs: an installed project has no ADR
# files, so a relative link would not resolve in the generated plugin trees.
EV_ADR_CITE = "(ADR-032)"
# Reason codes the spec does not name. The skill lists each one (Story 2 Notes).
EV_NEW_REASONS = (
    "low_severity", "repro_passed", "recorded_passed", "check_passed",
    "no_changed_file_named", "test_not_in_run", "no_recorded_run",
    "no_gate2_record", "command_not_recorded", "command_not_found",
    "not_security", "unknown_kind", "missing_test_block", "repro_write_failed",
    "stopped_after_mutation",
)


def _ev_env(**extra: str) -> dict:
    """The caller's env minus GIT_* and STUB_*, git config isolated, and the
    stub runners first on PATH."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_") and not k.startswith("STUB_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PATH": str(EV_STUBS) + os.pathsep + os.environ.get("PATH", ""),
    })
    env.update(extra)
    return env


def _ev_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, env=_ev_env())
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout


def _ev_config(runner: str | None, lines: tuple = ()) -> str:
    body = ["# Writ Project Config", "", "## Conventions", "", "- **Default Branch:** main"]
    if runner is not None:
        body.append(("- **Test Runner:** %s" % runner).rstrip())
    body.extend(lines)
    return "\n".join(body) + "\n"


def _ev_repo(root: Path, *, runner: str | None = EV_PYTEST, lines: tuple = (),
             files: dict | None = None, git: bool = True) -> Path:
    """Copy the fixture project to `root/repo`, write its config and any extra
    files, then `git init` and commit everything (unless `git=False`)."""
    repo = root / "repo"
    shutil.copytree(str(EV_PROJECT), str(repo))
    (repo / ".writ").mkdir()
    (repo / ".writ" / "config.md").write_text(_ev_config(runner, lines), encoding="utf-8")
    for rel, text in (files or {}).items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if git:
        _ev_git(repo, "-c", "init.defaultBranch=main", "init", "-q")
        _ev_git(repo, "add", "-A")
        _ev_git(repo, "-c", "user.name=Evidence Test", "-c", "user.email=evidence@example.com",
                "-c", "commit.gpgsign=false", "commit", "-q", "--no-verify", "-m", "base")
    return repo


def _ev_issue(issue: str = "`parse_limit()` accepts a negative limit", *,
              location: str | None = EV_LOCATION, severity: str = "Major",
              category: str = "criterion [AC-1.1]", evidence: str | None = None,
              block: str | None = None, indent: str = "  ", extra: tuple = ()) -> list:
    """One `### Issues Found` entry; `block` is the fenced code after Evidence."""
    lines = ["- **Issue:** %s" % issue]
    if location is not None:
        lines.append("- **Location:** %s" % location)
    lines += ["- **Severity:** %s" % severity, "- **Category:** %s" % category]
    if evidence is not None:
        lines.append("- **Evidence:** %s" % evidence)
    if block is not None:
        lines.append(indent + "```python")
        lines.extend((indent + ln) if ln else "" for ln in block.splitlines())
        lines.append(indent + "```")
    lines.extend(extra)
    lines.append("")
    return lines


def _ev_test(path: str = EV_REPRO, content: str = EV_REPRO_FAIL, **kwargs) -> list:
    return _ev_issue(evidence="test `%s`" % path, block=content, **kwargs)


def _ev_review(*issues: list, verdict: str | None = "FAIL",
               heading: str | None = "### Issues Found") -> str:
    lines: list = []
    if verdict is not None:
        lines += ["### EVALUATION_RESULT: %s" % verdict, ""]
    lines += ["### Summary", "Fixture review.", ""]
    if heading is not None:
        lines += [heading, ""]
        for issue in issues:
            lines += issue
    lines += ["### Drift Analysis", "", "**Overall Drift:** None", ""]
    return "\n".join(lines) + "\n"


def _ev_run(root: Path, repo: Path, review: str | None, *,
            changed: tuple | None = ("src/limits.py",), tests: str | None = None,
            checks: str | None = None, extra: tuple = (),
            env: dict | None = None) -> subprocess.CompletedProcess:
    """Run `evidence`. `review=None` points at a file that does not exist."""
    review_path = root / "review.md"
    if review is not None:
        review_path.write_text(review, encoding="utf-8")
    args = ["evidence", "--review-output", str(review_path), "--repo", str(repo)]
    if changed is not None:
        args += ["--changed", *changed]
    if tests is not None:
        (root / "tests-output.txt").write_text(tests, encoding="utf-8")
        args += ["--tests-output", str(root / "tests-output.txt")]
    if checks is not None:
        (root / "gate2-checks.txt").write_text(checks, encoding="utf-8")
        args += ["--checks", str(root / "gate2-checks.txt")]
    args += list(extra)
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, env=env if env is not None else _ev_env(),
                          cwd=str(root), timeout=300)


def _ev_summary(verdict: str, confirmed: int, advisory: int, unverifiable: int) -> str:
    return ("review-override evidence: %s (%d confirmed, %d advisory, %d unverifiable)"
            % (verdict, confirmed, advisory, unverifiable))


def _ev_unverifiable(reason: str) -> list:
    return ["unverifiable", "reason: %s" % reason,
            "review-override evidence: unverifiable (%s)" % reason]


def _ev_findings(stdout: str) -> dict:
    """`finding F<n>:` lines keyed by F<n>, the text after the colon."""
    found = {}
    for line in stdout.splitlines():
        match = re.match(r"^finding (F\d+): (.*)$", line)
        if match:
            found[match.group(1)] = match.group(2)
    return found


def _ev_argv(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _ev_module():
    spec = importlib.util.spec_from_file_location("review_override_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvidenceTestCase(unittest.TestCase):
    """Shared assertions for the Story 2 `evidence` tests."""

    def assert_output(self, proc: subprocess.CompletedProcess, expected: list) -> None:
        self.assertEqual(proc.stdout.splitlines(), expected, proc.stdout + proc.stderr)
        self.assertEqual(proc.returncode, 1 if expected[0] == "fail" else 0,
                         proc.stdout + proc.stderr)

    def assert_finding(self, proc: subprocess.CompletedProcess, key: str, text: str) -> None:
        self.assertEqual(_ev_findings(proc.stdout).get(key), text, proc.stdout + proc.stderr)


class EvidenceSkillRegistrationTests(unittest.TestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — the skill lints, carries
    its frontmatter, sections, kinds, and reason codes, and is registered in
    the manifest, the README, root `SKILL.md`, the config docs, and the
    generated trees. [AC-2.1]"""

    def skill_text(self) -> str:
        path = REPO_ROOT / EV_SKILL_REL
        self.assertTrue(path.is_file(), "%s missing" % EV_SKILL_REL)
        return path.read_text(encoding="utf-8")

    def test_skill_lints_pass(self) -> None:
        """AC-2.1 — `lint-skill.sh` prints `pass` on line 1 and exits 0."""
        self.skill_text()
        proc = subprocess.run(["bash", str(REPO_ROOT / "scripts" / "lint-skill.sh"), EV_SKILL_REL],
                              cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(proc.stdout.splitlines()[:1], ["pass"], proc.stdout + proc.stderr)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_skill_frontmatter_sections_kinds_and_reasons(self) -> None:
        """AC-2.1 — frontmatter keys, the three sections in order, the four
        kinds, the ADR-032 citation, and every reason code the spec leaves
        unnamed."""
        text = self.skill_text()
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
        self.assertIsNotNone(match, "no frontmatter")
        front = dict(re.findall(r"^([\w-]+):\s*(.*)$", match.group(1), re.MULTILINE))
        body = match.group(2)
        self.assertEqual(front.get("name"), EV_SKILL_NAME)
        self.assertTrue(front.get("description", "").strip('"'), front)
        self.assertEqual(front.get("disable-model-invocation"), "true")
        self.assertEqual(front.get("status"), "candidate")
        self.assertIn("2026-11-04-evidence-gated-review", front.get("status_evidence", ""))
        headings = [ln for ln in body.splitlines() if ln.startswith("## ")]
        required = ["## Purpose", "## When to Use", "## How to Apply"]
        for heading in required:
            self.assertIn(heading, headings)
        self.assertEqual([headings.index(h) for h in required],
                         sorted(headings.index(h) for h in required))
        for kind in ("test", "recorded", "check", "security-path"):
            self.assertIn("`%s`" % kind, body)
        self.assertIn(EV_ADR_CITE, body)
        flat = " ".join(body.split())
        self.assertIn("An import error at the top of the file, a syntax error, or a missing "
                      "fixture is a broken repro", flat)
        self.assertIn("an exception raised inside the test body counts as a test failure", flat)
        self.assertNotIn("decision-records/", body)
        for reason in EV_NEW_REASONS:
            self.assertIn("`%s" % reason, body, reason)

    def test_skill_registered_everywhere(self) -> None:
        """AC-2.1 — manifest entry (alphabetical), README row and live count,
        root `SKILL.md` row (alphabetical), the `Evidence Gate` config row and
        section beside `Reviewer Filters`, and current generated trees."""
        front = re.search(r'^description:\s*"(.*)"$', self.skill_text(), re.MULTILINE)
        self.assertIsNotNone(front)
        description = front.group(1)

        manifest = (REPO_ROOT / ".writ" / "manifest.yaml").read_text(encoding="utf-8")
        skills = manifest.split("\nskills:\n", 1)[1]
        names = re.findall(r"^  - name:\s*(\S+)", skills, re.MULTILINE)
        self.assertIn(EV_SKILL_NAME, names)
        self.assertEqual(names, sorted(names))
        entry = skills.split("  - name: %s\n" % EV_SKILL_NAME, 1)[1].split("\n  - name:", 1)[0]
        self.assertIn("    file: %s" % EV_SKILL_REL, entry)
        self.assertIn('    description: "%s"' % description, entry)
        self.assertIn("    status: candidate", entry)
        self.assertRegex(entry, r"    tags: \[[^\]]+\]")

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        table = readme.split("\n## Skills\n", 1)[1].split("\n## ", 1)[0]
        rows = [ln for ln in table.splitlines() if ln.startswith("| [`")]
        self.assertTrue(any(ln.startswith("| [`%s`](%s) |" % (EV_SKILL_NAME, EV_SKILL_REL))
                            for ln in rows), rows)
        count = re.search(r"(\d+) skills are live today", readme)
        self.assertIsNotNone(count)
        self.assertEqual(int(count.group(1)), len(rows))

        catalog = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        catalog_rows = re.findall(r"^\| `([\w-]+)` \| `(?:candidate|proven|promoted)` \| `skills/",
                                  catalog, re.MULTILINE)
        self.assertIn("| `%s` | `candidate` | `%s` | %s |" % (EV_SKILL_NAME, EV_SKILL_REL,
                                                            description), catalog)
        self.assertEqual(catalog_rows, sorted(catalog_rows))

        config_doc = (REPO_ROOT / ".writ" / "docs" / "config-format.md").read_text(encoding="utf-8")
        self.assertRegex(config_doc, r"(?m)^\| `Evidence Gate` \| .*\[Evidence Gate\]\(#evidence-gate\)")
        self.assertRegex(config_doc, r"(?m)^\| `Reviewer Filters` \| ")
        self.assertIn("\n## Reviewer Filters\n", config_doc)
        section = config_doc.split("\n## Evidence Gate\n", 1)
        self.assertEqual(len(section), 2, "no ## Evidence Gate section")
        section = section[1].split("\n## ", 1)[0]
        self.assertIn("- **Evidence Gate:** off", section)
        self.assertIn("python3 scripts/review-override.py switch --name evidence-gate --repo .",
                      section)

        for base in ("plugins/writ/skills", "cursor/plugin/skills"):
            copy = REPO_ROOT / base / EV_SKILL_NAME / "SKILL.md"
            self.assertTrue(copy.is_file(), "%s missing" % copy.relative_to(REPO_ROOT))
        proc = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "gen-platform-trees.py"),
                               "--check"], cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(proc.stdout.splitlines()[:1], ["pass"], proc.stdout + proc.stderr)


class EvidenceEnvelopeTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — the switch, usage
    errors, the review output read, the verdict gate, and the empty Issues
    section. [AC-2.2]"""

    def test_switch_off_any_case_runs_nothing(self) -> None:
        """AC-2.2 — `Evidence Gate: off` in any case prints `unverifiable` with
        `switch_off`, exits 0, and no repro runs."""
        for value in ("off", "OFF", "Off"):
            with self.subTest(value=value), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root, runner="jest",
                                lines=("- **Evidence Gate:** %s" % value,))
                argv = root / "argv.jsonl"
                proc = _ev_run(root, repo, _ev_review(_ev_test("src/limits.test.js")),
                               env=_ev_env(STUB_ARGV=str(argv)))
                self.assert_output(proc, _ev_unverifiable("switch_off"))
                self.assertEqual(_ev_argv(argv), [])
                self.assertFalse((repo / "src" / "limits.test.js").exists())

    def test_switch_absent_empty_on_or_malformed_proceeds(self) -> None:
        """AC-2.2 — no line, an empty value, `on`, or a malformed value lets
        the run proceed."""
        for lines in ((), ("- **Evidence Gate:**",), ("- **Evidence Gate:** on",),
                      ("- **Evidence Gate:** of",)):
            with self.subTest(lines=lines), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root, lines=lines)
                proc = _ev_run(root, repo, _ev_review())
                self.assert_output(proc, ["pass", _ev_summary("pass", 0, 0, 0)])

    def test_evidence_gate_switch_resolves(self) -> None:
        """AC-2.2 — `switch --name evidence-gate` resolves the config line."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write_config(repo, _switch_config("- **Evidence Gate:** OFF"))
            proc = _switch(["--name", "evidence-gate", "--repo", str(repo)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.splitlines(),
                         _switch_expected("evidence-gate", "off", "config_off"))

    def test_missing_review_output_flag_is_usage_error(self) -> None:
        """AC-2.2 — no `--review-output`: exit 2, stdout empty, usage on stderr."""
        with TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(SCRIPT), "evidence", "--repo", tmp],
                                  capture_output=True, text=True, env=_ev_env())
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_unknown_surface_is_usage_error(self) -> None:
        """AC-2.2 — `--surface` other than `gate3` or `review`: exit 2, stdout empty."""
        for value in ("gate2", "Review", ""):
            with self.subTest(value=value), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root, git=False)
                proc = _ev_run(root, repo, _ev_review(), extra=("--surface", value))
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(proc.stdout, "")
                self.assertIn("usage:", proc.stderr)

    def test_known_surfaces_and_later_story_flags_parse(self) -> None:
        """AC-2.2 — `--surface gate3|review`, `--manifest-out`, and `--timeout`
        parse; with nothing confirmed, `--manifest-out` writes nothing. `review`
        (Story 5) adds its header line and finds no registry here. `--prior`
        has behavior since Story 4 (`EvidenceManifestTests`)."""
        for case in ("gate3", "review", "manifest"):
            with self.subTest(case=case), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                out = root / "out"
                extra = ("--surface", case) if case != "manifest" else (
                    "--manifest-out", str(out / "evidence.json"), "--timeout", "30")
                proc = _ev_run(root, repo, _ev_review(), extra=extra)
                header = ["evidence-gate: on"] if case == "review" else []
                self.assert_output(proc, ["pass"] + header + [_ev_summary("pass", 0, 0, 0)])
                self.assertFalse(out.exists())

    def test_missing_review_file_is_no_review_output(self) -> None:
        """AC-2.2 — a missing or unreadable review file: `unverifiable`,
        `no_review_output`, exit 0 (Nil shadow path)."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, None)
            self.assert_output(proc, _ev_unverifiable("no_review_output"))
            (root / "review.md").mkdir()
            proc = _ev_run(root, repo, None)
            self.assert_output(proc, _ev_unverifiable("no_review_output"))

    def test_verdict_other_than_fail_is_verdict_not_fail(self) -> None:
        """AC-2.2 — PASS, PAUSE, or no verdict line: `verdict_not_fail <verdict>`."""
        for verdict, word in (("PASS", "PASS"), ("PAUSE", "PAUSE"), (None, "none")):
            with self.subTest(verdict=verdict), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                proc = _ev_run(root, repo, _ev_review(_ev_test(), verdict=verdict))
                self.assert_output(proc, _ev_unverifiable("verdict_not_fail %s" % word))
                self.assertFalse((repo / "tests").exists())

    def test_fail_with_empty_issues_passes_with_zero_counts(self) -> None:
        """AC-2.2 — a FAIL with an empty or missing Issues Found section prints
        `pass` and `0 confirmed, 0 advisory, 0 unverifiable` (Empty shadow path)."""
        for heading in ("### Issues Found", "### Issues Found (if FAIL)", None):
            with self.subTest(heading=heading), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                proc = _ev_run(root, repo, _ev_review(heading=heading))
                self.assert_output(proc, ["pass", _ev_summary("pass", 0, 0, 0)])

    def test_bold_fail_verdict_counts(self) -> None:
        """AC-2.2 — `### REVIEW_RESULT: **FAIL**` reads as FAIL."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, _ev_review(verdict="**FAIL**"))
            self.assert_output(proc, ["pass", _ev_summary("pass", 0, 0, 0)])


class EvidenceSelectionTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — which findings are
    evaluated, the finding keys, the Evidence field parse, the verdict line,
    and the five-run cap. [AC-2.3]"""

    def run_one(self, *issues: list, runner: str = "jest", changed: tuple = ("src/limits.py",),
                **kwargs) -> tuple:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root, runner=runner)
            argv = root / "argv.jsonl"
            proc = _ev_run(root, repo, _ev_review(*issues), changed=changed,
                           env=_ev_env(STUB_ARGV=str(argv)), **kwargs)
            return proc, _ev_argv(argv)

    def test_lower_severity_is_advisory_and_never_runs(self) -> None:
        """AC-2.3 — Minor (or any non-Critical, non-Major) findings are advisory
        and their repros never run."""
        for severity in ("Minor", "Low", "Taste"):
            with self.subTest(severity=severity):
                proc, runs = self.run_one(_ev_test("src/limits.test.js", severity=severity))
                self.assert_output(proc, [
                    "pass", "finding F1: advisory (low_severity %s)%s" % (severity, EV_AT),
                    _ev_summary("pass", 0, 1, 0)])
                self.assertEqual(runs, [])

    def test_location_outside_change_set_is_advisory(self) -> None:
        """AC-2.3 — a Location outside `--changed`, or no Location at all, is
        `advisory (location_outside_change_set)` and never runs."""
        proc, runs = self.run_one(_ev_test("src/limits.test.js", location="`src/routes.py:5`"))
        self.assert_finding(proc, "F1", "advisory (location_outside_change_set) at src/routes.py")
        self.assertEqual(runs, [])
        proc, runs = self.run_one(_ev_test("src/limits.test.js", location=None))
        self.assert_finding(proc, "F1", "advisory (location_outside_change_set)")
        proc, runs = self.run_one(_ev_test("src/limits.test.js"), changed=())
        self.assert_finding(proc, "F1", "advisory (location_outside_change_set)" + EV_AT)
        self.assertEqual(runs, [])

    def test_location_normalizes_before_matching(self) -> None:
        """AC-2.3 — `./src/limits.py:3-9` and a `./` changed path both match."""
        proc, runs = self.run_one(_ev_test("src/limits.test.js", location="`./src/limits.py:3-9`"),
                                  changed=("./src/limits.py",))
        self.assert_finding(proc, "F1", "confirmed (test src/limits.test.js, exit 1)" + EV_AT)

    def test_no_claim_is_advisory(self) -> None:
        """AC-2.3 — no AC ID and a Category other than security or architecture
        is `advisory (no_claim)`."""
        for category in ("taste", "criterion", ""):
            with self.subTest(category=category):
                proc, runs = self.run_one(_ev_test("src/limits.test.js", category=category))
                self.assert_finding(proc, "F1", "advisory (no_claim)" + EV_AT)
                self.assertEqual(runs, [])

    def test_claim_from_category_issue_or_location(self) -> None:
        """AC-2.3 — `security`, `architecture`, or an AC ID in the Issue or
        Location text is a claim."""
        cases = (
            {"category": "security"},
            {"category": "Architecture"},
            {"category": "criterion", "issue": "AC-2.3 is not met"},
            {"category": "criterion", "location": "`src/limits.py:3` (AC-2.3)"},
        )
        for kwargs in cases:
            with self.subTest(**kwargs):
                proc, runs = self.run_one(_ev_test("src/limits.test.js", **kwargs))
                self.assert_finding(proc, "F1", "confirmed (test src/limits.test.js, exit 1)" + EV_AT)

    def test_no_evidence_is_advisory(self) -> None:
        """AC-2.3 — a selected finding with no Evidence field is `advisory (no_evidence)`."""
        proc, runs = self.run_one(_ev_issue(severity="Critical"))
        self.assert_output(proc, ["pass", "finding F1: advisory (no_evidence)" + EV_AT,
                                  _ev_summary("pass", 0, 1, 0)])

    def test_unknown_kind_and_missing_test_block(self) -> None:
        """AC-2.3 — an unknown kind word and a `test` field with no fenced
        block are unverifiable with their own reasons."""
        proc, runs = self.run_one(_ev_issue(evidence="screenshot `shot.png`"),
                                  _ev_issue(evidence="test `src/limits.test.js`"))
        self.assert_finding(proc, "F1", "advisory (unverifiable unknown_kind screenshot)" + EV_AT)
        self.assert_finding(proc, "F2", "advisory (unverifiable missing_test_block)" + EV_AT)
        self.assertEqual(runs, [])

    def test_keys_follow_output_order(self) -> None:
        """AC-2.3 — keys run F1 to Fn in output order across every severity."""
        proc, runs = self.run_one(_ev_issue(severity="Minor"),
                                  _ev_test("src/limits.test.js", severity="Critical"),
                                  _ev_issue(severity="Major", category="taste"))
        self.assert_output(proc, [
            "fail",
            "finding F1: advisory (low_severity Minor)" + EV_AT,
            "finding F2: confirmed (test src/limits.test.js, exit 1)" + EV_AT,
            "finding F3: advisory (no_claim)" + EV_AT,
            "reason: confirmed F2",
            _ev_summary("fail", 1, 2, 0)])

    def test_field_names_ignore_case_and_bold(self) -> None:
        """AC-2.3 — `Severity:` and `evidence:` without bold, any case, still parse."""
        issue = ["- **Issue:** negative limit", "- Location: `src/limits.py:3`",
                 "- severity: major", "- CATEGORY: criterion [AC-1.1]",
                 "- evidence: test `src/limits.test.js`", "  ```js",
                 "  test('x', () => {})", "  ```", ""]
        proc, runs = self.run_one(issue)
        self.assert_finding(proc, "F1", "confirmed (test src/limits.test.js, exit 1)" + EV_AT)

    def test_second_evidence_field_is_ignored(self) -> None:
        """AC-2.3 — a second Evidence field is ignored with `extra_evidence F<n>`."""
        issue = _ev_test("src/limits.test.js",
                         extra=("- **Evidence:** test `src/other.test.js`",
                                "  ```js", "  x", "  ```"))
        proc, runs = self.run_one(issue)
        self.assert_output(proc, [
            "fail", "finding F1: confirmed (test src/limits.test.js, exit 1)" + EV_AT,
            "reason: extra_evidence F1", "reason: confirmed F1", _ev_summary("fail", 1, 0, 0)])
        self.assertEqual(runs, [["src/limits.test.js"]])

    def test_comment_lines_in_an_unindented_block_do_not_end_the_section(self) -> None:
        """AC-2.3 — `# comment` lines inside a fence are code, not headings."""
        content = "# arrange\nfrom src.limits import parse_limit\n\n\n# act and assert\n" \
                  "def test_negative_limit_rejected():\n    assert parse_limit(\"-1\") is None\n"
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, _ev_review(_ev_test(content=content, indent=""),
                                                  _ev_issue()))
            self.assert_output(proc, [
                "fail", "finding F1: confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT),
                "finding F2: advisory (no_evidence)" + EV_AT, "reason: confirmed F1",
                _ev_summary("fail", 1, 1, 0)])

    def test_line_one_is_fail_only_with_a_confirmed_finding(self) -> None:
        """AC-2.3 — line 1 `fail` (exit 1) when a finding is confirmed, `pass`
        (exit 0) when none is."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root, runner="jest")
            proc = _ev_run(root, repo, _ev_review(_ev_test("src/limits.test.js")),
                           env=_ev_env(STUB_MODE="pass"))
            self.assert_output(proc, [
                "pass", "finding F1: advisory (repro_passed)" + EV_AT, _ev_summary("pass", 0, 1, 0)])

    def test_five_run_cap(self) -> None:
        """AC-2.3 — at most five `test` or `check` runs per call; later ones are
        `unverifiable repro_cap`; `recorded` costs no run."""
        issues = [_ev_test("src/a%d.test.js" % n) for n in range(1, 6)]
        issues.append(_ev_issue(evidence="check `lint src/limits.py`"))
        issues.append(_ev_test("src/a7.test.js"))
        issues.append(_ev_issue(evidence="recorded `tests/test_limits.py::test_negative`"))
        tests = "command: pytest\nexit code: 1\nFAILED tests/test_limits.py::test_negative\n"
        proc, runs = self.run_one(*issues, tests=tests, checks="lint\n")
        found = _ev_findings(proc.stdout)
        for n in range(1, 6):
            self.assertEqual(found["F%d" % n],
                             "confirmed (test src/a%d.test.js, exit 1)%s" % (n, EV_AT))
        self.assertEqual(found["F6"], "advisory (unverifiable repro_cap)" + EV_AT)
        self.assertEqual(found["F7"], "advisory (unverifiable repro_cap)" + EV_AT)
        self.assertEqual(found["F8"], "confirmed (recorded tests/test_limits.py::test_negative, "
                                      "exit 1)" + EV_AT)
        self.assertEqual(len(runs), 5)
        self.assertEqual(proc.stdout.splitlines()[-1], _ev_summary("fail", 6, 0, 2))


class EvidenceRecordedTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — the `recorded` kind
    against the `recorded_test_results` text. [AC-2.3]"""

    def run_recorded(self, test_id: str, tests: str | None) -> subprocess.CompletedProcess:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            return _ev_run(root, repo, _ev_review(_ev_issue(evidence="recorded `%s`" % test_id)),
                           tests=tests)

    def test_failed_in_a_failing_run_is_confirmed(self) -> None:
        """AC-2.3 — exit non-zero and the test named as failed: confirmed."""
        cases = (
            ("tests/test_limits.py::test_negative",
             "FAILED tests/test_limits.py::test_negative - assert -1 is None"),
            ("tests/test_limits.py::test_negative", "tests/test_limits.py::test_negative FAILED"),
            ("tests/test_limits.py::LimitTests::test_negative",
             "FAILED tests/test_limits.py::LimitTests::test_negative"),
            ("tests/test_limits.py::test_negative", "FAILED tests/test_limits.py::test_negative[-1]"),
        )
        for test_id, line in cases:
            with self.subTest(line=line):
                tests = "command: python3 -m pytest\nexit code: 1\n%s\n1 failed\n" % line
                proc = self.run_recorded(test_id, tests)
                self.assert_output(proc, [
                    "fail", "finding F1: confirmed (recorded %s, exit 1)%s" % (test_id, EV_AT),
                    "reason: confirmed F1", _ev_summary("fail", 1, 0, 0)])

    def test_passed_is_advisory(self) -> None:
        """AC-2.3 — the test is in the recorded run and passed: `recorded_passed`."""
        cases = (
            "command: python3 -m pytest tests/test_limits.py\nexit code: 0\n2 passed\n",
            "command: python3 -m pytest -v\nexit code: 1\n"
            "tests/test_limits.py::test_negative PASSED\ntests/test_other.py::test_x FAILED\n",
            # A FAILED line in a run that exited 0 does not confirm.
            "command: python3 -m pytest\nexit code: 0\nFAILED tests/test_limits.py::test_negative\n",
        )
        for tests in cases:
            with self.subTest(tests=tests):
                proc = self.run_recorded("tests/test_limits.py::test_negative", tests)
                self.assert_finding(proc, "F1", "advisory (recorded_passed)" + EV_AT)
                self.assertEqual(proc.stdout.splitlines()[0], "pass")

    def test_absent_from_the_run_is_unverifiable(self) -> None:
        """AC-2.3 — the test is not in the recorded run: `test_not_in_run`; a
        longer name that only starts with the cited one does not count."""
        tests = ("command: python3 -m pytest tests/test_other.py\nexit code: 1\n"
                 "FAILED tests/test_limits.py::test_negative_two\n")
        proc = self.run_recorded("tests/test_limits.py::test_negative", tests)
        self.assert_finding(proc, "F1", "advisory (unverifiable test_not_in_run)" + EV_AT)

    def test_no_recorded_run_is_unverifiable(self) -> None:
        """AC-2.3 — no `--tests-output`, or a file with no `exit code:` line:
        `no_recorded_run`."""
        for tests in (None, "FAILED tests/test_limits.py::test_negative\n"):
            with self.subTest(tests=tests):
                proc = self.run_recorded("tests/test_limits.py::test_negative", tests)
                self.assert_finding(proc, "F1", "advisory (unverifiable no_recorded_run)" + EV_AT)


class EvidenceCheckTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — the `check` kind runs
    only a Gate 2 recorded command and confirms on a changed file in its
    output. [AC-2.3]"""

    def run_check(self, command: str, checks: str | None = "lint\n", **env: str) -> tuple:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            argv = root / "argv.jsonl"
            proc = _ev_run(root, repo, _ev_review(_ev_issue(evidence="check `%s`" % command)),
                           checks=checks, env=_ev_env(STUB_ARGV=str(argv), **env),
                           extra=("--timeout", "1") if env.get("STUB_SLEEP") else ())
            return proc, _ev_argv(argv), repo

    def test_names_a_changed_file_is_confirmed(self) -> None:
        """AC-2.3 — a recorded command that exits non-zero and names a changed
        file, relative or absolute, is confirmed."""
        for mode in ("names", "absolute"):
            with self.subTest(mode=mode):
                proc, runs, _ = self.run_check("lint src/limits.py", STUB_MODE=mode)
                self.assert_output(proc, [
                    "fail", "finding F1: confirmed (check lint src/limits.py, exit 1)" + EV_AT,
                    "reason: confirmed F1", _ev_summary("fail", 1, 0, 0)])
                self.assertEqual(runs, [["src/limits.py"]])

    def test_exit_zero_or_no_changed_file_is_advisory(self) -> None:
        """AC-2.3 — exit 0 is `check_passed`; a non-zero exit that names no
        changed file is `no_changed_file_named`."""
        proc, runs, _ = self.run_check("lint src/limits.py", STUB_MODE="clean")
        self.assert_finding(proc, "F1", "advisory (check_passed)" + EV_AT)
        proc, runs, _ = self.run_check("lint src/limits.py", STUB_MODE="other")
        self.assert_finding(proc, "F1", "advisory (no_changed_file_named)" + EV_AT)

    def test_no_record_or_unrecorded_command_never_runs(self) -> None:
        """AC-2.3 — no `--checks` is `no_gate2_record`; a command that does not
        start with a recorded command, token by token, is `command_not_recorded`."""
        proc, runs, _ = self.run_check("lint src/limits.py", checks=None)
        self.assert_finding(proc, "F1", "advisory (unverifiable no_gate2_record)" + EV_AT)
        self.assertEqual(runs, [])
        for record in ("ruff check\n", "lint --strict\n", "lin\n", "\n"):
            with self.subTest(record=record):
                proc, runs, _ = self.run_check("lint src/limits.py", checks=record)
                self.assert_finding(proc, "F1",
                                    "advisory (unverifiable command_not_recorded)" + EV_AT)
                self.assertEqual(runs, [])
        proc, runs, _ = self.run_check("lint --strict src/limits.py",
                                       checks="ruff check\nlint --strict\n", STUB_MODE="names")
        self.assert_finding(proc, "F1",
                            "confirmed (check lint --strict src/limits.py, exit 1)" + EV_AT)

    def test_missing_command_binary_is_unverifiable(self) -> None:
        """AC-2.3 — a recorded command whose binary is missing is `command_not_found`."""
        proc, runs, _ = self.run_check("/nonexistent/bin/lint src/limits.py",
                                       checks="/nonexistent/bin/lint\n")
        self.assert_finding(proc, "F1", "advisory (unverifiable command_not_found)" + EV_AT)

    def test_timeout_is_unverifiable(self) -> None:
        """AC-2.3 — a check that outlives `--timeout` is `unverifiable timeout <s>`."""
        start = time.monotonic()
        proc, runs, _ = self.run_check("lint src/limits.py", STUB_SLEEP="30")
        self.assertLess(time.monotonic() - start, 20)
        self.assert_finding(proc, "F1", "advisory (unverifiable timeout 1)" + EV_AT)


class EvidenceSecurityPathTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — the `security-path` kind
    confirms on two resolving citations with the sink in the change set. [AC-2.3]"""

    def run_path(self, evidence: str, *, category: str = "security",
                 severity: str = "Major") -> subprocess.CompletedProcess:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            (root / "outside.py").write_text("x = 1\n", encoding="utf-8")
            return _ev_run(root, repo, _ev_review(_ev_issue(
                evidence=evidence, category=category, severity=severity)))

    def test_resolving_citations_are_confirmed(self) -> None:
        """AC-2.3 — Category security, Major or Critical, both citations
        resolve, sink in the change set: confirmed, with no run."""
        for severity in ("Major", "Critical"):
            for evidence in ("security-path source `src/routes.py:5` sink `src/limits.py:3`",
                             "security-path source: src/routes.py:5 sink: src/limits.py:3"):
                with self.subTest(severity=severity, evidence=evidence):
                    proc = self.run_path(evidence, severity=severity)
                    self.assert_output(proc, [
                        "fail", "finding F1: confirmed (security-path source src/routes.py:5 "
                                "sink src/limits.py:3)" + EV_AT,
                        "reason: confirmed F1", _ev_summary("fail", 1, 0, 0)])

    def test_bad_citation_is_unverifiable(self) -> None:
        """AC-2.3 — a citation that does not resolve is `bad_citation <token>`."""
        cases = (
            ("security-path source src/routes.py:99 sink src/limits.py:3", "src/routes.py:99"),
            ("security-path source src/routes.py:5 sink src/missing.py:1", "src/missing.py:1"),
            ("security-path source ../outside.py:1 sink src/limits.py:3", "../outside.py:1"),
            ("security-path source src/routes.py sink src/limits.py:3", "src/routes.py"),
            ("security-path sink src/limits.py:3", "source"),
        )
        for evidence, token in cases:
            with self.subTest(evidence=evidence):
                proc = self.run_path(evidence)
                self.assert_finding(proc, "F1",
                                    "advisory (unverifiable bad_citation %s)%s" % (token, EV_AT))

    def test_sink_outside_change_set_is_advisory(self) -> None:
        """AC-2.3 — a sink outside the change set is
        `advisory (location_outside_change_set)` (a Story 2 decision)."""
        proc = self.run_path("security-path source src/limits.py:3 sink src/routes.py:5")
        self.assert_finding(proc, "F1", "advisory (location_outside_change_set)" + EV_AT)

    def test_not_security_is_unverifiable(self) -> None:
        """AC-2.3 — `security-path` on a non-security finding is `not_security`."""
        proc = self.run_path("security-path source src/routes.py:5 sink src/limits.py:3",
                             category="criterion [AC-1.1]")
        self.assert_finding(proc, "F1", "advisory (unverifiable not_security)" + EV_AT)


class EvidenceRunnerTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — `test` repros through
    the real pytest fixture and the stub runners: each runner's test-failed
    class, runner detection, and repro path rules. [AC-2.4]"""

    def run_test(self, *issues: list, runner: str | None = EV_PYTEST, files: dict | None = None,
                 extra: tuple = (), **env: str) -> tuple:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root, runner=runner, files=files)
            argv = root / "argv.jsonl"
            proc = _ev_run(root, repo, _ev_review(*issues), extra=extra,
                           env=_ev_env(STUB_ARGV=str(argv), **env))
            leftovers = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*")
                               if ".git" not in p.relative_to(repo).parts
                               and "__pycache__" not in p.parts)
            return proc, _ev_argv(argv), leftovers

    def test_pytest_failure_is_confirmed(self) -> None:
        """AC-2.4 — a real pytest repro that fails on exit 1 is confirmed, the
        repro and its created parent are gone after (Happy shadow path)."""
        proc, _, leftovers = self.run_test(_ev_test())
        self.assert_output(proc, [
            "fail", "finding F1: confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT),
            "reason: confirmed F1", _ev_summary("fail", 1, 0, 0)])
        self.assertNotIn(EV_REPRO, leftovers)
        self.assertNotIn("tests", leftovers)

    def test_pytest_pass_is_advisory(self) -> None:
        """AC-2.4 — a pytest repro that passes is `advisory (repro_passed)`."""
        proc, _, leftovers = self.run_test(_ev_test(content=EV_REPRO_PASS))
        self.assert_output(proc, ["pass", "finding F1: advisory (repro_passed)" + EV_AT,
                                  _ev_summary("pass", 0, 1, 0)])
        self.assertNotIn(EV_REPRO, leftovers)

    def test_pytest_collection_error_is_unverifiable(self) -> None:
        """AC-2.4 — a repro with a syntax error (pytest exit 2) is
        `unverifiable collection_error`."""
        proc, _, leftovers = self.run_test(_ev_test(content=EV_REPRO_BROKEN))
        self.assert_output(proc, [
            "pass", "finding F1: advisory (unverifiable collection_error)" + EV_AT,
            _ev_summary("pass", 0, 0, 1)])
        self.assertNotIn(EV_REPRO, leftovers)

    def test_pytest_setup_error_is_unverifiable(self) -> None:
        """AC-2.4 — a repro that errors in setup (a missing fixture: pytest
        exit 1 with `1 error`, no failed count) is `collection_error`."""
        content = "def test_x(no_such_fixture):\n    assert True\n"
        proc, _, leftovers = self.run_test(_ev_test(content=content))
        self.assert_output(proc, [
            "pass", "finding F1: advisory (unverifiable collection_error)" + EV_AT,
            _ev_summary("pass", 0, 0, 1)])
        self.assertNotIn(EV_REPRO, leftovers)

    def test_pytest_exit_one_needs_a_failed_count(self) -> None:
        """AC-2.4 — pytest confirms only on exit 1 with a failed count; an
        interpreter without pytest also exits 1 and is `collection_error`."""
        module = _ev_module()
        self.assertEqual(module._classify("pytest", 1, "python3: No module named pytest\n"),
                         ("unverifiable", "collection_error"))
        self.assertEqual(module._classify("pytest", 1, "=== 1 error in 0.01s ===\n"),
                         ("unverifiable", "collection_error"))
        self.assertEqual(module._classify("pytest", 1, "=== 1 failed, 2 passed in 0.02s ===\n"),
                         ("confirmed", ""))

    def test_repro_is_deleted_when_the_run_raises(self) -> None:
        """AC-2.4 — an unexpected exception or an interrupt during the run
        still deletes the repro, then propagates."""
        module = _ev_module()
        for error in (RuntimeError("boom"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), TemporaryDirectory() as tmp:
                repo = _ev_repo(Path(tmp)).resolve()
                finding = module.Finding("F1")
                finding.block = EV_REPRO_FAIL
                runner, _ = module._detect_runner(EV_PYTEST, repo)
                run = module.EvidenceRun(repo, module._git_root(repo), {"src/limits.py"},
                                         runner, "", None, 5)

                def raising(*args, **kwargs):
                    self.assertTrue((repo / EV_REPRO).is_file())
                    raise error

                with mock.patch.object(module, "_run_bounded", raising):
                    with self.assertRaises(type(error)):
                        run.test(finding, EV_REPRO)
                self.assertFalse((repo / EV_REPRO).exists())

    def test_interrupted_run_kills_the_process_group(self) -> None:
        """AC-2.4 — an interrupt while waiting kills the runner's own session
        group, so no runner outlives the call."""
        module = _ev_module()

        class InterruptedProc:
            pid = 0

            def communicate(self, timeout=None):
                raise KeyboardInterrupt

        fake = types.SimpleNamespace(Popen=lambda *args, **kwargs: InterruptedProc(),
                                     DEVNULL=subprocess.DEVNULL, PIPE=subprocess.PIPE,
                                     STDOUT=subprocess.STDOUT,
                                     TimeoutExpired=subprocess.TimeoutExpired)
        killed: list = []
        with mock.patch.object(module, "subprocess", fake), \
                mock.patch.object(module, "_kill_group", killed.append):
            with self.assertRaises(KeyboardInterrupt):
                module._run_bounded(["runner"], Path("."), 5)
        self.assertEqual(len(killed), 1)

    def test_existing_parent_stays(self) -> None:
        """AC-2.4 — a repro beside existing files leaves its directory in place."""
        proc, _, leftovers = self.run_test(_ev_test("src/test_limits_repro.py"))
        self.assert_finding(proc, "F1", "confirmed (test src/test_limits_repro.py, exit 1)" + EV_AT)
        self.assertIn("src/limits.py", leftovers)
        self.assertNotIn("src/test_limits_repro.py", leftovers)

    def test_stub_runner_classes(self) -> None:
        """AC-2.4 — jest, vitest, go test, cargo test, rspec, and `npm test`:
        confirmed only in the runner's test-failed class, advisory on a pass,
        otherwise `collection_error`; each run gets the scoped command."""
        cases = (
            ("jest", "src/limits.test.js", ["src/limits.test.js"],
             {"fail": "confirmed (test src/limits.test.js, exit 1)", "pass": "advisory (repro_passed)",
              "broken": "advisory (unverifiable collection_error)",
              "suite_error": "advisory (unverifiable collection_error)",
              "no_tests": "advisory (unverifiable collection_error)"}),
            ("vitest", "src/limits.test.ts", ["run", "src/limits.test.ts"],
             {"fail": "confirmed (test src/limits.test.ts, exit 1)", "pass": "advisory (repro_passed)",
              "broken": "advisory (unverifiable collection_error)",
              "error_first": "advisory (unverifiable collection_error)",
              "no_tests": "advisory (unverifiable collection_error)"}),
            ("go test ./...", "pkg/limits_test.go", ["test", "./pkg"],
             {"fail": "confirmed (test pkg/limits_test.go, exit 1)", "pass": "advisory (repro_passed)",
              "build": "advisory (unverifiable collection_error)",
              "setup": "advisory (unverifiable collection_error)",
              "mixed": "advisory (unverifiable collection_error)"}),
            ("cargo test", "tests/limits_repro.rs", ["test", "--test", "limits_repro"],
             {"fail": "confirmed (test tests/limits_repro.rs, exit 101)",
              "pass": "advisory (repro_passed)",
              "compile": "advisory (unverifiable collection_error)",
              "mixed": "advisory (unverifiable collection_error)"}),
            ("rspec", "spec/limits_spec.rb", ["spec/limits_spec.rb"],
             {"fail": "confirmed (test spec/limits_spec.rb, exit 1)", "pass": "advisory (repro_passed)",
              "outside": "advisory (unverifiable collection_error)",
              "outside_fail": "advisory (unverifiable collection_error)"}),
            ("npm test", "src/limits.test.js", ["test", "--", "src/limits.test.js"],
             {"fail": "confirmed (test src/limits.test.js, exit 1)", "pass": "advisory (repro_passed)"}),
        )
        package = {"package.json": json.dumps({"scripts": {"test": "jest"}})}
        for runner, path, args, modes in cases:
            for mode, expected in modes.items():
                with self.subTest(runner=runner, mode=mode):
                    proc, runs, leftovers = self.run_test(_ev_test(path), runner=runner,
                                                          files=package, STUB_MODE=mode)
                    self.assert_finding(proc, "F1", expected + EV_AT)
                    self.assertEqual(runs, [args])
                    self.assertNotIn(path, leftovers)
                    top = path.split("/")[0]
                    if top != "src":
                        self.assertNotIn(top, leftovers)

    def test_detection_skips_prefixes_and_scopes_the_command(self) -> None:
        """AC-2.4 — detection skips `uv run`, `poetry run`, `bundle exec`,
        `npx`, `pnpm`, `yarn`, and `python* -m`, drops a `(detected: …)` note,
        and builds each runner's scoped command."""
        module = _ev_module()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": "vitest --silent"}}), encoding="utf-8")
            cases = (
                ("pytest -q tests", "tests/test_x.py", ["pytest", "tests/test_x.py"]),
                ("uv run pytest", "test_x.py", ["uv", "run", "pytest", "test_x.py"]),
                ("poetry run pytest", "a/b_test.py", ["poetry", "run", "pytest", "a/b_test.py"]),
                ("python3 -m pytest", "t/test_a.py", ["python3", "-m", "pytest", "t/test_a.py"]),
                ("python -m pytest", "t/test_a.py", ["python", "-m", "pytest", "t/test_a.py"]),
                ("/usr/bin/python3.9 -m pytest", "t/test_a.py",
                 ["/usr/bin/python3.9", "-m", "pytest", "t/test_a.py"]),
                (EV_PYTEST, "t/test_a.py", [sys.executable, "-m", "pytest", "t/test_a.py"]),
                ("npx jest", "a.test.js", ["npx", "jest", "a.test.js"]),
                ("pnpm jest --ci", "a.spec.ts", ["pnpm", "jest", "a.spec.ts"]),
                ("yarn vitest", "a.test.ts", ["yarn", "vitest", "run", "a.test.ts"]),
                ("vitest run --reporter=dot", "a.test.ts", ["vitest", "run", "a.test.ts"]),
                ("bundle exec rspec", "spec/a_spec.rb", ["bundle", "exec", "rspec", "spec/a_spec.rb"]),
                ("go test ./...", "x_test.go", ["go", "test", "./."]),
                ("go test -race", "a/b/x_test.go", ["go", "test", "./a/b"]),
                ("cargo test --all", "tests/it.rs", ["cargo", "test", "--test", "it"]),
                ("jest (detected: package.json scripts.test)", "a.test.js", ["jest", "a.test.js"]),
                ("npm test", "a.test.ts", ["npm", "test", "--", "run", "a.test.ts"]),
                ("npm run test", "a.test.ts", ["npm", "run", "test", "--", "run", "a.test.ts"]),
            )
            for value, path, want in cases:
                with self.subTest(value=value):
                    runner, reason = module._detect_runner(value, repo)
                    self.assertEqual(reason, "")
                    self.assertEqual(module._scoped_command(runner, path), want)
            for value, reason in (("make test", "unknown_runner make"),
                                  ("go build", "unknown_runner go"),
                                  ("cargo bench", "unknown_runner cargo"),
                                  ("uv run", "unknown_runner uv"),
                                  ("pytest 'unbalanced", "unknown_runner pytest")):
                with self.subTest(value=value):
                    self.assertEqual(module._detect_runner(value, repo), (None, reason))
            (repo / "package.json").unlink()
            self.assertEqual(module._detect_runner("npm test", repo), (None, "unknown_runner npm"))

    def test_runner_file_patterns(self) -> None:
        """AC-2.4 — each runner's own test-file pattern decides `not_a_test_path`."""
        module = _ev_module()
        good = {
            "pytest": ("test_a.py", "tests/test_a.py", "pkg/a_test.py"),
            "jest": ("a.test.js", "src/a.spec.tsx", "src/__tests__/a.js"),
            "vitest": ("a.test.ts", "a.spec.mjs", "__tests__/deep/a.ts"),
            "go": ("pkg/a_test.go", "a_test.go"),
            "cargo": ("tests/a.rs", "crates/x/tests/it.rs"),
            "rspec": ("spec/a_spec.rb", "a_spec.rb"),
        }
        bad = {
            "pytest": ("tests/a.py", "test_a.txt", "tests/conftest.py"),
            "jest": ("src/a.js", "tests/a.js"),
            "vitest": ("src/a.ts",),
            "go": ("pkg/a.go", "_test.go"),
            "cargo": ("src/a.rs", "tests/sub/a.rs", "a.rs"),
            "rspec": ("spec/a.rb", "a_spec.py"),
        }
        for kind, paths in good.items():
            for path in paths:
                with self.subTest(kind=kind, path=path):
                    self.assertTrue(module._test_path_ok(kind, path))
        for kind, paths in bad.items():
            for path in paths:
                with self.subTest(kind=kind, path=path):
                    self.assertFalse(module._test_path_ok(kind, path))

    def test_unknown_runner_is_unverifiable(self) -> None:
        """AC-2.4 — `Test Runner: make test` makes the finding `unknown_runner make`."""
        proc, runs, leftovers = self.run_test(_ev_test(), runner="make test")
        self.assert_output(proc, [
            "pass", "finding F1: advisory (unverifiable unknown_runner make)" + EV_AT,
            _ev_summary("pass", 0, 0, 1)])
        self.assertNotIn("tests", leftovers)

    def test_no_test_runner_leaves_the_call_unverifiable(self) -> None:
        """AC-2.4 — no `Test Runner` line (or an empty one) and nothing decided
        otherwise: line 1 `unverifiable no_test_runner`."""
        for runner in (None, ""):
            with self.subTest(runner=runner):
                proc, runs, leftovers = self.run_test(_ev_test(), _ev_issue(severity="Critical"),
                                                      runner=runner)
                self.assert_output(proc, _ev_unverifiable("no_test_runner"))
                self.assertNotIn("tests", leftovers)

    def test_no_test_runner_with_a_decided_finding_still_decides(self) -> None:
        """AC-2.4 — with no `Test Runner`, the `test` finding is
        `no_test_runner` but a decided `security-path` finding sets line 1."""
        proc, runs, leftovers = self.run_test(
            _ev_test(), _ev_issue(category="security",
                                  evidence="security-path source src/routes.py:5 sink src/limits.py:3"),
            runner=None)
        self.assert_output(proc, [
            "fail", "finding F1: advisory (unverifiable no_test_runner)" + EV_AT,
            "finding F2: confirmed (security-path source src/routes.py:5 sink src/limits.py:3)"
            + EV_AT, "reason: confirmed F2", _ev_summary("fail", 1, 0, 1)])

    def test_no_test_runner_with_only_minor_findings_passes(self) -> None:
        """AC-2.4 — no `Test Runner` and no selected finding: `pass`."""
        proc, runs, leftovers = self.run_test(_ev_test(severity="Minor"), runner=None)
        self.assert_output(proc, ["pass", "finding F1: advisory (low_severity Minor)" + EV_AT,
                                  _ev_summary("pass", 0, 1, 0)])

    def test_missing_runner_binary_is_runner_not_found(self) -> None:
        """AC-2.4 — a known runner whose binary is missing is project-level
        `runner_not_found`; nothing is written (Upstream error shadow path)."""
        proc, runs, leftovers = self.run_test(_ev_test(), runner="/nonexistent/bin/pytest")
        self.assert_output(proc, _ev_unverifiable("runner_not_found"))
        self.assertNotIn("tests", leftovers)

    def test_timeout_kills_the_process_group(self) -> None:
        """AC-2.4 — a run past `--timeout` is `unverifiable timeout <s>`, its
        process group is killed, and the repro is deleted."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root, runner="jest")
            argv = root / "argv.jsonl"
            start = time.monotonic()
            proc = _ev_run(root, repo, _ev_review(_ev_test("src/limits.test.js")),
                           extra=("--timeout", "1"),
                           env=_ev_env(STUB_ARGV=str(argv), STUB_SLEEP="30"))
            self.assertLess(time.monotonic() - start, 20)
            self.assert_output(proc, [
                "pass", "finding F1: advisory (unverifiable timeout 1)" + EV_AT,
                _ev_summary("pass", 0, 0, 1)])
            self.assertFalse((repo / "src" / "limits.test.js").exists())
            child = int(Path(str(argv) + ".child").read_text(encoding="utf-8"))
            alive = True
            for _ in range(100):
                try:
                    os.kill(child, 0)
                except ProcessLookupError:
                    alive = False
                    break
                time.sleep(0.1)
            self.assertFalse(alive, "child %d of the timed-out runner survived" % child)

    def test_path_exists_on_disk_or_declared_earlier(self) -> None:
        """AC-2.4 — a path already on disk, or one an earlier finding declared,
        is `path_exists`; the existing file is untouched."""
        existing = "tests/test_existing.py"
        proc, runs, leftovers = self.run_test(_ev_test(existing), _ev_test(), _ev_test(),
                                              files={existing: "x = 1\n"})
        self.assert_finding(proc, "F1", "advisory (unverifiable path_exists)" + EV_AT)
        self.assert_finding(proc, "F2", "confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT))
        self.assert_finding(proc, "F3", "advisory (unverifiable path_exists)" + EV_AT)
        self.assertIn(existing, leftovers)

    def test_path_outside_repo_is_unverifiable(self) -> None:
        """AC-2.4 — an absolute path, or one that resolves outside the repo, is
        `path_outside_repo`; nothing is written."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            absolute = str(root / "test_abs.py")
            proc = _ev_run(root, repo, _ev_review(_ev_test("../test_outside.py"),
                                                  _ev_test(absolute)))
            self.assert_finding(proc, "F1", "advisory (unverifiable path_outside_repo)" + EV_AT)
            self.assert_finding(proc, "F2", "advisory (unverifiable path_outside_repo)" + EV_AT)
            self.assertFalse((root / "test_outside.py").exists())
            self.assertFalse((root / "test_abs.py").exists())

    def test_not_a_test_path_is_unverifiable(self) -> None:
        """AC-2.4 — a path outside the runner's test-file pattern is
        `not_a_test_path`; nothing is written."""
        cases = ((EV_PYTEST, "tests/limits_repro.py"), ("jest", "src/limits_repro.js"),
                 ("go test", "pkg/limits.go"), ("cargo test", "src/limits_repro.rs"),
                 ("rspec", "spec/limits.rb"))
        for runner, path in cases:
            with self.subTest(runner=runner):
                proc, runs, leftovers = self.run_test(_ev_test(path), runner=runner)
                self.assert_finding(proc, "F1", "advisory (unverifiable not_a_test_path)" + EV_AT)
                self.assertEqual(runs, [])
                self.assertNotIn(path, leftovers)
                top = path.split("/")[0]
                if top != "src":
                    self.assertNotIn(top, leftovers)

    def test_repro_write_failure_is_unverifiable(self) -> None:
        """AC-2.4 — a repro whose parent is a file cannot be written:
        `repro_write_failed`, no run."""
        proc, runs, leftovers = self.run_test(_ev_test("src/limits.py/test_x.py"))
        self.assert_finding(proc, "F1", "advisory (unverifiable repro_write_failed)" + EV_AT)


class EvidenceTreeSnapshotTests(EvidenceTestCase):
    """Story 2 of `2026-11-04-evidence-gated-review` — the git snapshot around
    each run: mutation stops the call, a failed delete counts as mutation,
    no git is `no_git`, and `evidence` writes nothing else. [AC-2.5]"""

    WRITE_X = ("from pathlib import Path\n\n\n"
               "def test_writes():\n"
               "    Path(\"src/x.py\").write_text(\"y = 2\\n\")\n"
               "    assert False\n")
    APPEND_LIMITS = ("from pathlib import Path\n\n\n"
                     "def test_appends():\n"
                     "    with open(\"src/limits.py\", \"a\") as handle:\n"
                     "        handle.write(\"# changed\\n\")\n"
                     "    assert False\n")

    def test_new_file_outside_repro_is_repro_mutated_tree(self) -> None:
        """AC-2.5 — a repro that writes `src/x.py`: line 1 `fail`, first reason
        `repro_mutated_tree src/x.py`, no later repro runs, nothing restored."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, _ev_review(
                _ev_test(content=self.WRITE_X), _ev_test("tests/test_second.py"),
                _ev_issue(category="security",
                          evidence="security-path source src/routes.py:5 sink src/limits.py:3")))
            self.assert_output(proc, [
                "fail", "finding F1: advisory (unverifiable repro_mutated_tree)" + EV_AT,
                "finding F2: advisory (unverifiable stopped_after_mutation)" + EV_AT,
                "finding F3: confirmed (security-path source src/routes.py:5 sink src/limits.py:3)"
                + EV_AT,
                "reason: repro_mutated_tree src/x.py", "reason: confirmed F3",
                _ev_summary("fail", 1, 0, 2)])
            self.assertEqual((repo / "src" / "x.py").read_text(encoding="utf-8"), "y = 2\n")
            self.assertFalse((repo / EV_REPRO).exists())
            self.assertFalse((repo / "tests" / "test_second.py").exists())

    def test_tracked_file_change_is_repro_mutated_tree(self) -> None:
        """AC-2.5 — editing a clean tracked file, or an already-modified one,
        is `repro_mutated_tree <path>`; the edit stays."""
        for dirty in (False, True):
            with self.subTest(dirty=dirty), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                limits = repo / "src" / "limits.py"
                if dirty:
                    limits.write_text(limits.read_text(encoding="utf-8") + "# wip\n",
                                      encoding="utf-8")
                before = limits.read_text(encoding="utf-8")
                proc = _ev_run(root, repo, _ev_review(_ev_test(content=self.APPEND_LIMITS)))
                self.assertEqual(proc.stdout.splitlines()[0], "fail", proc.stdout + proc.stderr)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("reason: repro_mutated_tree src/limits.py", proc.stdout)
                self.assertEqual(limits.read_text(encoding="utf-8"), before + "# changed\n")

    def test_check_with_fix_flag_is_repro_mutated_tree(self) -> None:
        """AC-2.5 — a `check` that writes files (a fix flag) is caught by the snapshot."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, _ev_review(_ev_issue(evidence="check `lint --fix src/limits.py`")),
                           checks="lint\n", env=_ev_env(STUB_MODE="clean", STUB_WRITE="src/limits.py"))
            self.assert_output(proc, [
                "fail", "finding F1: advisory (unverifiable repro_mutated_tree)" + EV_AT,
                "reason: repro_mutated_tree src/limits.py", _ev_summary("fail", 0, 0, 1)])

    def test_head_move_is_repro_mutated_tree(self) -> None:
        """AC-2.5 — a run that moves HEAD on a clean tree (a commit, or a
        branch switch) is `repro_mutated_tree (HEAD)`."""
        commands = (
            '["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "--allow-empty", "-qm", "x"]',
            '["git", "checkout", "-q", "-b", "other"]',
        )
        for command in commands:
            content = ("import subprocess\n\n\n"
                       "def test_moves_head():\n"
                       "    subprocess.run(%s, check=True)\n"
                       "    assert False\n" % command)
            with self.subTest(command=command), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                proc = _ev_run(root, repo, _ev_review(_ev_test(content=content)))
                self.assert_output(proc, [
                    "fail", "finding F1: advisory (unverifiable repro_mutated_tree)" + EV_AT,
                    "reason: repro_mutated_tree (HEAD)", _ev_summary("fail", 0, 0, 1)])

    def test_ignored_writes_do_not_count(self) -> None:
        """AC-2.5 — a write to a git-ignored path is not a mutation."""
        content = ("from pathlib import Path\n\n\n"
                   "def test_cache():\n"
                   "    Path(\"src/__pycache__\").mkdir(exist_ok=True)\n"
                   "    Path(\"src/__pycache__/junk.txt\").write_text(\"x\")\n"
                   "    assert False\n")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, _ev_review(_ev_test(content=content)))
            self.assert_finding(proc, "F1", "confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT))
            self.assertEqual(proc.stdout.splitlines()[0], "fail")
            self.assertNotIn("repro_mutated_tree", proc.stdout)

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "needs POSIX permissions and a non-root user")
    def test_undeletable_repro_is_repro_mutated_tree(self) -> None:
        """AC-2.5 — a repro that cannot be deleted (its parent made read-only)
        is `fail` with `repro_mutated_tree <path>`."""
        path = "tests/ro/test_ro_repro.py"
        content = ("import os\n\n"
                   "os.chmod(os.path.dirname(os.path.abspath(__file__)), 0o555)\n\n\n"
                   "def test_locked():\n"
                   "    assert False\n")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            try:
                proc = _ev_run(root, repo, _ev_review(_ev_test(path, content=content)))
                self.assert_output(proc, [
                    "fail", "finding F1: advisory (unverifiable repro_mutated_tree)" + EV_AT,
                    "reason: repro_mutated_tree %s" % path, _ev_summary("fail", 0, 0, 1)])
            finally:
                ro = repo / "tests" / "ro"
                if ro.exists():
                    os.chmod(str(ro), 0o755)

    def test_no_git_is_unverifiable(self) -> None:
        """AC-2.5 — a repo with no git, or no `git` binary, is `unverifiable
        no_git`; nothing is written."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root, git=False)
            proc = _ev_run(root, repo, _ev_review(_ev_test()),
                           env=_ev_env(GIT_CEILING_DIRECTORIES=str(root)))
            self.assert_output(proc, _ev_unverifiable("no_git"))
            self.assertFalse((repo / "tests").exists())
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            proc = _ev_run(root, repo, _ev_review(_ev_test()), env=_ev_env(PATH=str(EV_STUBS)))
            self.assert_output(proc, _ev_unverifiable("no_git"))
            self.assertFalse((repo / "tests").exists())

    def test_run_writes_no_state_and_no_git_data(self) -> None:
        """AC-2.5 — without `--manifest-out`, nothing lands under `.writ/state/`;
        the git index, HEAD, and status are what they were."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            status_args = ("--no-optional-locks", "status", "--porcelain=v1",
                           "--untracked-files=all")
            status = _ev_git(repo, *status_args)
            head = _ev_git(repo, "rev-parse", "HEAD")
            index = (repo / ".git" / "index").read_bytes()
            proc = _ev_run(root, repo, _ev_review(_ev_test(), _ev_test("tests/test_two.py",
                                                                       content=EV_REPRO_PASS)))
            self.assertEqual(proc.stdout.splitlines()[0], "fail", proc.stdout + proc.stderr)
            self.assertFalse((repo / ".writ" / "state").exists())
            self.assertEqual((repo / ".git" / "index").read_bytes(), index)
            self.assertEqual(_ev_git(repo, "rev-parse", "HEAD"), head)
            self.assertEqual(_ev_git(repo, *status_args), status)


# ---------------------------------------------------------------------------
# Story 5 of `2026-11-04-evidence-gated-review`: `evidence --surface review`
# reads a `/review` report. Severities come from the Failure Modes Registry
# table and evidence from `#### FM-NNN` blocks under `## Evidence`. Line 2 is
# the report header's `evidence-gate:` value, and each finding line ends with
# the row's mapped severity. Same fixture project and stubs as Story 2.
# [AC-5.1, AC-5.2, AC-5.3, AC-5.4]
# ---------------------------------------------------------------------------

RV_UNCONFIRMED = "Medium (unconfirmed)"
RV_SECURITY = "security-path source `src/routes.py:5` sink `src/limits.py:3`"
RV_SECURITY_SHOWN = "security-path source src/routes.py:5 sink src/limits.py:3"
RV_REGISTRY_HEADER = "| ID | Category | Severity | Description | Status |"


def _rv_block(fm: str, *, location: str | None = EV_LOCATION, category: str | None = None,
              evidence: str | None = None, block: str | None = None, indent: str = "  ",
              severity: str | None = None) -> list:
    """One `#### FM-NNN` evidence block; `block` is the fenced file after Evidence."""
    lines = ["#### %s" % fm]
    if location is not None:
        lines.append("- **Location:** %s" % location)
    if severity is not None:
        lines.append("- **Severity:** %s" % severity)
    if category is not None:
        lines.append("- **Category:** %s" % category)
    if evidence is not None:
        lines.append("- **Evidence:** %s" % evidence)
    if block is not None:
        lines.append(indent + "```python")
        lines.extend((indent + ln) if ln else "" for ln in block.splitlines())
        lines.append(indent + "```")
    return lines + [""]


def _rv_test(fm: str, path: str = EV_REPRO, content: str = EV_REPRO_FAIL, **kwargs) -> list:
    return _rv_block(fm, evidence="test `%s`" % path, block=content, **kwargs)


def _rv_report(rows: tuple, *blocks: list, evidence_heading: str | None = "## Evidence",
               table: list | None = None, verdict: str | None = None) -> str:
    """A `/review` report. `rows` are (ID, Category, Severity); `table`
    replaces the whole registry table when a test needs other columns."""
    lines = ["# Code Review: feature", "", "> Reviewed: 2026-11-04", "> Reviewer filters: on", ""]
    if verdict is not None:
        lines += ["### REVIEW_RESULT: %s" % verdict, ""]
    lines += ["## Failure Modes Registry", ""]
    if table is None:
        table = [RV_REGISTRY_HEADER, "|---|---|---|---|---|"]
        table += ["| %s | %s | %s | Fixture finding %s | Unresolved |" % (fm, category, severity, fm)
                  for fm, category, severity in rows]
    lines += table + ["**Summary:** fixture", ""]
    if evidence_heading is not None:
        lines += [evidence_heading, ""]
        for block in blocks:
            lines += block
    lines += ["## Recommendation", "", "Draft.", ""]
    return "\n".join(lines) + "\n"


def _rv_output(verdict: str, findings: list, reasons: list, counts: tuple) -> list:
    """Expected `--surface review` output for a run that evaluated the rows."""
    return ([verdict, "evidence-gate: on"] + ["finding %s: %s" % pair for pair in findings]
            + ["reason: %s" % reason for reason in reasons] + [_ev_summary(verdict, *counts)])


def _rv_unverifiable(reason: str, header: str | None = None) -> list:
    """Expected run-level output: no finding lines, so no row is downgraded."""
    return ["unverifiable", "evidence-gate: %s" % (header or "unverifiable (%s)" % reason),
            "reason: %s" % reason, "review-override evidence: unverifiable (%s)" % reason]


class ReviewSurfaceTestCase(EvidenceTestCase):
    """Runs `evidence --surface review` on a `/review` report in a temp git repo."""

    def assert_finding(self, proc: subprocess.CompletedProcess, key: str, text: str) -> None:
        found = dict(re.findall(r"(?m)^finding (FM-\d+): (.*)$", proc.stdout))
        self.assertEqual(found.get(key), text, proc.stdout + proc.stderr)

    def run_review(self, report: str | None, *, runner: str | None = EV_PYTEST,
                   lines: tuple = (), git: bool = True, changed: tuple = ("src/limits.py",),
                   tests: str | None = None, checks: str | None = None, **env: str) -> tuple:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root, runner=runner, lines=lines, git=git)
            argv = root / "argv.jsonl"
            proc = _ev_run(root, repo, report, changed=changed, tests=tests, checks=checks,
                           extra=("--surface", "review"),
                           env=_ev_env(STUB_ARGV=str(argv), GIT_CEILING_DIRECTORIES=str(root),
                                       **env))
            leftovers = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*")
                               if ".git" not in p.relative_to(repo).parts
                               and "__pycache__" not in p.parts)
            return proc, _ev_argv(argv), leftovers


class ReviewSurfaceParseTests(ReviewSurfaceTestCase):
    """Story 5 of `2026-11-04-evidence-gated-review` — the registry table and
    `#### FM-NNN` block parse on `--surface review`. [AC-5.1]"""

    def test_severity_column_is_read(self) -> None:
        """AC-5.1 — each row's Severity cell decides whether it is evaluated:
        a Critical or High row with no block maps to `Medium (unconfirmed)`, a
        Medium or Low row keeps its severity; every row keeps its ID."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Shadow path", "**High**"),
                ("FM-003", "Interaction", "Medium"), ("FM-004", "Error handling", "Low"))
        proc, runs, _ = self.run_review(_rv_report(rows))
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED),
            ("FM-002", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED),
            ("FM-003", "advisory (low_severity Medium); severity Medium"),
            ("FM-004", "advisory (low_severity Low); severity Low"),
        ], [], (0, 4, 0)))

    def test_columns_are_found_by_header_name(self) -> None:
        """AC-5.1 — the ID and Severity columns are found by header name, in
        any order, and a row whose ID cell is not `FM-NNN` is skipped."""
        table = ["| Severity | ID | Description | Category |", "|---|---|---|---|",
                 "| Low | FM-001 | x | Error handling |", "| Critical | `FM-002` | y | Error handling |",
                 "| Critical | total | z | Error handling |"]
        proc, runs, _ = self.run_review(
            _rv_report((), _rv_test("FM-002", "src/limits.test.js"), table=table), runner="jest")
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "advisory (low_severity Low); severity Low"),
            ("FM-002", "confirmed (test src/limits.test.js, exit 1)%s; severity Critical" % EV_AT),
        ], ["confirmed FM-002"], (1, 1, 0)))

    def test_block_binds_to_its_row_by_id(self) -> None:
        """AC-5.1 — `#### FM-NNN` blocks bind to their rows by ID, in any
        order; a block whose ID has no registry row is ignored, and a second
        block for one row is ignored with `extra_evidence FM-NNN`."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Security", "High"))
        proc, runs, leftovers = self.run_review(_rv_report(
            rows,
            _rv_block("FM-009", category="security", evidence=RV_SECURITY),
            _rv_block("FM-002", category="security", evidence=RV_SECURITY),
            _rv_test("FM-001", content=EV_REPRO_PASS),
            _rv_test("FM-002", "tests/test_second.py")))
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "advisory (repro_passed)%s; severity %s" % (EV_AT, RV_UNCONFIRMED)),
            ("FM-002", "confirmed (%s)%s; severity High" % (RV_SECURITY_SHOWN, EV_AT)),
        ], ["extra_evidence FM-002", "confirmed FM-002"], (1, 1, 0)))
        self.assertNotIn(EV_REPRO, leftovers)

    def test_row_without_a_block_is_no_evidence(self) -> None:
        """AC-5.1 — a Critical or High row with no block, or with a block that
        has no Evidence field, is `advisory (no_evidence)`; a block outside
        `## Evidence` binds to nothing."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Shadow path", "High"))
        proc, runs, _ = self.run_review(_rv_report(rows, _rv_block("FM-002")))
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED),
            ("FM-002", "advisory (no_evidence)%s; severity %s" % (EV_AT, RV_UNCONFIRMED)),
        ], [], (0, 2, 0)))
        proc, runs, _ = self.run_review(_rv_report(
            rows, _rv_test("FM-001", "src/limits.test.js"), evidence_heading="## Notes"),
            runner="jest")
        self.assert_finding(proc, "FM-001", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED)
        self.assertEqual(runs, [])

    def test_only_critical_and_high_rows_run(self) -> None:
        """AC-5.1 — Medium, Low, and Major (not a `/review` severity) rows never
        run, even with a failing repro; Critical and High rows do."""
        severities = ("Medium", "Low", "Major", "Critical", "High")
        rows = tuple(("FM-00%d" % n, "Error handling", s) for n, s in enumerate(severities, 1))
        blocks = [_rv_test("FM-00%d" % n, "src/a%d.test.js" % n) for n in range(1, 6)]
        proc, runs, _ = self.run_review(_rv_report(rows, *blocks), runner="jest")
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "advisory (low_severity Medium)%s; severity Medium" % EV_AT),
            ("FM-002", "advisory (low_severity Low)%s; severity Low" % EV_AT),
            ("FM-003", "advisory (low_severity Major)%s; severity Major" % EV_AT),
            ("FM-004", "confirmed (test src/a4.test.js, exit 1)%s; severity Critical" % EV_AT),
            ("FM-005", "confirmed (test src/a5.test.js, exit 1)%s; severity High" % EV_AT),
        ], ["confirmed FM-004", "confirmed FM-005"], (2, 3, 0)))
        self.assertEqual(runs, [["src/a4.test.js"], ["src/a5.test.js"]])

    def test_empty_changed_is_location_outside_change_set(self) -> None:
        """AC-5.1 — with no diff files, every Critical and High row, with a
        block or without one, is `advisory (location_outside_change_set)` and
        nothing runs (Error & Rescue Map, `/review` row). With diff files, a
        block whose Location is not among them is outside too."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Shadow path", "High"),
                ("FM-003", "Security", "Critical"))
        report = _rv_report(rows, _rv_test("FM-001", "src/limits.test.js"),
                            _rv_block("FM-003", category="security", evidence=RV_SECURITY))
        proc, runs, _ = self.run_review(report, runner="jest", changed=())
        outside = "advisory (location_outside_change_set)"
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "%s%s; severity %s" % (outside, EV_AT, RV_UNCONFIRMED)),
            ("FM-002", "%s; severity %s" % (outside, RV_UNCONFIRMED)),
            ("FM-003", "%s%s; severity %s" % (outside, EV_AT, RV_UNCONFIRMED)),
        ], [], (0, 3, 0)))
        self.assertEqual(runs, [])
        proc, runs, _ = self.run_review(report, runner="jest", changed=("src/routes.py",))
        self.assert_finding(proc, "FM-001", "%s%s; severity %s" % (outside, EV_AT, RV_UNCONFIRMED))
        self.assert_finding(proc, "FM-002", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED)
        self.assertEqual(runs, [])

    def test_report_without_a_registry_passes_with_zero_counts(self) -> None:
        """AC-5.1 — no Failure Modes Registry, or one with no rows: `pass`,
        `0 confirmed, 0 advisory, 0 unverifiable`."""
        for report in ("# Code Review: feature\n\nNo failure modes in scope.\n", _rv_report(())):
            with self.subTest(report=report[:40]):
                proc, runs, _ = self.run_review(report)
                self.assert_output(proc, _rv_output("pass", [], [], (0, 0, 0)))

    def test_duplicate_registry_row_keeps_the_first(self) -> None:
        """AC-5.1 — a second registry row with the same FM ID is dropped with
        `reason: duplicate_row FM-NNN`; the first row keeps its outcome."""
        rows = (("FM-001", "Security", "Critical"), ("FM-001", "Error handling", "Low"),
                ("FM-001", "Error handling", "High"))
        proc, runs, _ = self.run_review(_rv_report(rows, _rv_block("FM-001", evidence=RV_SECURITY)))
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "confirmed (%s)%s; severity Critical" % (RV_SECURITY_SHOWN, EV_AT)),
        ], ["confirmed FM-001", "duplicate_row FM-001", "duplicate_row FM-001"], (1, 0, 0)))

    def test_registry_severity_wins_over_a_block_severity(self) -> None:
        """AC-5.1 — a block's own `**Severity:** Critical` does not lift a
        Medium registry row: it stays `low_severity Medium` and never runs."""
        rows = (("FM-001", "Error handling", "Medium"),)
        proc, runs, _ = self.run_review(_rv_report(
            rows, _rv_test("FM-001", "src/limits.test.js", severity="Critical")), runner="jest")
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "advisory (low_severity Medium)%s; severity Medium" % EV_AT),
        ], [], (0, 1, 0)))
        self.assertEqual(runs, [])

    def test_fenced_registry_lines_are_not_rows(self) -> None:
        """AC-5.1 — a table line inside a fence in the registry section is not
        a row."""
        table = [RV_REGISTRY_HEADER, "|---|---|---|---|---|",
                 "| FM-001 | Error handling | Low | x | Unresolved |", "```",
                 "| FM-009 | Error handling | Critical | y | Unresolved |", "```"]
        proc, runs, _ = self.run_review(_rv_report((), table=table))
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "advisory (low_severity Low); severity Low"),
        ], [], (0, 1, 0)))

    def test_mapped_severity_prints_the_word_not_the_cell(self) -> None:
        """AC-5.1 — a bold `**High**` cell that confirms prints `severity High`,
        and a bold `**Low**` cell prints `severity Low`."""
        rows = (("FM-001", "Security", "**High**"), ("FM-002", "Error handling", "**Low**"))
        proc, runs, _ = self.run_review(_rv_report(rows, _rv_block("FM-001", evidence=RV_SECURITY)))
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "confirmed (%s)%s; severity High" % (RV_SECURITY_SHOWN, EV_AT)),
            ("FM-002", "advisory (low_severity Low); severity Low"),
        ], ["confirmed FM-001"], (1, 1, 0)))

    def test_fenced_lines_never_open_a_block(self) -> None:
        """AC-5.1 — a `# FM-002` comment inside an unindented repro is code: it
        neither opens a block nor ends the Evidence section."""
        content = "# FM-002 is the same bug\n" + EV_REPRO_FAIL
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Error handling", "High"))
        proc, runs, _ = self.run_review(_rv_report(rows, _rv_test("FM-001", content=content,
                                                                  indent="")))
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "confirmed (test %s, exit 1)%s; severity Critical" % (EV_REPRO, EV_AT)),
            ("FM-002", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED),
        ], ["confirmed FM-001"], (1, 1, 0)))


class ReviewSurfaceMappingTests(ReviewSurfaceTestCase):
    """Story 5 of `2026-11-04-evidence-gated-review` — the kind rules, the
    per-row mapped severity, and the switch on `--surface review`.
    [AC-5.2, AC-5.3, AC-5.4]"""

    def test_confirmed_test_row_keeps_its_severity(self) -> None:
        """AC-5.2 — a real pytest repro that fails confirms a Critical row with
        Category `Error handling`; the row keeps its severity, line 1 is
        `fail`, exit 1, and the repro is deleted."""
        rows = (("FM-001", "Error handling", "Critical"),)
        proc, runs, leftovers = self.run_review(_rv_report(rows, _rv_test("FM-001")))
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "confirmed (test %s, exit 1)%s; severity Critical" % (EV_REPRO, EV_AT)),
        ], ["confirmed FM-001"], (1, 0, 0)))
        self.assertNotIn(EV_REPRO, leftovers)
        self.assertNotIn("tests", leftovers)

    def test_no_row_reports_no_claim(self) -> None:
        """AC-5.2 — rows carry no AC IDs, and any category can confirm: no row
        reports `no_claim` on this surface."""
        for category in ("Shadow path", "Interaction", "Architecture", "taste", ""):
            with self.subTest(category=category):
                rows = (("FM-001", category, "High"),)
                proc, runs, _ = self.run_review(
                    _rv_report(rows, _rv_test("FM-001", "src/limits.test.js")), runner="jest")
                self.assertNotIn("no_claim", proc.stdout)
                self.assert_finding(proc, "FM-001", "confirmed (test src/limits.test.js, exit 1)"
                                                    "%s; severity High" % EV_AT)

    def test_unconfirmed_rows_map_to_medium_unconfirmed(self) -> None:
        """AC-5.1, AC-5.2 — a passing repro and a per-row unverifiable both map a
        Critical or High row to `Medium (unconfirmed)`; line 1 `pass`, exit 0."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Shadow path", "High"),
                ("FM-003", "Interaction", "Critical"))
        proc, runs, _ = self.run_review(_rv_report(
            rows, _rv_test("FM-001", content=EV_REPRO_PASS),
            _rv_test("FM-002", "src/repro.py"),
            _rv_block("FM-003", evidence="screenshot `shot.png`")))
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "advisory (repro_passed)%s; severity %s" % (EV_AT, RV_UNCONFIRMED)),
            ("FM-002", "advisory (unverifiable not_a_test_path)%s; severity %s"
             % (EV_AT, RV_UNCONFIRMED)),
            ("FM-003", "advisory (unverifiable unknown_kind screenshot)%s; severity %s"
             % (EV_AT, RV_UNCONFIRMED)),
        ], [], (0, 1, 2)))

    def test_recorded_and_check_are_kind_unavailable(self) -> None:
        """AC-5.3 — `recorded` and `check` blocks are `unverifiable
        kind_unavailable` and map to `Medium (unconfirmed)`, even with a failing
        recorded run and a recorded Gate 2 command; nothing runs."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Shadow path", "High"))
        report = _rv_report(rows,
                            _rv_block("FM-001", evidence="recorded `tests/test_limits.py::test_neg`"),
                            _rv_block("FM-002", evidence="check `lint src/limits.py`"))
        tests = "command: pytest\nexit code: 1\nFAILED tests/test_limits.py::test_neg\n"
        proc, runs, _ = self.run_review(report, runner="jest", tests=tests, checks="lint\n",
                                        STUB_MODE="names")
        unavailable = "advisory (unverifiable kind_unavailable)%s; severity %s" % (EV_AT,
                                                                                   RV_UNCONFIRMED)
        self.assert_output(proc, _rv_output("pass", [("FM-001", unavailable),
                                                     ("FM-002", unavailable)], [], (0, 0, 2)))
        self.assertEqual(runs, [])

    def test_security_path_confirms_a_high_row(self) -> None:
        """AC-5.3 — `security-path` confirms a High row (High counts as Major+).
        The block's Category is used, or the registry's when the block has
        none, and it must be security."""
        rows = (("FM-001", "Security", "High"), ("FM-002", "Error handling", "High"),
                ("FM-003", "Error handling", "Critical"))
        proc, runs, _ = self.run_review(_rv_report(
            rows, _rv_block("FM-001", evidence=RV_SECURITY),
            _rv_block("FM-002", evidence=RV_SECURITY),
            _rv_block("FM-003", category="security", evidence=RV_SECURITY)))
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "confirmed (%s)%s; severity High" % (RV_SECURITY_SHOWN, EV_AT)),
            ("FM-002", "advisory (unverifiable not_security)%s; severity %s"
             % (EV_AT, RV_UNCONFIRMED)),
            ("FM-003", "confirmed (%s)%s; severity Critical" % (RV_SECURITY_SHOWN, EV_AT)),
        ], ["confirmed FM-001", "confirmed FM-003"], (2, 0, 1)))

    def test_no_verdict_check_on_this_surface(self) -> None:
        """AC-5.2 — `/review` writes no verdict: a report with no verdict line,
        or with a PASS line, is still evaluated."""
        rows = (("FM-001", "Error handling", "Critical"),)
        for verdict in (None, "PASS"):
            with self.subTest(verdict=verdict):
                proc, runs, _ = self.run_review(_rv_report(
                    rows, _rv_test("FM-001", "src/limits.test.js"), verdict=verdict), runner="jest")
                self.assert_output(proc, _rv_output("fail", [
                    ("FM-001", "confirmed (test src/limits.test.js, exit 1)%s; severity Critical"
                     % EV_AT)], ["confirmed FM-001"], (1, 0, 0)))

    def test_switch_off_prints_off_and_runs_nothing(self) -> None:
        """AC-5.4 — `Evidence Gate: off`: line 2 is `evidence-gate: off`, there
        are no finding lines, so no row is downgraded, and no repro runs."""
        rows = (("FM-001", "Error handling", "Critical"),)
        for value in ("off", "OFF"):
            with self.subTest(value=value):
                proc, runs, leftovers = self.run_review(
                    _rv_report(rows, _rv_test("FM-001", "src/limits.test.js")), runner="jest",
                    lines=("- **Evidence Gate:** %s" % value,))
                self.assert_output(proc, _rv_unverifiable("switch_off", header="off"))
                self.assertEqual(runs, [])
                self.assertNotIn("src/limits.test.js", leftovers)

    def test_run_level_unverifiable_leaves_every_severity(self) -> None:
        """AC-5.4 — no Test Runner and no `security-path` row, no git, a missing
        runner binary, or no review output: line 1 `unverifiable`, the reason
        in the header line, and no finding lines, so every severity stays."""
        report = _rv_report((("FM-001", "Error handling", "Critical"),
                             ("FM-002", "Shadow path", "High")), _rv_test("FM-001"))
        cases = (
            ("no_test_runner", report, {"runner": None}),
            ("no_git", report, {"git": False}),
            ("runner_not_found", report, {"runner": "/nonexistent/bin/pytest"}),
            ("no_review_output", None, {}),
        )
        for reason, text, kwargs in cases:
            with self.subTest(reason=reason):
                proc, runs, leftovers = self.run_review(text, **kwargs)
                self.assert_output(proc, _rv_unverifiable(reason))
                self.assertNotIn("tests", leftovers)

    def test_no_test_runner_with_a_decided_security_path_row(self) -> None:
        """AC-5.1, AC-5.3 — with no Test Runner, a confirmed `security-path` row
        decides the run: the `test` row is a per-row `unverifiable
        no_test_runner` and maps to `Medium (unconfirmed)`."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Security", "High"))
        proc, runs, _ = self.run_review(_rv_report(
            rows, _rv_test("FM-001"), _rv_block("FM-002", evidence=RV_SECURITY)), runner=None)
        self.assert_output(proc, _rv_output("fail", [
            ("FM-001", "advisory (unverifiable no_test_runner)%s; severity %s"
             % (EV_AT, RV_UNCONFIRMED)),
            ("FM-002", "confirmed (%s)%s; severity High" % (RV_SECURITY_SHOWN, EV_AT)),
        ], ["confirmed FM-002"], (1, 0, 1)))

    def test_no_test_runner_with_an_advisory_security_path_row(self) -> None:
        """AC-5.1, AC-5.3 — with no Test Runner, an advisory `security-path` row
        (sink outside the diff) also decides the run: line 1 `pass`, and the
        unevidenced Critical row maps to `Medium (unconfirmed)`."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Security", "High"))
        proc, runs, _ = self.run_review(_rv_report(rows, _rv_block(
            "FM-002", evidence="security-path source `src/limits.py:3` sink `src/routes.py:5`")),
            runner=None)
        self.assert_output(proc, _rv_output("pass", [
            ("FM-001", "advisory (no_evidence); severity %s" % RV_UNCONFIRMED),
            ("FM-002", "advisory (location_outside_change_set)%s; severity %s"
             % (EV_AT, RV_UNCONFIRMED)),
        ], [], (0, 2, 0)))

    def test_tree_mutation_is_run_level_unverifiable(self) -> None:
        """AC-5.4 — a repro run that changes a tracked file is run-level
        `unverifiable (repro_mutated_tree <paths>)`: no finding lines, so every
        severity stays as written, and no later repro runs."""
        rows = (("FM-001", "Error handling", "Critical"), ("FM-002", "Shadow path", "High"))
        proc, runs, _ = self.run_review(_rv_report(
            rows, _rv_test("FM-001", "src/a1.test.js"), _rv_test("FM-002", "src/a2.test.js")),
            runner="jest", STUB_WRITE="src/limits.py")
        self.assert_output(proc, _rv_unverifiable("repro_mutated_tree src/limits.py"))
        self.assertEqual(runs, [["src/a1.test.js"]])


# ---------------------------------------------------------------------------
# Story 4 of `2026-11-04-evidence-gated-review`: confirmed repros become
# regression tests. `--manifest-out` records each confirmed `test` repro in an
# `evidence-manifest-v1` file, written atomically and merged with an existing
# one. `--prior` checks each recorded repro first, on any verdict: still in
# `--changed`, unmodified after normalization, and named by a recorded run
# that exited 0. Same fixture project and stubs as Story 2.
# [AC-4.1, AC-4.2, AC-4.3, AC-4.4]
# ---------------------------------------------------------------------------

MF_SCHEMA = "evidence-manifest-v1"
MF_STEM = "story-9-replay"
MF_NAME = "evidence-%s.json" % MF_STEM
# EV_REPRO_FAIL is already in normal form: LF endings, no trailing whitespace,
# one final newline. So its plain SHA-256 is the normalized one.
MF_SHA = hashlib.sha256(EV_REPRO_FAIL.encode("utf-8")).hexdigest()
MF_ENTRY = {"finding": "F1", "path": EV_REPRO, "sha256": MF_SHA, "kind": "test",
            "location": "src/limits.py:3", "content": EV_REPRO_FAIL}
MF_RUN_OK = "command: python3 -m pytest %s\nexit code: 0\n1 passed in 0.01s\n" % EV_REPRO
MF_CHANGED = ("src/limits.py", EV_REPRO)
MF_PRIOR_OK = ["pass", "reason: prior_ok", "review-override evidence: pass (prior_ok)"]


def _mf_doc(*repros: dict, story: str = MF_STEM) -> dict:
    return {"schema": MF_SCHEMA, "story": story, "repros": list(repros)}


def _mf_write(path: Path, doc) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _mf_read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _mf_prior_fail(*reasons: str) -> list:
    """Output on a PASS or PAUSE verdict when `--prior` checks fail: only the
    prior checks ran, so the summary names the first reason."""
    return (["fail"] + ["reason: %s" % r for r in reasons]
            + ["review-override evidence: fail (%s)" % reasons[0]])


class EvidenceManifestTests(EvidenceTestCase):
    """Story 4 of `2026-11-04-evidence-gated-review` — the `--manifest-out`
    write and the `--prior` checks. [AC-4.1, AC-4.2, AC-4.3, AC-4.4]"""

    def prior_repo(self, root: Path, content: str | None = EV_REPRO_FAIL, *,
                   runner: str | None = EV_PYTEST, repros: tuple = (MF_ENTRY,),
                   files: dict | None = None, git: bool = True) -> tuple:
        """The fixture repo with the repro on disk as the coder created it
        (uncommitted, exact bytes), and a manifest outside the repo."""
        repo = _ev_repo(root, runner=runner, files=files, git=git)
        if content is not None:
            (repo / EV_REPRO).parent.mkdir(parents=True, exist_ok=True)
            (repo / EV_REPRO).write_bytes(content.encode("utf-8"))
        return repo, _mf_write(root / "state" / MF_NAME, _mf_doc(*repros))

    def run_prior(self, root: Path, repo: Path, manifest: Path, verdict: str, *issues: list,
                  changed: tuple = MF_CHANGED, tests: str | None = MF_RUN_OK,
                  env: dict | None = None) -> subprocess.CompletedProcess:
        return _ev_run(root, repo, _ev_review(*issues, verdict=verdict), changed=changed,
                       tests=tests, extra=("--prior", str(manifest)), env=env)

    # --- the manifest write ------------------------------------------------

    def test_confirmed_test_repro_writes_one_entry(self) -> None:
        """AC-4.1 — one entry per confirmed `test` repro: finding key, path,
        normalized SHA-256, kind, Location, and the normalized `content` a
        row 4a recode brief restores it from. An advisory repro and a
        confirmed `recorded` finding get none, the output is unchanged, and
        no temporary file is left beside the manifest."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            manifest = root / "state" / MF_NAME
            tests = ("command: python3 -m pytest\nexit code: 1\n"
                     "FAILED tests/test_limits.py::test_negative\n1 failed\n")
            review = _ev_review(_ev_test(), _ev_test("tests/test_two.py", content=EV_REPRO_PASS),
                                _ev_issue(evidence="recorded `tests/test_limits.py::test_negative`"))
            proc = _ev_run(root, repo, review, tests=tests,
                           extra=("--manifest-out", str(manifest)))
            self.assert_output(proc, [
                "fail", "finding F1: confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT),
                "finding F2: advisory (repro_passed)" + EV_AT,
                "finding F3: confirmed (recorded tests/test_limits.py::test_negative, exit 1)"
                + EV_AT,
                "reason: confirmed F1", "reason: confirmed F3", _ev_summary("fail", 2, 1, 0)])
            self.assertEqual(_mf_read(manifest), _mf_doc(MF_ENTRY))
            self.assertEqual([p.name for p in manifest.parent.iterdir()], [MF_NAME])

    def test_manifest_hash_is_of_the_normalized_repro(self) -> None:
        """AC-4.1, AC-4.2 — a fenced repro with trailing whitespace and extra
        blank lines at the end is recorded with the clean file's SHA-256 and
        its normalized text as `content`."""
        messy = ("from src.limits import parse_limit \t\n"
                 "\n"
                 "\n"
                 "def test_negative_limit_rejected():  \n"
                 "    assert parse_limit(\"-1\") is None\n\n\n")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            manifest = root / "state" / MF_NAME
            proc = _ev_run(root, repo, _ev_review(_ev_test(content=messy)),
                           extra=("--manifest-out", str(manifest)))
            self.assertIn("reason: confirmed F1", proc.stdout, proc.stdout + proc.stderr)
            self.assertEqual(_mf_read(manifest), _mf_doc(MF_ENTRY))

    def test_one_normalization_for_the_write_and_the_compare(self) -> None:
        """AC-4.1, AC-4.2 — CRLF endings, trailing whitespace, and a missing or
        repeated final newline hash as the clean file does; a change inside a
        line, to indentation, or a dropped blank line does not."""
        module = _ev_module()
        same = (EV_REPRO_FAIL.replace("\n", "\r\n"), EV_REPRO_FAIL.replace("\n", " \t\n"),
                EV_REPRO_FAIL.rstrip("\n"), EV_REPRO_FAIL + "\n\n\n",
                EV_REPRO_FAIL.replace("\n", "  \r\n").rstrip())
        for text in same:
            with self.subTest(text=text):
                self.assertEqual(module._normalized_sha256(text), MF_SHA)
        for text in (EV_REPRO_FAIL.replace("-1", "-2"),
                     EV_REPRO_FAIL.replace("    assert", "        assert"),
                     EV_REPRO_FAIL.replace("\n\n\n", "\n\n", 1)):
            with self.subTest(text=text):
                self.assertNotEqual(module._normalized_sha256(text), MF_SHA)

    def test_merge_keeps_earlier_entries_and_replaces_the_same_path(self) -> None:
        """AC-4.1 — an existing manifest keeps its other entries and its story
        in place; a new confirmation at a recorded path replaces that entry,
        and one at a new path is appended."""
        earlier = {"finding": "F2", "path": "tests/test_earlier_repro.py", "sha256": "a" * 64,
                   "kind": "test", "location": "src/routes.py:5"}
        stale = dict(MF_ENTRY, finding="F3", sha256="b" * 64, location="src/limits.py:9")
        for existing in ((earlier,), (earlier, stale)):
            with self.subTest(existing=len(existing)), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                manifest = _mf_write(root / "state" / MF_NAME,
                                     _mf_doc(*existing, story="story-9-earlier"))
                proc = _ev_run(root, repo, _ev_review(_ev_test()),
                               extra=("--manifest-out", str(manifest)))
                self.assertIn("reason: confirmed F1", proc.stdout, proc.stdout + proc.stderr)
                self.assertEqual(_mf_read(manifest),
                                 _mf_doc(earlier, MF_ENTRY, story="story-9-earlier"))

    def test_no_new_confirmation_leaves_the_file_unchanged(self) -> None:
        """AC-4.1 — a run that confirms no `test` repro leaves an existing
        manifest byte for byte, and creates none when there is none."""
        raw = b'{"schema":"evidence-manifest-v1","story":"x","repros":[]}'
        for existing in (True, False):
            with self.subTest(existing=existing), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                manifest = root / "state" / MF_NAME
                if existing:
                    manifest.parent.mkdir()
                    manifest.write_bytes(raw)
                proc = _ev_run(root, repo, _ev_review(_ev_test(content=EV_REPRO_PASS)),
                               extra=("--manifest-out", str(manifest)))
                self.assert_output(proc, ["pass", "finding F1: advisory (repro_passed)" + EV_AT,
                                          _ev_summary("pass", 0, 1, 0)])
                if existing:
                    self.assertEqual(manifest.read_bytes(), raw)
                else:
                    self.assertFalse(manifest.parent.exists())

    def test_unwritable_manifest_adds_manifest_write_failed(self) -> None:
        """AC-4.1 — a manifest that cannot be written (its parent is a file, or
        its path is a directory) adds `reason: manifest_write_failed`; line 1,
        the exit code, and the summary stay, and no temporary file is left."""
        for case in ("parent_is_file", "path_is_dir"):
            with self.subTest(case=case), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                state = root / "state"
                state.mkdir()
                if case == "parent_is_file":
                    (state / "blocker").write_text("", encoding="utf-8")
                    manifest = state / "blocker" / MF_NAME
                else:
                    manifest = state / MF_NAME
                    manifest.mkdir()
                proc = _ev_run(root, repo, _ev_review(_ev_test()),
                               extra=("--manifest-out", str(manifest)))
                self.assert_output(proc, [
                    "fail", "finding F1: confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT),
                    "reason: confirmed F1", "reason: manifest_write_failed",
                    _ev_summary("fail", 1, 0, 0)])
                left = sorted(p.name for p in state.iterdir())
                self.assertEqual(left, ["blocker"] if case == "parent_is_file" else [MF_NAME])

    def test_tree_mutation_writes_no_manifest(self) -> None:
        """AC-4.1 — a run that changed the tree is a BLOCKED escalation, not a
        recode, so not even the confirmed repro before it is recorded."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            manifest = root / "state" / MF_NAME
            proc = _ev_run(root, repo, _ev_review(
                _ev_test(), _ev_test("tests/test_second.py",
                                     content=EvidenceTreeSnapshotTests.WRITE_X)),
                extra=("--manifest-out", str(manifest)))
            self.assertEqual(proc.stdout.splitlines()[:2], [
                "fail", "finding F1: confirmed (test %s, exit 1)%s" % (EV_REPRO, EV_AT)],
                proc.stdout + proc.stderr)
            self.assertIn("reason: repro_mutated_tree src/x.py", proc.stdout)
            self.assertFalse(manifest.parent.exists())

    # --- the --prior checks ------------------------------------------------

    def test_removed_repro_fails_on_every_verdict(self) -> None:
        """AC-4.2 — a recorded path missing from `--changed`, or gone from disk:
        line 1 `fail` with `reason: repro_removed <path>`, on PASS, PAUSE, and
        FAIL alike."""
        reason = "repro_removed %s" % EV_REPRO
        for verdict in ("PASS", "PAUSE", "FAIL"):
            for case in ("not_in_changed", "deleted"):
                with self.subTest(verdict=verdict, case=case), TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    deleted = case == "deleted"
                    repo, manifest = self.prior_repo(root, None if deleted else EV_REPRO_FAIL)
                    proc = self.run_prior(root, repo, manifest, verdict,
                                          changed=MF_CHANGED if deleted else ("src/limits.py",))
                    self.assert_output(proc, _mf_prior_fail(reason) if verdict != "FAIL" else [
                        "fail", "reason: " + reason, _ev_summary("fail", 0, 0, 0)])

    def test_modified_repro_fails(self) -> None:
        """AC-4.2 — a recorded repro whose normalized content differs from the
        manifest: `reason: repro_modified <path>`, on any verdict."""
        weakened = EV_REPRO_FAIL.replace("is None", "== -1")
        for verdict in ("PASS", "FAIL"):
            with self.subTest(verdict=verdict), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root, weakened)
                proc = self.run_prior(root, repo, manifest, verdict)
                reason = "repro_modified %s" % EV_REPRO
                self.assert_output(proc, _mf_prior_fail(reason) if verdict == "PASS" else [
                    "fail", "reason: " + reason, _ev_summary("fail", 0, 0, 0)])

    def test_a_path_that_is_not_the_recorded_file_is_modified(self) -> None:
        """AC-4.2 — a directory at the path, or a file that is not UTF-8
        (Latin-1 bytes of the recorded text): `repro_modified <path>`."""
        latin = EV_REPRO_FAIL + "# caf\u00e9\n"
        for case in ("directory", "latin1"):
            with self.subTest(case=case), TemporaryDirectory() as tmp:
                root = Path(tmp)
                # The Latin-1 file holds the recorded text, so only a strict
                # UTF-8 read tells it apart.
                entry = (dict(MF_ENTRY, sha256=_ev_module()._normalized_sha256(latin))
                         if case == "latin1" else MF_ENTRY)
                repo, manifest = self.prior_repo(root, None, repros=(entry,))
                target = repo / EV_REPRO
                target.parent.mkdir(parents=True, exist_ok=True)
                if case == "directory":
                    target.mkdir()
                else:
                    target.write_bytes(latin.encode("latin-1"))
                proc = self.run_prior(root, repo, manifest, "PASS")
                self.assert_output(proc, _mf_prior_fail("repro_modified %s" % EV_REPRO))

    @unittest.skipUnless(hasattr(os, "symlink"), "needs os.symlink")
    def test_outside_symlink_with_the_recorded_content_is_modified(self) -> None:
        """AC-4.2 — a symlink at the path to a file outside the repo with the
        recorded content: `repro_modified <path>`. The outside file is never
        read as the repro."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, manifest = self.prior_repo(root, None)
            outside = root / "outside_repro.py"
            outside.write_text(EV_REPRO_FAIL, encoding="utf-8")
            (repo / "tests").mkdir()
            os.symlink(str(outside), str(repo / EV_REPRO))
            proc = self.run_prior(root, repo, manifest, "PASS")
            self.assert_output(proc, _mf_prior_fail("repro_modified %s" % EV_REPRO))

    def test_run_level_stop_after_the_prior_checks_keeps_the_prior_failure(self) -> None:
        """AC-4.2 — on FAIL, a run-level stop after the prior checks (runner
        binary missing, a runner that cannot start, no git) still gives line 1
        `fail`: the prior reasons, then the run-level reason, and the summary
        names the first prior reason."""
        removed = "repro_removed %s" % EV_REPRO
        cases = (("missing_runner", "/nonexistent/bin/pytest", None, True, "runner_not_found"),
                 ("runner_cannot_start", "bin/pytest", {"bin/pytest": "not a program\n"}, True,
                  "runner_not_found"),
                 ("no_git", EV_PYTEST, None, False, "no_git"))
        for name, runner, files, git, reason in cases:
            with self.subTest(case=name), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root, runner=runner, files=files, git=git)
                if files:
                    os.chmod(str(repo / "bin" / "pytest"), 0o755)
                proc = self.run_prior(root, repo, manifest, "FAIL",
                                      _ev_test("tests/test_second_repro.py"),
                                      changed=("src/limits.py",),
                                      env=_ev_env(GIT_CEILING_DIRECTORIES=str(root)))
                self.assert_output(proc, ["fail", "reason: " + removed, "reason: " + reason,
                                          "review-override evidence: fail (%s)" % removed])
                self.assertFalse((repo / "tests" / "test_second_repro.py").exists())

    def test_unread_verdict_is_verdict_not_fail_with_prior(self) -> None:
        """AC-4.2 — only PASS or PAUSE takes the prior-only path. No verdict
        line, or one the script cannot read (`**REVIEW_RESULT:** FAIL` without
        a heading), is `verdict_not_fail none`, as without `--prior`; a failed
        prior check still makes line 1 `fail`, so it cannot pass as row 9."""
        unread = "**REVIEW_RESULT:** FAIL\n\n### Summary\nOne issue.\n"
        for review in (_ev_review(verdict=None), unread):
            with self.subTest(review=review[:24]), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root)
                flags = ("--prior", str(manifest))
                proc = _ev_run(root, repo, review, changed=MF_CHANGED, tests=MF_RUN_OK,
                               extra=flags)
                self.assert_output(proc, _ev_unverifiable("verdict_not_fail none"))
                proc = _ev_run(root, repo, review, changed=("src/limits.py",), tests=MF_RUN_OK,
                               extra=flags)
                removed = "repro_removed %s" % EV_REPRO
                self.assert_output(proc, ["fail", "reason: " + removed,
                                          "reason: verdict_not_fail none",
                                          "review-override evidence: fail (%s)" % removed])

    def test_manifest_without_content_stays_valid(self) -> None:
        """AC-4.4 — `content` is optional: an entry written before it existed
        still checks out (`prior_ok`); a `content` that is not a string is
        `bad_manifest`."""
        old = {k: v for k, v in MF_ENTRY.items() if k != "content"}
        for entry, expected in ((old, MF_PRIOR_OK),
                                (dict(MF_ENTRY, content=7), _ev_unverifiable("bad_manifest"))):
            with self.subTest(entry=sorted(entry)), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root, repros=(entry,))
                self.assert_output(self.run_prior(root, repo, manifest, "PASS"), expected)

    def test_line_endings_and_trailing_whitespace_are_not_a_change(self) -> None:
        """AC-4.2 — CRLF endings, trailing whitespace, and the final newline
        alone do not count: with a passing recorded run, `pass` and
        `reason: prior_ok`."""
        for text in (EV_REPRO_FAIL.replace("\n", "\r\n"), EV_REPRO_FAIL.replace("\n", "  \n"),
                     EV_REPRO_FAIL.rstrip("\n"), EV_REPRO_FAIL + "\n\n"):
            with self.subTest(text=text), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root, text)
                self.assert_output(self.run_prior(root, repo, manifest, "PASS"), MF_PRIOR_OK)

    def test_still_failing_when_the_run_misses_the_path_or_did_not_exit_0(self) -> None:
        """AC-4.3 — a recorded run that does not name the repro's path, has no
        `exit code: 0` line, or is missing: `reason: repro_still_failing <path>`."""
        runs = ("command: python3 -m pytest tests/test_limits.py\nexit code: 0\n1 passed\n",
                "command: python3 -m pytest %s\nexit code: 1\n1 failed\n" % EV_REPRO,
                "command: python3 -m pytest %s\n1 passed\n" % EV_REPRO,
                None)
        for tests in runs:
            with self.subTest(tests=tests), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root)
                proc = self.run_prior(root, repo, manifest, "PAUSE", tests=tests)
                self.assert_output(proc, _mf_prior_fail("repro_still_failing %s" % EV_REPRO))

    def test_passing_repro_prints_no_reason_line(self) -> None:
        """AC-4.3 — the recorded run names the path and exits 0: no reason line
        for it. On PASS or PAUSE that is `pass` with `prior_ok`; on FAIL the
        new findings decide, as they do without `--prior`."""
        for verdict in ("PASS", "PAUSE", "FAIL"):
            with self.subTest(verdict=verdict), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root)
                proc = self.run_prior(root, repo, manifest, verdict)
                self.assert_output(proc, MF_PRIOR_OK if verdict != "FAIL" else [
                    "pass", _ev_summary("pass", 0, 0, 0)])

    def test_fail_verdict_evaluates_new_findings_after_the_prior_checks(self) -> None:
        """AC-4.2 — on FAIL, the prior reasons print first and new findings are
        then evaluated as usual."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, manifest = self.prior_repo(root)
            proc = self.run_prior(root, repo, manifest, "FAIL",
                                  _ev_test("tests/test_second_repro.py"),
                                  changed=("src/limits.py",))
            self.assert_output(proc, [
                "fail", "finding F1: confirmed (test tests/test_second_repro.py, exit 1)" + EV_AT,
                "reason: repro_removed %s" % EV_REPRO, "reason: confirmed F1",
                _ev_summary("fail", 1, 0, 0)])

    def test_pass_or_pause_runs_only_the_prior_checks(self) -> None:
        """AC-4.2 — on PASS or PAUSE no new finding is evaluated or run, and
        `--prior` writes nothing: git index, HEAD, status, and the manifest
        bytes are unchanged."""
        for verdict in ("PASS", "PAUSE"):
            with self.subTest(verdict=verdict), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo, manifest = self.prior_repo(root, runner="jest")
                status_args = ("--no-optional-locks", "status", "--porcelain=v1",
                               "--untracked-files=all")
                status = _ev_git(repo, *status_args)
                index = (repo / ".git" / "index").read_bytes()
                before = manifest.read_bytes()
                argv = root / "argv.jsonl"
                proc = self.run_prior(root, repo, manifest, verdict,
                                      _ev_test("src/limits.test.js"),
                                      env=_ev_env(STUB_ARGV=str(argv)))
                self.assert_output(proc, MF_PRIOR_OK)
                self.assertEqual(_ev_argv(argv), [])
                self.assertEqual((repo / ".git" / "index").read_bytes(), index)
                self.assertEqual(_ev_git(repo, *status_args), status)
                self.assertEqual(manifest.read_bytes(), before)

    def test_each_repro_reports_its_first_failing_check_in_manifest_order(self) -> None:
        """AC-4.2, AC-4.3 — removed, then modified, then still failing: one
        reason per repro, in manifest order; a passing repro adds none."""
        def entry(path: str) -> dict:
            return dict(MF_ENTRY, path=path)
        repros = (entry("tests/test_c_repro.py"), entry("tests/test_a_repro.py"), MF_ENTRY,
                  entry("tests/test_b_repro.py"))
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, manifest = self.prior_repo(root, repros=repros)
            (repo / "tests" / "test_c_repro.py").write_text(EV_REPRO_FAIL, encoding="utf-8")
            (repo / "tests" / "test_b_repro.py").write_text(EV_REPRO_PASS, encoding="utf-8")
            changed = ("src/limits.py", EV_REPRO, "tests/test_b_repro.py", "tests/test_c_repro.py")
            proc = self.run_prior(root, repo, manifest, "PASS", changed=changed)
            self.assert_output(proc, _mf_prior_fail(
                "repro_still_failing tests/test_c_repro.py", "repro_removed tests/test_a_repro.py",
                "repro_modified tests/test_b_repro.py"))

    def test_bad_manifest_is_unverifiable_and_the_verdict_stands(self) -> None:
        """AC-4.4 — a `--prior` manifest that is missing, unreadable, not JSON,
        not `evidence-manifest-v1`, or holds a malformed repro: `unverifiable`
        with `reason: bad_manifest`, exit 0, and nothing runs."""
        cases = {
            "missing": None,
            "directory": "dir",
            "not_json": "{",
            "wrong_schema": dict(_mf_doc(MF_ENTRY), schema="evidence-manifest-v0"),
            "no_schema": {"repros": [MF_ENTRY]},
            "not_an_object": [MF_ENTRY],
            "repros_not_a_list": dict(_mf_doc(), repros=MF_ENTRY),
            "entry_without_sha256": _mf_doc({"path": EV_REPRO, "kind": "test"}),
            "entry_outside_the_repo": _mf_doc(dict(MF_ENTRY, path="../outside_repro.py")),
            "absolute_entry": _mf_doc(dict(MF_ENTRY, path="/tmp/test_x_repro.py")),
        }
        for verdict in ("FAIL", "PASS"):
            for name, doc in cases.items():
                with self.subTest(verdict=verdict, case=name), TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    repo, manifest = self.prior_repo(root, runner="jest")
                    manifest.unlink()
                    if doc == "dir":
                        manifest.mkdir()
                    elif isinstance(doc, str):
                        manifest.write_text(doc, encoding="utf-8")
                    elif doc is not None:
                        _mf_write(manifest, doc)
                    argv = root / "argv.jsonl"
                    proc = self.run_prior(root, repo, manifest, verdict,
                                          _ev_test("src/limits.test.js"),
                                          env=_ev_env(STUB_ARGV=str(argv)))
                    self.assert_output(proc, _ev_unverifiable("bad_manifest"))
                    self.assertEqual(_ev_argv(argv), [])

    def test_switch_off_runs_no_prior_check(self) -> None:
        """AC-4.2 — with `Evidence Gate: off`, `--prior` checks nothing:
        `unverifiable` with `switch_off`, even for a removed repro."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, manifest = self.prior_repo(root, None)
            (repo / ".writ" / "config.md").write_text(
                _ev_config(EV_PYTEST, ("- **Evidence Gate:** off",)), encoding="utf-8")
            proc = self.run_prior(root, repo, manifest, "PASS")
            self.assert_output(proc, _ev_unverifiable("switch_off"))

    def test_round_trip_through_the_written_manifest(self) -> None:
        """AC-4.1, AC-4.2, AC-4.3 — the manifest a confirmed FAIL writes under
        `.writ/state/` guards the repro on re-review: absent, `repro_removed`;
        created from the brief (here with CRLF endings) and passing, `prior_ok`,
        and the manifest is left as it was."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _ev_repo(root)
            manifest = repo / ".writ" / "state" / MF_NAME
            flags = ("--manifest-out", str(manifest), "--prior", str(manifest))
            first = _ev_run(root, repo, _ev_review(_ev_test()), extra=flags[:2])
            self.assertIn("reason: confirmed F1", first.stdout, first.stdout + first.stderr)
            self.assertEqual(_mf_read(manifest), _mf_doc(MF_ENTRY))
            written = manifest.read_bytes()

            missing = _ev_run(root, repo, _ev_review(verdict="PASS"), tests=MF_RUN_OK, extra=flags)
            self.assert_output(missing, _mf_prior_fail("repro_removed %s" % EV_REPRO))

            (repo / "tests").mkdir()
            (repo / EV_REPRO).write_bytes(EV_REPRO_FAIL.replace("\n", "\r\n").encode("utf-8"))
            again = _ev_run(root, repo, _ev_review(verdict="PASS"), changed=MF_CHANGED,
                            tests=MF_RUN_OK, extra=flags)
            self.assert_output(again, MF_PRIOR_OK)
            self.assertEqual(manifest.read_bytes(), written)


if __name__ == "__main__":
    unittest.main()
