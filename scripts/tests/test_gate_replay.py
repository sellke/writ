#!/usr/bin/env python3
"""Read-only replay of the 16 committed Stage 1 / Stage 2a baseline records
against the Stage 2b gate scripts (Story 5, AC-5.5).

A gate is replayed only from inputs the record itself carries. The records
come from runs in another repository (the `story_id` paths are not in this
repo) and carry one list of paths: `tests.original.files`. So:

- `gate2_5_surface` (`change-surface.py classify --changed`) is replayed per
  record from that file list.
- The other five gates need the record's story file, spec folder, drift log,
  review output, or changed source files. None of those is in the record or
  in this repo, so each cell is `not_replayable` with a reason. Feeding a
  stand-in (this spec's Story 5, `README.md`, no `--spec`) would print the
  same verdict on every row and is not a measurement of the record.

Disagreement is a note, not a failure. Historical
`test_integrity: nothing_inspected` is expected. Committed JSON files are
not rewritten. [AC-5.4, AC-5.5]

Run with `-s` to print the per-row table and the `REPLAY_TABLE` totals.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional


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

# Why each gate cannot be replayed from a baseline record. The record has
# `story_id` (a path in the benchmarked repo, absent here) and the original
# story's test files; nothing else these scripts read.
NOT_REPLAYABLE = {
    "gate0_arch": "record_spec_absent",          # story-deps graph of the record's spec
    "gate3_review": "record_spec_absent",        # --spec / story for ac-trace
    "gate5_docs": "record_checkout_absent",      # changed source exports + that repo's docs
    "gate0_5_boundary": "record_story_absent",   # the record's story file
    "gate3_5_drift": "record_story_absent",      # story + drift log + review output
}

SURFACE_CLASSES = ("style-only", "single-component", "cross-component", "full-stack")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(rec: dict) -> List[str]:
    original = ((rec.get("tests") or {}).get("original") or {})
    files = original.get("files") or []
    return [str(f) for f in files if f]


def _record_story(rec: dict) -> Optional[Path]:
    """The record's story file, if it exists in this repo."""
    story_id = rec.get("story_id") or ""
    if "/" not in story_id:
        return None
    spec, story = story_id.split("/", 1)
    path = REPO_ROOT / ".writ" / "specs" / spec / "user-stories" / ("%s.md" % story)
    return path if path.is_file() else None


