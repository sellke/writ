#!/usr/bin/env python3
"""Gate 0 architecture re-derivation (Story 2 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Re-derives PROCEED/CAUTION from `story-deps.py` plus the planned (or
replayed) file set and an optional boundary map. Never re-derives ABORT;
that residual stays with the architecture-check agent.

Subcommand:
  check --story PATH --repo . [--planned FILE … | --changed FILE …]
        [--boundary PATH] [--classify-abort]
  `--project` is accepted as an alias of `--repo`.

`--planned` is Gate 0's live pre-implementation set. `--changed` is
replay. Neither mode is `unverifiable` (`reason: no_file_mode`), not an
invented empty-tree proceed. Both modes is usage (exit 2).

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`rederived:` / `reason:` lines, then a summary line last.

Exit 0: ran, no blocking verdict (`pass` or `unverifiable`).
Exit 1: `fail`.
Exit 2: usage.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


HELPER_DIR = Path(__file__).resolve().parent
VERDICTS = frozenset({"pass", "fail", "unverifiable"})


class UsageError(Exception):
    """Exit-2 conditions."""


def _emit(
    verdict: str,
    reasons: Sequence[str],
    summary: str,
    rederived: Optional[str] = None,
) -> int:
    print(verdict)
    if rederived is not None:
        print("rederived: %s" % rederived)
    for reason in reasons:
        print("reason: %s" % reason)
    print(summary)
    if verdict == "fail":
        return 1
    return 0


def _run_helper(script: Path, argv: List[str]) -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *argv],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def _load_json(stdout: str) -> Optional[dict]:
    text = stdout.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def spec_dir_from_story(story: Path, repo: Path) -> Optional[Path]:
    """Ancestor of `--story` that contains a `user-stories/` directory."""
    candidate = story if story.is_absolute() else (repo / story)
    try:
        path = candidate.resolve()
    except OSError:
        path = candidate
    start = path if path.is_dir() else path.parent
    for folder in [start, *start.parents]:
        if (folder / "user-stories").is_dir():
            return folder
    return None


def _norm_path(value: str, repo: Path) -> str:
    raw = Path(value)
    if raw.is_absolute():
        try:
            return raw.resolve().relative_to(repo.resolve()).as_posix()
        except (OSError, ValueError):
            return raw.as_posix()
    return raw.as_posix().lstrip("./")


def _covers(entry: str, path: str) -> bool:
    entry_n = entry.rstrip("/")
    if path == entry or path == entry_n:
        return True
    prefix = entry if entry.endswith("/") else entry_n + "/"
    return path.startswith(prefix)


def _in_any(entries: Sequence[str], path: str) -> bool:
    return any(_covers(entry, path) for entry in entries if entry)


def _load_boundary(path: Path) -> Optional[Dict[str, List[str]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None

    def _list(key: str) -> List[str]:
        raw = payload.get(key) or []
        if not isinstance(raw, list):
            return []
        return [str(item) for item in raw]

    return {
        "owned": _list("owned"),
        "readable": _list("readable"),
        "out_of_scope": _list("out_of_scope"),
    }


def _warning_class(payload: dict) -> bool:
    if str(payload.get("status") or "") == "warning":
        return True
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        return True
    return False


def check(
    story: Optional[Path],
    repo: Path,
    planned: Optional[List[str]],
    changed: Optional[List[str]],
    boundary: Optional[Path],
    classify_abort: bool,
) -> int:
    if planned is not None and changed is not None:
        print("error: pass exactly one of --planned or --changed", file=sys.stderr)
        return 2

    if classify_abort:
        return _emit(
            "unverifiable",
            ["abort_is_llm_residual"],
            "arch-check: unverifiable (llm residual)",
        )

    if planned is None and changed is None:
        return _emit(
            "unverifiable",
            ["no_file_mode"],
            "arch-check: unverifiable (no --planned or --changed)",
        )

    files = list(planned if planned is not None else changed or [])

    helper = HELPER_DIR / "story-deps.py"
    if not helper.is_file():
        return _emit(
            "unverifiable",
            ["helper_missing"],
            "arch-check: unverifiable (story-deps.py missing)",
        )

    if story is None:
        return _emit(
            "unverifiable",
            ["missing_story"],
            "arch-check: unverifiable (missing --story)",
        )

    spec_dir = spec_dir_from_story(story, repo)
    if spec_dir is None:
        return _emit(
            "unverifiable",
            ["spec_dir_unresolved"],
            "arch-check: unverifiable (no user-stories ancestor for --story)",
        )

    rc, stdout = _run_helper(helper, ["validate", "--spec-dir", str(spec_dir)])
    payload: Dict[str, Any] = _load_json(stdout) or {}

    if rc == 2:
        return _emit(
            "unverifiable",
            ["helper_unverifiable"],
            "arch-check: unverifiable (story-deps.py usage)",
        )

    if rc != 0 or payload.get("blocker"):
        blocker = payload.get("blocker") or {}
        code = "story_deps_blocker"
        if isinstance(blocker, dict) and blocker.get("code"):
            code = str(blocker["code"])
        return _emit(
            "fail",
            [code],
            "arch-check: fail (invalid story graph)",
        )

    if _warning_class(payload):
        return _emit(
            "pass",
            ["story_deps_warning"],
            "arch-check: pass (rederived caution)",
            rederived="caution",
        )

    if not files:
        return _emit(
            "pass",
            ["empty_file_set"],
            "arch-check: pass (rederived caution)",
            rederived="caution",
        )

    if boundary is not None:
        mapped = _load_boundary(boundary)
        if mapped is None:
            return _emit(
                "unverifiable",
                ["boundary_unreadable"],
                "arch-check: unverifiable (boundary map unreadable)",
            )
        normalized = [_norm_path(item, repo) for item in files]
        owned = [_norm_path(item, repo) for item in mapped["owned"]]
        readable = [_norm_path(item, repo) for item in mapped["readable"]]
        out_of_scope = [_norm_path(item, repo) for item in mapped["out_of_scope"]]
        if any(_in_any(out_of_scope, path) for path in normalized):
            return _emit(
                "pass",
                ["out_of_scope"],
                "arch-check: pass (rederived caution)",
                rederived="caution",
            )
        allowed = owned + readable
        if any(not _in_any(allowed, path) for path in normalized):
            return _emit(
                "pass",
                ["outside_boundary"],
                "arch-check: pass (rederived caution)",
                rederived="caution",
            )

    return _emit(
        "pass",
        [],
        "arch-check: pass (rederived proceed)",
        rederived="proceed",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("check", help="re-derive Gate 0 proceed/caution")
    p.add_argument("--story", type=Path, default=None)
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    p.add_argument("--planned", nargs="*", default=None)
    p.add_argument("--changed", nargs="*", default=None)
    p.add_argument("--boundary", type=Path, default=None)
    p.add_argument(
        "--classify-abort",
        action="store_true",
        dest="classify_abort",
        help="report ABORT as unverifiable llm residual (tests / explicit callers)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    return check(
        args.story,
        args.repo,
        args.planned,
        args.changed,
        args.boundary,
        args.classify_abort,
    )


if __name__ == "__main__":
    sys.exit(main())
