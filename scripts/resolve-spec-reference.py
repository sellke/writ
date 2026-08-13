#!/usr/bin/env python3
"""Shared Spec Reference resolution (Story 1 of post-merge-archival-hook).

`commands/ship.md`'s Step 5 PR-body population has always described Spec
Reference matching only as prose: match the branch name or recent
story-file references in commits against `.writ/specs/`. There was no
discrete, callable implementation, so `commands/release.md` could not reuse
it without either duplicating the prose or drifting into a second,
independent heuristic. This script is the single shared implementation both
commands call.

Matching strategy (either signal alone can resolve; conflicting signals do
not tie-break):

1. Branch name vs. spec-folder name: case-insensitive substring match,
   checked against both the full branch string and its last `/`-separated
   path segment (so `feature/`, `chore/`, `fix/`, or even a multi-segment
   prefix like `writ/phase/8/` never needs an exhaustive prefix list -- the
   final segment is what actually carries the descriptive slug), and against
   both the full folder name and the folder name with its leading
   `YYYY-MM-DD-` date component stripped.
2. Commit messages vs. spec-folder name: case-insensitive substring scan of
   both the full folder name (covers `.writ/specs/<name>/` path references)
   and the folder name with its leading `YYYY-MM-DD-` date component
   stripped (covers a completing commit naming the spec by its bare slug,
   e.g. "Completes Story 6 and the machine-evaluable-exit-criteria spec." --
   the exact phrasing that silently missed a real spec pre-v0.31.1, since
   this signal previously checked only the dated folder name while signal 1
   already stripped the date prefix), plus a scan for any of that spec's
   `user-stories/*.md` filenames (covers a commit mentioning
   `story-3-session-management.md` without the full path).
3. Candidates from both signals are deduplicated by resolved spec-folder
   name *before* counting distinctness -- the same spec surfaced by two
   signals is one match, not two. Zero distinct matches after dedup is
   `none`; exactly one is `matched`; two or more is `ambiguous`. Ambiguity is
   the safeguard (Business Rule 3: ambiguous or absent resolution always
   skips, never guesses) -- there is deliberately no tie-breaking logic.

Subcommand:
  resolve --specs-dir DIR [--branch NAME] [--commits TEXT]
    Resolve a branch name and/or commit-message text against every spec
    folder under DIR. Always prints one JSON object and exits 0 -- this is a
    best-effort resolver, not a fail-closed validator, and it never raises:
    a missing `--specs-dir` degrades to a `none` result, an absent/empty
    `--branch` simply skips signal 1 and falls through to commit matching.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_RESOLVE = "resolve-spec-reference-v1"

DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# Only files that look like an actual story file count as a commit-message
# signal (technical-spec.md's own example: "story-3-session-management.md").
# Every spec's `user-stories/` folder also has a generic `README.md` index
# (Writ convention) -- if that filename counted too, any commit merely
# mentioning the word "README.md" (extremely common; verified against this
# repo's own history) would false-positive-match nearly every spec at once.
STORY_FILE_PATTERN = re.compile(r"^story-\d+-.+\.md$")


def _list_spec_folders(specs_dir: Path) -> list[str]:
    """Return spec folder names directly under `specs_dir`.

    Uses the same single-level `*/spec.md` glob as `spec-status.py` -- the
    archive-exclusion mechanism (Business Rule 5): a spec.md living two
    levels deep under `archive/<name>/` is never picked up here. A missing
    or unreadable `specs_dir` degrades to an empty list rather than raising.
    """
    try:
        return sorted(p.parent.name for p in specs_dir.glob("*/spec.md"))
    except OSError:
        return []


def _branch_variants(branch_name: str) -> list[str]:
    """Lowercase strings to test against spec-folder names/slugs."""
    lowered = branch_name.strip().lower()
    variants = {lowered}
    if "/" in lowered:
        variants.add(lowered.rsplit("/", 1)[-1])
    return [v for v in variants if v]


def _match_branch_name(branch_name: str | None, spec_folders: list[str]) -> list[str]:
    """Signal 1: substring match branch name against spec-folder names.

    Graceful degradation: an absent/empty branch name skips this signal
    entirely (returns no matches) rather than matching everything or raising.
    """
    if not branch_name:
        return []
    variants = _branch_variants(branch_name)
    matches: list[str] = []
    for folder in spec_folders:
        folder_lower = folder.lower()
        slug = DATE_PREFIX.sub("", folder_lower)
        for variant in variants:
            if (
                variant in folder_lower
                or variant in slug
                or folder_lower in variant
                or slug in variant
            ):
                matches.append(folder)
                break
    return matches


def _match_commit_messages(
    commit_messages: list[str], spec_folders: list[str], specs_dir: Path
) -> list[str]:
    """Signal 2: scan commit text for spec-folder names or story-file names."""
    if not commit_messages:
        return []
    blob = "\n".join(commit_messages).lower()
    matches: list[str] = []
    for folder in spec_folders:
        folder_lower = folder.lower()
        slug = DATE_PREFIX.sub("", folder_lower)
        if folder_lower in blob or slug in blob:
            matches.append(folder)
            continue
        stories_dir = specs_dir / folder / "user-stories"
        try:
            story_names = [
                p.name.lower()
                for p in stories_dir.glob("*.md")
                if STORY_FILE_PATTERN.match(p.name.lower())
            ]
        except OSError:
            story_names = []
        if any(name in blob for name in story_names):
            matches.append(folder)
    return matches


def resolve_spec_reference(
    branch_name: str | None,
    commit_messages: list[str] | None,
    specs_dir: Path,
) -> dict[str, Any]:
    """Resolve which single spec folder a branch/commit set refers to.

    Returns a tri-state JSON-shaped dict: `result` is `"matched"` (exactly
    one distinct spec across both signals, reported as `spec`), `"none"`
    (zero matches), or `"ambiguous"` (two or more distinct specs, reported
    as `candidates`) -- see module docstring for the dedup rule. Never
    raises: an unreadable `specs_dir` or missing branch name degrade to
    fewer signals rather than an error.
    """
    specs_dir = Path(specs_dir)
    spec_folders = _list_spec_folders(specs_dir)

    branch_matches = _match_branch_name(branch_name, spec_folders)
    commit_matches = _match_commit_messages(commit_messages or [], spec_folders, specs_dir)

    distinct = sorted(set(branch_matches) | set(commit_matches))

    if len(distinct) == 1:
        result, spec, candidates = "matched", distinct[0], []
    elif len(distinct) > 1:
        result, spec, candidates = "ambiguous", None, distinct
    else:
        result, spec, candidates = "none", None, []

    return {
        "schema": SCHEMA_RESOLVE,
        "result": result,
        "spec": spec,
        "candidates": candidates,
        "signals": {
            "branch_matches": sorted(set(branch_matches)),
            "commit_matches": sorted(set(commit_matches)),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="resolve a branch/commit set to a spec folder")
    p_resolve.add_argument("--branch", default=None, help="branch name to match (optional)")
    p_resolve.add_argument(
        "--commits", default=None, help="commit message text to scan (optional)"
    )
    p_resolve.add_argument(
        "--specs-dir", default=Path(".writ/specs"), type=Path, help="specs directory to scan"
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "resolve":
            commit_messages = [args.commits] if args.commits else []
            result = resolve_spec_reference(args.branch, commit_messages, args.specs_dir)
        else:  # pragma: no cover - argparse's `required=True` prevents this
            result = {"schema": SCHEMA_RESOLVE, "result": "none", "spec": None, "candidates": []}
    except Exception:
        # Best-effort resolver -- never fail closed (module docstring).
        result = {
            "schema": SCHEMA_RESOLVE,
            "result": "none",
            "spec": None,
            "candidates": [],
            "signals": {"branch_matches": [], "commit_matches": []},
        }

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
