#!/usr/bin/env python3
"""Generate the per-platform trees from source (spec `2026-10-22-generated-platform-trees`).

    python3 scripts/gen-platform-trees.py                  # write all identity targets and the plugin in place
    python3 scripts/gen-platform-trees.py --check          # report stale|missing|orphan|unmapped|vendor|malformed; write nothing
    python3 scripts/gen-platform-trees.py coverage         # unmapped + vendor only
    python3 scripts/gen-platform-trees.py --target fixture --out-dir <dir>   # commands/ + skills/ with the fixture script root
    python3 scripts/gen-platform-trees.py --target claude-code-plugin [--out-dir <dir>]   # the Claude Code plugin only

Dev-only (it reads adapters/*.md and .writ/manifest.yaml, which installed
projects do not have); never hand-edit a generated file. Story 1 ships the
adapter tool-table parser and the vocabulary rule; Story 2 the capability
map, `cursor/writ.mdc`, and write mode; Story 3 `codex/AGENTS.md.template`;
Story 4 `--check`, `coverage`, the vendor scan, and the targets.

Check shape: line 1 `pass`/`fail`/`unverifiable`, `reason: <kind> <detail>`
lines, `wrote <path>` lines in write mode, then `removed <path>` lines (an
orphan file write mode deleted from the plugin tree), then the summary: write mode and
a target print `gen-platform-trees: <verdict> (<n> written, <r> reasons)`;
`--check` and `coverage` print `gen-platform-trees: <verdict> (<s> stale,
<m> missing, <o> orphan, <u> unmapped, <v> vendor)`, counting own and folded
reasons by kind (a folded reason's kind is the token after `<gen>: `) and 0
for a kind the mode does not check. Exit 0 pass or unverifiable, 1 fail, 2
usage. Nothing is written when any reason exists.

`--check` (spec.md -> Rule 1, AC-4.1), in order, writing nothing: the four
adapters and `unmapped`, as in coverage; when every table parsed, each
GENERATED file is rendered in memory and compared byte for byte with disk
(`stale <path>` when they differ, `missing <path>` when there is no file; a
source OSError is `unverifiable`, `missing <source path>`; a ValueError is
`fail` with its text), then each sub-generator's `--check` runs: an exit of 2
or more, or no verdict, is `fail`, `<gen> --check exited <rc>`; an
`unverifiable` verdict makes the run `unverifiable`; the reasons that name
this driver's own files are translated to its kinds (gen-claude-md `stale
claude-code/CLAUDE.md` -> `stale claude-code/CLAUDE.md`, `absent
claude-code/CLAUDE.md` -> `missing claude-code/CLAUDE.md`; gen-claude-agents
`orphan <stem>` -> `orphan claude-code/agents/<stem>.md`; gen-codex-agent-tomls
`orphan <stem>` -> `orphan codex/agents/<stem>.toml`) and every other reason
folds as `<gen>: <kind> <detail>` (TRANSLATED); then the plugin tree (below:
Claude Code plugin). gen-claude-agents' orphan
check sees only `writ-*.md`, so a `claude-code/agents/*.md` with another
name is reported by the driver itself as `orphan claude-code/agents/<name>`
(`stray_agent_reasons`): no generator produces it, and `install.sh` ships
every file in that directory. Last, the vendor scan. The renders and the
sub-generator checks are skipped when a table did not parse, because they
read the same tables and would repeat the parser's reason.

`coverage` (spec.md -> Rules 3 and 4, AC-4.2): the four adapters' own
reasons, `unmapped`, and the vendor scan; nothing else; nothing written.

Vendor scan (`vendor_hits`): every line of commands/*.md, agents/*.md, and
skills/*/SKILL.md, in that order and sorted within each, is searched for
single-backticked tokens; a token references a tool (`tool_reference`) when
its leading identifier, normalized like a first-column cell, is followed by
nothing or by call syntax (`(` or `{`): `` `TodoWrite` ``, `` `Grep("p")` ``,
and `` `sessions_spawn({ task })` `` reference TodoWrite, Grep, and
sessions_spawn; `` `message.usage` `` (a field), `` `http://x` ``, a path, a
`key: value`, or a flag reference none. A referenced vendor-only name is
`vendor <name> in <path>:<line>` (1-based), once per name, file, and line.
An allowlisted bare verb (`` `Read` ``) is never vendor-only. Write mode runs
the scan among its pre-checks, so a hit blocks a write.

Targets (spec.md -> Rule 11, AC-4.3): TARGETS maps a name to its
`script_root`. `--target <identity>` (root `scripts`: cursor, claude-code,
codex) runs write mode restricted to that platform's generated files and
sub-generators and never writes a commands/ or skills/ copy. `--target
fixture --out-dir <dir>` (root `${PLUGIN_ROOT}/scripts`, tests only) runs
`emit_tree`: every commands/*.md and skills/*/SKILL.md is copied as bytes to
`<dir>/fixture/<same path>` with each TOKEN match, `(python3|bash)
scripts/<name>.py|.sh`, rewritten to the same interpreter and
`<script_root>/<name>` and every other byte unchanged; one `wrote
<dir-relative path>` line per file; nothing in place. `--target
claude-code-plugin` (root `${CLAUDE_PLUGIN_ROOT}/scripts`) is write mode
restricted to the plugin tree, in place or, with --out-dir, under <dir> at
the same repository-relative paths. An identity target with --out-dir, the
fixture target without it, --target beside --check or coverage, or --out-dir
alone is a usage error (exit 2).

Write mode (spec.md -> Rule 1; technical-spec.md -> ## Driver CLI), in
order: parse the four adapters (a table that is not `pass` ends the run with
its verdict and reasons); `unmapped` names end it with `fail`; so do vendor
hits and, when gen-claude-agents is among the sub-generators, stray
`claude-code/agents/*.md` files (`stray_agent_reasons`); each
sub-generator's `--check` runs (SUBGENERATORS, as subprocesses from this
tree): an exit of 2 or more, or a first line that is not a verdict, is
`reason: <gen> --check exited <rc>`; an `unverifiable` verdict makes the run
`unverifiable`; every other `reason: <kind> <detail>` line folds in as
`reason: <gen>: <kind> <detail>`, except the output-state kinds in
REPAIRED_KINDS (`stale`, `missing`, `absent`, `extra`), which are what a
write repairs. With no reason left, each GENERATED file is rendered, and the
plugin tree when the run writes it (no --target, or --target
claude-code-plugin); a render error ends the run before any write. Each
GENERATED file is written through a temp file plus os.replace (`wrote
<path>`), then the sub-generators run in write mode and their `wrote` lines
are relayed; one that exits non-zero ends the run with `fail`, `reason: <gen>
exited <rc>`, and its folded reasons. Last, every plugin file is written the
same way and every orphan under plugins/writ/ is deleted (`removed <path>`).
Before the first write, a run that writes the plugin refuses a symlink at
`.claude-plugin/`, `plugins/`, `plugins/writ/`, the marketplace file, or
anywhere under `plugins/writ/` (`reason: symlink <path>`, walked without
following links), and a rendered file whose resolved path is not the one it
names (`reason: outside <path>`): verdict `fail`, nothing written or deleted.
Each write and delete re-checks its own path.

Claude Code plugin (spec `2026-10-22-plugin-distribution`, Story 2; its
technical-spec.md -> Candidate Layouts, Decision: layout B). The
`claude-code-plugin` target renders `.claude-plugin/marketplace.json` (name
`writ`, a description, `owner.name`, one entry with source `./plugins/writ`) and the plugin
under `plugins/writ/` (`render_plugin`):

- `.claude-plugin/plugin.json`: name, `version` read from VERSION,
  description, author, repository, license, `commands` (every
  `./commands/<x>.md` but `_preamble.md`, which would otherwise register as
  `/writ:_preamble`; the key replaces the default scan) and `agents` (the
  generated Claude agents, so the prompt-template docs beside them never load
  as agents). Fixed key order, two-space indent, one trailing newline.
- `commands/*.md` (the preamble included), `agents/*.md` (the prompt-template
  docs and gen-claude-agents.py's render of each, from agents/<stem>.md and
  its overlay, not from claude-code/agents/ on disk), and
  `skills/<name>/SKILL.md`: the YAML frontmatter verbatim, the generated-file
  comment, then the body with the token classes rewritten
  (`rewrite_plugin_body`). Bodies only: Claude Code substitutes
  `${CLAUDE_PLUGIN_ROOT}` in a body, not in frontmatter.
- `scripts/`: byte copies, modes kept, of the top-level scripts/ files
  `is_shippable_script` admits (install.sh's rule, mirrored); no dev-only
  script and no tests/.
- `system-instructions.md` with the comment after its frontmatter, and the
  Prime Directive carrier `output-styles/writ.md`: CARRIER_FRONTMATTER (the
  generated-file note is a YAML comment there) + the body of
  system-instructions.md after its frontmatter, byte for byte.

The scripts and the two JSON files carry no comment: a comment would change a
byte copy or break strict JSON. `--check` covers every file: `stale <path>`
(bytes differ, or a symlink stands where a file belongs), `missing <path>`,
and `orphan <path>` for a file under plugins/writ/ that no render produces
(`__pycache__/`, `*.pyc`, and `.DS_Store`, which .gitignore drops, excepted).
The orphan scan never follows a symlink: a linked `plugins/` or
`plugins/writ/` is the one orphan, a linked directory below is an orphan not
descended, and a rendered path with a link on it is `stale`.

Token classes (technical-spec.md -> Relative Path Inventory), applied line by
line, skipping a whole-line HTML comment (`<!-- ... -->`, such as the
gen-claude-agents header, whose regenerate command names the Writ repository),
in this order, each to a match that no path character (`[A-Za-z0-9_./-]`) precedes,
so `.claude/agents/<x>.md`, `$WRIT_SRC/system-instructions.md`, a URL
segment, and a class's own output never match: `script-root` and
`script-path` (`[../]scripts/<shipped name>`, interpreter or not, to
`${CLAUDE_PLUGIN_ROOT}/scripts/<name>`; dev-only and unknown names stay),
`agent-path` (`[../]agents/<x>.md` for a file the plugin's agents/ holds),
`skill-path` (`[../]skills/<x>/SKILL.md`), `preamble-path`
(`[../]commands/_preamble.md` and a bare `_preamble.md`), each to
`${CLAUDE_PLUGIN_ROOT}/<path>`, `instructions-path` (a Markdown link whose
target is `[../]system-instructions.md`: the target and the name in its text;
a bare mention names an installed file and stays), and
`command-ref` (`/<command>` to `/writ:<command>`, unless followed by a
word character, `-`, `:`, `/`, or `.` plus a word character). A second pass
changes nothing.

Capability map (spec.md -> Rule 5; technical-spec.md -> ## Capability Map
Section): `render_map` turns a parsed table into the `## Capability Map`
section, one row per table row in adapter order, the mapping cell verbatim,
and the "When unavailable" cell from `degradation`: the first sentence of
the notes cell (split at `. `, `! `, `? `) that starts with `No renderer:`,
`If the platform`, or `No agent-side`, else `—`. `capability_map(adapter,
root)` parses `root/adapters/<adapter>.md` and raises ValueError with the
reasons when the table is not `pass`; gen-claude-md.py loads it by path for
its `{capability_map}` slot.

`cursor/writ.mdc` (spec.md -> Rule 6) = `---\nalwaysApply: true\n---\n` +
the generated-file comment (Rule 12) + the body of system-instructions.md
with only its leading frontmatter block removed + a blank line + the Cursor
map; its `## Prime Directive` section is therefore byte-equal to the
source's (eval.sh check_prime_directive_sync).

`codex/AGENTS.md.template` (spec.md -> Rule 8) = the merge-marker line that
install.sh merge_agents_md and update.sh rely on (CODEX_MARKER, byte-identical
to the hand-maintained file's line 1), the generated-file comment, then one
`## ` section per AC-3.2 in order: `## Writ on Codex`; `## Available
Commands`, one `### <label>` table per manifest category that has commands,
categories and rows in manifest order, purposes verbatim, path
`.codex/commands/<name>.md`; `## Available Agents` (`.codex/agents/<name>.toml`);
`## Available Skills`, every skills/*/SKILL.md with its frontmatter
description and path `.agents/skills/<name>/SKILL.md`; the built-ins
paragraph (CODEX_BUILTINS, a literal); the Codex map; `## Catalog source`.
Sections are separated by one blank line. The manifest is read line by line
(`read_manifest`, after gen-claude-md.py's reader; no YAML library on the 3.9
floor). `render_codex_template` raises ValueError, which write mode reports
as `fail`, when a manifest section or an entry's name, label, category, or
purpose is missing, a command's category is undeclared, a SKILL.md has no
description, the render reaches CODEX_TEMPLATE_CAP bytes (Codex may truncate
a long AGENTS.md), or the text mentions `adapters/` (an installed project has
none); a missing manifest or skills/ directory is `unverifiable`, `missing
<path>`.

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
import errno
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, NamedTuple, Optional, Set, Tuple, Union

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_DIR = ROOT / "adapters"
ADAPTERS = ("cursor", "claude-code", "codex", "openclaw")
SYSTEM_INSTRUCTIONS = "system-instructions.md"
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
# Capability map section (technical-spec.md -> ## Capability Map Section).
MAP_LEAD = "Commands name capabilities; this table maps them to this platform."
MAP_HEADER = ("| Capability | On this platform | When unavailable |", "|---|---|---|")
# A notes-cell sentence that starts with one of these is the degradation text.
DEGRADATION_OPENERS = ("No renderer:", "If the platform", "No agent-side")
SENTENCE_END = re.compile(r"(?<=[.!?]) ")
NO_DEGRADATION = "\u2014"
WRIT_MDC_FRONTMATTER = "---\nalwaysApply: true\n---\n"
# Generated-file comment (spec.md -> Rule 12); the agent generators keep their own.
COMMENT = "<!-- generated by scripts/gen-platform-trees.py from %s \u2014 do not hand-edit; regenerate -->\n"
# The sub-generators write mode checks, then runs, as `scripts/<name>.py`,
# producers before consumers: gen-claude-md reads claude-code/agents/*.md,
# which gen-claude-agents writes, so one run converges.
SUBGENERATORS = ("gen-claude-agents", "gen-codex-agent-tomls", "gen-claude-md")
VERDICTS = ("pass", "fail", "unverifiable")
# Reason kinds from a sub-generator's --check that describe its outputs, not
# its inputs: a write regenerates them, so write mode drops them silently.
REPAIRED_KINDS = frozenset({"stale", "missing", "absent", "extra"})
Reason = Tuple[str, str]  # (verdict class: fail | unverifiable, text without the `reason: ` prefix)


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


# ---------------------------------------------------------------------------
# Vendor scan
# ---------------------------------------------------------------------------

# (directory, glob) of the shipped text the vendor scan reads, in report order.
SCANNED = (("commands", "*.md"), ("agents", "*.md"), ("skills", "*/SKILL.md"))


def tool_reference(token: str) -> Optional[str]:
    """The tool a backticked token references: its leading identifier
    (`capability_name`'s rule) when the rest of the token is empty or call
    syntax starting with `(` or `{`; None when the rest starts with anything
    else (`message.usage` is a field, `scripts/x.py` a path, `http://x` a
    URL, `key: value` a key, `exec=1` an assignment) or when there is no
    identifier (`--check`, an empty token)."""
    text = token.strip()
    match = NAME_RE.match(text)
    if not match:
        return None
    rest = text[match.end():]
    if rest and rest[0] not in "({":
        return None
    return match.group(0).rstrip()


def vendor_hits(root: Path, vendor_only: Set[str]) -> List[str]:
    """`vendor <name> in <path>:<line>` for each vendor-only name a
    single-backticked token references in SCANNED, one per name, file, and
    1-based line; files in SCANNED order, sorted within each directory."""
    out = []  # type: List[str]
    for folder, pattern in SCANNED:
        for path in sorted((Path(root) / folder).glob(pattern)):
            rel = path.relative_to(root).as_posix()
            text = path.read_bytes().decode("utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), 1):
                seen = []  # type: List[str]
                for token in BACKTICK.findall(line):
                    name = tool_reference(token)
                    if name in vendor_only and name not in seen:
                        seen.append(name)
                        out.append("vendor %s in %s:%d" % (name, rel, number))
    return out


# ---------------------------------------------------------------------------
# Capability map and generated files
# ---------------------------------------------------------------------------


def degradation(notes: str) -> str:
    """The "When unavailable" cell for a notes cell: its first sentence
    (split at `. `, `! `, `? `) that starts with one of DEGRADATION_OPENERS,
    terminal punctuation kept; `\u2014` when none does."""
    for sentence in SENTENCE_END.split(notes.strip()):
        if sentence.startswith(DEGRADATION_OPENERS):
            return sentence
    return NO_DEGRADATION


def render_map(table: AdapterTable) -> str:
    """The `## Capability Map` section for a parsed table: the lead
    sentence, the header, one row per table row in adapter order. A name's
    first row has `` `<name>` `` in column 1; each further variant of the
    same name (a second `Task` row) is a sub-row with `` `<variant text>` ``.
    The mapping cell is verbatim. Ends with exactly one newline."""
    lines = ["## Capability Map", "", MAP_LEAD, ""] + list(MAP_HEADER)
    seen = set()  # type: Set[str]
    for row in table.rows:
        first = row.variant if row.name in seen else row.name
        seen.add(row.name)
        lines.append("| `%s` | %s | %s |" % (first, row.mapping, degradation(row.notes)))
    return "\n".join(lines) + "\n"


def capability_map(adapter: str, root: Path) -> str:
    """`render_map` of `root/adapters/<adapter>.md`. Raises ValueError whose
    message is the table's reasons joined by `; ` when the table is not
    `pass`, so no caller embeds a partial map."""
    table = parse_adapter(Path(root) / "adapters" / (adapter + ".md"), adapter)
    if table.verdict != "pass":
        raise ValueError("; ".join(table.reasons))
    return render_map(table)


def split_frontmatter(text: str) -> Tuple[str, str]:
    """(the leading `---\n...\n---\n` block, the rest); ("", text) when there
    is none. Every byte lands in one of the two."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[:end + 5], text[end + 5:]
    return "", text


def strip_frontmatter(text: str) -> str:
    """`text` without its leading `---\n...\n---\n` block; every other byte
    stays, so a body that opened with a blank line still does."""
    return split_frontmatter(text)[1]


def render_writ_mdc(root: Path) -> str:
    """`cursor/writ.mdc` (spec.md -> Rule 6): the alwaysApply frontmatter, the
    generated-file comment, the system-instructions.md body with only its
    frontmatter removed, a blank line, then the Cursor map."""
    body = strip_frontmatter((Path(root) / SYSTEM_INSTRUCTIONS).read_text(encoding="utf-8"))
    if not body.endswith("\n"):
        body += "\n"
    comment = COMMENT % (SYSTEM_INSTRUCTIONS + " and adapters/cursor.md")
    return WRIT_MDC_FRONTMATTER + comment + body + "\n" + capability_map("cursor", root)


# ---------------------------------------------------------------------------
# codex/AGENTS.md.template
# ---------------------------------------------------------------------------

MANIFEST_REL = ".writ/manifest.yaml"
SKILLS_DIR = "skills"
# Byte cap on the rendered template (spec.md -> Rule 8). Codex's AGENTS.md
# budget is 32 KiB; the cap is tighter on purpose.
CODEX_TEMPLATE_CAP = 16384
# Line 1 of the template. install.sh merge_agents_md and update.sh merge the
# file between the writ:start/writ:end markers and this line names the file
# as the source of truth; it stays byte-identical to the hand-maintained
# file's line 1. Line 2, the generated-file comment, says to regenerate.
CODEX_MARKER = (
    "<!-- Writ-managed AGENTS.md fragment: merged between HTML comment markers "
    "writ:start and writ:end by install/update scripts. Source of truth: "
    "codex/AGENTS.md.template in the Writ repository (edit there, not by hand in "
    "downstream AGENTS.md). -->")
# Rule 12 `<sources>`. The Codex adapter is named without its path: the
# generated file must not mention adapters/, which an installed project
# does not have (AC-3.2, AC-5.2).
CODEX_SOURCES = ".writ/manifest.yaml, skills/*/SKILL.md, and the Codex adapter tool table"
CODEX_INTRO = (
    "Writ uses `.writ/` for specs and artifacts, `.codex/commands/*.md` for workflows, "
    "`.codex/agents/*.toml` for subagents, `.agents/skills/` for AgentSkills-format "
    "capabilities. Read bundled `system-instructions.md` for Writ identity; map tools "
    "with the Capability Map below.")
# The hand-maintained file's paragraph, verbatim (story 3 Notes -> Built-ins literal).
CODEX_BUILTINS = (
    "Codex built-ins include `/plan`, `/review`, `/status`, `/init`, `/agent`, `/fork`, "
    "`/side`, and more ([official list](https://developers.openai.com/codex/cli/slash-commands)). "
    "Writ keeps its own `/plan`-style command files under `.codex/commands/` and does **not** "
    "rename them. Bare `/status` or `/review` in the Codex UI runs Codex's built-in. To execute "
    "**Writ's** `/status` or `/review` workflows, ask explicitly to load and follow the Markdown "
    "in `.codex/commands/status.md` or `.codex/commands/review.md`.")
CODEX_CATALOG_SOURCE = (
    "Command and agent metadata also lives in `.writ/manifest.yaml` (upstream Writ repo). "
    "Regenerate root `SKILL.md` with `scripts/gen-skill.sh` when extending the manifest.")
COMMAND_TABLE = ("| Command | File | Purpose |", "|---------|------|---------|")
AGENT_TABLE = ("| Agent | TOML | Purpose |", "|-------|------|---------|")
SKILL_TABLE = ("| Skill | File | Description |", "|-------|------|-------------|")


class Manifest(NamedTuple):
    categories: List[Tuple[str, str]]     # (id, label), manifest order
    commands: List[Tuple[str, str, str]]  # (name, category id, purpose), manifest order
    agents: List[Tuple[str, str]]         # (name, purpose), manifest order


def parse_value(raw: str) -> Optional[str]:
    """A one-line YAML scalar, quoted or bare (gen-claude-md.py's reader).
    None for a broken quote."""
    raw = raw.strip()
    if raw.startswith('"'):
        m = re.match(r'"((?:[^"\\]|\\.)*)"\s*(#.*)?\Z', raw)
        return re.sub(r'\\(["\\])', r"\1", m.group(1)) if m else None
    if raw.startswith("'"):
        m = re.match(r"'((?:[^']|'')*)'\s*(#.*)?\Z", raw)
        return m.group(1).replace("''", "'") if m else None
    return re.sub(r"\s+#.*\Z", "", raw).strip()


def manifest_entries(lines: List[str], key: str, head: str) -> List[Dict[str, Optional[str]]]:
    """Entries of the manifest's top-level `<key>:` list: each starts with
    `  - <head>:` and continues with `    <field>:` lines; the list ends at
    the next unindented, non-comment line. ValueError `manifest no <key>
    section` when the key is absent, `manifest no <key>` when it is empty."""
    start = next((i for i, line in enumerate(lines)
                  if re.match(r"%s:\s*(#.*)?\Z" % re.escape(key), line)), None)
    if start is None:
        raise ValueError("manifest no %s section" % key)
    entries = []  # type: List[Dict[str, Optional[str]]]
    for line in lines[start + 1:]:
        if line.strip() and not line[0].isspace() and not line.startswith("#"):
            break
        match = re.match(r"  - %s:(.*)\Z" % re.escape(head), line)
        if match:
            entries.append({head: parse_value(match.group(1))})
            continue
        match = re.match(r"    ([A-Za-z_][\w-]*):(.*)\Z", line)
        if match and entries:
            entries[-1].setdefault(match.group(1), parse_value(match.group(2)))
    if not entries:
        raise ValueError("manifest no %s" % key)
    return entries


def read_manifest(root: Path) -> Manifest:
    """Categories, commands, and agents of root/.writ/manifest.yaml, in
    manifest order, purposes verbatim. ValueError `manifest <detail>` for a
    missing section, a category without its id or label, a command or agent
    without its name or purpose, a command without a category or with one no
    `categories:` entry declares, or a duplicate command. A missing file is
    the OSError write mode reports as `missing .writ/manifest.yaml`."""
    lines = (Path(root) / MANIFEST_REL).read_text(encoding="utf-8").splitlines()
    categories = []  # type: List[Tuple[str, str]]
    for entry in manifest_entries(lines, "categories", "id"):
        if not entry.get("id"):
            raise ValueError("manifest category missing id")
        if not entry.get("label"):
            raise ValueError("manifest category %s missing label" % entry["id"])
        categories.append((entry["id"] or "", entry["label"] or ""))
    ids = {cid for cid, _ in categories}
    commands = []  # type: List[Tuple[str, str, str]]
    for entry in manifest_entries(lines, "commands", "name"):
        name = entry.get("name")
        if not name:
            raise ValueError("manifest command missing name")
        for field in ("category", "purpose"):
            if not entry.get(field):
                raise ValueError("manifest %s missing %s" % (name, field))
        if entry["category"] not in ids:
            raise ValueError("manifest %s category %s" % (name, entry["category"]))
        if any(name == seen for seen, _, _ in commands):
            raise ValueError("manifest duplicate %s" % name)
        commands.append((name, entry["category"] or "", entry["purpose"] or ""))
    agents = []  # type: List[Tuple[str, str]]
    for entry in manifest_entries(lines, "agents", "name"):
        name = entry.get("name")
        if not name:
            raise ValueError("manifest agent missing name")
        if not entry.get("purpose"):
            raise ValueError("manifest %s missing purpose" % name)
        agents.append((name, entry["purpose"] or ""))
    return Manifest(categories, commands, agents)


def read_skills(root: Path) -> List[Tuple[str, str]]:
    """(directory name, frontmatter `description:`) per root/skills/*/SKILL.md,
    sorted by directory name. ValueError `skill <name> missing description`
    when the value is absent or empty; a missing skills/ directory is the
    OSError write mode reports as `missing skills`."""
    folder = Path(root) / SKILLS_DIR
    if not folder.is_dir():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(folder))
    skills = []  # type: List[Tuple[str, str]]
    for path in sorted(folder.glob("*/SKILL.md"), key=lambda p: p.parent.name):
        text = path.read_text(encoding="utf-8")
        end = text.find("\n---\n", 4) if text.startswith("---\n") else -1
        match = re.search(r"^description:(.*)$", text[4:end], re.M) if end > 0 else None
        description = parse_value(match.group(1)) if match else None
        if not description:
            raise ValueError("skill %s missing description" % path.parent.name)
        skills.append((path.parent.name, description))
    return skills


