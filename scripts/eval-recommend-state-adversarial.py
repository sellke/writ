#!/usr/bin/env python3
"""Fresh adversarial Story 3 scenarios for the executable state reducer."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable


HELPER = pathlib.Path(sys.argv[1]).resolve()
WORKSPACE = pathlib.Path(tempfile.mkdtemp(prefix="writ-story3-adversarial-"))
EMPTY_ANSWER = {
    "decision_id": None,
    "question_id": None,
    "option_ids": [],
    "selected_option_id": None,
    "resume_transition": None,
    "interaction_id": None,
}


def emit(name: str, ok: bool, reason: Any = "") -> None:
    safe = "" if ok else str(reason).replace("\t", " ").replace("\r", " ").replace("\n", "\\n")
    print(("PASS" if ok else "FAIL") + "\t" + name + "\t" + safe)


def command(args: list[str], cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def run_helper(*args: Any) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    result = command([sys.executable, str(HELPER), *map(str, args)])
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"invalid_output": result.stdout, "stderr": result.stderr}
    return result, payload


def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def fixture(name: str, *, baseline_story_1: bool = False, totals: bool = True) -> tuple[pathlib.Path, pathlib.Path]:
    repo = WORKSPACE / name / "repo"
    repo.mkdir(parents=True)
    for args in (
        ["git", "init", "-b", "main"],
        ["git", "config", "user.name", "Writ Eval"],
        ["git", "config", "user.email", "eval@example.invalid"],
    ):
        result = command(args, repo)
        if result.returncode:
            raise RuntimeError(result.stderr)
    spec = pathlib.Path(".writ/specs/2026-07-10-fixture")
    root = repo / spec
    write(repo / ".gitignore", ".writ/state/\n")
    write(root / "spec.md", "# Fixture\n\n> **Status:** Not Started\n> **Contract Locked:** ✅\n")
    write(root / "spec-lite.md", "# Fixture Lite\n\nLocked.\n")
    write(root / "sub-specs/technical-spec.md", "# Technical\n\nLocked.\n")
    story = """# Story {number}: Fixture

> **Status:** {status}
> **Dependencies:** {dependencies}

## Acceptance Criteria
- [{mark}] Given one, when handled, then one.
- [{mark}] Given two, when handled, then two.
- [{mark}] Given three, when handled, then three.

## Implementation Tasks
- [{mark}] {number}.1 First task
- [{mark}] {number}.2 Second task
- [{mark}] {number}.3 Third task
- [{mark}] {number}.4 Fourth task
- [{mark}] {number}.5 Fifth task
"""
    first_status = "Completed ✅" if baseline_story_1 else "Not Started"
    first_mark = "x" if baseline_story_1 else " "
    write(
        root / "user-stories/story-1-one.md",
        story.format(number=1, status=first_status, dependencies="None", mark=first_mark),
    )
    write(
        root / "user-stories/story-2-two.md",
        story.format(number=2, status="Not Started", dependencies="Story 1", mark=" "),
    )
    completed_stories = 1 if baseline_story_1 else 0
    completed_tasks = 5 if baseline_story_1 else 0
    totals_text = ""
    if totals:
        totals_text = f"""
## Totals

- **Stories:** 2
- **Acceptance criteria:** 6
- **Implementation tasks:** 10
- **Completed tasks:** {completed_tasks}
- **Overall progress:** {completed_tasks * 10}%
"""
    write(
        root / "user-stories/README.md",
        f"""# Stories

> **Progress:** {completed_stories}/2

| Story | Title | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---:|---:|
| [1](story-1-one.md) | One | {first_status} | High | None | 5 | {completed_tasks}/5 |
| [2](story-2-two.md) | Two | Not Started | High | Story 1 | 5 | 0/5 |
{totals_text}""",
    )
    write(
        root / "recommendation-log.md",
        """# Recommendation Log

## REC-001 — 2026-07-10T15:00:00Z — planning