def _run(argv: List[str]) -> tuple[int, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return proc.returncode, proc.stdout


def _surface(stdout: str) -> str:
    for line in stdout.splitlines():
        if line in SURFACE_CLASSES:
            return line
    return "unverifiable"


def _load_records() -> List[dict]:
    records: List[dict] = []
    for path in BASELINES:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for rec in doc.get("runs") or []:
            rec = dict(rec)
            rec["_baseline"] = path.name[:10]
            records.append(rec)
    return records


def replay_record(rec: dict) -> Dict[str, Any]:
    files = _files(rec)
    agent = {g: ((rec.get("gates") or {}).get(g) or {}).get("verdict") for g in NEW_GATES}
    integrity = ((rec.get("rederivation") or {}).get("test_integrity") or {})
    row: Dict[str, Any] = {
        "story_id": rec.get("story_id") or "",
        "run": rec.get("run"),
        "baseline": rec.get("_baseline"),
        "agent": agent,
        "rederived": {},
        "notes": [],
    }

    for gate, reason in NOT_REPLAYABLE.items():
        row["rederived"][gate] = {"status": "not_replayable", "reason": reason}

    if files:
        _code, out = _run([sys.executable, str(SCRIPTS / "change-surface.py"),
                           "classify", "--changed", *files])
        row["rederived"]["gate2_5_surface"] = {"status": "replayed", "value": _surface(out)}
    else:
        row["rederived"]["gate2_5_surface"] = {
            "status": "not_replayable", "reason": "record_has_no_files"}

    if integrity.get("reason") == "nothing_inspected":
        row["notes"].append("test_integrity nothing_inspected -> unverifiable expected")

    # Compare only replayed cells that also carry an agent verdict.
    for gate, cell in row["rederived"].items():
        claimed = agent.get(gate)
        if cell["status"] != "replayed" or not claimed:
            continue
        if str(claimed).lower() != str(cell["value"]).lower():
            row["notes"].append(
                "disagreement %s agent=%s rederived=%s" % (gate, claimed, cell["value"]))
    return row


def totals(table: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"rows": len(table), "cells": 0, "replayed": 0, "not_replayable": 0,
           "compared": 0, "agree": 0, "disagree": 0, "expected_integrity_notes": 0}
    for row in table:
        for gate, cell in row["rederived"].items():
            out["cells"] += 1
            out[cell["status"]] += 1
            if cell["status"] == "replayed" and row["agent"].get(gate):
                out["compared"] += 1
        for note in row["notes"]:
            if "nothing_inspected" in note:
                out["expected_integrity_notes"] += 1
            if note.startswith("disagreement"):
                out["disagree"] += 1
    out["agree"] = out["compared"] - out["disagree"]
    return out


def _cell_text(agent: Optional[str], cell: Dict[str, Any]) -> str:
    left = agent or "-"
    if cell["status"] == "replayed":
        return "%s->%s" % (left, cell["value"])
    return "%s->n/r" % left


class GateReplayTests(unittest.TestCase):
    def test_sixteen_records_replay_without_mutating_baselines(self) -> None:
        before = {path: _sha(path) for path in BASELINES}
        records = _load_records()
        self.assertEqual(len(records), 16)

        table = [replay_record(rec) for rec in records]
        t = totals(table)
        self.assertEqual(t["rows"], 16)
        self.assertEqual(t["cells"], 16 * len(NEW_GATES))
        # Categories are disjoint: every cell is replayed or not_replayable.
        self.assertEqual(t["replayed"] + t["not_replayable"], t["cells"])
        self.assertEqual(t["agree"] + t["disagree"], t["compared"])
        self.assertLessEqual(t["compared"], t["replayed"])
        # Historical integrity unverifiable is the expected majority.
        self.assertGreaterEqual(t["expected_integrity_notes"], 8)

        after = {path: _sha(path) for path in BASELINES}
        self.assertEqual(before, after)

        for row in table:
            print("REPLAY_ROW %s %s r%s %s" % (
                row["baseline"], row["story_id"].rsplit("/", 1)[-1], row["run"],
                " ".join("%s=%s" % (g, _cell_text(row["agent"].get(g), row["rederived"][g]))
                         for g in NEW_GATES)))
        print("REPLAY_TABLE rows=%(rows)d cells=%(cells)d replayed=%(replayed)d "
              "not_replayable=%(not_replayable)d compared=%(compared)d agree=%(agree)d "
              "disagree=%(disagree)d expected_integrity_notes=%(expected_integrity_notes)d" % t)

    def test_constant_input_gates_are_marked_not_replayable(self) -> None:
        for rec in _load_records():
            # If a future baseline records a story that lives in this repo,
            # the story-dependent gates can be replayed and this test must be
            # extended rather than keep reporting them as not_replayable.
            self.assertIsNone(_record_story(rec), rec.get("story_id"))
            row = replay_record(rec)
            for gate in NEW_GATES:
                cell = row["rederived"][gate]
                self.assertIsInstance(cell, dict, (gate, cell))
            for gate in ("gate0_arch", "gate3_review", "gate5_docs",
                         "gate0_5_boundary", "gate3_5_drift"):
                self.assertEqual(row["rederived"][gate]["status"], "not_replayable", gate)
                self.assertTrue(row["rederived"][gate]["reason"], gate)
            surface = row["rederived"]["gate2_5_surface"]
            self.assertEqual(surface["status"], "replayed")
            self.assertIn(surface["value"], SURFACE_CLASSES)

    def test_new_run_record_carries_watch_field(self) -> None:
        pb = _load_pipeline_baseline()
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
