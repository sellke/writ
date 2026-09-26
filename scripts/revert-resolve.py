#!/usr/bin/env python3
"""Deterministic logical-unit → commit resolver for `/revert`.

Maps a Writ *logical unit* (a `story` or a whole `spec`) to the real git
commits that implemented it, resilient to rewritten SHAs. This is the
executable reference consumed by `commands/revert.md`. It is **read-only**:
it never mutates git state or any file, and it never auto-selects a fuzzy
"ghost" match — those are surfaced for the command to confirm.

Resolution order (per commit source), highest confidence first:

  1. `recorded`     - the story file's `> **Commit:** <sha>` field
                      (written by `/implement-story` Step 4). Verified present
                      in history; if absent it becomes a `ghost` candidate.
  2. `ref-footer`   - a `/ship` `Ref:` footer naming this spec's folder (and,
                      for a story, that story file). A Ref naming another spec,
                      or no spec, never matches on story number alone.
  2b. `task-subject` - `Story N (N.x): ...` subjects between the spec-scaffold
                      commit and the story's completion commit, excluding any
                      commit whose Ref or `.writ/specs/` paths name only
                      another spec.
  3. `phase-state`  - `.writ/state/phase-execution-*.json` `commit`/`mergeCommit`
                      tied to the spec (read-only lookup).
  4. `ghost`        - for any recorded SHA absent from history, the top
                      subject-similarity candidate (stdlib difflib). Never
                      auto-selected; emitted under `ghost`.

A `spec` unit is the union of every story's commits plus the spec-scaffolding
commit (the commit that first added `.writ/specs/<id>/spec.md`) plus any
phase-state commit for the spec.

CLI:
  revert-resolve.py <unit> <id> [--repo PATH] [--spec SPEC_ID] [--json]

`unit` in {story, spec}. Success prints the resolution object (JSON with
`--json`, otherwise a human summary) and exits 0. A contract violation prints
a JSON `blocker` object and exits non-zero.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


RESULT_SCHEMA = "revert-resolve-v1"
GHOST_SIMILARITY_FLOOR = 0.30

STORY_NUM = re.compile(r"(\d+)")
COMMIT_FIELD = re.compile(r"^>\s*\*\*Commit:\*\*\s*([0-9a-fA-F]{7,40})\s*$")
STORY_TITLE = re.compile(r"^#\s*Story\s+[^:]*:\s*(.+?)\s*$")
REVERTED_BANNER = "> **Reverted:**"
# Conventional-commit prefix: feat(scope): ...  -> strip for fair similarity.
CC_PREFIX = re.compile(r"^[a-z]+(\([^)]*\))?!?:\s*", re.IGNORECASE)


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _fail(err: ContractError) -> None:
    print(json.dumps({"blocker": {"code": err.code, "summary": err.summary}}))
    raise SystemExit(1)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise ContractError(
            "git_error",
            f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}",
        )
    return proc


def _commit_exists(repo: Path, sha: str) -> bool:
    return _git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0


def _subject(repo: Path, sha: str) -> str:
    return _git(repo, "log", "-1", "--format=%s", sha, check=False).stdout.strip()


def _full_sha(repo: Path, sha: str) -> str:
    out = _git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}", check=False).stdout.strip()
    return out or sha


def _depth(repo: Path, sha: str) -> int:
    """Number of commits reachable from `sha` — a deterministic newness proxy
    (higher = newer on a linear or topo-ordered history)."""
    out = _git(repo, "rev-list", "--count", sha, check=False).stdout.strip()
    return int(out) if out.isdigit() else 0


def _is_merge(repo: Path, sha: str) -> bool:
    out = _git(repo, "rev-list", "--parents", "-n", "1", sha, check=False).stdout.split()
    return len(out) > 2  # sha + 2+ parents


def _parent(repo: Path, sha: str) -> str | None:
    proc = _git(repo, "rev-parse", "--verify", f"{sha}^", check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _normalize(subject: str) -> str:
    subject = CC_PREFIX.sub("", subject.strip().lower())
    return re.sub(r"\s+", " ", subject)


def _all_commits(repo: Path) -> list[tuple[str, str]]:
    """[(sha, subject)] for the whole history, newest first."""
    out = _git(repo, "log", "--format=%H%x00%s", check=False).stdout
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        if "\x00" in line:
            sha, subject = line.split("\x00", 1)
            commits.append((sha, subject))
    return commits


# --------------------------------------------------------------------------- #
# Story-file discovery + field parsing
# --------------------------------------------------------------------------- #

def _specs_dir(repo: Path) -> Path:
    return repo / ".writ" / "specs"


def _normalize_story_key(story_id: str) -> str:
    m = STORY_NUM.search(story_id)
    if not m:
        raise ContractError(
            "bad_story_id",
            f"cannot derive a story number from {story_id!r} (expected e.g. story-3)",
        )
    return f"story-{m.group(1)}"


def _find_story_file(repo: Path, story_id: str, spec_id: str | None) -> Path:
    key = _normalize_story_key(story_id)
    search_roots: list[Path]
    if spec_id:
        search_roots = [_specs_dir(repo) / spec_id / "user-stories"]
    else:
        search_roots = sorted(_specs_dir(repo).glob("*/user-stories"))

    matches: list[Path] = []
    for root in search_roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob(f"{key}-*.md")) + sorted(root.glob(f"{key}.md")):
            matches.append(path)

    if not matches:
        raise ContractError(
            "story_not_found",
            f"no story file for {key} under {_specs_dir(repo)}"
            + (f"/{spec_id}" if spec_id else ""),
        )
    if len(matches) > 1 and not spec_id:
        specs = ", ".join(sorted({p.parent.parent.name for p in matches}))
        raise ContractError(
            "ambiguous_story",
            f"{key} exists in multiple specs ({specs}); pass --spec to disambiguate",
        )
    return matches[0]


def _story_files_for_spec(repo: Path, spec_id: str) -> list[Path]:
    root = _specs_dir(repo) / spec_id / "user-stories"
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("story-*.md") if p.is_file())


def _read_commit_field(story_path: Path) -> str | None:
    for raw in story_path.read_text(encoding="utf-8").splitlines():
        m = COMMIT_FIELD.match(raw)
        if m:
            return m.group(1)
    return None


def _story_title(story_path: Path) -> str:
    for raw in story_path.read_text(encoding="utf-8").splitlines():
        m = STORY_TITLE.match(raw)
        if m:
            return m.group(1)
    return story_path.stem


# --------------------------------------------------------------------------- #
# Resolution layers
# --------------------------------------------------------------------------- #

def _ghost_candidate(repo: Path, recorded: str, target_subject: str) -> dict[str, Any] | None:
    target = _normalize(target_subject)
    best: dict[str, Any] | None = None
    for sha, subject in _all_commits(repo):
        ratio = difflib.SequenceMatcher(None, target, _normalize(subject)).ratio()
        if best is None or ratio > best["similarity"]:
            best = {"recorded": recorded, "candidate": sha, "subject": subject,
                    "similarity": round(ratio, 2)}
    if best is None or best["similarity"] < GHOST_SIMILARITY_FLOOR:
        return None
    return best


def _resolve_recorded(repo: Path, story_path: Path,
                      commits: dict[str, dict], ghosts: list[dict],
                      warnings: list[str]) -> None:
    recorded = _read_commit_field(story_path)
    if not recorded:
        return
    if _commit_exists(repo, recorded):
        full = _full_sha(repo, recorded)
        commits.setdefault(full, {
            "sha": full,
            "subject": _subject(repo, full),
            "source": "recorded",
            "confidence": "exact",
        })
    else:
        candidate = _ghost_candidate(repo, recorded, _story_title(story_path))
        if candidate:
            ghosts.append(candidate)
            warnings.append(
                f"recorded SHA {recorded} for {story_path.name} is absent from "
                f"history; offering ghost candidate {candidate['candidate'][:8]} "
                f"(similarity {candidate['similarity']}) — confirm before use"
            )
        else:
            warnings.append(
                f"recorded SHA {recorded} for {story_path.name} is absent from "
                f"history and no similar commit was found"
            )


REF_LINE = re.compile(r"^\s*Ref:\s*(.+?)\s*$", re.MULTILINE)
SPEC_IN_REF = re.compile(r"\.writ/specs/([^/\s]+)")


def _ref_values(body: str) -> list[str]:
    return REF_LINE.findall(body)


def _ref_matches(ref: str, spec_id: str, story_key: str | None) -> bool:
    """True when a `Ref:` value names `spec_id` (and, for a story, that exact
    story file). A Ref naming another spec, or no spec, never matches."""
    specs = SPEC_IN_REF.findall(ref)
    if spec_id not in specs:
        return False
    if story_key is None:
        return True
    pattern = re.compile(
        re.escape(f"{spec_id}/user-stories/{story_key}") + r"(?:[-.]|$)")
    return bool(pattern.search(ref))


def _resolve_ref_footer(repo: Path, spec_id: str, story_key: str | None,
                        commits: dict[str, dict]) -> None:
    """`/ship` `Ref:` footers scoped to the spec (and story, when given)."""
    out = _git(
        repo, "log", f"--grep=Ref: .*{re.escape(spec_id)}",
        "--extended-regexp", "--format=%H%x00%s%x00%B%x1e", check=False,
    ).stdout
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if record.count("\x00") < 2:
            continue
        sha, subject, body = record.split("\x00", 2)
        if not any(_ref_matches(r, spec_id, story_key) for r in _ref_values(body)):
            continue
        if _commit_exists(repo, sha):
            commits.setdefault(sha, {
                "sha": sha,
                "subject": subject,
                "source": "ref-footer",
                "confidence": "exact",
            })


def _scaffold_sha(repo: Path, spec_id: str) -> str | None:
    rel = f".writ/specs/{spec_id}/spec.md"
    out = _git(repo, "log", "--diff-filter=A", "--format=%H", "--", rel,
               check=False).stdout.split()
    return out[-1] if out else None


def _story_upper_bound(repo: Path, story_path: Path) -> str | None:
    """The story's completion commit (recorded SHA) or, failing that, the
    latest commit that touched the story file."""
    recorded = _read_commit_field(story_path)
    if recorded and _commit_exists(repo, recorded):
        return _full_sha(repo, recorded)
    rel = story_path.relative_to(repo).as_posix()
    out = _git(repo, "log", "-1", "--format=%H", "--", rel, check=False).stdout.strip()
    return out or None


def _foreign_only(repo: Path, sha: str, body: str, spec_id: str) -> bool:
    """True when a commit belongs to another spec: its Ref footer names a
    different spec, or it touches other specs' folders and not this one's."""
    for ref in _ref_values(body):
        named = SPEC_IN_REF.findall(ref)
        if named and spec_id not in named:
            return True
    files = _git(repo, "show", "--name-only", "--format=", sha,
                 check=False).stdout.split("\n")
    touched = {m.group(1) for f in files
               for m in [re.match(r"\.writ/specs/([^/]+)/", f)] if m}
    return bool(touched) and spec_id not in touched


def _resolve_task_subjects(repo: Path, spec_id: str, story_path: Path,
                           commits: dict[str, dict]) -> None:
    """Task-numbered subjects (`Story N (N.x): ...`) inside the spec's commit
    range: after the spec-scaffold commit, up to the story's completion."""
    scaffold = _scaffold_sha(repo, spec_id)
    upper = _story_upper_bound(repo, story_path)
    if not scaffold or not upper:
        return
    num = _normalize_story_key(story_path.stem).split("-", 1)[1]
    subject_re = re.compile(rf"^Story\s+{num}\s*\(\s*{num}\.")
    out = _git(repo, "log", "--format=%H%x00%s%x00%B%x1e",
               upper, f"^{scaffold}", check=False).stdout
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if record.count("\x00") < 2:
            continue
        sha, subject, body = record.split("\x00", 2)
        if not subject_re.match(subject):
            continue
        if _foreign_only(repo, sha, body, spec_id):
            continue
        commits.setdefault(sha, {
            "sha": sha,
            "subject": subject,
            "source": "task-subject",
            "confidence": "exact",
        })


