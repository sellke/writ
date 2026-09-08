#!/usr/bin/env python3
"""Gate 0.5 boundary map (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Checkable artifact for `skills/boundary-map-computation/SKILL.md`: extract
owned paths from a story's Implementation Tasks and, when an assess-spec
Check 5 overlap table is supplied, merge shared paths. Overlap-absent
degrades to owned = named paths, readable = [], out_of_scope = [].

Subcommand:
  compute --story PATH --repo . [--overlap PATH]

Prints JSON `{owned, readable, out_of_scope}` only. Writes nothing.

Exit 0: well-formed map.
Exit 1: malformed story.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
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


def looks_like_path(token: str) -> bool:
    token = token.strip().strip(".,;:()[]{}\"'")
    if not token or any(ch.isspace() for ch in token):
        return False
    if token.startswith("http://") or token.startswith("https://"):
        return False
    if AC_ID.fullmatch(token):
        return False
    if "/" in token:
        return True
    if FILENAME.fullmatch(token) and not NUMERIC.fullmatch(token):
        return True
    return False


def normalize_path(token: str) -> str:
    return token.strip().strip(".,;:()[]{}\"'")


def extract_paths(text: str) -> List[str]:
    found: List[str] = []
    seen: Set[str] = set()
    for match in BACKTICK.finditer(text):
        raw = normalize_path(match.group(1))
        if looks_like_path(raw) and raw not in seen:
            seen.add(raw)
            found.append(raw)
    return found


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


def compute(story: Path, repo: Path, overlap: Optional[Path]) -> dict:
    if repo is None:
        raise UsageError("missing --repo")
    story = _under_repo(repo, story)
    if overlap is not None:
        overlap = _under_repo(repo, overlap)
    text = load_story(story)
    owned = owned_from_story(text)
    readable: List[str] = []
    if overlap is not None:
        if not overlap.is_file():
            raise UsageError("overlap file is not readable")
        try:
            overlap_text = overlap.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise UsageError("overlap file is not readable") from exc
        readable_merged = merge_overlap(owned, parse_overlap(overlap_text))[1]
        readable = readable_merged
    return {
        "owned": owned,
        "readable": readable,
        "out_of_scope": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("compute", help="emit JSON owned/readable/out_of_scope")
    p.add_argument("--story", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--overlap", type=Path, default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    try:
        payload = compute(args.story, args.repo, args.overlap)
    except UsageError:
        return 2
    except StoryError:
        return 1
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
