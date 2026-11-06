#!/usr/bin/env python3
"""Gate 2.5 change-surface class (Story 4 of
`2026-09-08-phase11-stage2b-mechanize-the-gates`).

Path heuristic for `skills/change-surface-classification/SKILL.md` — not
an LLM. Six steps in order; classify UP when ambiguous.

Subcommands:
  classify --changed FILE … [--pretty]
  blast-radius --changed FILE … [--repo DIR] [--limit N] [--pretty]

classify prints one JSON object `{"class": CLASS}`, where CLASS is one of:
  style-only | single-component | cross-component | full-stack
`--pretty` prints the bare class word instead.

blast-radius (Story 3 of `2026-10-25-review-route-rigor`) lists, for each
changed file that is not test-like, the files that mention it: a text
heuristic, not a call graph. Tokens are the repo-relative path with and
without its extension, plus the file stem unless the stem is under 4
characters or generic (`index`, `utils`, `config`, ...); an extensionless
path that is itself such a stem is dropped too. A token matches only with
no `[A-Za-z0-9_-]` character on either side. Candidates come from
`git ls-files` in `--repo`, or a walk that skips `.git/`, `node_modules/`,
and dot-directories when git fails (reason `no_git_walked`, verdict stays
`pass`). Skipped silently: anything under a `.writ/` directory, the changed
files, files over 1 MB, non-UTF-8 files, and unreadable paths. Test-like
referrers (`.test.`, `.spec.`, `__tests__/`, `test_*.py`, `*_test.py`,
`*_test.go`, a `test/` or `tests/` directory) go under `tests`, the rest
under `consumers`. Each list is sorted and capped at `--limit` (default 20);
a capped changed file is listed once in `truncated`. Prints one JSON object
with keys `verdict`, `consumers`, `tests`, `truncated`, `reasons`; every
non-test changed file is a key in both maps. A `--repo` that is not a
readable directory gives `unverifiable` with `repo_unreadable`. `--pretty`
prints the verdict, one `<changed>: <n> consumer(s), <m> test(s)` line per
non-test changed file (counts taken before the cap), `reason:` lines, and
the summary `change-surface blast-radius: <verdict> (<n> changed, <k>
consumers)`.

`--json` is accepted as a no-op by both (agent CLI contract, data shape).

Exit 0: printed a class, or a blast-radius `pass` or `unverifiable`.
Exit 2: `--changed` empty or omitted, `--limit` below 1, or other usage.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import posixpath
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Sequence, Set, Tuple


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


# --- blast-radius -----------------------------------------------------------

GENERIC_STEMS = frozenset({
    "index", "main", "mod", "__init__", "utils", "util", "types", "type",
    "constants", "config", "helpers", "readme", "setup", "app",
})
MIN_STEM_LEN = 4
MAX_CANDIDATE_BYTES = 1024 * 1024
TEST_BASENAME_GLOBS = ("test_*.py", "*_test.py", "*_test.go")
TEST_DIR_SEGMENTS = ("test", "tests", "__tests__")
WALK_SKIP_DIRS = ("node_modules",)
BLAST_USAGE = (
    "usage: change-surface.py blast-radius --changed FILE [FILE ...] "
    "[--repo DIR] [--limit N] [--pretty]\n"
)


def is_test_like(path: str) -> bool:
    """Blast-radius test check. Wider than `is_test`, which `classify` uses
    and which stays as it is."""
    parts = [p for p in _norm(path).lower().split("/") if p]
    if not parts:
        return False
    name = parts[-1]
    if ".test." in name or ".spec." in name:
        return True
    if any(part in TEST_DIR_SEGMENTS for part in parts[:-1]):
        return True
    return any(fnmatch.fnmatchcase(name, glob) for glob in TEST_BASENAME_GLOBS)


def normalize_changed(path: str) -> str:
    """Repo-relative POSIX form: backslashes to `/`, leading `./` removed."""
    norm = _norm(path)
    while norm.startswith("./"):
        norm = norm[2:].lstrip("/")
    return norm


def search_tokens(path: str) -> List[str]:
    """Path, path without extension, and the stem unless it is short or generic."""
    no_ext = posixpath.splitext(path)[0]
    stem = posixpath.basename(no_ext)
    stem_ok = len(stem) >= MIN_STEM_LEN and stem.lower() not in GENERIC_STEMS
    tokens = [path]
    # At the repo root the extensionless path is the bare stem; keep the
    # generic / short filter from being bypassed through it.
    if no_ext and (stem_ok or no_ext != stem):
        tokens.append(no_ext)
    if stem_ok:
        tokens.append(stem)
    return list(dict.fromkeys(t for t in tokens if t))


def token_pattern(tokens: Sequence[str]) -> Pattern[str]:
    alternatives = "|".join(re.escape(t) for t in sorted(tokens, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9_-])(?:%s)(?![A-Za-z0-9_-])" % alternatives)


def _git_files(repo: Path) -> Optional[List[str]]:
    """Tracked files relative to `repo`, or None when git cannot list them."""
    try:
        proc = subprocess.run(["git", "ls-files", "-z"], cwd=str(repo),
                              capture_output=True)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return [os.fsdecode(raw) for raw in proc.stdout.split(b"\0") if raw]


def _walk_files(repo: Path) -> List[str]:
    found: List[str] = []
    for dirpath, dirnames, filenames in os.walk(str(repo)):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in WALK_SKIP_DIRS]
        rel_dir = os.path.relpath(dirpath, str(repo))
        for name in filenames:
            rel = name if rel_dir == "." else os.path.join(rel_dir, name)
            found.append(rel.replace(os.sep, "/"))
    return found


def _read_text(path: Path) -> Optional[str]:
    """File text, or None when not a regular file (a directory, or a FIFO
    that would block `open`), unreadable, over 1 MB, or not UTF-8."""
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            return None
        with path.open("rb") as handle:
            raw = handle.read(MAX_CANDIDATE_BYTES + 1)
    except OSError:
        return None
    if len(raw) > MAX_CANDIDATE_BYTES:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _under_writ(rel: str) -> bool:
    return ".writ" in rel.split("/")[:-1]


def blast_radius(changed: Sequence[str], repo: Path, limit: int
                 ) -> Tuple[dict, Dict[str, Tuple[List[str], List[str]]]]:
    """Return the JSON result and, per non-test changed file, the uncapped
    (consumers, tests) lists that `--pretty` counts."""
    files = list(dict.fromkeys(normalize_changed(c) for c in changed))
    targets = sorted(f for f in files if not is_test_like(f))
    result: dict = {"verdict": "pass", "consumers": {}, "tests": {},
                    "truncated": [], "reasons": []}
    try:
        os.listdir(str(repo))
    except OSError:
        result.update(verdict="unverifiable", reasons=["repo_unreadable"])
        return result, {}
    if not targets:
        return result, {}

    candidates = _git_files(repo)
    if candidates is None:
        candidates = _walk_files(repo)
        result["reasons"].append("no_git_walked")

    patterns = [(target, token_pattern(search_tokens(target))) for target in targets]
    consumers: Dict[str, List[str]] = {target: [] for target in targets}
    tests: Dict[str, List[str]] = {target: [] for target in targets}
    skip = set(files)
    # One read per candidate, tested against every changed file's pattern.
    for rel in candidates:
        if rel in skip or _under_writ(rel):
            continue
        text = _read_text(repo / rel)
        if text is None:
            continue
        bucket = tests if is_test_like(rel) else consumers
        for target, pattern in patterns:
            if pattern.search(text):
                bucket[target].append(rel)

    full: Dict[str, Tuple[List[str], List[str]]] = {}
    truncated: Set[str] = set()
    for target in targets:
        full[target] = (sorted(set(consumers[target])), sorted(set(tests[target])))
        for key, listed in zip(("consumers", "tests"), full[target]):
            if len(listed) > limit:
                truncated.add(target)
            result[key][target] = listed[:limit]
    result["truncated"] = sorted(truncated)
    return result, full


def pretty_blast(result: dict, full: Dict[str, Tuple[List[str], List[str]]],
                 changed_total: int) -> str:
    """Check shape: verdict, per-file counts (before the cap), reasons, summary."""
    lines = [result["verdict"]]
    distinct: Set[str] = set()
    for target in sorted(full):
        found_consumers, found_tests = full[target]
        distinct.update(found_consumers)
        lines.append("%s: %d consumer(s), %d test(s)"
                     % (target, len(found_consumers), len(found_tests)))
    lines.extend("reason: %s" % reason for reason in result["reasons"])
    lines.append("change-surface blast-radius: %s (%d changed, %d consumers)"
                 % (result["verdict"], changed_total, len(distinct)))
    return "\n".join(lines)


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        number = 0
    if number < 1:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    return number


def run_blast_radius(args: argparse.Namespace) -> int:
    changed = [f for f in map(normalize_changed, args.changed or []) if f]
    if not changed:
        sys.stderr.write(BLAST_USAGE + "error: --changed needs at least one file\n")
        return 2
    result, full = blast_radius(changed, Path(args.repo), args.limit)
    if args.pretty:
        targets = {f for f in changed if not is_test_like(f)}
        print(pretty_blast(result, full, len(targets)))
    else:
        print(json.dumps(result))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("classify", help='print {"class": CLASS} as JSON')
    p.add_argument("--changed", nargs="*", default=None)
    p.add_argument("--pretty", action="store_true",
                   help="print the bare class word instead of JSON")
    p.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    b = sub.add_parser("blast-radius", help="list the files that mention each changed file")
    b.add_argument("--changed", nargs="*", default=None)
    b.add_argument("--repo", default=".")
    b.add_argument("--limit", type=_positive_int, default=20)
    b.add_argument("--pretty", action="store_true",
                   help="print the check shape instead of JSON")
    b.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2
    if args.action == "blast-radius":
        return run_blast_radius(args)
    if args.action != "classify" or not args.changed:
        return 2
    try:
        surface = classify(args.changed)
    except UsageError:
        return 2
    print(surface if args.pretty else json.dumps({"class": surface}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
