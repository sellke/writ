#!/usr/bin/env python3
"""Build smoke check (Story 4 of `2026-08-14-script-backed-quality-gates`).

Boots the project's framework and distinguishes a compiler failure from an
unreachable database.

The defect class this exists to catch is real and was reported from the field
before this check was written. From a drift log entry in the repository whose
year of use produced this spec:

    Error: You cannot use different slug names for the same dynamic path
    ('id' !== 'token')

Build-breaking, deployment-blocking, and invisible to every gate that does not
boot the framework — because "every test in this repo imports route handlers as
plain functions … and invokes them directly", so neither the unit tests nor
`tsc --noEmit` ever started the router. That same entry named the fix and its
position: "add a cheap `next build` (or at least a route-manifest check) to
Gate 2".

**Environment failure is never code failure.** This is the hardest constraint
in the parent spec, made operational here. A project's own build script may
chain database migration and seeding before the compiler ever runs — the
reference case is `pnpm verify-db && pnpm prisma:deploy && prisma generate &&
tsx scripts/seed-preview-test-user.ts && next build`, four database-dependent
steps deep. A smoke check that ran that script naively would report FAIL on
every machine without a Postgres branch, and would be disabled within a week.
So this module:

  - selects the narrowest invocation that boots the framework, declining a
    composite script that chains non-compiler steps;
  - classifies a failure as environment-attributable *before* considering
    source, and defaults to `unverifiable` for anything it does not recognize.

When the classifier is uncertain, `unverifiable` is always the correct answer.

This is the only checker that executes rather than reads, and it is therefore
exempt from the subprocess ban Stories 2 and 3 carry. It is **not** exempt from
the write ban: it never writes a file itself. Artifacts the build tool produces
in its own output directory belong to the build tool.

Subcommand:
  check --project PATH [--timeout 300]

Prints exactly one JSON object to stdout, schema `build-smoke-v1`.
Exit 0: ran correctly, no blocking findings — an `unverifiable` verdict may be
        present, and usually is on a machine without the project's services.
Exit 1: ran correctly, the build failed for a reason attributable to source.
Exit 2: could not run correctly — usage error or missing project root.

See `.writ/docs/quality-signal-classification.md` for the finding vocabulary,
verdict rules and the enumerated `unverifiable` causes this implements against.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


SCHEMA = "build-smoke-v1"

SEVERITY: dict[str, str] = {
    "build_failed_source": "blocking",
    "build_failed_environment": "informational",
    "unsupported_stack": "informational",
}

REASON_ENVIRONMENT = "environment"
REASON_TIMEOUT = "timeout"
REASON_UNSUPPORTED_STACK = "unsupported_stack"
REASON_COULD_NOT_PARSE = "could_not_parse"

# How much of the build log a finding may quote. A build log can be megabytes;
# the finding carries the error, not the transcript.
EXCERPT_LIMIT = 3000


class UsageError(Exception):
    """Exit-2 conditions: a `--project` path that is missing or not a
    directory. Never used for a build that failed, and never for a build that
    could not be classified."""


@dataclass(frozen=True)
class BuildOutcome:
    """What running the build produced. `exit_code` is None when the build was
    killed by the timeout."""
    exit_code: int | None
    output: str
    timed_out: bool


@dataclass(frozen=True)
class BuildCommand:
    argv: list[str]
    reason: str


@dataclass(frozen=True)
class Classification:
    kind: str          # "source" | "environment" | "unverifiable"
    signature: str     # the matched marker, or "" when nothing matched


# --- Failure classification --------------------------------------------------

# Enumerated environment-failure signatures. Checked FIRST, and deliberately
# so: output carrying both an environment and a source signal resolves to
# environment, because a check that reports `fail` when it means "could not
# tell" gets muted and takes the true findings with it.
ENVIRONMENT_SIGNATURES = (
    # Database unreachable
    "econnrefused",
    "can't reach database server",
    "cannot reach database server",
    "p1001",
    "connection refused",
    "could not connect to server",
    "connection to server",
    "no pg_hba.conf entry",
    # Credentials and configuration
    "environment variable not found",
    "missing required environment variable",
    "missing environment variable",
    "invalid credentials",
    "authentication failed",
    # Dependencies not installed
    "cannot find module",
    "module not found: can't resolve 'next'",
    "command not found",
    "is not recognized as an internal or external command",
    "enoent: no such file or directory, open",
    # Network
    "enotfound",
    "eai_again",
    "etimedout",
    "network is unreachable",
    "socket hang up",
    # Machine
    "eacces",
    "permission denied",
    "enospc",
    "javascript heap out of memory",
)

# Enumerated source-failure signatures. Anything matching neither list is
# `unverifiable` — the classifier does not guess.
SOURCE_SIGNATURES = (
    "you cannot use different slug names for the same dynamic path",
    "type error:",
    "failed to compile",
    "module parse failed",
    "syntaxerror",
    "syntax error",
    "unexpected token",
    "build failed because of webpack errors",
    "cannot find name",
    "parsing error:",
    "duplicate page detected",
    "error: route",
)


def classify_failure(output: str, exit_code: int | None) -> Classification:
    """Decide what a non-zero build is attributable to.

    Environment first, source second, `unverifiable` by default. The ordering
    is the Business Rule "environment failure is never code failure" expressed
    as control flow.
    """
    haystack = output.lower()

    for signature in ENVIRONMENT_SIGNATURES:
        if signature in haystack:
            return Classification("environment", signature)

    for signature in SOURCE_SIGNATURES:
        if signature in haystack:
            return Classification("source", signature)

    return Classification("unverifiable", "")


def _excerpt(output: str, signature: str) -> str:
    """The build tool's own error text, centred on the matched signature."""
    if not output:
        return ""
    haystack = output.lower()
    index = haystack.find(signature) if signature else -1
    if index < 0:
        return output.strip()[-EXCERPT_LIMIT:]
    start = max(0, index - 400)
    return output[start:start + EXCERPT_LIMIT].strip()


