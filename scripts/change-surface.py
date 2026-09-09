#!/usr/bin/env python3
"""Gate 2.5 change-surface class (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Path heuristic for `skills/change-surface-classification/SKILL.md` — not
an LLM. Six steps in order; classify UP when ambiguous.

Subcommand:
  classify --changed FILE …

Prints exactly one of:
  style-only | single-component | cross-component | full-stack

Exit 0: printed a class.
Exit 2: `--changed` empty or omitted, or other usage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence


STYLE_SUFFIXES = (".css", ".scss", ".sass", ".less")
COMPONENT_SUFFIXES = (".tsx", ".jsx", ".vue")

SHARED_DIRS = ("hooks", "utils", "context", "lib")
FULLSTACK_DIRS = (
    "middleware",
    "migration",
    "migrations",
    "auth",
    "schema",
    "api",
)


class UsageError(Exception):
    """Exit-2 conditions."""


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip()


def _parts(path: str) -> List[str]:
    return [p for p in _norm(path).lower().split("/") if p]


def _name(path: str) -> str:
    return Path(_norm(path)).name.lower()


def is_style(path: str) -> bool:
    name = _name(path)
    if name.startswith("tailwind.config"):
        return True
    lowered = _norm(path).lower()
    return lowered.endswith(STYLE_SUFFIXES)


def is_test(path: str) -> bool:
    name = _name(path)
    lowered = _norm(path).lower()
    if ".test." in name or ".spec." in name:
        return True
    if "/__tests__/" in lowered or lowered.startswith("__tests__/"):
        return True
    return False


def is_fullstack(path: str) -> bool:
    parts = _parts(path)
    name = _name(path)
    if any(part in FULLSTACK_DIRS for part in parts):
        return True
    if "middleware" in name or "migration" in name:
        return True
    if name.endswith(".prisma") or name in ("schema.sql", "schema.prisma"):
        return True
    if name in ("route.ts", "route.js", "route.tsx"):
        return True
    return False


def is_shared(path: str) -> bool:
    return any(part in SHARED_DIRS for part in _parts(path))


def is_component(path: str) -> bool:
    if is_test(path) or is_style(path) or is_fullstack(path) or is_shared(path):
        return False
    parts = _parts(path)
    if "components" in parts:
        return True
    lowered = _norm(path).lower()
    return lowered.endswith(COMPONENT_SUFFIXES)


def _stem(path: str) -> str:
    name = Path(_norm(path)).name
    lower = name.lower()
    for token in (".test.", ".spec."):
        idx = lower.find(token)
        if idx != -1:
            return name[:idx]
    return Path(name).stem


def tests_pair_with_component(tests: Sequence[str], component: str) -> bool:
    stem = _stem(component)
    for test in tests:
        if _stem(test) != stem:
            return False
    return True


def classify(changed: Sequence[str]) -> str:
    files = [_norm(item) for item in changed if item and str(item).strip()]
    if not files:
        raise UsageError("empty --changed")

    # Step 2: ALL changes are style files (path heuristic; className/style
    # prop edits are not visible from paths, so .tsx/.jsx never count here).
    if all(is_style(path) for path in files):
        return "style-only"

    # Steps 3–5 collect signals; step 6 classifies UP when more than one
    # class could apply (stylesheet + migration → full-stack).
    has_full = any(is_fullstack(path) for path in files)
    has_shared = any(is_shared(path) for path in files)
    components = [path for path in files if is_component(path)]
    tests = [path for path in files if is_test(path)]
    leftovers = [
        path
        for path in files
        if not is_style(path)
        and not is_test(path)
        and not is_component(path)
        and not is_shared(path)
        and not is_fullstack(path)
    ]

    if has_full:
        return "full-stack"

    single = (
        len(components) == 1
        and not has_shared
        and not leftovers
        and tests_pair_with_component(tests, components[0])
    )
    if single and not has_shared:
        return "single-component"

    if has_shared:
        return "cross-component"

    # Two+ components, unpaired tests, or leftover files: not a clean
    # single-component. Ambiguous → classify UP to cross-component.
    return "cross-component"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("classify", help="print one change-surface class")
    p.add_argument("--changed", nargs="*", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if args.action != "classify" or not args.changed:
        return 2
    try:
        print(classify(args.changed))
    except UsageError:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
