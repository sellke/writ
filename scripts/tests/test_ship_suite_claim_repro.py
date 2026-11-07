from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_full_suite_claim_matches_ship_default():
    ship = (ROOT / "commands" / "ship.md").read_text(encoding="utf-8")
    story = (ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
    ship_skips_tests_by_default = "Tests do not run by default" in ship
    claims_plain_ship = "or in `/ship` for a standalone story" in story
    assert not (ship_skips_tests_by_default and claims_plain_ship)
