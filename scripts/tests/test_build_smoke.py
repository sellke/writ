#!/usr/bin/env python3
"""Unit tests for scripts/build-smoke.py (Story 4 of
`2026-08-14-script-backed-quality-gates`).

Written before the implementation, per task 4.1. The classifier is tested
directly on captured build output rather than by running real builds — a
real toolchain in CI would make these tests slow, flaky, and dependent on
the very environment the classifier exists to reason about.

The governing rule, from the parent spec's Business Rules: **environment
failure is never code failure.** A build gate that reports `fail` because
Postgres is down gets disabled within a week and takes the other three
checks with it by association. When the classifier is uncertain,
`unverifiable` is always the correct answer.

Run: python3 scripts/tests/test_build_smoke.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HELPER_PATH = Path(__file__).resolve().parents[1] / "build-smoke.py"

_spec = importlib.util.spec_from_file_location("build_smoke", HELPER_PATH)
assert _spec and _spec.loader
bs = importlib.util.module_from_spec(_spec)
# Registered before exec_module because this module uses dataclasses under
# `from __future__ import annotations`: resolving a string annotation looks the
# defining module up in sys.modules, and an unregistered module resolves to
# None. The sibling suites omit this only because their targets have no
# dataclass.
sys.modules[_spec.name] = bs
_spec.loader.exec_module(bs)


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


# --- Captured build output ---------------------------------------------------

# The reference defect, verbatim from the drift log that requested this check.
# Build-breaking, deployment-blocking, and invisible to every gate that does
# not boot the framework.
SLUG_COLLISION_OUTPUT = """   Creating an optimized production build ...
Error: You cannot use different slug names for the same dynamic path ('id' !== 'token').
    at handleSlug (/proj/node_modules/next/dist/shared/lib/router/utils/sorted-routes.js:83:15)
Build failed because of webpack errors
"""

TYPE_ERROR_OUTPUT = """   Creating an optimized production build ...
Failed to compile.

./lib/settlement-utils.ts:412:9
Type error: Property 'amountCents' does not exist on type 'Expense'.
"""

SYNTAX_ERROR_OUTPUT = """   Creating an optimized production build ...
Failed to compile.

./components/Widget.tsx
Module parse failed: Unexpected token (12:4)
SyntaxError: Unexpected token
"""

ESLINT_ERROR_OUTPUT = """   Creating an optimized production build ...
Failed to compile.

./app/page.tsx
5:1  Error: 'useState' is defined but never used.  @typescript-eslint/no-unused-vars
"""

# Environment failures. None of these is a code defect.
PRISMA_UNREACHABLE_OUTPUT = """Environment variables loaded from .env
Prisma schema loaded from prisma/schema.prisma
Error: P1001: Can't reach database server at `localhost`:`5432`

Please make sure your database server is running at `localhost`:`5432`.
"""

CONNECTION_REFUSED_OUTPUT = """> next build
Error: connect ECONNREFUSED 127.0.0.1:5432
    at TCPConnectWrap.afterConnect [as oncomplete]
"""

MISSING_ENV_OUTPUT = """> next build
Error: Environment variable not found: DATABASE_URL.
  -->  schema.prisma:14
"""

MISSING_MODULE_OUTPUT = """> next build
Error: Cannot find module 'sharp'
Require stack:
- /proj/node_modules/next/dist/server/image-optimizer.js
"""

NETWORK_OUTPUT = """> next build
Error: getaddrinfo ENOTFOUND registry.npmjs.org
    at GetAddrInfoReqWrap.onlookup [as oncomplete]
"""

TOOL_MISSING_OUTPUT = """sh: next: command not found
"""

PERMISSION_OUTPUT = """> next build
Error: EACCES: permission denied, open '/proj/.next/trace'
"""

# Neither list matches this. The honest answer is "I could not tell".
UNRECOGNIZED_OUTPUT = """> next build
Error: something went wrong in a way nobody enumerated
exit status 7
"""

SUCCESS_WITH_WARNINGS_OUTPUT = """   Creating an optimized production build ...
 ⚠ Compiled with warnings

./lib/legacy.ts
Attempted import error: 'foo' is not exported.

