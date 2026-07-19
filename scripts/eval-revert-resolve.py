#!/usr/bin/env python3
"""Scenario emitter for the logical-unit revert resolver (Story 2/4).

Runs the real unit suite in scripts/tests/test_revert_resolve.py and emits one
PASS/FAIL TSV line per test, consumed by scripts/eval.sh check_revert. The unit
tests build disposable git repositories and exercise every resolution layer
(recorded / ref-footer / phase-state / ghost), spec union, ordering, base, and
the read-only guarantee — so wiring them here keeps a single source of truth
rather than duplicating fixtures.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path


TEST_PATH = Path(__file__).with_name("tests") / "test_revert_resolve.py"


def _load_suite() -> unittest.TestSuite:
    spec = importlib.util.spec_from_file_location("test_revert_resolve", TEST_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return unittest.defaultTestLoader.loadTestsFromModule(module)


class TsvResult(unittest.TestResult):
    """Emits a PASS/FAIL TSV line per test to stdout."""

    def _name(self, test: unittest.TestCase) -> str:
        return test.id().rsplit(".", 2)[-2] + "." + test.id().rsplit(".", 1)[-1]

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        print(f"PASS\t{self._name(test)}")

    def _fail(self, test: unittest.TestCase, err) -> None:
        reason = str(err[1]).replace("\n", "\\n").replace("\t", " ")[:200]
        print(f"FAIL\t{self._name(test)}\t{reason}")

    def addFailure(self, test, err) -> None:
        super().addFailure(test, err)
        self._fail(test, err)

    def addError(self, test, err) -> None:
        super().addError(test, err)
        self._fail(test, err)


def main() -> int:
    if not TEST_PATH.is_file():
        print(f"FAIL\tsuite-missing\t{TEST_PATH} not found")
        return 1
    suite = _load_suite()
    result = TsvResult()
    with redirect_stderr(io.StringIO()):
        suite.run(result)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
