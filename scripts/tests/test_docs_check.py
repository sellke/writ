#!/usr/bin/env python3
"""Tests for scripts/docs-check.py (Story 3 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Tiny app trees only — this markdown repo is never a `pass` fixture.
Writ-the-product is the `unverifiable` case. [AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "docs-check.py"


def _run(repo: Path, args: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or repo),
    )
    return proc.returncode, proc.stdout


def _verdict_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
    return stdout.splitlines()[0] if stdout.splitlines() else ""


def _reasons(stdout: str) -> list[str]:
    return [ln[8:] for ln in stdout.splitlines() if ln.startswith("reason: ")]


def _summary(stdout: str) -> str:
    lines = [ln for ln in stdout.splitlines() if ln]
    return lines[-1] if lines else ""


def _assert_shape(test: unittest.TestCase, stdout: str, verdict: str) -> None:
    lines = [ln for ln in stdout.splitlines() if ln]
    test.assertTrue(lines, stdout)
    test.assertEqual(lines[0], verdict, stdout)
    test.assertFalse(lines[-1].startswith("reason: "), stdout)
    test.assertNotIn(lines[-1], ("pass", "fail", "unverifiable"), stdout)
    for line in lines[1:-1]:
        test.assertTrue(line.startswith("reason: "), stdout)


class DocsCheckFixtures(unittest.TestCase):
    def test_export_documented_is_pass(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src" / "api.py"
            src.parent.mkdir(parents=True)
            src.write_text(
                '__all__ = ["create_user"]\n\n'
                "def create_user():\n"
                "    return None\n",
                encoding="utf-8",
            )
            (repo / "README.md").write_text(
                "# Demo\n\nPublic API: `create_user`.\n",
                encoding="utf-8",
            )
            code, out = _run(
                repo,
                ["check", "--repo", str(repo), "--changed", "src/api.py"],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")
            self.assertEqual(_reasons(out), [])
            _assert_shape(self, out, "pass")
            self.assertIn("docs-check:", _summary(out))

    def test_export_undocumented_is_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src" / "api.py"
            src.parent.mkdir(parents=True)
            src.write_text(
                '__all__ = ["create_user"]\n\n'
                "def create_user():\n"
                "    return None\n",
                encoding="utf-8",
            )
            (repo / "README.md").write_text("# Demo\n\nNo public symbols named.\n", encoding="utf-8")
            code, out = _run(
                repo,
                ["check", "--repo", str(repo), "--changed", "src/api.py"],
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(_verdict_line(out), "fail")
            self.assertIn("undocumented_export", _reasons(out))
            _assert_shape(self, out, "fail")

    def test_markdown_only_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "commands").mkdir()
            (repo / "README.md").write_text("# Writ-shaped markdown product\n", encoding="utf-8")
            (repo / "commands" / "ship.md").write_text("# Ship\n\nA command file.\n", encoding="utf-8")
            code, out = _run(
                repo,
                [
                    "check",
                    "--repo",
                    str(repo),
                    "--changed",
                    "README.md",
                    "commands/ship.md",
                ],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("no_public_exports", _reasons(out))
            _assert_shape(self, out, "unverifiable")

    def test_omitted_changed_without_git_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("# No git\n", encoding="utf-8")
            code, out = _run(repo, ["check", "--repo", str(repo)])
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("changed_set_unresolved", _reasons(out))
            _assert_shape(self, out, "unverifiable")

    def test_omitted_changed_without_head_parent_is_unverifiable(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git_dir = repo / ".git"
            git_dir.mkdir()
            (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            (repo / "README.md").write_text("# Broken git (no HEAD^)\n", encoding="utf-8")
            code, out = _run(repo, ["check", "--repo", str(repo)])
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("changed_set_unresolved", _reasons(out))

    def test_usage_without_subcommand_is_exit_2(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_missing_repo_is_exit_2(self) -> None:
        code, out = _run(
            REPO_ROOT,
            ["check", "--repo", str(REPO_ROOT / "does-not-exist"), "--changed", "x.py"],
        )
        self.assertEqual(code, 2, out)

    def test_writ_markdown_changed_file_is_unverifiable_not_pass(self) -> None:
        code, out = _run(
            REPO_ROOT,
            ["check", "--repo", str(REPO_ROOT), "--changed", "README.md"],
        )
        self.assertEqual(code, 0, out)
        self.assertEqual(_verdict_line(out), "unverifiable")
        self.assertNotEqual(_verdict_line(out), "pass")
        self.assertNotEqual(_verdict_line(out), "fail")

    def test_adjacent_docstring_counts_as_documented(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src" / "api.py"
            src.parent.mkdir(parents=True)
            src.write_text(
                '__all__ = ["create_user"]\n\n'
                "def create_user():\n"
                '    """Register an account."""\n'
                "    return None\n",
                encoding="utf-8",
            )
            code, out = _run(
                repo,
                ["check", "--repo", str(repo), "--changed", "src/api.py"],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")

    def test_js_export_documented_is_pass(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src" / "api.ts"
            src.parent.mkdir(parents=True)
            src.write_text("export function createUser(): void {}\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text("Added createUser.\n", encoding="utf-8")
            code, out = _run(
                repo,
                ["check", "--repo", str(repo), "--changed", "src/api.ts"],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "pass")

    def test_does_not_invent_exports_from_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text(
                "This names create_user and ship_release but they are not exports.\n",
                encoding="utf-8",
            )
            code, out = _run(
                repo,
                ["check", "--repo", str(repo), "--changed", "README.md"],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")
            self.assertIn("no_public_exports", _reasons(out))

    def test_bare_python_defs_are_not_exports(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            src = repo / "src" / "api.py"
            src.parent.mkdir(parents=True)
            src.write_text(
                "def create_user():\n"
                "    return None\n",
                encoding="utf-8",
            )
            (repo / "README.md").write_text("create_user\n", encoding="utf-8")
            code, out = _run(
                repo,
                ["check", "--repo", str(repo), "--changed", "src/api.py"],
            )
            self.assertEqual(code, 0, out)
            self.assertEqual(_verdict_line(out), "unverifiable")


class Gate5WiringTests(unittest.TestCase):
    """AC-3.5 — Gate 5 verify block and frontmatter."""

    def test_gate_5_has_verify_block(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 5: Documentation Agent")
        gate5 = text[start:]
        self.assertIn("Verify the claim, don't trust it.", gate5)
        self.assertIn("scripts/docs-check.py check", gate5)
        self.assertIn("documentation-agent", gate5)
        self.assertIn("⚠️ DEGRADED", gate5)

    def test_frontmatter_names_docs_check(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate5_docs\n    script: scripts/docs-check.py", text)


if __name__ == "__main__":
    unittest.main()
