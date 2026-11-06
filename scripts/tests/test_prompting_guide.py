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

Story 2 adds two checks beside the guide:

- `test_readme_links_guide` reads `README.md` from `## Quick Start` to the
  next H2 and asserts that slice names `.writ/docs/prompting-guide.md`
  (AC-2.2). It pins the path only. The exact pointer sentence and its place
  above the five-command table (AC-2.1) are read by hand, because the
  front-door spec later appends a `/writ` clause to the same paragraph.
- `test_ships` extracts `is_shippable_writ_doc` from `scripts/install.sh`
  and `scripts/update.sh` with `sed`, sources it in a `bash` subprocess, and
  asserts that calling it with `prompting-guide.md` exits 0 (AC-2.3). An
  empty extraction fails with its own message naming the script and the
  function: fix the test's extraction, not the guide.

AC-2.4 is the run of this file (seven tests, and one test file for the
guide) and AC-2.5 is `bash scripts/eval.sh`. Both are verification runs,
not assertions here.

Run: uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py
"""

from __future__ import annotations

import re
import subprocess
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
    ("### A why or how question", "/why", None),
]
RECIPE_LABELS = ("Weak:", "Strong:", "Route:")

INTERNAL_PREFIXES = (
    ".writ/research/",
    ".writ/decision-records/",
    ".writ/specs/",
    ".writ/product/",
)

README = REPO_ROOT / "README.md"
QUICK_START = "## Quick Start"

SHIP_FUNCTION = "is_shippable_writ_doc"
SHIP_SCRIPTS = ["scripts/install.sh", "scripts/update.sh"]
GUIDE_NAME = Path(GUIDE_REL).name
# Exit code the bash snippet uses when the sed extraction is empty, so the
# test can tell "function missing or restructured" from "function rejects
# the file" (is_shippable_writ_doc itself returns 0 or 1).
NO_FUNCTION = 64
# $1 is the script path and $2 the filename; both arrive as positional
# arguments to `bash -c`, never interpolated into this string. The function
# is sourced from a here-string, not `source <(sed ...)`: on macOS bash 3.2
# that process-substitution form defines nothing and reports no error.
SHIP_SNIPPET = r'''
fn=$(sed -n '/^is_shippable_writ_doc()/,/^}/p' "$1")
[ -n "$fn" ] || exit 64
source /dev/stdin <<<"$fn"
is_shippable_writ_doc "$2"
'''

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
            assert "/research" in route, "%r route %r does not name /research" % (heading, route)
    assert "when it ships" not in text(), "the guide still says 'when it ships'"


def test_no_internal_links():
    # AC-1.4
    content = text()
    refs = LINK_TARGET.findall(content) + CODE_SPAN.findall(content)
    bad = [ref for ref in refs if ref.startswith(INTERNAL_PREFIXES)]
    assert not bad, "the guide links Writ-internal paths: %r" % bad


def test_readme_links_guide():
    # AC-2.2; AC-2.1 (the exact sentence and its place) is read by hand.
    assert README.exists(), "README.md does not exist"
    body = README.read_text(encoding="utf-8").splitlines()
    quick_start = "\n".join(section(body, QUICK_START))
    assert GUIDE_REL in quick_start, "README.md section %r does not link %s" % (
        QUICK_START,
        GUIDE_REL,
    )


def test_ships():
    # AC-2.3
    for script_rel in SHIP_SCRIPTS:
        script = REPO_ROOT / script_rel
        assert script.exists(), "%s does not exist" % script_rel
        proc = subprocess.run(
            ["bash", "-c", SHIP_SNIPPET, "bash", str(script), GUIDE_NAME],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == NO_FUNCTION:
            pytest.fail(
                "sed found no %s() in %s; fix this test's extraction, not the guide"
                % (SHIP_FUNCTION, script_rel)
            )
        assert proc.returncode == 0, "%s %s exits %d in %s (stderr: %s)" % (
            SHIP_FUNCTION,
            GUIDE_NAME,
            proc.returncode,
            script_rel,
            proc.stderr.strip(),
        )
