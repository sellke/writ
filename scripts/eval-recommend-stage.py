#!/usr/bin/env python3
"""Executable Story 4 provider fakes and reducer scenarios."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


HELPER = Path(__file__).with_name("recommend-state.py")
SHA_A = "a" * 40
SHA_B = "b" * 40
passed = 0
failed = 0


def operation_key(kind: str, *parts: str) -> str:
    return f"{kind}:{hashlib.sha256(chr(0).join(parts).encode()).hexdigest()}"


SHIP_KEY = operation_key("ship", "stage", SHA_A)
PR_KEY = operation_key("pr-create", "repo-1", "main", "feature/stage")


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n")
        print(f"FAIL\t{name}\t{safe}")


def command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def helper(*args: object) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = command([sys.executable, str(HELPER), *map(str, args)])
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout, "stderr": result.stderr}
    return result, payload


def fixture(root: Path) -> tuple[Path, Path]:
    global SHA_A, SHIP_KEY, PR_KEY
    repo = root / "repo"
    repo.mkdir(parents=True)
    command(["git", "init", "-b", "feature/stage"], repo)
    command(["git", "config", "user.name", "Writ Eval"], repo)
    command(["git", "config", "user.email", "eval@example.invalid"], repo)
    spec = repo / ".writ/specs/fixture"
    write(spec / "spec.md", "# Fixture\n\n> **Status:** Not Started\n> **Contract Locked:** ✅\n")
    write(spec / "spec-lite.md", "# Fixture Lite\n")
    write(spec / "sub-specs/technical-spec.md", """# Technical

## Error & Rescue Map

| Operation | Failure | Handling |
|---|---|---|
| Stage | Provider unavailable | Preserve resumable state |

## Shadow Paths

| Flow | Nil Input | Upstream Error |
|---|---|---|
| Preview | Block | Resume safely |

## Interaction Edge Cases

| Edge Case | Handling |
|---|---|
| Duplicate approval | Deduplicate event |
""")
    write(
        spec / "user-stories/story-1-fixture.md",
        """# Story 1: Fixture

> **Status:** Completed ✅
> **Dependencies:** None

## Acceptance Criteria
- [x] Given one, when run, then one.
- [x] Given two, when run, then two.
- [x] Given three, when run, then three.

## Implementation Tasks
- [x] 1.1 One
- [x] 1.2 Two
- [x] 1.3 Three
- [x] 1.4 Four
- [x] 1.5 Five

## Context for Agents

- **Error map rows:** Stage provider unavailable
- **Shadow paths:** Preview nil and upstream error

## What Was Built

Implemented the fixture staging flow and its error paths.
""",
    )
    write(
        spec / "user-stories/README.md",
        """# Stories

> **Progress:** 1/1

| Story | Title | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---:|---:|
| [1](story-1-fixture.md) | Fixture | Completed ✅ | High | None | 5 | 5/5 |
""",
    )
    write(
        spec / "recommendation-log.md",
        """# Recommendation Log: Fixture

> **Spec:** `.writ/specs/fixture/spec.md`
> **Purpose:** Eval
> **Privacy:** Decisions only

## REC-001 — 2026-07-10T15:00:00Z — planning

