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
REPO_ROOT = Path(__file__).resolve().parents[2]
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


class KnowledgeWritebackPayloadShapeTests(unittest.TestCase):
    """2026-09-05-phase11-repair-and-baseline Story 1 (AC-1.3).

    The phase-close writeback shredded ten ledger entries because a candidate
    whose `evidence` arrived as a plain string was iterated character by
    character: one `- <char>` bullet per character, and `related_artifacts`
    full of `/` and `.` because `_looks_like_path` admitted single characters.
    These tests pin the repaired shape."""

    EVIDENCE = ("2026-08-11-loop-bounds re-verification (all citations shifted +6); "
                ".writ/specs/archive/2026-08-11-component-contract/spec.md Story 1 AC")

    def _candidate(self, **overrides: Any) -> dict:
        cand = {
            "id": "cand-1",
            "title": "Cite anchor text, not line numbers",
            "statement": "Anchor spec citations to text a sibling spec cannot shift.",
            "generalizes": True,
            "evidence": self.EVIDENCE,
        }
        cand.update(overrides)
        return cand

    def _write(self, tmp: str, cand: dict) -> tuple[dict, Path]:
        knowledge = Path(tmp) / ".writ" / "knowledge"
        (knowledge / "lessons").mkdir(parents=True)
        result = ps.knowledge_writeback([cand], knowledge, set())
        return result, knowledge

    def test_string_evidence_becomes_one_full_bullet(self) -> None:
        with TemporaryDirectory() as tmp:
            result, knowledge = self._write(tmp, self._candidate())
            self.assertEqual(len(result["written"]), 1, result)
            entries = list((knowledge / "lessons").glob("*.md"))
            self.assertEqual(len(entries), 1)
            text = entries[0].read_text(encoding="utf-8")
            self.assertIn(f"- {self.EVIDENCE}\n", text)
            bullets = [ln for ln in text.splitlines() if ln.startswith("- ")]
            for bullet in bullets:
                self.assertGreater(len(bullet[2:].strip()), 1, f"single-character bullet: {bullet!r}")
            self.assertIn("## TL;DR\n\nAnchor spec citations", text)

    def test_string_evidence_yields_no_single_character_related_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            _, knowledge = self._write(tmp, self._candidate())
            text = next((knowledge / "lessons").glob("*.md")).read_text(encoding="utf-8")
            frontmatter = text.split("---")[1]
            for line in frontmatter.splitlines():
                if line.startswith("  - "):
                    self.assertGreater(len(line[4:].strip()), 1, f"single-character artifact: {line!r}")
            # The path-like token inside the prose is not extracted from a
            # string payload (the string is one evidence item, not a path);
            # an explicit string `artifacts` is normalized the same way.
            self.assertIn("related_artifacts: []", text)

    def test_string_artifacts_is_normalized_to_a_list(self) -> None:
        with TemporaryDirectory() as tmp:
            cand = self._candidate(artifacts="commands/implement-story.md")
            _, knowledge = self._write(tmp, cand)
            text = next((knowledge / "lessons").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("related_artifacts:\n  - commands/implement-story.md\n", text)
            self.assertNotIn("  - c\n", text)

    def test_list_evidence_keeps_only_multi_character_path_tokens(self) -> None:
        with TemporaryDirectory() as tmp:
            cand = self._candidate(evidence=["/", ".", "commands/ship.md", "transcript 7f3a"])
            _, knowledge = self._write(tmp, cand)
            text = next((knowledge / "lessons").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("related_artifacts:\n  - commands/ship.md\n---", text)

    def test_empty_statement_is_rejected_not_written(self) -> None:
        with TemporaryDirectory() as tmp:
            result, knowledge = self._write(tmp, self._candidate(statement=""))
            self.assertEqual(result["written"], [])
            self.assertEqual(len(result["rejected"]), 1)
            self.assertIn("statement", result["rejected"][0]["reason"])
            self.assertEqual(list((knowledge / "lessons").glob("*.md")), [])

    def test_looks_like_path_rejects_single_characters(self) -> None:
        for token in ("/", ".", " / ", ""):
            self.assertFalse(ps._looks_like_path(token), token)
        self.assertTrue(ps._looks_like_path("commands/ship.md"))
        self.assertTrue(ps._looks_like_path("README.md"))

    def test_as_list_normalizes_scalars_sequences_and_none(self) -> None:
        self.assertEqual(ps._as_list(None), [])
        self.assertEqual(ps._as_list("one string"), ["one string"])
        self.assertEqual(ps._as_list(["a", None, "b"]), ["a", "b"])
        self.assertEqual(ps._as_list(("a", "b")), ["a", "b"])

    def test_rejection_gates_each_name_their_reason(self) -> None:
        """Every D6 gate rejects with a reason a human can act on, and a rejected
        candidate never reaches disk. `evidence` normalization feeds the
        `unsupported` gate: None, an empty string, and a list of blanks are all
        'no evidence', not one bullet of nothing."""
        cases = [
            ({"generalizes": False}, "one-off"),
            ({"evidence": None}, "unsupported"),
            ({"evidence": ""}, "unsupported"),
            ({"evidence": ["", "   "]}, "unsupported"),
            ({"adr_scale": True}, "adr-scale"),
        ]
        for overrides, expected in cases:
            with self.subTest(**overrides), TemporaryDirectory() as tmp:
                result, knowledge = self._write(tmp, self._candidate(**overrides))
                self.assertEqual(result["written"], [])
                self.assertEqual(len(result["rejected"]), 1, result)
                self.assertEqual(result["rejected"][0]["id"], "cand-1")
                self.assertIn(expected, result["rejected"][0]["reason"])
                self.assertEqual(list((knowledge / "lessons").glob("*.md")), [])

    def test_duplicate_of_an_existing_entry_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            knowledge = Path(tmp) / ".writ" / "knowledge"
            (knowledge / "lessons").mkdir(parents=True)
            existing = knowledge / "lessons" / "2026-01-01-already-here.md"
            existing.write_text(self._candidate()["statement"], encoding="utf-8")
            result = ps.knowledge_writeback([self._candidate(id="cand-2")], knowledge, set())
            self.assertEqual(result["written"], [])
            self.assertIn("duplicate", result["rejected"][0]["reason"])
            self.assertEqual(list((knowledge / "lessons").glob("*.md")), [existing])

    def test_already_written_id_is_skipped_silently(self) -> None:
        """Resume-safe: a candidate whose id is in `already` is neither written
        nor rejected — it was written on a prior run and stays that way."""
        with TemporaryDirectory() as tmp:
            knowledge = Path(tmp) / ".writ" / "knowledge"
            (knowledge / "lessons").mkdir(parents=True)
            result = ps.knowledge_writeback([self._candidate()], knowledge, {"cand-1"})
            self.assertEqual(result, {"written": [], "rejected": []})
            self.assertEqual(list((knowledge / "lessons").glob("*.md")), [])


class InitUatRequestedTests(unittest.TestCase):
    """2026-11-06-lean-implement-phase Story 1: `init --uat` records the UAT
    request at the top level, so `exit-criteria.py`'s c2 predicate knows
    whether plans were promised (AC-1.1, AC-1.3)."""

    def _init(self, tmp: str, *extra: str) -> tuple[int, dict, dict]:
        state_path = Path(tmp) / "state.json"
        code, payload = run_cli(
            "init", "--state", str(state_path), "--repo", tmp,
            "--phase", "6", "--phase-branch", "phase/6-example",
            "--spec-order", "spec-a,spec-b", *extra,
        )
        written = json.loads(state_path.read_text(encoding="utf-8"))
        return code, payload, written

    def test_init_with_uat_records_uat_requested_true(self) -> None:
        """AC-1.3: a run launched with --uat promises a plan per merged spec."""
        with TemporaryDirectory() as tmp:
            code, payload, written = self._init(tmp, "--uat")
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "initialized")
            self.assertIs(written["uatRequested"], True)

    def test_init_without_uat_records_uat_requested_false(self) -> None:
        """AC-1.1: a new run without --uat writes the key as false explicitly,
        because a missing key reads as requested for pre-change state files."""
        with TemporaryDirectory() as tmp:
            code, _, written = self._init(tmp)
            self.assertEqual(code, 0)
            self.assertIn("uatRequested", written)
            self.assertIs(written["uatRequested"], False)


class HealthGivenSourcesTests(unittest.TestCase):
    """2026-11-06-lean-implement-phase Story 2: `health` judges only the
    sources the caller passes. An omitted `--eval`, `--verification` or
    `--drift` reads `not_requested` and adds no Warning; a passed path that
    does not exist reads `missing` and is a Warning (AC-2.1, AC-2.2)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        for args in (("init", "-q"), ("config", "user.email", "t@writ.test"),
                     ("config", "user.name", "Writ Test"),
                     ("checkout", "-q", "-b", "phase/6")):
            self._git(*args)
        (self.repo / "b.txt").write_text("b\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        self.state = self.tmp / "state.json"
        code, _ = run_cli("init", "--state", str(self.state), "--repo", str(self.repo),
                          "--phase", "6", "--phase-branch", "phase/6",
                          "--spec-order", "a,b")
        self.assertEqual(code, 0)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git(self, *args: str) -> None:
        import subprocess
        subprocess.run(["git", "-C", str(self.repo), *args],
                       capture_output=True, text=True, check=True)

    def _write(self, name: str, text: str) -> str:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def _health(self, *extra: str) -> dict:
        code, payload = run_cli("health", "--state", str(self.state),
                                "--repo", str(self.repo), *extra)
        self.assertEqual(code, 0, payload)
        return payload

    def test_no_source_flags_reads_not_requested_and_healthy(self) -> None:
        """AC-2.1: no --eval/--verification/--drift on a reconciling state →
        every omitted source is not_requested and the category is Healthy."""
        out = self._health()
        self.assertEqual(out["sources"]["state"], "consistent")
        for source in ("eval", "verification", "drift"):
            self.assertEqual(out["sources"][source], "not_requested", out)
        self.assertEqual(out["unavailable"], [])
        self.assertEqual(out["category"], "Healthy")

    def test_only_produced_clean_sources_is_healthy(self) -> None:
        """AC-2.1: the phase's own sources (eval + drift, no verification) all
        clean → Healthy; the omitted verification report is not_requested."""
        out = self._health("--eval", self._write("eval.md", "- Findings: 0\n"),
                           "--drift", self._write("drift.md", "All resolved.\n"))
        self.assertEqual(out["sources"]["eval"], "pass")
        self.assertEqual(out["sources"]["drift"], "none")
        self.assertEqual(out["sources"]["verification"], "not_requested")
        self.assertEqual(out["category"], "Healthy")

    def test_passed_missing_verification_is_missing_and_warning(self) -> None:
        """AC-2.2: a --verification path that does not exist → missing, Warning."""
        out = self._health("--verification", str(self.tmp / "no-such-report.md"))
        self.assertEqual(out["sources"]["verification"], "missing")
        self.assertIn("verification report", out["unavailable"])
        self.assertEqual(out["category"], "Warning")

    def test_passed_missing_drift_is_missing_and_warning(self) -> None:
        """AC-2.2: a --drift path that does not exist → missing, Warning. This
        is the caller that used to get `missing` from an omitted --drift."""
        out = self._health("--drift", str(self.tmp / "no-such-drift-log.md"))
        self.assertEqual(out["sources"]["drift"], "missing")
        self.assertIn("drift log", out["unavailable"])
        self.assertEqual(out["category"], "Warning")

    def test_passed_missing_eval_is_missing_and_warning(self) -> None:
        """AC-2.2: the same rule holds for --eval."""
        out = self._health("--eval", str(self.tmp / "no-such-eval.md"))
        self.assertEqual(out["sources"]["eval"], "missing")
        self.assertEqual(out["category"], "Warning")

    def test_repeated_drift_flags_judge_every_log(self) -> None:
        """AC-2.1, AC-2.2: Step 4.1c passes --drift once per merged spec's log;
        every log counts, so one material log is Attention and one missing
        path is a Warning input."""
        clean = self._write("drift-a.md", "All resolved.\n")
        material = self._write("drift-b.md", "unresolved material issue\n")
        out = self._health("--drift", material, "--drift", clean)
        self.assertEqual(out["sources"]["drift"], "material")
        self.assertEqual(out["category"], "Attention")

        out = self._health("--drift", str(self.tmp / "gone.md"), "--drift", clean)
        self.assertEqual(out["sources"]["drift"], "missing")
        self.assertEqual(out["category"], "Warning")

        out = self._health("--drift", clean, "--drift",
                           self._write("drift-c.md", "Nothing open.\n"))
        self.assertEqual(out["sources"]["drift"], "none")
        self.assertEqual(out["category"], "Healthy")


class HealthCallSitesPassOnlyProducedSources(unittest.TestCase):
    """AC-2.3: Step 1.4 (Goal emit) is gone from /implement-phase, Step 4.1c
    passes only the sources the phase produced and never --verification, and
    /status passes only the sources it has."""

    def test_step_1_4_goal_emit_is_removed(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-phase.md").read_text(encoding="utf-8")
        self.assertNotIn("#### Step 1.4", text)
        self.assertNotIn("goal-emit.py", text)

    def test_step_4_1c_health_call_has_no_verification(self) -> None:
        text = (REPO_ROOT / "commands" / "implement-phase.md").read_text(encoding="utf-8")
        start = text.index("#### Step 4.1c:")
        step = text[start:text.index("#### Step 4.2:", start)]
        call = step[step.index("phase-state.py health"):]
        call = call[:call.index("```")]
        self.assertIn("--drift", call)
        self.assertIn("--eval", call)
        self.assertNotIn("--verification", call)
        self.assertIn("never", step)

    def test_status_passes_only_sources_it_has(self) -> None:
        text = (REPO_ROOT / "commands" / "status.md").read_text(encoding="utf-8")
        self.assertIn("Pass only the sources you have", text)
        self.assertIn("not_requested", text)



VALID_RESULT = {
    "spec_id": "a", "status": "succeeded", "stories_completed": 1,
    "stories_total": 1,
    "verification": {"summary": "green", "evidence": ["pytest -> 3 passed"]},
    "files_changed": ["b.txt"], "commit": "0" * 40, "failure": None,
    "challenge": None,
}


class LaneResultFileTests(unittest.TestCase):
    """2026-11-06-lean-implement-phase Story 3: `create-lane` names the file a
    lane writes its `phase-spec-result-v1` to, under the main checkout's
    `.writ/state/` so it outlives the lane worktree (AC-3.1), and
    `validate-result --input` reads that file, naming a missing or unparseable
    one so the orchestrator can resume the lane once (AC-3.3)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        for args in (("init", "-q"), ("config", "user.email", "t@writ.test"),
                     ("config", "user.name", "Writ Test"),
                     ("checkout", "-q", "-b", "phase/6")):
            self._git(*args)
        (self.repo / "b.txt").write_text("b\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        self.state = self.tmp / "state.json"
        code, _ = run_cli("init", "--state", str(self.state), "--repo", str(self.repo),
                          "--phase", "6", "--phase-branch", "phase/6",
                          "--spec-order", "a,b")
        self.assertEqual(code, 0)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git(self, *args: str) -> None:
        import subprocess
        subprocess.run(["git", "-C", str(self.repo), *args],
                       capture_output=True, text=True, check=True)

    def _create_lane(self, spec: str = "a") -> tuple[int, dict]:
        return run_cli("create-lane", "--state", str(self.state), "--repo", str(self.repo),
                       "--spec", spec, "--worktree-root", str(self.tmp / "lanes"))

    def _expected_path(self, spec: str = "a") -> Path:
        return self.repo.resolve() / ".writ" / "state" / f"lane-result-6-{spec}.json"

    def test_create_lane_records_result_path_in_main_checkout_state(self) -> None:
        """AC-3.1: resultPath is absolute, under the main checkout's
        .writ/state/, named lane-result-<phase>-<spec>.json, and not inside
        the lane worktree."""
        code, out = self._create_lane()
        self.assertEqual(code, 0, out)
        record = json.loads(self.state.read_text(encoding="utf-8"))["specs"]["a"]
        result_path = Path(record["resultPath"])
        self.assertTrue(result_path.is_absolute())
        self.assertEqual(result_path, self._expected_path())
        self.assertNotIn(str(Path(record["worktreePath"])), str(result_path))
        self.assertEqual(out["resultPath"], record["resultPath"])

    def test_create_lane_names_one_result_file_per_spec(self) -> None:
        """AC-3.1: each spec's lane gets its own file."""
        self._create_lane("a")
        self._create_lane("b")
        specs = json.loads(self.state.read_text(encoding="utf-8"))["specs"]
        self.assertEqual(Path(specs["b"]["resultPath"]), self._expected_path("b"))
        self.assertNotEqual(specs["a"]["resultPath"], specs["b"]["resultPath"])

    def test_resume_candidate_reports_the_recorded_result_path(self) -> None:
        """AC-3.1: a resumed lane is told the same file to write."""
        _, first = self._create_lane()
        code, again = self._create_lane()
        self.assertEqual(code, 0, again)
        self.assertEqual(again["status"], "resume_candidate")
        self.assertEqual(again["resultPath"], first["resultPath"])

    def test_validate_result_reads_the_lane_result_file(self) -> None:
        """AC-3.3: the orchestrator validates the file at resultPath."""
        _, lane = self._create_lane()
        path = Path(lane["resultPath"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(VALID_RESULT), encoding="utf-8")
        code, out = run_cli("validate-result", "--input", str(path))
        self.assertEqual(code, 0, out)
        self.assertEqual(out, {"schema": "phase-spec-result-v1",
                               "status": "succeeded", "verified": True})

    def test_missing_result_file_is_a_result_missing_blocker(self) -> None:
        """AC-3.3: a lane that never wrote its file gets a named blocker, not a
        traceback, so the orchestrator resumes the lane once."""
        _, lane = self._create_lane()
        code, out = run_cli("validate-result", "--input", lane["resultPath"])
        self.assertEqual(code, 1)
        self.assertEqual(out["blocker"]["code"], "result_missing")
        self.assertIn(lane["resultPath"], out["blocker"]["summary"])

    def test_unparseable_result_file_is_an_invalid_result_blocker(self) -> None:
        """AC-3.3: a file that is not JSON, or JSON that is not an object, does
        not parse as phase-spec-result-v1."""
        path = self.tmp / "lane-result-6-a.json"
        for text in ('{"spec_id": "a", "status": "succ', "[1, 2]"):
            path.write_text(text, encoding="utf-8")
            code, out = run_cli("validate-result", "--input", str(path))
            self.assertEqual(code, 1, text)
            self.assertEqual(out["blocker"]["code"], "invalid_result", text)


def _section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


class LaneBriefTemplateTests(unittest.TestCase):
    """2026-11-06-lean-implement-phase Story 3: the lane brief is a shipped
    template, the lane writes its result to `{result_path}` before replying,
    and the orchestrator validates that file (AC-3.2, AC-3.3)."""

    PLACEHOLDERS = ("{spec_path}", "{phase_state}", "{lane_branch}", "{worktree}",
                    "{mode}", "{result_path}", "{answer_sources}")

    def setUp(self) -> None:
        commands = REPO_ROOT / "commands"
        self.brief = (commands / "_lane-brief.md").read_text(encoding="utf-8")
        phase = (commands / "implement-phase.md").read_text(encoding="utf-8")
        self.step = _section(phase, "#### Step 3.2:", "#### Step 3.2b:")
        spec = (commands / "implement-spec.md").read_text(encoding="utf-8")
        self.lane_mode = _section(spec, "## Phase-Orchestrated Lane Mode", "## Resume Support")

    def test_template_names_every_placeholder(self) -> None:
        """AC-3.2: spec path, phase state, lane branch, worktree, mode, result
        path and answer sources."""
        for placeholder in self.PLACEHOLDERS:
            self.assertIn(placeholder, self.brief)

    def test_template_writes_the_result_file_before_replying(self) -> None:
        """AC-3.2: the lane writes phase-spec-result-v1 JSON to {result_path}
        as its last action, then replies with the path."""
        self.assertIn("phase-spec-result-v1", self.brief)
        write = self.brief.index("write")
        self.assertLess(write, self.brief.index("reply"))
        self.assertIn("last action", self.brief)

    def test_template_is_shorter_than_the_brief_it_replaces(self) -> None:
        """AC-3.2: Phase 15's first brief was 2,962 characters and grew to
        6,323; the template stays under the starting size."""
        self.assertLess(len(self.brief), 2962)

    def test_step_3_2_fills_the_template_and_validates_the_file(self) -> None:
        """AC-3.2: Step 3.2 fills the template, validates {result_path}, and
        hands the supervisor the file path, not a pasted report."""
        self.assertIn("(_lane-brief.md)", self.step)
        self.assertIn("validate-result --input {result_path}", self.step)
        supervise = _section(self.step, "**Supervise the result**", "4. **")
        self.assertIn("{result_path}", supervise)
        self.assertNotIn("report verbatim", supervise)

    def test_step_3_2_resumes_once_then_classifies_transient(self) -> None:
        """AC-3.3: a missing or unparseable file → resume the same lane agent
        once to write it → a second miss is classified transient. The
        truncated-result paragraph is gone."""
        self.assertIn("result_missing", self.step)
        self.assertIn("resume the same lane agent once", self.step)
        self.assertIn("`transient`", self.step)
        self.assertNotIn("A truncated or dropped result", self.step)
        self.assertNotIn("restate its report verbatim", self.step)

    def test_lane_mode_writes_the_result_file_before_replying(self) -> None:
        """AC-3.2: implement-spec's lane mode cites the template and writes
        the result to {result_path} before it replies."""
        self.assertIn("(_lane-brief.md)", self.lane_mode)
        self.assertIn("{result_path}", self.lane_mode)
        self.assertIn("before", self.lane_mode[self.lane_mode.index("{result_path}"):])


if __name__ == "__main__":
    unittest.main()