Route (app)                              Size     First Load JS
┌ ○ /                                    1.2 kB          89 kB
"""


class ClassifierSourceTests(unittest.TestCase):
    """AC-4.1 — a framework-level structural error typechecking cannot see."""

    def test_slug_collision_is_source_attributable(self) -> None:
        verdict = bs.classify_failure(SLUG_COLLISION_OUTPUT, exit_code=1)
        self.assertEqual(verdict.kind, "source")
        self.assertIn("slug names", verdict.signature)

    def test_type_error_is_source_attributable(self) -> None:
        self.assertEqual(bs.classify_failure(TYPE_ERROR_OUTPUT, exit_code=1).kind, "source")

    def test_syntax_error_is_source_attributable(self) -> None:
        self.assertEqual(
            bs.classify_failure(SYNTAX_ERROR_OUTPUT, exit_code=1).kind, "source"
        )

    def test_eslint_error_is_source_attributable(self) -> None:
        self.assertEqual(
            bs.classify_failure(ESLINT_ERROR_OUTPUT, exit_code=1).kind, "source"
        )


class ClassifierEnvironmentTests(unittest.TestCase):
    """AC-4.2 — an unavailable environment is never a code defect."""

    def test_unreachable_database_is_environment(self) -> None:
        verdict = bs.classify_failure(PRISMA_UNREACHABLE_OUTPUT, exit_code=1)
        self.assertEqual(verdict.kind, "environment")

    def test_connection_refused_is_environment(self) -> None:
        self.assertEqual(
            bs.classify_failure(CONNECTION_REFUSED_OUTPUT, exit_code=1).kind,
            "environment",
        )

    def test_missing_env_var_is_environment(self) -> None:
        self.assertEqual(
            bs.classify_failure(MISSING_ENV_OUTPUT, exit_code=1).kind, "environment"
        )

    def test_missing_dependency_is_environment(self) -> None:
        self.assertEqual(
            bs.classify_failure(MISSING_MODULE_OUTPUT, exit_code=1).kind, "environment"
        )

    def test_network_failure_is_environment(self) -> None:
        self.assertEqual(
            bs.classify_failure(NETWORK_OUTPUT, exit_code=1).kind, "environment"
        )

    def test_absent_build_tool_is_environment(self) -> None:
        self.assertEqual(
            bs.classify_failure(TOOL_MISSING_OUTPUT, exit_code=127).kind, "environment"
        )

    def test_permission_failure_is_environment(self) -> None:
        self.assertEqual(
            bs.classify_failure(PERMISSION_OUTPUT, exit_code=1).kind, "environment"
        )

    def test_environment_is_checked_before_source(self) -> None:
        """Output carrying both signals resolves to environment. The spec's
        direction is unambiguous: a check that reports fail when it means
        'could not tell' gets muted, and takes the true findings with it."""
        mixed = PRISMA_UNREACHABLE_OUTPUT + TYPE_ERROR_OUTPUT
        self.assertEqual(bs.classify_failure(mixed, exit_code=1).kind, "environment")


class ClassifierUncertaintyTests(unittest.TestCase):
    """The default. Anything unrecognized is `unverifiable`, never `fail`."""

    def test_unrecognized_output_is_unverifiable(self) -> None:
        self.assertEqual(
            bs.classify_failure(UNRECOGNIZED_OUTPUT, exit_code=7).kind, "unverifiable"
        )

    def test_empty_output_is_unverifiable(self) -> None:
        self.assertEqual(bs.classify_failure("", exit_code=1).kind, "unverifiable")

    def test_empty_output_yields_an_empty_excerpt(self) -> None:
        self.assertEqual(bs._excerpt("", ""), "")

    def test_excerpt_falls_back_to_the_tail_when_nothing_matched(self) -> None:
        excerpt = bs._excerpt(UNRECOGNIZED_OUTPUT, "")
        self.assertIn("exit status 7", excerpt)

    def test_classification_is_case_insensitive(self) -> None:
        self.assertEqual(
            bs.classify_failure("ERROR: ECONNREFUSED 5432", exit_code=1).kind,
            "environment",
        )


class BuildCommandSelectionTests(unittest.TestCase):
    """AC-4.3 — invoke the narrowest step that boots the framework, never a
    composite script that chains database work before the compiler."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_composite_build_script_is_declined(self) -> None:
        """The reference fixture: four database-dependent steps before the
        compiler runs. Running this naively reports FAIL on every machine
        without a Postgres branch."""
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "dependencies": {"next": "15.0.0"},
            "scripts": {
                "build": "pnpm verify-db && pnpm prisma:deploy && prisma generate "
                         "&& tsx scripts/seed-preview-test-user.ts && next build",
            },
        }))
        choice = bs.select_build_command(self.fx.root)
        self.assertIsNotNone(choice)
        assert choice is not None
        self.assertNotIn("verify-db", " ".join(choice.argv))
        self.assertNotIn("prisma", " ".join(choice.argv))
        self.assertIn("next", choice.argv)
        self.assertIn("build", choice.argv)
        self.assertIn("declined", choice.reason)

    def test_simple_build_script_is_still_narrowed_to_the_framework(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "dependencies": {"next": "15.0.0"},
            "scripts": {"build": "next build"},
        }))
        choice = bs.select_build_command(self.fx.root)
        assert choice is not None
        self.assertIn("next", choice.argv)
        self.assertIn("build", choice.argv)

    def test_next_detected_from_dev_dependencies(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "devDependencies": {"next": "15.0.0"},
        }))
        choice = bs.select_build_command(self.fx.root)
        assert choice is not None
        self.assertIn("next", choice.argv)

    def test_package_manager_is_honored(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "packageManager": "pnpm@10.33.0",
            "dependencies": {"next": "15.0.0"},
        }))
        choice = bs.select_build_command(self.fx.root)
        assert choice is not None
        self.assertEqual(choice.argv[0], "pnpm")

    def test_each_package_manager_gets_its_own_runner(self) -> None:
        for declared, expected_head in (
            ("pnpm@10.33.0", "pnpm"),
            ("yarn@4.1.0", "yarn"),
            ("bun@1.1.0", "bun"),
            ("npm@10.0.0", "npx"),
        ):
            self.fx.write("package.json", json.dumps({
                "name": "fixture",
                "packageManager": declared,
                "dependencies": {"next": "15.0.0"},
            }))
            choice = bs.select_build_command(self.fx.root)
            assert choice is not None
            self.assertEqual(choice.argv[0], expected_head, declared)

    def test_absent_package_manager_falls_back_to_npx(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "dependencies": {"next": "15.0.0"},
        }))
        choice = bs.select_build_command(self.fx.root)
        assert choice is not None
        self.assertEqual(choice.argv[0], "npx")

    def test_other_frameworks_are_recognized(self) -> None:
        for package, expected in (
            ("nuxt", "nuxt"), ("astro", "astro"),
            ("@remix-run/dev", "remix"), ("@sveltejs/kit", "svelte-kit"),
        ):
            self.fx.write("package.json", json.dumps({
                "name": "fixture", "dependencies": {package: "1.0.0"},
            }))
            choice = bs.select_build_command(self.fx.root)
            assert choice is not None, package
            self.assertIn(expected, choice.argv)

    def test_package_json_that_is_not_an_object_yields_no_command(self) -> None:
        self.fx.write("package.json", "[1, 2, 3]")
        self.assertIsNone(bs.select_build_command(self.fx.root))

    def test_non_string_build_script_is_tolerated(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "dependencies": {"next": "15.0.0"},
            "scripts": {"build": 7},
        }))
        choice = bs.select_build_command(self.fx.root)
        assert choice is not None
        self.assertIn("next", choice.argv)

    def test_no_framework_yields_no_command(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "dependencies": {"lodash": "4.0.0"},
        }))
        self.assertIsNone(bs.select_build_command(self.fx.root))

    def test_no_package_json_yields_no_command(self) -> None:
        self.assertIsNone(bs.select_build_command(self.fx.root))

    def test_unparseable_package_json_yields_no_command(self) -> None:
        self.fx.write("package.json", "{ not json")
        self.assertIsNone(bs.select_build_command(self.fx.root))


