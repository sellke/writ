#!/usr/bin/env python3
"""Checks for spec `2026-10-25-retro-fix-ladder`.

Story 2: the seeded rule table `.writ/retros/rule-enforcers.md` has the
required heading and header, passes `scripts/retro-check.py --table`, and
holds at least two enforced rows and one `none` row (AC-2.1 to AC-2.4).

Run: uv run --python 3.9 pytest scripts/tests/test_retro_fix_ladder.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
RETRO_CHECK = REPO_ROOT / "scripts" / "retro-check.py"
TABLE = REPO_ROOT / ".writ" / "retros" / "rule-enforcers.md"

TABLE_HEADING = "# Rule-to-Enforcer Table"
TABLE_HEADER = "| Rule | Written in | Enforcer | Rung | Proof | Since |"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_retro_check(*args: str) -> Tuple[int, List[str]]:
    """Run retro-check.py with an argument list; (exit code, stdout lines)."""
    proc = subprocess.run([sys.executable, str(RETRO_CHECK), *args], cwd=str(REPO_ROOT),
                          capture_output=True, check=False, encoding="utf-8")
    return proc.returncode, proc.stdout.splitlines()


def _cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def table_blocks(text: str) -> List[List[str]]:
    """Each run of consecutive `|` lines, as a list of lines."""
    blocks: List[List[str]] = []
    current: List[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            current.append(line.strip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def table_rows(text: str) -> List[List[str]]:
    """Data rows of the first table, as cell lists (header and delimiter dropped)."""
    blocks = table_blocks(text)
    return [_cells(line) for line in blocks[0][2:]] if blocks else []


def test_table_heading_and_header() -> None:
    """AC-2.1: first heading is `# Rule-to-Enforcer Table`, one table, six-column header."""
    assert TABLE.is_file(), "%s is missing" % TABLE.relative_to(REPO_ROOT)
    text = read_text(TABLE)
    headings = [line for line in text.splitlines() if line.startswith("#")]
    assert headings and headings[0] == TABLE_HEADING
    blocks = table_blocks(text)
    assert len(blocks) == 1, "expected one table, found %d" % len(blocks)
    assert blocks[0][0] == TABLE_HEADER


def test_table_passes_retro_check_with_enforced_and_unenforced_rows() -> None:
    """AC-2.2, AC-2.3, AC-2.4: `retro-check.py --table` prints `pass` on line 1
    (every enforced row has a `<sha>: fails` Proof whose SHA resolves here);
    at least two rows name an enforcer and at least one is `none` with Rung
    `docs` and Proof `—`."""
    code, lines = run_retro_check("--table", str(TABLE), "--repo", str(REPO_ROOT))
    assert lines and lines[0] == "pass", "\n".join(lines)
    assert code == 0

    rows = table_rows(read_text(TABLE))
    # retro-check.py reads a backticked `none` as none, so count it the same way.
    enforced = [row for row in rows if row[2].strip("`") != "none"]
    unenforced = [row for row in rows if row[2].strip("`") == "none"]
    assert len(enforced) >= 2, "need at least two enforced rows"
    assert len(unenforced) >= 1, "need at least one `none` row"
    for row in enforced:
        assert row[2].startswith("`") and row[2].endswith("`"), row
        assert row[4].endswith(": fails"), row
    for row in unenforced:
        assert row[3] == "docs" and row[4] == "—", row
