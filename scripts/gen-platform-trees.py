#!/usr/bin/env python3
"""Generate the per-platform trees from source (spec `2026-10-22-generated-platform-trees`).

    python3 scripts/gen-platform-trees.py                  # write all identity targets in place
    python3 scripts/gen-platform-trees.py --check          # report stale|missing|orphan|unmapped|vendor|malformed; write nothing
    python3 scripts/gen-platform-trees.py coverage         # unmapped + vendor only
    python3 scripts/gen-platform-trees.py --target fixture --out-dir <dir>   # commands/ + skills/ with the fixture script root

Dev-only (it reads adapters/*.md and .writ/manifest.yaml, which installed
projects do not have); never hand-edit a generated file. Story 1 ships the
adapter tool-table parser and the vocabulary rule that the generators build
on; `main()` is a stub that prints `unverifiable` with one
`reason: not-implemented <mode>` line until Stories 2 to 4 add the writers,
`--check`, and `coverage`.

Check shape: line 1 `pass`/`fail`/`unverifiable`, `reason: <kind> <detail>`
lines, `wrote <path>` lines in write mode, then `gen-platform-trees:
<verdict> (<n> stale, <m> missing, <o> orphan, <u> unmapped, <v> vendor)`.
Exit 0 pass or unverifiable, 1 fail, 2 usage. Nothing is written when any
reason exists.

Parser (technical-spec.md -> ## Adapter Table Grammar). Each adapter has one
tool table: the first contiguous block of `|` lines under its HEADINGS
chain, each heading searched inside the previous one. A section ends at the
next heading of the same or a higher level; lines inside ``` fences are
never headings. The capability name is column 1's leading identifier
(`capability_name`); the mapping is column 2, or column 3 for cursor, whose
column 2 is a command list; the notes are the last column. Reasons, without
the `reason: ` prefix: `malformed adapters/<x>.md:<line>` for a row whose
cell count differs from the header's or whose first cell has no identifier
(verdict `fail`); `empty adapters/<x>.md` for a header with no body rows
(`fail`); `section <heading> in adapters/<x>.md` for a missing heading, and
`missing adapters/<x>.md` for an unreadable file (`unverifiable`).
`parse_adapter` never raises on bad input.

Vocabulary (technical-spec.md -> ## Vocabulary Rule): the neutral names are
the union of the tables' names in first-seen order; `unmapped` lists each
neutral name absent from a table that parsed; `vendor_only` is the set of
backticked identifiers in mapping cells minus the neutral names and
ALLOWLIST.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_DIR = ROOT / "adapters"
ADAPTERS = ("cursor", "claude-code", "codex", "openclaw")
# Heading chain to each adapter's tool table, innermost last.
HEADINGS = {
    "cursor": ("## Native Tool Availability",),
    "claude-code": ("## Tool Mapping (Cursor → Claude Code)", "### Quick Reference"),
    "codex": (
        "## Tool Mapping (Cursor → Codex CLI)",
        "### Quick reference — orchestration primitives",
    ),
    "openclaw": ("## Quick Reference",),
}  # type: Dict[str, Tuple[str, ...]]
# 0-based column of the mapping cell. Cursor's column 2 (`Used By`) is a
# command list, so its mapping is column 3 (`Purpose`); elsewhere column 2.
MAPPING_COLUMN = {"cursor": 2}
# Backticked tokens that are bare English verbs in Writ prose, not vendor
# tool names. Adding an entry needs a reason in the commit (spec.md ->
# Business Rules (Expanded), Rule 4).
ALLOWLIST = {
    "Read",   # "`Read` the story file": a bare verb in command prose
    "Write",  # "`Write` one file per draft": a bare verb in command prose
    "Bash",   # "run it via `Bash`": the shell named as a bare verb in command prose
}
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_ -]*")
HEADING_RE = re.compile(r"^(#{1,6}) \S")
SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
BACKTICK = re.compile(r"`([^`]+)`")
TOOL = "gen-platform-trees"


class Row(NamedTuple):
    name: str      # capability: the leading identifier of column 1
    variant: str   # column 1 with backticks stripped, e.g. Task({ readonly: true })
    mapping: str   # the platform's mapping cell
    notes: str     # the last cell
    line: int      # 1-based line in the adapter file


class AdapterTable(NamedTuple):
    adapter: str
    path: Path
    verdict: str          # pass | fail | unverifiable
    reasons: List[str]    # without the `reason: ` prefix
    rows: List[Row]

    @property
    def names(self) -> List[str]:
        """Capability names in row order, each once (variants collapse)."""
        return list(dict.fromkeys(row.name for row in self.rows))

    @property
    def rel(self) -> str:
        """The path the reasons name: `adapters/<basename>`."""
        return "adapters/" + self.path.name


def capability_name(cell: str) -> str:
    """Leading identifier of a first-column cell: backticks stripped, the run
    of `[A-Za-z_][A-Za-z0-9_ -]*` (it stops at `(`, `{`, `:`), right-trimmed.
    `` `Task({ readonly: true })` `` -> Task; `` `Plan Mode` `` -> Plan Mode;
    `` `readonly: true` `` -> readonly; no identifier -> ""."""
    match = NAME_RE.match(variant_text(cell))
    return match.group(0).rstrip() if match else ""


def variant_text(cell: str) -> str:
    return cell.replace("`", "").strip()


def cells(row: str) -> List[str]:
    """Cell texts of a markdown table row, splitting on unescaped pipes."""
    return [c.strip() for c in CELL_SPLIT.split(row.strip())[1:-1]]


def section(lines: List[str], headings: Tuple[str, ...]) -> Tuple[Optional[Tuple[int, int]], Optional[str]]:
    """Line span (start, end) of the body under a chain of headings, each
    searched inside the previous one, or (None, the heading not found)."""
    start, end = 0, len(lines)
    for heading in headings:
        level = len(heading) - len(heading.lstrip("#"))
        found = None
        in_fence = False
        for i in range(start, end):
            if lines[i].startswith("```"):
                in_fence = not in_fence
            elif not in_fence and lines[i].rstrip() == heading:
                found = i
                break
        if found is None:
            return None, heading
        stop = end
        in_fence = False
        for j in range(found + 1, end):
            if lines[j].startswith("```"):
                in_fence = not in_fence
                continue
            match = HEADING_RE.match(lines[j])
            if not in_fence and match and len(match.group(1)) <= level:
                stop = j
                break
        start, end = found + 1, stop
    return (start, end), None


def first_table(lines: List[str], start: int, end: int) -> List[Tuple[int, str]]:
    """(index, text) of the first contiguous block of `|` lines in the span;
    lines inside ``` fences do not count."""
    rows = []  # type: List[Tuple[int, str]]
    in_fence = False
    for i in range(start, end):
        if lines[i].startswith("```"):
            in_fence = not in_fence
        elif not in_fence and lines[i].startswith("|"):
            rows.append((i, lines[i]))
            continue
        if rows:
            break
    return rows


