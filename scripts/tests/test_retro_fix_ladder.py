#!/usr/bin/env python3
"""Checks for spec `2026-10-25-retro-fix-ladder`.

Story 2: the seeded rule table `.writ/retros/rule-enforcers.md` has the
required heading and header, passes `scripts/retro-check.py --table`, and
holds at least two enforced rows and one `none` row (AC-2.1 to AC-2.4).

Story 3: `commands/retro.md` read as text. A step is the region from its
`### Step <n>:` heading to the next `### Step ` or `## ` heading, so the
`### Fix ladder` block after Step 5's routes belongs to Step 5 (AC-3.1 to
AC-3.5).

Run: uv run --python 3.9 pytest scripts/tests/test_retro_fix_ladder.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
RETRO_CHECK = REPO_ROOT / "scripts" / "retro-check.py"
TABLE = REPO_ROOT / ".writ" / "retros" / "rule-enforcers.md"
COMMAND = REPO_ROOT / "commands" / "retro.md"

TABLE_HEADING = "# Rule-to-Enforcer Table"
TABLE_HEADER = "| Rule | Written in | Enforcer | Rung | Proof | Since |"

BYTE_CEILING = 24960  # COMMAND_BYTE_BUDGET in scripts/eval-leanness.py
RUNGS = ["architecture", "types", "lint", "test", "docs"]
LADDER_GRAMMAR = "<rung>: no (<reason>); ...; <rung>: yes"
PROOF_PREFIX = "mistake <ref>; check "
PROOF_SUFFIX = "; result <fails|passes|pending>"
RETRO_CHECK_CALL = "python3 scripts/retro-check.py --retro <file>"
BANNED = ("signals.jsonl", "signal.py", "ADR-025", "--friction", "Writ friction")
# Literals scripts/eval.sh check_knowledge_consolidate pins in Step 7.
STEP7_PINS = ("read-only", "mutates no knowledge file")

# Recorded before the Story 3 edit; the story leaves it unchanged.
DESCRIPTION_LINE = (
    'description: "Read agent transcripts from a story, spec, or phase run and '
    "propose ranked fixes to the agent's environment (steering files, navigation "
    'hints, lint rules, skills, docs), never to the code."'
)
EXISTING_EXIT_CRITERIA = (
    '".writ/retros/YYYY-MM-DD-<scope>.md exists, names the scope and every '
    "transcript read, and lists each finding with a severity, a transcript path "
    "plus observable signal, the proposed change, and a disposition of applied, "
    'refreshed, issue, dismissed, or deferred"',
    '"the run edited no source file, no test, and no Writ command or agent file; '
    'every approved command or agent change was handed to /refresh-command"',
    '"no transcript body, prompt, or chain-of-thought appears in the retro file '
    'or in any file the run edited"',
)


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


# ---------------------------------------------------------------------------
# Story 3: commands/retro.md
# ---------------------------------------------------------------------------

def command_text() -> str:
    return read_text(COMMAND)


def unfenced(lines: List[str]) -> List[bool]:
    """True for each line outside a code fence (fence lines count as inside)."""
    out: List[bool] = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(False)
            continue
        out.append(not in_fence)
    return out


def step(text: str, n: int) -> str:
    """`### Step <n>:` through the line before the next `### Step ` or `## `
    heading. Headings inside code fences do not count."""
    lines = text.splitlines()
    outside = unfenced(lines)
    start = None
    for i, line in enumerate(lines):
        if not outside[i]:
            continue
        if start is None:
            if line.startswith("### Step %d:" % n):
                start = i
        elif line.startswith("### Step ") or line.startswith("## "):
            return "\n".join(lines[start:i])
    assert start is not None, "### Step %d not found in %s" % (n, COMMAND.name)
    return "\n".join(lines[start:])


def after_heading(text: str, heading: str) -> str:
    lines = text.splitlines()
    outside = unfenced(lines)
    for i, line in enumerate(lines):
        if outside[i] and line.strip() == heading:
            return "\n".join(lines[i + 1:])
    raise AssertionError("heading %r not found" % heading)


def paragraphs(text: str) -> List[str]:
    return [block for block in re.split(r"\n\s*\n", text) if block.strip()]


def frontmatter(text: str) -> List[str]:
    lines = text.splitlines()
    assert lines[0] == "---", "no frontmatter"
    return lines[1:lines.index("---", 1)]


def exit_criteria(text: str) -> List[str]:
    lines = frontmatter(text)
    start = lines.index("exit_criteria:")
    items: List[str] = []
    for line in lines[start + 1:]:
        if not line.startswith("  - "):
            break
        items.append(line[4:])
    return items


def test_fix_ladder_table_lists_five_rungs_in_order() -> None:
    """AC-3.1: the first table under Step 5's `### Fix ladder` heading has
    the rungs architecture, types, lint, test, docs in its first column, in
    order, each with a non-empty meaning cell and route cell. Routes follow
    Business Rule 5: config-only rungs `apply` or `issue`, test only
    `issue`, docs `apply`, `refresh`, or `knowledge`."""
    ladder = after_heading(step(command_text(), 5), "### Fix ladder")
    blocks = table_blocks(ladder)
    assert blocks, "no table under ### Fix ladder"
    header = [cell.strip() for cell in blocks[0][0].strip("|").split("|")]
    assert len(header) == 3, header
    rows = table_rows(ladder)
    assert [row[0].strip("`") for row in rows] == RUNGS
    for row in rows:
        assert len(row) == 3 and row[1] and row[2], row
    routes = {row[0].strip("`"): row[2] for row in rows}
    for rung in ("architecture", "types", "lint"):
        assert "`apply`" in routes[rung] and "`issue`" in routes[rung], routes[rung]
    assert "`issue`" in routes["test"] and "`apply`" not in routes["test"]
    for route in ("`apply`", "`refresh`", "`knowledge`"):
        assert route in routes["docs"], routes["docs"]


def test_step5_states_the_ladder_and_proof_grammar() -> None:
    """AC-3.1: Step 5 carries the Ladder grammar and a Proof grammar line
    that starts `mistake <ref>; check ` and ends `; result <fails|passes|pending>`;
    the example finding carries Rule, Rung, Ladder, Target, Change, Proof,
    and Route; `Never target source code or tests.` stays."""
    text = step(command_text(), 5)
    assert LADDER_GRAMMAR in text
    proof_lines = [line for line in text.splitlines()
                   if PROOF_PREFIX in line and PROOF_SUFFIX in line
                   and line.index(PROOF_PREFIX) < line.index(PROOF_SUFFIX)]
    assert proof_lines, "no Proof grammar line in Step 5"
    for field in ("Rule", "Rung", "Ladder", "Target", "Change", "Proof", "Route"):
        assert re.search(r"^\*\*%s:\*\* " % field, text, re.M), field
    assert "Never target source code or tests." in text


def test_step5_example_finding_passes_the_retro_check_grammar(tmp_path: Path) -> None:
    """AC-3.1: the Step 5 example, written to a retro file with a
    Disposition line, raises no fail reason in `retro-check.py`. Outside a
    git work tree its SHA cannot resolve, so the only reason is `no_git`."""
    text = step(command_text(), 5)
    match = re.search(r"```markdown\n(### F1 .*?)\n```", text, re.S)
    assert match, "no ```markdown example finding in Step 5"
    retro = tmp_path / "2026-01-01-example.md"
    retro.write_text("## Transcripts\n\n## Findings\n\n%s\n**Disposition:** issue\n"
                     % match.group(1), encoding="utf-8")
    code, lines = run_retro_check("--retro", str(retro), "--repo", str(tmp_path))
    assert lines[:2] == ["unverifiable", "reason: no_git"], "\n".join(lines)
    assert len(lines) == 3 and code == 0, "\n".join(lines)


def test_step6_runs_the_proof_and_restores_on_a_passing_check() -> None:
    """AC-3.2: Step 6 runs the proof after an Apply on architecture, types,
    or lint. A check that does not fail restores the file, sets `result
    passes`, and records `issue`; a check that cannot run sets `result
    pending` and records `issue`."""
    text = step(command_text(), 6)
    assert "architecture, types, or lint" in text
    lines = text.splitlines()
    assert any("does not fail" in line and "restore" in line
               and "`result passes`" in line and "`issue`" in line for line in lines)
    assert any("cannot run" in line and "`result pending`" in line
               and "`issue`" in line for line in lines)
    assert any("`result fails`" in line and "`applied`" in line for line in lines)


def test_step8_writes_the_checked_record_and_updates_the_table() -> None:
    """AC-3.2: Step 8 names `## Transcripts`, `## Findings`, `**Disposition:**`,
    `## Rule table changes`, the table path with its heading and header row,
    the Since value, and the `retro-check.py --retro` run; a second `fail`
    is reported with its reason lines."""
    text = step(command_text(), 8)
    for literal in ("`## Transcripts`", "`## Findings`", "`**Disposition:**`",
                    "`## Rule table changes`", "`.writ/retros/rule-enforcers.md`",
                    "`%s`" % TABLE_HEADING, "`%s`" % TABLE_HEADER,
                    "`<retro file name> F<n>`", "`%s`" % RETRO_CHECK_CALL):
        assert literal in text, literal
    assert any("second `fail`" in block and "reason lines" in block
               for block in paragraphs(text))
    # One row per rule: an applied fix replaces the rule's row, so a `none`
    # row never sits beside an enforced row for the same rule.
    assert any("replace the rule's row" in block and "otherwise add a row" in block
               for block in paragraphs(text))
    assert "each row this run added or replaced, or `none`" in text
    # retro-check.py matches Since against the retro file's basename, `.md` included.
    assert re.search(r"`\S+\.md F\d+`", text), "no Since example with the .md name"


def test_step3_renames_the_command_signal_and_counts_unenforced_rules() -> None:
    """AC-3.3: Step 3's signal row is `Writ command defect`, and a user
    correction against a rule whose enforcer is `none` counts on its own as
    a Repeated mistake."""
    text = step(command_text(), 3)
    first_cells = [row[0] for row in table_rows(text)]
    assert "**Writ command defect**" in first_cells, first_cells
    assert any("user correction" in line.lower()
               and "whose enforcer is `none`" in line
               and "counts on its own, as a Repeated mistake" in line
               for line in text.splitlines())


def test_step4_reads_the_table_before_ranking() -> None:
    """AC-3.3: Step 4 reads `.writ/retros/rule-enforcers.md` before the
    severity table and names **enforcer did not hold** in the same
    paragraph as **fix did not hold**."""
    text = step(command_text(), 4)
    path = "`.writ/retros/rule-enforcers.md`"
    assert path in text
    assert text.index(path) < text.index("| Severity | Criteria |")
    assert any("**fix did not hold**" in block and "**enforcer did not hold**" in block
               for block in paragraphs(text))
    # Contract item 4: one event against an enforced row is reported; a single
    # correction or mistake that matches no row at all is dropped.
    assert any("**enforcer did not hold**" in block and "even for a single event" in block
               for block in paragraphs(text))
    assert "Drop single user corrections and mistakes that match no row." in text


def test_retired_tokens_absent_and_pins_kept() -> None:
    """AC-3.4: no friction-signal remnant, Step 7 keeps the two literals
    `check_knowledge_consolidate` pins, and the file is under the byte
    ceiling."""
    text = command_text()
    for token in BANNED:
        assert token not in text, token
    step7 = step(text, 7)
    for literal in STEP7_PINS:
        assert literal in step7, literal
    assert len(COMMAND.read_bytes()) < BYTE_CEILING


def test_frontmatter_keeps_description_and_adds_two_exit_criteria() -> None:
    """AC-3.5: `description` is unchanged, `exit_criteria` keeps its three
    lines and adds the proof line and the retro-check line, and `outcome`
    names the highest-rung fix and the rule table."""
    text = command_text()
    lines = frontmatter(text)
    assert DESCRIPTION_LINE in lines
    items = exit_criteria(text)
    for line in EXISTING_EXIT_CRITERIA:
        assert line in items, line
    assert len(items) == 5, items
    new = [item for item in items if item not in EXISTING_EXIT_CRITERIA]
    assert any("cites a proof run against a real past mistake" in item for item in new)
    assert any("retro-check.py --retro" in item for item in new)
    outcome = [line for line in lines if line.startswith("outcome:")]
    assert outcome and "highest rung that works" in outcome[0]
    assert "rule table" in outcome[0]
