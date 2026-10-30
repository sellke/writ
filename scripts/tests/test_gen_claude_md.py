#!/usr/bin/env python3
"""Tests for scripts/gen-claude-md.py. CapabilityMapTests at the end come from
Story 2 of `2026-10-22-generated-platform-trees` (the `{capability_map}` slot);
everything else is Story 1 of `2026-10-20-claude-code-parity`.

The generator builds `claude-code/CLAUDE.md` from the Claude Code capability
map that `scripts/gen-platform-trees.py` renders from `adapters/claude-code.md`,
after validating the `commands:` list in `.writ/manifest.yaml`. The template
lists no commands and no agents: Claude Code's skill listing and Agent tool
show both every session. It prints the check shape from the agent CLI
contract and writes nothing on any failure.

CLI tests copy the script, the driver, and the adapter into a temp root,
because the script resolves its root from its own path. Nothing here writes
to the real repo. The module name has a hyphen, so in-process tests import it
by path, the way test_gen_codex_agent_tomls.py does.

Expected command counts and map rows come from the real manifest and adapter,
never from a hard-coded count.

Run: uv run pytest scripts/tests/test_gen_claude_md.py
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "gen-claude-md.py"
TREES_PATH = REPO_ROOT / "scripts" / "gen-platform-trees.py"
MANIFEST = REPO_ROOT / ".writ" / "manifest.yaml"
ADAPTER = REPO_ROOT / "adapters" / "claude-code.md"
TEMPLATE = REPO_ROOT / "claude-code" / "CLAUDE.md"
IMPORT_LINE = "@.claude/system-instructions.md"
SENTINEL = b"SENTINEL TEMPLATE\n"
# A minimal adapter with the real Claude Code headings and one row whose
# mapping cell holds an `@` outside backticks.
AT_SIGN_ADAPTER = "\n".join([
    "# Claude Code Adapter", "", "## Tool Mapping (Cursor → Claude Code)", "",
    "### Quick Reference", "", "| Cursor Tool | Claude Code Native | Notes |", "|---|---|---|",
    "| `read_file` | Load @docs/x.md first | Direct equivalent |", "",
]) + "\n"


def load_module(path: Path = MODULE_PATH, name: str = "gen_claude_md"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def claude_map() -> str:
    """The Claude Code capability map the driver renders from the real adapter."""
    return load_module(TREES_PATH, "gen_platform_trees").capability_map("claude-code", REPO_ROOT)


def manifest_commands() -> List[Tuple[str, str]]:
    """(name, purpose) per manifest command, read without the generator."""
    text = MANIFEST.read_text(encoding="utf-8")
    section = text.split("\ncommands:\n", 1)[1]
    section = re.split(r"\n(?=[^\s#])", section, maxsplit=1)[0]
    out = []
    for block in re.split(r"\n(?=  - name: )", section):
        name = re.search(r"^  - name: (\S+)$", block, re.M)
        purpose = re.search(r'^    purpose: "(.*)"$', block, re.M)
        if name and purpose:
            value = re.sub(r'\\(["\\])', r"\1", purpose.group(1))
            out.append((name.group(1), value))
    return out


def fixture_manifest(entries: List[Tuple[str, Optional[str]]]) -> str:
    """A small manifest: one command per (name, purpose); None omits purpose."""
    lines = ["version: 1", "metadata:", "  name: fixture", "", "commands:"]
    for name, purpose in entries:
        lines += ["  - name: %s" % name, "    file: commands/%s.md" % name,
                  "    category: planning"]
        if purpose is not None:
            lines.append('    purpose: "%s"' % purpose)
        lines.append("    tags: [x]")
    lines += ["", "agents:", "  - name: coding-agent", "    file: agents/coding-agent.md",
              '    purpose: "Not a command."', ""]
    return "\n".join(lines)


PIPELINE_ENTRIES = [
    ("plan-product", "Plan the product."),
    ("create-spec", "Write a spec | contract first."),
    ("implement-spec", "Build a spec from `@scope` code."),
    ("verify-spec", "Check a spec."),
    ("release", "Cut a release."),
    ("implement-phase", "Run a phase."),
]

EXPECTED_HEAD = [
    "# Writ",
    "",
    "You are **Writ** — a methodical AI development partner. You organize all work in `.writ/` folders.",
    "",
    "Writ's root contract (Prime Directive, interaction rules, model tiers) loads from this import:",
    "",
    "@.claude/system-instructions.md",
    "",
    "## Commands",
    "",
    'Start with `/writ "<what you want>"`: it restates the request and routes it to the right command.',
    "",
    "Writ commands live in `.claude/commands/` and its subagents in `.claude/agents/`; "
    "Claude Code lists both every session. To run a command, read its file and follow its workflow.",
]
EXPECTED_TAIL = [
    "## Pipeline",
    "",
    "```",
    "/plan-product → /create-spec → /implement-spec → /verify-spec → /release",
    "```",
    "",
    "`/implement-phase` runs `/implement-spec` once per spec in a roadmap phase.",
    "",
    "## Principles",
    "",
    "- **Contract-first**: Establish agreement before creating files",
    "- **TDD**: Tests first, then implementation",
    "- **Challenge assumptions**: Push back on bad ideas with evidence",
    "- **Commit incrementally**: Small commits, not big bangs",
]


def expected_fixture() -> str:
    """The exact fixture output: the Commands section, a blank line, the real
    Claude Code map, a blank line, then `## Pipeline` onward."""
    return "\n".join(EXPECTED_HEAD) + "\n\n" + claude_map() + "\n" + "\n".join(EXPECTED_TAIL) + "\n"


class TempRoot(unittest.TestCase):
    """A temp repo root holding a copy of the generator."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / ".writ").mkdir()
        (self.root / "adapters").mkdir()
        (self.root / "claude-code").mkdir()
        self.out = self.root / "claude-code" / "CLAUDE.md"
        self.manifest = self.root / ".writ" / "manifest.yaml"
        self.adapter = self.root / "adapters" / "claude-code.md"
        self.trees = self.root / "scripts" / "gen-platform-trees.py"
        if MODULE_PATH.is_file():
            shutil.copy(MODULE_PATH, self.root / "scripts" / "gen-claude-md.py")
        if TREES_PATH.is_file():
            shutil.copy(TREES_PATH, self.trees)
        if ADAPTER.is_file():
            shutil.copy(ADAPTER, self.adapter)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def use_real_inputs(self) -> None:
        shutil.copy(MANIFEST, self.manifest)

    def use_fixture(self, entries=PIPELINE_ENTRIES) -> None:
        self.manifest.write_text(fixture_manifest(entries), encoding="utf-8")

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "gen-claude-md.py"), *args],
            capture_output=True, text=True)

    def lines(self, result: subprocess.CompletedProcess) -> List[str]:
        return result.stdout.splitlines()

    def generate(self) -> bytes:
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.out.read_bytes()

    def assert_fail_untouched(self, reasons: List[str], *args: str) -> None:
        """Write mode prints fail with these reasons, exits 1, and leaves the template."""
        self.out.write_bytes(SENTINEL)
        result = self.run_cli(*args)
        lines = self.lines(result)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(lines[0], "fail")
        self.assertEqual([l for l in lines if l.startswith("reason: ")],
                         ["reason: " + r for r in reasons])
        self.assertTrue(lines[-1].startswith("gen-claude-md: fail ("), lines[-1])
        self.assertEqual(self.out.read_bytes(), SENTINEL)
        self.assertEqual(sorted(p.name for p in self.out.parent.iterdir()),
                         ["CLAUDE.md"], "a temp file was left behind")

    def assert_unverifiable(self, reason: str) -> None:
        """Both modes print unverifiable with this reason, exit 0, and leave the template."""
        for args in ((), ("--check",)):
            self.out.write_bytes(SENTINEL)
            result = self.run_cli(*args)
            lines = self.lines(result)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(lines[0], "unverifiable")
            self.assertIn("reason: " + reason, lines)
            self.assertTrue(lines[-1].startswith("gen-claude-md: unverifiable ("), lines[-1])
            self.assertEqual(self.out.read_bytes(), SENTINEL)


