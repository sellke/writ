#!/usr/bin/env python3
"""Wiring assertions for spec `2026-10-25-repro-first-bug-fixing`.

The spec ships markdown, so these checks read the files as text. Each test
pins one row of the spec's Removal Inventory, so a partial removal fails.

Story 2 (the tdd-cycle bug path and the config row):

- `skills/tdd-cycle/SKILL.md` holds `### Bug fixes: repro first` right after
  `### Staying honest`, with the `- **Repro First:** off` skip line, the
  recognition rule and its deciding test, and the surface rule (AC-2.1).
- That section's steps require a valid red, a test-only repro commit with a
  `Repro:` trailer, a fix commit that leaves the repro's test files alone,
  the `python3 scripts/repro-order.py check` command, and the `Repro: none`
  escape (AC-2.2).
- The When to Use bug bullet names the section, and the Examples bug example
  shows the repro commit, the fix commit, and a `repro-order: pass` line in
  place of the former `parseDate('')` example (AC-2.3).
- `.writ/docs/config-format.md` has a `Repro First` row in Supported Keys and
  a `## Repro First` section after `## Reviewer Filters` (AC-2.4). Both are
  pinned by presence and order, not adjacency, so a later switch can follow.
- `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` passes (AC-2.5).
  The rest of AC-2.5 (the plain-prose scan, `gen-platform-trees.py --check`,
  the full suites, `bash scripts/eval.sh`) is the verification run.

Stories 3 and 4 extend this file with the coding agent's `### Repro` block,
the consumer lines, and the cherry-pick paragraph.

Run: uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py -q
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

SKILL_REL = "skills/tdd-cycle/SKILL.md"
CONFIG_FORMAT_REL = ".writ/docs/config-format.md"
LINT_REL = "scripts/lint-skill.sh"

BUG_HEADING = "### Bug fixes: repro first"
STAYING_HONEST = "### Staying honest"
WHEN_TO_USE = "## When to Use"
EXAMPLES = "## Examples"

# The exact config line. Story 1's reader matches it at the start of a line.
SKIP_LINE = "- **Repro First:** off"
CHECK_COMMAND = "python3 scripts/repro-order.py check"
NO_REPRO_LEAD = "No repro possible"
OLD_BUG_EXAMPLE = "parseDate('')"

SUPPORTED_KEYS = "## Supported Keys"
CONFIG_HEADING = "## Repro First"
CONFIG_ROW_PREFIX = "| `Repro First` |"
# Order only: later switches may add sections after this one.
CONFIG_PREV_SECTION = "## Reviewer Filters"
CONFIG_CHECK_COMMAND = "python3 scripts/repro-order.py check --base <rev>"

HEADING = re.compile(r"^(#{1,6}) \S")
FENCE = re.compile(r"^\s*```")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read(rel: str) -> str:
    path = REPO_ROOT / rel
    assert path.exists(), "%s does not exist" % rel
    return path.read_text(encoding="utf-8")


def headings(text: str) -> List[str]:
    """Heading lines outside code fences, in order."""
    out = []  # type: List[str]
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and HEADING.match(line):
            out.append(line.rstrip())
    return out


def section(text: str, heading: str) -> str:
    """Text under `heading` (exact line) up to the next heading of the same or
    a higher level, ignoring `#` lines inside code fences. Fails the test when
    the heading is absent."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.rstrip() == heading]
    if not starts:
        pytest.fail("heading not found: %r" % heading)
    out = []  # type: List[str]
    in_fence = False
    for line in lines[starts[0] + 1:]:
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            m = HEADING.match(line)
            if m and len(m.group(1)) <= level:
                break
        out.append(line)
    return "\n".join(out)


def flat(block: str) -> str:
    """Collapse whitespace so a phrase wrapped across lines still matches."""
    return " ".join(block.split())


