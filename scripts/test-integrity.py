#!/usr/bin/env python3
"""Read-only test-integrity checker (Story 3 of
`2026-08-14-script-backed-quality-gates`).

Two claims Writ has always stated and never verified:

  coverage      Recomputes per-file line coverage from the test tooling's own
                machine-readable output. `agents/testing-agent.md:133` carries
                `- **Coverage threshold met:** [YES/NO]` — a field the agent
                types, which nothing recomputed. This subcommand takes no
                input by which a caller can assert the answer; the number in
                the report becomes the number the tool measured, and where the
                two disagree the tool wins, exactly as `scripts/exit-criteria.py`
                overrides a self-reported COMPLETE.

  authenticity  Flags a test file that resolves zero module specifiers into
                project source — a test that cannot fail when the code it
                claims to cover changes.

**The specifier extractor is the whole story, and a line-oriented regex is
the wrong implementation.** Measured against 147 real unit-test files:

    hand-audit                      ->  6 files  (over-counted by 50%)
    naive single-line import regex  -> 22 files  (82% false positives)
    whole-file specifier extraction ->  4 files  (ground truth)

Multi-line `import {\\n…\\n} from '…'` blocks and dynamic
`await import('…')` calls both escape a per-line match. Specifiers are
therefore extracted from the entire file text, never line by line.

A false positive costs more than a false negative here: a check that cries
about good tests gets muted, and takes the real findings with it. So where a
specifier cannot be cheaply resolved, this module prefers flagging nothing.

This module is READ-ONLY in the strict sense `scripts/exit-criteria.py` and
`scripts/ac-trace.py` document about themselves: it never writes a file and
never invokes a subprocess. It reads a coverage report someone else produced;
it does not run the test suite.

Subcommands:
  coverage     --project PATH [--report PATH] [--new-files PATH ...]
               [--threshold N] [--prior PATH]
  authenticity --project PATH [--tests PATH ...]

Prints exactly one JSON object to stdout, schema `test-integrity-v1`.
Exit 0: ran correctly, no blocking findings — an `unverifiable` verdict may
        be present.
Exit 1: ran correctly, at least one blocking finding.
Exit 2: could not run correctly — usage error or missing project root.

`UNVERIFIABLE` is never exit 2. See
`.writ/docs/quality-signal-classification.md` for the finding vocabulary,
verdict rules and the enumerated `unverifiable` causes this implements
against.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Any


SCHEMA = "test-integrity-v1"

SEVERITY: dict[str, str] = {
    "coverage_below_threshold": "blocking",
    "coverage_regression": "blocking",
    "coverage_report_absent": "informational",
    "test_imports_no_source": "blocking",
    "could_not_parse": "informational",
    "unsupported_stack": "informational",
}

REASON_NO_COVERAGE_REPORT = "no_coverage_report"
REASON_UNKNOWN_REPORT_FORMAT = "unknown_report_format"
REASON_TRUNCATED_REPORT = "truncated_report"
REASON_COULD_NOT_PARSE = "could_not_parse"
REASON_NOTHING_INSPECTED = "nothing_inspected"

SOURCE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs")
TEST_SUFFIX_RE = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$")
TEST_DIR_SEGMENTS = {"__tests__", "__mocks__", "tests", "test", "spec", "e2e"}
TEST_HELPER_NAMES = {"test-utils", "test-helpers", "testUtils", "setupTests", "jest.setup"}

SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", "out", "coverage", ".writ"}


class UsageError(Exception):
    """Exit-2 conditions: a `--project` path that is missing or not a
    directory. Reserved for the checker being unable to operate at all —
    never for it being unable to decide, which is `unverifiable` and exit 0."""


# --- Specifier extraction ----------------------------------------------------

# Comments are stripped before extraction so a commented-out import cannot
# vouch for a file. Same character-scan reasoning as the JSONC reader in
# quality-config-audit.py: a regex would strip a `//` inside a string literal.
def strip_js_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    length = len(text)
    quote: str | None = None
    while i < length:
        char = text[i]
        if quote is not None:
            out.append(char)
            if char == "\\" and i + 1 < length:
                out.append(text[i + 1])
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char in "\"'`":
            quote = char
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
    return "".join(out)


# Every pattern below runs against the WHOLE file text, never a single line.
# `from '…'` alone covers both the single-line and the multi-line import form,
# because the `from` clause and its specifier always sit together regardless of
# how many lines the brace list spans — which is precisely what a per-line
# match gets wrong.
SPECIFIER_PATTERNS = (
    re.compile(r"""\bfrom\s*['"]([^'"]+)['"]"""),
    re.compile(r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""(?<![\w$.])require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""^\s*import\s+['"]([^'"]+)['"]""", re.MULTILINE),
)