def escape_cell(text: str) -> str:
    """A table cell: `|` escaped as `\\|`."""
    return text.replace("|", "\\|")


def render_codex_template(root: Path) -> str:
    """`codex/AGENTS.md.template` (module docstring -> codex/AGENTS.md.template).
    Writes nothing. ValueError `codex template <n> bytes exceeds <cap>` when
    the UTF-8 encoding reaches CODEX_TEMPLATE_CAP, `codex template mentions
    adapters/` when any source put that path into the text."""
    root = Path(root)
    manifest = read_manifest(root)
    skills = read_skills(root)
    codex_map = capability_map("codex", root)
    blocks = [
        CODEX_MARKER + "\n" + (COMMENT % CODEX_SOURCES).rstrip("\n"),
        "## Writ on Codex\n\n" + CODEX_INTRO,
        "## Available Commands",
    ]
    for cid, label in manifest.categories:
        rows = ["| `/%s` | `.codex/commands/%s.md` | %s |" % (name, name, escape_cell(purpose))
                for name, category, purpose in manifest.commands if category == cid]
        if rows:
            blocks.append("\n".join(["### " + label, ""] + list(COMMAND_TABLE) + rows))
    blocks.append("\n".join(["## Available Agents", ""] + list(AGENT_TABLE) + [
        "| %s | `.codex/agents/%s.toml` | %s |" % (name, name, escape_cell(purpose))
        for name, purpose in manifest.agents]))
    blocks.append("\n".join(["## Available Skills", ""] + list(SKILL_TABLE) + [
        "| `%s` | `.agents/skills/%s/SKILL.md` | %s |" % (name, name, escape_cell(description))
        for name, description in skills]))
    blocks.append("## Built-in Codex slash commands vs Writ\n\n" + CODEX_BUILTINS)
    blocks.append(codex_map.rstrip("\n"))
    blocks.append("## Catalog source\n\n" + CODEX_CATALOG_SOURCE)
    text = "\n\n".join(blocks) + "\n"
    size = len(text.encode("utf-8"))
    if size >= CODEX_TEMPLATE_CAP:
        raise ValueError("codex template %d bytes exceeds %d" % (size, CODEX_TEMPLATE_CAP))
    if "adapters/" in text:
        raise ValueError("codex template mentions adapters/")
    return text


