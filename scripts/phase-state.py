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
  record-exit-criterion --state --id --source --class --verdict [--evidence]
  set-terminal-status   --state --status
  record-halt    --state --unit --bound --reached [--last-integrated]
  show           --state
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 2
RESULT_SCHEMA = "phase-spec-result-v1"
RESULT_STATUSES = {"succeeded", "failed", "challenge_required"}
CHALLENGE_TRIGGERS = {"scope_degradation", "exit_criteria_degradation"}
CHALLENGE_PARTS = (
    "roadmap_or_spec_said", "recommendation",
    "possibly_missing_context", "cost_if_wrong",
)
SPEC_STATUSES = {
    "pending", "implementing", "integrated", "failed",
    "quarantined", "skipped_blocked", "challenge_required",
    "closed_not_implemented",
}
# Story 2: run-record extensions for machine-evaluable exit criteria.
EXIT_CRITERION_CLASSES = {"machine", "human"}
EXIT_CRITERION_VERDICTS = {"pass", "fail", "unachievable", "handed_off"}
TERMINAL_STATUSES = {
    "COMPLETE", "IMPLEMENTED_PENDING_HUMAN_VALIDATION", "PARTIALLY_COMPLETE",
}
# Statuses from which no further execution follows. A spec here is never
# retried, relaunched, or downgraded by another spec's disposition.
TERMINAL_SPEC_STATUSES = {
    "integrated", "quarantined", "skipped_blocked", "closed_not_implemented",
}


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _set_status(record: dict[str, Any], value: str) -> None:
    """The single spec-status mutation point.

    Validate on **write**, tolerate on **read**. The schema's compatibility
    promise is that unknown fields survive a round-trip so later stories can
    extend it; rejecting an unrecognized status while *reading* would turn a
    state file written by a newer reducer into a hard failure. So this guard
    covers mutation only, and the read paths (`progress`, `show`, `reconcile`)
    stay permissive.
    """
    if value not in SPEC_STATUSES:
        raise ContractError("invalid_status", f"unknown spec status: {value!r}")
    record["status"] = value


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
    for record in specs.values():
        _set_status(record, "pending")
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

    _set_status(record, "implementing")
    record.update({
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
    if payload.get("status") == "challenge_required":
        validate_challenge(payload.get("challenge"))
    return validate_result(payload)


def validate_challenge(payload: Any) -> dict[str, Any]:
    """Validate the four-part User Challenge contract (D5).

    A malformed challenge (missing any required part, bad trigger, or empty
    options) is a contract error — never silently treated as a User Challenge
    or as an ordinary implementation failure.
    """
    if not isinstance(payload, dict):
        raise ContractError("invalid_challenge", "challenge must be a JSON object")

    trigger = payload.get("trigger")
    if trigger not in CHALLENGE_TRIGGERS:
        raise ContractError("invalid_challenge", f"unknown challenge trigger: {trigger!r}")

    missing = [part for part in CHALLENGE_PARTS
               if not isinstance(payload.get(part), str) or not payload.get(part).strip()]
    if missing:
        raise ContractError("invalid_challenge", f"challenge missing required parts: {missing}")

    options = payload.get("options")
    if not isinstance(options, list) or not options:
        raise ContractError("invalid_challenge", "challenge must offer at least one option")
    option_ids = set()
    for opt in options:
        if not isinstance(opt, dict) or not opt.get("id") or not opt.get("label"):
            raise ContractError("invalid_challenge", "each option needs an id and a label")
        option_ids.add(opt["id"])

    decision = payload.get("decision")
    if decision is not None:
        if not isinstance(decision, dict) or decision.get("option_id") not in option_ids \
                or not decision.get("decided_at"):
            raise ContractError("invalid_challenge",
                                "decision must name a known option_id and decided_at")

    return {"schema": "phase-user-challenge-v1", "trigger": trigger,
            "resolved": decision is not None}


def cmd_validate_challenge(args: argparse.Namespace) -> dict[str, Any]:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    return validate_challenge(payload)


def _challenge_id(state: dict[str, Any]) -> str:
    return f"CHAL-{len(state.get('challenges', [])) + 1}"


def cmd_record_challenge(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    state = _load(state_path)
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_challenge(payload)

    resolved = payload.get("decision") is not None
    entry = {
        "id": _challenge_id(state),
        "spec": args.spec,
        "status": "resolved" if resolved else "unresolved",
        "challenge": payload,
    }
    state.setdefault("challenges", []).append(entry)
    # An unresolved challenge blocks the challenged decision: mark the spec so
    # the scheduler will not pass the decision until it is answered.
    if not resolved and args.spec in state.get("specs", {}):
        _set_status(state["specs"][args.spec], "challenge_required")
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": entry["status"], "challengeId": entry["id"], "blocked": not resolved}


def cmd_resolve_challenge(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    state = _load(state_path)
    for entry in state.get("challenges", []):
        if entry["id"] == args.challenge_id:
            options = {o["id"] for o in entry["challenge"].get("options", [])}
            if args.option not in options:
                raise ContractError("invalid_challenge",
                                    f"option {args.option!r} is not offered by {args.challenge_id}")
            entry["status"] = "resolved"
            entry["challenge"]["decision"] = {
                "option_id": args.option, "decided_at": _now(),
            }
            state["updatedAt"] = _now()
            _atomic_write(state_path, state)
            return {"status": "resolved", "challengeId": args.challenge_id,
                    "selected": args.option}
    raise ContractError("unknown_challenge", f"no challenge {args.challenge_id!r} in state")


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
        _set_status(record, "failed")
        record["evidence"].append("merge_conflict")
        state["updatedAt"] = _now()
        _atomic_write(state_path, state)
        return {"status": "attention_required", "reason": "merge_conflict", "merged": False}

    merge_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    worktree_path = record.get("worktreePath")
    if worktree_path:
        _git(repo, "worktree", "remove", "--force", worktree_path, check=False)

    _set_status(record, "integrated")
    record.update({
        "mergeCommit": merge_commit,
        "worktreePath": None,
    })
    record["evidence"].extend(payload["verification"]["evidence"])
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "integrated", "mergeCommit": merge_commit, "merged": True}


def cmd_record_exit_criterion(args: argparse.Namespace) -> dict[str, Any]:
    """Record one exit-criterion verdict onto `exitCriteria[]` (Story 2).

    Idempotent by `id`: re-recording the same criterion (e.g. re-verified
    after `--resume`) updates its entry in place instead of accumulating
    duplicates. `.class` and `.verdict` are validated on write, same as
    `_set_status` — readers stay tolerant of an unrecognized value written by
    a newer reducer; only mutation is guarded.
    """
    if args.cls not in EXIT_CRITERION_CLASSES:
        raise ContractError("invalid_criterion", f"unknown criterion class: {args.cls!r}")
    if args.verdict not in EXIT_CRITERION_VERDICTS:
        raise ContractError("invalid_criterion", f"unknown criterion verdict: {args.verdict!r}")

    state_path = Path(args.state)
    state = _load(state_path)
    entry = {
        "id": args.id,
        "source": args.source,
        "class": args.cls,
        "verdict": args.verdict,
        "evidence": args.evidence,
    }
    criteria = state.setdefault("exitCriteria", [])
    for i, existing in enumerate(criteria):
        if existing.get("id") == args.id:
            criteria[i] = entry
            break
    else:
        criteria.append(entry)
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "recorded", "id": args.id, "verdict": args.verdict}


def cmd_set_terminal_status(args: argparse.Namespace) -> dict[str, Any]:
    """Set the phase's terminal status (Story 2).

    Mutually exclusive with `haltReported` by construction: a run that hit
    its loop bound has not reached a terminal status. This writer always
    clears any stale `haltReported` left by an earlier halt in the same
    write — a phase that halted once and later `--resume`s to completion
    must not carry both fields, or Story 3's checker would keep reporting it
    `impossible` forever.
    """
    if args.status not in TERMINAL_STATUSES:
        raise ContractError("invalid_terminal_status", f"unknown terminal status: {args.status!r}")

    state_path = Path(args.state)
    state = _load(state_path)
    state["terminalStatus"] = args.status
    halt_reported_cleared = state.pop("haltReported", None) is not None
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "recorded", "terminalStatus": args.status,
            "haltReportedCleared": halt_reported_cleared}


def cmd_record_halt(args: argparse.Namespace) -> dict[str, Any]:
    """Record loop-bound exhaustion as `haltReported` (Story 2).

    Never sets `terminalStatus`: a halted run has not reached a terminal
    status, and writing one here would be exactly the self-certification
    `on_exhaustion: halt_reported` forbids.
    """
    try:
        bound = int(args.bound)
        reached = int(args.reached)
    except ValueError:
        raise ContractError("invalid_halt", "bound and reached must be integers")

    state_path = Path(args.state)
    state = _load(state_path)
    state["haltReported"] = {
        "unit": args.unit,
        "bound": bound,
        "reached": reached,
        "lastIntegrated": args.last_integrated or None,
    }
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "recorded", "haltReported": state["haltReported"]}


