#!/usr/bin/env python3
"""Tests for scripts/gen-platform-trees.py, Stories 1 and 2 of `2026-10-22-generated-platform-trees`.

Story 1 ships the adapter tool-table parser (`parse_adapter`), the
vocabulary rule (`vocabulary`, `unmapped`), and the repairs the golden
neutral set depends on: a `file_search` row in the Codex table, the OpenClaw
`readonly: true` row folded into `Task`, a `Plan Mode` row in all four
tables, one sentence in three command files, and the Plan Mode issue's
resolution. Story 2 adds the capability map (`degradation`, `render_map`,
`capability_map`), `render_writ_mdc`, and the driver's write mode, which
checks the four adapters and the three sub-generators before it writes
`cursor/writ.mdc` and runs the sub-generators' writers. `--check`,
`coverage`, and `--target` stay a stub until Story 4.

The module name has a hyphen, so the tests import it by path, the way
test_gen_claude_md.py does. Fixture adapters live under
scripts/tests/fixtures/platform-trees/<case>/<adapter>.md and carry the real
adapter headings, so `parse_adapter` selects the grammar by basename and the
reason strings name `adapters/<basename>`. Write-mode tests copy the tree
into `tmp_path` (`tmp_tree`) and run the driver there. Nothing here writes
to the repo.

Covers AC-1.1 to AC-1.5 and AC-2.1 to AC-2.5.

Run: uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "gen-platform-trees.py"
ADAPTERS_DIR = REPO_ROOT / "adapters"
FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "platform-trees"

ADAPTERS = ("cursor", "claude-code", "codex", "openclaw")
# technical-spec.md -> ## Vocabulary Rule: the neutral set after the repairs.
GOLDEN = {
    "Task", "AskQuestion", "codebase_search", "file_search", "todo_write",
    "read_file", "run_terminal_cmd", "list_dir", "canvas-preview", "Plan Mode",
}
ALLOWLIST = {"Read", "Write", "Bash"}

# technical-spec.md -> ## Plan Mode Rows: mapping cell per adapter and the
# shared degradation sentence. The cursor row carries both in column 3.
DEGRADATION = "If the platform has no toggle, say so and proceed read-only."
PLAN_MODE_MAPPING = {
    "cursor": "Ask the user to switch to Plan Mode; continue when they have",
    "claude-code": (
        "`EnterPlanMode`; present the contract proposal as the plan; "
        "after `ExitPlanMode` approval, lock with AskQuestion"),
    "codex": (
        "No agent-side mode: run discovery as a read-only conversation and say so; "
        "Codex's `/plan` is user-side"),
    "openclaw": "No agent-side mode: run discovery as a read-only conversation and say so",
}
CURSOR_USED_BY = "create-spec, plan-product, new-command"

# (command file, the one sentence that changed, a fragment of the old wording)
COMMAND_SENTENCES = [
    (
        "commands/create-spec.md",
        "After the context scan, run discovery in Plan Mode, entered through the "
        "adapter's `Plan Mode` row; the user controls when to switch back.",
        "run discovery in Plan Mode; the user controls when to switch.",
    ),
    (
        "commands/plan-product.md",
        "**After context scan and initial product direction selection, run discovery "
        "in Plan Mode through the adapter's `Plan Mode` row.**",
        "run discovery in Plan Mode.**",
    ),
    (
        "commands/new-command.md",
        "After the context scan, switch to Plan Mode through the adapter's `Plan Mode` row.",
        "switch to Plan Mode. Designing",
    ),
]

ISSUE = ".writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md"
SPEC_SLUG = "2026-10-22-generated-platform-trees"
SPEC_REF = "> **spec_ref:** .writ/specs/%s/spec.md" % SPEC_SLUG
LANE_BRANCH = "writ/phase/14/%s" % SPEC_SLUG
RESOLUTION_PHRASES = (
    "2026-10-22", "`%s`" % SPEC_SLUG, "`%s`" % LANE_BRANCH,
    "`EnterPlanMode`", "`ExitPlanMode`", "AskQuestion",
    "`adapters/cursor.md`", "`adapters/claude-code.md`", "`adapters/codex.md`",
    "`adapters/openclaw.md`", "`commands/create-spec.md`", "`commands/plan-product.md`",
    "`commands/new-command.md`", "Scenario 29",
)

# (fixture case, the bad row's text, or None for the header-only table)
MALFORMED = [
    ("malformed-cells", "| `file_search` | two cells only |"),
    ("malformed-empty-first-cell", '| | `Glob("**/pattern*")` | Built-in Glob tool |'),
    ("empty-table", None),
]
MISSING_HEADING = "### Quick reference — orchestration primitives"


def load_module():
    spec = importlib.util.spec_from_file_location("gen_platform_trees", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def gen():
    return load_module()


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def cells(row: str) -> List[str]:
    """Cell texts of a markdown table row, splitting on unescaped pipes."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", row.strip())[1:-1]]


