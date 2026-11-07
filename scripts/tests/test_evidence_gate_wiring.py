#!/usr/bin/env python3
"""Wiring and replay tests for Story 3 of `2026-11-04-evidence-gated-review`:
Gate 3 of `/implement-story` runs `review-override.py evidence` on an agent
FAIL and applies the spec's nine-row Gate 3 decision.
[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]

- Gate 2 saves the lint and typecheck commands it ran; Gate 3 saves the
  review and the recorded run on every agent FAIL, whether or not
  `safety_fact` is on [AC-3.3].
- Gate 3 runs `check`, then `safety-fact`, then `evidence`, and lists the
  rows of spec.md § Gate 3 decision in order, first match wins [AC-3.1].
- Every State Catalog report line matches exactly one documented
  `evidence-gate:` form [AC-3.2].
- Both Gate 3 agents take `evidence_gate`, read the skill only when it is
  `on`, carry one `**Evidence:**` field after `**Category:**`, and say a
  Critical or Major issue blocks only with evidence; the `reviewer_filters`
  lines stay (spec.md → Amendment) [AC-3.4].
- Replay: two saved evaluator FAIL outputs run through the `evidence`
  command exactly as Gate 3 documents it, in a temp `git init` copy of the
  fixture project, then through the decision rows [AC-3.5]. Nothing runs in
  the Writ checkout.

Story 4 of `2026-11-04-evidence-gated-review` adds the `--prior` row (4a),
the `<manifest>` binding, `--prior` on every verdict once the manifest
exists, the `## Evidence repros` recode brief, and manifest paths in the
re-review's recorded run, plus a re-review replay [AC-4.5]. The Gate 3 save
is unconditional now, so Story 3's save condition moved with it. Its recode
(DEV-026) moved the tree-mutation row to the top: the contract's Hardest
Constraint makes any mutation BLOCKED, ahead of every other row.

Story 3 of the 2026-11-06 lean-story-pipeline spec moved the evidence call, the
switch, `--prior`, and the decision table out of the command prose into
`scripts/story-gate.py` post-review (`evidence_args`, `evidence_runs`,
`decide_gate3`, `evidence_gate_line`). The pins below assert the same
guarantees against those functions; the replays run `review-override.py` with
the runner's own arguments.

Run: uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_evidence_gate_wiring.py
"""

from __future__ import annotations

import json
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
STORY_GATE = REPO_ROOT / "scripts" / "story-gate.py"
POST_REVIEW = "python3 scripts/story-gate.py run --phase post-review"
GATE2_CHECKS = "`.writ/state/gate2-checks-<story-stem>.txt`"
GATE3_REVIEW = ".writ/state/gate3-review-<story-stem>.md"
GATE3_TESTS = "gate3-tests-<story-stem>.txt"
MANIFEST = ".writ/state/evidence-<story-stem>.json"
PRIOR_REASONS = ("repro_removed", "repro_modified", "repro_still_failing")
RECORDED_RUN_DEF = "of the story's tests and each path in `<manifest>` = `%s`" % MANIFEST
REPROS_HEADING = "`## Evidence repros`"
NO_EDIT = "Create it exactly; do not edit it. Make it pass."
BRIEF_SOURCE = "(row 4a: from `<manifest>`)"

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

# spec.md → ## Business Rules (Expanded) → ### Gate 3 decision, with the
# Story 4 recode's order (DEV-026): the tree-mutation row first, then spec
# rows 1 to 3 as 2 to 4, row 3a as 4a, and rows 4 and 5 as 5 and 6. Rows 7 to
# 9 keep their numbers. (terms in the condition cell, terms in the result cell)
DECISION_ROWS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "1": (("repro_mutated_tree",), ("BLOCKED escalation", "restart Gate 3")),
    "2": (("`check`", "`fail`"), ("FAIL", "recode")),
    "3": (("safety_fact_contradicts_verdict",), ("FAIL", "recode")),
    "4": (("safety_fact_missing", "safety_fact_below_floor"), ("routing",)),
    "4a": (tuple("`%s`" % r for r in PRIOR_REASONS), ("FAIL", "recode")),
    "5": (("PASS", "PAUSE"), ("that verdict",)),
    "6": (("`evidence_gate` `off`",), ("FAIL stands",)),
    "7": (("line 1 `fail`",), ("FAIL", "recode", "`confirmed`")),
    "8": (("line 1 `unverifiable`", "exit 2"), ("FAIL stands", "never `⚠️ DEGRADED`")),
    "9": (("line 1 `pass`",), ("PASS",)),
}
ROW_ORDER = ["1", "2", "3", "4", "4a", "5", "6", "7", "8", "9"]

