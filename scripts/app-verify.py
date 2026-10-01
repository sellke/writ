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

Without `--json`, stdout is exactly one `app-verify:` summary line. With
`--json`, that line is followed by one JSON object (schema `app-verify-v1`).
Exit 0: valid. Exit 1: findings. Exit 2: unverifiable (recipe missing or
unreadable).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCHEMA = "app-verify-v1"

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("validate", help="check a recipe against the grammar")
    p.add_argument("--recipe", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=run_validate)

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