# --- AC-1.1: the template from the real manifest --------------------------------


class RealTemplateTests(TempRoot):
    """AC-1.1: no command table or agent list, pipeline, import line, bytes, and determinism."""

    def setUp(self) -> None:
        super().setUp()
        self.use_real_inputs()
        self.result = self.run_cli()
        self.text = self.out.read_text(encoding="utf-8") if self.out.is_file() else ""

    def test_ac_1_1_no_command_table_or_agent_list(self) -> None:
        """AC-1.1: the harness lists commands and agents, so the template does not:
        no command rows, no `## Agents`, no agent file names, no command purposes."""
        self.assertTrue(self.text)
        lines = self.text.splitlines()
        self.assertEqual([l for l in lines if l.startswith("| `/")], [])
        self.assertNotIn("| Command | File | Purpose |", lines)
        self.assertNotIn("## Agents", lines)
        self.assertNotIn("writ-evaluator", self.text)
        for _, purpose in manifest_commands():
            self.assertNotIn(purpose, self.text)

    def test_ac_1_1_sections_in_order(self) -> None:
        """AC-1.1: Commands, Capability Map, Pipeline, Principles, in that order,
        with the `/writ` entry line under Commands."""
        lines = self.text.splitlines()
        headings = [l for l in lines if l.startswith("## ")]
        self.assertEqual(headings, ["## Commands", "## Capability Map", "## Pipeline", "## Principles"])
        start = [i for i, l in enumerate(lines) if l.startswith('Start with `/writ "<what you want>"`')]
        self.assertEqual(len(start), 1)
        self.assertLess(lines.index("## Commands"), start[0])
        self.assertLess(start[0], lines.index("## Capability Map"))

    def test_ac_1_1_pipeline_line(self) -> None:
        """AC-1.1: the pipeline line sits in its fence under ## Pipeline."""
        self.assertIn("## Pipeline\n\n```\n/plan-product → /create-spec → /implement-spec"
                      " → /verify-spec → /release\n```\n", self.text)

    def test_ac_1_1_import_line_alone_outside_code(self) -> None:
        """AC-1.1: the import line is alone on its line, outside any backtick span or fence."""
        lines = self.text.splitlines()
        self.assertEqual(lines.count(IMPORT_LINE), 1)
        index = lines.index(IMPORT_LINE)
        fences = sum(1 for l in lines[:index] if l.startswith("```"))
        self.assertEqual(fences % 2, 0, "import line sits inside a fenced block")
        self.assertEqual(lines[index - 1], "")
        self.assertEqual(lines[index + 1], "")

    def test_ac_1_1_lf_endings_and_one_final_newline(self) -> None:
        """AC-1.1: LF endings and exactly one final newline."""
        data = self.out.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))

    def test_ac_1_1_stdout_line_one_is_pass(self) -> None:
        """AC-1.1: stdout line 1 is pass; the summary counts the manifest commands checked."""
        self.assertEqual(self.result.returncode, 0, self.result.stdout + self.result.stderr)
        lines = self.lines(self.result)
        self.assertEqual(lines[0], "pass")
        self.assertEqual(lines[-1], "gen-claude-md: pass (%d commands)" % len(manifest_commands()))

    def test_ac_1_1_second_run_leaves_bytes_unchanged(self) -> None:
        """AC-1.1: a second run writes the same bytes."""
        first = self.out.read_bytes()
        self.assertEqual(self.generate(), first)

    def test_ac_1_1_no_retired_loop_name(self) -> None:
        """AC-1.1: the template never names the retired Ralph loop (check_ralph_retirement)."""
        self.assertTrue(self.text)
        self.assertNotIn("ralph", self.text.lower())


