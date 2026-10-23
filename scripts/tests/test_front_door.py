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

Registration section (Story 2). Every surface is read as text; the two
generator `--check` calls are the only subprocesses.

- `test_manifest`: `.writ/manifest.yaml` `categories:` opens with
  `- id: entry` / `label: "Start here"`; `commands:` holds `writ` with
  `file: commands/writ.md`, `category: entry`, `tags: [entry, routing]`, and
  the spec's purpose; the `name:` sequence is sorted, with `writ` after
  `verify-spec` and before `writ-design` (AC-2.1).
- `test_catalogs`: `SKILL.md` renders `### Start here` before
  `### Planning & Specification` with a `/writ` row; `claude-code/CLAUDE.md`
  has a `/writ` row and the "Start with" line above its Commands table;
  `bash scripts/gen-skill.sh --check` and `gen-claude-md.py --check` exit 0
  with `pass` as the first stdout line (gen-skill.sh prints its `Parser:`
  line on stderr); `codex/AGENTS.md.template` has `### Start here` above
  Planning with the `/writ` row (AC-2.2, AC-2.3).
- `test_readme`: in `## Quick Start`, `/writ` appears before the first pipe
  table, the heading `### What `/writ` routes to` exists, and the
  prompting-guide pointer sentence ends with the `/writ` clause;
  `## Commands` has a `### Start here` table with a `/writ` row (AC-2.4,
  AC-2.3).
- `test_surfaces`: the cursor tree line for `writ.md` sits between
  `verify-spec.md` and `writ-design.md` in the same comment column, with
  the count comment at (33); the `status.md` allowlist starts with `/writ`;
  the `model-tiers.md` `high` row names `writ` between `security-audit` and
  `writ-design` and ends `(16)`; the Claude Code adapter `todo_write` row
  maps to `TodoWrite` with Notes "Native todo list; phases mirror here"
  (AC-2.5).

Story 3 adds the structure-row and issue section to this same file.

Run: uv run --python 3.9 pytest scripts/tests/test_front_door.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

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


# ---------------------------------------------------------------------------
# Registration section (Story 2)

MANIFEST_REL = ".writ/manifest.yaml"
SKILL_REL = "SKILL.md"
CLAUDE_MD_REL = "claude-code/CLAUDE.md"
CODEX_TEMPLATE_REL = "codex/AGENTS.md.template"
README_REL = "README.md"
CURSOR_ADAPTER_REL = "adapters/cursor.md"
CLAUDE_ADAPTER_REL = "adapters/claude-code.md"
STATUS_REL = "commands/status.md"
MODEL_TIERS_REL = ".writ/docs/model-tiers.md"

WRIT_PURPOSE = (
    "Restate a request, route it to the fitting command, "
    "and run it with its phases on the todo list."
)
WRIT_FIELDS = (
    "file: commands/writ.md",
    "category: entry",
    "tags: [entry, routing]",
    'purpose: "%s"' % WRIT_PURPOSE,
)
WRIT_ROW_PREFIX = "| `/writ` |"
START_HERE = "### Start here"
PLANNING = "### Planning & Specification"
START_WITH = 'Start with `/writ "<what you want>"`'
CLAUDE_MD_TABLE_HEADER = "| Command | File | Purpose |"
CODEX_WRIT_CELLS = ["`/writ`", "`.codex/commands/writ.md`"]
ROUTES_HEADING = "### What `/writ` routes to"
GUIDE_REL = ".writ/docs/prompting-guide.md"
POINTER_END = "then type `/writ` followed by what you want."
CURSOR_TREE_LINE = "│   │   ├── writ.md                # /writ"
CURSOR_COUNT_ANCHOR = "one file per `commands:` entry"
CURSOR_COUNT = "(33)"
HIGH_ROW_PREFIX = "| `high` |"
HIGH_COUNT = "(16)"
TODO_ROW = ["`todo_write`", "`TodoWrite`", "Native todo list; phases mirror here"]
# argv per generator check; both must exit 0 with `pass` as the first stdout line.
CHECKS = [
    ["bash", "scripts/gen-skill.sh", "--check"],
    [sys.executable, "scripts/gen-claude-md.py", "--check"],
]
NAME_IN_TICKS = re.compile(r"`([a-z0-9-]+)`")


