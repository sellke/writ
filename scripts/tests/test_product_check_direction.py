#!/usr/bin/env python3
"""Tests for spec `2026-10-01-product-check-direction`.

Product-doc verification reads as a post-implementation check whose findings
feed `/plan-product --reconcile`, and reconcile hands back to delivery. The
eval check `product-check-direction` pins the wording; the mutation tests run
a copy of that check against a temp tree so every pin is proven to bite.
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS = REPO_ROOT / "commands"

DIRECTION = ("Verification surfaces drift after implementation; "
             "`/plan-product --reconcile` realigns the baseline when it does.")
PHASE_LINE = "Product docs may lag what shipped — run /verify-spec --product."
RELEASE_POINTER = "run /verify-spec --product to check product docs against what shipped"
OLD_RELEASE_POINTER = ("consider `/plan-product --reconcile` if `mission-lite.md` "
                       "needs a matching update")
OLD_R4 = "suggest `/verify-spec --product` to confirm"

PINNED_FILES = ("verify-spec.md", "verify-spec.lean.md", "plan-product.md",
                "implement-phase.md", "release.md")


def read(name: str) -> str:
    return (COMMANDS / name).read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    head = text.index(start)
    return text[head:text.index(end, head)]


def run_check_on(edits: Dict[str, Tuple[str, str]]) -> int:
    """Run eval.sh's product-check-direction check on a temp copy of the
    pinned files, with `edits` mapping a file to an (old, new) replacement."""
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "scripts").mkdir()
        (root / "commands").mkdir()
        shutil.copy(REPO_ROOT / "scripts" / "eval.sh", root / "scripts" / "eval.sh")
        for name in PINNED_FILES:
            text = read(name)
            if name in edits:
                old, new = edits[name]
                assert old in text, f"{old!r} not in {name}"
                text = text.replace(old, new)
            (root / "commands" / name).write_text(text, encoding="utf-8")
        proc = subprocess.run(
            ["bash", str(root / "scripts" / "eval.sh"),
             "--check=product-check-direction", f"--report={root / 'report.md'}"],
            capture_output=True, text=True, check=False)
        return proc.returncode


class Story1BoundaryTests(unittest.TestCase):
    """Story 1 of `2026-10-01-product-check-direction`."""

    def test_direction_sentence_replaces_before_after_framing(self):
        """AC-1.1 — one direction sentence; no before/after or /assess-spec analogy."""
        for name in ("verify-spec.md", "verify-spec.lean.md", "plan-product.md"):
            text = read(name)
            self.assertIn(DIRECTION, text, name)
            for old in ("a lint you run before deciding anything",
                        "consistency lint (before)", "lints (before"):
                self.assertNotIn(old, text, name)
            boundary = section(text, "**Boundary (critical):**", "\n\n") \
                if "**Boundary (critical):**" in text else ""
            self.assertNotIn("/assess-spec", boundary, name)

    def test_description_and_modes_row_say_after_implementation(self):
        """AC-1.2 — description names product docs; --product runs after specs ship."""
        text = read("verify-spec.md")
        frontmatter = text.split("---", 2)[1]
        self.assertIn("or with --product the product docs, after implementation",
                      frontmatter)
        row = next(line for line in text.splitlines()
                   if line.startswith("| `/verify-spec --product` |"))
        self.assertIn("After specs ship", row)

    def test_reconcile_points_to_delivery_not_verification(self):
        """AC-1.3 — only Step R2 names /verify-spec --product; R4 hands back."""
        text = read("plan-product.md")
        r2 = section(text, "### Step R2", "### Step R3")
        hits = [line for line in text.splitlines() if "verify-spec --product" in line]
        self.assertTrue(hits)
        for line in hits:
            self.assertIn(line, r2)
        r4 = section(text, "### Step R4", "## Command Process")
        self.assertIn("suggest `/create-spec` for the next roadmap item", r4)
        self.assertIn("roadmap.md", r4)
        self.assertNotIn(OLD_R4, text)
        self.assertNotIn("(before)", section(text, "**Boundary (critical):**", "### Step R1"))

    def test_story1_pins_pass_and_each_mutation_bites(self):
        """AC-1.4 — the check is clean on the tree and fails on each mutation."""
        self.assertEqual(run_check_on({}), 0)
        mutations = [
            {"verify-spec.md": (DIRECTION, "")},
            {"verify-spec.lean.md": (DIRECTION, "")},
            {"plan-product.md": (DIRECTION, "")},
            {"plan-product.md": ("suggest `/create-spec`", OLD_R4)},
        ]
        for name in ("verify-spec.md", "verify-spec.lean.md"):
            for old in ("a lint you run before deciding anything",
                        "consistency lint (before)", "lints (before a decision)"):
                mutations.append({name: (DIRECTION, DIRECTION + " " + old)})
        for edits in mutations:
            with self.subTest(edits=edits):
                self.assertEqual(run_check_on(edits), 1)

    def test_verify_spec_did_not_grow(self):
        """AC-1.5 — verify-spec.md stays at or below its pre-story 35858 bytes."""
        self.assertLessEqual(len((COMMANDS / "verify-spec.md").read_bytes()), 35858)


class Story2CompletionLineTests(unittest.TestCase):
    """Story 2 of `2026-10-01-product-check-direction`."""

    def test_phase_report_line_follows_phase_status_conditionally(self):
        """AC-2.1 — the line sits right after `Phase status:` and is conditional."""
        text = read("implement-phase.md")
        report = section(text, "#### Step 4.2", "**The command never declares")
        lines = report.splitlines()
        status = next(i for i, line in enumerate(lines) if line.startswith("Phase status:"))
        self.assertEqual(lines[status + 1], PHASE_LINE)
        self.assertIn("appears only when `.writ/product/` exists", report)

    def test_release_summary_replaces_reconcile_pointer(self):
        """AC-2.2 — one product pointer on the Roadmap bullet, the old one gone."""
        text = read("release.md")
        summary = section(text, "### Phase 5: Release Summary", "## Changes Released")
        roadmap = [line for line in summary.splitlines() if line.startswith("- **Roadmap:**")]
        self.assertEqual(len(roadmap), 1)
        self.assertIn(RELEASE_POINTER, roadmap[0])
        self.assertNotIn(OLD_RELEASE_POINTER, text)
        self.assertEqual(summary.count("/verify-spec --product"), 1)
        self.assertNotIn("/plan-product --reconcile", summary)
        after = section(text, "## Changes Released", "## Dry Run Mode")
        self.assertIn("The `Roadmap:` line appears only when `.writ/product/` exists", after)

    def test_release_boundary_and_derivative_put_verification_first(self):
        """AC-2.3 — verification, then reconcile; P3 regenerates mission-lite.md."""
        text = read("release.md")
        self.assertIn("`/verify-spec --product`'s P1/P4 checks, then "
                      "`/plan-product --reconcile`", text)
        derivative = next(line for line in text.splitlines()
                          if line.startswith("**Derivative note:**"))
        self.assertIn("`/verify-spec --product` regenerates it (Check P3)", derivative)

    def test_ratchet_repins_are_disclosed(self):
        """AC-2.4 — both re-pins carry a dated comment naming this spec's Story 2."""
        text = (REPO_ROOT / "scripts" / "tests" / "test_governor_enforcement.py").read_text(
            encoding="utf-8")
        marker = "Updated 2026-10-02 (spec 2026-10-01-product-check-direction, Story 2):"
        self.assertIn(marker, text)
        disclosure = text.split(marker, 1)[1].split("KNOWN_OVER_BUDGET", 1)[0]
        for name in ("implement-phase.md", "release.md"):
            self.assertIn(name, disclosure)

    def test_story2_pins_bite_and_issue_is_resolved(self):
        """AC-2.5 — each Story 2 pin fails on its mutation; the issue is resolved."""
        mutations = [
            {"implement-phase.md": ("\n" + PHASE_LINE + "\n", "\n")},
            {"release.md": (RELEASE_POINTER, OLD_RELEASE_POINTER)},
            {"release.md": (RELEASE_POINTER, RELEASE_POINTER + "; " + OLD_RELEASE_POINTER)},
        ]
        for edits in mutations:
            with self.subTest(edits=edits):
                self.assertEqual(run_check_on(edits), 1)
        issue = (REPO_ROOT / ".writ" / "issues" / "improvements" /
                 "2026-10-01-product-lint-misread-as-verify-spec.md").read_text(encoding="utf-8")
        resolution = issue.split("\n## Resolution\n", 1)[1]
        self.assertTrue(resolution.startswith("\n2026-10-02, "))
        self.assertRegex(resolution, r"commit [0-9a-f]{7,40}\b")
        self.assertNotIn("_SHA", resolution)


if __name__ == "__main__":
    unittest.main()