- **Decision:** Commit grouping strategy single.
- **Evidence:** Locked files.
- **Alternatives:** Stop.
- **Risk:** Low.
- **Reversibility:** High.
- **Selection:** Automatic.
- **Result:** Applied — strategy single; operation key __SHIP_KEY__; head __HEAD__; commits __HEAD__.
""",
    )
    command(["git", "add", "."], repo)
    command(["git", "commit", "-m", "fixture"], repo)
    SHA_A = command(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    SHIP_KEY = operation_key("ship", "stage", SHA_A)
    PR_KEY = operation_key("pr-create", "repo-1", "main", "feature/stage")
    log = spec / "recommendation-log.md"
    log.write_text(
        log.read_text().replace("__SHIP_KEY__", SHIP_KEY).replace("__HEAD__", SHA_A),
        encoding="utf-8",
    )
    state = repo / ".writ/state/recommend-execution-stage.json"
    result, payload = helper(
        "start", "--repo", repo, "--spec", ".writ/specs/fixture", "--state", state,
        "--execution-id", "stage", "--token", "token-stage",
        "--entry-command", "implement-spec",
        "--invocation-json", json.dumps(["--recommend", "fixture"]),
    )
    if result.returncode:
        raise RuntimeError(payload)
    value = json.loads(state.read_text())
    evidence = repo / ".writ/state/evidence/integration.txt"
    write(evidence, json.dumps({
        "schema": "recommend-test-evidence-v1", "status": "passed",
        "command": "fixture-test", "exitCode": 0, "headSha": SHA_A,
    }, sort_keys=True) + "\n")
    value["status"] = "verifying"
    value["resumeTarget"] = "verifying"
    value["repository"]["currentHeadSha"] = SHA_A
    value["repository"]["ownedPathWorktreeSnapshot"]["headSha"] = SHA_A
    value["storyExecution"]["planDigest"] = hashlib.sha256(b"plan").hexdigest()
    value["storyExecution"]["integrationVerification"] = {
        "status": "passed",
        "headSha": SHA_A,
        "packageManifestSha256": value["spec"]["packageManifestSha256"],
        "planDigest": value["storyExecution"]["planDigest"],
        "completedStoryIds": [],
        "command": "fixture-test",
        "exitCode": 0,
        "completedAt": "2026-07-10T15:01:00Z",
        "evidenceSummary": "passed",
        "evidenceArtifact": evidence.relative_to(repo).as_posix(),
        "evidenceArtifactSha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
    }
    state.write_text(json.dumps(value), encoding="utf-8")
    return repo, state


def event(state: Path, operation: str, evidence: dict) -> tuple[subprocess.CompletedProcess[str], dict]:
    evidence_path = state.with_name(f"{operation}-{hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()[:8]}.json")
    write(evidence_path, json.dumps(evidence))
    return helper(operation, "--state", state, "--evidence", evidence_path)


def sync_log(state: Path) -> None:
    value = json.loads(state.read_text())
    repo = Path(value["repository"]["rootIdentity"])
    log_path = repo / value["spec"]["recommendationLog"]["path"]
    data = log_path.read_bytes()
    text = data.decode()
    matches = list(re.finditer(r"(?m)^## (REC-\d+) — .+$", text))
    entries = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start():end].rstrip() + "\n"
        result = re.search(r"(?m)^- \*\*Result:\*\* (.+)$", body).group(1)
        entries.append((match.group(1), hashlib.sha256(body.encode()).hexdigest(), result))
    saved = value["spec"]["recommendationLog"]
    saved["revision"] = max(saved["revision"], len(entries))
    saved["digestSha256"] = hashlib.sha256(data).hexdigest()
    saved["entryIds"] = [item[0] for item in entries]
    saved["entryDigests"] = {item[0]: item[1] for item in entries}
    saved["pendingEntryIds"] = [item[0] for item in entries if item[2].startswith("Pending")]
    state.write_text(json.dumps(value), encoding="utf-8")


audit_counter = 1


def append_audit(state: Path, operation: str, *, pending: bool) -> str:
    global audit_counter
    audit_counter += 1
    entry_id = f"REC-{audit_counter:03d}"
    value = json.loads(state.read_text())
    repo = Path(value["repository"]["rootIdentity"])
    log_path = repo / value["spec"]["recommendationLog"]["path"]
    result = "Pending" if pending else "Applied"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"""
## {entry_id} — 2026-07-10T15:{audit_counter:02d}:00Z — staging

- **Decision:** Exercise staged operation.
- **Evidence:** Deterministic fixture evidence.
- **Alternatives:** Stop.
- **Risk:** Low.
- **Reversibility:** High.
- **Selection:** Automatic.
- **Result:** {result} — operation key {operation}.
""")
    sync_log(state)
    return entry_id


def append_unrelated_pending(state: Path) -> str:
    global audit_counter
    audit_counter += 1
    entry_id = f"REC-{audit_counter:03d}"
    value = json.loads(state.read_text())
    repo = Path(value["repository"]["rootIdentity"])
    log_path = repo / value["spec"]["recommendationLog"]["path"]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"""
## {entry_id} — 2026-07-10T15:{audit_counter:02d}:00Z — decision

