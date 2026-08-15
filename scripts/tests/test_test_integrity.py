#!/usr/bin/env python3
"""Unit tests for scripts/test-integrity.py (Story 3 of
`2026-08-14-script-backed-quality-gates`).

Written before the extractor, per task 3.1. The two false-positive fixtures
— the multi-line `import {` block and the dynamic `await import()` — are the
highest-value tests in this story and are pinned here first.

The reason they are pinned is measured, not argued. Three passes over the
same 147 yuss unit-test files, asking one question:

  hand-audit                      -> 6 files   (over-counted by 50%)
  naive single-line import regex  -> 22 files  (82% false-positive rate)
  whole-file specifier extraction -> 4 files   (ground truth)

A false positive on this check costs more than a false negative: a check
that cries about good tests gets muted, and takes the four real findings
with it.

Run: python3 scripts/tests/test_test_integrity.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HELPER_PATH = Path(__file__).resolve().parents[1] / "test-integrity.py"

_spec = importlib.util.spec_from_file_location("test_integrity", HELPER_PATH)
assert _spec and _spec.loader
ti = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ti)


def codes(result: dict) -> list[str]:
    return [f["code"] for f in result["findings"]]


def flagged_files(result: dict) -> set[str]:
    return {
        f["file"] for f in result["findings"] if f["code"] == "test_imports_no_source"
    }


def unverifiable_codes(result: dict) -> list[str]:
    return [entry["code"] for entry in result["unverifiable"]]


class ProjectFixture:
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


# --- The pinned false-positive fixtures, verbatim in shape from yuss --------

# lib/__tests__/quick-split-utils.test.ts:1 — a multi-line import block. A
# line-oriented regex sees line 1 as `import {` with no `from`, and concludes
# the file imports nothing.
MULTILINE_IMPORT_TEST = """import {
  QUICK_SPLIT_TYPES,
  isQuickSplitType,
  calculateSplitShares,
  type QuickSplitType,
} from '../quick-split-utils'

describe('quick-split-utils', () => {
  it('works', () => {
    expect(isQuickSplitType(QUICK_SPLIT_TYPES[0])).toBe(true)
  })
})
"""

# components/__tests__/Toast.test.tsx:262 — a dynamic import inside a test
# body. No `import ... from` line exists anywhere in the file.
DYNAMIC_IMPORT_TEST = """describe('Toaster Integration', () => {
  it('exports all required toast components', async () => {
    const toast = await import('@/components/ui/toast')
    expect(toast.Toast).toBeDefined()
  })
})
"""

# app/api/user/password/__tests__/password-change.test.ts — the real finding.
# 351 lines whose only import is bcryptjs, and which defines its own copy of
# the function it claims to test, annotated "matches implementation".
NO_SOURCE_TEST = """/**
 * Password Change API Tests
 */

import bcrypt from 'bcryptjs'

jest.mock('bcryptjs', () => ({
  hash: jest.fn().mockResolvedValue('$2a$10$mockedHashedPassword'),
  compare: jest.fn(),
}))

/**
 * Password strength validation function (matches implementation)
 */
function validatePasswordStrength(password: string): string[] {
  const errors: string[] = []
  if (!password) {
    errors.push('New password is required')
  }
  return errors
}

