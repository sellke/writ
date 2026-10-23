#!/usr/bin/env python3
"""Static checks for spec `2026-10-22-plugin-distribution`.

Verification Record (Story 1):

- The table under `## Verification Record` in the spec's technical-spec.md has
  the five record columns, at least one data row, a Status per row in the
  anchored grammar written under that heading, and a Source per row that
  starts with `https://`.
- Each row's Claim starts with a unique `V<nn>` ID, and every ID cited on a
  decision's `Rests on:` line names a row whose Status is `verified`.

The record is read with the table grammar of `scripts/gen-platform-trees.py`
(`section`, `first_table`, `cells`), loaded by path, so a change to that
grammar shows up here. Stories 2, 3, and 5 extend the same import.

Claude Code plugin (Story 2), layout B (technical-spec.md -> Candidate
Layouts -> Decision): the `claude-code-plugin` target of
`scripts/gen-platform-trees.py` writes `.claude-plugin/marketplace.json` at
the repository root and the plugin under `plugins/writ/`. Every tree test
renders into a temp directory from a temp copy of the sources
(`copy_sources`); nothing here writes to the repository.

- TestPluginManifest: plugin.json keys, `version` equal to VERSION, the
  `commands` list without `_preamble.md` (V02, V11), the `agents` list of the
  eight generated agents (V03, V23), deterministic bytes.
- TestMarketplace: `name`, `owner.name`, one entry `writ` whose source is
  `./plugins/writ` (V24, V25).
- TestTokenClasses: the rewrite on a fixture text written independently of
  the generator; YAML frontmatter untouched (V07); idempotent.
- TestPluginTree: the generated-tree scan: no bare shipped-script call or
  path, every command cross-reference namespaced, no un-namespaced agent
  spawn, every `${CLAUDE_PLUGIN_ROOT}/` path resolves, dev-only calls and
  `.writ/docs/` references unchanged, and only inventory forms differ from
  the source.
- TestShippableSet: the generator's `is_shippable_script` agrees with the
  bash function in install.sh on every file in scripts/, and the plugin's
  scripts/ holds exactly that set.
- TestCarrier: `output-styles/writ.md` frontmatter and body equality with
  system-instructions.md.
- TestPluginCheck: `--check` names each stale, missing, or orphan plugin file,
  fails on a system-instructions.md or carrier edit, and a write repairs.
- TestPluginValidate: `claude plugin validate` exits 0 on the plugin and the
  marketplace root; skip with reason `no claude CLI` when the CLI is absent.
- TestAdapterPluginSection: `adapters/claude-code.md` -> Installation ->
  Plugin.

- TestStory1Record: Story 1's live rows, Cursor rows, UAT protocol, and
  path inventory (AC-1.2, AC-1.3, AC-1.4).

Covers AC-1.1 to AC-1.5 and AC-2.1 to AC-2.5.

Run: uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Set, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "gen-platform-trees.py"
TECH_SPEC = (REPO_ROOT / ".writ" / "specs" / "2026-10-22-plugin-distribution"
             / "sub-specs" / "technical-spec.md")

RECORD_HEADING = "## Verification Record"
RECORD_COLUMNS = ["Claim", "Platform & version", "Observed", "Source", "Status"]
# technical-spec.md -> Verification Record. Anchored at both ends: a version or
# a reason outside the two parentheticals fails.
STATUS_GRAMMAR = re.compile(
    r"^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$"
)
ROW_ID = re.compile(r"^(V\d{2,})\b")
CITED_ID = re.compile(r"\bV\d{2,}\b")


def load_module():
    spec = importlib.util.spec_from_file_location("gen_platform_trees", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def gen():
    return load_module()


def spec_text() -> str:
    return TECH_SPEC.read_text(encoding="utf-8")


def record_rows(gen) -> List[List[str]]:
    """Cells of each data row in the first table under `## Verification Record`,
    after asserting the header is the five record columns."""
    lines = spec_text().splitlines()
    span, missing = gen.section(lines, (RECORD_HEADING,))
    assert span is not None, "technical-spec.md has no %r heading" % missing
    table = gen.first_table(lines, *span)
    assert table, "no table under %r" % RECORD_HEADING
    header = gen.cells(table[0][1])
    assert header == RECORD_COLUMNS, "record columns are %s" % header
    rows = [gen.cells(text) for _, text in table[2:]]
    assert rows, "the Verification Record has no data row"
    return rows


def status_by_id(gen) -> Dict[str, str]:
    statuses = {}  # type: Dict[str, str]
    for row in record_rows(gen):
        match = ROW_ID.match(row[0])
        assert match, "Claim cell has no V<nn> ID: %r" % row[0]
        assert match.group(1) not in statuses, "duplicate row ID %s" % match.group(1)
        statuses[match.group(1)] = row[4]
    return statuses


class TestVerificationRecord:
    def test_rows_have_five_cells(self, gen):
        for row in record_rows(gen):
            assert len(row) == len(RECORD_COLUMNS), "row has %d cells: %r" % (len(row), row)

    def test_status_matches_grammar(self, gen):
        for row in record_rows(gen):
            assert STATUS_GRAMMAR.match(row[4]), "Status %r fails the grammar (row %r)" % (
                row[4], row[0][:60])

    def test_source_is_https_url(self, gen):
        for row in record_rows(gen):
            assert row[3].startswith("https://"), "Source %r is not an https:// URL (row %r)" % (
                row[3], row[0][:60])

    def test_decisions_cite_only_verified_rows(self, gen):
        statuses = status_by_id(gen)
        rests_on = [line for line in spec_text().splitlines()
                    if line.lstrip("-* ").startswith("Rests on:")]
        assert rests_on, "no decision has a 'Rests on:' line"
        for line in rests_on:
            cited = CITED_ID.findall(line)
            assert cited, "'Rests on:' line cites no row: %r" % line
            for row_id in cited:
                assert row_id in statuses, "%s is not a Verification Record row" % row_id
                assert statuses[row_id].startswith("verified "), "%s is %r, not verified" % (
                    row_id, statuses[row_id])


LIVE_PLATFORM = "Claude Code 2.1.309"
CURSOR_LIVE_PLATFORM = "Cursor (no session in lane)"
PENDING_UAT = re.compile(r"^unverified \d{4}-\d{2}-\d{2} \(pending UAT\)$")
# AC-1.2's live checks, each named by a phrase its row's Claim carries.
LIVE_CHECKS = ("claude plugin validate", "marketplace add", "claude plugin install", "/writ:stub",
               "writ:writ-coder", "${CLAUDE_PLUGIN_ROOT}", "Prime Directive probe")
INVENTORY_COLUMNS = ["Form", "Example", "Count (grep)", "Reference kind",
                     "Resolves under plugin to", "Token class"]
AGENT_KEYS = ("permissionMode", "isolation", "memory", "maxTurns", "model", "tools", "disallowedTools")


def spec_section(gen, heading: str) -> List[str]:
    lines = spec_text().splitlines()
    span, missing = gen.section(lines, (heading,))
    assert span is not None, "technical-spec.md has no %r" % missing
    return lines[span[0]:span[1]]


class TestStory1Record:
    """Story 1's record, read as text: the live rows (AC-1.2), the Cursor
    rows and UAT protocol (AC-1.3), and the path inventory (AC-1.4)."""

    def test_live_rows_name_the_version_and_the_observation(self, gen):
        """AC-1.2: each live check has a row on the recorded Claude Code
        version; a verified row quotes a transcript line or an exit code, and
        a check that did not run is `unverified` with no guessed result."""
        live = [row for row in record_rows(gen) if row[1].startswith("Claude Code 2")]
        assert live, "no live Claude Code rows"
        for row in live:
            assert row[1] == LIVE_PLATFORM, row[0][:40]
            if row[4].startswith("verified "):
                assert any(mark in row[2] for mark in ("rc=", "\u00a7", "\u2192", '"')), row[0][:40]
            else:
                assert row[2].startswith("Not "), row[0][:40]
        for check in LIVE_CHECKS:
            assert any(check in row[0] for row in live), "no live row for %r" % check

    def test_cursor_live_rows_are_pending_uat(self, gen):
        """AC-1.3: every Cursor row that claims live behavior is
        `unverified <date> (pending UAT)`, the record says nothing was written
        to the local plugins folder, and § UAT Protocols lists the fields a
        maintainer records."""
        cursor = [row for row in record_rows(gen) if row[1] == CURSOR_LIVE_PLATFORM]
        assert cursor, "no Cursor live rows"
        for row in cursor:
            assert PENDING_UAT.match(row[4]), row[0][:40]
        assert any("nothing written to `~/.cursor/plugins/local/`" in row[2] for row in cursor)
        protocol = "\n".join(spec_section(gen, "## UAT Protocols (Story 3 and Story 5 write)"))
        for field in ("Cursor version:", "Rules list result", "Commands seen", "Script call result",
                      "Result: `pass` or `fail`", "cursor.com/marketplace/publish"):
            assert field in protocol, field

    def test_inventory_counts_and_classes(self, gen):
        """AC-1.4: each path form has a grep count, a reference kind, and a
        token class (or none), the 22 grep commands are recorded, and each
        generated-agent frontmatter key is marked with its record row."""
        lines = spec_section(gen, "## Relative Path Inventory")
        table = gen.first_table(lines, 0, len(lines))
        assert gen.cells(table[0][1]) == INVENTORY_COLUMNS
        rows = [gen.cells(text) for _, text in table[2:]]
        assert len(rows) >= 10
        for row in rows:
            assert re.search(r"\d", row[2]), row[0]
            assert row[3] and row[5], row[0]
        block = "\n".join(lines)
        for n in range(1, 23):
            assert re.search(r"# G%d\s+\d+" % n, block), "G%d" % n
        for key in AGENT_KEYS:
            assert re.search(r"^- `%s` \(\d+( of \d+)?\): `(survives|ignored|unverified)` \(V\d+" % key,
                             block, re.M), key


# ---------------------------------------------------------------------------
# Story 2: the Claude Code plugin
# ---------------------------------------------------------------------------

TARGET = "claude-code-plugin"
PLUGIN_REL = "plugins/writ"
MARKETPLACE_REL = ".claude-plugin/marketplace.json"
MANIFEST_REL = PLUGIN_REL + "/.claude-plugin/plugin.json"
CARRIER_REL = PLUGIN_REL + "/output-styles/writ.md"
ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"
DRIVER = "scripts/gen-platform-trees.py"
# What the driver reads and writes, as test_gen_platform_trees.py's tmp_tree
# copies it, plus VERSION (the manifest version) and every top-level file in
# scripts/ (the plugin's script copy reads them).
TREE_DIRS = ("adapters", "agents", "commands", "skills", "cursor", "claude-code", "codex")
TREE_FILES = ("system-instructions.md", ".writ/manifest.yaml", "VERSION")
# The generated-file comment (gen-platform-trees.py COMMENT), as a literal.
COMMENT = ("<!-- generated by scripts/gen-platform-trees.py from %s — "
           "do not hand-edit; regenerate -->\n")
COMMENT_PREFIX = "<!-- generated by scripts/gen-platform-trees.py from "
CHECK_SUMMARY = "gen-platform-trees: %s (%d stale, %d missing, %d orphan, %d unmapped, %d vendor)"
CLEAN_SUMMARY = CHECK_SUMMARY % ("pass", 0, 0, 0, 0, 0)
MANIFEST_KEYS = ["name", "version", "description", "author", "repository", "license",
                 "commands", "agents"]
CLAUDE_AGENT_NAMES = ("architect", "coder", "documenter", "evaluator", "reviewer",
                      "story-gen", "tester", "visual-qa")


def copy_sources(dest: Path) -> Path:
    """A copy of the driver's inputs and the identity targets' generated
    files: every top-level file in scripts/, TREE_DIRS, TREE_FILES. No
    plugin tree; a test renders its own."""
    (dest / "scripts").mkdir(parents=True)
    for path in (REPO_ROOT / "scripts").iterdir():
        if path.is_file():
            shutil.copy2(path, dest / "scripts" / path.name)
    for name in TREE_DIRS:
        shutil.copytree(REPO_ROOT / name, dest / name)
    for rel in TREE_FILES:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, dest / rel)
    return dest


def run(tree: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(tree / DRIVER)] + list(args),
                          cwd=str(tree), capture_output=True, text=True)


class Rendered(NamedTuple):
    src: Path      # the source copy
    out: Path      # the --out-dir: holds .claude-plugin/ and plugins/writ/
    plugin: Path   # out/plugins/writ


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> Rendered:
    """`--target claude-code-plugin --out-dir <out>` on a source copy."""
    base = tmp_path_factory.mktemp("plugin")
    src = copy_sources(base / "src")
    out = base / "out"
    proc = run(src, "--target", TARGET, "--out-dir", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return Rendered(src, out, out / PLUGIN_REL)


@pytest.fixture
def built(tmp_path) -> Path:
    """A source copy with the plugin written in place by the target."""
    tree = copy_sources(tmp_path / "tree")
    proc = run(tree, "--target", TARGET)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return tree


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def split_frontmatter(text: str) -> Tuple[str, str]:
    """(frontmatter with both `---` lines, body); ("", text) without one."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[:end + 5], text[end + 5:]
    return "", text


