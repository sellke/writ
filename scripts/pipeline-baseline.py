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
  run      --baseline PATH --yuss PATH [--model ID] [--runs N] [--story ID]
           [--cap S] [--budget-usd N] [--keep] [--force] [--tmp-root DIR]
           [--writ-root DIR]
  ingest   --baseline PATH --yuss PATH --checkout DIR --transcript FILE
           [--story-id ID --run N] [--force] [--tmp-root DIR] [--writ-root DIR]
  validate FILE
  compare  A B

`run` (Story 4) replays each selected story `--runs` times: a fresh
`git init` + `fetch --depth 1 <yuss> <parent_sha>` checkout under
`$TMPDIR/writ-baseline-<story-stem>-<n>/checkout/` (Business Rule 1: exactly
one reachable commit, asserted and recorded before anything else touches the
tree), the current Writ overlaid via `scripts/install.sh --platform <driver>`,
`pnpm install`, then the selected headless driver (`claude` today; others
via `--driver` or `ingest` after an IDE session) under a wall-clock cap
and a dollar budget. Afterwards jest runs twice (the
produced tree's whole suite with coverage, then the story's original test
files restored from `git show <story_commit>:<path>`), Gates 2 and 4 are
re-derived by `--writ-root`'s `build-smoke.py` and `test-integrity.py`
(Business Rule 5), completion is re-derived from `/implement-story`'s own
success predicates, and the transcript's `result` event supplies tokens,
cost, and wall-clock. One record per run is appended to `runs[]` and flushed
before the next run starts; `ingest` computes the identical record from an
existing checkout + transcript. A run directory is removed only after its
record is complete; on any exception it is kept and its path printed.

Exit codes: 0 written · 1 (`select`) a surface class has no admissible story
(`--out` untouched); (`validate`) one or more schema/leak findings · 2 usage
or refusal (invalid `--yuss`, refused `--out`, no candidates, `run` preflight:
missing driver or `pnpm`, or a model with no headless driver; `compare`
selection mismatch) ·
3 (`run`/`ingest`) a record failed `scrub()` or yuss's HEAD moved.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
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


# ---------------------------------------------------------------------------
# run / ingest — record contract
# ---------------------------------------------------------------------------

# Key order of one `runs[]` record. Story 5's validator imports this.
RUN_KEYS = (
    "story_id", "run", "status", "reason", "started_at", "isolation", "writ", "inputs", "deps",
    "invocation", "wall_clock_s", "num_turns", "tokens", "tokens_main_thread", "cost_usd",
    "interrupts", "review_iterations", "tests", "gates", "rederivation", "exit_criteria", "yuss_head_unchanged",
)
# Numeric (or nested-numeric) fields `compare` medians. Exit-criteria is
# pass-count / run-count, not a median, and is handled beside this list.
COMPARE_METRICS = (
    "wall_clock_s", "num_turns",
    "tokens.input", "tokens.output", "tokens.cache_read", "tokens.cache_creation",
    "tokens_main_thread.input", "tokens_main_thread.output",
    "tokens_main_thread.cache_read", "tokens_main_thread.cache_creation",
    "interrupts.ask_user_question", "interrupts.status_blocked",
    "review_iterations", "cost_usd",
)
GATE_NAMES = (
    "gate0_arch", "gate0_5_boundary", "gate2_build", "gate2_5_surface",
    "gate3_review", "gate3_5_drift", "gate4_tests", "gate5_docs",
)
GATE_KEYS = ("verdict", "source", "rederived")      # gate4_tests also carries `integrity`
ISOLATION_KEYS = ("reachable_commits", "expected", "asserted", "answer_scrub_asserted")
WRIT_KEYS = ("source", "commit", "dirty", "checkout_manifest_version", "manifest_diff_count")
TEST_BLOCK_KEYS = ("passed", "total", "reason")
# Business Rule 5: Gate 2 and Gate 4 are re-derived by Writ's own scripts, run
# from `--writ-root` against the produced checkout. Each block is
# {argv, verdict, reason}; `gate2_build.rederived` and `gate4_tests.integrity`
# carry the verdicts. Argv paths are shown as <writ_root>/<checkout>/<artifacts>.
REDERIVATION_KEYS = (
    "build_smoke", "test_integrity",
    "arch_check", "review_override", "docs_check",
    "boundary_map", "change_surface", "drift_format",
)
BACKGROUND_DROP = "Background tasks still running after 600s"


def count_background_drops(text: str) -> int:
    """Count Claude Code print-mode 'Background tasks still running after 600s'."""
    if not text:
        return 0
    return text.count(BACKGROUND_DROP)
REDERIVATION_BLOCK_KEYS = ("argv", "verdict", "reason")
GATE_SCRIPT_VERDICTS = ("pass", "fail", "unverifiable")
BUILD_SMOKE_REL = "scripts/build-smoke.py"
TEST_INTEGRITY_REL = "scripts/test-integrity.py"
BUILD_SMOKE_TIMEOUT_S = 300           # the script's own --timeout
GATE_SCRIPT_TIMEOUT_S = 600           # our wrapper around either script
PATH_PLACEHOLDERS = ("<writ_root>", "<checkout>", "<artifacts>")
INVOCATION_KEYS = ("driver", "argv", "model", "model_resolved", "claude_version", "permission_mode", "api_key_source")
TOKEN_KEYS = ("input", "output", "cache_read", "cache_creation")
INTERRUPT_KEYS = ("ask_user_question", "status_blocked")
RUN_STATUSES = ("complete", "budget", "error", "timeout")
INPUT_SOURCES = ("parent", "parent_show")      # checkout tree · `git show <parent_sha>:<path>`
EXPECTED_REACHABLE = 1
REDERIVED_BY = "implement-story success predicates"

# stream-json event shape (`claude -p --output-format stream-json --verbose`).
# Pinned here so the task 4.2 smoke run confirms one place. Tokens and cost
# come from the `result` event: subagent spend is invisible on the main
# thread's per-message `usage`, which is kept only as `tokens_main_thread`.
RESULT_TYPE = "result"
RESULT_SUBTYPE_STATUS = {
    "success": "complete",
    "error_max_budget_usd": "budget", "error_max_budget": "budget",
    "error_during_execution": "error", "error_max_turns": "error",
}
RESULT_USAGE_FIELDS = {"input": "input_tokens", "output": "output_tokens",
                       "cache_read": "cache_read_input_tokens", "cache_creation": "cache_creation_input_tokens"}
RESULT_COST_FIELD = "total_cost_usd"
RESULT_DURATION_FIELD = "duration_ms"
RESULT_TURNS_FIELD = "num_turns"
INIT_FIELDS = {"model_resolved": "model", "api_key_source": "apiKeySource", "claude_version": "claude_code_version"}
SUBAGENT_TOOLS = frozenset({"Task", "Agent"})
INTERRUPT_TOOLS = frozenset({"AskUserQuestion", "ExitPlanMode"})
READ_TOOL = "Read"
# No `[` in the alternation: the agent templates read `ARCH_CHECK: [PROCEED/CAUTION/ABORT]`.
VERDICT_LINE = re.compile(
    r"\b(ARCH_CHECK|REVIEW_RESULT|TEST_RESULT|DOCS_UPDATED): "
    r"(PROCEED|CAUTION|ABORT|PASS|FAIL|PAUSE|YES|NO|BLOCKED)\b")
VERDICT_GATE = {"ARCH_CHECK": "gate0_arch", "REVIEW_RESULT": "gate3_review",
                "TEST_RESULT": "gate4_tests", "DOCS_UPDATED": "gate5_docs"}
STATUS_BLOCKED = re.compile(r"\bSTATUS: BLOCKED\b")
DEGRADED_REPORT = re.compile(r"\bDEGRADED\b")
COMPLETED_REPORT = re.compile(r"(?i)\bcomplete(d)?\b")
WWB_HEADING = re.compile(r"(?m)^## What Was Built\s*$")

# Headless invocation. `bypass`: Writ's gates run Bash, spawn subagents, and
# commit; a permission prompt in `-p` mode would hang the cap away.
PERMISSION_MODE = "bypass"
PERMISSION_FLAGS = ("--dangerously-skip-permissions", "--permission-prompts", "none",
                    "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence")