# spec.md → ## Experience Design → ### State Catalog, one example line per state.
STATE_CATALOG = (
    ("agent PASS", "evidence-gate: not run (PASS)"),
    ("agent PAUSE", "evidence-gate: not run (PAUSE)"),
    ("FAIL, a finding confirmed", "evidence-gate: 1 confirmed, 2 advisory, 0 unverifiable"),
    ("FAIL, nothing confirmed", "evidence-gate: 0 confirmed, 3 advisory, 1 unverifiable"),
    ("FAIL, no Test Runner", "evidence-gate: unverifiable (no_test_runner)"),
    ("FAIL, helper missing or exit 2", "evidence-gate: unverifiable (runner_not_found)"),
    ("a repro changed the tree", "evidence-gate: blocked (repro_mutated_tree src/x.py)"),
    ("re-review, prior repro removed", "evidence-gate: fail (repro_removed tests/x_repro.py)"),
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
    """Gate 3 from the post-review call on: the call, the restart table, the
    re-spawn, the recode brief, and the report lines."""
    text = gate3()
    if POST_REVIEW not in text:
        raise AssertionError("Gate 3 does not run story-gate.py post-review")
    return text[text.index("**Verify the claim, don't trust it.**"):]


_MODULE = None


def story_gate():
    """scripts/story-gate.py, loaded once."""
    global _MODULE
    if _MODULE is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("story_gate", str(STORY_GATE))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULE = module
    return _MODULE


def evidence_tokens(prior: bool = False) -> List[str]:
    """The `review-override.py evidence` call post-review makes, placeholders
    for its inputs; `prior` once `<manifest>` exists."""
    args = story_gate().evidence_args("<review>", ["<files>"], "<tests>", "<checks>",
                                      "<manifest>", prior)
    return ["python3", "scripts/review-override.py"] + args


def evidence_command() -> str:
    return " ".join(evidence_tokens())


def report_forms() -> List[str]:
    """The `evidence-gate: <state>` forms the runner prints, each with its prefix."""
    return ["evidence-gate: " + f for f in story_gate().EVIDENCE_GATE_FORMS]


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


def prior_failed(reasons: List[str]) -> bool:
    return any(r.split()[0] in PRIOR_REASONS for r in reasons if r.split())


def evidence_result(lines: List[str]) -> Optional[dict]:
    """An `evidence` run's stdout lines as the runner records them; [] = not run."""
    if not lines:
        return None
    verdict = lines[0] if lines[0] in ("pass", "fail", "unverifiable") else "unverifiable"
    return {"verdict": verdict, "reasons": evidence_reasons(lines),
            "summary": lines[-1] if len(lines) > 1 else ""}


def gate3_decision(*, verdict: str, evidence: List[str], check: str = "pass",
                   safety: Optional[str] = None, evidence_gate: str = "on") -> Tuple[str, str]:
    """Gate 3's first-match decision (DECISION_ROWS), as `story-gate.py`
    `decide_gate3` applies it. Returns (Gate 3 result, row)."""
    sf = {"verdict": "fail", "reasons": [safety]} if safety else None
    decision = story_gate().decide_gate3(
        verdict, {"verdict": check, "reasons": [] if check != "fail" else ["untested_criterion"]},
        sf, evidence_result(evidence), evidence_gate)
    named = {"1": "BLOCKED", "4": "safety-fact routing"}
    return named.get(decision["row"], decision["verdict"]), decision["row"]


def gate3_report_line(*, verdict: str, evidence: List[str], evidence_gate: str = "on") -> str:
    """The `evidence-gate:` line, as `story-gate.py` `evidence_gate_line` prints it."""
    return story_gate().evidence_gate_line(verdict, evidence_result(evidence), evidence_gate)


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
        """Gate 2 binds `<checks>` once; the evidence call reads it (Story 4),
        and post-review defaults `--checks` to that same path."""
        self.assertIn("`<checks>` = %s" % GATE2_CHECKS, gate2())
        self.assertEqual(read(IMPLEMENT_STORY).count(GATE2_CHECKS.strip("`")), 1)
        argv = evidence_tokens()
        self.assertEqual(argv[argv.index("--checks") + 1], "<checks>")
        self.assertIn('"gate2-checks-%s.txt"', read(STORY_GATE))


class Gate3SaveTest(unittest.TestCase):
    """Gate 3 saves the review and recorded run on every verdict, so every
    agent FAIL has them whether or not `safety_fact` is on. Story 4 made the
    save unconditional: `--prior` also runs on PASS and PAUSE, and the Jev
    shadow reuses the two files. [AC-3.3]"""

    def test_save_is_not_inside_the_safety_fact_paragraph(self) -> None:
        paragraphs = [p for p in gate3().split("\n\n")
                      if GATE3_REVIEW in p and GATE3_TESTS in p]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        save = paragraphs[0]
        self.assertFalse(save.startswith("**Safety fact"), save)
        self.assertTrue(save.startswith("Save the review to `<review>`"), save)
        self.assertNotIn("agent FAIL", save)  # no condition: every verdict
        self.assertIn("`recorded_test_results`", save)
        self.assertLess(gate3().index(save), gate3().index("**Safety fact"))

    def test_jev_shadow_reuses_the_saved_files(self) -> None:
        """Post-review passes the saved `<tests>` and `<review>` to the shadow."""
        jev = [l for l in gate3().splitlines() if "jev-judge.py ac-shadow" in l]
        self.assertEqual(len(jev), 1, jev)
        args = " ".join(story_gate().shadow_args("<story-file>", "<tests>", "<diff>", "<review>"))
        self.assertIn("--tests-output <tests> --diff <diff> --review-output <review>", args)
        self.assertIn("--review-output <review> --tests-output <tests>", gate3())

    def test_save_binds_the_placeholders_and_re_saves(self) -> None:
        """`<review>` and `<tests>` name the saved paths; a re-spawn re-saves."""
        save = next(p for p in gate3().split("\n\n") if GATE3_REVIEW in p)
        self.assertIn("`<review>` = `%s`" % GATE3_REVIEW, save)
        self.assertIn("`<tests>` = `.writ/state/%s`" % GATE3_TESTS, save)
        self.assertIn("re-spawn", save)

    def test_safety_fact_paragraph_keeps_its_condition(self) -> None:
        self.assertIn("**Safety fact (`safety_fact` on).**", gate3())

    def test_evidence_reads_the_saved_review_and_tests(self) -> None:
        argv = evidence_tokens()
        self.assertEqual(argv[argv.index("--review-output") + 1], "<review>")
        self.assertEqual(argv[argv.index("--tests-output") + 1], "<tests>")


# ---------------------------------------------------------------------------
# AC-3.1: order, the evidence call, and the nine decision rows
# ---------------------------------------------------------------------------


class Gate3OrderTest(unittest.TestCase):
    """`check`, then `safety-fact`, then `evidence`; `evidence` runs on every
    agent FAIL with the technical spec's arguments. [AC-3.1]"""

    def test_check_then_safety_fact_then_evidence(self) -> None:
        ids = [row.id for row in story_gate().CHECKS["post-review"]]
        positions = [ids.index(c) for c in ("gate3_override", "gate3_safety_fact",
                                            "gate3_evidence")]
        self.assertEqual(positions, sorted(positions))
        self.assertIn(POST_REVIEW, gate3())

    def test_evidence_runs_only_in_gate3(self) -> None:
        self.assertEqual(read(IMPLEMENT_STORY).count("review-override.py evidence"), 0)
        rows = [row.id for phase in story_gate().CHECKS.values() for row in phase
                if row.run.__name__ == "evidence"]
        self.assertEqual(rows, ["gate3_evidence"])

    def test_evidence_runs_on_every_agent_fail_after_the_other_checks(self) -> None:
        runs = story_gate().evidence_runs
        self.assertTrue(runs("FAIL", False))
        self.assertFalse(runs("PASS", False))
        self.assertFalse(runs("PAUSE", False))
        # Evidence runs after `check`, `safety-fact`, and any re-spawn: never in a
        # run whose safety-fact result re-spawns Gate 3 (row 4), manifest or not.
        respawn = {"verdict": "fail", "restart": "gate3",
                   "reasons": ["safety_fact_below_floor traced"]}
        for verdict in ("FAIL", "PASS"):
            self.assertFalse(runs(verdict, True, respawn), verdict)
        self.assertFalse(runs("FAIL", False, respawn))
        recode = {"verdict": "fail", "restart": "gate1",
                  "reasons": ["safety_fact_contradicts_verdict"]}
        self.assertTrue(runs("FAIL", False, recode))
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=[], check="pass",
                                        safety="safety_fact_below_floor"),
                         ("safety-fact routing", "4"))
        # Rows 2 and 4 decide a PASS or PAUSE too, so the table applies on any verdict.
        self.assertEqual(gate3_decision(verdict="PASS", evidence=[], check="fail"), ("FAIL", "2"))
        self.assertIn("first-match decision", evidence_block())

    def test_evidence_arguments(self) -> None:
        argv = evidence_tokens()
        self.assertEqual(argv[:3], ["python3", "scripts/review-override.py", "evidence"])
        self.assertNotIn("--repo", argv)  # `.` is the CLI default; cwd is the repo
        self.assertEqual(argv[argv.index("--changed") + 1], "<files>")
        timeout = argv[argv.index("--timeout") + 1]
        self.assertTrue(timeout.isdigit() and 0 < int(timeout) <= 120, timeout)
        for flag in ("--review-output", "--tests-output", "--checks"):
            self.assertIn(flag, argv)


