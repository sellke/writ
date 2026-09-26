#!/usr/bin/env python3
"""Unit tests for scripts/arch-lint.py (Story 3 of
`2026-09-26-arch-lint-and-follow-ups`).

Written before the implementation, per task 3.1. Every fixture is a temp
repo; nothing here creates `package.json`, `pyproject.toml`, `setup.cfg` or
`src/` at the real repo root. The CLI runs in a subprocess with `PATH`
pointed at a temp bin dir, so `lint-imports` presence is controlled exactly.

Detection table and output format: `sub-specs/technical-spec.md` §3.

Run: python3 scripts/tests/test_arch_lint.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "arch-lint.py"


class Fixture:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        self.bin = Path(self._tmp.name) / "bin"
        self.bin.mkdir()

    def write(self, rel: str, text: str = "") -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, rel: str, data: bytes) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def package(self, **fields: object) -> None:
        self.write("package.json", json.dumps(fields))

    def install_depcruise(self) -> None:
        self.write("node_modules/.bin/depcruise", "#!/bin/sh\n")

    def install_lint_imports(self) -> None:
        exe = self.bin / "lint-imports"
        exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        exe.chmod(0o755)

    def snapshot(self) -> Dict[str, bytes]:
        return {
            str(p.relative_to(self.root)): p.read_bytes()
            for p in sorted(self.root.rglob("*")) if p.is_file()
        }

    def cleanup(self) -> None:
        self._tmp.cleanup()


def run(args: List[str], path: Optional[Path] = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if path is not None:
        env["PATH"] = str(path)
    return subprocess.run(
        [sys.executable, str(HELPER)] + args,
        capture_output=True, text=True, env=env,
    )


class DetectCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def detect(self) -> List[str]:
        proc = run(["detect", "--repo", str(self.fx.root)], path=self.fx.bin)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.splitlines()


class DependencyCruiserTests(DetectCase):
    """AC-3.1, AC-3.2"""

    def test_every_config_extension_is_detected(self) -> None:
        for ext in ("js", "cjs", "mjs", "json"):
            with self.subTest(ext=ext):
                fx = Fixture()
                self.addCleanup(fx.cleanup)
                fx.write(".dependency-cruiser." + ext, "module.exports = {};\n")
                out = run(["detect", "--repo", str(fx.root)], path=fx.bin).stdout
                self.assertIn(
                    "tool: dependency-cruiser not-installed .dependency-cruiser." + ext,
                    out.splitlines(),
                )

    def test_not_installed_prints_no_command(self) -> None:
        self.fx.write(".dependency-cruiser.js")
        lines = self.detect()
        self.assertEqual(lines, [
            "pass",
            "tool: dependency-cruiser not-installed .dependency-cruiser.js",
            "arch-lint detect: 1 ruleset(s), 0 runnable",
        ])

    def test_npx_form_targets_src_when_it_exists(self) -> None:
        """AC-3.2: the §3 example output, verbatim."""
        self.fx.write(".dependency-cruiser.js")
        self.fx.write("src/index.js")
        self.fx.install_depcruise()
        self.fx.package(devDependencies={"eslint-plugin-boundaries": "^4.0.0"})
        self.assertEqual(self.detect(), [
            "pass",
            "tool: dependency-cruiser run .dependency-cruiser.js",
            "command: npx --no-install depcruise --config .dependency-cruiser.js src",
            "tool: eslint-plugin-boundaries via-eslint package.json",
            "arch-lint detect: 2 ruleset(s), 1 runnable",
        ])

    def test_npx_form_targets_dot_without_src(self) -> None:
        """AC-3.2"""
        self.fx.write(".dependency-cruiser.cjs")
        self.fx.install_depcruise()
        self.assertIn(
            "command: npx --no-install depcruise --config .dependency-cruiser.cjs .",
            self.detect(),
        )

    def test_package_script_containing_depcruise_is_preferred(self) -> None:
        """AC-3.2"""
        self.fx.write(".dependency-cruiser.js")
        self.fx.install_depcruise()
        self.fx.package(scripts={
            "test": "jest",
            "lint:deps": "depcruise --config .dependency-cruiser.js src",
        })
        lines = self.detect()
        self.assertIn("command: npm run lint:deps", lines)
        self.assertFalse(any("npx" in ln for ln in lines))

    def test_script_name_is_shell_quoted(self) -> None:
        """AC-3.2: Gate 2 runs the line in a shell, so the name stays one word."""
        self.fx.write(".dependency-cruiser.js")
        self.fx.install_depcruise()
        self.fx.package(scripts={"deps check": "depcruise src"})
        self.assertIn("command: npm run 'deps check'", self.detect())

    def test_package_script_is_ignored_when_not_installed(self) -> None:
        """AC-3.2: only runnable tools print `command:`."""
        self.fx.write(".dependency-cruiser.js")
        self.fx.package(scripts={"deps": "depcruise src"})
        self.assertFalse(any(ln.startswith("command:") for ln in self.detect()))

    def test_first_config_extension_wins(self) -> None:
        self.fx.write(".dependency-cruiser.js")
        self.fx.write(".dependency-cruiser.json", "{}")
        tools = [ln for ln in self.detect() if ln.startswith("tool:")]
        self.assertEqual(tools, [
            "tool: dependency-cruiser not-installed .dependency-cruiser.js",
        ])


class ImportLinterTests(DetectCase):
    """AC-3.1, AC-3.2"""

    def test_dot_importlinter_not_installed(self) -> None:
        self.fx.write(".importlinter", "[importlinter]\nroot_package = app\n")
        self.assertEqual(self.detect(), [
            "pass",
            "tool: import-linter not-installed .importlinter",
            "arch-lint detect: 1 ruleset(s), 0 runnable",
        ])

    def test_dot_importlinter_run_uses_lint_imports(self) -> None:
        self.fx.write(".importlinter", "[importlinter]\nroot_package = app\n")
        self.fx.install_lint_imports()
        self.assertEqual(self.detect(), [
            "pass",
            "tool: import-linter run .importlinter",
            "command: lint-imports",
            "arch-lint detect: 1 ruleset(s), 1 runnable",
        ])

    def test_setup_cfg_section(self) -> None:
        self.fx.write("setup.cfg", "[metadata]\nname = app\n\n[importlinter]\nroot_package = app\n")
        self.assertIn("tool: import-linter not-installed setup.cfg", self.detect())

    def test_setup_cfg_without_section_is_not_a_ruleset(self) -> None:
        self.fx.write("setup.cfg", "[metadata]\nname = app\n[importlinter:contract:1]\n")
        self.assertEqual(self.detect(), [
            "pass", "arch-lint detect: 0 ruleset(s), 0 runnable",
        ])

    def test_pyproject_only(self) -> None:
        self.fx.write("pyproject.toml", "[project]\nname = 'app'\n\n[tool.importlinter]\nroot_package = 'app'\n")
        self.fx.install_lint_imports()
        lines = self.detect()
        self.assertIn("tool: import-linter run pyproject.toml", lines)
        self.assertIn("command: lint-imports", lines)

    def test_pyproject_without_section_is_not_a_ruleset(self) -> None:
        self.fx.write("pyproject.toml", "[tool.ruff]\nline-length = 100\n")
        self.assertEqual(self.detect(), [
            "pass", "arch-lint detect: 0 ruleset(s), 0 runnable",
        ])


class ReportedOnlyTests(DetectCase):
    """AC-3.1, AC-3.2: eslint-plugin-boundaries and ArchUnit are reported,
    never run (spec Business Rule 3)."""

    def test_boundaries_in_dependencies(self) -> None:
        self.fx.package(dependencies={"eslint-plugin-boundaries": "4.0.0"})
        self.assertEqual(self.detect(), [
            "pass",
            "tool: eslint-plugin-boundaries via-eslint package.json",
            "arch-lint detect: 1 ruleset(s), 0 runnable",
        ])

    def test_archunit_in_each_build_file(self) -> None:
        for name, text in (
            ("pom.xml", "<artifactId>ArchUnit-junit5</artifactId>"),
            ("build.gradle", "testImplementation 'com.tngtech.archunit:archunit:1.2.0'"),
            ("build.gradle.kts", 'testImplementation("com.tngtech.ARCHUNIT:archunit")'),
        ):
            with self.subTest(file=name):
                fx = Fixture()
                self.addCleanup(fx.cleanup)
                fx.write(name, text)
                out = run(["detect", "--repo", str(fx.root)], path=fx.bin).stdout
                self.assertEqual(out.splitlines(), [
                    "pass",
                    "tool: archunit via-tests " + name,
                    "arch-lint detect: 1 ruleset(s), 0 runnable",
                ])

    def test_build_file_without_archunit_is_not_a_ruleset(self) -> None:
        self.fx.write("pom.xml", "<artifactId>junit</artifactId>")
        self.assertEqual(self.detect(), [
            "pass", "arch-lint detect: 0 ruleset(s), 0 runnable",
        ])


class OutputContractTests(DetectCase):
    """AC-3.1, AC-3.3"""

    def test_no_ruleset(self) -> None:
        self.assertEqual(self.detect(), [
            "pass", "arch-lint detect: 0 ruleset(s), 0 runnable",
        ])

    def test_empty_package_json_object(self) -> None:
        self.fx.write("package.json", "{}")
        self.assertEqual(self.detect(), [
            "pass", "arch-lint detect: 0 ruleset(s), 0 runnable",
        ])

    def test_all_four_print_in_table_order(self) -> None:
        self.fx.write("build.gradle", "archunit")
        self.fx.package(devDependencies={"eslint-plugin-boundaries": "4"})
        self.fx.write(".importlinter", "[importlinter]\n")
        self.fx.write(".dependency-cruiser.mjs")
        self.fx.install_depcruise()
        self.fx.install_lint_imports()
        self.assertEqual(self.detect(), [
            "pass",
            "tool: dependency-cruiser run .dependency-cruiser.mjs",
            "command: npx --no-install depcruise --config .dependency-cruiser.mjs .",
            "tool: import-linter run .importlinter",
            "command: lint-imports",
            "tool: eslint-plugin-boundaries via-eslint package.json",
            "tool: archunit via-tests build.gradle",
            "arch-lint detect: 4 ruleset(s), 2 runnable",
        ])

    def test_invalid_package_json_is_unverifiable_and_others_still_print(self) -> None:
        """AC-3.3"""
        self.fx.write("package.json", "{ not json")
        self.fx.write(".dependency-cruiser.js")
        self.fx.write(".importlinter", "[importlinter]\n")
        self.fx.install_depcruise()
        self.assertEqual(self.detect(), [
            "unverifiable",
            "tool: dependency-cruiser run .dependency-cruiser.js",
            "command: npx --no-install depcruise --config .dependency-cruiser.js .",
            "tool: import-linter not-installed .importlinter",
            "reason: config_unreadable package.json",
            "arch-lint detect: 2 ruleset(s), 1 runnable",
        ])

    def test_non_object_package_json_is_unverifiable(self) -> None:
        """AC-3.3"""
        self.fx.write("package.json", "[]")
        self.assertEqual(self.detect(), [
            "unverifiable",
            "reason: config_unreadable package.json",
            "arch-lint detect: 0 ruleset(s), 0 runnable",
        ])

    def test_undecodable_file_is_unverifiable(self) -> None:
        """AC-3.3"""
        self.fx.write_bytes("setup.cfg", b"[importlinter]\n\xff\xfe\xfa\n")
        self.fx.write("pom.xml", "archunit")
        self.assertEqual(self.detect(), [
            "unverifiable",
            "tool: archunit via-tests pom.xml",
            "reason: config_unreadable setup.cfg",
            "arch-lint detect: 1 ruleset(s), 0 runnable",
        ])

    def test_repo_defaults_to_cwd(self) -> None:
        self.fx.write(".importlinter", "[importlinter]\n")
        env = dict(os.environ, PATH=str(self.fx.bin))
        proc = subprocess.run(
            [sys.executable, str(HELPER), "detect"],
            capture_output=True, text=True, env=env, cwd=str(self.fx.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("tool: import-linter not-installed .importlinter", proc.stdout)

    def test_detection_writes_nothing(self) -> None:
        """AC-3.2: read-only."""
        self.fx.write(".dependency-cruiser.js")
        self.fx.write("package.json", "{ broken")
        self.fx.install_depcruise()
        before = self.fx.snapshot()
        self.detect()
        self.assertEqual(self.fx.snapshot(), before)


class UsageTests(unittest.TestCase):
    """AC-3.3: exit 2 on usage."""

    def test_no_subcommand(self) -> None:
        self.assertEqual(run([]).returncode, 2)

    def test_unknown_subcommand(self) -> None:
        self.assertEqual(run(["scan"]).returncode, 2)

    def test_missing_repo_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(["detect", "--repo", str(Path(tmp) / "absent")])
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")


class OfflineSourceTests(unittest.TestCase):
    """AC-3.2: no subprocess, no network, nothing installed; stdlib only.
    AC-3.3: the module docstring names the spec."""

    def setUp(self) -> None:
        self.source = HELPER.read_text(encoding="utf-8")

    def test_no_subprocess_or_network_imports(self) -> None:
        for banned in ("subprocess", "socket", "urllib", "http.client",
                       "os.system", "os.popen", "os.exec", "os.spawn"):
            self.assertNotIn(banned, self.source, banned)

    def test_lint_imports_is_found_with_shutil_which(self) -> None:
        self.assertIn("shutil.which", self.source)

    def test_docstring_names_the_spec(self) -> None:
        self.assertIn("2026-09-26-arch-lint-and-follow-ups", self.source.split('"""')[1])


if __name__ == "__main__":
    unittest.main()
