#!/usr/bin/env python3
"""Unit tests for scripts/quality-config-audit.py (Story 2 of
`2026-08-14-script-backed-quality-gates`).

Written before the implementation, per task 2.1. The highest-value tests in
this suite are the parse-failure downgrades: a heuristic that fails to find
`ignoreBuildErrors` has learned nothing about whether the gate is on, and a
checker that reports the absence of a pattern as a clean bill of health
reproduces exactly the defect this story exists to catch.

Run: python3 -m unittest scripts.tests.test_quality_config_audit
  or: python3 scripts/tests/test_quality_config_audit.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HELPER_PATH = Path(__file__).resolve().parents[1] / "quality-config-audit.py"

_spec = importlib.util.spec_from_file_location("quality_config_audit", HELPER_PATH)
assert _spec and _spec.loader
qca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qca)


def codes(result: dict) -> list[str]:
    return [f["code"] for f in result["findings"]]


def finding(result: dict, code: str) -> dict | None:
    for f in result["findings"]:
        if f["code"] == code:
            return f
    return None


def unverifiable_codes(result: dict) -> list[str]:
    return [entry["code"] for entry in result["unverifiable"]]


class ProjectFixture:
    """A disposable project tree. Only the files a test names exist, so a
    finding can never be produced by a file the test did not intend."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def cleanup(self) -> None:
        self._tmp.cleanup()


# --- Fixture content ---------------------------------------------------------

PACKAGE_JSON_MINIMAL = json.dumps({"name": "fixture", "version": "1.0.0"})

# The yuss shape, reproduced structurally: the two disabling keys sit at
# lines 8 and 11 of the real file, and the wrapper call is what defeats any
# attempt to evaluate the module.
NEXT_CONFIG_DISABLED = """const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
}

module.exports = withBundleAnalyzer(nextConfig)
"""

NEXT_CONFIG_ENABLED = """/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
}

module.exports = nextConfig
"""

# No anchor of any kind: nothing to match on, so nothing may be concluded.
NEXT_CONFIG_OPAQUE = """module.exports = require('./config/build')(process.env.NODE_ENV)
"""

JEST_CONFIG_NO_THRESHOLD = """const nextJest = require('next/jest')
const createJestConfig = nextJest({ dir: './' })

const customJestConfig = {
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/$1' },
  collectCoverageFrom: [
    'lib/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'utils/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
}

module.exports = createJestConfig(customJestConfig)
"""

JEST_CONFIG_ZERO_THRESHOLD = """module.exports = {
  collectCoverageFrom: ['lib/**/*.ts'],
  coverageThreshold: {
    global: { lines: 0, statements: 0 },
  },
}
"""

JEST_CONFIG_REAL_THRESHOLD = """module.exports = {
  collectCoverageFrom: ['lib/**/*.ts'],
  coverageThreshold: {
    global: { lines: 80, statements: 80 },
  },
}
"""

JEST_CONFIG_OPAQUE = """module.exports = require('./jest/base')
"""

TSCONFIG_JSONC = """{
  // Comments are legal here and json.loads rejects them.
  "compilerOptions": {
    "strict": true,
  },
  "include": ["**/*.ts"],
  "exclude": ["node_modules", "**/__tests__/**", "tests/**"],
}
"""

TSCONFIG_CLEAN = """{
  "compilerOptions": { "strict": true },
  "include": ["**/*.ts"],
  "exclude": ["node_modules"]
}
"""