class CheckIntegrationTests(unittest.TestCase):
    """The end-to-end verdict, with the build runner stubbed. The classifier
    is the unit under test; actually invoking a toolchain is task 4.6's job
    and is never done in CI."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "dependencies": {"next": "15.0.0"},
            "scripts": {"build": "next build"},
        }))

    def _run(self, outcome: bs.BuildOutcome) -> tuple[int, dict]:
        return bs.check(self.fx.root, timeout=300, runner=lambda *_a, **_k: outcome)

    def test_source_failure_is_blocking_and_exits_one(self) -> None:
        exit_code, result = self._run(
            bs.BuildOutcome(exit_code=1, output=SLUG_COLLISION_OUTPUT, timed_out=False)
        )
        findings = [f for f in result["findings"] if f["code"] == "build_failed_source"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "blocking")
        self.assertIn("slug names", findings[0]["detail"])
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(exit_code, 1)

    def test_source_failure_includes_the_build_tools_own_error_text(self) -> None:
        _, result = self._run(
            bs.BuildOutcome(exit_code=1, output=SLUG_COLLISION_OUTPUT, timed_out=False)
        )
        finding = result["findings"][0]
        self.assertIn(
            "You cannot use different slug names for the same dynamic path",
            finding["measured"],
        )

    def test_environment_failure_is_informational_and_exits_zero(self) -> None:
        exit_code, result = self._run(
            bs.BuildOutcome(exit_code=1, output=PRISMA_UNREACHABLE_OUTPUT, timed_out=False)
        )
        findings = [
            f for f in result["findings"] if f["code"] == "build_failed_environment"
        ]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "informational")
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(exit_code, 0)
        self.assertIn("environment", [e["reason"] for e in result["unverifiable"]])

    def test_successful_build_passes(self) -> None:
        exit_code, result = self._run(
            bs.BuildOutcome(exit_code=0, output="Compiled successfully", timed_out=False)
        )
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["findings"], [])
        self.assertEqual(exit_code, 0)

    def test_warnings_do_not_fail_a_successful_build(self) -> None:
        exit_code, result = self._run(
            bs.BuildOutcome(
                exit_code=0, output=SUCCESS_WITH_WARNINGS_OUTPUT, timed_out=False
            )
        )
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(exit_code, 0)

    def test_timeout_is_unverifiable_never_fail(self) -> None:
        exit_code, result = self._run(
            bs.BuildOutcome(exit_code=None, output="", timed_out=True)
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertIn("timeout", [e["reason"] for e in result["unverifiable"]])
        self.assertEqual(exit_code, 0)
        self.assertNotIn("build_failed_source", [f["code"] for f in result["findings"]])

    def test_unrecognized_failure_is_unverifiable_never_fail(self) -> None:
        exit_code, result = self._run(
            bs.BuildOutcome(exit_code=7, output=UNRECOGNIZED_OUTPUT, timed_out=False)
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertEqual(exit_code, 0)
        self.assertNotIn("build_failed_source", [f["code"] for f in result["findings"]])

    def test_chosen_command_is_recorded_in_inspected_method(self) -> None:
        _, result = self._run(
            bs.BuildOutcome(exit_code=0, output="ok", timed_out=False)
        )
        self.assertIn("next", result["inspected"]["method"])
        self.assertIn("build", result["inspected"]["method"])

    def test_the_yuss_composite_script_is_declined_and_recorded(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture",
            "dependencies": {"next": "15.0.0"},
            "scripts": {
                "build": "pnpm verify-db && pnpm prisma:deploy && prisma generate "
                         "&& tsx scripts/seed-preview-test-user.ts && next build",
            },
        }))
        _, result = self._run(bs.BuildOutcome(exit_code=0, output="ok", timed_out=False))
        method = result["inspected"]["method"]
        invoked, _, reason = method.partition(" — ")

        # The command actually run carries none of the database steps...
        self.assertNotIn("prisma", invoked)
        self.assertNotIn("seed", invoked)
        self.assertNotIn("verify-db", invoked)
        self.assertIn("next build", invoked)

        # ...while the recorded reason names exactly what was declined, so an
        # operator can see why the check did not run their build script.
        self.assertIn("declined", reason)
        self.assertIn("prisma", reason)


class UnsupportedStackTests(unittest.TestCase):
    """AC-4.4 — no recognized build command is `unsupported_stack`, never
    `fail`, and never a silent pass."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_no_build_command_is_unsupported_stack(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        exit_code, result = bs.check(
            self.fx.root, timeout=300, runner=self._never_run
        )
        self.assertEqual(result["verdict"], "unverifiable")
        self.assertIn("unsupported_stack", [f["code"] for f in result["findings"]])
        self.assertIn("unsupported_stack", [e["reason"] for e in result["unverifiable"]])
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["inspected"]["files"], 0)

    def test_non_node_project_is_unsupported_stack(self) -> None:
        self.fx.write("Cargo.toml", "[package]\nname = 'fixture'\n")
        _, result = bs.check(self.fx.root, timeout=300, runner=self._never_run)
        self.assertEqual(result["verdict"], "unverifiable")

    def test_missing_project_raises_usage_error(self) -> None:
        with self.assertRaises(bs.UsageError):
            bs.check(self.fx.root / "absent", timeout=300, runner=self._never_run)

    @staticmethod
    def _never_run(*_args, **_kwargs):  # pragma: no cover - must never be called
        raise AssertionError("the build must not be invoked for an unsupported stack")


