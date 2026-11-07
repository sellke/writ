import re
from pathlib import Path

REPORT = (Path(__file__).resolve().parents[2] / ".writ" / "specs"
          / "2026-11-06-lean-story-pipeline" / "trial-report.md")


def _row(label):
    for line in REPORT.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower().startswith(label):
            return cells
    raise AssertionError("no row " + label)


def _output_tokens(cell):
    match = re.search(r"([\d,]+)\s+output", cell)
    assert match, cell
    return int(match.group(1).replace(",", ""))


def test_arm_after_output_tokens_exceed_arm_before():
    # Stream result events: arm-after story 1 has three result events whose
    # per-segment usage must be summed (15,397 + 1,712 + 13,531), giving
    # 51,969 orchestrator output tokens for arm-after against 40,076 for
    # arm-before; modelUsage (all agents) gives 155,475 against 90,994.
    cells = _row("cost and tokens")
    assert _output_tokens(cells[2]) > _output_tokens(cells[1]), cells
