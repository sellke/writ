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

Reference gate section (Story 3):

- `writ_design_refs(root)` lists every tracked line outside the record list
  that names the old command, by slash name or file name. The real repo has
  none; a fixture repo shows which lines it reports and which it ignores; a
  `git grep` error fails instead of passing.
- Both origin issues end with a `## Resolution` section and point their
  `spec_ref` at this spec.

RECORD_PREFIXES and DATED_SNAPSHOTS come from technical-spec.md → Reference
Gate → Record list, with every `.writ/specs/` folder counted as a record.
Story 1's confinement test and Story 3's reference gate share them.

Covers AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-2.1, AC-2.2, AC-2.3, AC-2.4,
AC-2.5, AC-3.4, and AC-3.5. The install and update criteria are tested in
`scripts/tests/test_install_update_writ_design.sh`.

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
    # Every spec folder, archived or in flight, is a planning or history record
    # (Phase 13 precedent: the harness-cuts guard grep, DEV-009).
    ".writ/specs/",
    ".writ/research/",
    ".writ/decision-records/",
    ".writ/product/",
    ".writ/decision-log.md",
    ".writ/issues/",
    # Regenerated after each story; quotes story and drift titles from the spec folders.
    ".writ/context.md",
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
    # The Cursor docs (rendering-delegation rows, 2026-10-22) document no canvas
    # that renders a local HTML file, so the row names the HTML-file floor.
    ("adapters/cursor.md", ("## Native Tool Availability",), (PROTOTYPES_DIR, "HTML")),
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


def git_grep(root: Path, *patterns: str) -> List[Tuple[str, str, str]]:
    """Fixed-string `git grep` over tracked text files as (path, line, text).

    A line is a hit when it contains any of `patterns`. Parses `-n --null`
    output (`path\\0line\\0text`), so paths with spaces stay whole. Exit 1
    means no matches. Any other non-zero exit raises, so a broken grep never
    reads as a clean result.
    """
    assert patterns, "git_grep needs at least one pattern"
    argv = ["git", "-C", str(root), "grep", "-n", "-I", "--null", "-F"]
    for pattern in patterns:
        argv += ["-e", pattern]
    proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    # A row states facts; only the adapter's verification record says "verified".
    assert "verified" not in row, "%s: the row must not say 'verified'" % adapter


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
# citations below attributed to it: ac-trace attributes a token to the spec
# folder named most recently above it, so another spec folder named earlier
# in this file would otherwise claim them.
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
    # The slash list opens with the front door (`/writ`), so anchor on the
    # `/create-spec` token rather than the line start.
    quick = [
        line for line in text.splitlines()
        if line.startswith("`/") and "`/create-spec`, " in line
    ]
    assert len(quick) == 1, quick
    listed = re.findall(r"`([^`]+)`", quick[0])
    assert "/writ-design" in listed and OLD_SLASH not in listed, listed

    note = section(text, "## Maintainer Note: Command Allowlist")
    # The bare list opens with `writ` too, so anchor on the `create-spec`
    # token rather than the line start.
    bare = [
        line for line in note.splitlines()
        if line.startswith("`") and "`create-spec`, " in line
    ]
    assert len(bare) == 1, bare
    listed = re.findall(r"`([^`]+)`", bare[0])
    assert "writ-design" in listed and OLD_NAME not in listed, listed


def test_cursor_tree():
    """AC-2.3: the `adapters/cursor.md` directory tree lists
    `writ-design.md` in sorted position (last, `└──`), lists one file per
    manifest command with the count in its header, and keeps the comment
    column aligned."""
    # Sorted by command name, as the manifest is: `writ` precedes `writ-design`
    # by name while `writ.md` would follow `writ-design.md` by file name.
    manifest = [
        Path(str(entry["file"])).name
        for entry in sorted(
            manifest_commands(read(".writ/manifest.yaml")), key=lambda e: str(e["name"]))
    ]
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
    # `/why` (why-command spec, Story 2) sorts between the two.
    assert commands[-3:] == ["`/verify-spec`", "`/why`", "`/writ-design`"], commands
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
# blind OLD_SLASH -> `/writ-design` replace would rewrite it.
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


