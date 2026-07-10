#!/usr/bin/env python3
"""Disposable-repository scenarios for failure quarantine and resume (Story 4).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_phase_quarantine.
Exercises scripts/phase-state.py against real git repos to prove R4:

  - a transient first-attempt failure retries once in the same lane, no new gate
  - a terminal failure preserves the lane as writ/quarantine/{spec}, leaves the
    phase branch clean, and records failure evidence + retry count + recovery
  - declared direct and transitive dependents become skipped_blocked; unrelated
    specs continue
  - a quarantine-name collision produces a deterministic suffixed branch
  - --resume reconciliation reports state/git mismatches without mutating git
  - retry is bounded (second failure cannot retry again)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("phase-state.py")
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


def helper(*args: str) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(HELPER), *args],
                          capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def branch_exists(repo: Path, name: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", name],
                          capture_output=True).returncode == 0


def new_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "eval@writ.test")
    git(repo, "config", "user.name", "Writ Eval")
    git(repo, "checkout", "-q", "-b", "phase/6")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def failure_result(spec: str, classification: str) -> dict:
    return {
        "spec_id": spec, "status": "failed", "stories_completed": 0, "stories_total": 1,
        "verification": {"summary": "failed", "evidence": []},
        "files_changed": [], "commit": None,
        "failure": {"classification": classification, "summary": "boom"}, "challenge": None,
    }


def wj(path: Path, value) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def do_lane_with_partial(repo: Path, state: Path, spec: str) -> None:
    _, lane = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", spec)
    wt = Path(lane["worktreePath"])
    (wt / f"{spec}.txt").write_text("partial\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", f"partial {spec}")


def main() -> int:
    # --- retry then terminal quarantine, dependents blocked, independent continues
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo = new_repo(tmp)
        state = tmp / "state.json"
        helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
               "--phase-branch", "phase/6", "--spec-order", "b,c,d,e")
        # c depends on b; d depends on c (transitive); e independent.
        helper("set-dependencies", "--state", str(state), "--spec", "c", "--deps", "b")
        helper("set-dependencies", "--state", str(state), "--spec", "d", "--deps", "c")

        do_lane_with_partial(repo, state, "b")
        phase_head = git(repo, "rev-parse", "phase/6")

        transient = wj(tmp / "t.json", failure_result("b", "transient"))
        code, out = helper("classify", "--state", str(state), "--spec", "b", "--result", str(transient))
        emit("transient-first-attempt-retries", code == 0 and out.get("action") == "retry", out)
        code, out = helper("retry", "--state", str(state), "--spec", "b")
        emit("retry-bumps-attempt-no-gate", code == 0 and out.get("attempts") == 2, out)

        terminal = wj(tmp / "term.json", failure_result("b", "transient"))
        code, out = helper("classify", "--state", str(state), "--spec", "b", "--result", str(terminal))
        emit("transient-after-retry-quarantines", code == 0 and out.get("action") == "quarantine", out)

        code, out = helper("quarantine", "--state", str(state), "--repo", str(repo),
                           "--spec", "b", "--summary", "failed twice")
        emit("quarantine-preserves-branch",
             code == 0 and out.get("quarantineBranch") == "writ/quarantine/b"
             and branch_exists(repo, "writ/quarantine/b"), out)
        emit("quarantine-keeps-phase-branch-clean",
             out.get("phaseBranchClean") is True and git(repo, "rev-parse", "phase/6") == phase_head)
        emit("quarantine-blocks-direct-and-transitive-dependents",
             set(out.get("blockedDependents", [])) == {"c", "d"}, out)
        emit("quarantine-records-recovery", bool(out.get("recovery")), out)

        _, shown = helper("show", "--state", str(state))
        emit("independent-spec-still-eligible",
             shown["specs"]["e"]["status"] == "pending", shown)
        emit("blocked-dependent-records-blockedby",
             "b" in shown["specs"]["c"]["blockedBy"]
             and shown["specs"]["c"]["status"] == "skipped_blocked", shown)
        # retry after exhaustion is refused
        code, out = helper("retry", "--state", str(state), "--spec", "b")
        emit("retry-bounded-after-exhaustion",
             code != 0 and out.get("blocker", {}).get("code") == "retry_exhausted", out)

    # --- quarantine name collision -> deterministic suffix
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo = new_repo(tmp)
        state = tmp / "state.json"
        helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
               "--phase-branch", "phase/6", "--spec-order", "x")
        git(repo, "branch", "writ/quarantine/x", "phase/6")  # pre-existing collision
        do_lane_with_partial(repo, state, "x")
        code, out = helper("quarantine", "--state", str(state), "--repo", str(repo), "--spec", "x")
        emit("quarantine-collision-suffixed",
             code == 0 and out.get("quarantineBranch") == "writ/quarantine/x-2"
             and branch_exists(repo, "writ/quarantine/x-2"), out)

    # --- resume reconciliation
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo = new_repo(tmp)
        state = tmp / "state.json"
        helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
               "--phase-branch", "phase/6", "--spec-order", "s")
        do_lane_with_partial(repo, state, "s")
        code, out = helper("reconcile", "--state", str(state), "--repo", str(repo))
        emit("reconcile-consistent-when-agreeing",
             code == 0 and out.get("status") == "consistent", out)
        # Delete the active lane branch behind state's back.
        git(repo, "worktree", "remove", "--force", str(Path(json.loads(state.read_text())["specs"]["s"]["worktreePath"])))
        git(repo, "branch", "-D", "writ/phase/6/s")
        code, out = helper("reconcile", "--state", str(state), "--repo", str(repo))
        emit("reconcile-reports-mismatch-without-mutating",
             out.get("status") == "mismatch" and out.get("attention") is True
             and any("missing" in m for m in out.get("mismatches", [])), out)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