class ReadOnlyTests(unittest.TestCase):
    """`build-smoke` executes a build and is exempt from the subprocess ban.
    It is not exempt from the write ban."""

    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_checker_writes_no_file_of_its_own(self) -> None:
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "dependencies": {"next": "15.0.0"},
        }))
        before = {p.relative_to(self.fx.root) for p in self.fx.root.rglob("*")}
        bs.check(
            self.fx.root, timeout=300,
            runner=lambda *_a, **_k: bs.BuildOutcome(
                exit_code=1, output=SLUG_COLLISION_OUTPUT, timed_out=False
            ),
        )
        after = {p.relative_to(self.fx.root) for p in self.fx.root.rglob("*")}
        self.assertEqual(before, after)


class DeterminismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.write("package.json", json.dumps({
            "name": "fixture", "dependencies": {"next": "15.0.0"},
        }))

    def test_two_runs_byte_identical(self) -> None:
        outcome = bs.BuildOutcome(
            exit_code=1, output=SLUG_COLLISION_OUTPUT, timed_out=False
        )
        first_code, first = bs.check(
            self.fx.root, timeout=300, runner=lambda *_a, **_k: outcome
        )
        second_code, second = bs.check(
            self.fx.root, timeout=300, runner=lambda *_a, **_k: outcome
        )
        self.assertEqual(first_code, second_code)
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )

    def test_output_excerpt_is_bounded(self) -> None:
        """A build log can be megabytes. The finding quotes the error, not the
        transcript."""
        noisy = ("filler line\n" * 5000) + SLUG_COLLISION_OUTPUT
        _, result = bs.check(
            self.fx.root, timeout=300,
            runner=lambda *_a, **_k: bs.BuildOutcome(
                exit_code=1, output=noisy, timed_out=False
            ),
        )
        self.assertLess(len(result["findings"][0]["measured"]), 4000)


