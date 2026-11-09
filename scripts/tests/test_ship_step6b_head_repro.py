import re
from pathlib import Path

SHIP = Path(__file__).resolve().parents[2] / "commands" / "ship.md"


def test_watch_pass_on_merged_pr_reads_head_ref_oid_for_step_6b():
    text = SHIP.read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if l.startswith("**7.1 Resolve the PR.**"))
    fields = re.search(r"`gh pr view --json ([A-Za-z,]+)`", line)
    assert fields, line
    assert "headRefOid" in fields.group(1).split(",")