class Gate3DecisionTest(unittest.TestCase):
    """The nine rows of spec.md § Gate 3 decision, in order. [AC-3.1]"""

    # One input per row, in row order: (agent verdict, evidence lines, check,
    # safety reason, evidence_gate switch).
    CASES = {
        "1": ("FAIL", ["fail", "reason: repro_mutated_tree src/x.py", "s"], "pass", None, "on"),
        "2": ("PASS", [], "fail", None, "on"),
        "3": ("PASS", [], "pass", "safety_fact_contradicts_verdict", "on"),
        "4": ("PASS", [], "pass", "safety_fact_missing", "on"),
        "4a": ("PASS", ["fail", "reason: repro_removed tests/x.py", "s"], "pass", None, "on"),
        "5": ("PAUSE", [], "pass", None, "on"),
        "6": ("FAIL", ["unverifiable", "reason: switch_off", "s"], "pass", None, "off"),
        "7": ("FAIL", ["fail", "reason: confirmed F1", "s (1 confirmed, 0 advisory, 0 unverifiable)"],
              "pass", None, "on"),
        "8": ("FAIL", ["unverifiable", "reason: no_test_runner", "s"], "pass", None, "on"),
        "9": ("FAIL", ["pass", "s (0 confirmed, 2 advisory, 0 unverifiable)"], "pass", None, "on"),
    }

    def decide(self, label: str) -> dict:
        verdict, lines, check, safety, gate = self.CASES[label]
        sf = {"verdict": "fail", "reasons": [safety]} if safety else None
        chk = {"verdict": check, "reasons": ["untested_criterion"] if check == "fail" else []}
        return story_gate().decide_gate3(verdict, chk, sf, evidence_result(lines), gate)

    def test_rows_numbered_in_order(self) -> None:
        """Rows 1 to 9, with Story 4's `--prior` row 4a between 4 and 5: each
        row's input reaches that row and no earlier one."""
        self.assertEqual(list(self.CASES), ROW_ORDER)
        for label in ROW_ORDER:
            self.assertEqual(self.decide(label)["row"], label)

    def test_a_tree_mutation_outranks_every_row(self) -> None:
        """DEV-026: the contract's Hardest Constraint makes any tree mutation
        BLOCKED. Row 1 is the only row naming `repro_mutated_tree`, so a FAIL
        re-review with a failed prior check, or a `check` fail, and a mutation
        is BLOCKED, not a recode. [AC-3.1, AC-4.5]"""
        self.assertEqual(self.decide("1")["restart"], "gate3-blocked")
        mutated = ["fail", "reason: repro_mutated_tree src/x.py",
                   "reason: repro_removed %s" % REPRO, "review-override evidence: fail (x)"]
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=mutated), ("BLOCKED", "1"))
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=mutated, check="fail"),
                         ("BLOCKED", "1"))
        self.assertEqual(gate3_report_line(verdict="FAIL", evidence=mutated),
                         "evidence-gate: blocked (repro_mutated_tree src/x.py)")

    def test_each_row_names_its_condition_and_result(self) -> None:
        """Each row's documented condition and result, against the runner:
        BLOCKED and re-spawn rows carry their own restart targets, recodes
        `gate1`, and PASS/PAUSE rows none. The `decide_gate3` docstring lists
        every row's condition."""
        doc = story_gate().decide_gate3.__doc__
        expected = {"1": ("FAIL", "gate3-blocked"), "2": ("FAIL", "gate1"),
                    "3": ("FAIL", "gate1"), "4": ("FAIL", "gate3"), "4a": ("FAIL", "gate1"),
                    "5": ("PAUSE", None), "6": ("FAIL", "gate1"), "7": ("FAIL", "gate1"),
                    "8": ("FAIL", "gate1"), "9": ("PASS", None)}
        for label in ROW_ORDER:
            decision = self.decide(label)
            self.assertEqual((decision["verdict"], decision["restart"]), expected[label], label)
            condition, _ = DECISION_ROWS[label]
            for term in condition:
                self.assertIn(term.replace("`", "").split()[0], doc, "row %s: %s" % (label, term))
        self.assertIn("never DEGRADED", doc)
        self.assertIn("`confirmed`", doc)


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
        """`off` follows `evidence_gate`, on every verdict, and leads the list;
        row 6 reads the switch, not the `switch_off` reason."""
        self.assertEqual(report_forms()[0], "evidence-gate: off")
        decide = story_gate().decide_gate3
        self.assertEqual(decide("FAIL", None, None, None, "off")["row"], "6")
        self.assertIn("`evidence-gate:`", evidence_block())

    def test_report_mirror_prints_off_on_every_verdict(self) -> None:
        for verdict, evidence in (("PASS", []), ("PAUSE", []),
                                  ("FAIL", ["unverifiable", "reason: switch_off"])):
            line = gate3_report_line(verdict=verdict, evidence=evidence, evidence_gate="off")
            self.assertEqual(line, "evidence-gate: off", verdict)
            self.assertEqual(matching_forms(line), ["evidence-gate: off"], verdict)

    def test_downgraded_findings_print_advisory_lines(self) -> None:
        self.assertIn("`evidence-gate advisory: ", evidence_block())

    def test_switch_resolved_once_and_passed_to_every_spawn(self) -> None:
        """Pre-review resolves the switch (story-gate.py); Gate 3 passes its
        `evidence_gate:` value to every spawn and never calls the switch."""
        text = read(IMPLEMENT_STORY)
        self.assertEqual(text.count(SWITCH_COMMAND), 0)
        self.assertIn('("safety-fact", "reviewer-filters", "evidence-gate")', read(STORY_GATE))
        paragraphs = [p for p in gate3().split("\n\n") if p.startswith("**Evidence gate.**")]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        self.assertIn("`evidence_gate:` value", paragraphs[0])
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