def parse_adapter(path: Path, adapter: Optional[str] = None) -> AdapterTable:
    """The adapter's tool table. `adapter` defaults to the file's stem, so a
    fixture named `codex.md` parses with the codex headings and its reasons
    name `adapters/codex.md`."""
    path = Path(path)
    adapter = adapter or path.stem
    rel = "adapters/" + path.name
    headings = HEADINGS.get(adapter)
    if headings is None:
        return AdapterTable(adapter, path, "unverifiable", ["adapter %s in %s" % (adapter, rel)], [])
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return AdapterTable(adapter, path, "unverifiable", ["missing %s" % rel], [])
    span, missing = section(lines, headings)
    if span is None:
        return AdapterTable(adapter, path, "unverifiable", ["section %s in %s" % (missing, rel)], [])
    table = first_table(lines, *span)
    if len(table) < 3:
        return AdapterTable(adapter, path, "fail", ["empty %s" % rel], [])

    width = len(cells(table[0][1]))
    reasons = []  # type: List[str]
    separator = table[1][1]
    if not SEPARATOR_RE.match(separator) or len(cells(separator)) != width:
        reasons.append("malformed %s:%d" % (rel, table[1][0] + 1))
    mapping_index = min(MAPPING_COLUMN.get(adapter, 1), max(width - 1, 0))
    rows = []  # type: List[Row]
    for index, text in table[2:]:
        cs = cells(text)
        name = capability_name(cs[0]) if cs else ""
        if len(cs) != width or not name:
            reasons.append("malformed %s:%d" % (rel, index + 1))
            continue
        rows.append(Row(name, variant_text(cs[0]), cs[mapping_index], cs[-1], index + 1))
    return AdapterTable(adapter, path, "fail" if reasons else "pass", reasons, rows)


def identifiers(cell: str) -> List[str]:
    """Backticked identifiers in a mapping cell, each reduced to its leading
    identifier. A token that is URL- or path-shaped (contains `://`, or
    starts with `.`, `/`, `@`, or `~`) is not an identifier."""
    out = []  # type: List[str]
    for token in BACKTICK.findall(cell):
        token = token.strip()
        if not token or "://" in token or token[0] in "./@~":
            continue
        name = capability_name(token)
        if name:
            out.append(name)
    return out


def vocabulary(tables: Iterable[AdapterTable]) -> Tuple[List[str], Set[str]]:
    """(neutral names in first-seen order across the tables, vendor-only
    identifiers from the mapping cells)."""
    tables = list(tables)
    neutral = list(dict.fromkeys(name for table in tables for name in table.names))
    found = set()  # type: Set[str]
    for table in tables:
        for row in table.rows:
            found.update(identifiers(row.mapping))
    return neutral, found - set(neutral) - ALLOWLIST


def unmapped(tables: Iterable[AdapterTable]) -> List[str]:
    """`unmapped <name> in adapters/<x>.md` for each neutral name absent from
    a table that parsed, neutral names in order, then table order. A table
    that did not parse already carries its own reason."""
    tables = list(tables)
    neutral, _ = vocabulary(tables)
    out = []  # type: List[str]
    for name in neutral:
        for table in tables:
            if table.verdict == "pass" and name not in table.names:
                out.append("unmapped %s in %s" % (name, table.rel))
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gen-platform-trees.py", allow_abbrev=False,
        description="Generate or check the per-platform trees from adapters/*.md, "
                    "system-instructions.md, and .writ/manifest.yaml. Dev-only; never shipped.")
    parser.add_argument("mode", nargs="?", choices=["coverage"],
                        help="coverage: run only the unmapped and vendor checks")
    parser.add_argument("--check", action="store_true",
                        help="report stale, missing, orphan, unmapped, vendor, and malformed; "
                             "write nothing; exit 0 pass or unverifiable, 1 fail")
    parser.add_argument("--target", metavar="NAME",
                        help="one target (cursor, claude-code, codex, fixture) instead of every identity target")
    parser.add_argument("--out-dir", metavar="DIR",
                        help="with a non-identity --target: the directory that receives <target>/commands and <target>/skills")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    mode = args.mode or ("check" if args.check else "write")
    print("unverifiable")
    print("reason: not-implemented %s" % mode)
    print("%s: unverifiable (story 1: parser only)" % TOOL)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