class BuildGateDisabledTests(unittest.TestCase):
    """AC-2.1 — a Next.js config that switches off the typecheck or lint gate.

    The NEXT_CONFIG_DISABLED fixture reproduces the shape of the real checkout
    this spec's evidence comes from, including both keys' line numbers, so it
    also stands behind AC-2.5.
    """

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_both_disabling_keys_reported_with_file_and_line(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        exit_code, result = qca.check(self.fx.root, baseline=None)

        gate_findings = [f for f in result["findings"] if f["code"] == "build_gate_disabled"]
        self.assertEqual(len(gate_findings), 2)
        self.assertEqual([f["line"] for f in gate_findings], [8, 11])
        self.assertTrue(all(f["file"] == "next.config.js" for f in gate_findings))
        self.assertTrue(all(f["severity"] == "blocking" for f in gate_findings))
        self.assertEqual(exit_code, 1)
        self.assertEqual(result["verdict"], "fail")

    def test_explicitly_false_keys_are_not_a_finding(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_ENABLED)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("build_gate_disabled", codes(result))
        self.assertNotIn("could_not_parse", codes(result))

    def test_measured_field_quotes_the_offending_source(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        _, result = qca.check(self.fx.root, baseline=None)
        gate = finding(result, "build_gate_disabled")
        assert gate is not None
        self.assertIn("ignoreDuringBuilds", gate["measured"])


class CoverageThresholdTests(unittest.TestCase):
    """AC-2.2 — a zero bar and an absent bar are the same bar. AC-2.5 pins the
    same finding against the real checkout's jest.config.js."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_absent_threshold_with_collection_configured_is_blocking(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        exit_code, result = qca.check(self.fx.root, baseline=None)
        threshold = finding(result, "coverage_threshold_absent")
        assert threshold is not None
        self.assertEqual(threshold["severity"], "blocking")
        self.assertEqual(threshold["file"], "jest.config.js")
        self.assertEqual(exit_code, 1)

    def test_zero_threshold_is_the_same_finding_as_no_threshold(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_ZERO_THRESHOLD)
        exit_code, result = qca.check(self.fx.root, baseline=None)
        threshold = finding(result, "coverage_threshold_absent")
        assert threshold is not None
        self.assertEqual(threshold["severity"], "blocking")
        self.assertEqual(exit_code, 1)

    def test_real_threshold_is_clean(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_REAL_THRESHOLD)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("coverage_threshold_absent", codes(result))

    def test_threshold_configured_in_package_json_is_found(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "jest": {
                "collectCoverageFrom": ["lib/**/*.ts"],
                "coverageThreshold": {"global": {"lines": 75}},
            },
        }))
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("coverage_threshold_absent", codes(result))

    def test_absent_threshold_in_package_json_jest_block_is_blocking(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "jest": {"collectCoverageFrom": ["lib/**/*.ts"]},
        }))
        exit_code, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("coverage_threshold_absent", codes(result))
        self.assertEqual(exit_code, 1)


class ParseFailureDowngradeTests(unittest.TestCase):
    """AC-2.3 — the heart of the story. A pattern's absence is never evidence
    the gate is enabled."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_opaque_next_config_downgrades_build_gate_to_unverifiable(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_OPAQUE)
        exit_code, result = qca.check(self.fx.root, baseline=None)

        self.assertIn("could_not_parse", codes(result))
        self.assertIn("build_gate_disabled", unverifiable_codes(result))
        self.assertIn("next.config.js", result["inspected"]["unparsed"])
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(exit_code, 0, "unverifiable never exits 2, and never exits 1")

    def test_opaque_next_config_does_not_report_gate_enabled(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_OPAQUE)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotEqual(
            result["verdict"], "pass",
            "a config that defeated the parser must never produce a clean verdict",
        )

    def test_opaque_jest_config_downgrades_threshold_to_unverifiable(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_OPAQUE)
        exit_code, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("coverage_threshold_absent", unverifiable_codes(result))
        self.assertNotIn("coverage_threshold_absent", codes(result))
        self.assertEqual(exit_code, 0)

    def test_jest_config_with_collection_anchor_may_conclude_threshold_absent(self) -> None:
        """The one place a non-match is informative: finding
        collectCoverageFrom proves the file was read and understood."""
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("coverage_threshold_absent", codes(result))
        self.assertNotIn("coverage_threshold_absent", unverifiable_codes(result))

    def test_jsonc_tsconfig_is_parsed_not_downgraded(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("tsconfig.json", TSCONFIG_JSONC)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("tsconfig.json", result["inspected"]["unparsed"])
        self.assertIn("tests_excluded_from_typecheck", codes(result))

    def test_unparseable_package_json_is_could_not_parse(self) -> None:
        self.fx.write("package.json", "{ this is not json")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("could_not_parse", codes(result))
        self.assertIn("package.json", result["inspected"]["unparsed"])
        self.assertEqual(result["verdict"], "unverifiable")

    def test_unparseable_tsconfig_downgrades_its_finding(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("tsconfig.json", "{{{ not recoverable by comment stripping")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("tsconfig.json", result["inspected"]["unparsed"])
        self.assertIn("tests_excluded_from_typecheck", unverifiable_codes(result))


class InformationalFindingTests(unittest.TestCase):
    """AC-2.4 — findings that report without changing the exit code. AC-2.5
    pins duplicate_lockfile and coverage_scope_gap against the real checkout."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_duplicate_lockfile_is_informational_and_exits_zero(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "packageManager": "pnpm@10.33.0",
        }))
        self.fx.write("bun.lock", "{}\n")
        self.fx.write("pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        exit_code, result = qca.check(self.fx.root, baseline=None)

        dup = finding(result, "duplicate_lockfile")
        assert dup is not None
        self.assertEqual(dup["severity"], "informational")
        self.assertEqual(exit_code, 0)
        self.assertIn("pnpm", dup["detail"])

    def test_single_lockfile_is_clean(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("duplicate_lockfile", codes(result))

    def test_lint_script_excluding_tests_is_informational(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "scripts": {
                "lint": "next lint --ignore-pattern '**/__tests__/**' "
                        "--ignore-pattern 'tests/**'",
            },
        }))
        exit_code, result = qca.check(self.fx.root, baseline=None)
        excluded = finding(result, "tests_excluded_from_typecheck")
        assert excluded is not None
        self.assertEqual(excluded["severity"], "informational")
        self.assertEqual(excluded["file"], "package.json")
        self.assertEqual(exit_code, 0)

    def test_tsconfig_excluding_tests_is_informational(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("tsconfig.json", TSCONFIG_JSONC)
        exit_code, result = qca.check(self.fx.root, baseline=None)
        excluded = finding(result, "tests_excluded_from_typecheck")
        assert excluded is not None
        self.assertEqual(excluded["severity"], "informational")
        self.assertEqual(exit_code, 0)

    def test_coverage_scope_gap_names_the_uncollected_source_dir(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("lib/util.ts", "export const a = 1\n")
        self.fx.write("app/api/thing/route.ts", "export async function GET() {}\n")
        _, result = qca.check(self.fx.root, baseline=None)

        gap = finding(result, "coverage_scope_gap")
        assert gap is not None
        self.assertEqual(gap["severity"], "informational")
        self.assertEqual(gap["file"], "app")

    def test_nested_package_is_not_a_scope_gap_of_the_root(self) -> None:
        """A directory carrying its own package.json is a separate package,
        not root source excluded from collection. Measured against a real
        checkout this was the checker's only false positive."""
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("lib/util.ts", "export const a = 1\n")
        self.fx.write("vendored/package.json", json.dumps({"name": "vendored"}))
        self.fx.write("vendored/src/index.ts", "export const b = 2\n")
        _, result = qca.check(self.fx.root, baseline=None)
        gaps = [f["file"] for f in result["findings"] if f["code"] == "coverage_scope_gap"]
        self.assertNotIn("vendored", gaps)

    def test_source_inside_a_nested_package_is_not_counted(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("features/thing.ts", "export const a = 1\n")
        self.fx.write("features/embedded/package.json", json.dumps({"name": "embedded"}))
        for n in range(5):
            self.fx.write(f"features/embedded/src/f{n}.ts", "export const x = 1\n")
        _, result = qca.check(self.fx.root, baseline=None)
        gap = finding(result, "coverage_scope_gap")
        assert gap is not None
        self.assertEqual(gap["file"], "features")
        self.assertEqual(gap["measured"], "1 uncollected source files")

    def test_directory_with_no_source_files_is_not_a_scope_gap(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("lib/util.ts", "export const a = 1\n")
        self.fx.write("assets/logo.svg", "<svg/>\n")
        self.fx.write("assets/copy.md", "# words\n")
        _, result = qca.check(self.fx.root, baseline=None)
        gaps = [f["file"] for f in result["findings"] if f["code"] == "coverage_scope_gap"]
        self.assertNotIn("assets", gaps)

    def test_lint_script_without_test_exclusions_is_clean(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "scripts": {"lint": "eslint . --ext .ts --ignore-pattern node_modules"},
        }))
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("tests_excluded_from_typecheck", codes(result))

    def test_collected_directory_is_not_a_scope_gap(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("lib/util.ts", "export const a = 1\n")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("coverage_scope_gap", codes(result))

    def test_informational_findings_alone_do_not_fail(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "packageManager": "pnpm@10.33.0",
        }))
        self.fx.write("bun.lock", "{}\n")
        self.fx.write("pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        self.fx.write("tsconfig.json", TSCONFIG_JSONC)
        exit_code, result = qca.check(self.fx.root, baseline=None)
        self.assertEqual(exit_code, 0)
        self.assertNotEqual(result["verdict"], "fail")


class BaselineTests(unittest.TestCase):
    """Baseline suppression, and the deliberate awkwardness of re-baselining."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)

    def test_absent_baseline_reports_every_finding_as_new(self) -> None:
        exit_code, result = qca.check(self.fx.root, baseline=self.fx.root / "nope.md")
        self.assertEqual(exit_code, 1)
        self.assertTrue(all(not f.get("baselined") for f in result["findings"]))

    def test_baselined_finding_is_acknowledged_not_blocking(self) -> None:
        baseline = self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

Preamble prose, no entries here.

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — predates adoption; tracked for Phase 3.
- `next.config.js:11` — 2026-08-14 — predates adoption.
""")
        exit_code, result = qca.check(self.fx.root, baseline=baseline)
        gate_findings = [f for f in result["findings"] if f["code"] == "build_gate_disabled"]
        self.assertEqual(len(gate_findings), 2)
        self.assertTrue(all(f["baselined"] for f in gate_findings))
        self.assertEqual(exit_code, 0)
        self.assertNotEqual(result["verdict"], "fail")

    def test_finding_absent_from_baseline_still_blocks(self) -> None:
        baseline = self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — only this one is acknowledged.
""")
        exit_code, result = qca.check(self.fx.root, baseline=baseline)
        unbaselined = [
            f for f in result["findings"]
            if f["code"] == "build_gate_disabled" and not f.get("baselined")
        ]
        self.assertEqual(len(unbaselined), 1)
        self.assertEqual(unbaselined[0]["line"], 11)
        self.assertEqual(exit_code, 1)

    def test_malformed_baseline_exits_two_naming_the_line(self) -> None:
        baseline = self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — no date here, just prose
""")
        with self.assertRaises(qca.UsageError) as caught:
            qca.check(self.fx.root, baseline=baseline)
        self.assertIn("5", str(caught.exception))

    def test_baseline_naming_an_unregistered_code_exits_two(self) -> None:
        baseline = self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

## invented_finding_code

- `next.config.js:8` — 2026-08-14 — a code that does not exist.
""")
        with self.assertRaises(qca.UsageError):
            qca.check(self.fx.root, baseline=baseline)

    def test_baseline_entry_missing_rationale_is_malformed(self) -> None:
        baseline = self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 —
""")
        with self.assertRaises(qca.UsageError):
            qca.check(self.fx.root, baseline=baseline)

    def test_checker_never_writes_the_baseline(self) -> None:
        baseline = self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — acknowledged.
""")
        before = baseline.read_bytes()
        qca.check(self.fx.root, baseline=baseline)
        self.assertEqual(baseline.read_bytes(), before)


class ShadowPathTests(unittest.TestCase):
    """The four shadow paths from technical-spec.md."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_nil_input_missing_project_raises_usage_error(self) -> None:
        with self.assertRaises(qca.UsageError):
            qca.check(self.fx.root / "does-not-exist", baseline=None)

    def test_project_path_is_a_file_not_a_directory(self) -> None:
        path = self.fx.write("a-file.txt", "x")
        with self.assertRaises(qca.UsageError):
            qca.check(path, baseline=None)

    def test_empty_project_is_unverifiable_never_pass(self) -> None:
        exit_code, result = qca.check(self.fx.root, baseline=None)
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(result["inspected"]["files"], 0)
        self.assertEqual(exit_code, 0)
        self.assertIn("unsupported_stack", unverifiable_codes(result))

    def test_zero_findings_and_zero_inspected_do_not_read_the_same(self) -> None:
        empty_exit, empty_result = qca.check(self.fx.root, baseline=None)

        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_ENABLED)
        clean_exit, clean_result = qca.check(self.fx.root, baseline=None)

        # Neither run produced a blocking finding, and both exit 0. That is
        # exactly the condition under which a vacuous pass hides: the guard is
        # that the two are still distinguishable downstream.
        self.assertEqual(empty_exit, clean_exit)
        self.assertEqual(
            [f for f in empty_result["findings"] if f["severity"] == "blocking"], []
        )
        self.assertEqual(clean_result["findings"], [])
        self.assertNotEqual(
            empty_result["verdict"], clean_result["verdict"],
            "an empty project and a clean project must not produce the same verdict",
        )
        self.assertEqual(clean_result["verdict"], "pass")
        self.assertEqual(empty_result["verdict"], "unverifiable")
        self.assertEqual(empty_result["inspected"]["files"], 0)
        self.assertGreater(clean_result["inspected"]["files"], 0)

    def test_happy_path_reports_what_it_inspected(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_ENABLED)
        self.fx.write("tsconfig.json", TSCONFIG_CLEAN)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertEqual(result["verdict"], "pass")
        self.assertGreater(result["inspected"]["files"], 0)
        self.assertEqual(result["inspected"]["unparsed"], [])
        self.assertIn("method", result["inspected"])

    def test_non_node_project_is_unsupported_stack(self) -> None:
        self.fx.write("Cargo.toml", "[package]\nname = 'fixture'\n")
        self.fx.write("src/main.rs", "fn main() {}\n")
        exit_code, result = qca.check(self.fx.root, baseline=None)
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertIn("unsupported_stack", unverifiable_codes(result))
        self.assertEqual(exit_code, 0)