def adapter_path(adapter: str) -> Path:
    return ADAPTERS_DIR / (adapter + ".md")


def parse_real(gen, adapters=ADAPTERS):
    return [gen.parse_adapter(adapter_path(a)) for a in adapters]


# ---------------------------------------------------------------------------
# Parser and vocabulary
# ---------------------------------------------------------------------------


def test_parse_real_adapters(gen):
    """AC-1.1: the four repaired adapters parse; the neutral set is the golden
    set with no duplicate; the `Task` variants share one name; `vendor_only`
    has `EnterPlanMode` and none of the allowlisted verbs; nothing is
    unmapped."""
    tables = parse_real(gen)
    for table in tables:
        assert table.verdict == "pass", "%s: %s" % (table.adapter, table.reasons)
        assert table.reasons == []
    assert [t.adapter for t in tables] == list(ADAPTERS)
    assert gen.ADAPTERS == ADAPTERS
    assert gen.ALLOWLIST == ALLOWLIST

    neutral, vendor_only = gen.vocabulary(tables)
    assert set(neutral) == GOLDEN, "neutral set: %r" % neutral
    assert len(neutral) == len(GOLDEN), "neutral names repeat: %r" % neutral
    assert neutral[0] == "Task", "first-seen order starts with the cursor Task row"

    for adapter in ("claude-code", "openclaw"):
        table = tables[ADAPTERS.index(adapter)]
        variants = [row.variant for row in table.rows if row.name == "Task"]
        assert len(variants) >= 2, "%s: expected Task variants, got %r" % (adapter, variants)
        assert len(set(variants)) == len(variants), "%s: variant text repeats" % adapter
        assert table.names.count("Task") == 1, "%s: names must be unique" % adapter

    assert "EnterPlanMode" in vendor_only
    assert "ExitPlanMode" in vendor_only
    assert not (ALLOWLIST & vendor_only), "allowlisted verbs leaked: %r" % (ALLOWLIST & vendor_only)
    assert not (GOLDEN & vendor_only), "neutral names leaked: %r" % (GOLDEN & vendor_only)
    assert gen.unmapped(tables) == []


@pytest.mark.parametrize(
    "cell, name",
    [
        ("`Task({ prompt })`", "Task"),
        ("`Task({ readonly: true })`", "Task"),
        ("`AskQuestion()`", "AskQuestion"),
        ("`Plan Mode`", "Plan Mode"),
        ("`canvas-preview`", "canvas-preview"),
        ("`readonly: true`", "readonly"),
        ("`Glob(\"**/pattern*\")`", "Glob"),
        ("", ""),
        ("`123`", ""),
    ],
)
def test_capability_name(gen, cell, name):
    """AC-1.1: column 1 normalizes to its leading identifier, keeping an inner
    space or hyphen, stopping at `(`, `{`, or `:`; no identifier is empty."""
    assert gen.capability_name(cell) == name


