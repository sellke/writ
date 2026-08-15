#!/usr/bin/env python3
"""Fixture scenarios for the build smoke check (Story 4 of
`2026-08-14-script-backed-quality-gates`).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh's check_build_smoke.

**No real toolchain is ever invoked here.** Per task 4.5, the classifier is
driven over recorded build output and `check()` is called with a stubbed
runner. A CI job that actually ran `next build` would be slow, would need a
JavaScript toolchain Writ does not depend on, and would make this check's
result depend on the very environment it exists to reason about.

The recorded outputs below are real. The slug-collision error is verbatim from
the drift-log entry that requested this check; the `P1001` block was captured
from Prisma against an unreachable database on the same checkout the parent
spec's evidence comes from.

  - slug collision / type error / syntax error -> source, blocking, exit 1
  - unreachable DB / missing env / missing dep -> environment, informational,
                                                  unverifiable, exit 0
  - both signals present                       -> environment wins
  - unrecognized output                        -> unverifiable, never fail
  - timeout                                    -> unverifiable, never fail
  - composite build script                     -> declined, narrowed to the framework
  - no framework                               -> unsupported_stack, build never run
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("build-smoke.py")

_spec = importlib.util.spec_from_file_location("build_smoke_eval", HELPER)
assert _spec and _spec.loader
bs = importlib.util.module_from_spec(_spec)
# Registered before exec: the module uses dataclasses under
# `from __future__ import annotations`, and resolving a string annotation
# looks the defining module up in sys.modules.
sys.modules[_spec.name] = bs
_spec.loader.exec_module(bs)

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


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- Recorded build output ---------------------------------------------------

SLUG_COLLISION = """   Creating an optimized production build ...
Error: You cannot use different slug names for the same dynamic path ('id' !== 'token').
    at handleSlug (/proj/node_modules/next/dist/shared/lib/router/utils/sorted-routes.js:83:15)
Build failed because of webpack errors
"""

TYPE_ERROR = """Failed to compile.

./lib/settlement-utils.ts:412:9
Type error: Property 'amountCents' does not exist on type 'Expense'.
"""

SYNTAX_ERROR = """Failed to compile.

./components/Widget.tsx
Module parse failed: Unexpected token (12:4)
"""

# Captured from `prisma migrate status` against an unreachable database.
PRISMA_UNREACHABLE = """Prisma schema loaded from prisma/schema.prisma
Datasource "db": PostgreSQL database "nodb", schema "public" at "127.0.0.1:59999"
Error: P1001: Can't reach database server at `127.0.0.1:59999`

Please make sure your database server is running at `127.0.0.1:59999`.
"""

MISSING_ENV = """Error: Environment variable not found: DATABASE_URL.
  -->  schema.prisma:14
"""

MISSING_MODULE = """Error: Cannot find module 'sharp'
Require stack:
- /proj/node_modules/next/dist/server/image-optimizer.js
"""

UNRECOGNIZED = """Error: something went wrong in a way nobody enumerated
exit status 7
"""

NEXT_PACKAGE = json.dumps({
    "name": "fixture",
    "dependencies": {"next": "15.0.0"},
    "scripts": {"build": "next build"},
})

COMPOSITE_PACKAGE = json.dumps({
    "name": "fixture",
    "packageManager": "pnpm@10.33.0",
    "dependencies": {"next": "15.0.0"},
    "scripts": {
        "build": "pnpm verify-db && pnpm prisma:deploy && prisma generate "
                 "&& tsx scripts/seed-preview-test-user.ts && next build",
    },
})


def _check(root: Path, outcome: bs.BuildOutcome) -> tuple[int, dict]:
    return bs.check(root, timeout=300, runner=lambda *_a, **_k: outcome)


def scenario_source_failures() -> None:
    for name, output in (
        ("slug-collision", SLUG_COLLISION),
        ("type-error", TYPE_ERROR),
        ("syntax-error", SYNTAX_ERROR),
    ):
        emit(f"classify-{name}-as-source",
             bs.classify_failure(output, exit_code=1).kind == "source", name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        code, payload = _check(
            root, bs.BuildOutcome(exit_code=1, output=SLUG_COLLISION, timed_out=False)
        )
        findings = [f for f in payload["findings"] if f["code"] == "build_failed_source"]
        emit("source-failure-blocking-exit-one",
             code == 1
             and payload["verdict"] == "fail"
             and len(findings) == 1
             and findings[0]["severity"] == "blocking"
             and "slug names" in (findings[0]["measured"] or ""),
             payload)


def scenario_environment_failures() -> None:
    for name, output in (
        ("unreachable-database", PRISMA_UNREACHABLE),
        ("missing-env-var", MISSING_ENV),
        ("missing-dependency", MISSING_MODULE),
    ):
        emit(f"classify-{name}-as-environment",
             bs.classify_failure(output, exit_code=1).kind == "environment", name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        code, payload = _check(
            root,
            bs.BuildOutcome(exit_code=1, output=PRISMA_UNREACHABLE, timed_out=False),
        )
        findings = [
            f for f in payload["findings"] if f["code"] == "build_failed_environment"
        ]
        emit("environment-failure-informational-exit-zero",
             code == 0
             and payload["verdict"] == "unverifiable"
             and len(findings) == 1
             and findings[0]["severity"] == "informational"
             and "environment" in [e["reason"] for e in payload["unverifiable"]],
             payload)


def scenario_environment_beats_source() -> None:
    """Output carrying both signals resolves to environment. A check that
    reports fail when it means 'could not tell' gets disabled within a week."""
    mixed = PRISMA_UNREACHABLE + TYPE_ERROR
    emit("environment-wins-over-source",
         bs.classify_failure(mixed, exit_code=1).kind == "environment", mixed[:120])


def scenario_uncertainty_is_never_failure() -> None:
    emit("unrecognized-output-is-unverifiable",
         bs.classify_failure(UNRECOGNIZED, exit_code=7).kind == "unverifiable")
    emit("empty-output-is-unverifiable",
         bs.classify_failure("", exit_code=1).kind == "unverifiable")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        code, payload = _check(
            root, bs.BuildOutcome(exit_code=7, output=UNRECOGNIZED, timed_out=False)
        )
        emit("unrecognized-failure-never-blocks",
             code == 0
             and payload["verdict"] == "unverifiable"
             and not any(f["code"] == "build_failed_source" for f in payload["findings"]),
             payload)


def scenario_timeout_is_unverifiable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        code, payload = _check(
            root, bs.BuildOutcome(exit_code=None, output="", timed_out=True)
        )
        emit("timeout-is-unverifiable-never-fail",
             code == 0
             and payload["verdict"] == "unverifiable"
             and "timeout" in [e["reason"] for e in payload["unverifiable"]],
             payload)


def scenario_successful_build_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        code, payload = _check(
            root,
            bs.BuildOutcome(exit_code=0, output="Compiled with warnings", timed_out=False),
        )
        emit("successful-build-with-warnings-passes",
             code == 0 and payload["verdict"] == "pass" and payload["findings"] == [],
             payload)


def scenario_composite_script_declined() -> None:
    """AC-4.3: four database-dependent steps run before the compiler in the
    reference project. Running that script naively reports FAIL on every
    machine without a Postgres branch."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", COMPOSITE_PACKAGE)
        choice = bs.select_build_command(root)
        invoked = " ".join(choice.argv) if choice else ""
        emit("composite-build-script-declined",
             choice is not None
             and "prisma" not in invoked
             and "verify-db" not in invoked
             and "seed" not in invoked
             and "next" in invoked and "build" in invoked
             and "declined" in choice.reason,
             invoked)

        _code, payload = _check(
            root, bs.BuildOutcome(exit_code=0, output="ok", timed_out=False)
        )
        emit("declined-choice-recorded-in-inspected-method",
             "declined" in payload["inspected"]["method"], payload["inspected"])


