#!/usr/bin/env python3
"""Tests for scripts/gen-platform-trees.py, Story 1 of `2026-10-22-generated-platform-trees`.

Story 1 ships the adapter tool-table parser (`parse_adapter`), the
vocabulary rule (`vocabulary`, `unmapped`), and the repairs the golden
neutral set depends on: a `file_search` row in the Codex table, the OpenClaw
`readonly: true` row folded into `Task`, a `Plan Mode` row in all four
tables, one sentence in three command files, and the Plan Mode issue's
resolution. Stories 2 to 4 add the generators and the CLI on top of this
module; the `main()` stub here only prints `unverifiable`.

The module name has a hyphen, so the tests import it by path, the way
test_gen_claude_md.py does. Fixture adapters live under
scripts/tests/fixtures/platform-trees/<case>/<adapter>.md and carry the real
adapter headings, so `parse_adapter` selects the grammar by basename and the
reason strings name `adapters/<basename>`. Nothing here writes to the repo.

Covers AC-1.1, AC-1.2, AC-1.3, AC-1.4, and AC-1.5.

Run: uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import List

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
    """Story 1 CLI stub: `--help` exits 0 and names the modes Stories 2 to 4 add."""
    proc = run_cli("--help")
    assert proc.returncode == 0, proc.stderr
    assert "usage" in proc.stdout.lower()
    for word in ("--check", "--target", "--out-dir", "coverage"):
        assert word in proc.stdout


@pytest.mark.parametrize(
    "args, mode", [((), "write"), (("--check",), "check"), (("coverage",), "coverage")],
    ids=["write", "check", "coverage"])
def test_cli_stub(args, mode):
    """Story 1 CLI stub: every mode prints the check shape with
    `unverifiable`, one `reason: not-implemented <mode>` line, and the
    summary, exit 0, and writes nothing."""
    proc = run_cli(*args)
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[0] == "unverifiable"
    assert lines[1] == "reason: not-implemented %s" % mode
    assert lines[-1] == "gen-platform-trees: unverifiable (story 1: parser only)"
    assert len(lines) == 3
