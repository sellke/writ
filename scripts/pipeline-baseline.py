#!/usr/bin/env python3
"""Fixed-criteria story selection for the Writ pipeline baseline.

`select` scans a yuss.app checkout's archived specs
(`<yuss>/.writ/specs/archive/*/user-stories/story-*.md`), admits the stories
that meet every rule in the spec (Completed status, a resolvable closing
commit with a parent, at least one touched test file, tests that need no
live service, no database-migration prerequisite in `## Notes`), classifies
each admitted story by the surface its commit touched, and writes exactly
four stories — one per class — into a `pipeline-baseline-v1` JSON skeleton
that Story 4's `run` fills with run records.

Every rule that admitted a story is echoed into the JSON's `criteria` block
and every selected entry's `criteria_values`, so a reader can tell why those
four stories were chosen from the file alone. The most recent rejections are
kept in `excluded` (capped) and every rejection is counted in
`rejection_tally`.

Business Rule 2: `<yuss>` is read-only. Every subprocess this script spawns
is `git -C <yuss> {rev-parse,log,show,diff-tree}`; file contents at a commit
come from `git show <commit>:<path>`, never a checkout. Business Rule 3: the
JSON carries paths, SHAs, counts, and reason codes — never source or story
text. `excluded[].detail` is capped at 200 characters.

Subcommands:
  select   --yuss PATH --out PATH [--model ID] [--deny-list a,b,...]
           [--excluded-cap N] [--live-test-scope story|file] [--force]
  run / ingest / compare   stubs until Story 4 / Story 5

Exit codes: 0 written · 1 a surface class has no admissible story
(`--out` untouched) · 2 usage, invalid `--yuss`, refused `--out`, or no
candidates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional


SCHEMA = "pipeline-baseline-v1"
DEFAULT_MODEL = "claude-fable-5-1"

# Top-level key order of the JSON. Story 5's validator imports this.
SCHEMA_KEYS = (
    "schema", "model", "generated_at", "yuss_head", "runs_per_story",
    "criteria", "selection", "excluded", "rejection_tally", "runs",
)
# Per-entry key order in `selection[]`. Story 4 reads these verbatim.
SELECTION_KEYS = (
    "story_path", "spec_folder", "story_id", "story_commit", "parent_sha",
    "parent_is_merge", "surface_class", "eligible_classes", "test_files",
    "criteria_values",
)
SURFACE_CLASSES = ("api_route", "ui", "data_model", "refactor")
REASONS = (
    "status_not_completed", "commit_unresolved", "git_error", "no_test_files",
    "live_service_import", "migration_prerequisite", "no_surface_class",
    "class_filled",
)

DEFAULT_DENY_LIST = ("prisma", "stripe", "@neondatabase", "next-auth")
DEFAULT_EXCLUDED_CAP = 10
DETAIL_MAX_CHARS = 200
LIVE_TEST_SCOPES = ("story", "file")

TEST_FILE_GLOBS = ("*.test.*", "*.spec.*", "__tests__/**", "tests/**")
# A path matching a glob is a test file only with a source extension: the
# yuss archive has `tests/integration/README.md` and fixture JSON under the
# `tests/**` glob, which are neither runnable nor scannable for imports.
TEST_FILE_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts")
# Directories whose tests are treated as live under `--live-test-scope file`.
LIVE_TEST_DIRS = ("tests/integration/", "tests/e2e/")
SCHEMA_PATH_PREFIXES = ("prisma/", "lib/db/")
CLASS_PATHS = {
    "api_route": ["app/api/**"],
    "ui": ["components/**", "app/**/page.tsx"],
    "data_model": ["prisma/**", "lib/db/**"],
}
REFACTOR_RULE = "no new files and net negative lines (renames counted as delete+add)"
STATUS_REQUIRED = "Completed"
STATUS_PATTERN = (
    "^complete(d)?$ case-insensitive, after stripping non-ASCII symbols, "
    "parentheticals, and whitespace"
)
TIE_BREAK = "commit date desc, then story number desc, then story_path asc"
CLASS_FILL_ORDER = "ascending eligible-candidate count, then api_route, ui, data_model, refactor"

# Subcommands the `Git` helper will spawn. Anything else is refused before a
# process is started — Business Rule 2 enforced in code, not only in tests.
READ_ONLY_GIT = frozenset({"rev-parse", "log", "show", "diff-tree"})

# `git log --grep` regex (ERE, case-insensitive). No `\b`: Apple Git's ERE
# silently matches nothing on it. `([^0-9]|$)` keeps "Story 30" from
# resolving "Story 3".
LOG_GREP_TEMPLATE = "stor(y|ies)[ -]?%d([^0-9]|$)"
LOG_GREP_PATHSPECS = (".writ/specs/<folder>", ".writ/specs/archive/<folder>")

STATUS_LINE = re.compile(r"(?m)^> \*\*Status:\*\*\s*(.*?)\s*$")
COMMIT_LINE = re.compile(r"(?m)^> \*\*Commit:\*\*\s*(.*?)\s*$")
NOTES_SECTION = re.compile(r"(?ms)^## Notes\s*$(.*?)(?=^## |\Z)")
STORY_FILE = re.compile(r"^story-(\d+)-")
HEX_TOKEN = re.compile(r"\b[0-9a-fA-F]{7,40}\b")
PARENTHETICAL = re.compile(r"\([^)]*\)")
NON_ASCII = re.compile(r"[^\x00-\x7f]")
COMPLETED = re.compile(r"(?i)^complete(d)?$")
# A `## Notes` line that names a migration *and* frames it as a precondition.
MIGRATION_NOTE = re.compile(
    r"(?im)^(?=.*\bmigrations?\b)"
    r"(?=.*\b(prerequisites?|requires?|required|must|before|first|depends?|apply|applied|run)\b).*$"
)
# Module specifiers in ES imports, dynamic imports, and require() calls.
IMPORT_SPEC = re.compile(
    r"""(?m)(?:\bfrom\s*|\bimport\s*\(\s*|\brequire\s*\(\s*|^\s*import\s+)['"]([^'"]+)['"]"""
)
JEST_MOCK = re.compile(r"""\bjest\.mock\(\s*['"]([^'"]+)['"]""")


class GitError(Exception):
    """A git invocation failed or was refused."""


class Git:
    """Read-only `git -C <yuss>` runner. Every call goes through `run`."""

    def __init__(self, yuss: Path) -> None:
        self.yuss = yuss

    def run(self, *args: str, check: bool = True) -> Optional[str]:
        if not args or args[0] not in READ_ONLY_GIT:
            raise GitError("refusing non-read-only git subcommand: %s" % (args[:1] or ("",))[0])
        # `errors="replace"`: a non-UTF-8 test file read via `show <commit>:<path>`
        # must not raise UnicodeDecodeError past `admit`'s GitError handling.
        proc = subprocess.run(
            ["git", "-C", str(self.yuss), *args], capture_output=True,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            if check:
                raise GitError("git %s exited %d" % (args[0], proc.returncode))
            return None
        return proc.stdout


@dataclass
class Candidate:
    story_path: str          # relative to <yuss>, posix
    spec_folder: str
    story_id: str            # <spec_folder>/<file stem>
    story_number: int
    status: str
    commit_header: Optional[str]
    notes: str


@dataclass
class Change:
    sha: str
    parents: list
    commit_time: int
    paths: list              # every touched path (renames as delete+add)
    net_lines: int           # added - deleted over text files
    new_files: list          # `--diff-filter=A`, sorted
    deleted_files: list      # `--diff-filter=D`, sorted


@dataclass
class Rules:
    model: str = DEFAULT_MODEL
    deny_list: tuple = DEFAULT_DENY_LIST
    excluded_cap: int = DEFAULT_EXCLUDED_CAP
    live_test_scope: str = "story"


@dataclass
class SelectionSortKey:
    commit_time: int
    story_number: int
    story_path: str


@dataclass
class Verdict:
    rejection: Optional[tuple] = None        # (reason, detail)
    commit: Optional[str] = None
    parent: Optional[str] = None
    parent_is_merge: bool = False
    commit_time: int = 0
    test_files: list = field(default_factory=list)
    eligible: list = field(default_factory=list)
    criteria_values: dict = field(default_factory=dict)


def preference(key) -> tuple:
    """Sort key: most recent commit first, then higher story number, then
    lexical path. `min()` over this picks the winner of a class."""
    return (-key.commit_time, -key.story_number, key.story_path)


def clip(text: str) -> str:
    return text[:DETAIL_MAX_CHARS]


# ---------------------------------------------------------------------------
# Story-file parsing
# ---------------------------------------------------------------------------


def is_completed(raw: str) -> bool:
    cleaned = NON_ASCII.sub("", PARENTHETICAL.sub("", raw)).strip()
    return bool(COMPLETED.match(cleaned))


def commit_from_header(raw: str) -> Optional[str]:
    match = HEX_TOKEN.search(raw)
    return match.group(0) if match else None


def mentions_migration_prerequisite(notes: str) -> bool:
    return bool(MIGRATION_NOTE.search(notes))


def parse_story(yuss: Path, path: Path) -> Candidate:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(yuss).as_posix()
    number_match = STORY_FILE.match(path.name)
    status = STATUS_LINE.search(text)
    commit = COMMIT_LINE.search(text)
    notes = NOTES_SECTION.search(text)
    spec_folder = path.parent.parent.name
    return Candidate(
        story_path=rel,
        spec_folder=spec_folder,
        story_id="%s/%s" % (spec_folder, path.stem),
        story_number=int(number_match.group(1)) if number_match else 0,
        status=status.group(1) if status else "",
        commit_header=commit.group(1) if commit else None,
        notes=notes.group(1) if notes else "",
    )


def discover(yuss: Path) -> list:
    archive = yuss / ".writ" / "specs" / "archive"
    files = sorted(archive.glob("*/user-stories/story-*.md"),
                   key=lambda p: p.relative_to(yuss).as_posix())
    return [parse_story(yuss, p) for p in files if p.is_file()]


# ---------------------------------------------------------------------------
# Git-backed analysis
# ---------------------------------------------------------------------------


def resolve_commit(git: Git, folder: str, number: int, header: Optional[str]) -> tuple:
    """Return (sha, source). `source` is `header`, `log_grep`, or the reason
    code `commit_unresolved` when `sha` is None."""
    if header:
        token = commit_from_header(header)
        if token:
            out = git.run("rev-parse", "--verify", "-q", token + "^{commit}", check=False)
            if out:
                return out.strip(), "header"
    out = git.run(
        "log", "-1", "--format=%H", "-E", "-i", "--grep", LOG_GREP_TEMPLATE % number,
        "--", ".writ/specs/%s" % folder, ".writ/specs/archive/%s" % folder,
        check=False,
    )
    if out and out.strip():
        return out.strip().splitlines()[0], "log_grep"
    return None, "commit_unresolved"


def analyze_commit(git: Git, sha: str) -> Change:
    out = git.run("show", "-m", "--first-parent", "--no-renames", "--numstat",
                  "--format=%H%n%P%n%ct", sha) or ""
    lines = out.splitlines()
    if len(lines) < 3:
        raise GitError("git show returned no header for %s" % sha[:12])
    parents = lines[1].split()
    commit_time = int(lines[2])
    paths, net = [], 0
    for row in lines[3:]:
        parts = row.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        paths.append(path)
        if added != "-" and deleted != "-":
            net += int(added) - int(deleted)
    def listed(status: str) -> list:
        out = git.run("diff-tree", "-r", "--no-renames", "--diff-filter=" + status,
                      "--name-only", sha + "^1", sha) or ""
        return sorted(l for l in out.splitlines() if l)

    return Change(sha=lines[0], parents=parents, commit_time=commit_time,
                  paths=paths, net_lines=net, new_files=listed("A"), deleted_files=listed("D"))


# ---------------------------------------------------------------------------
# Pure admission rules
# ---------------------------------------------------------------------------


def is_test_file(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    if not name.endswith(TEST_FILE_EXTENSIONS):
        return False
    return (fnmatch(name, "*.test.*") or fnmatch(name, "*.spec.*")
            or "__tests__" in parts[:-1] or parts[0] == "tests")


def is_refactor(change: Change) -> bool:
    return not change.new_files and change.net_lines < 0


def eligible_classes(paths: list, new_files: list, net_lines: int) -> list:
    source = [p for p in paths if not is_test_file(p)]
    classes = []
    if any(p.startswith("app/api/") for p in source):
        classes.append("api_route")
    if any(p.startswith("components/") or (p.startswith("app/") and p.endswith("/page.tsx"))
           or p == "app/page.tsx" for p in source):
        classes.append("ui")
    if any(p.startswith(SCHEMA_PATH_PREFIXES) for p in source):
        classes.append("data_model")
    if not new_files and net_lines < 0:
        classes.append("refactor")
    return classes


def deny_hits(content: str, deny_list: tuple) -> tuple:
    """Return (hits, mocked): deny-list entries matched by an import
    specifier, and entries named by a `jest.mock(` call, in the file."""
    hits, mocked = [], set()
    for spec in IMPORT_SPEC.findall(content):
        for entry in deny_list:
            if entry in spec and entry not in hits:
                hits.append(entry)
    for spec in JEST_MOCK.findall(content):
        for entry in deny_list:
            if entry in spec:
                mocked.add(entry)
    return hits, mocked


def live_service_scan(git: Git, commit: str, test_files: list, source_paths: list,
                      rules: Rules) -> tuple:
    """Return (clean_test_files, rejection_or_None, mocked_count, dropped_count).

    `story` scope: any uncovered deny hit rejects the story; a hit is covered
    only when the file `jest.mock`s the module and the commit's non-test
    touches are all schema files (`prisma/**`, `lib/db/**`).
    `file` scope: a test file is live if it sits under a live directory or has
    an uncovered hit (`jest.mock` in the same file covers it); live files are
    dropped and the story is admitted if one clean file remains.
    """
    schema_only = bool(source_paths) and all(p.startswith(SCHEMA_PATH_PREFIXES) for p in source_paths)
    clean, live, mocked_total = [], [], 0
    for path in test_files:
        content = git.run("show", "%s:%s" % (commit, path)) or ""
        hits, mocked = deny_hits(content, rules.deny_list)
        if rules.live_test_scope == "file":
            if path.startswith(LIVE_TEST_DIRS):
                live.append((path, "live_dir"))
                continue
            uncovered = [h for h in hits if h not in mocked]
        else:
            uncovered = [h for h in hits if not (schema_only and h in mocked)]
        if uncovered:
            live.append((path, uncovered[0]))
            continue
        mocked_total += len([h for h in hits if h in mocked])
        clean.append(path)
    if rules.live_test_scope == "story" and live:
        path, entry = live[0]
        more = "; +%d more" % (len(live) - 1) if len(live) > 1 else ""
        return [], ("live_service_import", clip("%s: %s%s" % (path, entry, more))), 0, 0
    if not clean:
        path, entry = live[0]
        detail = "%s: %s; 0 clean test files of %d" % (path, entry, len(test_files))
        return [], ("live_service_import", clip(detail)), 0, len(live)
    return clean, None, mocked_total, len(live)


def admit(git: Git, cand: Candidate, rules: Rules) -> Verdict:
    """Apply every admission rule to one candidate. Never raises for git
    failures: they become a `git_error` rejection."""
    verdict = Verdict()
    if not is_completed(cand.status):
        verdict.rejection = ("status_not_completed", "Status header is not Completed")
        return verdict
    try:
        commit, source = resolve_commit(git, cand.spec_folder, cand.story_number, cand.commit_header)
        if commit is None:
            how = "Commit header unresolvable" if cand.commit_header else "no Commit header"
            verdict.rejection = ("commit_unresolved", clip(
                "%s; log --grep found nothing under %d pathspecs" % (how, len(LOG_GREP_PATHSPECS))))
            return verdict
        parent = git.run("rev-parse", "--verify", "-q", commit + "^1", check=False)
        if not parent:
            verdict.rejection = ("commit_unresolved", "%s has no parent (root commit)" % commit[:12])
            return verdict
        verdict.commit, verdict.parent = commit, parent.strip()
        verdict.parent_is_merge = bool(git.run("rev-parse", "--verify", "-q", commit + "^2", check=False))
        change = analyze_commit(git, commit)
        verdict.commit_time = change.commit_time
        # A test file the commit deleted has no content at <commit> and cannot
        # be run against the produced tree, so it is not one of the story's tests.
        test_files = [p for p in change.paths if is_test_file(p) and p not in change.deleted_files]
        if not test_files:
            verdict.rejection = ("no_test_files", "%d changed paths, 0 test files" % len(change.paths))
            return verdict
        source_paths = [p for p in change.paths if not is_test_file(p)]
        clean, rejection, mocked, dropped = live_service_scan(
            git, commit, test_files, source_paths, rules)
    except GitError as exc:
        # `exc` carries only the subcommand and exit code (see Git.run), never
        # git's stderr, so it is safe to record as the detail.
        verdict.rejection = ("git_error", clip("%s for %s" % (exc, (verdict.commit or cand.story_id)[:40])))
        return verdict
    if rejection:
        verdict.rejection = rejection
        return verdict
    if mentions_migration_prerequisite(cand.notes):
        count = len(MIGRATION_NOTE.findall(cand.notes))
        verdict.rejection = ("migration_prerequisite",
                             "## Notes: %d line(s) match migration_note_pattern" % count)
        return verdict
    classes = eligible_classes(change.paths, change.new_files, change.net_lines)
    if not classes:
        verdict.rejection = ("no_surface_class", "%d non-test paths; new_files=%d net_lines=%d" % (
            len(source_paths), len(change.new_files), change.net_lines))
        return verdict
    verdict.test_files = clean
    verdict.eligible = classes
    verdict.criteria_values = {
        "status": STATUS_REQUIRED,
        "commit_source": source,
        "commit_timestamp": change.commit_time,
        "test_file_count": len(clean),
        "deny_list_hits": 0,
        "deny_list_mocked": mocked,
        "live_test_files_dropped": dropped,
        "migration_note": False,
        "new_files": len(change.new_files),
        "net_lines": change.net_lines,
    }
    return verdict


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


@dataclass
class Admitted:
    cand: Candidate
    verdict: Verdict
    key: SelectionSortKey


def assign_classes(admitted: list) -> tuple:
    """Fill classes in ascending eligible-candidate order, each with the
    most preferred unassigned eligible story. Returns (assigned, displaced)
    where `assigned` maps class -> Admitted and `displaced` lists the
    admissible stories no class took."""
    counts = {cls: sum(1 for a in admitted if cls in a.verdict.eligible) for cls in SURFACE_CLASSES}
    order = sorted(SURFACE_CLASSES, key=lambda c: (counts[c], SURFACE_CLASSES.index(c)))
    assigned, taken = {}, set()
    for cls in order:
        pool = [a for a in admitted if cls in a.verdict.eligible and id(a) not in taken]
        if not pool:
            continue
        best = min(pool, key=lambda a: preference(a.key))
        assigned[cls] = best
        taken.add(id(best))
    displaced = [a for a in admitted if id(a) not in taken]
    return assigned, displaced


def selection_entry(cls: str, a: Admitted) -> dict:
    v = a.verdict
    values = {
        "story_path": a.cand.story_path,
        "spec_folder": a.cand.spec_folder,
        "story_id": a.cand.story_id,
        "story_commit": v.commit,
        "parent_sha": v.parent,
        "parent_is_merge": v.parent_is_merge,
        "surface_class": cls,
        "eligible_classes": list(v.eligible),
        "test_files": list(v.test_files),
        "criteria_values": dict(v.criteria_values),
    }
    return {k: values[k] for k in SELECTION_KEYS}


def criteria_block(rules: Rules) -> dict:
    return {
        "status_required": STATUS_REQUIRED,
        "status_pattern": STATUS_PATTERN,
        "commit_resolution": {
            "header": "> **Commit:** first 7-40 hex token, verified with rev-parse --verify <token>^{commit}",
            "fallback": "git log -1 -E -i --grep <regex> -- <pathspecs>",
            "log_grep_regex": LOG_GREP_TEMPLATE.replace("%d", "<N>"),
            "log_grep_pathspecs": list(LOG_GREP_PATHSPECS),
            "parent": "rev-parse <commit>^1; root commits are commit_unresolved",
        },
        "requires_test_file": True,
        "test_file_globs": list(TEST_FILE_GLOBS),
        "test_file_extensions": list(TEST_FILE_EXTENSIONS),
        "test_files_exclude_deleted": True,
        "deny_list": list(rules.deny_list),
        "deny_list_scan": ("direct import/require specifiers of each touched test file at <commit>; "
                           "transitive imports are not followed"),
        "deny_list_match": "deny-list entry is a substring of the module specifier",
        "live_test_scope": rules.live_test_scope,
        "live_test_dirs": list(LIVE_TEST_DIRS) if rules.live_test_scope == "file" else [],
        "schema_only_relaxation": {
            "schema_paths": [p + "**" for p in SCHEMA_PATH_PREFIXES],
            "story_scope": ("a deny-list import is tolerated only when the same file jest.mock()s "
                            "that module and every non-test touch is a schema path"),
            "file_scope": "jest.mock() in the same file covers the import; live_test_dirs are always live",
        },
        "surface_classes": dict(CLASS_PATHS, refactor=REFACTOR_RULE),
        "class_paths_exclude_test_files": True,
        "migration_note_pattern": MIGRATION_NOTE.pattern,
        "migration_note_scope": "## Notes section only",
        "tie_break": TIE_BREAK,
        "class_fill_order": CLASS_FILL_ORDER,
        "exclusion_cap": rules.excluded_cap,
        "detail_max_chars": DETAIL_MAX_CHARS,
        "reason_codes": list(REASONS),
    }


def _umask() -> int:
    current = os.umask(0)
    os.umask(current)
    return current


def write_json(out: Path, doc: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(out.parent), prefix="." + out.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        # mkstemp creates 0600 and os.replace keeps it; a committed baseline
        # should carry the mode a plain `open(..., "w")` would have given it.
        os.chmod(tmp, 0o666 & ~_umask())
        os.replace(tmp, out)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# select
# ---------------------------------------------------------------------------


def _fail(message: str, code: int = 2) -> None:
    print("select: error: %s" % message, file=sys.stderr)
    sys.exit(code)


def cmd_select(args: argparse.Namespace) -> None:
    yuss = Path(args.yuss).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    rules = Rules(
        model=args.model,
        deny_list=tuple(e.strip() for e in args.deny_list.split(",") if e.strip()),
        excluded_cap=args.excluded_cap,
        live_test_scope=args.live_test_scope,
    )

    if not yuss.is_dir():
        _fail("--yuss %s is not a directory" % yuss)
    git = Git(yuss)
    toplevel = git.run("rev-parse", "--show-toplevel", check=False)
    if not toplevel or Path(toplevel.strip()).resolve() != yuss:
        _fail("--yuss %s is not a git repository" % yuss)
    if not (yuss / ".writ" / "specs" / "archive").is_dir():
        _fail("--yuss %s has no .writ/specs/archive folder" % yuss)
    try:
        out.relative_to(yuss)
    except ValueError:
        pass
    else:
        _fail("--out %s is inside --yuss; yuss is read-only (Business Rule 2)" % out)
    if out.exists() and not args.force:
        _fail("%s exists; pass --force to overwrite" % out)
    if not out.name.endswith("-%s.json" % rules.model):
        print("select: warning: --out basename %r does not end in '-%s.json' (Business Rule 4)"
              % (out.name, rules.model), file=sys.stderr)

    candidates = discover(yuss)
    if not candidates:
        _fail("no candidates under %s" % (yuss / ".writ" / "specs" / "archive"))

    excluded = deque(maxlen=rules.excluded_cap)
    tally = Counter()
    admitted = []

    def reject(cand: Candidate, reason: str, detail: str) -> None:
        tally[reason] += 1
        excluded.append({"story_path": cand.story_path, "reason": reason, "detail": clip(detail)})

    for cand in candidates:
        verdict = admit(git, cand, rules)
        if verdict.rejection:
            reject(cand, *verdict.rejection)
            continue
        key = SelectionSortKey(verdict.commit_time, cand.story_number, cand.story_path)
        admitted.append(Admitted(cand, verdict, key))

    assigned, displaced = assign_classes(admitted)
    for a in displaced:
        reject(a.cand, "class_filled", "eligible classes already filled: %s" % ",".join(a.verdict.eligible))

    short = [cls for cls in SURFACE_CLASSES if cls not in assigned]
    if short:
        total = sum(tally.values())
        breakdown = ", ".join("%s=%d" % (r, tally[r]) for r in REASONS if tally[r])
        for cls in short:
            print("select: no admissible story for class %s (%d candidates rejected: %s)"
                  % (cls, total, breakdown))
        sys.exit(1)

    head = (git.run("rev-parse", "HEAD") or "").strip()
    doc = {
        "schema": SCHEMA,
        "model": rules.model,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "yuss_head": head,
        "runs_per_story": None,
        "criteria": criteria_block(rules),
        "selection": [selection_entry(cls, assigned[cls]) for cls in SURFACE_CLASSES],
        "excluded": list(excluded),
        "rejection_tally": {r: tally[r] for r in REASONS if tally[r]},
        "runs": [],
    }
    assert tuple(doc) == SCHEMA_KEYS
    write_json(out, doc)
    print("select: wrote %s (4 stories, %d candidates rejected)" % (out, sum(tally.values())))
    sys.exit(0)


def cmd_stub(args: argparse.Namespace) -> None:
    owner = {"run": "Story 4", "ingest": "Story 4", "compare": "Story 5"}[args.command]
    print("%s: not implemented until %s" % (args.command, owner), file=sys.stderr)
    sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline-baseline.py",
        description="Select, replay, and compare yuss.app stories for the Writ pipeline baseline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sel = sub.add_parser("select", help="pick four Completed yuss stories by fixed criteria")
    sel.add_argument("--yuss", required=True, help="path to the read-only yuss.app checkout")
    sel.add_argument("--out", required=True,
                     help="baseline JSON to write, conventionally .writ/eval/baselines/<date>-<model>.json")
    sel.add_argument("--model", default=DEFAULT_MODEL, help="model ID recorded in the file (default: %(default)s)")
    sel.add_argument("--deny-list", default=",".join(DEFAULT_DENY_LIST),
                     help="comma-separated module substrings whose import marks a test as live (default: %(default)s)")
    sel.add_argument("--excluded-cap", type=int, default=DEFAULT_EXCLUDED_CAP,
                     help="how many of the most recent rejections to keep in excluded[] (default: %(default)s)")
    sel.add_argument("--live-test-scope", choices=LIVE_TEST_SCOPES, default="story",
                     help="story: one live test file rejects the story; "
                          "file: live files are dropped and the story is admitted if a clean file remains "
                          "(default: %(default)s)")
    sel.add_argument("--force", action="store_true", help="overwrite an existing --out")
    sel.set_defaults(func=cmd_select)

    for name in ("run", "ingest", "compare"):
        stub = sub.add_parser(name, help="not implemented until Story 4/5")
        stub.set_defaults(func=cmd_stub)
    return parser


def main(argv: Optional[list] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