def cmd_set_dependencies(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    state = _load(state_path)
    record = _spec_record(state, args.spec)
    record["dependencies"] = [d.strip() for d in args.deps.split(",") if d.strip()]
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "ok", "spec": args.spec, "dependencies": record["dependencies"]}


def cmd_classify(args: argparse.Namespace) -> dict[str, Any]:
    """Decide retry vs quarantine for a non-successful result.

    One retry is permitted only for a transient first-attempt failure. A
    terminal failure, or a transient failure after the permitted retry, is a
    terminal disposition (quarantine).
    """
    state = _load(Path(args.state))
    record = _spec_record(state, args.spec)
    payload = json.loads(Path(args.result).read_text(encoding="utf-8"))
    failure = payload.get("failure") or {}
    classification = failure.get("classification")
    attempts = record.get("attempts", 0)
    if classification == "transient" and attempts < 2:
        return {"action": "retry", "attempts": attempts}
    return {"action": "quarantine", "attempts": attempts,
            "classification": classification or "terminal"}


def cmd_retry(args: argparse.Namespace) -> dict[str, Any]:
    """Record a bounded retry in the same lane without a new confirmation."""
    state_path = Path(args.state)
    state = _load(state_path)
    record = _spec_record(state, args.spec)
    if record.get("attempts", 0) >= 2:
        raise ContractError("retry_exhausted",
                            f"{args.spec} already used its permitted retry")
    record["attempts"] = record.get("attempts", 0) + 1
    _set_status(record, "implementing")
    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {"status": "retrying", "attempts": record["attempts"], "laneBranch": record.get("laneBranch")}


