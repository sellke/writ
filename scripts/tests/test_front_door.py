#!/usr/bin/env python3
"""Static checks for spec `2026-10-22-front-door`.

Command section (Story 1). `commands/writ.md` is read as text; nothing here
runs the command.

- `test_command_file`: the file exists and has fewer than 200 lines; its
  frontmatter has `name: writ`, `entry_level: high`, `description`,
  `problem`, `outcome`, and an `exit_criteria` list of exactly four items;
  `## References` names `commands/_preamble.md` and
  `system-instructions.md` (AC-1.1).
- `test_guide_cited`: the file names `.writ/docs/prompting-guide.md` and
  the guide heading `What a request carries` (AC-1.2).
- `test_routing_rules`: the first table under `## Routing Rules` has a
  `Signal | Route` header and six data rows whose Route cells, in order,
  contain `/prototype` (without `--no-diverge`), `/prototype --no-diverge`,
  `/create-spec`, `/implement-phase`, `/research`, `/prototype`; the fifth
  row mentions `/why`; and `### Step 2` names both `/prototype --no-diverge`
  and `/create-spec` and sends their conflict to `/create-spec` on an
  escalation signal (AC-1.3).
- `test_confirmation_step`: `### Step 3` contains `AskQuestion`,
  `(Recommended)`, and `Not what I meant` (AC-1.4).
- `test_mirroring_step`: `### Step 4` contains `skip:` and `todo_write`
  (AC-1.5).

Story 2 adds the registration section (manifest, catalogs, README, adapter
and doc surfaces) and Story 3 adds the structure-row and issue section to
this same file.

Run: uv run --python 3.9 pytest scripts/tests/test_front_door.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND_REL = "commands/writ.md"
COMMAND = REPO_ROOT / COMMAND_REL

LINE_BUDGET = 200

FRONTMATTER_KEYS = ("description", "problem", "outcome", "exit_criteria")
EXIT_CRITERIA_COUNT = 4

# (text the Route cell must contain, text it must not contain)
ROUTES = [
    ("/prototype", "--no-diverge"),
    ("/prototype --no-diverge", None),
    ("/create-spec", None),
    ("/implement-phase", None),
    ("/research", None),
    ("/prototype", None),
]
TABLE_HEADER = ["Signal", "Route"]

HEADING = re.compile(r"^(#{1,6}) \S")
FENCE = re.compile(r"^\s*(```|~~~)")


def text() -> str:
    assert COMMAND.exists(), "%s does not exist" % COMMAND_REL
    return COMMAND.read_text(encoding="utf-8")


def lines() -> List[str]:
    return text().splitlines()


def frontmatter(body: List[str]) -> List[str]:
    """Lines between the opening `---` and the closing `---`."""
    assert body and body[0].strip() == "---", "%s has no frontmatter" % COMMAND_REL
    for i, line in enumerate(body[1:], start=1):
        if line.strip() == "---":
            return body[1:i]
    pytest.fail("%s frontmatter never closes" % COMMAND_REL)


def section(body: List[str], heading: str) -> List[str]:
    """Lines under the first heading that starts with `heading`, up to the next
    heading of the same or a higher level. Headings inside fenced code do not
    start or end a section."""
    level = len(heading) - len(heading.lstrip("#"))
    starts = [
        i for i, line in enumerate(body) if line.rstrip().startswith(heading)
    ]
    if not starts:
        pytest.fail("heading not found: %r" % heading)
    out = []  # type: List[str]
    in_fence = False
    for line in body[starts[0] + 1:]:
        if FENCE.match(line):
            in_fence = not in_fence
        m = HEADING.match(line)
        if m and not in_fence and len(m.group(1)) <= level:
            break
        out.append(line)
    return out


def first_table(body: List[str]) -> List[List[str]]:
    """Rows of the first pipe table in `body`, header row first, separator
    row dropped, each row a list of stripped cells."""
    rows = []  # type: List[List[str]]
    for line in body:
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
        elif rows:
            break
    if len(rows) < 2:
        pytest.fail("no pipe table found")
    return [rows[0]] + rows[2:]


def test_command_file():
    # AC-1.1
    body = lines()
    assert len(body) < LINE_BUDGET, "%s has %d lines; the budget is under %d" % (
        COMMAND_REL,
        len(body),
        LINE_BUDGET,
    )

    fm = frontmatter(body)
    assert "name: writ" in [line.strip() for line in fm]
    assert "entry_level: high" in [line.strip() for line in fm]
    for key in FRONTMATTER_KEYS:
        assert any(line.startswith(key + ":") for line in fm), "frontmatter lacks %s:" % key

    start = next(i for i, line in enumerate(fm) if line.startswith("exit_criteria:"))
    items = 0
    for line in fm[start + 1:]:
        if not line.startswith(" "):
            break
        if line.lstrip().startswith("- "):
            items += 1
    assert items == EXIT_CRITERIA_COUNT, "exit_criteria has %d items, expected %d" % (
        items,
        EXIT_CRITERIA_COUNT,
    )

    refs = "\n".join(section(body, "## References"))
    assert "commands/_preamble.md" in refs
    assert "system-instructions.md" in refs


def test_guide_cited():
    # AC-1.2
    content = text()
    assert ".writ/docs/prompting-guide.md" in content
    assert "What a request carries" in content


def test_routing_rules():
    # AC-1.3
    body = lines()
    table = first_table(section(body, "## Routing Rules"))
    header, rows = table[0], table[1:]
    assert header == TABLE_HEADER, "header is %r" % header
    assert len(rows) == len(ROUTES), "%d data rows, expected %d" % (len(rows), len(ROUTES))
    for n, (row, (route, forbidden)) in enumerate(zip(rows, ROUTES), start=1):
        assert len(row) == 2, "row %d has %d cells" % (n, len(row))
        assert route in row[1], "row %d Route cell %r lacks %r" % (n, row[1], route)
        if forbidden:
            assert forbidden not in row[1], "row %d Route cell %r carries %r" % (
                n,
                row[1],
                forbidden,
            )
    assert "/why" in rows[4][1], "row 5 Route cell %r does not mention /why" % rows[4][1]

    step2 = "\n".join(section(body, "### Step 2"))
    assert "/prototype --no-diverge" in step2
    assert "/create-spec" in step2
    assert "over 5 files" in step2 or "escalation" in step2


def test_confirmation_step():
    # AC-1.4
    step3 = "\n".join(section(lines(), "### Step 3"))
    assert "AskQuestion" in step3
    assert "(Recommended)" in step3
    assert "Not what I meant" in step3


def test_mirroring_step():
    # AC-1.5
    step4 = "\n".join(section(lines(), "### Step 4"))
    assert "skip:" in step4
    assert "todo_write" in step4
