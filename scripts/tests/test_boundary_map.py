#!/usr/bin/env python3
"""Tests for scripts/boundary-map.py (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Overlap-present vs overlap-absent JSON maps; malformed story → exit 1;
usage → exit 2. [AC-4.1, AC-4.2, AC-4.4, AC-4.5]
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "boundary-map.py"

WELL_FORMED_STORY = """# Story 1: Fixture

> **Status:** Not Started

## User Story

Fixture.

## Acceptance Criteria

- [ ] Given `AC-4.1`, when it runs, then it passes

## Implementation Tasks

- [ ] 1.1 Create `src/auth/login.ts`
- [ ] 1.2 Modify `src/auth/session.ts`
- [ ] 1.3 Add to `src/lib/utils.ts`
- [ ] 1.4 Update `src/auth/login.test.ts`

## Notes

Ignore `src/other/out-of-scope.ts` here.
"""

OVERLAP_TABLE = """## Check 5 — File overlap

| File / area | Stories sharing | Severity (note / warn) |
|-------------|-----------------|-------------------------|
| `src/lib/utils.ts` | 1, 2, 3 | warn |
| `src/shared/types.ts` | 1, 2 | note |
"""


def _run(args, cwd=None):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _payload(stdout):
    return json.loads(stdout)


class BoundaryMapTests(unittest.TestCase):
    def test_overlap_absent_owned_only(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            code, out, err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0, err)
            payload = _payload(out)
            self.assertEqual(
                set(payload.keys()),
                {"owned", "readable", "out_of_scope"},
            )
            self.assertEqual(
                payload["owned"],
                [
                    "src/auth/login.ts",
                    "src/auth/session.ts",
                    "src/lib/utils.ts",
                    "src/auth/login.test.ts",
                ],
            )
            self.assertEqual(payload["readable"], [])
            self.assertEqual(payload["out_of_scope"], [])
            self.assertNotIn("src/other/out-of-scope.ts", payload["owned"])

    def test_overlap_present_merges_shared_unread_paths(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            overlap = root / "assessment-report.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            overlap.write_text(OVERLAP_TABLE, encoding="utf-8")
            code, out, err = _run(
                [
                    "compute",
                    "--story",
                    str(story),
                    "--repo",
                    str(root),
                    "--overlap",
                    str(overlap),
                ],
            )
            self.assertEqual(code, 0, err)
            payload = _payload(out)
            self.assertIn("src/lib/utils.ts", payload["owned"])
            self.assertNotIn("src/lib/utils.ts", payload["readable"])
            self.assertEqual(payload["readable"], ["src/shared/types.ts"])
            self.assertEqual(payload["out_of_scope"], [])

    def test_malformed_story_missing_tasks_exits_1(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text("# Story\n\nNo tasks.\n", encoding="utf-8")
            code, out, _err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 1)
            self.assertEqual(out.strip(), "")

    def test_malformed_empty_story_exits_1(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text("", encoding="utf-8")
            code, _out, _err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 1)

    def test_missing_story_file_exits_1(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, _out, _err = _run(
                [
                    "compute",
                    "--story",
                    str(root / "missing.md"),
                    "--repo",
                    str(root),
                ],
            )
            self.assertEqual(code, 1)

    def test_usage_missing_flags_exits_2(self):
        code, _out, _err = _run(["compute"])
        self.assertEqual(code, 2)

    def test_usage_missing_subcommand_exits_2(self):
        code, _out, _err = _run([])
        self.assertEqual(code, 2)

    def test_writes_nothing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "story.md"
            story.write_text(WELL_FORMED_STORY, encoding="utf-8")
            before = {p.relative_to(root) for p in root.rglob("*")}
            code, _out, _err = _run(
                ["compute", "--story", str(story), "--repo", str(root)],
            )
            self.assertEqual(code, 0)
            after = {p.relative_to(root) for p in root.rglob("*")}
            self.assertEqual(before, after)


class Gate05WiringTests(unittest.TestCase):
    """AC-4.4 / AC-4.5 — Gate 0.5 runs the script; maps stay advisory."""

    def test_gate_0_5_invokes_compute_and_stays_advisory(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        start = text.index("#### Gate 0.5: Boundary Computation")
        end = text.index("#### Gate 1:", start)
        gate = text[start:end]
        self.assertIn("scripts/boundary-map.py compute", gate)
        self.assertIn("advisory", gate.lower())
        self.assertIn("no hard file locking", gate)

    def test_frontmatter_names_boundary_map(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-story.md").read_text(encoding="utf-8")
        self.assertIn("  - id: gate0_5_boundary\n    script: scripts/boundary-map.py", text)


if __name__ == "__main__":
    unittest.main()
