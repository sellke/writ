#!/usr/bin/env python3
"""Read-only acceptance-criterion traceability checker (Story 2 of
`2026-08-13-acceptance-criteria-traceability-ids`).

Given one spec folder, decides deterministically whether every acceptance
criterion tagged per `.writ/docs/acceptance-criteria-ids.md` is covered by an
implementation task, and — once its story reads `Completed ✅` — by a test,
and whether every task/test citation resolves to a criterion that still
exists. This is the executable reference `/verify-spec` Check 3e/3f names;
the command file describes the contract, this script decides it, so a human
and an agent reach the same verdict.

This module is READ-ONLY: it never writes a file, and the only git
subcommands it invokes are `rev-parse` and `check-ignore` (the latter
batched via `--stdin`, never one subprocess call per file) — the same
read-only discipline `scripts/exit-criteria.py` documents about itself.

Subcommand:
  check --spec PATH [--repo .]

Prints exactly one JSON object to stdout, schema `ac-trace-check-v1`.
Exit 0: ran correctly, no blocking findings (informational `legacy_story`
        entries may still be present).
Exit 1: ran correctly, at least one blocking finding.
Exit 2: could not run correctly — usage error, missing `user-stories/`, or
        an unreadable/malformed story file. Never a silent skip that would
        report clean coverage for a story that was never actually read.

See `.writ/docs/acceptance-criteria-ids.md` for the grammar this implements
against, and this spec's `sub-specs/technical-spec.md` for the CLI/JSON
contract this module is bound to.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "ac-trace-check-v1"

# --- Grammar (verbatim from .writ/docs/acceptance-criteria-ids.md) --------

# The end-anchored tag. Verbatim from technical-spec.md's Parsing Contract —
# copied character for character, not re-derived.
TAG = re.compile(r"`\[((?:AC-\d+\.\d+)(?:,\s*AC-\d+\.\d+)*)\]`\s*$")

# A permissive "something tag-shaped is here" detector. It exists to tell a
# genuinely untagged line (no finding at all) apart from a line carrying a
# malformed tag -- the Error & Rescue Map's "Tag present but ID malformed"
# row (`AC-3`, `AC-x.1`, ...), which is a `marker_violation` naming the
# line, not a silent non-match. TAG is the strict grammar; this is
# deliberately looser so a malformed form cannot fall through unreported.
TAG_SHAPE = re.compile(r"`\[([^\]]*)\]`\s*$")

ID_RE = re.compile(r"^AC-(\d+)\.(\d+)$")

# Bare-token citation scan. Neither the grammar doc nor technical-spec.md
# gives a literal regex for the bare-token case (only the backticked TAG
# has one), so the token-boundary decision is made here and pinned by a
# test: a bare id abutting non-whitespace on either side ("AC-3.1x",
# "xAC-3.1") is not a standalone token and must not match.
BARE_ID = re.compile(r"(?<![\w-])AC-(\d+)\.(\d+)(?![\w-])")

MARKER_LINE = re.compile(r"^> \*\*AC IDs assigned through:\*\*\s*(.*?)\s*$")
STATUS_LINE = re.compile(r"^> \*\*Status:\*\*\s*(.+?)\s*$")
STORY_FILENAME = re.compile(r"^story-(\d+)-")
CRITERION_LINE = re.compile(r"^- \[[ xX]\]\s")
HEADING_LINE = re.compile(r"^##\s+\S")

SEVERITY: dict[str, str] = {
    "untasked_criterion": "blocking",
    "untested_criterion": "blocking",
    "dangling_reference": "blocking",
    "duplicate_id": "blocking",
    "marker_violation": "blocking",
    "partial_adoption": "blocking",
    "legacy_story": "informational",
}

# Test-shaped path patterns, verbatim from the grammar doc's "Test-shaped
# path patterns" section.
TEST_DIR_SEGMENTS = {"tests", "test", "spec", "__tests__"}
TEST_BASENAME_GLOBS = ("test_*", "*_test.*", "*.test.*", "*.spec.*")


class UsageError(Exception):
    """Exit-2 conditions: a bad `--spec` path, a spec folder with no
    `user-stories/`, or a story file that cannot be read or whose filename
    cannot be parsed. Raised instead of a silent skip, which would report
    clean coverage for a story that was never actually read
    (technical-spec.md Error & Rescue Map)."""


# --- Story-file parsing -----------------------------------------------------

def read_story_file(path: Path) -> str:
    """Read one story file as UTF-8 text. A permissions failure or invalid
    UTF-8 is `UsageError` naming the file — never a silent skip."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError(f"story file unreadable: {path} ({exc})") from exc


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    """Return the (start, end) 0-based half-open line range of the body of
    the first `## <heading>` section — end exclusive, EOF if there is no
    following `## ` heading. `None` if the heading is absent."""
    heading_re = re.compile(rf"^##\s+{re.escape(heading)}\s*$")
    start = None
    for i, line in enumerate(lines):
        if heading_re.match(line):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if HEADING_LINE.match(lines[j]):
            end = j
            break
    return start, end