def _quarantine_name(repo: Path, spec: str) -> str:
    base = f"writ/quarantine/{spec}"
    if _git(repo, "rev-parse", "--verify", base, check=False).returncode != 0:
        return base
    suffix = 2
    while _git(repo, "rev-parse", "--verify", f"{base}-{suffix}", check=False).returncode == 0:
        suffix += 1
    return f"{base}-{suffix}"


def _transitive_dependents(state: dict[str, Any], root: str) -> list[str]:
    specs = state.get("specs", {})
    blocked: list[str] = []
    frontier = [root]
    while frontier:
        current = frontier.pop()
        for spec, rec in specs.items():
            if current in rec.get("dependencies", []) and spec not in blocked and spec != root:
                blocked.append(spec)
                frontier.append(spec)
    return blocked


def cmd_quarantine(args: argparse.Namespace) -> dict[str, Any]:
    """Terminal disposition: preserve the failed lane as a quarantine branch,
    guarantee the phase branch is clean of it, and block declared dependents."""
    state_path = Path(args.state)
    repo = Path(args.repo)
    state = _load(state_path)
    record = _spec_record(state, args.spec)
    phase_head_before = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()

    lane_branch = record.get("laneBranch")
    worktree_path = record.get("worktreePath")
    if worktree_path and Path(worktree_path).exists():
        _git(repo, "worktree", "remove", "--force", worktree_path, check=False)

    quarantine_branch = _quarantine_name(repo, args.spec)
    if lane_branch and _git(repo, "rev-parse", "--verify", lane_branch, check=False).returncode == 0:
        rename = _git(repo, "branch", "-m", lane_branch, quarantine_branch, check=False)
        if rename.returncode != 0:
            # Renaming failed: keep the lane, mark attention, leave phase clean.
            _set_status(record, "failed")
            record["evidence"].append("quarantine_rename_failed")
            state["updatedAt"] = _now()
            _atomic_write(state_path, state)
            return {"status": "attention_required", "reason": "quarantine_rename_failed",
                    "laneBranch": lane_branch}

    # The failed lane never merged, so the phase branch must be unchanged.
    phase_head_after = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()
    phase_clean = phase_head_after == phase_head_before

    _set_status(record, "quarantined")
    record.update({
        "quarantineBranch": quarantine_branch,
        "worktreePath": None,
        "failure": {"summary": args.summary or "terminal failure",
                    "attempts": record.get("attempts", 0)},
    })
    record.setdefault("evidence", []).append(f"quarantine:{quarantine_branch}")

    blocked = _transitive_dependents(state, args.spec)
    for dep in blocked:
        _set_status(state["specs"][dep], "skipped_blocked")
        bl = state["specs"][dep].setdefault("blockedBy", [])
        if args.spec not in bl:
            bl.append(args.spec)

    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {
        "status": "quarantined",
        "quarantineBranch": quarantine_branch,
        "phaseBranchClean": phase_clean,
        "blockedDependents": blocked,
        "recovery": f"git checkout {quarantine_branch}  # inspect, fix, then re-run the phase",
    }