- **Decision:** Consider a non-mutation choice.
- **Evidence:** Product context.
- **Alternatives:** Defer.
- **Risk:** Low.
- **Reversibility:** High.
- **Selection:** Pending human choice.
- **Result:** Pending — unrelated decision only.
""")
    sync_log(state)
    return entry_id


def finalize_audit(state: Path, entry_id: str, result: str) -> None:
    value = json.loads(state.read_text())
    repo = Path(value["repository"]["rootIdentity"])
    log_path = repo / value["spec"]["recommendationLog"]["path"]
    text = log_path.read_text()
    match = re.search(
        rf"(?ms)(^## {re.escape(entry_id)} — .+?^- \*\*Result:\*\* )(.+?)(?=\n(?:## REC-|\Z))",
        text,
    )
    if not match:
        raise RuntimeError(f"missing audit entry {entry_id}")
    replacement = match.group(1) + result.rstrip() + "\n"
    log_path.write_text(text[:match.start()] + replacement + text[match.end():], encoding="utf-8")
    sync_log(state)


def finalize_pr(state: Path, audit_id: str, outcome: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    record = pr_record()
    finalize_audit(
        state, audit_id,
        f"Applied — operation key {PR_KEY}; outcome {outcome}; "
        f"provider ID {record['providerId']}; number {record['number']}; URL {record['url']}.",
    )
    return event(state, "finalize-pr-audit", {
        "schema": "recommend-pr-audit-finalization-v1", "operationKey": PR_KEY,
        "auditEntryId": audit_id, "outcome": outcome,
    })


def adopt_pr(state: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    audit_id = append_audit(state, PR_KEY, pending=True)
    result, payload = event(state, "record-pr-lookup", {
        "schema": "recommend-pr-lookup-v1", "result": "one", "matches": [pr_record()],
        "operationKey": PR_KEY, "auditEntryId": audit_id,
    })
    if result.returncode:
        return result, payload
    return finalize_pr(state, audit_id, "adopted")


def activate(state: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    return event(state, "activate-staging", {
        "schema": "recommend-staging-activation-v1",
        "provider": "github",
        "repositoryId": "repo-1",
        "sourceRemote": "origin",
        "sourceIdentity": "https://github.com/example/repo",
        "baseBranch": "main",
        "featureBranch": "feature/stage",
        "headSha": SHA_A,
        "capabilities": {"pr": "available", "checks": "available", "preview": "available"},
        "config": {
            "requiredChecks": ["local-policy"],
            "previewProvider": "vercel",
            "previewProjectId": "project-7",
            "previewEvidenceSource": "deployment-status",
            "previewUrlPattern": "https://*.example.dev",
            "ciWaitTimeout": "30m",
            "previewWaitTimeout": "20m",
        },
    })


def ship(state: Path, **overrides: object) -> tuple[subprocess.CompletedProcess[str], dict]:
    sync_log(state)
    value = json.loads(state.read_text())
    repo = Path(value["repository"]["rootIdentity"])
    artifact = repo / ".writ/state/evidence/integration.txt"
    evidence = {
        "schema": "recommend-ship-evidence-v1",
        "testStatus": "passed",
        "testCommand": "fixture-test",
        "testEvidence": ".writ/state/evidence/integration.txt",
        "testEvidenceDigestSha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "testEvidenceHeadSha": SHA_A,
        "testExitCode": 0,
        "strategy": "single",
        "groupingBasis": "tightly-coupled",
        "commitShas": [SHA_A],
        "headSha": SHA_A,
        "decisionId": "REC-001",
        "auditEntryId": "REC-001",
    }
    evidence.update(overrides)
    return event(state, "record-ship", evidence)


def pr_record(head: str | None = None, state: str = "open") -> dict:
    head = SHA_A if head is None else head
    return {
        "providerId": "pr-7", "number": 7, "url": "https://github.com/example/repo/pull/7",
        "repositoryId": "repo-1", "baseBranch": "main", "headBranch": "feature/stage",
        "headSha": head, "state": state,
    }


def checks(statuses: list[tuple[str, str]], *, capability: str = "available",
           explicit_zero: bool = False, timed_out: bool = False, interrupted: bool = False) -> dict:
    provider_statuses = [(name, status) for name, status in statuses if name != "local-policy"]
    config_status = next((status for name, status in statuses if name == "local-policy"), "success")
    provider_set = [{"id": f"check-{name}", "name": name} for name, _ in provider_statuses]
    return {
        "schema": "recommend-required-checks-v1", "capability": capability,
        "authenticated": capability == "available",
        "queryOperation": {
            "id": "checks-query-2", "kind": "listRequiredChecks",
            "provider": "github", "repositoryId": "repo-1", "headSha": SHA_A,
            "startedAt": "2026-07-10T15:19:59Z",
            "completedAt": "2026-07-10T15:20:00Z",
        },
        "providerRequiredKnown": capability == "available", "explicitZeroRequired": explicit_zero,
        "provider": "github", "repositoryId": "repo-1",
        "queriedAt": "2026-07-10T15:20:00Z",
        "providerRequiredCheckIds": [item["id"] for item in provider_set],
        "providerRequiredCheckNames": [item["name"] for item in provider_set],
        "providerRequiredSetDigestSha256": hashlib.sha256(
            json.dumps(provider_set, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "requiredSetReconciled": True, "querySequence": 2,
        "headSha": SHA_A, "timedOut": timed_out, "interrupted": interrupted,
        "evidenceUrl": "https://github.com/example/repo/pull/7/checks",
        "checks": [
            {"id": f"check-{name}", "name": name, "status": status, "requiredBy": "provider"}
            for name, status in provider_statuses
        ] + [{"id": "config-local-policy", "name": "local-policy",
              "status": config_status, "requiredBy": "config"}],
    }


def preview(*, head: str | None = None, url: str = "https://stage-7.example.dev",
            status: str = "ready", capability: str = "available", timed_out: bool = False) -> dict:
    head = SHA_A if head is None else head
    return {
        "schema": "recommend-preview-evidence-v1", "capability": capability,
        "deploymentId": "deploy-7", "provider": "vercel", "url": url, "status": status,
        "headSha": head, "source": "deployment-status", "timedOut": timed_out,
        "repositoryId": "repo-1", "projectId": "project-7",
        "provenance": {
            "kind": "provider-deployment", "integrationId": "integration-7",
            "repositoryId": "repo-1", "projectId": "project-7",
            "headSha": head, "observedAt": "2026-07-10T15:25:00Z",
        },
        "evidenceUrl": "https://provider.example/deployments/deploy-7",
    }


def uat_derivation() -> dict:
    return {
        "schema": "recommend-uat-derivation-v1", "headSha": SHA_A,
        "recommendedVersion": "0.14.0",
        "releaseConsequences": "protected merge then versioned release",
        "validationInstructions": ["Open the preview URL.", "Run every scenario."],
        "warnings": ["Fixture warning."],
    }


def derive_uat(state: Path, repo: Path) -> dict:
    evidence = uat_derivation()
    evidence_path = state.with_name("derive-uat-evidence.json")
    write(evidence_path, json.dumps(evidence))
    output = repo / ".writ/specs/fixture/uat-plan.md"
    result, payload = helper(
        "derive-uat", "--state", state, "--evidence", evidence_path, "--output", output
    )
    if result.returncode:
        raise RuntimeError(payload)
    return payload


def make_ready(state: Path, repo: Path) -> None:
    activate(state)
    ship(state)
    adopt_pr(state)
    event(state, "record-checks", checks([("build", "success"), ("local-policy", "success")]))
    event(state, "record-preview", preview())
    derived = derive_uat(state, repo)
    event(state, "record-uat", {
        **uat_derivation(), **derived, "schema": "recommend-uat-evidence-v1",
    })


def approval_event(state: Path, decision: str, event_id: str, *, reconcile: bool = True) -> dict:
    value = json.loads(state.read_text())
    delivery = value["delivery"]
    capability = delivery["capabilitySnapshot"]
    key = operation_key(
        "approval", capability["repositoryId"], delivery["pr"]["providerId"], SHA_A,
        delivery["checksEvidence"]["providerRequiredSetDigestSha256"],
        delivery["preview"]["deploymentId"], delivery["uat"]["digestSha256"], event_id,
    )
    audit_id = append_audit(state, key, pending=False)
    current = json.loads(state.read_text())
    current_digest = hashlib.sha256(state.read_bytes()).hexdigest()
    latest_values = [
        delivery["pr"].get("observedAt"),
        delivery["checksEvidence"].get("lastObservedAt"),
        delivery["preview"].get("lastObservedAt"),
        delivery["uat"].get("generatedAt"),
    ]
    latest = max(
        [datetime.now(timezone.utc)] + [
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            for value in latest_values if value
        ]
    )
    presented = latest
    observed = latest + timedelta(seconds=1)
    occurred = latest + timedelta(seconds=2)
    timestamp = lambda value: value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    attempt_id = f"reconcile-{event_id}"
    payload = {
        "schema": "recommend-approval-event-v1", "decision": decision, "headSha": SHA_A,
        "actor": "reviewer", "eventId": event_id, "interactionId": event_id,
        "occurredAt": timestamp(occurred), "auditEntryId": audit_id,
    }
    if reconcile and decision == "approve":
        checks_by_id = {item["id"]: item["status"] for item in delivery["checks"]}
        preview_evidence = {
            "status": "ready", "provider": delivery["preview"]["provider"],
            "source": delivery["preview"]["source"],
            "repositoryId": capability["repositoryId"],
            "projectId": capability["config"]["previewProjectId"],
            "deploymentId": delivery["preview"]["deploymentId"], "headSha": SHA_A,
            "provenance": delivery["preview"]["provenance"],
            "attemptId": attempt_id, "observedAt": timestamp(observed),
        }
        payload["reconciliation"] = {
            "operationKey": key, "attemptId": attempt_id,
            "presentationStartedAt": timestamp(presented),
            "queriedAt": timestamp(observed),
            "stateRevision": current["revision"], "stateDigestSha256": current_digest,
            "capabilitySnapshotDigestSha256": capability["digestSha256"],
            "uatDigestSha256": delivery["uat"]["digestSha256"],
            "uatObservedAt": timestamp(observed),
            "pullRequest": {
                **delivery["pr"], "attemptId": attempt_id,
                "observedAt": timestamp(observed),
            },
            "checks": {
                "provider": capability["provider"],
                "repositoryId": capability["repositoryId"], "headSha": SHA_A,
                "requiredCheckIds": delivery["checksEvidence"]["requiredCheckIds"],
                "providerRequiredSetDigestSha256":
                    delivery["checksEvidence"]["providerRequiredSetDigestSha256"],
                "attemptId": attempt_id, "observedAt": timestamp(observed),
            },
            "checkStatuses": checks_by_id,
            "preview": preview_evidence,
        }
    return payload


class FakeProvider:
    """Deterministic, local provider with mutation counters."""

    def __init__(self, matches: list[dict] | None = None, lose_create_response: bool = False) -> None:
        self.matches = list(matches or [])
        self.lose_create_response = lose_create_response
        self.create_calls = 0

    def find_pull_request(self) -> dict:
        result = "absent" if not self.matches else ("one" if len(self.matches) == 1 else "multiple")
        return {"schema": "recommend-pr-lookup-v1", "result": result, "matches": self.matches,
                "operationKey": PR_KEY}

    def create_pull_request(self) -> dict | None:
        self.create_calls += 1
        created = pr_record()
        self.matches.append(created)
        return None if self.lose_create_response else created


def run() -> None:
    root = Path(tempfile.mkdtemp(prefix="writ-story4-eval-"))
    try:
        repo, base = fixture(root)

        def fresh(name: str) -> Path:
            base_value = json.loads(base.read_text())
            log_path = Path(base_value["repository"]["rootIdentity"]) / base_value["spec"]["recommendationLog"]["path"]
            log_path.write_text(
                log_path.read_text().replace("- **Result:** Pending", "- **Result:** Cancelled"),
                encoding="utf-8",
            )
            path = base.with_name(f"recommend-execution-{name}.json")
            shutil.copy2(base, path)
            sync_log(path)
            return path

        state = fresh("happy")
        result, _ = activate(state)
        emit("activate-existing-v1-staging", result.returncode == 0, result.stdout)
        result, _ = ship(state)
        emit("ship-requires-passing-tests-and-persists-grouping", result.returncode == 0, result.stdout)
        result, _ = adopt_pr(state)
        emit("existing-open-pr-adopted", result.returncode == 0, result.stdout)
        result, _ = event(state, "record-checks", checks([("build", "success"), ("local-policy", "success")]))
        emit("provider-plus-config-required-checks-pass", result.returncode == 0, result.stdout)
        result, _ = event(state, "record-preview", preview())
        emit("same-sha-safe-preview-ready", result.returncode == 0, result.stdout)

        state = fresh("absent")
        activate(state); ship(state)
        provider = FakeProvider()
        pr_audit = append_audit(state, PR_KEY, pending=True)
        lookup = {**provider.find_pull_request(), "auditEntryId": pr_audit}
        result, payload = event(state, "record-pr-lookup", lookup)
        emit("absent-pr-requests-at-most-one-create", result.returncode == 0 and payload.get("action") == "createPullRequest", payload)
        event(state, "mark-pr-create-attempt", {
            "schema": "recommend-pr-create-attempt-v1", "operationKey": PR_KEY,
            "auditEntryId": pr_audit,
        })
        created = provider.create_pull_request()
        result, _ = event(state, "record-pr-created", {
            "schema": "recommend-pr-created-v1", "operationKey": PR_KEY,
            "auditEntryId": pr_audit, "pullRequest": created,
        })
        if result.returncode == 0:
            result, _ = finalize_pr(state, pr_audit, "created")
        emit("created-pr-canonical-id-persisted", result.returncode == 0 and provider.create_calls == 1, result.stdout)

        state = fresh("lost")
        activate(state); ship(state)
        provider = FakeProvider(lose_create_response=True)
        pr_audit = append_audit(state, PR_KEY, pending=True)
        event(state, "record-pr-lookup", {**provider.find_pull_request(), "auditEntryId": pr_audit})
        event(state, "mark-pr-create-attempt", {
            "schema": "recommend-pr-create-attempt-v1", "operationKey": PR_KEY,
            "auditEntryId": pr_audit,
        })
        provider.create_pull_request()
        result, _ = event(state, "record-pr-lookup", provider.find_pull_request())
        if result.returncode == 0:
            result, _ = finalize_pr(state, pr_audit, "reconciled")
        emit("lost-create-response-relookup-prevents-duplicate", result.returncode == 0 and provider.create_calls == 1, result.stdout)

        for name, matches, code in (
            ("ambiguous", [pr_record(), {**pr_record(), "providerId": "pr-8", "number": 8}], "pr_ambiguous"),
            ("mismatch", [{**pr_record(), "headBranch": "other"}], "pr_mismatch"),
            ("closed", [pr_record(state="closed")], "pr_closed"),
        ):
            state = fresh(name); activate(state); ship(state)
            result, payload = event(state, "record-pr-lookup", FakeProvider(matches).find_pull_request())
            emit(f"pr-{name}-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == code, payload)

        for name, evidence, expected_ok, code in (
            ("explicit-zero", checks([], explicit_zero=True), True, None),
            ("unavailable", checks([], capability="unavailable"), False, "checks_unavailable"),
            ("pending", checks([("build", "pending")]), True, None),
            ("late-added", checks([("build", "success"), ("late", "pending")]), True, None),
            ("failed", checks([("build", "failed")]), False, "checks_failed"),
            ("cancelled", checks([("build", "cancelled")]), False, "checks_cancelled"),
            ("unknown", checks([("build", "mystery")]), False, "checks_unknown"),
            ("timeout", checks([("build", "pending")], timed_out=True), True, None),
            ("interruption", checks([("build", "pending")], interrupted=True), True, None),
            ("success", checks([("build", "success")]), True, None),
        ):
            state = fresh("checks-" + name); activate(state); ship(state)
            adopt_pr(state)
            result, payload = event(state, "record-checks", evidence)
            ok = result.returncode == 0 if expected_ok else (
                result.returncode != 0 and payload.get("blocker", {}).get("code") == code
            )
            emit("checks-" + name, ok, payload)

        for name, evidence, expected_ok, code in (
            ("same-sha", preview(), True, None),
            ("stale", preview(head=SHA_B), False, "preview_stale"),
            ("unsafe", preview(url="https://stage.example.dev/?token=secret"), False, "preview_unsafe_url"),
            ("missing", preview(status="missing", capability="unavailable"), False, "preview_unavailable"),
            ("timeout", preview(status="pending", timed_out=True), True, None),
            ("error", preview(status="error"), False, "preview_error"),
        ):
            state = fresh("preview-" + name)
            activate(state); ship(state)
            adopt_pr(state)
            event(state, "record-checks", checks([("build", "success")]))
            result, payload = event(state, "record-preview", evidence)
            ok = result.returncode == 0 if expected_ok else (
                result.returncode != 0 and payload.get("blocker", {}).get("code") == code
            )
            emit("preview-" + name, ok, payload)

        state = fresh("uat")
        make_ready(state, repo)
        first = json.loads(state.read_text())["delivery"]["uat"]["digestSha256"]
        state2 = fresh("uat-repeat")
        make_ready(state2, repo)
        second = json.loads(state2.read_text())["delivery"]["uat"]["digestSha256"]
        emit("uat-digest-deterministic", first == second, (first, second))

        state = fresh("approval")
        make_ready(state, repo)
        before = json.loads(state.read_text())["revision"]
        result, _ = event(state, "record-approval", {
            "schema": "recommend-approval-event-v1", "decision": "silence", "headSha": SHA_A,
            "actor": None, "eventId": None, "occurredAt": None,
        })
        after = json.loads(state.read_text())["revision"]
        emit("approval-silence-is-not-approval", result.returncode == 0 and before == after, result.stdout)
        approve_payload = approval_event(state, "approve", "approve-1")
        result, _ = event(state, "record-approval", approve_payload)
        approved = json.loads(state.read_text())
        emit("explicit-approval-binds-sha", result.returncode == 0 and approved["status"] == "production_approved", result.stdout)
        revision = approved["revision"]
        result, _ = event(state, "record-approval", approve_payload)
        emit("duplicate-approval-dedupes", result.returncode == 0 and json.loads(state.read_text())["revision"] == revision, result.stdout)
        result, _ = event(state, "revalidate-staging", {
            "schema": "recommend-staging-revalidation-v1", "repositoryId": "repo-1",
            "pullRequest": pr_record(head=SHA_B),
        })
        invalidated = json.loads(state.read_text())
        emit("head-change-invalidates-all-sha-evidence",
             result.returncode == 0 and invalidated["status"] == "waiting_ci"
             and invalidated["delivery"]["approval"]["status"] == "invalidated"
             and invalidated["delivery"]["checks"] == [] and invalidated["delivery"]["preview"] is None,
             result.stdout)

        state = fresh("reject")
        make_ready(state, repo)
        result, _ = event(state, "record-approval", approval_event(
            state, "reject", "reject-1", reconcile=False
        ))
        rejected = json.loads(state.read_text())
        emit("approval-rejection-returns-implementation",
             result.returncode == 0 and rejected["status"] == "implementing"
             and rejected["mode"]["name"] == "recommend", result.stdout)

        # Gate 3 adversarial regressions: each prior false positive must block.
        state = fresh("adversarial-pr-key"); activate(state); ship(state)
        result, payload = event(state, "record-pr-lookup", {
            "schema": "recommend-pr-lookup-v1", "result": "absent", "matches": [],
            "operationKey": "attacker-selected-key",
        })
        emit("adversarial-pr-arbitrary-operation-key-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "pr_operation_key_mismatch",
             payload)

        state = fresh("adversarial-pr-no-audit"); activate(state); ship(state)
        result, payload = event(state, "record-pr-lookup", FakeProvider().find_pull_request())
        emit("adversarial-pr-absent-audit-entry-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") in {
                 "invalid_state", "audit_entry_missing"
             }, payload)

        state = fresh("adversarial-pr-repeat"); activate(state); ship(state)
        absent = FakeProvider().find_pull_request()
        repeated_audit = append_audit(state, PR_KEY, pending=True)
        absent = {**absent, "auditEntryId": repeated_audit}
        event(state, "record-pr-lookup", absent)
        result, payload = event(state, "record-pr-lookup", absent)
        emit("adversarial-pr-repeated-absence-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "pr_create_already_authorized",
             payload)

        state = fresh("adversarial-check-config-only"); activate(state); ship(state)
        adopt_pr(state)
        config_only = checks([("local-policy", "success")])
        config_only["checks"][0]["requiredBy"] = "config"
        result, payload = event(state, "record-checks", config_only)
        emit("adversarial-config-check-cannot-substitute-provider-discovery",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "checks_provider_evidence_missing",
             payload)

        state = fresh("adversarial-check-auth"); activate(state); ship(state)
        adopt_pr(state)
        auth = checks([], capability="needs_auth")
        result, payload = event(state, "record-checks", auth)
        emit("adversarial-check-auth-remains-classified",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "checks_needs_auth",
             payload)

        state = fresh("adversarial-check-authorization"); activate(state); ship(state)
        adopt_pr(state)
        denied = checks([], capability="authorization_denied")
        result, payload = event(state, "record-checks", denied)
        emit("adversarial-check-authorization-remains-classified",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "checks_authorization_denied",
             payload)

        state = fresh("adversarial-preview-provider")
        activate(state); ship(state)
        adopt_pr(state)
        event(state, "record-checks", checks([("build", "success")]))
        fabricated = preview()
        fabricated["provider"] = "fabricated-host"
        result, payload = event(state, "record-preview", fabricated)
        emit("adversarial-preview-unconfigured-provider-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "preview_provenance_mismatch",
             payload)

        state = fresh("adversarial-preview-pattern-only")
        activate(state); ship(state)
        adopt_pr(state)
        event(state, "record-checks", checks([("build", "success")]))
        pattern_only = preview()
        pattern_only["source"] = "url-pattern"
        result, payload = event(state, "record-preview", pattern_only)
        emit("adversarial-preview-pattern-only-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "preview_provenance_mismatch",
             payload)

        state = fresh("adversarial-uat")
        activate(state); ship(state)
        adopt_pr(state)
        event(state, "record-checks", checks([("build", "success")]))
        event(state, "record-preview", preview())
        arbitrary = repo / ".writ/specs/fixture/uat-plan.md"
        write(arbitrary, "# UAT\n\nInvented content.\n")
        result, payload = event(state, "record-uat", {
            "schema": "recommend-uat-evidence-v1", "path": ".writ/specs/fixture/uat-plan.md",
            "digestSha256": hashlib.sha256(arbitrary.read_bytes()).hexdigest(), "headSha": SHA_A,
            "sourceDigestSha256": hashlib.sha256(b"invented").hexdigest(),
            "recommendedVersion": "0.14.0", "releaseConsequences": "invented",
            "warnings": [],
        })
        emit("adversarial-uat-arbitrary-file-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "uat_derivation_mismatch",
             payload)

        state = fresh("adversarial-approval")
        make_ready(state, repo)
        result, payload = event(state, "record-approval", {
            "schema": "recommend-approval-event-v1", "decision": "approve", "headSha": SHA_A,
            "actor": "reviewer", "eventId": "approve-stale", "interactionId": "approve-stale",
            "occurredAt": "2026-07-10T16:00:00Z",
        })
        emit("adversarial-approval-cached-fields-alone-block",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "approval_reconciliation_missing",
             payload)

        state = fresh("adversarial-approval-stale-reconciliation")
        make_ready(state, repo)
        stale_approval = approval_event(state, "approve", "approve-stale-reconciliation")
        stale_approval["reconciliation"]["checkStatuses"].pop(
            next(iter(stale_approval["reconciliation"]["checkStatuses"]))
        )
        result, payload = event(state, "record-approval", stale_approval)
        emit("adversarial-approval-stale-reconciliation-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "approval_reconciliation_stale",
             payload)

        state = fresh("adversarial-ship"); activate(state)
        result, payload = event(state, "record-ship", {
            "schema": "recommend-ship-evidence-v1", "testStatus": "passed",
            "testCommand": None, "testEvidence": "missing.txt", "strategy": "bogus",
            "commitShas": [SHA_A], "headSha": SHA_A, "decisionId": "",
        })
        emit("adversarial-ship-marker-only-evidence-blocks",
             result.returncode != 0 and payload.get("blocker", {}).get("code") == "ship_evidence_invalid",
             payload)

        state = fresh("adversarial-uat-source-change")
        activate(state); ship(state)
        adopt_pr(state)
        event(state, "record-checks", checks([("build", "success")]))
        event(state, "record-preview", preview())
        first_derived = derive_uat(state, repo)
        story = repo / ".writ/specs/fixture/user-stories/story-1-fixture.md"
        story.write_text(
            story.read_text().replace("then one.", "then changed one."),
            encoding="utf-8",
        )
        second_derived = derive_uat(state, repo)
        result, payload = event(state, "record-uat", {
            **uat_derivation(), **first_derived, "schema": "recommend-uat-evidence-v1",
        })
        emit("adversarial-uat-source-change-invalidates-old-output",
             first_derived["sourceDigestSha256"] != second_derived["sourceDigestSha256"]
             and first_derived["digestSha256"] != second_derived["digestSha256"]
             and result.returncode != 0
             and payload.get("blocker", {}).get("code") == "uat_derivation_mismatch",
             payload)

        # Second Gate 3 residual probes.
        state = fresh("residual-pending-pr-audit"); activate(state); ship(state)
        pending_adopt = append_audit(state, PR_KEY, pending=True)
        result, payload = event(state, "record-pr-lookup", {
            "schema": "recommend-pr-lookup-v1", "result": "one",
            "matches": [pr_record()], "operationKey": PR_KEY,
            "auditEntryId": pending_adopt,
        })
        emit("residual-pr-audit-must-finalize-before-checks",
             result.returncode == 0 and payload.get("status") == "pr_open",
             payload)
        result, payload = event(state, "record-checks", checks([("build", "success")]))
        emit("residual-pending-pr-audit-cannot-enter-checks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "invalid_transition",
             payload)

        state = fresh("residual-unrelated-pending"); activate(state); ship(state)
        unrelated_id = append_unrelated_pending(state)
        result, payload = event(state, "record-pr-lookup", {
            "schema": "recommend-pr-lookup-v1", "result": "absent", "matches": [],
            "operationKey": PR_KEY, "auditEntryId": unrelated_id,
        })
        emit("residual-unrelated-pending-cannot-authorize-mutation",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "audit_operation_mismatch",
             payload)

        state = fresh("residual-ship-commit-binding"); activate(state)
        result, payload = ship(state, commitShas=["f" * 40])
        emit("residual-ship-nonexistent-commit-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "ship_commit_binding_invalid",
             payload)
        state = fresh("residual-ship-audit-id"); activate(state)
        result, payload = ship(state, decisionId="REC-999")
        emit("residual-ship-unbound-decision-id-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "ship_commit_binding_invalid",
             payload)

        state = fresh("residual-approval-temporal"); make_ready(state, repo)
        stale_time = approval_event(state, "approve", "approve-year-2000")
        stale_time["reconciliation"]["queriedAt"] = "2000-01-01T00:00:00Z"
        result, payload = event(state, "record-approval", stale_time)
        emit("residual-approval-year-2000-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "approval_reconciliation_temporal",
             payload)

        state = fresh("residual-approval-attempt"); make_ready(state, repo)
        mixed_attempt = approval_event(state, "approve", "approve-mixed-attempt")
        mixed_attempt["reconciliation"]["preview"]["attemptId"] = "other-attempt"
        result, payload = event(state, "record-approval", mixed_attempt)
        emit("residual-approval-one-attempt-id-required",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "approval_reconciliation_stale",
             payload)

        state = fresh("residual-approval-future"); make_ready(state, repo)
        future = approval_event(state, "approve", "approve-future")
        future_at = "2999-01-01T00:00:00Z"
        future["occurredAt"] = future_at
        future["reconciliation"]["presentationStartedAt"] = future_at
        future["reconciliation"]["queriedAt"] = future_at
        future["reconciliation"]["uatObservedAt"] = future_at
        future["reconciliation"]["pullRequest"]["observedAt"] = future_at
        future["reconciliation"]["checks"]["observedAt"] = future_at
        future["reconciliation"]["preview"]["observedAt"] = future_at
        result, payload = event(state, "record-approval", future)
        emit("residual-approval-future-clock-skew-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "approval_reconciliation_temporal",
             payload)

        state = fresh("residual-check-authenticated"); activate(state); ship(state)
        adopt_pr(state)
        unauthenticated = checks([("build", "success")])
        unauthenticated["authenticated"] = False
        result, payload = event(state, "record-checks", unauthenticated)
        emit("residual-checks-require-authenticated-query",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "checks_unauthenticated",
             payload)

        state = fresh("residual-check-auth-missing"); activate(state); ship(state)
        adopt_pr(state)
        missing_auth = checks([("build", "success")])
        missing_auth.pop("authenticated")
        result, payload = event(state, "record-checks", missing_auth)
        emit("residual-checks-missing-authentication-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "checks_unauthenticated",
             payload)

        state = fresh("residual-check-query-missing"); activate(state); ship(state)
        adopt_pr(state)
        missing_query = checks([("build", "success")])
        missing_query.pop("queryOperation")
        result, payload = event(state, "record-checks", missing_query)
        emit("residual-checks-missing-query-operation-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "checks_unauthenticated",
             payload)

        state = fresh("residual-preview-kind"); activate(state); ship(state)
        adopt_pr(state)
        event(state, "record-checks", checks([("build", "success")]))
        contradictory_preview = preview()
        contradictory_preview["provenance"]["kind"] = "project-convention"
        result, payload = event(state, "record-preview", contradictory_preview)
        emit("residual-preview-source-kind-contradiction-blocks",
             result.returncode != 0
             and payload.get("blocker", {}).get("code") == "preview_provenance_mismatch",
             payload)

        config_text = (HELPER.parent.parent / ".writ/docs/config-format.md").read_text()
        emit("residual-config-documents-preview-project",
             "`Preview Project`" in config_text and "`previewProjectId`" in config_text,
             "Preview Project mapping absent")

        helper_text = HELPER.read_text()
        emit("helper-remains-provider-local",
             "import requests" not in helper_text and "urllib.request" not in helper_text
             and "deploy_to_vercel" not in helper_text
             and "browser_" not in helper_text and "mergePullRequest" not in helper_text,
             "forbidden provider/network operation found")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    run()
    print(f"SUMMARY\tpassed={passed}\tfailed={failed}")
    raise SystemExit(1 if failed else 0)
