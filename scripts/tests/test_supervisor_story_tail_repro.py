import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = REPO_ROOT / "agents" / "supervisor-agent.md"
TAIL = "..{head_ref} -- . ':(exclude).writ'"


def story_gate_section():
    text = SUPERVISOR.read_text(encoding="utf-8")
    start = text.index("## Story-gate record")
    return text[start : text.index("\n## ", start + 1)]


def test_code_after_the_story_commit_is_checked_for_every_story():
    # A single story's range can hold a code commit after its `> **Commit:**`
    # SHA; no record covers it, so the tail check cannot be lane-only.
    sentences = re.split(r"(?<=\.)\s+(?=[A-Z])", story_gate_section())
    tails = [s for s in sentences if TAIL in s]
    assert tails, "no check for code after the story's Commit SHA"
    assert not any(s.startswith("For a lane") for s in tails)
