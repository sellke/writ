#!/usr/bin/env python3
"""Default-path spawn-cap scan (Story 3 of
`2026-09-09-phase11-stage4b-pipeline-demote`).

Counts default-path spawn sites in a command file. Does not spawn
Tasks. Does not decide accept / reject / modify-spec.

Subcommand:
  check --command PATH [--repo .]

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` lines, then a summary line last.

Exit 0: ran, no blocking helper defect (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set


ALLOWED_STEMS = frozenset(("coding-agent", "evaluator-agent"))
STEM = re.compile(r"([a-z0-9-]+-agent)")
TASK_SPAWN = re.compile(r"(?:Task\s*\(|sessions_spawn\s*\()")


class UsageError(Exception):
    """Exit-2 conditions."""


def _emit(verdict: str, reasons: Sequence[str], summary: str) -> int:
    print(verdict)
    for reason in reasons:
        print("reason: %s" % reason)
    print(summary)
    if verdict == "fail":
        return 1
    return 0


def _stems_in(line: str) -> Set[str]:
    return {m.group(1) for m in STEM.finditer(line)}


def _is_spawn_marker(line: str) -> bool:
    stems = _stems_in(line)
    if not stems:
        return False
    if line.startswith("> **Agent:**"):
        return True
    if TASK_SPAWN.search(line):
        return True
    return False


def _default_agent_markers(text: str) -> List[str]:
    """Spawn markers not immediately guarded by `--full-pipeline`."""
    last_nonempty = ""
    out: List[str] = []
    for line in text.splitlines():
        if _is_spawn_marker(line):
            guarded = (
                "--full-pipeline" in last_nonempty or "--full-pipeline" in line
            )
            if not guarded:
                out.append(line)
        if line.strip():
            last_nonempty = line
    return out


def _read_command(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _resolve_command(command: Optional[Path], repo: Path) -> Optional[Path]:
    if command is None:
        return None
    if command.is_file():
        return command
    alt = repo / command
    if alt.is_file():
        return alt
    return command


def check(command: Optional[Path], repo: Path) -> int:
    resolved = _resolve_command(command, repo)
    if resolved is None:
        return _emit(
            "unverifiable",
            ["missing_command"],
            "spawn-cap: unverifiable (no --command)",
        )
    text = _read_command(resolved)
    if text is None:
        return _emit(
            "unverifiable",
            ["missing_command"],
            "spawn-cap: unverifiable (command unreadable)",
        )

    markers = _default_agent_markers(text)
    stems: Set[str] = set()
    for line in markers:
        stems |= _stems_in(line)

    over = (not markers) or (len(markers) > 2) or (not stems.issubset(ALLOWED_STEMS))
    if over:
        return _emit(
            "fail",
            ["over_cap"],
            "spawn-cap: fail (default spawn sites over cap)",
        )
    return _emit(
        "pass",
        [],
        "spawn-cap: pass (default spawn sites at or under cap)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="scan default-path spawn sites")
    p.add_argument("--command", type=Path, default=None)
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if getattr(args, "action", None) != "check":
        return 2
    return check(args.command, args.repo)


if __name__ == "__main__":
    sys.exit(main())
