#!/usr/bin/env python3
"""Fail-closed reducer and git-lane manager for `/implement-phase`.

This is the executable reference for the platform-neutral phase orchestration
state machine (`phase-execution-v2`). It owns the safety-critical mechanics that
must behave identically across Cursor, Claude Code, and Codex:

  - creating an isolated per-spec lane (branch + worktree) BEFORE any work,
    starting from the current phase-branch head,
  - validating the `phase-spec-result-v1` structured result a fresh subagent
    returns,
  - merging ONLY a verified successful lane back into the phase branch and
    removing its worktree,
  - leaving any non-successful or unverifiable lane untouched and preserved
    (Story 4 classifies, quarantines, and recovers it).

State is written atomically (temp file + rename) and unknown fields are
preserved so later stories can extend the schema without this reducer dropping
data. Nothing outside the phase branch, lane branches, and the named state file
is ever mutated.

Subcommands:
  init           --state --repo --phase --phase-branch --spec-order
  create-lane    --state --repo --spec [--worktree-root]
  validate-result --input
  integrate      --state --repo --spec --result
  show           --state
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 2
RESULT_SCHEMA = "phase-spec-result-v1"
RESULT_STATUSES = {"succeeded", "failed", "challenge_required"}
SPEC_STATUSES = {
    "pending", "implementing", "integrated", "failed",
    "quarantined", "skipped_blocked",
}


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _fail(err: ContractError) -> None:
    print(json.dumps({"blocker": {"code": err.code, "summary": err.summary}}))
    raise SystemExit(1)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True,
    )
    if check and proc.returncode != 0:
        raise ContractError(
            "git_error",
            f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}",
        )
    return proc


def _load(state_path: Path) -> dict[str, Any]:
    if not state_path.is_file():
        raise ContractError("missing_state", f"no phase state at {state_path}")
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError("invalid_state", f"phase state is not valid JSON: {exc}")


def _atomic_write(state_path: Path, value: dict[str, Any]) -> None:
    """Write via a sibling temp file + rename so an interrupt leaves either the
    prior valid state or the next valid state, never a torn file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(state_path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, state_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _require_clean(repo: Path) -> None:
    status = _git(repo, "status", "--porcelain").stdout.strip()
    if status:
        raise ContractError(
            "dirty_base",
            "phase branch has uncommitted changes; refusing to create a lane "
            "that could hide unrelated work",
        )


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    if state_path.exists():
        raise ContractError("state_exists", f"phase state already exists: {state_path}")
    order = [s.strip() for s in args.spec_order.split(",") if s.strip()]
    specs = {
        spec: {
            "dependencies": [],
            "status": "pending",
            "attempts": 0,
            "laneBranch": None,
            "worktreePath": None,
            "agentRunId": None,
            "mergeCommit": None,
            "quarantineBranch": None,
            "blockedBy": [],
            "uatPlan": None,
            "evidence": [],
        }
        for spec in order
    }
    state = {
        "schemaVersion": SCHEMA_VERSION,
        "phase": args.phase,
        "phaseBranch": args.phase_branch,
        "startedAt": _now(),
        "updatedAt": _now(),
        "status": "executing",
        "specOrder": order,
        "specs": specs,
        "challenges": [],
        "knowledgeWritten": [],
    }
    _atomic_write(state_path, state)
    return {"status": "initialized", "phase": args.phase, "specOrder": order}


def _spec_record(state: dict[str, Any], spec: str) -> dict[str, Any]:
    if spec not in state.get("specs", {}):
        raise ContractError("unknown_spec", f"spec {spec!r} is not in phase state")
    return state["specs"][spec]


def cmd_create_lane(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    repo = Path(args.repo)
    state = _load(state_path)
    record = _spec_record(state, args.spec)
    phase_branch = state["phaseBranch"]
    lane_branch = f"writ/phase/{state['phase']}/{args.spec}"

    # Isolation must begin from a clean phase-branch head.
    _require_clean(repo)
    _git(repo, "rev-parse", "--verify", phase_branch)

    exists = _git(repo, "rev-parse", "--verify", lane_branch, check=False).returncode == 0
    if exists:
        # Matching live state => resume candidate. Otherwise ownership is
        # ambiguous and we must stop rather than clobber someone's branch.
        if record.get("laneBranch") == lane_branch and record.get("status") == "implementing":
            return {"status": "resume_candidate", "laneBranch": lane_branch,
                    "worktreePath": record.get("worktreePath")}
        raise ContractError(
            "lane_collision",
            f"branch {lane_branch} already exists without matching live state",
        )

    worktree_root = Path(args.worktree_root) if args.worktree_root else (
        repo.parent / f".writ-lanes-{state['phase']}"
    )
    worktree_root.mkdir(parents=True, exist_ok=True)
    worktree_path = worktree_root / args.spec

    _git(repo, "worktree", "add", "-b", lane_branch, str(worktree_path), phase_branch)

    record.update({
        "status": "implementing",
        "attempts": record.get("attempts", 0) + 1,
        "laneBranch": lane_branch,
        "worktreePath": str(worktree_path),
    })
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "lane_created", "laneBranch": lane_branch,
            "worktreePath": str(worktree_path), "base": phase_branch}


def validate_result(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContractError("invalid_result", "result must be a JSON object")

    required = {"spec_id", "status", "stories_completed", "stories_total",
                "verification", "files_changed", "commit", "failure", "challenge"}
    missing = sorted(required - set(payload))
    if missing:
        raise ContractError("invalid_result", f"result missing keys: {missing}")

    status = payload["status"]
    if status not in RESULT_STATUSES:
        raise ContractError("invalid_result", f"unknown result status: {status!r}")

    verification = payload["verification"]
    if not isinstance(verification, dict) or "summary" not in verification \
            or "evidence" not in verification:
        raise ContractError("invalid_result", "verification must have summary and evidence")
    if not isinstance(verification["evidence"], list):
        raise ContractError("invalid_result", "verification.evidence must be a list")
    if not isinstance(payload["files_changed"], list):
        raise ContractError("invalid_result", "files_changed must be a list")

    if status == "succeeded":
        if not payload.get("commit"):
            raise ContractError("invalid_result", "succeeded result must carry a commit")
        if not verification["evidence"]:
            raise ContractError("invalid_result", "succeeded result must carry verification evidence")
    if status == "challenge_required" and not payload.get("challenge"):
        raise ContractError("invalid_result", "challenge_required result must carry a challenge")

    return {"schema": RESULT_SCHEMA, "status": status, "verified": status == "succeeded"}


def cmd_validate_result(args: argparse.Namespace) -> dict[str, Any]:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    return validate_result(payload)


def cmd_integrate(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    repo = Path(args.repo)
    state = _load(state_path)
    record = _spec_record(state, args.spec)
    payload = json.loads(Path(args.result).read_text(encoding="utf-8"))

    # A malformed or non-successful result never touches the phase branch.
    # The lane is preserved for Story 4 to classify and quarantine.
    try:
        verdict = validate_result(payload)
    except ContractError as err:
        return {"status": "preserved_lane", "reason": err.code, "summary": err.summary,
                "merged": False}
    if not verdict["verified"]:
        return {"status": "preserved_lane", "reason": "not_verified",
                "summary": f"result status is {verdict['status']}", "merged": False}

    lane_branch = record["laneBranch"]
    phase_branch = state["phaseBranch"]
    _require_clean(repo)
    _git(repo, "checkout", phase_branch)
    merge = _git(repo, "merge", "--no-ff", lane_branch,
                 "-m", f"Merge lane {lane_branch}", check=False)
    if merge.returncode != 0:
        # Abort safely; retain the lane and mark attention (Story 4 territory).
        _git(repo, "merge", "--abort", check=False)
        record["status"] = "failed"
        record["evidence"].append("merge_conflict")
        state["updatedAt"] = _now()
        _atomic_write(state_path, state)
        return {"status": "attention_required", "reason": "merge_conflict", "merged": False}

    merge_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    worktree_path = record.get("worktreePath")
    if worktree_path:
        _git(repo, "worktree", "remove", "--force", worktree_path, check=False)

    record.update({
        "status": "integrated",
        "mergeCommit": merge_commit,
        "worktreePath": None,
    })
    record["evidence"].extend(payload["verification"]["evidence"])
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "integrated", "mergeCommit": merge_commit, "merged": True}


def cmd_show(args: argparse.Namespace) -> dict[str, Any]:
    return _load(Path(args.state))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--phase", required=True)
    p.add_argument("--phase-branch", required=True)
    p.add_argument("--spec-order", default="")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("create-lane")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--worktree-root", default="")
    p.set_defaults(func=cmd_create_lane)

    p = sub.add_parser("validate-result")
    p.add_argument("--input", required=True)
    p.set_defaults(func=cmd_validate_result)

    p = sub.add_parser("integrate")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--result", required=True)
    p.set_defaults(func=cmd_integrate)

    p = sub.add_parser("show")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_show)

    args = parser.parse_args(argv)
    try:
        print(json.dumps(args.func(args)))
    except ContractError as err:
        _fail(err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