def test_vendor_only_tokens(gen):
    """AC-1.1: `vendor_only` holds backticked identifiers from mapping cells
    minus the neutral names and the allowlist. URL- and path-shaped tokens are
    not identifiers."""
    mapping = (
        "`Grep(\"p\")` or `Bash(\"rg\")`; `Read`; `http://localhost:3000`; "
        "`.codex/agents/*.toml`; `@browser`; `/plan`; `~/x`; `permissionMode: plan`; "
        "`codebase_search`; `sessions_spawn({ task })`"
    )
    row = gen.Row("codebase_search", "codebase_search", mapping, "notes", 5)
    table = gen.AdapterTable("codex", Path("adapters/codex.md"), "pass", [], [row])
    neutral, vendor_only = gen.vocabulary([table])
    assert neutral == ["codebase_search"]
    assert vendor_only == {"Grep", "permissionMode", "sessions_spawn"}


@pytest.mark.parametrize("case, bad_row", MALFORMED, ids=[c for c, _ in MALFORMED])
def test_malformed_row(gen, case, bad_row):
    """AC-1.2: a row with the wrong cell count or an empty first cell fails
    with `malformed adapters/<x>.md:<line>` (1-based); a header with no body
    rows fails with `empty adapters/<x>.md`. The path is the fixture's
    basename, not its location."""
    path = FIXTURES / case / "codex.md"
    table = gen.parse_adapter(path)
    assert table.adapter == "codex"
    assert table.verdict == "fail"
    if bad_row is None:
        assert table.reasons == ["empty adapters/codex.md"]
        assert table.rows == []
    else:
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines.count(bad_row) == 1, "%s: fixture must hold the bad row once" % case
        line = lines.index(bad_row) + 1
        assert table.reasons == ["malformed adapters/codex.md:%d" % line]


def test_missing_section(gen):
    """AC-1.3: an adapter without its tool-table heading is `unverifiable`
    with `section <heading> in adapters/<x>.md`, and the call returns instead
    of raising."""
    table = gen.parse_adapter(FIXTURES / "missing-section" / "codex.md")
    assert table.verdict == "unverifiable"
    assert table.reasons == ["section %s in adapters/codex.md" % MISSING_HEADING]
    assert table.rows == []
    assert table.names == []


def test_parity(gen):
    """AC-1.4: a codex table that lists every neutral name except
    `file_search`, combined with the three real adapters, yields exactly
    `unmapped file_search in adapters/codex.md`."""
    fixture = gen.parse_adapter(FIXTURES / "parity-no-file-search" / "codex.md")
    assert fixture.verdict == "pass", fixture.reasons
    assert "file_search" not in fixture.names
    tables = parse_real(gen, ("cursor", "claude-code"))
    tables.append(fixture)
    tables.extend(parse_real(gen, ("openclaw",)))
    assert gen.unmapped(tables) == ["unmapped file_search in adapters/codex.md"]


# ---------------------------------------------------------------------------
# Repairs: tables, command sentences, issue
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter", ADAPTERS)
def test_plan_mode_row(gen, adapter):
    """AC-1.5: each tool table ends with one `Plan Mode` row whose mapping
    and notes match technical-spec.md -> ## Plan Mode Rows. The cursor row
    lists its commands in column 2 and carries the mapping sentence and the
    degradation sentence in column 3."""
    table = gen.parse_adapter(adapter_path(adapter))
    assert table.verdict == "pass", table.reasons
    rows = [row for row in table.rows if row.name == "Plan Mode"]
    assert len(rows) == 1, "%s: expected one Plan Mode row, got %d" % (adapter, len(rows))
    row = rows[0]
    assert row == table.rows[-1], "%s: Plan Mode must be the last row" % adapter
    assert row.variant == "Plan Mode"
    raw = cells(read("adapters/%s.md" % adapter).splitlines()[row.line - 1])
    assert raw[0] == "`Plan Mode`"
    if adapter == "cursor":
        assert raw[1] == CURSOR_USED_BY
        assert row.mapping == PLAN_MODE_MAPPING["cursor"] + ". " + DEGRADATION
        assert row.notes == row.mapping
    else:
        assert row.mapping == PLAN_MODE_MAPPING[adapter]
        assert row.notes == DEGRADATION


