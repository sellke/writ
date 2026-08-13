#!/usr/bin/env python3
"""Fixture scenarios for the exit-criteria checker (Story 4 of
`2026-08-12-machine-evaluable-exit-criteria`).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_exit_criteria, in
the exact shape scripts/eval-story-deps.py emits and scripts/eval.sh
check_story_deps consumes. Every scenario builds a disposable git repo and a
synthetic phase-execution-v2 state file in a temp directory (mirroring
scripts/tests/test_exit_criteria.py's PhaseGitFixture), then runs the REAL
`scripts/exit-criteria.py check` CLI against it via subprocess -- never
imported, so this exercises the shipped executable exactly as a caller would.

NEVER reads a real `.writ/state/phase-execution-*.json` archive: `.writ/state/`
is gitignored and its contents are a maintainer's own working copy, not a
fixture. Every scenario here is self-contained inside its own tempdir.

Scenarios:
  - met            all criteria non-blocking -> verdict met, exit 0
  - unmet          a spec not yet terminal -> implement-phase.c1 unmet
  - pre-Story-2    no exitCriteria[] recorded -> c3 unknown, verdict still met
  - impossible x4  each of the four impossible-trigger pre-pass checks
  - determinism    the checker is read-only and produces byte-identical output
                    across repeat runs against the same fixture
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "exit-criteria.py"
CLASSIFICATION = ROOT / ".writ" / "docs" / "exit-criteria-classification.md"

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}

passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, env=_GIT_ENV,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    proc = subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", "commit", "-m", message],
        capture_output=True, text=True, env=_GIT_ENV,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git commit failed: {proc.stderr}")
    return git(repo, "rev-parse", "HEAD")


@contextlib.contextmanager
def git_repo() -> Iterator[Path]:
    """A minimal real git repo standing in for `--repo`, with a `main` branch
    that is also the phase branch -- mirrors PhaseGitFixture in
    scripts/tests/test_exit_criteria.py."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "commit.gpgsign", "false")
        write(repo / "README.md", "root\n")
        commit_all(repo, "chore: root commit")
        yield repo


def write_phase_state(path: Path, **overrides: Any) -> None:
    state: dict[str, Any] = {
        "schemaVersion": 2,
        "phase": "6",
        "phaseBranch": "main",
        "startedAt": "2026-08-12T00:00:00Z",
        "updatedAt": "2026-08-12T00:00:00Z",
        "status": "executing",
        "specOrder": ["spec-a"],
        "specs": {
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                "worktreePath": None, "agentRunId": None,
                "mergeCommit": None,
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "quarantined",
            }
        },
        "exitCriteria": [
            {"id": "roadmap-x", "source": "roadmap", "class": "machine",
             "verdict": "pass", "evidence": "measured directly"},
        ],
        "challenges": [],
        "knowledgeWritten": [],
    }
    state.update(overrides)
    write(path, json.dumps(state, indent=2))


def run_checker(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True, text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def check_phase(repo: Path, state_path: Path) -> tuple[int, dict]:
    return run_checker(
        "check", "--command", "implement-phase",
        "--state", str(state_path), "--repo", str(repo),
        "--classification", str(CLASSIFICATION),
    )


# --------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------


def scenario_met() -> None:
    """Every criterion non-blocking (a quarantined spec, no reachable
    quarantine branch, a properly recorded exitCriteria[]) rolls up to `met`,
    exit 0 -- even though implement-phase.c4 is always `unknown`."""
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path)
        code, payload = check_phase(repo, state_path)
        emit("met-exits-zero", code == 0, payload)
        emit("met-verdict", payload.get("verdict") == "met", payload)
        c4 = next((c for c in payload.get("criteria", []) if c["id"] == "implement-phase.c4"), {})
        emit("met-c4-still-unknown-and-non-blocking", c4.get("verdict") == "unknown", payload)