class MonorepoTests(unittest.TestCase):
    """Interaction edge case: several package.json files."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_root_package_is_inspected_and_recorded(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "root", "workspaces": ["packages/*"]}))
        self.fx.write("packages/web/package.json", json.dumps({"name": "web"}))
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("build_gate_disabled", codes(result))
        self.assertIn("package.json", result["inspected"]["method"])

    def test_nested_package_config_is_not_scanned_from_the_root(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "root"}))
        self.fx.write("packages/web/next.config.js", NEXT_CONFIG_DISABLED)
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("build_gate_disabled", codes(result))


class DeterminismTests(unittest.TestCase):
    """Two runs, byte-identical input, byte-identical stdout — asserted both
    in-process and through the CLI, mirroring test_ac_trace.py."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "packageManager": "pnpm@10.33.0",
            "scripts": {"lint": "next lint --ignore-pattern 'tests/**'"},
        }))
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("tsconfig.json", TSCONFIG_JSONC)
        self.fx.write("bun.lock", "{}\n")
        self.fx.write("pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        self.fx.write("lib/util.ts", "export const a = 1\n")
        self.fx.write("app/api/thing/route.ts", "export async function GET() {}\n")

    def test_two_runs_byte_identical(self) -> None:
        first_code, first = qca.check(self.fx.root, baseline=None)
        second_code, second = qca.check(self.fx.root, baseline=None)
        self.assertEqual(first_code, second_code)
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )

    def test_cli_two_runs_stdout_byte_identical(self) -> None:
        argv = [sys.executable, str(HELPER_PATH), "check", "--project", str(self.fx.root)]
        first = subprocess.run(argv, capture_output=True, text=True)
        second = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.returncode, second.returncode)

    def test_findings_sorted_by_file_line_code(self) -> None:
        _, result = qca.check(self.fx.root, baseline=None)
        keys = [(f["file"] or "", f["line"] or 0, f["code"]) for f in result["findings"]]
        self.assertEqual(keys, sorted(keys))


