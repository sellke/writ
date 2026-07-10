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
        state["specs"][args.spec]["status"] = "challenge_required"
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
    record["status"] = "implementing"
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
            record["status"] = "failed"
            record["evidence"].append("quarantine_rename_failed")
            state["updatedAt"] = _now()
            _atomic_write(state_path, state)
            return {"status": "attention_required", "reason": "quarantine_rename_failed",
                    "laneBranch": lane_branch}

    # The failed lane never merged, so the phase branch must be unchanged.
    phase_head_after = _git(repo, "rev-parse", state["phaseBranch"]).stdout.strip()
    phase_clean = phase_head_after == phase_head_before

    record.update({
        "status": "quarantined",
        "quarantineBranch": quarantine_branch,
        "worktreePath": None,
        "failure": {"summary": args.summary or "terminal failure",
                    "attempts": record.get("attempts", 0)},
    })
    record.setdefault("evidence", []).append(f"quarantine:{quarantine_branch}")

    blocked = _transitive_dependents(state, args.spec)
    for dep in blocked:
        state["specs"][dep]["status"] = "skipped_blocked"
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
        artifacts = "\n".join(f"  - {a}" for a in cand["evidence"])
        path.write_text(
            f"---\ncategory: lessons\ntags: [{', '.join(tags)}]\n"
            f"created: {date}\nrelated_artifacts:\n{artifacts}\n---\n\n"
            f"# {title}\n\n## TL;DR\n\n{statement}\n\n## Context\n\n"
            f"Recorded at phase close from evidence-bound knowledge writeback.\n\n"
            f"## Detail\n\n{statement}\n\n## Related\n\n",
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

    p = sub.add_parser("reconcile")
    p.add_argument("--state", required=True)
    p.add_argument("--repo", required=True)
    p.set_defaults(func=cmd_reconcile)

    p = sub.add_parser("knowledge-writeback")
    p.add_argument("--candidates", required=True)
    p.add_argument("--knowledge-dir", required=True)
    p.add_argument("--state", default="")
    p.set_defaults(func=cmd_knowledge_writeback)

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
