#!/usr/bin/env python3
"""Disposable-repository scenarios for fresh isolated execution lanes (Story 2).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_phase_lanes. Every
scenario builds a throwaway git repository in a temp directory and exercises
scripts/phase-state.py to prove the locked R2/D2/D3 contract:

  - a lane branch + worktree are created from the phase-branch head BEFORE work
  - the primary checkout is never mutated while the lane runs
  - only a verified `succeeded` phase-spec-result-v1 merges into the phase branch
  - a malformed or non-successful result never touches the phase branch and its
    lane is preserved for Story 4
  - a dirty base or a lane-branch collision stops before launch
  - the result-schema validator rejects each malformed shape
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
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True, text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip()


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


def result_for(repo: Path, spec: str, commit: str, status: str = "succeeded",
               evidence=None) -> dict:
    return {
        "spec_id": spec,
        "status": status,
        "stories_completed": 1,
        "stories_total": 1,
        "verification": {"summary": "ok", "evidence": evidence if evidence is not None
                         else (["eval-green"] if status == "succeeded" else [])},
        "files_changed": ["lane.txt"],
        "commit": commit if status == "succeeded" else None,
        "failure": None if status != "failed" else {"classification": "terminal", "summary": "boom"},
        "challenge": None,
    }


def write_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def scenario_success_merge(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "state.json"
    helper("init", "--state", str(state), "--repo", str(repo),
           "--phase", "6", "--phase-branch", "phase/6", "--spec-order", "spec-a")

    primary_head_before = git(repo, "rev-parse", "HEAD")
    code, lane = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "spec-a")
    emit("lane-created-from-phase-head",
         code == 0 and lane.get("status") == "lane_created"
         and lane.get("base") == "phase/6", lane)
    wt = Path(lane["worktreePath"])
    emit("worktree-exists", wt.is_dir(), lane)

    # Do work inside the lane worktree and commit on the lane branch.
    (wt / "lane.txt").write_text("lane work\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "lane work")
    lane_commit = git(wt, "rev-parse", "HEAD")

    # Primary checkout must be untouched by lane work.
    emit("primary-head-untouched-during-lane",
         git(repo, "rev-parse", "HEAD") == primary_head_before)
    emit("primary-worktree-has-no-lane-file", not (repo / "lane.txt").exists())

    result = write_json(tmp / "r.json", result_for(repo, "spec-a", lane_commit))
    code, out = helper("integrate", "--state", str(state), "--repo", str(repo),
                       "--spec", "spec-a", "--result", str(result))
    emit("verified-success-merges", code == 0 and out.get("merged") is True, out)
    emit("phase-branch-has-lane-file", (repo / "lane.txt").exists())
    emit("worktree-removed-after-merge", not wt.exists())
    _, shown = helper("show", "--state", str(state))
    emit("state-records-integrated",
         shown["specs"]["spec-a"]["status"] == "integrated"
         and shown["specs"]["spec-a"]["mergeCommit"], shown)


def scenario_unverified_preserved(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "state.json"
    helper("init", "--state", str(state), "--repo", str(repo),
           "--phase", "6", "--phase-branch", "phase/6", "--spec-order", "spec-b")
    _, lane = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "spec-b")
    wt = Path(lane["worktreePath"])
    (wt / "lane.txt").write_text("partial\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "partial")
    phase_head_before = git(repo, "rev-parse", "phase/6")

    # A 'failed' result must never merge and must preserve the lane.
    result = write_json(tmp / "rf.json", result_for(repo, "spec-b", "", status="failed"))
    code, out = helper("integrate", "--state", str(state), "--repo", str(repo),
                       "--spec", "spec-b", "--result", str(result))
    emit("failed-result-not-merged",
         code == 0 and out.get("merged") is False and out.get("status") == "preserved_lane", out)
    emit("phase-branch-unchanged-on-failure",
         git(repo, "rev-parse", "phase/6") == phase_head_before)
    emit("lane-branch-preserved",
         subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify",
                         "writ/phase/6/spec-b"], capture_output=True).returncode == 0)


def scenario_malformed_result(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "state.json"
    helper("init", "--state", str(state), "--repo", str(repo),
           "--phase", "6", "--phase-branch", "phase/6", "--spec-order", "spec-c")
    helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "spec-c")
    phase_head_before = git(repo, "rev-parse", "phase/6")
    bad = write_json(tmp / "bad.json", {"spec_id": "spec-c", "status": "succeeded"})
    code, out = helper("integrate", "--state", str(state), "--repo", str(repo),
                       "--spec", "spec-c", "--result", str(bad))
    emit("malformed-result-not-merged",
         code == 0 and out.get("merged") is False, out)
    emit("phase-branch-unchanged-on-malformed",
         git(repo, "rev-parse", "phase/6") == phase_head_before)


def scenario_dirty_and_collision(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "state.json"
    helper("init", "--state", str(state), "--repo", str(repo),
           "--phase", "6", "--phase-branch", "phase/6", "--spec-order", "spec-d,spec-e")
    (repo / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")
    code, out = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "spec-d")
    emit("dirty-base-blocks-lane",
         code != 0 and out.get("blocker", {}).get("code") == "dirty_base", out)
    (repo / "dirty.txt").unlink()

    # Pre-create a colliding lane branch with no matching state.
    git(repo, "branch", "writ/phase/6/spec-e", "phase/6")
    code, out = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "spec-e")
    emit("lane-collision-blocks",
         code != 0 and out.get("blocker", {}).get("code") == "lane_collision", out)


def scenario_result_schema(tmp: Path) -> None:
    repo = new_repo(tmp)
    good = result_for(repo, "s", "deadbeef")
    for name, mutate in (
        ("missing-key", lambda v: v.pop("verification")),
        ("bad-status", lambda v: v.update(status="done")),
        ("succeeded-without-commit", lambda v: v.update(commit=None)),
        ("succeeded-without-evidence", lambda v: v["verification"].update(evidence=[])),
        ("challenge-without-payload", lambda v: v.update(status="challenge_required", challenge=None)),
    ):
        value = json.loads(json.dumps(good))
        mutate(value)
        path = write_json(tmp / f"{name}.json", value)
        code, out = helper("validate-result", "--input", str(path))
        emit(f"validate-rejects-{name}",
             code != 0 and out.get("blocker", {}).get("code") == "invalid_result", out)
    path = write_json(tmp / "good.json", good)
    code, out = helper("validate-result", "--input", str(path))
    emit("validate-accepts-verified-success",
         code == 0 and out.get("verified") is True, out)


def main() -> int:
    with tempfile.TemporaryDirectory() as t1:
        scenario_success_merge(Path(t1))
    with tempfile.TemporaryDirectory() as t2:
        scenario_unverified_preserved(Path(t2))
    with tempfile.TemporaryDirectory() as t3:
        scenario_malformed_result(Path(t3))
    with tempfile.TemporaryDirectory() as t4:
        scenario_dirty_and_collision(Path(t4))
    with tempfile.TemporaryDirectory() as t5:
        scenario_result_schema(Path(t5))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