def command_names(root: Path) -> List[str]:
    return sorted(p.stem for p in (root / "commands").glob("*.md") if p.stem != "_preamble")


def ship_filter() -> str:
    """install.sh's `is_shippable_script` body, from `is_shippable_script() {`
    to the next line that is `}` (test_install_update_dev_scripts.sh's cut)."""
    lines = (REPO_ROOT / "scripts" / "install.sh").read_text(encoding="utf-8").splitlines(True)
    start = lines.index("is_shippable_script() {\n")
    end = next(i for i in range(start, len(lines)) if lines[i] == "}\n")
    return "".join(lines[start:end + 1])


def bash_shippable(names: List[str]) -> Set[str]:
    """The names the bash rule admits, from one bash run."""
    script = ship_filter() + '\nfor n in "$@"; do is_shippable_script "$n" && printf "%s\\n" "$n"; done\n'
    proc = subprocess.run(["bash", "-c", script, "_"] + names, capture_output=True, text=True)
    assert proc.returncode in (0, 1), proc.stderr
    return set(proc.stdout.split())


def source_shipped() -> Set[str]:
    files = [p.name for p in (REPO_ROOT / "scripts").iterdir() if p.is_file()]
    return bash_shippable(files)


def rewritten_files(plugin: Path) -> List[Path]:
    """The token-rewritten Markdown: commands, agents, skills."""
    return (sorted((plugin / "commands").glob("*.md")) + sorted((plugin / "agents").glob("*.md"))
            + sorted((plugin / "skills").glob("*/SKILL.md")))


