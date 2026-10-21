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

Registration section (Story 2):

- The old command file is now `commands/writ-design.md` and names itself
  `writ-design`.
- The manifest entry, `SKILL.md`, and the generated `claude-code/CLAUDE.md`
  name `writ-design`; no alias keeps the old name.
- The rename-class lines in technical-spec.md → Reference Inventory, and the
  five `referenced_paths_allowlist` rows in `scripts/eval.sh`, name
  `/writ-design`.

RECORD_PREFIXES and DATED_SNAPSHOTS come from technical-spec.md → Reference
Gate → Record list. Story 3's reference gate reuses them.

Covers AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-2.1, AC-2.2, AC-2.3, AC-2.4,
and AC-2.5.

Run: uv run --python 3.9 pytest scripts/tests/test_platform_neutral_names.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union

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


# ---------------------------------------------------------------------------
# Registration section (Story 2 of 2026-10-20-platform-neutral-names): the old
# command is renamed to `/writ-design`. Naming the spec here keeps the AC
# citations below attributed to it (ac-trace attributes a token to the spec
# folder named most recently above it; RECORD_PREFIXES names another).
# ---------------------------------------------------------------------------

# The old name is built from parts, never spelled as a slash command or a
# file name, so this file is not a hit for the Story 3 reference gate.
OLD_NAME = "design"
OLD_SLASH = "/" + OLD_NAME
OLD_FILE = "commands/%s.md" % OLD_NAME
NEW_FILE = "commands/writ-design.md"
DESIGN_CATEGORY = "planning"
DESIGN_PURPOSE = "Create and compare visual references for Writ specifications."
DESIGN_TAGS = ["planning", "design", "visual"]
# OLD_SLASH used as a command name. Not a `design-system.md` path, not
# "artboard" + OLD_SLASH, and not `/writ-design`.
OLD_COMMAND = re.compile(r"(?<![\w./-])" + re.escape(OLD_SLASH) + r"(?![\w-])")
# The bare old name in a code span, as in the manifest-style lists.
OLD_BARE_NAME = "`%s`" % OLD_NAME
# technical-spec.md → Rename → File edits, scripts/eval.sh row.
DESIGN_ALLOWLIST_PATHS = (
    ".writ/docs/design-system.md",
    "design-system.md",
    "component-inventory.md",
    "mockups/README.md",
    "mockups/component-inventory.md",
)

ManifestValue = Union[str, List[str]]


def manifest_value(raw: str) -> ManifestValue:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [item.strip().strip("\"'") for item in raw[1:-1].split(",") if item.strip()]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def manifest_commands(text: str) -> List[Dict[str, ManifestValue]]:
    """Entries of the manifest's top-level `commands:` list, in file order.

    A line reader for the manifest's fixed shape (no PyYAML): `  - name: x`
    opens an entry, `    key: value` sets a field, and a deeper `- item`
    line appends to the previous field as a block list. The list ends at the
    next top-level key. Any other line inside the list fails the test, so a
    shape this reader does not know is never read as an empty list.
    """
    entries = []  # type: List[Dict[str, ManifestValue]]
    in_commands = False
    last_key = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            in_commands = line.rstrip() == "commands:"
            continue
        if not in_commands:
            continue
        opened = re.match(r"^  - (\w+):\s*(.*)$", line)
        field = re.match(r"^    (\w+):\s*(.*)$", line)
        item = re.match(r"^ {4,}- (.*)$", line)
        if opened:
            last_key = opened.group(1)
            entries.append({last_key: manifest_value(opened.group(2))})
        elif field and entries:
            last_key = field.group(1)
            value = field.group(2).strip()
            entries[-1][last_key] = manifest_value(value) if value else []
        elif item and entries and isinstance(entries[-1].get(last_key), list):
            entries[-1][last_key].append(manifest_value(item.group(1)))  # type: ignore[union-attr]
        else:
            raise AssertionError("manifest line this reader does not know: %r" % line)
    return entries


