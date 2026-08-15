#!/usr/bin/env python3
"""Fixture scenarios for the test-integrity checker (Story 3 of
`2026-08-14-script-backed-quality-gates`).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh's check_test_integrity.
Every scenario builds a disposable project in a temp directory and exercises
scripts/test-integrity.py via its CLI, following scripts/eval-ac-trace.py's
exact shape.

CI runs scripts/eval.sh and never scripts/tests/, so these scenarios plus
eval.sh's require_literal/forbid_literal bindings are this checker's entire
CI protection.

The first two scenarios are the load-bearing ones. Measured against 147 real
unit-test files, a naive single-line import regex flagged 22 where the truth
is 4 -- an 82% false-positive rate -- because multi-line `import {` blocks and
dynamic `await import()` calls both escape a per-line match. A false positive
costs more than a false negative here: a check that cries about good tests
gets muted, and takes the real findings with it.

  - multi-line import block           -> NOT flagged
  - dynamic await import()            -> NOT flagged
  - test importing only externals     -> flagged, blocking, exit 1
  - three fixtures together           -> exactly one flagged
  - e2e spec / project ignore pattern -> out of scope, not flagged
  - coverage below/above threshold, lcov, regression
  - absent / unknown / truncated report -> unverifiable, exit 0
  - judging nothing                   -> unverifiable, never pass
  - byte-identical repeat runs
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("test-integrity.py")
passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args], capture_output=True, text=True
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def flagged(payload: dict) -> set[str]:
    return {
        f["file"] for f in payload.get("findings", [])
        if f["code"] == "test_imports_no_source"
    }


def reasons(payload: dict) -> list[str]:
    return [e["reason"] for e in payload.get("unverifiable", [])]


PACKAGE = json.dumps({"name": "fixture"})

MULTILINE_IMPORT_TEST = """import {
  QUICK_SPLIT_TYPES,
  isQuickSplitType,
} from '../quick-split-utils'

describe('quick-split-utils', () => {
  it('works', () => { expect(isQuickSplitType('x')).toBe(false) })
})
"""

DYNAMIC_IMPORT_TEST = """describe('Toaster Integration', () => {
  it('exports all required toast components', async () => {
    const toast = await import('@/components/ui/toast')
    expect(toast.Toast).toBeDefined()
  })
})
"""

NO_SOURCE_TEST = """import bcrypt from 'bcryptjs'

jest.mock('bcryptjs', () => ({ hash: jest.fn() }))

function validatePasswordStrength(password) {
  return password ? [] : ['New password is required']
}

describe('validatePasswordStrength', () => {
  it('rejects empty', () => {
    expect(validatePasswordStrength('')).toHaveLength(1)
  })
})
"""

JEST_SUMMARY = json.dumps({
    "total": {
        "statements": {"covered": 572, "total": 1000, "pct": 57.2},
        "lines": {"covered": 572, "total": 1000, "pct": 57.2},
    },
    "/proj/lib/good.ts": {"lines": {"covered": 10, "total": 10, "pct": 100}},
    "/proj/lib/bad.ts": {"lines": {"covered": 40, "total": 100, "pct": 40}},
})

LCOV = """SF:lib/good.ts
DA:1,1
DA:2,1
DA:3,1
end_of_record
SF:lib/bad.ts
DA:1,1
DA:2,0
DA:3,0
DA:4,0
DA:5,0
end_of_record
"""


def _base_project(root: Path) -> None:
    write(root, "package.json", PACKAGE)
    write(root, "lib/quick-split-utils.ts", "export const QUICK_SPLIT_TYPES = []\n")
    write(root, "components/ui/toast.tsx", "export const Toast = () => null\n")


def scenario_multiline_import_not_flagged() -> None:
    """A line-oriented regex reads line 1 as `import {` with no `from` and
    concludes the file imports nothing. It does."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        code, payload = run("authenticity", "--project", str(root))
        emit("multiline-import-block-not-flagged",
             code == 0 and flagged(payload) == set()
             and payload.get("verdict") == "pass",
             payload)


def scenario_dynamic_import_not_flagged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "components/__tests__/Toast.test.tsx", DYNAMIC_IMPORT_TEST)
        code, payload = run("authenticity", "--project", str(root))
        emit("dynamic-import-not-flagged",
             code == 0 and flagged(payload) == set(), payload)


