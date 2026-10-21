#!/usr/bin/env python3
"""Claim checks for adapters/claude-code.md, Story 3 of
`2026-10-20-claude-code-parity`.

The adapter must name only commands, flags, hook events, agents, and worktree
behavior that exist, and its manual install must not copy the template over
the user's `CLAUDE.md`. These tests read the adapter as text.

Agent names, models, permission modes, and isolation come from the frontmatter
of `claude-code/agents/*.md`, never from a hard-coded list or count. Skill step
numbers come from the headings of
`skills/subagent-worktree-integration/SKILL.md`.

Covers AC-3.1, AC-3.2, AC-3.3, AC-3.4, and AC-3.5.

Run: uv run pytest scripts/tests/test_claude_code_adapter_claims.py
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER = REPO_ROOT / "adapters" / "claude-code.md"
AGENTS_DIR = REPO_ROOT / "claude-code" / "agents"
SKILL = REPO_ROOT / "skills" / "subagent-worktree-integration" / "SKILL.md"

SKILL_LINK = "../skills/subagent-worktree-integration/SKILL.md"
WORKTREES_URL = "https://code.claude.com/docs/en/worktrees"
HOOKS_URL = "https://code.claude.com/docs/en/hooks"
IMPORT_LINE = "@.claude/system-instructions.md"
START_MARKER = "<!-- writ:start -->"
END_MARKER = "<!-- writ:end -->"
MERGE_BACK_PHRASES = (
    "Merges changes back",
    "changes merge back",
    "merge back automatically",
)


def adapter_text() -> str:
    return ADAPTER.read_text(encoding="utf-8")


def _headings(lines: List[str]) -> Iterator[Tuple[int, int, str]]:
    """(line index, level, heading line) for each heading outside a fence."""
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6}) \S", line)
        if m:
            yield i, len(m.group(1)), line


def section(text: str, heading_prefix: str) -> str:
    """The heading line that starts with `heading_prefix`, through the line
    before the next heading of the same or a higher level."""
    lines = text.split("\n")
    heads = list(_headings(lines))
    for n, (start, level, line) in enumerate(heads):
        if not line.startswith(heading_prefix):
            continue
        end = len(lines)
        for later, later_level, _ in heads[n + 1:]:
            if later_level <= level:
                end = later
                break
        return "\n".join(lines[start:end])
    raise AssertionError("adapter has no heading starting with %r" % heading_prefix)


def fences(text: str, info: str = "") -> List[str]:
    """Bodies of the fenced blocks in `text` whose info string equals `info`."""
    out = []
    pattern = re.compile(r"^```([^\n]*)\n(.*?)\n```$", re.M | re.S)
    for m in pattern.finditer(text):
        if m.group(1).strip() == info:
            out.append(m.group(2))
    return out


def strip_code(text: str) -> str:
    """Text with fenced blocks and backtick spans removed."""
    text = re.sub(r"^```.*?^```$", "", text, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def agent_frontmatter() -> Dict[str, Dict[str, str]]:
    """Frontmatter keys of each claude-code/agents/*.md, keyed by `name`."""
    out: Dict[str, Dict[str, str]] = {}
    for path in sorted(AGENTS_DIR.glob("*.md")):
        lines = path.read_text(encoding="utf-8").split("\n")
        assert lines[0] == "---", path
        fields: Dict[str, str] = {}
        for line in lines[1:]:
            if line == "---":
                break
            m = re.match(r"^([A-Za-z]+):\s*(.*)$", line)
            if m:
                fields[m.group(1)] = m.group(2).strip()
        assert "name" in fields, path
        out[fields["name"]] = fields
    assert out, "no agent files under claude-code/agents/"
    return out


def agent_rows(section_text: str) -> Dict[str, List[str]]:
    """Table rows whose first cell is an agent name, keyed by that name."""
    rows: Dict[str, List[str]] = {}
    for line in section_text.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if re.fullmatch(r"writ-[a-z-]+", cells[0]):
            rows[cells[0]] = cells
    return rows


def skill_step(keyword: str) -> int:
    """Number of the skill's `### N. ...` step whose title holds `keyword`."""
    text = SKILL.read_text(encoding="utf-8")
    for m in re.finditer(r"^### (\d+)\. (.+)$", text, re.M):
        if keyword.lower() in m.group(2).lower():
            return int(m.group(1))
    raise AssertionError("skill has no step titled with %r" % keyword)


def gotchas(text: str) -> List[Tuple[int, str]]:
    """(number, body) per numbered item in `## Gotchas`."""
    body = section(text, "## Gotchas")
    items = re.split(r"\n(?=\d+\. \*\*)", body)
    out = []
    for item in items:
        m = re.match(r"^(\d+)\. \*\*", item)
        if m:
            out.append((int(m.group(1)), item))
    return out


class NoNonexistentFeatures(unittest.TestCase):
    """AC-3.1: no `--all`, no agent-teams workflow, no merge-back claim."""

    def test_no_all_flag(self) -> None:
        """AC-3.1: `--all` as a whole flag; `--allowedTools` does not count."""
        hits = [
            "%d: %s" % (n, line)
            for n, line in enumerate(adapter_text().split("\n"), 1)
            if re.search(r"--all\b", line)
        ]
        self.assertEqual(hits, [], "\n".join(hits))

    def test_no_agent_teams_heading(self) -> None:
        """AC-3.1: no heading names Agent Teams."""
        lines = adapter_text().split("\n")
        heads = [line for _, _, line in _headings(lines) if "agent teams" in line.lower()]
        self.assertEqual(heads, [])

    def test_no_agent_teams_mention(self) -> None:
        """AC-3.1: no case-insensitive `agent teams`, intro line and gotchas included."""
        hits = [
            "%d: %s" % (n, line)
            for n, line in enumerate(adapter_text().split("\n"), 1)
            if "agent teams" in line.lower()
        ]
        self.assertEqual(hits, [], "\n".join(hits))

    def test_no_merge_back_claims(self) -> None:
        """AC-3.1: worktree changes do not come back on their own."""
        lower = adapter_text().lower()
        for phrase in MERGE_BACK_PHRASES:
            self.assertNotIn(phrase.lower(), lower, phrase)


class WorktreeFacts(unittest.TestCase):
    """AC-3.2: worktree base, cleanup, and reconciliation match the docs and skill."""

    def setUp(self) -> None:
        self.text = adapter_text()
        self.worktree = section(self.text, "### Git Worktree Isolation")

    def test_base_branch_and_base_ref(self) -> None:
        """AC-3.2: default branch unless `worktree.baseRef` is `"head"`."""
        self.assertIn("default branch", self.worktree)
        self.assertIn("worktree.baseRef", self.worktree)
        self.assertIn('"head"', self.worktree)

    def test_cleanup_rule(self) -> None:
        """AC-3.2: removed with no changes; otherwise stays on disk with them."""
        self.assertIn("no changes", self.worktree)
        self.assertIn("stays on disk", self.worktree)

    def test_reconcile_per_skill(self) -> None:
        """AC-3.2: the orchestrator diffs, copies, re-verifies, removes, per the skill."""
        self.assertIn("](%s" % SKILL_LINK, self.worktree)
        lower = self.worktree.lower()
        for step in ("diff", "copy", "re-verify", "remove"):
            self.assertIn(step, lower, step)
        self.assertIn("reconcile", lower)

    def test_cites_worktrees_docs(self) -> None:
        """AC-3.2: the worktree facts cite the Claude Code worktrees page."""
        self.assertIn(WORKTREES_URL, self.worktree)

    def test_worktree_agent_list_matches_frontmatter(self) -> None:
        """AC-3.2: the agents listed as using worktrees are those with `isolation: worktree`."""
        expected = {
            name for name, fm in agent_frontmatter().items()
            if fm.get("isolation") == "worktree"
        }
        listed = set(re.findall(r"^- `(writ-[a-z-]+)` —", self.worktree, re.M))
        self.assertEqual(listed, expected)

    def test_create_spec_example_points_at_skill(self) -> None:
        """AC-3.2: story files stay in their worktrees until copied back per the skill."""
        example = section(self.text, "### create-spec: Parallel Story Generation")
        self.assertIn("stays in its worktree", example)
        self.assertIn("](%s" % SKILL_LINK, example)


class ParallelStoriesAndStaleWorktrees(unittest.TestCase):
    """AC-3.3: parallel stories come from /implement-spec; Gotcha 1 is the stale-worktree risk."""

    def setUp(self) -> None:
        self.text = adapter_text()

    def test_parallel_stories_are_implement_spec_batches(self) -> None:
        """AC-3.3: `/implement-spec` runs independent stories in parallel batches."""
        worktree = section(self.text, "### Git Worktree Isolation")
        self.assertIn("`/implement-spec` runs independent stories in parallel batches", worktree)

    def test_merge_conflict_gotcha_is_gone(self) -> None:
        """AC-3.3: the 'Worktree merges can conflict' gotcha is replaced."""
        self.assertNotIn("Worktree merges can conflict", self.text)

    def test_gotcha_one_is_stale_worktree_with_skill_pointer(self) -> None:
        """AC-3.3: copying a stale worktree back can overwrite newer work; see the skill's stale step."""
        items = gotchas(self.text)
        self.assertTrue(items, "no numbered gotchas")
        number, first = items[0]
        self.assertEqual(number, 1)
        lower = first.lower()
        self.assertIn("stale", lower)
        self.assertIn("overwrite", lower)
        self.assertIn("](%s" % SKILL_LINK, first)
        self.assertIn("step %d" % skill_step("stale worktree"), first)

    def test_gotcha_one_gives_both_causes_of_staleness(self) -> None:
        """AC-3.3: the default base is the remote default branch, so unpushed
        commits are missing; with `"head"`, later commits are missing."""
        _, first = gotchas(self.text)[0]
        lower = first.lower()
        self.assertIn("remote", lower)
        self.assertIn("unpushed", lower)
        self.assertIn('worktree.baseRef: "head"', first)
        self.assertIn("after it was created", lower)

    def test_gotchas_are_numbered_in_order(self) -> None:
        """AC-3.3: the gotchas are renumbered 1..n after the removal."""
        numbers = [n for n, _ in gotchas(self.text)]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))


class InstallationSection(unittest.TestCase):
    """AC-3.4: install text copies system-instructions.md and merges between markers."""

    def setUp(self) -> None:
        self.text = adapter_text()
        self.install = section(self.text, "## Installation")

    def test_automated_text_names_system_instructions(self) -> None:
        """AC-3.4: the automated-install text mentions `.claude/system-instructions.md`."""
        automated = section(self.install, "### Automated")
        self.assertIn(".claude/system-instructions.md", automated)

    def test_manual_step_one_appends_between_markers(self) -> None:
        """AC-3.4: manual Step 1 appends the template between the markers."""
        step1 = section(self.install, "#### Step 1")
        self.assertIn(START_MARKER, step1)
        self.assertIn(END_MARKER, step1)
        self.assertRegex(step1, r"cat\s+\S*claude-code/CLAUDE\.md")
        self.assertIn(">> CLAUDE.md", step1)
        self.assertIn("tail -c 1 CLAUDE.md", step1)

    def test_manual_step_one_copies_system_instructions(self) -> None:
        """AC-3.4: manual Step 1 copies `system-instructions.md` into `.claude/`."""
        step1 = section(self.install, "#### Step 1")
        self.assertRegex(
            step1, r"cp\s+\S*system-instructions\.md\s+\.claude/system-instructions\.md"
        )

    def test_manual_step_one_names_the_scripted_path(self) -> None:
        """AC-3.4: `--force` replaces only the block; install.sh does all of it."""
        step1 = section(self.install, "#### Step 1")
        self.assertIn("install.sh --platform claude", step1)
        self.assertIn("only the block", step1)
        self.assertIn("--force", step1)
        self.assertIn("outside the markers", step1)

    def test_manual_step_one_names_the_missing_baseline(self) -> None:
        """AC-3.4: a manual install writes no manifest, so later scripted runs
        keep a block that differs from the template and report it as modified."""
        step1 = section(self.install, "#### Step 1")
        self.assertIn("no manifest", step1)
        self.assertIn("baseline", step1)
        self.assertIn("update.sh", step1)
        self.assertIn("even if you edited nothing", step1)

    def test_manual_step_one_warns_force_overwrites_other_files(self) -> None:
        """AC-3.4: `--force` also overwrites every other Writ file that differs
        from upstream, so a customized command is lost after a manual install."""
        step1 = section(self.install, "#### Step 1")
        force = [p for p in re.split(r"\n\s*\n", step1) if "`--force`" in p]
        self.assertEqual(len(force), 1, "expected one paragraph naming --force")
        self.assertIn("only the block", force[0])
        self.assertIn("also overwrites every other Writ file that differs from upstream", force[0])
        self.assertIn("customized or not", force[0])

    def test_no_copy_over_claude_md(self) -> None:
        """AC-3.4: no line copies `claude-code/CLAUDE.md` onto `CLAUDE.md`, with or without `./`."""
        pattern = r"cp\s+\S*claude-code/CLAUDE\.md\s+(\./)?CLAUDE\.md\b"
        self.assertIsNone(re.search(pattern, self.text))
        for line in (
            "cp path/to/writ/claude-code/CLAUDE.md ./CLAUDE.md",
            "cp path/to/writ/claude-code/CLAUDE.md CLAUDE.md",
        ):
            self.assertIsNotNone(re.search(pattern, line), line)

    def test_final_structure_lists_system_instructions_under_claude_dir(self) -> None:
        """AC-3.4: the Final Structure tree lists `.claude/system-instructions.md`."""
        tree = fences(section(self.install, "### Final Structure"))[0].split("\n")
        start = next(i for i, line in enumerate(tree) if "── .claude/" in line)
        end = next(i for i, line in enumerate(tree) if "── .writ/" in line)
        inside = [line for line in tree[start + 1:end]
                  if re.match(r"^│   [├└]── system-instructions\.md\b", line)]
        self.assertEqual(len(inside), 1, "\n".join(tree))

    def test_import_sentence(self) -> None:
        """AC-3.4: `CLAUDE.md` imports the file; an import outside the working directory needs one approval."""
        paragraphs = re.split(r"\n\s*\n", self.install)
        hits = [
            p for p in paragraphs
            if "`%s`" % IMPORT_LINE in p
            and "outside the working directory" in p
            and "approve" in p
        ]
        self.assertEqual(len(hits), 1, "expected one import paragraph")

    def test_import_line_only_inside_code(self) -> None:
        """AC-3.4: the adapter shows the import line only inside backticks or a fence."""
        self.assertNotIn(IMPORT_LINE, strip_code(self.text))


class HooksAndAgents(unittest.TestCase):
    """AC-3.5: documented hook events and inputs only; every agent in the tables and tree."""

    def setUp(self) -> None:
        self.text = adapter_text()
        self.agents = agent_frontmatter()
        self.hooks = section(self.text, "### Quality Gates with Hooks")

    def test_no_undocumented_event_or_variable(self) -> None:
        """AC-3.5: no `SubagentCompleted` and no `$WORKTREE`."""
        self.assertNotIn("SubagentCompleted", self.text)
        self.assertNotIn("$WORKTREE", self.text)

    def test_hook_example_is_subagent_stop_on_writ_coder(self) -> None:
        """AC-3.5: the settings example registers `SubagentStop` with matcher `^writ-coder$`."""
        blocks = fences(self.hooks, "json")
        self.assertEqual(len(blocks), 1)
        body = "\n".join(
            line for line in blocks[0].split("\n") if not line.lstrip().startswith("//")
        )
        config = json.loads(body)
        self.assertEqual(list(config["hooks"]), ["SubagentStop"])
        entries = config["hooks"]["SubagentStop"]
        self.assertEqual([e["matcher"] for e in entries], ["^writ-coder$"])
        self.assertIn("writ-coder", self.agents)
        commands = [h["command"] for e in entries for h in e["hooks"]]
        self.assertTrue(commands)
        self.assertTrue(all("writ-coder-checks.sh" in c for c in commands), commands)

    def test_hook_script_reads_cwd_and_exits_two(self) -> None:
        """AC-3.5: the hook script reads `cwd` from its input JSON and exits 2 with stderr text."""
        scripts = [b for b in fences(self.hooks, "bash") if "writ-coder-checks.sh" in b]
        self.assertEqual(len(scripts), 1)
        script = scripts[0]
        self.assertIn('["cwd"]', script)
        self.assertIn("sys.stdin", script)
        self.assertIn(">&2", script)
        self.assertRegex(script, r"(?m)^exit 2$")

    def test_hook_facts_and_citation(self) -> None:
        """AC-3.5: cites the hooks page; checks re-run in the orchestrator checkout per skill step."""
        self.assertIn(HOOKS_URL, self.hooks)
        prose = strip_code(self.hooks)
        self.assertIn("SubagentStop", self.hooks)
        self.assertIn("frontmatter", prose)
        self.assertIn("](%s" % SKILL_LINK, self.hooks)
        self.assertIn("step %d" % skill_step("re-verify"), self.hooks)

    def test_goal_section_points_at_subagent_stop(self) -> None:
        """AC-3.5: the /goal section points at the `SubagentStop` example."""
        goal = section(self.text, "### The /goal Stop Hook")
        self.assertIn("the `SubagentStop` example above", goal)

    def test_model_selection_intro_names_every_agent(self) -> None:
        """AC-3.5: the Model Selection intro names each agent; no six/seventh wording."""
        model = section(self.text, "### Model Selection")
        intro = model.split("\n|", 1)[0]
        for name in self.agents:
            self.assertIn("`%s`" % name, intro, name)
        self.assertNotIn("six Claude-native", self.text)
        self.assertNotIn("seventh", self.text)
        if "writ-visual-qa" in self.agents:
            self.assertNotIn("There is no `visual-qa` equivalent here yet", self.text)

    def test_model_tier_table_matches_frontmatter(self) -> None:
        """AC-3.5: one tier-table row per agent, with its frontmatter `model:`."""
        rows = agent_rows(section(self.text, "### Model Selection"))
        self.assertEqual(set(rows), set(self.agents))
        for name, cells in rows.items():
            self.assertEqual(cells[2], self.agents[name]["model"], name)

    def test_permission_table_matches_frontmatter(self) -> None:
        """AC-3.5: one Permission Modes row per agent, with its frontmatter `permissionMode`."""
        rows = agent_rows(section(self.text, "### Permission Modes"))
        self.assertEqual(set(rows), set(self.agents))
        for name, cells in rows.items():
            self.assertEqual(cells[1], self.agents[name]["permissionMode"], name)

    def test_final_structure_tree_lists_every_agent(self) -> None:
        """AC-3.5: the Final Structure tree lists each agent file once."""
        tree = fences(section(self.text, "### Final Structure"))[0]
        listed = re.findall(r"[├└]── (writ-[a-z-]+)\.md", tree)
        self.assertEqual(sorted(listed), sorted(self.agents))


if __name__ == "__main__":
    unittest.main()
