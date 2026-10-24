"""`/prototype` brings a worktree-isolated coding agent's change into the
user's checkout (Phase 14 acceptance).

Headless runs of `/writ:writ` -> `/writ:prototype --no-diverge` under the
Claude Code plugin finished the fix in the `writ-coder` agent's isolated
worktree and left the user's checkout unchanged in 2 of 3 runs, while the
reply said the tests passed. `/implement-story` already cites the
integration skill; Step 3 of `/prototype` did not.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = "skills/subagent-worktree-integration/SKILL.md"


def step(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.index("\n### ", start + len(heading))
    return text[start:end]


def test_step_3_integrates_worktree_results():
    body = step((REPO / "commands/prototype.md").read_text(encoding="utf-8"), "### Step 3: Spawn Coding Agent")
    assert "`Read %s`" % SKILL in body
    assert "done only when it is in the user's checkout" in body
    assert "git status" in body
    # A post-fix run wrote its patch to the project's parent directory.
    assert "writing no temporary file outside the project" in body
    assert (REPO / SKILL).is_file()


def test_plugin_render_resolves_the_skill():
    body = step((REPO / "plugins/writ/commands/prototype.md").read_text(encoding="utf-8"),
                "### Step 3: Spawn Coding Agent")
    assert "`Read ${CLAUDE_PLUGIN_ROOT}/%s`" % SKILL in body
