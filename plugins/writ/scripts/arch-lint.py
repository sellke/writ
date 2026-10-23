#!/usr/bin/env python3
"""Architecture ruleset detection for Gate 2 (Story 3 of
`2026-09-26-arch-lint-and-follow-ups`).

Finds a project's architecture lint ruleset and prints how Gate 2 runs it.
Detection table (technical-spec §3), in output order:

  dependency-cruiser        `.dependency-cruiser.{js,cjs,mjs,json}`; `run`
                            when `node_modules/.bin/depcruise` exists
  import-linter             `.importlinter`, `[importlinter]` in setup.cfg,
                            `[tool.importlinter]` in pyproject.toml; `run`
                            when `lint-imports` is on PATH
  eslint-plugin-boundaries  package.json dependency; `via-eslint`
  archunit                  `archunit` in pom.xml / build.gradle(.kts);
                            `via-tests`

Only the first two are standalone checkers, so only they get a `command:`
line; the other two already run inside eslint and the test suite.

Read-only and offline: this module opens files and checks PATH. It never
starts a process, touches the network, or installs anything; Gate 2 runs
the printed commands, and `npx --no-install` keeps that offline too.

Subcommand:
  detect [--repo .]

Prints `pass` or `unverifiable` first, one `tool: <name> <mode> <config>`
line per ruleset (each runnable one followed by its `command:` line),
`reason: config_unreadable <path>` lines, and
`arch-lint detect: <n> ruleset(s), <m> runnable` last. A missing ruleset is
`pass`; it never blocks. Exit 0 when it ran, 2 on usage.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


DEPCRUISE_CONFIGS = tuple(".dependency-cruiser." + ext for ext in ("js", "cjs", "mjs", "json"))
IMPORTLINTER_SECTIONS = (
    ("setup.cfg", re.compile(r"^\s*\[importlinter\]\s*$", re.MULTILINE)),
    ("pyproject.toml", re.compile(r"^\s*\[tool\.importlinter\]\s*$", re.MULTILINE)),
)
ARCHUNIT_FILES = ("pom.xml", "build.gradle", "build.gradle.kts")


class UsageError(Exception):
    """Exit-2 conditions."""


class Unreadable(Exception):
    """A config file exists but cannot be read or parsed."""


class Detection:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.tools: List[Tuple[str, str, str, Optional[str]]] = []
        self.reasons: List[str] = []
        self._package: Optional[Dict[str, Any]] = None

    def read_text(self, rel: str) -> Optional[str]:
        """File text, None when absent; records and raises when unreadable."""
        path = self.repo / rel
        if not path.exists():
            return None
        try:
            return path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            self.reasons.append("config_unreadable " + rel)
            raise Unreadable(rel)

    def package(self) -> Dict[str, Any]:
        """Parsed package.json, `{}` when absent or unreadable (recorded once)."""
        if self._package is None:
            self._package = {}
            try:
                text = self.read_text("package.json")
            except Unreadable:
                return self._package
            if text is not None:
                try:
                    parsed = json.loads(text)
                except ValueError:
                    parsed = None
                if isinstance(parsed, dict):
                    self._package = parsed
                else:
                    self.reasons.append("config_unreadable package.json")
        return self._package

    def add(self, name: str, mode: str, config: str, command: Optional[str] = None) -> None:
        self.tools.append((name, mode, config, command))


def detect_dependency_cruiser(d: Detection) -> None:
    config = next((c for c in DEPCRUISE_CONFIGS if (d.repo / c).is_file()), None)
    if config is None:
        return
    if not (d.repo / "node_modules" / ".bin" / "depcruise").exists():
        d.add("dependency-cruiser", "not-installed", config)
        return
    scripts = d.package().get("scripts")
    script = None
    if isinstance(scripts, dict):
        script = next(
            (name for name, body in scripts.items()
             if isinstance(body, str) and "depcruise" in body),
            None,
        )
    if script is not None:
        command = "npm run " + shlex.quote(script)
    else:
        target = "src" if (d.repo / "src").is_dir() else "."
        command = "npx --no-install depcruise --config %s %s" % (config, target)
    d.add("dependency-cruiser", "run", config, command)


def detect_import_linter(d: Detection) -> None:
    config = None
    if (d.repo / ".importlinter").is_file():
        config = ".importlinter"
    else:
        for rel, section in IMPORTLINTER_SECTIONS:
            try:
                text = d.read_text(rel)
            except Unreadable:
                continue
            if text is not None and section.search(text):
                config = rel
                break
    if config is None:
        return
    if shutil.which("lint-imports"):
        d.add("import-linter", "run", config, "lint-imports")
    else:
        d.add("import-linter", "not-installed", config)


def detect_eslint_boundaries(d: Detection) -> None:
    package = d.package()
    for key in ("dependencies", "devDependencies"):
        block = package.get(key)
        if isinstance(block, dict) and "eslint-plugin-boundaries" in block:
            d.add("eslint-plugin-boundaries", "via-eslint", "package.json")
            return


def detect_archunit(d: Detection) -> None:
    for rel in ARCHUNIT_FILES:
        try:
            text = d.read_text(rel)
        except Unreadable:
            continue
        if text is not None and "archunit" in text.lower():
            d.add("archunit", "via-tests", rel)
            return


DETECTORS = (
    detect_dependency_cruiser,
    detect_import_linter,
    detect_eslint_boundaries,
    detect_archunit,
)


def detect(repo: Path) -> List[str]:
    if not repo.is_dir():
        raise UsageError("repo not found or not a directory: %s" % repo)
    d = Detection(repo)
    for detector in DETECTORS:
        detector(d)

    lines = ["unverifiable" if d.reasons else "pass"]
    for name, mode, config, command in d.tools:
        lines.append("tool: %s %s %s" % (name, mode, config))
        if command is not None:
            lines.append("command: " + command)
    lines.extend("reason: " + reason for reason in d.reasons)
    runnable = sum(1 for tool in d.tools if tool[3] is not None)
    lines.append("arch-lint detect: %d ruleset(s), %d runnable" % (len(d.tools), runnable))
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("detect", help="detect architecture lint rulesets")
    p.add_argument("--repo", default=Path("."), type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        lines = detect(args.repo)
    except UsageError as exc:
        print("arch-lint: %s" % exc, file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
