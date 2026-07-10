#!/usr/bin/env python3
"""
Story 5 adversarial scenarios: merge, ancestry, release substeps, finalize, and recovery.
Bootstraps state through Story 4 pipeline (via eval-recommend-stage helpers) then drives
Story 5 operations with provider fakes and disposable git repos.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HELPER = Path(__file__).with_name("recommend-state.py")
_stage_spec = importlib.util.spec_from_file_location(
    "stage4", Path(__file__).with_name("eval-recommend-stage.py")
)
_stage4 = importlib.util.module_from_spec(_stage_spec)
_stage_spec.loader.exec_module(_stage4)

# ── result counters ──────────────────────────────────────────────────────────
passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n")
        print(f"FAIL\t{name}\t{safe}")


def helper(*args: object) -> tuple[subprocess.CompletedProcess[str], dict]:
    return _stage4.helper(*args)


def event(state: Path, operation: str, evidence: dict) -> tuple[subprocess.CompletedProcess[str], dict]:
    return _stage4.event(state, operation, evidence)


def write(path: Path, text: str) -> None:
    _stage4.write(path, text)


def sync_log(state: Path) -> None:
    _stage4.sync_log(state)


def append_audit(state: Path, operation: str, *, pending: bool) -> str:
    return _stage4.append_audit(state, operation, pending=pending)


def finalize_audit(state: Path, entry_id: str, result: str) -> None:
    _stage4.finalize_audit(state, entry_id, result)


def operation_key(kind: str, *parts: str) -> str:
    return _stage4.operation_key(kind, *parts)


# ── fixture: fully approved state via Story 4 pipeline ──────────────────────

def make_approved_fixture(root: Path) -> tuple[Path, Path, str]:
    """Run through the full Story 4 pipeline to production_approved.
    Returns (repo, state_path, feature_sha)."""
    global _stage4
    repo, base_state = _stage4.fixture(root)
    sha_a = _stage4.SHA_A

    # Duplicate base state for Story 5 fixture
    state = base_state.with_name("recommend-execution-story5.json")
    shutil.copy2(base_state, state)
    base_val = json.loads(base_state.read_text())
    log_path = Path(base_val["repository"]["rootIdentity"]) / base_val["spec"]["recommendationLog"]["path"]
    log_path.write_text(
        log_path.read_text().replace("- **Result:** Pending", "- **Result:** Cancelled")
    )
    sync_log(state)

    # Full Story 4 pipeline
    _stage4.make_ready(state, repo)
    approve_payload = _stage4.approval_event(state, "approve", "approve-s5")
    result, _ = event(state, "record-approval", approve_payload)
    if result.returncode != 0:
        raise RuntimeError(f"Could not reach production_approved: {result.stdout}")
    val = json.loads(state.read_text())
    if val["status"] != "production_approved":
        raise RuntimeError(f"Unexpected status after approval: {val['status']}")
    return repo, state, sha_a


def fresh_approved(root: Path, base: Path, base_repo: Path, sha_a: str, name: str) -> Path:
    """Copy an approved state to a fresh named path and reset log pending entries."""
    # Reset any pending log entries (left from prior tests) before copying state
    base_val = json.loads(base.read_text())
    log_path = Path(base_val["repository"]["rootIdentity"]) / base_val["spec"]["recommendationLog"]["path"]
    log_path.write_text(
        log_path.read_text().replace("- **Result:** Pending", "- **Result:** Cancelled"),
        encoding="utf-8",
    )
    state = base.with_name(f"recommend-execution-{name}.json")
    shutil.copy2(base, state)
    sync_log(state)
    return state


def get_sha_a() -> str:
    return _stage4.SHA_A


# ── Story 5 operation helpers ────────────────────────────────────────────────

def merge_op_key(state: Path) -> str:
    val = json.loads(state.read_text())
    d = val["delivery"]
    sha_a = _stage4.SHA_A
    return operation_key("merge", d["capabilitySnapshot"]["repositoryId"],
                         d["pr"]["providerId"], sha_a, "merge")


def do_merge_attempt(state: Path, strategy: str = "merge", *,
                     bypass: bool = False, force: bool = False,
                     fresh_head: str | None = None,
                     audit_entry: str | None = None) -> tuple[subprocess.CompletedProcess[str], dict]:
    sha_a = _stage4.SHA_A
    val = json.loads(state.read_text())
    d = val["delivery"]
    head = fresh_head or sha_a
    mk = operation_key("merge", d["capabilitySnapshot"]["repositoryId"],
                       d["pr"]["providerId"], sha_a, strategy)
    if audit_entry is None:
        audit_entry = append_audit(state, mk, pending=True)
    return event(state, "record-merge-attempt", {
        "schema": "recommend-merge-attempt-v1",
        "strategy": strategy,
        "auditEntryId": audit_entry,
        "bypassProtection": bypass,
        "forceStrategy": force,
        "freshPr": {
            "provider": d["capabilitySnapshot"]["provider"],
            "repositoryId": d["capabilitySnapshot"]["repositoryId"],
            "providerId": d["pr"]["providerId"],
            "baseBranch": d["pr"]["baseBranch"],
            "headBranch": d["pr"]["headBranch"],
            "headSha": head,
            "state": "open",
        },
    })


def do_merge_result(state: Path, merge_commit_sha: str, *,
                    outcome: str = "merged") -> tuple[subprocess.CompletedProcess[str], dict]:
    """Record merge result. Expects merge attempt already recorded (pending entry present).
    Finalizes the pending audit entry before recording result."""
    val = json.loads(state.read_text())
    audit_entry = val["delivery"]["merge"]["auditEntryId"]
    merge_key = val["delivery"]["merge"]["operationKey"]
    # Finalize the pending audit entry, preserving the operation key for require_audit_binding
    finalize_audit(state, audit_entry,
                   f"Applied — operation key {merge_key}; outcome {outcome}; merge commit {merge_commit_sha}.")
    return event(state, "record-merge-result", {
        "schema": "recommend-merge-result-v1",
        "mergeCommitSha": merge_commit_sha,
        "outcome": outcome,
        "providerOperationId": f"merge-op-{merge_commit_sha[:8]}",
        "mergedAt": "2026-07-10T15:30:00Z",
        "auditEntryId": audit_entry,
    })


def simulate_merge(repo: Path, sha_a: str) -> str:
    """Create a merge commit of HEAD into a fake default branch. Returns merge commit SHA."""
    # The fixture uses 'feature/stage' branch. We need to simulate merge onto 'main'.
    # Create main branch from an earlier point.
    cwd = str(repo)
    # Switch to main (or create it) and merge the feature branch
    branches_out = subprocess.check_output(["git", "branch", "--list", "main"], cwd=cwd, text=True)
    if "main" not in branches_out:
        # Create main at the initial commit
        first = subprocess.check_output(
            ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=cwd, text=True
        ).strip()
        subprocess.run(["git", "branch", "main", first], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "main"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(
        ["git", "merge", "--no-ff", "feature/stage", "-m", "merge feature into main"],
        cwd=cwd, check=True, capture_output=True,
    )
    merge_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True).strip()
    subprocess.run(["git", "checkout", "feature/stage"], cwd=cwd, check=True, capture_output=True)
    return merge_sha


def do_verify_ancestry(state: Path, repo: Path, merge_sha: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    return event(state, "verify-ancestry", {
        "schema": "recommend-ancestry-verification-v1",
        "defaultBranchHeadSha": merge_sha,
        "observedAt": "2026-07-10T15:35:00Z",
    })


def do_substep(state: Path, substep: str, extra: dict | None = None,
               *, audit_entry: str | None = None) -> tuple[subprocess.CompletedProcess[str], dict]:
    val = json.loads(state.read_text())
    cap = val["delivery"]["capabilitySnapshot"]
    substep_id = (extra or {}).get("substepId", substep + "-id")
    mk = operation_key("substep", cap["repositoryId"], substep, substep_id)
    if audit_entry is None:
        audit_entry = append_audit(state, mk, pending=False)
    base = {"schema": "recommend-release-substep-v1", "substep": substep,
            "substepId": substep_id, "auditEntryId": audit_entry}
    if extra:
        base.update(extra)
    return event(state, "record-release-substep", base)


SHA_TAG = "f" * 40
SHA_REL = "e" * 40


def do_all_substeps(state: Path) -> bool:
    sha_a = _stage4.SHA_A
    steps = [
        ("version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"}),
        ("changelog-write", {"sha": sha_a, "substepId": sha_a}),
        ("release-commit", {"sha": sha_a, "substepId": sha_a + "-rel"}),
        ("tag-create", {"tag": "v0.14.1", "sha": sha_a, "substepId": "v0.14.1"}),
        ("push-commit", {"sha": sha_a, "substepId": sha_a + "-push"}),
        ("push-tag", {"tag": "v0.14.1", "substepId": "v0.14.1-push"}),
        ("provider-release", {"providerId": "gh-rel-001",
                              "url": "https://github.com/example/repo/releases/tag/v0.14.1",
                              "substepId": "gh-rel-001"}),
    ]
    for substep, extra in steps:
        result, payload = do_substep(state, substep, extra)
        if result.returncode != 0:
            return False
    return True


def do_finalize(state: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    return event(state, "finalize-release", {"schema": "recommend-release-finalization-v1"})


# ── tests ────────────────────────────────────────────────────────────────────

def run() -> None:
    root = Path(tempfile.mkdtemp(prefix="writ-story5-eval-"))
    try:
        repo, approved_base, sha_a = make_approved_fixture(root)

        def fresh(name: str) -> Path:
            return fresh_approved(root, approved_base, repo, sha_a, name)

        # ── merge attempt ────────────────────────────────────────────────
        state = fresh("merge-happy")
        result, payload = do_merge_attempt(state)
        emit("merge-attempt-advances-to-merging",
             result.returncode == 0 and payload.get("status") == "merging", payload)

        state = fresh("merge-wrong-state")
        val = json.loads(state.read_text())
        val["status"] = "awaiting_approval"
        val["resumeTarget"] = "awaiting_approval"
        state.write_text(json.dumps(val))
        sync_log(state)
        result, payload = do_merge_attempt(state)
        emit("merge-attempt-wrong-state-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_transition",
             payload)

        state = fresh("merge-bypass")
        result, payload = do_merge_attempt(state, bypass=True)
        emit("merge-bypass-protection-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "policy_violation",
             payload)

        state = fresh("merge-force")
        result, payload = do_merge_attempt(state, force=True)
        emit("merge-force-strategy-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "policy_violation",
             payload)

        state = fresh("merge-bad-strategy")
        result, payload = do_merge_attempt(state, strategy="fast-forward")
        emit("merge-unknown-strategy-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_evidence",
             payload)

        state = fresh("merge-stale-head")
        result, payload = do_merge_attempt(state, fresh_head="b" * 40)
        emit("merge-stale-fresh-head-blocks",
             result.returncode != 0, payload)

        state = fresh("merge-rejected-approval")
        val = json.loads(state.read_text())
        val["delivery"]["approval"]["status"] = "rejected"
        val["delivery"]["approval"]["approvedPrHeadSha"] = None
        state.write_text(json.dumps(val))
        sync_log(state)
        result, payload = do_merge_attempt(state)
        emit("merge-rejected-approval-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "approval_invalid",
             payload)

        # ── merge result ─────────────────────────────────────────────────
        merge_sha = simulate_merge(repo, sha_a)

        state = fresh("merge-result-happy")
        result, _ = do_merge_attempt(state)
        if result.returncode == 0:
            result, payload = do_merge_result(state, merge_sha)
            emit("merge-result-records-commit-sha",
                 result.returncode == 0 and payload.get("mergeCommitSha") == merge_sha, payload)
        else:
            emit("merge-result-records-commit-sha", False, "pre-step failed")

        state = fresh("merge-result-bad-sha")
        result, _ = do_merge_attempt(state)
        if result.returncode == 0:
            val = json.loads(state.read_text())
            val["spec"]["recommendationLog"]["pendingEntryIds"] = []
            state.write_text(json.dumps(val))
            result, payload = event(state, "record-merge-result", {
                "schema": "recommend-merge-result-v1",
                "mergeCommitSha": "not-a-sha",
                "outcome": "merged",
                "providerOperationId": "op-001",
                "auditEntryId": val["delivery"]["merge"]["auditEntryId"],
            })
            emit("merge-result-invalid-sha-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_evidence",
                 payload)
        else:
            emit("merge-result-invalid-sha-blocks", False, "pre-step failed")

        # ── ancestry verification ────────────────────────────────────────
        state = fresh("ancestry-happy")
        result, _ = do_merge_attempt(state)
        if result.returncode == 0:
            result, _ = do_merge_result(state, merge_sha)
            if result.returncode == 0:
                result, payload = do_verify_ancestry(state, repo, merge_sha)
                emit("ancestry-verified-advances-to-releasing",
                     result.returncode == 0 and payload.get("status") == "releasing", payload)
            else:
                emit("ancestry-verified-advances-to-releasing", False, "pre-step failed")
        else:
            emit("ancestry-verified-advances-to-releasing", False, "pre-step failed")

        state = fresh("ancestry-missing-commit")
        result, _ = do_merge_attempt(state)
        if result.returncode == 0:
            val = json.loads(state.read_text())
            val["delivery"]["merge"]["mergeCommitSha"] = "b" * 40
            val["spec"]["recommendationLog"]["pendingEntryIds"] = []
            state.write_text(json.dumps(val))
            result, payload = event(state, "verify-ancestry", {
                "schema": "recommend-ancestry-verification-v1",
                "defaultBranchHeadSha": "c" * 40,
                "observedAt": "2026-07-10T15:35:00Z",
            })
            emit("ancestry-missing-commit-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "merge_commit_missing",
                 payload)
        else:
            emit("ancestry-missing-commit-blocks", False, "pre-step failed")

        state = fresh("ancestry-not-in-branch")
        result, _ = do_merge_attempt(state)
        if result.returncode == 0:
            # Create a commit on a temporary branch that is NOT merged into main
            subprocess.run(["git", "checkout", "-b", "orphan-branch"], cwd=str(repo),
                           check=True, capture_output=True)
            (repo / "orphan.txt").write_text("orphan\n")
            subprocess.run(["git", "add", "orphan.txt"], cwd=str(repo), check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "orphan"], cwd=str(repo), check=True, capture_output=True)
            orphan_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(repo), text=True
            ).strip()
            subprocess.run(["git", "checkout", "feature/stage"], cwd=str(repo), check=True, capture_output=True)
            # Use merge_sha (main HEAD after simulate_merge) as default branch head
            # orphan_sha is NOT an ancestor of merge_sha (it's on a separate branch)
            val = json.loads(state.read_text())
            val["delivery"]["merge"]["mergeCommitSha"] = orphan_sha
            val["spec"]["recommendationLog"]["pendingEntryIds"] = []
            state.write_text(json.dumps(val))
            result, payload = event(state, "verify-ancestry", {
                "schema": "recommend-ancestry-verification-v1",
                "defaultBranchHeadSha": merge_sha,
                "observedAt": "2026-07-10T15:35:00Z",
            })
            emit("ancestry-not-in-branch-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "merge_ancestry_not_confirmed",
                 payload)
        else:
            emit("ancestry-not-in-branch-blocks", False, "pre-step failed")

        # ── release substeps ─────────────────────────────────────────────
        def reach_releasing(name: str) -> Path | None:
            s = fresh(name)
            if do_merge_attempt(s)[0].returncode != 0:
                return None
            if do_merge_result(s, merge_sha)[0].returncode != 0:
                return None
            if do_verify_ancestry(s, repo, merge_sha)[0].returncode != 0:
                return None
            return s

        state = reach_releasing("substep-version")
        if state:
            result, payload = do_substep(state, "version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"})
            emit("substep-version-reconcile-ok", result.returncode == 0, payload)
        else:
            emit("substep-version-reconcile-ok", False, "pre-step failed")

        state = reach_releasing("substep-npm-blocks")
        if state:
            val = json.loads(state.read_text())
            cap = val["delivery"]["capabilitySnapshot"]
            mk = operation_key("substep", cap["repositoryId"], "provider-release", "npm-pub")
            audit_id = append_audit(state, mk, pending=False)
            result, payload = event(state, "record-release-substep", {
                "schema": "recommend-release-substep-v1",
                "substep": "provider-release",
                "substepId": "npm-pub",
                "providerId": "npm-001",
                "url": "https://npmjs.com/package/@sellke/writ",
                "publishNpm": True,
                "auditEntryId": audit_id,
            })
            emit("substep-npm-publish-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "policy_violation",
                 payload)
        else:
            emit("substep-npm-publish-blocks", False, "pre-step failed")

        state = reach_releasing("substep-force-push-blocks")
        if state:
            force_sha = sha_a
            val = json.loads(state.read_text())
            cap = val["delivery"]["capabilitySnapshot"]
            mk = operation_key("substep", cap["repositoryId"], "push-commit", force_sha)
            audit_id = append_audit(state, mk, pending=False)
            result, payload = event(state, "record-release-substep", {
                "schema": "recommend-release-substep-v1",
                "substep": "push-commit",
                "substepId": force_sha,
                "sha": force_sha,
                "forced": True,
                "auditEntryId": audit_id,
            })
            emit("substep-force-push-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "policy_violation",
                 payload)
        else:
            emit("substep-force-push-blocks", False, "pre-step failed")

        state = reach_releasing("substep-conflict-blocks")
        if state:
            # First do version-reconcile once successfully
            result1, p1 = do_substep(state, "version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"})
            if result1.returncode == 0:
                # Now try again with different version → conflict
                result2, payload = do_substep(state, "version-reconcile", {"version": "0.14.2", "substepId": "0.14.2"})
                emit("substep-conflict-blocks",
                     result2.returncode != 0 and payload.get("blocker", {}).get("code") == "release_substep_conflict",
                     payload)
            else:
                emit("substep-conflict-blocks", False, f"first substep failed: {p1}")
        else:
            emit("substep-conflict-blocks", False, "pre-step failed")

        state = reach_releasing("substep-unknown-blocks")
        if state:
            result, payload = event(state, "record-release-substep", {
                "schema": "recommend-release-substep-v1",
                "substep": "upload-to-s3",
            })
            emit("substep-unknown-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_evidence",
                 payload)
        else:
            emit("substep-unknown-blocks", False, "pre-step failed")

        state = reach_releasing("substep-dedup")
        if state:
            result1, _ = do_substep(state, "version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"})
            if result1.returncode == 0:
                result2, payload = do_substep(state, "version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"})
                emit("substep-identical-deduplicates",
                     result2.returncode == 0 and payload.get("action") == "deduplicated",
                     payload)
            else:
                emit("substep-identical-deduplicates", False, "first substep failed")
        else:
            emit("substep-identical-deduplicates", False, "pre-step failed")

        # ── finalize-release ─────────────────────────────────────────────
        state = reach_releasing("finalize-happy")
        if state:
            ok = do_all_substeps(state)
            if ok:
                result, payload = do_finalize(state)
                emit("finalize-release-completes-delivery",
                     result.returncode == 0 and payload.get("status") == "complete", payload)
                ids = payload.get("finalIdentifiers", [])
                emit("finalize-release-identifiers-nonempty", len(ids) > 0, ids)
            else:
                emit("finalize-release-completes-delivery", False, "substeps failed")
                emit("finalize-release-identifiers-nonempty", False, "substeps failed")
        else:
            emit("finalize-release-completes-delivery", False, "pre-step failed")
            emit("finalize-release-identifiers-nonempty", False, "pre-step failed")

        state = reach_releasing("finalize-missing-substeps")
        if state:
            # Only do one substep then try to finalize
            do_substep(state, "version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"})
            result, payload = do_finalize(state)
            emit("finalize-missing-substeps-blocks",
                 result.returncode != 0 and payload.get("blocker", {}).get("code") == "release_substeps_incomplete",
                 payload)
        else:
            emit("finalize-missing-substeps-blocks", False, "pre-step failed")

        state = fresh("finalize-wrong-state")
        result, payload = do_finalize(state)
        emit("finalize-wrong-state-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_transition",
             payload)

        # ── Story 5 fields inert in pre-staging ──────────────────────────
        state = fresh("s5-fields-inert")
        val = json.loads(state.read_text())
        # Manually inject merge field into a non-staging delivery (impossible normally but test the guard)
        # We need to reach implementing status without staging
        state2 = fresh("s5-inert-impl")
        val2 = json.loads(state2.read_text())
        val2["status"] = "implementing"
        val2["resumeTarget"] = "implementing"
        val2["delivery"] = {
            "test": None, "commits": None, "pr": None, "checks": [],
            "preview": None, "uat": None, "approval": None,
            "merge": {"something": "here"}, "release": None,
        }
        state2.write_text(json.dumps(val2))
        result, payload = event(state2, "record-merge-attempt", {
            "schema": "recommend-merge-attempt-v1", "strategy": "merge",
        })
        emit("story5-fields-inert-in-pre-staging",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_state",
             payload)

        # ── partially_released recovery ──────────────────────────────────
        state = reach_releasing("partial-recovery")
        if state:
            # Do version-reconcile first
            result1, _ = do_substep(state, "version-reconcile", {"version": "0.14.1", "substepId": "0.14.1"})
            if result1.returncode == 0:
                # Manually set status to partially_released
                val = json.loads(state.read_text())
                val["status"] = "partially_released"
                val["resumeTarget"] = "partially_released"
                state.write_text(json.dumps(val))
                sync_log(state)
                # Now do changelog-write; should succeed and move back to releasing
                result2, payload = do_substep(state, "changelog-write", {"sha": sha_a, "substepId": sha_a})
                emit("partial-released-can-add-substeps",
                     result2.returncode == 0, payload)
                # After completing the contiguous prefix (v-r and c-w), should be releasing
                val3 = json.loads(state.read_text())
                emit("partial-released-recovers-to-releasing",
                     val3.get("status") == "releasing", val3.get("status"))
            else:
                emit("partial-released-can-add-substeps", False, "version-reconcile failed")
                emit("partial-released-recovers-to-releasing", False, "version-reconcile failed")
        else:
            emit("partial-released-can-add-substeps", False, "pre-step failed")
            emit("partial-released-recovers-to-releasing", False, "pre-step failed")

        # ── Story 4 regression: approval still works ─────────────────────
        state = fresh("s4-regression-approval")
        approve_payload = _stage4.approval_event(state, "approve", "approve-regression")
        result, payload = event(state, "record-approval", approve_payload)
        emit("story4-regression-approval-still-works",
             result.returncode == 0 and payload.get("status") == "production_approved", payload)

    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"\nSUMMARY\tpassed={passed}\tfailed={failed}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    _stage4.audit_counter = 100  # avoid collision with stage4 counter
    run()