# --- Build-command selection -------------------------------------------------

# Steps that are not the compiler. A build script chaining any of these is
# declined in favour of invoking the framework's own build directly.
NON_COMPILER_MARKERS = (
    "prisma", "migrate", "seed", "verify-db", "db:push", "db:migrate",
    "drizzle", "sequelize", "typeorm", "flyway", "liquibase",
    "docker", "wait-on", "dotenv-cli",
)

# Frameworks whose build boots a router or otherwise performs structural
# validation a typechecker cannot. Node/TypeScript only — the single
# first-class stack, per the classification doc's support matrix.
FRAMEWORK_BUILDS = (
    ("next", ["next", "build"]),
    ("nuxt", ["nuxt", "build"]),
    ("@remix-run/dev", ["remix", "build"]),
    ("@sveltejs/kit", ["svelte-kit", "build"]),
    ("astro", ["astro", "build"]),
)


def _runner_prefix(package_manager: Any) -> list[str]:
    """How to invoke a project-local binary. `packageManager` decides, since a
    project with two lockfiles still declares which toolchain is real."""
    if isinstance(package_manager, str):
        name = package_manager.split("@", 1)[0].strip()
        if name == "pnpm":
            return ["pnpm", "exec"]
        if name == "yarn":
            return ["yarn"]
        if name == "bun":
            return ["bun", "x"]
    return ["npx", "--no-install"]


def select_build_command(project: Path) -> BuildCommand | None:
    """The narrowest invocation that boots the framework, or None when no
    recognized build exists.

    Selecting narrowly is a correctness requirement for adoption, not an
    optimization: the goal is booting the router, not producing a deployable
    artifact, and every non-compiler step chained ahead of it is another way
    for a healthy codebase to report failure on a developer's laptop.
    """
    package_json = project / "package.json"
    if not package_json.is_file():
        return None
    try:
        parsed = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None

    dependencies: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies"):
        block = parsed.get(key)
        if isinstance(block, dict):
            dependencies.update(block)

    framework_argv: list[str] | None = None
    for package, argv in FRAMEWORK_BUILDS:
        if package in dependencies:
            framework_argv = argv
            break
    if framework_argv is None:
        return None

    prefix = _runner_prefix(parsed.get("packageManager"))

    scripts = parsed.get("scripts")
    build_script = scripts.get("build") if isinstance(scripts, dict) else None
    declined = ""
    if isinstance(build_script, str):
        lowered = build_script.lower()
        chained = [m for m in NON_COMPILER_MARKERS if m in lowered]
        if chained:
            declined = (
                f"declined the composite build script — it chains "
                f"{', '.join(sorted(set(chained)))} before the compiler"
            )

    reason = declined or "invoked the framework build directly"
    return BuildCommand(argv=prefix + framework_argv, reason=reason)


# --- Build execution ---------------------------------------------------------