class ReplayCase(unittest.TestCase):
    """A temp `git init` copy of the fixture project, and the documented
    `evidence` command run in it."""

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

    def run_gate3_evidence(self, review: str, *, tests: str = RECORDED_RUN,
                           changed: Tuple[str, ...] = tuple(CHANGED)) -> Tuple[List[str], int]:
        """Save the Gate 3 inputs where Gate 3 saves them, then run the
        documented command with its placeholders filled in, adding the
        documented `--prior` flag once the manifest exists."""
        state = self.repo / ".writ" / "state"
        state.mkdir(parents=True, exist_ok=True)
        review_rel = GATE3_REVIEW.replace("<story-stem>", STORY_STEM)
        tests_rel = ".writ/state/" + GATE3_TESTS.replace("<story-stem>", STORY_STEM)
        checks_rel = GATE2_CHECKS.strip("`").replace("<story-stem>", STORY_STEM)
        manifest_rel = MANIFEST.replace("<story-stem>", STORY_STEM)
        (self.repo / review_rel).write_text(review, encoding="utf-8")
        (self.repo / tests_rel).write_text(tests, encoding="utf-8")
        (self.repo / checks_rel).write_text("", encoding="utf-8")

        tokens = evidence_tokens(prior=(self.repo / manifest_rel).exists())
        fill = {"<review>": [review_rel], "<tests>": [tests_rel], "<files>": list(changed),
                "<checks>": [checks_rel], "<manifest>": [manifest_rel]}
        argv: List[str] = []
        for token in tokens:
            if token == "python3":
                argv.append(sys.executable)
            elif token == "scripts/review-override.py":
                argv.append(str(SCRIPT))
            elif token in fill:
                argv.extend(fill[token])
            else:
                argv.append(token.replace("<story-stem>", STORY_STEM))
        self.assertFalse([t for t in argv if "<" in t], argv)
        proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(self.repo),
                              env=replay_env(), timeout=300)
        self.assertIn(proc.returncode, (0, 1), proc.stdout + proc.stderr)
        return proc.stdout.splitlines(), proc.returncode


class ReplayTest(ReplayCase):
    """A saved evaluator FAIL, with and without a confirmed `test` repro, run
    through the documented `evidence` command and the decision rows. [AC-3.5]"""

    def test_fail_without_evidence_becomes_pass_with_advisory_findings(self) -> None:
        """AC-3.5 — no Evidence blocks: row 9, PASS, every finding advisory."""
        out, code = self.run_gate3_evidence(evaluator_fail(with_repro=False))
        self.assertEqual(out[0], "pass", out)
        self.assertEqual(code, 0)
        self.assertEqual(finding_lines(out), {
            "F1": "advisory (no_evidence) at src/limits.py",
            "F2": "advisory (no_evidence) at src/routes.py",
        })
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out), ("PASS", "9"))
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
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out), ("FAIL", "7"))
        confirmed = [k for k, v in findings.items() if v.startswith("confirmed")]
        self.assertEqual(confirmed, ["F1"])
        report = gate3_report_line(verdict="FAIL", evidence=out)
        self.assertEqual(report, "evidence-gate: 1 confirmed, 1 advisory, 0 unverifiable")
        self.assertEqual(len(matching_forms(report)), 1, report)
        self.assertFalse((self.repo / REPRO).exists(), "the repro was left on disk")

    def test_the_decision_rows_outrank_evidence(self) -> None:
        """AC-3.5 — the same confirmed run under rows 2, 5, and 6."""
        out, _ = self.run_gate3_evidence(evaluator_fail(with_repro=True))
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out, check="fail"), ("FAIL", "2"))
        self.assertEqual(gate3_decision(verdict="PASS", evidence=[]), ("PASS", "5"))
        self.assertEqual(gate3_decision(verdict="FAIL", evidence=out, evidence_gate="off"),
                         ("FAIL", "6"))


# ---------------------------------------------------------------------------
# Story 4 of `2026-11-04-evidence-gated-review`: confirmed repros become
# regression tests. Gate 3 binds `<manifest>`, passes `--manifest-out` always
# and `--prior` on every verdict once the manifest exists, recodes on row 4a,
# hands the coder `## Evidence repros`, and runs every manifest path in the
# re-review's recorded run. [AC-4.5]
# ---------------------------------------------------------------------------

PASS_REVIEW = "### EVALUATION_RESULT: PASS\n\n### Summary\nEvery criterion holds.\n"
RE_REVIEW_RUN = (
    "command: python3 -m pytest tests/test_limits.py %s\n"
    "exit code: 0\n"
    "2 passed in 0.01s\n" % REPRO
)


