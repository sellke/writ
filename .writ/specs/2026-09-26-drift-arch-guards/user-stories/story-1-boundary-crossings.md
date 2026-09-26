# Story 1: Boundary Crossings Script

> **Status:** Completed ✅
> **Commit:** 7d1d263f389f48fcd87c4feff735d5fa6d54c856
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer relying on the default two-agent story path
**I want to** a mechanical list of the files a story changed outside its boundary map, with a Gate 3 route derived from it
**So that** out-of-scope edits are caught by a script instead of depending on an agent noticing them

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [x] Given `boundary-map.py crossings --map M --changed F…` with every changed file covered by an `owned` entry (exact match or directory prefix) and no `--surface full-stack`, when it runs, then it prints `pass`, `route: evaluator-agent`, no `reason:` lines, and the summary line last, exiting 0 `[AC-1.1]`
- [x] Given changed files covered by `out_of_scope`, by `readable`, or by no entry, when it runs, then it prints `route: review-agent` and one `reason:` line per file (`out_of_scope <path>`, `readable_modified <path>`, `outside_boundary <path>`) in input order, with paths normalized repo-relative `[AC-1.2]`
- [x] Given `--story S` and changed files under S's spec folder, equal to `.writ/context.md`, or under `.writ/state/`, when it runs, then those files are never reported; and given `--surface full-stack`, then the route is `review-agent` with `reason: full_stack_surface` after any crossing lines `[AC-1.3]`
- [x] Given a missing, unreadable, or non-object `--map`, when it runs, then it prints `unverifiable`, `route: review-agent`, `reason: map_unreadable` and exits 0; and given no or empty `--changed`, then it exits 2 `[AC-1.4]`

## Implementation Tasks

- [x] 1.1 Write failing tests in `scripts/tests/test_boundary_map.py` for the owned-only pass, each crossing class, input-order reasons, and path normalization (absolute, `./`, dot-directories) `[AC-1.1, AC-1.2]`
- [x] 1.2 Write failing tests for pipeline-output exclusion with and without `--story`, and for `--surface full-stack` routing and reason order `[AC-1.3]`
- [x] 1.3 Write failing tests for missing / unreadable / non-object map (unverifiable, route review-agent, exit 0) and empty `--changed` (exit 2) `[AC-1.4]`
- [x] 1.4 Add the `crossings` subcommand to `scripts/boundary-map.py` per technical-spec §1, reusing its existing path normalization and spec-folder resolution; update the module docstring `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.5 Verify: `uv run --python 3.9 pytest scripts/tests/test_boundary_map.py` and `bash scripts/tests/test_eval_boundary_map.sh` green `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`

## Notes

`compute` already resolves the spec folder and normalizes paths; `crossings` should share those helpers, not duplicate them. `arch-check.py` has a similar `_covers` prefix rule — match its semantics (entry `dir/` or `dir` covers `dir/x`). A crossing is a routing signal, never `fail`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (2 Route UP on doubt, 3 Triggers, 4 Pipeline outputs)
- **Technical:** sub-specs/technical-spec.md → ## 1
- **Shadow paths:** spec-lite.md → ## For Testing Agents → Shadow Paths

---

## What Was Built

**Implementation Date:** 2026-09-26

### Files Modified

1. **`scripts/boundary-map.py`**
   - New `crossings` subcommand: classifies each changed path as excluded, owned, `out_of_scope`, `readable_modified`, or `outside_boundary`, and prints `pass`/`unverifiable`, a `route:` line, one `reason:` per crossing in first-seen order, then `full_stack_surface`, summary last.
   - Helpers `repo_relative`, `covers` (same prefix rule as `arch-check.py` `_covers`), `load_map`, `excluded_prefixes` (reuses `_spec_dir`), `classify`. `compute` unchanged. [AC-1.1, AC-1.2, AC-1.3, AC-1.4]
2. **`scripts/tests/test_boundary_map.py`** — `CrossingsTests`: 22 new tests, including a `compute` regression guard. [AC-1.1, AC-1.2, AC-1.3, AC-1.4]

### Implementation Decisions

1. A map list that is not a list of strings is `map_unreadable` (DEV-001, route UP on doubt).
2. Changed paths use git-path normalization, not the prose-oriented `normalize_path` (DEV-004).
3. Crossings are de-duplicated in first-seen order; all-blank `--changed` exits 2 (DEV-005).

### Test Results

- `uv run --python 3.9 pytest scripts/tests/test_boundary_map.py`: 40 passed. `test_eval_boundary_map.sh`: 8/8.
- Gate 3 evaluator: PASS, Overall Drift Small. `review-override.py`: `fail dangling_reference` from other specs' test docstrings (`AC-1.5`, `AC-3.5`, `AC-4.5`), a pre-existing ac-trace attribution limitation, not this story; filed as an issue.