class CliTests(unittest.TestCase):
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

    def test_unsupported_stack_exits_zero_through_the_cli(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        code, payload = self.run_cli("check", "--project", str(self.fx.root))
        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], "build-smoke-v1")
        self.assertEqual(payload["verdict"], "unverifiable")

    def test_missing_project_exits_two(self) -> None:
        code, payload = self.run_cli("check", "--project", str(self.fx.root / "absent"))
        self.assertEqual(code, 2)
        self.assertIn("error", payload)

    def test_missing_subcommand_exits_nonzero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(HELPER_PATH)], capture_output=True, text=True
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_main_in_process(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        self.assertEqual(bs.main(["check", "--project", str(self.fx.root)]), 0)
        self.assertEqual(
            bs.main(["check", "--project", str(self.fx.root / "absent")]), 2
        )

    def test_timeout_flag_is_accepted(self) -> None:
        self.fx.write("package.json", json.dumps({"name": "fixture"}))
        code, payload = self.run_cli(
            "check", "--project", str(self.fx.root), "--timeout", "5"
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["timeout"], 5)


class RunnerTests(unittest.TestCase):
    """The real subprocess runner, exercised against trivial commands rather
    than a toolchain."""

    def test_runner_captures_output_and_exit_code(self) -> None:
        outcome = bs.run_build(
            [sys.executable, "-c", "print('hello'); raise SystemExit(3)"],
            cwd=Path.cwd(), timeout=30,
        )
        self.assertEqual(outcome.exit_code, 3)
        self.assertIn("hello", outcome.output)
        self.assertFalse(outcome.timed_out)

    def test_runner_reports_timeout(self) -> None:
        outcome = bs.run_build(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            cwd=Path.cwd(), timeout=1,
        )
        self.assertTrue(outcome.timed_out)

    def test_runner_reports_a_missing_executable_as_environment(self) -> None:
        outcome = bs.run_build(
            ["definitely-not-a-real-command-xyz"], cwd=Path.cwd(), timeout=10
        )
        self.assertNotEqual(outcome.exit_code, 0)
        self.assertEqual(
            bs.classify_failure(outcome.output, exit_code=outcome.exit_code).kind,
            "environment",
        )


if __name__ == "__main__":
    unittest.main()