class CliTests(unittest.TestCase):
    """The three exit codes, through the real CLI surface."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def run_cli(self, *args: str) -> tuple[int, dict]:
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH), *args], capture_output=True, text=True
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {"_raw": proc.stdout, "_err": proc.stderr}
        return proc.returncode, payload

    def test_exit_zero_on_clean_project(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_ENABLED)
        code, payload = self.run_cli("check", "--project", str(self.fx.root))
        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "quality-config-audit-v1")
        self.assertEqual(payload["verdict"], "pass")

    def test_exit_one_on_blocking_finding(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        code, payload = self.run_cli("check", "--project", str(self.fx.root))
        self.assertEqual(code, 1)
        self.assertEqual(payload["verdict"], "fail")

    def test_exit_two_on_missing_project(self) -> None:
        code, payload = self.run_cli(
            "check", "--project", str(self.fx.root / "absent")
        )
        self.assertEqual(code, 2)
        self.assertIn("error", payload)

    def test_exit_two_on_malformed_baseline(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        bad = self.fx.write("bad-baseline.md", "## build_gate_disabled\n\n- garbage\n")
        code, payload = self.run_cli(
            "check", "--project", str(self.fx.root), "--baseline", str(bad)
        )
        self.assertEqual(code, 2)
        self.assertIn("error", payload)

    def test_exit_zero_on_unverifiable(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_OPAQUE)
        code, payload = self.run_cli("check", "--project", str(self.fx.root))
        self.assertEqual(code, 0, "unverifiable is not exit 2 and not exit 1")
        self.assertEqual(payload["verdict"], "unverifiable")

    def test_missing_subcommand_exits_nonzero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH)], capture_output=True, text=True
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_default_baseline_is_discovered_under_project(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        self.fx.write(".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — acknowledged.
- `next.config.js:11` — 2026-08-14 — acknowledged.
""")
        code, payload = self.run_cli("check", "--project", str(self.fx.root))
        self.assertEqual(code, 0)
        self.assertTrue(all(f["baselined"] for f in payload["findings"]))


