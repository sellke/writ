#!/usr/bin/env python3
"""Wiring and replay tests for Story 3 of `2026-11-04-evidence-gated-review`:
Gate 3 of `/implement-story` runs `review-override.py evidence` on an agent
FAIL and applies the spec's nine-row Gate 3 decision.
[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]

- Gate 2 saves the lint and typecheck commands it ran; Gate 3 saves the
  review and the recorded run on every agent FAIL, whether or not
  `safety_fact` is on [AC-3.3].
- Gate 3 runs `check`, then `safety-fact`, then `evidence`, and lists the
  nine rows of spec.md § Gate 3 decision in order, first match wins
  [AC-3.1]. Row 3a is Story 4's and is not asserted here.
- Every State Catalog report line matches exactly one documented
  `evidence-gate:` form [AC-3.2]. The re-review rows need `--prior`
  (Story 4) and are not asserted.
- Both Gate 3 agents take `evidence_gate`, read the skill only when it is
  `on`, carry one `**Evidence:**` field after `**Category:**`, and say a
  Critical or Major issue blocks only with evidence; the `reviewer_filters`
  lines stay (spec.md → Amendment) [AC-3.4].
- Replay: two saved evaluator FAIL outputs run through the `evidence`
  command exactly as Gate 3 documents it, in a temp `git init` copy of the
  fixture project, then through the decision rows [AC-3.5]. Nothing runs in
  the Writ checkout.

Run: uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_evidence_gate_wiring.py
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "review-override.py"
IMPLEMENT_STORY = REPO_ROOT / "commands" / "implement-story.md"
EVALUATOR_AGENT = REPO_ROOT / "agents" / "evaluator-agent.md"
REVIEW_AGENT = REPO_ROOT / "agents" / "review-agent.md"

EV_FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "review-override" / "evidence"
EV_PROJECT = EV_FIXTURES / "pytest-project"

SKILL_REL = "skills/evidence-gated-findings/SKILL.md"
SWITCH_COMMAND = "python3 scripts/review-override.py switch --name evidence-gate"
SWITCH_INPUT = "evidence_gate"
OFF_CLAUSE = "`off` when `evidence_gate` is off, on any verdict"
EVIDENCE_COMMAND = re.compile(r"`(python3 scripts/review-override\.py evidence [^`]*)`")
GATE2_CHECKS = "`.writ/state/gate2-checks-<story-stem>.txt`"
GATE3_REVIEW = ".writ/state/gate3-review-<story-stem>.md"
GATE3_TESTS = "gate3-tests-<story-stem>.txt"

EVIDENCE_LINE = (
    "When `{evidence_gate}` is `on`, `Read skills/evidence-gated-findings/SKILL.md` "
    "and give each Critical or Major issue you want to block an `**Evidence:**` field. "
    "Still set FAIL; Gate 3 makes unbacked issues advisory."
)
CATEGORY_LINE = "- **Category:** [criterion/security/architecture/taste]"
EVIDENCE_FIELD = "- **Evidence:** [only when evidence_gate is on; format in the skill]"
BLOCKS_ONLY = "blocks only with an `**Evidence:**` field"

# The lines the evidence Read line follows: the reviewer-filters line in the
# evaluator, the safety-fact line in the review agent. Both stay unchanged.
EVALUATOR_FILTERS_LINE = (
    "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` "
    "and apply it before you set EVALUATION_RESULT."
)
REVIEW_FILTERS_LINE = (
    "When `{reviewer_filters}` is `on`, `Read skills/review-judgment-filters/SKILL.md` "
    "and apply it before you set REVIEW_RESULT."
)
SAFETY_LINE = (
    "When `{safety_fact}` is `on`, `Read skills/blast-radius/SKILL.md` and write its "
    "`### Safety Fact` section, starting from `{blast_radius}`."
)

# Generated copies of the two agents. Plugin copies prefix skill paths with
# `${CLAUDE_PLUGIN_ROOT}/`, so the path is matched as a substring.
GENERATED_AGENTS = (
    "claude-code/agents/writ-evaluator.md",
    "claude-code/agents/writ-reviewer.md",
    "plugins/writ/agents/evaluator-agent.md",
    "plugins/writ/agents/review-agent.md",
    "plugins/writ/agents/writ-evaluator.md",
    "plugins/writ/agents/writ-reviewer.md",
    "cursor/plugin/agents/evaluator-agent.md",
    "cursor/plugin/agents/review-agent.md",
    "codex/agents/evaluator-agent.toml",
    "codex/agents/review-agent.toml",
)

# spec.md → ## Business Rules (Expanded) → ### Gate 3 decision, rows 1 to 9:
# (terms in the condition cell, terms in the result cell).
DECISION_ROWS: Dict[int, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    1: (("`check`", "`fail`"), ("FAIL", "recode")),
    2: (("safety_fact_contradicts_verdict",), ("FAIL", "recode")),
    3: (("safety_fact_missing", "safety_fact_below_floor"), ("routing",)),
    4: (("PASS", "PAUSE"), ("that verdict",)),
    5: (("`evidence_gate` `off`",), ("FAIL stands",)),
    6: (("repro_mutated_tree",), ("BLOCKED escalation", "restart Gate 3")),
    7: (("line 1 `fail`",), ("FAIL", "recode", "`confirmed`")),
    8: (("line 1 `unverifiable`", "exit 2"), ("FAIL stands", "never `⚠️ DEGRADED`")),
    9: (("line 1 `pass`",), ("PASS",)),
}

# spec.md → ## Experience Design → ### State Catalog, one example line per
# state Story 3 wires. The re-review rows wait for `--prior` (Story 4).
STATE_CATALOG = (
    ("agent PASS", "evidence-gate: not run (PASS)"),
    ("agent PAUSE", "evidence-gate: not run (PAUSE)"),
    ("FAIL, a finding confirmed", "evidence-gate: 1 confirmed, 2 advisory, 0 unverifiable"),
    ("FAIL, nothing confirmed", "evidence-gate: 0 confirmed, 3 advisory, 1 unverifiable"),
    ("FAIL, no Test Runner", "evidence-gate: unverifiable (no_test_runner)"),
    ("FAIL, helper missing or exit 2", "evidence-gate: unverifiable (runner_not_found)"),
    ("a repro changed the tree", "evidence-gate: blocked (repro_mutated_tree src/x.py)"),
    ("switch off", "evidence-gate: off"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def slice_between(text: str, start: str, end: str) -> str:
    """From the line starting with `start` up to the line starting with `end`.
    Empty when `start` is absent; to the end of text when `end` is."""
    lines = text.splitlines()
    begin = next((i for i, l in enumerate(lines) if l.startswith(start)), None)
    if begin is None:
        return ""
    stop = next((i for i in range(begin + 1, len(lines)) if lines[i].startswith(end)),
                len(lines))
    return "\n".join(lines[begin:stop])


def table_rows(block: str) -> List[List[str]]:
    """Cells of the first markdown table in `block`, header and rule dropped."""
    rows: List[str] = []
    for line in block.splitlines():
        if line.startswith("|"):
            rows.append(line)
        elif rows:
            break
    body = [r for r in rows[1:] if not re.match(r"^\|[\s:|-]+\|$", r)]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in body]


def gate2() -> str:
    block = slice_between(read(IMPLEMENT_STORY), "#### Gate 2: Lint", "#### Gate 2.5:")
    if not block:
        raise AssertionError("Gate 2 section not found")
    return block


def gate3() -> str:
    block = slice_between(read(IMPLEMENT_STORY), "#### Gate 3: Review Agent", "#### Gate 3.5:")
    if not block:
        raise AssertionError("Gate 3 section not found")
    return block


def evidence_block() -> str:
    """The Gate 3 evidence paragraph, its decision table, and its report line."""
    block = slice_between(gate3(), "**Evidence.**", "**Jev shadow")
    if not block:
        raise AssertionError("Gate 3 has no **Evidence.** paragraph")
    return block


def evidence_command() -> str:
    found = EVIDENCE_COMMAND.findall(read(IMPLEMENT_STORY))
    if len(found) != 1:
        raise AssertionError("expected one documented evidence command, found %r" % found)
    return found[0]


def report_forms() -> List[str]:
    """The documented `evidence-gate: <state>` forms, each with its prefix."""
    lead = "Report `evidence-gate: <state>`"
    lines = [l for l in evidence_block().splitlines() if l.startswith(lead)]
    if len(lines) != 1:
        raise AssertionError("expected one report-line sentence, found %d" % len(lines))
    tail = lines[0][len(lead):]
    tail = tail.split("evidence-gate advisory:")[0]
    forms = [f for f in re.findall(r"`([^`]+)`", tail) if f != SWITCH_INPUT]
    return ["evidence-gate: " + f for f in forms]


def form_regex(form: str) -> "re.Pattern[str]":
    """`<placeholder>` matches any text; `A|B` inside parentheses matches either."""
    pattern = re.escape(form)
    pattern = re.sub(r"\\<[^>]*\\>|<[^>]*>", ".+", pattern)
    pattern = pattern.replace(r"PASS\|PAUSE", "(?:PASS|PAUSE)")
    return re.compile(pattern)


def matching_forms(line: str) -> List[str]:
    return [f for f in report_forms() if form_regex(f).fullmatch(line)]


# --- the decision rows and report line, as Gate 3 applies them -------------


def evidence_reasons(lines: List[str]) -> List[str]:
    return [l[len("reason: "):] for l in lines if l.startswith("reason: ")]


def gate3_decision(*, verdict: str, evidence: List[str], check: str = "pass",
                   safety: Optional[str] = None, evidence_gate: str = "on") -> Tuple[str, int]:
    """spec.md § Gate 3 decision, rows 1 to 9, first match wins.
    Returns (Gate 3 result, row)."""
    if check == "fail":
        return "FAIL", 1
    if safety == "safety_fact_contradicts_verdict":
        return "FAIL", 2
    if safety in ("safety_fact_missing", "safety_fact_below_floor"):
        return "safety-fact routing", 3
    if verdict in ("PASS", "PAUSE"):
        return verdict, 4
    if evidence_gate == "off":
        return "FAIL", 5
    reasons = evidence_reasons(evidence)
    if reasons and reasons[0].startswith("repro_mutated_tree"):
        return "BLOCKED", 6
    line1 = evidence[0] if evidence else ""
    if line1 == "fail":
        return "FAIL", 7
    if line1 == "pass":
        return "PASS", 9
    return "FAIL", 8


def gate3_report_line(*, verdict: str, evidence: List[str], evidence_gate: str = "on") -> str:
    if evidence_gate == "off":
        return "evidence-gate: off"
    if verdict in ("PASS", "PAUSE"):
        return "evidence-gate: not run (%s)" % verdict
    reasons = evidence_reasons(evidence)
    if reasons and reasons[0].startswith("repro_mutated_tree"):
        return "evidence-gate: blocked (%s)" % reasons[0]
    if not evidence or evidence[0] not in ("pass", "fail"):
        return "evidence-gate: unverifiable (%s)" % (reasons[0] if reasons else "helper")
    counts = re.search(r"\((\d+ confirmed, \d+ advisory, \d+ unverifiable)\)$", evidence[-1])
    if counts is None:
        raise AssertionError("no summary counts in %r" % evidence[-1])
    return "evidence-gate: " + counts.group(1)


def finding_lines(lines: List[str]) -> Dict[str, str]:
    found = {}
    for line in lines:
        match = re.match(r"^finding (F\d+): (.*)$", line)
        if match:
            found[match.group(1)] = match.group(2)
    return found


# ---------------------------------------------------------------------------
# AC-3.3: Gate 2 and Gate 3 save the evidence inputs
# ---------------------------------------------------------------------------


class Gate2SaveTest(unittest.TestCase):
    """Gate 2 saves its lint and typecheck commands, one per line. [AC-3.3]"""

    def test_gate2_saves_the_commands_it_ran(self) -> None:
        lines = [l for l in gate2().splitlines() if GATE2_CHECKS in l]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("lint and typecheck commands", lines[0])
        self.assertIn("not the auto-fixes", lines[0])
        self.assertIn("one per line", lines[0])

    def test_evidence_reads_the_gate2_record(self) -> None:
        self.assertIn("--checks %s" % GATE2_CHECKS.strip("`"), evidence_command())


class Gate3SaveTest(unittest.TestCase):
    """Gate 3 saves the review and recorded run on every agent FAIL, whether
    or not `safety_fact` is on. [AC-3.3]"""

    def test_save_is_not_inside_the_safety_fact_paragraph(self) -> None:
        paragraphs = [p for p in gate3().split("\n\n")
                      if GATE3_REVIEW in p and GATE3_TESTS in p]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        save = paragraphs[0]
        self.assertFalse(save.startswith("**Safety fact"), save)
        self.assertIn("agent FAIL", save)
        self.assertIn("`safety_fact` on", save)
        self.assertIn("`recorded_test_results`", save)
        self.assertLess(gate3().index(save), gate3().index("**Safety fact"))

    def test_save_binds_the_placeholders_and_re_saves(self) -> None:
        """`<review>` and `<tests>` name the saved paths; a re-spawn re-saves."""
        save = next(p for p in gate3().split("\n\n") if GATE3_REVIEW in p)
        self.assertIn("`<review>` = `%s`" % GATE3_REVIEW, save)
        self.assertIn("`<tests>` = `.writ/state/%s`" % GATE3_TESTS, save)
        self.assertIn("re-spawn", save)

    def test_safety_fact_paragraph_keeps_its_condition(self) -> None:
        self.assertIn("**Safety fact (`safety_fact` on).**", gate3())

    def test_evidence_reads_the_saved_review_and_tests(self) -> None:
        argv = shlex.split(evidence_command())
        self.assertEqual(argv[argv.index("--review-output") + 1], "<review>")
        self.assertEqual(argv[argv.index("--tests-output") + 1], "<tests>")


# ---------------------------------------------------------------------------
# AC-3.1: order, the evidence call, and the nine decision rows
# ---------------------------------------------------------------------------


class Gate3OrderTest(unittest.TestCase):
    """`check`, then `safety-fact`, then `evidence`; `evidence` runs on every
    agent FAIL with the technical spec's arguments. [AC-3.1]"""

    def test_check_then_safety_fact_then_evidence(self) -> None:
        text = gate3()
        positions = [text.find("review-override.py %s" % sub)
                     for sub in ("check", "safety-fact", "evidence")]
        self.assertNotIn(-1, positions, positions)
        self.assertEqual(positions, sorted(positions))

    def test_evidence_runs_only_in_gate3(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertEqual(text.count("review-override.py evidence"), 1)
        self.assertEqual(gate3().count("review-override.py evidence"), 1)

    def test_evidence_runs_on_every_agent_fail_after_the_other_checks(self) -> None:
        opening = evidence_block().split("\n\n")[0]
        self.assertIn("On an agent FAIL", opening)
        self.assertIn("after `check`, `safety-fact`, and any re-spawn", opening)
        # Rows 2 and 4 decide a PASS or PAUSE too, so the table applies on any verdict.
        self.assertIn("First match wins, on any verdict", opening)

    def test_evidence_arguments(self) -> None:
        argv = shlex.split(evidence_command())
        self.assertEqual(argv[:3], ["python3", "scripts/review-override.py", "evidence"])
        self.assertNotIn("--repo", argv)  # `.` is the CLI default; cwd is the repo
        self.assertEqual(argv[argv.index("--changed") + 1], "<files>")
        timeout = argv[argv.index("--timeout") + 1]
        self.assertTrue(timeout.isdigit() and 0 < int(timeout) <= 120, timeout)
        for flag in ("--review-output", "--tests-output", "--checks"):
            self.assertIn(flag, argv)


class Gate3DecisionTest(unittest.TestCase):
    """The nine rows of spec.md § Gate 3 decision, in order. [AC-3.1]"""

    def setUp(self) -> None:
        self.rows = table_rows(evidence_block())

    def test_nine_rows_numbered_in_order(self) -> None:
        self.assertEqual([r[0] for r in self.rows], [str(n) for n in range(1, 10)])

    def test_each_row_names_its_condition_and_result(self) -> None:
        for row in self.rows:
            number = int(row[0])
            condition, result = DECISION_ROWS[number]
            for term in condition:
                self.assertIn(term, row[1], "row %d condition: %r" % (number, row))
            for term in result:
                self.assertIn(term, row[2], "row %d result: %r" % (number, row))


# ---------------------------------------------------------------------------
# AC-3.2: one `evidence-gate:` line per State Catalog state
# ---------------------------------------------------------------------------


class Gate3ReportLineTest(unittest.TestCase):
    """Each State Catalog line matches exactly one documented form; the
    switch is resolved once and passed to every spawn. [AC-3.2]"""

    def test_each_state_matches_exactly_one_form(self) -> None:
        for state, line in STATE_CATALOG:
            self.assertEqual(len(matching_forms(line)), 1,
                             "%s: %r matches %r of %r"
                             % (state, line, matching_forms(line), report_forms()))

    def test_off_is_tied_to_the_switch_on_any_verdict(self) -> None:
        """`off` follows `evidence_gate`, on every verdict, and leads the list."""
        sentence = next(l for l in evidence_block().splitlines() if l.startswith("Report `"))
        self.assertIn(OFF_CLAUSE, sentence)
        self.assertNotIn("(row 5)", sentence)
        self.assertEqual(report_forms()[0], "evidence-gate: off")
        rows = {r[0]: r for r in table_rows(evidence_block())}
        self.assertNotIn("switch_off", rows["5"][1])

    def test_report_mirror_prints_off_on_every_verdict(self) -> None:
        for verdict, evidence in (("PASS", []), ("PAUSE", []),
                                  ("FAIL", ["unverifiable", "reason: switch_off"])):
            line = gate3_report_line(verdict=verdict, evidence=evidence, evidence_gate="off")
            self.assertEqual(line, "evidence-gate: off", verdict)
            self.assertEqual(matching_forms(line), ["evidence-gate: off"], verdict)

    def test_downgraded_findings_print_advisory_lines(self) -> None:
        self.assertIn("`evidence-gate advisory: ", evidence_block())

    def test_switch_resolved_once_and_passed_to_every_spawn(self) -> None:
        text = read(IMPLEMENT_STORY)
        self.assertEqual(text.count(SWITCH_COMMAND), 1)
        paragraphs = [p for p in gate3().split("\n\n") if SWITCH_COMMAND in p]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        self.assertIn("`evidence_gate`", paragraphs[0])
        self.assertIn("every Gate 3 spawn", paragraphs[0])

    def test_gate3_carries_no_skill_text(self) -> None:
        """The skill owns the evidence grammar; Gate 3 owns when and what."""
        self.assertNotIn(SKILL_REL, gate3())


# ---------------------------------------------------------------------------
# AC-3.4: the two Gate 3 agents
# ---------------------------------------------------------------------------


class AgentEvidenceWiringTest(unittest.TestCase):
    """Input row, one conditional `Read` line, the `**Evidence:**` field after
    `**Category:**`, severity text that blocks only with evidence, and the
    `reviewer_filters` lines unchanged. [AC-3.4]"""

    CASES = (
        (EVALUATOR_AGENT, EVALUATOR_FILTERS_LINE, EVALUATOR_FILTERS_LINE),
        (REVIEW_AGENT, SAFETY_LINE, REVIEW_FILTERS_LINE),
    )

    def test_input_row(self) -> None:
        for path, _, _ in self.CASES:
            inputs = slice_between(read(path), "## Input Requirements", "## ")
            rows = [r for r in table_rows(inputs) if r[0] == "`evidence_gate`"]
            self.assertEqual(len(rows), 1, path.name)
            for term in ("`on`", "`off`", "Gate 3", "`evidence-gate`"):
                self.assertIn(term, rows[0][1], path.name)

    def test_one_conditional_read_line(self) -> None:
        for path, _, _ in self.CASES:
            reads = [l for l in read(path).splitlines() if SKILL_REL in l]
            self.assertEqual(reads, [EVIDENCE_LINE], path.name)

    def test_read_line_placement(self) -> None:
        for path, anchor, _ in self.CASES:
            lines = read(path).splitlines()
            at = lines.index(EVIDENCE_LINE)
            self.assertEqual(lines[at - 2], anchor, path.name)
            self.assertLess(lines.index("## Prompt Template"), at, path.name)
            output = next(i for i in range(at, len(lines)) if lines[i].startswith("## Output Format"))
            self.assertLess(at, output, path.name)

    def test_evidence_field_follows_category(self) -> None:
        for path, _, _ in self.CASES:
            lines = read(path).splitlines()
            fields = [l for l in lines if l.startswith("- **Evidence:**")]
            self.assertEqual(fields, [EVIDENCE_FIELD], path.name)
            self.assertEqual(lines[lines.index(EVIDENCE_FIELD) - 1], CATEGORY_LINE, path.name)

    def test_critical_and_major_block_only_with_evidence(self) -> None:
        for path, _, _ in self.CASES:
            block = slice_between(read(path), "## Severity Definitions", "## ")
            rows = {r[0]: r for r in table_rows(block)}
            for severity in ("**Critical**", "**Major**"):
                self.assertIn(BLOCKS_ONLY, rows[severity][2], "%s %s" % (path.name, severity))
                self.assertIn("`evidence_gate`", rows[severity][2], path.name)
            self.assertNotIn("Evidence", rows["**Minor**"][2], path.name)

    def test_when_to_fail_bullets_match_the_severity_text(self) -> None:
        for path, _, _ in self.CASES:
            block = slice_between(read(path), "### When to FAIL", "### ")
            named = [l for l in block.splitlines() if "Critical or Major" in l]
            self.assertTrue(named, path.name)
            for line in named:
                self.assertIn(BLOCKS_ONLY, line, path.name)

    def test_criterion_examples_cite_an_ac_id(self) -> None:
        for path, _, _ in self.CASES:
            lines = [l for l in read(path).splitlines()
                     if l.startswith("- **Category:** criterion")]
            self.assertTrue(lines, path.name)
            for line in lines:
                self.assertRegex(line, r"\[AC-\d+\.\d+\]", path.name)

    def test_reviewer_filters_lines_stay(self) -> None:
        for path, _, filters_line in self.CASES:
            text = read(path)
            self.assertEqual(text.splitlines().count(filters_line), 1, path.name)
            self.assertEqual(text.count("| `reviewer_filters` |"), 1, path.name)

    def test_generated_copies_carry_the_wiring(self) -> None:
        for rel in GENERATED_AGENTS:
            text = read(REPO_ROOT / rel)
            self.assertIn(SKILL_REL, text, rel)
            self.assertIn("When `{evidence_gate}` is `on`", text, rel)
            self.assertIn("| `evidence_gate` |", text, rel)
            self.assertIn(EVIDENCE_FIELD, text, rel)


# ---------------------------------------------------------------------------
# AC-3.5: replay a saved evaluator FAIL through the documented command
# ---------------------------------------------------------------------------

STORY_STEM = "story-9-replay"
CHANGED = ["src/limits.py", "src/routes.py"]
REPRO = "tests/test_limits_repro.py"
REPRO_BODY = (
    "from src.limits import parse_limit\n"
    "\n"
    "\n"
    "def test_negative_limit_rejected():\n"
    "    assert parse_limit(\"-1\") is None\n"
)
RECORDED_RUN = (
    "command: python3 -m pytest tests/test_limits.py\n"
    "exit code: 0\n"
    "1 passed in 0.01s\n"
)


def replay_env() -> dict:
    """The caller's env minus GIT_*, with git config isolated."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                "PYTHONDONTWRITEBYTECODE": "1"})
    return env


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, env=replay_env())
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
    return proc.stdout


def evaluator_fail(*, with_repro: bool) -> str:
    """A saved evaluator FAIL: a Critical criterion issue and a Major
    architecture issue, both in the change set. `with_repro` gives the first
    one a `test` repro that fails on the fixture's bug."""
    lines = [
        "### EVALUATION_RESULT: FAIL",
        "",
        "### Summary",
        "Two findings against the limit parser.",
        "",
        "### Checklist Results",
        "",
        "#### Acceptance Criteria",
        "- [ ] Given a negative limit, when it is parsed, then it is rejected [AC-1.1]",
        "",
        "### Issues Found",
        "",
        "- **Issue:** `parse_limit()` accepts a negative limit and returns every row",
        "- **Location:** `src/limits.py:3`",
        "- **Severity:** Critical",
        "- **Category:** criterion [AC-1.1]",
    ]
    if with_repro:
        lines.append("- **Evidence:** test `%s`" % REPRO)
        lines.append("  ```python")
        lines.extend(("  " + l) if l else "" for l in REPRO_BODY.splitlines())
        lines.append("  ```")
    lines += [
        "",
        "- **Issue:** `list_rows()` passes the raw limit straight through",
        "- **Location:** `src/routes.py:5`",
        "- **Severity:** Major",
        "- **Category:** architecture",
        "",
        "### Drift Analysis",
        "",
        "**Overall Drift:** None",
        "",
    ]
    return "\n".join(lines)


class ReplayTest(unittest.TestCase):
    """A saved evaluator FAIL, with and without a confirmed `test` repro, run
    through the documented `evidence` command and the decision rows. [AC-3.5]"""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        shutil.copytree(str(EV_PROJECT), str(self.repo))
        runner = "%s -m pytest" % shlex.quote(sys.executable)
        (self.repo / ".writ").mkdir()
        (self.repo / ".writ" / "config.md").write_text(
            "# Writ Project Config\n\n## Conventions\n\n"
            "- **Test Runner:** %s\n" % runner, encoding="utf-8")
        git(self.repo, "-c", "init.defaultBranch=main", "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=Replay Test", "-c", "user.email=replay@example.com",
            "-c", "commit.gpgsign=false", "commit", "-q", "--no-verify", "-m", "base")
        self.assertNotEqual(self.repo.resolve(), REPO_ROOT.resolve())

    def run_gate3_evidence(self, review: str) -> Tuple[List[str], int]:
        """Save the Gate 3 inputs where Gate 3 saves them, then run the
        documented command with its placeholders filled in."""
        state = self.repo / ".writ" / "state"
        state.mkdir(parents=True, exist_ok=True)
        review_rel = GATE3_REVIEW.replace("<story-stem>", STORY_STEM)
        tests_rel = ".writ/state/" + GATE3_TESTS.replace("<story-stem>", STORY_STEM)
        (self.repo / review_rel).write_text(review, encoding="utf-8")
        (self.repo / tests_rel).write_text(RECORDED_RUN, encoding="utf-8")
        (state / ("gate2-checks-%s.txt" % STORY_STEM)).write_text("", encoding="utf-8")

        argv: List[str] = []
        for token in shlex.split(evidence_command()):
            if token == "python3":
                argv.append(sys.executable)
            elif token == "scripts/review-override.py":
                argv.append(str(SCRIPT))
            elif token == "<review>":
                argv.append(review_rel)
            elif token == "<tests>":
                argv.append(tests_rel)
            elif token == "<files>":
                argv.extend(CHANGED)
            else:
                argv.append(token.replace("<story-stem>", STORY_STEM))
        self.assertFalse([t for t in argv if "<" in t], argv)
        proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(self.repo),
                              env=replay_env(), timeout=300)
        self.assertIn(proc.returncode, (0, 1), proc.stdout + proc.stderr)
        return proc.stdout.splitlines(), proc.returncode

    def test_fail_without_evidence_becomes_pass_with_advisory_findings(self) -> None:
        """AC-3.5 — no Evidence blocks: row 9, PASS, every finding advisory."""
        out, code = self.run_gate3_evidence(evaluator_fail(with_repro=False))
        self.assertEqual(out[0], "pass", out)
        self.assertEqual(code, 0)
        self.assertEqual(finding_lines(out), {
            "F1": "advisory (no_evidence) at src/limits.py",
            "F2": "advisory (no_evidence) at src/routes.py",
        })
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out), ("PASS", 9))
        report = gate3_report_line(verdict="FAIL", evidence=out)
        self.assertEqual(report, "evidence-gate: 0 confirmed, 2 advisory, 0 unverifiable")
        self.assertEqual(len(matching_forms(report)), 1, report)

    def test_fail_with_a_confirmed_repro_stays_fail_and_names_it(self) -> None:
        """AC-3.5 — one confirmed `test` repro: row 7, FAIL, F1 named."""
        out, code = self.run_gate3_evidence(evaluator_fail(with_repro=True))
        self.assertEqual(out[0], "fail", out)
        self.assertEqual(code, 1)
        findings = finding_lines(out)
        self.assertEqual(findings["F1"], "confirmed (test %s, exit 1) at src/limits.py" % REPRO)
        self.assertEqual(findings["F2"], "advisory (no_evidence) at src/routes.py")
        self.assertIn("reason: confirmed F1", out)
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out), ("FAIL", 7))
        confirmed = [k for k, v in findings.items() if v.startswith("confirmed")]
        self.assertEqual(confirmed, ["F1"])
        report = gate3_report_line(verdict="FAIL", evidence=out)
        self.assertEqual(report, "evidence-gate: 1 confirmed, 1 advisory, 0 unverifiable")
        self.assertEqual(len(matching_forms(report)), 1, report)
        self.assertFalse((self.repo / REPRO).exists(), "the repro was left on disk")

    def test_the_decision_rows_outrank_evidence(self) -> None:
        """AC-3.5 — the same confirmed run under rows 1, 4, and 5."""
        out, _ = self.run_gate3_evidence(evaluator_fail(with_repro=True))
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out, check="fail"), ("FAIL", 1))
        self.assertEqual(gate3_decision(verdict="PASS", evidence=[]), ("PASS", 4))
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out, evidence_gate="off"),
                         ("FAIL", 5))


if __name__ == "__main__":
    unittest.main()
