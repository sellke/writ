#!/usr/bin/env python3
"""Wiring assertions for Story 4 of `2026-09-26-arch-lint-and-follow-ups`.

Story 4 ships prose, not code: `.writ/docs/architecture-lint.md` and one
step in `commands/create-adr.md`. These tests pin the parts other files
depend on: the four tool names, each tool's detection file as
`scripts/arch-lint.py detect` looks for it (technical-spec §3), the four
example markers, the Gate 2 `none` report line that points readers here,
and the `/create-adr` Enforcement step that links the guide.

Run: python3 scripts/tests/test_architecture_lint_doc.py
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

DOC = REPO_ROOT / ".writ" / "docs" / "architecture-lint.md"
CREATE_ADR = REPO_ROOT / "commands" / "create-adr.md"
DOC_LINK = ".writ/docs/architecture-lint.md"


def load_helper():
    spec = importlib.util.spec_from_file_location(
        "arch_lint", REPO_ROOT / "scripts" / "arch-lint.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()

# File names come from the helper so a new detection name fails here until
# the guide names it too.
DETECTION_FILES = {
    "dependency-cruiser": tuple(HELPER.DEPCRUISE_CONFIGS),
    "import-linter": (".importlinter", "setup.cfg", "[importlinter]",
                      "pyproject.toml", "[tool.importlinter]"),
    "eslint-plugin-boundaries": ("package.json",),
    "ArchUnit": tuple(HELPER.ARCHUNIT_FILES),
}

EXAMPLE_MARKERS = ("forbidden", "layers", "element-types", "layeredArchitecture()")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def after_writing_steps(text: str) -> list:
    """Numbered steps of Step 4's "After writing" list, in order."""
    block = text.split("**After writing:**", 1)[1].split("\n---", 1)[0]
    return re.findall(r"^(\d+)\. (.+)$", block, re.MULTILINE)


class GuideSectionTests(unittest.TestCase):
    """AC-4.1 — why, how Gate 2 finds and runs rulesets, relation to ADRs."""

    def test_doc_exists(self) -> None:
        self.assertTrue(DOC.is_file(), DOC)

    def test_doc_has_the_three_sections(self) -> None:
        text = read(DOC)
        for heading in ("## Why mechanical rules", "## How Gate 2 finds and runs",
                        "## Relation to ADRs"):
            self.assertIn(heading, text)

    def test_doc_describes_every_detect_mode(self) -> None:
        text = read(DOC)
        for mode in ("`run`", "`not-installed`", "`via-eslint`", "`via-tests`"):
            self.assertIn(mode, text)

    def test_doc_links_the_helper_and_its_command(self) -> None:
        text = read(DOC)
        self.assertIn("scripts/arch-lint.py", text)
        self.assertIn("python3 scripts/arch-lint.py detect", text)
        self.assertIn("npx --no-install depcruise", text)
        self.assertIn("lint-imports", text)

    def test_doc_carries_the_state_catalog_none_line(self) -> None:
        self.assertIn("arch-lint: none — see .writ/docs/architecture-lint.md", read(DOC))

    def test_doc_says_a_missing_ruleset_never_blocks(self) -> None:
        self.assertIn("never fails the gate", read(DOC))


class GuideExampleTests(unittest.TestCase):
    """AC-4.2, AC-4.4 — four tools, their detection files, four examples."""

    def test_doc_names_all_four_tools(self) -> None:
        text = read(DOC)
        for tool in DETECTION_FILES:
            self.assertIn(tool, text)

    def test_doc_names_each_detection_file(self) -> None:
        text = read(DOC)
        for tool, files in DETECTION_FILES.items():
            for name in files:
                self.assertIn(name, text, "%s detection file %s" % (tool, name))

    def test_doc_carries_each_example_marker(self) -> None:
        text = read(DOC)
        for marker in EXAMPLE_MARKERS:
            self.assertIn(marker, text)

    def test_each_example_is_a_fenced_block(self) -> None:
        blocks = re.findall(r"^```(\w+)\n(.*?)^```", read(DOC), re.MULTILINE | re.DOTALL)
        bodies = "\n".join(body for _, body in blocks)
        for marker in EXAMPLE_MARKERS:
            self.assertIn(marker, bodies, "example marker outside a code block")
        self.assertIn("ini", {lang for lang, _ in blocks})
        self.assertIn("java", {lang for lang, _ in blocks})

    def test_eslint_example_uses_current_rule_names(self) -> None:
        """AC-4.2: `element-types` is a deprecated alias; the config uses v7 names."""
        blocks = re.findall(r"^```js\n(.*?)^```", read(DOC), re.MULTILINE | re.DOTALL)
        js = "\n".join(blocks)
        self.assertIn('"boundaries/dependencies"', js)
        self.assertIn("policies", js)
        self.assertNotIn('"boundaries/element-types":', js)


class CreateAdrEnforcementTests(unittest.TestCase):
    """AC-4.3, AC-4.4 — one numbered Enforcement step linking the guide."""

    def test_create_adr_links_the_guide(self) -> None:
        self.assertIn(DOC_LINK, read(CREATE_ADR))

    def test_enforcement_step_sits_before_present(self) -> None:
        steps = after_writing_steps(read(CREATE_ADR))
        numbers = [int(n) for n, _ in steps]
        self.assertEqual(numbers, list(range(1, len(steps) + 1)))
        self.assertIn("**Enforcement**", steps[-2][1])
        self.assertIn(DOC_LINK, steps[-2][1])
        for trigger in ("layering", "import direction", "module dependencies"):
            self.assertIn(trigger, steps[-2][1])
        self.assertTrue(steps[-1][1].startswith("Present the completed ADR"))


if __name__ == "__main__":
    unittest.main()
