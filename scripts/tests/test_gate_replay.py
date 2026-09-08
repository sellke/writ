#!/usr/bin/env python3
"""Read-only replay of the 16 committed Stage 1 / Stage 2a baseline records
against the Stage 2b gate scripts (Story 5, AC-5.5).

Disagreement is a note, not a failure. Historical
`test_integrity: nothing_inspected` → unverifiable is expected.
Committed JSON files are not rewritten. [AC-5.4, AC-5.5]
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List


def _load_pipeline_baseline():
    path = REPO_ROOT / "scripts" / "pipeline-baseline.py"
    spec = importlib.util.spec_from_file_location("pipeline_baseline_replay", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINES = (
    REPO_ROOT / ".writ" / "eval" / "baselines" / "2026-09-06-claude-fable-5-1.json",
    REPO_ROOT / ".writ" / "eval" / "baselines" / "2026-09-07-claude-fable-5-1.json",
)
SCRIPTS = REPO_ROOT / "scripts"

NEW_GATES = (
    "gate0_arch",
    "gate3_review",
    "gate5_docs",
    "gate0_5_boundary",
    "gate2_5_surface",
    "gate3_5_drift",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(rec: dict) -> List[str]:
    original = ((rec.get("tests") or {}).get("original") or {})
    files = original.get("files") or []
    return [str(f) for f in files if f]


def _run(argv: List[str]) -> tuple[int, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return proc.returncode, proc.stdout


def _verdict_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if line in ("pass", "fail", "unverifiable"):
            return line
        if line in ("style-only", "single-component", "cross-component", "full-stack"):
            return line
    stripped = stdout.strip()
    if stripped.startswith("{") and "owned" in stripped:
        return "map"
    return "unverifiable"


def replay_record(rec: dict) -> Dict[str, Any]:
    files = _files(rec)
    story_id = rec.get("story_id") or ""
    agent = {g: ((rec.get("gates") or {}).get(g) or {}).get("verdict") for g in NEW_GATES}
    integrity = ((rec.get("rederivation") or {}).get("test_integrity") or {})
    rows: Dict[str, Any] = {
        "story_id": story_id,
        "run": rec.get("run"),
        "agent": agent,
        "rederived": {},
        "notes": [],
    }

    # Gate 0 replay: --changed from recorded test files (post-hoc).
    argv = [sys.executable, str(SCRIPTS / "arch-check.py"), "check",
            "--repo", str(REPO_ROOT), "--story",
            str(REPO_ROOT / ".writ" / "specs" / "2026-09-08-phase11-stage2b-mechanize-the-gates"
                / "user-stories" / "story-5-drift-format-flip-and-watch.md")]
    if files:
        argv.append("--changed")
        argv.extend(files[:8])
    code, out = _run(argv)
    rows["rederived"]["gate0_arch"] = _verdict_line(out)

    argv = [sys.executable, str(SCRIPTS / "review-override.py"), "check",
            "--repo", str(REPO_ROOT)]
    _code, out = _run(argv)
    rows["rederived"]["gate3_review"] = _verdict_line(out)

    argv = [sys.executable, str(SCRIPTS / "docs-check.py"), "check",
            "--repo", str(REPO_ROOT), "--changed", "README.md"]
    _code, out = _run(argv)
    rows["rederived"]["gate5_docs"] = _verdict_line(out)

    argv = [sys.executable, str(SCRIPTS / "boundary-map.py"), "compute",
            "--repo", str(REPO_ROOT), "--story",
            str(REPO_ROOT / ".writ" / "specs" / "2026-09-08-phase11-stage2b-mechanize-the-gates"
                / "user-stories" / "story-5-drift-format-flip-and-watch.md")]
    _code, out = _run(argv)
    rows["rederived"]["gate0_5_boundary"] = "map" if _verdict_line(out) == "map" else _verdict_line(out)

    if files:
        argv = [sys.executable, str(SCRIPTS / "change-surface.py"), "classify",
                "--changed", *files[:8]]
        _code, out = _run(argv)
        rows["rederived"]["gate2_5_surface"] = _verdict_line(out)
    else:
        rows["rederived"]["gate2_5_surface"] = "unverifiable"
        rows["notes"].append("change-surface: no recorded files")

    argv = [sys.executable, str(SCRIPTS / "drift-format.py"), "check",
            "--story",
            str(REPO_ROOT / ".writ" / "specs" / "2026-09-08-phase11-stage2b-mechanize-the-gates"
                / "user-stories" / "story-5-drift-format-flip-and-watch.md")]
    _code, out = _run(argv)
    rows["rederived"]["gate3_5_drift"] = _verdict_line(out)

    if integrity.get("reason") == "nothing_inspected":
        rows["notes"].append("test_integrity nothing_inspected → unverifiable expected")
        if integrity.get("verdict") == "unverifiable":
            rows["notes"].append("historical integrity unverifiable matches helper")

    for gate, claimed in agent.items():
        measured = rows["rederived"].get(gate)
        if claimed and measured and str(claimed).lower() != str(measured).lower():
            rows["notes"].append(
                "disagreement %s agent=%s rederived=%s" % (gate, claimed, measured)
            )
    return rows


class GateReplayTests(unittest.TestCase):
    def test_sixteen_records_replay_without_mutating_baselines(self) -> None:
        before = {path: _sha(path) for path in BASELINES}
        records: List[dict] = []
        for path in BASELINES:
            doc = json.loads(path.read_text(encoding="utf-8"))
            records.extend(doc.get("runs") or [])
        self.assertEqual(len(records), 16)

        table = [replay_record(rec) for rec in records]
        self.assertEqual(len(table), 16)

        expected_notes = 0
        disagreements = 0
        unverifiable = 0
        for row in table:
            for note in row["notes"]:
                if "nothing_inspected" in note:
                    expected_notes += 1
                if note.startswith("disagreement"):
                    disagreements += 1
            for measured in row["rederived"].values():
                if measured == "unverifiable":
                    unverifiable += 1

        # Historical integrity unverifiable is the expected majority.
        self.assertGreaterEqual(expected_notes, 8)
        # Disagreement is a note, not a test failure.
        self.assertIsInstance(disagreements, int)

        after = {path: _sha(path) for path in BASELINES}
        self.assertEqual(before, after)

        # Expose totals for What Was Built.
        print("REPLAY_TABLE rows=%d expected_integrity_notes=%d disagreements=%d unverifiable_cells=%d"
              % (len(table), expected_notes, disagreements, unverifiable))

    def test_new_run_record_carries_watch_field(self) -> None:
        pb = _load_pipeline_baseline()
        rec = pb._null_record("s", 1, "2026-09-08T00:00:00Z")
        rec = pb.assemble_record(
            {"story_id": "s", "run": 1, "started_at": "2026-09-08T00:00:00Z",
             "background_tasks_outstanding": 2},
            None, None, None,
        )
        self.assertEqual(rec["background_tasks_outstanding"], 2)
        self.assertIn("arch_check", pb.REDERIVATION_KEYS)
        self.assertIn("gate0_5_boundary", pb.GATE_NAMES)

    def test_ingest_counts_background_drop_line(self) -> None:
        pb = _load_pipeline_baseline()
        text = "ok\nBackground tasks still running after 600s\nagain\nBackground tasks still running after 600s\n"
        self.assertEqual(pb.count_background_drops(text), 2)
        self.assertEqual(pb.count_background_drops(""), 0)


if __name__ == "__main__":
    unittest.main()