def parse_story_file(path: Path) -> dict[str, Any]:
    """Parse one `story-N-*.md` file into its checkable shape: story number,
    raw status text, every marker-line match inside `## Acceptance
    Criteria`, and every checkbox line inside `## Acceptance Criteria` and
    `## Implementation Tasks` (1-based line numbers, for reporting)."""
    match = STORY_FILENAME.match(path.name)
    if not match:
        raise UsageError(f"unparseable story filename: {path.name}")
    number = int(match.group(1))

    text = read_story_file(path)
    lines = text.splitlines()

    status = None
    for line in lines[:15]:
        status_match = STATUS_LINE.match(line)
        if status_match:
            status = status_match.group(1)
            break

    marker_matches: list[tuple[int, str]] = []
    ac_lines: list[tuple[int, str]] = []
    ac_bounds = _section_bounds(lines, "Acceptance Criteria")
    if ac_bounds:
        start, end = ac_bounds
        for i in range(start, end):
            line = lines[i]
            marker_match = MARKER_LINE.match(line)
            if marker_match:
                marker_matches.append((i + 1, marker_match.group(1)))
                continue
            if CRITERION_LINE.match(line):
                ac_lines.append((i + 1, line))

    task_lines: list[tuple[int, str]] = []
    task_bounds = _section_bounds(lines, "Implementation Tasks")
    if task_bounds:
        start, end = task_bounds
        for i in range(start, end):
            line = lines[i]
            if CRITERION_LINE.match(line):
                task_lines.append((i + 1, line))

    return {
        "number": number,
        "path": path,
        "status": status,
        "marker_matches": marker_matches,
        "ac_lines": ac_lines,
        "task_lines": task_lines,
    }


def _is_completed(status: str | None) -> bool:
    return bool(status) and status.strip().startswith("Completed")


# --- Finding helpers ---------------------------------------------------------

def _finding(code: str, *, story: int, id_str: str | None, file: Path | str | None,
             line: int | None, detail: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": SEVERITY[code],
        "story": story,
        "id": id_str,
        "file": str(file) if file is not None else None,
        "line": line,
        "detail": detail,
    }


def _sort_key(finding: dict[str, Any]) -> tuple[int, int, str]:
    id_str = finding.get("id")
    ordinal = 0
    if id_str:
        id_match = ID_RE.match(id_str)
        if id_match:
            ordinal = int(id_match.group(2))
    return (finding.get("story") or 0, ordinal, finding["code"])


# --- Per-story analysis: definitions, marker, duplicates, adoption ---------