def scenario_unsupported_stack() -> None:
    def never_run(*_args, **_kwargs):
        raise AssertionError("the build must not run for an unsupported stack")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", json.dumps({"name": "fixture"}))
        code, payload = bs.check(root, timeout=300, runner=never_run)
        emit("no-build-command-is-unsupported-stack",
             code == 0
             and payload["verdict"] == "unverifiable"
             and any(f["code"] == "unsupported_stack" for f in payload["findings"])
             and payload["inspected"]["files"] == 0,
             payload)


def scenario_read_only() -> None:
    """build-smoke executes a build and is exempt from the subprocess ban. It
    is not exempt from the write ban."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        before = {str(p.relative_to(root)) for p in root.rglob("*")}
        _check(root, bs.BuildOutcome(exit_code=1, output=SLUG_COLLISION, timed_out=False))
        after = {str(p.relative_to(root)) for p in root.rglob("*")}
        emit("checker-writes-no-file-of-its-own", before == after, after - before)


def scenario_usage_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        proc = subprocess.run(
            [sys.executable, str(HELPER), "check", "--project", str(root / "absent")],
            capture_output=True, text=True,
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        emit("missing-project-exits-two",
             proc.returncode == 2 and "error" in payload, proc.stdout)

        # A project with no framework never reaches a build, so this CLI call
        # is safe: it cannot invoke a toolchain.
        write(root, "package.json", json.dumps({"name": "fixture"}))
        proc = subprocess.run(
            [sys.executable, str(HELPER), "check", "--project", str(root)],
            capture_output=True, text=True,
        )
        payload = json.loads(proc.stdout or "{}")
        emit("cli-unsupported-stack-exits-zero",
             proc.returncode == 0
             and payload.get("schema") == "build-smoke-v1"
             and payload.get("verdict") == "unverifiable",
             proc.stdout)

    proc = subprocess.run([sys.executable, str(HELPER)], capture_output=True, text=True)
    emit("missing-subcommand-exits-nonzero", proc.returncode != 0, proc.returncode)


def scenario_determinism() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", NEXT_PACKAGE)
        outcome = bs.BuildOutcome(exit_code=1, output=SLUG_COLLISION, timed_out=False)
        first_code, first = _check(root, outcome)
        second_code, second = _check(root, outcome)
        emit("repeated-runs-byte-identical",
             first_code == second_code
             and json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True),
             (first, second))

        noisy = ("filler\n" * 5000) + SLUG_COLLISION
        _code, payload = _check(
            root, bs.BuildOutcome(exit_code=1, output=noisy, timed_out=False)
        )
        emit("output-excerpt-is-bounded",
             len(payload["findings"][0]["measured"]) < 4000,
             len(payload["findings"][0]["measured"]))


def main() -> int:
    scenario_source_failures()
    scenario_environment_failures()
    scenario_environment_beats_source()
    scenario_uncertainty_is_never_failure()
    scenario_timeout_is_unverifiable()
    scenario_successful_build_passes()
    scenario_composite_script_declined()
    scenario_unsupported_stack()
    scenario_read_only()
    scenario_usage_errors()
    scenario_determinism()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
