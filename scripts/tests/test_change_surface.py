#!/usr/bin/env python3
"""Tests for scripts/change-surface.py (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

One fixture per surface class; empty / omitted `--changed` → exit 2.
[AC-4.3, AC-4.4, AC-4.5]
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "change-surface.py"

CLASSES = (
    "style-only",
    "single-component",
    "cross-component",
    "full-stack",
)


def _run(args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr


class ChangeSurfaceTests(unittest.TestCase):
    def test_style_only(self):
        code, out, err = _run(
            ["classify", "--changed", "src/styles/theme.css", "src/app.module.css"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "style-only")

    def test_style_only_tailwind_config(self):
        code, out, err = _run(
            ["classify", "--changed", "tailwind.config.ts"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "style-only")

    def test_single_component_plus_test(self):
        code, out, err = _run(
            [
                "classify",
                "--changed",
                "src/components/Form.tsx",
                "src/components/Form.test.tsx",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "single-component")

    def test_cross_component_shared_hook(self):
        code, out, err = _run(
            ["classify", "--changed", "src/hooks/useAuth.ts"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "cross-component")

    def test_full_stack_schema(self):
        code, out, err = _run(
            ["classify", "--changed", "prisma/schema.prisma"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "full-stack")

    def test_style_plus_migration_classifies_up_to_full_stack(self):
        code, out, err = _run(
            [
                "classify",
                "--changed",
                "src/styles/theme.css",
                "db/migrations/001_init.sql",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "full-stack")

    def test_two_components_classifies_up_to_cross_component(self):
        code, out, err = _run(
            [
                "classify",
                "--changed",
                "src/components/Form.tsx",
                "src/components/List.tsx",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "cross-component")

    def test_empty_changed_exits_2(self):
        code, out, _err = _run(["classify", "--changed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_omitted_changed_exits_2(self):
        code, out, _err = _run(["classify"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_prints_exactly_one_class_token(self):
        code, out, err = _run(["classify", "--changed", "src/lib/utils.ts"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "cross-component")
        self.assertIn(out, CLASSES)
        self.assertEqual(len(out.splitlines()), 1)


class Gate25WiringTests(unittest.TestCase):
    """AC-4.4 / AC-4.5 — Gate 2.5 runs the classifier."""

    def test_gate_2_5_invokes_classify(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 2.5: Change Surface Classification")
        end = text.index("#### Gate 3:", start)
        gate = text[start:end]
        self.assertIn("scripts/change-surface.py classify", gate)

    def test_frontmatter_names_change_surface(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate2_5_surface\n    script: scripts/change-surface.py", text)


if __name__ == "__main__":
    unittest.main()
