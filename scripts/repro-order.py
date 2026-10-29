#!/usr/bin/env python3
"""Repro-before-fix order check (Story 1 of `2026-10-25-repro-first-bug-fixing`).

Re-derives from git whether each bug's repro commit precedes its fix.

CLI:
  repro-order.py check --base REV [--head REV] [--repo DIR] [--test-glob PATTERN]...

  --base       the commit before the repro; the range read is BASE..HEAD
  --head       default HEAD
  --repo       repository root, default `.`
  --test-glob  fnmatch pattern on the repo-relative POSIX path that also marks
               a test file; repeatable

Switch: the first `- **Repro First:** <value>` line in <repo>/.writ/config.md.
`off` (any case) prints `unverifiable` and `reason: repro-first off` and exits
0 before any git call. No file, no line, an empty value, or `on` reads as on.
Any other value reads as on and adds `reason: repro-first value <v> read as on`.

Commits in BASE..HEAD are read oldest first. A repro commit has a line
`Repro: <non-empty value>` in its message's final paragraph. Each changed path
is classified: under `.writ/` it is ignored; it is a test file when a
directory segment is test, tests, __tests__, spec, e2e, or cypress, when the
basename matches test_*, *_test.*, *.test.*, *.spec.*, *_spec.*, *Test.*,
*Tests.*, or is conftest.py, or when it matches a --test-glob; otherwise it is
source. Both sides of a rename count. A fix commit is a non-repro commit after
the first repro commit that changes a source file.

Rules (all run; every finding prints, in rule order):
  1  at least one repro commit                       no_repro_commit
  2  each repro changes a test file                  repro_empty <sha>
  3  each repro changes no source file               repro_touches_source <sha> <path>
  4  no commit before the first repro changes source source_before_repro <sha> <path>
  5  each repro has a later fix commit               no_fix_after_repro <sha>
  6  no later non-repro commit modifies, renames, or deletes a test file a repro
     commit added or modified                        repro_test_modified <sha> <path>
In rules 4 and 6, <sha> is the offending commit; in 2, 3, and 5 it is the repro.
A later repro commit may change an earlier repro's test file. An empty range
fails rule 1. A merge commit in the range makes the result `unverifiable` with
`reason: merge_in_range`.

Output (check shape): line 1 `pass`, `fail`, or `unverifiable`; then `reason:`
lines; last line `repro-order: <verdict> (<r> repro, <f> fix commit(s))`, with
`, <n> finding(s)` added inside the parentheses on `fail`. On `pass` each repro
and fix commit gets one line, oldest first:
  reason: repro <short-sha> <subject> (<n> test file(s))
  reason: fix <short-sha> <subject> (<n> source file(s))
Control characters in a printed path, subject, or switch value are escaped
(`\\n`, `\\x1b`), so every `reason:` line stays one line.

Exit 0 pass or unverifiable, 1 fail, 2 usage or a check that could not start
(unreadable config, unresolvable revision, base not an ancestor of head, not a
git repository, git not found): stdout empty, cause on stderr after
`repro-order: `.

Stdlib only, Python 3.9. Runs only `git`. Writes nothing.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

CONFIG_REL = ".writ/config.md"
SWITCH_LINE = re.compile(r"^- \*\*Repro First:\*\*[ \t]*(.*)$", re.MULTILINE)
TRAILER = re.compile(r"^Repro:[ \t]*\S")
PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
IGNORED_PREFIX = ".writ/"
TEST_DIRS = frozenset({"test", "tests", "__tests__", "spec", "e2e", "cypress"})
TEST_NAMES = ("test_*", "*_test.*", "*.test.*", "*.spec.*", "*_spec.*", "*Test.*",
              "*Tests.*", "conftest.py")
# C0, DEL, C1, and the Unicode line and paragraph separators: any of them in a
# printed path or subject could start a new output line.
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
TWO_PATH_STATUSES = ("R", "C")  # rename and copy entries carry old and new path
WRITE_STATUSES = ("A", "M", "T")
SHORT_SHA = 7


class UsageError(Exception):
    """Exit-2 conditions: the check could not start."""


class Commit(NamedTuple):
    sha: str
    subject: str
    repro: bool
    paths: List[str]    # every changed path, both sides of a rename, in diff order
    written: List[str]  # paths that hold new content after the commit
    tests: List[str]
    sources: List[str]


# ---------------------------------------------------------------------------
# Switch
# ---------------------------------------------------------------------------

def switch_value(repo: Path) -> Optional[str]:
    """The raw Repro First value (first matching line); None when the file or
    the line is absent. An existing but unreadable file is a usage error."""
    config = repo / CONFIG_REL
    try:
        # exists() itself raises when `.writ/` cannot be searched.
        if not config.exists():
            return None
        text = config.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError("cannot read %s (%s)" % (CONFIG_REL, exc))
    match = SWITCH_LINE.search(text)
    return match.group(1).strip() if match else None


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run one git command in `repo`. Never raises on a non-zero exit; each
    caller maps the exit code to its own error."""
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              check=False, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise UsageError("git not found")
    except OSError as exc:
        raise UsageError("cannot run git (%s)" % exc)


