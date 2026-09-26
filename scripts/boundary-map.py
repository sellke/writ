#!/usr/bin/env python3
"""Gate 0.5 boundary map (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Checkable artifact for `skills/boundary-map-computation/SKILL.md`: extract
owned paths from a story's Implementation Tasks and, when an assess-spec
Check 5 overlap table is supplied, merge shared paths. Overlap-absent
degrades to owned = named paths, readable = [], out_of_scope = [].

Subcommands:
  compute --story PATH --repo . [--overlap PATH]
  crossings --map PATH --changed FILE... [--story PATH] [--surface CLASS] [--repo .]

compute prints JSON `{owned, readable, out_of_scope}` only. Writes nothing.
Exit 0: well-formed map. Exit 1: malformed story. Exit 2: usage.

crossings (Story 1 of `2026-09-26-drift-arch-guards`) classifies each
changed file against a saved compute map and names the Gate 3 agent.
Paths are normalized repo-relative; classification order is excluded
(the story's spec folder, `.writ/context.md`, `.writ/state/`) → owned →
out_of_scope → readable_modified → outside_boundary. Output is a verdict
line (`pass` | `unverifiable`), `route: evaluator-agent|review-agent`,
one `reason:` line per crossing in input order then `full_stack_surface`
when `--surface full-stack`, and the summary line last. A missing,
unreadable, or non-object map is `unverifiable` / `map_unreadable`.
Crossings are a routing signal, never `fail`: exit 0 whenever it ran,
exit 2 when `--changed` is omitted or empty.
"""

from __future__ import annotations

import argparse
import subprocess
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple


TASK_HEADING = re.compile(r"^## Implementation Tasks\s*$", re.MULTILINE)
NEXT_H2 = re.compile(r"^## ", re.MULTILINE)
BACKTICK = re.compile(r"`([^`]+)`")
AC_ID = re.compile(r"^AC-\d+(?:\.\d+)*$", re.IGNORECASE)
FILENAME = re.compile(r"^[\w.-]+\.[A-Za-z][A-Za-z0-9]{0,9}$")
NUMERIC = re.compile(r"^\d+\.\d+$")
TABLE_SEP = re.compile(r"^[\s|:-]+$")


class UsageError(Exception):
    """Exit-2 conditions."""


class StoryError(Exception):
    """Exit-1: story file exists but is not a well-formed story."""


# Surrounding punctuation stripped from a token. The leading side never
# strips `.` so dot-directories (`.writ/`, `.github/`) survive intact.
_EDGE_PUNCT = ",;:()[]{}\"'"
LINE_SUFFIX = re.compile(r":\d+(?:\s*[-\u2013\u2014]\s*\d+)?$")
BAD_CHARS = re.compile(r"[<>{}|=$*?!@#%^&+,;\\\u2026]")
NUMERIC_SEGMENT = re.compile(r"^\d+$")


def normalize_path(token: str) -> str:
    """Trim punctuation, `:line` / `:a-b` suffixes, and `./` prefixes.

    Leading dots that belong to the path (`.writ/`, `.github/`) are kept.
    """
    token = token.strip().lstrip(_EDGE_PUNCT).rstrip(_EDGE_PUNCT + ".")
    token = LINE_SUFFIX.sub("", token)
    if "::" in token:  # `path::symbol` names a symbol in that file
        token = token.split("::", 1)[0]
    while token.startswith("./"):
        token = token[2:]
    return token


def looks_like_path(token: str) -> bool:
    """True when the token is a plausible repo-relative path.

    Rejects URLs, AC ids, slash commands / absolute paths, tokens with
    whitespace or template/shell characters, and slash tokens whose
    segments are numbers (`70/219/231`).
    """
    token = normalize_path(token)
    if not token or any(ch.isspace() for ch in token):
        return False
    if "://" in token:
        return False
    if AC_ID.fullmatch(token):
        return False
    if token.startswith("/") or token.startswith("~") or token.startswith("-"):
        return False
    if BAD_CHARS.search(token) or ".." in token.split("/"):
        return False
    if "/" in token:
        segments = [seg for seg in token.split("/") if seg]
        if not segments:
            return False
        if any(NUMERIC_SEGMENT.fullmatch(seg) for seg in segments):
            return False
        return True
    if FILENAME.fullmatch(token) and not NUMERIC.fullmatch(token):
        return True
    return False


def extract_paths(text: str) -> List[str]:
    """Backticked plausible paths, in order, deduplicated.

    A bare filename is dropped when a fuller path with the same basename
    was also named (`test_x.py` beside `scripts/tests/test_x.py`).
    """
    found: List[str] = []
    seen: Set[str] = set()
    for match in BACKTICK.finditer(text):
        raw = normalize_path(match.group(1))
        if looks_like_path(raw) and raw not in seen:
            seen.add(raw)
            found.append(raw)
    basenames = {p.rstrip("/").rsplit("/", 1)[-1] for p in found if "/" in p}
    return [p for p in found if "/" in p or p not in basenames]


