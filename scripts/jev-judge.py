#!/usr/bin/env python3
"""Optional Jev judgment provider (Story 1 of `2026-09-25-jev-judgment-pilot`).

Decision record: `.writ/decision-records/adr-027-optional-judgment-provider.md`.

Subcommand:
  status [--repo .]   Resolve the double opt-in. Reads `.writ/config.md` and
                      the environment; prints stdout only; sends nothing.

The provider is enabled only when `.writ/config.md` has a line
`- **Judgment Provider:** <backend>` naming `typesafe` or `vercel-gateway`
AND that backend's key is set and non-empty. A key alone never enables it.

Prints one verdict line (`pass` / `fail` / `unverifiable`), optional
`reason:` lines, then a summary line last.

Exit 0: `pass` or `unverifiable`.
Exit 1: `fail`.
Exit 2: usage.

Key handling: this script never prints, logs, or writes a key value. The
resolver returns the NAME of the env var that holds the key, never the value.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple


CONFIG_LINE = re.compile(r"^- \*\*Judgment Provider:\*\*\s*(\S+)", re.MULTILINE)


class Backend(NamedTuple):
    name: str
    base_url: str
    key_vars: Tuple[str, ...]  # first non-empty wins
    model: str
    pinned: bool


# technical-spec §2. Both use POST <base_url>/v1/systemone.
BACKENDS: Dict[str, Backend] = {
    "typesafe": Backend(
        name="typesafe",
        base_url="https://api.typesafe.ai",
        key_vars=("TYPESAFE_API_KEY",),
        model="jev-1.13.0",
        pinned=True,
    ),
    "vercel-gateway": Backend(
        name="vercel-gateway",
        base_url="https://ai-gateway.vercel.sh/typesafe",
        key_vars=("AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN"),
        model="typesafe-ai/jev",
        pinned=False,
    ),
}
DISABLED_VALUE = "none"


class UsageError(Exception):
    """Exit-2 conditions."""


class Resolution(NamedTuple):
    verdict: str
    reasons: List[str]
    backend: Optional[Backend]
    key_var: Optional[str]  # env var NAME holding the key; never the value


def _emit(verdict: str, reasons: Sequence[str], summary: str) -> int:
    print(verdict)
    for reason in reasons:
        print("reason: %s" % reason)
    print(summary)
    if verdict == "fail":
        return 1
    return 0


def _config_value(repo: Path) -> Optional[str]:
    """The Judgment Provider value, lowercased; None when file or line is absent."""
    try:
        text = (repo / ".writ" / "config.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = CONFIG_LINE.search(text)
    if not match:
        return None
    return match.group(1).lower()


def _key_var(backend: Backend, environ: Mapping[str, str]) -> Optional[str]:
    """Name of the first env var with a non-blank value, or None."""
    for var in backend.key_vars:
        if environ.get(var, "").strip():
            return var
    return None


def resolve(repo: Path, environ: Mapping[str, str]) -> Resolution:
    """Double opt-in: config line naming a backend AND that backend's key."""
    value = _config_value(repo)
    if value is None:
        return Resolution("unverifiable", ["no_config_line"], None, None)
    backend = BACKENDS.get(value)
    if backend is None:
        # `none` or an unknown value. The value is never echoed: a key pasted
        # into the config line by mistake must not reach output.
        return Resolution("unverifiable", ["provider_disabled"], None, None)
    info = [] if backend.pinned else ["model_unpinned"]
    var = _key_var(backend, environ)
    if var is None:
        return Resolution("unverifiable", ["no_api_key"] + info, backend, None)
    return Resolution("pass", ["enabled"] + info, backend, var)


def status(repo: Path, environ: Mapping[str, str]) -> int:
    res = resolve(repo, environ)
    primary = res.reasons[0]
    if res.backend is None:
        return _emit(res.verdict, res.reasons,
                     "jev-judge: %s (%s) backend=none" % (res.verdict, primary))
    detail = "backend=%s model=%s" % (res.backend.name, res.backend.model)
    if res.verdict == "pass":
        return _emit(res.verdict, res.reasons,
                     "jev-judge: pass (enabled) %s key_env=%s" % (detail, res.key_var))
    return _emit(res.verdict, res.reasons,
                 "jev-judge: unverifiable (no_api_key) %s export=%s"
                 % (detail, res.backend.key_vars[0]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("status", help="report whether the judgment provider is enabled")
    p.add_argument("--repo", "--project", dest="repo", type=Path, default=Path("."))
    return parser


def main(argv: Optional[List[str]] = None,
         environ: Optional[Mapping[str, str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    env = os.environ if environ is None else environ
    try:
        if args.action == "status":
            if not args.repo.is_dir():
                raise UsageError("--repo is not a directory: %s" % args.repo)
            return status(args.repo, env)
    except UsageError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