def scenario_no_source_import_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "app/api/user/password/__tests__/password-change.test.ts",
              NO_SOURCE_TEST)
        code, payload = run("authenticity", "--project", str(root))
        findings = payload.get("findings", [])
        emit("test-importing-no-source-is-blocking",
             code == 1
             and payload.get("verdict") == "fail"
             and len(findings) == 1
             and findings[0]["code"] == "test_imports_no_source"
             and findings[0]["severity"] == "blocking",
             payload)


def scenario_three_fixtures_flag_exactly_one() -> None:
    """The measurement in miniature: a naive line regex flags two of these
    three; the truth is one."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        write(root, "components/__tests__/Toast.test.tsx", DYNAMIC_IMPORT_TEST)
        write(root, "app/__tests__/password-change.test.ts", NO_SOURCE_TEST)
        _code, payload = run("authenticity", "--project", str(root))
        emit("three-fixtures-flag-exactly-one",
             len(flagged(payload)) == 1
             and payload.get("inspected", {}).get("files") == 3,
             payload)


def scenario_e2e_and_ignore_patterns_are_out_of_scope() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        write(root, "tests/e2e/smoke.spec.ts",
              "import { test, expect } from '@playwright/test'\n")
        _code, payload = run("authenticity", "--project", str(root))
        emit("e2e-driver-spec-out-of-scope",
             flagged(payload) == set()
             and payload.get("inspected", {}).get("files") == 1
             and payload.get("inspected", {}).get("out_of_scope") == 1,
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "jest.config.js", """module.exports = {
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    // integration tests that can't connect to a DB locally
    '<rootDir>/tests/integration/',
  ],
}
""")
        write(root, "lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        write(root, "tests/integration/db.integration.test.ts", "const x = 1\n")
        _code, payload = run("authenticity", "--project", str(root))
        emit("project-ignore-patterns-honored-despite-comment-apostrophe",
             flagged(payload) == set()
             and payload.get("inspected", {}).get("files") == 1,
             payload)


def scenario_zero_tests_is_unverifiable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        code, payload = run("authenticity", "--project", str(root))
        emit("zero-tests-unverifiable-never-pass",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and payload.get("inspected", {}).get("files") == 0
             and "nothing_inspected" in reasons(payload),
             payload)


def scenario_coverage_below_threshold() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        write(root, "coverage/coverage-summary.json", JEST_SUMMARY)
        code, payload = run(
            "coverage", "--project", str(root), "--threshold", "80",
            "--new-files", "lib/bad.ts",
        )
        below = [f for f in payload.get("findings", [])
                 if f["code"] == "coverage_below_threshold"]
        emit("coverage-below-threshold-blocking",
             code == 1
             and payload.get("verdict") == "fail"
             and len(below) == 1
             and below[0]["severity"] == "blocking",
             payload)


def scenario_coverage_above_threshold() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        write(root, "coverage/coverage-summary.json", JEST_SUMMARY)
        code, payload = run(
            "coverage", "--project", str(root), "--threshold", "80",
            "--new-files", "lib/good.ts",
        )
        emit("coverage-above-threshold-passes",
             code == 0 and payload.get("verdict") == "pass"
             and payload.get("findings") == [],
             payload)


def scenario_measured_value_is_reported() -> None:
    """The number Gate 4 prints against the agent's self-reported field."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        write(root, "coverage/coverage-summary.json", JEST_SUMMARY)
        _code, payload = run(
            "coverage", "--project", str(root), "--new-files", "lib/good.ts",
        )
        measured = payload.get("measured", {})
        emit("measured-statements-pct-reported",
             abs(measured.get("statements_pct", 0) - 57.2) < 0.05, payload)


