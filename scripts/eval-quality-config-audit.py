#!/usr/bin/env python3
"""Fixture scenarios for the quality-configuration audit (Story 2 of
`2026-08-14-script-backed-quality-gates`).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh's
check_quality_config_audit. Every scenario builds a disposable project in a
temp directory and exercises scripts/quality-config-audit.py via its CLI,
following scripts/eval-ac-trace.py's exact shape.

CI runs scripts/eval.sh and never scripts/tests/, so these scenarios plus
eval.sh's require_literal/forbid_literal bindings are this checker's entire
CI protection.

  - clean project                    -> exit 0, verdict pass
  - build_gate_disabled (both keys)  -> blocking, exit 1, lines 8 and 11
  - coverage_threshold_absent        -> blocking, exit 1
  - zero coverageThreshold           -> same finding as an absent one
  - could_not_parse downgrade        -> unverifiable, exit 0, never pass
  - informational findings only      -> exit 0
  - empty project                    -> unverifiable, inspected.files 0
  - baseline suppression / new finding / malformed baseline
  - byte-identical repeat runs
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("quality-config-audit.py")
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
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
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


def codes(payload: dict) -> list[str]:
    return [f["code"] for f in payload.get("findings", [])]


def unverifiable_codes(payload: dict) -> list[str]:
    return [e["code"] for e in payload.get("unverifiable", [])]


PACKAGE_MINIMAL = json.dumps({"name": "fixture", "version": "1.0.0"})

NEXT_DISABLED = """const withBundleAnalyzer = require('@next/bundle-analyzer')({
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

NEXT_ENABLED = """/** @type {import('next').NextConfig} */
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

NEXT_OPAQUE = "module.exports = require('./config/build')(process.env.NODE_ENV)\n"

JEST_NO_THRESHOLD = """module.exports = {
  collectCoverageFrom: ['lib/**/*.ts'],
}
"""

JEST_ZERO_THRESHOLD = """module.exports = {
  collectCoverageFrom: ['lib/**/*.ts'],
  coverageThreshold: { global: { lines: 0, statements: 0 } },
}
"""

JEST_REAL_THRESHOLD = """module.exports = {
  collectCoverageFrom: ['lib/**/*.ts'],
  coverageThreshold: { global: { lines: 80, statements: 80 } },
}
"""

JEST_OPAQUE = "module.exports = require('./jest/base')\n"


def scenario_clean_project_exits_zero() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "next.config.js", NEXT_ENABLED)
        write(root, "jest.config.js", JEST_REAL_THRESHOLD)
        code, payload = run("check", "--project", str(root))
        emit("clean-project-exits-zero",
             code == 0 and payload.get("verdict") == "pass" and payload.get("findings") == [],
             payload)


def scenario_build_gate_disabled() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "next.config.js", NEXT_DISABLED)
        code, payload = run("check", "--project", str(root))
        gates = [f for f in payload.get("findings", []) if f["code"] == "build_gate_disabled"]
        emit("build-gate-disabled-blocking",
             code == 1
             and payload.get("verdict") == "fail"
             and len(gates) == 2
             and [g["line"] for g in gates] == [8, 11]
             and all(g["severity"] == "blocking" for g in gates),
             payload)


def scenario_coverage_threshold_absent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "jest.config.js", JEST_NO_THRESHOLD)
        code, payload = run("check", "--project", str(root))
        emit("coverage-threshold-absent-blocking",
             code == 1 and "coverage_threshold_absent" in codes(payload),
             payload)


def scenario_zero_threshold_is_absent_threshold() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "jest.config.js", JEST_ZERO_THRESHOLD)
        code, payload = run("check", "--project", str(root))
        emit("zero-threshold-is-absent-threshold",
             code == 1 and "coverage_threshold_absent" in codes(payload),
             payload)


def scenario_could_not_parse_downgrades() -> None:
    """The load-bearing scenario: a config that defeated the parser must never
    produce a clean verdict. Treating 'pattern not found' as 'gate enabled'
    reproduces the exact defect this checker exists to catch."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "next.config.js", NEXT_OPAQUE)
        code, payload = run("check", "--project", str(root))
        emit("could-not-parse-downgrades-to-unverifiable",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and "could_not_parse" in codes(payload)
             and "build_gate_disabled" in unverifiable_codes(payload)
             and "next.config.js" in payload.get("inspected", {}).get("unparsed", []),
             payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "jest.config.js", JEST_OPAQUE)
        code, payload = run("check", "--project", str(root))
        emit("opaque-jest-config-never-reports-clean",
             code == 0
             and payload.get("verdict") != "pass"
             and "coverage_threshold_absent" in unverifiable_codes(payload)
             and "coverage_threshold_absent" not in codes(payload),
             payload)


def scenario_collection_anchor_licenses_conclusion() -> None:
    """The one licensed asymmetry: finding collectCoverageFrom proves the file
    was read and understood, which makes a missing coverageThreshold a fact
    about the config rather than about the parser."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "jest.config.js", JEST_NO_THRESHOLD)
        _code, payload = run("check", "--project", str(root))
        emit("collection-anchor-licenses-threshold-conclusion",
             "coverage_threshold_absent" in codes(payload)
             and "coverage_threshold_absent" not in unverifiable_codes(payload),
             payload)


def scenario_informational_only_exits_zero() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", json.dumps({
            "name": "fixture", "packageManager": "pnpm@10.33.0",
            "scripts": {"lint": "eslint . --ignore-pattern 'tests/**'"},
        }))
        write(root, "bun.lock", "{}\n")
        write(root, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        code, payload = run("check", "--project", str(root))
        found = set(codes(payload))
        emit("informational-findings-do-not-block",
             code == 0
             and payload.get("verdict") != "fail"
             and "duplicate_lockfile" in found
             and "tests_excluded_from_typecheck" in found,
             payload)


def scenario_empty_project_is_unverifiable() -> None:
    """The vacuous-pass guard: '0 findings' and '0 things inspected' must not
    read the same."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, payload = run("check", "--project", str(root))
        emit("empty-project-unverifiable-never-pass",
             code == 0
             and payload.get("verdict") == "unverifiable"
             and payload.get("inspected", {}).get("files") == 0
             and "unsupported_stack" in unverifiable_codes(payload),
             payload)


def scenario_nested_package_not_a_scope_gap() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "jest.config.js", JEST_NO_THRESHOLD)
        write(root, "lib/util.ts", "export const a = 1\n")
        write(root, "vendored/package.json", json.dumps({"name": "vendored"}))
        write(root, "vendored/src/index.ts", "export const b = 2\n")
        _code, payload = run("check", "--project", str(root))
        gaps = [f["file"] for f in payload.get("findings", [])
                if f["code"] == "coverage_scope_gap"]
        emit("nested-package-is-not-a-scope-gap", "vendored" not in gaps, payload)


def scenario_coverage_scope_gap() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "jest.config.js", JEST_NO_THRESHOLD)
        write(root, "lib/util.ts", "export const a = 1\n")
        write(root, "app/api/thing/route.ts", "export async function GET() {}\n")
        _code, payload = run("check", "--project", str(root))
        gaps = [f for f in payload.get("findings", []) if f["code"] == "coverage_scope_gap"]
        emit("coverage-scope-gap-names-uncollected-dir",
             len(gaps) == 1
             and gaps[0]["file"] == "app"
             and gaps[0]["severity"] == "informational",
             payload)


