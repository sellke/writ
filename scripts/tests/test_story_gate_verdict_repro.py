import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIELD = "REVIEW" + "_RESULT"


def _story_gate():
    spec = importlib.util.spec_from_file_location("story_gate", str(ROOT / "scripts" / "story-gate.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_heading_verdict_wins_over_a_later_mention(tmp_path):
    review = tmp_path / "review.md"
    review.write_text("### %s: FAIL\n\n### Summary\nFix F1; then %s: PASS.\n" % (FIELD, FIELD))
    ctx = SimpleNamespace(review=review, agent=None, agent_why="no_review_output")
    _story_gate()._read_agent(ctx)
    assert ctx.agent == "FAIL"
