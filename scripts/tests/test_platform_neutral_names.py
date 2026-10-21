#!/usr/bin/env python3
"""Static checks for spec `2026-10-20-platform-neutral-names`.

Canvas section (Story 1):

- `commands/prototype.md` names the `canvas-preview` capability in Step 2 and
  Step 2.5, keeps the three-row render table and "Never degrade silently.",
  and names no vendor tool.
- Each of the four adapters has exactly one `canvas-preview` row in its tool
  table. The row maps the capability to the platform's tool and ends with the
  degradation clause.
- The Cursor tool name appears only in `adapters/cursor.md` and in record
  paths.

RECORD_PREFIXES and DATED_SNAPSHOTS come from technical-spec.md → Reference
Gate → Record list. Story 3's reference gate reuses them.

Covers AC-1.1, AC-1.2, AC-1.3, AC-1.4, and AC-1.5.

Run: uv run --python 3.9 pytest scripts/tests/test_platform_neutral_names.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

RECORD_PREFIXES = (
    "CHANGELOG.md",
    ".writ/specs/archive/",
    ".writ/research/",
    ".writ/decision-records/",
    ".writ/product/",
    ".writ/decision-log.md",
    ".writ/issues/",
    ".writ/specs/2026-10-20-platform-neutral-names/",  # this spec describes the rename
    ".writ/specs/2026-10-20-claude-code-parity/",  # its technical spec cites the rename as a generator edge case
)
DATED_SNAPSHOTS = {
    ".writ/docs/leanness-audit-2026-07-11.md": "dated leanness audit",
    ".writ/docs/swot-2026-03-01.md": "dated SWOT analysis",
    ".writ/explanations/2026-03-20-WritPipelineArchitecture .md": "dated pipeline explanation",
}

CAPABILITY = "canvas-preview"
# Built from two parts so this file is not a hit for its own grep.
CURSOR_TOOL = "cursor-ide" + "-browser"
CANVAS_ROW_PREFIX = "| `canvas-preview` |"
DEGRADATION_CLAUSE = (
    "No renderer: write a structural description of each draft "
    "and say the drafts were not rendered."
)
PROTOTYPES_DIR = ".writ/prototypes/<date>-<slug>/"

# (adapter, heading chain to the tool table, keywords the row must contain)
ADAPTER_TABLES = [
    ("adapters/cursor.md", ("## Native Tool Availability",), (CURSOR_TOOL,)),
    (
        "adapters/claude-code.md",
        ("## Tool Mapping (Cursor → Claude Code)", "### Quick Reference"),
        ("artifact", "preview pane"),
    ),
    (
        "adapters/codex.md",
        (
            "## Tool Mapping (Cursor → Codex CLI)",
            "### Quick reference — orchestration primitives",
        ),
        (PROTOTYPES_DIR, "HTML"),
    ),
    ("adapters/openclaw.md", ("## Quick Reference",), (PROTOTYPES_DIR, "HTML")),
]

HEADING = re.compile(r"^(#{1,6}) \S")


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def section(text: str, *headings: str) -> str:
    """Body under a chain of headings, each searched inside the previous one.

    A section runs to the next heading of the same or a higher level. Lines
    inside fenced code blocks are never treated as headings.
    """
    lines = text.splitlines()
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
            raise AssertionError("heading not found: %r" % heading)
        stop = end
        in_fence = False
        for j in range(found + 1, end):
            if lines[j].startswith("```"):
                in_fence = not in_fence
                continue
            m = HEADING.match(lines[j])
            if not in_fence and m and len(m.group(1)) <= level:
                stop = j
                break
        start, end = found + 1, stop
    return "\n".join(lines[start:end])


def first_table(text: str) -> List[str]:
    """The first contiguous block of `|` lines: header, separator, rows."""
    rows = []  # type: List[str]
    for line in text.splitlines():
        if line.startswith("|"):
            rows.append(line)
        elif rows:
            break
    return rows


def cells(row: str) -> List[str]:
    """Cell texts of a markdown table row, splitting on unescaped pipes."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", row.strip())[1:-1]]


