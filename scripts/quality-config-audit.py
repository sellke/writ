#!/usr/bin/env python3
"""Read-only quality-configuration audit (Story 2 of
`2026-08-14-script-backed-quality-gates`).

Inspects a project's build, typecheck, lint and coverage configuration and
reports what is switched off, so that a year of running Gate 2's
`tsc --noEmit` inside a pipeline cannot coexist with `ignoreBuildErrors:
true` in the project's own config without anyone noticing.

This is the **first** Writ script whose input surface is the host project's
own source-of-truth config rather than `.writ/**`, command markdown, or git.
That crosses the product-source / development-workspace boundary described
in `CLAUDE.md` deliberately: the whole point of the check is that Writ's
gates were being enforced on top of a harness whose native equivalents were
disabled, and no command in the framework ever looked.

This module is READ-ONLY in the strict sense `scripts/exit-criteria.py` and
`scripts/ac-trace.py` document about themselves: it never writes a file and
never invokes a subprocess. Only `/initialize` writes the baseline it reads.

Subcommand:
  check --project PATH [--baseline PATH]

Prints exactly one JSON object to stdout, schema `quality-config-audit-v1`.
Exit 0: ran correctly, no blocking findings — informational findings and an
        `unverifiable` verdict may be present.
Exit 1: ran correctly, at least one blocking finding.
Exit 2: could not run correctly — usage error, missing project root, or a
        malformed baseline. Never a silent skip.

`UNVERIFIABLE` is never exit 2. A check that ran and honestly could not
decide exits 0 with `verdict: "unverifiable"`.

The governing rule this module exists to obey, from
`.writ/docs/quality-signal-classification.md`: **unparseable is not
absent**. A heuristic that fails to find `ignoreBuildErrors` has learned
nothing about whether the gate is on. The forbidden outcome is a clean
report produced by a parser that gave up.

See `.writ/docs/quality-signal-classification.md` for the finding
vocabulary, verdict rules, parse-failure rule and baseline format this
implements against.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "quality-config-audit-v1"

SEVERITY: dict[str, str] = {
    "build_gate_disabled": "blocking",
    "coverage_threshold_absent": "blocking",
    "coverage_scope_gap": "informational",
    "tests_excluded_from_typecheck": "informational",
    "duplicate_lockfile": "informational",
    "could_not_parse": "informational",
    "unsupported_stack": "informational",
}

# Verbatim from the classification doc's enumerated cause list. A reason not
# on this list is a defect in this checker, not a new kind of uncertainty.
REASON_COULD_NOT_PARSE = "could_not_parse"
REASON_UNSUPPORTED_STACK = "unsupported_stack"
REASON_NOTHING_INSPECTED = "nothing_inspected"

# --- Config discovery --------------------------------------------------------

NEXT_CONFIG_NAMES = ("next.config.js", "next.config.mjs", "next.config.cjs", "next.config.ts")
JEST_CONFIG_NAMES = ("jest.config.js", "jest.config.mjs", "jest.config.cjs", "jest.config.ts")
LOCKFILE_NAMES = (
    "bun.lock", "bun.lockb", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
)

# Directories that never contain shipped first-party source, and so can never
# be a coverage_scope_gap.
NON_SOURCE_DIRS = {
    "node_modules", "dist", "build", "out", "coverage", "public", "static",
    "docs", "doc", "scripts", "bin", "tests", "test", "__tests__", "e2e",
    "cypress", "playwright", "fixtures", "examples", "vendor", "target",
}

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs"}

# Test-tree markers, shared by the tsconfig-exclude and lint-script readings.
TEST_TREE_MARKERS = ("__tests__", "tests/", "test/", "*.test.", "*.spec.", "__mocks__")


class UsageError(Exception):
    """Exit-2 conditions: a `--project` path that is missing or not a
    directory, or a baseline file that exists and does not parse. Raised
    instead of a silent skip — a silently-ignored baseline either floods the
    developer with findings they already acknowledged or hides real findings
    behind a typo, and both train dismissal."""


# --- JSONC-tolerant reading --------------------------------------------------

def strip_jsonc(text: str) -> str:
    """Remove `//` and `/* */` comments and trailing commas from JSONC,
    leaving string literals intact.

    `tsconfig.json` is JSONC by convention and `json.loads` rejects both
    constructs. This is a character scan rather than a regex because a regex
    over the whole text would happily strip a `//` that lives inside a
    string — e.g. a `"paths"` entry containing a URL — and corrupt the very
    file it was meant to rescue.
    """
    out: list[str] = []
    i = 0
    length = len(text)
    in_string = False
    while i < length:
        char = text[i]
        if in_string:
            out.append(char)
            if char == "\\" and i + 1 < length:
                out.append(text[i + 1])
                i += 2
                continue
            if char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            i += 1
            continue
        if char == "/" and i + 1 < length and text[i + 1] == "/":
            while i < length and text[i] != "\n":
                i += 1
            continue
        if char == "/" and i + 1 < length and text[i + 1] == "*":
            i += 2
            while i + 1 < length and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(char)
        i += 1

    stripped = "".join(out)
    # Trailing commas, now that no comment can hide one.
    return re.sub(r",(\s*[}\]])", r"\1", stripped)


def read_json_file(path: Path, *, jsonc: bool) -> tuple[Any | None, str]:
    """Return `(parsed, method)`. `parsed` is `None` when the file exists but
    cannot be reduced to a bounded answer — the caller then emits
    `could_not_parse` and downgrades, never treating the absence as clean."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, "unreadable"
    try:
        return json.loads(text), "json"
    except json.JSONDecodeError:
        pass
    if not jsonc:
        return None, "json-failed"
    try:
        return json.loads(strip_jsonc(text)), "jsonc-stripped"
    except json.JSONDecodeError:
        return None, "jsonc-failed"