# (relative path, renderer taking the tree root) per file the driver writes
# itself, in write order.
GENERATED = [
    ("cursor/writ.mdc", render_writ_mdc),
    ("codex/AGENTS.md.template", render_codex_template),
]  # type: List[Tuple[str, Callable[[Path], str]]]


def write_file(out: Path, data: Union[str, bytes], mode: Optional[int] = None) -> Optional[str]:
    """Write `data` (text as UTF-8, or bytes verbatim) through a temp file in
    the same directory and os.replace it over `out`, with `mode`, or by
    default `out`'s mode (0o644 for a new file). Returns the error text, or None."""
    if mode is None:
        mode = out.stat().st_mode & 0o777 if out.is_file() else 0o644
    tmp = None
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(out.parent), prefix="." + out.name + ".")
        with os.fdopen(fd, "wb") as handle:
            handle.write(data.encode("utf-8") if isinstance(data, str) else data)
        os.chmod(tmp, mode)
        os.replace(tmp, str(out))
    except OSError as err:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        return str(err)
    return None


# ---------------------------------------------------------------------------
# Targets and tokens
# ---------------------------------------------------------------------------

IDENTITY_SCRIPT_ROOT = "scripts"
# One entry per target (spec.md -> Rule 11; technical-spec.md -> ## Tokens).
# `script_root` replaces `scripts` in every TOKEN match. An identity target
# (root `scripts`) writes its platform's files in place and never a commands/
# or skills/ copy: `generated` names its GENERATED paths and `subgenerators`
# its sub-generators, producers first. The fixture target writes a full
# commands/ + skills/ tree under <out-dir>/<target>/. `in_place` marks a
# non-identity target that writes in place without --out-dir (the plugin).
PLUGIN_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"
TARGETS = {
    "cursor": {"script_root": IDENTITY_SCRIPT_ROOT,
               "generated": ("cursor/writ.mdc",), "subgenerators": ()},
    "claude-code": {"script_root": IDENTITY_SCRIPT_ROOT,
                    "generated": (), "subgenerators": ("gen-claude-agents", "gen-claude-md")},
    "codex": {"script_root": IDENTITY_SCRIPT_ROOT,
              "generated": ("codex/AGENTS.md.template",), "subgenerators": ("gen-codex-agent-tomls",)},
    # Tests only (test_fixture_target): the non-identity target of
    # `2026-10-22-generated-platform-trees`.
    "fixture": {"script_root": "${PLUGIN_ROOT}/scripts"},
    # `2026-10-22-plugin-distribution` Story 2: the Claude Code plugin tree.
    "claude-code-plugin": {"script_root": PLUGIN_ROOT_VAR + "/scripts", "in_place": True},
}  # type: Dict[str, Dict[str, object]]
# The script-root token: an invocation of a script under scripts/. Bytes, so
# a file round-trips with every other byte intact.
TOKEN = re.compile(rb"\b(python3|bash) scripts/([a-z0-9_-]+\.(?:py|sh))")
# What a non-identity target copies, in output order.
EMITTED = (("commands", "*.md"), ("skills", "*/SKILL.md"))


