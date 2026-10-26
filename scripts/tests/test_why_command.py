#!/usr/bin/env python3
"""Static checks for spec `2026-10-25-why-command`.

Command section (Story 1). `commands/why.md` is read as text; nothing here
runs the command.

- `test_command_file`: the file exists; its frontmatter has `name: why`,
  `entry_level: high`, `description`, `problem`, `outcome`, and exactly three
  `exit_criteria`; the body has the eight `##` sections, with `## Completion`
  immediately before `## References` (AC-1.1).
- `test_tiers`: the first table under `## Confidence Tiers` lists `Recorded`,
  `Stated`, `Corroborated`, `Inferred`, `Unknown` in order; the section says
  code is not evidence of its own intent and conflicting sources give the
  lower tier (AC-1.2).
- `test_source_order`: Step 2 names the ledger sources, Step 3 `git log`,
  Step 4 MCP and `Stated`; Steps 2 to 4 appear in that order; each step names
  its absent-source case (AC-1.3).
- `test_step_headings`: six `### Step N:` headings numbered 1 to 6 (AC-1.3).
- `test_handoff_shape`: the fixed heading and its four subsections in order,
  and the saved-record path pattern (AC-1.4).
- `test_budgets`: under 200 lines and under 24,960 bytes.
- No test here covers AC-1.5: it is the dogfood fixture run (questions 1 to
  3) recorded in Story 1's What Was Built.

Registration section (Story 2). `test_registration` reads every surface in
technical-spec.md → Registration Edits as text and runs the two generator
`--check` commands and `scripts/eval-command-structure.py` (AC-2.1 to
AC-2.4).

Run: uv run --python 3.9 pytest scripts/tests/test_why_command.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND_REL = "commands/why.md"
COMMAND = REPO_ROOT / COMMAND_REL

LINE_BUDGET = 200
BYTE_BUDGET = 24960

FRONTMATTER_KEYS = ("description", "problem", "outcome", "exit_criteria")
EXIT_CRITERIA_COUNT = 3
SECTIONS = (
    "## Overview",
    "## Invocation",
    "## Required Artifacts",
    "## Confidence Tiers",
    "## Command Process",
    "## Integration with Writ",
    "## Completion",
    "## References",
)
TIERS = ["Recorded", "Stated", "Corroborated", "Inferred", "Unknown"]
HANDOFF_HEADING = "## Preserve / Change / Avoid / Risk"
HANDOFF_SUBSECTIONS = ("### Preserve", "### Change", "### Avoid", "### Risk")
RECORD_PATH = ".writ/research/<YYYY-MM-DD>-why-<slug>.md"

HEADING = re.compile(r"^(#{1,6}) \S")
FENCE = re.compile(r"^\s*(```|~~~)")
STEP_HEADING = re.compile(r"^### Step (\d+): \S")


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
    starts = []  # type: List[int]
    in_fence = False
    for i, line in enumerate(body):
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence and line.rstrip().startswith(heading):
            starts.append(i)
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
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    if len(rows) < 2:
        pytest.fail("no pipe table found")
    return [rows[0]] + rows[2:]


def unfenced_headings(body: List[str]) -> List[str]:
    out = []  # type: List[str]
    in_fence = False
    for line in body:
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and HEADING.match(line):
            out.append(line.rstrip())
    return out


def test_command_file():
    # AC-1.1
    body = lines()
    fm = frontmatter(body)
    stripped = [line.strip() for line in fm]
    assert "name: why" in stripped
    assert "entry_level: high" in stripped
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

    h2s = [h for h in unfenced_headings(body) if h.startswith("## ")]
    for name in SECTIONS:
        assert name in h2s, "%s lacks %r" % (COMMAND_REL, name)
    assert h2s.index("## References") == h2s.index("## Completion") + 1, (
        "## Completion is not immediately before ## References: %r" % h2s
    )
    refs = "\n".join(section(body, "## References"))
    assert "commands/_preamble.md" in refs
    assert "system-instructions.md" in refs


def test_tiers():
    # AC-1.2
    tiers = section(lines(), "## Confidence Tiers")
    table = first_table(tiers)
    names = [row[0].strip("`") for row in table[1:]]
    assert names == TIERS, "tier column is %r" % names
    prose = "\n".join(tiers)
    assert "not evidence of its own intent" in prose
    assert "lower tier" in prose


def test_step_headings():
    # AC-1.3
    process = section(lines(), "## Command Process")
    numbers = [int(m.group(1)) for m in (STEP_HEADING.match(line) for line in process) if m]
    assert numbers == [1, 2, 3, 4, 5, 6], "step numbers are %r" % numbers


def test_source_order():
    # AC-1.3
    body = lines()
    process = section(body, "## Command Process")
    starts = {}
    for i, line in enumerate(process):
        m = STEP_HEADING.match(line)
        if m:
            starts[int(m.group(1))] = i
    assert starts.get(2, -1) < starts.get(3, -1) < starts.get(4, -1), starts

    step1 = "\n".join(section(body, "### Step 1:"))
    step2 = "\n".join(section(body, "### Step 2:"))
    step3 = "\n".join(section(body, "### Step 3:"))
    step4 = "\n".join(section(body, "### Step 4:"))

    assert "one natural-language question" in step1
    for needle in ("refs/notes/writ", "drift-log.md", "What Was Built", ".writ/decision-records/"):
        assert needle in step2, "Step 2 does not name %r" % needle
    assert "No `.writ/`" in step2, "Step 2 does not name the absent-ledger case"
    assert "git log" in step3
    assert "not a git repository" in step3, "Step 3 does not name the no-repository case"
    assert "MCP" in step4
    assert "below `Stated`" in step4
    assert "none connected" in step4, "Step 4 does not name the no-server case"
    assert "Never prompt to connect" in step4


def test_handoff_shape():
    # AC-1.4
    body = lines()
    content = "\n".join(body)
    assert RECORD_PATH in content
    at = [i for i, line in enumerate(body) if line.rstrip() == HANDOFF_HEADING]
    assert at, "%s lacks %r" % (COMMAND_REL, HANDOFF_HEADING)
    after = [line.rstrip() for line in body[at[-1] + 1:]]
    found = [line for line in after if line in HANDOFF_SUBSECTIONS]
    assert tuple(found[:4]) == HANDOFF_SUBSECTIONS, "subsections after the heading: %r" % found

    step6 = "\n".join(section(body, "### Step 6:"))
    assert "only when a change follows" in step6


def test_budgets():
    body = lines()
    assert len(body) < LINE_BUDGET, "%s has %d lines; the budget is under %d" % (
        COMMAND_REL,
        len(body),
        LINE_BUDGET,
    )
    size = len(COMMAND.read_bytes())
    assert size < BYTE_BUDGET, "%s is %d bytes; the budget is under %d" % (
        COMMAND_REL,
        size,
        BYTE_BUDGET,
    )


# ---------------------------------------------------------------------------
# Registration section (Story 2). Every surface is read as text; the two
# generator `--check` calls are the only subprocesses.

import subprocess  # noqa: E402
import sys  # noqa: E402

MANIFEST_REL = ".writ/manifest.yaml"
WHY_FIELDS = (
    "file: commands/why.md",
    "category: planning",
    'purpose: "Answer why code is the way it is from the ledger, git history, '
    'and MCP servers, with a confidence tier on every claim."',
    "tags: [planning, why, history, ledger]",
)
WHY_ROW_PREFIX = "| `/why` |"
README_ROW = (
    "| `/why` | Answers why code is the way it is from the ledger, git history, "
    "and MCP servers, with a confidence tier on every claim; when a change "
    "follows, ends with a Preserve / Change / Avoid / Risk list `/create-spec` reads |"
)
STRUCTURE_ARGV = [sys.executable, "scripts/eval-command-structure.py", "--root", "."]
STRUCTURE_ROWS = (
    "command-structure:commands/why.md:heading:Confidence Tiers",
    "command-structure:commands/why.md:frontmatter:entry_level",
)
GENERATED = (
    "SKILL.md",
    "claude-code/CLAUDE.md",
    "codex/AGENTS.md.template",
    "cursor/plugin/commands/why.md",
    "plugins/writ/commands/why.md",
)
CHECKS = [
    ["bash", "scripts/gen-skill.sh", "--check"],
    [sys.executable, "scripts/gen-platform-trees.py", "--check"],
]
CURSOR_TREE_LINE = "│   │   ├── why.md                 # /why"
CURSOR_COUNT_ANCHOR = "one file per `commands:` entry"
CURSOR_COUNT = "(34)"
HIGH_ROW_PREFIX = "| `high` |"
HIGH_COUNT = "(17)"
NAME_IN_TICKS = re.compile(r"`([a-z0-9-]+)`")


def read(rel: str) -> str:
    path = REPO_ROOT / rel
    assert path.exists(), "%s does not exist" % rel
    return path.read_text(encoding="utf-8")


def manifest_commands() -> List[tuple]:
    """(name, stripped field lines) per entry under the top-level `commands:`."""
    body = read(MANIFEST_REL).splitlines()
    start = [i for i, line in enumerate(body) if line.rstrip() == "commands:"]
    assert start, "manifest has no commands: block"
    entries = []  # type: List[tuple]
    for line in body[start[0] + 1:]:
        if line.strip() and not line.startswith(" ") and not line.startswith("#"):
            break
        m = re.match(r"^  - name:\s*(\S+)", line)
        if m:
            entries.append((m.group(1), []))
        elif entries and line.startswith("    "):
            entries[-1][1].append(line.strip())
    return entries


def line_index(body: List[str], needle: str) -> int:
    hits = [i for i, line in enumerate(body) if needle in line]
    assert hits, "no line containing %r" % needle
    return hits[0]


def test_registration():
    # AC-2.1
    entries = manifest_commands()
    names = [name for name, _ in entries]
    assert "why" in names, "manifest commands have no why entry"
    assert names == sorted(names), "manifest commands are not sorted: %r" % names
    at = names.index("why")
    assert names[at - 1:at + 2] == ["verify-spec", "why", "writ"], names[at - 1:at + 2]
    for field in WHY_FIELDS:
        assert field in entries[at][1], "why entry lacks %r: %r" % (field, entries[at][1])

    # AC-2.2
    for argv in CHECKS:
        proc = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True, text=True)
        out = proc.stdout.splitlines()
        first = out[0] if out else ""
        assert proc.returncode == 0 and first == "pass", "%s exit %d:\n%s%s" % (
            " ".join(argv[1:]),
            proc.returncode,
            proc.stdout,
            proc.stderr,
        )
    source = read(COMMAND_REL)
    for rel in GENERATED:
        body = read(rel)
        if rel.endswith("/why.md"):
            assert "## Confidence Tiers" in body and "entry_level: high" in body, (
                "%s is not a copy of %s" % (rel, COMMAND_REL)
            )
        else:
            assert "/why" in body, "%s does not carry /why" % rel
    assert "Confidence Tiers" in source
    for rel in ("SKILL.md", "claude-code/CLAUDE.md", "codex/AGENTS.md.template"):
        assert any(
            line.startswith(WHY_ROW_PREFIX) for line in read(rel).splitlines()
        ), "%s has no /why row" % rel

    # AC-2.3
    planning = section(read("README.md").splitlines(), "### Planning & Specification")
    rows = [row[0] for row in first_table(planning)[1:]]
    assert "`/why`" in rows, "README Planning table: %r" % rows
    assert rows.index("`/why`") == rows.index("`/research`") + 1, rows
    assert README_ROW in [line.rstrip() for line in planning], "README /why row text differs"

    tree = section(read("adapters/cursor.md").splitlines(), "## Directory Structure")
    why_at = line_index(tree, CURSOR_TREE_LINE)
    verify_at = line_index(tree, "verify-spec.md")
    writ_at = line_index(tree, "├── writ.md")
    assert verify_at < why_at < writ_at, (verify_at, why_at, writ_at)
    assert tree[why_at].index("#") == tree[verify_at].index("#"), "comment column not aligned"
    assert CURSOR_COUNT in tree[line_index(tree, CURSOR_COUNT_ANCHOR)]

    status = read("commands/status.md").splitlines()
    slash = [line for line in status if line.startswith("`/writ`, ")]
    assert len(slash) == 1, slash
    assert "`/research`, `/why`," in slash[0], slash[0]
    bare = [line for line in status if line.startswith("`writ`, ")]
    assert len(bare) == 1, bare
    assert "`research`, `why`," in bare[0], bare[0]

    high = [
        line
        for line in read(".writ/docs/model-tiers.md").splitlines()
        if line.startswith(HIGH_ROW_PREFIX)
    ]
    assert len(high) == 1, high
    listed = [c.strip() for c in high[0].strip().strip("|").split("|")][1]
    names = NAME_IN_TICKS.findall(listed)
    assert names.index("security-audit") < names.index("why") < names.index("writ"), names
    assert listed.endswith(HIGH_COUNT), listed

    # AC-2.4
    proc = subprocess.run(STRUCTURE_ARGV, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = proc.stdout.splitlines()
    for name in STRUCTURE_ROWS:
        assert "PASS\t" + name in out, "no PASS line for %s:\n%s" % (name, proc.stdout)
    front_door = read("scripts/tests/test_front_door.py")
    assert 'CURSOR_COUNT = "(34)"' in front_door