def test_codex_file_search_row(gen):
    """AC-1.5: the Codex table has a `file_search` row directly after
    `codebase_search`."""
    table = gen.parse_adapter(adapter_path("codex"))
    names = table.names
    assert "file_search" in names
    assert names.index("file_search") == names.index("codebase_search") + 1
    row = next(r for r in table.rows if r.name == "file_search")
    assert row.mapping == '`Glob("**/pattern*")`'
    assert row.notes == "Built-in Glob tool"


def test_openclaw_readonly_folded(gen):
    """AC-1.5: the OpenClaw table has a `Task({ readonly: true })` row with
    the old row's mapping and notes, and no `readonly: true` row."""
    table = gen.parse_adapter(adapter_path("openclaw"))
    variants = [row.variant for row in table.rows]
    assert "Task({ readonly: true })" in variants
    assert "readonly: true" not in variants
    assert "readonly" not in table.names
    row = next(r for r in table.rows if r.variant == "Task({ readonly: true })")
    assert row.name == "Task"
    assert row.mapping == "Add constraint to task prompt"
    assert row.notes == '"Do NOT modify any files"'


@pytest.mark.parametrize("rel, sentence, old", COMMAND_SENTENCES, ids=[Path(r).stem for r, _, _ in COMMAND_SENTENCES])
def test_command_sentence(rel, sentence, old):
    """AC-1.5: each command's Plan Mode step points at the adapter's
    `Plan Mode` row, once, and the old wording is gone."""
    text = read(rel)
    assert text.count(sentence) == 1, "%s: expected the sentence once" % rel
    assert old not in text, "%s: old wording still present: %r" % (rel, old)


def test_issue_resolution():
    """AC-1.5: the Plan Mode issue's last section is `## Resolution`; it
    names the date, this spec, the lane branch, the decision per platform,
    the four adapters, the three commands, and what is left to UAT; its
    `spec_ref` points at this spec."""
    lines = read(ISSUE).splitlines()
    assert lines.count("## Resolution") == 1
    body = lines[lines.index("## Resolution") + 1:]
    later = [line for line in body if re.match(r"^#{1,2} ", line)]
    assert later == [], "Resolution is not the last section: %s" % later
    text = "\n".join(body)
    for phrase in RESOLUTION_PHRASES:
        assert phrase in text, "Resolution lacks %r" % phrase
    refs = [line for line in lines if line.startswith("> **spec_ref:**")]
    assert refs == [SPEC_REF], refs


# ---------------------------------------------------------------------------
# CLI stub
# ---------------------------------------------------------------------------


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(MODULE_PATH)] + list(args),
                          cwd=str(REPO_ROOT), capture_output=True, text=True)


def test_cli_help():
    """CLI: `--help` exits 0 and names every mode, including the ones Story 4 adds."""
    proc = run_cli("--help")
    assert proc.returncode == 0, proc.stderr
    assert "usage" in proc.stdout.lower()
    for word in ("--check", "--target", "--out-dir", "coverage"):
        assert word in proc.stdout


def test_cli_unknown_flag_is_usage_error():
    """CLI: an unknown flag prints usage on stderr, nothing on stdout, exit 2."""
    proc = run_cli("--bogus")
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "usage:" in proc.stderr


@pytest.mark.parametrize(
    "args, mode",
    [(("--check",), "check"), (("coverage",), "coverage"),
     (("--target", "fixture", "--out-dir", "x"), "target")],
    ids=["check", "coverage", "target"])
def test_cli_stub(args, mode):
    """Story 4 modes, still stubbed: `--check`, `coverage`, and `--target`
    print the check shape with `unverifiable`, one `reason: not-implemented
    <mode>` line, and the summary, exit 0, and write nothing. Write mode is
    real since Story 2 (see below)."""
    proc = run_cli(*args)
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "unverifiable"
    assert lines[1] == "reason: not-implemented %s" % mode
    assert lines[-1].startswith("gen-platform-trees: unverifiable (")
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# Story 2: capability map, cursor/writ.mdc, claude-code/CLAUDE.md, write mode
# ---------------------------------------------------------------------------

