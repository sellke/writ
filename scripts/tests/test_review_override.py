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


if __name__ == "__main__":
    unittest.main()