- **Decision:** Use fixture.
- **Evidence:** Locked files.
- **Alternatives:** Stop.
- **Risk:** Low.
- **Reversibility:** High.
- **Selection:** Automatic.
- **Result:** Applied — fixture.
""",
    )
    for args in (["git", "add", "."], ["git", "commit", "-m", "fixture"]):
        result = command(args, repo)
        if result.returncode:
            raise RuntimeError(result.stderr)
    return repo, spec


def start(repo: pathlib.Path, spec: pathlib.Path, name: str) -> pathlib.Path:
    state = repo / f".writ/state/recommend-execution-{name}.json"
    result, payload = run_helper(
        "start",
        "--repo",
        repo,
        "--spec",
        spec,
        "--state",
        state,
        "--execution-id",
        name,
        "--token",
        f"token-{name}",
        "--entry-command",
        "implement-spec",
        "--invocation-json",
        json.dumps(["--recommend", spec.name]),
    )
    if result.returncode:
        raise RuntimeError(payload)
    return state


def complete_story(repo: pathlib.Path, spec: pathlib.Path, number: int) -> None:
    path = next((repo / spec / "user-stories").glob(f"story-{number}-*.md"))
    text = path.read_text(encoding="utf-8")
    text = text.replace("> **Status:** Not Started", "> **Status:** Completed ✅").replace("- [ ]", "- [x]")
    write(path, text + "\n## What Was Built\n\nVerified fixture output.\n")
    readme = repo / spec / "user-stories/README.md"
    text = readme.read_text(encoding="utf-8")
    old = f"| [{number}](story-{number}-{'one' if number == 1 else 'two'}.md) | {'One' if number == 1 else 'Two'} | Not Started"
    new = f"| [{number}](story-{number}-{'one' if number == 1 else 'two'}.md) | {'One' if number == 1 else 'Two'} | Completed ✅"
    text = text.replace(old, new).replace(
        f"| 5 | 0/5 |", f"| 5 | 5/5 |", 1 if number == 1 else 0
    )
    # The second replacement needs the second matching row.
    if number == 2:
        rows = text.splitlines()
        for index, line in enumerate(rows):
            if line.startswith("| [2]("):
                rows[index] = line.replace("| 5 | 0/5 |", "| 5 | 5/5 |")
        text = "\n".join(rows) + "\n"
    completed = sum(" | Completed ✅ | " in line for line in text.splitlines() if line.startswith("| ["))
    text = __import__("re").sub(r"> \*\*Progress:\*\* \d+/2", f"> **Progress:** {completed}/2", text)
    text = __import__("re").sub(r"- \*\*Completed tasks:\*\* \d+", f"- **Completed tasks:** {completed * 5}", text)
    text = __import__("re").sub(r"- \*\*Overall progress:\*\* \d+%", f"- **Overall progress:** {completed * 50}%", text)
    write(readme, text)


def result_for(execution_id: str, story_id: str, status: str = "succeeded") -> dict[str, Any]:
    blocked = status == "blocked"
    return {
        "schema": "recommend-command-result-v1",
        "execution_id": execution_id,
        "mode": "recommend",
        "command": "implement-story",
        "status": status,
        "completed_state": None,
        "resume_state": "implementing" if blocked else None,
        "evidence": {"summary": "Story gates passed." if not blocked else "Story gates blocked.", "artifacts": []},
        "identifiers": {"story_id": story_id},
        "required_answer": copy.deepcopy(EMPTY_ANSWER),
        "blocker": {"code": "story_failed" if blocked else None, "summary": "Story failed." if blocked else None},
    }


def add_execution(
    repo: pathlib.Path,
    state_path: pathlib.Path,
    *,
    plan: dict[str, Any],
    statuses: dict[str, str],
    completed: list[str],
    active: list[str] | None = None,
    failed: list[str] | None = None,
    results: dict[str, dict[str, Any]] | None = None,
) -> pathlib.Path:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    nested = repo / ".writ/state/execution-adversarial.json"
    write(nested, json.dumps({"spec": state["spec"]["id"], "plan": plan, "stories": {
        story_id: {"status": status, "phase": "complete" if status == "completed" else None}
        for story_id, status in statuses.items()
    }}))
    state["storyExecution"].update({
        "executionStatePath": nested.relative_to(repo).as_posix(),
        "planDigest": canonical_digest(plan),
        "completedStoryIds": completed,
        "activeStoryIds": active or [],
        "failedStoryIds": failed or [],
        "storyResults": results or {},
    })
    write(state_path, json.dumps(state))
    return nested


def add_passed_integration(repo: pathlib.Path, state_path: pathlib.Path) -> pathlib.Path:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    artifact = repo / ".writ/state/evidence/integration.txt"
    write(artifact, "integration passed\n")
    head = command(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    state["storyExecution"]["integrationVerification"] = {
        "status": "passed",
        "headSha": head,
        "packageManifestSha256": state["spec"]["packageManifestSha256"],
        "planDigest": state["storyExecution"]["planDigest"],
        "completedStoryIds": state["storyExecution"]["completedStoryIds"],
        "command": "python -m fixture_tests",
        "exitCode": 0,
        "completedAt": "2026-07-10T16:00:00Z",
        "evidenceSummary": "Full fixture suite passed.",
        "evidenceArtifact": artifact.relative_to(repo).as_posix(),
        "evidenceArtifactSha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }
    write(state_path, json.dumps(state))
    return artifact


def reserve_serial(repo: pathlib.Path, state_path: pathlib.Path, story_id: str) -> str:
    state = json.loads(state_path.read_text())
    head = command(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    branch = command(["git", "symbolic-ref", "HEAD"], repo).stdout.strip()
    launch = repo / f".writ/state/launch-{story_id}.json"
    write(launch, json.dumps({
        "schema": "recommend-worktree-launch-v1",
        "execution_id": state["executionId"],
        "story_id": story_id,
        "delegated_execution_id": f"delegate-{story_id}",
        "ownership_token": f"owner-{story_id}",
        "path": str(repo),
        "branch_ref": branch,
        "head_sha": head,
        "starting_sha": head,
        "active_gate": "launch",
        "mode": "serial_in_place",
    }))
    result, payload = run_helper(
        "reserve-worktree", "--state", state_path, "--repo", repo, "--launch-result", launch,
    )
    if result.returncode:
        raise RuntimeError(payload)
    return payload["worktree_key"]


def set_story_execution(
    repo: pathlib.Path,
    state_path: pathlib.Path,
    story_id: str,
    status: str,
    completed: list[str],
    results: dict[str, dict[str, Any]],
) -> None:
    state = json.loads(state_path.read_text())
    nested = repo / state["storyExecution"]["executionStatePath"]
    nested_value = json.loads(nested.read_text())
    nested_value["stories"][story_id] = {
        "status": status,
        "phase": "complete" if status == "completed" else "coding",
    }
    write(nested, json.dumps(nested_value))
    state["storyExecution"]["completedStoryIds"] = completed
    state["storyExecution"]["activeStoryIds"] = [story_id] if status == "in_progress" else []
    state["storyExecution"]["storyResults"] = results
    write(state_path, json.dumps(state))


def reconcile(repo: pathlib.Path, state: pathlib.Path) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], int]:
    before = json.loads(state.read_text(encoding="utf-8"))["revision"]
    result, payload = run_helper("reconcile", "--state", state, "--repo", repo)
    after = json.loads(state.read_text(encoding="utf-8"))["revision"]
    return result, payload, after - before


def complete_claim(name: str) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    repo, spec = fixture(name)
    state = start(repo, spec, name)
    plan = {
        "batches": [
            {"parallel": False, "stories": ["story-1"]},
            {"parallel": False, "stories": ["story-2"]},
        ]
    }
    execution_id = json.loads(state.read_text())["executionId"]
    add_execution(
        repo,
        state,
        plan=plan,
        statuses={"story-1": "pending", "story-2": "pending"},
        completed=[],
        results={},
    )
    results: dict[str, dict[str, Any]] = {}
    for number in (1, 2):
        story_id = f"story-{number}"
        set_story_execution(repo, state, story_id, "in_progress", [f"story-{item}" for item in range(1, number)], results)
        worktree_key = reserve_serial(repo, state, story_id)
        complete_story(repo, spec, number)
        command(["git", "add", str(repo / spec / "user-stories")], repo)
        committed = command(["git", "commit", "-m", f"complete {story_id}"], repo)
        if committed.returncode:
            raise RuntimeError(committed.stderr)
        results[story_id] = result_for(execution_id, story_id)
        completed = [f"story-{item}" for item in range(1, number + 1)]
        set_story_execution(repo, state, story_id, "completed", completed, results)
        completed_result, completed_payload = run_helper(
            "complete-worktree", "--state", state, "--repo", repo, "--worktree-key", worktree_key,
        )
        if completed_result.returncode:
            raise RuntimeError(completed_payload)
    artifact = add_passed_integration(repo, state)
    return repo, state, artifact


def expect_block(
    name: str,
    mutate: Callable[[pathlib.Path, pathlib.Path, pathlib.Path], None],
    expected_code: str,
) -> None:
    repo, state, artifact = complete_claim(name)
    mutate(repo, state, artifact)
    result, payload, revision_delta = reconcile(repo, state)
    emit(
        name,
        result.returncode == 2
        and payload.get("status") == "blocked"
        and payload.get("blocker", {}).get("code") == expected_code
        and revision_delta == 0,
        payload,
    )


try:
    repo, spec = fixture("fabricated-completion")
    state = start(repo, spec, "fabricated-completion")
    value = json.loads(state.read_text())
    value["storyExecution"]["completedStoryIds"] = ["story-1"]
    write(state, json.dumps(value))
    result, payload, delta = reconcile(repo, state)
    emit(
        "fabricated-completed-ids-block",
        result.returncode == 2 and payload.get("blocker", {}).get("code") == "execution_state_contradiction" and delta == 0,
        payload,
    )

    repo, spec = fixture("artifact-pending")
    state = start(repo, spec, "artifact-pending")
    complete_story(repo, spec, 1)
    plan = {"batches": [{"parallel": False, "stories": ["story-1"]}, {"parallel": False, "stories": ["story-2"]}]}
    execution_id = json.loads(state.read_text())["executionId"]
    add_execution(
        repo, state, plan=plan, statuses={"story-1": "pending", "story-2": "pending"},
        completed=["story-1"], results={"story-1": result_for(execution_id, "story-1")},
    )
    result, payload, delta = reconcile(repo, state)
    emit(
        "complete-artifact-pending-nested-blocks",
        result.returncode == 2 and payload.get("blocker", {}).get("code") == "completion_contradiction" and delta == 0,
        payload,
    )

    repo, spec = fixture("nested-without-result")
    state = start(repo, spec, "nested-without-result")
    complete_story(repo, spec, 1)
    add_execution(
        repo, state, plan=plan, statuses={"story-1": "completed", "story-2": "pending"},
        completed=["story-1"], results={},
    )
    result, payload, delta = reconcile(repo, state)
    emit(
        "nested-completion-without-result-blocks",
        result.returncode == 2 and payload.get("blocker", {}).get("code") == "completion_contradiction" and delta == 0,
        payload,
    )

    for suffix, path_value, content in (
        ("missing", ".writ/state/missing.json", None),
        ("escaping", "../outside.json", "{}"),
        ("malformed", ".writ/state/execution-bad.json", "{"),
        ("wrong-spec", ".writ/state/execution-wrong.json", json.dumps({"spec": "other", "plan": plan, "stories": {}})),
    ):
        repo, spec = fixture("execution-path-" + suffix)
        state = start(repo, spec, "execution-path-" + suffix)
        value = json.loads(state.read_text())
        value["storyExecution"]["executionStatePath"] = path_value
        value["storyExecution"]["planDigest"] = canonical_digest(plan)
        write(state, json.dumps(value))
        if content is not None:
            write((repo / path_value).resolve(), content)
        result, payload, delta = reconcile(repo, state)
        expected_code = "invalid_json" if suffix == "malformed" else "execution_state_contradiction"
        emit(
            "execution-path-" + suffix + "-blocks",
            result.returncode == 2
            and payload.get("blocker", {}).get("code") == expected_code
            and delta == 0,
            payload,
        )

    for suffix, mutate in (
        ("duplicate", lambda plan_value: plan_value["batches"][1]["stories"].append("story-1")),
        ("missing", lambda plan_value: plan_value["batches"].pop()),
    ):
        repo, state, _ = complete_claim("plan-" + suffix)
        nested = repo / json.loads(state.read_text())["storyExecution"]["executionStatePath"]
        value = json.loads(nested.read_text())
        mutate(value["plan"])
        write(nested, json.dumps(value))
        result, payload, delta = reconcile(repo, state)
        emit(
            "plan-" + suffix + "-story-blocks",
            result.returncode == 2 and payload.get("blocker", {}).get("code") == "plan_contradiction" and delta == 0,
            payload,
        )
    expect_block(
        "forged-plan-digest-blocks",
        lambda _repo, state, _artifact: (
            (lambda value: (value["storyExecution"].update(planDigest="0" * 64), write(state, json.dumps(value))))(
                json.loads(state.read_text())
            )
        ),
        "plan_contradiction",
    )

    def commit_drift(repo: pathlib.Path, _state: pathlib.Path, _artifact: pathlib.Path) -> None:
        write(repo / "unexplained.txt", "drift\n")
        command(["git", "add", "unexplained.txt"], repo)
        command(["git", "commit", "-m", "unexplained drift"], repo)

    expect_block("unexplained-head-drift-blocks", commit_drift, "repository_head_contradiction")
    expect_block(
        "integration-manifest-binding-blocks",
        lambda _repo, state, _artifact: (
            (lambda value: (
                value["storyExecution"]["integrationVerification"].update(packageManifestSha256="0" * 64),
                write(state, json.dumps(value)),
            ))(json.loads(state.read_text()))
        ),
        "integration_evidence_contradiction",
    )

    for suffix, mutate in (
        ("missing", lambda repo, state, artifact: artifact.unlink()),
        ("empty", lambda repo, state, artifact: write(artifact, "")),
        ("changed", lambda repo, state, artifact: write(artifact, "changed\n")),
        ("escaping", lambda repo, state, artifact: (
            (lambda value: (
                value["storyExecution"]["integrationVerification"].update(evidenceArtifact="../outside.txt"),
                write(state, json.dumps(value)),
                write(repo.parent / "outside.txt", "outside\n"),
            ))(json.loads(state.read_text()))
        )),
        ("wrong-hash", lambda repo, state, artifact: (
            (lambda value: (
                value["storyExecution"]["integrationVerification"].update(evidenceArtifactSha256="0" * 64),
                write(state, json.dumps(value)),
            ))(json.loads(state.read_text()))
        )),
    ):
        expect_block("integration-evidence-" + suffix + "-blocks", mutate, "integration_evidence_contradiction")

    repo, state, _ = complete_claim("completion-without-ownership")
    value = json.loads(state.read_text())
    value["worktrees"] = {}
    write(state, json.dumps(value))
    result, payload, delta = reconcile(repo, state)
    emit(
        "executed-completion-without-ownership-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "completion_contradiction"
        and delta == 0,
        payload,
    )

    repo, spec = fixture("repository-branch-switch")
    state = start(repo, spec, "repository-branch-switch")
    command(["git", "switch", "-c", "unexpected-branch"], repo)
    result, payload, delta = reconcile(repo, state)
    emit(
        "repository-branch-switch-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "repository_identity_mismatch"
        and delta == 0,
        payload,
    )

    repo, spec = fixture("repository-detached-head")
    state = start(repo, spec, "repository-detached-head")
    command(["git", "checkout", "--detach"], repo)
    result, payload, delta = reconcile(repo, state)
    emit(
        "repository-detached-head-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "repository_identity_mismatch"
        and delta == 0,
        payload,
    )

    repo, spec = fixture("repository-remote-change")
    command(["git", "remote", "add", "origin", "https://example.invalid/original.git"], repo)
    state = start(repo, spec, "repository-remote-change")
    command(["git", "remote", "set-url", "origin", "https://example.invalid/changed.git"], repo)
    result, payload, delta = reconcile(repo, state)
    emit(
        "repository-remote-change-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "repository_identity_mismatch"
        and delta == 0,
        payload,
    )

    repo, spec = fixture("authorized-spec-lite-drift")
    state = start(repo, spec, "authorized-spec-lite-drift")
    spec_lite = repo / spec / "spec-lite.md"
    prior_digest = hashlib.sha256(spec_lite.read_bytes()).hexdigest()
    write(spec_lite, spec_lite.read_text() + "\nClarified implementation note.\n")
    drift_log = repo / spec / "drift-log.md"
    write(drift_log, """# Drift Log

