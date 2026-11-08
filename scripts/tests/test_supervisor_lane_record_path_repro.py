from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = REPO_ROOT / "agents" / "supervisor-agent.md"


def test_lane_record_path_resolves_in_the_lane_worktree():
    # .writ/state/ is gitignored and the lane's records live in its worktree,
    # not in the checkout /implement-phase spawns the supervisor from.
    text = SUPERVISOR.read_text(encoding="utf-8")
    start = text.index("## Input Requirements")
    rules = text[start : text.index("## Output Format", start)]
    assert "git worktree list" in rules