def allowlist_rows(text: str) -> List[List[str]]:
    """`path|command|reason` rows of `referenced_paths_allowlist` in eval.sh."""
    lines = text.splitlines()
    start = lines.index("referenced_paths_allowlist() {")
    assert lines[start + 1].strip() == "cat <<'EOF'", lines[start + 1]
    end = lines.index("EOF", start)
    rows = [line.split("|", 2) for line in lines[start + 2:end] if line.strip()]
    for row in rows:
        assert len(row) == 3, "allowlist row is not path|command|reason: %r" % "|".join(row)
    return rows


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(argv),
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def test_writ_design_file():
    """AC-2.1: `commands/writ-design.md` exists and names itself `writ-design`
    in the frontmatter, the H1, and the five invocation rows; no line uses
    the old slash name; the old command file does not exist."""
    assert not (REPO_ROOT / OLD_FILE).exists(), "%s still exists" % OLD_FILE
    assert (REPO_ROOT / NEW_FILE).is_file(), "%s is missing" % NEW_FILE
    text = read(NEW_FILE)

    lines = text.splitlines()
    assert lines[0] == "---", "%s has no frontmatter" % NEW_FILE
    frontmatter = lines[1:lines.index("---", 1)]
    names = [line for line in frontmatter if line.startswith("name:")]
    assert names == ["name: writ-design"], names

    h1 = [line for line in lines if line.startswith("# ")]
    assert h1 == ["# Design Command (writ-design)"], h1

    rows = first_table(section(text, "## Invocation"))[2:]
    invocations = [cells(row)[0] for row in rows]
    assert len(invocations) == 5, invocations
    for invocation in invocations:
        assert invocation.startswith("`/writ-design"), invocation

    stray = [line for line in lines if OLD_COMMAND.search(line)]
    assert stray == [], "%s still names %s:\n%s" % (NEW_FILE, OLD_SLASH, "\n".join(stray))


def test_manifest_entry():
    """AC-2.2: the manifest has one `writ-design` entry pointing at
    `commands/writ-design.md` with the old category, purpose, and tags; no
    command has the old name; no `aliases` list contains it; the
    commands list is sorted by name."""
    entries = manifest_commands(read(".writ/manifest.yaml"))
    names = [entry["name"] for entry in entries]
    assert len(names) >= 30, "manifest reader found only %d commands" % len(names)

    assert OLD_NAME not in names, "manifest still has a command named %s" % OLD_NAME
    matches = [entry for entry in entries if entry["name"] == "writ-design"]
    assert len(matches) == 1, "expected one writ-design entry, found %d" % len(matches)
    entry = matches[0]
    assert entry.get("file") == NEW_FILE, entry
    assert entry.get("category") == DESIGN_CATEGORY, entry
    assert entry.get("purpose") == DESIGN_PURPOSE, entry
    assert entry.get("tags") == DESIGN_TAGS, entry

    aliased = [e["name"] for e in entries if OLD_NAME in (e.get("aliases") or [])]
    assert aliased == [], "aliases name %s: %s" % (OLD_NAME, aliased)
    assert names == sorted(names), "manifest commands are not sorted: %s" % names


def test_skill_catalog():
    """AC-2.2: `gen-skill.sh --check` passes and `SKILL.md` lists
    `/writ-design`, last in the Planning & Specification table, with no
    row for the old name."""
    proc = run("bash", "scripts/gen-skill.sh", "--check")
    first = proc.stdout.splitlines()[0] if proc.stdout else ""
    assert proc.returncode == 0 and first == "pass", "gen-skill.sh --check exit %d:\n%s%s" % (
        proc.returncode, proc.stdout, proc.stderr)

    text = read("SKILL.md")
    rows = first_table(section(text, "## Available Commands", "### Planning & Specification"))[2:]
    commands = [cells(row)[0] for row in rows]
    assert commands[-1] == "`/writ-design`", commands
    assert cells(rows[-1]) == ["`/writ-design`", "`%s`" % NEW_FILE, DESIGN_PURPOSE], rows[-1]
    stray = [line for line in text.splitlines() if OLD_COMMAND.search(line)]
    assert stray == [], "SKILL.md still names %s:\n%s" % (OLD_SLASH, "\n".join(stray))