# --- Bounded regex heuristics for executable-JS configs ----------------------

# A key set to a truthy literal. Deliberately narrow: `ignoreBuildErrors:
# process.env.CI !== 'true'` is NOT a match, because this heuristic cannot
# evaluate it and must not pretend to. A non-match is uninformative and the
# caller downgrades rather than reporting the gate enabled.
DISABLE_KEY_RE = re.compile(
    r"^\s*(ignoreBuildErrors|ignoreDuringBuilds)\s*:\s*(true|false)\s*,?\s*$"
)

# Anchors proving the file was read and its shape understood. Finding
# `collectCoverageFrom` is what licenses concluding that a missing
# `coverageThreshold` is a fact about the config rather than about the parser.
COVERAGE_THRESHOLD_RE = re.compile(r"^\s*coverageThreshold\s*:", re.MULTILINE)
COLLECT_COVERAGE_RE = re.compile(r"^\s*collectCoverageFrom\s*:", re.MULTILINE)

# Numeric leaves under coverageThreshold, for the zero-bar reading. The
# optional closing quote is load-bearing: a JS config writes `lines: 0` with a
# bare key, but the package.json route reaches this through json.dumps, which
# writes `"lines": 0`. Without it the zero-bar reading silently never fired on
# package.json -- and a zero bar is the obvious way to launder the check.
THRESHOLD_NUMBER_RE = re.compile(
    r"""\b(statements|branches|functions|lines)['"]?\s*:\s*(-?\d+(?:\.\d+)?)"""
)

# Glob roots inside collectCoverageFrom: 'lib/**/*.ts' -> lib. Negations
# (`!**/node_modules/**`) are exclusions, not collected roots, and are skipped.
GLOB_ROOT_RE = re.compile(r"""['"](!?)([A-Za-z0-9_.@-]+)/""")


def scan_disable_keys(text: str) -> list[tuple[int, str, str]]:
    """Every `ignoreBuildErrors`/`ignoreDuringBuilds` line, as
    `(line_no, key, literal)`. 1-based line numbers, for reporting."""
    hits: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = DISABLE_KEY_RE.match(line)
        if match:
            hits.append((line_no, match.group(1), match.group(2)))
    return hits