def implementation_tasks(text: str) -> Optional[str]:
    match = TASK_HEADING.search(text)
    if match is None:
        return None
    rest = text[match.end():]
    nxt = NEXT_H2.search(rest)
    return rest[: nxt.start()] if nxt else rest


def owned_from_story(text: str) -> List[str]:
    section = implementation_tasks(text)
    if section is None:
        raise StoryError("missing Implementation Tasks")
    return extract_paths(section)


def _table_cells(line: str) -> List[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_overlap(text: str) -> List[Tuple[str, bool]]:
    """Read Check 5 overlap rows: (path, high_overlap).

    Accepts the persisted table from `## Check 5 — File overlap` (skill
    Persistence) or a bare table / bullet list of shared paths.
    """
    rows: List[Tuple[str, bool]] = []
    seen: Set[str] = set()

    def add(path: str, warn: bool) -> None:
        path = normalize_path(path)
        if not looks_like_path(path) or path in seen:
            return
        seen.add(path)
        rows.append((path, warn))

    for line in text.splitlines():
        cells = _table_cells(line)
        if cells:
            if TABLE_SEP.fullmatch(re.sub(r"\|", "", line.strip())):
                continue
            head = cells[0].lower()
            if "file" in head and "area" in head:
                continue
            if head in ("signal", "file / area", "file/area"):
                continue
            severity = cells[-1].lower() if len(cells) > 1 else ""
            warn = (
                "warn" in severity
                or "⚠️" in severity
                or "three+" in severity
                or "3+" in severity
            )
            for path in extract_paths(cells[0]) or (
                [cells[0]] if looks_like_path(cells[0]) else []
            ):
                add(path, warn)
            continue
        stripped = line.lstrip()
        if stripped.startswith(("-", "*")):
            warn = "warn" in line.lower() or "⚠️" in line
            for path in extract_paths(line):
                add(path, warn)
    return rows


def merge_overlap(owned: Sequence[str], overlap: Sequence[Tuple[str, bool]]) -> Tuple[List[str], List[str]]:
    """Skill step 5: shared paths not explicitly OWNED become Readable.

    High-overlap (warn / three+ stories / ⚠️) stays on the same list —
    Owned if tasks named the path, otherwise Readable. out_of_scope stays
    implicit (empty list); the skill forbids enumerating the tree.
    """
    owned_set = set(owned)
    readable: List[str] = []
    seen_readable: Set[str] = set()
    for path, _warn in overlap:
        if path in owned_set:
            continue
        if path not in seen_readable:
            seen_readable.add(path)
            readable.append(path)
    return list(owned), readable


def load_story(path: Path) -> str:
    if not path.is_file():
        raise StoryError("story is not a readable file")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise StoryError("story is not a readable file") from exc
    if not text.strip():
        raise StoryError("story is empty")
    return text


def _under_repo(repo: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo / path


def _spec_dir(story: Path) -> Optional[Path]:
    for folder in story.resolve().parents:
        if (folder / "user-stories").is_dir():
            return folder
    return None


def _tracked_files(repo: Path) -> List[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "ls-files"],
            capture_output=True, text=True,
        )
    except OSError:
        return []
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def resolve_spec_relative(paths: Sequence[str], story: Path, repo: Path) -> List[str]:
    """Rewrite spec-relative paths (`sub-specs/x.md`) to repo-relative.

    Only when the path is missing under the repo but present under the
    story's spec folder. New files the story will create stay as named.
    """
    spec = _spec_dir(story)
    if spec is None:
        return list(paths)
    try:
        repo_r = repo.resolve()
        spec_rel = spec.relative_to(repo_r)
    except (OSError, ValueError):
        return list(paths)
    tracked: Optional[List[str]] = None
    out: List[str] = []
    for path in paths:
        if not (repo_r / path).exists() and (spec / path).exists():
            path = (spec_rel / path).as_posix()
        elif "/" not in path and not (repo_r / path).exists():
            # A bare filename resolves when exactly one tracked file has it.
            if tracked is None:
                tracked = _tracked_files(repo_r)
            hits = [t for t in tracked if t.rsplit("/", 1)[-1] == path]
            if len(hits) == 1:
                path = hits[0]
        if path not in out:
            out.append(path)
    return out


def compute(story: Path, repo: Path, overlap: Optional[Path]) -> dict:
    if repo is None:
        raise UsageError("missing --repo")
    story = _under_repo(repo, story)
    if overlap is not None:
        overlap = _under_repo(repo, overlap)
    text = load_story(story)
    owned = resolve_spec_relative(owned_from_story(text), story, repo)
    readable: List[str] = []
    if overlap is not None:
        if not overlap.is_file():
            raise UsageError("overlap file is not readable: %s" % overlap)
        try:
            overlap_text = overlap.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise UsageError("overlap file is not readable: %s" % overlap) from exc
        readable_merged = merge_overlap(owned, parse_overlap(overlap_text))[1]
        readable = readable_merged
    return {
        "owned": owned,
        "readable": readable,
        "out_of_scope": [],
    }


MAP_KEYS = ("owned", "readable", "out_of_scope")
PIPELINE_OUTPUTS = (".writ/context.md", ".writ/state/")


def repo_relative(value: str, repo: Path) -> str:
    """Changed-file path as repo-relative posix; dot-directories kept.

    `Path` collapses `./` without touching a leading-dot directory. File
    names are taken verbatim (no `normalize_path` punctuation trimming):
    they come from git, not prose.
    """
    raw = Path(value.strip())
    if raw.is_absolute():
        # Unresolved first so a symlinked path (`.cursor/commands/x.md`)
        # keeps its own name; resolved second for `/var` → `/private/var`.
        for base, path in ((repo.absolute(), raw), (repo.resolve(), raw.resolve())):
            try:
                return path.relative_to(base).as_posix()
            except ValueError:
                continue
        return raw.as_posix()
    text = raw.as_posix()
    return "" if text == "." else text


def covers(entry: str, path: str) -> bool:
    """Entry equals the path, or is a directory (`dir` or `dir/`) above it."""
    entry = entry.rstrip("/")
    return bool(entry) and (path == entry or path.startswith(entry + "/"))


def load_map(path: Path) -> Optional[dict]:
    """Saved compute map, or None when missing / unreadable / malformed."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    lists = {}
    for key in MAP_KEYS:
        raw = payload.get(key, [])
        if not isinstance(raw, list) or not all(isinstance(e, str) for e in raw):
            return None
        lists[key] = [normalize_path(e) for e in raw]
    return lists


def excluded_prefixes(story: Optional[Path], repo: Path) -> List[str]:
    entries = list(PIPELINE_OUTPUTS)
    if story is None:
        return entries
    spec = _spec_dir(_under_repo(repo, story))
    if spec is not None:
        try:
            entries.append(spec.relative_to(repo.resolve()).as_posix() + "/")
        except (OSError, ValueError):
            pass
    return entries


def classify(path: str, boundary: dict, excluded: Sequence[str]) -> Optional[str]:
    """Crossing class for one changed path; None when not reported."""
    if any(covers(e, path) for e in excluded):
        return None
    if any(covers(e, path) for e in boundary["owned"]):
        return None
    if any(covers(e, path) for e in boundary["out_of_scope"]):
        return "out_of_scope"
    if any(covers(e, path) for e in boundary["readable"]):
        return "readable_modified"
    return "outside_boundary"


def crossings(
    map_path: Path,
    changed: Sequence[str],
    story: Optional[Path],
    surface: Optional[str],
    repo: Path,
) -> List[str]:
    """Report lines for `crossings`; raises UsageError on empty --changed."""
    paths: List[str] = []
    for value in changed:
        path = repo_relative(value, repo) if value.strip() else ""
        if path and path not in paths:
            paths.append(path)
    if not paths:
        raise UsageError("--changed needs at least one file")
    boundary = load_map(_under_repo(repo, map_path))
    if boundary is None:
        return [
            "unverifiable",
            "route: review-agent",
            "reason: map_unreadable",
            "boundary-map crossings: map unreadable (route review-agent)",
        ]
    excluded = excluded_prefixes(story, repo)
    reasons = []
    for path in paths:
        kind = classify(path, boundary, excluded)
        if kind is not None:
            reasons.append("%s %s" % (kind, path))
    count = len(reasons)
    if surface == "full-stack":
        reasons.append("full_stack_surface")
    route = "review-agent" if reasons else "evaluator-agent"
    return (
        ["pass", "route: %s" % route]
        + ["reason: %s" % r for r in reasons]
        + [
            "boundary-map crossings: %d crossing(s), surface %s (route %s)"
            % (count, surface or "none", route)
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("compute", help="emit JSON owned/readable/out_of_scope")
    p.add_argument("--story", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--overlap", type=Path, default=None)
    c = sub.add_parser("crossings", help="route Gate 3 from changed files vs a map")
    c.add_argument("--map", type=Path, required=True)
    c.add_argument("--changed", nargs="*", required=True)
    c.add_argument("--story", type=Path, default=None)
    c.add_argument("--surface", default=None)
    c.add_argument("--repo", type=Path, default=Path("."))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if args.action == "crossings":
        try:
            lines = crossings(args.map, args.changed, args.story, args.surface, args.repo)
        except UsageError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        print("\n".join(lines))
        return 0
    try:
        payload = compute(args.story, args.repo, args.overlap)
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except StoryError:
        return 1
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