def _analyze_story(story: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, int]:
    """Analyze one parsed story's `## Acceptance Criteria` section: extract
    valid same-story definitions, and append `marker_violation`,
    `duplicate_id`, `partial_adoption`, and `legacy_story` findings directly
    onto `findings`. Returns {id: definition_line_no} for this story's valid
    (same-story) definitions only — a cross-story-tagged definition is
    reported and excluded, never silently re-homed."""
    number = story["number"]
    path = story["path"]
    total_count = len(story["ac_lines"])
    tagged_count = 0
    occurrences: dict[str, list[int]] = {}

    for line_no, line in story["ac_lines"]:
        tag_match = TAG.search(line)
        if tag_match:
            tagged_count += 1
            for id_str in (part.strip() for part in tag_match.group(1).split(",")):
                id_match = ID_RE.match(id_str)
                assert id_match is not None  # TAG's grammar already guarantees this shape
                id_story = int(id_match.group(1))
                if id_story != number:
                    findings.append(_finding(
                        "marker_violation", story=number, id_str=id_str, file=path, line=line_no,
                        detail=f"definition tag {id_str} names story {id_story}, but this file "
                               f"is story {number} — reported, not silently re-homed",
                    ))
                    continue
                occurrences.setdefault(id_str, []).append(line_no)
            continue

        shape_match = TAG_SHAPE.search(line)
        if shape_match:
            tagged_count += 1
            findings.append(_finding(
                "marker_violation", story=number, id_str=None, file=path, line=line_no,
                detail=f"malformed criterion tag `[{shape_match.group(1)}]`",
            ))

    for id_str, id_lines in occurrences.items():
        if len(id_lines) > 1:
            findings.append(_finding(
                "duplicate_id", story=number, id_str=id_str, file=path, line=id_lines[0],
                detail=f"{id_str} defined on lines {', '.join(str(n) for n in id_lines)}",
            ))

    marker_ordinal = _validate_marker(story, tagged_count, findings)
    if marker_ordinal is not None:
        for id_str in occurrences:
            id_match = ID_RE.match(id_str)
            assert id_match is not None
            ordinal = int(id_match.group(2))
            if ordinal > marker_ordinal:
                findings.append(_finding(
                    "marker_violation", story=number, id_str=id_str, file=path,
                    line=occurrences[id_str][0],
                    detail=f"{id_str} exceeds the marker (AC-{number}.{marker_ordinal})",
                ))

    if total_count > 0:
        if tagged_count == 0:
            findings.append(_finding(
                "legacy_story", story=number, id_str=None, file=path, line=None,
                detail="zero criteria in this story carry an ID",
            ))
        elif tagged_count < total_count:
            findings.append(_finding(
                "partial_adoption", story=number, id_str=None, file=path, line=None,
                detail=f"{tagged_count}/{total_count} criteria in this story carry an ID",
            ))

    return {id_str: id_lines[0] for id_str, id_lines in occurrences.items()}


def _validate_marker(story: dict[str, Any], tagged_count: int,
                      findings: list[dict[str, Any]]) -> int | None:
    """Validate this story's high-water-mark marker. Returns the marker's
    ordinal if it parses cleanly and names this story, else `None`. Absent
    marker with zero tagged criteria is `legacy_story` territory, not a
    violation — every other absent/malformed/duplicated shape is."""
    number = story["number"]
    path = story["path"]
    markers = story["marker_matches"]

    if len(markers) > 1:
        findings.append(_finding(
            "marker_violation", story=number, id_str=None, file=path, line=markers[0][0],
            detail=f"{len(markers)} marker lines found; exactly one is allowed",
        ))
        return None

    if len(markers) == 0:
        if tagged_count > 0:
            findings.append(_finding(
                "marker_violation", story=number, id_str=None, file=path, line=None,
                detail="marker missing while criterion IDs are present",
            ))
        return None

    marker_line_no, marker_value = markers[0]
    marker_match = ID_RE.match(marker_value)
    if not marker_match:
        findings.append(_finding(
            "marker_violation", story=number, id_str=None, file=path, line=marker_line_no,
            detail=f"malformed marker value {marker_value!r}",
        ))
        return None

    marker_story = int(marker_match.group(1))
    if marker_story != number:
        findings.append(_finding(
            "marker_violation", story=number, id_str=None, file=path, line=marker_line_no,
            detail=f"marker names story {marker_story}, but this file is story {number}",
        ))
        return None

    return int(marker_match.group(2))


def _task_citations(story: dict[str, Any]) -> dict[str, int]:
    """{id: first citing line_no} for this story's `## Implementation
    Tasks` section — `TAG` match only, non-anchored ID tokens are prose."""
    cites: dict[str, int] = {}
    for line_no, line in story["task_lines"]:
        tag_match = TAG.search(line)
        if not tag_match:
            continue
        for id_str in (part.strip() for part in tag_match.group(1).split(",")):
            cites.setdefault(id_str, line_no)
    return cites