TREE_DIRS = ("adapters", "agents", "commands", "skills", "cursor", "claude-code", "codex")
TREE_FILES = ("system-instructions.md", ".writ/manifest.yaml")
MAP_LEAD = "Commands name capabilities; this table maps them to this platform."
MAP_HEADER = ["| Capability | On this platform | When unavailable |", "|---|---|---|"]
NO_RENDERER = ("No renderer: write a structural description of each draft and say the "
               "drafts were not rendered.")
NO_AGENT_SIDE = "No agent-side mode: run discovery as a read-only conversation and say so"
FRONTMATTER = "---\nalwaysApply: true\n---\n"
WRIT_MDC_COMMENT = ("<!-- generated by scripts/gen-platform-trees.py from system-instructions.md "
                    "and adapters/cursor.md — do not hand-edit; regenerate -->")
TREES_SCRIPT = "scripts/gen-platform-trees.py"
GENERATED_ROOT_FILES = ("cursor/writ.mdc", "claude-code/CLAUDE.md")
BAD_ROW = "| `zz_bad` | two cells only |\n"
CURSOR_HEADING = "## Native Tool Availability"


def tmp_tree(tmp_path: Path) -> Path:
    """A copy of what the driver reads and writes: scripts/*.py, the source
    and generated directories, system-instructions.md, and the manifest."""
    (tmp_path / "scripts").mkdir(parents=True)
    for script in (REPO_ROOT / "scripts").glob("*.py"):
        shutil.copy(script, tmp_path / "scripts" / script.name)
    for name in TREE_DIRS:
        shutil.copytree(REPO_ROOT / name, tmp_path / name)
    for rel in TREE_FILES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    return tmp_path


def run_tree(tree: Path, *args: str) -> subprocess.CompletedProcess:
    """The driver copied into `tree`, run from `tree`."""
    return subprocess.run([sys.executable, str(tree / TREES_SCRIPT)] + list(args),
                          cwd=str(tree), capture_output=True, text=True)


def generated_bytes(tree: Path) -> Dict[str, bytes]:
    """Bytes of every generated file in the tree, keyed by relative path."""
    paths = [tree / rel for rel in GENERATED_ROOT_FILES]
    paths += sorted((tree / "claude-code" / "agents").glob("*.md"))
    paths += sorted((tree / "codex" / "agents").glob("*.toml"))
    return {p.relative_to(tree).as_posix(): p.read_bytes() for p in paths}


def prime_directive(text: str) -> str:
    """The `## Prime Directive` section, the way eval.sh's
    extract_prime_directive reads it: from the heading to the next `## `."""
    out = []  # type: List[str]
    capture = False
    for line in text.splitlines():
        if re.match(r"^## Prime Directive\s*$", line):
            capture = True
        elif capture and re.match(r"^## [^#]", line):
            break
        if capture:
            out.append(line)
    return "\n".join(out)


def seed_bad_row(adapter: Path) -> int:
    """Insert a two-cell row after the tool table's `file_search` row;
    returns the bad row's 1-based line."""
    lines = adapter.read_text(encoding="utf-8").splitlines(True)
    hits = [i for i, l in enumerate(lines) if l.startswith("| `file_search` |")]
    assert len(hits) == 1, "%s: expected one file_search row" % adapter.name
    lines.insert(hits[0] + 1, BAD_ROW)
    adapter.write_text("".join(lines), encoding="utf-8")
    return hits[0] + 2


def wrote_lines(proc: subprocess.CompletedProcess) -> List[str]:
    return [l for l in proc.stdout.splitlines() if l.startswith("wrote ")]