def cmd_close_spec(args: argparse.Namespace) -> dict[str, Any]:
    """Terminal disposition by *decision*: this spec will never be built.

    Distinct from quarantine in three ways that all follow from "nothing
    failed": the lane branch keeps its `writ/phase/...` name rather than being
    renamed into `writ/quarantine/...`, no recovery command is offered, and the
    reason is mandatory — the phase report is obliged to print it, so an
    unexplained closure is an invalid write rather than a blank line in a report.
    """
    reason = (args.reason or "").strip()
    if not reason:
        # Validated before _load and before any git call: a refused closure must
        # leave the state file byte-identical.
        raise ContractError("invalid_closure",
                            "a closure must record why the spec will not be built")

    state_path = Path(args.state)
    repo = Path(args.repo)
    state = _load(state_path)
    record = _spec_record(state, args.spec)

    if record.get("status") == "closed_not_implemented":
        # Never silently overwrite the first decision's reason and timestamp.
        raise ContractError(
            "already_closed",
            f"{args.spec} was already closed: "
            f"{(record.get('closure') or {}).get('reason', 'no reason recorded')}",
        )

    phase_head_before = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()

    # Free the worktree, but keep the lane branch: partial work is preserved
    # without a quarantine rename that would imply something went wrong.
    worktree_path = record.get("worktreePath")
    if worktree_path and Path(worktree_path).exists():
        _git(repo, "worktree", "remove", "--force", worktree_path, check=False)
    record["worktreePath"] = None

    _set_status(record, "closed_not_implemented")
    record["closure"] = {"reason": reason, "closedAt": _now()}
    record.setdefault("evidence", []).append(f"closed:{reason}")

    blocked: list[str] = []
    for dep in _transitive_dependents(state, args.spec):
        dep_record = state["specs"][dep]
        if dep_record.get("status") in TERMINAL_SPEC_STATUSES:
            # A dependent that already reached a terminal status keeps it —
            # downgrading an integrated spec would discard its merge commit.
            continue
        _set_status(dep_record, "skipped_blocked")
        bl = dep_record.setdefault("blockedBy", [])
        if args.spec not in bl:
            bl.append(args.spec)
        blocked.append(dep)

    phase_head_after = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()

    state["updatedAt"] = _now()
    _atomic_write(state_path, state)
    return {
        "status": "closed_not_implemented",
        "spec": args.spec,
        "reason": reason,
        "laneBranch": record.get("laneBranch"),
        "phaseBranchClean": phase_head_after == phase_head_before,
        "blockedDependents": blocked,
    }