def git_grep(root: Path, pattern: str) -> List[Tuple[str, str, str]]:
    """Fixed-string `git grep` over tracked text files as (path, line, text).

    Parses `-n --null` output (`path\\0line\\0text`), so paths with spaces stay
    whole. Exit 1 means no matches. Any other non-zero exit raises, so a broken
    grep never reads as a clean result.
    """
    proc = subprocess.run(
        ["git", "-C", str(root), "grep", "-n", "-I", "--null", "-F", "-e", pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode == 1:
        return []
    if proc.returncode != 0:
        raise RuntimeError(
            "git grep failed (exit %d): %s"
            % (proc.returncode, proc.stderr.decode("utf-8", "replace"))
        )
    hits = []  # type: List[Tuple[str, str, str]]
    for raw in proc.stdout.decode("utf-8", "replace").split("\n"):
        if not raw:
            continue
        parts = raw.split("\0", 2)
        if len(parts) != 3:
            raise RuntimeError("unparseable git grep line: %r" % raw)
        hits.append((parts[0], parts[1], parts[2]))
    return hits


def is_record(path: str) -> bool:
    return path.startswith(RECORD_PREFIXES) or path in DATED_SNAPSHOTS


def test_prototype_names_capability():
    """AC-1.1: Step 2's Figma MCP detection sentence and Step 2.5's render
    table name `canvas-preview`; the file names no vendor tool; the table keeps
    its three rows in order; "Never degrade silently." stays."""
    text = read("commands/prototype.md")

    assert CURSOR_TOOL not in text, "commands/prototype.md still names %s" % CURSOR_TOOL

    step2 = section(text, "### Step 2: Context Scan")
    figma = [line for line in step2.splitlines() if line.startswith("**Figma MCP detection:**")]
    assert len(figma) == 1, "expected one Figma MCP detection line in Step 2, found %d" % len(figma)
    assert "`%s`" % CAPABILITY in figma[0], figma[0]

    render = section(
        text, "### Step 2.5: Diverge & Choose", "#### Render through the platform"
    )
    rows = first_table(render)[2:]
    labels = [cells(row)[0] for row in rows]
    assert labels == [
        "Native artboard/design surface",
        "`canvas-preview` (the adapter maps it)",
        "Neither",
    ], labels
    assert "Never degrade silently." in render


@pytest.mark.parametrize(
    "adapter, headings, keywords",
    ADAPTER_TABLES,
    ids=[Path(a).stem for a, _, _ in ADAPTER_TABLES],
)
def test_adapter_canvas_row(adapter, headings, keywords):
    """AC-1.2, AC-1.3, AC-1.4: the adapter has exactly one `canvas-preview`
    row, in its tool table, with that table's column count. The row carries
    the platform mapping keywords and its last cell ends with the degradation
    clause."""
    text = read(adapter)
    matches = [line for line in text.splitlines() if line.startswith(CANVAS_ROW_PREFIX)]
    assert len(matches) == 1, "%s: expected one %s row, found %d" % (
        adapter, CANVAS_ROW_PREFIX, len(matches))
    row = matches[0]

    table = first_table(section(text, *headings))
    assert row in table[2:], "%s: the %s row is not in the %s table" % (
        adapter, CAPABILITY, headings[-1])
    assert len(cells(row)) == len(cells(table[0])), "%s: row has %d cells, header has %d" % (
        adapter, len(cells(row)), len(cells(table[0])))

    for keyword in keywords:
        assert keyword in row, "%s: row lacks %r" % (adapter, keyword)
    assert cells(row)[-1].endswith(DEGRADATION_CLAUSE), "%s: last cell must end with %r" % (
        adapter, DEGRADATION_CLAUSE)


def test_cursor_ide_browser_confined():
    """AC-1.5: every tracked line naming the Cursor tool is in
    `adapters/cursor.md` or a record path."""
    stray = [
        "%s:%s: %s" % hit
        for hit in git_grep(REPO_ROOT, CURSOR_TOOL)
        if hit[0] != "adapters/cursor.md" and not is_record(hit[0])
    ]
    assert stray == [], "%s outside adapters/cursor.md and record paths:\n%s" % (
        CURSOR_TOOL, "\n".join(stray))
