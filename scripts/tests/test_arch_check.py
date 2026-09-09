#!/usr/bin/env python3
"""Tests for scripts/arch-check.py (Story 2 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Fixtures cover planned-inside-boundary → proceed, planned-empty → caution,
out-of-scope → caution, invalid story-deps → fail, no mode → unverifiable,
both flags → exit 2, and --classify-abort → abort_is_llm_residual.
Helpers are invoked as subprocesses — stubs record argv so the tests prove
the script did not re-parse the story graph itself. [AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "arch-check.py"
REAL_STORY_DEPS = REPO_ROOT / "scripts" / "story-deps.py"

STUB_STORY_DEPS = r'''
import json, sys
from pathlib import Path
Path(__file__).with_name("story-deps.calls").write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
payload = json.loads(Path(__file__).with_name("story-deps.out.json").read_text(encoding="utf-8"))
print(json.dumps(payload, sort_keys=True))
raise SystemExit(int(payload.get("exit", 0)))
'''


def _write_story(spec: Path, number: int, dependencies: str = "None") -> Path:
    stories = spec / "user-stories"
    stories.mkdir(parents=True, exist_ok=True)
    path = stories / ("story-%d-fixture.md" % number)
    path.write_text(
        "\n".join([
            "# Story %d: Fixture" % number,
            "",
            "> **Status:** Not Started",
            "> **Priority:** High",
            "> **Dependencies:** %s" % dependencies,
            "",
            "## User Story",
            "",
            "Fixture.",
            "",
        ]) + "\n",
        encoding="utf-8",
    )
    return path


def _stub_tree(tmp: Path, payload: dict) -> Path:
    scripts = tmp / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts / "arch-check.py")
    (scripts / "story-deps.py").write_text(STUB_STORY_DEPS, encoding="utf-8")
    (scripts / "story-deps.out.json").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8"
    )
    return scripts / "arch-check.py"


def _run(script: Path, args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or script.parent.parent),
    )
    return proc.returncode, proc.stdout


def _verdict_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return stdout


def _reasons(stdout: str) -> list[str]:
    return [ln[8:] for ln in stdout.splitlines() if ln.startswith("reason: ")]


def _rederived(stdout: str) -> str | None:
    for ln in stdout.splitlines():
        if ln.startswith("rederived: "):
            return ln[11:]
    return None


def _ok_payload() -> dict:
    return {
        "schema": "story-graph/v1",
        "status": "ok",
        "batches": [["story-1"]],
        "graph": {"story-1": []},
        "exit": 0,
    }


class ArchCheckCliTests(unittest.TestCase):
    def test_planned_inside_boundary_is_proceed(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            boundary = repo / "boundary.json"
            boundary.write_text(
                json.dumps({
                    "owned": ["src/app.py"],
                    "readable": ["docs/readme.md"],
                    "out_of_scope": ["secrets/key"],
                }),
                encoding="utf-8",
            )
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned", "src/app.py",
                    "--boundary", str(boundary),
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")
            self.assertEqual(_rederived(out), "proceed")
            calls = json.loads(
                (repo / "scripts" / "story-deps.calls").read_text(encoding="utf-8")
            )
            self.assertEqual(calls[0], "validate")
            self.assertIn("--spec-dir", calls)
            spec_dir = Path(calls[calls.index("--spec-dir") + 1]).resolve()
            self.assertEqual(spec_dir, spec.resolve())

    def test_planned_empty_is_caution(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned",
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")
            self.assertEqual(_rederived(out), "caution")
            self.assertIn("empty_file_set", _reasons(out))
            self.assertTrue((repo / "scripts" / "story-deps.calls").exists())

    def test_out_of_scope_path_is_caution(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            boundary = repo / "boundary.json"
            boundary.write_text(
                json.dumps({
                    "owned": ["src/app.py"],
                    "readable": [],
                    "out_of_scope": ["secrets/key"],
                }),
                encoding="utf-8",
            )
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned", "secrets/key",
                    "--boundary", str(boundary),
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")
            self.assertEqual(_rederived(out), "caution")
            self.assertIn("out_of_scope", _reasons(out))

    def test_invalid_story_deps_stub_blocker_is_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(
                repo,
                {
                    "blocker": {
                        "code": "dependency_cycle",
                        "summary": "story-1 -> story-2 -> story-1",
                    },
                    "exit": 1,
                },
            )
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned", "src/app.py",
                ],
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict_line(out), "fail")
            self.assertIn("dependency_cycle", _reasons(out))
            self.assertTrue((repo / "scripts" / "story-deps.calls").exists())

    def test_invalid_story_deps_real_cycle_is_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1, dependencies="Story 2")
            _write_story(spec, 2, dependencies="Story 1")
            scripts = repo / "scripts"
            scripts.mkdir()
            shutil.copy2(SCRIPT, scripts / "arch-check.py")
            shutil.copy2(REAL_STORY_DEPS, scripts / "story-deps.py")
            code, out = _run(
                scripts / "arch-check.py",
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--changed", "src/app.py",
                ],
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict_line(out), "fail")
            self.assertTrue(_reasons(out), out)

    def test_no_mode_flag_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            code, out = _run(
                script,
                ["check", "--story", str(story), "--repo", str(repo)],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("no_file_mode", _reasons(out))
            self.assertFalse((repo / "scripts" / "story-deps.calls").exists())

    def test_both_planned_and_changed_is_exit_2(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned", "src/a.py",
                    "--changed", "src/b.py",
                ],
            )
            self.assertEqual(code, 2, out)
            self.assertNotEqual(_verdict_line(out), "pass")
            self.assertFalse((repo / "scripts" / "story-deps.calls").exists())

    def test_classify_abort_is_unverifiable_residual(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned", "src/app.py",
                    "--classify-abort",
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("abort_is_llm_residual", _reasons(out))
            self.assertIsNone(_rederived(out))
            for line in out.splitlines():
                self.assertNotEqual(line.strip(), "abort", out)
            self.assertIsNone(
                re.search(r"(?m)^abort$", out),
                "stdout must not contain a standalone abort verdict:\n%s" % out,
            )
            self.assertNotIn("ABORT", out)
            self.assertFalse((repo / "scripts" / "story-deps.calls").exists())

    def test_no_boundary_does_not_treat_tree_as_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            spec = repo / "demo-spec"
            story = _write_story(spec, 1)
            script = _stub_tree(repo, _ok_payload())
            code, out = _run(
                script,
                [
                    "check",
                    "--story", str(story),
                    "--repo", str(repo),
                    "--planned", "anywhere/file.py",
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")
            self.assertEqual(_rederived(out), "proceed")

    def test_usage_without_subcommand_is_exit_2(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_check_repo_only_is_no_file_mode(self) -> None:
        code, out = _run(SCRIPT, ["check", "--repo", str(REPO_ROOT)])
        self.assertEqual(code, 0, out)
        self.assertEqual(_verdict_line(out), "unverifiable")
        self.assertIn("no_file_mode", _reasons(out))


class Gate0WiringTests(unittest.TestCase):
    """AC-2.3 / AC-2.4 — command body and frontmatter after Story 2."""

    def test_gate_0_has_verify_block_and_leaves_abort_untouched(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 0: Architecture Check")
        end = text.index("#### Gate 0.5:", start)
        gate0 = text[start:end]
        self.assertIn("Verify the claim, don't trust it.", gate0)
        self.assertIn("scripts/arch-check.py check", gate0)
        self.assertIn("--planned", gate0)
        self.assertIn("never on ABORT", gate0)
        self.assertIn("ADR-024", gate0)
        self.assertIn("⚠️ DEGRADED", gate0)

    def test_frontmatter_names_arch_check(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate0_arch\n    script: scripts/arch-check.py", text)


if __name__ == "__main__":
    unittest.main()