class FixtureLayoutTests(TempRoot):
    """AC-1.1: the exact output layout, from a small fixture."""

    def test_ac_1_1_exact_bytes(self) -> None:
        """AC-1.1: the exact layout; no fixture purpose reaches the output."""
        self.use_fixture()
        self.assertEqual(self.generate().decode("utf-8"), expected_fixture())

    def test_ac_1_1_render_matches_cli(self) -> None:
        """AC-1.1: render() returns the same text the CLI writes."""
        gen = load_module()
        self.assertEqual(gen.render(claude_map()), expected_fixture())


# --- AC-1.2: --check ------------------------------------------------------------


class CheckModeTests(TempRoot):
    """AC-1.2: --check compares with the committed file and writes nothing."""

    def setUp(self) -> None:
        super().setUp()
        self.use_real_inputs()

    def test_ac_1_2_committed_template_passes(self) -> None:
        """AC-1.2: --check on the real repo prints pass and exits 0."""
        result = subprocess.run([sys.executable, str(MODULE_PATH), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(self.lines(result)[:1], ["pass"], result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0)

    def test_ac_1_2_fresh_template_passes(self) -> None:
        """AC-1.2: --check after a write prints pass, exits 0, and writes nothing."""
        before = self.generate()
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.lines(result)[0], "pass")
        self.assertTrue(self.lines(result)[-1].startswith("gen-claude-md: pass ("))
        self.assertEqual(self.out.read_bytes(), before)

    def test_ac_1_2_new_manifest_command_needs_no_regeneration(self) -> None:
        """AC-1.2: the template lists no commands, so a command added to the
        manifest leaves the committed template current."""
        before = self.generate()
        text = self.manifest.read_text(encoding="utf-8")
        self.manifest.write_text(text.replace("\ncommands:\n", "\ncommands:\n"
                                              "  - name: zz-new\n    file: commands/zz-new.md\n"
                                              "    purpose: \"A new command.\"\n", 1),
                                 encoding="utf-8")
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.lines(result)[0], "pass")
        self.assertEqual(self.out.read_bytes(), before)

    def test_ac_1_2_byte_difference_is_stale(self) -> None:
        """AC-1.2: any byte difference is `stale`."""
        text = self.generate().decode("utf-8")
        self.out.write_text(text.replace("## Principles", "## Principles!"), encoding="utf-8")
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 1)
        lines = self.lines(result)
        self.assertEqual(lines[:2], ["fail", "reason: stale claude-code/CLAUDE.md"])
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[-1].startswith("gen-claude-md: fail ("))

    def test_ac_1_2_crlf_copy_is_stale(self) -> None:
        """AC-1.2: CRLF line endings are a byte difference, so `stale`."""
        text = self.generate().decode("utf-8")
        self.out.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        result = self.run_cli("--check")
        self.assertIn("reason: stale claude-code/CLAUDE.md", self.lines(result))

    def test_ac_1_2_absent_template(self) -> None:
        """AC-1.2: no committed template is `absent`, exit 1, and nothing is created."""
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.lines(result)[:2],
                         ["fail", "reason: absent claude-code/CLAUDE.md"])
        self.assertFalse(self.out.exists())