def cmd_reconcile(args: argparse.Namespace) -> dict[str, Any]:
    """Read-only resume reconciliation: does recorded state agree with git?

    Reports the first mismatch and a recovery command without mutating git or
    guessing. Only when state and git agree may execution continue.
    """
    repo = Path(args.repo)
    state = _load(Path(args.state))
    mismatches: list[str] = []

    def branch_exists(name: str) -> bool:
        return _git(repo, "rev-parse", "--verify", name, check=False).returncode == 0

    if not branch_exists(state["phaseBranch"]):
        mismatches.append(f"phase branch {state['phaseBranch']} is missing")

    for spec, rec in state.get("specs", {}).items():
        status = rec.get("status")
        if status == "implementing":
            lane = rec.get("laneBranch")
            if lane and not branch_exists(lane):
                mismatches.append(f"{spec}: active lane {lane} recorded but missing in git")
            wt = rec.get("worktreePath")
            if wt and not Path(wt).exists():
                mismatches.append(f"{spec}: worktree {wt} recorded but missing on disk")
        if status == "quarantined":
            qb = rec.get("quarantineBranch")
            if qb and not branch_exists(qb):
                mismatches.append(f"{spec}: quarantine branch {qb} recorded but missing in git")
        if status == "closed_not_implemented":
            # A closed spec keeps its lane branch as preserved evidence, so a
            # recorded lane that has vanished is reported — symmetric with a
            # missing quarantine branch. Its worktree must already be released.
            lane = rec.get("laneBranch")
            if lane and not branch_exists(lane):
                mismatches.append(
                    f"{spec}: retained lane {lane} recorded for a closed spec but missing in git")
            if rec.get("worktreePath"):
                mismatches.append(
                    f"{spec}: closed spec still records worktree {rec['worktreePath']}")
        if status == "integrated" and not rec.get("mergeCommit"):
            mismatches.append(f"{spec}: integrated without a recorded merge commit")

    if mismatches:
        return {"status": "mismatch", "attention": True, "mismatches": mismatches,
                "recovery": "Reconcile git and phase state manually before resuming; "
                            "Writ will not rename, delete, or merge branches to 'repair' state."}
    return {"status": "consistent", "attention": False}


_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    stop = {"the", "a", "an", "and", "or", "of", "to", "in", "is", "for",
            "when", "then", "with", "that", "this", "it", "be", "on", "as"}
    return {w for w in _WORD.findall(text.lower()) if len(w) > 2 and w not in stop}


def _is_duplicate(statement: str, knowledge_dir: Path) -> bool:
    """Substantive (meaning-oriented) dedup: compare token overlap against every
    existing knowledge entry, not filenames or exact text. Conservative: a high
    Jaccard overlap with any existing entry is treated as a duplicate to avoid
    noisy repeated writeback."""
    candidate = _tokens(statement)
    if not candidate:
        return False
    for entry in knowledge_dir.rglob("*.md"):
        if entry.name == "README.md":
            continue
        existing = _tokens(entry.read_text(encoding="utf-8"))
        if not existing:
            continue
        overlap = len(candidate & existing) / len(candidate | existing)
        if overlap >= 0.5:
            return True
    return False


def _slug(title: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")


def _looks_like_path(token: str) -> bool:
    """True when a string is a plausible repo-relative path (no spaces; has a
    path separator or a dotted filename). Evidence entries are human-readable
    provenance (transcript ids, commit notes, observations); only path-like
    tokens belong in `related_artifacts`, or the consolidation reducer's stale
    detector misreads the prose as dangling references."""
    t = token.strip()
    if not t or " " in t:
        return False
    return "/" in t or "." in t


def knowledge_writeback(candidates: list[dict[str, Any]], knowledge_dir: Path,
                        already: set[str]) -> dict[str, Any]:
    """Apply the D6 evidence-bound qualification gates. A no-op (no qualifying
    candidate) changes no file and returns empty written/rejected-only results."""
    lessons_dir = knowledge_dir / "lessons"
    written: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for cand in candidates:
        cid = cand.get("id")
        if cid in already:
            continue  # resume-safe: never write a completed lesson twice
        statement = cand.get("statement", "")
        if not cand.get("generalizes"):
            rejected.append({"id": cid, "reason": "one-off (does not generalize beyond one spec)"})
            continue
        if not cand.get("evidence"):
            rejected.append({"id": cid, "reason": "unsupported (no cited artifact or repeated drift)"})
            continue
        if cand.get("adr_scale"):
            rejected.append({"id": cid, "reason": "adr-scale (architectural decision belongs in an ADR)"})
            continue
        if _is_duplicate(statement, knowledge_dir):
            rejected.append({"id": cid, "reason": "duplicate (substantively covered in the ledger)"})
            continue

        lessons_dir.mkdir(parents=True, exist_ok=True)
        title = cand.get("title") or statement[:60]
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = lessons_dir / f"{date}-{_slug(title)}.md"
        tags = cand.get("tags", []) or ["phase-close"]

        # `related_artifacts` must hold resolvable repo paths only; the prose
        # `evidence` becomes cited provenance in Context. Prefer an explicit
        # `artifacts` list, else keep only path-like evidence tokens.
        evidence = cand.get("evidence", [])
        artifact_paths = cand.get("artifacts") or [e for e in evidence if _looks_like_path(e)]
        if artifact_paths:
            related_block = "related_artifacts:\n" + "\n".join(f"  - {a}" for a in artifact_paths)
        else:
            related_block = "related_artifacts: []"
        context = "Recorded at phase close from evidence-bound knowledge writeback."
        if evidence:
            context += "\n\n**Cited evidence:**\n\n" + "\n".join(f"- {e}" for e in evidence)
        related_links = "\n".join(f"- `{a}`" for a in artifact_paths)
        path.write_text(
            f"---\ncategory: lessons\ntags: [{', '.join(tags)}]\n"
            f"created: {date}\n{related_block}\n---\n\n"
            f"# {title}\n\n## TL;DR\n\n{statement}\n\n## Context\n\n"
            f"{context}\n\n## Related\n\n{related_links}\n",
            encoding="utf-8",
        )
        written.append({"id": cid, "path": str(path.relative_to(knowledge_dir.parent.parent))
                        if knowledge_dir.parent.parent in path.parents else str(path)})

    return {"written": written, "rejected": rejected}


def cmd_knowledge_writeback(args: argparse.Namespace) -> dict[str, Any]:
    knowledge_dir = Path(args.knowledge_dir)
    payload = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])

    already: set[str] = set()
    state = None
    state_path = None
    if args.state:
        state_path = Path(args.state)
        state = _load(state_path)
        already = {w.get("id") for w in state.get("knowledgeWritten", [])}

    result = knowledge_writeback(candidates, knowledge_dir, already)

    if state is not None and result["written"]:
        state.setdefault("knowledgeWritten", []).extend(result["written"])
        state["updatedAt"] = _now()
        _atomic_write(state_path, state)

    result["noop"] = not result["written"]
    return result