def _git_out(repo: Path, *args: str) -> str:
    proc = _git(repo, *args)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or "exit %d" % proc.returncode
        raise UsageError("git %s failed (%s)" % (args[0], detail))
    return proc.stdout


def _resolve(repo: Path, rev: str) -> str:
    if rev.startswith("-"):  # git would read it as an option, not a revision
        raise UsageError("cannot resolve %s" % rev)
    proc = _git(repo, "rev-parse", "--verify", "--quiet", "%s^{commit}" % rev)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise UsageError("cannot resolve %s" % rev)
    return proc.stdout.strip()


def _parse_name_status(raw: str) -> List[Tuple[str, List[str]]]:
    """`git diff-tree --name-status -z` output -> [(status letter, paths)]."""
    fields = raw.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    entries: List[Tuple[str, List[str]]] = []
    i = 0
    while i < len(fields):
        letter = fields[i][:1]
        count = 2 if letter in TWO_PATH_STATUSES else 1
        paths = fields[i + 1:i + 1 + count]
        if len(paths) != count:
            raise UsageError("unexpected git diff-tree output")
        entries.append((letter, paths))
        i += 1 + count
    return entries


def is_repro(message: str) -> bool:
    final = PARAGRAPH_BREAK.split(message.strip())[-1]
    return any(TRAILER.match(line) for line in final.splitlines())


def classify(path: str, globs: Sequence[str]) -> str:
    """`ignored`, `test`, or `source` for one repo-relative POSIX path."""
    if path.startswith(IGNORED_PREFIX):
        return "ignored"
    parts = path.split("/")
    if any(part in TEST_DIRS for part in parts[:-1]):
        return "test"
    if any(fnmatch.fnmatchcase(parts[-1], pattern) for pattern in TEST_NAMES):
        return "test"
    if any(fnmatch.fnmatchcase(path, pattern) for pattern in globs):
        return "test"
    return "source"


def _unique(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))


def printable(text: str) -> str:
    """Escape control characters (`\\n` -> `\\\\n`, ESC -> `\\\\x1b`) so a crafted
    path or subject cannot add an output line. Other text is unchanged."""
    return CONTROL.sub(lambda m: repr(m.group())[1:-1], text)


def load_commit(repo: Path, sha: str, globs: Sequence[str]) -> Commit:
    message = _git_out(repo, "show", "-s", "--no-color", "--no-show-signature",
                       "--format=%B", sha)
    raw = _git_out(repo, "diff-tree", "--no-commit-id", "--root", "-r", "-M",
                   "--name-status", "-z", sha)
    paths: List[str] = []
    written: List[str] = []
    for letter, entry_paths in _parse_name_status(raw):
        paths.extend(entry_paths)
        if letter in TWO_PATH_STATUSES:
            written.append(entry_paths[-1])
        elif letter in WRITE_STATUSES:
            written.append(entry_paths[0])
    paths = _unique(paths)
    kinds = {path: classify(path, globs) for path in paths}
    lines = message.strip().splitlines()
    return Commit(sha=sha, subject=lines[0].strip() if lines else "",
                  repro=is_repro(message), paths=paths, written=_unique(written),
                  tests=[p for p in paths if kinds[p] == "test"],
                  sources=[p for p in paths if kinds[p] == "source"])


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def apply_rules(commits: List[Commit]) -> Tuple[List[str], List[Commit], List[Commit]]:
    """(findings in rule order, repro commits, fix commits)."""
    repro_at = [i for i, c in enumerate(commits) if c.repro]
    repros = [commits[i] for i in repro_at]
    first = repro_at[0] if repro_at else len(commits)
    fix_at = [i for i, c in enumerate(commits)
              if i > first and not c.repro and c.sources]
    findings: List[str] = []
    if not repros:
        findings.append("no_repro_commit")
    findings += ["repro_empty %s" % c.sha[:SHORT_SHA] for c in repros if not c.tests]
    findings += ["repro_touches_source %s %s" % (c.sha[:SHORT_SHA], path)
                 for c in repros for path in c.sources]
    if repros:  # with no repro there is no "before the first repro"
        findings += ["source_before_repro %s %s" % (c.sha[:SHORT_SHA], path)
                     for c in commits[:first] for path in c.sources]
    findings += ["no_fix_after_repro %s" % commits[i].sha[:SHORT_SHA]
                 for i in repro_at if not any(j > i for j in fix_at)]
    # Rule 6: a test file a repro wrote is frozen from that repro on.
    frozen_at: Dict[str, int] = {}
    for i in repro_at:
        written = set(commits[i].written)
        for path in commits[i].tests:
            if path in written:
                frozen_at.setdefault(path, i)
    for j, c in enumerate(commits):
        if c.repro:
            continue
        findings += ["repro_test_modified %s %s" % (c.sha[:SHORT_SHA], path)
                     for path in c.paths if frozen_at.get(path, j) < j]
    return findings, repros, [commits[j] for j in fix_at]


