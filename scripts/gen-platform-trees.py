#!/usr/bin/env python3
"""Generate the per-platform trees from source (spec `2026-10-22-generated-platform-trees`).

    python3 scripts/gen-platform-trees.py                  # write all identity targets in place
    python3 scripts/gen-platform-trees.py --check          # report stale|missing|orphan|unmapped|vendor|malformed; write nothing
    python3 scripts/gen-platform-trees.py coverage         # unmapped + vendor only
    python3 scripts/gen-platform-trees.py --target fixture --out-dir <dir>   # commands/ + skills/ with the fixture script root

Dev-only (it reads adapters/*.md and .writ/manifest.yaml, which installed
projects do not have); never hand-edit a generated file. Story 1 ships the
adapter tool-table parser and the vocabulary rule; Story 2 the capability
map, `cursor/writ.mdc`, and write mode. `--check`, `coverage`, and
`--target` print `unverifiable` with one `reason: not-implemented <mode>`
line until Story 4 adds them.

Check shape: line 1 `pass`/`fail`/`unverifiable`, `reason: <kind> <detail>`
lines, `wrote <path>` lines in write mode, then `gen-platform-trees:
<verdict> (<n> written, <r> reasons)` (Story 4 adds the per-kind counts).
Exit 0 pass or unverifiable, 1 fail, 2 usage. Nothing is written when any
reason exists.

Write mode (spec.md -> Rule 1; technical-spec.md -> ## Driver CLI), in
order: parse the four adapters (a table that is not `pass` ends the run with
its verdict and reasons); `unmapped` names end it with `fail`; each
sub-generator's `--check` runs (SUBGENERATORS, as subprocesses from this
tree): an exit of 2 or more, or a first line that is not a verdict, is
`reason: <gen> --check exited <rc>`; an `unverifiable` verdict makes the run
`unverifiable`; every other `reason: <kind> <detail>` line folds in as
`reason: <gen>: <kind> <detail>`, except the output-state kinds in
REPAIRED_KINDS (`stale`, `missing`, `absent`, `extra`), which are what a
write repairs. With no reason left, each GENERATED file is rendered and
written through a temp file plus os.replace (`wrote <path>`), then the
sub-generators run in write mode and their `wrote` lines are relayed; one
that exits non-zero ends the run with `fail`, `reason: <gen> exited <rc>`,
and its folded reasons.

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
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

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


def strip_frontmatter(text: str) -> str:
    """`text` without its leading `---\n...\n---\n` block; every other byte
    stays, so a body that opened with a blank line still does."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5:]
    return text


def render_writ_mdc(root: Path) -> str:
    """`cursor/writ.mdc` (spec.md -> Rule 6): the alwaysApply frontmatter, the
    generated-file comment, the system-instructions.md body with only its
    frontmatter removed, a blank line, then the Cursor map."""
    body = strip_frontmatter((Path(root) / SYSTEM_INSTRUCTIONS).read_text(encoding="utf-8"))
    if not body.endswith("\n"):
        body += "\n"
    comment = COMMENT % (SYSTEM_INSTRUCTIONS + " and adapters/cursor.md")
    return WRIT_MDC_FRONTMATTER + comment + body + "\n" + capability_map("cursor", root)


# (relative path, renderer taking the tree root) per file the driver writes
# itself, in write order. Story 3 appends codex/AGENTS.md.template.
GENERATED = [("cursor/writ.mdc", render_writ_mdc)]  # type: List[Tuple[str, Callable[[Path], str]]]


def write_file(out: Path, text: str) -> Optional[str]:
    """Write `text` through a temp file in the same directory and os.replace
    it over `out`, keeping `out`'s mode. Returns the error text, or None."""
    mode = out.stat().st_mode & 0o777 if out.is_file() else 0o644
    tmp = None
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(out.parent), prefix="." + out.name + ".")
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8"))
        os.chmod(tmp, mode)
        os.replace(tmp, str(out))
    except OSError as err:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        return str(err)
    return None


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