def _phase_state_commits(repo: Path, spec_id: str) -> list[str]:
    state_dir = repo / ".writ" / "state"
    if not state_dir.is_dir():
        return []
    found: list[str] = []
    for state_file in sorted(state_dir.glob("phase-execution-*.json")):
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        specs = data.get("specs", {})
        entry = specs.get(spec_id)
        if not isinstance(entry, dict):
            continue
        for key in ("commit", "mergeCommit"):
            sha = entry.get(key)
            if isinstance(sha, str) and sha:
                found.append(sha)
    return found


def _resolve_phase_state(repo: Path, spec_id: str,
                         commits: dict[str, dict]) -> None:
    for sha in _phase_state_commits(repo, spec_id):
        if _commit_exists(repo, sha):
            commits.setdefault(sha, {
                "sha": _full_sha(repo, sha),
                "subject": _subject(repo, sha),
                "source": "phase-state",
                "confidence": "exact",
            })


def _spec_scaffold_commit(repo: Path, spec_id: str,
                          commits: dict[str, dict]) -> None:
    sha = _scaffold_sha(repo, spec_id)
    if sha and _commit_exists(repo, sha):
        commits.setdefault(sha, {
            "sha": sha,
            "subject": _subject(repo, sha),
            "source": "spec-scaffold",
            "confidence": "exact",
        })


