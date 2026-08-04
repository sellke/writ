# Story 2: Make /release Self-Sufficient with Conditional Gate

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1 (needs to know verify-spec's final scope to avoid duplication)

## User Story

**As a** developer using Writ
**I want to** run `/release` and have it validate everything it needs internally — tests, build, spec metadata — without requiring me to run separate commands first
**So that** releasing is a 2-command flow (`--dry-run` then execute) instead of a 5-command ceremony

## Acceptance Criteria

1. **Given** the rewritten `release.md`, **when** an AI agent executes `/release`, **then** it runs an inline release gate (spec metadata validation + build verification + conditional test suite) before generating the changelog.

2. **Given** HEAD matches the merge commit of the last merged PR, **when** the release gate runs, **then** the test suite is skipped with a message like "Tests skipped — HEAD matches last merged PR (SHA). Build verification still runs."

3. **Given** HEAD does NOT match the last merged PR (intervening commits exist), **when** the release gate runs, **then** the full test suite executes.

4. **Given** the rewritten file, **when** the `--skip-gate` flag is set, **then** the entire release gate (tests, build, spec validation) is skipped.

5. **Given** the rewritten file, **when** reviewing the integration table, **then** there is no reference to `verify-spec --pre-deploy` as a prerequisite. The recommended flow is `/release --dry-run` then `/release`.

6. **Given** the rewritten file, **when** searching for `Trello`, **then** zero matches are found.

## Implementation Tasks

- [x] 2.1 Add Phase 1.5: Release Gate — insert between change analysis (Phase 1.2) and version proposal (Phase 1.4). Contains three sub-steps: spec metadata validation, build verification, conditional test execution.

- [x] 2.2 Implement spec metadata validation — run verify-spec checks 1-5 and 8 inline against completed specs since last release. Auto-fix discrepancies. Report unfixable issues as warnings (don't block release unless critical).

- [x] 2.3 Implement build verification — run typecheck, lint, and format checks. These are fast and always run (even when test suite is skipped). Detect tooling the same way ship detects test runners.

- [x] 2.4 Implement conditional test execution — detect last merged PR's merge commit via `gh pr list --state merged --limit 1 --json mergeCommit`. Compare against HEAD. If match: skip tests, log reason. If no match: run full test suite. If `gh` unavailable: fall back to always running tests.

- [x] 2.5 Add `--skip-gate` flag — bypasses the entire release gate. For use when CI already validated or manual testing was done.

- [x] 2.6 Update dry-run output — `--dry-run` should preview gate results (what would be validated, whether tests would run or be skipped) alongside the existing changelog/version preview.

- [x] 2.7 Replace the 5-command ceremony — update integration table and recommended flow. Remove all references to `verify-spec --pre-deploy` as a prerequisite. New flow: `/release --dry-run` then `/release`.

- [x] 2.8 Remove all Trello references from release.md.

## Notes

- **Key design decision:** Build verification (typecheck/lint/format) always runs even when tests are skipped. These are fast (~5-10 seconds) and catch config drift that tests don't cover.

- **Conditional test heuristic:** The `gh pr list` approach assumes GitHub. For repos without `gh` CLI, fall back to always running tests — better safe than sorry. Don't try to be clever with git-only heuristics.

- **Risk:** The spec metadata validation in the release gate overlaps with standalone `/verify-spec`. This is intentional — release runs the checks inline for self-sufficiency, verify-spec exists as a standalone diagnostic. The checks are the same logic, just invoked differently.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Release gate runs inline without external prerequisites
- [x] Conditional test skip works when HEAD matches last merged PR
- [x] No references to verify-spec --pre-deploy or Trello remain
- [x] Recommended flow is 2 commands, not 5