DEFAULT_CAP_S = 5400
DEFAULT_BUDGET_USD = 75.0
KILL_GRACE_S = 15
# `signal` is outside the 3.9 import set Story 3's StdlibOnlyTest pins, so the
# POSIX numbers are spelled out. `start_new_session=True` makes pgid == pid.
SIGTERM, SIGKILL = 15, 9
PNPM_INSTALL_HINT = "https://pnpm.io/installation"
# `claude` refuses to start inside another Claude Code session; a maintainer
# launching `run` from one must not pass that marker down.
NESTED_SESSION_VARS = frozenset({"CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"})
CLAUDE_INSTALL_HINT = "https://docs.anthropic.com/en/docs/claude-code/setup"
CODEX_INSTALL_HINT = "https://github.com/openai/codex"
CURSOR_INSTALL_HINT = "https://cursor.com/docs/cli/overview"


@dataclass(frozen=True)
class Driver:
    """A headless agent CLI that can execute `/implement-story`.

    This is not a model vendor. Claude Code, Codex, and a future Cursor
    agent CLI are drivers; Grok, local weights, and any other IDE-session
    model have no driver and are captured with `ingest`.
    """

    name: str
    binary: str
    platform: str
    hint: str
    nested_vars: frozenset
    model_prefixes: tuple
    implemented: bool


DRIVERS = {
    "claude": Driver("claude", "claude", "claude", CLAUDE_INSTALL_HINT,
                     NESTED_SESSION_VARS, ("claude-",), True),
    "codex": Driver("codex", "codex", "codex", CODEX_INSTALL_HINT,
                    frozenset(), ("gpt-", "o1-", "o1", "o3-", "o3", "o4-", "o4", "codex-"), False),
    "cursor": Driver("cursor", "cursor-agent", "cursor", CURSOR_INSTALL_HINT,
                     frozenset(), (), False),
}
DRIVER_NAMES = ("auto",) + tuple(DRIVERS)
# Prefixes that resolve to an IDE session, never a headless CLI we own.
INGEST_ONLY_PREFIXES = (
    "grok-", "llama", "qwen", "mistral", "gemma", "deepseek", "phi-", "olmo",
    "yi-", "glm-", "command-r",
)
INGEST_HINT = (
    "this model has no headless driver; run /implement-story in your CLI or IDE "
    "(Cursor, Claude Code, Codex, a local agent) and capture with "
    "pipeline-baseline.py ingest --checkout --transcript"
)


def _classify_model(model: str) -> Optional[str]:
    """Driver name, the ingest-only sentinel, or None if the id matches nothing."""
    lower = model.lower()
    if any(lower.startswith(p) for p in INGEST_ONLY_PREFIXES):
        return "ingest"
    for name, driver in DRIVERS.items():
        if any(lower.startswith(p) for p in driver.model_prefixes):
            return name
    return None


def resolve_driver(requested: str, model: Optional[str] = None) -> Driver:
    """Pick a driver. ``auto`` uses the model id; an explicit name wins."""
    if requested != "auto":
        if requested not in DRIVERS:
            raise Refusal("unknown driver %r (known: %s); %s"
                          % (requested, ", ".join(DRIVERS), INGEST_HINT))
        driver = DRIVERS[requested]
        if not driver.implemented:
            raise Refusal("%s driver is registered but has no headless argv yet; %s"
                          % (driver.name, INGEST_HINT))
        return driver
    if not model:
        implemented = [d for d in DRIVERS.values() if d.implemented]
        if not implemented:
            raise Refusal("no implemented headless driver is registered; %s" % INGEST_HINT)
        return implemented[0]
    kind = _classify_model(model)
    if kind == "ingest":
        raise Refusal("model %r: %s" % (model, INGEST_HINT))
    if kind is None:
        raise Refusal("no headless driver for model %r; pass --driver if a CLI can "
                      "run /implement-story, otherwise %s" % (model, INGEST_HINT))
    driver = DRIVERS[kind]
    if not driver.implemented:
        raise Refusal("model %r maps to the %s driver, which has no headless argv yet; %s"
                      % (model, driver.name, INGEST_HINT))
    return driver


def overlay_args(platform: str) -> tuple:
    return ("--platform", platform, "--no-commit", "--force")


TMP_PREFIX = "writ-baseline-"
SIDECAR = "run-meta.json"
PNPM_INSTALL = ("pnpm", "install", "--frozen-lockfile", "--prefer-offline")
DEPS_TIMEOUT_S = 900
# `--forceExit`: a hung handle must not outlive the run. Coverage goes to an
# out-of-tree directory so test-integrity can read it without the tree
# ever holding an artifact.
JEST_ARGV = ("pnpm", "exec", "jest", "--ci", "--json", "--forceExit")
JEST_TIMEOUT_S = 1200
COVERAGE_DIR = "coverage"
COVERAGE_REPORT = "coverage-final.json"     # jest's default `json` reporter
MANIFEST_REL = ".claude/.writ-manifest"
MANIFEST_VERSION = re.compile(r"(?m)^# version: (\S+)")


class Refusal(Exception):
    """`run`/`ingest` cannot start. Exit 2, nothing written."""