# --- AC-1.3: error paths ------------------------------------------------------------


class ErrorPathTests(TempRoot):
    """AC-1.3: unverifiable, usage, and named fail reasons; no write on any failure."""

    def test_ac_1_3_missing_manifest_is_unverifiable(self) -> None:
        """AC-1.3: a missing .writ/manifest.yaml prints unverifiable and exits 0."""
        self.use_fixture()
        self.manifest.unlink()
        self.assert_unverifiable("manifest missing: .writ/manifest.yaml")

    def test_ac_1_3_agents_dir_is_not_an_input(self) -> None:
        """AC-1.3: the template lists no agents, so no claude-code/agents/ still passes."""
        self.use_fixture()
        self.assertFalse((self.root / "claude-code" / "agents").exists())
        self.assertEqual(self.generate().decode("utf-8"), expected_fixture())

    def test_ac_1_3_unknown_flag_is_usage_error(self) -> None:
        """AC-1.3: an unknown flag prints usage on stderr, empty stdout, exit 2."""
        self.use_fixture()
        self.out.write_bytes(SENTINEL)
        for args in (("--bogus",), ("--check", "--bogus"), ("--che",)):
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2, args)
            self.assertEqual(result.stdout, "", args)
            self.assertIn("usage:", result.stderr)
        self.assertEqual(self.out.read_bytes(), SENTINEL)

    def test_ac_1_3_help_exits_zero(self) -> None:
        """AC-1.3: --help documents --check and exits 0."""
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--check", result.stdout)

    def test_ac_1_3_command_without_purpose(self) -> None:
        """AC-1.3: a manifest command without purpose fails and names the entry."""
        self.use_fixture(PIPELINE_ENTRIES + [("knowledge", None)])
        self.assert_fail_untouched(["manifest knowledge missing purpose"])
        self.assert_fail_untouched(["manifest knowledge missing purpose"], "--check")

    def test_ac_1_3_at_sign_in_purpose_is_not_rendered(self) -> None:
        """AC-1.3: purposes are not rendered, so `@` in one is no import token."""
        self.use_fixture(PIPELINE_ENTRIES + [("knowledge", "Load @notes.md first.")])
        self.assertEqual(self.generate().decode("utf-8"), expected_fixture())

    def test_ac_1_3_pipeline_command_absent_from_manifest(self) -> None:
        """AC-1.3: a pipeline command missing from the manifest fails and names it."""
        self.use_fixture([e for e in PIPELINE_ENTRIES if e[0] != "verify-spec"])
        self.assert_fail_untouched(["pipeline verify-spec"])

    def test_ac_1_3_manifest_validation_reasons(self) -> None:
        """AC-1.3: bad name, wrong file, and duplicate name each name the entry."""
        self.use_fixture()
        text = self.manifest.read_text(encoding="utf-8")
        text = text.replace("commands:\n", "commands:\n"
                            "  - name: Bad_Name\n    file: commands/Bad_Name.md\n"
                            "    purpose: \"x\"\n"
                            "  - name: release\n    file: commands/release.md\n"
                            "    purpose: \"again\"\n"
                            "  - name: wrong-file\n    file: commands/other.md\n"
                            "    purpose: \"y\"\n", 1)
        self.manifest.write_text(text, encoding="utf-8")
        self.assert_fail_untouched(["manifest bad name Bad_Name",
                                    "manifest wrong-file file commands/other.md",
                                    "manifest duplicate release"])

    def test_ac_1_3_empty_and_absent_commands_section(self) -> None:
        """AC-1.3: `commands:` with no entries, or no `commands:` line, fails."""
        self.use_fixture()
        self.manifest.write_text("version: 1\ncommands:\n\nagents:\n  - name: x\n",
                                 encoding="utf-8")
        self.assert_fail_untouched(["manifest no commands"])
        self.manifest.write_text("version: 1\nagents:\n  - name: x\n", encoding="utf-8")
        self.assert_fail_untouched(["manifest no commands section"])

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores mode bits")
    def test_ac_1_3_write_error_leaves_template(self) -> None:
        """AC-1.3: a failed write prints `write <error>`, exits 1, and changes nothing."""
        self.use_fixture()
        self.out.write_bytes(SENTINEL)
        folder = self.out.parent
        folder.chmod(0o555)
        try:
            result = self.run_cli()
        finally:
            folder.chmod(0o755)
        lines = self.lines(result)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(lines[0], "fail")
        self.assertTrue(lines[1].startswith("reason: write "), lines)
        self.assertEqual(self.out.read_bytes(), SENTINEL)
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["CLAUDE.md"])


