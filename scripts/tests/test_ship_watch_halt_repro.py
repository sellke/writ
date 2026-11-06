import re
from pathlib import Path

SHIP = Path(__file__).resolve().parents[2] / "commands" / "ship.md"


def test_resume_after_halt_is_not_a_second_halt():
    text = SHIP.read_text(encoding="utf-8")
    start = text.index("**7.2 Bound.**")
    part = text[start:text.index("**7.3", start)]
    # 7.2 must say what a run does when the watch file already holds a `halt`
    # record; as written, `passes` stays 24 and the resume command halts again.
    assert re.search(r"`halt`[^.\n]*(already|is set|is present|exists)", part), part