def is_identity(target: str) -> bool:
    return TARGETS[target]["script_root"] == IDENTITY_SCRIPT_ROOT


def writes_in_place(target: str) -> bool:
    return bool(TARGETS[target].get("in_place"))


def rewrite_tokens(data: bytes, script_root: str) -> bytes:
    """`data` with every TOKEN match rewritten to the same interpreter and
    `<script_root>/<name>`. The replacement is a callable, so `$` and `\\`
    in `script_root` (`${PLUGIN_ROOT}`) stay literal."""
    root = script_root.encode("utf-8")
    return TOKEN.sub(lambda m: m.group(1) + b" " + root + b"/" + m.group(2), data)


def emit_tree(root: Path, target: str, out_dir: Path) -> Tuple[List[Reason], List[str]]:
    """Write every EMITTED file of `root`, tokens rewritten for `target`, to
    `out_dir/<target>/<same relative path>`; returns (reasons, `wrote
    <out_dir-relative path>` lines). A missing commands/ or skills/ directory
    is `unverifiable`, `missing <dir>`, and nothing is written; a write error
    is `fail`, `write <error>`."""
    root, out_dir = Path(root), Path(out_dir)
    script_root = str(TARGETS[target]["script_root"])
    reasons = []  # type: List[Reason]
    wrote = []  # type: List[str]
    files = []  # type: List[Tuple[Path, str]]
    for folder, pattern in EMITTED:
        if not (root / folder).is_dir():
            reasons.append(("unverifiable", "missing %s" % folder))
            continue
        for src in sorted((root / folder).glob(pattern)):
            files.append((src, "%s/%s" % (target, src.relative_to(root).as_posix())))
    if reasons:
        return reasons, wrote
    for src, rel in files:
        error = write_file(out_dir / rel, rewrite_tokens(src.read_bytes(), script_root))
        if error:
            reasons.append(("fail", "write %s" % error))
            return reasons, wrote
        wrote.append("wrote " + rel)
    return reasons, wrote