def fold_check(gen: str, rc: int, lines: List[str]) -> List[Reason]:
    """The driver's reasons for one sub-generator's --check output. An exit
    of 2 or more, or no verdict on line 1, is `<gen> --check exited <rc>`.
    Reasons fold as `<gen>: <kind> <detail>`; an `unverifiable` verdict makes
    them unverifiable; a `fail` drops the REPAIRED_KINDS a write fixes."""
    verdict = lines[0] if lines else ""
    if rc >= 2 or verdict not in VERDICTS:
        return [("fail", "%s --check exited %d" % (gen, rc))]
    reasons = reason_lines(lines)
    if verdict == "unverifiable":
        return [("unverifiable", "%s: %s" % (gen, text)) for text in reasons]
    if verdict == "fail" and not reasons:
        return [("fail", "%s --check printed fail without a reason" % gen)]
    return [("fail", "%s: %s" % (gen, text)) for text in reasons
            if text.split(" ", 1)[0] not in REPAIRED_KINDS]


def verdict_of(reasons: List[Reason]) -> str:
    classes = {cls for cls, _ in reasons}
    return "fail" if "fail" in classes else "unverifiable" if classes else "pass"


def finish(reasons: List[Reason], wrote: List[str]) -> int:
    """Print the check shape: verdict, reasons, `wrote` lines, summary."""
    verdict = verdict_of(reasons)
    print(verdict)
    for _, text in reasons:
        print("reason: " + text)
    for line in wrote:
        print(line)
    print("%s: %s (%d written, %d reasons)" % (TOOL, verdict, len(wrote), len(reasons)))
    return 1 if verdict == "fail" else 0


def write_mode(root: Path) -> int:
    """Check the adapters, the vocabulary, and every sub-generator, then
    write GENERATED and run the sub-generators' writers; nothing is written
    when any reason exists (module docstring -> Write mode)."""
    reasons = []  # type: List[Reason]
    wrote = []  # type: List[str]

    tables = [parse_adapter(root / "adapters" / (adapter + ".md"), adapter) for adapter in ADAPTERS]
    for table in tables:
        if table.verdict != "pass":
            reasons += [(table.verdict, text) for text in table.reasons]
    if reasons:
        return finish(reasons, wrote)
    reasons += [("fail", text) for text in unmapped(tables)]
    if reasons:
        return finish(reasons, wrote)

    for gen in SUBGENERATORS:
        rc, lines = run_subgenerator(root, gen, ["--check"])
        reasons += fold_check(gen, rc, lines)
    if reasons:
        return finish(reasons, wrote)

    texts = []  # type: List[Tuple[str, str]]
    for rel, render in GENERATED:
        try:
            texts.append((rel, render(root)))
        except OSError as err:
            reasons.append(("unverifiable", "missing %s" % relative(root, err.filename or rel)))
        except ValueError as err:
            reasons.append(("fail", str(err)))
    if reasons:
        return finish(reasons, wrote)

    for rel, text in texts:
        error = write_file(root / rel, text)
        if error:
            reasons.append(("fail", "write %s" % error))
            return finish(reasons, wrote)
        wrote.append("wrote " + rel)
    for gen in SUBGENERATORS:
        rc, lines = run_subgenerator(root, gen, [])
        wrote += [line for line in lines if line.startswith("wrote ")]
        if rc != 0:
            reasons.append(("fail", "%s exited %d" % (gen, rc)))
            reasons += [("fail", "%s: %s" % (gen, text)) for text in reason_lines(lines)]
            return finish(reasons, wrote)
    return finish(reasons, wrote)


def relative(root: Path, path: str) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(path)


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


def main(argv: Optional[List[str]] = None, root: Path = ROOT) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "coverage" or args.check or args.target or args.out_dir:
        # Story 4 adds --check, coverage, and the fixture target.
        mode = args.mode or ("check" if args.check else "target")
        print("unverifiable")
        print("reason: not-implemented %s" % mode)
        print("%s: unverifiable (0 written, 1 reasons)" % TOOL)
        return 0
    return write_mode(Path(root))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
