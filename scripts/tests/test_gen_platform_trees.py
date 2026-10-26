#!/usr/bin/env python3
"""Tests for scripts/gen-platform-trees.py, Stories 1 to 4 of `2026-10-22-generated-platform-trees`.

Story 1 ships the adapter tool-table parser (`parse_adapter`), the
vocabulary rule (`vocabulary`, `unmapped`), and the repairs the golden
neutral set depends on: a `file_search` row in the Codex table, the OpenClaw
`readonly: true` row folded into `Task`, a `Plan Mode` row in all four
tables, one sentence in three command files, and the Plan Mode issue's
resolution. Story 2 adds the capability map (`degradation`, `render_map`,
`capability_map`), `render_writ_mdc`, and the driver's write mode, which
checks the four adapters and the three sub-generators before it writes
`cursor/writ.mdc` and runs the sub-generators' writers. Story 3 adds the
manifest and skills readers (`read_manifest`, `read_skills`) and
`render_codex_template`, which replaces the hand-maintained
`codex/AGENTS.md.template` as the second GENERATED file. Story 4 adds
`--check` (stale, missing, and orphan per generated path, the sub-generators'
checks folded in), `coverage` (unmapped names and vendor hits in commands/,
agents/, and skills/), the TARGETS table with the `fixture` target that
rewrites `(python3|bash) scripts/<name>` tokens into a `--out-dir` tree, and
the per-platform identity targets.

The module name has a hyphen, so the tests import it by path, the way
test_gen_claude_md.py does. Fixture adapters live under
scripts/tests/fixtures/platform-trees/<case>/<adapter>.md and carry the real
adapter headings, so `parse_adapter` selects the grammar by basename and the
reason strings name `adapters/<basename>`. Write-mode tests copy the tree
into `tmp_path` (`tmp_tree`) and run the driver there. Nothing here writes
to the repo.

Covers AC-1.1 to AC-1.5, AC-2.1 to AC-2.5, AC-3.1 to AC-3.4, and AC-4.1 to AC-4.5.

Run: uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

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
        "`EnterPlanMode`; present the contract proposal as the plan, opening with one "
        "line that approving it accepts the draft and runs nothing; "
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
    # Corrected after UAT (DEV-013): Codex's event stream shows shell
    # commands only, no Glob tool (codex-cli 0.163.0, 2026-10-24).
    assert row.mapping == "`rg --files -g '*pattern*'` through the shell"
    assert row.notes == "Codex has no Glob tool"


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
# CLI
# ---------------------------------------------------------------------------


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(MODULE_PATH)] + list(args),
                          cwd=str(REPO_ROOT), capture_output=True, text=True)


def test_cli_help():
    """CLI: `--help` exits 0 and names every mode."""
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


# ---------------------------------------------------------------------------
# Story 2: capability map, cursor/writ.mdc, claude-code/CLAUDE.md, write mode
# ---------------------------------------------------------------------------

TREE_DIRS = ("adapters", "agents", "commands", "skills", "cursor", "claude-code", "codex",
             # The claude-code-plugin target's output.
             "plugins", ".claude-plugin")
TREE_FILES = ("system-instructions.md", ".writ/manifest.yaml", "VERSION")
MAP_LEAD = "Commands name capabilities; this table maps them to this platform."
MAP_HEADER = ["| Capability | On this platform | When unavailable |", "|---|---|---|"]
NO_RENDERER = ("No renderer: write a structural description of each draft and say the "
               "drafts were not rendered.")
NO_AGENT_SIDE = "No agent-side mode: run discovery as a read-only conversation and say so"
FRONTMATTER = "---\nalwaysApply: true\n---\n"
WRIT_MDC_COMMENT = ("<!-- generated by scripts/gen-platform-trees.py from system-instructions.md "
                    "and adapters/cursor.md — do not hand-edit; regenerate -->")
TREES_SCRIPT = "scripts/gen-platform-trees.py"
GENERATED_ROOT_FILES = ("cursor/writ.mdc", "codex/AGENTS.md.template", "claude-code/CLAUDE.md")
BAD_ROW = "| `zz_bad` | two cells only |\n"
CURSOR_HEADING = "## Native Tool Availability"


def tmp_tree(tmp_path: Path) -> Path:
    """A copy of what the driver reads and writes: every top-level file in
    scripts/ (the plugin target copies the shipped ones), the source and
    generated directories, system-instructions.md, the manifest, and VERSION."""
    (tmp_path / "scripts").mkdir(parents=True)
    for script in (REPO_ROOT / "scripts").iterdir():
        if script.is_file():
            shutil.copy2(script, tmp_path / "scripts" / script.name)
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
    # Claude Code's question tool exists only in interactive sessions
    # (Phase 14 acceptance, 2026-10-24); the other adapters map no fallback.
    assert by_name["AskQuestion"][2] == (ASK_FALLBACK if adapter == "claude-code" else "—")
    assert by_name["Plan Mode"][1] == table.rows[-1].mapping


ASK_FALLBACK = ("If the platform has no question tool, as in headless `claude -p`, print the "
                "question as formatted text with numbered options.")


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
    # cursor/plugin/ is the cursor-plugin target's layout (Story 3 of the
    # plugin-distribution spec; its folder is not named here, so ac-trace
    # keeps crediting this file's AC tokens to this file's spec).
    assert sorted(p.name for p in (tree / "cursor").iterdir()) == ["plugin", "writ.mdc"]


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
    assert wrote[:2] == ["wrote cursor/writ.mdc", "wrote codex/AGENTS.md.template"]
    assert "wrote claude-code/CLAUDE.md" in wrote
    claude_agents = sorted(p.name for p in (tree / "claude-code" / "agents").glob("writ-*.md"))
    stems = sorted(p.stem for p in (tree / "agents").glob("*.md"))
    assert len(claude_agents) == len(stems) >= 8
    for name in claude_agents:
        assert "wrote claude-code/agents/%s" % name in wrote
    for stem in stems:
        assert "wrote codex/agents/%s.toml" % stem in wrote
    # The plugin trees (claude-code-plugin, then cursor-plugin) are written
    # last, one line per file.
    plugin = sorted(["wrote .claude-plugin/marketplace.json"] + [
        "wrote " + p.relative_to(tree).as_posix()
        for top in (("plugins", "writ"), ("cursor", "plugin"))
        for p in tree.joinpath(*top).rglob("*") if p.is_file()])
    assert sorted(wrote[len(wrote) - len(plugin):]) == plugin
    assert len(wrote) == 3 + 2 * len(stems) + len(plugin)
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
    # cursor/plugin/ is the cursor-plugin target's layout (Story 3 of the
    # plugin-distribution spec; its folder is not named here, so ac-trace
    # keeps crediting this file's AC tokens to this file's spec).
    assert sorted(p.name for p in (tree / "cursor").iterdir()) == ["plugin", "writ.mdc"]


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
    (tree / "codex" / "AGENTS.md.template").write_text("hand edit\n", encoding="utf-8")
    (tree / "codex" / "agents" / "coding-agent.toml").unlink()
    (tree / "claude-code" / "agents" / "writ-coder.md").unlink()
    with (tree / "claude-code" / "agents" / "writ-tester.md").open("a", encoding="utf-8") as handle:
        handle.write("\nhand edit\n")
    proc = run_tree(tree)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.splitlines()[0] == "pass"
    assert "wrote claude-code/CLAUDE.md" in wrote_lines(proc)
    assert "wrote codex/AGENTS.md.template" in wrote_lines(proc)
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


# ---------------------------------------------------------------------------
# Story 3: codex/AGENTS.md.template
# ---------------------------------------------------------------------------

CODEX_TEMPLATE_REL = "codex/AGENTS.md.template"
MANIFEST_REL = ".writ/manifest.yaml"
# Line 1 of the hand-maintained file, the contract install.sh merge_agents_md
# and update.sh rely on; pinned as a literal copied from that file, not read
# from git, so a regeneration that changes it fails here.
CODEX_MARKER = (
    "<!-- Writ-managed AGENTS.md fragment: merged between HTML comment markers "
    "writ:start and writ:end by install/update scripts. Source of truth: "
    "codex/AGENTS.md.template in the Writ repository (edit there, not by hand in "
    "downstream AGENTS.md). -->")
# Rule 12's comment; the sources name no adapters/ path (AC-3.2, AC-5.2).
CODEX_COMMENT = (
    "<!-- generated by scripts/gen-platform-trees.py from .writ/manifest.yaml, "
    "skills/*/SKILL.md, and the Codex adapter tool table \u2014 do not hand-edit; regenerate -->")
# AC-3.2: the `## ` headings, in this order and no other.
CODEX_SECTIONS = [
    "## Writ on Codex", "## Prime Directive", "## Available Commands", "## Available Agents", "## Available Skills",
    "## Built-in Codex slash commands vs Writ", "## Capability Map", "## Catalog source",
]
CODEX_INTRO = (
    "Writ uses `.writ/` for specs and artifacts, `.codex/commands/*.md` for workflows, "
    "`.codex/agents/*.toml` for subagents, `.agents/skills/` for AgentSkills-format "
    "capabilities. The Prime Directive below applies to every session; the full system "
    "instructions are in `.codex/system-instructions.md`. Map tools with the Capability Map below.")
# The intro's second paragraph, verbatim as run in .writ/eval/codex-verify-d2/
# (variant intro-op); a rewording is an untested variant.
CODEX_VERIFY = (
    "On Codex, verify a claim about this project by reading or running the code through the "
    "shell before you answer; the read-only sandbox allows that. Do it even when the user says "
    "checking is unnecessary. Declining to confirm is not verification.")
CODEX_BUILTINS_LINK = "https://developers.openai.com/codex/cli/slash-commands"
CODEX_CATALOG_SOURCE = (
    "Command and agent metadata also lives in `.writ/manifest.yaml` (upstream Writ repo). "
    "Regenerate root `SKILL.md` with `scripts/gen-skill.sh` when extending the manifest.")
COMMAND_HEADER = ["| Command | File | Purpose |", "|---------|------|---------|"]
AGENT_HEADER = ["| Agent | TOML | Purpose |", "|-------|------|---------|"]
SKILL_HEADER = ["| Skill | File | Description |", "|-------|------|-------------|"]
CODEX_CAP = 16384  # bytes; Codex's own AGENTS.md budget is 32 KiB (story Notes)

MINI_MANIFEST = """version: 1
categories:
  - id: entry
    label: "Start here"