def test_claude_md_generated():
    """AC-2.4: `gen-claude-md.py --check` passes, and the generated
    `claude-code/CLAUDE.md` lists `/writ-design` and not the old name."""
    proc = run(sys.executable, "scripts/gen-claude-md.py", "--check")
    first = proc.stdout.splitlines()[0] if proc.stdout else ""
    assert proc.returncode == 0 and first == "pass", "gen-claude-md.py --check exit %d:\n%s%s" % (
        proc.returncode, proc.stdout, proc.stderr)

    text = read("claude-code/CLAUDE.md")
    row = "| `/writ-design` | `.claude/commands/writ-design.md` | %s |" % DESIGN_PURPOSE
    assert row in text.splitlines(), "claude-code/CLAUDE.md lacks %r" % row
    stray = [line for line in text.splitlines() if OLD_COMMAND.search(line)]
    assert stray == [], "claude-code/CLAUDE.md still names %s:\n%s" % (OLD_SLASH, "\n".join(stray))


def test_eval_allowlist_rows():
    """AC-2.3: no `referenced_paths_allowlist` row names the old command; the five
    rows for the command's outputs name `/writ-design` as the creating
    command; every row's creating command exists, so the stale-row check
    judges every row instead of skipping it."""
    rows = allowlist_rows(read("scripts/eval.sh"))
    assert len(rows) >= len(DESIGN_ALLOWLIST_PATHS), rows

    stray = ["|".join(row) for row in rows if OLD_COMMAND.search(row[1] + " " + row[2])]
    assert stray == [], "allowlist rows still name %s:\n%s" % (OLD_SLASH, "\n".join(stray))

    by_path = {}  # type: Dict[str, List[List[str]]]
    for row in rows:
        by_path.setdefault(row[0], []).append(row)
    for path in DESIGN_ALLOWLIST_PATHS:
        assert len(by_path.get(path, [])) == 1, "expected one allowlist row for %s" % path
        _, command, reason = by_path[path][0]
        assert command == "/writ-design", "%s: creating command is %r" % (path, command)
        if reason.startswith("Written by "):
            assert reason.startswith("Written by /writ-design "), reason

    missing = sorted(
        {row[1] for row in rows if not (REPO_ROOT / "commands" / (row[1].lstrip("/") + ".md")).is_file()}
    )
    assert missing == [], "allowlist rows name commands with no file: %s" % missing


# (file, anchors). Each anchor finds one renamed line by text that the rename
# did not touch, so a later edit to the rest of the line does not break the
# test. Files with an empty list have a dedicated test below; every file gets
# the whole-file check for the old name.
RENAMED_ANCHORS = [
    ("README.md", ["Visual design companion"]),
    ("commands/create-spec.md", ["Follow wireframe conventions from"]),
    ("commands/create-adr.md", ["Design explorations may produce ADR-worthy decisions"]),
    ("commands/research.md", ["Research provides evidence base for design decisions"]),
    ("commands/prototype.md", ["Mockups for a spec that already exists", "Terminal constraint:"]),
    ("adapters/cursor.md", []),
    ("codex/AGENTS.md.template", []),
    ("commands/status.md", []),
    (".writ/docs/model-tiers.md", []),
]


@pytest.mark.parametrize("rel, anchors", RENAMED_ANCHORS, ids=[r for r, _ in RENAMED_ANCHORS])
def test_rename_class_references(rel, anchors):
    """AC-2.3: each rename-class file from the Reference Inventory names
    `/writ-design` (or bare `writ-design`) and no longer uses the old name,
    slash or bare, as a command name. Each anchored line names `/writ-design`.
    Keep-class text in the same files (`design-system.md` paths, the
    "artboard" and "roadmap" pairs) is not a command name and does not
    match."""
    text = read(rel)
    lines = text.splitlines()
    for anchor in anchors:
        found = [line for line in lines if anchor in line]
        assert len(found) == 1, "%s: expected one line with %r, found %d" % (
            rel, anchor, len(found))
        assert "`/writ-design`" in found[0], "%s: %r line does not name /writ-design: %r" % (
            rel, anchor, found[0])
    assert "writ-design" in text, "%s does not name writ-design" % rel
    stray = [line for line in lines if OLD_COMMAND.search(line) or OLD_BARE_NAME in line]
    assert stray == [], "%s still names %s as a command:\n%s" % (rel, OLD_NAME, "\n".join(stray))


def test_status_allowlists():
    """AC-2.3: both command allowlists in `commands/status.md` name
    `writ-design` where the old name stood."""
    text = read("commands/status.md")
    quick = [line for line in text.splitlines() if line.startswith("`/create-spec`, ")]
    assert len(quick) == 1, quick
    listed = re.findall(r"`([^`]+)`", quick[0])
    assert "/writ-design" in listed and OLD_SLASH not in listed, listed

    note = section(text, "## Maintainer Note: Command Allowlist")
    bare = [line for line in note.splitlines() if line.startswith("`create-spec`, ")]
    assert len(bare) == 1, bare
    listed = re.findall(r"`([^`]+)`", bare[0])
    assert "writ-design" in listed and OLD_NAME not in listed, listed


