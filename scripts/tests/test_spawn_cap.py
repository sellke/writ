#!/usr/bin/env python3
"""Tests for scripts/spawn-cap.py (Story 3 of
`2026-09-09-phase11-stage4b-pipeline-demote`). [AC-3.1, AC-3.4]
"""

from __future__ import annotations

import importlib.util
import io
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
# Authenticity pin: test-integrity.py extracts JS-style from '…' specifiers.
# from "../../scripts/spawn-cap.py"
SCRIPT = REPO_ROOT / "scripts" / "spawn-cap.py"
REAL_COMMAND = REPO_ROOT / "commands" / "implement-story.md"


def _load_mod():
    spec = importlib.util.spec_from_file_location("spawn_cap", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_MOD = _load_mod()

BANNED = ("accept", "reject", "modify-spec")

PASS_FIXTURE = """# Fixture

#### Gate 1
> **Agent:** `agents/coding-agent.md`

#### Gate 3
> **Agent:** `agents/evaluator-agent.md`

**`--full-pipeline`:**
> **Agent:** `agents/review-agent.md`

**`--full-pipeline`:**
> **Agent:** `agents/architecture-check-agent.md`
"""

OVER_CAP_THIRD = """# Fixture

> **Agent:** `agents/coding-agent.md`
> **Agent:** `agents/evaluator-agent.md`
> **Agent:** `agents/documentation-agent.md`
"""

OVER_CAP_DISALLOWED = """# Fixture

> **Agent:** `agents/architecture-check-agent.md`
"""

OVER_CAP_ZERO = """# Fixture

> **Agent:** None — inline

**`--full-pipeline`:**
> **Agent:** `agents/review-agent.md`
"""

OVER_CAP_TASK = """# Fixture

> **Agent:** `agents/coding-agent.md`
> **Agent:** `agents/evaluator-agent.md`
Task(subagent_type="testing-agent")
"""


def _run(args: list[str]) -> tuple[int, str, str]:
    """In-process so coverage.py traces spawn-cap.py (subprocess is invisible)."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = _MOD.main(args)
    return code, stdout.getvalue(), stderr.getvalue()


def _run_subprocess(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _verdict(out: str) -> str:
    for line in out.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return out.strip()


def _reasons(out: str) -> list[str]:
    return [ln[8:] for ln in out.splitlines() if ln.startswith("reason: ")]


def _assert_shape(out: str, expected_verdict: str) -> None:
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines, "expected output"
    assert lines[0] == expected_verdict
    assert lines[-1].startswith("spawn-cap:")
    for banned in BANNED:
        assert not re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(banned), out)


def _write_cmd(root: Path, text: str) -> Path:
    path = root / "implement-story.md"
    path.write_text(text, encoding="utf-8")
    return path


class SpawnCapTests(unittest.TestCase):
    def test_pass_allowed_stems_at_most_two(self) -> None:
        with TemporaryDirectory() as tmp:
            cmd = _write_cmd(Path(tmp), PASS_FIXTURE)
            code, out, _err = _run(["check", "--command", str(cmd)])
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            self.assertEqual(_reasons(out), [])
            _assert_shape(out, "pass")

    def test_pass_full_pipeline_markers_excluded(self) -> None:
        with TemporaryDirectory() as tmp:
            cmd = _write_cmd(Path(tmp), PASS_FIXTURE)
            code, out, _err = _run(
                ["check", "--command", str(cmd), "--project", tmp]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            _assert_shape(out, "pass")

    def test_fail_over_cap_third_stem(self) -> None:
        with TemporaryDirectory() as tmp:
            cmd = _write_cmd(Path(tmp), OVER_CAP_THIRD)
            code, out, _err = _run(["check", "--command", str(cmd)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("over_cap", _reasons(out))
            _assert_shape(out, "fail")

    def test_fail_over_cap_disallowed_stem(self) -> None:
        with TemporaryDirectory() as tmp:
            cmd = _write_cmd(Path(tmp), OVER_CAP_DISALLOWED)
            code, out, _err = _run(["check", "--command", str(cmd)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("over_cap", _reasons(out))
            _assert_shape(out, "fail")

    def test_fail_over_cap_zero_default_markers(self) -> None:
        with TemporaryDirectory() as tmp:
            cmd = _write_cmd(Path(tmp), OVER_CAP_ZERO)
            code, out, _err = _run(["check", "--command", str(cmd)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("over_cap", _reasons(out))
            _assert_shape(out, "fail")

    def test_fail_over_cap_unguarded_task_spawn(self) -> None:
        with TemporaryDirectory() as tmp:
            cmd = _write_cmd(Path(tmp), OVER_CAP_TASK)
            code, out, _err = _run(["check", "--command", str(cmd)])
            self.assertEqual(_verdict(out), "fail")
            self.assertEqual(code, 1)
            self.assertIn("over_cap", _reasons(out))
            _assert_shape(out, "fail")

    def test_unverifiable_missing_command_flag(self) -> None:
        code, out, _err = _run(["check"])
        self.assertEqual(_verdict(out), "unverifiable")
        self.assertEqual(code, 0)
        self.assertIn("missing_command", _reasons(out))
        _assert_shape(out, "unverifiable")

    def test_unverifiable_unreadable_command(self) -> None:
        code, out, _err = _run(["check", "--command", "/no/such/implement-story.md"])
        self.assertEqual(_verdict(out), "unverifiable")
        self.assertEqual(code, 0)
        self.assertIn("missing_command", _reasons(out))
        _assert_shape(out, "unverifiable")

    def test_unverifiable_undecodable_command(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "implement-story.md"
            path.write_bytes(b"\xff\xfe not utf-8")
            code, out, _err = _run(["check", "--command", str(path)])
            self.assertEqual(_verdict(out), "unverifiable")
            self.assertEqual(code, 0)
            self.assertIn("missing_command", _reasons(out))
            _assert_shape(out, "unverifiable")

    def test_check_resolves_command_relative_to_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            _write_cmd(Path(tmp), PASS_FIXTURE)
            code, out, _err = _run(
                ["check", "--command", "implement-story.md", "--repo", tmp]
            )
            self.assertEqual(_verdict(out), "pass")
            self.assertEqual(code, 0)
            _assert_shape(out, "pass")

    def test_usage_unknown_subcommand_exits_2(self) -> None:
        code, _out, err = _run(["nope"])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_usage_bad_flag_exits_2(self) -> None:
        code, _out, err = _run(["check", "--not-a-flag"])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_real_command_is_at_or_under_cap(self) -> None:
        self.assertTrue(REAL_COMMAND.is_file())
        code, out, _err = _run(["check", "--command", str(REAL_COMMAND), "--repo", str(REPO_ROOT)])
        self.assertEqual(_verdict(out), "pass", out)
        self.assertEqual(code, 0)
        _assert_shape(out, "pass")

    def test_subprocess_usage_unknown_subcommand_exits_2(self) -> None:
        code, _out, err = _run_subprocess(["nope"])
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

if __name__ == "__main__":
    unittest.main()