def is_comment_line(line: str) -> bool:
    """A whole-line HTML comment, which the token classes leave alone."""
    text = line.strip()
    return text.startswith("<!--") and text.endswith("-->")


def without_comment_lines(body: str) -> str:
    return "".join(line for line in body.splitlines(True) if not is_comment_line(line))


def scanned_body(path: Path) -> str:
    """The body after the frontmatter, without its HTML comment lines: the
    generated-file comment names the source path in the Writ repository on
    purpose, and the inherited gen-claude-agents header keeps its paths."""
    _, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return without_comment_lines(body)


def source_bodies(root: Path) -> List[str]:
    """The bodies the plugin's rewritten files come from: commands, the
    prompt-template docs, the generated Claude agents, and skills."""
    paths = (sorted((root / "commands").glob("*.md")) + sorted((root / "agents").glob("*.md"))
             + sorted((root / "claude-code" / "agents").glob("writ-*.md"))
             + sorted((root / "skills").glob("*/SKILL.md")))
    return [split_frontmatter(p.read_text(encoding="utf-8"))[1] for p in paths]


def files_under(root: Path) -> List[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def snapshot(tree: Path) -> Dict[str, bytes]:
    return {p.relative_to(tree).as_posix(): p.read_bytes()
            for p in sorted(tree.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def check_reasons(proc: subprocess.CompletedProcess) -> List[str]:
    return [l[len("reason: "):] for l in proc.stdout.splitlines() if l.startswith("reason: ")]


# -- AC-2.1: the manifest and the marketplace ------------------------------


class TestPluginManifest:
    def test_required_keys(self, rendered):
        """AC-2.1: `name` writ, a `description`, an `author` with a name, MIT."""
        manifest = load_json(rendered.out / MANIFEST_REL)
        assert manifest["name"] == "writ"
        assert manifest["description"].strip()
        assert manifest["author"]["name"].strip()
        assert manifest["license"] == "MIT"
        assert manifest["repository"] == "https://github.com/sellke/writ"

    def test_version_is_the_version_file(self, rendered):
        """AC-2.1: `version` is read from VERSION at generation time."""
        manifest = load_json(rendered.out / MANIFEST_REL)
        assert manifest["version"] == (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    def test_commands_list_every_command_but_the_preamble(self, rendered):
        """V02, V11: the `commands` key replaces the default scan, so listing
        every command but `_preamble.md` keeps `/writ:_preamble` from
        registering while the preamble file still ships."""
        manifest = load_json(rendered.out / MANIFEST_REL)
        assert manifest["commands"] == ["./commands/%s.md" % n for n in command_names(REPO_ROOT)]
        assert len(manifest["commands"]) == len(list((REPO_ROOT / "commands").glob("*.md"))) - 1
        for rel in manifest["commands"]:
            assert (rendered.plugin / rel).is_file(), rel
        assert (rendered.plugin / "commands" / "_preamble.md").is_file()

    def test_agents_list_the_generated_claude_agents(self, rendered):
        """V03, V23: `agents` lists the eight generated agents, so the
        prompt-template docs beside them never load as agents."""
        manifest = load_json(rendered.out / MANIFEST_REL)
        expected = ["./agents/%s" % p.name
                    for p in sorted((REPO_ROOT / "claude-code" / "agents").glob("writ-*.md"))]
        assert len(expected) == len(CLAUDE_AGENT_NAMES)
        assert manifest["agents"] == expected
        for rel in manifest["agents"]:
            fm, _ = split_frontmatter((rendered.plugin / rel).read_text(encoding="utf-8"))
            assert "\nname: %s\n" % Path(rel).stem in fm, rel
        for doc in sorted((REPO_ROOT / "agents").glob("*.md")):
            assert "./agents/%s" % doc.name not in manifest["agents"], doc.name
            assert (rendered.plugin / "agents" / doc.name).is_file(), doc.name

    def test_json_is_deterministic(self, rendered, tmp_path):
        """Fixed key order, two-space indent, one trailing newline, and a
        second render produces the same bytes for every file."""
        raw = (rendered.out / MANIFEST_REL).read_text(encoding="utf-8")
        assert list(json.loads(raw)) == MANIFEST_KEYS
        assert raw == json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n"
        again = tmp_path / "again"
        proc = run(rendered.src, "--target", TARGET, "--out-dir", str(again))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert snapshot(again) == snapshot(rendered.out)


class TestMarketplace:
    def test_shape(self, rendered):
        """AC-2.1, V24, V25: `name`, `owner.name`, one plugin entry `writ`
        whose source is the relative path the record verified."""
        data = load_json(rendered.out / MARKETPLACE_REL)
        assert data["name"] == "writ"
        assert data["owner"]["name"].strip()
        assert [entry["name"] for entry in data["plugins"]] == ["writ"]
        assert data["plugins"][0]["source"] == "./" + PLUGIN_REL
        assert data["plugins"][0]["description"].strip()
        assert (rendered.out / data["plugins"][0]["source"] / ".claude-plugin" / "plugin.json").is_file()

    def test_committed_files_exist(self):
        """The repository root carries the marketplace and the plugin
        manifest, so `--check` always has the plugin tree to compare."""
        assert (REPO_ROOT / MARKETPLACE_REL).is_file()
        assert (REPO_ROOT / MANIFEST_REL).is_file()
        assert not (REPO_ROOT / ".claude-plugin" / "plugin.json").exists(), \
            "layout B: no plugin manifest at the repository root"


# -- AC-2.2: token classes --------------------------------------------------

# One line per inventory form (technical-spec.md -> Relative Path Inventory),
# plus the forms that must stay: dev-only and unknown scripts, a prose
# `scripts/` mention, directory-prefixed install paths, bare
# `system-instructions.md` mentions (instructions-path rewrites the Markdown
# link only; Story 2 review, 2026-10-23), a whole-line HTML comment, an
# already namespaced command, a refspec, a URL, a longer word, project docs,
# and a command file path.
TOKEN_TEXT = (
    "Run `python3 scripts/spec-status.py --x` and `bash scripts/lint-skill.sh`.\n"
    "Then `scripts/phase-state.py init`; see [`scripts/lint-skill.sh`](../scripts/lint-skill.sh).\n"
    "Dev-only stays: `bash scripts/eval.sh`, `scripts/install.sh`, `scripts/nope.py`.\n"
    "Data: `scripts/jev-thresholds.json`. Prose: see scripts/ for details.\n"
    "Read `agents/coding-agent.md`; installed: `.claude/agents/writ-coder.md`, "
    "`claude-code/agents/writ-coder.md`.\n"
    "Read `skills/tdd-cycle/SKILL.md` and [tdd](../skills/tdd-cycle/SKILL.md); "
    "Codex: `.agents/skills/tdd-cycle/SKILL.md`.\n"
    "Preamble: [`commands/_preamble.md`](../commands/_preamble.md), [`_preamble.md`](_preamble.md).\n"
    "Identity: [`system-instructions.md`](../system-instructions.md); "
    "installed: `.claude/system-instructions.md`, `$WRIT_SRC/system-instructions.md`.\n"
    "Bare mentions name installed files: `system-instructions.md` and system-instructions.md; "
    "[rules](system-instructions.md).\n"
    "<!-- Regenerate: python3 scripts/spec-status.py; see agents/coding-agent.md and /create-spec -->\n"
    "Next `/create-spec`, then /implement-story. Run /ship. Or `/writ-design`.\n"
    "Kept: `/writ:writ`, refspec `refs/notes/writ:*`, path `.claude/commands/status.md`, "
    "url https://x.dev/review, `/statusline`.\n"
    "Docs: `.writ/docs/app-verification.md`; other command: `commands/status.md`.\n"
)
TOKEN_EXPECTED = (
    "Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spec-status.py --x` and "
    "`bash ${CLAUDE_PLUGIN_ROOT}/scripts/lint-skill.sh`.\n"
    "Then `${CLAUDE_PLUGIN_ROOT}/scripts/phase-state.py init`; see "
    "[`${CLAUDE_PLUGIN_ROOT}/scripts/lint-skill.sh`](${CLAUDE_PLUGIN_ROOT}/scripts/lint-skill.sh).\n"
    "Dev-only stays: `bash scripts/eval.sh`, `scripts/install.sh`, `scripts/nope.py`.\n"
    "Data: `${CLAUDE_PLUGIN_ROOT}/scripts/jev-thresholds.json`. Prose: see scripts/ for details.\n"
    "Read `${CLAUDE_PLUGIN_ROOT}/agents/coding-agent.md`; installed: "
    "`.claude/agents/writ-coder.md`, `claude-code/agents/writ-coder.md`.\n"
    "Read `${CLAUDE_PLUGIN_ROOT}/skills/tdd-cycle/SKILL.md` and "
    "[tdd](${CLAUDE_PLUGIN_ROOT}/skills/tdd-cycle/SKILL.md); "
    "Codex: `.agents/skills/tdd-cycle/SKILL.md`.\n"
    "Preamble: [`${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md`](${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md), "
    "[`${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md`](${CLAUDE_PLUGIN_ROOT}/commands/_preamble.md).\n"
    "Identity: [`${CLAUDE_PLUGIN_ROOT}/system-instructions.md`](${CLAUDE_PLUGIN_ROOT}/system-instructions.md); "
    "installed: `.claude/system-instructions.md`, `$WRIT_SRC/system-instructions.md`.\n"
    "Bare mentions name installed files: `system-instructions.md` and system-instructions.md; "
    "[rules](${CLAUDE_PLUGIN_ROOT}/system-instructions.md).\n"
    "<!-- Regenerate: python3 scripts/spec-status.py; see agents/coding-agent.md and /create-spec -->\n"
    "Next `/writ:create-spec`, then /writ:implement-story. Run /writ:ship. Or `/writ:writ-design`.\n"
    "Kept: `/writ:writ`, refspec `refs/notes/writ:*`, path `.claude/commands/status.md`, "
    "url https://x.dev/review, `/statusline`.\n"
    "Docs: `.writ/docs/app-verification.md`; other command: `commands/status.md`.\n"
)


def fixture_names(gen):
    return gen.PluginNames(
        scripts=frozenset({"spec-status.py", "lint-skill.sh", "phase-state.py", "jev-thresholds.json"}),
        agents=frozenset({"coding-agent.md"}),
        skills=frozenset({"tdd-cycle"}),
        commands=frozenset({"create-spec", "implement-story", "ship", "status", "review",
                            "writ", "writ-design"}),
    )


class TestTokenClasses:
    def test_fixture_rewrite(self, gen):
        """AC-2.2: script-root, script-path, agent-path, skill-path,
        preamble-path, instructions-path, and command-ref rewrite their
        inventory forms; every other byte stays."""
        assert gen.rewrite_plugin_body(TOKEN_TEXT, fixture_names(gen)) == TOKEN_EXPECTED

    def test_rewrite_is_idempotent(self, gen):
        """A second pass changes nothing, on the fixture and on every source
        body, so no class rewrites another class's output."""
        names = fixture_names(gen)
        assert gen.rewrite_plugin_body(TOKEN_EXPECTED, names) == TOKEN_EXPECTED
        real = gen.plugin_names(REPO_ROOT)
        for body in source_bodies(REPO_ROOT):
            once = gen.rewrite_plugin_body(body, real)
            assert gen.rewrite_plugin_body(once, real) == once

    def test_frontmatter_is_untouched(self, gen):
        """V07: `${CLAUDE_PLUGIN_ROOT}` is substituted in bodies only, so the
        YAML frontmatter keeps its paths and command names; the
        generated-file comment follows the frontmatter."""
        fm = ("---\nname: x\nref: agents/coding-agent.md\n"
              "description: run /create-spec and scripts/spec-status.py\n---\n")
        out = gen.render_plugin_markdown(fm + "\nRun /create-spec.\n", fixture_names(gen), "commands/x.md")
        assert out == fm + COMMENT % "commands/x.md" + "\nRun /writ:create-spec.\n"

    def test_comment_leads_a_file_without_frontmatter(self, gen):
        out = gen.render_plugin_markdown("# Doc\n\nRead `agents/coding-agent.md`.\n",
                                         fixture_names(gen), "agents/coding-agent.md")
        assert out == (COMMENT % "agents/coding-agent.md"
                       + "# Doc\n\nRead `${CLAUDE_PLUGIN_ROOT}/agents/coding-agent.md`.\n")


# -- AC-2.2: the generated tree --------------------------------------------

BARE_CALL = re.compile(r"\b(?:python3|bash) scripts/([a-z0-9_-]+\.(?:py|sh))")
BARE_SCRIPT = re.compile(r"(?<![A-Za-z0-9_./-])(?:\.\./)?scripts/([a-z0-9_-]+\.(?:py|sh|json))")
BARE_AGENT = re.compile(r"(?<![A-Za-z0-9_./-])(?:\.\./)?agents/([a-z0-9-]+\.md)")
# technical-spec.md -> Relative Path Inventory G8, minus file names.
AGENT_SPAWN = re.compile(r"(?:^|[^a-z0-9_:/.-])writ-(%s)\b(?!\.md)" % "|".join(CLAUDE_AGENT_NAMES))
PLUGIN_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")
NAMESPACED = re.compile(r"(?<![A-Za-z0-9_./-])/writ:([a-z][a-z0-9-]*)")
RELATIVE_LINK = re.compile(
    r"\]\((?:\.\./(?:scripts|agents|skills|commands)/|\.\./system-instructions\.md|_preamble\.md)")
PROJECT_DOC = re.compile(r"\.writ/docs/[a-z0-9_.-]+")


def unnamespaced_command(names: List[str]) -> re.Pattern:
    """Inventory G19 (`(^|[^A-Za-z0-9_./-])/(<cmd>)\\b`), names longest first,
    minus a name followed by `-` (a longer word) or `:` (namespaced)."""
    alternation = "|".join(sorted(names, key=len, reverse=True))
    return re.compile(r"(?:^|[^A-Za-z0-9_./-])/(%s)\b(?![-:])" % alternation, re.M)


def normalize(text: str) -> str:
    """Undo the inventory rewrites: the plugin root prefix and the command
    namespace go, and the relative and preamble forms take one spelling."""
    text = text.replace(ROOT_VAR + "/", "").replace("/writ:", "/")
    for rel in ("scripts/", "agents/", "skills/", "commands/_preamble.md", "system-instructions.md"):
        text = text.replace("../" + rel, rel)
    text = text.replace("(_preamble.md)", "(commands/_preamble.md)")
    return text.replace("`_preamble.md`", "`commands/_preamble.md`")


class TestPluginTree:
    def test_tree_holds_exactly_the_components(self, rendered):
        """Layout B: commands, agents, skills, the shipped scripts, the
        system instructions, the carrier, and the manifest; no
        `settings.json` (carrier 1 not taken), no plugin-root CLAUDE.md
        (V37), no `bin/` (V10), no symlink (V32, V33, V34)."""
        commands = ["commands/%s" % p.name for p in (REPO_ROOT / "commands").glob("*.md")]
        agents = (["agents/%s" % p.name for p in (REPO_ROOT / "agents").glob("*.md")]
                  + ["agents/%s" % p.name for p in (REPO_ROOT / "claude-code" / "agents").glob("writ-*.md")])
        skills = ["skills/%s/SKILL.md" % p.parent.name for p in (REPO_ROOT / "skills").glob("*/SKILL.md")]
        scripts = ["scripts/%s" % n for n in source_shipped()]
        expected = commands + agents + skills + scripts + [
            ".claude-plugin/plugin.json", "system-instructions.md", "output-styles/writ.md"]
        assert files_under(rendered.plugin) == sorted(expected)
        assert not any(p.is_symlink() for p in rendered.plugin.rglob("*"))
        assert files_under(rendered.out / ".claude-plugin") == ["marketplace.json"]

    def test_no_bare_shipped_script_call(self, rendered):
        """AC-2.2: no `python3 scripts/<shipped>` or `bash scripts/<shipped>`."""
        shipped = source_shipped()
        hits = ["%s: %s" % (p.relative_to(rendered.plugin), m.group(0))
                for p in rewritten_files(rendered.plugin)
                for m in BARE_CALL.finditer(scanned_body(p)) if m.group(1) in shipped]
        assert hits == []

    def test_no_bare_shipped_script_path(self, rendered):
        """AC-2.2: every shipped-script reference reads
        `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`, link targets included."""
        shipped = source_shipped()
        hits = ["%s: %s" % (p.relative_to(rendered.plugin), m.group(0))
                for p in rewritten_files(rendered.plugin)
                for m in BARE_SCRIPT.finditer(scanned_body(p)) if m.group(1) in shipped]
        assert hits == []

    def test_dev_only_calls_are_unchanged(self, rendered):
        """Spec Rule 3: dev-only script names keep their bare form (the four
        `bash scripts/eval.sh` lines, inventory G2), in the same number."""
        shipped = source_shipped()

        def dev_calls(bodies: List[str]) -> List[str]:
            return sorted(m.group(0) for body in bodies for m in BARE_CALL.finditer(body)
                          if m.group(1) not in shipped)

        expected = dev_calls(source_bodies(REPO_ROOT))
        assert expected, "the source has dev-only script calls (inventory G2)"
        assert dev_calls([scanned_body(p) for p in rewritten_files(rendered.plugin)]) == expected

    def test_command_refs_are_namespaced(self, rendered):
        """AC-2.2, V11: every command cross-reference reads `/writ:<command>`,
        and every `/writ:<name>` names a plugin command."""
        names = command_names(REPO_ROOT)
        pattern = unnamespaced_command(names)
        hits = []  # type: List[str]
        for p in rewritten_files(rendered.plugin):
            body = scanned_body(p)
            hits += ["%s: /%s" % (p.relative_to(rendered.plugin), m.group(1)) for m in pattern.finditer(body)]
            for m in NAMESPACED.finditer(body):
                assert m.group(1) in names, "%s: /writ:%s is not a command" % (p.name, m.group(1))
        assert hits == []

    def test_no_unnamespaced_agent_spawn(self, rendered):
        """AC-2.2, V13, V62: no Claude agent is named without `writ:`
        (file names such as `writ-coder.md` are paths, not spawns)."""
        hits = ["%s: %s" % (p.relative_to(rendered.plugin), m.group(0).strip())
                for p in rewritten_files(rendered.plugin)
                for m in AGENT_SPAWN.finditer(scanned_body(p))]
        assert hits == []

    def test_plugin_root_paths_resolve(self, rendered):
        """Every `${CLAUDE_PLUGIN_ROOT}/<path>` names a file in the plugin,
        and no bare `agents/<x>.md` reference is left in a body."""
        seen = 0
        for p in rewritten_files(rendered.plugin):
            body = scanned_body(p)
            for m in PLUGIN_PATH.finditer(body):
                rel = m.group(1).rstrip(".")
                seen += 1
                assert (rendered.plugin / rel).is_file(), "%s: %s" % (p.relative_to(rendered.plugin), rel)
            assert [m.group(0) for m in BARE_AGENT.finditer(body)] == [], p.name
            assert RELATIVE_LINK.findall(body) == [], p.name
        assert seen

    def test_project_docs_are_unchanged(self, rendered):
        """Inventory class none: `.writ/docs/<x>` stays a project path."""
        def docs(bodies: List[str]) -> List[str]:
            return sorted(m.group(0) for body in bodies for m in PROJECT_DOC.finditer(body))

        expected = docs(source_bodies(REPO_ROOT))
        assert expected
        assert docs([scanned_body(p) for p in rewritten_files(rendered.plugin)]) == expected
        assert not (rendered.plugin / ".writ").exists()

    def test_only_inventory_forms_change(self, gen, rendered):
        """Story risk "a token class that rewrites prose": each file's
        frontmatter is byte-equal to its source's, and its body, with the
        inventory rewrites undone, equals the source body. The Claude agents'
        source is gen-claude-agents' render, which the committed
        claude-code/agents/ files equal."""
        sources = {}  # type: Dict[str, Path]
        for folder, pattern in (("commands", "*.md"), ("agents", "*.md"), ("skills", "*/SKILL.md")):
            for p in (REPO_ROOT / folder).glob(pattern):
                sources[p.relative_to(REPO_ROOT).as_posix()] = p
        for p in (REPO_ROOT / "claude-code" / "agents").glob("writ-*.md"):
            sources["agents/" + p.name] = p
        for path in rewritten_files(rendered.plugin):
            rel = path.relative_to(rendered.plugin).as_posix()
            src_fm, src_body = split_frontmatter(sources[rel].read_text(encoding="utf-8"))
            fm, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            assert fm == src_fm, rel
            assert normalize(scanned_body(path)) == normalize(without_comment_lines(src_body)), rel
        assert len(rewritten_files(rendered.plugin)) == len(sources)

    def test_instructions_path_rewrites_links_only(self, rendered):
        """instructions-path (inventory row, Story 2 review 2026-10-23): a
        Markdown link to system-instructions.md, target and link text, reads
        the plugin path; every bare mention outside such a link stays, because
        it names an installed or project file."""
        link = re.compile(r"\[[^\]\n]*\]\([^)\s]*system-instructions\.md\)")

        def outside_links(bodies: List[str]) -> str:
            return "\n".join(link.sub("", body) for body in bodies)

        rendered_bodies = [scanned_body(p) for p in rewritten_files(rendered.plugin)]
        source = outside_links([without_comment_lines(b) for b in source_bodies(REPO_ROOT)])
        bare = outside_links(rendered_bodies)
        assert source.count("system-instructions.md") >= 10, "the source has bare mentions"
        assert bare.count("system-instructions.md") == source.count("system-instructions.md")
        assert ROOT_VAR + "/system-instructions.md" not in bare
        links = [m.group(0) for body in rendered_bodies for m in link.finditer(body)]
        assert links and all(m.endswith("(%s/system-instructions.md)" % ROOT_VAR) for m in links)

    def test_comment_lines_are_not_rewritten(self, rendered):
        """Token classes skip whole-line HTML comments: the gen-claude-agents
        header in each plugin agent keeps `python3 scripts/gen-claude-agents.py`,
        which regenerates the Writ repository, not the plugin."""
        for source in sorted((REPO_ROOT / "claude-code" / "agents").glob("writ-*.md")):
            want = [l for l in source.read_text(encoding="utf-8").splitlines() if is_comment_line(l)]
            assert want, source.name
            got = [l for l in (rendered.plugin / "agents" / source.name).read_text(encoding="utf-8").splitlines()
                   if is_comment_line(l) and not l.startswith(COMMENT_PREFIX)]
            assert got == want, source.name
            assert ROOT_VAR not in "\n".join(got)

    def test_every_markdown_file_carries_the_comment(self, rendered):
        """Lane rule: each generated Markdown file names its source after its
        frontmatter (the carrier carries it as a YAML comment instead)."""
        for path in rewritten_files(rendered.plugin) + [rendered.plugin / "system-instructions.md"]:
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
            assert body.startswith(COMMENT_PREFIX), path.relative_to(rendered.plugin)


# -- AC-2.2: the shipped set -----------------------------------------------


class TestShippableSet:
    def test_python_rule_matches_bash(self, gen):
        """Task 2.3: the generator's rule and install.sh's agree on every
        file in scripts/ and on controls for each denylist branch."""
        names = sorted(p.name for p in (REPO_ROOT / "scripts").iterdir() if p.is_file())
        controls = ["eval.sh", "eval-x.py", "_x.py", "sweep-x.py", "gen-platform-trees.py",
                    "writ-runtime-readme.md", "spec-status.py", "x.sh", "jev-thresholds.json",
                    "other.json", "notes.md", "tests"]
        for group in (names, controls):
            bash = bash_shippable(group)
            assert {n for n in group if gen.is_shippable_script(n)} == bash, group
        assert "spec-status.py" in bash_shippable(names)

    def test_plugin_scripts_are_the_shipped_set(self, rendered):
        """Spec Rule 3: the plugin's scripts/ holds exactly the files the
        bash rule admits, as byte copies, and no directory (no tests/)."""
        shipped = source_shipped()
        entries = list((rendered.plugin / "scripts").iterdir())
        assert all(p.is_file() for p in entries)
        assert sorted(p.name for p in entries) == sorted(shipped)
        for name in shipped:
            assert (rendered.plugin / "scripts" / name).read_bytes() == \
                (REPO_ROOT / "scripts" / name).read_bytes(), name
        assert "eval.sh" not in shipped and "gen-platform-trees.py" not in shipped


# -- AC-2.3: the Prime Directive carrier -----------------------------------


def frontmatter_fields(fm: str) -> Dict[str, str]:
    fields = {}  # type: Dict[str, str]
    for line in fm.splitlines()[1:-1]:
        if line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


class TestCarrier:
    def test_frontmatter(self, rendered):
        """Carrier 2 (technical-spec.md -> Prime Directive Carrier, V41 to
        V43): `name` writ, a description, both flags true; the generated
        note is a YAML comment so the body stays equal."""
        fm, _ = split_frontmatter((rendered.out / CARRIER_REL).read_text(encoding="utf-8"))
        fields = frontmatter_fields(fm)
        assert fields["name"] == "writ"
        assert fields["description"]
        assert fields["keep-coding-instructions"] == "true"
        assert fields["force-for-plugin"] == "true"
        assert sorted(fields) == ["description", "force-for-plugin", "keep-coding-instructions", "name"]
        comments = [l for l in fm.splitlines() if l.startswith("#")]
        assert comments == ["# generated by scripts/gen-platform-trees.py from system-instructions.md "
                            "— do not hand-edit; regenerate"]

    def test_body_equals_system_instructions(self, rendered):
        """AC-2.3: the carrier's body equals system-instructions.md's body
        (each after its own frontmatter)."""
        _, body = split_frontmatter((rendered.out / CARRIER_REL).read_text(encoding="utf-8"))
        _, source = split_frontmatter((REPO_ROOT / "system-instructions.md").read_text(encoding="utf-8"))
        assert body == source
        assert "## Prime Directive" in body

    def test_one_carrier(self, rendered):
        """Rule 5: one mechanism. Carrier 1's `settings.json` and main-thread
        agent are absent."""
        assert files_under(rendered.plugin / "output-styles") == ["writ.md"]
        assert not (rendered.plugin / "settings.json").exists()
        assert not (rendered.plugin / "agents" / "writ.md").exists()


# -- AC-2.2, AC-2.3: --check and write --------------------------------------


def edit(rel: str):
    def mutate(tree: Path) -> None:
        with (tree / rel).open("a", encoding="utf-8") as handle:
            handle.write("\nhand edit\n")
    return mutate


def delete(rel: str):
    def mutate(tree: Path) -> None:
        (tree / rel).unlink()
    return mutate


def add(rel: str):
    def mutate(tree: Path) -> None:
        (tree / rel).write_text("# stray\n", encoding="utf-8")
    return mutate


def bump_version(tree: Path) -> None:
    (tree / "VERSION").write_text("99.0.0\n", encoding="utf-8")


# (id, mutation, the reason lines --check prints, the five counts)
CHECK_CASES = [
    ("stale-command", edit(PLUGIN_REL + "/commands/status.md"),
     ["stale plugins/writ/commands/status.md"], (1, 0, 0, 0, 0)),
    ("stale-script", edit(PLUGIN_REL + "/scripts/spec-status.py"),
     ["stale plugins/writ/scripts/spec-status.py"], (1, 0, 0, 0, 0)),
    ("stale-carrier", edit(CARRIER_REL), ["stale plugins/writ/output-styles/writ.md"], (1, 0, 0, 0, 0)),
    ("stale-marketplace", edit(MARKETPLACE_REL), ["stale .claude-plugin/marketplace.json"], (1, 0, 0, 0, 0)),
    ("version", bump_version, ["stale plugins/writ/.claude-plugin/plugin.json"], (1, 0, 0, 0, 0)),
    ("missing-skill", delete(PLUGIN_REL + "/skills/tdd-cycle/SKILL.md"),
     ["missing plugins/writ/skills/tdd-cycle/SKILL.md"], (0, 1, 0, 0, 0)),
    ("orphan-command", add(PLUGIN_REL + "/commands/zz-stray.md"),
     ["orphan plugins/writ/commands/zz-stray.md"], (0, 0, 1, 0, 0)),
    ("orphan-script", add(PLUGIN_REL + "/scripts/eval.sh"),
     ["orphan plugins/writ/scripts/eval.sh"], (0, 0, 1, 0, 0)),
]


class TestPluginCheck:
    def test_fresh_tree_passes(self, built):
        """A tree whose plugin was just written passes `--check`."""
        proc = run(built, "--check")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.splitlines() == ["pass", CLEAN_SUMMARY]

    @pytest.mark.parametrize("mutate, expected, counts", [(m, r, c) for _, m, r, c in CHECK_CASES],
                             ids=[i for i, _, _, _ in CHECK_CASES])
    def test_drift_is_a_reason(self, built, mutate, expected, counts):
        """AC-2.2: a plugin file that differs from a fresh render is `stale`,
        one that is gone is `missing`, one no render produces is `orphan`;
        exit 1, nothing written."""
        mutate(built)
        before = snapshot(built)
        proc = run(built, "--check")
        assert proc.returncode == 1, proc.stdout + proc.stderr
        lines = proc.stdout.splitlines()
        assert lines[0] == "fail"
        assert check_reasons(proc) == expected
        assert lines[-1] == CHECK_SUMMARY % (("fail",) + counts)
        assert snapshot(built) == before

    def test_system_instructions_edit_fails_check(self, built):
        """AC-2.3: editing system-instructions.md without regenerating makes
        the carrier, and the plugin's copy, stale."""
        path = built / "system-instructions.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nNew rule.\n", encoding="utf-8")
        proc = run(built, "--check")
        assert proc.returncode == 1, proc.stdout + proc.stderr
        reasons = check_reasons(proc)
        assert "stale plugins/writ/output-styles/writ.md" in reasons
        assert "stale plugins/writ/system-instructions.md" in reasons

    def test_source_command_edit_fails_check(self, built):
        """A source command edited without regenerating makes its plugin copy stale."""
        edit("commands/status.md")(built)
        proc = run(built, "--check")
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "stale plugins/writ/commands/status.md" in check_reasons(proc)

    def test_write_repairs_and_removes_orphans(self, built):
        """Write mode repairs every CHECK_CASES drift: it rewrites each
        rendered file, removes each orphan under plugins/writ/ with a
        `removed <path>` line, and `--check` passes afterwards."""
        for _, mutate, _, _ in CHECK_CASES:
            mutate(built)
        proc = run(built, "--target", TARGET)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        lines = proc.stdout.splitlines()
        assert lines[0] == "pass"
        removed = [l for l in lines if l.startswith("removed ")]
        assert removed == ["removed plugins/writ/commands/zz-stray.md", "removed plugins/writ/scripts/eval.sh"]
        assert "wrote plugins/writ/skills/tdd-cycle/SKILL.md" in lines
        assert "wrote .claude-plugin/marketplace.json" in lines
        check = run(built, "--check")
        assert check.returncode == 0, check.stdout + check.stderr
        assert check.stdout.splitlines() == ["pass", CLEAN_SUMMARY]

    def test_committed_tree_is_fresh(self):
        """AC-2.2: the committed plugin tree equals a fresh render (the whole
        `--check` on the repository passes)."""
        assert (REPO_ROOT / MANIFEST_REL).is_file(), "no committed plugin tree"
        proc = subprocess.run([sys.executable, str(MODULE_PATH), "--check"],
                              cwd=str(REPO_ROOT), capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.splitlines()[0] == "pass", proc.stdout


# -- write safety: symlinks under the plugin output -------------------------


def tree_state(tree: Path) -> Dict[str, bytes]:
    """Every regular file's bytes and every symlink's target, keyed by path,
    walked without following a link, so a write or delete through a link
    shows up as a change."""
    state = {}  # type: Dict[str, bytes]
    for dirpath, dirnames, filenames in os.walk(str(tree), followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        here = Path(dirpath)
        for name in dirnames + sorted(filenames):
            path = here / name
            rel = path.relative_to(tree).as_posix()
            if path.is_symlink():
                state[rel] = b"link:" + os.readlink(str(path)).encode("utf-8")
            elif path.is_file():
                state[rel] = path.read_bytes()
    return state


def link_subdirectory(tree: Path) -> None:
    shutil.rmtree(str(tree / PLUGIN_REL / "commands"))
    os.symlink("../../commands", str(tree / PLUGIN_REL / "commands"))


def link_plugin_root(tree: Path) -> None:
    shutil.rmtree(str(tree / PLUGIN_REL))
    os.symlink("..", str(tree / PLUGIN_REL))


def link_file(tree: Path) -> None:
    path = tree / PLUGIN_REL / "commands" / "status.md"
    path.unlink()
    os.symlink("../../../commands/status.md", str(path))


def link_marketplace_dir(tree: Path) -> None:
    shutil.rmtree(str(tree / ".claude-plugin"))
    os.symlink(PLUGIN_REL + "/.claude-plugin", str(tree / ".claude-plugin"))


# (id, mutation, the link the write refuses, the reason --check prints for it)
LINK_CASES = [
    ("subdirectory", link_subdirectory, "plugins/writ/commands", "orphan plugins/writ/commands"),
    ("plugin-root", link_plugin_root, "plugins/writ", "orphan plugins/writ"),
    ("file", link_file, "plugins/writ/commands/status.md", "stale plugins/writ/commands/status.md"),
    ("marketplace-dir", link_marketplace_dir, ".claude-plugin", "stale .claude-plugin/marketplace.json"),
]


class TestPluginWriteSafety:
    @pytest.mark.parametrize("args", [(), ("--target", TARGET)], ids=["write", "target"])
    @pytest.mark.parametrize("mutate, link", [(m, l) for _, m, l, _ in LINK_CASES],
                             ids=[i for i, _, _, _ in LINK_CASES])
    def test_write_refuses_a_symlink(self, built, mutate, link, args):
        """A symlink at or under the plugin output (the plugin root, a
        subdirectory, a file, or `.claude-plugin`) ends the run before any
        write: `fail`, `reason: symlink <path>`, no `wrote` or `removed`
        line, and no file in the tree written, changed, or deleted."""
        edit("commands/status.md")(built)  # a stale plugin, so a write has work to do
        mutate(built)
        before = tree_state(built)
        proc = run(built, *args)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        lines = proc.stdout.splitlines()
        assert lines[0] == "fail"
        assert "reason: symlink " + link in lines, proc.stdout
        assert [l for l in lines if l.startswith(("wrote ", "removed "))] == []
        assert tree_state(built) == before

    @pytest.mark.parametrize("mutate, expected", [(m, r) for _, m, _, r in LINK_CASES],
                             ids=[i for i, _, _, _ in LINK_CASES])
    def test_check_reports_a_symlink_without_following_it(self, built, mutate, expected):
        """`--check` names the link (an orphan where no render puts a file,
        stale where a file belongs) and reads nothing through it as an orphan."""
        mutate(built)
        before = tree_state(built)
        proc = run(built, "--check")
        assert proc.returncode == 1, proc.stdout + proc.stderr
        reasons = check_reasons(proc)
        assert expected in reasons, proc.stdout
        assert not [r for r in reasons if r.startswith("orphan ") and not r.startswith("orphan plugins/writ")]
        assert tree_state(built) == before


# -- AC-2.4: claude plugin validate ----------------------------------------


def validate_or_skip(path: Path) -> subprocess.CompletedProcess:
    """`claude plugin validate <path>` when `claude` is on PATH, else skip
    with reason `no claude CLI` (V30: exit 0 pass or pass with warnings).
    No network and no model call."""
    exe = shutil.which("claude")
    if exe is None:
        pytest.skip("no claude CLI")
    return subprocess.run([exe, "plugin", "validate", str(path)],
                          capture_output=True, text=True, timeout=300)


class TestPluginValidate:
    def test_plugin_directory_validates(self, rendered):
        """AC-2.4: validate on a temp copy of plugins/writ exits 0."""
        proc = validate_or_skip(rendered.plugin)
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_marketplace_root_validates(self, rendered):
        """AC-2.4, V31: validate on the temp root holding marketplace.json exits 0."""
        proc = validate_or_skip(rendered.out)
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_skips_without_claude(self, monkeypatch, tmp_path):
        """AC-2.4: with no `claude` on PATH the check is a skip with reason
        `no claude CLI`, never a pass."""
        monkeypatch.setattr(shutil, "which", lambda *args, **kwargs: None)
        with pytest.raises(pytest.skip.Exception, match="no claude CLI"):
            validate_or_skip(tmp_path)


# -- AC-2.5: adapters/claude-code.md -> Installation -> Plugin --------------

ADAPTER = REPO_ROOT / "adapters" / "claude-code.md"
DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def plugin_section(gen) -> str:
    lines = ADAPTER.read_text(encoding="utf-8").splitlines()
    span, missing = gen.section(lines, ("## Installation", "### Plugin"))
    assert span is not None, "adapters/claude-code.md has no %r" % missing
    return "\n".join(lines[span[0]:span[1]])


def ignored_keys() -> List[str]:
    """The keys technical-spec.md -> Generated-agent frontmatter keys under
    a plugin marks `ignored`, plus the ones its closing line names."""
    lines = spec_text().splitlines()
    start = lines.index("### Generated-agent frontmatter keys under a plugin")
    keys = []  # type: List[str]
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        m = re.match(r"^- `([A-Za-z]+)` \(\d+ of \d+\): `ignored`", line)
        if m:
            keys.append(m.group(1))
        if "also ignored in plugin agents" in line:
            keys += re.findall(r"`([A-Za-z]+)`", line.split("are also ignored")[0])
    return keys


class TestAdapterPluginSection:
    def test_install_commands(self, gen):
        """AC-2.5: both install commands, in a bash block."""
        text = plugin_section(gen)
        block = re.search(r"```bash\n(.*?)\n```", text, re.S)
        assert block, "no bash block under ### Plugin"
        assert "claude plugin marketplace add sellke/writ" in block.group(1)
        assert "claude plugin install writ@writ" in block.group(1)

    def test_carrier_with_its_observation(self, gen):
        """AC-2.5: the carrier is named with the observation's date, Claude
        Code version, and source URL (V69)."""
        bullets = [b for b in self.bullets(gen) if "output-styles/writ.md" in b]
        assert bullets, "no bullet names the carrier"
        claim = bullets[0]
        for needle in ("force-for-plugin: true", "keep-coding-instructions: true", "2026-10-23",
                       "Claude Code 2.1.309", "https://code.claude.com/docs/en/output-styles.md"):
            assert needle in claim, needle

    def test_ignored_keys(self, gen):
        """AC-2.5: every agent frontmatter key the record marks ignored in
        plugins (V15, V16) is listed."""
        keys = ignored_keys()
        assert keys == ["permissionMode", "hooks", "mcpServers", "initialPrompt"]
        text = plugin_section(gen)
        for key in keys:
            assert "`%s`" % key in text, key
        assert "https://code.claude.com/docs/en/sub-agents.md" in text

    def test_both_command_sets(self, gen):
        """AC-2.5: a project with an install.sh install and the plugin has
        both command sets; the adapter recommends one install path."""
        claim = [b for b in self.bullets(gen) if "install.sh" in b and "`/writ:create-spec`" in b]
        assert claim, "no bullet states both command sets"
        assert "`/create-spec`" in claim[0]
        assert "one install path per project" in claim[0]

    def test_every_claim_has_a_date_and_url(self, gen):
        """Hardest Constraint: each platform claim (one bullet each) carries
        a date and an https URL."""
        bullets = self.bullets(gen)
        assert len(bullets) >= 6
        for bullet in bullets:
            assert DATE.search(bullet), bullet[:80]
            assert "https://" in bullet, bullet[:80]

    @staticmethod
    def bullets(gen) -> List[str]:
        """Top-level `- ` items outside fences, continuation lines joined."""
        items = []  # type: List[str]
        open_item = False
        in_fence = False
        for line in plugin_section(gen).splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                open_item = False
                continue
            if in_fence:
                continue
            if line.startswith("- "):
                items.append(line[2:].strip())
                open_item = True
            elif open_item and line.startswith("  ") and line.strip():
                items[-1] += " " + line.strip()
            else:
                open_item = False
        return items