def cmd_progress(args: argparse.Namespace) -> dict[str, Any]:
    """Read-only phase progress summary for /status."""
    state = _load(Path(args.state))
    specs = state.get("specs", {})
    # Seeded from the vocabulary so the counts and SPEC_STATUSES cannot drift —
    # the drift that let `challenge_required` go uncounted for three stories.
    # Accumulation below still uses .get(), so a status written by a newer
    # reducer is reported under its own key rather than crashing or vanishing.
    counts = {status: 0 for status in sorted(SPEC_STATUSES)}
    quarantine = []
    closed = {}
    current = None
    for spec, rec in specs.items():
        counts[rec.get("status", "pending")] = counts.get(rec.get("status", "pending"), 0) + 1
        if rec.get("status") == "implementing" and current is None:
            current = {"spec": spec, "laneBranch": rec.get("laneBranch")}
        if rec.get("quarantineBranch"):
            quarantine.append(rec["quarantineBranch"])
        if rec.get("status") == "closed_not_implemented":
            closed[spec] = (rec.get("closure") or {}).get("reason")

    # `blockedBy` means "upstream reached a terminal status without delivering"
    # — which is either a quarantine or a closure. Report which, or a reader who
    # sees skipped_blocked goes hunting for a quarantine branch that was never
    # created.
    blocked = {}
    for spec, rec in specs.items():
        if rec.get("status") != "skipped_blocked":
            continue
        upstream = [u for u in rec.get("blockedBy", []) if u in specs]
        causes = {specs[u].get("status") for u in upstream}
        blocked[spec] = {
            "by": upstream,
            "cause": causes.pop() if len(causes) == 1 else ("mixed" if causes else None),
        }

    return {
        "phase": state.get("phase"),
        "phaseBranch": state.get("phaseBranch"),
        "current": current,
        "counts": counts,
        "quarantineBranches": quarantine,
        "blocked": blocked,
        "closed": closed,
    }


def _artifact_status(path: str | None) -> str:
    """Classify a summary artifact as pass / fail / missing.

    An eval or verification report is 'pass' only when it records zero findings;
    a missing file is 'missing' (a Warning input, never a failure)."""
    if not path:
        return "missing"
    p = Path(path)
    if not p.is_file():
        return "missing"
    text = p.read_text(encoding="utf-8")
    m = re.search(r"Findings:\s*(\d+)", text)
    if m:
        return "pass" if int(m.group(1)) == 0 else "fail"
    low = text.lower()
    if "fail" in low and "0 fail" not in low:
        return "fail"
    return "pass"