# ---------------------------------------------------------------------------
# Claude Code plugin (spec `2026-10-22-plugin-distribution`, Story 2)
# ---------------------------------------------------------------------------

PLUGIN_TARGET = "claude-code-plugin"
PLUGIN_NAME = "writ"
PLUGIN_DIR = "plugins/writ"
MARKETPLACE_FILE = ".claude-plugin/marketplace.json"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"  # under PLUGIN_DIR
CARRIER_FILE = "output-styles/writ.md"          # under PLUGIN_DIR
VERSION_FILE = "VERSION"
PREAMBLE = "_preamble"
PLUGIN_AUTHOR = "Adam Sellke"
PLUGIN_REPOSITORY = "https://github.com/sellke/writ"
PLUGIN_LICENSE = "MIT"
PLUGIN_DESCRIPTION = (
    "AI development workflow: contract-first specs, a test-first multi-agent story "
    "pipeline, and script-backed quality gates.")
# Optional; `claude plugin validate` 2.1.309 warns when it is absent.
MARKETPLACE_DESCRIPTION = "The Writ plugin for Claude Code, built from this repository."
# Carrier 2 (technical-spec.md -> Prime Directive Carrier -> Decision): the
# style is forced while the plugin is enabled and keeps Claude Code's coding
# instructions. The generated-file note is a YAML comment, so the body after
# this block is system-instructions.md's body byte for byte.
CARRIER_FRONTMATTER = (
    "---\n"
    "name: writ\n"
    "description: Writ identity, Prime Directive, and interaction rules, sent with every "
    "request while the Writ plugin is enabled.\n"
    "keep-coding-instructions: true\n"
    "force-for-plugin: true\n"
    "# generated by scripts/gen-platform-trees.py from system-instructions.md "
    "— do not hand-edit; regenerate\n"
    "---\n")
CLAUDE_AGENTS_GENERATOR = "gen-claude-agents"
# install.sh `is_shippable_script`, mirrored (update.sh and unlink.sh carry
# byte-identical copies); test_plugin_distribution.py asserts the two rules
# agree on every file in scripts/.
DEV_ONLY_SCRIPTS = frozenset((
    "install.sh", "update.sh", "uninstall.sh", "unlink.sh", "migrate.sh",
    "publish-writ-runtime.sh", "eval.sh", "writ-runtime-readme.md",
    "pipeline-baseline.py", "measure-invocation.py", "harness-cost.py", "prune-ledger.py",
    "spawn-cap.py", "recommend-state.py", "gen-claude-md.py", "gen-platform-trees.py",
))
DEV_ONLY_PREFIXES = ("eval-", "_", "sweep-")
SHIPPED_DATA = frozenset(("jev-thresholds.json",))
# Files under plugins/writ/ that .gitignore drops and the orphan scan skips.
IGNORED_DIRS = frozenset(("__pycache__",))
IGNORED_FILES = frozenset((".DS_Store",))
IGNORED_SUFFIXES = (".pyc",)

# Token classes (module docstring -> Claude Code plugin). PATH_START: no path
# character before the match, so a directory-prefixed install path, a URL
# segment, or `${CLAUDE_PLUGIN_ROOT}/...` (a class's own output) never
# matches; PATH_END: the name ends there.
PATH_START = r"(?<![A-Za-z0-9_./-])"
PATH_END = r"(?![A-Za-z0-9_-])"
SCRIPT_REF = re.compile(PATH_START + r"(?:\.\./)?scripts/([a-z0-9_-]+\.(?:py|sh|json))" + PATH_END)
AGENT_REF = re.compile(PATH_START + r"(?:\.\./)?agents/([a-z0-9-]+\.md)" + PATH_END)
SKILL_REF = re.compile(PATH_START + r"(?:\.\./)?skills/([a-z0-9-]+)/SKILL\.md" + PATH_END)
PREAMBLE_REF = re.compile(PATH_START + r"(?:(?:\.\./)?commands/)?_preamble\.md" + PATH_END)
# instructions-path rewrites the Markdown link only, its target and the name
# in its text; a bare mention names an installed or project file and stays
# (technical-spec.md -> Relative Path Inventory, Story 2 review 2026-10-23).
INSTRUCTIONS_LINK = re.compile(r"\[([^\]\n]*)\]\((?:\.\./)?system-instructions\.md\)")
INSTRUCTIONS_REF = re.compile(PATH_START + r"(?:\.\./)?system-instructions\.md" + PATH_END)


class PluginNames(NamedTuple):
    scripts: FrozenSet[str]   # shipped scripts/ file names
    agents: FrozenSet[str]    # file names in the plugin's agents/
    skills: FrozenSet[str]    # skill directory names
    commands: FrozenSet[str]  # command names, the preamble excluded


class PluginFile(NamedTuple):
    rel: str               # path under the output root (the repository root in place)
    data: bytes
    mode: Optional[int]    # a script copy's source mode; None keeps write_file's default


def is_shippable_script(name: str) -> bool:
    """install.sh `is_shippable_script` for one scripts/ file name."""
    if name in DEV_ONLY_SCRIPTS or name.startswith(DEV_ONLY_PREFIXES):
        return False
    return name.endswith((".py", ".sh")) or name in SHIPPED_DATA


def command_ref(commands: FrozenSet[str]) -> "re.Pattern[str]":
    """The `command-ref` class for these command names, longest first."""
    names = sorted(commands, key=lambda name: (-len(name), name))
    return re.compile(r"(?<![A-Za-z0-9_./-])/(%s)(?![A-Za-z0-9_:/-]|\.[A-Za-z0-9])"
                      % "|".join(re.escape(name) for name in names))


def is_comment_line(line: str) -> bool:
    """A whole-line HTML comment (`<!-- ... -->`). The sources hold no
    multi-line comment; an inline `<!-- writ:start -->` in prose is not one."""
    text = line.strip()
    return text.startswith("<!--") and text.endswith("-->")


def rewrite_plugin_line(line: str, names: PluginNames, commands: "Optional[re.Pattern[str]]") -> str:
    root = PLUGIN_ROOT_VAR
    script_root = str(TARGETS[PLUGIN_TARGET]["script_root"])
    instructions = "%s/%s" % (root, SYSTEM_INSTRUCTIONS)
    line = SCRIPT_REF.sub(lambda m: "%s/%s" % (script_root, m.group(1))
                          if m.group(1) in names.scripts else m.group(0), line)
    line = AGENT_REF.sub(lambda m: "%s/agents/%s" % (root, m.group(1))
                         if m.group(1) in names.agents else m.group(0), line)
    line = SKILL_REF.sub(lambda m: "%s/skills/%s/SKILL.md" % (root, m.group(1))
                         if m.group(1) in names.skills else m.group(0), line)
    line = PREAMBLE_REF.sub(lambda m: "%s/commands/%s.md" % (root, PREAMBLE), line)
    line = INSTRUCTIONS_LINK.sub(lambda m: "[%s](%s)" % (
        INSTRUCTIONS_REF.sub(lambda _: instructions, m.group(1)), instructions), line)
    if commands is not None:
        line = commands.sub(lambda m: "/%s:%s" % (PLUGIN_NAME, m.group(1)), line)
    return line


def rewrite_plugin_body(body: str, names: PluginNames) -> str:
    """A Markdown body with each token class rewritten for the plugin
    (module docstring -> Token classes), line by line; a whole-line HTML
    comment and every other character stay unchanged."""
    commands = command_ref(names.commands) if names.commands else None
    return "".join(line if is_comment_line(line) else rewrite_plugin_line(line, names, commands)
                   for line in body.splitlines(True))


def render_plugin_markdown(text: str, names: PluginNames, source: str) -> str:
    """The frontmatter verbatim, the generated-file comment naming `source`,
    then the body rewritten."""
    frontmatter, body = split_frontmatter(text)
    return frontmatter + COMMENT % source + rewrite_plugin_body(body, names)


def read_source(path: Path) -> str:
    """A source file's text with its line endings untouched."""
    return path.read_bytes().decode("utf-8")


def require_dir(path: Path) -> None:
    if not path.is_dir():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))


