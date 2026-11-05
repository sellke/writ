#!/usr/bin/env python3
"""Checks for Story 1 of spec `2026-11-04-evidence-gated-review`.
[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]

The story ships records, not code, so these checks read the files directly:

- `.writ/decision-records/adr-032-evidence-gated-review.md` has the header
  lines of ADR-031 (Date, Status Accepted, Category, Deciders @AdamSellke,
  Origin, Amends), the Context, Decision, Decision Drivers, Alternatives, and
  Consequences sections, at least one negative consequence, and no relative
  link to a missing file [AC-1.1].
- Its inventory table has one row for each of the 13 named review surfaces
  [AC-1.2].
- Each row names the fact, the cost in spawns and instruction bytes, a verdict
  from keep / replace / demote / remove, and a reason. Each verdict matches
  spec.md Scope Boundaries and Removals as the 2026-11-04 Amendment changes
  them; the reviewer filters row is keep and cites the removal trial [AC-1.3].
- Its Removals section names every file in the Safety Fact floor and Review
  panel tables of technical-spec.md, plus the removed sections, keys, flag,
  and functions. It labels the floor a change, lists no reviewer-filters item
  as removed, and no other part of the ADR says the filters are removed. The
  pruned-instructions ledger has no row for any of it [AC-1.4].
- ADR-028's header block has an `Amended by` line that links ADR-032 and
  covers the review panel. Roadmap Phase 15's Features list has one unchecked
  line for this spec [AC-1.5].

Run: uv run --isolated --python 3.9 --with pytest pytest scripts/tests/test_adr_032_inventory.py
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ID = "2026-11-04-evidence-gated-review"

DECISIONS = REPO_ROOT / ".writ" / "decision-records"
ADR = DECISIONS / "adr-032-evidence-gated-review.md"
ADR_028 = DECISIONS / "adr-028-behavioral-verification-and-cross-family-panels.md"
LEDGER = DECISIONS / "pruned-instructions-ledger.md"
TECH_SPEC = REPO_ROOT / ".writ" / "specs" / SPEC_ID / "sub-specs" / "technical-spec.md"
ROADMAP = REPO_ROOT / ".writ" / "product" / "roadmap.md"

ORIGIN_LINK = "(../issues/improvements/2026-11-03-minimize-adversarial-review-surface.md)"
ADR_028_LINK = "(adr-028-behavioral-verification-and-cross-family-panels.md)"
ADR_032_LINK = "[ADR-032](adr-032-evidence-gated-review.md)"

SECTION_HEADINGS = (
    "## Decision",
    "## Context and Problem Statement",
    "## Decision Drivers",
    "## Alternatives Considered",
    "## Consequences",
)

INVENTORY_HEADING = "## Review-Surface Inventory"
INVENTORY_HEADER = ["Surface", "Fact it tries to establish",
                    "Cost (spawns; instruction bytes)", "Verdict", "Reason"]
VERDICTS = ("keep", "replace", "demote", "remove")

# One row per surface named in AC-1.2, with the verdict spec.md sets:
# - keep: spec.md Scope Boundaries → Excluded (Gate 0 arch check, /security-audit,
#   visual-qa-agent, the Jev shadow, create-spec Step 2.6c, discovery prompts),
#   and the reviewer filters, which spec.md → Amendment (2026-11-04) keeps on
#   the removal trial's verdict.
# - remove: spec.md Business Rules (Expanded) → Removals (the review panel), and
#   Gate 0 divergence, which design-divergence Story 6 removed on 2026-11-04.
# - demote: Gate 3 agents and /review stay, but an unbacked finding becomes
#   advisory (spec.md Deliverable, Must Include 3 and 5).
# - replace: the Safety Fact floor `traced` (a reading rung) becomes `tested`.
EXPECTED_VERDICTS = (
    ("gate 0 architecture check", "keep"),
    ("gate 0 divergence", "remove"),  # design-divergence Story 6, merged a6a8e8c
    ("evaluator-agent", "demote"),
    ("review-agent", "demote"),
    ("reviewer filters", "keep"),
    ("safety fact", "replace"),
    ("review panel", "remove"),
    ("/review", "demote"),
    ("jev shadow", "keep"),
    ("/security-audit", "keep"),
    ("spec analysis (create-spec step 2.6c)", "keep"),
    ("visual-qa-agent", "keep"),
    ("discovery challenge prompts", "keep"),
)

# The removal trial that kept the reviewer filters (spec.md → Amendment).
REMOVAL_TRIAL_LINK = "(../specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md)"

# technical-spec.md § Removals: the two tables whose files ADR-032 must name.
REMOVAL_TABLES = ("### Safety Fact floor (Story 6)", "### Review panel (Story 7)")
# Rows that name test files or regenerated trees, not removed product files.
NON_FILE_ROWS = ("Tests", "Generated trees")

# Removed keys, flag, report line, eval check, and functions, plus the changed
# floor constant, written in code spans in the ADR.
REMOVED_CODE_NAMES = (
    "Review Panel", "--panel", "review-panel:", "review-panel",
    "status", "tally", "resolve", "config_value", "slug_vendor",
    "origin_vendor", "load_tally", "cmd_tally", "cmd_status", "FLOOR",
)
# Removed paragraphs, named by their bold titles, and the trimmed words.
REMOVED_PARAGRAPHS = ("Review panel (opt-in)", "Review panel (ADR-028)", "panel reviewers")
FLOOR_HEADING = "### Safety Fact floor (Story 6)"

# Reviewer-filter items that the Amendment keeps. None may appear in Removals.
KEPT_FILTER_ITEMS = (
    "skills/review-judgment-filters/", "`reviewer-filters`", "`Reviewer Filters`",
    "`reviewer_filters`", "### Reviewer Filters",
)
# Claims that the filters are removed, compared lowercased with whitespace
# collapsed. The ADR said these before the Amendment.
FILTER_REMOVAL_CLAIMS = (
    "the reviewer filters and the review panel are removed",
    "the filters and the panel go",
    "removes the filters",
    "remove the reviewer filters",
    "the reviewer filters are removed",
    "takes over",
)

# scripts/prune-ledger.py BASE_FILES: the only files the ledger covers.
LEDGER_FILES = ("system-instructions.md", "commands/_preamble.md")
LEDGER_FORBIDDEN = ("review panel", "review-panel", "adr-032", "evidence-gated")

ROADMAP_LINE = re.compile(
    r"^- \[ \] \*\*[^*]+\*\* `Effort: (XS|S|M|L|XL)` — `" + re.escape(SPEC_ID) + r"`(:|$)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError("%s does not exist" % path.relative_to(REPO_ROOT))
    return path.read_text(encoding="utf-8")


def header_block(text: str) -> List[str]:
    """The `> ` lines right after the H1 title, before any other line."""
    lines = text.splitlines()
    block: List[str] = []
    started = False
    for line in lines[1:]:
        if line.startswith(">"):
            started = True
            block.append(line)
        elif started or line.strip():
            break
    return block


def header_values(text: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in header_block(text):
        match = re.match(r"^> \*\*([^*]+):\*\*\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def section(text: str, heading: str) -> str:
    """Body from an exact `## ` heading line to the next `## ` heading."""
    lines = text.splitlines()
    if heading not in lines:
        raise AssertionError("missing heading: %s" % heading)
    start = lines.index(heading) + 1
    body: List[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def subsection(text: str, heading: str) -> str:
    """Body from an exact `### ` heading line to the next `#` heading of level 2 or 3."""
    lines = text.splitlines()
    if heading not in lines:
        raise AssertionError("missing heading: %s" % heading)
    start = lines.index(heading) + 1
    body: List[str] = []
    for line in lines[start:]:
        if line.startswith("## ") or line.startswith("### "):
            break
        body.append(line)
    return "\n".join(body)


def cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def first_table(text: str) -> Tuple[List[str], List[List[str]]]:
    """Header cells and data rows of the first table in `text`."""
    rows: List[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            rows.append(line)
        elif rows:
            break
    if len(rows) < 2:
        raise AssertionError("no table found")
    return cells(rows[0]), [cells(row) for row in rows[2:]]


def surface_key(cell: str) -> str:
    return cell.replace("`", "").strip().lower()


def relative_links(text: str) -> List[str]:
    targets = []
    for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        targets.append(target.split("#", 1)[0])
    return targets


def inventory_rows() -> List[List[str]]:
    header, rows = first_table(section(read(ADR), INVENTORY_HEADING))
    if header != INVENTORY_HEADER:
        raise AssertionError("inventory header is %r" % header)
    return rows


# ---------------------------------------------------------------------------
# AC-1.1: header, sections, negative consequence, links
# ---------------------------------------------------------------------------


class AdrHeaderTest(unittest.TestCase):
    """AC-1.1: the header block follows ADR-031's layout."""

    def setUp(self) -> None:
        self.text = read(ADR)
        self.values = header_values(self.text)

    def test_title_names_adr_032(self) -> None:
        self.assertTrue(self.text.startswith("# ADR-032: "), self.text[:80])

    def test_header_has_every_required_line(self) -> None:
        for key in ("Date", "Status", "Category", "Deciders", "Origin", "Amends"):
            self.assertIn(key, self.values, "missing header line: %s" % key)
            self.assertTrue(self.values[key], "empty header line: %s" % key)

    def test_date_and_status(self) -> None:
        self.assertRegex(self.values["Date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(self.values["Status"], "Accepted")

    def test_deciders_name_the_maintainer(self) -> None:
        self.assertIn("@AdamSellke", self.values["Deciders"])

    def test_origin_links_the_issue(self) -> None:
        self.assertIn(ORIGIN_LINK, self.values["Origin"])

    def test_amends_names_adr_028_for_the_review_panel(self) -> None:
        amends = self.values["Amends"]
        self.assertIn("[ADR-028]" + ADR_028_LINK, amends)
        self.assertIn("review panel", amends.lower())


class AdrSectionsTest(unittest.TestCase):
    """AC-1.1: the five sections, a negative consequence, and resolving links."""

    def setUp(self) -> None:
        self.text = read(ADR)

    def test_required_sections_present(self) -> None:
        lines = self.text.splitlines()
        for heading in SECTION_HEADINGS:
            self.assertIn(heading, lines, "missing section: %s" % heading)

    def test_header_block_precedes_every_section(self) -> None:
        lines = self.text.splitlines()
        last_header = max(i for i, line in enumerate(lines) if line.startswith("> **"))
        first_section = min(i for i, line in enumerate(lines) if line.startswith("## "))
        self.assertLess(last_header, first_section)

    def test_consequences_name_a_negative_consequence(self) -> None:
        body = section(self.text, "## Consequences")
        self.assertIn("**Negative", body)
        negative = body.split("**Negative", 1)[1]
        bullets = [line for line in negative.splitlines() if line.startswith("- ")]
        self.assertGreaterEqual(len(bullets), 1, "no negative consequence bullet")

    def test_every_relative_link_resolves(self) -> None:
        targets = relative_links(self.text)
        self.assertTrue(targets, "the ADR has no relative links")
        missing = [t for t in targets if not (ADR.parent / t).resolve().exists()]
        self.assertEqual(missing, [])


# ---------------------------------------------------------------------------
# AC-1.2 and AC-1.3: the inventory table
# ---------------------------------------------------------------------------


class InventoryRowsTest(unittest.TestCase):
    """AC-1.2: one row for each of the 13 named surfaces."""

    def test_one_row_per_named_surface(self) -> None:
        names = [surface_key(row[0]) for row in inventory_rows()]
        self.assertEqual(len(names), 13, names)
        self.assertEqual(sorted(names), sorted(name for name, _ in EXPECTED_VERDICTS))


class InventoryCellsTest(unittest.TestCase):
    """AC-1.3: fact, cost, verdict, and reason in every row."""

    def setUp(self) -> None:
        self.rows = inventory_rows()

    def test_every_row_has_five_filled_cells(self) -> None:
        for row in self.rows:
            self.assertEqual(len(row), 5, row)
            for cell in row:
                self.assertTrue(cell, row)
                self.assertNotIn("<br", cell, row)

    def test_cost_names_spawns_bytes_and_what_was_measured(self) -> None:
        for row in self.rows:
            cost = row[2]
            self.assertRegex(cost, r"Spawns: \d", row[0])
            self.assertRegex(cost, r"Bytes: \d[\d,]*", row[0])
            self.assertRegex(cost, r"`[^`]+\.(md|py)`", row[0])

    def test_verdict_is_one_of_four_words(self) -> None:
        for row in self.rows:
            self.assertIn(row[3], VERDICTS, row[0])

    def test_verdict_matches_the_spec(self) -> None:
        expected = dict(EXPECTED_VERDICTS)
        for row in self.rows:
            self.assertEqual(row[3], expected[surface_key(row[0])], row[0])

    def _reason(self, surface: str) -> str:
        return [r for r in self.rows if surface_key(r[0]) == surface][0][4]

    def test_divergence_reason_names_both_trials(self) -> None:
        reason = self._reason("gate 0 divergence").lower()
        self.assertIn("removal trial", reason)
        self.assertIn("design-divergence", reason)

    def test_filters_reason_cites_the_removal_trial_and_the_amendment(self) -> None:
        reason = self._reason("reviewer filters")
        self.assertIn(REMOVAL_TRIAL_LINK, reason)
        self.assertIn("removal trial", reason.lower())
        self.assertIn("F01", reason)
        self.assertIn("Amendment", reason)


# ---------------------------------------------------------------------------
# AC-1.4: the removal list and the ledger
# ---------------------------------------------------------------------------


def technical_spec_files() -> List[str]:
    """Backticked paths in the File column of the two removal tables."""
    text = read(TECH_SPEC)
    paths: List[str] = []
    for heading in REMOVAL_TABLES:
        _, rows = first_table(subsection(text, heading))
        for row in rows:
            if row[0] in NON_FILE_ROWS:
                continue
            paths.extend(re.findall(r"`([^`]+)`", row[0]))
    return paths


class RemovalListTest(unittest.TestCase):
    """AC-1.4: ADR-032 names every removed file, section, and key."""

    def setUp(self) -> None:
        self.removals = section(read(ADR), "## Removals")

    def test_technical_spec_tables_are_parsed(self) -> None:
        self.assertGreaterEqual(len(technical_spec_files()), 12)

    def test_names_every_file_in_the_technical_spec_tables(self) -> None:
        missing = [path for path in technical_spec_files() if path not in self.removals]
        self.assertEqual(missing, [])

    def test_names_removed_keys_switch_flag_and_functions(self) -> None:
        missing = [name for name in REMOVED_CODE_NAMES if "`%s`" % name not in self.removals]
        self.assertEqual(missing, [])

    def test_names_removed_paragraphs(self) -> None:
        missing = [title for title in REMOVED_PARAGRAPHS if title not in self.removals]
        self.assertEqual(missing, [])

    def test_floor_is_labeled_a_change(self) -> None:
        self.assertIn("change, not a removal", subsection(self.removals, FLOOR_HEADING))

    def test_lists_no_reviewer_filter_item_as_removed(self) -> None:
        listed = [item for item in KEPT_FILTER_ITEMS if item in self.removals]
        self.assertEqual(listed, [])


class FilterClaimsTest(unittest.TestCase):
    """AC-1.4: no part of the ADR says the reviewer filters are removed."""

    def test_no_filter_removal_claim(self) -> None:
        text = re.sub(r"\s+", " ", read(ADR)).lower()
        found = [claim for claim in FILTER_REMOVAL_CLAIMS if claim in text]
        self.assertEqual(found, [])


class LedgerTest(unittest.TestCase):
    """AC-1.4: the ledger gets no rows for this spec.

    The ledger is append-only and other specs may add rows, so the check is
    on content, not a pinned row count: every row names one of the two files
    the ledger covers, and no row names this spec's removals.
    """

    def setUp(self) -> None:
        lines = read(LEDGER).splitlines()
        start = [i for i, line in enumerate(lines) if line.startswith("| Date |")][0]
        self.rows = [cells(line) for line in lines[start + 2:] if line.startswith("|")]

    def test_every_row_names_a_ledger_file(self) -> None:
        self.assertTrue(self.rows)
        for row in self.rows:
            self.assertIn(row[1], LEDGER_FILES, row)

    def test_no_row_names_this_spec_or_its_removals(self) -> None:
        for row in self.rows:
            line = " | ".join(row).lower()
            for term in LEDGER_FORBIDDEN:
                self.assertNotIn(term, line, row)


# ---------------------------------------------------------------------------
# AC-1.5: ADR-028 header and the roadmap line
# ---------------------------------------------------------------------------


class Adr028AmendedByTest(unittest.TestCase):
    """AC-1.5: ADR-028's header block names ADR-032 for the review panel."""

    def test_header_has_one_amended_by_line_for_adr_032(self) -> None:
        lines = [line for line in header_block(read(ADR_028))
                 if line.startswith("> **Amended by:**") and ADR_032_LINK in line]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("review panel", lines[0].lower())


class RoadmapLineTest(unittest.TestCase):
    """AC-1.5: Phase 15's Features list has one unchecked line for this spec.

    Story 7 checks the line off; it updates this assertion when it does.
    """

    def test_phase_15_features_list_the_spec_once_unchecked(self) -> None:
        text = read(ROADMAP)
        phase = [line for line in text.splitlines() if line.startswith("## Phase 15:")]
        self.assertEqual(len(phase), 1, phase)
        features = subsection(section(text, phase[0]), "### Features")
        lines = [line for line in features.splitlines() if SPEC_ID in line]
        self.assertEqual(len(lines), 1, lines)
        self.assertRegex(lines[0], ROADMAP_LINE)
        self.assertNotIn("filters", lines[0].lower())


if __name__ == "__main__":
    unittest.main()