class RecodeBriefTest(unittest.TestCase):
    """The recode brief, the manifest binding, `--prior`, row 4a, and the
    re-review's recorded run in Gate 3. [AC-4.5]"""

    def test_recode_brief_carries_evidence_repros_and_the_no_edit_line(self) -> None:
        """AC-4.5 — one sentence, after the decision table so it covers every
        recode the table names (rows 4a and 7): each `confirmed` `test` repro's
        finding, path, fenced content, and the no-edit instruction. A row 4a
        recode takes them from the `<manifest>` entry, which holds `content`."""
        lines = [l for l in read(IMPLEMENT_STORY).splitlines() if REPROS_HEADING in l]
        self.assertEqual(len(lines), 1, lines)
        brief = lines[0]
        self.assertTrue(brief.startswith("Recode briefs add %s:" % REPROS_HEADING), brief)
        for term in ("each `confirmed` `test` repro's %s finding, path, fenced content"
                     % BRIEF_SOURCE, '"%s"' % NO_EDIT):
            self.assertIn(term, brief)
        block = evidence_block().splitlines()
        self.assertIn(brief, block)
        last_row = max(i for i, l in enumerate(block) if l.startswith("| "))
        self.assertGreater(block.index(brief), last_row)

    def test_manifest_is_bound_once_and_always_passed_as_manifest_out(self) -> None:
        """AC-4.5 — `<manifest>` names the manifest path once; the evidence
        call writes to it, and adds `--prior` only once it exists. Post-review
        defaults `--manifest` to that same path."""
        self.assertEqual(read(IMPLEMENT_STORY).count(MANIFEST), 1)
        self.assertIn("`<manifest>` = `%s`" % MANIFEST, gate3())
        argv = evidence_tokens()
        self.assertEqual(argv[argv.index("--manifest-out") + 1], "<manifest>")
        self.assertNotIn("--prior", argv)
        self.assertIn('"evidence-%s.json"', read(STORY_GATE))

    def test_prior_runs_on_every_verdict_once_the_manifest_exists(self) -> None:
        """AC-4.5 — spec.md § Gate 3 decision row 3a: once the manifest
        exists, every run, the FAIL case included, adds `--prior <manifest>`,
        and the step runs on PASS and PAUSE too."""
        for verdict in ("PASS", "PAUSE", "FAIL"):
            self.assertTrue(story_gate().evidence_runs(verdict, True), verdict)
        argv = " ".join(evidence_tokens(prior=True))
        self.assertIn("--prior <manifest>", argv)

    def test_re_review_recorded_run_includes_every_manifest_path(self) -> None:
        """AC-4.5 — `recorded_test_results` is defined, before any Gate 3
        spawn, as the run of the story's tests and every manifest path, so a
        failing repro makes the whole recorded run non-zero."""
        defs = [l for l in gate3().splitlines() if "`recorded_test_results` = " in l]
        self.assertEqual(len(defs), 1, defs)
        self.assertIn(RECORDED_RUN_DEF, defs[0])
        self.assertLess(gate3().index(defs[0]), gate3().index("**Risk route:**"))

    def test_row_4a_follows_row_4_and_recodes(self) -> None:
        """AC-4.5 — row 4a names the three `--prior` reasons and recodes,
        ahead of row 5, so an agent PASS or PAUSE recodes too."""
        both = ["fail", "reason: repro_modified %s" % REPRO, "review-override evidence: fail (x)"]
        self.assertEqual(gate3_decision(verdict="PASS", evidence=both,
                                        safety="safety_fact_missing"),
                         ("safety-fact routing", "4"))
        self.assertEqual(gate3_decision(verdict="PASS", evidence=[
            "fail", "reason: repro_modified %s" % REPRO, "review-override evidence: fail (x)"]),
            ("FAIL", "4a"))

    def test_generated_copies_carry_the_wiring(self) -> None:
        for rel in ("cursor/plugin/commands/implement-story.md",
                    "plugins/writ/commands/implement-story.md"):
            text = read(REPO_ROOT / rel)
            for term in (REPROS_HEADING, NO_EDIT, BRIEF_SOURCE, RECORDED_RUN_DEF):
                self.assertIn(term, text, rel)
            self.assertIn("story-gate.py run --phase post-review", text, rel)
        # The plugin carries the runner itself, byte for byte.
        self.assertEqual(read(REPO_ROOT / "plugins" / "writ" / "scripts" / "story-gate.py"),
                         read(STORY_GATE))


class ReReviewReplayTest(ReplayCase):
    """The documented command writes the manifest on a confirmed repro, then
    guards the repro on the re-review's PASS. [AC-4.5]"""

    def setUp(self) -> None:
        super().setUp()
        self.manifest = self.repo / MANIFEST.replace("<story-stem>", STORY_STEM)
        out, _ = self.run_gate3_evidence(evaluator_fail(with_repro=True))
        self.assertEqual(out[0], "fail", out)

    def test_confirmed_repro_lands_in_the_manifest(self) -> None:
        """AC-4.5 — the first FAIL records F1's repro at `<manifest>`, with the
        content a row 4a brief restores it from."""
        doc = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], "evidence-manifest-v1")
        self.assertEqual([(r["finding"], r["path"], r["kind"], r["content"])
                          for r in doc["repros"]], [("F1", REPRO, "test", REPRO_BODY)])

    def test_re_review_pass_with_the_repro_in_place_stays_pass(self) -> None:
        """AC-4.5 — the coder created the repro from the brief and the recorded
        run names it and exits 0: row 5, PASS."""
        (self.repo / "tests").mkdir(exist_ok=True)
        (self.repo / REPRO).write_text(REPRO_BODY, encoding="utf-8")
        out, code = self.run_gate3_evidence(PASS_REVIEW, tests=RE_REVIEW_RUN,
                                            changed=tuple(CHANGED) + (REPRO,))
        self.assertEqual(out, ["pass", "reason: prior_ok",
                               "review-override evidence: pass (prior_ok)"])
        self.assertEqual(code, 0)
        self.assertEqual(gate3_decision(verdict="PASS", evidence=out), ("PASS", "5"))
        self.assertEqual(gate3_report_line(verdict="PASS", evidence=out),
                         "evidence-gate: not run (PASS)")

    def test_re_review_pass_without_the_repro_recodes(self) -> None:
        """AC-4.5 — the coder dropped the repro: row 4a, FAIL on a PASS, and
        the report line is the re-review `fail (<reason>)` form."""
        out, code = self.run_gate3_evidence(PASS_REVIEW, tests=RE_REVIEW_RUN)
        self.assertEqual(out[:2], ["fail", "reason: repro_removed %s" % REPRO], out)
        self.assertEqual(code, 1)
        self.assertEqual(gate3_decision(verdict="PASS", evidence=out), ("FAIL", "4a"))
        report = gate3_report_line(verdict="PASS", evidence=out)
        self.assertEqual(report, "evidence-gate: fail (repro_removed %s)" % REPRO)
        self.assertEqual(len(matching_forms(report)), 1, report)


# ---------------------------------------------------------------------------
# Story 5: `/review` evidence gating. `commands/review.md` reads the skill
# after the filters Read, records `#### FM-NNN` blocks, runs `evidence
# --surface review` on the draft, and counts confirmed findings only. The
# reviewer filters stay (spec.md → Amendment). [AC-5.2, AC-5.4, AC-5.5]
# ---------------------------------------------------------------------------