def threshold_is_zero_bar(text: str) -> bool:
    """True when every numeric threshold leaf is zero. A zero bar and an
    absent bar are the same bar, and setting zero is the obvious way to
    launder the check."""
    numbers = THRESHOLD_NUMBER_RE.findall(text)
    if not numbers:
        return False
    return all(float(value) <= 0 for _key, value in numbers)


def collect_roots(text: str) -> set[str]:
    """Top-level directory names a `collectCoverageFrom` block collects."""
    roots: set[str] = set()
    for negated, root in GLOB_ROOT_RE.findall(text):
        if negated:
            continue
        if root in ("**", "*") or root.startswith("."):
            continue
        roots.add(root)
    return roots


# --- Findings ----------------------------------------------------------------

def _finding(code: str, *, file: str | None, line: int | None,
             detail: str, measured: str | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "severity": SEVERITY[code],
        "file": file,
        "line": line,
        "detail": detail,
        "measured": measured,
    }


def _sort_key(finding: dict[str, Any]) -> tuple[str, int, str]:
    return (finding["file"] or "", finding["line"] or 0, finding["code"])


class Audit:
    """Accumulates findings, unverifiable entries, and the inspection
    envelope for one run.

    The envelope is built *before* any finding logic, per task 2.2, so a
    vacuous pass is structurally impossible: a report with `findings: []`
    and `inspected.files: 0` is `unverifiable`, never `pass`.
    """

    def __init__(self, project: Path) -> None:
        self.project = project
        self.findings: list[dict[str, Any]] = []
        self.unverifiable: list[dict[str, Any]] = []
        self.inspected_files: list[str] = []
        self.unparsed: list[str] = []
        self.methods: list[str] = []

    def inspect(self, rel: str, method: str) -> None:
        self.inspected_files.append(rel)
        self.methods.append(f"{rel}:{method}")

    def could_not_parse(self, rel: str, *, downgrades: tuple[str, ...], detail: str) -> None:
        """Record a file that defeated the parser, and downgrade every
        finding it would have decided. This pairing is the whole rule — a
        `could_not_parse` that did not downgrade anything would leave the
        report reading clean."""
        self.unparsed.append(rel)
        self.add("could_not_parse", file=rel, line=None, detail=detail)
        for code in downgrades:
            self.mark_unverifiable(code, REASON_COULD_NOT_PARSE, rel)

    def add(self, code: str, **kwargs: Any) -> None:
        self.findings.append(_finding(code, **kwargs))

    def mark_unverifiable(self, code: str, reason: str, detail: str) -> None:
        self.unverifiable.append({"code": code, "reason": reason, "detail": detail})


# --- Per-config-file readings ------------------------------------------------

def audit_next_config(audit: Audit, path: Path) -> None:
    """`next.config.*` is executable JavaScript. Bounded pattern match for a
    key set to a truthy literal; anything else is uninformative."""
    rel = path.name
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        audit.inspect(rel, "unreadable")
        audit.could_not_parse(
            rel, downgrades=("build_gate_disabled",),
            detail=f"{rel} could not be read",
        )
        return

    hits = scan_disable_keys(text)
    audit.inspect(rel, "pattern-match")

    disabled = [(line_no, key) for line_no, key, literal in hits if literal == "true"]
    for line_no, key in disabled:
        audit.add(
            "build_gate_disabled", file=rel, line=line_no,
            detail=f"{key} is true — {'typecheck' if key == 'ignoreBuildErrors' else 'lint'} "
                   f"errors are configured not to fail the build",
            measured=f"{key}: true",
        )

    if hits:
        return

    # No anchor of any kind matched. The file exists, it is executable
    # JavaScript, and this heuristic learned nothing — which is not the same
    # as learning the gate is on.
    audit.could_not_parse(
        rel, downgrades=("build_gate_disabled",),
        detail=f"{rel} is executable JavaScript and no bounded pattern matched; "
               f"the state of the build gate is undetermined, not enabled",
    )


