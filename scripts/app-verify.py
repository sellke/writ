#!/usr/bin/env python3
"""App verification runner (spec `2026-10-01-behavioral-verification`).

Reads a project's app-verification recipe (`.writ/docs/app-verification.md`,
grammar in `.writ/docs/app-verification-format.md`) and decides whether a
feature works from the exit code of the project's own check, never from an
agent's opinion.

Writ ships no runtime. This script runs only commands the recipe names,
keeps no state between runs, and runs no daemon — the `build-smoke.py`
posture.

Subcommands:
  validate --recipe PATH [--json]
  touched  --recipe PATH --changed FILE... [--json]
  run      --recipe PATH --spec DIR --run-label LABEL [--features id,...] [--json]

Without `--json`, stdout is exactly one `app-verify:` summary line (`touched`
prints matching feature IDs instead, one per line, when any match). With
`--json`, one JSON object (schema `app-verify-v1`) follows.

Exit codes:
  validate: 0 valid, 1 findings, 2 recipe missing or unreadable.
  touched:  0 (matches or none), 2 no recipe or invalid recipe.
  run:      0 every check passed, 1 any check, launch, or readiness failed,
            2 nothing ran (no recipe, invalid recipe, refused, unsupported
            platform, no runnable feature).

`run` writes `{spec}/evidence/<label>/<feature>/result.json` (schema
`app-verify-result-v1`) plus truncated `stdout.log`/`stderr.log`, and launch
output under `{spec}/evidence/<label>/_launch/`. Cleanup always runs: SIGTERM
to the process group it started, SIGKILL after a grace period, then the
recipe's `After` command. It never signals a process it did not start.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "app-verify-v1"
RESULT_SCHEMA = "app-verify-result-v1"

CHECK_TIMEOUT_S = 300
CLEANUP_GRACE_S = 10
READY_POLL_S = 0.5
AFTER_TIMEOUT_S = 120
LOG_CAP_BYTES = 256 * 1024
ARTIFACT_CAP_BYTES = 5 * 1024 * 1024

REQUIRED_SECTIONS = ("Launch", "Safety", "Login", "Feature Map", "Evidence", "Cleanup")

DEFAULT_READY_TIMEOUT_S = 120

_SETTING = re.compile(r"^\s*-\s+\*\*(?P<key>[^*]+?):\*\*\s*(?P<value>.*?)\s*$")
_SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$")
_FEATURE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_READY_URL = re.compile(r"^https?://\S+$")
_READY_PORT = re.compile(r"^port\s+(?P<port>\d{1,5})$", re.IGNORECASE)
_TIMEOUT = re.compile(r"^(?P<n>\d+)\s*s?$")
_SAFETY_NONE = re.compile(r"^none\s*(?:—|–|--?)\s*(?P<reason>\S.*)$", re.IGNORECASE)
_URL_CREDENTIALS = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://[^\s/@:]*:[^\s/@]+@")
_LONG_TOKEN = re.compile(r"(?<![A-Za-z0-9_+=])[A-Za-z0-9_+=]{32,}(?![A-Za-z0-9_+=])")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")
_BACKTICK_SPAN = re.compile(r"`[^`]*`")


class RecipeUnavailable(Exception):
    """Exit-2 conditions: the recipe file is missing or cannot be decoded."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class Variable:
    name: str
    allowed: list[str] = field(default_factory=list)
    never: list[str] = field(default_factory=list)


@dataclass
class Feature:
    id: str
    name: str
    paths: list[str]
    check: str | None
    human_only: str | None
    line: int


@dataclass
class Recipe:
    sections: list[str] = field(default_factory=list)
    launch_command: str | None = None
    ready_when: str | None = None
    ready_timeout_s: int = DEFAULT_READY_TIMEOUT_S
    reuse_running: bool = False
    safety_none_reason: str | None = None
    variables: list[Variable] = field(default_factory=list)
    env_file: str | None = None
    features: list[Feature] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    after: str | None = None

    def ready_port(self) -> int | None:
        match = _READY_PORT.match(self.ready_when or "")
        return int(match.group("port")) if match else None


# --- Parsing -----------------------------------------------------------------

