# Story 1: Boundary Crossings Script

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer relying on the default two-agent story path
**I want to** a mechanical list of the files a story changed outside its boundary map, with a Gate 3 route derived from it
**So that** out-of-scope edits are caught by a script instead of depending on an agent noticing them

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [ ] Given `boundary-map.py crossings --map M --changed F…` with every changed file covered by an `owned` entry (exact match or directory prefix) and no `--surface full-stack`, when it runs, then it prints `pass`, `route: evaluator-agent`, no `reason:` lines, and the summary line last, exiting 0 `[AC-1.1]`
- [ ] Given changed files covered by `out_of_scope`, by `readable`, or by no entry, when it runs, then it prints `route: review-agent` and one `reason:` line per file (`out_of_scope <path>`, `readable_modified <path>`, `outside_boundary <path>`) in input order, with paths normalized repo-relative `[AC-1.2]`
- [ ] Given `--story S` and changed files under S's spec folder, equal to `.writ/context.md`, or under `.writ/state/`, when it runs, then those files are never reported; and given `--surface full-stack`, then the route is `review-agent` with `reason: full_stack_surface` after any crossing lines `[AC-1.3]`
- [ ] Given a missing, unreadable, or non-object `--map`, when it runs, then it prints `unverifiable`, `route: review-agent`, `reason: map_unreadable` and exits 0; and given no or empty `--changed`, then it exits 2 `[AC-1.4]`

## Implementation Tasks

- [ ] 1.1 Write failing tests in `scripts/tests/test_boundary_map.py` for the owned-only pass, each crossing class, input-order reasons, and path normalization (absolute, `./`, dot-directories) `[AC-1.1, AC-1.2]`
- [ ] 1.2 Write failing tests for pipeline-output exclusion with and without `--story`, and for `--surface full-stack` routing and reason order `[AC-1.3]`
- [ ] 1.3 Write failing tests for missing / unreadable / non-object map (unverifiable, route review-agent, exit 0) and empty `--changed` (exit 2) `[AC-1.4]`
- [ ] 1.4 Add the `crossings` subcommand to `scripts/boundary-map.py` per technical-spec §1, reusing its existing path normalization and spec-folder resolution; update the module docstring `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.5 Verify: `uv run --python 3.9 pytest scripts/tests/test_boundary_map.py` and `bash scripts/tests/test_eval_boundary_map.sh` green `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`

## Notes

`compute` already resolves the spec folder and normalizes paths; `crossings` should share those helpers, not duplicate them. `arch-check.py` has a similar `_covers` prefix rule — match its semantics (entry `dir/` or `dir` covers `dir/x`). A crossing is a routing signal, never `fail`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (2 Route UP on doubt, 3 Triggers, 4 Pipeline outputs)
- **Technical:** sub-specs/technical-spec.md → ## 1
- **Shadow paths:** spec-lite.md → ## For Testing Agents → Shadow Paths