# ---------------------------------------------------------------------------
# Reference gate section (Story 3 of 2026-10-20-platform-neutral-names): no
# tracked file outside the record list names the old command. Naming the spec
# here keeps the AC citations below attributed to it.
# ---------------------------------------------------------------------------

OLD_MD = OLD_NAME + ".md"
# technical-spec.md → Reference Gate, steps 3 and 5. Built from the old-name
# parts so this file is not a hit of its own gate.
GATE_CMD = re.compile(r"(?<![\w-])" + re.escape(OLD_SLASH) + r"(?![\w-])")
GATE_FILE = re.compile(r"(?<![\w-])" + re.escape(OLD_MD))
GATE_NATIVE = re.compile(r"native\s+`?" + re.escape(OLD_SLASH) + r"(?![\w-])", re.I)


def writ_design_refs(root: Path) -> List[str]:
    """Tracked lines under `root` that name the old command, as
    `path:line: text`.

    Greps tracked text files for the old slash name or the old file name
    (fixed strings, the same match as the spec's escaped-dot regex). Keeps a
    hit whose text names the command (GATE_CMD) or its file (GATE_FILE), then
    drops record paths and lines that name Claude Code's native command
    (GATE_NATIVE). `git grep` exit 1 means no hits; any other error raises.
    """
    refs = []  # type: List[str]
    for path, line, text in git_grep(root, OLD_SLASH, OLD_MD):
        if not (GATE_CMD.search(text) or GATE_FILE.search(text)):
            continue
        if is_record(path) or GATE_NATIVE.search(text):
            continue
        refs.append("%s:%s: %s" % (path, line, text))
    return refs


# (path, line text, reported). The fixture repo for test_gate_fixture: each
# file holds its text on line 3. Every text is built from the old-name parts.
GATE_FIXTURE = [
    ("commands/a.md", "Run `%s` to draw a wireframe." % OLD_SLASH, True),
    ("commands/b.md", "The command file is `%s`." % OLD_FILE, True),
    # "native" elsewhere on the line does not exempt it.
    ("commands/f.md", "`%s` uses native browser tools." % OLD_SLASH, True),
    # Only the three named snapshots are exempt in `.writ/docs/`.
    (".writ/docs/other.md", "Draw the screens with %s first." % OLD_SLASH, True),
    ("commands/c.md", "Read `%s` first." % DESIGN_SYSTEM_PATH, False),
    ("commands/d.md", "Run `/writ-design`; its file is `%s`." % NEW_FILE, False),
    ("commands/e.md", "Locks a contract (spec/ADR/roadmap%s)." % OLD_SLASH, False),
    ("adapters/x.md", "Claude Code's native `%s` is the platform's own command." % OLD_SLASH, False),
    ("CHANGELOG.md", "- `%s` is renamed to `/writ-design`." % OLD_SLASH, False),
    (".writ/docs/swot-2026-03-01.md", "| `%s` | Visual design companion |" % OLD_SLASH, False),
    # A snapshot path with a space: `--null` keeps it whole.
    (
        ".writ/explanations/2026-03-20-WritPipelineArchitecture .md",
        '    DESIGN["%s"] -.->|mockups| SPEC' % OLD_SLASH,
        False,
    ),
    (".writ/specs/2026-10-20-platform-neutral-names/spec.md", "Rename `%s`." % OLD_SLASH, False),
    (".writ/specs/2026-01-01-other/spec.md", "Use `%s` for the mockups." % OLD_SLASH, False),
]