def load_claude_agents(root: Path):
    """scripts/gen-claude-agents.py of `root`, loaded by path for its
    `source_stems`, OVERLAY, and `render`. ValueError when loading it raises
    or exits; a missing file is the OSError reported as `missing`."""
    path = Path(root) / "scripts" / (CLAUDE_AGENTS_GENERATOR + ".py")
    if not path.is_file():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))
    spec = importlib.util.spec_from_file_location("gen_claude_agents_plugin", str(path))
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except (Exception, SystemExit) as err:
        raise ValueError("%s load %s" % (CLAUDE_AGENTS_GENERATOR, type(err).__name__))
    return module


def claude_agents(root: Path) -> List[Tuple[str, str, str]]:
    """(stem, file name, text) of gen-claude-agents.py's render of each
    agents/*.md stem its overlay maps, sorted by file name. An unmapped stem
    is gen-claude-agents' own `unmapped` reason, so it is skipped here."""
    module = load_claude_agents(root)
    agents_dir = Path(root) / "agents"
    out = [(stem, module.OVERLAY[stem]["file"], module.render(agents_dir, stem))
           for stem in module.source_stems(agents_dir) if stem in module.OVERLAY]
    return sorted(out, key=lambda entry: entry[1])


class PluginSources(NamedTuple):
    commands: List[Path]                  # commands/*.md, by name
    docs: List[Path]                      # agents/*.md, the prompt-template docs
    agents: List[Tuple[str, str, str]]    # claude_agents(root)
    skills: List[Path]                    # skills/*/SKILL.md, by skill name
    scripts: List[Path]                   # the shipped scripts/ files


def plugin_sources(root: Path) -> PluginSources:
    """What the plugin target reads, in output order. A missing commands/,
    agents/, skills/, or scripts/ directory is the OSError reported as
    `missing <dir>`."""
    root = Path(root)
    for folder in ("commands", "agents", "skills", "scripts"):
        require_dir(root / folder)
    return PluginSources(
        commands=sorted((root / "commands").glob("*.md")),
        docs=sorted((root / "agents").glob("*.md")),
        agents=claude_agents(root),
        skills=sorted((root / "skills").glob("*/SKILL.md"), key=lambda p: p.parent.name),
        scripts=sorted(p for p in (root / "scripts").iterdir() if p.is_file() and is_shippable_script(p.name)),
    )


def names_of(sources: PluginSources) -> PluginNames:
    return PluginNames(
        scripts=frozenset(p.name for p in sources.scripts),
        agents=frozenset([p.name for p in sources.docs] + [name for _, name, _ in sources.agents]),
        skills=frozenset(p.parent.name for p in sources.skills),
        commands=frozenset(p.stem for p in sources.commands if p.stem != PREAMBLE),
    )


def plugin_names(root: Path) -> PluginNames:
    """The names the token classes rewrite for `root`'s plugin."""
    return names_of(plugin_sources(root))