def audit_jest_config(audit: Audit, path: Path | None, package_jest: Any | None) -> None:
    """Coverage threshold, from `jest.config.*` or a `jest` block in
    `package.json`.

    The `package.json` route is real parsed JSON, so its answers are exact.
    The `jest.config.*` route is pattern matching, with one licensed
    asymmetry: finding `collectCoverageFrom` proves the file was read and its
    shape understood, which makes a missing `coverageThreshold` a fact about
    the config rather than a fact about the parser.
    """
    if package_jest is not None and isinstance(package_jest, dict):
        audit.inspect("package.json#jest", "json")
        threshold = package_jest.get("coverageThreshold")
        if threshold is None:
            audit.add(
                "coverage_threshold_absent", file="package.json", line=None,
                detail="jest is configured in package.json with no coverageThreshold key",
                measured="coverageThreshold: absent",
            )
        elif threshold_is_zero_bar(json.dumps(threshold)):
            audit.add(
                "coverage_threshold_absent", file="package.json", line=None,
                detail="coverageThreshold is present but every bar is zero — "
                       "a zero bar and an absent bar are the same bar",
                measured=json.dumps(threshold, sort_keys=True),
            )
        return

    if path is None:
        return

    rel = path.name
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        audit.inspect(rel, "unreadable")
        audit.could_not_parse(
            rel, downgrades=("coverage_threshold_absent", "coverage_scope_gap"),
            detail=f"{rel} could not be read",
        )
        return

    audit.inspect(rel, "pattern-match")
    has_threshold = COVERAGE_THRESHOLD_RE.search(text) is not None
    has_collection = COLLECT_COVERAGE_RE.search(text) is not None

    if has_threshold:
        if threshold_is_zero_bar(text):
            line_no = text[:COVERAGE_THRESHOLD_RE.search(text).start()].count("\n") + 1
            audit.add(
                "coverage_threshold_absent", file=rel, line=line_no,
                detail="coverageThreshold is present but every bar is zero — "
                       "a zero bar and an absent bar are the same bar",
                measured="coverageThreshold: 0",
            )
        return

    if has_collection:
        # Licensed conclusion: the anchor proves the parser understood the file.
        audit.add(
            "coverage_threshold_absent", file=rel, line=None,
            detail="collectCoverageFrom is configured and coverageThreshold is absent — "
                   "coverage is measured and enforces nothing",
            measured="coverageThreshold: absent",
        )
        return

    audit.could_not_parse(
        rel, downgrades=("coverage_threshold_absent", "coverage_scope_gap"),
        detail=f"{rel} is executable JavaScript and neither coverageThreshold nor "
               f"collectCoverageFrom matched; the threshold's state is undetermined",
    )


