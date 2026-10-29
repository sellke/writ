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


if __name__ == "__main__":
    unittest.main()
