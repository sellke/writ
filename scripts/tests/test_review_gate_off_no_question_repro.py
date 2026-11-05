from pathlib import Path

REVIEW = Path(__file__).resolve().parents[2] / "commands" / "review.md"


def test_the_question_is_skipped_when_the_evidence_gate_is_off():
    text = REVIEW.read_text(encoding="utf-8")
    step4 = text[text.index("### Step 4:"):text.index("### Step 5:")]
    before = " ".join(step4[:step4.index("review-override.py evidence")].split())
    assert "`off`" in before or "`on`" in before[:before.index("AskQuestion")]
