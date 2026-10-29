#!/usr/bin/env python3
"""Tests for scripts/review-override.py (Story 1 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Fixtures cover pass, fail-from-ac-trace, fail-from-integrity,
unverifiable-helper, and missing --spec / --story. Helpers are invoked as
subprocesses — stubs record argv so the tests prove the script did not
re-derive findings itself. [AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


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
        self.assertIn("FAIL-only", gate3)
        self.assertIn("does not force PASS", gate3)
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

SWITCH_KEYS = {"safety-fact": "Safety Fact", "reviewer-filters": "Reviewer Filters"}


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


if __name__ == "__main__":
    unittest.main()