def table_rows(block: str) -> List[str]:
    """Data rows of the first markdown table in `block`."""
    rows = []  # type: List[str]
    in_table = False
    for line in block.splitlines():
        if line.startswith("|"):
            in_table = True
            rows.append(line)
        elif in_table:
            break
    return rows[2:]


def bug_section() -> str:
    return section(read(SKILL_REL), BUG_HEADING)


def assert_in_order(text: str, needles: List[str]) -> None:
    """Each needle occurs in `text`, and each first occurrence follows the
    previous one."""
    last = -1
    previous = "the start"
    for needle in needles:
        at = text.find(needle, last + 1)
        assert at > last, "%r not found after %r" % (needle, previous)
        last = at
        previous = needle


# ---------------------------------------------------------------------------
# Story 2: skills/tdd-cycle/SKILL.md
# ---------------------------------------------------------------------------


def test_section_present():
    """AC-2.1: one bug-path section, and it is the heading right after
    `### Staying honest`, inside How to Apply."""
    found = headings(read(SKILL_REL))
    assert found.count(BUG_HEADING) == 1, "expected one %r heading, found %r" % (
        BUG_HEADING,
        found,
    )
    assert STAYING_HONEST in found, "%r heading missing" % STAYING_HONEST
    after = found[found.index(STAYING_HONEST) + 1]
    assert after == BUG_HEADING, "heading after %r is %r, expected %r" % (
        STAYING_HONEST,
        after,
        BUG_HEADING,
    )
    assert found.index(BUG_HEADING) < found.index(EXAMPLES), "%r must sit before %r" % (
        BUG_HEADING,
        EXAMPLES,
    )


def test_skip_line():
    """AC-2.1: the section opens with the switch-off skip line and keeps the
    ordinary rule that a bug fix starts from a failing test."""
    sec = bug_section()
    assert SKIP_LINE in sec, "section does not name %r" % SKIP_LINE
    assert ".writ/config.md" in sec, "skip line does not name .writ/config.md"
    first_step = re.search(r"(?m)^1\. ", sec)
    assert first_step, "section has no numbered steps"
    assert sec.index(SKIP_LINE) < first_step.start(), "skip line must come before step 1"
    assert re.search(r"(?i)failing test", flat(sec[: first_step.start()])), (
        "skip line does not say a bug fix still starts from a failing test"
    )


def test_recognition_and_surface():
    """AC-2.1: recognition signals, the deciding test, and the surface rule."""
    text = flat(bug_section())
    for signal in ("`**Type:** Bug`", "`.writ/issues/bugs/`", "Origin"):
        assert signal in text, "recognition rule does not name %s" % signal
    assert re.search(r"(?i)existing behavior is wrong", text), (
        "recognition rule does not cover wording that existing behavior is wrong"
    )
    assert re.search(r"(?i)fail today", text) and re.search(r"(?i)code is missing", text), (
        "deciding test missing: a test can fail today because the code does the "
        "wrong thing, not because code is missing"
    )
    assert re.search(r"(?i)surface", text), "surface rule missing"
    for entry in ("CLI", "request", "component", "public function"):
        assert entry in text, "surface rule does not name the %r entry point" % entry
    assert re.search(r"(?i)unit test of the suspected cause is not the repro", text), (
        "surface rule does not exclude a unit test of the suspected cause"
    )
    assert re.search(r"(?i)nearest", text) and re.search(r"(?i)gap", text), (
        "surface rule does not cover the harness gap"
    )