def scenario_judging_nothing_is_unverifiable() -> None:
    """Re-deriving the aggregate is not judging a file. Reporting `pass` while
    measuring 57% against an 80% bar is the clean-report failure mode."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        write(root, "coverage/coverage-summary.json", JEST_SUMMARY)
        code, payload = run("coverage", "--project", str(root), "--threshold", "80")
        emit("judging-nothing-is-unverifiable-not-pass",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and "nothing_inspected" in reasons(payload),
             payload)


def scenario_lcov_and_regression() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        report = write(root, "coverage/lcov.info", LCOV)
        code, payload = run(
            "coverage", "--project", str(root), "--report", str(report),
            "--threshold", "80", "--new-files", "lib/bad.ts",
        )
        below = [f for f in payload.get("findings", [])
                 if f["code"] == "coverage_below_threshold"]
        emit("lcov-parsed-and-below-threshold",
             code == 1 and len(below) == 1 and below[0]["measured"] == "20.0%",
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        report = write(root, "coverage/lcov.info", LCOV)
        prior = write(root, "prior/lcov.info", """SF:lib/bad.ts
DA:1,1
DA:2,1
DA:3,1
DA:4,1
DA:5,0
end_of_record
""")
        code, payload = run(
            "coverage", "--project", str(root), "--report", str(report),
            "--prior", str(prior), "--threshold", "0",
        )
        regressions = [f for f in payload.get("findings", [])
                       if f["code"] == "coverage_regression"]
        emit("coverage-regression-blocking",
             code == 1 and len(regressions) == 1
             and regressions[0]["file"] == "lib/bad.ts",
             payload)


def scenario_report_problems_are_unverifiable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        code, payload = run(
            "coverage", "--project", str(root), "--new-files", "lib/x.ts",
        )
        emit("absent-report-unverifiable-exit-zero",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and "no_coverage_report" in reasons(payload)
             and "coverage_report_absent" in
                 [f["code"] for f in payload.get("findings", [])],
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        report = write(root, "coverage/weird.dat", "some proprietary format\n")
        code, payload = run(
            "coverage", "--project", str(root), "--report", str(report),
        )
        emit("unknown-format-unverifiable-not-a-guess",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and "unknown_report_format" in reasons(payload),
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE)
        report = write(root, "coverage/coverage-summary.json", '{"total": {"lines"')
        code, payload = run(
            "coverage", "--project", str(root), "--report", str(report),
        )
        emit("truncated-report-unverifiable-not-pass-not-fail",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and "truncated_report" in reasons(payload),
             payload)


def scenario_usage_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, payload = run("authenticity", "--project", str(root / "absent"))
        emit("missing-project-exits-two", code == 2 and "error" in payload, payload)

        code, _ = run("coverage", "--project", str(root / "absent"))
        emit("coverage-missing-project-exits-two", code == 2, code)

    proc = subprocess.run([sys.executable, str(HELPER)], capture_output=True, text=True)
    emit("missing-subcommand-exits-nonzero", proc.returncode != 0, proc.returncode)


def scenario_determinism() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _base_project(root)
        write(root, "lib/__tests__/quick-split-utils.test.ts", MULTILINE_IMPORT_TEST)
        write(root, "lib/__tests__/z-bad.test.ts", NO_SOURCE_TEST)
        write(root, "lib/__tests__/a-bad.test.ts", NO_SOURCE_TEST)

        argv = [sys.executable, str(HELPER), "authenticity", "--project", str(root)]
        first = subprocess.run(argv, capture_output=True, text=True)
        second = subprocess.run(argv, capture_output=True, text=True)
        emit("repeated-runs-byte-identical",
             first.returncode == second.returncode and first.stdout == second.stdout,
             (first.stdout, second.stdout))

        payload = json.loads(first.stdout)
        keys = [(f["file"] or "", f["line"] or 0, f["code"])
                for f in payload["findings"]]
        emit("findings-sorted-by-file-line-code", keys == sorted(keys), keys)


def main() -> int:
    scenario_multiline_import_not_flagged()
    scenario_dynamic_import_not_flagged()
    scenario_no_source_import_is_flagged()
    scenario_three_fixtures_flag_exactly_one()
    scenario_e2e_and_ignore_patterns_are_out_of_scope()
    scenario_zero_tests_is_unverifiable()
    scenario_coverage_below_threshold()
    scenario_coverage_above_threshold()
    scenario_measured_value_is_reported()
    scenario_judging_nothing_is_unverifiable()
    scenario_lcov_and_regression()
    scenario_report_problems_are_unverifiable()
    scenario_usage_errors()
    scenario_determinism()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