def test_degradation(gen):
    """AC-2.2: the "When unavailable" cell is the first sentence of the
    notes cell that starts with `No renderer:`, `If the platform`, or
    `No agent-side`, with its terminal period; `—` when none does."""
    assert gen.degradation("Built-in Glob tool") == "—"
    assert gen.degradation("") == "—"
    assert gen.degradation("One self-contained HTML page per draft. " + NO_RENDERER) == NO_RENDERER
    assert gen.degradation("Ask the user to switch to Plan Mode; continue when they have. "
                           + DEGRADATION) == DEGRADATION
    assert gen.degradation(DEGRADATION + " Then carry on.") == DEGRADATION
    assert gen.degradation("Really? " + NO_AGENT_SIDE) == NO_AGENT_SIDE
    assert gen.degradation("Not the platform. If the platform has no toggle, stop!") == (
        "If the platform has no toggle, stop!")


@pytest.mark.parametrize("adapter", ("cursor", "claude-code"))
def test_capability_map(gen, adapter):
    """AC-2.2: the map opens with the lead sentence and the three-column
    header, has one row per neutral name in the adapter's row order with the
    mapping cell verbatim, a sub-row per further `Task` variant, and the
    degradation sentence (or `—`) in the last cell."""
    table = gen.parse_adapter(adapter_path(adapter))
    assert table.verdict == "pass", table.reasons
    text = gen.capability_map(adapter, REPO_ROOT)
    assert text == gen.render_map(table)
    assert text.endswith("|\n") and not text.endswith("\n\n")
    lines = text.splitlines()
    assert lines[:6] == ["## Capability Map", "", MAP_LEAD, ""] + MAP_HEADER
    rows = [cells(line) for line in lines[6:]]
    assert len(rows) == len(table.rows)

    seen = set()
    expected_first = []  # type: List[str]
    for row in table.rows:
        expected_first.append("`%s`" % (row.variant if row.name in seen else row.name))
        seen.add(row.name)
    assert [r[0] for r in rows] == expected_first
    assert [c for c in expected_first if c.strip("`") in table.names] == \
        ["`%s`" % name for name in table.names], "one row per neutral name, adapter order"
    assert [r[1] for r in rows] == [row.mapping for row in table.rows]
    if adapter == "claude-code":
        assert "`Task({ readonly: true })`" in [r[0] for r in rows]
        assert [r[0] for r in rows][:2] == ["`Task`", "`Task({ readonly: true })`"]

    by_name = {r[0].strip("`"): r for r in rows}
    assert by_name["canvas-preview"][2] == NO_RENDERER
    assert by_name["Plan Mode"][2] == DEGRADATION
    assert by_name["AskQuestion"][2] == "—"
    assert by_name["Plan Mode"][1] == table.rows[-1].mapping


def test_capability_map_rejects_bad_table(gen, tmp_path):
    """AC-2.2: a table that does not parse raises ValueError carrying the
    parser's reasons, so a caller never renders a partial map."""
    (tmp_path / "adapters").mkdir()
    shutil.copy(FIXTURES / "malformed-cells" / "codex.md", tmp_path / "adapters" / "codex.md")
    with pytest.raises(ValueError, match=r"^malformed adapters/codex\.md:\d+$"):
        gen.capability_map("codex", tmp_path)
    shutil.copy(FIXTURES / "missing-section" / "codex.md", tmp_path / "adapters" / "codex.md")
    with pytest.raises(ValueError, match=r"^section .* in adapters/codex\.md$"):
        gen.capability_map("codex", tmp_path)


