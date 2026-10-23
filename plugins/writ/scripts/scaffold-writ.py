#!/usr/bin/env python3
"""Create the `.writ/` tree that Writ's commands write into.

`/initialize` runs this as Step 0, so a project that got Writ from a plugin,
with no `install.sh` run, gets the same tree an `install.sh` project gets.
`install.sh` and `update.sh` keep a bash `init_writ_workspace` with the same
list and the same `.gitignore` rule; `scripts/tests/test_scaffold_writ.py`
fails when the two drift. ADR-031 records why the installers do not call this
script.

Subcommand:
  scaffold [--project DIR] [--check]

`scaffold` creates each missing directory in PATHS and adds each missing
entry in IGNORE_ENTRIES to `DIR/.gitignore`, creating the file when absent.
A second run creates nothing and leaves `.gitignore` byte-identical.
`--check` writes nothing and reports what is missing. `--project` defaults to
the current directory.

`.gitignore` lines compare trimmed and whole, with one trailing `/` ignored,
so `.writ/state` and `.writ/state/` are one entry. Missing entries are
appended in one write, under a new `# Writ ephemeral state` comment unless the
file already has that comment line. The write goes through a temp file and
`os.replace`.

Output (check shape, paths relative to DIR):
  scaffold          pass | fail
                    created <path>                 one per directory created
                    added .gitignore entry <entry> one per entry added
                    reason: not a directory <path> a non-directory is in the way
                    scaffold-writ: <verdict> (<n> created, <m> existing[, <k> not a directory])
  scaffold --check  pass | fail
                    reason: missing <path>
                    reason: missing .gitignore entry <entry>
                    reason: not a directory <path>
                    scaffold-writ: <verdict> (<m> missing)

`<n>` and `<m>` in the scaffold summary count the eleven PATHS only.

Exit 0: pass. Exit 1: fail. Exit 2: usage, or `--project` is not a directory.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path
from typing import List, Optional, Tuple

PATHS = (
    ".writ/specs",
    ".writ/product",
    ".writ/research",
    ".writ/decision-records",
    ".writ/docs",
    ".writ/knowledge",
    ".writ/state",
    ".writ/issues/bugs",
    ".writ/issues/features",
    ".writ/issues/improvements",
    ".writ/issues/goals",
)
IGNORE_ENTRIES = (".writ/state/", ".writ-lanes-*/")
IGNORE_COMMENT = "# Writ ephemeral state"
# The characters bash's [[:space:]] matches in the C locale, so the bash
# mirror in the installers trims the same way.
SPACE = " \t\n\r\v\f"


def _key(line: str) -> str:
    line = line.strip(SPACE)
    return line[:-1] if line.endswith("/") else line


def read_gitignore(path: Path) -> Optional[str]:
    """The file's text (undecodable bytes kept through surrogateescape), or None if absent."""
    if not path.is_file():
        return None
    return path.read_bytes().decode("utf-8", errors="surrogateescape")


def missing_entries(text: Optional[str]) -> List[str]:
    present = {_key(line) for line in (text or "").split("\n")}
    return [entry for entry in IGNORE_ENTRIES if _key(entry) not in present]


def with_entries(text: Optional[str], entries: List[str]) -> str:
    """`text` plus `entries`, one per line; the comment is written only when absent."""
    block = "".join(entry + "\n" for entry in entries)
    if text is None:
        return IGNORE_COMMENT + "\n" + block
    if any(line.strip(SPACE) == IGNORE_COMMENT for line in text.split("\n")):
        head = "\n" if text and not text.endswith("\n") else ""
        return text + head + block
    return text + "\n" + IGNORE_COMMENT + "\n" + block


def write_atomic(path: Path, text: str) -> None:
    """Write through a temp file beside the target, then rename it over the target.

    A symlinked `.gitignore` keeps its link: the file it points to is replaced.
    The mode of an existing file is kept; a new file gets 0666 minus the umask.
    """
    target = Path(os.path.realpath(str(path)))
    tmp = target.with_name("%s.scaffold-writ.%d.tmp" % (target.name, os.getpid()))
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8", errors="surrogateescape"))
        if mode is not None:
            os.chmod(str(tmp), mode)
        os.replace(str(tmp), str(target))
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise


def emit(verdict: str, details: List[str], summary: str) -> int:
    print(verdict)
    for line in details:
        print(line)
    print(summary)
    return 1 if verdict == "fail" else 0


def classify(project: Path) -> Tuple[List[str], List[str], List[str]]:
    """(existing, missing, blocked) PATHS: blocked means a non-directory is at the path."""
    existing: List[str] = []
    missing: List[str] = []
    blocked: List[str] = []
    for rel in PATHS:
        path = project / rel
        if path.is_dir():
            existing.append(rel)
        elif path.exists() or path.is_symlink():
            blocked.append(rel)
        else:
            missing.append(rel)
    return existing, missing, blocked


def run_check(project: Path) -> int:
    _, missing, blocked = classify(project)
    entries = missing_entries(read_gitignore(project / ".gitignore"))
    details = (["reason: missing %s" % rel for rel in missing]
               + ["reason: missing .gitignore entry %s" % entry for entry in entries]
               + ["reason: not a directory %s" % rel for rel in blocked])
    verdict = "fail" if details else "pass"
    return emit(verdict, details, "scaffold-writ: %s (%d missing)" % (verdict, len(details)))


def run_scaffold(project: Path) -> int:
    existing, missing, blocked = classify(project)
    created: List[str] = []
    for rel in missing:
        try:
            (project / rel).mkdir(parents=True, exist_ok=True)
            created.append(rel)
        except OSError:
            # A file where a parent directory belongs, e.g. `.writ` itself.
            blocked.append(rel)
    blocked.sort(key=PATHS.index)

    gitignore = project / ".gitignore"
    text = read_gitignore(gitignore)
    entries = missing_entries(text)
    if entries:
        write_atomic(gitignore, with_entries(text, entries))

    details = (["created %s" % rel for rel in created]
               + ["added .gitignore entry %s" % entry for entry in entries]
               + ["reason: not a directory %s" % rel for rel in blocked])
    verdict = "fail" if blocked else "pass"
    counts = "%d created, %d existing" % (len(created), len(existing))
    if blocked:
        counts += ", %d not a directory" % len(blocked)
    return emit(verdict, details, "scaffold-writ: %s (%s)" % (verdict, counts))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scaffold-writ.py",
        description="Create the .writ/ tree Writ's commands write into, and the "
                    ".gitignore entries for its ephemeral state.")
    sub = parser.add_subparsers(dest="command", metavar="scaffold")
    sub.required = True
    scaffold = sub.add_parser(
        "scaffold", help="create missing .writ/ directories and .gitignore entries",
        description="Create each missing .writ/ directory and .gitignore entry. "
                    "Idempotent: a second run creates nothing.")
    scaffold.add_argument("--project", default=".", metavar="DIR",
                          help="project root (default: the current directory)")
    scaffold.add_argument("--check", action="store_true",
                          help="write nothing; report each missing path and entry")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(args.project)
    if not project.is_dir():
        parser.print_usage(sys.stderr)
        print("scaffold-writ.py: error: --project %s is not a directory" % args.project,
              file=sys.stderr)
        return 2
    if args.check:
        return run_check(project)
    return run_scaffold(project)


if __name__ == "__main__":
    sys.exit(main())