class JsoncStrippingTests(unittest.TestCase):
    """`strip_jsonc` directly. The character scan exists because a regex over
    the whole text would strip a `//` living inside a string literal and
    corrupt the file it was meant to rescue — so the string-literal cases are
    the ones that matter."""

    def test_line_comment_removed(self) -> None:
        self.assertEqual(json.loads(qca.strip_jsonc('{"a": 1 // note\n}')), {"a": 1})

    def test_block_comment_removed(self) -> None:
        text = '{\n  /* multi\n     line */\n  "a": 1\n}'
        self.assertEqual(json.loads(qca.strip_jsonc(text)), {"a": 1})

    def test_unterminated_block_comment_does_not_hang(self) -> None:
        self.assertIsInstance(qca.strip_jsonc('{"a": 1 /* never closed'), str)

    def test_double_slash_inside_a_string_is_preserved(self) -> None:
        text = '{"url": "https://example.com/x"}'
        self.assertEqual(
            json.loads(qca.strip_jsonc(text)), {"url": "https://example.com/x"}
        )

    def test_block_comment_opener_inside_a_string_is_preserved(self) -> None:
        text = '{"glob": "src/*/**"}'
        self.assertEqual(json.loads(qca.strip_jsonc(text)), {"glob": "src/*/**"})

    def test_escaped_quote_inside_a_string_does_not_end_it(self) -> None:
        text = '{"q": "say \\"hi\\" // not a comment"}'
        self.assertEqual(
            json.loads(qca.strip_jsonc(text)), {"q": 'say "hi" // not a comment'}
        )

    def test_trailing_commas_removed(self) -> None:
        self.assertEqual(
            json.loads(qca.strip_jsonc('{"a": [1, 2,], "b": 3,}')), {"a": [1, 2], "b": 3}
        )

    def test_threshold_with_no_numeric_leaf_is_not_a_zero_bar(self) -> None:
        """`coverageThreshold` referencing a computed value has no numeric leaf
        to read. Absent evidence of a zero bar is not evidence of one."""
        self.assertFalse(qca.threshold_is_zero_bar("coverageThreshold: BASE_THRESHOLDS"))

    def test_quoted_and_bare_threshold_keys_both_read(self) -> None:
        self.assertTrue(qca.threshold_is_zero_bar('{"lines": 0, "statements": 0}'))
        self.assertTrue(qca.threshold_is_zero_bar("{ lines: 0, statements: 0 }"))
        self.assertFalse(qca.threshold_is_zero_bar('{"lines": 80}'))

    def test_negated_glob_is_not_a_collected_root(self) -> None:
        roots = qca.collect_roots("['lib/**/*.ts', '!**/node_modules/**', '!vendor/x.ts']")
        self.assertIn("lib", roots)
        self.assertNotIn("vendor", roots)


