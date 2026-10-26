# Story 3: Blast radius at Gate 2.5

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** /implement-story orchestrator, and the review-agent that traces callers
**I want to** list, for each changed non-test file, the tracked files outside the change set that reference it, and save that list at Gate 2.5 on the review-agent route
**So that** the reviewer starts its caller trace from a concrete list, and Story 4's verifier can check a `traced` claim against it

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given a changed non-test file that a tracked file outside the change set references by path (with or without extension) or by stem, when `python3 scripts/change-surface.py blast-radius --changed FILE --repo .` runs, then the referring file appears under `consumers` for that changed file, a test-like referrer (`.test.`, `.spec.`, `__tests__/`, `test_*.py`, `*_test.py`, `*_test.go`, or a `test/` or `tests/` segment) appears under `tests` instead, no changed file and no file under `.writ/` appears in either list, and a candidate over 1 MB or not valid UTF-8 is skipped without an error `[AC-3.1]`
- [ ] Given a changed file whose stem is generic (for example `index` or `utils`) or shorter than 4 characters, when blast-radius runs, then a file that contains only the bare stem is not listed and a file that contains the file's path is listed; and given any token, a match counts only when the characters on both sides are not `[A-Za-z0-9_-]`, so `review-override` does not match inside `review-override-v2` `[AC-3.2]`
- [ ] Given a changed file with more matching referrers than `--limit`, when blast-radius runs with `--limit 2`, then that file's `consumers` list holds exactly 2 entries sorted by path and the changed file's path appears in `truncated` `[AC-3.3]`
- [ ] Given `git ls-files` fails in `--repo`, when blast-radius runs, then it walks the filesystem and returns `verdict: pass` with `reasons: ["no_git_walked"]`; given `--repo` is not a readable directory, then it returns `verdict: unverifiable` with `reasons: ["repo_unreadable"]` and exit 0; given an empty `--changed`, then it exits 2; and `classify` output and exit codes match the behavior before this story `[AC-3.4]`
- [ ] Given `gate3_route` names `review-agent` and `review-override.py switch --name safety-fact` prints `on`, when Gate 2.5 in `commands/implement-story.md` runs, then it writes `.writ/state/blast-radius-<story-stem>.json` and passes that file to Gate 3 as `blast_radius`; given the switch prints `off` or the route is `evaluator-agent`, then `blast_radius` is `(none)` and no file is written `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write tests first by extending `scripts/tests/test_change_surface.py`: stem match, path match with and without extension, generic-stem and short-stem path-only match, token boundaries, `.writ/` and changed-file exclusion, test split, cap and `truncated`, no-git walk, non-UTF-8 and >1 MB skip, bad `--repo`, empty `--changed` exit 2, `--pretty` shape, and existing `classify` tests unchanged. Build fixtures in `TemporaryDirectory` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.2 Implement the `blast-radius` subcommand and a new test-like helper in `scripts/change-surface.py` (leave `is_test` and `classify` as they are): build search tokens, list candidates with `git ls-files` or the walk fallback, skip `.writ/`, changed files, files over 1 MB and non-UTF-8 files, split into `consumers` and `tests`, cap at `--limit` (default 20) with `truncated`, print JSON by default and the check shape with `--pretty`; update the module docstring `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.3 Add the "Blast radius" paragraph to the `#### Gate 2.5` section of `commands/implement-story.md`, after the existing `unverifiable` sentence, as drafted in technical-spec § Gate 2.5 Change; record `wc -c commands/implement-story.md` before and after `[AC-3.5]`
- [ ] 3.4 Regenerate trees with `python3 scripts/gen-platform-trees.py`; do not hand-edit generated files `[AC-3.5]`
- [ ] 3.5 Run `uv run --python 3.9 pytest scripts/tests/test_change_surface.py`, `bash scripts/eval.sh --check=change-surface`, and `python3 scripts/gen-platform-trees.py --check`, and confirm all pass `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.6 Verify each acceptance criterion against script output and the Gate 2.5 text `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- The blast radius is a text-reference heuristic, not a call graph. It finds files that mention a changed file. It does not prove they call it.
- Story 4's verifier uses the union of `consumers` to accept the `traced` rung, and accepts `traced: none` only when that union is empty and the verdict is `pass`. Keep the JSON keys (`verdict`, `consumers`, `tests`, `truncated`, `reasons`) exactly as technical-spec § Blast Radius states.
- Generic stems: `index`, `main`, `mod`, `__init__`, `utils`, `util`, `types`, `type`, `constants`, `config`, `helpers`, `readme`, `setup`, `app` (case-insensitive). These and stems under 4 characters match by path only.
- `no_git_walked` is informational and keeps `pass`. Only an unreadable `--repo` gives `unverifiable`.
- The walk fallback skips `.git/`, `node_modules/`, and dot-directories. `.writ/` is always skipped.
- Byte budget: Gate 2.5 and Gate 3 may grow by at most 1,800 bytes net across the whole spec. This story's paragraph should stay well under that so Story 4 has room.
- Edit only the `#### Gate 2.5` section. Do not edit Gate 0 (owned by the design-divergence spec), Gate 3 (Story 4), or Step 4's report-line list.
- Story 1 provides `review-override.py switch`. Story 2 edits Gate 3 of the same command file, so run this story after Story 2 and regenerate trees after rebasing.
- Python 3.9 floor. No `match`, no `X | Y` unions at runtime, no 3.10+ `pathlib` or `str` methods. Use `from __future__ import annotations`.
- Risk: a large repo makes the scan slow. Use one pass over candidates and one compiled pattern per changed file.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`blast-radius` lists candidates (`git ls-files` fails), `blast-radius` reads a candidate (binary, non-UTF-8, or >1 MB), `blast-radius` on a huge repo (slow scan)] — from technical-spec.md § Error & Rescue Map
- **Shadow paths:** [Blast radius] — from technical-spec.md § Shadow Paths
- **Business rules:** [Safety fact applies only when `gate3_route` names `review-agent` and the `safety-fact` switch is on; switches default to on] — from spec.md → Business Rules and → Business Rules (Expanded) → When the safety fact applies
- **Experience:** [Journey steps 1–2 (Gate 2.5 computes `gate3_route`, then runs blast-radius and saves `.writ/state/blast-radius-<story-stem>.json`); State Catalog row "Blast radius unverifiable"] — from spec.md → Experience Design → Journey and → State Catalog

Contracts: technical-spec.md → ## Blast Radius (tokens, candidates, split, cap, JSON and `--pretty` shapes, exit codes) and → ## Gate 2.5 Change (the paragraph to add).