def cmd_health(args: argparse.Namespace) -> dict[str, Any]:
    """Categorical health (D7). Missing/stale evidence is a Warning, never a
    failure; Attention requires an affirmative current failure, unresolved
    material drift, or a state/git mismatch. No score, no deep or external checks."""
    eval_status = _artifact_status(args.eval or None)
    verify_status = _artifact_status(args.verification or None)

    drift_status = "none"
    if args.drift:
        dp = Path(args.drift)
        if not dp.is_file():
            drift_status = "missing"
        else:
            text = dp.read_text(encoding="utf-8").lower()
            drift_status = "material" if ("unresolved" in text or "material" in text) else "none"
    else:
        drift_status = "missing"

    state_status = "n/a"
    if args.state and args.repo:
        reconciled = cmd_reconcile(args)
        state_status = "mismatch" if reconciled.get("attention") else "consistent"

    unavailable = []
    if eval_status == "missing":
        unavailable.append("eval summary")
    if verify_status == "missing":
        unavailable.append("verification report")
    if drift_status == "missing":
        unavailable.append("drift log")

    failures = []
    if eval_status == "fail":
        failures.append("eval findings present")
    if verify_status == "fail":
        failures.append("verification failing")
    if drift_status == "material":
        failures.append("unresolved material drift")
    if state_status == "mismatch":
        failures.append("phase-state/git mismatch")

    if failures:
        category = "Attention"
    elif unavailable:
        category = "Warning"
    else:
        category = "Healthy"

    return {
        "category": category,
        "sources": {"eval": eval_status, "verification": verify_status,
                    "drift": drift_status, "state": state_status},
        "unavailable": unavailable,
        "failures": failures,
    }


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

    p = sub.add_parser("validate-challenge")
    p.add_argument("--input", required=True)
    p.set_defaults(func=cmd_validate_challenge)

    p = sub.add_parser("record-challenge")
    p.add_argument("--state", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--input", required=True)
    p.set_defaults(func=cmd_record_challenge)

    p = sub.add_parser("resolve-challenge")
    p.add_argument("--state", required=True)
    p.add_argument("--challenge-id", required=True)
    p.add_argument("--option", required=True)
    p.set_defaults(func=cmd_resolve_challenge)

    p = sub.add_parser("integrate")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--result", required=True)
    p.set_defaults(func=cmd_integrate)

    p = sub.add_parser("record-exit-criterion")
    p.add_argument("--state", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--class", dest="cls", required=True)
    p.add_argument("--verdict", required=True)
    p.add_argument("--evidence", default="")
    p.set_defaults(func=cmd_record_exit_criterion)

    p = sub.add_parser("set-terminal-status")
    p.add_argument("--state", required=True)
    p.add_argument("--status", required=True)
    p.set_defaults(func=cmd_set_terminal_status)

    p = sub.add_parser("record-halt")
    p.add_argument("--state", required=True)
    p.add_argument("--unit", required=True)
    p.add_argument("--bound", required=True)
    p.add_argument("--reached", required=True)
    p.add_argument("--last-integrated", default="")
    p.set_defaults(func=cmd_record_halt)

    p = sub.add_parser("set-dependencies")
    p.add_argument("--state", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--deps", default="")
    p.set_defaults(func=cmd_set_dependencies)

    p = sub.add_parser("classify")
    p.add_argument("--state", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--result", required=True)
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("retry")
    p.add_argument("--state", required=True)
    p.add_argument("--spec", required=True)
    p.set_defaults(func=cmd_retry)

    p = sub.add_parser("quarantine")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--summary", default="")
    p.set_defaults(func=cmd_quarantine)

    p = sub.add_parser("close-spec")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_close_spec)

    p = sub.add_parser("reconcile")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.set_defaults(func=cmd_reconcile)

    p = sub.add_parser("knowledge-writeback")
    p.add_argument("--candidates", required=True)
    p.add_argument("--knowledge-dir", required=True)
    p.add_argument("--state", default="")
    p.set_defaults(func=cmd_knowledge_writeback)

    p = sub.add_parser("progress")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_progress)

    p = sub.add_parser("health")
    p.add_argument("--state", default="")
    p.add_argument("--repo", default="")
    p.add_argument("--eval", default="")
    p.add_argument("--verification", default="")
    p.add_argument("--drift", default="")
    p.set_defaults(func=cmd_health)

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