REVIEW_COMMAND = REPO_ROOT / "commands" / "review.md"
REVIEW_GENERATED = ("cursor/plugin/commands/review.md", "plugins/writ/commands/review.md")
FILTERS_PARAGRAPH = (
    "Run `python3 scripts/review-override.py switch --name reviewer-filters` and keep "
    "line 1 (`on` or `off`) for the Step 4 header. On `on`, "
    "`Read skills/review-judgment-filters/SKILL.md` and apply it before Technique 4 "
    "assigns severities and before the Recommendation."
)
FILTERS_HEADER = "> Reviewer filters: on|off"
EVIDENCE_HEADER = "> Evidence gate: on|off|unverifiable (<reason>)"
REVIEW_EVIDENCE_COMMAND = re.compile(r"python3 scripts/review-override\.py evidence [^`\n]*")
UNCONFIRMED = "`Medium (unconfirmed)`"
UNTRUSTED_HEADER = "`> Evidence gate: unverifiable (untrusted_branch)`"
SKILL = REPO_ROOT / "skills" / "evidence-gated-findings" / "SKILL.md"


class ReviewWiringTests(unittest.TestCase):
    """`commands/review.md` wires the evidence gate beside the reviewer
    filters. [AC-5.2, AC-5.4, AC-5.5]"""

    def setUp(self) -> None:
        self.text = read(REVIEW_COMMAND)
        self.opening = slice_between(self.text, "### Step 3:", "#### Technique 1")
        self.technique4 = slice_between(self.text, "#### Technique 4", "#### Technique 5")
        self.step4 = slice_between(self.text, "### Step 4:", "### Step 5:")
        self.completion = slice_between(self.text, "## Completion", "## References")
        for name in ("opening", "technique4", "step4", "completion"):
            self.assertTrue(getattr(self, name), "%s not found in commands/review.md" % name)

    def template(self) -> List[str]:
        """The Step 4 report template, between its markdown fence lines."""
        lines = self.step4.splitlines()
        start = lines.index("```markdown")
        end = lines.index("```", start + 1)
        return lines[start + 1:end]

    def test_step3_reads_the_evidence_skill_after_the_filters_read(self) -> None:
        """AC-5.5 — Step 3 resolves the `evidence-gate` switch and, on `on`,
        reads the evidence skill, on a line after the filters Read."""
        lines = self.opening.splitlines()
        filters = [i for i, l in enumerate(lines) if "`Read skills/review-judgment-filters/" in l]
        evidence = [i for i, l in enumerate(lines) if "`Read %s`" % SKILL_REL in l]
        self.assertEqual(len(filters), 1, lines)
        self.assertEqual(len(evidence), 1, lines)
        self.assertLess(filters[0], evidence[0])
        self.assertIn(SWITCH_COMMAND, lines[evidence[0]])
        self.assertIn("On `on`", lines[evidence[0]])
        self.assertEqual(len([l for l in self.text.splitlines() if SKILL_REL in l]), 1)

    def test_filters_read_switch_line_and_header_sentence_stay(self) -> None:
        """AC-5.5 — the `reviewer-filters` switch line, the filters Read, and
        the sentence that feeds the Step 4 filters header are unchanged."""
        self.assertIn(FILTERS_PARAGRAPH, self.opening.splitlines())

    def test_header_has_both_lines_side_by_side(self) -> None:
        """AC-5.4 — the template header carries `> Evidence gate:` on the line
        after `> Reviewer filters:`, and Step 4 fills it from the run."""
        template = self.template()
        self.assertIn(FILTERS_HEADER, template)
        self.assertIn(EVIDENCE_HEADER, template)
        self.assertEqual(template.index(EVIDENCE_HEADER), template.index(FILTERS_HEADER) + 1)
        self.assertIn("`> Evidence gate:`", self.step4)

    def test_step4_runs_evidence_on_the_draft_then_maps_severities(self) -> None:
        """AC-5.2, AC-5.4 — Step 4 writes the draft, runs `evidence --surface
        review` on it with the diff files, then maps each row: unconfirmed
        Critical or High rows become `Medium (unconfirmed)` and keep their ID
        and description; a run-level `unverifiable` changes no severity."""
        commands = REVIEW_EVIDENCE_COMMAND.findall(self.text)
        self.assertEqual(len(commands), 1, commands)
        tokens = shlex.split(commands[0])
        self.assertEqual(tokens[tokens.index("--surface") + 1], "review")
        self.assertEqual(tokens[tokens.index("--review-output") + 1],
                         ".writ/state/review-[branch-name].md")
        self.assertEqual(tokens[tokens.index("--timeout") + 1], "60")
        self.assertTrue(commands[0].endswith(" --changed <diff files>"), commands[0])
        flat = " ".join(self.step4.split())
        self.assertIn("the Step 1 scope's changed files as `<diff files>`", flat)
        draft = flat.index("draft")
        run = flat.index(commands[0])
        mapping = flat.index(UNCONFIRMED)
        template = flat.index("```markdown")
        self.assertLess(draft, run)
        self.assertLess(run, mapping)
        self.assertLess(mapping, template)
        self.assertIn("keeps its ID and description", flat)
        self.assertRegex(flat, r"`unverifiable`: leave every severity as written")
        self.assertRegex(flat, r"Summary line .*after this step")

    def test_report_template_has_the_evidence_section_after_the_registry(self) -> None:
        """AC-5.5 — the template's `## Evidence` section sits between the
        Failure Modes Registry and the Recommendation."""
        headings = [l for l in self.template() if l.startswith("## ")]
        for heading in ("## Failure Modes Registry", "## Evidence", "## Recommendation"):
            self.assertIn(heading, headings)
        self.assertEqual(headings.index("## Evidence"),
                         headings.index("## Failure Modes Registry") + 1)
        self.assertEqual(headings.index("## Recommendation"), headings.index("## Evidence") + 1)

    def test_technique4_records_one_block_per_critical_or_high_row(self) -> None:
        """AC-5.2 — Technique 4 records one `#### FM-NNN` block per Critical or
        High row under `## Evidence`; any category can confirm, only `test` and
        `security-path` apply, and the Location must be in the diff."""
        flat = " ".join(self.technique4.split())
        for phrase in ("`#### FM-NNN`", "`## Evidence`", "Critical or High row",
                       "read High where the skill says Major",
                       "Any category can confirm", "`test` and `security-path`",
                       "a file in the diff", UNCONFIRMED):
            self.assertIn(phrase, flat)

    def test_recommendation_and_outcome_table_count_confirmed_findings(self) -> None:
        """AC-5.2, AC-5.5 — the Recommendation and every Outcome row count
        confirmed findings only; with none, the report is ready to ship and
        lists the `Medium (unconfirmed)` rows as worth a look."""
        recommendation = [l for l in self.step4.splitlines()
                          if l.startswith("**Recommendation section:**")]
        self.assertEqual(len(recommendation), 1)
        for phrase in ("confirmed", UNCONFIRMED, "worth a look", "ready to ship"):
            self.assertIn(phrase, recommendation[0])
        outcome = slice_between(self.completion, "**Outcome interpretation", "A review with zero")
        self.assertIn("evidence step", outcome.splitlines()[0])
        rows = {r[1].split(" — ")[0]: r[0] for r in table_rows(outcome)}
        self.assertEqual(sorted(rows), ["Code is ready to ship", "Do not ship", "Ship with caution"])
        for result, findings in rows.items():
            self.assertIn("confirmed", findings.lower(), result)
        self.assertIn("critical", rows["Do not ship"].lower())
        self.assertIn("high", rows["Ship with caution"].lower())
        ready = [r for r in table_rows(outcome) if r[1].startswith("Code is ready to ship")][0]
        self.assertIn(UNCONFIRMED, ready[1])
        self.assertIn("worth a look", ready[1])

    def test_step4_always_asks_before_running_repros(self) -> None:
        """AC-5.4 — before every run, Step 4 asks with AskQuestion, saying the
        branch's own test code runs in the user's working tree. A decline, a
        headless run where nobody can be asked, or no answer each skip the run,
        write `untrusted_branch` in the header, and leave every severity as
        written. No author-email rule remains."""
        flat = " ".join(self.step4.split())
        before = flat[:flat.index(REVIEW_EVIDENCE_COMMAND.findall(self.text)[0])]
        self.assertIn("Before every run, ask with AskQuestion", before)
        ask = before[before.index("AskQuestion"):]
        self.assertIn("the branch's own test code in the user's working tree", ask)
        sentence = [s for s in re.split(r"(?<=\.) ", before) if UNTRUSTED_HEADER in s]
        self.assertEqual(len(sentence), 1, before)
        for phrase in ("declines", "headless", "no answer", "skip the run",
                       "leave every severity as written"):
            self.assertIn(phrase, sentence[0])
        for gone in ("%ae", "user.email", "<base>"):
            self.assertNotIn(gone, self.step4)

    def test_step4_stops_on_a_tree_mutation(self) -> None:
        """AC-5.4 — a `repro_mutated_tree` result stops `/review` before the
        `unverifiable` rule: the user is told what changed and that nothing was
        restored, and no Recommendation or `/ship` follows until they decide."""
        bullets = [l for l in self.step4.splitlines() if l.startswith("- ")]
        mutation = [i for i, l in enumerate(bullets) if l.startswith("- `reason: repro_mutated_tree")]
        unverifiable = [i for i, l in enumerate(bullets) if l.startswith("- `unverifiable`")]
        self.assertEqual(len(mutation), 1, bullets)
        self.assertEqual(len(unverifiable), 1, bullets)
        self.assertLess(mutation[0], unverifiable[0])
        line = bullets[mutation[0]]
        for phrase in ("stop", "nothing was restored", "Recommendation", "`/ship`"):
            self.assertIn(phrase, line)
        # Line 1 is `unverifiable` on a mutation, so the order decides the rule.
        self.assertIn("apply the first rule that matches", self.step4)

    def test_gate_off_or_unverifiable_counts_rows_as_written(self) -> None:
        """AC-5.4 — with the gate `off` or `unverifiable`, the Recommendation and
        the Outcome table count every Critical and High row as written."""
        recommendation = [l for l in self.step4.splitlines()
                          if l.startswith("**Recommendation section:**")][0]
        outcome = slice_between(self.completion, "**Outcome interpretation", "A review with zero")
        for text in (recommendation, " ".join(outcome.split())):
            self.assertRegex(text, r"`off` or `unverifiable`, every Critical and High row "
                                   r"counts as written")

    def test_skill_names_kind_unavailable_and_defers_to_review(self) -> None:
        """AC-5.5 — the evidence skill lists `kind_unavailable` in its reason
        table and says `/review` has its own blocking rules in its command."""
        text = read(SKILL)
        self.assertRegex(text, r"(?m)^\| `kind_unavailable` \| ")
        blocking = slice_between(text, "### Which findings can block", "### ")
        self.assertIn("`/review`", blocking)
        self.assertIn("`commands/review.md`", blocking)

    def test_generated_copies_carry_the_wiring(self) -> None:
        """AC-5.4, AC-5.5 — the regenerated command copies carry the evidence
        Read, the run, and both header lines."""
        for rel in REVIEW_GENERATED:
            text = read(REPO_ROOT / rel)
            self.assertIn(SKILL_REL, text, rel)
            self.assertIn("review-override.py evidence --surface review", text, rel)
            self.assertIn(FILTERS_HEADER, text, rel)
            self.assertIn(EVIDENCE_HEADER, text, rel)