# --- Citation scan outside .writ/ -------------------------------------------

def _is_git_worktree(repo: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _git_ignored_set(repo: Path, rel_paths: list[str]) -> set[str]:
    """The subset of `rel_paths` git-ignores, via one batched
    `git check-ignore --stdin -v` call — never one subprocess per file,
    per the spec's explicit performance requirement for a checker meant to
    run inside `/verify-spec`."""
    if not rel_paths:
        return set()
    proc = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "--stdin", "-v"],
        input="\n".join(rel_paths) + "\n",
        capture_output=True, text=True,
    )
    ignored: set[str] = set()
    for line in proc.stdout.splitlines():
        if "\t" in line:
            ignored.add(line.rsplit("\t", 1)[1])
    return ignored


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(2048)
    except OSError:
        return True
    return b"\x00" in chunk


def _is_test_shaped(rel_path: Path) -> bool:
    for part in rel_path.parts[:-1]:
        if part in TEST_DIR_SEGMENTS:
            return True
    basename = rel_path.name
    return any(fnmatch.fnmatch(basename, pattern) for pattern in TEST_BASENAME_GLOBS)


def _under_repo(path: Path, repo: Path) -> bool:
    return path == repo or repo in path.parents


def _walk_candidates(repo: Path) -> list[Path]:
    """Enumerate candidate files for the citation scan.

    Skips `.git/` and `.writ/` at any depth, skips a nested git worktree's
    subtree (recognized by a `.git` entry that is a *file*, not a
    directory — unlike a normal repo root — containing a `gitdir:`
    pointer), and does not follow a symlink that leaves the repo. This is
    the walk only; the git-ignore filter is a separate batched pass.
    """
    candidates: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo, followlinks=False):
        dirpath_p = Path(dirpath)
        keep_dirs = []
        for name in dirnames:
            child = dirpath_p / name
            if name in (".git", ".writ"):
                continue
            if child.is_symlink():
                try:
                    resolved = child.resolve()
                except OSError:
                    continue
                if not _under_repo(resolved, repo):
                    continue
            if (child / ".git").is_file():
                # Nested worktree boundary: do not descend.
                continue
            keep_dirs.append(name)
        dirnames[:] = keep_dirs

        for name in filenames:
            file_path = dirpath_p / name
            if file_path.is_symlink():
                try:
                    resolved = file_path.resolve()
                except OSError:
                    continue
                if not _under_repo(resolved, repo):
                    continue
            candidates.append(file_path)
    return candidates


def scan_repo_citations(repo: Path) -> dict[str, Any]:
    """Scan the repo outside `.writ/` for bare `AC-<n>.<m>` tokens,
    classifying each occurrence's containing file as test-shaped (a test
    citation, which satisfies coverage) or not (an informational source
    citation, which never does). Reports `scanned_files` and
    `ignore_filter` so a pathological or degraded scan is visible rather
    than silently narrowed."""
    repo = repo.resolve()
    candidates = _walk_candidates(repo)

    ignore_filter = _is_git_worktree(repo)
    if ignore_filter:
        rel_paths = [str(path.relative_to(repo)) for path in candidates]
        ignored = _git_ignored_set(repo, rel_paths)
        candidates = [
            path for path in candidates
            if str(path.relative_to(repo)) not in ignored
        ]

    test_citations: dict[str, list[dict[str, Any]]] = {}
    source_citations: dict[str, list[dict[str, Any]]] = {}
    scanned_files = 0

    for path in sorted(candidates):
        if _is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned_files += 1

        rel = path.relative_to(repo)
        bucket = test_citations if _is_test_shaped(rel) else source_citations
        for line_no, line in enumerate(text.splitlines(), start=1):
            for token_match in BARE_ID.finditer(line):
                id_str = f"AC-{token_match.group(1)}.{token_match.group(2)}"
                bucket.setdefault(id_str, []).append({"file": str(rel), "line": line_no})

    return {
        "test_citations": test_citations,
        "source_citations": source_citations,
        "scanned_files": scanned_files,
        "ignore_filter": ignore_filter,
    }