class ValueParserTests(unittest.TestCase):
    """AC-1.3: the line-based manifest reader's value rules."""

    def test_ac_1_3_quoted_and_bare_values(self) -> None:
        """AC-1.3: quotes drop and unescape; bare values drop a trailing comment."""
        gen = load_module()
        self.assertEqual(gen.parse_value(' "say \\"hi\\" \\\\ now" '), 'say "hi" \\ now')
        self.assertEqual(gen.parse_value("'it''s here'"), "it's here")
        self.assertEqual(gen.parse_value("plain words # comment"), "plain words")
        self.assertEqual(gen.parse_value("a#b"), "a#b")
        self.assertIsNone(gen.parse_value('"unterminated'))

    def test_ac_1_3_reader_ignores_other_sections_and_keys(self) -> None:
        """AC-1.3: only the `commands:` list is read; other keys and sections are ignored."""
        gen = load_module()
        commands, reasons = gen.read_commands(fixture_manifest([("ship", "Ship it.")]))
        self.assertEqual(reasons, [])
        self.assertEqual(commands, [("ship", "Ship it.")])


# --- 2026-10-22-generated-platform-trees, Story 2: the {capability_map} slot ---


class CapabilityMapTests(TempRoot):
    """2026-10-22-generated-platform-trees AC-2.3: the Claude Code capability
    map from scripts/gen-platform-trees.py fills the slot after the Commands
    section; its inputs and failures follow the generator's check shape."""

    def test_ac_2_3_capability_map_between_commands_and_pipeline(self) -> None:
        """AC-2.3: `## Capability Map` with the Claude Code rows sits after the
        Commands section and before `## Pipeline` in the real output."""
        self.use_real_inputs()
        lines = self.generate().decode("utf-8").splitlines()
        commands = lines.index("## Commands")
        heading = lines.index("## Capability Map")
        pipeline = lines.index("## Pipeline")
        self.assertLess(commands, heading)
        self.assertLess(heading, pipeline)
        expected = claude_map().splitlines()
        self.assertEqual(lines[heading:heading + len(expected)], expected)
        self.assertEqual(lines[heading - 1], "")
        self.assertEqual(lines[heading + len(expected):heading + len(expected) + 2], ["", "## Pipeline"])

    def test_ac_2_3_write_prints_wrote_line(self) -> None:
        """AC-2.3: write mode prints `wrote claude-code/CLAUDE.md` between the
        verdict and the summary, so the driver can relay it."""
        self.use_fixture()
        result = self.run_cli()
        self.assertEqual(self.lines(result), [
            "pass", "wrote claude-code/CLAUDE.md", "gen-claude-md: pass (6 commands)"])

    def test_ac_2_3_missing_adapter_is_unverifiable(self) -> None:
        """AC-2.3: a missing adapters/claude-code.md prints unverifiable and exits 0."""
        self.use_fixture()
        self.adapter.unlink()
        self.assert_unverifiable("adapter missing: adapters/claude-code.md")

    def test_ac_2_3_missing_driver_is_unverifiable(self) -> None:
        """AC-2.3: a missing scripts/gen-platform-trees.py prints unverifiable and exits 0."""
        self.use_fixture()
        self.trees.unlink()
        self.assert_unverifiable("platform-trees missing: scripts/gen-platform-trees.py")

    def test_ac_2_3_malformed_adapter_row(self) -> None:
        """AC-2.3: a malformed adapter row fails as `capability-map malformed
        adapters/claude-code.md:<line>` in both modes and writes nothing."""
        self.use_fixture()
        lines = self.adapter.read_text(encoding="utf-8").splitlines(True)
        hits = [i for i, l in enumerate(lines) if l.startswith("| `file_search` |")]
        self.assertEqual(len(hits), 1)
        lines.insert(hits[0] + 1, "| `zz_bad` | two cells only |\n")
        self.adapter.write_text("".join(lines), encoding="utf-8")
        reason = "capability-map malformed adapters/claude-code.md:%d" % (hits[0] + 2)
        self.assert_fail_untouched([reason])
        self.assert_fail_untouched([reason], "--check")

    def test_ac_2_3_at_sign_in_capability_map(self) -> None:
        """AC-2.3: an `@` outside backticks in the rendered map fails as
        `import-token capability-map`."""
        self.use_fixture()
        self.adapter.write_text(AT_SIGN_ADAPTER, encoding="utf-8")
        self.assert_fail_untouched(["import-token capability-map"])


if __name__ == "__main__":
    unittest.main()