def read(rel: str) -> str:
    path = REPO_ROOT / rel
    assert path.exists(), "%s does not exist" % rel
    return path.read_text(encoding="utf-8")


def first_equal(body: List[str], text: str) -> int:
    """Index of the first line equal to `text` (trailing space ignored)."""
    hits = [i for i, line in enumerate(body) if line.rstrip() == text]
    assert hits, "no line equal to %r" % text
    return hits[0]


def first_prefixed(body: List[str], prefix: str) -> int:
    hits = [i for i, line in enumerate(body) if line.startswith(prefix)]
    assert hits, "no line starting with %r" % prefix
    return hits[0]


def first_containing(body: List[str], needle: str) -> int:
    hits = [i for i, line in enumerate(body) if needle in line]
    assert hits, "no line containing %r" % needle
    return hits[0]


def cells(row: str) -> List[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def manifest_block(body: List[str], key: str) -> List[str]:
    """Indented lines under the top-level `key:` up to the next top-level key."""
    start = first_equal(body, key + ":")
    out = []  # type: List[str]
    for line in body[start + 1:]:
        if line.strip() and not line.startswith(" ") and not line.startswith("#"):
            break
        out.append(line)
    return out


def manifest_entries(block: List[str], opener: str) -> List[Tuple[str, List[str]]]:
    """(value, stripped field lines) per `  - <opener>: <value>` item."""
    entries = []  # type: List[Tuple[str, List[str]]]
    pattern = re.compile(r"^  - %s:\s*(.*)$" % re.escape(opener))
    for line in block:
        m = pattern.match(line)
        if m:
            entries.append((m.group(1).strip(), []))
        elif entries and line.startswith("    "):
            entries[-1][1].append(line.strip())
    return entries


def test_manifest():
    # AC-2.1
    body = read(MANIFEST_REL).splitlines()
    categories = manifest_entries(manifest_block(body, "categories"), "id")
    assert categories, "manifest has no categories"
    assert categories[0][0] == "entry", "first category is %r, not entry" % categories[0][0]
    assert 'label: "Start here"' in categories[0][1], categories[0][1]

    commands = manifest_entries(manifest_block(body, "commands"), "name")
    names = [name for name, _ in commands]
    assert "writ" in names, "manifest commands have no writ entry"
    assert names == sorted(names), "manifest commands are not sorted by name: %r" % names
    at = names.index("writ")
    assert names[at - 1:at + 2] == ["verify-spec", "writ", "writ-design"], names[at - 1:at + 2]
    fields = commands[at][1]
    for field in WRIT_FIELDS:
        assert field in fields, "writ entry lacks %r: %r" % (field, fields)


def test_catalogs():
    # AC-2.2, AC-2.3
    skill = read(SKILL_REL).splitlines()
    assert any(line.startswith(WRIT_ROW_PREFIX) for line in skill), "SKILL.md has no /writ row"
    assert first_equal(skill, START_HERE) < first_equal(skill, PLANNING), (
        "SKILL.md renders %r after %r" % (START_HERE, PLANNING)
    )
    rows = first_table(section(skill, START_HERE))
    assert any(row[0] == "`/writ`" for row in rows[1:]), "SKILL.md Start here table: %r" % rows

    claude_md = read(CLAUDE_MD_REL).splitlines()
    assert any(line.startswith(WRIT_ROW_PREFIX) for line in claude_md), (
        "%s has no /writ row" % CLAUDE_MD_REL
    )
    assert first_prefixed(claude_md, START_WITH) < first_equal(claude_md, CLAUDE_MD_TABLE_HEADER), (
        "%s: the Start with line is not above the Commands table" % CLAUDE_MD_REL
    )

    for argv in CHECKS:
        proc = subprocess.run(argv, cwd=REPO_ROOT, capture_output=True, text=True)
        out = proc.stdout.splitlines()
        first = out[0] if out else ""
        assert proc.returncode == 0 and first == "pass", "%s exit %d:\n%s%s" % (
            " ".join(argv[1:]),
            proc.returncode,
            proc.stdout,
            proc.stderr,
        )

    codex = section(read(CODEX_TEMPLATE_REL).splitlines(), "## Available Commands")
    assert first_equal(codex, START_HERE) < first_equal(codex, PLANNING), (
        "%s renders %r after %r" % (CODEX_TEMPLATE_REL, START_HERE, PLANNING)
    )
    rows = first_table(section(codex, START_HERE))
    assert rows[0][:2] == ["Command", "File"], rows[0]
    assert CODEX_WRIT_CELLS in [row[:2] for row in rows[1:]], "Codex Start here table: %r" % rows


def test_readme():
    # AC-2.4, AC-2.3
    body = read(README_REL).splitlines()
    quick = section(body, "## Quick Start")
    writ_at = first_containing(quick, "`/writ`")
    table_at = first_prefixed(quick, "|")
    assert writ_at < table_at, "Quick Start: /writ at line %d, first table at %d" % (
        writ_at,
        table_at,
    )
    first_equal(quick, ROUTES_HEADING)
    pointers = [line for line in quick if GUIDE_REL in line]
    assert len(pointers) == 1, "Quick Start names the guide %d times: %r" % (len(pointers), pointers)
    assert pointers[0].rstrip().endswith(POINTER_END), pointers[0]

    commands = section(body, "## Commands")
    assert first_equal(commands, START_HERE) < first_equal(commands, PLANNING), (
        "README Commands renders %r after %r" % (START_HERE, PLANNING)
    )
    rows = first_table(section(commands, START_HERE))
    assert rows[0] == ["Command", "Purpose"], rows[0]
    assert any(row[0] == "`/writ`" for row in rows[1:]), "README Start here table: %r" % rows


def test_surfaces():
    # AC-2.5
    tree = section(read(CURSOR_ADAPTER_REL).splitlines(), "## Directory Structure")
    writ_at = first_equal(tree, CURSOR_TREE_LINE)
    verify_at = first_containing(tree, "verify-spec.md")
    design_at = first_containing(tree, "writ-design.md")
    assert verify_at < writ_at < design_at, (verify_at, writ_at, design_at)
    assert tree[writ_at].index("#") == tree[verify_at].index("#"), "comment column not aligned"
    header = tree[first_containing(tree, CURSOR_COUNT_ANCHOR)]
    assert CURSOR_COUNT in header, header

    allowlist = [line for line in read(STATUS_REL).splitlines() if line.startswith("`/writ`, ")]
    assert len(allowlist) == 1, "status.md allowlist lines starting with /writ: %r" % allowlist
    assert "`/create-spec`" in allowlist[0], allowlist[0]

    high = [line for line in read(MODEL_TIERS_REL).splitlines() if line.startswith(HIGH_ROW_PREFIX)]
    assert len(high) == 1, high
    listed = cells(high[0])[1]
    names = NAME_IN_TICKS.findall(listed)
    assert "writ" in names, names
    assert names.index("security-audit") < names.index("writ") < names.index("writ-design"), names
    assert listed.endswith(HIGH_COUNT), listed

    quick_ref = section(read(CLAUDE_ADAPTER_REL).splitlines(), "### Quick Reference")
    todo = [row for row in first_table(quick_ref)[1:] if row and row[0] == "`todo_write`"]
    assert len(todo) == 1, todo
    assert todo[0] == TODO_ROW, todo[0]