def _count(n: int, noun: str) -> str:
    return "%d %s%s" % (n, noun, "" if n == 1 else "s")


def summary(verdict: str, repros: int, fixes: int, findings: Optional[int] = None) -> str:
    tail = "" if findings is None else ", %d finding(s)" % findings
    return "repro-order: %s (%d repro, %d fix commit(s)%s)" % (verdict, repros, fixes, tail)


def check(repo: Path, base: str, head: str,
          globs: Sequence[str]) -> Tuple[str, List[str], str]:
    """(verdict, reasons, summary line). Raises UsageError for exit 2."""
    reasons: List[str] = []
    value = switch_value(repo)
    if value is not None and value.lower() == "off":
        return "unverifiable", ["repro-first off"], summary("unverifiable", 0, 0)
    if value and value.lower() != "on":
        reasons.append("repro-first value %s read as on" % value)

    if _git(repo, "rev-parse", "--git-dir").returncode != 0:
        raise UsageError("not a git repository")
    base_sha = _resolve(repo, base)
    head_sha = _resolve(repo, head)
    ancestry = _git(repo, "merge-base", "--is-ancestor", base_sha, head_sha)
    if ancestry.returncode == 1:
        raise UsageError("%s is not an ancestor of %s" % (base, head))
    if ancestry.returncode != 0:
        raise UsageError("git merge-base failed (%s)" % ancestry.stderr.strip())

    span = "%s..%s" % (base_sha, head_sha)
    if _git_out(repo, "rev-list", "--merges", span).strip():
        reasons.append("merge_in_range")
        return "unverifiable", reasons, summary("unverifiable", 0, 0)

    shas = _git_out(repo, "rev-list", "--reverse", span).split()
    commits = [load_commit(repo, sha, globs) for sha in shas]
    findings, repros, fixes = apply_rules(commits)
    if findings:
        reasons += findings
        return "fail", reasons, summary("fail", len(repros), len(fixes), len(findings))
    fix_shas = {c.sha for c in fixes}
    for c in commits:
        if c.repro:
            reasons.append("repro %s %s (%s)" % (c.sha[:SHORT_SHA], c.subject,
                                                 _count(len(c.tests), "test file")))
        elif c.sha in fix_shas:
            reasons.append("fix %s %s (%s)" % (c.sha[:SHORT_SHA], c.subject,
                                               _count(len(c.sources), "source file")))
    return "pass", reasons, summary("pass", len(repros), len(fixes))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repro-order.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    c = sub.add_parser("check", help="check that each repro commit precedes its fix")
    c.add_argument("--base", required=True, help="the commit before the repro")
    c.add_argument("--head", default="HEAD", help="last commit of the range (default HEAD)")
    c.add_argument("--repo", type=Path, default=Path("."),
                   help="repository root (default .)")
    c.add_argument("--test-glob", action="append", default=[], metavar="PATTERN",
                   help="fnmatch pattern that also marks a test file; repeatable")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        verdict, reasons, last = check(args.repo, args.base, args.head, args.test_glob)
    except UsageError as exc:
        print("repro-order: %s" % exc, file=sys.stderr)
        return 2
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="backslashreplace")  # a non-UTF-8 console never crashes output
    print("\n".join([verdict] + ["reason: %s" % printable(r) for r in reasons] + [last]))
    return 1 if verdict == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
