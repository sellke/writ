#!/usr/bin/env python3
"""Unit tests for scripts/phase-state.py's Story 2 run-record extensions.

Covers the additive `exitCriteria[]`, `terminalStatus`, and `haltReported`
writer subcommands added by 2026-08-12-machine-evaluable-exit-criteria: the
`.class`/`.verdict` enums, the mutual exclusivity of `terminalStatus` and
`haltReported` (a halted-then-resumed-to-completion run must not carry both),
atomic-write discipline, and read/write compatibility with a state file
written before this story existed. The module filename contains a hyphen, so
it is imported by path — the recipe `test_story_deps.py` uses.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

MODULE_PATH = Path(__file__).resolve().parent.parent / "phase-state.py"
_spec = importlib.util.spec_from_file_location("phase_state", MODULE_PATH)
ps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ps)  # type: ignore[union-attr]


def run_cli(*args: str) -> tuple[int, dict]:
    buf = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(buf):
            ps.main(list(args))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    try:
        payload = json.loads(buf.getvalue())
    except json.JSONDecodeError:
        payload = {"_raw": buf.getvalue()}
    return code, payload


def write_state(path: Path, **overrides: Any) -> None:
    """A minimal valid phase-execution-v2 state file, the shape
    `phase-state.py init` produces, with optional field overrides so each
    test can start from a specific fixture shape."""
    state = {
        "schemaVersion": 2,
        "phase": "6",
        "phaseBranch": "phase/6-example",
        "startedAt": "2026-08-12T00:00:00Z",
        "updatedAt": "2026-08-12T00:00:00Z",
        "status": "executing",
        "specOrder": ["spec-a"],
        "specs": {
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "integrated",
            }
        },
        "challenges": [],
        "knowledgeWritten": [],
    }
    state.update(overrides)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


# A representative pre-Story-2 archived record: schemaVersion 2, but no
# exitCriteria, terminalStatus, or haltReported key at all -- exactly the
# shape every file under the gitignored .writ/state/ predates this story
# with, since there is no corpus to migrate (see the format doc's note).
PRE_STORY_2_FIXTURE = {
    "schemaVersion": 2,
    "phase": "10b",
    "phaseBranch": "phase/10-progressive-disclosure",
    "startedAt": "2026-08-12T03:01:13Z",
    "updatedAt": "2026-08-12T15:26:49Z",
    "status": "executing",
    "specOrder": ["spec-a"],
    "specs": {
        "spec-a": {
            "agentRunId": None, "attempts": 1, "blockedBy": [],
            "dependencies": [], "evidence": ["some evidence"],
            "laneBranch": "writ/phase/10b/spec-a",
            "mergeCommit": "abc123", "quarantineBranch": None,
            "status": "integrated", "uatPlan": None, "worktreePath": None,
        }
    },
    "challenges": [],
    "knowledgeWritten": [],
}


class ExitCriteriaWriterTests(unittest.TestCase):
    def test_records_a_new_criterion(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli(
                "record-exit-criterion", "--state", str(state_path),
                "--id", "implement-phase.c1", "--source", "roadmap",
                "--class", "machine", "--verdict", "pass",
                "--evidence", "5/5 specs terminal",
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "recorded")
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(written["exitCriteria"]), 1)
            self.assertEqual(written["exitCriteria"][0], {
                "id": "implement-phase.c1", "source": "roadmap",
                "class": "machine", "verdict": "pass",
                "evidence": "5/5 specs terminal",
            })

    def test_rewriting_the_same_id_updates_in_place(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            run_cli("record-exit-criterion", "--state", str(state_path),
                    "--id", "implement-phase.c1", "--source", "roadmap",
                    "--class", "machine", "--verdict", "fail",
                    "--evidence", "2 specs still pending")
            run_cli("record-exit-criterion", "--state", str(state_path),
                    "--id", "implement-phase.c1", "--source", "roadmap",
                    "--class", "machine", "--verdict", "pass",
                    "--evidence", "5/5 specs terminal")
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(written["exitCriteria"]), 1)
            self.assertEqual(written["exitCriteria"][0]["verdict"], "pass")
            self.assertEqual(written["exitCriteria"][0]["evidence"], "5/5 specs terminal")

    def test_a_different_id_appends_rather_than_overwrites(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            run_cli("record-exit-criterion", "--state", str(state_path),
                    "--id", "implement-phase.c1", "--source", "roadmap",
                    "--class", "machine", "--verdict", "pass", "--evidence", "a")
            run_cli("record-exit-criterion", "--state", str(state_path),
                    "--id", "implement-phase.c2", "--source", "roadmap",
                    "--class", "human", "--verdict", "handed_off", "--evidence", "b")
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual({c["id"] for c in written["exitCriteria"]},
                            {"implement-phase.c1", "implement-phase.c2"})

    def test_invalid_class_is_a_contract_error(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli(
                "record-exit-criterion", "--state", str(state_path),
                "--id", "x", "--source", "roadmap", "--class", "robot",
                "--verdict", "pass", "--evidence", "n/a",
            )
            self.assertEqual(code, 1)
            self.assertEqual(payload["blocker"]["code"], "invalid_criterion")
            self.assertNotIn("exitCriteria", json.loads(state_path.read_text(encoding="utf-8")))

    def test_invalid_verdict_is_a_contract_error(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli(
                "record-exit-criterion", "--state", str(state_path),
                "--id", "x", "--source", "roadmap", "--class", "machine",
                "--verdict", "maybe", "--evidence", "n/a",
            )
            self.assertEqual(code, 1)
            self.assertEqual(payload["blocker"]["code"], "invalid_criterion")


class TerminalStatusWriterTests(unittest.TestCase):
    def test_sets_terminal_status(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli("set-terminal-status", "--state", str(state_path),
                                    "--status", "COMPLETE")
            self.assertEqual(code, 0)
            self.assertEqual(payload["terminalStatus"], "COMPLETE")
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(written["terminalStatus"], "COMPLETE")

    def test_accepts_all_three_enum_values(self) -> None:
        for status in ("COMPLETE", "IMPLEMENTED_PENDING_HUMAN_VALIDATION", "PARTIALLY_COMPLETE"):
            with TemporaryDirectory() as tmp:
                state_path = Path(tmp) / "state.json"
                write_state(state_path)
                code, _ = run_cli("set-terminal-status", "--state", str(state_path),
                                  "--status", status)
                self.assertEqual(code, 0, status)

    def test_invalid_status_is_a_contract_error(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli("set-terminal-status", "--state", str(state_path),
                                    "--status", "DONE")
            self.assertEqual(code, 1)
            self.assertEqual(payload["blocker"]["code"], "invalid_terminal_status")
            self.assertNotIn("terminalStatus", json.loads(state_path.read_text(encoding="utf-8")))

    def test_halt_then_resume_to_completion_clears_stale_halt_reported(self) -> None:
        """The fixture this story exists to guard: a phase halted once
        (`haltReported` present), then `--resume` completes it. terminalStatus
        must be written AND the stale haltReported must be gone in the same
        write, so Story 3's checker stops reporting it `impossible` forever."""
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path, haltReported={
                "unit": "spec", "bound": 12, "reached": 12,
                "lastIntegrated": "spec-a",
            })
            code, payload = run_cli("set-terminal-status", "--state", str(state_path),
                                    "--status", "COMPLETE")
            self.assertEqual(code, 0)
            self.assertTrue(payload["haltReportedCleared"])
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(written["terminalStatus"], "COMPLETE")
            self.assertNotIn("haltReported", written)

    def test_haltReportedCleared_is_false_when_nothing_to_clear(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli("set-terminal-status", "--state", str(state_path),
                                    "--status", "COMPLETE")
            self.assertEqual(code, 0)
            self.assertFalse(payload["haltReportedCleared"])


class HaltReportedWriterTests(unittest.TestCase):
    def test_records_halt_without_setting_terminal_status(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli(
                "record-halt", "--state", str(state_path),
                "--unit", "spec", "--bound", "12", "--reached", "12",
                "--last-integrated", "spec-a",
            )
            self.assertEqual(code, 0)
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(written["haltReported"], {
                "unit": "spec", "bound": 12, "reached": 12,
                "lastIntegrated": "spec-a",
            })
            self.assertNotIn("terminalStatus", written)

    def test_last_integrated_optional(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            run_cli("record-halt", "--state", str(state_path),
                    "--unit", "story", "--bound", "12", "--reached", "5")
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIsNone(written["haltReported"]["lastIntegrated"])

    def test_non_integer_bound_is_a_contract_error(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            code, payload = run_cli(
                "record-halt", "--state", str(state_path),
                "--unit", "spec", "--bound", "many", "--reached", "5",
            )
            self.assertEqual(code, 1)
            self.assertEqual(payload["blocker"]["code"], "invalid_halt")
            self.assertNotIn("haltReported", json.loads(state_path.read_text(encoding="utf-8")))


class AtomicWriteDisciplineTests(unittest.TestCase):
    def test_no_leftover_temp_file_after_any_new_writer(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path)
            run_cli("record-exit-criterion", "--state", str(state_path),
                    "--id", "x", "--source", "roadmap", "--class", "machine",
                    "--verdict", "pass", "--evidence", "n/a")
            run_cli("set-terminal-status", "--state", str(state_path), "--status", "COMPLETE")
            run_cli("record-halt", "--state", str(state_path), "--unit", "spec",
                    "--bound", "12", "--reached", "3")
            entries = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(entries, ["state.json"])

    def test_unknown_fields_survive_every_new_writer(self) -> None:
        """The preserve-unknown-fields rule: a field this reducer doesn't
        recognize (e.g. written by a newer reducer) must round-trip untouched."""
        with TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            write_state(state_path, futureField={"fromANewerReducer": True})
            run_cli("record-exit-criterion", "--state", str(state_path),
                    "--id", "x", "--source", "roadmap", "--class", "machine",
                    "--verdict", "pass", "--evidence", "n/a")
            run_cli("set-terminal-status", "--state", str(state_path), "--status", "COMPLETE")
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(written["futureField"], {"fromANewerReducer": True})


class PreStory2CompatibilityTests(unittest.TestCase):
    """A state file written before exitCriteria/terminalStatus/haltReported
    existed must still load unchanged through the read-only subcommands
    (schemaVersion stays 2; absent fields are simply absent, never a load
    failure) and must accept every new writer cleanly."""

    def _fixture(self, tmp: str) -> Path:
        state_path = Path(tmp) / "archived.json"
        state_path.write_text(json.dumps(PRE_STORY_2_FIXTURE, indent=2, sort_keys=True),
                              encoding="utf-8")
        return state_path

    def test_show_loads_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = self._fixture(tmp)
            before = state_path.read_text(encoding="utf-8")
            code, payload = run_cli("show", "--state", str(state_path))
            self.assertEqual(code, 0)
            self.assertEqual(payload["schemaVersion"], 2)
            self.assertNotIn("exitCriteria", payload)
            self.assertNotIn("terminalStatus", payload)
            self.assertNotIn("haltReported", payload)
            self.assertEqual(state_path.read_text(encoding="utf-8"), before)  # read-only, untouched

    def test_progress_loads_unchanged(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = self._fixture(tmp)
            before = state_path.read_text(encoding="utf-8")
            code, payload = run_cli("progress", "--state", str(state_path))
            self.assertEqual(code, 0)
            self.assertEqual(payload["phase"], "10b")
            self.assertEqual(state_path.read_text(encoding="utf-8"), before)

    def test_reconcile_loads_without_crashing(self) -> None:
        # Not a git repo, so every branch check reports missing -- a mismatch,
        # not a crash -- confirming _load succeeded against the old fixture.
        with TemporaryDirectory() as tmp:
            state_path = self._fixture(tmp)
            code, payload = run_cli("reconcile", "--state", str(state_path), "--repo", tmp)
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "mismatch")

    def test_every_new_writer_accepts_the_old_fixture(self) -> None:
        with TemporaryDirectory() as tmp:
            state_path = self._fixture(tmp)
            code, _ = run_cli("record-exit-criterion", "--state", str(state_path),
                              "--id", "implement-phase.c1", "--source", "roadmap",
                              "--class", "machine", "--verdict", "pass", "--evidence", "ok")
            self.assertEqual(code, 0)
            code, _ = run_cli("set-terminal-status", "--state", str(state_path),
                              "--status", "COMPLETE")
            self.assertEqual(code, 0)
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schemaVersion"], 2)
            # Pre-existing fields untouched by the new writers.
            self.assertEqual(written["specs"]["spec-a"]["mergeCommit"], "abc123")
            self.assertEqual(written["phase"], "10b")
            # New fields now present.
            self.assertEqual(len(written["exitCriteria"]), 1)
            self.assertEqual(written["terminalStatus"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