# ---------------------------------------------------------------------------
# Story 7: the review panel is removed (ADR-032) [AC-7.2, AC-7.4]
# ---------------------------------------------------------------------------

LEFTOVER_LINE = "`review-panel: removed (ADR-032)`"
PANEL_REJECTION = "`--panel was removed (ADR-032)`"
# The one allowance: a panel token may appear only on a line that points to ADR-032.
PANEL_POINTER = "removed (ADR-032)"
PANEL_TOKENS = ("Review Panel", "--panel")
# technical-spec.md → ## Test Plan: the shipped surfaces the scan reads.
SHIPPED_DIRS = ("commands", "agents", "skills", "adapters", "claude-code", "cursor",
                "plugins", "codex")
SHIPPED_FILES = ("README.md", "SKILL.md")


def panel_scan(root: Path) -> Tuple[int, List[str]]:
    """Scan the shipped paths under `root` for the panel tokens.

    Returns (files read, hits). A hit is `path:line: text` for a line that
    names a token and lacks `removed (ADR-032)`. No `.writ/` directory is
    read, at the root or nested. Undecodable files are skipped: a binary asset
    holds no instruction line."""
    files: List[Path] = []
    for rel in SHIPPED_DIRS:
        for dirpath, dirnames, filenames in os.walk(str(root / rel)):
            dirnames[:] = sorted(d for d in dirnames if d != ".writ")
            files.extend(Path(dirpath) / name for name in sorted(filenames))
    files.extend(root / rel for rel in SHIPPED_FILES if (root / rel).is_file())
    read_count = 0
    hits: List[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        read_count += 1
        for number, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in PANEL_TOKENS) and PANEL_POINTER not in line:
                hits.append("%s:%d: %s" % (path.relative_to(root).as_posix(), number,
                                           line.strip()[:160]))
    return read_count, hits


