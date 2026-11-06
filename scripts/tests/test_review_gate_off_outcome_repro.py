from pathlib import Path

REVIEW = Path(__file__).resolve().parents[2] / "commands" / "review.md"


def test_outcome_table_keeps_written_severities_when_the_gate_is_off_or_unverifiable():
    text = REVIEW.read_text(encoding="utf-8")
    start = text.index("**Outcome interpretation")
    outcome = text[start:text.index("A review with zero", start)]
    assert "`off`" in outcome
    assert "`unverifiable`" in outcome
