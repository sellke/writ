#!/usr/bin/env python3
"""Fail-closed local reducer for recommended delivery state."""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


SCHEMA = "recommend-execution-v1"
RESULT_SCHEMA = "recommend-command-result-v1"
LAUNCH_SCHEMA = "recommend-worktree-launch-v1"
ACK_SCHEMA = "recommend-worktree-reservation-ack-v1"
ACTIVE_WORKTREE_STATUSES = {"reserved", "active", "adopted"}
WORKTREE_STATUSES = ACTIVE_WORKTREE_STATUSES | {"integrated", "blocked"}
STATE_STATUSES = {
    "planning", "implementing", "verifying", "committing", "opening_pr",
    "pr_open", "waiting_ci", "discovering_preview", "preview_ready",
    "awaiting_approval", "production_approved",
    "merging", "releasing", "complete", "partially_released",
    "blocked",
}
STORY5_STATUSES = {"merging", "releasing", "complete", "partially_released"}
RESULT_STATUSES = {"succeeded", "blocked", "answer_required", "failed"}
STORY_STATUSES = {"Not Started", "In Progress", "Completed", "Blocked"}
NESTED_STORY_STATUSES = {"pending", "in_progress", "completed", "failed"}
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
REQUIRED_LOG_FIELDS = (
    "Decision",
    "Evidence",
    "Alternatives",
    "Risk",
    "Reversibility",
    "Selection",
    "Result",
)


