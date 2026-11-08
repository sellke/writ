from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = REPO_ROOT / "agents" / "supervisor-agent.md"


def story_gate_section():
    text = SUPERVISOR.read_text(encoding="utf-8")
    start = text.index("## Story-gate record")
    return text[start : text.index("\n## ", start + 1)]


def test_lane_story_final_code_commit_is_bounded_by_the_story_commit():
    # A lane passes one range for several stories; each story's final code
    # commit must end at that story's own recorded `> **Commit:**` SHA, or
    # every story but the last fails the head rule.
    assert "**Commit:**" in story_gate_section()
