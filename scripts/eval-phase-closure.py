#!/usr/bin/env python3
"""Disposable-repository scenarios for closure by decision (phase-closure).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_phase_closure.
Exercises scripts/phase-state.py to prove the closed-by-decision contract:

  Story 1 — the status vocabulary is enforced, not documentary
  - SPEC_STATUSES admits closed_unimplemented and challenge_required
  - every spec-status write goes through one guard that rejects unknown values
  - an unknown status read from disk is tolerated, never rejected
  - progress counts are seeded from the vocabulary so the two cannot drift

  Story 2 — close-spec records the decision
  - a closure without a reason is refused before any mutation
  - a mid-run closure frees the worktree, retains the lane branch, and leaves
    the phase branch byte-identical
  - transitive dependents cascade to skipped_blocked without downgrading a
    dependent that already reached a terminal status
  - a phase containing closed specs reconciles as consistent
  - a repeat closure is refused rather than overwriting the first decision
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
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


def load_module():
    """Import the reducer directly so the write-guard can be exercised without
    routing through a subcommand that only ever writes valid values."""
    spec = importlib.util.spec_from_file_location("writ_phase_state", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def unresolved_challenge() -> dict:
    return {
        "trigger": "scope_degradation",
        "roadmap_or_spec_said": "the spec said X",
        "recommendation": "do Y instead",
        "possibly_missing_context": "maybe Z",
        "cost_if_wrong": "rework",
        "options": [{"id": "keep", "label": "Keep X"}],
    }


def wj(path: Path, value) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def do_lane_with_partial(repo: Path, state: Path, spec: str) -> dict:
    _, lane = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", spec)
    wt = Path(lane["worktreePath"])
    (wt / f"{spec}.txt").write_text("partial\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", f"partial {spec}")
    return lane


# --------------------------------------------------------------------------
# Story 1 — enforced status vocabulary
# --------------------------------------------------------------------------

def story1_vocabulary(mod) -> None:
    statuses = getattr(mod, "SPEC_STATUSES", set())
    emit("vocabulary-admits-closed-unimplemented",
         "closed_unimplemented" in statuses, sorted(statuses))
    emit("vocabulary-admits-challenge-required",
         "challenge_required" in statuses, sorted(statuses))

    terminal = getattr(mod, "TERMINAL_SPEC_STATUSES", None)
    expected = {"integrated", "quarantined", "skipped_blocked", "closed_unimplemented"}
    emit("terminal-statuses-declared", terminal == expected, terminal)


def story1_write_guard(mod) -> None:
    setter = getattr(mod, "_set_status", None)
    if setter is None:
        emit("set-status-guard-exists", False, "_set_status is not defined")
        return
    emit("set-status-guard-exists", True)

    # Every declared status is accepted.
    ok = True
    detail = ""
    for value in sorted(getattr(mod, "SPEC_STATUSES", set())):
        record: dict = {}
        try:
            setter(record, value)
        except Exception as exc:  # noqa: BLE001 - scenario reports any rejection
            ok = False
            detail = f"{value}: {exc}"
            break
        if record.get("status") != value:
            ok = False
            detail = f"{value}: not written ({record})"
            break
    emit("set-status-accepts-every-declared-status", ok, detail)

    # An undeclared status is refused as a contract error, and nothing is written.
    record = {"status": "pending"}
    try:
        setter(record, "bogus_status")
        emit("set-status-rejects-unknown", False, "no error raised")
    except Exception as exc:  # noqa: BLE001
        code = getattr(exc, "code", None)
        emit("set-status-rejects-unknown",
             code == "invalid_status" and record["status"] == "pending",
             f"code={code!r} record={record}")


def _receiver_root(node: ast.AST) -> str:
    """Left-most identifier of a subscript/attribute chain, e.g. `state` in
    `state["specs"][dep]["status"]`."""
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value if isinstance(node, ast.Subscript) else node.value
    return node.id if isinstance(node, ast.Name) else ""


def story1_no_direct_assignment() -> None:
    """The guard is only load-bearing if nothing bypasses it.

    Walks the AST rather than grepping, because a line-based check misses the
    `record.update({"status": ...})` form entirely — which is how three of the
    original mutation sites were written.

    Allowed: the single assignment inside `_set_status`; `entry[...]` writes,
    which set a *challenge* entry's status rather than a spec's; and
    `state["status"]`, the phase-level status.
    """
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    guard_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_set_status":
            guard_lines = set(range(node.lineno, (node.end_lineno or node.lineno) + 1))

    offenders: list[str] = []
    for node in ast.walk(tree):
        # record["status"] = ... / state["specs"][x]["status"] = ...
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Subscript):
                    continue
                key = target.slice
                if not (isinstance(key, ast.Constant) and key.value == "status"):
                    continue
                if node.lineno in guard_lines:
                    continue
                root = _receiver_root(target.value)
                if root == "entry":
                    continue
                if isinstance(target.value, ast.Name) and root == "state":
                    continue  # phase-level status, not a spec's
                offenders.append(f'{node.lineno}: assign to ["status"] on {root!r}')
        # record.update({"status": ...})
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "update":
            for arg in node.args:
                if not isinstance(arg, ast.Dict):
                    continue
                for k in arg.keys:
                    if isinstance(k, ast.Constant) and k.value == "status":
                        root = _receiver_root(node.func.value)
                        if root == "entry":
                            continue
                        offenders.append(
                            f'{node.lineno}: .update() writes "status" on {root!r}')

    emit("no-spec-status-write-bypasses-the-guard", not offenders, offenders)


def story1_init_uses_guard() -> None:
    """cmd_init builds records from a literal; it must route its "pending"
    through the guard rather than trusting the literal."""
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "cmd_init":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) \
                        and inner.func.id == "_set_status":
                    found = True
    emit("init-routes-initial-status-through-the-guard", found,
         "cmd_init does not call _set_status")


def story1_progress_seeding(mod, tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "s1-state.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a,b")

    code, out = helper("progress", "--state", str(state))
    counts = out.get("counts", {})
    declared = getattr(mod, "SPEC_STATUSES", set())
    missing = sorted(declared - set(counts))
    emit("progress-counts-seeded-from-vocabulary",
         code == 0 and not missing, f"missing={missing} counts={counts}")
    emit("progress-reports-zero-for-absent-statuses",
         counts.get("closed_unimplemented") == 0 and counts.get("pending") == 2, counts)


def story1_read_tolerance(tmp: Path) -> None:
    """A status written by a newer reducer must still report, never crash."""
    state = tmp / "s1-future.json"
    wj(state, {
        "schemaVersion": 2, "phase": "6", "phaseBranch": "phase/6",
        "startedAt": "2026-08-12T00:00:00Z", "updatedAt": "2026-08-12T00:00:00Z",
        "status": "executing", "specOrder": ["a"],
        "specs": {"a": {"dependencies": [], "status": "future_value", "attempts": 0,
                        "laneBranch": None, "worktreePath": None, "agentRunId": None,
                        "mergeCommit": None, "quarantineBranch": None,
                        "blockedBy": [], "uatPlan": None, "evidence": []}},
        "challenges": [], "knowledgeWritten": [],
    })
    code, out = helper("progress", "--state", str(state))
    counts = out.get("counts", {})
    emit("progress-tolerates-unknown-status-on-read",
         code == 0 and counts.get("future_value") == 1, f"code={code} counts={counts}")


def story1_challenge_required_still_writable(tmp: Path) -> None:
    """cmd_record_challenge writes challenge_required today; enforcement must
    not start rejecting a write the reducer already performs."""
    repo = new_repo(tmp)
    state = tmp / "s1-chal.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    payload = wj(tmp / "chal.json", unresolved_challenge())
    code, out = helper("record-challenge", "--state", str(state), "--spec", "a",
                       "--input", str(payload))
    recorded = json.loads(state.read_text())["specs"]["a"]["status"]
    emit("record-challenge-still-writes-challenge-required",
         code == 0 and out.get("blocked") is True and recorded == "challenge_required",
         f"code={code} out={out} status={recorded}")


def story1_existing_transitions_intact(tmp: Path) -> None:
    """Routing every write through the guard must not change any existing
    transition. Smoke-tests the two most-travelled paths."""
    repo = new_repo(tmp)
    state = tmp / "s1-lane.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    do_lane_with_partial(repo, state, "a")
    status = json.loads(state.read_text())["specs"]["a"]["status"]
    emit("create-lane-still-sets-implementing", status == "implementing", status)

    result = wj(tmp / "ok.json", {
        "spec_id": "a", "status": "succeeded", "stories_completed": 1, "stories_total": 1,
        "verification": {"summary": "green", "evidence": ["tests pass"]},
        "files_changed": ["a.txt"], "commit": "deadbeef",
        "failure": None, "challenge": None,
    })
    code, out = helper("integrate", "--state", str(state), "--repo", str(repo),
                       "--spec", "a", "--result", str(result))
    status = json.loads(state.read_text())["specs"]["a"]["status"]
    emit("integrate-still-sets-integrated",
         code == 0 and out.get("merged") is True and status == "integrated",
         f"out={out} status={status}")


# --------------------------------------------------------------------------
# Story 2 — close-spec
# --------------------------------------------------------------------------

def story2_reason_gate(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "s2-reason.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    before = state.read_bytes()

    for label, extra in (("empty", [""]), ("whitespace", ["   "])):
        code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                           "--spec", "a", "--reason", *extra)
        emit(f"close-refuses-{label}-reason",
             code != 0 and out.get("blocker", {}).get("code") == "invalid_closure"
             and state.read_bytes() == before,
             f"code={code} out={out}")

    # A missing --reason is an argparse error: still refused, still no mutation.
    proc = subprocess.run([sys.executable, str(HELPER), "close-spec", "--state", str(state),
                           "--repo", str(repo), "--spec", "a"],
                          capture_output=True, text=True)
    emit("close-refuses-missing-reason",
         proc.returncode != 0 and state.read_bytes() == before,
         f"rc={proc.returncode} err={proc.stderr[-120:]}")

    code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                       "--spec", "nope", "--reason", "valid reason")
    emit("close-rejects-unknown-spec",
         code != 0 and out.get("blocker", {}).get("code") == "unknown_spec", out)


def story2_close_pending(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "s2-pending.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a,b")
    head_before = git(repo, "rev-parse", "phase/6")
    refs_before = git(repo, "for-each-ref", "--format=%(refname)")

    reason = "superseded by measured evidence"
    code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                       "--spec", "a", "--reason", reason)
    record = json.loads(state.read_text())["specs"]["a"]
    emit("close-pending-sets-closed-unimplemented",
         code == 0 and record["status"] == "closed_unimplemented",
         f"code={code} out={out} status={record.get('status')}")
    closure = record.get("closure") or {}
    emit("close-records-reason-and-timestamp",
         closure.get("reason") == reason
         and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
                               closure.get("closedAt") or "")),
         closure)
    emit("close-reports-phase-branch-clean", out.get("phaseBranchClean") is True, out)
    emit("close-pending-touches-no-git",
         git(repo, "rev-parse", "phase/6") == head_before
         and git(repo, "for-each-ref", "--format=%(refname)") == refs_before,
         "refs or head changed")

    code, out = helper("progress", "--state", str(state))
    counts = out.get("counts", {})
    emit("progress-counts-closed-separately",
         counts.get("closed_unimplemented") == 1 and counts.get("pending") == 1, counts)


def story2_close_midrun(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "s2-midrun.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    lane = do_lane_with_partial(repo, state, "a")
    lane_branch = lane["laneBranch"]
    worktree = Path(lane["worktreePath"])
    head_before = git(repo, "rev-parse", "phase/6")

    code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                       "--spec", "a", "--reason", "descoped mid-run")
    record = json.loads(state.read_text())["specs"]["a"]
    emit("close-midrun-removes-worktree",
         code == 0 and not worktree.exists() and record.get("worktreePath") is None,
         f"code={code} exists={worktree.exists()} recorded={record.get('worktreePath')}")
    emit("close-midrun-retains-lane-branch",
         record.get("laneBranch") == lane_branch and branch_exists(repo, lane_branch),
         f"recorded={record.get('laneBranch')} exists={branch_exists(repo, lane_branch)}")
    emit("close-midrun-creates-no-quarantine-branch",
         not branch_exists(repo, "writ/quarantine/a")
         and record.get("quarantineBranch") is None, record.get("quarantineBranch"))
    emit("close-midrun-leaves-phase-head-identical",
         git(repo, "rev-parse", "phase/6") == head_before
         and out.get("phaseBranchClean") is True, out)


def story2_missing_worktree(tmp: Path) -> None:
    """A recorded worktree already gone from disk must not fail the closure."""
    repo = new_repo(tmp)
    state = tmp / "s2-gonewt.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    lane = do_lane_with_partial(repo, state, "a")
    git(repo, "worktree", "remove", "--force", lane["worktreePath"])

    code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                       "--spec", "a", "--reason", "descoped after worktree cleanup")
    record = json.loads(state.read_text())["specs"]["a"]
    emit("close-survives-already-removed-worktree",
         code == 0 and record["status"] == "closed_unimplemented"
         and record.get("worktreePath") is None, f"code={code} out={out}")


def story2_cascade(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "s2-cascade.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a,b,c,d,e")
    # b -> a, c -> b (transitive), d -> a but already integrated, e independent.
    helper("set-dependencies", "--state", str(state), "--spec", "b", "--deps", "a")
    helper("set-dependencies", "--state", str(state), "--spec", "c", "--deps", "b")
    helper("set-dependencies", "--state", str(state), "--spec", "d", "--deps", "a")

    do_lane_with_partial(repo, state, "d")
    result = wj(tmp / "d-ok.json", {
        "spec_id": "d", "status": "succeeded", "stories_completed": 1, "stories_total": 1,
        "verification": {"summary": "green", "evidence": ["tests pass"]},
        "files_changed": ["d.txt"], "commit": "cafebabe",
        "failure": None, "challenge": None,
    })
    helper("integrate", "--state", str(state), "--repo", str(repo),
           "--spec", "d", "--result", str(result))
    merge_commit = json.loads(state.read_text())["specs"]["d"]["mergeCommit"]

    code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                       "--spec", "a", "--reason", "closed on measured evidence")
    specs = json.loads(state.read_text())["specs"]

    emit("cascade-blocks-direct-dependent",
         specs["b"]["status"] == "skipped_blocked" and "a" in specs["b"]["blockedBy"],
         specs["b"])
    emit("cascade-blocks-transitive-dependent",
         specs["c"]["status"] == "skipped_blocked" and bool(specs["c"]["blockedBy"]),
         specs["c"])
    emit("cascade-skips-terminal-dependent",
         specs["d"]["status"] == "integrated" and specs["d"]["mergeCommit"] == merge_commit,
         specs["d"])
    emit("cascade-leaves-independent-spec-pending",
         specs["e"]["status"] == "pending", specs["e"])
    emit("cascade-reports-blocked-dependents",
         sorted(out.get("blockedDependents", [])) == ["b", "c"], out)

    code, out = helper("progress", "--state", str(state))
    blocked = out.get("blocked")
    emit("progress-attributes-blocking-to-closure",
         isinstance(blocked, dict) and sorted(blocked) == ["b", "c"]
         and all(info.get("cause") == "closed_unimplemented"
                 for info in blocked.values()),
         f"blocked={blocked}")


def story2_progress_distinguishes_quarantine(tmp: Path) -> None:
    """The cascade widened blockedBy to mean 'upstream terminal without
    delivering'. Progress must still say WHICH, or a reader chases a quarantine
    branch that was never created."""
    repo = new_repo(tmp)
    state = tmp / "s2-qcause.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a,b")
    helper("set-dependencies", "--state", str(state), "--spec", "b", "--deps", "a")
    do_lane_with_partial(repo, state, "a")
    helper("quarantine", "--state", str(state), "--repo", str(repo), "--spec", "a",
           "--summary", "terminal failure")

    code, out = helper("progress", "--state", str(state))
    blocked = out.get("blocked") or {}
    emit("progress-attributes-blocking-to-quarantine",
         isinstance(blocked, dict) and blocked.get("b", {}).get("cause") == "quarantined",
         f"blocked={blocked}")


def story2_reconcile(tmp: Path) -> None:
    repo = new_repo(tmp)
    state = tmp / "s2-recon.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    lane = do_lane_with_partial(repo, state, "a")
    helper("close-spec", "--state", str(state), "--repo", str(repo),
           "--spec", "a", "--reason", "descoped mid-run")

    code, out = helper("reconcile", "--state", str(state), "--repo", str(repo))
    emit("reconcile-consistent-with-closed-spec",
         code == 0 and out.get("status") == "consistent" and out.get("attention") is False,
         out)

    code, out = helper("health", "--state", str(state), "--repo", str(repo))
    emit("health-no-attention-from-closure",
         out.get("category") != "Attention"
         and "phase-state/git mismatch" not in out.get("failures", []), out)

    # Deleting the retained lane behind state's back is a reportable mismatch,
    # symmetric with how a missing quarantine branch is treated.
    git(repo, "branch", "-D", lane["laneBranch"])
    code, out = helper("reconcile", "--state", str(state), "--repo", str(repo))
    emit("reconcile-reports-missing-retained-lane",
         out.get("status") == "mismatch" and out.get("attention") is True
         and any(m.startswith("a:") for m in out.get("mismatches", [])), out)


def story2_repeat_closure(tmp: Path) -> None:
    """Closing an already-closed spec is an explicit refusal, not a silent
    rewrite that would overwrite the original decision's reason and timestamp."""
    repo = new_repo(tmp)
    state = tmp / "s2-repeat.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a")
    helper("close-spec", "--state", str(state), "--repo", str(repo),
           "--spec", "a", "--reason", "first decision")
    first = json.loads(state.read_text())["specs"]["a"]["closure"]

    code, out = helper("close-spec", "--state", str(state), "--repo", str(repo),
                       "--spec", "a", "--reason", "second decision")
    after = json.loads(state.read_text())["specs"]["a"]["closure"]
    emit("repeat-closure-refused-and-preserves-original",
         code != 0 and out.get("blocker", {}).get("code") == "already_closed"
         and after == first, f"code={code} out={out} closure={after}")


def main() -> int:
    mod = load_module()
    story1_vocabulary(mod)
    story1_write_guard(mod)
    story1_no_direct_assignment()
    story1_init_uses_guard()

    with tempfile.TemporaryDirectory() as t:
        story1_progress_seeding(mod, Path(t))
    with tempfile.TemporaryDirectory() as t:
        story1_read_tolerance(Path(t))
    with tempfile.TemporaryDirectory() as t:
        story1_challenge_required_still_writable(Path(t))
    with tempfile.TemporaryDirectory() as t:
        story1_existing_transitions_intact(Path(t))

    for scenario in (story2_reason_gate, story2_close_pending, story2_close_midrun,
                     story2_missing_worktree, story2_cascade,
                     story2_progress_distinguishes_quarantine, story2_reconcile,
                     story2_repeat_closure):
        with tempfile.TemporaryDirectory() as t:
            scenario(Path(t))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