def test_repro_fix_check_order():
    """AC-2.2: valid red, test-only repro commit with a `Repro:` trailer, a
    fix commit that leaves the repro's tests alone, then the check."""
    text = flat(bug_section())
    assert re.search(r"(?i)fail for the bug's reason", text), (
        "steps do not require the repro to fail for the bug's reason"
    )
    assert re.search(r"(?i)test files only", text), "repro commit is not limited to test files"
    assert re.search(r"(?i)trailer `Repro: ", text), "repro commit does not carry a `Repro:` trailer"
    assert re.search(r"(?i)last paragraph", text), (
        "the `Repro:` trailer's place (the message's last paragraph) is not stated"
    )
    assert re.search(r"(?i)repro's test files untouched", text), (
        "fix commit does not leave the repro's test files untouched"
    )
    assert re.search(r"(?i)reset to before it", text), "wrong-repro reset rule missing"
    assert CHECK_COMMAND in text, "section does not name %r" % CHECK_COMMAND
    assert_in_order(text, ["Commit the repro", "commit the fix", CHECK_COMMAND])


def test_no_repro_escape():
    """AC-2.2: `Repro: none` with a stated reason, and no `Repro:` trailer.
    Every assertion binds to the escape paragraph, from `No repro possible`
    to the end of the section."""
    sec = bug_section()
    start = sec.find(NO_REPRO_LEAD)
    assert start >= 0, "no-repro escape (%r) missing" % NO_REPRO_LEAD
    text = flat(sec[start:])
    assert "`Repro: none`" in text, "escape does not say `Repro: none`"
    for reason in ("nondeterministic", "environment", "no harness"):
        assert reason in text, "escape does not list %r as a reason" % reason
    assert re.search(r"(?i)\bwhy\b", text), "escape does not ask why there is no repro"
    assert re.search(r"(?i)no\s+`Repro:`\s+trailer", text), (
        "escape does not forbid the `Repro:` trailer"
    )
    assert re.search(r"(?i)regression test", text), "escape drops the regression test"


def test_when_to_use_points_here():
    """AC-2.3: the When to Use bug bullet names the section."""
    block = section(read(SKILL_REL), WHEN_TO_USE)
    bullets = [flat(b) for b in re.split(r"(?m)^- ", block) if b.strip()]
    bug = [b for b in bullets if re.search(r"(?i)\bbug\b", b) and "Bug fixes: repro first" in b]
    assert len(bug) == 1, "expected one When to Use bullet naming %r, found %r" % (
        BUG_HEADING,
        bullets,
    )
    assert BUG_HEADING in bug[0], "bug bullet does not name %r" % BUG_HEADING


def test_example_shows_bug_path():
    """AC-2.3: the bug example shows the repro commit with its `Repro:`
    trailer on its own indented line under the subject, the fix commit, and
    the check's pass line; the `parseDate('')` example is gone."""
    skill = read(SKILL_REL)
    assert OLD_BUG_EXAMPLE not in skill, "the former %s example is still present" % OLD_BUG_EXAMPLE
    lines = section(skill, EXAMPLES).splitlines()
    commits = [i for i, line in enumerate(lines) if line.startswith("commit:")]
    assert len(commits) == 2, "expected a repro and a fix commit line, found %r" % [
        lines[i] for i in commits
    ]
    repro_at, fix_at = commits
    for i in commits:
        assert "Repro:" not in lines[i], (
            "the `Repro:` trailer sits on the subject line, where the check "
            "would not find it in a one-line message: %r" % lines[i]
        )
    assert re.search(r"commit:\s+test\(", lines[repro_at]), (
        "repro commit is not type `test`: %r" % lines[repro_at]
    )
    trailers = [i for i, line in enumerate(lines) if re.match(r"^\s+Repro: \S", line)]
    assert trailers == [repro_at + 1], (
        "expected one indented `Repro:` trailer line right under the repro commit, found %r"
        % [lines[i] for i in trailers]
    )
    check = [i for i, line in enumerate(lines) if line.startswith("check:")]
    assert len(check) == 1, "expected one check line, found %r" % lines
    assert "repro-order: pass (1 repro, 1 fix commit(s))" in lines[check[0]], (
        "check line is not the pass summary: %r" % lines[check[0]]
    )
    red = [i for i, line in enumerate(lines) if line.startswith("red:")]
    green = [i for i, line in enumerate(lines) if line.startswith("green:")]
    assert red and red[-1] < repro_at, "no failing repro (`red:`) before the repro commit"
    assert green and repro_at < green[-1] < fix_at, "no passing run (`green:`) between the commits"
    assert fix_at < check[0], "the check line must follow the fix commit"