class UnreadableFileTests(unittest.TestCase):
    """Every rescue in the Error & Rescue Map whose trigger is an I/O failure.
    Exercised by pointing the reader at a directory, which raises OSError on
    read without depending on filesystem permissions the CI user may hold."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_unreadable_json_returns_none_and_names_the_method(self) -> None:
        directory = self.fx.root / "adir"
        directory.mkdir()
        parsed, method = qca.read_json_file(directory, jsonc=False)
        self.assertIsNone(parsed)
        self.assertEqual(method, "unreadable")

    def test_unreadable_next_config_downgrades_build_gate(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        (self.fx.root / "next.config.js").mkdir()
        audit = qca.Audit(self.fx.root)
        qca.audit_next_config(audit, self.fx.root / "next.config.js")
        self.assertIn("next.config.js", audit.unparsed)
        self.assertIn(
            "build_gate_disabled", [e["code"] for e in audit.unverifiable]
        )

    def test_unreadable_jest_config_downgrades_threshold(self) -> None:
        (self.fx.root / "jest.config.js").mkdir()
        audit = qca.Audit(self.fx.root)
        qca.audit_jest_config(audit, self.fx.root / "jest.config.js", None)
        self.assertIn("jest.config.js", audit.unparsed)
        self.assertIn(
            "coverage_threshold_absent", [e["code"] for e in audit.unverifiable]
        )

    def test_unreadable_baseline_raises_usage_error(self) -> None:
        directory = self.fx.root / "baseline-dir"
        directory.mkdir()
        with self.assertRaises(qca.UsageError):
            qca.parse_baseline(directory)

    def test_undecodable_jest_config_downgrades_and_skips_scope_audit(self) -> None:
        """The realistic unreadable case end-to-end. A *directory* named
        jest.config.js is rejected by is_file() before any read is attempted,
        so it never reaches the rescue — invalid UTF-8 in a real file does."""
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        (self.fx.root / "jest.config.js").write_bytes(b"module.exports = {\xff\xfe}\n")
        self.fx.write("app/api/route.ts", "export async function GET() {}\n")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("jest.config.js", result["inspected"]["unparsed"])
        self.assertIn("coverage_threshold_absent", unverifiable_codes(result))
        self.assertNotIn("coverage_scope_gap", codes(result))
        self.assertEqual(result["verdict"], "unverifiable")

    def test_undecodable_next_config_downgrades_end_to_end(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        (self.fx.root / "next.config.js").write_bytes(b"module.exports = {\xff\xfe}\n")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertIn("next.config.js", result["inspected"]["unparsed"])
        self.assertIn("build_gate_disabled", unverifiable_codes(result))

    def test_directory_named_like_a_config_is_not_treated_as_one(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        (self.fx.root / "jest.config.js").mkdir()
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("coverage_scope_gap", codes(result))
        self.assertEqual(result["inspected"]["unparsed"], [])


class MalformedConfigShapeTests(unittest.TestCase):
    """Configs that parse but whose shape is not what the reader expects. A
    checker that assumed the shape would raise rather than report."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_package_json_that_is_a_list_is_tolerated(self) -> None:
        self.fx.write("package.json", "[1, 2, 3]")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("coverage_threshold_absent", codes(result))

    def test_tsconfig_that_is_not_an_object_is_tolerated(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("tsconfig.json", "[]")
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("tests_excluded_from_typecheck", codes(result))

    def test_tsconfig_exclude_that_is_not_a_list_is_tolerated(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("tsconfig.json", '{"exclude": "tests/**"}')
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("tests_excluded_from_typecheck", codes(result))

    def test_scripts_that_is_not_an_object_is_tolerated(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "f", "scripts": "nope"}))
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("tests_excluded_from_typecheck", codes(result))

    def test_lint_script_that_is_not_a_string_is_tolerated(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "f", "scripts": {"lint": 7}}))
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("tests_excluded_from_typecheck", codes(result))

    def test_jest_block_that_is_not_an_object_falls_through(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "f", "jest": "./jest.config"}))
        _, result = qca.check(self.fx.root, baseline=None)
        self.assertNotIn("coverage_threshold_absent", codes(result))

    def test_zero_threshold_in_package_json_is_the_same_finding(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "f",
            "jest": {
                "collectCoverageFrom": ["lib/**/*.ts"],
                "coverageThreshold": {"global": {"lines": 0}},
            },
        }))
        exit_code, result = qca.check(self.fx.root, baseline=None)
        threshold = finding(result, "coverage_threshold_absent")
        assert threshold is not None
        self.assertEqual(threshold["file"], "package.json")
        self.assertEqual(exit_code, 1)

    def test_scope_walk_skips_symlinks_and_non_source_dirs(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        self.fx.write("lib/util.ts", "export const a = 1\n")
        self.fx.write("feature/thing.ts", "export const b = 1\n")
        self.fx.write("feature/node_modules/dep/index.ts", "export const c = 1\n")
        self.fx.write("feature/.hidden/x.ts", "export const d = 1\n")
        (self.fx.root / "feature" / "linked.ts").symlink_to(self.fx.root / "lib" / "util.ts")
        _, result = qca.check(self.fx.root, baseline=None)
        gap = finding(result, "coverage_scope_gap")
        assert gap is not None
        self.assertEqual(gap["measured"], "1 uncollected source files")

    def test_scope_walk_tolerates_an_unlistable_directory(self) -> None:
        audit = qca.Audit(self.fx.root)
        self.assertEqual(qca._count_own_source(self.fx.root / "absent"), 0)
        self.assertEqual(audit.findings, [])


class BaselineParsingEdgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_non_code_heading_ends_the_section(self) -> None:
        """A `## Notes` heading closes the preceding code section, so bullets
        under it are prose and must not be read as malformed entries."""
        baseline = self.fx.write("b.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — acknowledged.

## Notes

- this is prose, not an entry, and must not raise
""")
        entries = qca.parse_baseline(baseline)
        self.assertEqual(entries, {("build_gate_disabled", "next.config.js:8")})

    def test_bullets_before_the_first_section_are_preamble(self) -> None:
        baseline = self.fx.write("b.md", """# Quality Baseline

- a preamble bullet that is not an entry

## duplicate_lockfile

- `bun.lock` — 2026-08-14 — stray lockfile.
""")
        entries = qca.parse_baseline(baseline)
        self.assertEqual(entries, {("duplicate_lockfile", "bun.lock")})

    def test_file_level_locator_matches_a_finding_with_no_line(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("jest.config.js", JEST_CONFIG_NO_THRESHOLD)
        baseline = self.fx.write("b.md", """## coverage_threshold_absent

- `jest.config.js` — 2026-08-14 — acknowledged.
""")
        exit_code, result = qca.check(self.fx.root, baseline=baseline)
        threshold = finding(result, "coverage_threshold_absent")
        assert threshold is not None
        self.assertTrue(threshold["baselined"])
        self.assertEqual(exit_code, 0)


class InProcessCliTests(unittest.TestCase):
    """`main()` in-process, so the argparse wiring and the exit-2 handler are
    measured rather than only observed through a subprocess."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_main_returns_zero_on_clean_project(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_ENABLED)
        self.assertEqual(qca.main(["check", "--project", str(self.fx.root)]), 0)

    def test_main_returns_one_on_blocking_finding(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        self.assertEqual(qca.main(["check", "--project", str(self.fx.root)]), 1)

    def test_main_returns_two_on_usage_error(self) -> None:
        self.assertEqual(
            qca.main(["check", "--project", str(self.fx.root / "absent")]), 2
        )

    def test_main_discovers_the_default_baseline(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.fx.write("next.config.js", NEXT_CONFIG_DISABLED)
        self.fx.write(".writ/quality-baseline.md", """## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — acknowledged.
- `next.config.js:11` — 2026-08-14 — acknowledged.
""")
        self.assertEqual(qca.main(["check", "--project", str(self.fx.root)]), 0)

    def test_main_without_a_baseline_present_is_fine(self) -> None:
        self.fx.write("package.json", PACKAGE_JSON_MINIMAL)
        self.assertEqual(qca.main(["check", "--project", str(self.fx.root)]), 0)


if __name__ == "__main__":
    unittest.main()
