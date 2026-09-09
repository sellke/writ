#!/usr/bin/env python3
"""Gold round-trip for scripts/goal-emit.py (Story 3). [AC-3.4, AC-3.5]
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "goal-emit.py"
FIXTURES = REPO_ROOT / "scripts" / "tests" / "fixtures" / "goal-emit"
ADAPTER = REPO_ROOT / "adapters" / "claude-code.md"
AC_TOKEN = re.compile(r"AC-\d+\.\d+")


def _run(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _adapter_invoke() -> str:
    text = ADAPTER.read_text(encoding="utf-8")
    marker = "Word the condition as an explicit three-way disjunction:"
    start = text.index(marker)
    fence_open = text.index("```\n", start) + 4
    fence_close = text.index("\n```", fence_open)
    return text[fence_open:fence_close]


class GoalEmitGoldTests(unittest.TestCase):
    def test_fixtures_have_no_ac_tokens(self) -> None:
        for path in FIXTURES.rglob("*"):
            if not path.is_file():
                continue
            body = path.read_text(encoding="utf-8")
            self.assertIsNone(AC_TOKEN.search(body), path)

    def test_loop_yes_emit_matches_gold_and_adapter(self) -> None:
        gold_dir = FIXTURES / "loop-yes"
        card = gold_dir / "card.md"
        gold_goal = (gold_dir / "GOAL.md").read_text(encoding="utf-8")
        gold_verify = (gold_dir / "VERIFY.md").read_text(encoding="utf-8")
        gold_invoke = (gold_dir / "invoke.txt").read_text(encoding="utf-8")
        adapter_invoke = _adapter_invoke()
        self.assertEqual(gold_invoke.rstrip("\n"), adapter_invoke)
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            emitted_goal = (out_dir / "GOAL.md").read_text(encoding="utf-8")
            emitted_verify = (out_dir / "VERIFY.md").read_text(encoding="utf-8")
            self.assertEqual(emitted_goal, gold_goal)
            self.assertEqual(emitted_verify, gold_verify)
            printed = out.split("goal-emit:", 1)[1]
            printed = printed.split("\n", 1)[1]
            self.assertEqual(printed.rstrip("\n"), gold_invoke.rstrip("\n"))
            self.assertEqual(printed.rstrip("\n"), adapter_invoke)

    def test_loop_no_unverifiable_no_dir(self) -> None:
        card = FIXTURES / "loop-no" / "card.md"
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            code, out, _err = _run(
                ["emit", "--card", str(card), "--out", str(out_dir)]
            )
            self.assertEqual(code, 0)
            self.assertIn("unverifiable", out.splitlines()[0])
            self.assertIn("loop_no", out)
            self.assertFalse(out_dir.exists())


if __name__ == "__main__":
    unittest.main()