def extract_specifiers(text: str) -> list[str]:
    """Every module specifier in the file, in first-seen order.

    Deliberately excludes `jest.mock('…')` and `jest.requireActual('…')`:
    mocking a module is the opposite of testing it, and a file whose only
    reference to production code is a mock has not exercised that code.
    """
    stripped = strip_js_comments(text)
    seen: dict[str, None] = {}
    for pattern in SPECIFIER_PATTERNS:
        for match in pattern.finditer(stripped):
            seen.setdefault(match.group(1), None)
    return list(seen)


# --- Specifier classification ------------------------------------------------

def load_aliases(project: Path) -> dict[str, str]:
    """Path aliases, read from `tsconfig.json` `compilerOptions.paths` where
    available. `@/` -> project root is the near-universal Next.js convention
    and is assumed as a fallback; assuming it is safe because the failure mode
    of a wrong alias is a *missed* flag, not a false one."""
    aliases: dict[str, str] = {"@/": ""}
    tsconfig = project / "tsconfig.json"
    if not tsconfig.is_file():
        return aliases
    try:
        raw = tsconfig.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return aliases
    raw = re.sub(r"//[^\n]*", "", raw)
    raw = re.sub(r",(\s*[}\]])", r"\1", raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return aliases
    if not isinstance(parsed, dict):
        return aliases
    paths = (parsed.get("compilerOptions") or {}).get("paths")
    if not isinstance(paths, dict):
        return aliases
    for pattern, targets in paths.items():
        if not isinstance(targets, list) or not targets:
            continue
        target = targets[0]
        if not isinstance(target, str):
            continue
        cleaned = target.replace("*", "")
        # Remove a leading "./" only. `lstrip("./")` strips any run of "." and
        # "/" characters, which silently turns a monorepo alias like
        # "../shared/" into "shared/" -- a different directory inside the
        # project, resolved wrongly and without complaint.
        while cleaned.startswith("./"):
            cleaned = cleaned[2:]
        aliases[pattern.replace("*", "")] = cleaned
    return aliases


def is_test_shaped(path: Path) -> bool:
    """A path that is itself test scaffolding — a helper, a mock, another
    test — is not production source, so importing it does not vouch for the
    file that imports it."""
    if TEST_SUFFIX_RE.search(path.name):
        return True
    if any(part in TEST_DIR_SEGMENTS for part in path.parts):
        return True
    return path.stem in TEST_HELPER_NAMES


def resolve_specifier(specifier: str, test_file: Path, project: Path,
                      aliases: dict[str, str]) -> tuple[Path | None, bool]:
    """Return `(resolved_path, is_project_shaped)`.

    `is_project_shaped` is True for a relative or aliased specifier — one that
    *claims* to point into this project. `resolved_path` is the file it
    actually names, or None when resolution failed.
    """
    base: Path | None = None
    if specifier.startswith("."):
        base = (test_file.parent / specifier).resolve()
    else:
        for prefix, target in sorted(aliases.items(), key=lambda kv: -len(kv[0])):
            if specifier.startswith(prefix):
                remainder = specifier[len(prefix):]
                base = (project / target / remainder).resolve()
                break
    if base is None:
        return None, False  # a bare package name: external

    for candidate in (base, *(base.with_suffix(suffix) for suffix in SOURCE_SUFFIXES)):
        if candidate.is_file():
            return candidate, True
    for suffix in SOURCE_SUFFIXES:
        candidate = base / f"index{suffix}"
        if candidate.is_file():
            return candidate, True
    return None, True


def imports_project_source(text: str, test_file: Path, project: Path,
                           aliases: dict[str, str]) -> bool:
    """True when at least one specifier reaches production source.

    An unresolvable project-shaped specifier counts as source. That is
    deliberate: generated types, build-time aliases and path mappings this
    module cannot see are all common, and flagging a good test wrongly costs
    more than missing a bad one.
    """
    for specifier in extract_specifiers(text):
        resolved, project_shaped = resolve_specifier(
            specifier, test_file, project, aliases
        )
        if not project_shaped:
            continue
        if resolved is None:
            return True
        try:
            relative = resolved.relative_to(project.resolve())
        except ValueError:
            continue  # an alias escaping the project is not project source
        if not is_test_shaped(relative):
            return True
    return False


# --- Test scope --------------------------------------------------------------

# A test importing one of these drives a running application through a browser
# or a wire protocol. It exercises production code without importing any of it,
# so `test_imports_no_source` is meaningless against it — flagging such a file
# is a false positive by construction. This list is the stack-general backstop
# used when a project declares no ignore patterns of its own.
E2E_DRIVERS = (
    "@playwright/test", "playwright", "cypress", "puppeteer",
    "selenium-webdriver", "webdriverio", "@wdio/globals", "testcafe",
    "detox", "@cucumber/cucumber",
)

TEST_IGNORE_ARRAY_RE = re.compile(
    r"testPathIgnorePatterns\s*:\s*\[(.*?)\]", re.DOTALL
)
QUOTED_RE = re.compile(r"""['"]([^'"]+)['"]""")


def load_test_ignore_patterns(project: Path) -> list[str]:
    """The project's own declaration of what is not a unit test, read from
    `testPathIgnorePatterns` in a jest config or a `package.json` jest block.

    Honouring this rather than inventing our own exclusions is what keeps the
    examined set equal to the set the project's own runner considers unit
    tests. Read by bounded pattern match, since jest configs are executable
    JavaScript; an unreadable config yields no patterns and the E2E-driver
    backstop carries the load.
    """
    patterns: list[str] = []

    package_json = project / "package.json"
    if package_json.is_file():
        try:
            parsed = json.loads(package_json.read_text(encoding="utf-8"))
            block = parsed.get("jest") if isinstance(parsed, dict) else None
            declared = block.get("testPathIgnorePatterns") if isinstance(block, dict) else None
            if isinstance(declared, list):
                patterns.extend(p for p in declared if isinstance(p, str))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            pass

    for name in ("jest.config.js", "jest.config.mjs", "jest.config.cjs", "jest.config.ts"):
        config = project / name
        if not config.is_file():
            continue
        try:
            text = config.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Comments are stripped first. A real config carries prose comments
        # inside this very array, and an apostrophe in one ("tests that can't
        # connect to a DB locally") reads as a string delimiter and corrupts
        # every pattern after it -- silently, into patterns that match nothing.
        match = TEST_IGNORE_ARRAY_RE.search(strip_js_comments(text))
        if match:
            patterns.extend(QUOTED_RE.findall(match.group(1)))
        break

    return [p.replace("<rootDir>/", "").replace("<rootDir>", "") for p in patterns]


def is_ignored_by_project(relative: str, patterns: list[str]) -> bool:
    """`testPathIgnorePatterns` entries are regexes matched against the full
    path. Matching against the repo-relative path with the `<rootDir>` prefix
    already stripped is the same test for every pattern a real config uses."""
    for pattern in patterns:
        try:
            if re.search(pattern, relative):
                return True
        except re.error:
            # A pattern that is not valid Python regex still carries a leading
            # literal segment worth honouring -- treat that as a substring
            # rather than discarding the project's stated intent entirely.
            literal = re.split(r"[\[\](){}*+?|\\^$]", pattern, maxsplit=1)[0]
            if literal.strip("/") and literal in relative:
                return True
    return False


def is_e2e_test(text: str) -> bool:
    return any(spec in E2E_DRIVERS for spec in extract_specifiers(text))


# --- Test discovery ----------------------------------------------------------

def discover_tests(project: Path) -> list[Path]:
    """Every unit-test file under the project, mirroring the conventional
    Jest `testMatch`: anything inside a `__tests__/` directory, plus any
    `*.test.*` / `*.spec.*` basename. Vendor, build and end-to-end trees are
    skipped — they are not this check's subject."""
    found: list[Path] = []
    stack = [project]
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
                if child.name in SKIP_DIRS or child.name.startswith("."):
                    continue
                if (child / "package.json").is_file() and child != project:
                    continue  # a nested package owns its own tests
                stack.append(child)
                continue
            if child.suffix not in SOURCE_SUFFIXES:
                continue
            relative = child.relative_to(project)
            if "__tests__" in relative.parts or TEST_SUFFIX_RE.search(child.name):
                found.append(child)
    return sorted(found)


# --- Coverage report parsing -------------------------------------------------

COVERAGE_REPORT_CANDIDATES = (
    "coverage/coverage-summary.json",
    "coverage/coverage-final.json",
    "coverage/lcov.info",
    "lcov.info",
    "coverage.xml",
)


class ReportError(Exception):
    """A report that was found but could not be reduced to per-file numbers.
    Carries the enumerated `unverifiable` reason so the caller never has to
    invent one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def parse_coverage_report(
    path: Path,
) -> tuple[dict[str, tuple[int, int]], str, tuple[int, int] | None]:
    """Return `({file: (covered_lines, total_lines)}, method, declared_total)`.

    `declared_total` is the report's own aggregate where the format carries
    one — Jest's `coverage-summary.json` has a `total` block covering every
    collected file. It is preferred over summing the per-file records, because
    the entire purpose of this subcommand is to report the number *the tool
    measured*, not a number re-aggregated from whichever records happened to
    parse. `None` means the format has no separate aggregate and summing the
    per-file records is exact.

    Raises `ReportError` rather than guessing. Guessing at a format and
    misparsing it produces a confident wrong number, which is worse than no
    number at all.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReportError(REASON_NO_COVERAGE_REPORT, f"{path} unreadable ({exc})")

    if path.suffix == ".json" or text.lstrip().startswith("{"):
        return _parse_json_report(text, path)
    if path.suffix == ".xml" or text.lstrip().startswith("<?xml"):
        files, method = _parse_cobertura(text, path)
        return files, method, None
    if "SF:" in text or text.startswith("TN:"):
        files, method = _parse_lcov(text)
        return files, method, None
    raise ReportError(
        REASON_UNKNOWN_REPORT_FORMAT, f"{path.name} is not a recognized coverage format"
    )


def _parse_json_report(
    text: str, path: Path,
) -> tuple[dict[str, tuple[int, int]], str, tuple[int, int] | None]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReportError(
            REASON_TRUNCATED_REPORT, f"{path.name} is not valid JSON ({exc.msg})"
        )
    if not isinstance(parsed, dict):
        raise ReportError(REASON_UNKNOWN_REPORT_FORMAT, f"{path.name} is not an object")

    files: dict[str, tuple[int, int]] = {}
    for key, entry in parsed.items():
        if key == "total" or not isinstance(entry, dict):
            continue
        lines = entry.get("lines")
        if isinstance(lines, dict) and "covered" in lines and "total" in lines:
            files[key] = (int(lines["covered"]), int(lines["total"]))
            continue
        statement_map = entry.get("s")
        if isinstance(statement_map, dict):
            hits = list(statement_map.values())
            files[key] = (sum(1 for h in hits if h), len(hits))
    if not files and "total" not in parsed:
        raise ReportError(
            REASON_UNKNOWN_REPORT_FORMAT, f"{path.name} has no recognizable file records"
        )

    declared: tuple[int, int] | None = None
    total_block = parsed.get("total")
    if isinstance(total_block, dict):
        # `statements` first, because the reported aggregate is named
        # statements_pct and the two differ -- a real suite measured 57.22%
        # statements and 58.2% lines, and quoting the wrong one against a
        # claim would be its own small dishonesty.
        stats = total_block.get("statements") or total_block.get("lines")
        if isinstance(stats, dict) and "covered" in stats and "total" in stats:
            declared = (int(stats["covered"]), int(stats["total"]))
    return files, "json-summary", declared


def _parse_lcov(text: str) -> tuple[dict[str, tuple[int, int]], str]:
    files: dict[str, tuple[int, int]] = {}
    current: str | None = None
    hit = total = 0
    for line in text.splitlines():
        if line.startswith("SF:"):
            current = line[3:].strip()
            hit = total = 0
        elif line.startswith("DA:") and current is not None:
            _, _, payload = line.partition(":")
            parts = payload.split(",")
            if len(parts) >= 2:
                total += 1
                try:
                    if int(parts[1]) > 0:
                        hit += 1
                except ValueError:
                    pass
        elif line.startswith("end_of_record") and current is not None:
            files[current] = (hit, total)
            current = None
    return files, "lcov"


def _parse_cobertura(text: str, path: Path) -> tuple[dict[str, tuple[int, int]], str]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise ReportError(REASON_TRUNCATED_REPORT, f"{path.name} is malformed XML ({exc})")
    files: dict[str, tuple[int, int]] = {}
    for klass in root.iter("class"):
        filename = klass.get("filename")
        if not filename:
            continue
        hit = total = 0
        for line in klass.iter("line"):
            total += 1
            try:
                if int(line.get("hits", "0")) > 0:
                    hit += 1
            except ValueError:
                pass
        if total:
            files[filename] = (hit, total)
    if not files:
        raise ReportError(
            REASON_UNKNOWN_REPORT_FORMAT, f"{path.name} has no class records"
        )
    return files, "cobertura-xml"


def _match_file(files: dict[str, tuple[int, int]], wanted: str) -> tuple[int, int] | None:
    """Coverage reports name files absolutely, relatively, or with a
    `<rootDir>` prefix. Match on a path suffix so the caller can pass the
    repo-relative path it already has."""
    if wanted in files:
        return files[wanted]
    normalized = wanted.lstrip("./")
    for key, value in files.items():
        candidate = key.replace("\\", "/").lstrip("./")
        if candidate == normalized or candidate.endswith("/" + normalized):
            return value
    return None


# --- Result assembly ---------------------------------------------------------

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


def _emit(project: Path, findings: list[dict[str, Any]],
          unverifiable: list[dict[str, Any]], inspected: dict[str, Any],
          extra: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    findings.sort(key=lambda f: (f["file"] or "", f["line"] or 0, f["code"]))
    blocking = [f for f in findings if f["severity"] == "blocking"]

    # The vacuous-pass guard: "0 findings" and "0 things inspected" must not
    # read the same.
    if not inspected["files"] and not any(
        e["reason"] == REASON_NOTHING_INSPECTED for e in unverifiable
    ):
        unverifiable.append({
            "code": "unsupported_stack",
            "reason": REASON_NOTHING_INSPECTED,
            "detail": "nothing was examined",
        })

    if blocking:
        verdict = "fail"
    elif unverifiable:
        verdict = "unverifiable"
    else:
        verdict = "pass"

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "verdict": verdict,
        "project": str(project),
        "findings": findings,
        "inspected": inspected,
        "unverifiable": sorted(
            unverifiable, key=lambda e: (e["code"], e["reason"], e["detail"])
        ),
    }
    if extra:
        result.update(extra)
    return (1 if blocking else 0), result


# --- authenticity ------------------------------------------------------------

def authenticity(project: Path, tests: list[Path] | None) -> tuple[int, dict[str, Any]]:
    if not project.is_dir():
        raise UsageError(f"project root not found or not a directory: {project}")
    project = project.resolve()

    candidates = [Path(t).resolve() for t in tests] if tests else discover_tests(project)
    aliases = load_aliases(project)
    ignore_patterns = load_test_ignore_patterns(project)

    findings: list[dict[str, Any]] = []
    unverifiable: list[dict[str, Any]] = []
    unparsed: list[str] = []
    examined = 0
    out_of_scope = 0

    for test_file in sorted(candidates):
        try:
            relative = str(test_file.relative_to(project))
        except ValueError:
            relative = str(test_file)

        # The project's own runner already decides what counts as a unit test.
        if is_ignored_by_project(relative, ignore_patterns):
            out_of_scope += 1
            continue

        try:
            text = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unparsed.append(relative)
            findings.append(_finding(
                "could_not_parse", file=relative, line=None,
                detail=f"{relative} could not be read as UTF-8; excluded from the verdict",
            ))
            unverifiable.append({
                "code": "test_imports_no_source",
                "reason": REASON_COULD_NOT_PARSE,
                "detail": relative,
            })
            continue

        if is_e2e_test(text):
            out_of_scope += 1
            continue

        examined += 1
        if imports_project_source(text, test_file, project, aliases):
            continue
        findings.append(_finding(
            "test_imports_no_source", file=relative, line=None,
            detail=f"{relative} resolves zero module specifiers into project source — "
                   f"it cannot fail when the code it claims to test changes",
            measured="0 project-source imports",
        ))

    inspected = {
        "files": examined,
        "method": "whole-file module-specifier extraction",
        "unparsed": sorted(unparsed),
        "out_of_scope": out_of_scope,
    }
    return _emit(project, findings, unverifiable, inspected)


# --- coverage ----------------------------------------------------------------

def coverage(project: Path, report: Path | None, new_files: list[str] | None,
             threshold: float, prior: Path | None) -> tuple[int, dict[str, Any]]:
    """Re-derive coverage from the tooling's own output.

    There is deliberately no parameter through which a caller can supply a
    claimed verdict. AC-3.1 requires this subcommand's answer to be
    independent of any `Coverage threshold met` value an agent typed, and the
    cheapest way to guarantee that is to make the claim unrepresentable.
    """
    if not project.is_dir():
        raise UsageError(f"project root not found or not a directory: {project}")
    project = project.resolve()

    findings: list[dict[str, Any]] = []
    unverifiable: list[dict[str, Any]] = []

    resolved_report = report
    if resolved_report is None:
        for candidate in COVERAGE_REPORT_CANDIDATES:
            if (project / candidate).is_file():
                resolved_report = project / candidate
                break

    if resolved_report is None or not resolved_report.is_file():
        findings.append(_finding(
            "coverage_report_absent", file=None, line=None,
            detail=f"no machine-readable coverage report found under {project}",
        ))
        unverifiable.append({
            "code": "coverage_below_threshold",
            "reason": REASON_NO_COVERAGE_REPORT,
            "detail": "no coverage report to re-derive from",
        })
        return _emit(project, findings, unverifiable,
                     {"files": 0, "method": "none", "unparsed": []})

    try:
        files, method, declared_total = parse_coverage_report(resolved_report)
    except ReportError as exc:
        unverifiable.append({
            "code": "coverage_below_threshold",
            "reason": exc.reason,
            "detail": exc.detail,
        })
        return _emit(project, findings, unverifiable, {
            "files": 0, "method": "unrecognized",
            "unparsed": [resolved_report.name],
        })

    if declared_total is not None:
        total_covered, total_lines = declared_total
    else:
        total_covered = sum(covered for covered, _ in files.values())
        total_lines = sum(total for _, total in files.values())
    overall = (100.0 * total_covered / total_lines) if total_lines else 0.0

    for wanted in sorted(new_files or []):
        record = _match_file(files, wanted)
        if record is None:
            # A new file the report never measured is not a passing file.
            unverifiable.append({
                "code": "coverage_below_threshold",
                "reason": REASON_NO_COVERAGE_REPORT,
                "detail": f"{wanted} does not appear in the coverage report",
            })
            continue
        covered, total = record
        pct = (100.0 * covered / total) if total else 0.0
        if pct < threshold:
            findings.append(_finding(
                "coverage_below_threshold", file=wanted, line=None,
                detail=f"{wanted} measured {pct:.1f}% line coverage against a "
                       f"{threshold:.0f}% bar",
                measured=f"{pct:.1f}%",
            ))

    if prior is not None and prior.is_file():
        try:
            prior_files, _, _ = parse_coverage_report(prior)
        except ReportError:
            prior_files = {}
        for key, (covered, total) in sorted(files.items()):
            before = _match_file(prior_files, key)
            if before is None or not total or not before[1]:
                continue
            now_pct = 100.0 * covered / total
            was_pct = 100.0 * before[0] / before[1]
            if now_pct < was_pct - 0.05:
                findings.append(_finding(
                    "coverage_regression", file=key, line=None,
                    detail=f"{key} fell from {was_pct:.1f}% to {now_pct:.1f}%",
                    measured=f"{now_pct:.1f}% (was {was_pct:.1f}%)",
                ))

    # Re-deriving the aggregate is not the same as judging anything. With no
    # new files and no prior report, this run compared zero files against the
    # bar -- and reporting `pass` while measuring 57% against an 80% threshold
    # is the clean-report failure mode this whole spec exists to end.
    if not new_files and prior is None:
        unverifiable.append({
            "code": "coverage_below_threshold",
            "reason": REASON_NOTHING_INSPECTED,
            "detail": f"no files were judged against the {threshold:.0f}% bar; "
                      f"the suite measures {overall:.1f}% overall. Pass --new-files "
                      f"to judge a story's files, or --prior to check for regression",
        })

    inspected = {
        "files": len(files),
        "method": f"{method} @ {resolved_report.name}",
        "unparsed": [],
    }
    extra = {
        "measured": {
            "statements_pct": round(overall, 4),
            "covered_lines": total_covered,
            "total_lines": total_lines,
            "threshold": threshold,
            "report": str(resolved_report),
        }
    }
    return _emit(project, findings, unverifiable, inspected, extra)


# --- CLI ---------------------------------------------------------------------

def run_coverage(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    return coverage(args.project, args.report, args.new_files, args.threshold, args.prior)


def run_authenticity(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    return authenticity(args.project, args.tests)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    c = sub.add_parser("coverage", help="re-derive coverage from the tool's own output")
    c.add_argument("--project", default=Path("."), type=Path)
    c.add_argument("--report", default=None, type=Path)
    c.add_argument("--new-files", nargs="*", default=None)
    c.add_argument("--threshold", default=80.0, type=float)
    c.add_argument("--prior", default=None, type=Path)
    c.set_defaults(func=run_coverage)

    a = sub.add_parser("authenticity", help="flag tests that import no project source")
    a.add_argument("--project", default=Path("."), type=Path)
    a.add_argument("--tests", nargs="*", default=None, type=Path)
    a.set_defaults(func=run_authenticity)

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