def plant(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PanelRemovalWiringTest(unittest.TestCase):
    """AC-7.2 — `commands/implement-story.md` keeps no panel wiring, keeps the
    "Reviewer filters." paragraph, and carries the two ADR-032 pointers as its
    only lines containing `removed (ADR-032)`."""

    def setUp(self) -> None:
        self.text = read(IMPLEMENT_STORY)
        self.lines = self.text.splitlines()

    def test_only_the_two_pointer_lines_mention_the_panel(self) -> None:
        pointers = [l for l in self.lines if PANEL_POINTER in l]
        self.assertEqual(len(pointers), 2, pointers)
        self.assertEqual(sum(LEFTOVER_LINE in l for l in pointers), 1, pointers)
        self.assertEqual(sum(PANEL_REJECTION in l for l in pointers), 1, pointers)
        panel = [l for l in self.lines if "panel" in l.lower()]
        self.assertEqual(panel, pointers)

    def test_invocation_has_no_panel_row_and_rejects_the_flag(self) -> None:
        inv = slice_between(self.text, "## Invocation", "## Pipeline")
        rows = [l for l in inv.splitlines() if l.startswith("|") and "--panel" in l]
        self.assertEqual(rows, [])
        self.assertNotIn("conflicts with `--quick`", inv)
        self.assertIn(PANEL_REJECTION, inv)
        self.assertIn("stop with a usage error before any gate; pick no winner", inv)

    def test_leftover_config_line_replaces_the_panel_paragraph_in_gate3(self) -> None:
        self.assertNotIn("**Review panel (opt-in).**", self.text)
        self.assertNotIn("review-panel.py", self.text)
        self.assertEqual(self.text.count(LEFTOVER_LINE), 1)
        self.assertEqual(gate3().count(LEFTOVER_LINE), 1)

    def test_safety_fact_fail_is_one_review_loop_increment(self) -> None:
        """2026-11-06 (lean-story-pipeline Story 3): a safety-fact fail ends in
        Gate 3 FAIL, a recode, and the `gate1` row counts one increment."""
        paragraphs = [p for p in gate3().split("\n\n")
                      if p.startswith("**Safety fact (`safety_fact` on).**")]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        self.assertIn("Gate 3 FAIL", paragraphs[0])
        self.assertNotIn("panel", paragraphs[0])
        row = next(l for l in gate3().splitlines() if l.startswith("| `gate1` |"))
        self.assertIn("one review-loop increment", row)

    def test_overview_gate0_gate35_and_report_name_no_panel(self) -> None:
        blocks = {
            "Overview": slice_between(self.text, "## Overview", "## Required Artifacts"),
            # Story 2 of 2026-11-06-lean-story-pipeline: Gate 4.5 follows Gate 0.
            "Gate 0": slice_between(self.text, "#### Gate 0: Architecture Check",
                                    "#### Gate 4.5:"),
            "Gate 3.5": slice_between(self.text, "#### Gate 3.5:", "#### Gate 4:"),
            "Step 4": slice_between(self.text, "### Step 4: Story Completion",
                                    "## Error Handling"),
        }
        for name, block in blocks.items():
            self.assertTrue(block, name)
            self.assertNotIn("panel", block.lower(), name)
        self.assertNotIn("`review-panel:`", blocks["Step 4"])

    def test_reviewer_filters_paragraph_stays_without_panel_reviewers(self) -> None:
        paragraphs = [p for p in gate3().split("\n\n") if p.startswith("**Reviewer filters.**")]
        self.assertEqual(len(paragraphs), 1, paragraphs)
        paragraph = paragraphs[0]
        self.assertNotIn("panel", paragraph)
        for phrase in ("pre-review's `reviewer_filters:` value",
                       "`reviewer_filters`", "every Gate 3 spawn", "re-review",
                       "`reviewer-filters: <on|off>`"):
            self.assertIn(phrase, paragraph, phrase)


class ShippedPanelScanTests(unittest.TestCase):
    """AC-7.4 — no shipped file names `Review Panel` or `--panel` except on a
    line containing `removed (ADR-032)`. `.writ/` is skipped, and a token
    planted in a temp root fails the scan."""

    def test_shipped_files_name_the_panel_only_beside_adr_032(self) -> None:
        for rel in SHIPPED_DIRS + SHIPPED_FILES:
            self.assertTrue((REPO_ROOT / rel).exists(), rel)
        read_count, hits = panel_scan(REPO_ROOT)
        self.assertGreater(read_count, 100)
        self.assertEqual(hits, [], "\n".join(hits))

    def test_a_planted_token_fails_the_scan(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, "commands/x.md", "- **Review Panel:** gpt-5.6-sol-medium\n")
            plant(root, "plugins/writ/commands/y.md", "ok\nRun `/implement-story story-3 --panel`.\n")
            read_count, hits = panel_scan(root)
        self.assertEqual(read_count, 2)
        self.assertEqual(hits, [
            "commands/x.md:1: - **Review Panel:** gpt-5.6-sol-medium",
            "plugins/writ/commands/y.md:2: Run `/implement-story story-3 --panel`.",
        ])

    def test_pointer_lines_pass_and_writ_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, "commands/x.md",
                  "A `- **Review Panel:**` line prints `review-panel: removed (ADR-032)`.\n"
                  "`--panel` stops with `--panel was removed (ADR-032)`.\n")
            plant(root, "README.md", "No panel tokens here.\n")
            plant(root, ".writ/config.md", "- **Review Panel:** gpt-5.6-sol-medium\n")
            plant(root, "cursor/plugin/.writ/docs/z.md", "- **Review Panel:** x\n")
            read_count, hits = panel_scan(root)
        self.assertEqual(hits, [])
        self.assertEqual(read_count, 2)

    def test_a_pointer_must_be_exact(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, "skills/s/SKILL.md", "`--panel` was removed (see ADR-032).\n")
            _, hits = panel_scan(root)
        self.assertEqual(hits, ["skills/s/SKILL.md:1: `--panel` was removed (see ADR-032)."])


if __name__ == "__main__":
    unittest.main()