def git_in(repo: Path, *args: str) -> None:
    proc = subprocess.run(
        ["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode == 0, "git %s failed: %s" % (
        " ".join(args), proc.stderr.decode("utf-8", "replace"))


@pytest.fixture
def isolated_git(tmp_path, monkeypatch):
    """Git sees only repos under tmp_path: no parent repo, no inherited
    GIT_DIR or index from a hook that runs the suite."""
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    ceilings = {str(tmp_path), str(tmp_path.resolve())}
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", ":".join(sorted(ceilings)))
    return tmp_path


def test_no_writ_design_reference():
    """AC-3.4: no tracked file outside the record list names the old command
    by slash name or file name."""
    refs = writ_design_refs(REPO_ROOT)
    assert refs == [], "%d line(s) still name %s or %s outside the record list:\n%s" % (
        len(refs), OLD_SLASH, OLD_FILE, "\n".join(refs))


def test_gate_fixture(isolated_git):
    """AC-3.4: in a fixture repo the gate reports exactly the four planted
    references, as `path:line: text`, and ignores the keep-class lines, the
    native-command line, and the record paths."""
    repo = isolated_git / "fixture"
    repo.mkdir()
    git_in(repo, "init", "-q")
    for rel, text, _ in GATE_FIXTURE:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Fixture\n\n%s\n" % text, encoding="utf-8")
    git_in(repo, "add", "-A")

    # Every planted file is a raw grep hit, so each ignored line is dropped
    # by the gate's filters, not missed by the grep.
    grepped = {hit[0] for hit in git_grep(repo, OLD_SLASH, OLD_MD)}
    assert grepped == {rel for rel, _, _ in GATE_FIXTURE}, sorted(grepped)

    expected = sorted("%s:3: %s" % (rel, text) for rel, text, reported in GATE_FIXTURE if reported)
    assert len(expected) == 4
    assert writ_design_refs(repo) == expected


def test_gate_git_error(isolated_git):
    """AC-3.4: a `git grep` error fails the gate instead of reading as no
    hits; a repo with no match (exit 1) is a clean result."""
    plain = isolated_git / "not-a-repo"
    plain.mkdir()
    (plain / "a.md").write_text("Run `%s`.\n" % OLD_SLASH, encoding="utf-8")
    with pytest.raises(RuntimeError, match=r"git grep failed \(exit \d+\): \S"):
        writ_design_refs(plain)

    clean = isolated_git / "clean"
    clean.mkdir()
    git_in(clean, "init", "-q")
    (clean / "a.md").write_text("Run `/writ-design`.\n", encoding="utf-8")
    git_in(clean, "add", "-A")
    assert writ_design_refs(clean) == []


SPEC_SLUG = "2026-10-20-platform-neutral-names"
SPEC_DIR = ".writ/specs/%s/" % SPEC_SLUG
LANE_BRANCH = "writ/phase/13/%s" % SPEC_SLUG
# (issue, phrases its Resolution must contain besides the spec and branch)
ISSUE_RESOLUTIONS = [
    (
        ".writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md",
        (
            "`canvas-preview`",
            "`adapters/cursor.md`",
            "`adapters/claude-code.md`",
            "`adapters/codex.md`",
            "`adapters/openclaw.md`",
            DEGRADATION_CLAUSE,
        ),
    ),
    (
        ".writ/issues/bugs/2026-10-19-design-command-name-collision.md",
        (
            "`/writ-design`",
            "Removed: %s" % OLD_FILE,
            "Stale (no longer shipped, locally modified — kept): %s" % OLD_FILE,
            "`scripts/tests/test_install_update_writ_design.sh`",
            "live Claude Code session",
        ),
    ),
]


@pytest.mark.parametrize(
    "rel, phrases", ISSUE_RESOLUTIONS, ids=[Path(r).stem for r, _ in ISSUE_RESOLUTIONS])
def test_issue_resolution(rel, phrases):
    """AC-3.5: the origin issue's last section is `## Resolution`; it names
    the date, this spec, the lane branch, and the fix; the issue's
    `spec_ref` points at this spec."""
    lines = read(rel).splitlines()
    assert lines.count("## Resolution") == 1, "%s: expected one '## Resolution' line" % rel
    body = lines[lines.index("## Resolution") + 1:]
    later = [line for line in body if re.match(r"^#{1,2} ", line)]
    assert later == [], "%s: Resolution is not the last section: %s" % (rel, later)
    text = "\n".join(body)
    for phrase in ("2026-10-21", "`%s`" % SPEC_SLUG, "`%s`" % LANE_BRANCH) + phrases:
        assert phrase in text, "%s: Resolution lacks %r" % (rel, phrase)

    refs = [line for line in lines if line.startswith("> **spec_ref:**")]
    assert refs == ["> **spec_ref:** %s" % SPEC_DIR], "%s: %s" % (rel, refs)


# ---------------------------------------------------------------------------
# Verification records (Story 1 of 2026-10-22-rendering-delegation-rows): the
# section that holds each adapter's tool table also carries a dated
# `#### Verification record` whose rows cite a first-party `https://` source
# and a status in the anchored grammar. Naming the spec here keeps the AC
# citations below attributed to it.
# ---------------------------------------------------------------------------

RECORD_HEADING = re.compile(r"^#### Verification record — \d{4}-\d{2}-\d{2}$")
# technical-spec.md → Verification Record Format. Anchored at both ends: a
# version or a reason outside the two parentheticals fails.
STATUS_GRAMMAR = re.compile(
    r"^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$"
)
RECORD_COLUMNS = ["Check", "Platform & version", "Observed", "Source", "Status"]

# (adapter, heading chain to the section that holds its tool table): the
# record lives in the same section as the `canvas-preview` row, so the
# chain is the one ADAPTER_TABLES already names. Story 1 covered
# `claude-code`; Story 2 (AC-2.2) covers the other three.
VERIFICATION_RECORDS = [(adapter, headings) for adapter, headings, _ in ADAPTER_TABLES]


def verification_record(text: str, *headings: str) -> List[str]:
    """The table under the first `#### Verification record — YYYY-MM-DD`
    heading inside the section `headings` names; `[]` when that section has
    no such heading. `first_table` on the section itself returns the tool
    table, so the search starts after the record heading."""
    lines = section(text, *headings).splitlines()
    for i, line in enumerate(lines):
        if RECORD_HEADING.match(line):
            return first_table("\n".join(lines[i + 1:]))
    return []




def check_record(adapter: str, table: List[str]) -> None:
    """Assert the record table's shape: the five record columns, at least one
    data row, five cells per row, a Status in the anchored grammar, and a
    Source starting with `https://`. Every message names the adapter and the
    failing cell."""
    assert cells(table[0]) == RECORD_COLUMNS, "%s: record columns are %s" % (
        adapter, cells(table[0]))
    rows = table[2:]
    assert rows, "%s: verification record has no data row" % adapter
    for row in rows:
        row_cells = cells(row)
        assert len(row_cells) == len(RECORD_COLUMNS), "%s: record row has %d cells: %r" % (
            adapter, len(row_cells), row)
        source, status = row_cells[3], row_cells[4]
        assert STATUS_GRAMMAR.match(status), "%s: Status %r does not match the status grammar" % (
            adapter, status)
        assert source.startswith("https://"), "%s: Source %r does not start with https://" % (
            adapter, source)


@pytest.mark.parametrize(
    "adapter, headings",
    VERIFICATION_RECORDS,
    ids=[Path(a).stem for a, _ in VERIFICATION_RECORDS],
)
def test_verification_records(adapter, headings):
    """AC-1.3, AC-1.5, AC-2.2, AC-2.5, AC-3.1: the adapter's tool-table section holds a dated
    verification record whose table has the five record columns and at
    least one data row; every Status cell matches the anchored status
    grammar and every Source cell starts with `https://`. No network: the
    source is checked for its prefix only."""
    table = verification_record(read(adapter), *headings)
    assert table, "%s: no '#### Verification record — YYYY-MM-DD' heading with a table under %s" % (
        adapter, headings[-1])
    check_record(adapter, table)


CLAUDE_CODE_RECORD = (
    "adapters/claude-code.md",
    ("## Tool Mapping (Cursor → Claude Code)", "### Quick Reference"),
)
CLAUDE_CODE_DOCS = "https://code.claude.com/docs/"
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")


def record_row(table: List[str], word: str) -> List[str]:
    """The one record row whose Check cell contains `word` (case-insensitive)."""
    hits = [cells(row) for row in table[2:] if word in cells(row)[0].lower()]
    assert len(hits) == 1, "expected one record row with %r in Check, found %d" % (word, len(hits))
    return hits[0]


def test_claude_code_record_checks():
    """AC-1.1, AC-1.2: the Claude Code record has one row each for the
    artifact attempt, the preview pane, the native design surface, and the
    headless no-renderer path. Every Source is a Claude Code docs page and
    every Platform cell names a version and the session kind; the headless
    row names the no-renderer clause."""
    table = verification_record(read(CLAUDE_CODE_RECORD[0]), *CLAUDE_CODE_RECORD[1])
    rows = [record_row(table, w) for w in ("artifact", "preview", "native design surface", "headless")]
    for row in rows:
        assert row[3].startswith(CLAUDE_CODE_DOCS), "Source %r is not a Claude Code docs page" % row[3]
        assert VERSION.search(row[1]), "Platform cell %r names no version" % row[1]
        assert "desktop" in row[1] or "terminal" in row[1], "Platform cell %r names no session kind" % row[1]
    assert "no-renderer" in rows[3][2], "headless row does not name the no-renderer clause"


def test_claude_code_canvas_row_states_facts():
    """AC-1.4: the Claude Code `canvas-preview` row keeps `artifact`,
    `preview pane`, and the degradation clause, and says nothing about
    verification; status lives in the record."""
    text = read(CLAUDE_CODE_RECORD[0])
    row = [line for line in text.splitlines() if line.startswith(CANVAS_ROW_PREFIX)]
    assert len(row) == 1, "expected one canvas-preview row, found %d" % len(row)
    assert "artifact" in row[0] and "preview pane" in row[0], row[0]
    assert cells(row[0])[-1].endswith(DEGRADATION_CLAUSE), row[0]
    assert "verified" not in row[0], row[0]


RENDERING_SPEC = ".writ/specs/2026-10-22-rendering-delegation-rows"
UAT_HEADING = "## UAT Protocols (maintainer, Story 2 writes; `/create-uat-plan` derives scenarios)"
UAT_FIELDS = ("- **Precondition:**", "- **Run:**", "- **Look for:**", "- **On pass", "- **On fail")
SAMPLE_IDEA = '"a settings page with a dark-mode toggle"'


def canvas_row(text: str) -> str:
    rows = [line for line in text.splitlines() if line.startswith(CANVAS_ROW_PREFIX)]
    assert len(rows) == 1, "expected one canvas-preview row, found %d" % len(rows)
    return rows[0]


def test_cursor_row_names_the_floor():
    """AC-2.1: the Cursor pages the record cites document no canvas that
    renders a local HTML file, so the Cursor row names the HTML-file floor,
    drops the old tool name, and keeps the degradation clause; the record's
    Sources are Cursor docs pages."""
    text = read("adapters/cursor.md")
    row = canvas_row(text)
    assert CURSOR_TOOL not in row, row
    assert PROTOTYPES_DIR in row and "HTML" in row, row
    assert cells(row)[-1].endswith(DEGRADATION_CLAUSE), row
    table = verification_record(text, "## Native Tool Availability")
    sources = [cells(r)[3] for r in table[2:]]
    assert sources and all(s.startswith("https://cursor.com/docs/") for s in sources), sources


def test_codex_row_has_cli_and_desktop_clauses():
    """AC-2.3: the Codex row's mapping cell reads a "CLI:" clause and then a
    "Desktop:" clause; the CLI clause keeps the HTML-file floor text."""
    mapping = cells(canvas_row(read("adapters/codex.md")))[1]
    cli = "CLI: `Write` one self-contained HTML file per draft to `%s`." % PROTOTYPES_DIR
    assert mapping.startswith(cli), mapping
    assert " Desktop: " in mapping, mapping


@pytest.mark.parametrize("platform", ["Cursor", "Codex Desktop"])
def test_uat_protocol(platform):
    """AC-2.4: each UAT protocol states a precondition, a `--diverge` run on
    the shared sample idea, what to look for, and the record edit on pass and
    on fail; the on-pass edit writes `verified <date>` in Status and the
    version in the Platform & version cell."""
    body = section(read(RENDERING_SPEC + "/sub-specs/technical-spec.md"), UAT_HEADING, "### " + platform)
    for field in UAT_FIELDS:
        assert field in body, "%s protocol lacks %r" % (platform, field)
    lines = body.splitlines()
    run = [l for l in lines if l.startswith("- **Run:**")][0]
    assert "--diverge " + SAMPLE_IDEA in run, run
    on_pass = [l for l in lines if l.startswith("- **On pass")][0]
    assert "`verified <date>`" in on_pass and "Platform & version" in on_pass, on_pass


RECORD_HEADER = "| Check | Platform & version | Observed | Source | Status |\n|---|---|---|---|---|\n"


@pytest.mark.parametrize(
    "row, message",
    [
        (
            "| Render | Cursor 2.3 | not documented | not documented | unverified 2026-10-22 (pending UAT) |",
            "cursor: Source 'not documented' does not start with https://",
        ),
        (
            "| Render | Cursor 2.3 | rendered | https://cursor.com/docs/ | verified |",
            "cursor: Status 'verified' does not match the status grammar",
        ),
        (
            "| Render | Cursor 2.3 | rendered | https://cursor.com/docs/ | verified 2026-10-22, Cursor 2.3 |",
            "cursor: Status 'verified 2026-10-22, Cursor 2.3' does not match the status grammar",
        ),
    ],
    ids=["source-not-documented", "status-without-date", "status-with-version"],
)
def test_check_record_rejects_bad_cells(row, message):
    """AC-3.1, AC-3.2: `check_record` rejects a Source of `not documented`
    and a Status without a date or with a version appended, naming the
    adapter and the failing cell; a record with no data row is rejected too."""
    with pytest.raises(AssertionError) as err:
        check_record("cursor", (RECORD_HEADER + row).splitlines())
    assert str(err.value).startswith(message), str(err.value)
    with pytest.raises(AssertionError, match="cursor: verification record has no data row"):
        check_record("cursor", RECORD_HEADER.splitlines())


def test_prototype_render_table_reconciled():
    """AC-3.3, AC-3.4: no recorded observation contradicts a Step 2.5
    render-table row, so `commands/prototype.md` keeps its three labels in
    order, names no vendor tool, and the spec's drift log has no DEV entry
    for a render-table change."""
    text = read("commands/prototype.md")
    assert CURSOR_TOOL not in text
    render = section(text, "### Step 2.5: Diverge & Choose", "#### Render through the platform")
    labels = [cells(row)[0] for row in first_table(render)[2:]]
    assert labels == [
        "Native artboard/design surface",
        "`canvas-preview` (the adapter maps it)",
        "Neither",
    ], labels
    titles = [l for l in read(RENDERING_SPEC + "/drift-log.md").splitlines() if l.startswith("#### [DEV-")]
    assert not any("prototype.md" in t or "Step 2.5" in t for t in titles), (
        "drift log has a Step 2.5 entry but commands/prototype.md is unchanged: %s" % titles)


def test_issue_verification_note():
    """AC-3.5: the origin issue's `## Resolution` section ends with a
    `### Verification` subsection naming this spec and each adapter's
    recorded status."""
    lines = read(ISSUE_RESOLUTIONS[0][0]).splitlines()
    body = lines[lines.index("## Resolution") + 1:]
    assert body.count("### Verification") == 1, body
    note = "\n".join(body[body.index("### Verification") + 1:])
    assert "`2026-10-22-rendering-delegation-rows`" in note
    for adapter, statuses in (
        ("adapters/claude-code.md", ("verified 2026-10-22",)),
        ("adapters/cursor.md", ("unverified 2026-10-22 (pending UAT)",)),
        ("adapters/codex.md", ("CLI clause verified 2026-10-24", "unverified 2026-10-22 (pending UAT)")),
        ("adapters/openclaw.md", ("unverified 2026-10-22 (no deployment)",)),
    ):
        line = [l for l in note.splitlines() if l.startswith("- `%s`" % adapter)]
        assert len(line) == 1, "%s: expected one status line, found %d" % (adapter, len(line))
        for status in statuses:
            assert status in line[0], line[0]