def scenario_unmet() -> None:
    """A spec still `pending` (never reached a terminal status) fails
    implement-phase.c1, rolling the whole verdict up to `unmet`, exit 1."""
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path, specs={
            "spec-a": {
                "dependencies": [], "attempts": 1, "laneBranch": None,
                "worktreePath": None, "agentRunId": None, "mergeCommit": None,
                "quarantineBranch": None, "blockedBy": [], "uatPlan": None,
                "evidence": [], "status": "pending",
            }
        })
        code, payload = check_phase(repo, state_path)
        emit("unmet-exits-one", code == 1, payload)
        emit("unmet-verdict", payload.get("verdict") == "unmet", payload)
        c1 = next((c for c in payload.get("criteria", []) if c["id"] == "implement-phase.c1"), {})
        emit("unmet-names-c1", c1.get("verdict") == "unmet", payload)


def scenario_pre_story_2_unknown() -> None:
    """A record predating Story 2's exitCriteria[] field: c3 must resolve to
    `unknown` with the exact PRE_STORY_2_REASON, never a false `unmet` -- and
    the overall verdict stays `met` since `unknown` never blocks."""
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path, exitCriteria=[])
        code, payload = check_phase(repo, state_path)
        c3 = next((c for c in payload.get("criteria", []) if c["id"] == "implement-phase.c3"), {})
        emit("pre-story-2-c3-is-unknown", c3.get("verdict") == "unknown", payload)
        emit("pre-story-2-reason-names-instrumentation-gap",
             c3.get("reason") == "record predates exit-criteria instrumentation", payload)
        emit("pre-story-2-overall-still-met", code == 0 and payload.get("verdict") == "met", payload)


def scenario_impossible_halt_reported() -> None:
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path, haltReported={
            "unit": "spec", "bound": 12, "reached": 12, "lastIntegrated": "spec-a",
        })
        code, payload = check_phase(repo, state_path)
        emit("impossible-halt-reported-exits-two", code == 2, payload)
        emit("impossible-halt-reported-names-trigger",
             "Loop bound tripped" in payload.get("reason", ""), payload)


def scenario_impossible_unresolved_escalation() -> None:
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path, challenges=[
            {"id": "CHAL-1", "spec": "spec-a", "status": "unresolved", "challenge": {}}
        ])
        code, payload = check_phase(repo, state_path)
        emit("impossible-unresolved-escalation-exits-two", code == 2, payload)
        emit("impossible-unresolved-escalation-names-trigger",
             "Unresolved escalation" in payload.get("reason", ""), payload)


def scenario_impossible_criterion_unachievable() -> None:
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path, exitCriteria=[
            {"id": "roadmap-x", "source": "roadmap", "class": "machine",
             "verdict": "unachievable", "evidence": "measured and withdrawn"}
        ])
        code, payload = check_phase(repo, state_path)
        emit("impossible-criterion-unachievable-exits-two", code == 2, payload)
        emit("impossible-criterion-unachievable-names-trigger",
             "Criterion recorded unachievable" in payload.get("reason", ""), payload)


def scenario_impossible_state_git_mismatch() -> None:
    """`phaseBranch` names a branch this fixture repo never created --
    `phase-state.py reconcile` reports the mismatch."""
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path, phaseBranch="phase/does-not-exist")
        code, payload = check_phase(repo, state_path)
        emit("impossible-state-git-mismatch-exits-two", code == 2, payload)
        emit("impossible-state-git-mismatch-names-trigger",
             "State/git mismatch" in payload.get("reason", ""), payload)


def scenario_repeated_runs_are_identical() -> None:
    """Read-only, no memoized state: running the checker twice against the
    same fixture produces byte-identical JSON (technical-spec.md Interaction
    Edge Cases: "Checker run twice in a row -> Identical verdict")."""
    with git_repo() as repo:
        state_path = repo / "state.json"
        write_phase_state(state_path)
        first_code, first_payload = check_phase(repo, state_path)
        second_code, second_payload = check_phase(repo, state_path)
        emit("repeated-runs-byte-identical",
             first_code == second_code and json.dumps(first_payload) == json.dumps(second_payload),
             (first_payload, second_payload))


def main() -> int:
    scenario_met()
    scenario_unmet()
    scenario_pre_story_2_unknown()
    scenario_impossible_halt_reported()
    scenario_impossible_unresolved_escalation()
    scenario_impossible_criterion_unachievable()
    scenario_impossible_state_git_mismatch()
    scenario_repeated_runs_are_identical()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