def _unwrap(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def _split_list(value: str) -> list[str]:
    return [_unwrap(part) for part in value.split(",") if _unwrap(part)]


def _split_row(line: str) -> list[str]:
    """Split a table row on `|`, ignoring pipes inside backtick spans."""
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            current.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    cells.append("".join(current).strip())
    return cells


def _finding(code: str, detail: str, line: int | None = None) -> dict[str, Any]:
    return {"code": code, "detail": detail, "line": line}


def _parse(text: str) -> tuple[Recipe, list[dict[str, Any]]]:
    recipe = Recipe()
    findings: list[dict[str, Any]] = []
    sections: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        heading = _SECTION.match(line)
        if heading:
            current = heading.group("title").strip()
            sections.setdefault(current.lower(), [])
            recipe.sections.append(current)
            continue
        if current is not None:
            sections[current.lower()].append((number, line))

    for name in REQUIRED_SECTIONS:
        if name.lower() not in sections:
            findings.append(_finding("missing_section", name))

    _parse_launch(sections.get("launch", []), recipe, findings)
    _parse_safety(sections.get("safety", []), recipe, findings)
    _parse_features(sections.get("feature map", []), recipe, findings)
    for _, line in sections.get("evidence", []):
        setting = _SETTING.match(line)
        if setting and setting.group("key").strip().lower() == "artifacts":
            value = setting.group("value")
            recipe.artifacts = [] if value.strip().lower() == "none" else _split_list(value)
    for _, line in sections.get("cleanup", []):
        setting = _SETTING.match(line)
        if setting and setting.group("key").strip().lower() == "after":
            value = _unwrap(setting.group("value"))
            recipe.after = None if value.lower() in ("", "none") else value

    findings.extend(_scan_secrets(text))
    findings.sort(key=lambda f: (f["line"] or 0, f["code"]))
    return recipe, findings


def _parse_launch(lines: list[tuple[int, str]], recipe: Recipe,
                  findings: list[dict[str, Any]]) -> None:
    for number, line in lines:
        setting = _SETTING.match(line)
        if not setting:
            continue
        key = setting.group("key").strip().lower()
        value = _unwrap(setting.group("value"))
        if key == "command" and value:
            recipe.launch_command = value
        elif key == "ready when":
            recipe.ready_when = value
        elif key == "ready timeout":
            match = _TIMEOUT.match(value)
            if match and int(match.group("n")) > 0:
                recipe.ready_timeout_s = int(match.group("n"))
            else:
                findings.append(_finding("bad_timeout", f"Ready timeout {value!r}", number))
        elif key == "reuse running instance":
            recipe.reuse_running = value.lower() == "yes"
    if lines and recipe.launch_command is None:
        findings.append(_finding("missing_launch_command", "Launch has no Command"))
    if lines and not (_READY_URL.match(recipe.ready_when or "")
                      or _READY_PORT.match(recipe.ready_when or "")):
        findings.append(_finding(
            "missing_ready", "Ready when must be an http(s) URL or `port N`"))


def _parse_safety(lines: list[tuple[int, str]], recipe: Recipe,
                  findings: list[dict[str, Any]]) -> None:
    if not lines:
        return
    for number, line in lines:
        setting = _SETTING.match(line)
        if not setting:
            continue
        key = setting.group("key").strip().lower()
        value = _unwrap(setting.group("value"))
        if key == "safety":
            match = _SAFETY_NONE.match(value)
            if match:
                recipe.safety_none_reason = match.group("reason").strip()
        elif key == "variable" and value:
            recipe.variables.append(Variable(name=value))
        elif key in ("allowed", "never") and recipe.variables:
            target = recipe.variables[-1].allowed if key == "allowed" else recipe.variables[-1].never
            target.extend(_split_list(value))
        elif key == "env file" and value:
            recipe.env_file = value
    if not recipe.variables and recipe.safety_none_reason is None:
        findings.append(_finding(
            "missing_safety",
            "Safety names no Variable and no `Safety: none — <reason>`"))
    for variable in recipe.variables:
        if not variable.allowed:
            findings.append(_finding(
                "missing_safety", f"Variable {variable.name} has no Allowed pattern"))


def _parse_features(lines: list[tuple[int, str]], recipe: Recipe,
                    findings: list[dict[str, Any]]) -> None:
    rows = [(n, line) for n, line in lines if line.strip().startswith("|")]
    if not rows:
        return
    header_number, header = rows[0]
    if [c.lower() for c in _split_row(header)] != ["id", "feature", "paths", "check"]:
        findings.append(_finding(
            "bad_feature_row", "header must be `ID | Feature | Paths | Check`", header_number))
        return
    seen: set[str] = set()
    for number, line in rows[1:]:
        cells = _split_row(line)
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        if len(cells) != 4:
            findings.append(_finding("bad_feature_row", f"{len(cells)} cells, expected 4", number))
            continue
        feature_id, name, paths_cell, check_cell = cells
        paths = _split_list(paths_cell)
        check: str | None = None
        human_only: str | None = None
        if check_cell.lower().startswith("human-only:"):
            human_only = check_cell.split(":", 1)[1].strip()
            if not human_only:
                findings.append(_finding("bad_feature_row", "human-only needs a reason", number))
                continue
        elif len(check_cell) >= 2 and check_cell.startswith("`") and check_cell.endswith("`") \
                and check_cell.count("`") == 2 and check_cell[1:-1].strip():
            check = check_cell[1:-1].strip()
            if not paths:
                findings.append(_finding("bad_feature_row", "a check row needs Paths", number))
                continue
        else:
            findings.append(_finding(
                "bad_feature_row", "Check must be a backticked command or `human-only: <reason>`",
                number))
            continue
        if not _FEATURE_ID.match(feature_id):
            findings.append(_finding("bad_feature_id", f"{feature_id!r} is not kebab-case", number))
            continue
        if feature_id in seen:
            findings.append(_finding("duplicate_feature_id", feature_id, number))
            continue
        seen.add(feature_id)
        recipe.features.append(Feature(
            id=feature_id, name=name, paths=paths, check=check,
            human_only=human_only, line=number))


def _scan_secrets(text: str) -> list[dict[str, Any]]:
    """Names and patterns only. The finding cites the line, never the value."""
    findings: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if _URL_CREDENTIALS.search(line):
            findings.append(_finding("secret_value", "URL with embedded credentials", number))
        elif any(not _ENV_NAME.match(token)
                 for token in _LONG_TOKEN.findall(_BACKTICK_SPAN.sub("", line))):
            findings.append(_finding("secret_value", "32+ character token", number))
    return findings


def parse_recipe(text: str) -> Recipe:
    return _parse(text)[0]


def validate_text(text: str) -> list[dict[str, Any]]:
    return _parse(text)[1]


def load_recipe(path: Path) -> str:
    if not path.is_file():
        raise RecipeUnavailable("no_recipe")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RecipeUnavailable(f"recipe_unreadable: {type(exc).__name__}") from exc


def describe_finding(finding: dict[str, Any]) -> str:
    where = f" line {finding['line']}" if finding.get("line") else ""
    return f"{finding['code']} ({finding['detail']}{where})"


def _load_valid(path: Path) -> tuple[Recipe, str]:
    """The recipe and its text, or RecipeUnavailable naming why not."""
    text = load_recipe(path)
    recipe, findings = _parse(text)
    if findings:
        raise RecipeUnavailable(f"recipe_invalid: {describe_finding(findings[0])}")
    return recipe, text


# --- Feature selection -------------------------------------------------------

def touched_features(recipe: Recipe, changed: list[str]) -> list[str]:
    """IDs of features with a check whose Paths match a changed path."""
    paths = [p[2:] if p.startswith("./") else p for p in changed]
    return [
        feature.id for feature in recipe.features
        if feature.check and any(fnmatch.fnmatchcase(path, glob)
                                 for glob in feature.paths for path in paths)
    ]


# --- Safety ------------------------------------------------------------------

def _read_env_file(path: Path) -> dict[str, str]:
    """`KEY=VALUE` lines only. Read, never written. Unreadable counts as empty."""
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return values
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def safety_refusal(recipe: Recipe, env: Mapping[str, str], cwd: Path) -> str | None:
    """None when every variable resolves to an allowed target, else the reason.
    The reason names the variable, never its value."""
    file_values: dict[str, str] | None = None
    for variable in recipe.variables:
        value = env.get(variable.name)
        if not value and recipe.env_file:
            if file_values is None:
                file_values = _read_env_file(cwd / recipe.env_file)
            value = file_values.get(variable.name)
        if not value:
            return f"{variable.name} unset"
        if any(fnmatch.fnmatchcase(value, pattern) for pattern in variable.never):
            return f"{variable.name} matches a Never pattern"
        if not any(fnmatch.fnmatchcase(value, pattern) for pattern in variable.allowed):
            return f"{variable.name} does not match an allowed target"
    return None


# --- Process control ---------------------------------------------------------

def _is_posix() -> bool:
    return os.name == "posix"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def probe_ready(target: str) -> bool:
    """HTTP: any status below 500. `port N`: a TCP connect to 127.0.0.1:N."""
    match = _READY_PORT.match(target)
    if match:
        try:
            with socket.create_connection(("127.0.0.1", int(match.group("port"))), timeout=1):
                return True
        except OSError:
            return False
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(target, timeout=2) as response:
            return response.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except (OSError, ValueError):
        return False


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_group(pgid: int, sig: int) -> None:
    try:
        os.killpg(pgid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def stop_group(proc: subprocess.Popen, grace_s: float) -> str | None:
    """SIGTERM the group `proc` leads, wait, then SIGKILL. Returns a note when
    SIGKILL was needed. Only ever signals the session this script started."""
    pgid = proc.pid
    _signal_group(pgid, signal.SIGTERM)
    deadline = time.monotonic() + grace_s
    while time.monotonic() < deadline:
        proc.poll()
        if not _group_alive(pgid):
            return None
        time.sleep(0.05)
    _signal_group(pgid, signal.SIGKILL)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    return f"process group {pgid} ignored SIGTERM for {grace_s:g}s; sent SIGKILL"


def _truncate(path: Path) -> bool:
    if path.stat().st_size <= LOG_CAP_BYTES:
        return False
    with open(path, "r+b") as handle:
        handle.truncate(LOG_CAP_BYTES)
    return True


def _tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def copy_artifacts(recipe: Recipe, cwd: Path, feature_dir: Path) -> list[dict[str, Any]]:
    """Copy named artifacts up to the per-feature cap. Never fails the run."""
    records: list[dict[str, Any]] = []
    budget = ARTIFACT_CAP_BYTES
    for rel in recipe.artifacts:
        source = cwd / rel
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            records.append({"path": rel, "status": "outside_project"})
            continue
        if not source.exists():
            records.append({"path": rel, "status": "missing"})
            continue
        size = _tree_size(source)
        if size > budget:
            records.append({"path": rel, "status": "too_large", "bytes": size})
            continue
        target = feature_dir / "artifacts" / rel.rstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)
        except OSError as exc:
            records.append({"path": rel, "status": "copy_failed", "detail": type(exc).__name__})
            continue
        budget -= size
        records.append({"path": rel, "status": "copied", "bytes": size})
    return records


def run_check(feature: Feature, recipe: Recipe, recipe_sha: str, feature_dir: Path,
              env: Mapping[str, str], cwd: Path, timeout_s: float,
              grace_s: float) -> dict[str, Any]:
    """Run one check in its own session; its exit code is the verdict."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = feature_dir / "stdout.log", feature_dir / "stderr.log"
    check_env = dict(env)
    check_env["APP_VERIFY_EVIDENCE_DIR"] = str(feature_dir.resolve())
    started_at, started = _now(), time.monotonic()
    exit_code: int | None
    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        proc = subprocess.Popen(
            feature.check or "", shell=True, cwd=str(cwd), env=check_env,
            stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
        try:
            exit_code = proc.wait(timeout=timeout_s)
            verdict = "pass" if exit_code == 0 else "fail"
        except subprocess.TimeoutExpired:
            exit_code, verdict = None, "fail (timeout)"
        finally:
            stop_group(proc, grace_s if exit_code is None else 0)
    result = {
        "schema": RESULT_SCHEMA,
        "feature": feature.id,
        "command": feature.check,
        "exit_code": exit_code,
        "verdict": verdict,
        "started_at": started_at,
        "ended_at": _now(),
        "duration_s": round(time.monotonic() - started, 3),
        "recipe_sha256": recipe_sha,
        "truncated": {"stdout": _truncate(stdout_path), "stderr": _truncate(stderr_path)},
        "artifacts": copy_artifacts(recipe, cwd, feature_dir),
    }
    (feature_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_verification(recipe_path: Path, spec_dir: Path, label: str,
                     features: list[str] | None = None, *,
                     env: Mapping[str, str] | None = None, cwd: Path | None = None,
                     check_timeout_s: float = CHECK_TIMEOUT_S,
                     cleanup_grace_s: float = CLEANUP_GRACE_S) -> tuple[int, str, dict[str, Any]]:
    """Safety, launch, checks, evidence, cleanup. Returns (exit, summary, payload)."""
    env = dict(os.environ if env is None else env)
    cwd = Path.cwd() if cwd is None else Path(cwd)
    payload: dict[str, Any] = {"schema": SCHEMA, "action": "run", "run_label": label,
                               "recipe": str(recipe_path), "launched": False,
                               "features": [], "human_only": [], "notes": []}

    def stop(code: int, verdict: str, summary: str, reason: str | None = None):
        payload["verdict"] = verdict
        if reason:
            payload["reason"] = reason
        return code, summary, payload

    if not _is_posix():
        return stop(2, "unverifiable", "app-verify: unverifiable (unsupported_platform)",
                    "unsupported_platform")
    try:
        recipe, text = _load_valid(recipe_path)
    except RecipeUnavailable as exc:
        return stop(2, "unverifiable", f"app-verify: unverifiable ({exc.reason})", exc.reason)
    if not spec_dir.is_dir():
        return stop(2, "unverifiable", "app-verify: unverifiable (no_spec_dir)", "no_spec_dir")

    by_id = {f.id: f for f in recipe.features}
    wanted = features if features else [f.id for f in recipe.features]
    unknown = [fid for fid in wanted if fid not in by_id]
    if unknown:
        reason = f"unknown_feature: {', '.join(unknown)}"
        return stop(2, "unverifiable", f"app-verify: unverifiable ({reason})", reason)
    selected = [by_id[fid] for fid in wanted if by_id[fid].check]
    payload["human_only"] = [{"feature": fid, "reason": by_id[fid].human_only}
                             for fid in wanted if by_id[fid].human_only]
    human = "; ".join(f"human-only — {h['feature']} ({h['reason']})"
                      for h in payload["human_only"])
    if not selected:
        summary = f"app-verify: {human}" if human else \
            "app-verify: unverifiable (no_runnable_features)"
        return stop(2, "unverifiable", summary, "no_runnable_features")
    human = f"; {human}" if human else ""

    refusal = safety_refusal(recipe, env, cwd)
    if refusal:
        return stop(2, "refused", f"app-verify: refused ({refusal})", refusal)
    ready_target = recipe.ready_when or ""
    already_up = probe_ready(ready_target)
    if already_up and not recipe.reuse_running:
        return stop(2, "refused", "app-verify: refused (instance_already_running)",
                    "instance_already_running")

    run_dir = spec_dir / "evidence" / label
    rel_run = f"evidence/{label}"
    recipe_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    proc: subprocess.Popen | None = None
    launch_dir = run_dir / "_launch"
    try:
        if not already_up:
            launch_dir.mkdir(parents=True, exist_ok=True)
            with open(launch_dir / "stdout.log", "wb") as out, \
                    open(launch_dir / "stderr.log", "wb") as err:
                proc = subprocess.Popen(
                    recipe.launch_command or "", shell=True, cwd=str(cwd), env=env,
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
            payload["launched"] = True
            deadline = time.monotonic() + recipe.ready_timeout_s
            while True:
                code = proc.poll()
                if code is not None:
                    reason = f"launch_exited {code}"
                    return stop(1, "fail", f"app-verify: fail ({reason}) — {rel_run}/_launch/",
                                reason)
                if probe_ready(ready_target):
                    break
                if time.monotonic() >= deadline:
                    reason = f"not_ready {recipe.ready_timeout_s}s"
                    return stop(1, "fail", f"app-verify: fail ({reason}) — {rel_run}/_launch/",
                                reason)
                time.sleep(READY_POLL_S)

        for feature in selected:
            result = run_check(feature, recipe, recipe_sha, run_dir / feature.id, env, cwd,
                               check_timeout_s, cleanup_grace_s)
            payload["features"].append({
                "feature": feature.id, "verdict": result["verdict"],
                "exit_code": result["exit_code"],
                "result": f"{rel_run}/{feature.id}/result.json"})
    finally:
        if proc is not None:
            note = stop_group(proc, cleanup_grace_s)
            if note:
                payload["notes"].append(note)
            for log in ("stdout.log", "stderr.log"):
                if (launch_dir / log).exists():
                    _truncate(launch_dir / log)
        if recipe.after and payload["launched"]:
            try:
                after = subprocess.run(recipe.after, shell=True, cwd=str(cwd), env=env,
                                       stdin=subprocess.DEVNULL, capture_output=True,
                                       timeout=AFTER_TIMEOUT_S)
                if after.returncode != 0:
                    payload["notes"].append(f"after command exited {after.returncode}")
            except subprocess.TimeoutExpired:
                payload["notes"].append(f"after command timed out after {AFTER_TIMEOUT_S}s")

    failed = [f for f in payload["features"] if f["verdict"] != "pass"]
    total = len(payload["features"])
    if failed:
        first = failed[0]
        why = "timeout" if first["exit_code"] is None else f"exit {first['exit_code']}"
        return stop(1, "fail", f"app-verify: {len(failed)}/{total} fail — {first['feature']} "
                               f"({why}) — {rel_run}/{first['feature']}/{human}")
    return stop(0, "pass", f"app-verify: {total}/{total} pass — {rel_run}/{human}")


# --- Subcommands -------------------------------------------------------------

def run_validate(args: argparse.Namespace) -> tuple[int, str, dict[str, Any]]:
    payload: dict[str, Any] = {"schema": SCHEMA, "action": "validate",
                               "recipe": str(args.recipe)}
    try:
        text = load_recipe(args.recipe)
    except RecipeUnavailable as exc:
        payload.update(verdict="unverifiable", reason=exc.reason, findings=[])
        return 2, f"app-verify: unverifiable ({exc.reason})", payload
    recipe, findings = _parse(text)
    payload["findings"] = findings
    if findings:
        payload["verdict"] = "invalid"
        return 1, f"app-verify: recipe invalid — {describe_finding(findings[0])}", payload
    checks = sum(1 for f in recipe.features if f.check)
    human = len(recipe.features) - checks
    payload["verdict"] = "valid"
    payload["features"] = [f.id for f in recipe.features]
    return 0, (f"app-verify: recipe valid — {len(recipe.features)} features "
               f"({checks} check, {human} human-only)"), payload


NO_TOUCHED = "app-verify: no mapped features touched by this story"


def run_touched(args: argparse.Namespace) -> tuple[int, str, dict[str, Any]]:
    payload: dict[str, Any] = {"schema": SCHEMA, "action": "touched",
                               "recipe": str(args.recipe)}
    try:
        recipe, _ = _load_valid(args.recipe)
    except RecipeUnavailable as exc:
        payload.update(verdict="unverifiable", reason=exc.reason, features=[])
        return 2, f"app-verify: unverifiable ({exc.reason})", payload
    ids = touched_features(recipe, args.changed)
    payload.update(verdict="ok", features=ids)
    return 0, ("\n".join(ids) if ids else NO_TOUCHED), payload


def _exit_on_sigterm(signum: int, frame: Any) -> None:
    raise SystemExit(128 + signum)


def run_run(args: argparse.Namespace) -> tuple[int, str, dict[str, Any]]:
    features = [f.strip() for f in args.features.split(",") if f.strip()] if args.features else None
    # A terminated run must still reach `finally`, or the app's session outlives it.
    signal.signal(signal.SIGTERM, _exit_on_sigterm)
    return run_verification(args.recipe, args.spec, args.run_label, features)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("validate", help="check a recipe against the grammar")
    p.add_argument("--recipe", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=run_validate)

    t = sub.add_parser("touched", help="print feature IDs whose Paths match changed files")
    t.add_argument("--recipe", required=True, type=Path)
    t.add_argument("--changed", nargs="*", default=[])
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=run_touched)

    r = sub.add_parser("run", help="launch the app, run checks, record evidence, clean up")
    r.add_argument("--recipe", required=True, type=Path)
    r.add_argument("--spec", required=True, type=Path)
    r.add_argument("--run-label", required=True)
    r.add_argument("--features", default=None, help="comma-separated feature IDs")
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=run_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, summary, payload = args.func(args)
    payload["summary"] = summary
    print(summary)
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
