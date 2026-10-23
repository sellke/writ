#!/usr/bin/env python3
"""Static checks for spec `2026-10-22-prompting-guide`.

The guide at `.writ/docs/prompting-guide.md` is read as text. These tests pin
the parts of it that other commands cite by heading or by name:

- The file exists and has fewer than 150 lines, headings and blank lines
  included (AC-1.1).
- The H2 headings are exactly `## What a request carries`, `## Recipes`,
  `## Pitfalls`, in that order, and the first H2 holds three list items that
  begin `- **Goal**`, `- **Done check**`, `- **Proof**` (AC-1.2).
- `## Recipes` holds five H3 recipes in a fixed order. Each has one `Weak:`,
  one `Strong:`, and one `Route:` line, and each `Route:` line names the
  command for its recipe (AC-1.3).
- No Markdown link target and no backticked path starts with
  `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, or
  `.writ/product/` (AC-1.4).

The pitfalls list and the prose standard (AC-1.5) are read by hand; the
em-dash count is part of Story 1's verification, not a test here.

Run: uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE_REL = ".writ/docs/prompting-guide.md"
GUIDE = REPO_ROOT / GUIDE_REL

LINE_BUDGET = 150

H2_HEADINGS = ["## What a request carries", "## Recipes", "## Pitfalls"]

PART_PREFIXES = ["- **Goal**", "- **Done check**", "- **Proof**"]

# (H3 heading, command the Route line must name, text the Route line must not carry)
RECIPES = [
    ("### An unsettled idea", "/prototype", "--no-diverge"),
    ("### A bug or a small change", "/prototype --no-diverge", None),
    ("### A feature", "/create-spec", None),
    ("### Roadmap work", "/implement-phase", None),
    ("### A why or how question", "/research", None),
]
RECIPE_LABELS = ("Weak:", "Strong:", "Route:")

INTERNAL_PREFIXES = (
    ".writ/research/",
    ".writ/decision-records/",
    ".writ/specs/",
    ".writ/product/",
)

HEADING = re.compile(r"^(#{1,6}) \S")
LINK_TARGET = re.compile(r"\]\(([^)]*)\)")
CODE_SPAN = re.compile(r"`([^`]+)`")


def text() -> str:
    assert GUIDE.exists(), "%s does not exist" % GUIDE_REL
    return GUIDE.read_text(encoding="utf-8")


def lines() -> List[str]:
    return text().splitlines()


def section(body: List[str], heading: str) -> List[str]:
    """Lines under `heading` up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    starts = [i for i, line in enumerate(body) if line.rstrip() == heading]
    if not starts:
        pytest.fail("heading not found: %r" % heading)
    out = []  # type: List[str]
    for line in body[starts[0] + 1:]:
        m = HEADING.match(line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return out


def test_exists_and_budget():
    # AC-1.1
    count = len(lines())
    assert count < LINE_BUDGET, "%s has %d lines; the budget is under %d" % (
        GUIDE_REL,
        count,
        LINE_BUDGET,
    )


def test_headings():
    # AC-1.2
    found = [line.rstrip() for line in lines() if line.startswith("## ")]
    assert found == H2_HEADINGS, "H2 headings are %r, expected %r" % (found, H2_HEADINGS)


def test_parts():
    # AC-1.2
    body = section(lines(), H2_HEADINGS[0])
    items = [line for line in body if line.startswith("- ")]
    assert len(items) == 3, "expected three parts under %r, found %d: %r" % (
        H2_HEADINGS[0],
        len(items),
        items,
    )
    for item, prefix in zip(items, PART_PREFIXES):
        assert item.startswith(prefix), "part %r does not begin %r" % (item, prefix)


def test_recipes():
    # AC-1.3
    recipes = section(lines(), "## Recipes")
    found = [line.rstrip() for line in recipes if line.startswith("### ")]
    expected = [heading for heading, _, _ in RECIPES]
    assert found == expected, "recipe headings are %r, expected %r" % (found, expected)

    for heading, command, forbidden in RECIPES:
        block = section(recipes, heading)
        for label in RECIPE_LABELS:
            matches = [line for line in block if line.startswith(label)]
            assert len(matches) == 1, "%r has %d %r lines, expected one" % (
                heading,
                len(matches),
                label,
            )
        route = next(line for line in block if line.startswith("Route:"))
        assert command in route, "%r routes %r, expected %r" % (heading, route, command)
        if forbidden:
            assert forbidden not in route, "%r route %r must not carry %r" % (
                heading,
                route,
                forbidden,
            )
        if heading == "### A why or how question":
            assert "/why" in route, "%r route %r does not mention /why" % (heading, route)


def test_no_internal_links():
    # AC-1.4
    content = text()
    refs = LINK_TARGET.findall(content) + CODE_SPAN.findall(content)
    bad = [ref for ref in refs if ref.startswith(INTERNAL_PREFIXES)]
    assert not bad, "the guide links Writ-internal paths: %r" % bad