#### [DEV-001] Clarified implementation note
- **Severity:** Small
- **Spec said:** Original concise note
- **Implementation did:** Clarified the implementation note
- **Resolution:** Auto-amended
- **Spec-lite updated:** Yes
""")
    review_result = repo / ".writ/state/review-result.json"
    write(review_result, json.dumps({
        "schema": "recommend-spec-lite-review-v1",
        "execution_id": "authorized-spec-lite-drift",
        "story_id": "story-1",
        "outcome": "passed",
        "drift_severity": "small",
        "dev_ids": ["DEV-001"],
        "summary": "Small drift accepted by Gate 3.5.",
    }))
    record_result, record_payload = run_helper(
        "record-spec-lite-amendment",
        "--state", state,
        "--repo", repo,
        "--story-id", "story-1",
        "--dev-id", "DEV-001",
        "--prior-sha256", prior_digest,
        "--review-result", review_result,
    )
    result, payload, delta = reconcile(repo, state)
    emit(
        "authorized-spec-lite-drift-chain-passes",
        record_result.returncode == 0 and result.returncode == 0 and delta == 1,
        {"record": record_payload, "reconcile": payload},
    )
    authorized_state = state.read_text()
    authorized_spec_lite = spec_lite.read_text()
    authorized_drift_log = drift_log.read_text()

    write(drift_log, authorized_drift_log.replace("Original concise note", "Rewritten note"))
    result, payload, delta = reconcile(repo, state)
    emit(
        "rewritten-amendment-drift-entry-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "spec_lite_amendment_contradiction"
        and delta == 0,
        payload,
    )
    write(drift_log, authorized_drift_log)

    write(spec_lite, authorized_spec_lite + "\nUnrecorded tamper.\n")
    result, payload, delta = reconcile(repo, state)
    emit(
        "unrecorded-spec-lite-drift-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "spec_lite_amendment_contradiction"
        and delta == 0,
        payload,
    )
    write(spec_lite, authorized_spec_lite)
    write(state, authorized_state)

    broken = json.loads(authorized_state)
    broken["spec"]["specLiteAmendments"]["amendments"][0]["priorSha256"] = "0" * 64
    write(state, json.dumps(broken))
    result, payload, delta = reconcile(repo, state)
    emit(
        "broken-spec-lite-amendment-chain-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "spec_lite_amendment_contradiction"
        and delta == 0,
        payload,
    )
    write(state, authorized_state)

    write(drift_log, authorized_drift_log.replace("DEV-001", "DEV-002"))
    result, payload, delta = reconcile(repo, state)
    emit(
        "missing-amendment-dev-id-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "spec_lite_amendment_contradiction"
        and delta == 0,
        payload,
    )
    write(drift_log, authorized_drift_log)
    write(state, authorized_state)

    duplicate = json.loads(authorized_state)
    duplicate["spec"]["specLiteAmendments"]["amendments"].append(
        copy.deepcopy(duplicate["spec"]["specLiteAmendments"]["amendments"][0])
    )
    write(state, json.dumps(duplicate))
    result, payload, delta = reconcile(repo, state)
    emit(
        "duplicate-amendment-dev-id-blocks",
        result.returncode == 2
        and payload.get("blocker", {}).get("code") == "invalid_state"
        and delta == 0,
        payload,
    )

    repo, state, _ = complete_claim("fully-corroborated")
    result, payload, delta = reconcile(repo, state)
    emit(
        "fully-corroborated-completion-one-revision",
        result.returncode == 0
        and delta == 1
        and json.loads(state.read_text())["storyExecution"]["completedStoryIds"] == ["story-1", "story-2"],
        payload,
    )

    repo, spec = fixture("baseline-prototype", baseline_story_1=True)
    state = start(repo, spec, "baseline-prototype")
    plan = {"batches": [{"parallel": False, "stories": ["story-2"]}]}
    add_execution(repo, state, plan=plan, statuses={"story-2": "pending"}, completed=["story-1"])
    result, payload, delta = reconcile(repo, state)
    emit("lock-time-completed-prototype-valid", result.returncode == 0 and delta == 1, payload)

    malformed_answer = WORKSPACE / "failed-malformed-answer.json"
    write(malformed_answer, json.dumps({
        **result_for("result-exec", "story-1"),
        "status": "failed",
        "required_answer": "garbage",
    }))
    result, payload = run_helper("normalize-result", "--input", malformed_answer, "--execution-id", "result-exec")
    emit(
        "failed-result-canonical-empty-answer",
        result.returncode == 0
        and payload.get("status") == "blocked"
        and payload.get("blocker", {}).get("code") == "nested_result_failed"
        and payload.get("required_answer") == EMPTY_ANSWER,
        payload,
    )

    invalid_json = WORKSPACE / "invalid-result.json"
    write(invalid_json, "{")
    wrong_identity = WORKSPACE / "wrong-identity.json"
    write(wrong_identity, json.dumps(result_for("other-execution", "story-1")))
    malformed_evidence = WORKSPACE / "malformed-evidence.json"
    bad_evidence_result = result_for("result-exec", "story-1")
    bad_evidence_result["evidence"] = {"summary": "", "artifacts": "not-a-list"}
    write(malformed_evidence, json.dumps(bad_evidence_result))
    cli_cases = (
        ("invalid-result-json", ["normalize-result", "--input", invalid_json, "--execution-id", "result-exec"]),
        ("missing-result-fields", ["normalize-result", "--input", WORKSPACE / "missing-fields.json", "--execution-id", "result-exec"]),
        ("mismatched-result-identity", ["normalize-result", "--input", wrong_identity, "--execution-id", "result-exec"]),
        ("malformed-result-evidence", ["normalize-result", "--input", malformed_evidence, "--execution-id", "result-exec"]),
        ("unknown-operation", ["unknown-operation"]),
        ("missing-cli-argument", ["reconcile", "--state", "missing"]),
    )
    write(WORKSPACE / "missing-fields.json", json.dumps({"status": "succeeded"}))
    for suffix, args in cli_cases:
        result, payload = run_helper(*args)
        canonical = (
            payload.get("schema") == "recommend-command-result-v1"
            and payload.get("status") == "blocked"
            and payload.get("required_answer") == EMPTY_ANSWER
            and result.stderr == ""
        )
        emit("canonical-blocked-" + suffix, result.returncode == 2 and canonical, {"payload": payload, "stderr": result.stderr})

    totals_mutations = (
        ("stories", lambda text: text.replace("**Stories:** 2", "**Stories:** 3")),
        ("acceptance", lambda text: text.replace("**Acceptance criteria:** 6", "**Acceptance criteria:** 7")),
        ("tasks", lambda text: text.replace("**Implementation tasks:** 10", "**Implementation tasks:** 11")),
        ("completed", lambda text: text.replace("**Completed tasks:** 0", "**Completed tasks:** 1")),
        ("progress", lambda text: text.replace("**Overall progress:** 0%", "**Overall progress:** 1%")),
        ("duplicate", lambda text: text.replace("- **Stories:** 2", "- **Stories:** 2\n- **Stories:** 2")),
        ("malformed", lambda text: text.replace("**Stories:** 2", "**Stories:** two")),
        ("unknown", lambda text: text.replace("- **Stories:** 2", "- **Stories:** 2\n- **Unknown:** 2")),
    )
    for suffix, mutate in totals_mutations:
        repo, spec = fixture("totals-" + suffix)
        readme = repo / spec / "user-stories/README.md"
        write(readme, mutate(readme.read_text()))
        state = repo / ".writ/state/candidate.json"
        result, payload = run_helper(
            "start", "--repo", repo, "--spec", spec, "--state", state,
            "--execution-id", "totals-" + suffix, "--token", "token",
            "--entry-command", "implement-spec", "--invocation-json", json.dumps(["--recommend", spec.name]),
        )
        emit("totals-" + suffix + "-blocks", result.returncode == 2 and not state.exists(), payload)
    for suffix, totals in (("correct", True), ("absent", False)):
        repo, spec = fixture("totals-" + suffix, totals=totals)
        state = start(repo, spec, "totals-" + suffix)
        emit("totals-" + suffix + "-passes", state.exists(), "")

    repo, spec = fixture("totals-round-half-up")
    root = repo / spec
    story1 = root / "user-stories/story-1-one.md"
    story1_text = story1.read_text().replace("> **Status:** Not Started", "> **Status:** In Progress")
    story1_text = story1_text.replace("- [ ] 1.1", "- [x] 1.1").replace("- [ ] 1.2", "- [x] 1.2")
    write(story1, story1_text)
    story2 = root / "user-stories/story-2-two.md"
    write(story2, story2.read_text() + "- [ ] 2.6 Sixth task\n")
    story3 = (root / "user-stories/story-1-one.md").read_text()
    story3 = story3.replace("# Story 1:", "# Story 3:").replace("> **Status:** In Progress", "> **Status:** Not Started")
    story3 = story3.replace("- [x]", "- [ ]").replace("1.", "3.")
    write(root / "user-stories/story-3-three.md", story3)
    readme = root / "user-stories/README.md"
    text = readme.read_text()
    text = text.replace("> **Progress:** 0/2", "> **Progress:** 0/3")
    text = text.replace(
        "| [1](story-1-one.md) | One | Not Started | High | None | 5 | 0/5 |",
        "| [1](story-1-one.md) | One | In Progress | High | None | 5 | 2/5 |",
    )
    text = text.replace("| [2](story-2-two.md) | Two | Not Started | High | Story 1 | 5 | 0/5 |",
                        "| [2](story-2-two.md) | Two | Not Started | High | Story 1 | 6 | 0/6 |\n"
                        "| [3](story-3-three.md) | Three | Not Started | High | None | 5 | 0/5 |")
    text = text.replace("**Stories:** 2", "**Stories:** 3")
    text = text.replace("**Acceptance criteria:** 6", "**Acceptance criteria:** 9")
    text = text.replace("**Implementation tasks:** 10", "**Implementation tasks:** 16")
    text = text.replace("**Completed tasks:** 0", "**Completed tasks:** 2")
    text = text.replace("**Overall progress:** 0%", "**Overall progress:** 13%")
    write(readme, text)
    state = start(repo, spec, "totals-round-half-up")
    emit("totals-progress-rounds-half-up", state.exists(), "")

    repo, spec = fixture("normal-no-mutation")
    state = repo / ".writ/state/normal.json"
    result, payload = run_helper(
        "start", "--repo", repo, "--spec", "missing", "--state", state,
        "--execution-id", "normal", "--token", "normal",
        "--entry-command", "implement-spec", "--invocation-json", json.dumps([spec.name]),
    )
    emit("normal-mode-no-recommended-mutation", result.returncode == 0 and not state.exists(), payload)

    repo, spec = fixture("story45-inert")
    state = start(repo, spec, "story45-inert")
    value = json.loads(state.read_text())
    value["delivery"]["pr"] = {"number": 4}
    write(state, json.dumps(value))
    result, payload, delta = reconcile(repo, state)
    emit("story-4-5-fields-remain-inert", result.returncode == 2 and delta == 0, payload)

    repo, spec = fixture("dirty-baseline")
    unrelated = repo / "unrelated-dirty.txt"
    write(unrelated, "preserve exactly\n")
    before = unrelated.read_bytes()
    state = start(repo, spec, "dirty-baseline")
    result, payload, delta = reconcile(repo, state)
    emit(
        "unrelated-dirty-baseline-preserved",
        result.returncode == 0 and delta == 1 and unrelated.read_bytes() == before,
        payload,
    )
finally:
    shutil.rmtree(WORKSPACE, ignore_errors=True)
