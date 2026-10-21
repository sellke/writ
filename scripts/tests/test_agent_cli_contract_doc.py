#!/usr/bin/env python3
"""Doc-content tests for Story 1 of `2026-10-12-agent-cli-contract`.

Story 1 ships prose: `.writ/docs/agent-cli-contract.md` and a dated
amendment to ADR-029. These tests pin what Story 3's contract test and
installed-project agents rely on: the section list, a Classification table
that covers every shipped script once, the two network allowances, and an
amendment that leaves ADR-029 rules 1-7 untouched.

The shipped set comes from `is_shippable_script` in `scripts/install.sh`,
never from a list kept here. The five dev-only names below are subtracted
so this file passes both before and after the ship filter excludes them.

Run: uv run pytest scripts/tests/test_agent_cli_contract_doc.py
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import unittest
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
INSTALL_SH = SCRIPTS / "install.sh"
DOC = REPO_ROOT / ".writ" / "docs" / "agent-cli-contract.md"
ADR = REPO_ROOT / ".writ" / "decision-records" / "adr-029-agent-cli-contract.md"

DEV_ONLY = {
    "pipeline-baseline.py",
    "measure-invocation.py",
    "harness-cost.py",
    "prune-ledger.py",
    "spawn-cap.py",
}
SECTIONS = (
    "Scope",
    "Data shape",
    "Check shape",
    "Usage errors",
    "Never spawn or wait unbounded",
    "Network",
    "State",
    "Runtime",
    "Adding a script",
    "Classification",
)
SHAPES = {"data", "check"}
ALLOWANCES = {"network: opt-in", "bounded-wait"}
NETWORK_ROWS = {"jev-judge.py", "app-verify.py"}

AMENDMENT_LINE = (
    "*Amended 2026-10-12 by "
    "[2026-10-12-agent-cli-contract](../specs/2026-10-12-agent-cli-contract/spec.md):*"
)
# sha256 of ADR-029 from "### The agent CLI contract" through the end of
# rule 7's line, taken before the amendment. Any edit to rules 1-7 changes it.
RULES_SHA256 = "1a8245d00310d03e4889271a9c36d330d2ca680f7d91cd5b33c47ee65f1cf93f"
RULE7_PREFIX = "7. **Document subcommands"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def shipped_scripts() -> Set[str]:
    """Run the real `is_shippable_script` over `scripts/*`; keep *.py/*.sh."""
    text = read(INSTALL_SH)
    match = re.search(r"^is_shippable_script\(\) \{\n.*?^\}\n", text, re.M | re.S)
    if match is None:
        raise AssertionError("cannot load is_shippable_script from scripts/install.sh")
    names = sorted(p.name for p in SCRIPTS.iterdir() if p.is_file())
    script = match.group(0) + (
        'for f in "$@"; do if is_shippable_script "$f"; then echo "$f"; fi; done\n')
    out = subprocess.run(["bash", "-c", script, "bash"] + names,
                         capture_output=True, text=True, check=True).stdout
    return {n for n in out.split() if n.endswith((".py", ".sh"))} - DEV_ONLY


def section(text: str, heading: str) -> str:
    """Body of `## heading` up to the next `## ` heading."""
    match = re.search(r"^## %s\n(.*?)(?=^## |\Z)" % re.escape(heading), text, re.M | re.S)
    if match is None:
        raise AssertionError("no '## %s' section in %s" % (heading, DOC))
    return match.group(1)


def split_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_table(body: str) -> List[List[str]]:
    """First markdown table in `body`: header row, then data rows."""
    lines = body.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("|")), None)
    if start is None:
        raise AssertionError("no classification table in %s" % DOC)
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        rows.append(split_row(line))
    return [rows[0]] + rows[2:]  # drop the |---| separator


def classification() -> Dict[str, List[str]]:
    """Map script name -> [shape, allowances, callers]; fails on duplicates."""
    table = parse_table(section(read(DOC), "Classification"))
    rows: Dict[str, List[str]] = {}
    for cells in table[1:]:
        name = cells[0].strip("`")
        if name in rows:
            raise AssertionError("%s appears twice in the Classification table" % name)
        rows[name] = cells[1:]
    return rows


def allowances(cell: str) -> Set[str]:
    return {a.strip() for a in cell.split(",") if a.strip()}


def text_after_table(body: str) -> str:
    lines = body.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("|"))
    end = next((i for i in range(start, len(lines)) if not lines[i].startswith("|")),
               len(lines))
    return "\n".join(lines[end:])


class SectionTests(unittest.TestCase):
    def test_doc_has_every_section(self) -> None:
        """AC-1.1 — the doc has a `## ` heading for each of the ten sections."""
        self.assertTrue(DOC.is_file(), "missing %s" % DOC)
        headings = re.findall(r"^## (.+)$", read(DOC), re.M)
        for name in SECTIONS:
            self.assertIn(name, headings)

    def test_scope_names_the_ship_filter_and_data_file(self) -> None:
        """AC-1.1 — Scope ties the contract to is_shippable_script and excludes the JSON data file."""
        body = section(read(DOC), "Scope")
        self.assertIn("is_shippable_script", body)
        self.assertIn("jev-thresholds.json", body)

    def test_network_lists_scanned_modules(self) -> None:
        """AC-1.1 — Network names the flagged modules and exempts urllib.parse."""
        body = section(read(DOC), "Network")
        for module in ("urllib.request", "urllib.error", "http.client", "socket",
                       "requests", "urllib.parse"):
            self.assertIn("`%s`" % module, body)

    def test_adding_a_script_names_the_contract_test(self) -> None:
        """AC-1.1 — Adding a script points at the contract test command."""
        body = section(read(DOC), "Adding a script")
        self.assertIn("uv run pytest scripts/tests/test_agent_cli_contract.py", body)


class ClassificationTests(unittest.TestCase):
    def test_header_columns(self) -> None:
        """AC-1.2 — the table columns are Script | Shape | Allowances | Callers."""
        header = parse_table(section(read(DOC), "Classification"))[0]
        self.assertEqual(header, ["Script", "Shape", "Allowances", "Callers"])

    def test_every_shipped_script_has_exactly_one_row(self) -> None:
        """AC-1.2 — table rows equal the shipped *.py/*.sh set minus the five dev-only scripts."""
        rows = set(classification())
        shipped = shipped_scripts()
        self.assertEqual(sorted(shipped - rows), [], "shipped but no row")
        self.assertEqual(sorted(rows - shipped), [], "row but not shipped")

    def test_dev_only_scripts_only_in_note_below_table(self) -> None:
        """AC-1.2 — the five dev-only scripts and the JSON data file sit in a note, not the table."""
        body = section(read(DOC), "Classification")
        rows = set(classification())
        note = text_after_table(body)
        for name in sorted(DEV_ONLY) + ["jev-thresholds.json"]:
            self.assertNotIn(name, rows)
            self.assertIn(name, note)

    def test_shape_allowances_and_callers_are_valid(self) -> None:
        """AC-1.2 — Shape is data or check, Allowances come from the two names, Callers is non-empty."""
        for name, (shape, allow, callers) in classification().items():
            self.assertIn(shape, SHAPES, name)
            self.assertLessEqual(allowances(allow), ALLOWANCES, name)
            self.assertTrue(callers, "%s has no callers" % name)

    def test_network_allowance_only_on_two_rows(self) -> None:
        """AC-1.3 — jev-judge and app-verify carry network: opt-in and bounded-wait; no other row is network."""
        rows = classification()
        for name in NETWORK_ROWS:
            self.assertEqual(allowances(rows[name][1]), ALLOWANCES, name)
        others = {n for n, cells in rows.items() if "network: opt-in" in allowances(cells[1])}
        self.assertEqual(others, NETWORK_ROWS)

    def test_test_integrity_is_not_bounded_wait(self) -> None:
        """AC-1.3 — test-integrity's while True walks folders; it is not marked as a wait."""
        self.assertEqual(allowances(classification()["test-integrity.py"][1]), set())


class AdrAmendmentTests(unittest.TestCase):
    def contract_section(self) -> str:
        text = read(ADR)
        start = text.index("### The agent CLI contract")
        return text[start:text.index("### Contribution", start)]

    def test_rules_one_to_seven_unchanged(self) -> None:
        """AC-1.4 — the heading through rule 7 is byte-identical to the pre-change ADR."""
        text = read(ADR)
        start = text.index("### The agent CLI contract")
        end = text.index("\n", text.index(RULE7_PREFIX, start))
        digest = hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()
        self.assertEqual(digest, RULES_SHA256)

    def test_amendment_follows_rule_seven(self) -> None:
        """AC-1.4 — the dated amendment line sits after rule 7, inside the contract section."""
        body = self.contract_section()
        self.assertIn(AMENDMENT_LINE, body)
        self.assertLess(body.index(RULE7_PREFIX), body.index(AMENDMENT_LINE))

    def test_amendment_records_each_change(self) -> None:
        """AC-1.4 — the amendment covers two shapes, error beside blocker, usage errors, bounded waits, dev-only."""
        body = self.contract_section()
        block = body[body.index(AMENDMENT_LINE):]
        for needle in ("data", "check", "`error`", "`blocker`", "stderr", "`orch`",
                       "timeout", "Dev-only", "agent-cli-contract.md"):
            self.assertIn(needle, block)


STORY4_SCRIPTS = ("test-integrity.py", "revert-resolve.py", "knowledge-consolidate.py",
                  "change-surface.py", "boundary-map.py", "goal-emit.py",
                  "verdict-provenance.py", "gen-codex-agent-tomls.py", "roadmap-sync.py")


class ConformanceNoteTests(unittest.TestCase):
    def test_no_note_describes_old_output_or_in_place_writes(self) -> None:
        """AC-1.1, AC-4.5 — State names no in-place writer; no note says what a Story 4 script prints "today"."""
        text = read(DOC)
        self.assertNotRegex(section(text, "State"), r"(?i)in place")
        notes = text.split("### Notes", 1)[1] if "### Notes" in text else ""
        for line in notes.splitlines():
            if any("`%s`" % name in line for name in STORY4_SCRIPTS):
                self.assertNotRegex(line, r"(?i)\btoday\b", line)


class SelfCitationTests(unittest.TestCase):
    def test_every_test_names_its_ac_id(self) -> None:
        """AC-1.5 — every test in this file names a Story 1 AC ID in its docstring."""
        for case in (SectionTests, ClassificationTests, AdrAmendmentTests, ConformanceNoteTests, SelfCitationTests):
            for name in dir(case):
                if not name.startswith("test_"):
                    continue
                doc = getattr(case, name).__doc__ or ""
                self.assertRegex(doc, r"\bAC-1\.[1-5]\b", "%s.%s" % (case.__name__, name))


if __name__ == "__main__":
    unittest.main()