describe('validatePasswordStrength', () => {
  it('rejects an empty password', () => {
    expect(validatePasswordStrength('')).toHaveLength(1)
  })
})
"""


class SpecifierExtractionTests(unittest.TestCase):
    """The extractor, tested directly on file text. This is the whole story."""

    def test_multiline_import_block_is_extracted(self) -> None:
        found = ti.extract_specifiers(MULTILINE_IMPORT_TEST)
        self.assertIn("../quick-split-utils", found)

    def test_dynamic_import_is_extracted(self) -> None:
        found = ti.extract_specifiers(DYNAMIC_IMPORT_TEST)
        self.assertIn("@/components/ui/toast", found)

    def test_single_line_import_is_extracted(self) -> None:
        found = ti.extract_specifiers("import { a } from '@/lib/thing'\n")
        self.assertIn("@/lib/thing", found)

    def test_default_and_named_imports(self) -> None:
        text = "import React from 'react'\nimport { b } from './b'\n"
        found = ti.extract_specifiers(text)
        self.assertIn("react", found)
        self.assertIn("./b", found)

    def test_side_effect_import_is_extracted(self) -> None:
        found = ti.extract_specifiers("import '@/styles/globals.css'\n")
        self.assertIn("@/styles/globals.css", found)

    def test_require_is_extracted(self) -> None:
        found = ti.extract_specifiers("const x = require('../lib/x')\n")
        self.assertIn("../lib/x", found)

    def test_export_from_is_extracted(self) -> None:
        found = ti.extract_specifiers("export { a } from './a'\n")
        self.assertIn("./a", found)

    def test_double_and_single_quotes_both_work(self) -> None:
        found = ti.extract_specifiers('import a from "@/lib/a"\n')
        self.assertIn("@/lib/a", found)

    def test_require_actual_is_not_mistaken_for_require(self) -> None:
        """`jest.requireActual(` must not be read as `require(` — the token
        boundary matters or every mock factory becomes a source import."""
        found = ti.extract_specifiers("const real = jest.requireActual('@/lib/x')\n")
        self.assertNotIn("@/lib/x", found)

    def test_jest_mock_is_not_a_source_import(self) -> None:
        """Mocking a module is the opposite of testing it."""
        found = ti.extract_specifiers("jest.mock('@/lib/db')\n")
        self.assertNotIn("@/lib/db", found)

    def test_specifier_inside_a_line_comment_is_ignored(self) -> None:
        found = ti.extract_specifiers("// import { a } from '@/lib/old'\nconst x = 1\n")
        self.assertNotIn("@/lib/old", found)

    def test_specifier_inside_a_block_comment_is_ignored(self) -> None:
        text = "/*\n * import { a } from '@/lib/old'\n */\nconst x = 1\n"
        found = ti.extract_specifiers(text)
        self.assertNotIn("@/lib/old", found)

    def test_empty_file_yields_no_specifiers(self) -> None:
        self.assertEqual(ti.extract_specifiers(""), [])


class AuthenticityTests(unittest.TestCase):
    """AC-3.2 and AC-3.3 — the two hazards must not flag, the real finding must.

    The three fixtures are the shapes measured on the real checkout, so this
    class also stands behind AC-3.5's count of exactly 4 flagged files."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.fx.write("lib/quick-split-utils.ts", "export const QUICK_SPLIT_TYPES = []\n")
        self.fx.write("components/ui/toast.tsx", "export const Toast = () => null\n")

    def test_multiline_import_file_is_not_flagged(self) -> None:
        self.fx.write("lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_dynamic_import_file_is_not_flagged(self) -> None:
        self.fx.write("components/__tests__/Toast.test.tsx", DYNAMIC_IMPORT_TEST)
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_file_importing_no_source_is_flagged_blocking(self) -> None:
        self.fx.write("app/api/user/password/__tests__/password-change.test.ts",
                      NO_SOURCE_TEST)
        exit_code, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(
            flagged_files(result),
            {"app/api/user/password/__tests__/password-change.test.ts"},
        )
        finding = result["findings"][0]
        self.assertEqual(finding["code"], "test_imports_no_source")
        self.assertEqual(finding["severity"], "blocking")
        self.assertEqual(exit_code, 1)
        self.assertEqual(result["verdict"], "fail")

    def test_the_three_fixtures_together_flag_exactly_one(self) -> None:
        """The measurement in miniature: a naive line regex flags two of these
        three, the truth is one."""
        self.fx.write("lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        self.fx.write("components/__tests__/Toast.test.tsx", DYNAMIC_IMPORT_TEST)
        self.fx.write("app/api/user/password/__tests__/password-change.test.ts",
                      NO_SOURCE_TEST)
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(len(flagged_files(result)), 1)
        self.assertEqual(result["inspected"]["files"], 3)

    def test_importing_only_external_packages_is_flagged(self) -> None:
        self.fx.write("lib/__tests__/pure.test.ts",
                      "import React from 'react'\nimport { z } from 'zod'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), {"lib/__tests__/pure.test.ts"})

    def test_scoped_package_is_not_mistaken_for_an_alias(self) -> None:
        """`@testing-library/react` is an external package; `@/lib/x` is a
        project alias. Both start with `@`."""
        self.fx.write("lib/__tests__/scoped.test.ts",
                      "import { render } from '@testing-library/react'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), {"lib/__tests__/scoped.test.ts"})

    def test_importing_a_sibling_test_helper_is_not_source(self) -> None:
        """A relative import of a test helper is not production source."""
        self.fx.write("lib/__tests__/helpers.ts", "export const mk = () => 1\n")
        self.fx.write("lib/__tests__/helper-only.test.ts",
                      "import { mk } from './helpers'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertIn("lib/__tests__/helper-only.test.ts", flagged_files(result))

    def test_importing_a_mock_is_not_source(self) -> None:
        self.fx.write("__mocks__/db.ts", "export const db = {}\n")
        self.fx.write("lib/__tests__/mock-only.test.ts",
                      "import { db } from '../../__mocks__/db'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertIn("lib/__tests__/mock-only.test.ts", flagged_files(result))

    def test_alias_import_resolves_to_project_source(self) -> None:
        self.fx.write("lib/__tests__/aliased.test.ts",
                      "import { Toast } from '@/components/ui/toast'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_index_resolution(self) -> None:
        self.fx.write("lib/widgets/index.ts", "export const w = 1\n")
        self.fx.write("lib/__tests__/index-import.test.ts",
                      "import { w } from '../widgets'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_unresolvable_project_shaped_specifier_is_given_the_benefit(self) -> None:
        """Where resolution is not cheaply possible, prefer flagging nothing
        over flagging wrongly — a false positive costs more here."""
        self.fx.write("lib/__tests__/unresolved.test.ts",
                      "import { x } from '@/generated/api-types'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_explicit_test_list_is_honored(self) -> None:
        self.fx.write("lib/__tests__/a.test.ts", NO_SOURCE_TEST)
        self.fx.write("lib/__tests__/b.test.ts", NO_SOURCE_TEST)
        _, result = ti.authenticity(
            self.fx.root, tests=[self.fx.root / "lib/__tests__/a.test.ts"]
        )
        self.assertEqual(result["inspected"]["files"], 1)
        self.assertEqual(flagged_files(result), {"lib/__tests__/a.test.ts"})

    def test_node_modules_is_never_scanned(self) -> None:
        self.fx.write("node_modules/pkg/__tests__/vendor.test.js", NO_SOURCE_TEST)
        self.fx.write("lib/__tests__/ours.test.ts", MULTILINE_IMPORT_TEST)
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["inspected"]["files"], 1)


class TestScopeTests(unittest.TestCase):
    """Which files are a unit test at all. An end-to-end spec drives the
    running app through a browser and imports no production module by design;
    flagging it is a false positive by construction, and false positives are
    what get this check muted."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.fx.write("lib/thing.ts", "export const a = 1\n")
        self.fx.write("lib/__tests__/thing.test.ts", "import { a } from '../thing'\n")

    def test_jest_test_path_ignore_patterns_are_honored(self) -> None:
        self.fx.write("jest.config.js", """module.exports = {
  testPathIgnorePatterns: [
    '<rootDir>/.next/',
    '<rootDir>/node_modules/',
    '<rootDir>/tests/e2e/',
    '<rootDir>/tests/integration/',
  ],
}
""")
        self.fx.write("tests/e2e/smoke.spec.ts", "const x = 1\n")
        self.fx.write("tests/integration/db.integration.test.ts", "const y = 1\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["inspected"]["files"], 1)
        self.assertEqual(flagged_files(result), set())

    def test_apostrophe_in_a_config_comment_does_not_corrupt_the_patterns(self) -> None:
        """Regression: a prose comment inside the array carries an apostrophe,
        which reads as a string delimiter and silently turns every later
        pattern into garbage that matches nothing. This is the real shape from
        the checkout this check was measured against."""
        self.fx.write("jest.config.js", """module.exports = {
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    // Exclude worktree subdirectories — each worktree has its own copy of
    // every test file (~4× duplicates + integration tests that can't
    // connect to a DB locally).
    '<rootDir>/tests/e2e/',
    '<rootDir>/tests/integration/'
  ],
}
""")
        patterns = ti.load_test_ignore_patterns(self.fx.root)
        self.assertIn("tests/integration/", patterns)
        self.assertIn("tests/e2e/", patterns)
        self.assertTrue(
            all("connect to a DB" not in p for p in patterns),
            f"comment text leaked into the patterns: {patterns}",
        )

    def test_integration_tree_is_excluded_when_the_project_says_so(self) -> None:
        self.fx.write("jest.config.js", """module.exports = {
  testPathIgnorePatterns: ['<rootDir>/tests/integration/'],
}
""")
        self.fx.write("tests/integration/db.integration.test.ts", "const y = 1\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["inspected"]["files"], 1)
        self.assertEqual(flagged_files(result), set())

    def test_unreadable_ignore_array_yields_no_patterns_not_garbage(self) -> None:
        self.fx.write("jest.config.js", "module.exports = require('./jest/base')\n")
        self.assertEqual(ti.load_test_ignore_patterns(self.fx.root), [])

    def test_undecodable_jest_config_yields_no_patterns(self) -> None:
        (self.fx.root / "jest.config.js").write_bytes(b"module.exports = {\xff\xfe}\n")
        self.assertEqual(ti.load_test_ignore_patterns(self.fx.root), [])

    def test_malformed_package_json_does_not_break_pattern_loading(self) -> None:
        self.fx.write("package.json", "{ not json")
        self.assertEqual(ti.load_test_ignore_patterns(self.fx.root), [])

    def test_invalid_regex_pattern_falls_back_to_substring(self) -> None:
        self.assertTrue(ti.is_ignored_by_project("tests/e2e/a.spec.ts", ["tests/e2e/["]))
        self.assertFalse(ti.is_ignored_by_project("lib/a.test.ts", ["tests/e2e/["]))

    def test_ignore_patterns_from_package_json_are_honored(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "jest": {"testPathIgnorePatterns": ["<rootDir>/tests/e2e/"]},
        }))
        self.fx.write("tests/e2e/smoke.spec.ts", "const x = 1\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["inspected"]["files"], 1)

    def test_playwright_spec_is_out_of_scope_without_any_config(self) -> None:
        """The stack-general backstop: no jest config exists here, so the
        driver import is the only available signal."""
        self.fx.write("tests/e2e/smoke.spec.ts",
                      "import { test, expect } from '@playwright/test'\n"
                      "import { AuthHelpers } from './fixtures/auth-helpers'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())
        self.assertEqual(result["inspected"]["files"], 1)

    def test_cypress_and_puppeteer_specs_are_out_of_scope(self) -> None:
        self.fx.write("e2e-cy/login.spec.ts", "import 'cypress'\n")
        self.fx.write("e2e-pp/render.spec.ts", "import puppeteer from 'puppeteer'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_an_e2e_driver_import_does_not_excuse_a_unit_test(self) -> None:
        """Scope is decided by the driver import, so a unit test that happens
        to sit in a normal location and imports no driver is still judged."""
        self.fx.write("lib/__tests__/fake.test.ts", NO_SOURCE_TEST)
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), {"lib/__tests__/fake.test.ts"})

    def test_out_of_scope_files_are_not_counted_as_inspected(self) -> None:
        self.fx.write("tests/e2e/a.spec.ts", "import { test } from '@playwright/test'\n")
        self.fx.write("tests/e2e/b.spec.ts", "import { test } from '@playwright/test'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["inspected"]["files"], 1)
        self.assertEqual(result["inspected"]["out_of_scope"], 2)

    def test_explicit_tests_flag_still_honors_scope(self) -> None:
        spec = self.fx.write("tests/e2e/a.spec.ts",
                             "import { test } from '@playwright/test'\n")
        _, result = ti.authenticity(self.fx.root, tests=[spec])
        self.assertEqual(flagged_files(result), set())


class AuthenticityShadowPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_zero_tests_examined_is_unverifiable_never_pass(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        exit_code, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(result["inspected"]["files"], 0)
        self.assertEqual(exit_code, 0)
        self.assertIn("nothing_inspected", [e["reason"] for e in result["unverifiable"]])

    def test_missing_project_raises_usage_error(self) -> None:
        with self.assertRaises(ti.UsageError):
            ti.authenticity(self.fx.root / "absent", tests=None)

    def test_undecodable_test_file_is_unparsed_not_flagged(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.fx.write("lib/thing.ts", "export const a = 1\n")
        self.fx.write("lib/__tests__/good.test.ts", "import { a } from '../thing'\n")
        (self.fx.root / "lib/__tests__/bad.test.ts").write_bytes(b"\xff\xfe import\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertIn("lib/__tests__/bad.test.ts", result["inspected"]["unparsed"])
        self.assertNotIn("lib/__tests__/bad.test.ts", flagged_files(result))
        self.assertIn("could_not_parse", codes(result))

    def test_a_clean_project_passes(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.fx.write("lib/thing.ts", "export const a = 1\n")
        self.fx.write("lib/__tests__/thing.test.ts", "import { a } from '../thing'\n")
        exit_code, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["findings"], [])
        self.assertEqual(exit_code, 0)


# --- Coverage report fixtures ------------------------------------------------

JEST_SUMMARY = json.dumps({
    "total": {
        "lines": {"total": 1000, "covered": 572, "skipped": 0, "pct": 57.2},
        "statements": {"total": 1000, "covered": 572, "skipped": 0, "pct": 57.2},
        "functions": {"total": 100, "covered": 50, "skipped": 0, "pct": 50},
        "branches": {"total": 200, "covered": 100, "skipped": 0, "pct": 50},
    },
    "/proj/lib/good.ts": {
        "lines": {"total": 10, "covered": 10, "skipped": 0, "pct": 100},
        "statements": {"total": 10, "covered": 10, "skipped": 0, "pct": 100},
        "functions": {"total": 2, "covered": 2, "skipped": 0, "pct": 100},
        "branches": {"total": 2, "covered": 2, "skipped": 0, "pct": 100},
    },
    "/proj/lib/bad.ts": {
        "lines": {"total": 100, "covered": 40, "skipped": 0, "pct": 40},
        "statements": {"total": 100, "covered": 40, "skipped": 0, "pct": 40},
        "functions": {"total": 10, "covered": 4, "skipped": 0, "pct": 40},
        "branches": {"total": 10, "covered": 4, "skipped": 0, "pct": 40},
    },
})

LCOV = """TN:
SF:lib/good.ts
DA:1,1
DA:2,1
DA:3,1
LF:3
LH:3
end_of_record
TN:
SF:lib/bad.ts
DA:1,1
DA:2,0
DA:3,0
DA:4,0
DA:5,0
LF:5
LH:1
end_of_record
"""

COVERAGE_PY_XML = """<?xml version="1.0" ?>
<coverage line-rate="0.572" version="7.0">
  <packages>
    <package name="lib">
      <classes>
        <class filename="lib/good.py" line-rate="1.0">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
        <class filename="lib/bad.py" line-rate="0.25">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
            <line number="3" hits="0"/>
            <line number="4" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


class CoverageTests(unittest.TestCase):
    """AC-3.1 — the verdict comes from the tool's own output, never from a
    field an agent typed. AC-3.5 pins the re-derived 57.2% against the real
    checkout."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))

    def test_jest_summary_below_threshold_is_blocking(self) -> None:
        report = self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/bad.ts"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(len(below), 1)
        self.assertEqual(below[0]["severity"], "blocking")
        self.assertEqual(below[0]["file"], "lib/bad.ts")
        self.assertEqual(exit_code, 1)

    def test_jest_summary_above_threshold_is_clean(self) -> None:
        report = self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/good.ts"], threshold=80.0,
            prior=None,
        )
        self.assertEqual(result["findings"], [])
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["verdict"], "pass")

    def test_overall_measured_percentage_is_reported(self) -> None:
        """The number Gate 4 prints against the agent's claim."""
        report = self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertAlmostEqual(result["measured"]["statements_pct"], 57.2, places=1)

    def test_statements_is_preferred_over_lines_for_the_aggregate(self) -> None:
        """A real suite measured 57.22% statements and 58.2% lines. The field
        is named statements_pct, so quoting the lines number against a claim
        would be its own small dishonesty."""
        report = self.fx.write("coverage/coverage-summary.json", json.dumps({
            "total": {
                "statements": {"covered": 5037, "total": 8802, "pct": 57.22},
                "lines": {"covered": 4656, "total": 8000, "pct": 58.2},
            },
            "/proj/lib/a.ts": {"lines": {"covered": 1, "total": 1, "pct": 100}},
        }))
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertAlmostEqual(result["measured"]["statements_pct"], 57.2256, places=3)
        self.assertEqual(result["measured"]["total_lines"], 8802)

    def test_judging_nothing_is_unverifiable_not_pass(self) -> None:
        """Re-deriving the aggregate is not the same as judging a file.
        Reporting `pass` while measuring 57% against an 80% bar is the exact
        clean-report failure mode this spec exists to end."""
        report = self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(exit_code, 0)
        self.assertIn(
            "nothing_inspected", [e["reason"] for e in result["unverifiable"]]
        )
        self.assertAlmostEqual(result["measured"]["statements_pct"], 57.2, places=1)

    def test_judging_a_file_that_passes_is_a_real_pass(self) -> None:
        report = self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/good.ts"], threshold=80.0,
            prior=None,
        )
        self.assertEqual(result["verdict"], "pass")

    def test_verdict_is_independent_of_any_claimed_value(self) -> None:
        """AC-3.1's core: there is no input by which a caller can assert the
        answer. The checker's signature simply has no such parameter."""
        import inspect
        params = set(inspect.signature(ti.coverage).parameters)
        self.assertEqual(
            params & {"claim", "claimed", "coverage_threshold_met", "self_report"},
            set(),
        )

    def test_lcov_is_parsed(self) -> None:
        report = self.fx.write("coverage/lcov.info", LCOV)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/bad.ts"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(len(below), 1)
        self.assertEqual(below[0]["measured"], "20.0%")
        self.assertEqual(exit_code, 1)

    def test_coverage_py_xml_is_parsed(self) -> None:
        report = self.fx.write("coverage.xml", COVERAGE_PY_XML)
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/bad.py"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(len(below), 1)
        self.assertEqual(below[0]["measured"], "25.0%")

    def test_report_is_discovered_when_not_supplied(self) -> None:
        self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        _, result = ti.coverage(
            self.fx.root, report=None, new_files=["lib/bad.ts"], threshold=80.0,
            prior=None,
        )
        self.assertIn("coverage_below_threshold", codes(result))

    def test_regression_against_a_prior_report_is_blocking(self) -> None:
        prior = self.fx.write("prior/lcov.info", """TN:
SF:lib/bad.ts
DA:1,1
DA:2,1
DA:3,1
DA:4,1
DA:5,0
LF:5
LH:4
end_of_record
""")
        report = self.fx.write("coverage/lcov.info", LCOV)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=0.0, prior=prior,
        )
        regressions = [f for f in result["findings"] if f["code"] == "coverage_regression"]
        self.assertEqual(len(regressions), 1)
        self.assertEqual(regressions[0]["file"], "lib/bad.ts")
        self.assertEqual(regressions[0]["severity"], "blocking")
        self.assertEqual(exit_code, 1)

    def test_no_regression_when_coverage_holds(self) -> None:
        report = self.fx.write("coverage/lcov.info", LCOV)
        prior = self.fx.write("prior/lcov.info", LCOV)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=0.0, prior=prior,
        )
        self.assertNotIn("coverage_regression", codes(result))
        self.assertEqual(exit_code, 0)


class CoverageUnverifiableTests(unittest.TestCase):
    """AC-3.4 — never a silent pass, never exit 2."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))

    def test_absent_report_is_unverifiable_exit_zero(self) -> None:
        exit_code, result = ti.coverage(
            self.fx.root, report=None, new_files=["lib/x.ts"], threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertIn("coverage_report_absent", codes(result))
        self.assertIn("no_coverage_report", [e["reason"] for e in result["unverifiable"]])
        self.assertEqual(exit_code, 0)

    def test_explicitly_named_absent_report_is_unverifiable(self) -> None:
        exit_code, result = ti.coverage(
            self.fx.root, report=self.fx.root / "nope.json", new_files=None,
            threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(exit_code, 0)

    def test_unknown_format_is_unverifiable_not_a_guess(self) -> None:
        report = self.fx.write("coverage/weird.dat", "some proprietary format\n")
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertIn(
            "unknown_report_format", [e["reason"] for e in result["unverifiable"]]
        )
        self.assertEqual(exit_code, 0)

    def test_truncated_report_is_unverifiable_not_pass_not_fail(self) -> None:
        report = self.fx.write("coverage/coverage-summary.json", '{"total": {"lines"')
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(exit_code, 0)
        self.assertNotIn("coverage_below_threshold", codes(result))

    def test_report_with_no_file_records_is_unverifiable(self) -> None:
        report = self.fx.write("coverage/lcov.info", "TN:\n")
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(result["inspected"]["files"], 0)
        self.assertEqual(exit_code, 0)

    def test_new_file_absent_from_the_report_is_unverifiable_not_a_pass(self) -> None:
        report = self.fx.write("coverage/lcov.info", LCOV)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/never-measured.ts"],
            threshold=80.0, prior=None,
        )
        self.assertEqual(exit_code, 0)
        self.assertNotEqual(result["verdict"], "pass")
        self.assertIn(
            "coverage_below_threshold", [e["code"] for e in result["unverifiable"]]
        )

    def test_missing_project_raises_usage_error(self) -> None:
        with self.assertRaises(ti.UsageError):
            ti.coverage(
                self.fx.root / "absent", report=None, new_files=None,
                threshold=80.0, prior=None,
            )

    def test_unreadable_prior_report_does_not_crash_the_run(self) -> None:
        report = self.fx.write("coverage/lcov.info", LCOV)
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=0.0,
            prior=self.fx.root / "absent-prior.info",
        )
        self.assertEqual(exit_code, 0)
        self.assertNotIn("coverage_regression", codes(result))


class DeterminismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.fx.write("lib/quick-split-utils.ts", "export const Q = []\n")
        self.fx.write("lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        self.fx.write("lib/__tests__/z-bad.test.ts", NO_SOURCE_TEST)
        self.fx.write("lib/__tests__/a-bad.test.ts", NO_SOURCE_TEST)
        self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)

    def test_authenticity_two_runs_byte_identical(self) -> None:
        first_code, first = ti.authenticity(self.fx.root, tests=None)
        second_code, second = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(first_code, second_code)
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )

    def test_findings_sorted_by_file_line_code(self) -> None:
        _, result = ti.authenticity(self.fx.root, tests=None)
        keys = [(f["file"] or "", f["line"] or 0, f["code"]) for f in result["findings"]]
        self.assertEqual(keys, sorted(keys))

    def test_cli_two_runs_stdout_byte_identical(self) -> None:
        argv = [sys.executable, str(HELPER_PATH), "authenticity",
                "--project", str(self.fx.root)]
        first = subprocess.run(argv, capture_output=True, text=True)
        second = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.returncode, second.returncode)

    def test_cli_coverage_two_runs_byte_identical(self) -> None:
        argv = [sys.executable, str(HELPER_PATH), "coverage",
                "--project", str(self.fx.root)]
        first = subprocess.run(argv, capture_output=True, text=True)
        second = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(first.stdout, second.stdout)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))

    def run_cli(self, *args: str) -> tuple[int, dict]:
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH), *args], capture_output=True, text=True
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {"_raw": proc.stdout, "_err": proc.stderr}
        return proc.returncode, payload

    def test_authenticity_schema_and_exit_zero(self) -> None:
        self.fx.write("lib/thing.ts", "export const a = 1\n")
        self.fx.write("lib/__tests__/thing.test.ts", "import { a } from '../thing'\n")
        code, payload = self.run_cli("authenticity", "--project", str(self.fx.root))
        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "test-integrity-v1")
        self.assertEqual(payload["verdict"], "pass")

    def test_authenticity_exit_one(self) -> None:
        self.fx.write("lib/__tests__/bad.test.ts", NO_SOURCE_TEST)
        code, payload = self.run_cli("authenticity", "--project", str(self.fx.root))
        self.assertEqual(code, 1)
        self.assertEqual(payload["verdict"], "fail")

    def test_coverage_exit_one(self) -> None:
        self.fx.write("coverage/coverage-summary.json", JEST_SUMMARY)
        code, payload = self.run_cli(
            "coverage", "--project", str(self.fx.root),
            "--new-files", "lib/bad.ts", "--threshold", "80",
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["verdict"], "fail")

    def test_exit_two_on_missing_project(self) -> None:
        code, payload = self.run_cli(
            "authenticity", "--project", str(self.fx.root / "absent")
        )
        self.assertEqual(code, 2)
        self.assertIn("error", payload)

    def test_coverage_exit_two_on_missing_project(self) -> None:
        code, _ = self.run_cli("coverage", "--project", str(self.fx.root / "absent"))
        self.assertEqual(code, 2)

    def test_unverifiable_exits_zero_through_the_cli(self) -> None:
        code, payload = self.run_cli("coverage", "--project", str(self.fx.root))
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "unverifiable")

    def test_missing_subcommand_exits_nonzero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH)], capture_output=True, text=True
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_main_in_process_returns_expected_codes(self) -> None:
        self.fx.write("lib/__tests__/bad.test.ts", NO_SOURCE_TEST)
        self.assertEqual(
            ti.main(["authenticity", "--project", str(self.fx.root)]), 1
        )
        self.assertEqual(
            ti.main(["authenticity", "--project", str(self.fx.root / "absent")]), 2
        )
        self.assertEqual(ti.main(["coverage", "--project", str(self.fx.root)]), 0)

    def test_tests_flag_narrows_the_examined_set(self) -> None:
        self.fx.write("lib/__tests__/a.test.ts", NO_SOURCE_TEST)
        self.fx.write("lib/__tests__/b.test.ts", NO_SOURCE_TEST)
        code, payload = self.run_cli(
            "authenticity", "--project", str(self.fx.root),
            "--tests", str(self.fx.root / "lib/__tests__/a.test.ts"),
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["inspected"]["files"], 1)


class AliasLoadingTests(unittest.TestCase):
    """`compilerOptions.paths`. A wrong alias costs a *missed* flag, never a
    false one — resolution failure gives the file the benefit of the doubt —
    so every degraded branch here must return the `@/` fallback rather than
    raise."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_no_tsconfig_yields_the_conventional_fallback(self) -> None:
        self.assertEqual(ti.load_aliases(self.fx.root), {"@/": ""})

    def test_paths_are_read(self) -> None:
        self.fx.write("tsconfig.json", json.dumps({
            "compilerOptions": {"paths": {"~/*": ["./src/*"], "@lib/*": ["./lib/*"]}}
        }))
        aliases = ti.load_aliases(self.fx.root)
        self.assertEqual(aliases["~/"], "src/")
        self.assertEqual(aliases["@lib/"], "lib/")

    def test_a_custom_alias_resolves_to_project_source(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.fx.write("tsconfig.json", json.dumps({
            "compilerOptions": {"paths": {"~/*": ["./src/*"]}}
        }))
        self.fx.write("src/widget.ts", "export const w = 1\n")
        self.fx.write("src/__tests__/widget.test.ts", "import { w } from '~/widget'\n")
        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertEqual(flagged_files(result), set())

    def test_jsonc_tsconfig_is_read(self) -> None:
        self.fx.write("tsconfig.json", """{
  // a comment
  "compilerOptions": {
    "paths": { "~/*": ["./src/*"] },
  },
}
""")
        self.assertEqual(ti.load_aliases(self.fx.root)["~/"], "src/")

    def test_malformed_tsconfig_falls_back(self) -> None:
        self.fx.write("tsconfig.json", "{{{ not json")
        self.assertEqual(ti.load_aliases(self.fx.root), {"@/": ""})

    def test_tsconfig_that_is_not_an_object_falls_back(self) -> None:
        self.fx.write("tsconfig.json", "[]")
        self.assertEqual(ti.load_aliases(self.fx.root), {"@/": ""})

    def test_tsconfig_without_paths_falls_back(self) -> None:
        self.fx.write("tsconfig.json", json.dumps({"compilerOptions": {"strict": True}}))
        self.assertEqual(ti.load_aliases(self.fx.root), {"@/": ""})

    def test_undecodable_tsconfig_falls_back(self) -> None:
        (self.fx.root / "tsconfig.json").write_bytes(b"\xff\xfe{}")
        self.assertEqual(ti.load_aliases(self.fx.root), {"@/": ""})

    def test_malformed_path_entries_are_skipped(self) -> None:
        self.fx.write("tsconfig.json", json.dumps({
            "compilerOptions": {"paths": {
                "a/*": "not-a-list", "b/*": [], "c/*": [7], "d/*": ["./d/*"],
            }}
        }))
        aliases = ti.load_aliases(self.fx.root)
        self.assertEqual(aliases["d/"], "d/")
        self.assertNotIn("a/", aliases)

    def test_alias_escaping_the_project_is_not_project_source(self) -> None:
        """An alias may point outside the project entirely. A file that
        resolves out there is somebody else's source, and importing it does
        not vouch for this project's test."""
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        neighbour = ProjectFixture()
        self.addCleanup(neighbour.cleanup)
        neighbour.write("thing.ts", "export const o = 1\n")

        relative_target = f"../{neighbour.root.name}/"
        self.fx.write("tsconfig.json", json.dumps({
            "compilerOptions": {"paths": {"~/*": [relative_target + "*"]}}
        }))
        self.fx.write("lib/__tests__/escape.test.ts", "import { o } from '~/thing'\n")

        resolved, project_shaped = ti.resolve_specifier(
            "~/thing",
            self.fx.root / "lib/__tests__/escape.test.ts",
            self.fx.root,
            ti.load_aliases(self.fx.root),
        )
        self.assertTrue(project_shaped)
        self.assertIsNotNone(resolved, "the fixture must actually resolve outside")

        _, result = ti.authenticity(self.fx.root, tests=None)
        self.assertIn("lib/__tests__/escape.test.ts", flagged_files(result))


class ReportFormatEdgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))

    def test_istanbul_coverage_final_statement_map_is_parsed(self) -> None:
        report = self.fx.write("coverage/coverage-final.json", json.dumps({
            "/proj/lib/bad.ts": {"path": "/proj/lib/bad.ts",
                                 "s": {"0": 1, "1": 0, "2": 0, "3": 0}},
        }))
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/bad.ts"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(len(below), 1)
        self.assertEqual(below[0]["measured"], "25.0%")

    def test_json_report_that_is_a_list_is_unknown_format(self) -> None:
        report = self.fx.write("coverage/x.json", "[1, 2, 3]")
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertIn(
            "unknown_report_format", [e["reason"] for e in result["unverifiable"]]
        )

    def test_json_report_with_no_file_records_is_unknown_format(self) -> None:
        report = self.fx.write("coverage/x.json", json.dumps({"meta": {"tool": "x"}}))
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")

    def test_unreadable_report_is_unverifiable(self) -> None:
        (self.fx.root / "coverage").mkdir()
        (self.fx.root / "coverage" / "lcov.info").write_bytes(b"SF:\xff\xfe\n")
        _, result = ti.coverage(
            self.fx.root, report=self.fx.root / "coverage" / "lcov.info",
            new_files=None, threshold=80.0, prior=None,
        )
        self.assertEqual(result["verdict"], "unverifiable")

    def test_malformed_xml_is_truncated_report(self) -> None:
        report = self.fx.write("coverage.xml", '<?xml version="1.0" ?><coverage>')
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertIn(
            "truncated_report", [e["reason"] for e in result["unverifiable"]]
        )

    def test_xml_with_no_class_records_is_unknown_format(self) -> None:
        report = self.fx.write("coverage.xml", '<?xml version="1.0" ?><coverage/>')
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=80.0, prior=None,
        )
        self.assertIn(
            "unknown_report_format", [e["reason"] for e in result["unverifiable"]]
        )

    def test_non_numeric_hits_are_tolerated(self) -> None:
        report = self.fx.write("coverage.xml", """<?xml version="1.0" ?>
<coverage><packages><package><classes>
<class filename="lib/a.py"><lines>
<line number="1" hits="x"/><line number="2" hits="1"/>
</lines></class>
</classes></package></packages></coverage>
""")
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/a.py"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(below[0]["measured"], "50.0%")

    def test_non_numeric_lcov_hit_counts_are_tolerated(self) -> None:
        report = self.fx.write("coverage/lcov.info", """SF:lib/a.ts
DA:1,x
DA:2,1
LF:2
LH:1
end_of_record
""")
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/a.ts"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(below[0]["measured"], "50.0%")

    def test_unparseable_prior_report_yields_no_regressions(self) -> None:
        report = self.fx.write("coverage/lcov.info", LCOV)
        prior = self.fx.write("prior/weird.dat", "not a coverage report\n")
        exit_code, result = ti.coverage(
            self.fx.root, report=report, new_files=None, threshold=0.0, prior=prior,
        )
        self.assertNotIn("coverage_regression", codes(result))
        self.assertEqual(exit_code, 0)

    def test_absolute_test_path_outside_the_project_is_reported_by_full_path(self) -> None:
        other = ProjectFixture()
        self.addCleanup(other.cleanup)
        stray = other.write("stray.test.ts", NO_SOURCE_TEST)
        _, result = ti.authenticity(self.fx.root, tests=[stray])
        self.assertEqual(flagged_files(result), {str(stray.resolve())})


class DiscoveryTests(unittest.TestCase):
    """What the walk includes and skips. Every skip here is a place a
    false positive would otherwise come from."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({"name": "fixture"}))

    def test_test_shaped_import_target_in_a_tests_dir_is_not_source(self) -> None:
        self.assertTrue(ti.is_test_shaped(Path("tests/helpers/db.ts")))
        self.assertTrue(ti.is_test_shaped(Path("lib/__mocks__/db.ts")))
        self.assertTrue(ti.is_test_shaped(Path("lib/a.test.ts")))
        self.assertTrue(ti.is_test_shaped(Path("lib/test-utils.ts")))
        self.assertFalse(ti.is_test_shaped(Path("lib/db.ts")))

    def test_symlinked_test_file_is_skipped(self) -> None:
        self.fx.write("lib/real.test.ts", NO_SOURCE_TEST)
        (self.fx.root / "lib" / "linked.test.ts").symlink_to(
            self.fx.root / "lib" / "real.test.ts"
        )
        found = {p.name for p in ti.discover_tests(self.fx.root)}
        self.assertIn("real.test.ts", found)
        self.assertNotIn("linked.test.ts", found)

    def test_build_and_hidden_directories_are_skipped(self) -> None:
        self.fx.write("lib/keep.test.ts", NO_SOURCE_TEST)
        self.fx.write("dist/bundled.test.js", NO_SOURCE_TEST)
        self.fx.write(".next/cached.test.js", NO_SOURCE_TEST)
        self.fx.write("coverage/report.test.js", NO_SOURCE_TEST)
        found = {p.name for p in ti.discover_tests(self.fx.root)}
        self.assertEqual(found, {"keep.test.ts"})

    def test_nested_package_owns_its_own_tests(self) -> None:
        self.fx.write("lib/keep.test.ts", NO_SOURCE_TEST)
        self.fx.write("vendored/package.json", json.dumps({"name": "vendored"}))
        self.fx.write("vendored/lib/theirs.test.ts", NO_SOURCE_TEST)
        found = {p.name for p in ti.discover_tests(self.fx.root)}
        self.assertEqual(found, {"keep.test.ts"})

    def test_non_source_suffixes_are_not_tests(self) -> None:
        self.fx.write("lib/__tests__/fixture.json", "{}")
        self.fx.write("lib/__tests__/notes.md", "# notes\n")
        self.fx.write("lib/__tests__/real.test.ts", NO_SOURCE_TEST)
        found = {p.name for p in ti.discover_tests(self.fx.root)}
        self.assertEqual(found, {"real.test.ts"})

    def test_unlistable_directory_does_not_abort_the_walk(self) -> None:
        self.fx.write("lib/keep.test.ts", NO_SOURCE_TEST)
        self.assertEqual(ti.discover_tests(self.fx.root / "absent"), [])

    def test_cobertura_class_without_a_filename_is_skipped(self) -> None:
        report = self.fx.write("coverage.xml", """<?xml version="1.0" ?>
<coverage><packages><package><classes>
<class><lines><line number="1" hits="1"/></lines></class>
<class filename="lib/a.py"><lines>
<line number="1" hits="0"/><line number="2" hits="0"/>
</lines></class>
</classes></package></packages></coverage>
""")
        _, result = ti.coverage(
            self.fx.root, report=report, new_files=["lib/a.py"], threshold=80.0,
            prior=None,
        )
        below = [f for f in result["findings"] if f["code"] == "coverage_below_threshold"]
        self.assertEqual(len(below), 1)
        self.assertEqual(result["inspected"]["files"], 1)


class CommentStrippingTests(unittest.TestCase):
    def test_escaped_quote_inside_a_string_does_not_end_it(self) -> None:
        text = r"""const s = 'it\'s fine // not a comment'
import { a } from '@/lib/a'
"""
        self.assertIn("@/lib/a", ti.extract_specifiers(text))

    def test_template_literal_containing_a_comment_marker(self) -> None:
        text = "const t = `https://example.com`\nimport { a } from '@/lib/a'\n"
        self.assertIn("@/lib/a", ti.extract_specifiers(text))

    def test_unterminated_block_comment_does_not_hang(self) -> None:
        self.assertIsInstance(ti.strip_js_comments("const a = 1 /* never closed"), str)


if __name__ == "__main__":
    unittest.main()