# ---------------------------------------------------------------------------
# Story 2: .writ/docs/config-format.md
# ---------------------------------------------------------------------------


def test_config_row():
    """AC-2.4: one `Repro First` row in Supported Keys, naming its consumers
    and linking its section."""
    rows = table_rows(section(read(CONFIG_FORMAT_REL), SUPPORTED_KEYS))
    ours = [r for r in rows if r.startswith(CONFIG_ROW_PREFIX)]
    assert len(ours) == 1, "expected one %r row, found %d" % (CONFIG_ROW_PREFIX, len(ours))
    row = ours[0]
    for needle in ("tdd-cycle", "coding-agent", "prototype", "implement-story (Gate 1)", "`off`"):
        assert needle in row, "row does not name %r: %r" % (needle, row)
    assert "(#repro-first)" in row, "row does not link the section"


def test_config_section():
    """AC-2.4: values, default, never detected or saved, and what `off`
    changes (Business Rule 9)."""
    config = read(CONFIG_FORMAT_REL)
    found = headings(config)
    assert found.count(CONFIG_HEADING) == 1, "expected one %r section" % CONFIG_HEADING
    assert CONFIG_PREV_SECTION in found, "%r section missing" % CONFIG_PREV_SECTION
    assert found.index(CONFIG_PREV_SECTION) < found.index(CONFIG_HEADING), (
        "%r must come after %r" % (CONFIG_HEADING, CONFIG_PREV_SECTION)
    )
    body = section(config, CONFIG_HEADING)
    assert re.search(r"(?m)^```markdown\n%s\n```$" % re.escape(SKIP_LINE), body), (
        "section does not open with a fenced %r example" % SKIP_LINE
    )
    text = flat(body)
    assert "`on`" in text and "`off`" in text, "values `on` and `off` not given"
    assert re.search(r"(?i)any case|case-insensitive", text), "values not stated case-insensitive"
    assert re.search(r"(?i)no line[^.]*means on|absent[^.]*means on", text), (
        "an absent key does not read as on"
    )
    assert re.search(r"(?i)never detected or offered for saving", text), (
        "section does not say the key is never detected or offered for saving"
    )
    assert "reason: repro-first value <value> read as on" in text, "unknown-value reason missing"
    assert re.search(r"(?i)first matching line wins", text), "first-match rule missing"
    # Business Rule 9: what `off` changes.
    assert re.search(r"(?i)ordinary cycle", text), "off does not say the ordinary cycle runs"
    assert "`Repro: off`" in text, "off does not say the report block reads `Repro: off`"
    assert "`/prototype`" in text and "`/implement-story`" in text, "off does not name both consumers"
    assert "cherry-pick" in text, "off does not cover the ordered-commits cherry-pick rule"
    assert CONFIG_CHECK_COMMAND in text, (
        "section does not name a runnable %r (argparse needs --base)" % CONFIG_CHECK_COMMAND
    )
    assert not re.search(r"repro-order\.py check`", text), (
        "section names `repro-order.py check` without --base, which exits 2"
    )
    for needle in ("`unverifiable`", "`reason: repro-first off`", "exits 0"):
        assert needle in text, "off does not state the check prints %s" % needle


# ---------------------------------------------------------------------------
# Story 2: lint
# ---------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not available")
def test_lint_skill_passes():
    """AC-2.5: `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` exits 0
    with `pass` on line 1."""
    proc = subprocess.run(
        ["bash", LINT_REL, SKILL_REL],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    first = proc.stdout.splitlines()[0] if proc.stdout else ""
    assert first == "pass", proc.stdout + proc.stderr
    assert proc.returncode == 0, proc.stdout + proc.stderr