def audit_coverage_scope(audit: Audit, project: Path, jest_text: str | None) -> None:
    """A source directory containing shipped code that coverage collection
    does not reach. Invisible to the measurement rather than counted against
    it, which inflates the reported number without any file looking
    under-covered."""
    if not jest_text:
        return
    roots = collect_roots(jest_text)
    if not roots:
        return

    for entry in sorted(project.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name in NON_SOURCE_DIRS or entry.name in roots:
            continue
        # A directory carrying its own package.json is a separate package, not
        # root source excluded from collection. Measured against a real
        # checkout, a vendored sub-package was this check's only false
        # positive — and a check that cries about correctly-scoped code gets
        # muted, taking the true findings with it.
        if (entry / "package.json").is_file():
            continue
        source_count = _count_own_source(entry)
        if source_count == 0:
            continue
        audit.add(
            "coverage_scope_gap", file=entry.name, line=None,
            detail=f"{entry.name}/ contains {source_count} source file(s) and is absent "
                   f"from collectCoverageFrom — excluded from measurement, not counted against it",
            measured=f"{source_count} uncollected source files",
        )


def _count_own_source(directory: Path) -> int:
    """Source files belonging to this directory's own package — the walk
    stops at any nested `package.json`, whose subtree belongs to a different
    package and is out of the root's coverage scope by construction."""
    count = 0
    stack = [directory]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_symlink():
                continue
            if child.is_dir():
                if child.name in NON_SOURCE_DIRS or child.name.startswith("."):
                    continue
                if (child / "package.json").is_file():
                    continue
                stack.append(child)
            elif child.suffix in SOURCE_SUFFIXES:
                count += 1
    return count


def audit_tsconfig(audit: Audit, path: Path) -> None:
    rel = path.name
    parsed, method = read_json_file(path, jsonc=True)
    audit.inspect(rel, method)
    if parsed is None:
        audit.could_not_parse(
            rel, downgrades=("tests_excluded_from_typecheck",),
            detail=f"{rel} did not parse as JSON or JSONC",
        )
        return
    if not isinstance(parsed, dict):
        return
    excluded = parsed.get("exclude")
    if not isinstance(excluded, list):
        return
    hits = [
        entry for entry in excluded
        if isinstance(entry, str) and any(marker in entry for marker in TEST_TREE_MARKERS)
    ]
    if hits:
        audit.add(
            "tests_excluded_from_typecheck", file=rel, line=None,
            detail=f"tsconfig exclude omits the test tree: {', '.join(sorted(hits))}",
            measured=", ".join(sorted(hits)),
        )


def audit_lint_script(audit: Audit, scripts: Any) -> None:
    """The tree most likely to accumulate dead assertions is the tree the
    linter is told to skip."""
    if not isinstance(scripts, dict):
        return
    lint = scripts.get("lint")
    if not isinstance(lint, str):
        return
    hits = [marker for marker in TEST_TREE_MARKERS if marker in lint]
    if not hits:
        return
    audit.add(
        "tests_excluded_from_typecheck", file="package.json", line=None,
        detail=f"the lint script excludes the test tree: {lint}",
        measured=lint,
    )


def audit_lockfiles(audit: Audit, project: Path, package_manager: Any) -> None:
    present = [name for name in LOCKFILE_NAMES if (project / name).is_file()]
    for name in present:
        audit.inspect(name, "presence")
    if len(present) < 2:
        return
    declared = package_manager if isinstance(package_manager, str) else "undeclared"
    audit.add(
        "duplicate_lockfile", file=sorted(present)[0], line=None,
        detail=f"{len(present)} lockfiles coexist ({', '.join(sorted(present))}) — "
               f"two possible dependency graphs; packageManager is {declared}",
        measured=", ".join(sorted(present)),
    )


# --- Baseline ----------------------------------------------------------------

BASELINE_SECTION_RE = re.compile(r"^##\s+([a-z_]+)\s*$")
BASELINE_ENTRY_RE = re.compile(
    r"^-\s+`([^`]+)`\s+—\s+(\d{4}-\d{2}-\d{2})\s+—\s+(\S.*?)\s*$"
)


def parse_baseline(path: Path) -> set[tuple[str, str]]:
    """Parse `.writ/quality-baseline.md` into `{(code, locator)}`.

    An absent baseline is not an error — it is empty, and every finding is
    new. A baseline that exists and does not parse is `UsageError` naming the
    line: refusing to run is the only honest option, because treating a
    malformed baseline as empty floods the developer with findings they
    already acknowledged, and treating it as suppressing everything hides
    real findings behind a typo.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError(f"baseline unreadable: {path} ({exc})") from exc

    entries: set[tuple[str, str]] = set()
    current: str | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        section = BASELINE_SECTION_RE.match(line)
        if section:
            code = section.group(1)
            if code not in SEVERITY:
                raise UsageError(
                    f"baseline {path} line {line_no}: '{code}' is not a registered "
                    f"finding code — register it in "
                    f".writ/docs/quality-signal-classification.md first"
                )
            current = code
            continue
        if line.startswith("## "):
            current = None
            continue
        if current is None or not line.startswith("- "):
            continue
        entry = BASELINE_ENTRY_RE.match(line)
        if not entry:
            raise UsageError(
                f"baseline {path} line {line_no}: malformed entry — expected "
                f"'- `<file>[:<line>]` — <YYYY-MM-DD> — <rationale>', got {line.strip()!r}"
            )
        entries.add((current, entry.group(1)))
    return entries


def apply_baseline(findings: list[dict[str, Any]], baseline: set[tuple[str, str]]) -> None:
    """Mark each finding acknowledged or new. Acknowledged findings are still
    reported — they are debt, made visible and dated, not debt made
    invisible — but they do not block."""
    for entry in findings:
        locator = entry["file"] or ""
        if entry["line"]:
            locator = f"{locator}:{entry['line']}"
        entry["baselined"] = (
            (entry["code"], locator) in baseline
            or (entry["code"], entry["file"] or "") in baseline
        )


# --- Top-level check ---------------------------------------------------------

def check(project: Path, baseline: Path | None) -> tuple[int, dict[str, Any]]:
    if not project.is_dir():
        raise UsageError(f"project root not found or not a directory: {project}")

    audit = Audit(project)

    baseline_entries: set[tuple[str, str]] = set()
    if baseline is not None and baseline.is_file():
        baseline_entries = parse_baseline(baseline)

    package_json = project / "package.json"
    if not package_json.is_file():
        audit.mark_unverifiable(
            "unsupported_stack", REASON_UNSUPPORTED_STACK,
            "no package.json found; Node/TypeScript is the only first-class stack",
        )
        audit.add(
            "unsupported_stack", file=None, line=None,
            detail="no Node manifest found; stack unsupported",
        )
        return _emit(audit, baseline_entries)

    package, method = read_json_file(package_json, jsonc=False)
    audit.inspect("package.json", method)
    if package is None:
        audit.could_not_parse(
            "package.json",
            downgrades=("coverage_threshold_absent", "tests_excluded_from_typecheck"),
            detail="package.json found but unparseable as JSON",
        )
        package = {}
    if not isinstance(package, dict):
        package = {}

    next_config = _first_existing(project, NEXT_CONFIG_NAMES)
    if next_config is not None:
        audit_next_config(audit, next_config)

    jest_config = _first_existing(project, JEST_CONFIG_NAMES)
    audit_jest_config(audit, jest_config, package.get("jest"))

    jest_text: str | None = None
    if jest_config is not None:
        try:
            jest_text = jest_config.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            jest_text = None
    elif isinstance(package.get("jest"), dict):
        jest_text = json.dumps(package["jest"])
    audit_coverage_scope(audit, project, jest_text)

    tsconfig = project / "tsconfig.json"
    if tsconfig.is_file():
        audit_tsconfig(audit, tsconfig)

    audit_lint_script(audit, package.get("scripts"))
    audit_lockfiles(audit, project, package.get("packageManager"))

    return _emit(audit, baseline_entries)


def _first_existing(project: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = project / name
        if candidate.is_file():
            return candidate
    return None


def _emit(audit: Audit, baseline: set[tuple[str, str]]) -> tuple[int, dict[str, Any]]:
    apply_baseline(audit.findings, baseline)
    audit.findings.sort(key=_sort_key)

    blocking = [
        f for f in audit.findings
        if f["severity"] == "blocking" and not f["baselined"]
    ]

    # The vacuous-pass guard. "0 findings" and "0 things inspected" must not
    # read the same, so an empty project is unverifiable, never pass.
    if not audit.inspected_files:
        audit.mark_unverifiable(
            "unsupported_stack", REASON_NOTHING_INSPECTED,
            "no configuration files were found to inspect",
        )

    if blocking:
        verdict = "fail"
    elif audit.unverifiable:
        verdict = "unverifiable"
    else:
        verdict = "pass"

    result = {
        "schema": SCHEMA,
        "verdict": verdict,
        "project": str(audit.project),
        "findings": audit.findings,
        "inspected": {
            "files": len(audit.inspected_files),
            "method": "; ".join(sorted(audit.methods)),
            "unparsed": sorted(set(audit.unparsed)),
        },
        "unverifiable": sorted(
            audit.unverifiable, key=lambda e: (e["code"], e["reason"], e["detail"])
        ),
    }
    return (1 if blocking else 0), result


def run_check(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    baseline = args.baseline
    if baseline is None:
        default = args.project / ".writ" / "quality-baseline.md"
        baseline = default if default.is_file() else None
    return check(args.project, baseline)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("check", help="audit a project's quality configuration")
    p.add_argument("--project", default=Path("."), type=Path)
    p.add_argument("--baseline", default=None, type=Path)
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