commands:
  - name: writ
    file: commands/writ.md
    category: entry
    purpose: "Route."
agents:
  - name: coding-agent
    file: agents/coding-agent.md
    purpose: "Code."
"""
# (id, old text, new text, the ValueError message read_manifest raises)
MANIFEST_ERRORS = [
    ("no-categories", "categories:\n", "categories_x:\n", "manifest no categories section"),
    ("no-commands", "commands:\n", "commands_x:\n", "manifest no commands section"),
    ("no-agents", "agents:\n", "agents_x:\n", "manifest no agents section"),
    ("empty-commands", "  - name: writ\n    file: commands/writ.md\n    category: entry\n    purpose: \"Route.\"\n",
     "", "manifest no commands"),
    ("category-missing-label", '    label: "Start here"\n', "", "manifest category entry missing label"),
    ("command-missing-name", "  - name: writ\n", "  - name:\n", "manifest command missing name"),
    ("command-missing-category", "    category: entry\n", "", "manifest writ missing category"),
    ("command-missing-purpose", '    purpose: "Route."\n', "", "manifest writ missing purpose"),
    ("command-unknown-category", "    category: entry\n", "    category: zz\n", "manifest writ category zz"),
    ("command-duplicate", "agents:\n",
     "  - name: writ\n    file: commands/writ.md\n    category: entry\n    purpose: \"Again.\"\nagents:\n",
     "manifest duplicate writ"),
    ("agent-missing-purpose", '    purpose: "Code."\n', "", "manifest coding-agent missing purpose"),
]


def manifest_section(text: str, key: str) -> List[Dict[str, str]]:
    """Entries of the top-level `key:` list in the manifest, read with a regex
    independent of the driver's reader: each `  - ` starts an entry, its
    `    field: value` lines fill it, and a double-quoted value loses its
    quotes. The section runs to the next unindented, non-comment line."""
    match = re.search(r"^%s:\n((?:[ #].*\n|\n)*)" % re.escape(key), text, re.M)
    assert match, "manifest has no %s section" % key
    entries = []  # type: List[Dict[str, str]]
    for block in re.split(r"^  - ", match.group(1), flags=re.M)[1:]:
        entry = {}  # type: Dict[str, str]
        for field in re.finditer(r"^\s*([a-z_]+): (.*)$", block, re.M):
            value = field.group(2).strip()
            entry[field.group(1)] = value[1:-1] if value.startswith('"') else value
        entries.append(entry)
    return entries


def skill_descriptions(root: Path) -> List[Tuple[str, str]]:
    """(directory name, frontmatter description) per skills/*/SKILL.md, sorted."""
    out = []  # type: List[Tuple[str, str]]
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        frontmatter = path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
        match = re.search(r'^description:\s*"?(.*?)"?\s*$', frontmatter, re.M)
        out.append((path.parent.name, match.group(1) if match else ""))
    return out


def sections(lines: List[str], level: int) -> List[Tuple[str, List[str]]]:
    """(heading, body) per heading with exactly `level` hashes; a body runs
    to the next heading of that level or higher."""
    out = []  # type: List[Tuple[str, List[str]]]
    current = None  # type: ignore[assignment]
    for line in lines:
        match = re.match(r"^(#{1,6}) ", line)
        if match and len(match.group(1)) <= level:
            current = (line, []) if len(match.group(1)) == level else None
            if current:
                out.append(current)
            continue
        if current is not None:
            current[1].append(line)
    return out


def table(body: List[str]) -> List[List[str]]:
    return [cells(line) for line in body if line.startswith("|")]


def drop_purpose(tree: Path) -> None:
    path = tree / MANIFEST_REL
    lines = path.read_text(encoding="utf-8").splitlines(True)
    at = lines.index("  - name: create-goal\n")
    del lines[next(i for i in range(at + 1, at + 6) if lines[i].startswith("    purpose:"))]
    path.write_text("".join(lines), encoding="utf-8")


def unknown_category(tree: Path) -> None:
    path = tree / MANIFEST_REL
    lines = path.read_text(encoding="utf-8").splitlines(True)
    at = lines.index("  - name: create-goal\n")
    lines[at + 2] = "    category: zz\n"
    path.write_text("".join(lines), encoding="utf-8")


def blank_description(tree: Path) -> None:
    path = tree / "skills" / "tdd-cycle" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert text.count("\ndescription: ") == 1
    path.write_text(re.sub(r"^description: .*$", 'description: ""', text, count=1, flags=re.M),
                    encoding="utf-8")


def inject_adapters(tree: Path) -> None:
    path = tree / "adapters" / "codex.md"
    text = path.read_text(encoding="utf-8")
    old = "| `file_search` | `rg --files -g '*pattern*'` through the shell |"
    assert text.count(old) == 1
    path.write_text(text.replace(old, "| `file_search` | `rg --files -g '*pattern*'` through the shell (see adapters/codex.md) |"),
                    encoding="utf-8")


# (id, mutation, the reason render_codex_template raises, whether the driver's
# own reason line carries it: gen-claude-md --check reads the same manifest
# and reports a missing purpose first, folded as `gen-claude-md: manifest …`)
FAIL_CLOSED = [
    ("manifest-purpose", drop_purpose, "manifest create-goal missing purpose", False),
    ("manifest-category", unknown_category, "manifest create-goal category zz", True),
    ("skill-description", blank_description, "skill tdd-cycle missing description", True),
    ("adapters-mention", inject_adapters, "codex template mentions adapters/", True),
]  # type: List[Tuple[str, Callable[[Path], None], str, bool]]


def test_read_manifest(gen):
    """AC-3.1: the manifest reader returns categories, commands (name,
    category, purpose), and agents in manifest order, purposes verbatim."""
    manifest = gen.read_manifest(REPO_ROOT)
    text = read(MANIFEST_REL)
    assert manifest.categories == [(e["id"], e["label"]) for e in manifest_section(text, "categories")]
    assert manifest.categories[0] == ("entry", "Start here")
    assert manifest.commands == [(e["name"], e["category"], e["purpose"])
                                 for e in manifest_section(text, "commands")]
    assert ("writ", "entry", "Restate a request, route it to the fitting command, and run it "
            "with its phases on the todo list.") in manifest.commands
    assert manifest.agents == [(e["name"], e["purpose"]) for e in manifest_section(text, "agents")]
    assert len(manifest.commands) >= 33 and len(manifest.agents) >= 8
    assert gen.read_skills(REPO_ROOT) == skill_descriptions(REPO_ROOT)
    assert len(gen.read_skills(REPO_ROOT)) >= 16


@pytest.mark.parametrize("old, new, reason", [(o, n, r) for _, o, n, r in MANIFEST_ERRORS],
                         ids=[i for i, _, _, _ in MANIFEST_ERRORS])
def test_read_manifest_errors(gen, tmp_path, old, new, reason):
    """AC-3.1: a manifest without a section, an entry without its name,
    category, or purpose, a category no `categories:` entry declares, or a
    duplicate command raises ValueError with `manifest <detail>`."""
    assert MINI_MANIFEST.count(old) == 1
    (tmp_path / ".writ").mkdir()
    (tmp_path / MANIFEST_REL).write_text(MINI_MANIFEST.replace(old, new), encoding="utf-8")
    with pytest.raises(ValueError) as err:
        gen.read_manifest(tmp_path)
    assert str(err.value) == reason
    (tmp_path / MANIFEST_REL).write_text(MINI_MANIFEST, encoding="utf-8")
    assert gen.read_manifest(tmp_path) == gen.Manifest(
        [("entry", "Start here")], [("writ", "entry", "Route.")], [("coding-agent", "Code.")])


def test_read_errors_name_the_missing_file(gen, tmp_path):
    """AC-3.1: a missing manifest or skills directory is an OSError whose
    filename write mode reports as `missing <path>`; a SKILL.md without a
    description is `skill <name> missing description`."""
    with pytest.raises(OSError) as err:
        gen.read_manifest(tmp_path)
    assert gen.relative(tmp_path, err.value.filename) == MANIFEST_REL
    with pytest.raises(OSError) as err:
        gen.read_skills(tmp_path)
    assert gen.relative(tmp_path, err.value.filename) == "skills"
    (tmp_path / "skills" / "zz-skill").mkdir(parents=True)
    (tmp_path / "skills" / "zz-skill" / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"^skill zz-skill missing description$"):
        gen.read_skills(tmp_path)
    (tmp_path / "skills" / "zz-skill" / "SKILL.md").write_text(
        "---\nname: zz-skill\ndescription: 'It''s a | test'\n---\n", encoding="utf-8")
    assert gen.read_skills(tmp_path) == [("zz-skill", "It's a | test")]


def test_codex_template(gen):
    """AC-3.1, AC-3.2, AC-3.4: the rendered template opens with the
    merge-marker line and the generator comment; its `## ` sections come in
    AC-3.2's order; every manifest command is one row in its category table
    (manifest order, purpose verbatim, `.codex/commands/<name>.md`), with
    `### Start here` first and holding `/writ`; every manifest agent and every
    skills/*/SKILL.md has its row; the built-ins paragraph keeps its link; the
    map is the Codex map; no `adapters/`; under 16384 bytes."""
    text = gen.render_codex_template(REPO_ROOT)
    manifest = read(MANIFEST_REL)
    categories = [(e["id"], e["label"]) for e in manifest_section(manifest, "categories")]
    commands = [(e["name"], e["category"], e["purpose"]) for e in manifest_section(manifest, "commands")]
    agents = [(e["name"], e["purpose"]) for e in manifest_section(manifest, "agents")]
    skills = skill_descriptions(REPO_ROOT)
    assert categories[0] == ("entry", "Start here")
    assert len(commands) >= 33 and len(agents) >= 8 and len(skills) >= 16

    lines = text.splitlines()
    assert lines[0] == CODEX_MARKER
    assert lines[1] == CODEX_COMMENT
    assert lines[2] == "" and lines[3] == "## Writ on Codex"
    assert "adapters/" not in text
    assert "\n\n\n" not in text and text.endswith("\n") and not text.endswith("\n\n")
    assert "\r" not in text
    assert len(text.encode("utf-8")) < CODEX_CAP

    h2 = sections(lines, 2)
    assert [heading for heading, _ in h2] == CODEX_SECTIONS
    body = dict(h2)
    assert body["## Writ on Codex"] == ["", CODEX_INTRO, "", CODEX_VERIFY, ""]
    assert "the Capability Map below" in CODEX_INTRO

    tables = sections(body["## Available Commands"], 3)
    with_commands = [(cid, label) for cid, label in categories
                     if any(category == cid for _, category, _ in commands)]
    assert len(with_commands) < len(categories), "a category with no commands renders no table"
    assert [heading for heading, _ in tables] == ["### %s" % label for _, label in with_commands]
    assert tables[0][0] == "### Start here"
    assert body["## Available Commands"][:2] == ["", "### Start here"]
    for (cid, _), (heading, tbody) in zip(with_commands, tables):
        rows = table(tbody)
        assert rows[:2] == [cells(line) for line in COMMAND_HEADER], heading
        assert rows[2:] == [["`/%s`" % name, "`.codex/commands/%s.md`" % name, purpose]
                            for name, category, purpose in commands if category == cid], heading
    assert ["`/writ`", "`.codex/commands/writ.md`"] in [row[:2] for row in table(tables[0][1])]
    for name, _, _ in commands:
        assert text.count("| `/%s` |" % name) == 1, name
    assert sum(len(table(tbody)) - 2 for _, tbody in tables) == len(commands)
    planning = [row[0] for row in table(dict(tables)["### Planning & Specification"])[2:]]
    # `/why` (why-command spec, Story 2) sorts between the two.
    assert planning[-3:] == ["`/verify-spec`", "`/why`", "`/writ-design`"]

    rows = table(body["## Available Agents"])
    assert rows[:2] == [cells(line) for line in AGENT_HEADER]
    assert rows[2:] == [[name, "`.codex/agents/%s.toml`" % name, purpose] for name, purpose in agents]

    rows = table(body["## Available Skills"])
    assert rows[:2] == [cells(line) for line in SKILL_HEADER]
    assert rows[2:] == [["`%s`" % name, "`.agents/skills/%s/SKILL.md`" % name, description]
                        for name, description in skills]

    builtins = body["## Built-in Codex slash commands vs Writ"]
    assert builtins[0] == "" and builtins[2] == "" and len(builtins) == 3
    assert builtins[1].startswith("Codex built-ins include `/plan`, `/review`, `/status`")
    assert "([official list](%s))" % CODEX_BUILTINS_LINK in builtins[1]
    assert "`.codex/commands/status.md` or `.codex/commands/review.md`" in builtins[1]

    assert ["## Capability Map"] + body["## Capability Map"] == \
        gen.capability_map("codex", REPO_ROOT).splitlines() + [""]
    assert body["## Catalog source"] == ["", CODEX_CATALOG_SOURCE]


def test_codex_template_carries_prime_directive(gen):
    """Phase 14 acceptance: Codex loads AGENTS.md every session but has no
    import, so the Writ block carries the Prime Directive itself. The section
    holds the obligation line, the Hard Constraints, and the Recommendation
    Semantics byte for byte from system-instructions.md, leaves the
    `--recommend` rules to the installed file, and names that file."""
    text = gen.render_codex_template(REPO_ROOT)
    source = read("system-instructions.md")

    def sub(heading, upto):
        start = source.index(heading)
        return source[start:source.index(upto, start)]

    section = text[text.index("## Prime Directive\n"):text.index("## Available Commands")]
    assert sub("### Hard Constraints", "### Recommended Delivery Exception") in section
    assert sub("### Recommendation Semantics", "## Interaction Tool Selection").rstrip("\n") in section
    obligation = source.splitlines()[source.splitlines().index("## Prime Directive") + 2]
    assert obligation.startswith("Writ's first obligation is accurate assessment")
    assert section.splitlines()[2] == obligation
    assert "### Recommended Delivery Exception" not in section
    assert "`.codex/system-instructions.md`" in section
    assert "Read bundled" not in text


def test_codex_template_verify_line(gen):
    """Phase 14 acceptance D2: under the Hard Constraints alone, Codex met
    "confirm this, no need to check the code" by declining to confirm and
    read the code in 1 of 10 runs. With the verify line in the intro it read
    the code in 10 of 10, and 5 of 5 on a reworded waiver; moving the Prime
    Directive first or last did not help (.writ/eval/codex-verify-d2/). The
    line sits in `## Writ on Codex`, above the Prime Directive, once."""
    text = gen.render_codex_template(REPO_ROOT)
    assert gen.CODEX_VERIFY == CODEX_VERIFY
    assert text.count(CODEX_VERIFY) == 1
    assert text.index("## Writ on Codex\n") < text.index(CODEX_VERIFY) < text.index("## Prime Directive\n")
    assert len(text.encode("utf-8")) < CODEX_CAP


def test_codex_template_matches_committed(gen):
    """AC-3.2, AC-3.3: the committed `codex/AGENTS.md.template` is a fresh
    render, byte for byte (Story 4's stale check depends on this baseline),
    and its line 1 is the merge-marker contract."""
    committed = read(CODEX_TEMPLATE_REL)
    assert committed.splitlines()[0] == CODEX_MARKER
    assert gen.render_codex_template(REPO_ROOT) == committed


@pytest.mark.parametrize("mutate, reason, own_reason",
                         [(m, r, o) for _, m, r, o in FAIL_CLOSED],
                         ids=[i for i, _, _, _ in FAIL_CLOSED])
def test_codex_template_fails_closed(gen, tmp_path, mutate, reason, own_reason):
    """AC-3.1: a manifest command without its purpose or with an undeclared
    category, a SKILL.md without a description, or an `adapters/` mention
    reaching a map cell makes `render_codex_template` raise ValueError naming
    it; write mode then prints `fail` with one reason, exit 1, and writes
    nothing (a sub-generator that reads the same manifest may own the reason
    line)."""
    tree = tmp_tree(tmp_path)
    before = generated_bytes(tree)
    mutate(tree)
    with pytest.raises(ValueError) as err:
        gen.render_codex_template(tree)
    assert str(err.value) == reason
    proc = run_tree(tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "fail"
    if own_reason:
        assert lines[1] == "reason: " + reason
    else:
        assert lines[1].startswith("reason: ") and lines[1].endswith(reason)
    assert wrote_lines(proc) == []
    assert lines[-1] == "gen-platform-trees: fail (0 written, 1 reasons)"
    assert len(lines) == 3
    assert generated_bytes(tree) == before
    assert not [p.name for p in (tree / "codex").iterdir() if p.name.startswith(".AGENTS")]


def test_codex_template_size_guard(gen, tmp_path):
    """AC-3.4: a render whose UTF-8 encoding reaches 16384 bytes raises
    ValueError with the byte count, so write mode fails closed instead of
    shipping a file Codex may truncate."""
    tree = tmp_tree(tmp_path)
    path = tree / MANIFEST_REL
    text = path.read_text(encoding="utf-8")
    old = '    purpose: "Create and compare visual references for Writ specifications."\n'
    assert text.count(old) == 1
    path.write_text(text.replace(old, '    purpose: "%s"\n' % ("x" * 12000)), encoding="utf-8")
    with pytest.raises(ValueError, match=r"^codex template \d+ bytes exceeds 16384$") as err:
        gen.render_codex_template(tree)
    assert int(str(err.value).split()[2]) >= 16384
    proc = run_tree(tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert proc.stdout.splitlines()[1] == "reason: " + str(err.value)
    assert wrote_lines(proc) == []


# ---------------------------------------------------------------------------
# Story 4: --check, coverage, tokens and targets, dev-only
# ---------------------------------------------------------------------------

CHECK_SUMMARY = "gen-platform-trees: %s (%d stale, %d missing, %d orphan, %d unmapped, %d vendor)"
CLEAN_SUMMARY = CHECK_SUMMARY % ("pass", 0, 0, 0, 0, 0)
UNMAPPED_REASON = "reason: unmapped file_search in adapters/codex.md"
VENDOR_FIXTURE = FIXTURES / "vendor" / "commands" / "vendor-fixture.md"
# technical-spec.md -> ## Tokens, applied here independently of the driver.
TOKEN = re.compile(rb"\b(python3|bash) scripts/([a-z0-9_-]+\.(?:py|sh))")
FIXTURE_ROOT = b"${PLUGIN_ROOT}/scripts"
# One invocation per interpreter, a prose mention, a bare path, and an
# uppercase name; CRLF, a tab, and a non-UTF-8 byte must survive untouched.
TOKEN_FIXTURE = (
    b"# Token fixture\n\n"
    b"Run `python3 scripts/foo.py --x` first.\n"
    b"Then `bash scripts/bar.sh`.\n"
    b"see scripts/ for details\n"
    b"scripts/foo.py\n"
    b"python3 scripts/Foo.py\n"
    b"\xe2\x80\x94 odd bytes\r\n\t\xff stay\n")
TOKEN_FIXTURE_REWRITTEN = (
    TOKEN_FIXTURE
    .replace(b"python3 scripts/foo.py --x", b"python3 ${PLUGIN_ROOT}/scripts/foo.py --x")
    .replace(b"bash scripts/bar.sh", b"bash ${PLUGIN_ROOT}/scripts/bar.sh"))
IDENTITY_TARGETS = ("cursor", "claude-code", "codex")
# (args, what makes it a usage error)
USAGE_ERRORS = [
    (("--target", "cursor", "--out-dir", "x"), "identity target with --out-dir"),
    (("--target", "fixture"), "non-identity target without --out-dir"),
    (("--target", "fixture", "--out-dir", "x", "--check"), "--target with --check"),
    (("--target", "fixture", "--out-dir", "x", "coverage"), "--target with coverage"),
    (("--target", "bogus", "--out-dir", "x"), "unknown target"),
    (("--out-dir", "x"), "--out-dir without --target"),
    (("coverage", "--check"), "two modes"),
]
# (id, token text inside the backticks, the tool it references or None)
TOOL_REFERENCES = [
    ("bare", "TodoWrite", "TodoWrite"),
    ("call-parens", 'Grep("pattern")', "Grep"),
    ("call-braces", "sessions_spawn({ task })", "sessions_spawn"),
    ("variant", "Task({ readonly: true })", "Task"),
    ("spaced-name", "Plan Mode", "Plan Mode"),
    ("dotted-field", "message.usage", None),
    ("url", "http://localhost:3000", None),
    ("path", "scripts/foo.py", None),
    ("dot-path", ".writ/state", None),
    ("key-value", "permissionMode: plan", None),
    ("flag", "--check", None),
    ("assignment", "exec=1", None),
    ("empty", "", None),
]


def snapshot(tree: Path) -> Dict[str, bytes]:
    """Every file under `tree` (bytecode caches excluded), keyed by relative
    path, so a test can assert that a run wrote nothing."""
    return {p.relative_to(tree).as_posix(): p.read_bytes()
            for p in sorted(tree.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def line_of(path: Path, needle: str) -> int:
    """The 1-based line of the one line in `path` that contains `needle`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [i for i, line in enumerate(lines) if needle in line]
    assert len(hits) == 1, "%s: expected %r on one line, found %d" % (path.name, needle, len(hits))
    return hits[0] + 1


def append_token(path: Path, token: str = "`TodoWrite`") -> int:
    """Append `token` as its own last line; returns that line's number."""
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n%s\n" % token)
    return len(path.read_text(encoding="utf-8").splitlines())


def reasons_of(proc: subprocess.CompletedProcess) -> List[str]:
    return [l for l in proc.stdout.splitlines() if l.startswith("reason: ")]


def check_lines(proc: subprocess.CompletedProcess, verdict: str, counts: Tuple[int, ...]) -> List[str]:
    """Assert the check shape with `verdict` on line 1 and the five-count
    summary last; returns the reason lines."""
    lines = proc.stdout.splitlines()
    assert lines[0] == verdict, proc.stdout + proc.stderr
    assert lines[-1] == CHECK_SUMMARY % ((verdict,) + counts), proc.stdout
    assert lines[1:-1] == reasons_of(proc), "only reason lines between verdict and summary"
    return reasons_of(proc)


def ship_filter(script: str) -> str:
    """The `is_shippable_script` body the way test_install_update_dev_scripts.sh
    extracts it: from `is_shippable_script() {` to the next line that is `}`."""
    lines = (REPO_ROOT / "scripts" / script).read_text(encoding="utf-8").splitlines(True)
    start = lines.index("is_shippable_script() {\n")
    end = next(i for i in range(start, len(lines)) if lines[i] == "}\n")
    return "".join(lines[start:end + 1])


def is_shippable(body: str, name: str) -> bool:
    proc = subprocess.run(["bash", "-c", body + '\nis_shippable_script "$1"', "_", name],
                          capture_output=True, text=True)
    return proc.returncode == 0


def edit_writ_mdc(tree: Path) -> None:
    with (tree / "cursor" / "writ.mdc").open("a", encoding="utf-8") as handle:
        handle.write("\nhand edit\n")


def delete_claude_md(tree: Path) -> None:
    (tree / "claude-code" / "CLAUDE.md").unlink()


def add_claude_agent(tree: Path) -> None:
    (tree / "claude-code" / "agents" / "writ-extra.md").write_text(
        "---\nname: writ-extra\ndescription: Extra.\n---\n\n# Extra\n", encoding="utf-8")


def add_stray_claude_agent(tree: Path) -> None:
    """A claude-code/agents/*.md outside gen-claude-agents' `writ-*.md` glob."""
    (tree / "claude-code" / "agents" / "helper.md").write_text(
        "---\nname: helper\ndescription: Stray.\n---\n\n# Helper\n", encoding="utf-8")


def add_codex_toml(tree: Path) -> None:
    (tree / "codex" / "agents" / "extra.toml").write_text('name = "extra"\n', encoding="utf-8")


def edit_codex_template(tree: Path) -> None:
    with (tree / "codex" / "AGENTS.md.template").open("a", encoding="utf-8") as handle:
        handle.write("\nhand edit\n")


def edit_claude_agent(tree: Path) -> None:
    with (tree / "claude-code" / "agents" / "writ-tester.md").open("a", encoding="utf-8") as handle:
        handle.write("\nhand edit\n")


# (id, mutation, the exact reason lines --check prints, the five counts).
# gen-claude-md lists claude-code/agents/*.md, so an orphan agent file also
# makes claude-code/CLAUDE.md stale; a hand-edited agent file is the agent
# generator's stale stem, folded. A stray file outside the `writ-*.md` glob
# is the driver's own orphan (no generator produces it; install.sh would
# ship it).
STALE_CASES = [
    ("stale-writ-mdc", edit_writ_mdc, ["stale cursor/writ.mdc"], (1, 0, 0, 0, 0)),
    ("missing-claude-md", delete_claude_md, ["missing claude-code/CLAUDE.md"], (0, 1, 0, 0, 0)),
    ("orphan-claude-agent", add_claude_agent,
     ["orphan claude-code/agents/writ-extra.md", "stale claude-code/CLAUDE.md"], (1, 0, 1, 0, 0)),
    ("orphan-stray-claude-agent", add_stray_claude_agent,
     ["orphan claude-code/agents/helper.md", "stale claude-code/CLAUDE.md"], (1, 0, 1, 0, 0)),
    ("orphan-codex-toml", add_codex_toml, ["orphan codex/agents/extra.toml"], (0, 0, 1, 0, 0)),
    ("stale-codex-template", edit_codex_template, ["stale codex/AGENTS.md.template"], (1, 0, 0, 0, 0)),
    ("stale-claude-agent", edit_claude_agent, ["gen-claude-agents: stale testing-agent"], (1, 0, 0, 0, 0)),
]  # type: List[Tuple[str, Callable[[Path], None], List[str], Tuple[int, int, int, int, int]]]


def test_check_clean(tmp_path):
    """AC-4.1: on a clean tree `--check` prints `pass` and the five-zero
    summary and nothing else, exit 0, and writes nothing; `coverage` prints
    the same; both also pass on the committed tree itself."""
    tree = tmp_tree(tmp_path)
    before = snapshot(tree)
    for args in (("--check",), ("coverage",)):
        proc = run_tree(tree, *args)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.splitlines() == ["pass", CLEAN_SUMMARY], args
        assert snapshot(tree) == before, args
    for args in (("--check",), ("coverage",)):
        proc = run_cli(*args)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        lines = proc.stdout.splitlines()
        assert lines[0] == "pass", "committed tree, %s: %s" % (args, proc.stdout)
        assert lines[-1] == CLEAN_SUMMARY


@pytest.mark.parametrize("mutate, expected, counts", [(m, r, c) for _, m, r, c in STALE_CASES],
                         ids=[i for i, _, _, _ in STALE_CASES])
def test_check_stale(tmp_path, mutate, expected, counts):
    """AC-4.1: a hand edit to a generated root file is `stale <path>`, a
    deleted `claude-code/CLAUDE.md` is `missing <path>`, an extra file under
    `claude-code/agents/` or `codex/agents/` is `orphan <path>`, and a
    hand-edited agent file is the agent generator's reason folded as
    `gen-claude-agents: stale <stem>`; in every case line 1 is `fail`, the
    summary counts the kinds, exit 1, and no byte changes."""
    tree = tmp_tree(tmp_path)
    mutate(tree)
    before = snapshot(tree)
    proc = run_tree(tree, "--check")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert check_lines(proc, "fail", counts) == ["reason: " + text for text in expected]
    assert wrote_lines(proc) == []
    assert snapshot(tree) == before


def test_check_counts(tmp_path):
    """AC-4.1: every STALE_CASES mutation at once -> one reason each and a
    summary whose counts add up (the deleted CLAUDE.md is missing, not stale,
    even though the orphan agent file would otherwise make it stale)."""
    tree = tmp_tree(tmp_path)
    for _, mutate, _, _ in STALE_CASES:
        mutate(tree)
    before = snapshot(tree)
    proc = run_tree(tree, "--check")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    reasons = check_lines(proc, "fail", (3, 1, 3, 0, 0))
    assert sorted(reasons) == sorted([
        "reason: stale cursor/writ.mdc", "reason: stale codex/AGENTS.md.template",
        "reason: missing claude-code/CLAUDE.md", "reason: orphan claude-code/agents/writ-extra.md",
        "reason: orphan claude-code/agents/helper.md",
        "reason: orphan codex/agents/extra.toml", "reason: gen-claude-agents: stale testing-agent"])
    assert snapshot(tree) == before


@pytest.mark.parametrize("token, name", [(t, n) for _, t, n in TOOL_REFERENCES],
                         ids=[i for i, _, _ in TOOL_REFERENCES])
def test_tool_reference(gen, token, name):
    """AC-4.2 (the whole-token rule): a backticked token references a tool
    when its leading identifier is followed by nothing or by call syntax
    (`(` or `{`); a dotted field, a URL, a path, a `key: value`, a flag, or
    an assignment references none."""
    assert gen.tool_reference(token) == name


def test_vendor_hit(tmp_path):
    """AC-4.2: the vendor fixture copied into a tree's commands/ makes
    `coverage` print exactly one `vendor <name> in commands/<f>.md:<line>`
    reason for `` `TodoWrite` `` and one for `` `Grep("pattern")` `` with the
    real line numbers, none for the allowlisted `` `Read` `` or the dotted
    `` `message.usage` ``, the summary counting 2 vendor, exit 1; `--check`
    reports the same two; a token in agents/<f>.md or skills/<name>/SKILL.md
    is reported with that path; nothing is written."""
    tree = tmp_tree(tmp_path)
    shutil.copy(VENDOR_FIXTURE, tree / "commands" / VENDOR_FIXTURE.name)
    rel = "commands/" + VENDOR_FIXTURE.name
    for needle in ("`Read`", "`message.usage`"):
        assert line_of(VENDOR_FIXTURE, needle)
    expected = [
        "reason: vendor TodoWrite in %s:%d" % (rel, line_of(VENDOR_FIXTURE, "`TodoWrite`")),
        "reason: vendor Grep in %s:%d" % (rel, line_of(VENDOR_FIXTURE, '`Grep("pattern")`')),
    ]
    before = snapshot(tree)
    proc = run_tree(tree, "coverage")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert check_lines(proc, "fail", (0, 0, 0, 0, 2)) == expected
    proc = run_tree(tree, "--check")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    # A new command also leaves the plugin trees behind (claude-code-plugin,
    # then cursor-plugin); those reasons come before the vendor scan.
    assert check_lines(proc, "fail", (1, 2, 0, 0, 2)) == [
        "reason: stale plugins/writ/.claude-plugin/plugin.json",
        "reason: missing plugins/writ/" + rel,
        "reason: missing cursor/plugin/" + rel,
    ] + expected
    assert wrote_lines(proc) == []
    assert snapshot(tree) == before

    agent_line = append_token(tree / "agents" / "coding-agent.md")
    skill_line = append_token(tree / "skills" / "tdd-cycle" / "SKILL.md", "`sessions_spawn({ task })`")
    proc = run_tree(tree, "coverage")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert check_lines(proc, "fail", (0, 0, 0, 0, 4)) == expected + [
        "reason: vendor TodoWrite in agents/coding-agent.md:%d" % agent_line,
        "reason: vendor sessions_spawn in skills/tdd-cycle/SKILL.md:%d" % skill_line,
    ]


def test_coverage_unmapped(tmp_path):
    """AC-4.2: the Story 1 parity fixture (no `file_search` row) copied over
    adapters/codex.md makes `coverage` print exactly
    `reason: unmapped file_search in adapters/codex.md` and `--check` print
    the same reason first, then the stale Codex template the missing row
    implies (every table parsed, so the renders still run), exit 1, nothing
    written."""
    tree = tmp_tree(tmp_path)
    shutil.copy(FIXTURES / "parity-no-file-search" / "codex.md", tree / "adapters" / "codex.md")
    before = snapshot(tree)
    proc = run_tree(tree, "coverage")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert check_lines(proc, "fail", (0, 0, 0, 1, 0)) == [UNMAPPED_REASON]
    proc = run_tree(tree, "--check")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert check_lines(proc, "fail", (1, 0, 0, 1, 0)) == [
        UNMAPPED_REASON, "reason: stale codex/AGENTS.md.template"]
    assert wrote_lines(proc) == []
    assert snapshot(tree) == before


def test_fixture_target(gen, tmp_path):
    """AC-4.3: `--target fixture --out-dir <dir>` writes every commands/*.md
    (the preamble included) and every skills/<name>/SKILL.md under
    `<dir>/fixture/`, each `python3 scripts/<name>` or `bash scripts/<name>`
    match rewritten to `${PLUGIN_ROOT}/scripts/<name>` with the same
    interpreter and every other byte identical: a prose `scripts/` mention, a
    bare path, and an uppercase name stay; one `wrote` line per file; nothing
    is written in place."""
    tree = tmp_tree(tmp_path / "tree")
    fixture = tree / "commands" / "zz-token-fixture.md"
    fixture.write_bytes(TOKEN_FIXTURE)
    assert gen.TARGETS["fixture"]["script_root"] == FIXTURE_ROOT.decode()
    assert gen.TOKEN.pattern == TOKEN.pattern
    commands = sorted((tree / "commands").glob("*.md"))
    skills = sorted((tree / "skills").glob("*/SKILL.md"))
    assert "_preamble.md" in [p.name for p in commands]
    assert any(TOKEN.search(p.read_bytes()) for p in commands if p != fixture), \
        "a real command must carry an invocation token"
    out = tmp_path / "out"
    before = snapshot(tree)

    proc = run_tree(tree, "--target", "fixture", "--out-dir", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    wrote = wrote_lines(proc)
    assert lines[0] == "pass"
    assert wrote == (["wrote fixture/commands/%s" % p.name for p in commands]
                     + ["wrote fixture/skills/%s/SKILL.md" % p.parent.name for p in skills])
    assert lines[-1] == "gen-platform-trees: pass (%d written, 0 reasons)" % len(wrote)
    assert len(lines) == len(wrote) + 2
    assert snapshot(tree) == before

    got = (out / "fixture" / "commands" / fixture.name).read_bytes()
    assert got == TOKEN_FIXTURE_REWRITTEN
    got_lines = got.split(b"\n")
    assert got_lines[2] == b"Run `python3 ${PLUGIN_ROOT}/scripts/foo.py --x` first."
    assert got_lines[3] == b"Then `bash ${PLUGIN_ROOT}/scripts/bar.sh`."
    assert got_lines[4:7] == [b"see scripts/ for details", b"scripts/foo.py", b"python3 scripts/Foo.py"]
    assert got_lines[7:] == TOKEN_FIXTURE.split(b"\n")[7:]

    def rewritten(data: bytes) -> bytes:
        return TOKEN.sub(lambda m: m.group(1) + b" " + FIXTURE_ROOT + b"/" + m.group(2), data)

    assert rewritten(TOKEN_FIXTURE) == TOKEN_FIXTURE_REWRITTEN
    for p in commands:
        assert (out / "fixture" / "commands" / p.name).read_bytes() == rewritten(p.read_bytes()), p.name
    for p in skills:
        assert (out / "fixture" / "skills" / p.parent.name / "SKILL.md").read_bytes() == \
            rewritten(p.read_bytes()), p.parent.name
    written = sorted(q.relative_to(out).as_posix() for q in out.rglob("*") if q.is_file())
    assert written == sorted(["fixture/commands/%s" % p.name for p in commands]
                             + ["fixture/skills/%s/SKILL.md" % p.parent.name for p in skills])


def test_targets_cover_every_generator(gen):
    """AC-4.3: the three identity targets share the `scripts` root and
    between them own every GENERATED path and every SUBGENERATOR exactly
    once, so no generated file is skipped by `--target <platform>`; the
    non-identity targets are the fixture and the two plugin trees
    (`claude-code-plugin`, and `cursor-plugin`, which keeps the `scripts`
    root but writes a tree)."""
    identity = [t for t in gen.TARGETS if gen.is_identity(t)]
    assert identity == list(IDENTITY_TARGETS)
    assert all(gen.TARGETS[t]["script_root"] == "scripts" for t in identity)
    assert [t for t in gen.TARGETS if t not in identity] == ["fixture", "claude-code-plugin", "cursor-plugin"]
    owned = [rel for t in identity for rel in gen.TARGETS[t]["generated"]]
    assert sorted(owned) == sorted(rel for rel, _ in gen.GENERATED) and len(owned) == len(set(owned))
    subs = [g for t in identity for g in gen.TARGETS[t]["subgenerators"]]
    assert sorted(subs) == sorted(gen.SUBGENERATORS) and len(subs) == len(set(subs))


@pytest.mark.parametrize("target", IDENTITY_TARGETS)
def test_identity_target(tmp_path, target):
    """AC-4.3: `--target <identity>` runs write mode for that platform's files
    only (cursor: writ.mdc; claude-code: the agent files and CLAUDE.md; codex:
    the template and the TOMLs) and writes no commands/ or skills/ output
    anywhere: on a clean tree the set of files and every byte are unchanged."""
    tree = tmp_tree(tmp_path)
    before = snapshot(tree)
    proc = run_tree(tree, "--target", target)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    wrote = wrote_lines(proc)
    assert lines[0] == "pass"
    assert lines[-1] == "gen-platform-trees: pass (%d written, 0 reasons)" % len(wrote)
    stems = sorted(p.stem for p in (tree / "agents").glob("*.md"))
    expected = {
        "cursor": {"wrote cursor/writ.mdc"},
        "claude-code": {"wrote claude-code/CLAUDE.md"} | {
            "wrote claude-code/agents/%s" % p.name for p in (tree / "claude-code" / "agents").glob("writ-*.md")},
        "codex": {"wrote codex/AGENTS.md.template"} | {"wrote codex/agents/%s.toml" % s for s in stems},
    }[target]
    assert set(wrote) == expected and len(wrote) == len(expected)
    assert all(line.startswith("wrote %s/" % target) for line in wrote)
    assert snapshot(tree) == before


@pytest.mark.parametrize("args, why", USAGE_ERRORS, ids=[w for _, w in USAGE_ERRORS])
def test_target_usage_errors(tmp_path, args, why):
    """AC-4.3: an identity target with --out-dir, a non-identity target
    without one, --target beside --check or coverage, an unknown target,
    --out-dir alone, or two modes at once is a usage error: usage on stderr,
    empty stdout, exit 2, nothing written."""
    tree = tmp_tree(tmp_path)
    before = snapshot(tree)
    proc = run_tree(tree, *args)
    assert proc.returncode == 2, why + ": " + proc.stdout + proc.stderr
    assert proc.stdout == "", why
    assert "usage:" in proc.stderr, why
    assert not (tree / "x").exists(), why
    assert snapshot(tree) == before


def test_dev_only():
    """AC-4.5: `is_shippable_script gen-platform-trees.py` returns non-zero in
    install.sh, update.sh, and unlink.sh, whose function bodies are
    byte-identical; the control `spec-status.py` stays shippable."""
    bodies = {script: ship_filter(script) for script in ("install.sh", "update.sh", "unlink.sh")}
    assert len(set(bodies.values())) == 1, "is_shippable_script bodies differ"
    for script, body in bodies.items():
        assert "gen-platform-trees.py" in body, script
        assert not is_shippable(body, "gen-platform-trees.py"), script
        assert is_shippable(body, "spec-status.py"), script


@pytest.mark.parametrize("target", [None, "claude-code"], ids=["all", "claude-code"])
def test_write_blocked_by_stray_agent(tmp_path, target):
    """Write mode, and the claude-code identity target, fail on a stray
    claude-code/agents/*.md outside the `writ-*.md` glob with `orphan
    claude-code/agents/<name>`, exit 1, nothing written: a write would
    otherwise list the stray in claude-code/CLAUDE.md and `--check` would
    then pass on a file install.sh ships. `--target cursor` does not read
    that directory and still writes."""
    tree = tmp_tree(tmp_path)
    add_stray_claude_agent(tree)
    before = snapshot(tree)
    proc = run_tree(tree, *(("--target", target) if target else ()))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert proc.stdout.splitlines() == [
        "fail", "reason: orphan claude-code/agents/helper.md",
        "gen-platform-trees: fail (0 written, 1 reasons)"]
    assert snapshot(tree) == before
    proc = run_tree(tree, "--target", "cursor")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert wrote_lines(proc) == ["wrote cursor/writ.mdc"]


def test_write_blocked_by_vendor(tmp_path):
    """Write mode runs the vendor scan among its pre-checks: a vendor token
    in a command fails the run with `vendor <name> in commands/<f>.md:<line>`,
    exit 1, and nothing is written."""
    tree = tmp_tree(tmp_path)
    line = append_token(tree / "commands" / "status.md")
    before = snapshot(tree)
    proc = run_tree(tree)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert proc.stdout.splitlines() == [
        "fail", "reason: vendor TodoWrite in commands/status.md:%d" % line,
        "gen-platform-trees: fail (0 written, 1 reasons)"]
    assert snapshot(tree) == before
