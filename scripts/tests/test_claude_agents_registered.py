"""`.claude/agents` registers the nine writ-* agents in this repo.

Story 1 of 2026-11-08-writ-agents-registered. Claude Code registers an agent
only from a file whose YAML frontmatter carries `name:`; `agents/*.md` has no
frontmatter and `claude-code/agents/*.md` does.
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LINK = REPO / ".claude" / "agents"
# The agent Gate 1 spawns by name, read through the link.
CODER = REPO / ".claude" / "agents" / "writ-coder.md"

WRIT_AGENTS = (
    "writ-architect",
    "writ-coder",
    "writ-documenter",
    "writ-evaluator",
    "writ-reviewer",
    "writ-story-gen",
    "writ-supervisor",
    "writ-tester",
    "writ-visual-qa",
)


def frontmatter_name(path):
    """The `name:` value inside the leading `---` block, or None."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        if line.startswith("name:"):
            return line[len("name:"):].strip()
    return None


def test_claude_agents_link_registers_the_nine_writ_agents():
    """AC-1.1: `.claude/agents` links to `../claude-code/agents`, and each of
    the nine writ-* names resolves to a frontmatter `name:` there."""
    assert os.readlink(LINK) == "../claude-code/agents"
    registered = {frontmatter_name(p) for p in sorted(LINK.glob("*.md"))}
    missing = [name for name in WRIT_AGENTS if name not in registered]
    assert missing == []
    assert CODER.resolve() == (REPO / "claude-code" / "agents" / "writ-coder.md").resolve()
    assert frontmatter_name(CODER) == "writ-coder"