def scenario_baseline_suppression() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "next.config.js", NEXT_DISABLED)
        write(root, ".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — predates adoption.
- `next.config.js:11` — 2026-08-14 — predates adoption.
""")
        code, payload = run("check", "--project", str(root))
        emit("baselined-finding-acknowledged-not-blocking",
             code == 0
             and payload.get("verdict") != "fail"
             and all(f["baselined"] for f in payload.get("findings", [])),
             payload)


def scenario_new_finding_still_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        write(root, "next.config.js", NEXT_DISABLED)
        write(root, ".writ/quality-baseline.md", """# Quality Baseline

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — only this one is acknowledged.
""")
        code, payload = run("check", "--project", str(root))
        new = [f for f in payload.get("findings", [])
               if f["code"] == "build_gate_disabled" and not f["baselined"]]
        emit("finding-absent-from-baseline-still-blocks",
             code == 1 and len(new) == 1 and new[0]["line"] == 11,
             payload)


def scenario_malformed_baseline_exits_two() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        bad = write(root, "bad.md", "## build_gate_disabled\n\n- no date, no rationale\n")
        code, payload = run("check", "--project", str(root), "--baseline", str(bad))
        emit("malformed-baseline-exits-two",
             code == 2 and "error" in payload, payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", PACKAGE_MINIMAL)
        bad = write(root, "bad.md",
                    "## invented_code\n\n- `a.js` — 2026-08-14 — nope.\n")
        code, payload = run("check", "--project", str(root), "--baseline", str(bad))
        emit("baseline-unregistered-code-exits-two",
             code == 2 and "error" in payload, payload)


def scenario_usage_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, payload = run("check", "--project", str(root / "absent"))
        emit("missing-project-exits-two", code == 2 and "error" in payload, payload)

    proc = subprocess.run([sys.executable, str(HELPER)], capture_output=True, text=True)
    emit("missing-subcommand-exits-nonzero", proc.returncode != 0, proc.returncode)


def scenario_determinism() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root, "package.json", json.dumps({
            "name": "fixture", "packageManager": "pnpm@10.33.0",
            "scripts": {"lint": "eslint . --ignore-pattern 'tests/**'"},
        }))
        write(root, "next.config.js", NEXT_DISABLED)
        write(root, "jest.config.js", JEST_NO_THRESHOLD)
        write(root, "bun.lock", "{}\n")
        write(root, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        write(root, "lib/util.ts", "export const a = 1\n")
        write(root, "app/api/thing/route.ts", "export async function GET() {}\n")

        argv = [sys.executable, str(HELPER), "check", "--project", str(root)]
        first = subprocess.run(argv, capture_output=True, text=True)
        second = subprocess.run(argv, capture_output=True, text=True)
        emit("repeated-runs-byte-identical",
             first.returncode == second.returncode and first.stdout == second.stdout,
             (first.stdout, second.stdout))

        payload = json.loads(first.stdout)
        keys = [(f["file"] or "", f["line"] or 0, f["code"]) for f in payload["findings"]]
        emit("findings-sorted-by-file-line-code", keys == sorted(keys), keys)


def main() -> int:
    scenario_clean_project_exits_zero()
    scenario_build_gate_disabled()
    scenario_coverage_threshold_absent()
    scenario_zero_threshold_is_absent_threshold()
    scenario_could_not_parse_downgrades()
    scenario_collection_anchor_licenses_conclusion()
    scenario_informational_only_exits_zero()
    scenario_empty_project_is_unverifiable()
    scenario_nested_package_not_a_scope_gap()
    scenario_coverage_scope_gap()
    scenario_baseline_suppression()
    scenario_new_finding_still_blocks()
    scenario_malformed_baseline_exits_two()
    scenario_usage_errors()
    scenario_determinism()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
