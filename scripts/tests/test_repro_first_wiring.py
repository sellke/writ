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

Story 3 (the coding agent's report, `agents/coding-agent.md`):

- Implementation Requirement 1 names the skill's `### Bug fixes: repro first`
  section without a second `Read` of the skill, and Requirement 3 has one
  sentence that puts a `Ref:` footer on the repro and fix commits under
  `/implement-story` and none on `/prototype` commits (AC-3.1).
- Output Requirements has a `### Repro` item, and the Output Format's
  `### Repro` block sits between `### Self-Check Results` and
  `### Boundary Compliance` inside a balanced four-backtick fence. Its
  bug-with-a-repro form carries the seven field labels in order, the
  `Commits` arrow shape Story 4 parses, and the 20-line and 10-line output
  caps (AC-3.2).
- The three short forms: `Repro: none` followed by `Regression test`,
  `Kind: not a bug fix`, and `Repro: off` (AC-3.3).
- The generated copies `claude-code/agents/writ-coder.md` and
  `codex/agents/coding-agent.toml` carry the same block, generator rewrites
  allowed, and `python3 scripts/gen-platform-trees.py --check` passes
  (AC-3.4).
- The Story 3 tests above pass in the full pytest run; the bash test loop
  and `bash scripts/eval.sh` are the rest of the verification run (AC-3.5).

Story 4 (the consumers and the ordered-commits paragraph):

- `commands/prototype.md` Step 3 principle 1 names the bug path in
  `skills/tdd-cycle/SKILL.md`, and a `**Bug path:**` line right after the
  integration paragraph records the base, brings the named commits in with
  `git cherry-pick`, oldest first, not through `git apply`, runs
  `python3 scripts/repro-order.py check`, and sends its output and the
  failing-then-passing output to the Step 5 summary, where `fail` reads
  "Prototype Complete (with issues)" (AC-4.1).
- `commands/implement-story.md` Gate 1 has a `**Bug path:**` line right after
  `**Report:**`: base recorded before the story's first Gate 1 spawn and
  reused on recodes, check re-run, a `repro-order:` line in the Step 4
  report, `fail` → `⚠️ DEGRADED` with its `reason:` lines, `unverifiable` or
  exit 2 with its stderr cause prints and continues. `gate1_coding` stays
  `verification: prose-only` and `scripts/verdict-provenance.py check` passes
  (AC-4.2).
- Both `**Bug path:**` lines fire only when the report's `### Repro` block
  names commits, and never read `.writ/config.md`; the agent's `Repro: off`
  form names no commits. Each command names `repro-order.py` only in that
  line, so Step 2.5, Gate 0, Gate 2.5, Gate 3, and Step 4 carry none of it
  (AC-4.1, AC-4.2).
- `skills/subagent-worktree-integration/SKILL.md` step 3 ends with the
  "Ordered commits" paragraph: `git cherry-pick`, oldest first, instead of
  copying; on a conflict `git cherry-pick --abort`, copy the files, and say
  the order was lost. `bash scripts/lint-skill.sh` passes on it (AC-4.3).
- `test_removal_inventory_row` has one case per row of the spec's
  `## Removal Inventory` (with the When to Use bullet added to the tdd-cycle
  row, drift DEV-007); its id and failure message name the row. The
  generated-trees row is `test_generated_trees_current` (AC-4.4).
- `test_generated_trees_current` is the `gen-platform-trees.py --check` part
  of AC-4.5; the full pytest run, the bash test loop, and
  `bash scripts/eval.sh` are the rest of the verification run (AC-4.5).

Run: uv run --python 3.9 pytest scripts/tests/test_repro_first_wiring.py -q
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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

AGENT_REL = "agents/coding-agent.md"
CLAUDE_CODER_REL = "claude-code/agents/writ-coder.md"
CODEX_CODER_REL = "codex/agents/coding-agent.toml"
GEN_REL = "scripts/gen-platform-trees.py"

REQ1_LEAD = "1. **Follow TDD**"
REQ3_LEAD = "3. **Small commits**"
SKILL_READ = "Read skills/tdd-cycle/SKILL.md"
REF_FOOTER = "Ref: .writ/specs/<spec-id>/user-stories/<story-file>.md"

OUTPUT_REQUIREMENTS = "## Output Requirements"
OUTPUT_REQUIREMENTS_END = "Do NOT mark the story as complete"
OUTPUT_FORMAT = "## Output Format"
OUTPUT_FORMAT_END = "## Iteration Cap"
REPRO_HEADING = "### Repro"
SELF_CHECK_HEADING = "### Self-Check Results"
BOUNDARY_HEADING = "### Boundary Compliance"

# Form labels are italic lines ending in a colon, as `_Bug with a repro:_`.
FORM_LABEL = re.compile(r"^_(.+):_$")
FORM_BUG = "Bug with a repro"
FORM_NO_REPRO = "Bug without a repro"
FORM_NOT_BUG = "Not a bug fix"
FORM_OFF = "Switch off"

# The seven field labels of the bug-with-a-repro form, in the technical
# spec's order (Kind, Surface, Command, Commits, Before, After, Check).
BUG_FIELDS = [
    "- **Kind:** bug: ",
    "- **Surface:** ",
    "- **Command:** ",
    "- **Commits:** ",
    "- **Before the fix (failing):**",
    "- **After the fix (passing):**",
    "- **Check:** ",
]
# Story 4's consumers read the SHAs from this exact shape.
COMMITS_LINE = re.compile(r"^- \*\*Commits:\*\* repro `\[sha\]` → fix `\[sha\]`\[, `\[sha\]`\]$")

PROTOTYPE_REL = "commands/prototype.md"
IMPLEMENT_STORY_REL = "commands/implement-story.md"
INTEGRATION_REL = "skills/subagent-worktree-integration/SKILL.md"
CONTRACT_REL = ".writ/docs/agent-cli-contract.md"
CONTRACT_TEST_REL = "scripts/tests/test_agent_cli_contract.py"
SCRIPT_REL = "scripts/repro-order.py"
SCRIPT_TEST_REL = "scripts/tests/test_repro_order.py"
WIRING_REL = "scripts/tests/test_repro_first_wiring.py"
VERDICT_REL = "scripts/verdict-provenance.py"

STEP25 = "### Step 2.5: Diverge & Choose"
STEP3 = "### Step 3: Spawn Coding Agent"
STEP5 = "### Step 5: Output Summary"
GATE0 = "#### Gate 0: Architecture Check (Pre-Implementation)"
GATE1 = "#### Gate 1: Coding Agent (TDD Implementation)"
GATE25 = "#### Gate 2.5: Change Surface Classification"
GATE3 = "#### Gate 3: Review Agent"
STEP4 = "### Step 4: Story Completion"
INTEGRATION_STEP3 = "### 3. Copy changed and created files into the main checkout"

PRINCIPLE1_LEAD = "1. **TDD**"
INTEGRATION_LEAD = "The change is done only when it is in the user's checkout."
REPORT_LEAD = "**Report:**"
BLOCKED_LEAD = "**On `STATUS: BLOCKED`:**"
BUG_PATH_LEAD = "**Bug path:**"
ORDERED_LEAD = "**Ordered commits.**"
SCRIPT_NAME = "repro-order.py"
# Both consumers run the check from the checkout's root against the recorded base.
CONSUMER_CHECK = "`python3 scripts/repro-order.py check --repo . --base <that SHA>`"
WITH_ISSUES = "Prototype Complete (with issues)"
DEGRADED = "⚠️ DEGRADED"
# A `### Repro` block names commits only in its bug-with-a-repro form.
COMMITS_FIELD = "- **Commits:** "

HEADING = re.compile(r"^(#{1,6}) \S")
FENCE = re.compile(r"^\s*```")
# A CommonMark fence line: up to three spaces, a run of backticks or tildes,
# then an info string.
FENCE_RUN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


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


def fences(lines: List[str]) -> List[Tuple[int, Optional[int]]]:
    """(open, close) line indexes of each fenced block under CommonMark rules:
    a closer uses the opener's character, is at least as long, and has no info
    string. An unclosed fence has close None."""
    out = []  # type: List[Tuple[int, Optional[int]]]
    open_at = None  # type: Optional[int]
    char, size = "", 0
    for i, line in enumerate(lines):
        m = FENCE_RUN.match(line)
        if not m:
            continue
        run, info = m.group(1), m.group(2)
        if open_at is None:
            open_at, char, size = i, run[0], len(run)
        elif run[0] == char and len(run) >= size and not info.strip():
            out.append((open_at, i))
            open_at = None
    if open_at is not None:
        out.append((open_at, None))
    return out


def slice_lines(text: str, start: str, end: str) -> List[str]:
    """Lines after the first line equal to `start`, up to the first later line
    that starts with `end`. Fails the test when either is absent."""
    lines = text.splitlines()
    if start not in lines:
        pytest.fail("line not found: %r" % start)
    first = lines.index(start) + 1
    for i in range(first, len(lines)):
        if lines[i].startswith(end):
            return lines[first:i]
    pytest.fail("no line starting with %r after %r" % (end, start))
    return []


def requirement(text: str, lead: str) -> str:
    """The one Implementation Requirement line that starts with `lead`."""
    found = [line for line in text.splitlines() if line.startswith(lead)]
    assert len(found) == 1, "expected one line starting %r, found %r" % (lead, found)
    return found[0]


def sentences(line: str) -> List[str]:
    return re.split(r"(?<=[.!?])\s+(?=[A-Z`])", line)


def repro_block(text: str) -> List[str]:
    """Lines of the `### Repro` block: from its heading up to the next `### `
    heading. The heading must occur once as a line of its own."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line == REPRO_HEADING]
    assert len(starts) == 1, "expected one %r line, found %d" % (REPRO_HEADING, len(starts))
    out = [lines[starts[0]]]
    for line in lines[starts[0] + 1:]:
        if line.startswith("### "):
            break
        out.append(line)
    return out


def repro_forms(block: List[str]) -> List[Tuple[str, List[str]]]:
    """(label, non-blank lines) for each form, split on the italic label
    lines."""
    forms = []  # type: List[Tuple[str, List[str]]]
    for line in block:
        m = FORM_LABEL.match(line)
        if m:
            forms.append((m.group(1), []))
        elif forms and line.strip():
            forms[-1][1].append(line)
    return forms


def form(block: List[str], name: str) -> List[str]:
    found = [body for label, body in repro_forms(block) if label.startswith(name)]
    assert len(found) == 1, "expected one %r form, found labels %r" % (
        name,
        [label for label, _ in repro_forms(block)],
    )
    return found[0]


def agent_repro_block() -> List[str]:
    return repro_block("\n".join(slice_lines(read(AGENT_REL), OUTPUT_FORMAT, OUTPUT_FORMAT_END)))


def unrewrite(text: str) -> str:
    """Undo the platform-term rewrites the generator may apply to a copy."""
    return text.replace("${CLAUDE_PLUGIN_ROOT}/", "").replace("/writ:", "/")


def paragraphs(block: str) -> List[str]:
    """Blank-line separated paragraphs of `block`, stripped, empty ones
    dropped."""
    return [p.strip() for p in re.split(r"\n\s*\n", block) if p.strip()]


def one_paragraph(block: str, lead: str, where: str) -> str:
    """The one paragraph of `block` that starts with `lead`."""
    found = [p for p in paragraphs(block) if p.startswith(lead)]
    assert len(found) == 1, "expected one paragraph starting %r in %s, found %d" % (
        lead,
        where,
        len(found),
    )
    return found[0]


def paragraph_after(block: str, lead: str, where: str) -> str:
    """The paragraph right after the one that starts with `lead`."""
    paras = paragraphs(block)
    at = [i for i, p in enumerate(paras) if p.startswith(lead)]
    assert len(at) == 1, "expected one paragraph starting %r in %s, found %d" % (
        lead,
        where,
        len(at),
    )
    assert at[0] + 1 < len(paras), "nothing follows %r in %s" % (lead, where)
    return paras[at[0] + 1]


def run_lint(rel: str) -> None:
    """`bash scripts/lint-skill.sh <rel>` exits 0 with `pass` on line 1."""
    proc = subprocess.run(
        ["bash", LINT_REL, rel],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    first = proc.stdout.splitlines()[0] if proc.stdout else ""
    assert first == "pass", proc.stdout + proc.stderr
    assert proc.returncode == 0, proc.stdout + proc.stderr


def prototype_step3() -> str:
    return section(read(PROTOTYPE_REL), STEP3)


def gate1() -> str:
    return section(read(IMPLEMENT_STORY_REL), GATE1)


def bug_path_line(rel: str, heading: str) -> str:
    return one_paragraph(section(read(rel), heading), BUG_PATH_LEAD, "%s %s" % (rel, heading))


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
    run_lint(SKILL_REL)


# ---------------------------------------------------------------------------
# Story 3: agents/coding-agent.md Implementation Requirements
# ---------------------------------------------------------------------------


def test_requirement_1_names_bug_path():
    """AC-3.1: Requirement 1 names the skill's bug-path section and the skill
    file, and the agent still reads the skill once."""
    agent = read(AGENT_REL)
    line = requirement(agent, REQ1_LEAD)
    named = [s for s in sentences(line) if BUG_HEADING in s]
    assert len(named) == 1, "Requirement 1 has no sentence naming %r: %r" % (BUG_HEADING, line)
    assert SKILL_REL in named[0], "the bug-path sentence does not name %s: %r" % (
        SKILL_REL,
        named[0],
    )
    assert agent.count(SKILL_READ) == 1, "expected one %r, found %d" % (
        SKILL_READ,
        agent.count(SKILL_READ),
    )
    assert BUG_HEADING in headings(read(SKILL_REL)), "%s has no %r heading" % (
        SKILL_REL,
        BUG_HEADING,
    )


def test_requirement_3_ref_footer():
    """AC-3.1: one Requirement 3 sentence puts the `Ref:` footer on the repro
    and fix commits under `/implement-story` and none on `/prototype`
    commits."""
    line = requirement(read(AGENT_REL), REQ3_LEAD)
    found = [s for s in sentences(line) if REF_FOOTER in s]
    assert len(found) == 1, "expected one sentence with %r in Requirement 3: %r" % (
        REF_FOOTER,
        line,
    )
    sentence = found[0]
    assert "`/implement-story`" in sentence, "footer sentence does not name `/implement-story`"
    assert re.search(r"(?i)repro and fix commits", sentence), (
        "footer sentence does not cover both the repro and the fix commits"
    )
    assert re.search(r"(?i)last paragraph", sentence), (
        "footer sentence does not put `Ref:` in the message's last paragraph"
    )
    assert re.search(r"(?i)on the repro commit, its `Repro:` trailer", sentence), (
        "footer sentence does not limit the `Repro:` trailer to the repro commit"
    )
    assert re.search(r"`/prototype` commits carry no `Ref:` footer", sentence), (
        "footer sentence does not say `/prototype` commits carry no `Ref:` footer"
    )


# ---------------------------------------------------------------------------
# Story 3: agents/coding-agent.md Output Requirements and Output Format
# ---------------------------------------------------------------------------


def test_output_requirements_repro_item():
    """AC-3.2: Output Requirements has one `### Repro` item, present in every
    report in one of four forms."""
    lines = slice_lines(read(AGENT_REL), OUTPUT_REQUIREMENTS, OUTPUT_REQUIREMENTS_END)
    items = [line for line in lines if line.startswith("- ") and REPRO_HEADING + "*" in line]
    assert len(items) == 1, "expected one Output Requirements item naming %r, found %r" % (
        REPRO_HEADING,
        items,
    )
    text = flat(items[0])
    assert re.search(r"(?i)every report", text), "the item does not say every report has it"
    assert re.search(r"(?i)four forms", text), "the item does not name the four forms"


def test_output_format_fence_and_position():
    """AC-3.2: the Output Format sits in a four-backtick fence that closes
    after `### Summary`, every fence in the file closes, and `### Repro`
    falls between Self-Check Results and Boundary Compliance."""
    lines = read(AGENT_REL).splitlines()
    blocks = fences(lines)
    unclosed = [lines[o] for o, c in blocks if c is None]
    assert not unclosed, "unclosed fence(s) in %s: %r" % (AGENT_REL, unclosed)
    start = lines.index(OUTPUT_FORMAT)
    end = lines.index(OUTPUT_FORMAT_END)
    inside = [(o, c) for o, c in blocks if start < o < end]
    assert len(inside) == 1, "expected one fenced block under %r, found %r" % (
        OUTPUT_FORMAT,
        [lines[o] for o, _ in inside],
    )
    o, c = inside[0]
    assert lines[o] == "````markdown", "Output Format opens with %r, expected ````markdown" % lines[o]
    body = lines[o + 1:c]
    for heading in (SELF_CHECK_HEADING, REPRO_HEADING, BOUNDARY_HEADING, "### Summary"):
        assert heading in body, "%r is not inside the Output Format fence" % heading
    assert (
        body.index(SELF_CHECK_HEADING) < body.index(REPRO_HEADING) < body.index(BOUNDARY_HEADING)
    ), "%r must sit after %r and before %r" % (REPRO_HEADING, SELF_CHECK_HEADING, BOUNDARY_HEADING)


def test_output_format_bug_with_repro_form():
    """AC-3.2: the bug-with-a-repro form carries Kind, Surface, Command,
    Commits, the failing output (at most 20 lines), the passing output (at
    most 10 lines, same command), and Check, in that order; Commits keeps the
    `repro [sha] → fix [sha]` shape."""
    block = agent_repro_block()
    labels = [label for label, _ in repro_forms(block)]
    for name in (FORM_BUG, FORM_NO_REPRO, FORM_NOT_BUG, FORM_OFF):
        assert any(label.startswith(name) for label in labels), (
            "form %r missing; labels: %r" % (name, labels)
        )
    body = form(block, FORM_BUG)
    at = []
    for field in BUG_FIELDS:
        hits = [i for i, line in enumerate(body) if line.startswith(field)]
        assert len(hits) == 1, "expected one %r line in the bug form, found %d" % (field, len(hits))
        at.append(hits[0])
    assert at == sorted(at), "field order is %r, expected %r" % (
        [body[i] for i in sorted(at)],
        BUG_FIELDS,
    )
    commits = body[at[3]]
    assert COMMITS_LINE.match(commits), "Commits line changed shape: %r" % commits

    def output_after(index: int) -> str:
        assert body[index + 1].strip() == "```text", "no ```text fence under %r" % body[index]
        assert body[index + 3].strip() == "```", "the output fence under %r does not close" % body[index]
        return body[index + 2]

    assert re.search(r"at most 20 lines", output_after(at[4])), "failing output cap is not 20 lines"
    passing = output_after(at[5])
    assert re.search(r"at most 10 lines", passing), "passing output cap is not 10 lines"
    assert re.search(r"(?i)same command", passing), "passing output is not tied to the same command"
    assert "repro-order.py check" in body[at[6]], "Check does not name repro-order.py check"


def test_output_format_short_forms():
    """AC-3.3: `Repro: none: <reason>` followed by `Regression test`,
    `Kind: not a bug fix: <reason>`, and `Repro: off`, none of them naming
    commits."""
    block = agent_repro_block()
    assert form(block, FORM_NO_REPRO) == [
        "- **Kind:** bug: [signal]",
        "- **Repro:** none: [reason]",
        "- **Regression test:** [path, or none]",
    ], "bug-without-a-repro form changed: %r" % form(block, FORM_NO_REPRO)
    assert form(block, FORM_NOT_BUG) == ["- **Kind:** not a bug fix: [reason]"], (
        "not-a-bug-fix form changed: %r" % form(block, FORM_NOT_BUG)
    )
    assert form(block, FORM_OFF) == ["- **Repro:** off"], (
        "switch-off form changed: %r" % form(block, FORM_OFF)
    )
    off_label = [label for label, _ in repro_forms(block) if label.startswith(FORM_OFF)][0]
    assert SKIP_LINE in off_label, "switch-off form does not name %r" % SKIP_LINE


# ---------------------------------------------------------------------------
# Story 3: generated copies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", [CLAUDE_CODER_REL, CODEX_CODER_REL])
def test_generated_copy_carries_repro_block(rel):
    """AC-3.4: the generated copy carries the `### Repro` block as rendered
    from agents/coding-agent.md, with its seven field labels and four forms;
    generator rewrites of platform terms are allowed."""
    source = agent_repro_block()
    copy = repro_block(read(rel))
    assert [unrewrite(line) for line in copy] == [unrewrite(line) for line in source], (
        "%s `### Repro` block differs from %s; run python3 %s" % (rel, AGENT_REL, GEN_REL)
    )
    text = "\n".join(copy)
    for field in BUG_FIELDS:
        assert field in text, "%s lacks field %r" % (rel, field)
    for name in (FORM_BUG, FORM_NO_REPRO, FORM_NOT_BUG, FORM_OFF):
        assert any(label.startswith(name) for label, _ in repro_forms(copy)), (
            "%s lacks form %r" % (rel, name)
        )


def test_generated_trees_current():
    """AC-3.4, AC-4.5: `python3 scripts/gen-platform-trees.py --check` exits
    0."""
    proc = subprocess.run(
        [sys.executable, GEN_REL, "--check"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    first = proc.stdout.splitlines()[0] if proc.stdout else ""
    assert proc.returncode == 0 and first == "pass", proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Story 4: commands/prototype.md Step 3
# ---------------------------------------------------------------------------


def test_prototype_principle_1_names_bug_path():
    """AC-4.1: Step 3 principle 1 keeps the TDD instruction and names the bug
    path in skills/tdd-cycle/SKILL.md, a failing repro committed before the
    fix."""
    line = requirement(prototype_step3(), PRINCIPLE1_LEAD)
    assert "tests first covering core behavior and obvious edge cases" in line, (
        "principle 1 lost its TDD instruction: %r" % line
    )
    assert "bug path in `%s`" % SKILL_REL in line, (
        "principle 1 does not name the bug path in %s: %r" % (SKILL_REL, line)
    )
    assert re.search(r"(?i)failing repro committed before the fix", line), (
        "principle 1 does not say the failing repro is committed before the fix: %r" % line
    )
    assert BUG_HEADING in headings(read(SKILL_REL)), "%s has no %r heading" % (SKILL_REL, BUG_HEADING)


def test_prototype_bug_path_line():
    """AC-4.1: the `**Bug path:**` line follows the integration paragraph,
    records the base before spawning, brings the named commits in with
    `git cherry-pick`, oldest first, not through `git apply` (which drops
    commits, so the check would fail `no_repro_commit`), runs the check, and
    puts its output and the failing-then-passing output in the Step 5
    summary; `fail` makes it "Prototype Complete (with issues)"."""
    step = prototype_step3()
    line = one_paragraph(step, BUG_PATH_LEAD, STEP3)
    assert paragraph_after(step, INTEGRATION_LEAD, STEP3) == line, (
        "the %s line does not follow the integration paragraph" % BUG_PATH_LEAD
    )
    assert_in_order(
        line,
        [
            "`git rev-parse HEAD`",
            "before spawning",
            "names commits",
            "`git cherry-pick`",
            "oldest first",
            "Ordered commits",
            "not through `git apply`",
            CONSUMER_CHECK,
            "failing-then-passing output",
            "Step 5 summary",
            "`fail`",
            '"%s"' % WITH_ISSUES,
        ],
    )
    assert WITH_ISSUES in section(read(PROTOTYPE_REL), STEP5), (
        "Step 5 has no %r summary for the line to point at" % WITH_ISSUES
    )


# ---------------------------------------------------------------------------
# Story 4: commands/implement-story.md Gate 1
# ---------------------------------------------------------------------------


def test_gate1_bug_path_line():
    """AC-4.2: the `**Bug path:**` line sits between `**Report:**` and the
    `STATUS: BLOCKED` handling, records the base before the story's first
    Gate 1 spawn and reuses it on recodes (a recode's fresh base would hold no
    repro and fail `no_repro_commit`), re-runs the check after integration,
    prints `repro-order:` in the Step 4 report, maps `fail` to `⚠️ DEGRADED`
    with its `reason:` lines, and lets `unverifiable` or exit 2 print and
    continue."""
    gate = gate1()
    line = one_paragraph(gate, BUG_PATH_LEAD, GATE1)
    assert paragraph_after(gate, REPORT_LEAD, GATE1) == line, (
        "the %s line does not follow %s" % (BUG_PATH_LEAD, REPORT_LEAD)
    )
    assert paragraph_after(gate, BUG_PATH_LEAD, GATE1).startswith(BLOCKED_LEAD), (
        "the %s handling no longer follows the %s line" % (BLOCKED_LEAD, BUG_PATH_LEAD)
    )
    assert_in_order(
        line,
        [
            "`git rev-parse HEAD`",
            "before the story's first Gate 1 spawn",
            "reuse it on recodes",
            "names commits",
            CONSUMER_CHECK,
            "after integration",
            "`repro-order:`",
            "Step 4 report",
            "`fail` marks the story `%s`" % DEGRADED,
            "`reason:` lines",
            "`unverifiable`, or exit 2 with its stderr cause, prints and continues",
        ],
    )
    after = line[line.index("`unverifiable`"):]
    assert "DEGRADED" not in after, "`unverifiable` must not mark the story DEGRADED: %r" % after
    command = read(IMPLEMENT_STORY_REL)
    assert DEGRADED in command.replace(gate, ""), (
        "%s is not a state the command defines outside Gate 1" % DEGRADED
    )


def test_gate1_stays_prose_only():
    """AC-4.2: the `gates:` frontmatter keeps `gate1_coding` as
    `verification: prose-only` with no `script:`, and
    `scripts/verdict-provenance.py check` passes, so no gate names both a
    script and prose-only."""
    frontmatter = read(IMPLEMENT_STORY_REL).split("\n---\n", 1)[0] + "\n"
    entry = re.search(r"(?m)^  - id: gate1_coding\n((?:    \S.*\n)*)", frontmatter)
    assert entry, "gates: has no gate1_coding entry"
    assert entry.group(1).split("\n")[:-1] == ["    verification: prose-only"], (
        "gate1_coding changed: %r" % entry.group(1)
    )
    proc = subprocess.run(
        [sys.executable, VERDICT_REL, "check", "--command", IMPLEMENT_STORY_REL],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    first = proc.stdout.splitlines()[0] if proc.stdout else ""
    assert proc.returncode == 0 and first == "pass", proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Story 4: both consumers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel,heading",
    [
        pytest.param(PROTOTYPE_REL, STEP3, id="prototype-step-3"),
        pytest.param(IMPLEMENT_STORY_REL, GATE1, id="implement-story-gate-1"),
    ],
)
def test_bug_path_fires_only_on_named_commits(rel, heading):
    """AC-4.1, AC-4.2: the line runs the check only when the report's
    `### Repro` block names commits, and never reads `.writ/config.md`. Only
    the agent's bug-with-a-repro form names commits, so a `Repro: off`,
    `Repro: none`, or not-a-bug report never triggers it."""
    line = bug_path_line(rel, heading)
    cond = re.search(r"When the (agent's|report's) `### Repro` block names commits", line)
    assert cond, "%s %s does not limit the check to a report that names commits: %r" % (
        rel,
        heading,
        line,
    )
    assert cond.start() < line.index(CONSUMER_CHECK), "the condition must come before the check"
    for needle in (".writ/config.md", "Repro First"):
        assert needle not in line, "%s %s reads the switch itself (%r)" % (rel, heading, needle)
    block = agent_repro_block()
    assert any(f.startswith(COMMITS_FIELD) for f in form(block, FORM_BUG)), (
        "the bug-with-a-repro form no longer names commits"
    )
    for name in (FORM_OFF, FORM_NO_REPRO, FORM_NOT_BUG):
        assert not any(COMMITS_FIELD.strip() in f for f in form(block, name)), (
            "the %r form names commits, so it would trigger the check" % name
        )


@pytest.mark.parametrize(
    "rel,owner,others",
    [
        pytest.param(PROTOTYPE_REL, STEP3, [STEP25], id="prototype"),
        pytest.param(IMPLEMENT_STORY_REL, GATE1, [GATE0, GATE25, GATE3, STEP4], id="implement-story"),
    ],
)
def test_bug_path_only_in_its_section(rel, owner, others):
    """AC-4.1, AC-4.2: each command has one `**Bug path:**` line and names
    `repro-order.py` only in its own section; the sibling specs' sections
    (`/prototype` Step 2.5; `/implement-story` Gates 0, 2.5, 3) and Step 4
    carry none of it."""
    text = read(rel)
    own = section(text, owner)
    assert text.count(BUG_PATH_LEAD) == own.count(BUG_PATH_LEAD) == 1, (
        "%s: expected one %s line, inside %r" % (rel, BUG_PATH_LEAD, owner)
    )
    assert text.count(SCRIPT_NAME) == own.count(SCRIPT_NAME), (
        "%s names %s outside %r" % (rel, SCRIPT_NAME, owner)
    )
    for heading in others:
        block = section(text, heading)
        for needle in (BUG_PATH_LEAD, SCRIPT_NAME):
            assert needle not in block, "%s %r carries %r" % (rel, heading, needle)


# ---------------------------------------------------------------------------
# Story 4: skills/subagent-worktree-integration/SKILL.md
# ---------------------------------------------------------------------------


def test_ordered_commits_paragraph():
    """AC-4.3: step 3 ends with the "Ordered commits" paragraph: carry the
    commits with `git cherry-pick`, oldest first, instead of copying their
    files; on a conflict run `git cherry-pick --abort`, copy the files, and
    say that the order was lost."""
    skill = read(INTEGRATION_REL)
    step = section(skill, INTEGRATION_STEP3)
    paras = paragraphs(step)
    assert paras and paras[-1].startswith(ORDERED_LEAD), (
        "step 3 does not end with the %s paragraph" % ORDERED_LEAD
    )
    assert sum(p.startswith(ORDERED_LEAD) for p in paras) == 1, "expected one %s paragraph" % ORDERED_LEAD
    text = flat(paras[-1])
    assert_in_order(
        text,
        [
            "repro commit before its fix",
            "`git cherry-pick <sha>...`",
            "oldest first",
            "instead of copying",
            "On a conflict",
            "`git cherry-pick --abort`",
            "copy the files",
            "order was lost",
        ],
    )
    assert skill.count("cherry-pick") == text.count("cherry-pick"), (
        "%s names cherry-pick outside the %s paragraph" % (INTEGRATION_REL, ORDERED_LEAD)
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not available")
def test_lint_integration_skill_passes():
    """AC-4.3: `bash scripts/lint-skill.sh
    skills/subagent-worktree-integration/SKILL.md` exits 0 with `pass` on
    line 1."""
    run_lint(INTEGRATION_REL)


# ---------------------------------------------------------------------------
# Story 4: one pin per Removal Inventory row
# ---------------------------------------------------------------------------


def read_or_empty(rel: str) -> str:
    path = REPO_ROOT / rel
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def section_or_empty(text: str, heading: str) -> str:
    if heading not in [line.rstrip() for line in text.splitlines()]:
        return ""
    return section(text, heading)


def has_paragraph(block: str, lead: str, needle: str) -> bool:
    return any(p.startswith(lead) and needle in p for p in paragraphs(block))


def inventory_tdd_cycle() -> List[str]:
    skill = read_or_empty(SKILL_REL)
    missing = []  # type: List[str]
    if BUG_HEADING not in headings(skill):
        missing.append("the %r section" % BUG_HEADING)
    if "repro-order: pass" not in section_or_empty(skill, EXAMPLES):
        missing.append("the bug example under %r" % EXAMPLES)
    if BUG_HEADING not in section_or_empty(skill, WHEN_TO_USE):
        missing.append("the When to Use bug bullet (drift DEV-007)")
    return missing


def inventory_coding_agent() -> List[str]:
    lines = read_or_empty(AGENT_REL).splitlines()
    missing = []  # type: List[str]
    if not any(line.startswith(REQ1_LEAD) and BUG_HEADING in line for line in lines):
        missing.append("the bug-path sentence in Implementation Requirement 1")
    if not any(line.startswith(REQ3_LEAD) and REF_FOOTER in line for line in lines):
        missing.append("the `Ref:` footer sentence in Implementation Requirement 3")
    if not any(line.startswith("- ") and REPRO_HEADING + "*" in line for line in lines):
        missing.append("the `### Repro` item in Output Requirements")
    if REPRO_HEADING not in lines:
        missing.append("the `### Repro` block in Output Format")
    return missing


def inventory_prototype() -> List[str]:
    step = section_or_empty(read_or_empty(PROTOTYPE_REL), STEP3)
    missing = []  # type: List[str]
    principle = "bug path in `%s`" % SKILL_REL
    if not any(line.startswith(PRINCIPLE1_LEAD) and principle in line for line in step.splitlines()):
        missing.append("the bug-path sentence in Step 3 principle 1")
    if not has_paragraph(step, BUG_PATH_LEAD, SCRIPT_NAME):
        missing.append("the %s line in Step 3" % BUG_PATH_LEAD)
    return missing


def inventory_implement_story() -> List[str]:
    gate = section_or_empty(read_or_empty(IMPLEMENT_STORY_REL), GATE1)
    if not has_paragraph(gate, BUG_PATH_LEAD, SCRIPT_NAME):
        return ["the %s line in Gate 1" % BUG_PATH_LEAD]
    return []


def inventory_integration() -> List[str]:
    step = section_or_empty(read_or_empty(INTEGRATION_REL), INTEGRATION_STEP3)
    if not has_paragraph(step, ORDERED_LEAD, "git cherry-pick"):
        return ["the ordered-commits paragraph in step 3"]
    return []


def inventory_files() -> List[str]:
    return [rel for rel in (SCRIPT_REL, SCRIPT_TEST_REL, WIRING_REL) if not (REPO_ROOT / rel).is_file()]


def inventory_contract() -> List[str]:
    missing = []  # type: List[str]
    rows = read_or_empty(CONTRACT_REL).splitlines()
    if not any(line.startswith("| `%s` |" % SCRIPT_NAME) for line in rows):
        missing.append("the `%s` row in %s" % (SCRIPT_NAME, CONTRACT_REL))
    if 'Smoke("%s"' % SCRIPT_NAME not in read_or_empty(CONTRACT_TEST_REL):
        missing.append("the `%s` Smoke entry in %s" % (SCRIPT_NAME, CONTRACT_TEST_REL))
    return missing


def inventory_config() -> List[str]:
    config = read_or_empty(CONFIG_FORMAT_REL)
    missing = []  # type: List[str]
    rows = table_rows(section_or_empty(config, SUPPORTED_KEYS))
    if not any(row.startswith(CONFIG_ROW_PREFIX) for row in rows):
        missing.append("the `Repro First` row in Supported Keys")
    if CONFIG_HEADING not in headings(config):
        missing.append("the %r section" % CONFIG_HEADING)
    return missing


# One entry per row of spec.md `## Removal Inventory`: (test id, the row's
# Location column, the check). DEV-007 adds the When to Use bullet to the
# tdd-cycle row. The ninth row, generated trees, is test_generated_trees_current.
REMOVAL_INVENTORY = [
    ("tdd-cycle", SKILL_REL, inventory_tdd_cycle),
    ("coding-agent", AGENT_REL, inventory_coding_agent),
    ("prototype", PROTOTYPE_REL, inventory_prototype),
    ("implement-story", IMPLEMENT_STORY_REL, inventory_implement_story),
    ("worktree-integration", INTEGRATION_REL, inventory_integration),
    ("script-files", ", ".join((SCRIPT_REL, SCRIPT_TEST_REL, WIRING_REL)), inventory_files),
    ("cli-contract", "%s, %s" % (CONTRACT_REL, CONTRACT_TEST_REL), inventory_contract),
    ("config-format", CONFIG_FORMAT_REL, inventory_config),
]


@pytest.mark.parametrize(
    "location,check",
    [pytest.param(location, check, id=row_id) for row_id, location, check in REMOVAL_INVENTORY],
)
def test_removal_inventory_row(location, check):
    """AC-4.4: the row's text or files are present, so deleting any part of
    the upgrade without the rest fails here, and the message names the row."""
    missing = check()
    assert not missing, "Removal Inventory row `%s`: missing %s" % (location, "; ".join(missing))
