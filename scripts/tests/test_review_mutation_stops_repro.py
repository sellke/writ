from pathlib import Path

REVIEW = Path(__file__).resolve().parents[2] / "commands" / "review.md"


def test_step4_stops_on_a_tree_mutation():
    text = REVIEW.read_text(encoding="utf-8")
    step4 = text[text.index("### Step 4:"):text.index("### Step 5:")]
    assert "repro_mutated_tree" in step4
