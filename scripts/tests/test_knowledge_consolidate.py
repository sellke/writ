#!/usr/bin/env python3
"""CLI output tests for scripts/knowledge-consolidate.py (agent CLI contract,
Story 4 of `2026-10-12-agent-cli-contract`).

The reducer's detection logic is covered by `scripts/eval-knowledge-consolidate.py`.
This file covers the output contract: JSON by default, `--json` a no-op, and
`--pretty` printing the markdown report byte for byte as the script printed it
by default before Story 4. The reports under
`fixtures/knowledge-consolidate/report-*.md` were captured from the unmodified
script against `fixtures/knowledge-consolidate/ledger/`, with the temp folder
replaced by `{TMP}`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "knowledge-consolidate.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "knowledge-consolidate"
LEDGER = FIXTURES / "ledger"
PLACEHOLDER = "{TMP}"


class LedgerCopy:
    """A temp repo holding a copy of the fixture ledger at `.writ/knowledge`."""

    def __enter__(self) -> "LedgerCopy":
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.knowledge = self.root / ".writ" / "knowledge"
        shutil.copytree(str(LEDGER), str(self.knowledge))
        return self

    def __exit__(self, *exc) -> None:
        self._tmp.cleanup()

    def run(self, *flags: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--knowledge-dir", str(self.knowledge),
             "--repo-root", str(self.root), *flags],
            capture_output=True, text=True)

    def normalize(self, text: str) -> str:
        return text.replace(str(self.root), PLACEHOLDER)


def capture(mode: str) -> str:
    return (FIXTURES / ("report-%s.md" % mode)).read_text(encoding="utf-8")


class PrettyReportTests(unittest.TestCase):
    def test_pretty_dry_run_matches_capture(self) -> None:
        """AC-4.2 — --pretty --dry-run prints the captured markdown report."""
        with LedgerCopy() as ledger:
            result = ledger.run("--pretty", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(ledger.normalize(result.stdout), capture("dry-run"))

    def test_pretty_apply_matches_capture(self) -> None:
        """AC-4.2 — --pretty --apply on a temp copy prints the captured report."""
        with LedgerCopy() as ledger:
            result = ledger.run("--pretty", "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(ledger.normalize(result.stdout), capture("apply"))


class JsonDefaultTests(unittest.TestCase):
    def test_default_is_one_compact_json_document(self) -> None:
        """AC-4.2 — no output flag prints one compact JSON document and exits 0."""
        with LedgerCopy() as ledger:
            result = ledger.run()
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(result.stdout, json.dumps(payload) + "\n")

    def test_json_flag_is_a_no_op(self) -> None:
        """AC-4.2 — --json still exits 0 and prints the same document as the default."""
        with LedgerCopy() as ledger:
            default = ledger.run()
            flagged = ledger.run("--json")
            self.assertEqual(flagged.returncode, 0, flagged.stderr)
            self.assertEqual(flagged.stdout, default.stdout)

    def test_dry_run_leaves_fixture_ledger_unchanged(self) -> None:
        """AC-4.2 — the default dry run writes nothing to the ledger it reads."""
        with LedgerCopy() as ledger:
            before = {p: p.read_bytes() for p in sorted(ledger.knowledge.rglob("*.md"))}
            ledger.run()
            after = {p: p.read_bytes() for p in sorted(ledger.knowledge.rglob("*.md"))}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