class ContractError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return digest_bytes(data)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("invalid_json", f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("invalid_json", f"{path}: top-level value must be an object")
    return value


def atomic_write_json(path: Path, value: dict[str, Any], exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if exclusive:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ContractError("state_collision", f"state already exists: {path}") from exc
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        return
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        raise ContractError("git_error", result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def normalize_remote_identity(raw: str) -> str:
    value = raw.strip()
    scp = re.fullmatch(r"(?:[^@/\s]+@)?([^:/\s]+):(.+)", value)
    if scp and "://" not in value:
        host, path = scp.groups()
        normalized_path = path.rstrip("/")
        if normalized_path.endswith(".git"):
            normalized_path = normalized_path[:-4]
        return f"ssh://{host.lower()}/{normalized_path}"
    parsed = urlsplit(value)
    if parsed.scheme and parsed.hostname:
        host = parsed.hostname.lower()
        try:
            port = parsed.port
        except ValueError as exc:
            raise ContractError("repository_identity_mismatch", "remote URL has an invalid port") from exc
        if port:
            host = f"{host}:{port}"
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return urlunsplit((parsed.scheme.lower(), host, path, "", ""))
    return value.rstrip("/")


def repo_identity(repo: Path) -> dict[str, str | None]:
    root = Path(git(repo, "rev-parse", "--show-toplevel")).resolve()
    remotes = sorted(filter(None, git(repo, "remote", check=False).splitlines()))
    if "origin" in remotes:
        remote_name = "origin"
    elif len(remotes) == 1:
        remote_name = remotes[0]
    elif not remotes:
        remote_name = None
    else:
        raise ContractError("repository_identity_mismatch", "repository has multiple remotes but no canonical origin")
    return {
        "root": str(root),
        "branchRef": git(repo, "symbolic-ref", "-q", "HEAD", check=False) or None,
        "headSha": git(repo, "rev-parse", "HEAD"),
        "remoteName": remote_name,
        "remoteIdentity": normalize_remote_identity(
            git(repo, "remote", "get-url", remote_name, check=False)
        ) if remote_name else None,
    }


def parse_invocation(command: str, argv: list[str]) -> dict[str, Any]:
    recommend = "--recommend" in argv
    if not recommend:
        return {"mode": "normal", "command": command, "action": "no_recommended_state"}
    forbidden_common = {"--quick", "--force", "--dry-run", "--draft", "--no-split", "--skip-gate", "--no-tag"}
    present = sorted(forbidden_common.intersection(argv))
    if present:
        raise ContractError("unsupported_invocation", f"{command}: unsupported with --recommend: {', '.join(present)}")
    if command == "implement-phase":
        raise ContractError("unsupported_invocation", "/implement-phase --recommend is unsupported")
    if command == "create-spec":
        source_modes = [flag for flag in ("--from-issue", "--from-prototype") if flag in argv]
        if len(source_modes) > 1:
            raise ContractError("unsupported_invocation", "create-spec accepts exactly one source mode")
        if "--resume" in argv:
            raise ContractError("unsupported_invocation", "create-spec recommendation resume is unsupported")
        positional = [item for item in argv if not item.startswith("--")]
        if "--from-issue" in argv and len(positional) != 1:
            raise ContractError("unsupported_invocation", "--from-issue requires exactly one issue path")
        if "--from-prototype" in argv and positional:
            raise ContractError("unsupported_invocation", "--from-prototype accepts no additional source")
        if not source_modes and len(positional) > 1:
            raise ContractError("unsupported_invocation", "create-spec accepts one idea/source argument")
        source_mode = source_modes[0][2:] if source_modes else "standard"
        return {"mode": "recommend", "command": command, "sourceMode": source_mode}
    if command == "implement-spec":
        if "--resume" in argv:
            raise ContractError("unsupported_invocation", "start cannot resume; load the explicit state through reconcile")
        if "--from" in argv:
            raise ContractError("unsupported_invocation", "partial DAG --from is unsupported")
        positional = [item for item in argv if not item.startswith("--") and item != "recommend"]
        if len(positional) > 1:
            raise ContractError("unsupported_invocation", "implement-spec accepts one spec")
        return {"mode": "recommend", "command": command, "sourceMode": "existing-spec"}
    raise ContractError("unsupported_invocation", f"unsupported command: {command}")


def project_story(text: str) -> str:
    text = text.split("\n## What Was Built", 1)[0]
    text = re.sub(r"(?m)^> \*\*Status:\*\*.*$", "> **Status:** {mutable}", text)
    return re.sub(r"(?m)^(\s*- )\[[ xX]\]", r"\1[ ]", text)


def project_readme(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("> **Progress:**"):
            lines.append("> **Progress:** {mutable}")
        elif line.startswith("- **Completed tasks:**"):
            lines.append("- **Completed tasks:** {mutable}")
        elif line.startswith("- **Overall progress:**"):
            lines.append("- **Overall progress:** {mutable}")
        elif re.match(r"^\| \[\d+\]", line):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 7:
                cells[2] = "{mutable-status}"
                cells[6] = "{mutable-progress}"
                line = "| " + " | ".join(cells) + " |"
            lines.append(line)
        else:
            lines.append(line)
    return "\n".join(lines)


def project_spec(text: str) -> str:
    return re.sub(r"(?m)^> \*\*Status:\*\*.*$", "> **Status:** {mutable}", text)


def status_value(text: str, label: str = "Status") -> str:
    match = re.search(rf"(?m)^> \*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", text)
    if not match:
        raise ContractError("invalid_package", f"missing {label} metadata")
    value = re.sub(r"\s*[✅⚠️].*$", "", match.group(1)).strip()
    if value not in STORY_STATUSES:
        raise ContractError("invalid_package", f"unsupported {label.lower()}: {value}")
    return value


def checked_count(text: str, pattern: str) -> tuple[int, int]:
    matches = re.findall(pattern, text, re.MULTILINE)
    return len(matches), sum(marker.lower() == "x" for marker in matches)


def parse_story_index(path: Path, text: str) -> tuple[list[dict[str, Any]], tuple[int, int]]:
    progress = re.search(
        r"(?m)^> \*\*Progress:\*\*\s*(\d+)\s*/\s*(\d+)(?:\s+stories(?:\s+·.*)?)?\s*$",
        text,
    )
    if not progress:
        raise ContractError("readme_mismatch", "README is missing overall Progress: completed/total")
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not re.match(r"^\|\s*\[\d+\]\([^)]+\.md\)\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            raise ContractError("readme_mismatch", f"README story row must have 7 cells: {line}")
        link = re.fullmatch(r"\[(\d+)\]\(([^)]+)\)", cells[0])
        task_progress = re.fullmatch(r"(\d+)\s*/\s*(\d+)", cells[6])
        if not link or not cells[5].isdigit() or not task_progress:
            raise ContractError("readme_mismatch", f"README story row is malformed: {line}")
        status = re.sub(r"\s*[✅⚠️].*$", "", cells[2]).strip()
        if status not in STORY_STATUSES:
            raise ContractError("readme_mismatch", f"README has unsupported status: {status}")
        rows.append({
            "number": int(link.group(1)),
            "path": link.group(2),
            "status": status,
            "tasks": int(cells[5]),
            "completedTasks": int(task_progress.group(1)),
            "progressTasks": int(task_progress.group(2)),
            "dependencies": cells[4],
        })
    if not rows:
        raise ContractError("readme_mismatch", "README contains no indexed story rows")
    numbers = [row["number"] for row in rows]
    paths = [row["path"] for row in rows]
    if len(numbers) != len(set(numbers)) or len(paths) != len(set(paths)):
        raise ContractError("readme_mismatch", "README contains duplicate story IDs or paths")
    return rows, (int(progress.group(1)), int(progress.group(2)))


def parse_readme_totals(text: str) -> dict[str, int] | None:
    headings = list(re.finditer(r"(?m)^## Totals\s*$", text))
    if not headings:
        return None
    if len(headings) != 1:
        raise ContractError("readme_mismatch", "README must contain at most one Totals section")
    start = headings[0].end()
    next_heading = re.search(r"(?m)^## ", text[start:])
    body = text[start:start + next_heading.start()] if next_heading else text[start:]
    expected = {
        "Stories": False,
        "Acceptance criteria": False,
        "Implementation tasks": False,
        "Completed tasks": False,
        "Overall progress": True,
    }
    claims: dict[str, int] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = re.fullmatch(r"- \*\*([^*]+):\*\*\s*(\d+)(%)?", line)
        if not match:
            raise ContractError("readme_mismatch", f"README Totals claim is malformed: {line}")
        label, number, percent = match.groups()
        if label not in expected:
            raise ContractError("readme_mismatch", f"README Totals contains unknown claim: {label}")
        if label in claims:
            raise ContractError("readme_mismatch", f"README Totals duplicates claim: {label}")
        if bool(percent) != expected[label]:
            raise ContractError("readme_mismatch", f"README Totals unit is invalid for {label}")
        claims[label] = int(number)
    missing = sorted(set(expected) - set(claims))
    if missing:
        raise ContractError("readme_mismatch", f"README Totals is missing claims: {missing}")
    return claims


def referenced_subspecs(spec_root: Path, initial: list[Path]) -> list[Path]:
    found: set[Path] = set()
    pending = list(initial)
    while pending:
        source = pending.pop()
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ContractError("incomplete_package", f"{source}: {exc}") from exc
        for raw in re.findall(r"\]\(([^)#?]+\.md)(?:#[^)]*)?\)", text):
            candidate = (source.parent / raw).resolve()
            try:
                relative = candidate.relative_to(spec_root)
            except ValueError:
                continue
            if relative.parts[:1] != ("sub-specs",):
                continue
            if not candidate.is_file():
                raise ContractError("incomplete_package", f"referenced sub-spec is missing: {relative}")
            if candidate not in found:
                found.add(candidate)
                pending.append(candidate)
    return sorted(found)


def count_story_contract(path: Path, text: str) -> tuple[str, list[str], dict[str, Any]]:
    match = re.match(r"story-(\d+)-", path.name)
    if not match:
        raise ContractError("invalid_story", f"unparseable story path: {path}")
    story_id = f"story-{match.group(1)}"
    acceptance, completed_acceptance = checked_count(text, r"^- \[([ xX])\] Given ")
    tasks, completed_tasks = checked_count(text, rf"^- \[([ xX])\] {match.group(1)}\.\d+ ")
    if not 3 <= acceptance <= 5:
        raise ContractError("invalid_story", f"{story_id}: expected 3-5 acceptance criteria, got {acceptance}")
    if not 5 <= tasks <= 7:
        raise ContractError("invalid_story", f"{story_id}: expected 5-7 tasks, got {tasks}")
    dependency_match = re.search(r"(?m)^> \*\*Dependencies:\*\* (.+)$", text)
    dependencies: list[str] = []
    if dependency_match and dependency_match.group(1).strip().lower() != "none":
        dependencies = [f"story-{number}" for number in re.findall(r"(?:Story|story-)\s*(\d+)", dependency_match.group(1))]
    return story_id, dependencies, {
        "status": status_value(text),
        "acceptance": acceptance,
        "completedAcceptance": completed_acceptance,
        "tasks": tasks,
        "completedTasks": completed_tasks,
    }


def validate_dag(dependencies: dict[str, list[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(story: str) -> None:
        if story in visiting:
            raise ContractError("invalid_dag", f"dependency cycle at {story}")
        if story in visited:
            return
        visiting.add(story)
        for dependency in dependencies.get(story, []):
            if dependency not in dependencies:
                raise ContractError("invalid_dag", f"{story}: missing dependency {dependency}")
            visit(dependency)
        visiting.remove(story)
        visited.add(story)

    for story in dependencies:
        visit(story)


def parse_log(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ContractError("missing_recommendation_log", f"{path}: {exc}") from exc
    text = data.decode("utf-8")
    matches = list(re.finditer(r"(?m)^## (REC-\d+) — .+$", text))
    if not matches:
        raise ContractError("invalid_recommendation_log", "recommendation log has no entries")
    entries: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start():end].rstrip() + "\n"
        fields = {name: value.strip() for name, value in re.findall(r"(?m)^- \*\*([^*]+):\*\* (.+)$", body)}
        missing = [field for field in REQUIRED_LOG_FIELDS if field not in fields]
        if missing:
            raise ContractError("invalid_recommendation_log", f"{match.group(1)} missing fields: {missing}")
        entries.append({"id": match.group(1), "digest": digest_bytes(body.encode()), "result": fields["Result"]})
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise ContractError("invalid_recommendation_log", "duplicate recommendation entry ID")
    return {
        "path": str(path),
        "digestSha256": digest_bytes(data),
        "entryIds": ids,
        "entryDigests": {entry["id"]: entry["digest"] for entry in entries},
        "pendingEntryIds": [entry["id"] for entry in entries if entry["result"].startswith("Pending")],
    }


def parse_drift_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"entryIds": [], "entryDigests": {}}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError("spec_lite_amendment_contradiction", f"{path}: {exc}") from exc
    matches = list(re.finditer(r"(?m)^#### \[(DEV-\d+)\] .+$", text))
    entries: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start():end].rstrip() + "\n"
        entries.append((match.group(1), digest_bytes(body.encode())))
    ids = [entry_id for entry_id, _ in entries]
    if len(ids) != len(set(ids)):
        raise ContractError("spec_lite_amendment_contradiction", "drift log contains duplicate DEV IDs")
    return {"entryIds": ids, "entryDigests": dict(entries)}


def validate_package(
    repo: Path, spec_relative: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    spec_root = (repo / spec_relative).resolve()
    try:
        spec_root.relative_to(repo.resolve())
    except ValueError as exc:
        raise ContractError("invalid_spec_path", "spec path escapes repository") from exc
    base_required = [
        spec_root / "spec.md",
        spec_root / "spec-lite.md",
        spec_root / "user-stories" / "README.md",
        spec_root / "sub-specs" / "technical-spec.md",
    ]
    missing = [str(path) for path in base_required if not path.is_file()]
    if missing:
        raise ContractError("incomplete_package", f"missing required artifacts: {missing}")
    readme = base_required[2].read_text(encoding="utf-8")
    index_rows, overall_progress = parse_story_index(base_required[2], readme)
    indexed_stories: list[Path] = []
    for row in index_rows:
        candidate = (base_required[2].parent / row["path"]).resolve()
        try:
            candidate.relative_to(base_required[2].parent.resolve())
        except ValueError as exc:
            raise ContractError("readme_mismatch", f"story path escapes user-stories: {row['path']}") from exc
        if not candidate.is_file():
            raise ContractError("incomplete_package", f"indexed story is missing: {row['path']}")
        indexed_stories.append(candidate)
    discovered = sorted((spec_root / "user-stories").glob("story-*.md"))
    if {path.resolve() for path in discovered} != set(indexed_stories):
        unindexed = sorted(path.name for path in set(discovered) - set(indexed_stories))
        raise ContractError("readme_mismatch", f"unindexed or mismatched story files: {unindexed}")
    sub_specs = referenced_subspecs(spec_root, base_required + indexed_stories)
    required = sorted(set(base_required + indexed_stories + sub_specs))
    spec_text = base_required[0].read_text(encoding="utf-8")
    if not re.search(r"(?m)^> \*\*Contract Locked:\*\* ✅\s*$", spec_text):
        raise ContractError("contract_unlocked", "spec.md is not contract locked")
    dependency_map: dict[str, list[str]] = {}
    story_facts: dict[str, dict[str, Any]] = {}
    completed_stories = 0
    total_acceptance = 0
    total_tasks = 0
    completed_tasks = 0
    for row, story in zip(index_rows, indexed_stories):
        story_id, dependencies, facts = count_story_contract(story, story.read_text(encoding="utf-8"))
        expected_id = f"story-{row['number']}"
        if story_id != expected_id:
            raise ContractError("readme_mismatch", f"README story {expected_id} points to {story.name}")
        if story_id in dependency_map:
            raise ContractError("invalid_story", f"duplicate story ID {story_id}")
        dependency_map[story_id] = dependencies
        story_facts[story_id] = {
            **facts,
            "dependencies": dependencies,
            "path": story.relative_to(repo).as_posix(),
            "byteSha256": digest_bytes(story.read_bytes()),
        }
        row_dependencies = [] if row["dependencies"].lower() == "none" else [
            f"story-{number}" for number in re.findall(r"(?:Story|story-)\s*(\d+)", row["dependencies"])
        ]
        if row["status"] != facts["status"] or row["tasks"] != facts["tasks"]:
            raise ContractError("readme_mismatch", f"{story_id}: README status/task count disagrees with story")
        if row["progressTasks"] != facts["tasks"] or row["completedTasks"] != facts["completedTasks"]:
            raise ContractError("readme_mismatch", f"{story_id}: README task progress disagrees with story")
        if row_dependencies != dependencies:
            raise ContractError("readme_mismatch", f"{story_id}: README dependencies disagree with story")
        completed = facts["status"] == "Completed"
        if completed and (facts["completedTasks"] != facts["tasks"] or facts["completedAcceptance"] != facts["acceptance"]):
            raise ContractError("readme_mismatch", f"{story_id}: completed story has unchecked tasks or acceptance criteria")
        if not completed and facts["completedTasks"] == facts["tasks"]:
            raise ContractError("readme_mismatch", f"{story_id}: all tasks are checked but story is not Completed")
        completed_stories += int(completed)
        total_acceptance += facts["acceptance"]
        total_tasks += facts["tasks"]
        completed_tasks += facts["completedTasks"]
    validate_dag(dependency_map)
    if overall_progress != (completed_stories, len(index_rows)):
        raise ContractError("readme_mismatch", "README overall progress disagrees with story statuses")
    totals = parse_readme_totals(readme)
    if totals is not None:
        expected_totals = {
            "Stories": len(index_rows),
            "Acceptance criteria": total_acceptance,
            "Implementation tasks": total_tasks,
            "Completed tasks": completed_tasks,
            "Overall progress": (200 * completed_tasks + total_tasks) // (2 * total_tasks),
        }
        mismatches = [
            label for label, expected in expected_totals.items()
            if totals[label] != expected
        ]
        if mismatches:
            raise ContractError("readme_mismatch", f"README Totals disagrees with indexed stories: {mismatches}")
    for path in required:
        if "[UNPLANNED]" in path.read_text(encoding="utf-8"):
            raise ContractError("unplanned_operation", f"unresolved [UNPLANNED] in {path}")
    artifacts: list[dict[str, str]] = []
    for path in sorted(required):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(repo).as_posix()
        if path.name.startswith("story-"):
            projected, rule = project_story(text), "story-contract-v1"
        elif path.name == "README.md":
            projected, rule = project_readme(text), "story-index-v1"
        elif path.name == "spec.md":
            projected, rule = project_spec(text), "spec-contract-v1"
        else:
            projected, rule = text, "exact-bytes-v1"
        artifacts.append({
            "path": relative,
            "immutableProjectionSha256": digest_bytes(projected.encode()),
            "byteSha256AtLock": digest_bytes(path.read_bytes()),
            "projectionRule": rule,
        })
    validation = {
        "contractLocked": True,
        "requiredFilesPresent": True,
        "storiesParseable": True,
        "acceptanceCriteriaValid": True,
        "tasksValid": True,
        "dagAcyclic": True,
        "readmeConsistent": True,
        "unresolvedUnplannedCount": 0,
    }
    manifest = {
        "schema": "recommend-package-manifest-v1",
        "specPath": Path(spec_relative).as_posix(),
        "artifacts": artifacts,
        "validation": validation,
    }
    immutable_identity = {
        "schema": manifest["schema"],
        "specPath": manifest["specPath"],
        "artifacts": [
            {
                "path": artifact["path"],
                "immutableProjectionSha256": artifact["immutableProjectionSha256"],
                "projectionRule": artifact["projectionRule"],
            }
            for artifact in artifacts
        ],
    }
    manifest["digestSha256"] = digest_json(immutable_identity)
    log_path = spec_root / "recommendation-log.md"
    log = parse_log(log_path)
    log["path"] = log_path.relative_to(repo).as_posix()
    return manifest, log, story_facts


def require_object(value: Any, keys: set[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("invalid_state", f"{location} must be an object")
    missing = sorted(keys - set(value))
    if missing:
        raise ContractError("invalid_state", f"{location} missing required keys: {missing}")
    return value


def require_string(value: Any, location: str, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value:
        raise ContractError("invalid_state", f"{location} must be a non-empty string")


def require_string_list(value: Any, location: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ContractError("invalid_state", f"{location} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ContractError("invalid_state", f"{location} must not contain duplicates")


def empty_required_answer() -> dict[str, Any]:
    return {
        "decision_id": None,
        "question_id": None,
        "option_ids": [],
        "selected_option_id": None,
        "resume_transition": None,
        "interaction_id": None,
    }


def canonical_blocked_result(
    code: str,
    summary: str,
    *,
    execution_id: str = "unknown",
    command: str = "recommend-state",
    resume_state: str | None = None,
) -> dict[str, Any]:
    value = {
        "schema": RESULT_SCHEMA,
        "execution_id": execution_id or "unknown",
        "mode": "recommend",
        "command": command or "recommend-state",
        "status": "blocked",
        "completed_state": None,
        "resume_state": resume_state,
        "evidence": {"summary": summary, "artifacts": []},
        "identifiers": {},
        "required_answer": empty_required_answer(),
        "blocker": {"code": code, "summary": summary},
    }
    validate_command_result(value, expected_execution_id=value["execution_id"])
    return value


def validate_command_result(
    value: Any,
    *,
    expected_execution_id: str | None = None,
    allow_failed: bool = False,
) -> dict[str, Any]:
    required = {
        "schema", "execution_id", "mode", "command", "status", "completed_state",
        "resume_state", "evidence", "identifiers", "required_answer", "blocker",
    }
    if not isinstance(value, dict):
        raise ContractError("invalid_result", "nested result must be an object")
    missing = sorted(required - set(value))
    if missing:
        raise ContractError("invalid_result", f"nested result missing required keys: {missing}")
    if value["schema"] != RESULT_SCHEMA or value["mode"] != "recommend":
        raise ContractError("invalid_result", "nested result schema or mode is invalid")
    require_string(value["execution_id"], "result.execution_id")
    if expected_execution_id is not None and value["execution_id"] != expected_execution_id:
        raise ContractError("invalid_result", "nested result execution identity is invalid")
    require_string(value["command"], "result.command")
    statuses = {"succeeded", "blocked", "answer_required"} | ({"failed"} if allow_failed else set())
    if value["status"] not in statuses:
        raise ContractError("invalid_result", f"unknown nested result status: {value['status']!r}")
    if value["completed_state"] not in {None, "verified_implementation", "production_approved"}:
        raise ContractError("invalid_result", "result.completed_state is invalid")
    if value["resume_state"] not in {None} | STATE_STATUSES:
        raise ContractError("invalid_result", "result.resume_state is invalid")
    evidence = require_object(value["evidence"], {"summary", "artifacts"}, "result.evidence")
    require_string(evidence["summary"], "result.evidence.summary")
    require_string_list(evidence["artifacts"], "result.evidence.artifacts")
    if not isinstance(value["identifiers"], dict):
        raise ContractError("invalid_result", "result.identifiers must be an object")
    blocker = require_object(value["blocker"], {"code", "summary"}, "result.blocker")
    require_string(blocker["code"], "result.blocker.code", nullable=True)
    require_string(blocker["summary"], "result.blocker.summary", nullable=True)
    status = value["status"]
    if status == "answer_required":
        answer = value["required_answer"]
        answer_keys = {
            "decision_id", "question_id", "option_ids", "selected_option_id",
            "resume_transition", "interaction_id",
        }
        if not isinstance(answer, dict) or not answer_keys <= set(answer):
            raise ContractError("invalid_required_answer", "answer_required result lacks stable identity")
        if (
            not isinstance(answer["decision_id"], str)
            or not answer["decision_id"].strip()
            or not isinstance(answer["question_id"], str)
            or not answer["question_id"].strip()
            or not isinstance(answer["resume_transition"], str)
            or not answer["resume_transition"].strip()
            or not answer["option_ids"]
        ):
            raise ContractError("invalid_required_answer", "answer_required result lacks stable identity")
        if (
            not isinstance(answer["option_ids"], list)
            or any(not isinstance(item, str) or not item.strip() for item in answer["option_ids"])
            or len(answer["option_ids"]) != len(set(answer["option_ids"]))
        ):
            raise ContractError("invalid_required_answer", "answer_required option_ids must be unique non-empty IDs")
        if answer["selected_option_id"] is not None and answer["selected_option_id"] not in answer["option_ids"]:
            raise ContractError("invalid_required_answer", "selected option ID is not one of the stable options")
        if blocker != {"code": None, "summary": None}:
            raise ContractError("invalid_result", "answer_required result cannot also claim a blocker")
    else:
        if value["required_answer"] != empty_required_answer():
            raise ContractError("invalid_result", "non-answer result must contain the canonical empty required_answer")
        if status == "blocked" and (not blocker["code"] or not blocker["summary"]):
            raise ContractError("invalid_result", "blocked result requires a stable blocker code and summary")
        if status == "succeeded" and blocker != {"code": None, "summary": None}:
            raise ContractError("invalid_result", "succeeded result cannot contain blocker data")
    return value


def validate_manifest(manifest: Any, expected_digest: Any) -> None:
    value = require_object(manifest, {"schema", "specPath", "artifacts", "validation", "digestSha256"}, "spec.packageManifest")
    if value["schema"] != "recommend-package-manifest-v1":
        raise ContractError("invalid_state", "unsupported package manifest schema")
    require_string(value["specPath"], "spec.packageManifest.specPath")
    if not isinstance(value["artifacts"], list) or not value["artifacts"]:
        raise ContractError("invalid_state", "spec.packageManifest.artifacts must be a non-empty list")
    paths: list[str] = []
    immutable: list[dict[str, str]] = []
    for index, raw in enumerate(value["artifacts"]):
        artifact = require_object(
            raw,
            {"path", "immutableProjectionSha256", "byteSha256AtLock", "projectionRule"},
            f"spec.packageManifest.artifacts[{index}]",
        )
        for field in ("path", "projectionRule"):
            require_string(artifact[field], f"artifact.{field}")
        for field in ("immutableProjectionSha256", "byteSha256AtLock"):
            if not isinstance(artifact[field], str) or not HEX_RE.fullmatch(artifact[field]):
                raise ContractError("invalid_state", f"artifact.{field} must be lowercase SHA-256")
        paths.append(artifact["path"])
        immutable.append({
            "path": artifact["path"],
            "immutableProjectionSha256": artifact["immutableProjectionSha256"],
            "projectionRule": artifact["projectionRule"],
        })
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ContractError("invalid_state", "package artifact paths must be unique and sorted")
    validation = require_object(
        value["validation"],
        {
            "contractLocked", "requiredFilesPresent", "storiesParseable",
            "acceptanceCriteriaValid", "tasksValid", "dagAcyclic",
            "readmeConsistent", "unresolvedUnplannedCount",
        },
        "spec.packageManifest.validation",
    )
    for field in (
        "contractLocked", "requiredFilesPresent", "storiesParseable",
        "acceptanceCriteriaValid", "tasksValid", "dagAcyclic", "readmeConsistent",
    ):
        if validation[field] is not True:
            raise ContractError("invalid_state", f"package validation {field} must be true")
    if validation["unresolvedUnplannedCount"] != 0:
        raise ContractError("invalid_state", "package validation unresolvedUnplannedCount must be zero")
    identity = {"schema": value["schema"], "specPath": value["specPath"], "artifacts": immutable}
    computed = digest_json(identity)
    if value["digestSha256"] != computed or expected_digest != computed:
        raise ContractError("invalid_state", "package manifest immutable digest is invalid")


def validate_state_shape(state: dict[str, Any]) -> None:
    required_top = {
        "schema", "schemaVersion", "executionId", "revision", "createdAt", "updatedAt",
        "entrypoint", "spec", "repository", "mode", "status", "resumeTarget",
        "blocked", "requiredAnswer", "storyExecution", "worktrees", "delivery", "transitions",
    }
    require_object(state, required_top, "state")
    schema = state.get("schema")
    version = state.get("schemaVersion")
    if not isinstance(schema, str) or not isinstance(version, int):
        raise ContractError("unsupported_schema", "schema and schemaVersion must identify a supported major")
    schema_major = re.fullmatch(r"recommend-execution-v(\d+)", schema)
    if not schema_major or int(schema_major.group(1)) != version or version != 1:
        raise ContractError("unsupported_schema", "only recommend-execution-v1 major 1 is supported")
    require_string(state["executionId"], "executionId")
    if isinstance(state["revision"], bool) or not isinstance(state["revision"], int) or state["revision"] < 1:
        raise ContractError("invalid_revision", "state revision must be a positive integer")
    for field in ("createdAt", "updatedAt"):
        require_string(state[field], field)

    entrypoint = require_object(
        state["entrypoint"], {"command", "sourceMode", "recommend", "resumeRequested"}, "entrypoint"
    )
    if entrypoint["command"] not in {"create-spec", "implement-spec"}:
        raise ContractError("invalid_state", "entrypoint.command is invalid")
    if entrypoint["sourceMode"] not in {"standard", "from-issue", "from-prototype", "existing-spec"}:
        raise ContractError("invalid_state", "entrypoint.sourceMode is invalid")
    if entrypoint["recommend"] is not True or not isinstance(entrypoint["resumeRequested"], bool):
        raise ContractError("invalid_state", "entrypoint recommendation fields are invalid")

    spec = require_object(
        state["spec"],
        {
            "id", "path", "packageManifest", "packageManifestSha256",
            "recommendationLog", "specLiteAmendments",
        },
        "spec",
    )
    require_string(spec["id"], "spec.id")
    require_string(spec["path"], "spec.path")
    validate_manifest(spec["packageManifest"], spec["packageManifestSha256"])
    log = require_object(
        spec["recommendationLog"],
        {"path", "revision", "digestSha256", "entryIds", "entryDigests", "pendingEntryIds", "lastReconciledAt"},
        "spec.recommendationLog",
    )
    require_string(log["path"], "spec.recommendationLog.path")
    if isinstance(log["revision"], bool) or not isinstance(log["revision"], int) or log["revision"] < 1:
        raise ContractError("invalid_state", "recommendation log revision must be positive")
    if not isinstance(log["digestSha256"], str) or not HEX_RE.fullmatch(log["digestSha256"]):
        raise ContractError("invalid_state", "recommendation log digest must be lowercase SHA-256")
    require_string_list(log["entryIds"], "spec.recommendationLog.entryIds")
    require_string_list(log["pendingEntryIds"], "spec.recommendationLog.pendingEntryIds")
    if not set(log["pendingEntryIds"]) <= set(log["entryIds"]):
        raise ContractError("invalid_state", "pending recommendation IDs must be known entries")
    if not isinstance(log["entryDigests"], dict) or set(log["entryDigests"]) != set(log["entryIds"]):
        raise ContractError("invalid_state", "recommendation entry digests must exactly cover entry IDs")
    if any(not isinstance(item, str) or not HEX_RE.fullmatch(item) for item in log["entryDigests"].values()):
        raise ContractError("invalid_state", "recommendation entry digests must be SHA-256")
    require_string(log["lastReconciledAt"], "spec.recommendationLog.lastReconciledAt")
    amendments = require_object(
        spec["specLiteAmendments"],
        {
            "path", "baselineSha256", "currentSha256", "driftLogPath",
            "baselineDriftEntryIds", "baselineDriftEntryDigests", "amendments",
        },
        "spec.specLiteAmendments",
    )
    for field in ("path", "driftLogPath"):
        require_string(amendments[field], f"spec.specLiteAmendments.{field}")
    for field in ("baselineSha256", "currentSha256"):
        if not isinstance(amendments[field], str) or not HEX_RE.fullmatch(amendments[field]):
            raise ContractError("invalid_state", f"spec.specLiteAmendments.{field} must be SHA-256")
    require_string_list(amendments["baselineDriftEntryIds"], "spec.specLiteAmendments.baselineDriftEntryIds")
    if (
        not isinstance(amendments["baselineDriftEntryDigests"], dict)
        or set(amendments["baselineDriftEntryDigests"]) != set(amendments["baselineDriftEntryIds"])
        or any(not isinstance(value, str) or not HEX_RE.fullmatch(value)
               for value in amendments["baselineDriftEntryDigests"].values())
    ):
        raise ContractError("invalid_state", "baseline drift entry digests must exactly cover baseline IDs")
    if not isinstance(amendments["amendments"], list):
        raise ContractError("invalid_state", "spec.specLiteAmendments.amendments must be a list")
    amendment_ids: list[str] = []
    for index, raw in enumerate(amendments["amendments"]):
        amendment = require_object(
            raw,
            {
                "devId", "priorSha256", "resultingSha256", "storyId", "path",
                "driftEntrySha256", "reviewResult", "reviewResultSha256", "recordedAt",
            },
            f"spec.specLiteAmendments.amendments[{index}]",
        )
        for field in ("devId", "storyId", "path", "recordedAt"):
            require_string(amendment[field], f"spec-lite amendment {field}")
        for field in ("priorSha256", "resultingSha256", "driftEntrySha256", "reviewResultSha256"):
            if not isinstance(amendment[field], str) or not HEX_RE.fullmatch(amendment[field]):
                raise ContractError("invalid_state", f"spec-lite amendment {field} must be SHA-256")
        review = require_object(
            amendment["reviewResult"],
            {
                "schema", "execution_id", "story_id", "outcome",
                "drift_severity", "dev_ids", "summary",
            },
            f"spec-lite amendment reviewResult[{index}]",
        )
        if (
            review["schema"] != "recommend-spec-lite-review-v1"
            or review["execution_id"] != state["executionId"]
            or review["story_id"] != amendment["storyId"]
            or review["outcome"] != "passed"
            or review["drift_severity"] != "small"
        ):
            raise ContractError("invalid_state", "spec-lite amendment review result identity is invalid")
        require_string_list(review["dev_ids"], "spec-lite amendment reviewResult.dev_ids")
        require_string(review["summary"], "spec-lite amendment reviewResult.summary")
        if amendment["devId"] not in review["dev_ids"] or digest_json(review) != amendment["reviewResultSha256"]:
            raise ContractError("invalid_state", "spec-lite amendment review result binding is invalid")
        amendment_ids.append(amendment["devId"])
    if len(amendment_ids) != len(set(amendment_ids)):
        raise ContractError("invalid_state", "spec-lite amendment DEV IDs must be unique")

    repository = require_object(
        state["repository"],
        {
            "rootIdentity", "remoteName", "remoteIdentity", "featureBranch",
            "startingHeadSha", "currentHeadSha", "ownedPathWorktreeSnapshot",
        },
        "repository",
    )
    require_string(repository["rootIdentity"], "repository.rootIdentity")
    require_string(repository["remoteName"], "repository.remoteName", nullable=True)
    require_string(repository["remoteIdentity"], "repository.remoteIdentity", nullable=True)
    require_string(repository["featureBranch"], "repository.featureBranch")
    for field in ("startingHeadSha", "currentHeadSha"):
        if not isinstance(repository[field], str) or not GIT_SHA_RE.fullmatch(repository[field]):
            raise ContractError("invalid_state", f"repository.{field} must be a full lowercase git object ID")
    snapshot = require_object(repository["ownedPathWorktreeSnapshot"], {"capturedAt", "headSha", "entries"}, "repository.ownedPathWorktreeSnapshot")
    require_string(snapshot["capturedAt"], "repository.ownedPathWorktreeSnapshot.capturedAt")
    if not isinstance(snapshot["headSha"], str) or not GIT_SHA_RE.fullmatch(snapshot["headSha"]):
        raise ContractError("invalid_state", "owned-path snapshot head must be a full git object ID")
    if not isinstance(snapshot["entries"], list):
        raise ContractError("invalid_state", "owned-path snapshot entries must be a list")

    mode = require_object(state["mode"], {"name", "propagationToken", "returnContract"}, "mode")
    if mode["name"] != "recommend" or mode["returnContract"] != RESULT_SCHEMA:
        raise ContractError("invalid_state", "mode contract is invalid")
    require_string(mode["propagationToken"], "mode.propagationToken")
    if state["status"] not in STATE_STATUSES or state["resumeTarget"] not in STATE_STATUSES:
        raise ContractError("invalid_state", "status or resumeTarget is invalid")

    blocked = require_object(
        state["blocked"],
        {"active", "code", "summary", "operation", "recoverable", "resumeFrom", "firstObservedAt", "lastObservedAt"},
        "blocked",
    )
    if not isinstance(blocked["active"], bool) or not isinstance(blocked["recoverable"], bool):
        raise ContractError("invalid_state", "blocked flags must be booleans")
    for field in ("code", "summary", "operation", "resumeFrom", "firstObservedAt", "lastObservedAt"):
        require_string(blocked[field], f"blocked.{field}", nullable=True)

    answer = require_object(
        state["requiredAnswer"],
        {"active", "decisionId", "questionId", "optionIds", "selectedOptionId", "resumeTransition", "interactionId"},
        "requiredAnswer",
    )
    if not isinstance(answer["active"], bool):
        raise ContractError("invalid_state", "requiredAnswer.active must be boolean")
    require_string_list(answer["optionIds"], "requiredAnswer.optionIds")
    for field in ("decisionId", "questionId", "selectedOptionId", "resumeTransition", "interactionId"):
        require_string(answer[field], f"requiredAnswer.{field}", nullable=True)
    if answer["active"] and (
        not answer["decisionId"] or not answer["questionId"] or not answer["optionIds"] or not answer["resumeTransition"]
    ):
        raise ContractError("invalid_state", "active required answer lacks stable identity")

    story = require_object(
        state["storyExecution"],
        {
            "executionStatePath", "planDigest", "baselineCompletedStoryIds",
            "completedStoryIds", "activeStoryIds", "failedStoryIds", "storyResults",
            "integrationVerification",
        },
        "storyExecution",
    )
    require_string(story["executionStatePath"], "storyExecution.executionStatePath", nullable=True)
    if story["planDigest"] is not None and (not isinstance(story["planDigest"], str) or not HEX_RE.fullmatch(story["planDigest"])):
        raise ContractError("invalid_state", "storyExecution.planDigest must be SHA-256 or null")
    for field in ("baselineCompletedStoryIds", "completedStoryIds", "activeStoryIds", "failedStoryIds"):
        require_string_list(story[field], f"storyExecution.{field}")
    if not isinstance(story["storyResults"], dict):
        raise ContractError("invalid_state", "storyExecution.storyResults must be an object")
    for story_id, result in story["storyResults"].items():
        require_string(story_id, "storyExecution.storyResults key")
        try:
            nested = validate_command_result(result, expected_execution_id=state["executionId"])
        except ContractError as exc:
            raise ContractError(
                "invalid_state",
                f"storyExecution.storyResults.{story_id} violates result contract: {exc.message}",
            ) from exc
        if nested["command"] != "implement-story" or nested["identifiers"].get("story_id") != story_id:
            raise ContractError("invalid_state", f"storyExecution.storyResults.{story_id} violates story identity")
    integration = require_object(
        story["integrationVerification"],
        {
            "status", "headSha", "packageManifestSha256", "planDigest",
            "completedStoryIds", "command", "exitCode", "completedAt",
            "evidenceSummary", "evidenceArtifact", "evidenceArtifactSha256",
        },
        "storyExecution.integrationVerification",
    )
    if integration["status"] not in {"not_started", "passed", "blocked"}:
        raise ContractError("invalid_state", "integration verification status is invalid")
    for field in (
        "headSha", "packageManifestSha256", "planDigest", "command", "completedAt",
        "evidenceSummary", "evidenceArtifact", "evidenceArtifactSha256",
    ):
        require_string(integration[field], f"integrationVerification.{field}", nullable=True)
    require_string_list(integration["completedStoryIds"], "integrationVerification.completedStoryIds")
    if integration["exitCode"] is not None and (
        isinstance(integration["exitCode"], bool) or not isinstance(integration["exitCode"], int)
    ):
        raise ContractError("invalid_state", "integrationVerification.exitCode must be an integer or null")

    if not isinstance(state["worktrees"], dict):
        raise ContractError("invalid_worktrees", "worktrees must be a map")
    for key, raw in state["worktrees"].items():
        require_string(key, "worktree key")
        record = require_object(
            raw,
            {
                "storyId", "delegatedExecutionId", "ownershipToken", "path", "branchRef",
                "headSha", "status", "activeGate", "activeStoryId", "startingSha",
                "currentSha", "adoptionState", "adoptionEvidence", "mergeEvidence",
                "launchMode", "parentExecutionId", "resultDigestSha256",
                "reservedAt", "updatedAt",
            },
            f"worktrees.{key}",
        )
        for field in (
            "storyId", "delegatedExecutionId", "ownershipToken", "path", "branchRef",
            "activeGate", "activeStoryId", "adoptionState", "launchMode",
            "parentExecutionId", "reservedAt", "updatedAt",
        ):
            require_string(record[field], f"worktrees.{key}.{field}")
        if record["launchMode"] not in {"linked_worktree", "serial_in_place"}:
            raise ContractError("invalid_worktrees", f"worktrees.{key}.launchMode is invalid")
        if record["parentExecutionId"] != state["executionId"]:
            raise ContractError("invalid_worktrees", f"worktrees.{key}.parentExecutionId is invalid")
        if record["resultDigestSha256"] is not None and (
            not isinstance(record["resultDigestSha256"], str)
            or not HEX_RE.fullmatch(record["resultDigestSha256"])
        ):
            raise ContractError("invalid_worktrees", f"worktrees.{key}.resultDigestSha256 is invalid")
        for field in ("headSha", "startingSha", "currentSha"):
            if not isinstance(record[field], str) or not GIT_SHA_RE.fullmatch(record[field]):
                raise ContractError("invalid_worktrees", f"worktrees.{key}.{field} must be a full git object ID")
        if record["status"] not in WORKTREE_STATUSES:
            raise ContractError("invalid_worktrees", f"worktrees.{key}.status is invalid")
        adoption = require_object(record["adoptionEvidence"], {"adoptedAt", "path", "headSha"}, f"worktrees.{key}.adoptionEvidence")
        for field in ("adoptedAt", "path", "headSha"):
            require_string(adoption[field], f"worktrees.{key}.adoptionEvidence.{field}", nullable=True)
        merge = require_object(
            record["mergeEvidence"],
            {"status", "sourceHeadSha", "targetHeadSha", "resultDigestSha256", "observedAt"},
            f"worktrees.{key}.mergeEvidence",
        )
        if merge["status"] not in {"not_started", "integrated"}:
            raise ContractError("invalid_worktrees", f"worktrees.{key}.mergeEvidence.status is invalid")
        for field in ("sourceHeadSha", "targetHeadSha", "resultDigestSha256", "observedAt"):
            require_string(merge[field], f"worktrees.{key}.mergeEvidence.{field}", nullable=True)
        if merge["status"] == "integrated" and not all(
            merge[field] for field in ("sourceHeadSha", "targetHeadSha", "resultDigestSha256", "observedAt")
        ):
            raise ContractError("invalid_worktrees", f"worktrees.{key}.mergeEvidence is incomplete")

    delivery = require_object(
        state["delivery"], {"pr", "checks", "preview", "approval", "merge", "release"}, "delivery"
    )
    if not isinstance(delivery["checks"], list):
        raise ContractError("invalid_state", "delivery.checks must be a list")
    staging_active = "capabilitySnapshot" in delivery
    if not staging_active:
        if any(delivery[field] is not None for field in ("pr", "preview", "approval", "merge", "release")) or delivery["checks"]:
            raise ContractError("invalid_state", "delivery fields require an activated Story 4 staging snapshot")
    else:
        require_object(
            delivery["capabilitySnapshot"],
            {"schema", "provider", "repositoryId", "sourceRemote", "sourceIdentity",
             "baseBranch", "featureBranch", "headSha", "capabilities", "config", "capturedAt"},
            "delivery.capabilitySnapshot",
        )
        if delivery["capabilitySnapshot"]["schema"] != "recommend-provider-capabilities-v1":
            raise ContractError("invalid_state", "delivery capability snapshot schema is invalid")
        if not isinstance(delivery.get("operations"), dict):
            raise ContractError("invalid_state", "delivery.operations must be an object")
        if delivery.get("uat") is not None and not isinstance(delivery["uat"], dict):
            raise ContractError("invalid_state", "delivery.uat must be an object or null")
        # merge/release fields are inert until Story 5 states are reached
        # Also allow when blocked with a Story 5 resumeTarget (stage_block changes status to blocked)
        s5_active = (
            state.get("status") in STORY5_STATUSES
            or (state.get("status") == "blocked" and state.get("resumeTarget") in STORY5_STATUSES)
        )
        if not s5_active:
            if delivery["merge"] is not None or delivery["release"] is not None:
                raise ContractError("invalid_state", "Story 5 merge and release fields must remain inert")
    if not isinstance(state["transitions"], list):
        raise ContractError("invalid_state", "transitions must be a list")
    previous_sequence = 0
    for index, raw in enumerate(state["transitions"]):
        transition = require_object(
            raw,
            {
                "sequence", "from", "to", "startedAt", "completedAt", "attempt",
                "operationKey", "evidenceSummary", "persistedIdentifiers", "outcome",
            },
            f"transitions[{index}]",
        )
        sequence = transition["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence != previous_sequence + 1:
            raise ContractError("invalid_state", "transition sequences must be contiguous positive integers")
        previous_sequence = sequence
        if transition["from"] not in STATE_STATUSES | {"entry"} or transition["to"] not in STATE_STATUSES:
            raise ContractError("invalid_state", f"transitions[{index}] has an invalid state token")
        for field in ("startedAt", "completedAt", "operationKey", "evidenceSummary"):
            require_string(transition[field], f"transitions[{index}].{field}", nullable=field == "completedAt")
        if isinstance(transition["attempt"], bool) or not isinstance(transition["attempt"], int) or transition["attempt"] < 1:
            raise ContractError("invalid_state", f"transitions[{index}].attempt must be positive")
        require_string_list(transition["persistedIdentifiers"], f"transitions[{index}].persistedIdentifiers")
        if transition["outcome"] not in {"pending", "succeeded", "blocked"}:
            raise ContractError("invalid_state", f"transitions[{index}].outcome is invalid")


def replace_state(path: Path, state: dict[str, Any], expected_digest: str | None = None) -> None:
    if expected_digest is not None:
        try:
            current_digest = digest_bytes(path.read_bytes())
        except OSError as exc:
            raise ContractError("state_missing", f"state disappeared before replacement: {path}") from exc
        if current_digest != expected_digest:
            raise ContractError("stale_state_writer", "canonical state changed after it was read")
    state["revision"] += 1
    state["updatedAt"] = now()
    validate_state_shape(state)
    atomic_write_json(path, state)


def reconcile_log(saved: dict[str, Any], observed: dict[str, Any]) -> str:
    saved_ids = saved["entryIds"]
    observed_ids = observed["entryIds"]
    if observed_ids[:len(saved_ids)] != saved_ids:
        raise ContractError("recommendation_log_contradiction", "entry identity was rewritten, removed, or reordered")
    changed = [
        entry_id for entry_id in saved_ids
        if saved["entryDigests"].get(entry_id) != observed["entryDigests"].get(entry_id)
    ]
    unauthorized = [entry_id for entry_id in changed if entry_id not in saved.get("pendingEntryIds", [])]
    if unauthorized:
        raise ContractError("recommendation_log_contradiction", f"terminal entry changed: {unauthorized}")
    if changed and len(observed_ids) > len(saved_ids):
        raise ContractError("recommendation_log_contradiction", "pending finalization and append must be separate revisions")
    if changed:
        still_pending = [entry_id for entry_id in changed if entry_id in observed.get("pendingEntryIds", [])]
        if still_pending:
            raise ContractError("recommendation_log_contradiction", f"pending entry changed without finalization: {still_pending}")
        return "pending_finalized"
    if len(observed_ids) == len(saved_ids) and observed["digestSha256"] != saved["digestSha256"]:
        raise ContractError("recommendation_log_contradiction", "log digest changed without a valid append")
    return "append_adopted" if len(observed_ids) > len(saved_ids) else "matched"


def git_worktrees(repo: Path) -> list[dict[str, str | None]]:
    output = git(repo, "worktree", "list", "--porcelain")
    records: list[dict[str, str | None]] = []
    current: dict[str, str | None] = {}
    for line in output.splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = str(Path(value).resolve())
        elif key == "HEAD":
            current["headSha"] = value
        elif key == "branch":
            current["branchRef"] = value
    return records


def worktree_key(story_id: str, delegated_id: str, token: str) -> str:
    safe = re.compile(r"^[A-Za-z0-9._-]+$")
    for value in (story_id, delegated_id, token):
        if not safe.fullmatch(value):
            raise ContractError("invalid_worktree_identity", "worktree identity components must be filesystem-safe")
    return f"{story_id}::{delegated_id}::{token}"


def validate_worktree_ownership(state: dict[str, Any], observed: list[dict[str, str | None]]) -> dict[str, dict[str, Any]]:
    ownership_fields = ("storyId", "path", "branchRef", "delegatedExecutionId", "ownershipToken")
    ownership: dict[str, dict[str, list[str]]] = {field: {} for field in ownership_fields}
    for key, record in state["worktrees"].items():
        if record.get("status") not in ACTIVE_WORKTREE_STATUSES:
            continue
        for field in ownership_fields:
            value = str(Path(record[field]).resolve()) if field == "path" else record[field]
            ownership[field].setdefault(value, []).append(key)
    duplicates = {
        field: {value: keys for value, keys in values.items() if len(keys) > 1}
        for field, values in ownership.items()
    }
    duplicates = {field: values for field, values in duplicates.items() if values}
    if duplicates:
        raise ContractError("worktree_ownership_ambiguous", f"duplicate ownership: {duplicates}")
    adopted: dict[str, dict[str, Any]] = {}
    for key, record in state["worktrees"].items():
        if record.get("status") not in ACTIVE_WORKTREE_STATUSES:
            continue
        path = str(Path(record["path"]).resolve())
        candidates = [item for item in observed if item.get("path") == path]
        if not candidates:
            raise ContractError("stranded_worktree_missing", f"active worktree is missing: {path}")
        if len(candidates) != 1:
            raise ContractError("worktree_ownership_ambiguous", f"multiple worktrees match {path}")
        candidate = candidates[0]
        if candidate.get("branchRef") != record.get("branchRef"):
            raise ContractError("worktree_identity_contradiction", f"branch mismatch for {key}")
        if candidate.get("headSha") != record.get("currentSha"):
            raise ContractError("worktree_identity_stale", f"HEAD mismatch for {key}")
        adopted[key] = candidate
    return adopted


def start(args: argparse.Namespace) -> dict[str, Any]:
    invocation = parse_invocation(args.entry_command, json.loads(args.invocation_json))
    if invocation["mode"] == "normal":
        return invocation
    repo = Path(args.repo).resolve()
    state_path = Path(args.state).resolve()
    try:
        canonical_state_path = state_path.relative_to(repo).as_posix()
    except ValueError as exc:
        raise ContractError("invalid_state_path", "state path must be inside repository") from exc
    manifest, log, story_facts = validate_package(repo, args.spec)
    identity = repo_identity(repo)
    if identity["branchRef"] is None:
        raise ContractError("repository_identity_mismatch", "recommended execution cannot start from detached HEAD")
    spec_lite_path = (repo / args.spec / "spec-lite.md").resolve()
    spec_lite_relative = spec_lite_path.relative_to(repo).as_posix()
    spec_lite_digest = digest_bytes(spec_lite_path.read_bytes())
    drift_log_path = (repo / args.spec / "drift-log.md").resolve()
    baseline_drift = parse_drift_log(drift_log_path)
    state = {
        "schema": SCHEMA,
        "schemaVersion": 1,
        "executionId": args.execution_id,
        "revision": 1,
        "createdAt": now(),
        "updatedAt": now(),
        "entrypoint": {**invocation, "recommend": True, "resumeRequested": False},
        "spec": {
            "id": Path(args.spec).name,
            "path": Path(args.spec).as_posix(),
            "packageManifest": manifest,
            "packageManifestSha256": manifest["digestSha256"],
            "recommendationLog": {**log, "revision": 1, "lastReconciledAt": now()},
            "specLiteAmendments": {
                "path": spec_lite_relative,
                "baselineSha256": spec_lite_digest,
                "currentSha256": spec_lite_digest,
                "driftLogPath": drift_log_path.relative_to(repo).as_posix(),
                "baselineDriftEntryIds": baseline_drift["entryIds"],
                "baselineDriftEntryDigests": baseline_drift["entryDigests"],
                "amendments": [],
            },
        },
        "repository": {
            "rootIdentity": identity["root"],
            "remoteName": identity["remoteName"],
            "remoteIdentity": identity["remoteIdentity"],
            "featureBranch": identity["branchRef"],
            "startingHeadSha": identity["headSha"],
            "currentHeadSha": identity["headSha"],
            "ownedPathWorktreeSnapshot": {
                "capturedAt": now(),
                "headSha": identity["headSha"],
                "entries": [],
            },
        },
        "mode": {"name": "recommend", "propagationToken": args.token, "returnContract": RESULT_SCHEMA},
        "status": "planning" if args.entry_command == "create-spec" else "implementing",
        "resumeTarget": "implementing",
        "blocked": {
            "active": False, "code": None, "summary": None, "operation": None,
            "recoverable": False, "resumeFrom": None, "firstObservedAt": None,
            "lastObservedAt": None,
        },
        "requiredAnswer": {
            "active": False, "decisionId": None, "questionId": None, "optionIds": [],
            "selectedOptionId": None, "resumeTransition": None, "interactionId": None,
        },
        "storyExecution": {
            "executionStatePath": None,
            "planDigest": None,
            "baselineCompletedStoryIds": [
                story_id for story_id, facts in story_facts.items()
                if facts["status"] == "Completed"
            ],
            "completedStoryIds": [
                story_id for story_id, facts in story_facts.items()
                if facts["status"] == "Completed"
            ],
            "activeStoryIds": [], "failedStoryIds": [], "storyResults": {},
            "integrationVerification": {
                "status": "not_started", "headSha": None,
                "packageManifestSha256": None, "planDigest": None,
                "completedStoryIds": [], "command": None, "exitCode": None,
                "completedAt": None, "evidenceSummary": None,
                "evidenceArtifact": None, "evidenceArtifactSha256": None,
            },
        },
        "worktrees": {},
        "delivery": {"pr": None, "checks": [], "preview": None, "approval": None, "merge": None, "release": None},
        "transitions": [],
    }
    validate_state_shape(state)
    atomic_write_json(state_path, state, exclusive=True)
    return {
        "schema": "recommend-start-result-v1",
        "delivery_context": {
            "execution_id": args.execution_id,
            "state_path": canonical_state_path,
            "spec_path": Path(args.spec).as_posix(),
            "mode": "recommend",
            "propagation_token": args.token,
            "parent_command": args.entry_command,
            "return_contract": RESULT_SCHEMA,
            "package_manifest_sha256": manifest["digestSha256"],
        },
    }


def validate_context(args: argparse.Namespace) -> dict[str, Any]:
    state = read_json(Path(args.state))
    validate_state_shape(state)
    context = read_json(Path(args.context))
    repo_root = Path(state["repository"]["rootIdentity"])
    try:
        canonical_state_path = Path(args.state).resolve().relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ContractError("invalid_state_path", "state path must be inside canonical repository") from exc
    expected = {
        "execution_id": state["executionId"],
        "state_path": canonical_state_path,
        "spec_path": state["spec"]["path"],
        "mode": "recommend",
        "propagation_token": state["mode"]["propagationToken"],
        "parent_command": state["entrypoint"]["command"],
        "return_contract": RESULT_SCHEMA,
        "package_manifest_sha256": state["spec"]["packageManifestSha256"],
    }
    mismatches = [key for key, value in expected.items() if context.get(key) != value]
    if mismatches:
        raise ContractError("delivery_context_mismatch", f"context mismatch: {mismatches}")
    return {"schema": "recommend-context-validation-v1", "status": "valid"}


def reserve_worktree(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    expected_digest = digest_bytes(state_path.read_bytes())
    state = read_json(state_path)
    validate_state_shape(state)
    repo = Path(args.repo).resolve()
    if str(repo) != state["repository"]["rootIdentity"]:
        raise ContractError("repository_identity_mismatch", "reservation repository root differs from state")
    parent_identity = repo_identity(repo)
    if (
        parent_identity["branchRef"] != state["repository"]["featureBranch"]
        or parent_identity["remoteName"] != state["repository"]["remoteName"]
        or parent_identity["remoteIdentity"] != state["repository"]["remoteIdentity"]
    ):
        raise ContractError("repository_identity_mismatch", "repository identity changed before reservation")
    launch = read_json(Path(args.launch_result))
    required = {
        "schema", "execution_id", "story_id", "delegated_execution_id",
        "ownership_token", "path", "branch_ref", "head_sha", "starting_sha",
        "active_gate", "mode",
    }
    if required - set(launch):
        raise ContractError("invalid_worktree_launch", f"launch result missing: {sorted(required - set(launch))}")
    if launch["schema"] != LAUNCH_SCHEMA or launch["execution_id"] != state["executionId"]:
        raise ContractError("invalid_worktree_launch", "launch schema/execution does not match state")
    if launch["mode"] not in {"linked_worktree", "serial_in_place"}:
        raise ContractError("invalid_worktree_launch", "unsupported worktree launch mode")
    story_id = launch["story_id"]
    delegated_execution_id = launch["delegated_execution_id"]
    ownership_token = launch["ownership_token"]
    key = worktree_key(story_id, delegated_execution_id, ownership_token)
    existing_active = [
        name for name, record in state["worktrees"].items()
        if record.get("storyId") == story_id and record.get("status") in ACTIVE_WORKTREE_STATUSES and name != key
    ]
    if existing_active:
        raise ContractError("worktree_ownership_ambiguous", f"{story_id} already has active ownership: {existing_active}")
    observed = git_worktrees(repo)
    path = str(Path(launch["path"]).resolve())
    for name, record in state["worktrees"].items():
        if record.get("status") not in ACTIVE_WORKTREE_STATUSES or name == key:
            continue
        conflicts = {
            "path": str(Path(record["path"]).resolve()) == path,
            "branchRef": record.get("branchRef") == launch["branch_ref"],
            "delegatedExecutionId": record.get("delegatedExecutionId") == delegated_execution_id,
            "ownershipToken": record.get("ownershipToken") == ownership_token,
        }
        if any(conflicts.values()):
            raise ContractError("worktree_ownership_ambiguous", f"launch ownership conflicts with {name}: {conflicts}")
    matches = [record for record in observed if record.get("path") == path]
    if len(matches) != 1:
        raise ContractError("worktree_identity_unavailable", f"expected one observable worktree at {path}, got {len(matches)}")
    match = matches[0]
    if match.get("branchRef") != launch["branch_ref"] or match.get("headSha") != launch["head_sha"]:
        raise ContractError("worktree_identity_contradiction", "launch result does not match git worktree identity")
    if launch["starting_sha"] != launch["head_sha"]:
        raise ContractError("invalid_worktree_launch", "launch starting SHA must equal observed launch HEAD")
    canonical_root = str(Path(state["repository"]["rootIdentity"]).resolve())
    if launch["mode"] == "serial_in_place":
        if path != canonical_root or launch["branch_ref"] != state["repository"]["featureBranch"]:
            raise ContractError(
                "invalid_worktree_launch",
                "serial in-place launch must bind the canonical root and feature branch",
            )
    elif path == canonical_root:
        raise ContractError("invalid_worktree_launch", "linked-worktree launch cannot claim the canonical root")
    timestamp = now()
    state["worktrees"][key] = {
        "storyId": story_id,
        "delegatedExecutionId": delegated_execution_id,
        "ownershipToken": ownership_token,
        "path": path,
        "branchRef": launch["branch_ref"],
        "headSha": launch["head_sha"],
        "launchMode": launch["mode"],
        "parentExecutionId": state["executionId"],
        "resultDigestSha256": None,
        "status": "reserved",
        "activeGate": launch["active_gate"],
        "activeStoryId": story_id,
        "startingSha": launch["starting_sha"],
        "currentSha": launch["head_sha"],
        "adoptionState": "not_required",
        "adoptionEvidence": {"adoptedAt": None, "path": None, "headSha": None},
        "mergeEvidence": {
            "status": "not_started", "sourceHeadSha": None,
            "targetHeadSha": None, "resultDigestSha256": None, "observedAt": None,
        },
        "reservedAt": timestamp,
        "updatedAt": timestamp,
    }
    replace_state(state_path, state, expected_digest)
    return {
        "schema": ACK_SCHEMA,
        "execution_id": state["executionId"],
        "worktree_key": key,
        "story_id": story_id,
        "persisted_revision": state["revision"],
        "status": "reserved",
    }


def safe_state_file(
    repo: Path,
    raw_path: str,
    location: str,
    code: str = "execution_state_contradiction",
) -> Path:
    if not isinstance(raw_path, str) or not raw_path or Path(raw_path).is_absolute():
        raise ContractError(code, f"{location} must be a repo-relative path")
    candidate = (repo / raw_path).resolve()
    state_root = (repo / ".writ/state").resolve()
    try:
        candidate.relative_to(state_root)
    except ValueError as exc:
        raise ContractError(code, f"{location} escapes .writ/state") from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise ContractError(code, f"{location} must identify an existing regular file")
    return candidate


def validate_spec_lite_amendments(
    repo: Path,
    state: dict[str, Any],
    observed_manifest: dict[str, Any],
) -> None:
    amendments_state = state["spec"]["specLiteAmendments"]
    spec_lite_path = (repo / amendments_state["path"]).resolve()
    try:
        spec_lite_path.relative_to((repo / state["spec"]["path"]).resolve())
    except ValueError as exc:
        raise ContractError(
            "spec_lite_amendment_contradiction",
            "spec-lite amendment path escapes the active spec",
        ) from exc
    expected_path = (repo / state["spec"]["path"] / "spec-lite.md").resolve()
    if spec_lite_path != expected_path or not spec_lite_path.is_file() or spec_lite_path.is_symlink():
        raise ContractError(
            "spec_lite_amendment_contradiction",
            "spec-lite amendment path must identify the active spec-lite.md",
        )
    current_digest = digest_bytes(spec_lite_path.read_bytes())
    prior = amendments_state["baselineSha256"]
    amended_ids: list[str] = []
    for amendment in amendments_state["amendments"]:
        if amendment["path"] != amendments_state["path"] or amendment["priorSha256"] != prior:
            raise ContractError(
                "spec_lite_amendment_contradiction",
                "spec-lite amendment chain is non-contiguous or targets another path",
            )
        prior = amendment["resultingSha256"]
        amended_ids.append(amendment["devId"])
    if amendments_state["currentSha256"] != prior or current_digest != prior:
        raise ContractError(
            "spec_lite_amendment_contradiction",
            "spec-lite amendment chain does not reach current bytes",
        )

    drift_path = (repo / amendments_state["driftLogPath"]).resolve()
    expected_drift_path = (repo / state["spec"]["path"] / "drift-log.md").resolve()
    if drift_path != expected_drift_path:
        raise ContractError("spec_lite_amendment_contradiction", "drift-log path is not canonical")
    observed_drift = parse_drift_log(drift_path)
    baseline_ids = amendments_state["baselineDriftEntryIds"]
    if observed_drift["entryIds"][:len(baseline_ids)] != baseline_ids:
        raise ContractError("spec_lite_amendment_contradiction", "baseline drift-log entries changed or reordered")
    for dev_id in baseline_ids:
        if observed_drift["entryDigests"].get(dev_id) != amendments_state["baselineDriftEntryDigests"].get(dev_id):
            raise ContractError("spec_lite_amendment_contradiction", f"baseline drift entry changed: {dev_id}")
    appended_ids = set(observed_drift["entryIds"][len(baseline_ids):])
    if any(dev_id not in appended_ids for dev_id in amended_ids):
        raise ContractError(
            "spec_lite_amendment_contradiction",
            "spec-lite amendment DEV IDs lack append-only drift-log entries",
        )
    for amendment in amendments_state["amendments"]:
        if observed_drift["entryDigests"].get(amendment["devId"]) != amendment["driftEntrySha256"]:
            raise ContractError(
                "spec_lite_amendment_contradiction",
                f"drift-log entry was rewritten: {amendment['devId']}",
            )

    expected_artifacts = {
        artifact["path"]: artifact for artifact in state["spec"]["packageManifest"]["artifacts"]
    }
    observed_artifacts = {
        artifact["path"]: artifact for artifact in observed_manifest["artifacts"]
    }
    if set(expected_artifacts) != set(observed_artifacts):
        raise ContractError("package_manifest_mismatch", "immutable package artifact paths changed")
    for path, expected in expected_artifacts.items():
        observed = observed_artifacts[path]
        if observed["projectionRule"] != expected["projectionRule"]:
            raise ContractError("package_manifest_mismatch", f"projection rule changed for {path}")
        if path == amendments_state["path"]:
            if (
                expected["byteSha256AtLock"] != amendments_state["baselineSha256"]
                or observed["immutableProjectionSha256"] != current_digest
            ):
                raise ContractError(
                    "spec_lite_amendment_contradiction",
                    "spec-lite baseline or current projection binding is invalid",
                )
        elif observed["immutableProjectionSha256"] != expected["immutableProjectionSha256"]:
            raise ContractError("package_manifest_mismatch", f"immutable package artifact changed: {path}")


def record_spec_lite_amendment(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    expected_digest = digest_bytes(state_path.read_bytes())
    state = read_json(state_path)
    validate_state_shape(state)
    repo = Path(args.repo).resolve()
    if str(repo) != state["repository"]["rootIdentity"]:
        raise ContractError("repository_identity_mismatch", "repository root differs from state")
    identity = repo_identity(repo)
    if (
        identity["branchRef"] != state["repository"]["featureBranch"]
        or identity["remoteName"] != state["repository"]["remoteName"]
        or identity["remoteIdentity"] != state["repository"]["remoteIdentity"]
    ):
        raise ContractError("repository_identity_mismatch", "repository identity changed before amendment recording")
    amendments_state = state["spec"]["specLiteAmendments"]
    if args.prior_sha256 != amendments_state["currentSha256"]:
        raise ContractError("spec_lite_amendment_contradiction", "amendment prior digest is stale")
    if not re.fullmatch(r"DEV-\d+", args.dev_id):
        raise ContractError("spec_lite_amendment_contradiction", "amendment DEV ID is invalid")
    known_ids = set(amendments_state["baselineDriftEntryIds"]) | {
        amendment["devId"] for amendment in amendments_state["amendments"]
    }
    if args.dev_id in known_ids:
        raise ContractError("spec_lite_amendment_contradiction", "amendment DEV ID is duplicate")
    review = read_json(Path(args.review_result))
    required_review = {
        "schema", "execution_id", "story_id", "outcome",
        "drift_severity", "dev_ids", "summary",
    }
    if required_review - set(review):
        raise ContractError("spec_lite_amendment_contradiction", "review result is incomplete")
    if (
        review["schema"] != "recommend-spec-lite-review-v1"
        or review["execution_id"] != state["executionId"]
        or review["story_id"] != args.story_id
        or review["outcome"] != "passed"
        or review["drift_severity"] != "small"
        or args.dev_id not in review.get("dev_ids", [])
        or not isinstance(review.get("summary"), str)
        or not review["summary"].strip()
    ):
        raise ContractError("spec_lite_amendment_contradiction", "review result does not authorize this amendment")
    require_string_list(review["dev_ids"], "review result dev_ids")
    spec_lite_path = repo / amendments_state["path"]
    resulting_digest = digest_bytes(spec_lite_path.read_bytes())
    if resulting_digest == args.prior_sha256:
        raise ContractError("spec_lite_amendment_contradiction", "amendment did not change spec-lite bytes")
    observed_drift = parse_drift_log(repo / amendments_state["driftLogPath"])
    drift_entry_digest = observed_drift["entryDigests"].get(args.dev_id)
    if drift_entry_digest is None:
        raise ContractError(
            "spec_lite_amendment_contradiction",
            "amendment DEV ID is not an append-only drift-log entry",
        )
    state["spec"]["specLiteAmendments"]["amendments"].append({
        "devId": args.dev_id,
        "priorSha256": args.prior_sha256,
        "resultingSha256": resulting_digest,
        "storyId": args.story_id,
        "path": amendments_state["path"],
        "driftEntrySha256": drift_entry_digest,
        "reviewResult": review,
        "reviewResultSha256": digest_json(review),
        "recordedAt": now(),
    })
    state["spec"]["specLiteAmendments"]["currentSha256"] = resulting_digest
    observed_manifest, _, _ = validate_package(repo, state["spec"]["path"])
    validate_spec_lite_amendments(repo, state, observed_manifest)
    replace_state(state_path, state, expected_digest)
    return {
        "schema": "recommend-spec-lite-amendment-result-v1",
        "status": "recorded",
        "dev_id": args.dev_id,
        "story_id": args.story_id,
        "resulting_sha256": resulting_digest,
        "revision": state["revision"],
    }


def canonical_plan_stories(
    plan: Any,
    all_story_ids: list[str],
    baseline_ids: set[str],
    story_facts: dict[str, dict[str, Any]],
) -> list[str]:
    value = require_object(plan, {"batches"}, "nested execution plan")
    if not isinstance(value["batches"], list):
        raise ContractError("plan_contradiction", "nested plan batches must be a list")
    planned: list[str] = []
    completed_batches = set(baseline_ids)
    for index, raw in enumerate(value["batches"]):
        batch = require_object(raw, {"parallel", "stories"}, f"nested plan batch {index}")
        if not isinstance(batch["parallel"], bool):
            raise ContractError("plan_contradiction", f"nested plan batch {index} parallel must be boolean")
        require_string_list(batch["stories"], f"nested plan batch {index} stories")
        if not batch["stories"]:
            raise ContractError("plan_contradiction", f"nested plan batch {index} must not be empty")
        for story_id in batch["stories"]:
            if story_id not in story_facts:
                raise ContractError("plan_contradiction", f"nested plan contains unknown story {story_id}")
            missing_dependencies = set(story_facts[story_id]["dependencies"]) - completed_batches
            if missing_dependencies:
                raise ContractError(
                    "plan_contradiction",
                    f"{story_id} is batched before dependencies {sorted(missing_dependencies)}",
                )
        planned.extend(batch["stories"])
        completed_batches.update(batch["stories"])
    expected = [story_id for story_id in all_story_ids if story_id not in baseline_ids]
    if len(planned) != len(set(planned)) or set(planned) != set(expected):
        raise ContractError("plan_contradiction", "nested plan must contain each non-baseline story exactly once")
    return planned


def reconcile_story_evidence(
    repo: Path,
    state: dict[str, Any],
    story_facts: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    observed_head: str,
) -> None:
    execution = state["storyExecution"]
    all_story_ids = list(story_facts)
    all_story_set = set(all_story_ids)
    baseline_ids = set(execution["baselineCompletedStoryIds"])
    if not baseline_ids <= all_story_set:
        raise ContractError("completion_contradiction", "baseline completion contains an unknown story")
    manifest_artifacts = {
        artifact["path"]: artifact for artifact in state["spec"]["packageManifest"]["artifacts"]
    }
    for story_id in baseline_ids:
        facts = story_facts[story_id]
        artifact = manifest_artifacts.get(facts["path"])
        if (
            artifact is None
            or facts["byteSha256"] != artifact["byteSha256AtLock"]
            or facts["status"] != "Completed"
            or facts["completedTasks"] != facts["tasks"]
            or facts["completedAcceptance"] != facts["acceptance"]
        ):
            raise ContractError(
                "completion_contradiction",
                f"{story_id} no longer proves unchanged lock-time completion",
            )

    claimed_sets = {
        "completed": set(execution["completedStoryIds"]),
        "active": set(execution["activeStoryIds"]),
        "failed": set(execution["failedStoryIds"]),
    }
    if any(not values <= all_story_set for values in claimed_sets.values()):
        raise ContractError("completion_contradiction", "story execution sets contain unknown stories")
    if (
        claimed_sets["completed"] & claimed_sets["active"]
        or claimed_sets["completed"] & claimed_sets["failed"]
        or claimed_sets["active"] & claimed_sets["failed"]
    ):
        raise ContractError("completion_contradiction", "completed, active, and failed story sets must be disjoint")

    raw_execution_path = execution["executionStatePath"]
    if raw_execution_path is None:
        if (
            execution["planDigest"] is not None
            or execution["storyResults"]
            or claimed_sets["active"]
            or claimed_sets["failed"]
            or claimed_sets["completed"] != baseline_ids
        ):
            raise ContractError("execution_state_contradiction", "story claims require a nested execution state")
        planned: list[str] = []
        nested_statuses: dict[str, str] = {}
    else:
        nested_path = safe_state_file(repo, raw_execution_path, "storyExecution.executionStatePath")
        nested = read_json(nested_path)
        if nested.get("spec") != state["spec"]["id"]:
            raise ContractError("execution_state_contradiction", "nested execution state identifies another spec")
        plan = nested.get("plan")
        planned = canonical_plan_stories(plan, all_story_ids, baseline_ids, story_facts)
        if execution["planDigest"] != digest_json(plan):
            raise ContractError("plan_contradiction", "storyExecution.planDigest does not match canonical nested plan")
        stories = nested.get("stories")
        if not isinstance(stories, dict) or set(stories) != set(planned):
            raise ContractError("execution_state_contradiction", "nested story state must exactly cover the plan")
        nested_statuses = {}
        for story_id, raw in stories.items():
            nested_story = require_object(raw, {"status", "phase"}, f"nested story {story_id}")
            if nested_story["status"] not in NESTED_STORY_STATUSES:
                raise ContractError("execution_state_contradiction", f"{story_id} has an invalid nested status")
            nested_statuses[story_id] = nested_story["status"]

    nested_completed = {story_id for story_id, status in nested_statuses.items() if status == "completed"}
    nested_active = {story_id for story_id, status in nested_statuses.items() if status == "in_progress"}
    nested_failed = {story_id for story_id, status in nested_statuses.items() if status == "failed"}
    results = execution["storyResults"]
    result_ids = set(results)
    allowed_result_ids = nested_completed | nested_failed | nested_active
    if not result_ids <= allowed_result_ids:
        raise ContractError("completion_contradiction", "story results do not agree with nested story states")
    if {story_id for story_id in nested_completed if results.get(story_id, {}).get("status") != "succeeded"}:
        raise ContractError("completion_contradiction", "nested completed stories require successful canonical results")
    if {story_id for story_id in nested_failed if results.get(story_id, {}).get("status") != "blocked"}:
        raise ContractError("completion_contradiction", "nested failed stories require blocked canonical results")
    for story_id in nested_active & result_ids:
        if results[story_id]["status"] != "answer_required":
            raise ContractError("completion_contradiction", "active story results may only require an answer")

    proven = set(baseline_ids)
    for story_id in planned:
        if story_id not in nested_completed:
            continue
        facts = story_facts[story_id]
        if (
            facts["status"] != "Completed"
            or facts["completedTasks"] != facts["tasks"]
            or facts["completedAcceptance"] != facts["acceptance"]
            or not set(facts["dependencies"]) <= proven
        ):
            raise ContractError("completion_contradiction", f"{story_id} lacks complete artifact/dependency evidence")
        proven.add(story_id)

    active_worktree_stories = {
        record["storyId"] for record in state["worktrees"].values()
        if record["status"] in ACTIVE_WORKTREE_STATUSES
    }
    blocked_worktree_stories = {
        record["storyId"] for record in state["worktrees"].values()
        if record["status"] == "blocked"
    }
    if active_worktree_stories != nested_active:
        raise ContractError("completion_contradiction", "active story and worktree sets disagree")
    if blocked_worktree_stories - nested_failed:
        raise ContractError("completion_contradiction", "blocked worktrees must correspond to failed stories")
    for story_id in nested_completed:
        records = [record for record in state["worktrees"].values() if record["storyId"] == story_id]
        if len(records) != 1:
            raise ContractError(
                "completion_contradiction",
                f"{story_id} requires exactly one persisted pre-Gate-1 ownership record",
            )
        result_digest = digest_json(results[story_id])
        record = records[0]
        target_is_integrated = subprocess.run(
            [
                "git", "-C", str(repo), "merge-base", "--is-ancestor",
                record["mergeEvidence"]["targetHeadSha"], observed_head,
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if (
            record["status"] != "integrated"
            or record["mergeEvidence"]["status"] != "integrated"
            or not target_is_integrated
            or record["parentExecutionId"] != state["executionId"]
            or record["resultDigestSha256"] != result_digest
            or record["mergeEvidence"]["resultDigestSha256"] != result_digest
            or record["currentSha"] != record["mergeEvidence"]["sourceHeadSha"]
        ):
            raise ContractError("completion_contradiction", f"{story_id} lacks integrated worktree evidence")
        if record["launchMode"] == "serial_in_place":
            if (
                str(Path(record["path"]).resolve()) != state["repository"]["rootIdentity"]
                or record["branchRef"] != state["repository"]["featureBranch"]
                or record["mergeEvidence"]["sourceHeadSha"] != record["mergeEvidence"]["targetHeadSha"]
            ):
                raise ContractError("completion_contradiction", f"{story_id} has invalid serial in-place evidence")
        elif record["launchMode"] != "linked_worktree":
            raise ContractError("completion_contradiction", f"{story_id} has invalid launch mode")

    expected_completed = [story_id for story_id in all_story_ids if story_id in proven]
    expected_active = [story_id for story_id in all_story_ids if story_id in nested_active]
    expected_failed = [story_id for story_id in all_story_ids if story_id in nested_failed]
    if execution["completedStoryIds"] != expected_completed:
        raise ContractError("completion_contradiction", "completedStoryIds does not exactly equal proven completion")
    if execution["activeStoryIds"] != expected_active or execution["failedStoryIds"] != expected_failed:
        raise ContractError("completion_contradiction", "active or failed story IDs disagree with nested evidence")

    saved_head = state["repository"]["currentHeadSha"]
    if observed_head != saved_head:
        explained = any(
            record["status"] == "integrated"
            and record["mergeEvidence"]["status"] == "integrated"
            and record["mergeEvidence"]["targetHeadSha"] == observed_head
            for record in state["worktrees"].values()
        )
        if not explained:
            raise ContractError("repository_head_contradiction", "current HEAD drift lacks integrated worktree evidence")
        state["repository"]["currentHeadSha"] = observed_head

    integration = execution["integrationVerification"]
    if integration["status"] == "passed":
        if set(proven) != all_story_set:
            raise ContractError("integration_evidence_contradiction", "integration cannot pass before every story is proven complete")
        required_bindings = (
            integration["headSha"] == observed_head,
            integration["packageManifestSha256"] == manifest["digestSha256"],
            integration["planDigest"] == execution["planDigest"],
            integration["completedStoryIds"] == expected_completed,
            isinstance(integration["command"], str) and bool(integration["command"].strip()),
            integration["exitCode"] == 0 and not isinstance(integration["exitCode"], bool),
            isinstance(integration["completedAt"], str) and bool(integration["completedAt"].strip()),
            isinstance(integration["evidenceSummary"], str) and bool(integration["evidenceSummary"].strip()),
            isinstance(integration["evidenceArtifactSha256"], str)
            and bool(HEX_RE.fullmatch(integration["evidenceArtifactSha256"])),
        )
        if not all(required_bindings):
            raise ContractError("integration_evidence_contradiction", "integration verification bindings are incomplete or stale")
        artifact = safe_state_file(
            repo,
            integration["evidenceArtifact"],
            "integrationVerification.evidenceArtifact",
            "integration_evidence_contradiction",
        )
        evidence_root = (repo / ".writ/state/evidence").resolve()
        try:
            artifact.relative_to(evidence_root)
        except ValueError as exc:
            raise ContractError(
                "integration_evidence_contradiction",
                "integration evidence artifact must be under .writ/state/evidence",
            ) from exc
        data = artifact.read_bytes()
        if not data or digest_bytes(data) != integration["evidenceArtifactSha256"]:
            raise ContractError("integration_evidence_contradiction", "integration evidence artifact hash is invalid")
    elif integration["status"] == "not_started":
        populated = [
            value for key, value in integration.items()
            if key not in {"status", "completedStoryIds"} and value is not None
        ]
        if populated or integration["completedStoryIds"]:
            raise ContractError("integration_evidence_contradiction", "not-started integration contains evidence claims")


def reconcile(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    expected_digest = digest_bytes(state_path.read_bytes())
    state = read_json(state_path)
    validate_state_shape(state)
    repo = Path(args.repo).resolve()
    if str(repo) != state["repository"]["rootIdentity"]:
        raise ContractError("repository_identity_mismatch", "repository root differs from state")
    identity = repo_identity(repo)
    if identity["branchRef"] is None:
        raise ContractError("repository_identity_mismatch", "repository is in detached HEAD state")
    identity_mismatches = [
        field for field, observed in (
            ("featureBranch", identity["branchRef"]),
            ("remoteName", identity["remoteName"]),
            ("remoteIdentity", identity["remoteIdentity"]),
        )
        if state["repository"][field] != observed
    ]
    if identity_mismatches:
        raise ContractError(
            "repository_identity_mismatch",
            f"repository branch or remote identity changed: {identity_mismatches}",
        )
    manifest, observed_log, story_facts = validate_package(repo, state["spec"]["path"])
    validate_spec_lite_amendments(repo, state, manifest)
    log_outcome = reconcile_log(state["spec"]["recommendationLog"], observed_log)
    if log_outcome in {"append_adopted", "pending_finalized"}:
        previous = state["spec"]["recommendationLog"]
        state["spec"]["recommendationLog"] = {
            **observed_log,
            "revision": previous["revision"] + 1,
            "lastReconciledAt": now(),
        }
    adopted = validate_worktree_ownership(state, git_worktrees(repo))
    for key, evidence in adopted.items():
        record = state["worktrees"][key]
        record["status"] = "adopted"
        record["adoptionState"] = "adopted"
        record["adoptionEvidence"] = {"adoptedAt": now(), "path": evidence["path"], "headSha": evidence["headSha"]}
        record["updatedAt"] = now()
    observed_head = git(repo, "rev-parse", "HEAD")
    reconcile_story_evidence(
        repo,
        state,
        story_facts,
        state["spec"]["packageManifest"],
        observed_head,
    )
    replace_state(state_path, state, expected_digest)
    return {
        "schema": "recommend-reconciliation-result-v1",
        "status": "reconciled",
        "log": log_outcome,
        "adopted_worktree_keys": sorted(adopted),
        "revision": state["revision"],
    }


def complete_worktree(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state)
    expected_digest = digest_bytes(state_path.read_bytes())
    state = read_json(state_path)
    validate_state_shape(state)
    record = state["worktrees"].get(args.worktree_key)
    if not isinstance(record, dict):
        raise ContractError("worktree_identity_contradiction", f"unknown worktree key: {args.worktree_key}")
    if record["status"] not in ACTIVE_WORKTREE_STATUSES:
        raise ContractError("worktree_identity_contradiction", "worktree ownership is not active")
    story_result = state["storyExecution"]["storyResults"].get(record["storyId"])
    if not isinstance(story_result, dict) or story_result.get("status") != "succeeded":
        raise ContractError("worktree_result_missing", "ownership completion requires a successful canonical story result")
    validate_command_result(story_result, expected_execution_id=state["executionId"])
    result_digest = digest_json(story_result)
    repo = Path(args.repo).resolve()
    if str(repo) != state["repository"]["rootIdentity"]:
        raise ContractError("repository_identity_mismatch", "completion target is not the canonical parent repository")
    target_identity = repo_identity(repo)
    if (
        target_identity["branchRef"] != state["repository"]["featureBranch"]
        or target_identity["remoteName"] != state["repository"]["remoteName"]
        or target_identity["remoteIdentity"] != state["repository"]["remoteIdentity"]
    ):
        raise ContractError("worktree_target_ambiguous", "parent target identity differs from the reserved repository")
    source = Path(record["path"]).resolve()
    observed = [item for item in git_worktrees(repo) if item.get("path") == str(source)]
    if len(observed) != 1 or observed[0].get("branchRef") != record["branchRef"]:
        raise ContractError("worktree_identity_contradiction", "worktree completion identity mismatch")
    source_head = git(source, "rev-parse", "HEAD")
    if source_head != observed[0]["headSha"]:
        raise ContractError("worktree_identity_stale", "observable worktree HEAD changed during completion")
    if git(source, "status", "--porcelain", "--untracked-files=all"):
        raise ContractError("worktree_dirty", "delegated worktree contains tracked or untracked changes")
    starting_sha = record["startingSha"]
    if source_head == starting_sha:
        raise ContractError("worktree_content_uncommitted", "delegated worktree has no committed story content")
    if subprocess.run(
        ["git", "-C", str(source), "merge-base", "--is-ancestor", starting_sha, source_head],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise ContractError("worktree_identity_stale", "delegated HEAD does not descend from its reserved starting SHA")
    if not git(source, "diff", "--name-only", f"{starting_sha}..{source_head}"):
        raise ContractError("worktree_content_uncommitted", "delegated commits contain no story file changes")
    target_head = git(repo, "rev-parse", "HEAD")
    if subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", source_head, target_head],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise ContractError("worktree_not_integrated", "worktree HEAD is not contained in parent HEAD")
    timestamp = now()
    record["status"] = "integrated"
    record["activeGate"] = "complete"
    record["currentSha"] = str(source_head)
    record["resultDigestSha256"] = result_digest
    record["mergeEvidence"] = {
        "status": "integrated",
        "sourceHeadSha": source_head,
        "targetHeadSha": target_head,
        "resultDigestSha256": result_digest,
        "observedAt": timestamp,
    }
    record["updatedAt"] = timestamp
    replace_state(state_path, state, expected_digest)
    return {
        "schema": "recommend-worktree-completion-v1",
        "status": "integrated",
        "worktree_key": args.worktree_key,
        "revision": state["revision"],
    }


def normalize_result(args: argparse.Namespace) -> dict[str, Any]:
    value = read_json(Path(args.input))
    required = {
        "schema", "execution_id", "mode", "command", "status", "completed_state",
        "resume_state", "evidence", "identifiers", "required_answer", "blocker",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ContractError("invalid_result", f"nested result missing required keys: {missing}")
    if (
        value.get("schema") != RESULT_SCHEMA
        or value.get("execution_id") != args.execution_id
        or value.get("mode") != "recommend"
    ):
        raise ContractError("invalid_result", "nested result schema, execution, or mode is invalid")
    require_string(value.get("command"), "result.command")
    if value.get("status") == "failed":
        return canonical_blocked_result(
            "nested_result_failed",
            "Nested command reported failure",
            execution_id=args.execution_id,
            command=value["command"],
            resume_state=value.get("resume_state") if value.get("resume_state") in ({None} | STATE_STATUSES) else None,
        )
    return validate_command_result(value, expected_execution_id=args.execution_id)


def stage_input(args: argparse.Namespace, schema: str) -> tuple[Path, dict[str, Any], str, dict[str, Any]]:
    state_path = Path(args.state).resolve()
    state = read_json(state_path)
    validate_state_shape(state)
    evidence = read_json(Path(args.evidence).resolve())
    if evidence.get("schema") != schema:
        raise ContractError("invalid_evidence", f"expected evidence schema {schema}")
    try:
        expected_digest = digest_bytes(state_path.read_bytes())
    except OSError as exc:
        raise ContractError("state_missing", f"cannot read state: {state_path}") from exc
    return state_path, state, expected_digest, evidence


def stage_transition(
    state: dict[str, Any],
    target: str,
    operation_key: str,
    summary: str,
    identifiers: list[str] | None = None,
    outcome: str = "succeeded",
) -> None:
    source = state["status"]
    state["status"] = target
    state["resumeTarget"] = target
    state["blocked"] = {
        "active": False, "code": None, "summary": None, "operation": None,
        "recoverable": False, "resumeFrom": None, "firstObservedAt": None,
        "lastObservedAt": None,
    }
    state["transitions"].append({
        "sequence": len(state["transitions"]) + 1,
        "from": source,
        "to": target,
        "startedAt": now(),
        "completedAt": None if outcome == "pending" else now(),
        "attempt": 1,
        "operationKey": operation_key,
        "evidenceSummary": summary,
        "persistedIdentifiers": identifiers or [],
        "outcome": outcome,
    })


def stage_block(
    state_path: Path,
    state: dict[str, Any],
    expected_digest: str,
    code: str,
    summary: str,
    operation: str,
    resume_from: str,
) -> None:
    observed = now()
    state["status"] = "blocked"
    state["resumeTarget"] = resume_from
    state["blocked"] = {
        "active": True, "code": code, "summary": summary, "operation": operation,
        "recoverable": True, "resumeFrom": resume_from,
        "firstObservedAt": observed, "lastObservedAt": observed,
    }
    state["transitions"].append({
        "sequence": len(state["transitions"]) + 1,
        "from": resume_from,
        "to": "blocked",
        "startedAt": observed,
        "completedAt": observed,
        "attempt": 1,
        "operationKey": operation,
        "evidenceSummary": summary,
        "persistedIdentifiers": [],
        "outcome": "blocked",
    })
    replace_state(state_path, state, expected_digest)
    raise ContractError(code, summary)


def active_delivery(state: dict[str, Any]) -> dict[str, Any]:
    delivery = state["delivery"]
    if "capabilitySnapshot" not in delivery:
        raise ContractError("staging_not_activated", "Story 4 staging has not been activated")
    return delivery


def deterministic_operation_key(kind: str, *parts: str) -> str:
    if any(not isinstance(part, str) or not part for part in parts):
        raise ContractError("invalid_evidence", f"{kind} operation identity is incomplete")
    identity = "\0".join(parts).encode()
    return f"{kind}:{hashlib.sha256(identity).hexdigest()}"


def current_log(state: dict[str, Any]) -> tuple[Path, dict[str, Any], str]:
    root = Path(state["repository"]["rootIdentity"]).resolve()
    path = (root / state["spec"]["recommendationLog"]["path"]).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ContractError("recommendation_log_contradiction", "recommendation log escapes repository") from exc
    observed = parse_log(path)
    saved = state["spec"]["recommendationLog"]
    if (
        observed["digestSha256"] != saved["digestSha256"]
        or observed["entryIds"] != saved["entryIds"]
        or observed["entryDigests"] != saved["entryDigests"]
        or observed["pendingEntryIds"] != saved["pendingEntryIds"]
    ):
        raise ContractError(
            "recommendation_log_contradiction",
            "recommendation log must be reconciled into state before external mutation",
        )
    return path, observed, path.read_text(encoding="utf-8")


def require_audit_binding(
    state: dict[str, Any],
    entry_id: Any,
    operation_key: str,
    *,
    pending: bool,
) -> str:
    require_string(entry_id, "auditEntryId")
    _, observed, text = current_log(state)
    if entry_id not in observed["entryIds"]:
        raise ContractError("audit_entry_missing", "audit entry is not persisted in canonical state")
    if pending and entry_id not in observed["pendingEntryIds"]:
        raise ContractError("audit_entry_not_pending", "external mutation requires a pending audit entry")
    matches = list(re.finditer(rf"(?m)^## {re.escape(entry_id)} — .+$", text))
    if len(matches) != 1:
        raise ContractError("audit_entry_missing", "audit entry identity is ambiguous")
    start = matches[0].start()
    following = re.search(r"(?m)^## REC-\d+ — .+$", text[matches[0].end():])
    end = matches[0].end() + following.start() if following else len(text)
    body = text[start:end]
    if operation_key not in body:
        raise ContractError("audit_operation_mismatch", "audit entry is not bound to the operation key")
    return body


def require_zero_pending_mutation_audits(state: dict[str, Any]) -> None:
    _, observed, text = current_log(state)
    unresolved: list[str] = []
    for entry_id in observed["pendingEntryIds"]:
        match = re.search(
            rf"(?ms)^## {re.escape(entry_id)} — .+?(?=^## REC-|\Z)", text
        )
        body = match.group(0) if match else ""
        if re.search(r"operation key (?:ship|pr-create|approval|merge):[0-9a-f]{64}", body):
            unresolved.append(entry_id)
    if unresolved:
        raise ContractError(
            "mutation_audit_pending",
            f"Mutation-related recommendation entries must be finalized: {unresolved}",
        )


def git_commit_exists(repo: Path, sha: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def git_is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def parse_utc_rfc3339(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ):
        raise ContractError("invalid_timestamp", f"{field} must be UTC RFC3339 seconds")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ContractError("invalid_timestamp", f"{field} is not a valid UTC timestamp") from exc


def duration_seconds(value: Any, field: str) -> int:
    if not isinstance(value, str):
        raise ContractError("invalid_evidence", f"{field} is invalid")
    match = re.fullmatch(r"([1-9]\d*)([smh])", value)
    if not match:
        raise ContractError("invalid_evidence", f"{field} is invalid")
    factor = {"s": 1, "m": 60, "h": 3600}[match.group(2)]
    return int(match.group(1)) * factor


def safe_repo_file(state: dict[str, Any], relative: Any, code: str) -> Path:
    require_string(relative, "evidence artifact path")
    root = Path(state["repository"]["rootIdentity"]).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ContractError(code, "evidence path escapes repository") from exc
    if not path.is_file():
        raise ContractError(code, "evidence artifact is missing")
    return path


def activate_staging(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(
        args, "recommend-staging-activation-v1"
    )
    integration = state["storyExecution"]["integrationVerification"]
    if state["status"] != "verifying" or integration["status"] != "passed":
        raise ContractError(
            "implementation_not_verified",
            "Story 4 staging requires passed integration verification",
        )
    required = (
        "provider", "repositoryId", "sourceRemote", "sourceIdentity", "baseBranch",
        "featureBranch", "headSha", "capabilities", "config",
    )
    for field in required:
        if field not in evidence or evidence[field] in (None, ""):
            raise ContractError("invalid_evidence", f"staging activation lacks {field}")
    if not GIT_SHA_RE.fullmatch(evidence["headSha"]):
        raise ContractError("invalid_evidence", "staging head must be a full lowercase SHA")
    if (
        evidence["headSha"] != integration["headSha"]
        or evidence["headSha"] != state["repository"]["currentHeadSha"]
    ):
        raise ContractError(
            "staging_head_mismatch",
            "staging, integration, and canonical repository heads must be identical",
        )
    state_branch = state["repository"]["featureBranch"]
    if evidence["featureBranch"] != state_branch and state_branch != f"refs/heads/{evidence['featureBranch']}":
        raise ContractError("repository_identity_mismatch", "staging feature branch does not match state")
    capabilities = evidence["capabilities"]
    if not isinstance(capabilities, dict) or any(
        capabilities.get(name) not in {"available", "unavailable", "needs_auth"}
        for name in ("pr", "checks", "preview")
    ):
        raise ContractError("invalid_evidence", "capability snapshot is incomplete")
    config = evidence["config"]
    required_config = {
        "requiredChecks", "previewProvider", "previewProjectId",
        "previewEvidenceSource", "previewUrlPattern", "ciWaitTimeout",
        "previewWaitTimeout",
    }
    if not isinstance(config, dict) or not required_config <= set(config):
        raise ContractError("invalid_evidence", "staging config snapshot is incomplete")
    require_string(config["previewProvider"], "config.previewProvider")
    require_string(config["previewProjectId"], "config.previewProjectId")
    require_string(config["previewEvidenceSource"], "config.previewEvidenceSource")
    if not isinstance(config["requiredChecks"], list) or any(
        not isinstance(item, str) or not item for item in config["requiredChecks"]
    ):
        raise ContractError("invalid_evidence", "configured required checks are invalid")
    state["repository"].update({
        "provider": evidence["provider"],
        "providerRepositoryId": evidence["repositoryId"],
        "deliveryRemote": evidence["sourceRemote"],
        "deliverySourceIdentity": evidence["sourceIdentity"],
        "defaultBranch": evidence["baseBranch"],
    })
    state["delivery"] = {
        "test": None,
        "commits": None,
        "pr": None,
        "checks": [],
        "preview": None,
        "uat": None,
        "approval": None,
        "merge": None,
        "release": None,
        "capabilitySnapshot": {
            "schema": "recommend-provider-capabilities-v1",
            "provider": evidence["provider"],
            "repositoryId": evidence["repositoryId"],
            "sourceRemote": evidence["sourceRemote"],
            "sourceIdentity": evidence["sourceIdentity"],
            "baseBranch": evidence["baseBranch"],
            "featureBranch": evidence["featureBranch"],
            "headSha": evidence["headSha"],
            "capabilities": copy.deepcopy(capabilities),
            "config": copy.deepcopy(config),
            "capturedAt": now(),
        },
        "operations": {},
    }
    state["delivery"]["capabilitySnapshot"]["digestSha256"] = digest_json(
        state["delivery"]["capabilitySnapshot"]
    )
    stage_transition(
        state, "committing", f"stage:{state['executionId']}:{evidence['headSha']}",
        "Verified implementation entered Story 4 staging", [evidence["headSha"]],
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "committing", "revision": state["revision"]}


def record_ship(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-ship-evidence-v1")
    delivery = active_delivery(state)
    if state["status"] != "committing":
        raise ContractError("invalid_transition", "ship evidence is accepted only while committing")
    if evidence.get("testStatus") != "passed":
        raise ContractError("ship_tests_failed", "recommended staging requires passing /ship --test evidence")
    head = evidence.get("headSha")
    if head != delivery["capabilitySnapshot"]["headSha"] or not GIT_SHA_RE.fullmatch(head or ""):
        raise ContractError("ship_head_mismatch", "ship evidence does not bind the staged head SHA")
    operation_key = deterministic_operation_key("ship", state["executionId"], head)
    try:
        require_string(evidence.get("testCommand"), "ship.testCommand")
        artifact = safe_repo_file(state, evidence.get("testEvidence"), "ship_evidence_invalid")
        artifact_digest = digest_bytes(artifact.read_bytes())
        try:
            artifact_payload = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "ship_evidence_invalid", "ship test artifact must be structured JSON evidence"
            ) from exc
        if (
            evidence.get("testExitCode") != 0
            or evidence.get("testEvidenceDigestSha256") != artifact_digest
            or evidence.get("testEvidenceHeadSha") != head
            or not isinstance(artifact_payload, dict)
            or artifact_payload.get("schema") != "recommend-test-evidence-v1"
            or artifact_payload.get("status") != "passed"
            or artifact_payload.get("command") != evidence.get("testCommand")
            or artifact_payload.get("exitCode") != 0
            or artifact_payload.get("headSha") != head
            or evidence.get("strategy") not in {"single", "split"}
            or evidence.get("groupingBasis") not in {
                "single-file", "under-50-lines", "tightly-coupled",
                "logical-layers-buildable",
            }
        ):
            raise ContractError("ship_evidence_invalid", "ship evidence is incomplete or unbound")
        require_string(evidence.get("decisionId"), "ship.decisionId")
        audit_body = require_audit_binding(
            state, evidence.get("auditEntryId"), operation_key, pending=False
        )
    except ContractError as exc:
        if exc.code in {"ship_evidence_invalid", "audit_entry_missing", "audit_operation_mismatch",
                        "recommendation_log_contradiction", "invalid_state"}:
            raise ContractError("ship_evidence_invalid", exc.message) from exc
        raise
    commits = evidence.get("commitShas")
    if not isinstance(commits, list) or not commits or any(
        not isinstance(item, str) or not GIT_SHA_RE.fullmatch(item) for item in commits
    ):
        raise ContractError("invalid_evidence", "ship evidence requires full commit SHAs")
    repo = Path(state["repository"]["rootIdentity"]).resolve()
    current_head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=False,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    ).stdout.strip()
    strategy = evidence.get("strategy")
    if (
        evidence.get("decisionId") != evidence.get("auditEntryId")
        or state["repository"]["currentHeadSha"] != head
        or current_head != head
        or commits[-1] != head
        or (strategy == "single" and len(commits) != 1)
        or (strategy == "split" and len(commits) < 2)
        or any(not git_commit_exists(repo, sha) for sha in commits)
        or any(not git_is_ancestor(repo, commits[index], commits[index + 1])
               for index in range(len(commits) - 1))
        or "- **Result:** Applied" not in audit_body
        or f"strategy {strategy}" not in audit_body
        or f"head {head}" not in audit_body
        or any(sha not in audit_body for sha in commits)
    ):
        raise ContractError(
            "ship_commit_binding_invalid",
            "Commit grouping audit, repository ancestry, sequence, and exact current head must agree",
        )
    require_zero_pending_mutation_audits(state)
    delivery["test"] = {
        "status": "passed", "command": evidence.get("testCommand"),
        "exitCode": 0, "evidenceArtifact": evidence.get("testEvidence"),
        "evidenceArtifactSha256": artifact_digest, "observedForHeadSha": head,
        "completedAt": now(),
    }
    delivery["commits"] = {
        "strategy": evidence.get("strategy"), "commitShas": commits, "headSha": head,
        "decisionId": evidence.get("decisionId"), "auditEntryId": evidence.get("auditEntryId"),
        "groupingBasis": evidence.get("groupingBasis"),
    }
    stage_transition(
        state, "opening_pr", operation_key,
        "Mandatory test evidence and commit grouping persisted", commits,
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "opening_pr", "revision": state["revision"]}


def validate_pr(state: dict[str, Any], record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ContractError("invalid_evidence", "pull request record must be an object")
    snapshot = active_delivery(state)["capabilitySnapshot"]
    expected = {
        "repositoryId": snapshot["repositoryId"],
        "baseBranch": snapshot["baseBranch"],
        "headBranch": snapshot["featureBranch"],
        "headSha": snapshot["headSha"],
    }
    if any(record.get(field) != value for field, value in expected.items()):
        raise ContractError("pr_mismatch", "pull request does not match repository/base/head identity")
    if record.get("state") != "open":
        raise ContractError("pr_closed", "matching pull request is closed; automatic replacement is forbidden")
    for field in ("providerId", "url"):
        require_string(record.get(field), f"pullRequest.{field}")
    if isinstance(record.get("number"), bool) or not isinstance(record.get("number"), int):
        raise ContractError("invalid_evidence", "pull request number must be an integer")
    return copy.deepcopy(record)


def record_pr_lookup(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-pr-lookup-v1")
    delivery = active_delivery(state)
    if state["status"] != "opening_pr":
        raise ContractError("invalid_transition", "PR lookup is accepted only while opening_pr")
    operation_key = evidence.get("operationKey")
    require_string(operation_key, "pr lookup operationKey")
    snapshot = delivery["capabilitySnapshot"]
    expected_key = deterministic_operation_key(
        "pr-create", snapshot["repositoryId"], snapshot["baseBranch"],
        snapshot["featureBranch"],
    )
    if operation_key != expected_key:
        raise ContractError("pr_operation_key_mismatch", "PR operation key is not canonical")
    result = evidence.get("result")
    matches = evidence.get("matches")
    if not isinstance(matches, list):
        raise ContractError("invalid_evidence", "PR lookup matches must be a list")
    if result == "multiple" or len(matches) > 1:
        stage_block(state_path, state, expected_digest, "pr_ambiguous",
                    "Multiple pull requests match repository/base/head", operation_key, "opening_pr")
    if result in {"needs_auth", "unavailable", "error"}:
        stage_block(state_path, state, expected_digest, f"pr_{result}",
                    "Pull request lookup capability is unavailable", operation_key, "opening_pr")
    if result == "absent":
        if matches:
            raise ContractError("invalid_evidence", "absent PR lookup cannot include matches")
        existing = delivery["operations"].get(operation_key)
        if existing is not None:
            stage_block(
                state_path, state, expected_digest, "pr_create_already_authorized",
                "A prior create authorization or attempt exists; repeated absence cannot authorize another",
                operation_key, "opening_pr",
            )
        require_audit_binding(
            state, evidence.get("auditEntryId"), operation_key, pending=True
        )
        delivery["operations"][operation_key] = {
            "kind": "createPullRequest", "status": "authorized",
            "auditEntryId": evidence["auditEntryId"],
            "authorizedAt": now(), "attemptedAt": None, "providerId": None,
        }
        stage_transition(
            state, "opening_pr", operation_key,
            "Lookup found no matching PR; one create mutation is authorized", outcome="pending",
        )
        replace_state(state_path, state, expected_digest)
        return {
            "schema": "recommend-staging-result-v1", "status": "opening_pr",
            "action": "createPullRequest", "operationKey": operation_key,
            "revision": state["revision"],
        }
    if result != "one" or len(matches) != 1:
        raise ContractError("invalid_evidence", "PR lookup result cardinality is invalid")
    pr = validate_pr(state, matches[0])
    operation = delivery["operations"].get(operation_key)
    if operation is not None and operation.get("status") not in {"attempted", "authorized"}:
        raise ContractError("pr_create_reconciliation_invalid", "PR reconciliation marker is invalid")
    if operation is None:
        require_audit_binding(
            state, evidence.get("auditEntryId"), operation_key, pending=True
        )
        operation = {
            "kind": "createPullRequest", "status": "adopted",
            "auditEntryId": evidence["auditEntryId"], "providerId": pr["providerId"],
            "observedAt": now(),
        }
        delivery["operations"][operation_key] = operation
    else:
        operation.update(
            status="reconciled", providerId=pr["providerId"], reconciledAt=now()
        )
    pr["observedAt"] = now()
    delivery["pr"] = pr
    stage_transition(
        state, "pr_open", operation_key,
        "One matching open PR was observed; audit finalization is required",
        [pr["providerId"], str(pr["number"]), pr["headSha"]],
        outcome="pending",
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "pr_open",
            "pullRequest": pr, "revision": state["revision"]}


def mark_pr_create_attempt(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(
        args, "recommend-pr-create-attempt-v1"
    )
    delivery = active_delivery(state)
    snapshot = delivery["capabilitySnapshot"]
    expected_key = deterministic_operation_key(
        "pr-create", snapshot["repositoryId"], snapshot["baseBranch"],
        snapshot["featureBranch"],
    )
    operation_key = evidence.get("operationKey")
    operation = delivery["operations"].get(operation_key)
    if (
        state["status"] != "opening_pr"
        or operation_key != expected_key
        or not isinstance(operation, dict)
        or operation.get("status") != "authorized"
    ):
        raise ContractError("pr_create_not_authorized", "PR create attempt lacks one current authorization")
    require_audit_binding(
        state, evidence.get("auditEntryId"), operation_key, pending=True
    )
    if evidence["auditEntryId"] != operation.get("auditEntryId"):
        raise ContractError("audit_operation_mismatch", "PR attempt audit identity changed")
    operation.update(status="attempted", attemptedAt=now())
    stage_transition(
        state, "opening_pr", operation_key,
        "At-most-one PR create attempt marker persisted", [evidence["auditEntryId"]],
        outcome="pending",
    )
    replace_state(state_path, state, expected_digest)
    return {
        "schema": "recommend-staging-result-v1", "status": "opening_pr",
        "action": "createPullRequest", "operationKey": operation_key,
        "revision": state["revision"],
    }


def record_pr_created(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-pr-created-v1")
    delivery = active_delivery(state)
    operation_key = evidence.get("operationKey")
    operation = delivery["operations"].get(operation_key)
    if state["status"] != "opening_pr" or not isinstance(operation, dict) or operation.get("status") != "attempted":
        raise ContractError("pr_create_not_pending", "PR creation lacks a persisted attempted marker")
    require_audit_binding(
        state, evidence.get("auditEntryId"), operation_key, pending=True
    )
    if evidence["auditEntryId"] != operation.get("auditEntryId"):
        raise ContractError("audit_operation_mismatch", "PR creation audit identity changed")
    pr = validate_pr(state, evidence.get("pullRequest"))
    pr["observedAt"] = now()
    delivery["pr"] = pr
    operation.update(status="created", providerId=pr["providerId"], createdAt=now())
    stage_transition(
        state, "pr_open", operation_key,
        "Created PR was observed; canonical IDs persisted pending audit finalization",
        [pr["providerId"], str(pr["number"]), pr["headSha"]],
        outcome="pending",
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "pr_open",
            "pullRequest": pr, "revision": state["revision"]}


def finalize_pr_audit(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(
        args, "recommend-pr-audit-finalization-v1"
    )
    delivery = active_delivery(state)
    snapshot = delivery["capabilitySnapshot"]
    operation_key = deterministic_operation_key(
        "pr-create", snapshot["repositoryId"], snapshot["baseBranch"],
        snapshot["featureBranch"],
    )
    operation = delivery["operations"].get(operation_key)
    pr = delivery.get("pr")
    if (
        state["status"] != "pr_open"
        or evidence.get("operationKey") != operation_key
        or not isinstance(operation, dict)
        or operation.get("status") not in {"adopted", "created", "reconciled"}
        or not isinstance(pr, dict)
        or evidence.get("auditEntryId") != operation.get("auditEntryId")
        or evidence.get("outcome") != operation.get("status")
    ):
        raise ContractError("pr_audit_finalization_invalid", "PR audit finalization identity is invalid")
    body = require_audit_binding(
        state, evidence["auditEntryId"], operation_key, pending=False
    )
    if (
        "- **Result:** Applied" not in body
        or f"outcome {evidence['outcome']}" not in body
        or f"provider ID {pr['providerId']}" not in body
        or f"number {pr['number']}" not in body
        or f"URL {pr['url']}" not in body
    ):
        raise ContractError(
            "pr_audit_finalization_invalid",
            "Final PR audit must contain canonical provider ID, number, URL, and outcome",
        )
    require_zero_pending_mutation_audits(state)
    operation.update(status="finalized", finalizedAt=now())
    stage_transition(
        state, "waiting_ci", operation_key,
        "Canonical PR audit entry finalized before required checks",
        [evidence["auditEntryId"], pr["providerId"], str(pr["number"]), pr["headSha"]],
    )
    replace_state(state_path, state, expected_digest)
    return {
        "schema": "recommend-staging-result-v1", "status": "waiting_ci",
        "pullRequest": pr, "revision": state["revision"],
    }


def record_checks(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-required-checks-v1")
    delivery = active_delivery(state)
    if state["status"] != "waiting_ci" or not delivery["pr"]:
        raise ContractError("invalid_transition", "required checks need one open PR in waiting_ci")
    require_zero_pending_mutation_audits(state)
    operation = f"checks:{delivery['pr']['providerId']}:{delivery['pr']['headSha']}"
    capability = evidence.get("capability")
    if capability in {"needs_auth", "authorization_denied"}:
        stage_block(
            state_path, state, expected_digest, f"checks_{capability}",
            "Required-check discovery was denied; resolve provider access and resume",
            operation, "waiting_ci",
        )
    if capability != "available":
        stage_block(
            state_path, state, expected_digest, "checks_unavailable",
            "Provider-required checks cannot be discovered; unknown is not empty",
            operation, "waiting_ci",
        )
    snapshot = delivery["capabilitySnapshot"]
    query = evidence.get("queryOperation")
    if evidence.get("authenticated") is not True or not isinstance(query, dict):
        stage_block(
            state_path, state, expected_digest, "checks_unauthenticated",
            "Required-check discovery must include explicit authenticated query evidence",
            operation, "waiting_ci",
        )
    for field in ("id", "kind", "provider", "repositoryId", "headSha", "startedAt", "completedAt"):
        require_string(query.get(field), f"checks.queryOperation.{field}")
    query_started = parse_utc_rfc3339(query["startedAt"], "checks.queryOperation.startedAt")
    query_completed = parse_utc_rfc3339(query["completedAt"], "checks.queryOperation.completedAt")
    if (
        query["kind"] != "listRequiredChecks"
        or query["provider"] != snapshot["provider"]
        or query["repositoryId"] != snapshot["repositoryId"]
        or query["headSha"] != delivery["pr"]["headSha"]
        or query["completedAt"] != evidence.get("queriedAt")
        or query_completed < query_started
    ):
        stage_block(
            state_path, state, expected_digest, "checks_unauthenticated",
            "Authenticated required-check query operation identity is inconsistent",
            operation, "waiting_ci",
        )
    for field in ("provider", "repositoryId", "queriedAt"):
        require_string(evidence.get(field), f"checks.{field}")
    if (
        evidence["provider"] != snapshot["provider"]
        or evidence["repositoryId"] != snapshot["repositoryId"]
    ):
        stage_block(
            state_path, state, expected_digest, "checks_provider_evidence_missing",
            "Required-check query provider/repository identity does not match the capability snapshot",
            operation, "waiting_ci",
        )
    if evidence.get("headSha") != delivery["pr"]["headSha"]:
        stage_block(state_path, state, expected_digest, "checks_stale",
                    "Required-check evidence is not for the current PR head", operation, "waiting_ci")
    records = evidence.get("checks")
    if not isinstance(records, list):
        raise ContractError("invalid_evidence", "checks must be a list")
    names: list[str] = []
    statuses: list[str] = []
    canonical: list[dict[str, Any]] = []
    for raw in records:
        if not isinstance(raw, dict):
            raise ContractError("invalid_evidence", "check record must be an object")
        for field in ("id", "name", "status", "requiredBy"):
            require_string(raw.get(field), f"check.{field}")
        if raw["id"] in [item["id"] for item in canonical] or raw["name"] in names:
            raise ContractError("invalid_evidence", "check IDs and names must be unique")
        names.append(raw["name"])
        statuses.append(raw["status"])
        canonical.append(copy.deepcopy(raw))
    provider_records = [item for item in canonical if item["requiredBy"] == "provider"]
    configured_records = [item for item in canonical if item["requiredBy"] == "config"]
    if len(provider_records) + len(configured_records) != len(canonical):
        stage_block(
            state_path, state, expected_digest, "checks_provider_evidence_missing",
            "Each required check must be classified as provider or additive config",
            operation, "waiting_ci",
        )
    provider_ids = evidence.get("providerRequiredCheckIds")
    provider_names = evidence.get("providerRequiredCheckNames")
    explicit_zero = evidence.get("explicitZeroRequired") is True
    if not isinstance(provider_ids, list) or not isinstance(provider_names, list):
        stage_block(
            state_path, state, expected_digest, "checks_provider_evidence_missing",
            "Stable provider-required IDs and names or explicit zero evidence are required",
            operation, "waiting_ci",
        )
    observed_provider_ids = [item["id"] for item in provider_records]
    observed_provider_names = [item["name"] for item in provider_records]
    if provider_ids != observed_provider_ids or provider_names != observed_provider_names:
        stage_block(
            state_path, state, expected_digest, "checks_provider_evidence_missing",
            "Provider-required set declaration does not match provider check records",
            operation, "waiting_ci",
        )
    if explicit_zero == bool(provider_records) or (not explicit_zero and not provider_records):
        stage_block(
            state_path, state, expected_digest, "checks_provider_evidence_missing",
            "Provider discovery must declare one stable nonempty set or explicit zero",
            operation, "waiting_ci",
        )
    required_set = [{"id": item["id"], "name": item["name"]} for item in provider_records]
    required_set_digest = digest_json(required_set)
    if evidence.get("providerRequiredSetDigestSha256") != required_set_digest:
        stage_block(
            state_path, state, expected_digest, "checks_provider_evidence_missing",
            "Provider-required set digest is missing or invalid",
            operation, "waiting_ci",
        )
    configured = delivery["capabilitySnapshot"]["config"].get("requiredChecks", [])
    configured_names = [item["name"] for item in configured_records]
    if not isinstance(configured, list) or sorted(configured_names) != sorted(configured):
        stage_block(state_path, state, expected_digest, "checks_config_missing",
                    "Configured additive required checks are absent from observed evidence",
                    operation, "waiting_ci")
    unknown = sorted(set(statuses) - {"pending", "success", "failed", "cancelled"})
    if unknown:
        stage_block(state_path, state, expected_digest, "checks_unknown",
                    f"Unknown required-check statuses: {unknown}", operation, "waiting_ci")
    delivery["checks"] = canonical
    delivery["checksEvidence"] = {
        "observedForHeadSha": evidence["headSha"],
        "provider": evidence["provider"],
        "repositoryId": evidence["repositoryId"],
        "queriedAt": evidence["queriedAt"],
        "authenticated": True,
        "queryOperation": copy.deepcopy(query),
        "providerRequiredCheckIds": provider_ids,
        "providerRequiredCheckNames": provider_names,
        "providerRequiredSetDigestSha256": required_set_digest,
        "requiredCheckIds": [item["id"] for item in canonical],
        "requiredCheckNames": names,
        "explicitZeroRequired": explicit_zero,
        "requiredSetReconciled": evidence.get("requiredSetReconciled") is True,
        "querySequence": evidence.get("querySequence"),
        "evidenceUrl": evidence.get("evidenceUrl"),
        "lastObservedAt": now(),
    }
    if "failed" in statuses or "cancelled" in statuses:
        code = "checks_failed" if "failed" in statuses else "checks_cancelled"
        stage_block(state_path, state, expected_digest, code,
                    "A required check did not succeed", operation, "implementing")
    if "pending" in statuses:
        summary = "Required checks remain pending"
        if evidence.get("timedOut"):
            summary += "; wait timed out resumably"
        if evidence.get("interrupted"):
            summary += "; wait was interrupted resumably"
        stage_transition(state, "waiting_ci", operation, summary, [item["id"] for item in canonical])
    else:
        if (
            evidence.get("requiredSetReconciled") is not True
            or not isinstance(evidence.get("querySequence"), int)
            or evidence["querySequence"] < 2
        ):
            stage_block(
                state_path, state, expected_digest, "checks_set_not_reconciled",
                "Re-query the complete required set before advancing; late-added checks must be included",
                operation, "waiting_ci",
            )
        stage_transition(
            state, "discovering_preview", operation,
            "Every provider and configured required check succeeded",
            [item["id"] for item in canonical],
        )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": state["status"],
            "revision": state["revision"]}


def safe_preview_url(value: Any, pattern: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.query or parsed.fragment:
        return False
    return pattern in (None, "") or (
        isinstance(pattern, str) and fnmatch.fnmatchcase(value, pattern)
    )


def record_preview(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-preview-evidence-v1")
    delivery = active_delivery(state)
    require_zero_pending_mutation_audits(state)
    if state["status"] != "discovering_preview" or not delivery.get("checksEvidence"):
        raise ContractError("invalid_transition", "preview discovery requires successful current checks")
    operation = f"preview:{delivery['pr']['providerId']}:{delivery['pr']['headSha']}"
    capability = evidence.get("capability")
    if capability in {"needs_auth", "authorization_denied"}:
        stage_block(
            state_path, state, expected_digest, f"preview_{capability}",
            "Preview discovery was denied; resolve configured integration access and resume",
            operation, "discovering_preview",
        )
    if capability != "available":
        stage_block(state_path, state, expected_digest, "preview_unavailable",
                    "No configured preview capability is available; configure an existing integration",
                    operation, "discovering_preview")
    if evidence.get("headSha") != delivery["pr"]["headSha"]:
        stage_block(state_path, state, expected_digest, "preview_stale",
                    "Preview evidence is not bound to the current PR head",
                    operation, "discovering_preview")
    snapshot = delivery["capabilitySnapshot"]
    config = snapshot["config"]
    provenance = evidence.get("provenance")
    allowed_provenance = {
        "deployment-status": {"provider-deployment", "provider-status"},
        "check-output": {"provider-check"},
        "project-convention": {"project-convention"},
    }
    configured_source = config.get("previewEvidenceSource")
    allowed_kinds = allowed_provenance.get(configured_source, set())
    if (
        evidence.get("provider") != config.get("previewProvider")
        or evidence.get("source") != configured_source
        or evidence.get("repositoryId") != snapshot["repositoryId"]
        or evidence.get("projectId") != config.get("previewProjectId")
        or evidence.get("source") == "url-pattern"
        or not isinstance(provenance, dict)
        or provenance.get("kind") not in allowed_kinds
        or provenance.get("headSha") != delivery["pr"]["headSha"]
        or provenance.get("repositoryId") != snapshot["repositoryId"]
        or provenance.get("projectId") != config.get("previewProjectId")
        or not isinstance(provenance.get("integrationId"), str)
        or not provenance.get("integrationId")
        or not isinstance(provenance.get("observedAt"), str)
        or not provenance.get("observedAt")
    ):
        stage_block(
            state_path, state, expected_digest, "preview_provenance_mismatch",
            "Preview provider/source/project provenance does not match configured capability evidence",
            operation, "discovering_preview",
        )
    status = evidence.get("status")
    if status == "pending":
        stage_transition(
            state, "discovering_preview", operation,
            "Preview remains pending" + ("; wait timed out resumably" if evidence.get("timedOut") else ""),
        )
        replace_state(state_path, state, expected_digest)
        return {"schema": "recommend-staging-result-v1", "status": "discovering_preview",
                "revision": state["revision"]}
    if status in {"missing", "error"}:
        code = "preview_unavailable" if status == "missing" else "preview_error"
        stage_block(state_path, state, expected_digest, code,
                    "Existing preview evidence is missing or failed; no provisioning was attempted",
                    operation, "discovering_preview")
    if status != "ready":
        stage_block(state_path, state, expected_digest, "preview_error",
                    "Preview returned an unknown status", operation, "discovering_preview")
    pattern = delivery["capabilitySnapshot"]["config"].get("previewUrlPattern")
    if not safe_preview_url(evidence.get("url"), pattern):
        stage_block(state_path, state, expected_digest, "preview_unsafe_url",
                    "Preview URL is unsafe to share or violates the configured pattern",
                    operation, "discovering_preview")
    for field in ("deploymentId", "provider", "source", "evidenceUrl"):
        require_string(evidence.get(field), f"preview.{field}")
    delivery["preview"] = {
        "deploymentId": evidence["deploymentId"], "provider": evidence["provider"],
        "url": evidence["url"], "status": "ready", "observedForHeadSha": evidence["headSha"],
        "source": evidence["source"], "lastObservedAt": now(),
        "repositoryId": evidence["repositoryId"], "projectId": evidence["projectId"],
        "provenance": copy.deepcopy(provenance), "evidenceUrl": evidence["evidenceUrl"],
    }
    stage_transition(
        state, "preview_ready", operation, "Safe existing preview bound to current PR head",
        [evidence["deploymentId"], evidence["headSha"]],
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "preview_ready",
            "revision": state["revision"]}


def completed_implementation_sources(
    state: dict[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    root = Path(state["repository"]["rootIdentity"]).resolve()
    spec_root = (root / state["spec"]["path"]).resolve()
    stories = sorted((spec_root / "user-stories").glob("story-*.md"))
    source_records: list[dict[str, str]] = []
    scenarios: list[dict[str, str]] = []
    completed_count = 0
    for story in stories:
        text = story.read_text(encoding="utf-8")
        if status_value(text) != "Completed":
            continue
        completed_count += 1
        relative = story.relative_to(root).as_posix()
        source_records.append({"path": relative, "sha256": digest_bytes(story.read_bytes())})
        title_match = re.search(r"(?m)^# (Story \d+:[^\n]+)$", text)
        title = title_match.group(1) if title_match else story.stem
        acceptance = [
            item.strip() for item in re.findall(r"(?m)^- \[x\] (Given .+)$", text)
        ]
        if not acceptance:
            raise ContractError("uat_derivation_mismatch", f"{relative} lacks completed acceptance criteria")
        wwb_at = text.find("## What Was Built")
        if wwb_at < 0 or not text[wwb_at:].strip():
            raise ContractError("uat_derivation_mismatch", f"{relative} lacks What Was Built evidence")
        for item in acceptance:
            scenarios.append({"story": title, "source": "Acceptance Criteria", "text": item})
        for item in re.findall(r"(?m)^- \*\*(Error map rows|Shadow paths|Business rules|Experience):\*\* (.+)$", text):
            scenarios.append({"story": title, "source": item[0], "text": item[1].strip()})
        wwb_summary = " ".join(line.strip() for line in text[wwb_at:].splitlines()[1:] if line.strip())
        scenarios.append({"story": title, "source": "What Was Built", "text": wwb_summary})
    if completed_count == 0:
        raise ContractError("uat_derivation_mismatch", "UAT requires at least one completed implementation story")
    technical = spec_root / "sub-specs/technical-spec.md"
    if technical.is_file():
        relative = technical.relative_to(root).as_posix()
        source_records.append({"path": relative, "sha256": digest_bytes(technical.read_bytes())})
        text = technical.read_text(encoding="utf-8")
        for heading in ("Error & Rescue Map", "Shadow Paths", "Interaction Edge Cases"):
            start = text.find(f"## {heading}")
            if start >= 0:
                following = text.find("\n## ", start + 4)
                section = text[start:following if following >= 0 else len(text)].strip()
                scenarios.append({"story": "Cross-story", "source": heading, "text": section})
    source_records.sort(key=lambda item: item["path"])
    scenarios.sort(key=lambda item: (item["story"], item["source"], item["text"]))
    return source_records, scenarios


def render_uat(state: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, list[dict[str, str]], str]:
    delivery = active_delivery(state)
    if state["status"] != "preview_ready" or not delivery["preview"]:
        raise ContractError("invalid_transition", "UAT derivation requires a current ready preview")
    if evidence.get("headSha") != delivery["pr"]["headSha"]:
        raise ContractError("uat_stale", "UAT evidence is not bound to the current PR head")
    warnings = evidence.get("warnings")
    instructions = evidence.get("validationInstructions")
    if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
        raise ContractError("uat_derivation_mismatch", "UAT warnings must be a list of strings")
    if not isinstance(instructions, list) or not instructions or any(
        not isinstance(item, str) or not item for item in instructions
    ):
        raise ContractError("uat_derivation_mismatch", "UAT validation instructions are required")
    require_string(evidence.get("recommendedVersion"), "uat.recommendedVersion")
    require_string(evidence.get("releaseConsequences"), "uat.releaseConsequences")
    sources, scenarios = completed_implementation_sources(state)
    source_digest = digest_json(sources)
    checks = sorted(
        delivery["checks"], key=lambda item: (item["requiredBy"], item["name"], item["id"])
    )
    lines = [
        f"# UAT Plan: {state['spec']['id']}",
        "",
        f"> **PR:** #{delivery['pr']['number']} — {delivery['pr']['url']}",
        f"> **Head SHA:** `{delivery['pr']['headSha']}`",
        f"> **Implementation Source Digest:** `{source_digest}`",
        "",
        "## Staging Evidence",
        "",
        f"- Provider repository: `{delivery['capabilitySnapshot']['repositoryId']}`",
        f"- Preview: {delivery['preview']['url']}",
        f"- Preview deployment: `{delivery['preview']['deploymentId']}`",
        f"- Preview provenance: `{delivery['preview']['provenance']['integrationId']}`",
        "",
        "## Required Checks",
        "",
    ]
    lines.extend(
        f"- `{item['name']}` ({item['requiredBy']}): {item['status']} — `{item['id']}`"
        for item in checks
    )
    lines.extend(["", "## Preview Validation", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(instructions, 1))
    lines.extend(["", "## Material Warnings", ""])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend([
        "",
        "## Release Consequences",
        "",
        f"- Proposed version: `{evidence['recommendedVersion']}`",
        f"- Consequences: {evidence['releaseConsequences']}",
        "",
        "## Implementation Sources",
        "",
    ])
    lines.extend(f"- `{item['path']}` — `{item['sha256']}`" for item in sources)
    lines.extend(["", "## Implementation-Derived Scenarios", ""])
    for index, item in enumerate(scenarios, 1):
        lines.extend([
            f"### Scenario {index}: {item['story']} — {item['source']}",
            "",
            item["text"],
            "",
            "**Status:** [ ] Pass  [ ] Fail",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n", sources, source_digest


def derive_uat(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, _, evidence = stage_input(args, "recommend-uat-derivation-v1")
    content, sources, source_digest = render_uat(state, evidence)
    output = Path(args.output).resolve()
    expected = (Path(state["repository"]["rootIdentity"]) / state["spec"]["path"] / "uat-plan.md").resolve()
    if output != expected:
        raise ContractError("uat_unavailable", "recommended UAT output must be the canonical spec uat-plan.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode()
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {
        "schema": "recommend-uat-derived-v1", "path": output.relative_to(
            Path(state["repository"]["rootIdentity"])
        ).as_posix(),
        "digestSha256": digest_bytes(data), "sourceDigestSha256": source_digest,
        "sourcePaths": [item["path"] for item in sources],
        "sourceDigests": {item["path"]: item["sha256"] for item in sources},
        "headSha": evidence["headSha"],
    }


def record_uat(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-uat-evidence-v1")
    require_zero_pending_mutation_audits(state)
    path = safe_repo_file(state, evidence.get("path"), "uat_unavailable")
    expected_content, sources, source_digest = render_uat(state, evidence)
    observed_digest = digest_bytes(path.read_bytes())
    expected_digest_value = digest_bytes(expected_content.encode())
    source_paths = [item["path"] for item in sources]
    source_digests = {item["path"]: item["sha256"] for item in sources}
    if (
        path.read_text(encoding="utf-8") != expected_content
        or observed_digest != expected_digest_value
        or evidence.get("digestSha256") != observed_digest
        or evidence.get("sourceDigestSha256") != source_digest
        or evidence.get("sourcePaths") != source_paths
        or evidence.get("sourceDigests") != source_digests
    ):
        raise ContractError(
            "uat_derivation_mismatch",
            "UAT bytes, source paths/digests, enrichment, or generated digest are not canonical",
        )
    delivery = active_delivery(state)
    delivery["uat"] = {
        "path": evidence["path"], "digestSha256": observed_digest,
        "sourceDigestSha256": source_digest, "sourcePaths": source_paths,
        "sourceDigests": source_digests, "observedForHeadSha": evidence["headSha"],
        "recommendedVersion": evidence["recommendedVersion"],
        "releaseConsequences": evidence["releaseConsequences"],
        "validationInstructions": copy.deepcopy(evidence["validationInstructions"]),
        "warnings": copy.deepcopy(evidence["warnings"]), "generatedAt": now(),
    }
    stage_transition(
        state, "awaiting_approval", f"uat:{evidence['headSha']}:{observed_digest}",
        "Deterministic implementation-derived UAT evidence persisted",
        [evidence["path"], observed_digest, source_digest, evidence["headSha"]],
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "awaiting_approval",
            "uatDigestSha256": observed_digest, "sourceDigestSha256": source_digest,
            "revision": state["revision"]}


def record_approval(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-approval-event-v1")
    delivery = active_delivery(state)
    decision = evidence.get("decision")
    if decision == "silence":
        return {"schema": "recommend-staging-result-v1", "status": state["status"],
                "action": "none", "revision": state["revision"]}
    require_zero_pending_mutation_audits(state)
    if state["status"] not in {"awaiting_approval", "production_approved"}:
        raise ContractError("invalid_transition", "approval event is not current")
    event_id = evidence.get("eventId")
    if delivery.get("approval") and delivery["approval"].get("eventId") == event_id:
        return {"schema": "recommend-staging-result-v1", "status": state["status"],
                "action": "deduplicated", "revision": state["revision"]}
    for field in ("actor", "eventId", "interactionId", "occurredAt"):
        require_string(evidence.get(field), f"approval.{field}")
    if evidence["interactionId"] != evidence["eventId"]:
        raise ContractError("approval_interaction_invalid", "approval interaction and event IDs must be stable")
    head = delivery["pr"]["headSha"]
    if evidence.get("headSha") != head:
        raise ContractError("approval_stale", "approval event does not bind the current PR head")
    if decision not in {"approve", "reject"}:
        raise ContractError("invalid_evidence", "approval decision must be approve, reject, or silence")
    checks_evidence = delivery.get("checksEvidence")
    capability = delivery["capabilitySnapshot"]
    capability_projection = {key: value for key, value in capability.items() if key != "digestSha256"}
    capability_digest = digest_json(capability_projection)
    operation_key = deterministic_operation_key(
        "approval", capability["repositoryId"], delivery["pr"]["providerId"], head,
        checks_evidence.get("providerRequiredSetDigestSha256") if checks_evidence else "",
        delivery["preview"]["deploymentId"] if delivery.get("preview") else "",
        delivery["uat"]["digestSha256"] if delivery.get("uat") else "",
        evidence["eventId"],
    )
    if decision == "approve":
        reconciliation = evidence.get("reconciliation")
        if not isinstance(reconciliation, dict):
            raise ContractError(
                "approval_reconciliation_missing",
                "Fresh PR/check/preview/UAT reconciliation is required immediately before approval",
            )
        fresh_pr = reconciliation.get("pullRequest")
        fresh_checks = reconciliation.get("checks")
        fresh_preview = reconciliation.get("preview")
        fresh_statuses = reconciliation.get("checkStatuses")
        required_ids = checks_evidence.get("requiredCheckIds") if checks_evidence else None
        attempt_id = reconciliation.get("attemptId")
        try:
            occurred_at = parse_utc_rfc3339(evidence["occurredAt"], "approval.occurredAt")
            presentation_at = parse_utc_rfc3339(
                reconciliation.get("presentationStartedAt"), "approval.presentationStartedAt"
            )
            queried_at = parse_utc_rfc3339(
                reconciliation.get("queriedAt"), "approval.queriedAt"
            )
            pr_observed_at = parse_utc_rfc3339(
                fresh_pr.get("observedAt") if isinstance(fresh_pr, dict) else None,
                "approval.pullRequest.observedAt",
            )
            checks_observed_at = parse_utc_rfc3339(
                fresh_checks.get("observedAt") if isinstance(fresh_checks, dict) else None,
                "approval.checks.observedAt",
            )
            preview_observed_at = parse_utc_rfc3339(
                fresh_preview.get("observedAt") if isinstance(fresh_preview, dict) else None,
                "approval.preview.observedAt",
            )
            uat_observed_at = parse_utc_rfc3339(
                reconciliation.get("uatObservedAt"), "approval.uatObservedAt"
            )
            persisted_latest = max(
                parse_utc_rfc3339(delivery["pr"]["observedAt"], "delivery.pr.observedAt"),
                parse_utc_rfc3339(checks_evidence["lastObservedAt"], "checks.lastObservedAt"),
                parse_utc_rfc3339(delivery["preview"]["lastObservedAt"], "preview.lastObservedAt"),
                parse_utc_rfc3339(delivery["uat"]["generatedAt"], "uat.generatedAt"),
            )
        except ContractError as exc:
            raise ContractError("approval_reconciliation_temporal", exc.message) from exc
        observations = [pr_observed_at, checks_observed_at, preview_observed_at, uat_observed_at]
        wall_clock = datetime.now(timezone.utc)
        freshness = min(
            300,
            duration_seconds(capability["config"]["ciWaitTimeout"], "CI wait timeout"),
            duration_seconds(capability["config"]["previewWaitTimeout"], "preview wait timeout"),
        )
        if (
            presentation_at < persisted_latest
            or any(observed < presentation_at for observed in observations)
            or queried_at < max(observations)
            or occurred_at < queried_at
            or max(observations + [queried_at, occurred_at]) > wall_clock + timedelta(seconds=30)
            or wall_clock - min(observations) > timedelta(seconds=freshness)
        ):
            raise ContractError(
                "approval_reconciliation_temporal",
                "Approval observations are stale, out of order, or outside bounded clock skew",
            )
        if (
            reconciliation.get("operationKey") != operation_key
            or not isinstance(attempt_id, str)
            or not attempt_id
            or fresh_pr.get("attemptId") != attempt_id
            or fresh_checks.get("attemptId") != attempt_id
            or fresh_preview.get("attemptId") != attempt_id
            or reconciliation.get("stateRevision") != state["revision"]
            or reconciliation.get("stateDigestSha256") != expected_digest
            or reconciliation.get("capabilitySnapshotDigestSha256") != capability_digest
            or reconciliation.get("uatDigestSha256") != delivery["uat"]["digestSha256"]
            or any(fresh_pr.get(field) != delivery["pr"].get(field) for field in (
                "providerId", "number", "url", "repositoryId", "baseBranch",
                "headBranch", "headSha", "state",
            ))
            or not isinstance(fresh_checks, dict)
            or fresh_checks.get("provider") != capability["provider"]
            or fresh_checks.get("repositoryId") != capability["repositoryId"]
            or fresh_checks.get("headSha") != head
            or fresh_checks.get("requiredCheckIds") != required_ids
            or fresh_checks.get("providerRequiredSetDigestSha256")
                != checks_evidence.get("providerRequiredSetDigestSha256")
            or not isinstance(fresh_statuses, dict)
            or set(fresh_statuses) != set(required_ids or [])
            or any(status != "success" for status in fresh_statuses.values())
            or not isinstance(fresh_preview, dict)
            or fresh_preview.get("status") != "ready"
            or fresh_preview.get("provider") != delivery["preview"]["provider"]
            or fresh_preview.get("source") != delivery["preview"]["source"]
            or fresh_preview.get("repositoryId") != capability["repositoryId"]
            or fresh_preview.get("projectId") != capability["config"]["previewProjectId"]
            or fresh_preview.get("deploymentId") != delivery["preview"]["deploymentId"]
            or fresh_preview.get("headSha") != head
            or fresh_preview.get("provenance") != delivery["preview"]["provenance"]
        ):
            raise ContractError(
                "approval_reconciliation_stale",
                "Fresh approval reconciliation does not match current canonical evidence",
            )
    require_audit_binding(
        state, evidence.get("auditEntryId"), operation_key, pending=False
    )
    delivery["approval"] = {
        "status": "approved" if decision == "approve" else "rejected",
        "decision": decision, "actor": evidence["actor"], "eventId": evidence["eventId"],
        "interactionId": evidence["interactionId"], "approvedPrHeadSha": head if decision == "approve" else None,
        "approvedAt": evidence["occurredAt"] if decision == "approve" else None,
        "uatPlanSha256": delivery["uat"]["digestSha256"],
        "previewUrl": delivery["preview"]["url"],
        "recommendedVersion": delivery["uat"].get("recommendedVersion"),
        "recommendationEntryId": evidence["auditEntryId"],
        "reconciliationOperationKey": operation_key,
        "capabilitySnapshotDigestSha256": capability_digest,
        "invalidatedAt": None, "invalidationReason": None,
    }
    target = "production_approved" if decision == "approve" else "implementing"
    stage_transition(
        state, target, operation_key,
        "Explicit production approval persisted" if decision == "approve"
        else "Production approval rejected; returning to implementation",
        [evidence["eventId"], head],
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": target,
            "revision": state["revision"]}


def revalidate_staging(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(
        args, "recommend-staging-revalidation-v1"
    )
    delivery = active_delivery(state)
    require_zero_pending_mutation_audits(state)
    pr = evidence.get("pullRequest")
    if not isinstance(pr, dict) or pr.get("repositoryId") != evidence.get("repositoryId"):
        raise ContractError("pr_mismatch", "revalidation repository identity is inconsistent")
    current = delivery.get("pr")
    if not current or any(pr.get(field) != current.get(field) for field in ("providerId", "baseBranch", "headBranch")):
        raise ContractError("pr_mismatch", "revalidation pull request identity changed")
    new_head = pr.get("headSha")
    if not GIT_SHA_RE.fullmatch(new_head or ""):
        raise ContractError("invalid_evidence", "revalidation head SHA is invalid")
    if new_head == current["headSha"]:
        return {"schema": "recommend-staging-result-v1", "status": state["status"],
                "action": "unchanged", "revision": state["revision"]}
    old_head = current["headSha"]
    current["headSha"] = new_head
    delivery["checks"] = []
    delivery.pop("checksEvidence", None)
    delivery["preview"] = None
    delivery["uat"] = None
    if delivery.get("approval"):
        delivery["approval"].update({
            "status": "invalidated", "invalidatedAt": now(),
            "invalidationReason": f"PR head changed from {old_head} to {new_head}",
        })
    stage_transition(
        state, "waiting_ci", f"invalidate:{current['providerId']}:{new_head}",
        "PR head changed; checks, preview, UAT, and approval were invalidated",
        [old_head, new_head],
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "waiting_ci",
            "invalidatedHeadSha": old_head, "currentHeadSha": new_head,
            "revision": state["revision"]}


MERGE_STRATEGIES = {"merge", "squash", "rebase"}
RELEASE_SUBSTEP_ORDER = [
    "version-reconcile", "changelog-write", "release-commit",
    "tag-create", "push-commit", "push-tag", "provider-release",
]


def _pending_mutation_entry_ids(state: dict[str, Any]) -> list[str]:
    """Return pending audit entry IDs that contain a mutation operation key."""
    _, observed, text = current_log(state)
    unresolved: list[str] = []
    for entry_id in observed["pendingEntryIds"]:
        match = re.search(
            rf"(?ms)^## {re.escape(entry_id)} — .+?(?=^## REC-|\Z)", text
        )
        body = match.group(0) if match else ""
        if re.search(r"operation key (?:ship|pr-create|approval|merge):[0-9a-f]{64}", body):
            unresolved.append(entry_id)
    return unresolved


def record_merge_attempt(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-merge-attempt-v1")
    delivery = active_delivery(state)
    # Merge attempt uses a pending audit entry (like PR create); verify there are no other pending
    # mutation entries besides the one we're about to bind.
    audit_entry_id = evidence.get("auditEntryId")
    pending_ids = _pending_mutation_entry_ids(state)
    other_pending = [eid for eid in pending_ids if eid != audit_entry_id]
    if other_pending:
        raise ContractError(
            "mutation_audit_pending",
            f"Mutation-related recommendation entries must be finalized before merging: {other_pending}",
        )
    if state["status"] != "production_approved":
        raise ContractError("invalid_transition", "merge attempt requires production_approved state")
    approval = delivery.get("approval")
    if not approval or approval.get("status") != "approved":
        raise ContractError("approval_invalid", "merge requires a valid approved status")
    current_head = delivery["pr"]["headSha"]
    if approval.get("approvedPrHeadSha") != current_head:
        raise ContractError("approval_stale", "approval head SHA does not match current PR head")
    strategy = evidence.get("strategy")
    if strategy not in MERGE_STRATEGIES:
        raise ContractError("invalid_evidence", f"merge strategy must be one of: {', '.join(sorted(MERGE_STRATEGIES))}")
    if evidence.get("bypassProtection"):
        raise ContractError("policy_violation", "branch protection bypass is not permitted")
    if evidence.get("forceStrategy"):
        raise ContractError("policy_violation", "force strategy escalation is not permitted")
    fresh_pr = evidence.get("freshPr")
    if not isinstance(fresh_pr, dict):
        raise ContractError("invalid_evidence", "merge attempt requires fresh PR re-read evidence")
    if fresh_pr.get("headSha") != current_head:
        raise ContractError("merge_head_mismatch", "fresh PR head SHA does not match persisted head")
    if fresh_pr.get("state") not in {"open"}:
        raise ContractError("pr_not_open", "PR must be open to merge")
    capability = delivery["capabilitySnapshot"]
    # provider and repositoryId come from capability snapshot; others from stored PR
    if fresh_pr.get("provider") != capability["provider"]:
        raise ContractError("pr_identity_changed", "fresh PR provider does not match capability snapshot")
    if fresh_pr.get("repositoryId") != capability["repositoryId"]:
        raise ContractError("pr_identity_changed", "fresh PR repositoryId does not match capability snapshot")
    for field in ("providerId", "baseBranch", "headBranch"):
        if fresh_pr.get(field) != delivery["pr"].get(field):
            raise ContractError("pr_identity_changed", f"fresh PR {field} does not match persisted value")
    operation_key = deterministic_operation_key(
        "merge", capability["repositoryId"], delivery["pr"]["providerId"], current_head, strategy,
    )
    require_audit_binding(state, evidence.get("auditEntryId"), operation_key, pending=True)
    delivery["merge"] = {
        "strategy": strategy,
        "approvedPrHeadSha": current_head,
        "providerId": delivery["pr"]["providerId"],
        "mergeCommitSha": None,
        "defaultBranchContainsMerge": False,
        "mergeAttemptedAt": now(),
        "mergedAt": None,
        "verifiedAt": None,
        "providerOperationId": evidence.get("providerOperationId"),
        "operationKey": operation_key,
        "auditEntryId": evidence.get("auditEntryId"),
    }
    stage_transition(
        state, "merging", operation_key,
        f"Merge attempt recorded: strategy={strategy}, head={current_head}",
        [delivery["pr"]["providerId"], current_head],
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "merging", "revision": state["revision"]}


def record_merge_result(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-merge-result-v1")
    delivery = active_delivery(state)
    if state["status"] != "merging":
        raise ContractError("invalid_transition", "merge result is accepted only while merging")
    merge = delivery.get("merge")
    if not isinstance(merge, dict) or not merge.get("operationKey"):
        raise ContractError("invalid_state", "merge attempt must be recorded before merge result")
    merge_commit_sha = evidence.get("mergeCommitSha")
    if not GIT_SHA_RE.fullmatch(merge_commit_sha or ""):
        raise ContractError("invalid_evidence", "mergeCommitSha is invalid")
    if evidence.get("outcome") not in {"merged", "already_merged"}:
        raise ContractError("invalid_evidence", "merge result outcome must be merged or already_merged")
    provider_op_id = evidence.get("providerOperationId")
    if not isinstance(provider_op_id, str) or not provider_op_id:
        raise ContractError("invalid_evidence", "providerOperationId is required for merge result")
    require_audit_binding(state, evidence.get("auditEntryId"), merge["operationKey"], pending=False)
    merge.update({
        "mergeCommitSha": merge_commit_sha,
        "mergedAt": evidence.get("mergedAt") or now(),
        "providerOperationId": provider_op_id,
        "auditEntryId": evidence.get("auditEntryId"),
    })
    state["transitions"].append({
        "sequence": len(state["transitions"]) + 1,
        "from": "merging", "to": "merging",
        "startedAt": now(), "completedAt": now(), "attempt": 1,
        "operationKey": merge["operationKey"],
        "evidenceSummary": f"Merge result recorded: {merge_commit_sha}",
        "persistedIdentifiers": [merge_commit_sha, provider_op_id],
        "outcome": "succeeded",
    })
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "merging",
            "mergeCommitSha": merge_commit_sha, "revision": state["revision"]}


def verify_ancestry(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-ancestry-verification-v1")
    delivery = active_delivery(state)
    if state["status"] != "merging":
        raise ContractError("invalid_transition", "ancestry verification requires merging state")
    merge = delivery.get("merge")
    if not isinstance(merge, dict) or not merge.get("mergeCommitSha"):
        raise ContractError("invalid_state", "merge result must be recorded before verifying ancestry")
    merge_commit = merge["mergeCommitSha"]
    default_branch_head = evidence.get("defaultBranchHeadSha")
    if not GIT_SHA_RE.fullmatch(default_branch_head or ""):
        raise ContractError("invalid_evidence", "defaultBranchHeadSha is invalid")
    if not isinstance(evidence.get("observedAt"), str):
        raise ContractError("invalid_evidence", "observedAt is required")
    capability = delivery["capabilitySnapshot"]
    repo_root = Path(state["repository"]["rootIdentity"]).resolve()
    if not git_commit_exists(repo_root, merge_commit):
        stage_block(
            state_path, state, expected_digest, "merge_commit_missing",
            f"Merge commit {merge_commit} is not present in local repository",
            f"ancestry:{merge_commit[:12]}:{default_branch_head[:12]}", "merging",
        )
    if merge_commit != default_branch_head and \
            not git_is_ancestor(repo_root, merge_commit, default_branch_head):
        stage_block(
            state_path, state, expected_digest, "merge_ancestry_not_confirmed",
            f"Merge commit {merge_commit} is not present in default branch {capability['baseBranch']}",
            f"ancestry:{merge_commit[:12]}:{default_branch_head[:12]}", "merging",
        )
    merge["defaultBranchContainsMerge"] = True
    merge["verifiedAt"] = evidence["observedAt"]
    delivery["release"] = {
        "substeps": {},
        "startedAt": now(),
        "completedAt": None,
        "finalIdentifiers": None,
    }
    operation_key = deterministic_operation_key(
        "ancestry", capability["repositoryId"], merge_commit, default_branch_head,
    )
    # Avoid duplicate persistedIdentifiers when merge commit IS the default branch head
    ancestry_ids = [merge_commit] if merge_commit == default_branch_head else [merge_commit, default_branch_head]
    stage_transition(
        state, "releasing", operation_key,
        f"Merge commit {merge_commit} confirmed in default branch; entering release",
        ancestry_ids,
    )
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": "releasing", "revision": state["revision"]}


def _substep_identifiers(substep: str, evidence: dict[str, Any]) -> list[str]:
    if substep == "version-reconcile":
        version = evidence.get("version")
        if not isinstance(version, str) or not version:
            raise ContractError("invalid_evidence", "version-reconcile requires a non-empty version")
        return [version]
    if substep == "changelog-write":
        sha = evidence.get("sha")
        if not GIT_SHA_RE.fullmatch(sha or ""):
            raise ContractError("invalid_evidence", "changelog-write requires a valid git SHA")
        return [sha]
    if substep == "release-commit":
        sha = evidence.get("sha")
        if not GIT_SHA_RE.fullmatch(sha or ""):
            raise ContractError("invalid_evidence", "release-commit requires a valid git SHA")
        return [sha]
    if substep == "tag-create":
        tag, sha = evidence.get("tag"), evidence.get("sha")
        if not isinstance(tag, str) or not tag:
            raise ContractError("invalid_evidence", "tag-create requires a non-empty tag name")
        if not GIT_SHA_RE.fullmatch(sha or ""):
            raise ContractError("invalid_evidence", "tag-create requires a valid git SHA")
        return [tag, sha]
    if substep == "push-commit":
        sha = evidence.get("sha")
        if not GIT_SHA_RE.fullmatch(sha or ""):
            raise ContractError("invalid_evidence", "push-commit requires a valid git SHA")
        if evidence.get("forced"):
            raise ContractError("policy_violation", "force-push is not permitted")
        return [sha]
    if substep == "push-tag":
        tag = evidence.get("tag")
        if not isinstance(tag, str) or not tag:
            raise ContractError("invalid_evidence", "push-tag requires a non-empty tag name")
        if evidence.get("forced"):
            raise ContractError("policy_violation", "force-push tag is not permitted")
        return [tag]
    if substep == "provider-release":
        provider_id, url = evidence.get("providerId"), evidence.get("url")
        if not isinstance(provider_id, str) or not provider_id:
            raise ContractError("invalid_evidence", "provider-release requires a non-empty providerId")
        if not isinstance(url, str) or not url:
            raise ContractError("invalid_evidence", "provider-release requires a non-empty url")
        if evidence.get("publishNpm"):
            raise ContractError("policy_violation", "@sellke/writ npm publishing is not permitted")
        return [provider_id, url]
    raise ContractError("invalid_evidence", f"unknown substep: {substep}")


def record_release_substep(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-release-substep-v1")
    delivery = active_delivery(state)
    require_zero_pending_mutation_audits(state)
    if state["status"] not in {"releasing", "partially_released"}:
        raise ContractError("invalid_transition", "release substep requires releasing or partially_released state")
    release = delivery.get("release")
    if not isinstance(release, dict):
        raise ContractError("invalid_state", "delivery.release must be initialized before recording substeps")
    substep = evidence.get("substep")
    if substep not in RELEASE_SUBSTEP_ORDER:
        raise ContractError("invalid_evidence", f"substep must be one of: {', '.join(RELEASE_SUBSTEP_ORDER)}")
    evidence_digest = digest_json({k: v for k, v in evidence.items() if k not in {"schema", "auditEntryId"}})
    existing = release["substeps"].get(substep)
    if existing and existing.get("evidenceDigest") == evidence_digest:
        return {"schema": "recommend-staging-result-v1", "status": state["status"],
                "action": "deduplicated", "substep": substep, "revision": state["revision"]}
    if existing and existing.get("status") == "complete":
        stage_block(
            state_path, state, expected_digest, "release_substep_conflict",
            f"Substep {substep} already completed with different evidence",
            f"substep:{substep}", "partially_released",
        )
    substep_ids = _substep_identifiers(substep, evidence)
    capability = delivery["capabilitySnapshot"]
    substep_id = evidence.get("substepId") or evidence_digest
    operation_key = deterministic_operation_key(
        "substep", capability["repositoryId"], substep, substep_id,
    )
    require_audit_binding(state, evidence.get("auditEntryId"), operation_key, pending=False)
    release["substeps"][substep] = {
        "status": "complete",
        "completedAt": now(),
        "identifiers": substep_ids,
        "evidenceDigest": evidence_digest,
        "auditEntryId": evidence.get("auditEntryId"),
        "operationKey": operation_key,
    }
    state["transitions"].append({
        "sequence": len(state["transitions"]) + 1,
        "from": state["status"], "to": state["status"],
        "startedAt": now(), "completedAt": now(), "attempt": 1,
        "operationKey": operation_key,
        "evidenceSummary": f"Release substep {substep} completed",
        "persistedIdentifiers": substep_ids,
        "outcome": "succeeded",
    })
    current_status = state["status"]
    if current_status == "partially_released":
        idx = RELEASE_SUBSTEP_ORDER.index(substep)
        prior_complete = all(s in release["substeps"] for s in RELEASE_SUBSTEP_ORDER[:idx + 1])
        if prior_complete:
            state["status"] = "releasing"
            state["resumeTarget"] = "releasing"
    replace_state(state_path, state, expected_digest)
    return {"schema": "recommend-staging-result-v1", "status": state["status"],
            "substep": substep, "revision": state["revision"]}


def finalize_release(args: argparse.Namespace) -> dict[str, Any]:
    state_path, state, expected_digest, evidence = stage_input(args, "recommend-release-finalization-v1")
    delivery = active_delivery(state)
    require_zero_pending_mutation_audits(state)
    if state["status"] != "releasing":
        raise ContractError("invalid_transition", "finalize-release requires releasing state")
    release = delivery.get("release")
    if not isinstance(release, dict):
        raise ContractError("invalid_state", "delivery.release must be initialized")
    missing = [s for s in RELEASE_SUBSTEP_ORDER
               if s not in release["substeps"] or release["substeps"][s].get("status") != "complete"]
    if missing:
        raise ContractError(
            "release_substeps_incomplete",
            f"All release substeps must be complete before finalizing. Missing: {missing}",
        )
    seen: set[str] = set()
    all_identifiers: list[str] = []
    for s in RELEASE_SUBSTEP_ORDER:
        for ident in release["substeps"][s].get("identifiers", []):
            if ident not in seen:
                all_identifiers.append(ident)
                seen.add(ident)
    completed_at = now()
    release["completedAt"] = completed_at
    release["finalIdentifiers"] = all_identifiers
    merge = delivery.get("merge") or {}
    capability = delivery["capabilitySnapshot"]
    tag_ids = release["substeps"].get("tag-create", {}).get("identifiers", [""])
    operation_key = deterministic_operation_key(
        "finalize", capability["repositoryId"],
        merge.get("mergeCommitSha", ""),
        tag_ids[0] if tag_ids else "",
    )
    stage_transition(
        state, "complete", operation_key,
        "All release substeps complete; recommended delivery finalized",
        all_identifiers,
    )
    replace_state(state_path, state, expected_digest)
    return {
        "schema": "recommend-staging-result-v1",
        "status": "complete",
        "finalIdentifiers": all_identifiers,
        "revision": state["revision"],
    }


class ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError("invalid_arguments", message)


def parser() -> argparse.ArgumentParser:
    root = ContractArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="operation", required=True)
    start_parser = sub.add_parser("start")
    start_parser.add_argument("--repo", required=True)
    start_parser.add_argument("--spec", required=True)
    start_parser.add_argument("--state", required=True)
    start_parser.add_argument("--execution-id", required=True)
    start_parser.add_argument("--token", required=True)
    start_parser.add_argument("--entry-command", choices=("create-spec", "implement-spec", "implement-phase"), required=True)
    start_parser.add_argument("--invocation-json", required=True)
    start_parser.set_defaults(handler=start)

    context_parser = sub.add_parser("validate-context")
    context_parser.add_argument("--state", required=True)
    context_parser.add_argument("--context", required=True)
    context_parser.set_defaults(handler=validate_context)

    reserve = sub.add_parser("reserve-worktree")
    reserve.add_argument("--state", required=True)
    reserve.add_argument("--repo", required=True)
    reserve.add_argument("--launch-result", required=True)
    reserve.set_defaults(handler=reserve_worktree)

    amendment = sub.add_parser("record-spec-lite-amendment")
    amendment.add_argument("--state", required=True)
    amendment.add_argument("--repo", required=True)
    amendment.add_argument("--story-id", required=True)
    amendment.add_argument("--dev-id", required=True)
    amendment.add_argument("--prior-sha256", required=True)
    amendment.add_argument("--review-result", required=True)
    amendment.set_defaults(handler=record_spec_lite_amendment)

    reconcile_parser = sub.add_parser("reconcile")
    reconcile_parser.add_argument("--state", required=True)
    reconcile_parser.add_argument("--repo", required=True)
    reconcile_parser.set_defaults(handler=reconcile)

    complete = sub.add_parser("complete-worktree")
    complete.add_argument("--state", required=True)
    complete.add_argument("--repo", required=True)
    complete.add_argument("--worktree-key", required=True)
    complete.set_defaults(handler=complete_worktree)

    normalize = sub.add_parser("normalize-result")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--execution-id", required=True)
    normalize.set_defaults(handler=normalize_result)

    for name, handler in (
        ("activate-staging", activate_staging),
        ("record-ship", record_ship),
        ("record-pr-lookup", record_pr_lookup),
        ("mark-pr-create-attempt", mark_pr_create_attempt),
        ("record-pr-created", record_pr_created),
        ("finalize-pr-audit", finalize_pr_audit),
        ("record-checks", record_checks),
        ("record-preview", record_preview),
        ("record-uat", record_uat),
        ("record-approval", record_approval),
        ("revalidate-staging", revalidate_staging),
        ("record-merge-attempt", record_merge_attempt),
        ("record-merge-result", record_merge_result),
        ("verify-ancestry", verify_ancestry),
        ("record-release-substep", record_release_substep),
        ("finalize-release", finalize_release),
    ):
        stage = sub.add_parser(name)
        stage.add_argument("--state", required=True)
        stage.add_argument("--evidence", required=True)
        stage.set_defaults(handler=handler)
    derive = sub.add_parser("derive-uat")
    derive.add_argument("--state", required=True)
    derive.add_argument("--evidence", required=True)
    derive.add_argument("--output", required=True)
    derive.set_defaults(handler=derive_uat)
    return root


def main() -> int:
    args: argparse.Namespace | None = None
    try:
        args = parser().parse_args()
        result = args.handler(args)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ContractError as exc:
        execution_id = getattr(args, "execution_id", "unknown") if args is not None else "unknown"
        operation = getattr(args, "operation", "recommend-state") if args is not None else "recommend-state"
        print(json.dumps(canonical_blocked_result(
            exc.code,
            exc.message,
            execution_id=execution_id,
            command=operation,
        ), sort_keys=True))
        return 2
    except Exception as exc:
        execution_id = getattr(args, "execution_id", "unknown") if args is not None else "unknown"
        operation = getattr(args, "operation", "recommend-state") if args is not None else "recommend-state"
        print(json.dumps(canonical_blocked_result(
            "operational_error",
            f"{type(exc).__name__}: {exc}",
            execution_id=execution_id,
            command=operation,
        ), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