def render_plugin_manifest(version: str, commands: List[Path], agents: List[str]) -> str:
    manifest = {
        "name": PLUGIN_NAME,
        "version": version,
        "description": PLUGIN_DESCRIPTION,
        "author": {"name": PLUGIN_AUTHOR},
        "repository": PLUGIN_REPOSITORY,
        "license": PLUGIN_LICENSE,
        "commands": ["./commands/%s.md" % stem
                     for stem in sorted(p.stem for p in commands if p.stem != PREAMBLE)],
        "agents": ["./agents/%s" % name for name in agents],
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def render_marketplace() -> str:
    marketplace = {
        "name": PLUGIN_NAME,
        "description": MARKETPLACE_DESCRIPTION,
        "owner": {"name": PLUGIN_AUTHOR},
        "plugins": [{"name": PLUGIN_NAME, "source": "./" + PLUGIN_DIR,
                     "description": PLUGIN_DESCRIPTION}],
    }
    return json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"


def render_plugin(root: Path) -> List[PluginFile]:
    """Every file of the plugin target, sorted by path (module docstring ->
    Claude Code plugin). Writes nothing. A missing source is the OSError
    reported as `missing <path>`; an empty VERSION or a gen-claude-agents
    load failure is a ValueError."""
    root = Path(root)
    sources = plugin_sources(root)
    commands, docs, agents, skills, scripts = sources
    names = names_of(sources)
    version = read_source(root / VERSION_FILE).strip()
    if not version:
        raise ValueError("empty %s" % VERSION_FILE)
    instructions = read_source(root / SYSTEM_INSTRUCTIONS)

    def markdown(rel: str, text: str, source: str) -> PluginFile:
        return PluginFile(PLUGIN_DIR + "/" + rel,
                          render_plugin_markdown(text, names, source).encode("utf-8"), None)

    files = [
        PluginFile(MARKETPLACE_FILE, render_marketplace().encode("utf-8"), None),
        PluginFile(PLUGIN_DIR + "/" + PLUGIN_MANIFEST, render_plugin_manifest(
            version, commands, [name for _, name, _ in agents]).encode("utf-8"), None),
    ]
    files += [markdown("commands/" + p.name, read_source(p), "commands/" + p.name) for p in commands]
    files += [markdown("agents/" + p.name, read_source(p), "agents/" + p.name) for p in docs]
    files += [markdown("agents/" + name, text, "agents/%s.md and the %s overlay" % (stem, CLAUDE_AGENTS_GENERATOR))
              for stem, name, text in agents]
    files += [markdown("skills/%s/SKILL.md" % p.parent.name, read_source(p),
                       "skills/%s/SKILL.md" % p.parent.name) for p in skills]
    files += [PluginFile("%s/scripts/%s" % (PLUGIN_DIR, p.name), p.read_bytes(), p.stat().st_mode & 0o777)
              for p in scripts]
    frontmatter, body = split_frontmatter(instructions)
    files.append(PluginFile(PLUGIN_DIR + "/" + SYSTEM_INSTRUCTIONS,
                            (frontmatter + COMMENT % SYSTEM_INSTRUCTIONS + body).encode("utf-8"), None))
    files.append(PluginFile(PLUGIN_DIR + "/" + CARRIER_FILE,
                            (CARRIER_FRONTMATTER + body).encode("utf-8"), None))
    return sorted(files, key=lambda f: f.rel)


def plugin_render(root: Path) -> Tuple[List[PluginFile], List[Reason]]:
    """(render_plugin's files, reasons): a source OSError is `unverifiable`,
    `missing <source path>`; a ValueError is `fail` with its text."""
    try:
        return render_plugin(root), []
    except OSError as err:
        return [], [("unverifiable", "missing %s" % relative(root, err.filename or PLUGIN_DIR))]
    except ValueError as err:
        return [], [("fail", str(err))]


# The directories above the plugin's files, outermost first: a symlink at
# any of them redirects every write below it.
PLUGIN_PARENTS = (".claude-plugin", "plugins", PLUGIN_DIR)


def link_in_chain(out_root: Path, rel: str) -> bool:
    """True when `rel` under `out_root`, or a directory between them, is a symlink."""
    path = Path(out_root)
    for part in rel.split("/"):
        path = path / part
        if path.is_symlink():
            return True
    return False


def plugin_orphans(out_root: Path, rendered: Set[str]) -> List[str]:
    """Paths (relative to `out_root`) under PLUGIN_DIR that no render
    produces, sorted, walked without following a symlink: a symlinked
    `plugins/` or `plugins/writ/` is the one orphan, and a symlinked
    directory below is an orphan that is not descended. The .gitignore'd
    caches are skipped."""
    out_root = Path(out_root)
    for rel in PLUGIN_PARENTS[1:]:
        if (out_root / rel).is_symlink():
            return [rel]
    top = out_root / PLUGIN_DIR
    if not top.is_dir():
        return []
    out = []  # type: List[str]
    for dirpath, dirnames, filenames in os.walk(str(top), followlinks=False):
        here = Path(dirpath)
        descend = []  # type: List[str]
        for name in sorted(dirnames):
            if (here / name).is_symlink():
                out.append((here / name).relative_to(out_root).as_posix())
            elif name not in IGNORED_DIRS:
                descend.append(name)
        dirnames[:] = descend
        for name in filenames:
            if name in IGNORED_FILES or name.endswith(IGNORED_SUFFIXES):
                continue
            rel = (here / name).relative_to(out_root).as_posix()
            if rel not in rendered:
                out.append(rel)
    return sorted(out)


def plugin_link_reasons(out_root: Path, files: List[PluginFile]) -> List[Reason]:
    """Write mode's guard, before anything is written: `symlink <path>` for
    each symlink at `.claude-plugin/`, `plugins/`, `plugins/writ/`, the
    marketplace file, or anywhere under `plugins/writ/` (walked without
    following links); then `outside <path>` for each rendered file whose
    resolved path is not the path it names under `out_root`."""
    out_root = Path(out_root)
    links = [rel for rel in PLUGIN_PARENTS + (MARKETPLACE_FILE,) if (out_root / rel).is_symlink()]
    top = out_root / PLUGIN_DIR
    if not links and top.is_dir():
        for dirpath, dirnames, filenames in os.walk(str(top), followlinks=False):
            here = Path(dirpath)
            dirnames.sort()
            for name in dirnames + filenames:
                if (here / name).is_symlink():
                    links.append((here / name).relative_to(out_root).as_posix())
    if links:
        return [("fail", "symlink " + rel) for rel in sorted(links)]
    base = os.path.realpath(str(out_root))
    return [("fail", "outside " + item.rel) for item in files
            if os.path.realpath(str(out_root / item.rel)) != os.path.join(base, *item.rel.split("/"))]


def plugin_reasons(root: Path) -> List[Reason]:
    """--check for the plugin target: `stale`, `missing`, and `orphan`
    against a fresh in-memory render, or the render's own reason."""
    files, reasons = plugin_render(root)
    if reasons:
        return reasons
    for item in files:
        path = Path(root) / item.rel
        if link_in_chain(root, item.rel) or (path.exists() and not path.is_file()):
            reasons.append(("fail", "stale " + item.rel))
        elif not path.is_file():
            reasons.append(("fail", "missing " + item.rel))
        elif path.read_bytes() != item.data:
            reasons.append(("fail", "stale " + item.rel))
    reasons += [("fail", "orphan " + rel) for rel in plugin_orphans(root, {f.rel for f in files})]
    return reasons


def write_plugin(out_root: Path, files: List[PluginFile]) -> Tuple[List[Reason], List[str], List[str]]:
    """Write every plugin file under `out_root`, then delete each orphan
    under PLUGIN_DIR and the directories it leaves empty; returns (reasons,
    `wrote <path>` lines, `removed <path>` lines). The caller has run
    `plugin_link_reasons`; each write and delete re-checks that its path has
    no symlink on it and resolves where it names, and stops the run if not."""
    out_root = Path(out_root)
    base = os.path.realpath(str(out_root))
    wrote = []  # type: List[str]
    removed = []  # type: List[str]

    def unsafe(rel: str) -> bool:
        return link_in_chain(out_root, rel) or \
            os.path.realpath(str(out_root / rel)) != os.path.join(base, *rel.split("/"))

    for item in files:
        if unsafe(item.rel):
            return [("fail", "outside " + item.rel)], wrote, removed
        error = write_file(out_root / item.rel, item.data, item.mode)
        if error:
            return [("fail", "write %s" % error)], wrote, removed
        wrote.append("wrote " + item.rel)
    top = out_root / PLUGIN_DIR
    for rel in plugin_orphans(out_root, {f.rel for f in files}):
        path = out_root / rel
        if unsafe(rel) or not rel.startswith(PLUGIN_DIR + "/"):
            return [("fail", "outside " + rel)], wrote, removed
        try:
            path.unlink()
            parent = path.parent
            while parent != top and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        except OSError as err:
            return [("fail", "remove %s" % err)], wrote, removed
        removed.append("removed " + rel)
    return [], wrote, removed


# ---------------------------------------------------------------------------
# Sub-generators and write mode
# ---------------------------------------------------------------------------


def run_subgenerator(root: Path, gen: str, args: List[str]) -> Tuple[int, List[str]]:
    """(exit code, stdout lines) of `scripts/<gen>.py <args>` run from `root`."""
    proc = subprocess.run([sys.executable, str(root / "scripts" / (gen + ".py"))] + args,
                          cwd=str(root), capture_output=True, text=True)
    return proc.returncode, proc.stdout.splitlines()


def reason_lines(lines: Iterable[str]) -> List[str]:
    return [line[len("reason: "):] for line in lines if line.startswith("reason: ")]


# (sub-generator, its reason kind) -> (this driver's kind, the path the
# detail becomes) for the sub-generator reasons that name a file this driver
# owns the check of; every other reason folds as `<gen>: <kind> <detail>`.
TRANSLATED = {
    ("gen-claude-md", "stale"): ("stale", "%s"),
    ("gen-claude-md", "absent"): ("missing", "%s"),
    ("gen-claude-agents", "orphan"): ("orphan", "claude-code/agents/%s.md"),
    ("gen-codex-agent-tomls", "orphan"): ("orphan", "codex/agents/%s.toml"),
}  # type: Dict[Tuple[str, str], Tuple[str, str]]
# The kinds the --check and coverage summary counts, in summary order.
COUNTED_KINDS = ("stale", "missing", "orphan", "unmapped", "vendor")


def fold_reason(gen: str, text: str, translate: bool) -> str:
    """One sub-generator reason as this driver reports it: the TRANSLATED
    form in --check (`translate`), else `<gen>: <text>`."""
    kind, _, detail = text.partition(" ")
    if translate and (gen, kind) in TRANSLATED:
        own_kind, path = TRANSLATED[(gen, kind)]
        return "%s %s" % (own_kind, path % detail)
    return "%s: %s" % (gen, text)


def fold_check(gen: str, rc: int, lines: List[str], translate: bool = False) -> List[Reason]:
    """The driver's reasons for one sub-generator's --check output. An exit
    of 2 or more, or no verdict on line 1, is `<gen> --check exited <rc>`.
    Reasons fold through `fold_reason`; an `unverifiable` verdict makes them
    unverifiable. Write mode (`translate` false) drops the REPAIRED_KINDS a
    write fixes; --check (`translate` true) keeps every reason."""
    verdict = lines[0] if lines else ""
    if rc >= 2 or verdict not in VERDICTS:
        return [("fail", "%s --check exited %d" % (gen, rc))]
    reasons = reason_lines(lines)
    if verdict == "unverifiable":
        return [("unverifiable", fold_reason(gen, text, translate)) for text in reasons]
    if verdict == "fail" and not reasons:
        return [("fail", "%s --check printed fail without a reason" % gen)]
    if not translate:
        reasons = [text for text in reasons if text.split(" ", 1)[0] not in REPAIRED_KINDS]
    return [("fail", fold_reason(gen, text, translate)) for text in reasons]


def verdict_of(reasons: List[Reason]) -> str:
    classes = {cls for cls, _ in reasons}
    return "fail" if "fail" in classes else "unverifiable" if classes else "pass"


def kind_of(text: str) -> str:
    """The kind of a reason: its first token, or for a folded
    `<gen>: <kind> <detail>` the token after the sub-generator's name."""
    for gen in SUBGENERATORS:
        if text.startswith(gen + ": "):
            text = text[len(gen) + 2:]
            break
    return text.split(" ", 1)[0]


def finish(reasons: List[Reason], wrote: List[str], removed: Iterable[str] = ()) -> int:
    """Print the write-mode check shape: verdict, reasons, `wrote` lines,
    `removed` lines, `(<n> written, <r> reasons)` summary."""
    verdict = verdict_of(reasons)
    print(verdict)
    for _, text in reasons:
        print("reason: " + text)
    for line in list(wrote) + list(removed):
        print(line)
    print("%s: %s (%d written, %d reasons)" % (TOOL, verdict, len(wrote), len(reasons)))
    return 1 if verdict == "fail" else 0


def finish_check(reasons: List[Reason]) -> int:
    """Print the --check and coverage shape: verdict, reasons, the
    five-count summary over COUNTED_KINDS."""
    verdict = verdict_of(reasons)
    print(verdict)
    for _, text in reasons:
        print("reason: " + text)
    kinds = [kind_of(text) for _, text in reasons]
    print("%s: %s (%s)" % (TOOL, verdict, ", ".join(
        "%d %s" % (kinds.count(kind), kind) for kind in COUNTED_KINDS)))
    return 1 if verdict == "fail" else 0


def adapter_reasons(root: Path) -> Tuple[List[AdapterTable], List[Reason]]:
    """The four parsed tables and the reasons of those that did not parse."""
    tables = [parse_adapter(root / "adapters" / (adapter + ".md"), adapter) for adapter in ADAPTERS]
    reasons = [(table.verdict, text) for table in tables if table.verdict != "pass"
               for text in table.reasons]
    return tables, reasons


def vendor_reasons(root: Path, tables: List[AdapterTable]) -> List[Reason]:
    return [("fail", text) for text in vendor_hits(root, vocabulary(tables)[1])]


def render_all(root: Path, generated: List[Tuple[str, Callable[[Path], str]]]) -> Tuple[List[Tuple[str, str]], List[Reason]]:
    """(rendered (path, text) pairs, reasons) for `generated`: a source
    OSError is `unverifiable`, `missing <source path>`; a ValueError is
    `fail` with its text."""
    texts = []  # type: List[Tuple[str, str]]
    reasons = []  # type: List[Reason]
    for rel, render in generated:
        try:
            texts.append((rel, render(root)))
        except OSError as err:
            reasons.append(("unverifiable", "missing %s" % relative(root, err.filename or rel)))
        except ValueError as err:
            reasons.append(("fail", str(err)))
    return texts, reasons


def stale_reasons(root: Path, texts: List[Tuple[str, str]]) -> List[Reason]:
    """`stale <path>` when the file's bytes differ from the render, `missing
    <path>` when there is no file."""
    reasons = []  # type: List[Reason]
    for rel, text in texts:
        path = root / rel
        if not path.is_file():
            reasons.append(("fail", "missing " + rel))
        elif path.read_bytes() != text.encode("utf-8"):
            reasons.append(("fail", "stale " + rel))
    return reasons


# gen-claude-agents.py owns only claude-code/agents/writ-*.md, so its --check
# cannot see a stray file with another name, while install.sh ships every
# claude-code/agents/*.md; the driver reports the rest itself.
CLAUDE_AGENT_PREFIX = "writ-"


def stray_agent_reasons(root: Path) -> List[Reason]:
    """`orphan claude-code/agents/<name>` for each .md under
    claude-code/agents/ that no generator produces: one whose name does not
    start with CLAUDE_AGENT_PREFIX (gen-claude-agents' own orphan check
    covers the rest). A missing directory yields no reason."""
    folder = Path(root) / "claude-code" / "agents"
    return [("fail", "orphan claude-code/agents/" + path.name)
            for path in sorted(folder.glob("*.md"))
            if not path.name.startswith(CLAUDE_AGENT_PREFIX)]


def check_mode(root: Path) -> int:
    """Report stale, missing, orphan, unmapped, and vendor without writing
    (module docstring -> --check)."""
    tables, reasons = adapter_reasons(root)
    reasons += [("fail", text) for text in unmapped(tables)]
    if all(table.verdict == "pass" for table in tables):
        texts, render_errors = render_all(root, GENERATED)
        reasons += render_errors + stale_reasons(root, texts) + stray_agent_reasons(root)
        for gen in SUBGENERATORS:
            rc, lines = run_subgenerator(root, gen, ["--check"])
            reasons += fold_check(gen, rc, lines, translate=True)
    reasons += plugin_reasons(root)
    reasons += vendor_reasons(root, tables)
    return finish_check(reasons)


def coverage_mode(root: Path) -> int:
    """Report the adapters' own reasons, unmapped, and vendor; nothing else
    (module docstring -> coverage)."""
    tables, reasons = adapter_reasons(root)
    reasons += [("fail", text) for text in unmapped(tables)]
    reasons += vendor_reasons(root, tables)
    return finish_check(reasons)


def write_mode(root: Path, generated: List[Tuple[str, Callable[[Path], str]]] = GENERATED,
               subgenerators: Tuple[str, ...] = SUBGENERATORS,
               plugin_out: Optional[Path] = None) -> int:
    """Check the adapters, the vocabulary, the vendor scan, the stray agent
    files (when gen-claude-agents is among `subgenerators`), and every
    sub-generator in `subgenerators`, then write `generated`, run those
    sub-generators' writers, and, with `plugin_out`, write the plugin tree
    under it; nothing is written when any reason exists (module docstring ->
    Write mode). An identity target narrows `generated` and `subgenerators`
    to its platform and passes no `plugin_out`."""
    wrote = []  # type: List[str]

    tables, reasons = adapter_reasons(root)
    if reasons:
        return finish(reasons, wrote)
    reasons += [("fail", text) for text in unmapped(tables)]
    if reasons:
        return finish(reasons, wrote)
    reasons += vendor_reasons(root, tables)
    if reasons:
        return finish(reasons, wrote)
    if "gen-claude-agents" in subgenerators:
        reasons += stray_agent_reasons(root)
        if reasons:
            return finish(reasons, wrote)

    for gen in subgenerators:
        rc, lines = run_subgenerator(root, gen, ["--check"])
        reasons += fold_check(gen, rc, lines)
    if reasons:
        return finish(reasons, wrote)

    texts, reasons = render_all(root, generated)
    if reasons:
        return finish(reasons, wrote)
    plugin_files = []  # type: List[PluginFile]
    if plugin_out is not None:
        plugin_files, reasons = plugin_render(root)
        if not reasons:
            reasons = plugin_link_reasons(plugin_out, plugin_files)
        if reasons:
            return finish(reasons, wrote)

    for rel, text in texts:
        error = write_file(root / rel, text)
        if error:
            reasons.append(("fail", "write %s" % error))
            return finish(reasons, wrote)
        wrote.append("wrote " + rel)
    for gen in subgenerators:
        rc, lines = run_subgenerator(root, gen, [])
        wrote += [line for line in lines if line.startswith("wrote ")]
        if rc != 0:
            reasons.append(("fail", "%s exited %d" % (gen, rc)))
            reasons += [("fail", "%s: %s" % (gen, text)) for text in reason_lines(lines)]
            return finish(reasons, wrote)
    removed = []  # type: List[str]
    if plugin_out is not None:
        reasons, plugin_wrote, removed = write_plugin(plugin_out, plugin_files)
        wrote += plugin_wrote
    return finish(reasons, wrote, removed)


def target_mode(root: Path, target: str, out_dir: Optional[str]) -> int:
    """`--target`: an identity target is write mode narrowed to its platform;
    the plugin target is write mode narrowed to the plugin tree, under
    `out_dir` or in place; the fixture target is `emit_tree` into `out_dir`."""
    if is_identity(target):
        entry = TARGETS[target]
        generated = [(rel, render) for rel, render in GENERATED if rel in entry["generated"]]  # type: ignore[operator]
        return write_mode(root, generated, tuple(entry["subgenerators"]))  # type: ignore[arg-type]
    if target == PLUGIN_TARGET:
        return write_mode(root, [], (), plugin_out=Path(out_dir) if out_dir else root)
    reasons, wrote = emit_tree(root, target, Path(out_dir or ""))
    return finish(reasons, wrote)


def relative(root: Path, path: str) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gen-platform-trees.py", allow_abbrev=False,
        description="Generate or check the per-platform trees and the Claude Code plugin from "
                    "adapters/*.md, system-instructions.md, .writ/manifest.yaml, and the command, "
                    "agent, skill, and script sources. Dev-only; never shipped.")
    parser.add_argument("mode", nargs="?", choices=["coverage"],
                        help="coverage: run only the unmapped and vendor checks")
    parser.add_argument("--check", action="store_true",
                        help="report stale, missing, orphan, unmapped, vendor, and malformed; "
                             "write nothing; exit 0 pass or unverifiable, 1 fail")
    parser.add_argument("--target", metavar="NAME", choices=list(TARGETS),
                        help="one target (%s) instead of every identity target and the plugin; an "
                             "identity target writes its platform's files in place, claude-code-plugin "
                             "writes the plugin in place or under --out-dir, fixture needs --out-dir"
                             % ", ".join(TARGETS))
    parser.add_argument("--out-dir", metavar="DIR",
                        help="with --target fixture: the directory that receives fixture/commands and "
                             "fixture/skills; with --target claude-code-plugin: the directory that "
                             "receives .claude-plugin/ and plugins/writ/")
    return parser


def main(argv: Optional[List[str]] = None, root: Path = ROOT) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    modes = [name for name, on in (("coverage", args.mode == "coverage"), ("--check", args.check),
                                   ("--target", args.target is not None)) if on]
    if len(modes) > 1:
        parser.error("%s cannot be combined" % " and ".join(modes))
    if args.out_dir and not args.target:
        parser.error("--out-dir needs --target")
    if args.target and is_identity(args.target) and args.out_dir:
        parser.error("--target %s writes in place; it takes no --out-dir" % args.target)
    if args.target and not is_identity(args.target) and not writes_in_place(args.target) \
            and not args.out_dir:
        parser.error("--target %s needs --out-dir" % args.target)
    root = Path(root)
    if args.mode == "coverage":
        return coverage_mode(root)
    if args.check:
        return check_mode(root)
    if args.target:
        return target_mode(root, args.target, args.out_dir)
    return write_mode(root, plugin_out=root)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