def run_build(argv: list[str], cwd: Path, timeout: int) -> BuildOutcome:
    """Execute the build. The only subprocess this package of checkers runs,
    and the reason this module alone is exempt from the subprocess ban."""
    try:
        proc = subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return BuildOutcome(exit_code=None, output="", timed_out=True)
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return BuildOutcome(exit_code=127, output=f"command not found: {exc}",
                            timed_out=False)
    return BuildOutcome(
        exit_code=proc.returncode,
        output=(proc.stdout or "") + (proc.stderr or ""),
        timed_out=False,
    )


# --- Result assembly ---------------------------------------------------------

def _finding(code: str, *, detail: str, measured: str | None = None,
             file: str | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "severity": SEVERITY[code],
        "file": file,
        "line": None,
        "detail": detail,
        "measured": measured,
    }


def check(project: Path, timeout: int,
          runner: Callable[..., BuildOutcome] = run_build) -> tuple[int, dict[str, Any]]:
    if not project.is_dir():
        raise UsageError(f"project root not found or not a directory: {project}")
    project = project.resolve()

    findings: list[dict[str, Any]] = []
    unverifiable: list[dict[str, Any]] = []

    command = select_build_command(project)
    if command is None:
        findings.append(_finding(
            "unsupported_stack",
            detail="no recognized build command; Node/TypeScript frameworks are the "
                   "only first-class stack for this check",
        ))
        unverifiable.append({
            "code": "build_failed_source",
            "reason": REASON_UNSUPPORTED_STACK,
            "detail": "no recognized build command",
        })
        return _emit(project, findings, unverifiable,
                     {"files": 0, "method": "none", "unparsed": []}, timeout)

    outcome = runner(command.argv, cwd=project, timeout=timeout)
    method = f"{' '.join(command.argv)} — {command.reason}"

    if outcome.timed_out:
        unverifiable.append({
            "code": "build_failed_source",
            "reason": REASON_TIMEOUT,
            "detail": f"build exceeded {timeout}s; treated as unverifiable",
        })
    elif outcome.exit_code == 0:
        pass  # A build that succeeds with warnings is a pass; warnings are not this check's job.
    else:
        verdict = classify_failure(outcome.output, outcome.exit_code)
        excerpt = _excerpt(outcome.output, verdict.signature)
        if verdict.kind == "source":
            findings.append(_finding(
                "build_failed_source",
                detail=f"the build failed for a reason attributable to source "
                       f"(matched {verdict.signature!r})",
                measured=excerpt,
            ))
        elif verdict.kind == "environment":
            findings.append(_finding(
                "build_failed_environment",
                detail=f"build could not run here: matched {verdict.signature!r} — "
                       f"an unavailable environment is never a code defect",
                measured=excerpt,
            ))
            unverifiable.append({
                "code": "build_failed_source",
                "reason": REASON_ENVIRONMENT,
                "detail": f"build failed on {verdict.signature!r}",
            })
        else:
            unverifiable.append({
                "code": "build_failed_source",
                "reason": REASON_COULD_NOT_PARSE,
                "detail": f"build exited {outcome.exit_code} and the output matched "
                          f"neither the environment nor the source signature list",
            })

    inspected = {"files": 1, "method": method, "unparsed": []}
    return _emit(project, findings, unverifiable, inspected, timeout)


def _emit(project: Path, findings: list[dict[str, Any]],
          unverifiable: list[dict[str, Any]], inspected: dict[str, Any],
          timeout: int) -> tuple[int, dict[str, Any]]:
    findings.sort(key=lambda f: (f["file"] or "", f["line"] or 0, f["code"]))
    blocking = [f for f in findings if f["severity"] == "blocking"]

    if blocking:
        verdict = "fail"
    elif unverifiable:
        verdict = "unverifiable"
    else:
        verdict = "pass"

    result = {
        "schema": SCHEMA,
        "verdict": verdict,
        "project": str(project),
        "findings": findings,
        "inspected": inspected,
        "timeout": timeout,
        "unverifiable": sorted(
            unverifiable, key=lambda e: (e["code"], e["reason"], e["detail"])
        ),
    }
    return (1 if blocking else 0), result


def run_check(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    return check(args.project, args.timeout)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("check", help="boot the project's framework and classify the result")
    p.add_argument("--project", default=Path("."), type=Path)
    p.add_argument("--timeout", default=300, type=int)
    p.set_defaults(func=run_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        exit_code, result = args.func(args)
    except UsageError as exc:
        print(json.dumps({"schema": SCHEMA, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
