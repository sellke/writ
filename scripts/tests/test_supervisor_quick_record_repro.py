from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = REPO_ROOT / "agents" / "supervisor-agent.md"


def story_gate_section():
    text = SUPERVISOR.read_text(encoding="utf-8")
    start = text.index("## Story-gate record")
    return text[start : text.index("\n## ", start + 1)]


def test_quick_and_accepted_pause_records_are_not_verdict_failures():
    # A --quick post-review record has no `gate3` key, and an accepted Gate 3
    # PAUSE records `gate3.verdict: PAUSE`; both stories complete legitimately.
    line = next(x for x in story_gate_section().splitlines()
                if "`story-gate record verdict fail`" in x)
    assert "`gate3.verdict` is not `PASS`" not in line