# --- Coverage / dangling-reference pass -------------------------------------

def _first_location(locations: list[dict[str, Any]]) -> dict[str, Any]:
    return min(locations, key=lambda entry: (entry["file"], entry["line"]))


def _coverage_findings(
    definitions: dict[str, dict[str, Any]],
    task_citations: dict[str, list[dict[str, Any]]],
    test_citations: dict[str, list[dict[str, Any]]],
    stories_by_number: dict[int, dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    for id_str, info in definitions.items():
        if id_str not in task_citations:
            findings.append(_finding(
                "untasked_criterion", story=info["story"], id_str=id_str,
                file=info["file"], line=info["line"],
                detail=f"{id_str} is defined but no implementation task in the spec cites it",
            ))
            continue

        story = stories_by_number.get(info["story"])
        if story is not None and _is_completed(story["status"]) and id_str not in test_citations:
            findings.append(_finding(
                "untested_criterion", story=info["story"], id_str=id_str,
                file=info["file"], line=info["line"],
                detail=(
                    f"{id_str} is tasked but has no test citation, and its story reads "
                    f"Completed"
                ),
            ))

    for id_str in sorted(set(task_citations) | set(test_citations)):
        if id_str in definitions:
            continue
        id_match = ID_RE.match(id_str)
        story_number = int(id_match.group(1)) if id_match else 0
        locations = list(task_citations.get(id_str, [])) + list(test_citations.get(id_str, []))
        first = _first_location(locations)
        source_kind = "a task" if id_str in task_citations else "a test"
        both = id_str in task_citations and id_str in test_citations
        findings.append(_finding(
            "dangling_reference", story=story_number, id_str=id_str,
            file=first["file"], line=first["line"],
            detail=(
                f"{id_str} is cited by {'both a task and a test' if both else source_kind} "
                f"but no criterion in the spec defines it"
            ),
        ))


# --- Top-level check ---------------------------------------------------------

def check(spec_dir: Path, repo: Path) -> tuple[int, dict[str, Any]]:
    if not spec_dir.is_dir():
        raise UsageError(f"spec folder not found: {spec_dir}")
    story_dir = spec_dir / "user-stories"
    if not story_dir.is_dir():
        raise UsageError(f"no user-stories/ directory under {spec_dir}")
    story_files = sorted(story_dir.glob("story-*.md"))
    if not story_files:
        raise UsageError(f"no story files found under {story_dir}")

    stories = [parse_story_file(path) for path in story_files]
    stories_by_number = {story["number"]: story for story in stories}

    findings: list[dict[str, Any]] = []
    definitions: dict[str, dict[str, Any]] = {}
    for story in stories:
        local_defs = _analyze_story(story, findings)
        for id_str, line_no in local_defs.items():
            if id_str in definitions:
                findings.append(_finding(
                    "duplicate_id", story=story["number"], id_str=id_str,
                    file=story["path"], line=line_no,
                    detail=f"{id_str} already defined in {definitions[id_str]['file']}",
                ))
                continue
            definitions[id_str] = {
                "story": story["number"], "file": story["path"], "line": line_no,
            }

    task_citations: dict[str, list[dict[str, Any]]] = {}
    for story in stories:
        for id_str, line_no in _task_citations(story).items():
            task_citations.setdefault(id_str, []).append(
                {"file": str(story["path"]), "line": line_no}
            )

    scan = scan_repo_citations(repo)

    _coverage_findings(definitions, task_citations, scan["test_citations"],
                        stories_by_number, findings)

    findings.sort(key=_sort_key)
    blocking = any(f["severity"] == "blocking" for f in findings)

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "spec": str(spec_dir),
        "findings": findings,
        "scanned_files": scan["scanned_files"],
        "ignore_filter": scan["ignore_filter"],
    }
    return (1 if blocking else 0), result


def run_check(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    return check(args.spec, args.repo)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("check", help="check one spec folder's acceptance-criterion traceability")
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--repo", default=Path("."), type=Path)
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