def test_writ_mdc(gen, tmp_path):
    """AC-2.1: the written `cursor/writ.mdc` is the three frontmatter lines,
    the generated-file comment, the `system-instructions.md` body with only
    its frontmatter removed, then the Cursor map as the last `## ` section;
    its `## Prime Directive` section is byte-equal to the source's."""
    tree = tmp_tree(tmp_path)
    proc = run_tree(tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (tree / "cursor" / "writ.mdc").read_text(encoding="utf-8")
    source = (tree / "system-instructions.md").read_text(encoding="utf-8")
    assert source.startswith(FRONTMATTER)
    body = source[len(FRONTMATTER):]
    assert body.startswith("\n# Writ") and body.endswith("\n")

    assert text.startswith(FRONTMATTER + WRIT_MDC_COMMENT + "\n" + body + "\n## Capability Map\n")
    assert text == FRONTMATTER + WRIT_MDC_COMMENT + "\n" + body + "\n" + gen.capability_map("cursor", tree)
    assert text == gen.render_writ_mdc(tree)
    headings = [l for l in text.splitlines() if l.startswith("## ")]
    assert headings[-1] == "## Capability Map"
    assert headings.count("## Capability Map") == 1
    assert prime_directive(source)
    assert prime_directive(text) == prime_directive(source)
    assert sorted(p.name for p in (tree / "cursor").iterdir()) == ["writ.mdc"]


def test_claude_md_map(gen, tmp_path):
    """AC-2.3: the written `claude-code/CLAUDE.md` carries `## Capability Map`
    with the Claude Code rows between the Commands table and `## Agents`, and
    `gen-claude-md.py --check` on the written tree prints `pass`."""
    tree = tmp_tree(tmp_path)
    proc = run_tree(tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = (tree / "claude-code" / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    table_header = lines.index("| Command | File | Purpose |")
    map_heading = lines.index("## Capability Map")
    agents_heading = lines.index("## Agents")
    assert table_header < map_heading < agents_heading
    command_rows = [i for i, l in enumerate(lines) if l.startswith("| `/")]
    assert command_rows[-1] == map_heading - 2 and lines[map_heading - 1] == ""
    expected = gen.capability_map("claude-code", tree).splitlines()
    assert lines[map_heading:map_heading + len(expected)] == expected
    assert lines[map_heading + len(expected):map_heading + len(expected) + 2] == ["", "## Agents"]

    check = subprocess.run([sys.executable, str(tree / "scripts" / "gen-claude-md.py"), "--check"],
                           cwd=str(tree), capture_output=True, text=True)
    assert check.returncode == 0, check.stdout + check.stderr
    assert check.stdout.splitlines()[0] == "pass"


def test_write_mode_shape(tmp_path):
    """AC-2.4: on a clean tree write mode prints `pass`, one `wrote <path>`
    line per generated file (the driver's own, then each sub-generator's,
    relayed), and the summary last, exit 0; a second run prints the same
    and leaves every generated file byte-identical."""
    tree = tmp_tree(tmp_path)
    proc = run_tree(tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    wrote = wrote_lines(proc)
    assert lines[0] == "pass"
    assert lines[1:1 + len(wrote)] == wrote, "wrote lines must follow the verdict directly"
    assert wrote[0] == "wrote cursor/writ.mdc"
    assert "wrote claude-code/CLAUDE.md" in wrote
    claude_agents = sorted(p.name for p in (tree / "claude-code" / "agents").glob("writ-*.md"))
    stems = sorted(p.stem for p in (tree / "agents").glob("*.md"))
    assert len(claude_agents) == len(stems) >= 8
    for name in claude_agents:
        assert "wrote claude-code/agents/%s" % name in wrote
    for stem in stems:
        assert "wrote codex/agents/%s.toml" % stem in wrote
    assert len(wrote) == 2 + 2 * len(stems)
    assert lines[-1] == "gen-platform-trees: pass (%d written, 0 reasons)" % len(wrote)
    assert len(lines) == len(wrote) + 2
    assert not any(l.startswith("reason: ") for l in lines)

    first = generated_bytes(tree)
    again = run_tree(tree)
    assert again.returncode == 0, again.stdout + again.stderr
    assert again.stdout == proc.stdout
    assert generated_bytes(tree) == first


def test_write_blocked_by_bad_row(tmp_path):
    """AC-2.4: a malformed adapter row fails the run with `malformed
    adapters/<x>.md:<line>`, exit 1, and nothing is written."""
    tree = tmp_tree(tmp_path)
    before = generated_bytes(tree)
    line = seed_bad_row(tree / "adapters" / "codex.md")
    proc = run_tree(tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "fail"
    assert "reason: malformed adapters/codex.md:%d" % line in lines
    assert wrote_lines(proc) == []
    assert lines[-1] == "gen-platform-trees: fail (0 written, 1 reasons)"
    assert generated_bytes(tree) == before
    assert sorted(p.name for p in (tree / "cursor").iterdir()) == ["writ.mdc"]


def test_write_blocked_by_subgenerator_exit(tmp_path):
    """AC-2.4 (upstream error): a sub-generator whose `--check` exits 2 fails
    the run with `<gen> --check exited 2`, exit 1, and nothing is written."""
    tree = tmp_tree(tmp_path)
    before = generated_bytes(tree)
    (tree / "scripts" / "gen-claude-agents.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    proc = run_tree(tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "fail"
    assert "reason: gen-claude-agents --check exited 2" in lines
    assert wrote_lines(proc) == []
    assert lines[-1].startswith("gen-platform-trees: fail (0 written, ")
    assert generated_bytes(tree) == before


def test_write_folds_subgenerator_reason(tmp_path):
    """AC-2.4: a sub-generator's input reason is folded as
    `reason: <gen>: <kind> <detail>`, the run fails, and nothing is written.
    A stray agents/*.md stem is `unmapped` for both agent generators."""
    tree = tmp_tree(tmp_path)
    before = generated_bytes(tree)
    (tree / "agents" / "zz-extra-agent.md").write_text(
        "---\nname: zz-extra-agent\ndescription: Stray.\n---\n\n# Stray\n", encoding="utf-8")
    proc = run_tree(tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "fail"
    assert "reason: gen-claude-agents: unmapped zz-extra-agent" in lines
    assert "reason: gen-codex-agent-tomls: unmapped zz-extra-agent" in lines
    assert wrote_lines(proc) == []
    assert lines[-1] == "gen-platform-trees: fail (0 written, 2 reasons)"
    assert generated_bytes(tree) == before


def test_write_ignores_stale_outputs(tmp_path):
    """AC-2.4: a stale, missing, or hand-edited generated file is what write
    mode repairs, so a sub-generator's `stale`/`missing` reason never blocks
    the run; and one run converges, because the agent generators run before
    gen-claude-md, which reads their output."""
    tree = tmp_tree(tmp_path)
    clean = tmp_tree(tmp_path / "clean")
    assert run_tree(clean).returncode == 0
    expected = generated_bytes(clean)

    (tree / "claude-code" / "CLAUDE.md").write_text("hand edit\n", encoding="utf-8")
    (tree / "codex" / "agents" / "coding-agent.toml").unlink()
    (tree / "claude-code" / "agents" / "writ-coder.md").unlink()
    with (tree / "claude-code" / "agents" / "writ-tester.md").open("a", encoding="utf-8") as handle:
        handle.write("\nhand edit\n")
    proc = run_tree(tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.splitlines()[0] == "pass"
    assert "wrote claude-code/CLAUDE.md" in wrote_lines(proc)
    assert generated_bytes(tree) == expected
    assert "- `writ-coder.md`" in (tree / "claude-code" / "CLAUDE.md").read_text(encoding="utf-8")


def test_unverifiable_heading(tmp_path):
    """AC-2.4 (nil input): an adapter without its tool-table heading makes
    the run `unverifiable` with `section <heading> in adapters/<x>.md`,
    exit 0, and nothing is written."""
    tree = tmp_tree(tmp_path)
    before = generated_bytes(tree)
    adapter = tree / "adapters" / "cursor.md"
    text = adapter.read_text(encoding="utf-8")
    assert text.count("\n%s\n" % CURSOR_HEADING) == 1
    adapter.write_text(text.replace("\n%s\n" % CURSOR_HEADING, "\n"), encoding="utf-8")
    proc = run_tree(tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "unverifiable"
    assert lines[1] == "reason: section %s in adapters/cursor.md" % CURSOR_HEADING
    assert wrote_lines(proc) == []
    assert lines[-1] == "gen-platform-trees: unverifiable (0 written, 1 reasons)"
    assert generated_bytes(tree) == before