class RunError(Exception):
    """One run failed before the model ran. `reason` is a short code."""

    def __init__(self, reason: str, isolation: Optional[dict] = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.isolation = isolation


class ScrubError(Exception):
    """A record carries a string the baseline must never hold."""


# ---------------------------------------------------------------------------
# Small stdlib stand-ins (shutil/signal/time are outside the pinned import set)
# ---------------------------------------------------------------------------


def which(name: str, path: Optional[str] = None) -> Optional[str]:
    for directory in (os.environ.get("PATH", "") if path is None else path).split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def rmtree(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        if path.is_symlink() or path.exists():
            path.unlink()
        return
    for root, dirs, files in os.walk(str(path), topdown=False):
        for name in files:
            os.unlink(os.path.join(root, name))
        for name in dirs:
            full = os.path.join(root, name)
            if os.path.islink(full):
                os.unlink(full)
            else:
                os.rmdir(full)
    os.rmdir(str(path))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(when: datetime) -> str:
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _seconds(start: datetime) -> float:
    return round((_utcnow() - start).total_seconds(), 3)


def preflight(env: Optional[dict] = None, driver: str = "auto",
              model: Optional[str] = None) -> None:
    """Refuse before any filesystem or subprocess side effect (AC-4.1).

    Writ holds no vendor key. Auth is the operator's CLI or IDE login.
    Preflight requires `pnpm` (yuss's package manager) and a headless
    driver when the model has one. Grok, local weights, and other
    IDE-session models are not a missing-binary error — they are ingest.
    """
    env = os.environ if env is None else env
    path = env.get("PATH", "")
    if driver != "auto" or model:
        resolved = resolve_driver(driver, model)
        if which(resolved.binary, path) is None:
            raise Refusal("%s binary not found on PATH; install it first: %s"
                          % (resolved.binary, resolved.hint))
    else:
        implemented = [d for d in DRIVERS.values() if d.implemented]
        found = [d for d in implemented if which(d.binary, path)]
        if not found:
            names = ", ".join(d.binary for d in implemented)
            hints = "; ".join("%s → %s" % (d.binary, d.hint) for d in implemented)
            raise Refusal("no implemented headless driver on PATH (looked for: %s). "
                          "Writ does not hold vendor keys; your CLI or IDE authenticates. "
                          "Grok, local weights, and other IDE-session models use ingest. "
                          "Install a driver: %s" % (names, hints))
    if which("pnpm", path) is None:
        raise Refusal("pnpm not found on PATH (yuss's package manager); install it first: %s" % PNPM_INSTALL_HINT)


# ---------------------------------------------------------------------------
# Checkout: isolation, inputs, overlay, deps
# ---------------------------------------------------------------------------


def local_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """`git -C <checkout> ...` — the checkout is ours, any subcommand goes.
    Never pointed at `<yuss>`; that is `Git.run`'s read-only job."""
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                          encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        verb = next((a for a in args if not a.startswith("-")), args[0] if args else "")
        raise RunError("git_%s_failed" % verb)
    return proc


def build_checkout(yuss: Path, parent_sha: str, run_dir: Path) -> tuple:
    """Fresh `git init` + `fetch --depth 1 <yuss> <parent_sha>` + checkout, so
    exactly one commit is reachable (Business Rule 1). Returns
    (checkout, isolation). `<yuss>` is only ever the fetch source."""
    checkout = run_dir / "checkout"
    checkout.mkdir(parents=True, exist_ok=True)
    isolation = {"reachable_commits": None, "expected": EXPECTED_REACHABLE,
                 "asserted": False, "answer_scrub_asserted": False}
    local_git(checkout, "init", "-q")
    fetch = local_git(checkout, "fetch", "-q", "--depth", "1", str(yuss), parent_sha, check=False)
    if fetch.returncode != 0:
        raise RunError("fetch_failed", isolation)
    local_git(checkout, "checkout", "-q", "FETCH_HEAD")
    # A signing key configured globally would make the pipeline's own commit
    # prompt inside a headless run.
    local_git(checkout, "config", "commit.gpgsign", "false")
    fetch_head = checkout / ".git" / "FETCH_HEAD"       # the only file naming yuss's path
    if fetch_head.exists():
        fetch_head.unlink()
    remotes = (local_git(checkout, "remote", "-v").stdout or "").strip()
    count = (local_git(checkout, "rev-list", "--all", "--count").stdout or "").strip()
    isolation["reachable_commits"] = int(count) if count.isdigit() else None
    isolation["asserted"] = isolation["reachable_commits"] == EXPECTED_REACHABLE and remotes == ""
    assert tuple(isolation) == ISOLATION_KEYS
    return checkout, isolation


def story_rel_path(entry: dict) -> str:
    """The story's path inside an *active* spec folder at the parent SHA.
    `story_path` in `selection[]` is the archived path at yuss HEAD."""
    return ".writ/specs/%s/user-stories/%s.md" % (entry["spec_folder"], Path(entry["story_path"]).stem)


def _show_tree(git: Git, sha: str, rel: str, checkout: Path) -> bool:
    """Materialize `<sha>:<rel>/` from yuss into the checkout. False if absent."""
    listing = git.run("show", "%s:%s/" % (sha, rel), check=False)
    if listing is None:
        return False
    names = [l for l in listing.splitlines()[1:] if l.strip()]
    for name in names:
        if name.endswith("/"):
            if not _show_tree(git, sha, "%s/%s" % (rel, name[:-1]), checkout):
                return False
            continue
        content = git.run("show", "%s:%s/%s" % (sha, rel, name), check=False)
        if content is None:
            return False
        target = checkout / rel / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return True


def stage_inputs(git: Git, checkout: Path, entry: dict) -> str:
    """The spec folder must be the one the parent commit had — never yuss
    HEAD, where the story is already Completed. Returns the `inputs` source."""
    base = ".writ/specs/%s" % entry["spec_folder"]
    parent = entry["parent_sha"]
    source = "parent"
    for rel in ("%s/spec.md" % base, "%s/spec-lite.md" % base, story_rel_path(entry)):
        if (checkout / rel).is_file():
            continue
        content = git.run("show", "%s:%s" % (parent, rel), check=False)
        if content is None:
            raise RunError("inputs_missing")
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(content, encoding="utf-8")
        source = "parent_show"
    if not (checkout / base / "sub-specs").is_dir():
        if not _show_tree(git, parent, "%s/sub-specs" % base, checkout):
            raise RunError("inputs_missing")
        source = "parent_show"
    return source


def assert_answer_scrubbed(checkout: Path, story_rel: str) -> None:
    """The staged story must not carry its own answer."""
    text = (checkout / story_rel).read_text(encoding="utf-8", errors="replace")
    status = STATUS_LINE.search(text)
    if WWB_HEADING.search(text) or COMMIT_LINE.search(text) or (status and is_completed(status.group(1))):
        raise RunError("answer_leak")


def _parse_manifest(text: str) -> tuple:
    version = MANIFEST_VERSION.search(text)
    entries = {}
    for line in text.splitlines():
        if line.startswith("#") or "  " not in line:
            continue
        digest, rel = line.split("  ", 1)
        entries[rel.strip()] = digest.strip()
    return (version.group(1) if version else None), entries


def overlay_writ(checkout: Path, writ_root: Path, log: Path, platform: str = "claude") -> dict:
    """Install the current repo's Writ into the checkout (`install.sh` run
    from `scripts/` uses the local repo as source). Records what it replaced."""
    manifest = checkout / MANIFEST_REL
    before_version, before = _parse_manifest(manifest.read_text(encoding="utf-8", errors="replace")) \
        if manifest.is_file() else (None, {})
    commit = (local_git(writ_root, "rev-parse", "HEAD").stdout or "").strip()
    # install.sh copies the working tree, so `commit` alone under-describes a
    # dirty repo.
    dirty = bool((local_git(writ_root, "status", "--porcelain").stdout or "").strip())
    proc = subprocess.run(["bash", str(writ_root / "scripts" / "install.sh"), *overlay_args(platform)],
                          cwd=str(checkout), capture_output=True, encoding="utf-8", errors="replace")
    log.write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
    if proc.returncode != 0:
        raise RunError("overlay_failed")
    _, after = _parse_manifest(manifest.read_text(encoding="utf-8", errors="replace")) \
        if manifest.is_file() else (None, {})
    diff = sum(1 for rel in set(before) | set(after) if before.get(rel) != after.get(rel))
    block = {"source": "overlay", "commit": commit, "dirty": dirty, "checkout_manifest_version": before_version,
             "manifest_diff_count": diff}
    assert tuple(block) == WRIT_KEYS
    return block


def install_deps(checkout: Path, log: Path) -> dict:
    start = _utcnow()
    try:
        proc = subprocess.run(list(PNPM_INSTALL), cwd=str(checkout), capture_output=True,
                              encoding="utf-8", errors="replace", timeout=DEPS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        log.write_text("pnpm install timed out after %ds\n" % DEPS_TIMEOUT_S, encoding="utf-8")
        return {"seconds": _seconds(start), "exit": "timeout"}
    log.write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
    return {"seconds": _seconds(start), "exit": proc.returncode}


# ---------------------------------------------------------------------------
# Headless invocation
# ---------------------------------------------------------------------------


def claude_argv(story_rel: str, model: str, budget_usd: float) -> list:
    return ["claude", "-p", "/implement-story %s" % story_rel, "--output-format", "stream-json", "--verbose",
            "--model", model, "--max-budget-usd", "%g" % budget_usd, *PERMISSION_FLAGS]


def driver_argv(driver: Driver, story_rel: str, model: str, budget_usd: float) -> list:
    if driver.name == "claude":
        return claude_argv(story_rel, model, budget_usd)
    raise Refusal("%s driver has no headless argv yet; %s" % (driver.name, INGEST_HINT))


def _kill_group(proc: "subprocess.Popen") -> None:
    """SIGTERM the process group, wait `KILL_GRACE_S`, then SIGKILL it — the
    SIGKILL always goes out because processes the agent spawned (a test run,
    a dev server) share the group and may outlive `claude` itself. Every step
    is best-effort: nothing here may raise past the caller."""
    for sig in (SIGTERM, SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            pass


def invoke_headless(argv: list, checkout: Path, transcript: Path, stderr_log: Path, cap_s: int,
                    nested_vars: Optional[frozenset] = None) -> tuple:
    """Stream stdout to `transcript` (never `capture_output` on a 90-minute
    run). Returns (timed_out, elapsed_s). On the cap the group is killed and
    the run is recorded as a timeout. `start_new_session=True` also detaches
    the group from the terminal, so a Ctrl-C reaches only this process: any
    other exception kills the group too, then propagates."""
    start = _utcnow()
    timed_out = False
    strip = NESTED_SESSION_VARS if nested_vars is None else nested_vars
    env = {k: v for k, v in os.environ.items() if k not in strip}
    with open(str(transcript), "wb") as out, open(str(stderr_log), "wb") as err:
        proc = subprocess.Popen(argv, cwd=str(checkout), stdout=out, stderr=err, env=env, start_new_session=True)
        try:
            proc.wait(timeout=cap_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(proc)
        except BaseException:
            _kill_group(proc)
            raise
    return timed_out, _seconds(start)


# ---------------------------------------------------------------------------
# Post-processing: tests, transcript, completion
# ---------------------------------------------------------------------------


def _jest_counts(report: Path) -> tuple:
    """(passed, total, success, failed_suites) from a jest `--json` report;
    `success` is None when the report is not JSON. A suite that fails to
    load reports `numTotalTests: 0` with `success: false` and a non-zero
    `numFailedTestSuites` — that is a failed run, not an empty one."""
    try:
        doc = json.loads(report.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise TypeError("jest report is not an object")
        success = doc.get("success")
        return (int(doc.get("numPassedTests", 0)), int(doc.get("numTotalTests", 0)),
                bool(success) if isinstance(success, bool) else None, int(doc.get("numFailedTestSuites", 0) or 0))
    except (OSError, ValueError, TypeError):
        return 0, 0, None, 0


def run_jest(checkout: Path, report: Path, paths: Optional[list] = None,
             coverage_dir: Optional[Path] = None) -> dict:
    """`pnpm exec jest --ci --json --outputFile=<report>` in the checkout; the
    report (and coverage, when asked for) live outside the tree. A compile
    failure is a failed test run, not an error: passed stays below total, or
    — when no test ever ran — `reason` names the failed suites so the gate
    still reads `fail`. A hang past `JEST_TIMEOUT_S` is 0/0 with a reason,
    not an exception."""
    if report.exists():
        report.unlink()
    argv = [*JEST_ARGV, "--outputFile=%s" % report]
    if coverage_dir is not None:
        argv += ["--coverage", "--coverageDirectory=%s" % coverage_dir]
    if paths:
        argv += ["--runTestsByPath", *paths]
    try:
        subprocess.run(argv, cwd=str(checkout), capture_output=True, encoding="utf-8", errors="replace",
                       timeout=JEST_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"passed": 0, "total": 0, "reason": "timeout after %ds" % JEST_TIMEOUT_S}
    if not report.is_file():
        return {"passed": 0, "total": 0, "reason": "no jest report"}
    passed, total, success, failed_suites = _jest_counts(report)
    if success is None:
        return {"passed": 0, "total": 0, "reason": "unreadable jest report"}
    if success is False and total == 0:
        return {"passed": 0, "total": 0, "reason": "suite failed to run (%d failed suites)" % failed_suites}
    return {"passed": passed, "total": total, "reason": None}


SUITE_FAILED_TO_RUN = re.compile(r"^suite failed to run \(")


def _suite_verdict(suite: dict) -> Optional[str]:
    """`gate4_tests.rederived` from the mechanical suite run: pass/fail when
    tests ran, fail when the suite could not even load, otherwise None."""
    if suite["total"]:
        return "pass" if suite["passed"] == suite["total"] else "fail"
    if SUITE_FAILED_TO_RUN.match(suite.get("reason") or ""):
        return "fail"
    return None


def _redact_paths(argv: list, names: dict) -> list:
    """Show machine-specific prefixes as placeholders; longest prefix wins so
    `<checkout>` (under the run dir) is not swallowed by `<artifacts>`."""
    shown = []
    for arg in argv:
        for prefix in sorted(names, key=len, reverse=True):
            if prefix in arg:
                arg = arg.replace(prefix, names[prefix])
        shown.append(arg)
    return shown


def run_gate_script(script: Path, argv_tail: list, checkout: Path, names: dict) -> dict:
    """Run one of Writ's quality-gate scripts (`build-smoke.py`,
    `test-integrity.py`) against the checkout and reduce it to
    {argv, verdict, reason}. Non-zero exit without a parseable verdict, a
    timeout, or a missing interpreter are `unverifiable` with a short reason —
    never an exception (Business Rule 5's re-derivation must not sink a paid
    run)."""
    argv = ["python3", str(script), *argv_tail]
    shown = _redact_paths(argv, names)
    try:
        proc = subprocess.run(argv, cwd=str(checkout), capture_output=True, encoding="utf-8", errors="replace",
                              timeout=GATE_SCRIPT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"argv": shown, "verdict": "unverifiable", "reason": "timeout after %ds" % GATE_SCRIPT_TIMEOUT_S}
    except OSError as exc:
        return {"argv": shown, "verdict": "unverifiable", "reason": "could not start: %s" % type(exc).__name__}
    try:
        doc = json.loads(proc.stdout or "")
    except ValueError:
        doc = None
    verdict = doc.get("verdict") if isinstance(doc, dict) else None
    if verdict not in GATE_SCRIPT_VERDICTS:
        return {"argv": shown, "verdict": "unverifiable",
                "reason": "exit %s, no verdict in output" % proc.returncode}
    reason = None
    if verdict == "unverifiable":
        causes = doc.get("unverifiable") if isinstance(doc.get("unverifiable"), list) else []
        codes = sorted({str(c.get("reason") or c.get("code")) for c in causes if isinstance(c, dict)
                        if c.get("reason") or c.get("code")})
        reason = (", ".join(codes) or "exit %s" % proc.returncode)[:DETAIL_MAX_CHARS]
    return {"argv": shown, "verdict": verdict, "reason": reason}


def rederive_gates(writ_root: Path, checkout: Path, artifacts: Path) -> dict:
    """Gate 2 (build smoke) and Gate 4 (coverage integrity) re-derived by the
    scripts `/implement-story` itself relies on, with cwd = the checkout."""
    names = {str(writ_root): "<writ_root>", str(checkout): "<checkout>", str(artifacts): "<artifacts>"}
    report = artifacts / COVERAGE_DIR / COVERAGE_REPORT
    block = {
        "build_smoke": run_gate_script(
            writ_root / BUILD_SMOKE_REL,
            ["check", "--project", str(checkout), "--timeout", str(BUILD_SMOKE_TIMEOUT_S)], checkout, names),
        "test_integrity": run_gate_script(
            writ_root / TEST_INTEGRITY_REL,
            ["coverage", "--project", str(checkout), "--report", str(report)], checkout, names),
    }
    for key in REDERIVATION_KEYS:
        block.setdefault(key, {"argv": None, "verdict": None, "reason": None})
    return block


def restore_original_tests(git: Git, checkout: Path, entry: dict) -> list:
    """Write the story's original test files (at `story_commit`) into the
    produced tree. Runs only after the agent has exited."""
    written = []
    for rel in entry["test_files"]:
        content = git.run("show", "%s:%s" % (entry["story_commit"], rel), check=False)
        if content is None:
            continue
        target = checkout / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel)
    return written


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _parse_timestamp(raw) -> Optional[datetime]:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_transcript(path: Path) -> dict:
    """Metrics from a `claude -p --output-format stream-json` transcript, or
    from a `~/.claude/projects/*.jsonl` session file (no `result` event:
    usage is summed and wall-clock comes from the first/last `timestamp`).

    Verdicts are read from `tool_result` blocks whose `tool_use_id` maps to a
    `Task`/`Agent` call (the gate agents' own output), then from assistant
    text as a fallback; the last occurrence wins. `Read` results of `*.md`
    files are skipped for `STATUS: BLOCKED`, which would otherwise count the
    command templates the agent reads."""
    tool_names, tool_inputs = {}, {}
    verdicts = {g: {"tool_result": None, "assistant_text": None} for g in VERDICT_GATE.values()}
    interrupts = {"ask_user_question": 0, "status_blocked": 0}
    # Counted per source so an orchestrator echoing the review agent's
    # `REVIEW_RESULT: FAIL` in its own text does not double the iteration count.
    review_fails = {"tool_result": 0, "assistant_text": 0}
    main = {k: 0 for k in TOKEN_KEYS}
    init, result = {}, None
    first_ts = last_ts = None
    assistant_turns = 0
    last_text = ""

    def note_verdicts(text: str, source: str) -> None:
        for m in VERDICT_LINE.finditer(text):
            verdicts[VERDICT_GATE[m.group(1)]][source] = m.group(2)
            if m.group(1) == "REVIEW_RESULT" and m.group(2) == "FAIL":
                review_fails[source] += 1

    with open(str(path), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            # With --verbose, subagent turns are echoed as assistant/user
            # events carrying `parent_tool_use_id`. Their usage, text and tool
            # calls belong to the subagent; the main thread sees each
            # subagent's outcome once, in the Task tool_result.
            if event.get("parent_tool_use_id"):
                continue
            kind = event.get("type")
            ts = _parse_timestamp(event.get("timestamp"))
            if ts is not None:
                first_ts = first_ts or ts
                last_ts = ts
            if kind == "system" and event.get("subtype") == "init":
                init = {k: event.get(field) for k, field in INIT_FIELDS.items()}
                continue
            if kind == RESULT_TYPE:
                result = event
                continue
            message = event.get("message") if isinstance(event.get("message"), dict) else {}
            content = message.get("content")
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
            if kind == "assistant":
                assistant_turns += 1
                usage = message.get("usage") or {}
                for k, field in RESULT_USAGE_FIELDS.items():
                    main[k] += int(usage.get(field) or 0)
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        tool_names[block.get("id")] = block.get("name")
                        tool_inputs[block.get("id")] = block.get("input") or {}
                        if block.get("name") in INTERRUPT_TOOLS:
                            interrupts["ask_user_question"] += 1
                    elif block.get("type") == "text":
                        text = block.get("text") or ""
                        if text.strip():
                            last_text = text
                        note_verdicts(text, "assistant_text")
                        interrupts["status_blocked"] += len(STATUS_BLOCKED.findall(text))
            elif kind == "user":
                for block in blocks:
                    if not isinstance(block, dict) or block.get("type") != "tool_result":
                        continue
                    name = tool_names.get(block.get("tool_use_id"))
                    text = _text_of(block.get("content"))
                    if name == READ_TOOL and str(tool_inputs.get(block.get("tool_use_id"), {})
                                                 .get("file_path", "")).endswith(".md"):
                        continue
                    if name in SUBAGENT_TOOLS:
                        note_verdicts(text, "tool_result")
                    interrupts["status_blocked"] += len(STATUS_BLOCKED.findall(text))

    gates = {}
    for g in GATE_NAMES:
        found = verdicts.get(g, {})
        if found.get("tool_result"):
            gates[g] = {"verdict": found["tool_result"], "source": "tool_result"}
        elif found.get("assistant_text"):
            gates[g] = {"verdict": found["assistant_text"], "source": "assistant_text"}
        else:
            gates[g] = {"verdict": None, "source": None}
    review_source = gates["gate3_review"]["source"] or "tool_result"
    review_iterations = review_fails[review_source]

    # A `-p` stream opens with `system/init` and closes with `result`; a
    # session file has neither but stamps every line with `timestamp`.
    if result is not None or init or first_ts is None:
        mode = "stream"
    else:
        mode = "session"
    if result is not None:
        usage = result.get("usage") or {}
        tokens = {k: usage.get(field) for k, field in RESULT_USAGE_FIELDS.items()}
        subtype = str(result.get("subtype") or "")
        status = RESULT_SUBTYPE_STATUS.get(subtype, "error")
        reason = None if status == "complete" else (subtype or "unknown_subtype")
        duration = result.get(RESULT_DURATION_FIELD)
        wall = round(duration / 1000.0, 3) if isinstance(duration, (int, float)) else None
        turns = result.get(RESULT_TURNS_FIELD)
        cost = result.get(RESULT_COST_FIELD)
        final = _text_of(result.get("result")) or last_text
    elif mode == "session":
        tokens = dict(main)
        status, reason = "complete", None
        wall = round((last_ts - first_ts).total_seconds(), 3) if first_ts and last_ts else None
        turns, cost, final = assistant_turns, None, last_text
    else:
        tokens = {k: None for k in TOKEN_KEYS}
        status, reason, wall, turns, cost, final = "error", "no_result_event", None, None, None, last_text

    if DEGRADED_REPORT.search(final or ""):
        exit_reported = "DEGRADED"
    elif COMPLETED_REPORT.search(final or ""):
        exit_reported = "COMPLETE"
    else:
        exit_reported = None
    return {
        "mode": mode, "status": status, "reason": reason,
        "init": init or {k: None for k in INIT_FIELDS},
        "tokens": tokens, "tokens_main_thread": main, "cost_usd": cost, "wall_clock_s": wall,
        "num_turns": turns, "interrupts": interrupts, "review_iterations": review_iterations,
        "gates": gates, "exit_reported": exit_reported,
    }


def rederive_completion(checkout: Path, story_rel: str) -> str:
    """`/implement-story` succeeds when the story reads Completed, carries the
    completion commit SHA in its header, ends with `## What Was Built`, and
    that commit exists in the checkout. `exit-criteria.py` has no
    implement-story mode, so the predicates are re-applied here."""
    story = checkout / story_rel
    if not story.is_file():
        return "unmet"
    text = story.read_text(encoding="utf-8", errors="replace")
    status = STATUS_LINE.search(text)
    header = COMMIT_LINE.search(text)
    sha = commit_from_header(header.group(1)) if header else None
    if not (status and is_completed(status.group(1)) and sha and WWB_HEADING.search(text)):
        return "unmet"
    exists = local_git(checkout, "cat-file", "-e", sha + "^{commit}", check=False)
    return "met" if exists.returncode == 0 else "unmet"


# ---------------------------------------------------------------------------
# Record assembly
# ---------------------------------------------------------------------------


def _null_record(story_id: str, run: int, started_at: str) -> dict:
    return {
        "story_id": story_id, "run": run, "status": "error", "reason": None, "started_at": started_at,
        "isolation": {"reachable_commits": None, "expected": EXPECTED_REACHABLE,
                      "asserted": False, "answer_scrub_asserted": False},
        "writ": None, "inputs": None, "deps": None,
        "invocation": {k: None for k in INVOCATION_KEYS},
        "wall_clock_s": None, "num_turns": None,
        "tokens": {k: None for k in TOKEN_KEYS}, "tokens_main_thread": {k: None for k in TOKEN_KEYS},
        "cost_usd": None, "interrupts": {k: None for k in INTERRUPT_KEYS}, "review_iterations": None,
        "tests": {"suite": {"passed": None, "total": None, "reason": None},
                  "original": {"passed": None, "total": None, "reason": None, "files": []}},
        "gates": {g: {"verdict": None, "source": None, "rederived": None} for g in GATE_NAMES},
        "rederivation": {k: {"argv": None, "verdict": None, "reason": None} for k in REDERIVATION_KEYS},
        "exit_criteria": {"reported": None, "rederived": None, "rederived_by": REDERIVED_BY},
        "yuss_head_unchanged": None,
    }


def assemble_record(meta: dict, transcript: Optional[dict], tests: Optional[dict], rederived: Optional[str],
                    gates_rederived: Optional[dict] = None) -> dict:
    """One `runs[]` entry in `RUN_KEYS` order. `meta` is the sidecar; the
    others are None for a run that never reached the model."""
    rec = _null_record(meta["story_id"], meta["run"], meta["started_at"])
    rec["gates"]["gate4_tests"]["integrity"] = None
    rec["isolation"] = dict(meta.get("isolation") or rec["isolation"])
    rec["writ"] = meta.get("writ")
    rec["inputs"] = meta.get("inputs")
    rec["deps"] = meta.get("deps")
    rec["yuss_head_unchanged"] = meta.get("yuss_head_unchanged")
    rec["reason"] = meta.get("reason")
    inv = meta.get("invocation") or {}
    rec["invocation"].update({k: inv.get(k) for k in ("driver", "argv", "model", "permission_mode") if k in inv})
    if transcript is not None:
        rec["invocation"].update(transcript["init"])
        rec["status"] = "timeout" if meta.get("timed_out") else transcript["status"]
        if not meta.get("timed_out"):
            # The transcript's own stop reason (`error_max_budget_usd`, ...)
            # explains a non-complete status; the sidecar's provenance note
            # only fills in when the transcript has nothing to say —
            # `isolation.asserted: false` already marks a sidecar-less ingest.
            if transcript["status"] != "complete" and transcript["reason"]:
                rec["reason"] = transcript["reason"]
            else:
                rec["reason"] = meta.get("reason") or transcript["reason"]
        rec["wall_clock_s"] = transcript["wall_clock_s"]
        if rec["wall_clock_s"] is None and meta.get("elapsed_s") is not None:
            rec["wall_clock_s"] = float(meta["elapsed_s"])
        rec["num_turns"] = transcript["num_turns"]
        rec["tokens"] = dict(transcript["tokens"])
        rec["tokens_main_thread"] = dict(transcript["tokens_main_thread"])
        rec["cost_usd"] = transcript["cost_usd"]
        rec["interrupts"] = dict(transcript["interrupts"])
        rec["review_iterations"] = transcript["review_iterations"]
        for g in GATE_NAMES:
            rec["gates"][g].update(transcript["gates"][g])
        rec["exit_criteria"]["reported"] = transcript["exit_reported"]
    if tests is not None:
        rec["tests"] = tests
        rec["gates"]["gate4_tests"]["rederived"] = _suite_verdict(tests["suite"])
    if gates_rederived is not None:
        rec["rederivation"] = {}
        for k in REDERIVATION_KEYS:
            src = gates_rederived.get(k) or {}
            rec["rederivation"][k] = {f: src.get(f) for f in REDERIVATION_BLOCK_KEYS}
        if "build_smoke" in gates_rederived:
            rec["gates"]["gate2_build"]["rederived"] = gates_rederived["build_smoke"].get("verdict")
        if "test_integrity" in gates_rederived:
            rec["gates"]["gate4_tests"]["integrity"] = gates_rederived["test_integrity"].get("verdict")
    if rederived is not None:
        rec["exit_criteria"]["rederived"] = rederived
    rec["background_tasks_outstanding"] = int(meta.get("background_tasks_outstanding") or 0)
    assert tuple(list(rec)[:len(RUN_KEYS)]) == RUN_KEYS
    return rec


CODE_LINE_STARTS = ("import ", "def ", "function ")
TURN_MARKERS = ("Human:", "Assistant:")
FILENAME_MODEL = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)\.json$")


def _string_leaks(value: str, path: str) -> list:
    """Leak heuristics shared with `scrub` plus Story 5's source/transcript
    patterns. Walks each string on its own — never join a list (argv)."""
    hits = []
    if "sk-ant-" in value:
        hits.append((path, "looks like key material (sk-ant-)"))
    if len(value) > DETAIL_MAX_CHARS:
        hits.append((path, "is %d characters (max %d)" % (len(value), DETAIL_MAX_CHARS)))
    if "\n" in value:
        hits.append((path, "contains a newline"))
    for line in value.splitlines() or [value]:
        if line.startswith(CODE_LINE_STARTS):
            hits.append((path, "looks like source code"))
            break
    if any(m in value for m in TURN_MARKERS):
        hits.append((path, "looks like a transcript turn marker"))
    return hits


def _walk_leaks(value, path: str) -> list:
    hits = []
    if isinstance(value, dict):
        for k, v in value.items():
            hits.extend(_walk_leaks(v, "%s.%s" % (path, k)))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            hits.extend(_walk_leaks(v, "%s[%d]" % (path, i)))
    elif isinstance(value, str):
        hits.extend(_string_leaks(value, path))
    return hits


def scrub(record: dict) -> None:
    """Business Rule 3 and Story 5's validator, enforced before the write:
    no key material, no string over `DETAIL_MAX_CHARS`, no newline anywhere."""
    hits = _walk_leaks(record, "$")
    if hits:
        raise ScrubError("%s %s" % (hits[0][0], hits[0][1]))


def model_from_filename(name: str) -> Optional[str]:
    match = FILENAME_MODEL.match(name)
    return match.group(1) if match else None


def validate_doc(doc, filename: str) -> list:
    """Return `(json_path, reason)` pairs. `selection` must be a list of 4
    objects — a `{stories: []}` wrapper is a violation on `selection`."""
    findings = []
    if not isinstance(doc, dict):
        return [("$", "not a JSON object")]
    schema = doc.get("schema")
    if schema is None:
        findings.append(("$.schema", "missing"))
    elif schema != SCHEMA:
        findings.append(("$.schema", "expected %s" % SCHEMA))
    if "model" not in doc:
        findings.append(("$.model", "missing"))
    else:
        segment = model_from_filename(filename)
        if segment is None:
            findings.append(("$.model", "filename is not <YYYY-MM-DD>-<model-id>.json"))
        elif doc.get("model") != segment:
            findings.append(("$.model", "does not match filename segment %r" % segment))
    if "criteria" not in doc or doc.get("criteria") in (None, ""):
        findings.append(("$.criteria", "missing"))
    sel = doc.get("selection")
    if not isinstance(sel, list) or len(sel) != 4:
        findings.append(("$.selection", "expected a list of 4 objects"))
    elif SELECTION_KEYS and any(not isinstance(e, dict) for e in sel):
        findings.append(("$.selection", "expected a list of 4 objects"))
    rps = doc.get("runs_per_story")
    if not isinstance(rps, int) or isinstance(rps, bool) or rps < 1:
        findings.append(("$.runs_per_story", "must be a positive int"))
        rps = None
    runs = doc.get("runs")
    if not isinstance(runs, list):
        findings.append(("$.runs", "expected a list"))
        runs = None
    elif rps is not None:
        expected = rps * 4
        if len(runs) != expected:
            findings.append(("$.runs", "expected %d records (runs_per_story * 4), got %d"
                             % (expected, len(runs))))
    if isinstance(runs, list):
        for i, rec in enumerate(runs):
            base = "$.runs[%d]" % i
            if not isinstance(rec, dict):
                findings.append((base, "expected an object"))
                continue
            for key in RUN_KEYS:
                if key not in rec:
                    findings.append(("%s.%s" % (base, key), "missing"))
    findings.extend(_walk_leaks(doc, "$"))
    return findings


def cmd_validate(args: argparse.Namespace) -> None:
    path = Path(args.file).expanduser()
    if not path.is_file():
        print("validate: error: %s does not exist" % path, file=sys.stderr)
        sys.exit(2)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        print("$: not valid JSON")
        sys.exit(1)
    findings = validate_doc(doc, path.name)
    if findings:
        for field, reason in findings:
            print("%s: %s" % (field, reason))
        sys.exit(1)
    sys.exit(0)


def _lookup(rec: dict, dotted: str):
    cur = rec
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _median(values: list):
    nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if not nums:
        return None
    return statistics.median(nums)


def _fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return "%g" % value
    if isinstance(value, tuple) and len(value) == 2:
        return "%d/%d" % value
    return str(value)


def _story_pairs(doc: dict) -> list:
    sel = doc.get("selection")
    if not isinstance(sel, list):
        return []
    pairs = []
    for entry in sel:
        if not isinstance(entry, dict):
            pairs.append((None, None, None))
            continue
        pairs.append((entry.get("story_path"), entry.get("parent_sha"), entry.get("story_id")))
    return pairs


def _runs_for(doc: dict, story_id) -> list:
    runs = doc.get("runs")
    if not isinstance(runs, list):
        return []
    return [r for r in runs if isinstance(r, dict) and r.get("story_id") == story_id]


def cmd_compare(args: argparse.Namespace) -> None:
    a_path = Path(args.a).expanduser()
    b_path = Path(args.b).expanduser()
    for label, path in (("a", a_path), ("b", b_path)):
        if not path.is_file():
            print("compare: error: %s does not exist" % path, file=sys.stderr)
            sys.exit(2)
    try:
        a_doc = json.loads(a_path.read_text(encoding="utf-8"))
        b_doc = json.loads(b_path.read_text(encoding="utf-8"))
    except ValueError:
        print("compare: error: a baseline file is not valid JSON", file=sys.stderr)
        sys.exit(2)
    if not isinstance(a_doc, dict) or not isinstance(b_doc, dict):
        print("compare: error: a baseline file is not a JSON object", file=sys.stderr)
        sys.exit(2)
    a_pairs, b_pairs = _story_pairs(a_doc), _story_pairs(b_doc)
    limit = max(len(a_pairs), len(b_pairs))
    for i in range(limit):
        aa = a_pairs[i] if i < len(a_pairs) else (None, None, None)
        bb = b_pairs[i] if i < len(b_pairs) else (None, None, None)
        if aa[0] != bb[0] or aa[1] != bb[1]:
            name = aa[0] or bb[0] or aa[2] or bb[2] or "story %d" % (i + 1)
            print("compare: selection mismatch: first differing story is %s" % name)
            sys.exit(2)
    a_runs = a_doc.get("runs") if isinstance(a_doc.get("runs"), list) else []
    b_runs = b_doc.get("runs") if isinstance(b_doc.get("runs"), list) else []
    if not a_runs and not b_runs:
        print("nothing to compare")
        sys.exit(0)
    rows = [("story", "metric", "a", "b", "delta")]
    for path, parent, story_id in a_pairs:
        ar, br = _runs_for(a_doc, story_id), _runs_for(b_doc, story_id)
        for metric in COMPARE_METRICS:
            av = _median([_lookup(r, metric) for r in ar])
            bv = _median([_lookup(r, metric) for r in br])
            delta = None if av is None or bv is None else bv - av
            rows.append((story_id or path or "", metric, _fmt(av), _fmt(bv), _fmt(delta)))
        a_met = sum(1 for r in ar if (_lookup(r, "exit_criteria.rederived") == "met"))
        b_met = sum(1 for r in br if (_lookup(r, "exit_criteria.rederived") == "met"))
        rows.append((story_id or path or "", "exit_criteria",
                     "%d/%d" % (a_met, len(ar)), "%d/%d" % (b_met, len(br)),
                     _fmt(b_met - a_met)))
    widths = [max(len(row[c]) for row in rows) for c in range(5)]
    for row in rows:
        print("  ".join(row[c].ljust(widths[c]) for c in range(5)))
    sys.exit(0)


def postprocess(git: Git, checkout: Path, transcript_path: Path, entry: dict, meta: dict, artifacts: Path,
                writ_root: Path) -> dict:
    """Everything after the agent exits — shared by `run` and `ingest` so the
    two produce identical records (AC-4.5)."""
    transcript = parse_transcript(transcript_path)
    suite = run_jest(checkout, artifacts / "jest-suite.json", coverage_dir=artifacts / COVERAGE_DIR)
    gates_rederived = rederive_gates(writ_root, checkout, artifacts)
    files = restore_original_tests(git, checkout, entry)
    original = run_jest(checkout, artifacts / "jest-original.json", files) if files \
        else {"passed": 0, "total": 0, "reason": None}
    tests = {"suite": suite, "original": {"passed": original["passed"], "total": original["total"],
                                          "reason": original["reason"], "files": files}}
    rederived = rederive_completion(checkout, story_rel_path(entry))
    return assemble_record(meta, transcript, tests, rederived, gates_rederived)


# ---------------------------------------------------------------------------
# run / ingest commands
# ---------------------------------------------------------------------------


def _refuse(command: str, message: str, code: int = 2) -> None:
    print("%s: error: %s" % (command, message), file=sys.stderr)
    sys.exit(code)


def load_baseline(command: str, path: Path, yuss: Path) -> dict:
    if not path.is_file():
        _refuse(command, "--baseline %s does not exist; run select first" % path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        _refuse(command, "--baseline %s is not valid JSON" % path)
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or tuple(doc) != SCHEMA_KEYS:
        _refuse(command, "--baseline %s is not a %s file" % (path, SCHEMA))
    if not doc["selection"]:
        _refuse(command, "--baseline %s has an empty selection; run select first" % path)
    if not yuss.is_dir():
        _refuse(command, "--yuss %s is not a directory" % yuss)
    git = Git(yuss)
    top = git.run("rev-parse", "--show-toplevel", check=False)
    if not top or Path(top.strip()).resolve() != yuss:
        _refuse(command, "--yuss %s is not a git repository" % yuss)
    return doc


def _present_pairs(doc: dict) -> set:
    return {(r.get("story_id"), r.get("run")) for r in doc["runs"] if isinstance(r, dict)}


def _select_entries(command: str, doc: dict, story: Optional[str]) -> list:
    entries = doc["selection"]
    if story:
        entries = [e for e in entries if story in (e["story_id"], Path(e["story_path"]).stem)]
        if not entries:
            _refuse(command, "--story %s matches no selected story" % story)
    return entries


def _write_sidecar(run_dir: Path, meta: dict) -> None:
    write_json(run_dir / SIDECAR, meta)


def _progress(command: str, rec: dict) -> str:
    tokens = rec["tokens"]
    tests = rec["tests"]["suite"]
    interrupts = sum(v or 0 for v in rec["interrupts"].values())

    def n(v):
        return "?" if v is None else v

    return ("%s: %s run %d: %s%s exit=%s tests=%s/%s tokens=%s/%s/%s wall=%ss interrupts=%d" % (
        command, rec["story_id"], rec["run"], rec["status"],
        " (%s)" % rec["reason"] if rec["reason"] else "",
        n(rec["exit_criteria"]["rederived"]), n(tests["passed"]), n(tests["total"]),
        n(tokens["input"]), n(tokens["output"]), n(tokens["cache_read"]), n(rec["wall_clock_s"]), interrupts))


def _append_and_flush(command: str, doc: dict, out: Path, rec: dict, replace: bool = False) -> None:
    try:
        scrub(rec)
    except ScrubError as exc:
        _refuse(command, "record for %s run %s failed scrub: %s; nothing written"
                % (rec.get("story_id"), rec.get("run"), exc), code=3)
    if replace:
        doc["runs"] = [r for r in doc["runs"] if (r.get("story_id"), r.get("run")) != (rec["story_id"], rec["run"])]
    doc["runs"].append(rec)
    write_json(out, doc)
    print(_progress(command, rec))


def execute_run(git: Git, yuss: Path, entry: dict, run: int, args: argparse.Namespace,
                model: str, driver: Driver) -> dict:
    """One (story, run): build, stage, overlay, deps, invoke, post-process.
    Every failure before the model runs becomes an error record."""
    stem = Path(entry["story_path"]).stem
    run_dir = Path(args.tmp_root) / ("%s%s-%d" % (TMP_PREFIX, stem, run))
    story_rel = story_rel_path(entry)
    head_before = (git.run("rev-parse", "HEAD") or "").strip()
    meta = {"story_id": entry["story_id"], "run": run, "parent_sha": entry["parent_sha"],
            "started_at": _stamp(_utcnow()), "isolation": None, "writ": None, "inputs": None, "deps": None,
            "invocation": {"driver": driver.name, "argv": driver_argv(driver, story_rel, model, args.budget_usd),
                           "model": model, "permission_mode": PERMISSION_MODE},
            "elapsed_s": None, "timed_out": False, "yuss_head_unchanged": None, "reason": None}
    if run_dir.exists():
        rmtree(run_dir)
    run_dir.mkdir(parents=True)
    try:
        rec = _replay(git, yuss, entry, run_dir, story_rel, meta, args, head_before)
        scrub(rec)
    except BaseException:
        # A Ctrl-C, a post-processing bug, a scrub failure: the transcript is
        # the paid artifact, and `ingest` can rebuild the record from it.
        print("run: run dir kept: %s" % run_dir, file=sys.stderr)
        raise
    if not args.keep:
        rmtree(run_dir)
    return rec


def _replay(git: Git, yuss: Path, entry: dict, run_dir: Path, story_rel: str, meta: dict,
            args: argparse.Namespace, head_before: str) -> dict:
    try:
        checkout, meta["isolation"] = build_checkout(yuss, entry["parent_sha"], run_dir)
        if not meta["isolation"]["asserted"]:
            raise RunError("isolation_failed")
        meta["inputs"] = stage_inputs(git, checkout, entry)
        assert_answer_scrubbed(checkout, story_rel)
        meta["isolation"]["answer_scrub_asserted"] = True
        driver = DRIVERS[meta["invocation"]["driver"]]
        meta["writ"] = overlay_writ(checkout, Path(args.writ_root), run_dir / "install.log",
                                   platform=driver.platform)
        meta["deps"] = install_deps(checkout, run_dir / "pnpm-install.log")
        _write_sidecar(run_dir, meta)               # persisted before the long-running step
    except RunError as exc:
        meta["reason"] = exc.reason
        if exc.isolation is not None:
            meta["isolation"] = exc.isolation
        meta["yuss_head_unchanged"] = (git.run("rev-parse", "HEAD") or "").strip() == head_before
        return assemble_record(meta, None, None, None)
    transcript = run_dir / "transcript.jsonl"
    driver = DRIVERS[meta["invocation"]["driver"]]
    stderr_log = run_dir / "stderr.log"
    meta["timed_out"], meta["elapsed_s"] = invoke_headless(
        meta["invocation"]["argv"], checkout, transcript, stderr_log, args.cap,
        nested_vars=driver.nested_vars)
    stderr_text = ""
    if stderr_log.is_file():
        stderr_text = stderr_log.read_text(encoding="utf-8", errors="replace")
    meta["background_tasks_outstanding"] = count_background_drops(stderr_text)
    meta["yuss_head_unchanged"] = (git.run("rev-parse", "HEAD") or "").strip() == head_before
    _write_sidecar(run_dir, meta)
    return postprocess(git, checkout, transcript, entry, meta, run_dir, Path(args.writ_root))


def cmd_run(args: argparse.Namespace) -> None:
    try:
        preflight(driver=args.driver, model=args.model)
    except Refusal as exc:
        _refuse("run", str(exc))
    baseline = Path(args.baseline).expanduser().resolve()
    # Refuse ingest-only models from --model or the filename before any git.
    hint = args.model or model_from_filename(baseline.name)
    if hint:
        try:
            resolve_driver(args.driver, hint)
        except Refusal as exc:
            _refuse("run", str(exc))
    yuss = Path(args.yuss).expanduser().resolve()
    doc = load_baseline("run", baseline, yuss)
    model = args.model or doc["model"]
    if model != doc["model"]:
        _refuse("run", "--model %s differs from the file's model %s; one model per file (Business Rule 4)"
                % (model, doc["model"]))
    try:
        driver = resolve_driver(args.driver, model)
    except Refusal as exc:
        _refuse("run", str(exc))
    if args.runs < 1:
        _refuse("run", "--runs must be at least 1")
    if doc["runs_per_story"] is not None and doc["runs_per_story"] != args.runs and not args.force:
        _refuse("run", "runs_per_story is already %s; pass --force to change it to %d"
                % (doc["runs_per_story"], args.runs))
    entries = _select_entries("run", doc, args.story)
    git = Git(yuss)
    runs_per_story_changed = doc["runs_per_story"] != args.runs
    doc["runs_per_story"] = args.runs
    present = _present_pairs(doc)
    flushed = False
    for entry in entries:
        for run in range(1, args.runs + 1):
            if (entry["story_id"], run) in present:
                print("run: %s run %d: skip (already recorded)" % (entry["story_id"], run))
                continue
            try:
                rec = execute_run(git, yuss, entry, run, args, model, driver)
            except ScrubError as exc:
                _refuse("run", "record for %s run %s failed scrub: %s; nothing written"
                        % (entry["story_id"], run, exc), code=3)
            _append_and_flush("run", doc, baseline, rec)
            flushed = True
            if rec["yuss_head_unchanged"] is False:
                _refuse("run", "yuss HEAD moved during %s run %d; yuss must stay read-only (Business Rule 2)"
                        % (entry["story_id"], run), code=3)
    if runs_per_story_changed and not flushed:
        # `--force --runs N` with every pair already present: the only change
        # is runs_per_story, and the loop wrote nothing.
        write_json(baseline, doc)
        print("run: runs_per_story set to %d" % args.runs)
    sys.exit(0)


def cmd_ingest(args: argparse.Namespace) -> None:
    baseline = Path(args.baseline).expanduser().resolve()
    yuss = Path(args.yuss).expanduser().resolve()
    checkout = Path(args.checkout).expanduser().resolve()
    transcript = Path(args.transcript).expanduser().resolve()
    if not (checkout / ".git").is_dir():
        _refuse("ingest", "--checkout %s is not a git checkout" % checkout)
    if not transcript.is_file():
        _refuse("ingest", "--transcript %s does not exist" % transcript)
    stderr_text = ""
    for candidate in (transcript.with_name("stderr.log"), checkout / "stderr.log"):
        if candidate.is_file():
            stderr_text = candidate.read_text(encoding="utf-8", errors="replace")
            break
    ingest_background = count_background_drops(stderr_text)
    doc = load_baseline("ingest", baseline, yuss)
    sidecar = next((p for p in (checkout.parent / SIDECAR, checkout / SIDECAR) if p.is_file()), None)
    if sidecar is not None:
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        story_id = args.story_id or meta.get("story_id")
        run = args.run or meta.get("run")
    else:
        if not (args.story_id and args.run):
            _refuse("ingest", "no %s beside %s; pass --story-id and --run" % (SIDECAR, checkout))
        story_id, run = args.story_id, args.run
        meta = {"story_id": story_id, "run": run, "started_at": _stamp(_utcnow()), "reason": "ingested without sidecar",
                "isolation": {"reachable_commits": None, "expected": EXPECTED_REACHABLE,
                              "asserted": False, "answer_scrub_asserted": False},
                "invocation": {"model": doc["model"]}}
    entry = next((e for e in doc["selection"] if e["story_id"] == story_id), None)
    if entry is None:
        _refuse("ingest", "story %s is not in the file's selection" % story_id)
    if (story_id, run) in _present_pairs(doc) and not args.force:
        _refuse("ingest", "%s run %s is already recorded; pass --force to replace it" % (story_id, run))
    artifacts = Path(args.tmp_root) / ("%singest-%s-%s" % (TMP_PREFIX, Path(entry["story_path"]).stem, run))
    if artifacts.exists():
        rmtree(artifacts)
    artifacts.mkdir(parents=True)
    meta["background_tasks_outstanding"] = ingest_background
    try:
        rec = postprocess(Git(yuss), checkout, transcript, entry, meta, artifacts, Path(args.writ_root))
    finally:
        rmtree(artifacts)
    _append_and_flush("ingest", doc, baseline, rec, replace=args.force)
    sys.exit(0)


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

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--baseline", required=True, help="the pipeline-baseline-v1 JSON select wrote; runs[] is appended")
        p.add_argument("--yuss", required=True, help="path to the read-only yuss.app checkout (fetch source only)")
        p.add_argument("--tmp-root", default=tempfile.gettempdir(),
                       help="where %s<story>-<n>/ run directories are created (default: $TMPDIR)" % TMP_PREFIX)
        p.add_argument("--force", action="store_true", help="run: change runs_per_story; ingest: replace a recorded pair")
        p.add_argument("--writ-root", default=str(Path(__file__).resolve().parent.parent),
                       help="Writ repo whose scripts/install.sh is overlaid onto the checkout and whose "
                            "build-smoke.py / test-integrity.py re-derive Gates 2 and 4 (default: this repo)")

    run = sub.add_parser("run", help="replay each selected story headless in an isolated checkout")
    common(run)
    run.add_argument("--model", default=None, help="model ID; must equal the file's model (default: the file's)")
    run.add_argument("--driver", default="auto", choices=DRIVER_NAMES,
                     help="headless agent CLI (default: auto — inferred from --model / the file). "
                          "Grok, local weights, and other IDE-session models use ingest")
    run.add_argument("--runs", type=int, default=2, help="runs per story; sets runs_per_story (default: %(default)s)")
    run.add_argument("--story", default=None, help="only this story_id or story file stem (smoke runs)")
    run.add_argument("--cap", type=int, default=DEFAULT_CAP_S,
                     help="wall-clock cap per run in seconds; a breach records status timeout (default: %(default)s)")
    run.add_argument("--budget-usd", type=float, default=DEFAULT_BUDGET_USD,
                     help="passed to the driver as a dollar cap when it supports one (default: %(default)s)")
    run.add_argument("--keep", action="store_true", help="keep the run directory (checkout, transcript, sidecar)")
    run.set_defaults(func=cmd_run)

    ingest = sub.add_parser("ingest", help="compute a run record from an existing checkout and transcript")
    common(ingest)
    ingest.add_argument("--checkout", required=True, help="the isolated checkout the session ran in")
    ingest.add_argument("--transcript", required=True,
                        help="driver transcript (claude stream-json, or an IDE session jsonl)")
    ingest.add_argument("--story-id", default=None, help="required when no %s sits beside --checkout" % SIDECAR)
    ingest.add_argument("--run", type=int, default=None, help="run number; required without a sidecar")
    ingest.set_defaults(func=cmd_ingest)

    val = sub.add_parser("validate", help="check a baseline JSON against the schema and leak heuristics")
    val.add_argument("file", help="pipeline-baseline-v1 JSON to validate (read-only)")
    val.set_defaults(func=cmd_validate)

    cmp_ = sub.add_parser("compare", help="print per-story metric deltas between two baseline files")
    cmp_.add_argument("a", help="baseline A (left column)")
    cmp_.add_argument("b", help="baseline B (right column)")
    cmp_.set_defaults(func=cmd_compare)
    return parser


def main(argv: Optional[list] = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