# --------------------------------------------------------------------------- #
# Ordering, base, warnings
# --------------------------------------------------------------------------- #

def _order_and_finalize(repo: Path, unit: str, unit_id: str,
                        commits: dict[str, dict], ghosts: list[dict],
                        warnings: list[str]) -> dict[str, Any]:
    ordered = sorted(
        commits.values(),
        key=lambda c: (_depth(repo, c["sha"]), c["sha"]),
        reverse=True,  # newest (deepest) first
    )

    subjects_seen: dict[str, str] = {}
    for commit in ordered:
        if _is_merge(repo, commit["sha"]):
            warnings.append(
                f"{commit['sha'][:8]} is a merge commit — reverting it needs a "
                f"mainline (-m); review before applying"
            )
        norm = _normalize(commit["subject"])
        if norm and norm in subjects_seen:
            warnings.append(
                f"{commit['sha'][:8]} shares a subject with "
                f"{subjects_seen[norm][:8]} (possible cherry-pick duplicate)"
            )
        else:
            subjects_seen[norm] = commit["sha"]

    base: str | None = None
    if ordered:
        earliest = ordered[-1]["sha"]
        base = _parent(repo, earliest)
        if base is None:
            warnings.append(
                f"earliest commit {earliest[:8]} is a root commit — no parent "
                f"base for hard reset"
            )
    else:
        warnings.append(
            f"no commits resolved for {unit} {unit_id}; nothing to revert"
        )

    return {
        "schema": RESULT_SCHEMA,
        "unit": unit,
        "id": unit_id,
        "commits": ordered,
        "ghost": ghosts,
        "base": base,
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- #
# Public resolution entry points
# --------------------------------------------------------------------------- #

def resolve_story(repo: Path, story_id: str, spec_id: str | None = None) -> dict[str, Any]:
    story_path = _find_story_file(repo, story_id, spec_id)
    resolved_spec = story_path.parent.parent.name
    key = _normalize_story_key(story_id)

    commits: dict[str, dict] = {}
    ghosts: list[dict] = []
    warnings: list[str] = []

    _resolve_recorded(repo, story_path, commits, ghosts, warnings)
    _resolve_ref_footer(repo, resolved_spec, key, commits)
    _resolve_task_subjects(repo, resolved_spec, story_path, commits)
    _resolve_phase_state(repo, resolved_spec, commits)

    return _order_and_finalize(repo, "story", key, commits, ghosts, warnings)


def resolve_spec(repo: Path, spec_id: str) -> dict[str, Any]:
    if not (_specs_dir(repo) / spec_id).is_dir():
        raise ContractError(
            "spec_not_found",
            f"no spec folder at .writ/specs/{spec_id}",
        )

    commits: dict[str, dict] = {}
    ghosts: list[dict] = []
    warnings: list[str] = []

    for story_path in _story_files_for_spec(repo, spec_id):
        _resolve_recorded(repo, story_path, commits, ghosts, warnings)

    _resolve_ref_footer(repo, spec_id, None, commits)
    for story_path in _story_files_for_spec(repo, spec_id):
        _resolve_task_subjects(repo, spec_id, story_path, commits)
    _resolve_phase_state(repo, spec_id, commits)
    _spec_scaffold_commit(repo, spec_id, commits)

    return _order_and_finalize(repo, "spec", spec_id, commits, ghosts, warnings)


def resolve(repo: Path, unit: str, unit_id: str, spec_id: str | None = None) -> dict[str, Any]:
    if unit == "story":
        return resolve_story(repo, unit_id, spec_id)
    if unit == "spec":
        return resolve_spec(repo, unit_id)
    raise ContractError("bad_unit", f"unit must be 'story' or 'spec', got {unit!r}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _render_human(result: dict[str, Any]) -> str:
    lines = [f"Revert plan for {result['unit']} {result['id']}:", ""]
    if result["commits"]:
        lines.append("Commits (newest → oldest, revert order):")
        for c in result["commits"]:
            lines.append(f"  {c['sha'][:8]}  [{c['source']}]  {c['subject']}")
    else:
        lines.append("Commits: (none resolved)")
    if result["ghost"]:
        lines.append("")
        lines.append("Ghost candidates (require confirmation — never auto-applied):")
        for g in result["ghost"]:
            lines.append(
                f"  recorded {g['recorded'][:8]} → candidate {g['candidate'][:8]}"
                f"  (similarity {g['similarity']})  {g['subject']}"
            )
    lines.append("")
    lines.append(f"Base (hard-reset target): {result['base'] or '(none)'}")
    if result["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        for w in result["warnings"]:
            lines.append(f"  - {w}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unit", choices=["story", "spec"])
    parser.add_argument("id")
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--spec", default=None,
                        help="disambiguate a story that exists in multiple specs")
    parser.add_argument("--json", action="store_true",
                        help="emit the machine-readable resolution object")
    args = parser.parse_args(argv)

    try:
        result = resolve(args.repo, args.unit, args.id, args.spec)
    except ContractError as err:
        _fail(err)
        return 1  # unreachable; _fail raises

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(_render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
