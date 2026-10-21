#!/usr/bin/env python3
"""Find links to Writ's own development history in shipped commands.

Spec: 2026-10-20-shipped-command-hygiene, Story 1. Consumed by scripts/eval.sh
check_shipped_refs.

An installed project has none of Writ's ADR files, archived specs, research
documents, or calibration records. A shipped command that links to one sends
the user, or the user's agent, to a path that does not exist. Four rules:

  archived-spec      a dated .writ/specs/archive/<date>-<name> path, or the
                     old .writ/specs/<date>-<name> path when that folder now
                     lives under <root>/.writ/specs/archive/
  research           a dated .writ/research/<date>-... document
  adr                a decision-records/adr-NNN-... file, any relative prefix
  calibration-state  on a calibrated_against: line, a .writ/state or
                     .writ/specs/archive token that is not a glob (no *)

Runtime paths stay: directories, placeholders, and globs over the user's own
files (.writ/state/, .writ/specs/<name>/, .writ/research/[DATE]-...,
.writ/decision-records/adr-*.md) and shipped .writ/docs/ files.

Output is PASS/FAIL TSV, the shape of the other eval-*.py emitters. One
self-test scenario per rule runs first, against synthetic lines, so a regex
that silently matches nothing fails the check instead of passing it. Then one
FAIL line per hit on the tree, or one PASS shipped-refs-tree line.

Exit codes: 0 all PASS, 1 any FAIL, 2 nothing to scan (no commands/*.md under
--root). Dev-only: install.sh never ships eval-* scripts. Python 3.9,
standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent

# Directories whose *.md files ship to installed projects and are scanned.
# The later agents/, adapters/, skills/, .writ/docs/ pass widens this tuple.
SCANNED_DIRS = ("commands",)

KINDS = ("archived-spec", "research", "adr", "calibration-state")

# Keyed by kind; a kind with two forms has a second key with a suffix, so
# every pattern for a kind starts with the kind's name.
PATTERNS = {
    "archived-spec": re.compile(r"\.writ/specs/archive/\d{4}-\d{2}-\d{2}-[\w.-]+"),
    "archived-spec-old": re.compile(r"\.writ/specs/(\d{4}-\d{2}-\d{2}-[\w-]+)"),
    "research": re.compile(r"\.writ/research/\d{4}-\d{2}-\d{2}-[\w.-]+"),
    "adr": re.compile(r"decision-records/adr-\d{3}-[\w.-]+"),
    "calibration-state-line": re.compile(r"^\s*(?:-\s+)?calibrated_against:"),
    "calibration-state": re.compile(
        r"\.writ/(?:state|specs/archive)(?![\w-])(?:/[\w.*{}<>\[\]/-]*)?"),
}

Hit = Tuple[str, str]  # (kind, token)
IsArchived = Callable[[str], bool]


def find_refs(line: str, is_archived: IsArchived) -> List[Hit]:
    """Return every internal reference on one line, in column order."""
    found: List[Tuple[int, int, str, str]] = []

    def add(kind: str, match: "re.Match[str]") -> None:
        # A trailing period ends the sentence, not the path.
        found.append((match.start(), match.end(), kind, match.group(0).rstrip(".")))

    for match in PATTERNS["archived-spec"].finditer(line):
        add("archived-spec", match)
    for match in PATTERNS["archived-spec-old"].finditer(line):
        if is_archived(match.group(1)):
            add("archived-spec", match)
    for match in PATTERNS["research"].finditer(line):
        add("research", match)
    for match in PATTERNS["adr"].finditer(line):
        add("adr", match)
    if PATTERNS["calibration-state-line"].search(line):
        for match in PATTERNS["calibration-state"].finditer(line):
            if "*" in match.group(0):
                continue  # a glob over the user's own records
            if any(start < match.end() and match.start() < end for start, end, _, _ in found):
                continue  # already reported as an archived-spec path
            add("calibration-state", match)

    found.sort(key=lambda item: item[0])
    return [(kind, token) for _, _, kind, token in found]


# One scenario per rule: every positive line must hit with that kind, and no
# negative line may.
SYNTHETIC_ARCHIVED = {"2026-01-01-synthetic-archived"}
SELF_TESTS = {
    "archived-spec": (
        [".writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md#x",
         "`.writ/specs/2026-01-01-synthetic-archived/sub-specs/technical-spec.md`"],
        ["`.writ/specs/archive/<name>/`", "`.writ/specs/archive/LEDGER.md`",
         "`.writ/specs/archive/**`", ".writ/specs/2026-03-15-auth-system/spec.md",
         "`.writ/specs/<name>/`"],
    ),
    "research": (
        ["(`.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`)"],
        ["`.writ/research/`", "`.writ/research/[DATE]-[topic-name]-research.md`",
         ".writ/research/<YYYY-MM-DD>-<topic>-research.md"],
    ),
    "adr": (
        ["[ADR-017](../.writ/decision-records/adr-017-git-notes-audit-channel.md)",
         "[ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md)"],
        ["`.writ/decision-records/adr-*.md`", ".writ/decision-records/adr-{NN}-*.md",
         "`ADR-000-product-posture.md`", "Design principle (ADR-001)"],
    ),
    "calibration-state": (
        ['  calibrated_against: "Observed: .writ/state/phase-execution-20260719-121255.json."',
         '  calibrated_against: "zero runs anywhere in .writ/state/, so"',
         '  calibrated_against: "41 specs under .writ/specs/archive/ = 9"'],
        ['  calibrated_against: "Recalibrate against .writ/state/phase-execution-*.json."',
         '  calibrated_against: "scripts/phase-state.py cmd_classify"',
         "Prose that names `.writ/state/` off a calibration line."],
    ),
}


def self_test() -> List[Tuple[str, bool, str]]:
    """Run each rule against its synthetic lines; return (name, ok, detail)."""
    results = []
    is_archived = SYNTHETIC_ARCHIVED.__contains__
    for kind in KINDS:
        positives, negatives = SELF_TESTS[kind]
        problems = []
        for line in positives:
            if kind not in [k for k, _ in find_refs(line, is_archived)]:
                problems.append(f"missed: {line}")
        for line in negatives:
            if kind in [k for k, _ in find_refs(line, is_archived)]:
                problems.append(f"flagged: {line}")
        results.append((f"shipped-refs-rule-{kind}", not problems, "; ".join(problems)))
    return results


def shipped_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for name in SCANNED_DIRS:
        folder = root / name
        if folder.is_dir():
            files.extend(path for path in sorted(folder.glob("*.md"))
                         if not path.name.endswith(".lean.md"))  # never ships
    return files


def scan(root: Path, files: Iterable[Path]) -> List[Tuple[str, int, str, str]]:
    archive = root / ".writ" / "specs" / "archive"

    def is_archived(name: str) -> bool:
        return (archive / name).is_dir()

    hits = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            for kind, token in find_refs(line, is_archived):
                hits.append((rel, number, kind, token))
    return hits


def clean(value: object) -> str:
    return str(value).replace("\n", "\\n").replace("\t", " ")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(ROOT), help="repo root to scan (default: this repo)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    failed = False
    for name, ok, detail in self_test():
        print(f"PASS\t{name}" if ok else f"FAIL\t{name}\t{clean(detail)}")
        failed = failed or not ok

    files = shipped_files(root)
    if not files:
        print(f"eval-shipped-refs: no shipped command files under {root} "
              f"({', '.join(d + '/*.md' for d in SCANNED_DIRS)})", file=sys.stderr)
        return 2

    hits = scan(root, files)
    for rel, number, kind, token in hits:
        print(f"FAIL\tshipped-refs:{rel}:{number}\t{kind}: {clean(token)}")
    if not hits:
        print("PASS\tshipped-refs-tree")
    return 1 if failed or hits else 0


if __name__ == "__main__":
    sys.exit(main())