def test_cursor_tree():
    """AC-2.3: the `adapters/cursor.md` directory tree lists
    `writ-design.md` in sorted position (last, `└──`), lists one file per
    manifest command with the count in its header, and keeps the comment
    column aligned."""
    manifest = sorted(
        Path(str(entry["file"])).name for entry in manifest_commands(read(".writ/manifest.yaml")))
    tree = section(read("adapters/cursor.md"), "## Directory Structure").splitlines()
    start = next(i for i, line in enumerate(tree) if line.startswith("│   ├── commands/"))
    assert "(%d)" % len(manifest) in tree[start], tree[start]
    entries = []
    for line in tree[start + 1:]:
        if not line.startswith(("│   │   ├── ", "│   │   └── ")):
            break
        entries.append(line)
    files = [line[len("│   │   ├── "):].split()[0] for line in entries]
    assert files == manifest, "tree files differ from the manifest: %s" % files
    assert entries[-1] == "│   │   └── writ-design.md         # /writ-design", entries[-1]
    assert all(line.startswith("│   │   ├── ") for line in entries[:-1]), entries
    assert len({line.index("#") for line in entries}) == 1, "comment column not aligned"


def test_codex_template_row():
    """AC-2.3: `codex/AGENTS.md.template` lists `/writ-design` as the last
    Planning & Specification row, after `/verify-spec`, with the same
    purpose."""
    text = read("codex/AGENTS.md.template")
    rows = first_table(section(text, "## Available Commands", "### Planning & Specification"))[2:]
    commands = [cells(row)[0] for row in rows]
    assert commands[-2:] == ["`/verify-spec`", "`/writ-design`"], commands
    assert cells(rows[-1]) == [
        "`/writ-design`", "`.codex/commands/writ-design.md`", DESIGN_PURPOSE], rows[-1]


def test_model_tiers_entry_level():
    """AC-2.3: the `high` row of the entry-level table in
    `.writ/docs/model-tiers.md` names `writ-design`, stays sorted, and its
    `(N)` count matches the names listed."""
    rows = [
        line for line in read(".writ/docs/model-tiers.md").splitlines()
        if line.startswith("| `high` |")
    ]
    assert len(rows) == 1, rows
    listed = cells(rows[0])[1]
    names = re.findall(r"`([a-z0-9-]+)`", listed)
    assert "writ-design" in names and "design" not in names, names
    assert names == sorted(names), names
    count = re.search(r"\((\d+)\)$", listed)
    assert count is not None, listed
    assert int(count.group(1)) == len(names), listed


# Files the sweep edits that also carry the keep-class design-system path. A
# blind `/design` -> `/writ-design` replace would rewrite it.
DESIGN_SYSTEM_PATH = ".writ/docs/design-system.md"
SWEPT_WITH_DESIGN_SYSTEM_PATH = [NEW_FILE, "commands/create-spec.md", "commands/prototype.md"]


@pytest.mark.parametrize("rel", SWEPT_WITH_DESIGN_SYSTEM_PATH)
def test_keep_class_lines_in_swept_files(rel):
    """AC-2.5: in each file the sweep edits, the keep-class
    `.writ/docs/design-system.md` path is still there and was not renamed."""
    text = read(rel)
    assert DESIGN_SYSTEM_PATH in text, "%s lost %s" % (rel, DESIGN_SYSTEM_PATH)
    renamed = DESIGN_SYSTEM_PATH.replace(OLD_SLASH, "/writ-design")
    assert renamed not in text, "%s: keep-class path renamed to %s" % (rel, renamed)


def test_keep_class_roadmap_pair():
    """AC-2.5: the "roadmap" pair in `.writ/docs/model-tiers.md` Q1 is not a
    command name and was not renamed."""
    text = read(".writ/docs/model-tiers.md")
    assert "roadmap" + OLD_SLASH in text, "model-tiers.md lost the roadmap pair"
    assert "roadmap/writ-design" not in text, "model-tiers.md renamed the roadmap pair"
