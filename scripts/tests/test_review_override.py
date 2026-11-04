#!/usr/bin/env python3
"""Tests for scripts/review-override.py (Story 1 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Fixtures cover pass, fail-from-ac-trace, fail-from-integrity,
unverifiable-helper, and missing --spec / --story. Helpers are invoked as
subprocesses — stubs record argv so the tests prove the script did not
re-derive findings itself. [AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
"""

from __future__ import annotations

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
        self.assertIn("scripts/review-override.py check", gate3)
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
        "review-override safety-fact: %s (measured %s, floor traced)" % (verdict, measured),
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
        """AC-4.2 — a `--blast-radius` path that does not exist is unreadable, not unverifiable."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            proc = _sf_run(root, repo, _sf_review(evidence=("- traced: src/other.py:1 — x",)),
                           extra=["--blast-radius", str(root / "missing.json")])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
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
    [AC-4.1, AC-4.3]"""

    TRACED = ("- read: src/lib.py:2", "- traced: src/caller.py:3 — passes [1, 2]")

    def run_review(self, review: str | None, **kwargs) -> subprocess.CompletedProcess:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _sf_repo(root)
            return _sf_run(root, repo, review, **kwargs)

    def assert_output(self, proc: subprocess.CompletedProcess, expected: list) -> None:
        self.assertEqual(proc.stdout.splitlines(), expected, proc.stderr)
        self.assertEqual(proc.returncode, 0 if expected[0] == "pass" else 1)

    def test_pass_prints_contract_lines(self) -> None:
        """AC-4.3 — section present, measured `traced`, `Holds: yes` → pass, exit 0."""
        proc = self.run_review(_sf_review(evidence=self.TRACED))
        self.assert_output(proc, _sf_expected("pass", "traced", "traced", SF_FACT, []))

    def test_holds_no_with_fail_or_pause_passes(self) -> None:
        """AC-4.3 — `Holds: no` agrees with a FAIL or PAUSE verdict."""
        for verdict in ("FAIL", "PAUSE", "**FAIL**"):
            with self.subTest(verdict=verdict):
                proc = self.run_review(_sf_review(holds="no", verdict=verdict,
                                                  evidence=self.TRACED))
                self.assert_output(proc, _sf_expected("pass", "traced", "traced", SF_FACT, []))

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
                proc = self.run_review(_sf_review(heading=heading, evidence=self.TRACED))
                self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)
        for heading in ("# Safety Fact", "### Safety Facts", "### Safety Fact (draft)"):
            with self.subTest(heading=heading):
                proc = self.run_review(_sf_review(heading=heading, evidence=self.TRACED))
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
                proc = self.run_review(_sf_review(fact=fact, evidence=self.TRACED))
                self.assert_output(proc, _sf_expected("fail", "traced", "traced", "(none)",
                                                      ["safety_fact_missing fact"]))

    def test_missing_holds_alone(self) -> None:
        """AC-4.3 — Holds not `yes`/`no` is `safety_fact_missing holds`."""
        for holds in ("maybe", "yes | no", "", None):
            with self.subTest(holds=holds):
                proc = self.run_review(_sf_review(holds=holds, evidence=self.TRACED))
                self.assert_output(proc, _sf_expected("fail", "traced", "traced", SF_FACT,
                                                      ["safety_fact_missing holds"]))

    def test_missing_rung_alone(self) -> None:
        """AC-4.3 — Rung not one of the five is `safety_fact_missing rung`; claimed prints `none`."""
        for rung in ("solid", "", None):
            with self.subTest(rung=rung):
                proc = self.run_review(_sf_review(rung=rung, evidence=self.TRACED))
                self.assert_output(proc, _sf_expected("fail", "none", "traced", SF_FACT,
                                                      ["safety_fact_missing rung"]))

    def test_missing_items_one_line_each_in_order(self) -> None:
        """AC-4.3 — every missing item gets its own line: fact, holds, rung."""
        proc = self.run_review(_sf_review(fact="", holds=None, rung="?", evidence=self.TRACED))
        self.assert_output(proc, _sf_expected(
            "fail", "none", "traced", "(none)",
            ["safety_fact_missing fact", "safety_fact_missing holds",
             "safety_fact_missing rung"]))

    def test_below_floor_alone(self) -> None:
        """AC-4.3 — measured `read` under the `traced` floor."""
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
                proc = self.run_review(_sf_review(holds="no", verdict=verdict,
                                                  evidence=self.TRACED))
                self.assert_output(proc, _sf_expected("fail", "traced", "traced", SF_FACT,
                                                      ["safety_fact_contradicts_verdict"]))

    def test_contradicts_when_no_verdict_line(self) -> None:
        """AC-4.3 — `Holds: no` with no FAIL or PAUSE verdict found is treated as a contradiction."""
        proc = self.run_review(_sf_review(holds="no", verdict=None, evidence=self.TRACED))
        self.assert_output(proc, _sf_expected("fail", "traced", "traced", SF_FACT,
                                              ["safety_fact_contradicts_verdict"]))

    def test_evaluation_result_verdict_is_read(self) -> None:
        """AC-4.3 — the verdict comes from the first REVIEW_RESULT or EVALUATION_RESULT heading."""
        review = _sf_review(holds="no", verdict=None, evidence=self.TRACED)
        proc = self.run_review("### EVALUATION_RESULT: FAIL\n\n" + review)
        self.assertEqual(proc.stdout.splitlines()[0], "pass", proc.stdout)
        proc = self.run_review("## REVIEW_RESULT: PASS\n\n### REVIEW_RESULT: FAIL\n\n" + review)
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
        """AC-4.3 — claimed `tested`, measured `traced`: the rung line shows both, verdict pass."""
        proc = self.run_review(_sf_review(rung="tested", evidence=self.TRACED))
        self.assert_output(proc, _sf_expected("pass", "tested", "traced", SF_FACT, []))

    def test_underclaim_prints_measured(self) -> None:
        """AC-4.3 — claimed `read` with `traced` evidence measures `traced` and passes."""
        proc = self.run_review(_sf_review(rung="read", evidence=self.TRACED))
        self.assert_output(proc, _sf_expected("pass", "read", "traced", SF_FACT, []))

    def test_fields_case_insensitive_bold_optional(self) -> None:
        """AC-4.3 — `Fact:`, `**holds:**`, `RUNG:`, `**Rung**:` and `- Traced:` all parse."""
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
        self.assert_output(proc, _sf_expected("pass", "traced", "traced", SF_FACT, []))

    def test_first_field_occurrence_wins(self) -> None:
        """AC-4.3 — a second `Holds:` line in the section is ignored."""
        review = _sf_review(evidence=self.TRACED + ("**Holds:** no",))
        proc = self.run_review(review)
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
            self.assert_output(proc, _sf_expected("pass", "traced", "traced", SF_FACT, []))
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
        """AC-2.2 — `--surface gate3|review`, `--manifest-out`, `--prior`, and
        `--timeout` parse; the manifest flags write nothing yet."""
        for case in ("gate3", "review", "manifest"):
            with self.subTest(case=case), TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = _ev_repo(root)
                out = root / "out"
                extra = ("--surface", case) if case != "manifest" else (
                    "--manifest-out", str(out / "evidence.json"),
                    "--prior", str(out / "prior.json"), "--timeout", "30")
                proc = _ev_run(root, repo, _ev_review(), extra=extra)
                self.assert_output(proc, ["pass", _ev_summary("pass", 0, 0, 0)])
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


if __name__ == "__main__":
    unittest.main()
