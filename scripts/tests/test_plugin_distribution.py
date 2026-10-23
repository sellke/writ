#!/usr/bin/env python3
"""Static checks for spec `2026-10-22-plugin-distribution`.

Verification Record (Story 1):

- The table under `## Verification Record` in the spec's technical-spec.md has
  the five record columns, at least one data row, a Status per row in the
  anchored grammar written under that heading, and a Source per row that
  starts with `https://`.
- Each row's Claim starts with a unique `V<nn>` ID, and every ID cited on a
  decision's `Rests on:` line names a row whose Status is `verified`.

The record is read with the table grammar of `scripts/gen-platform-trees.py`
(`section`, `first_table`, `cells`), loaded by path, so a change to that
grammar shows up here. Stories 2, 3, and 5 extend the same import.

Covers AC-1.1 and AC-1.5.

Run: uv run --python 3.9 pytest scripts/tests/test_plugin_distribution.py
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "gen-platform-trees.py"
TECH_SPEC = (REPO_ROOT / ".writ" / "specs" / "2026-10-22-plugin-distribution"
             / "sub-specs" / "technical-spec.md")

RECORD_HEADING = "## Verification Record"
RECORD_COLUMNS = ["Claim", "Platform & version", "Observed", "Source", "Status"]
# technical-spec.md -> Verification Record. Anchored at both ends: a version or
# a reason outside the two parentheticals fails.
STATUS_GRAMMAR = re.compile(
    r"^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$"
)
ROW_ID = re.compile(r"^(V\d{2,})\b")
CITED_ID = re.compile(r"\bV\d{2,}\b")


def load_module():
    spec = importlib.util.spec_from_file_location("gen_platform_trees", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def gen():
    return load_module()


def spec_text() -> str:
    return TECH_SPEC.read_text(encoding="utf-8")


def record_rows(gen) -> List[List[str]]:
    """Cells of each data row in the first table under `## Verification Record`,
    after asserting the header is the five record columns."""
    lines = spec_text().splitlines()
    span, missing = gen.section(lines, (RECORD_HEADING,))
    assert span is not None, "technical-spec.md has no %r heading" % missing
    table = gen.first_table(lines, *span)
    assert table, "no table under %r" % RECORD_HEADING
    header = gen.cells(table[0][1])
    assert header == RECORD_COLUMNS, "record columns are %s" % header
    rows = [gen.cells(text) for _, text in table[2:]]
    assert rows, "the Verification Record has no data row"
    return rows


def status_by_id(gen) -> Dict[str, str]:
    statuses = {}  # type: Dict[str, str]
    for row in record_rows(gen):
        match = ROW_ID.match(row[0])
        assert match, "Claim cell has no V<nn> ID: %r" % row[0]
        assert match.group(1) not in statuses, "duplicate row ID %s" % match.group(1)
        statuses[match.group(1)] = row[4]
    return statuses


class TestVerificationRecord:
    def test_rows_have_five_cells(self, gen):
        for row in record_rows(gen):
            assert len(row) == len(RECORD_COLUMNS), "row has %d cells: %r" % (len(row), row)

    def test_status_matches_grammar(self, gen):
        for row in record_rows(gen):
            assert STATUS_GRAMMAR.match(row[4]), "Status %r fails the grammar (row %r)" % (
                row[4], row[0][:60])

    def test_source_is_https_url(self, gen):
        for row in record_rows(gen):
            assert row[3].startswith("https://"), "Source %r is not an https:// URL (row %r)" % (
                row[3], row[0][:60])

    def test_decisions_cite_only_verified_rows(self, gen):
        statuses = status_by_id(gen)
        rests_on = [line for line in spec_text().splitlines()
                    if line.lstrip("-* ").startswith("Rests on:")]
        assert rests_on, "no decision has a 'Rests on:' line"
        for line in rests_on:
            cited = CITED_ID.findall(line)
            assert cited, "'Rests on:' line cites no row: %r" % line
            for row_id in cited:
                assert row_id in statuses, "%s is not a Verification Record row" % row_id
                assert statuses[row_id].startswith("verified "), "%s is %r, not verified" % (
                    row_id, statuses[row_id])
