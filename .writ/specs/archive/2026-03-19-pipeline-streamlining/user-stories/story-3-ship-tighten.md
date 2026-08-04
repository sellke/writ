# Story 3: Tighten /ship — Opt-In Tests, Inline Spec Check

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer using Writ
**I want to** run `/ship` and have it focus purely on getting my branch into a PR — fast, no mandatory test gate
**So that** ship's behavior matches its stated philosophy ("assumes the code is ready") and I opt into verification only when I want it

## Acceptance Criteria

1. **Given** the rewritten `ship.md`, **when** an AI agent executes `/ship` with no flags, **then** tests do NOT run. The pipeline goes: detect conventions, merge default branch, commit intelligence, PR creation.

2. **Given** the `--test` flag is set, **when** `/ship --test` executes, **then** the full test suite runs after merging and before commit intelligence, matching the current Step 3 behavior.

3. **Given** a `.writ/specs/` folder exists with an active spec, **when** PR creation runs, **then** checks 1-3 from verify-spec (story integrity, status consistency, completion integrity) run silently. Issues found are included in the PR body under a "Spec Health" subsection. If clean, the subsection is omitted entirely.

4. **Given** the rewritten file, **when** tests fail during `--test` mode, **then** the "Ship anyway" flow sets `--draft`, adds a `tests-failing` label, and moves on — no multi-paragraph explanation of options.

5. **Given** the rewritten file, **when** reviewing the pipeline diagram, **then** the "RUN TESTS" box is shown as optional (dashed or annotated with `--test`).

## Implementation Tasks

- [x] 3.1 Make tests opt-in — remove Step 3 (Run Tests) as a mandatory pipeline step. Add `--test` flag that re-enables it in the same position (after merge, before commit intelligence). Update the invocation table.

- [x] 3.2 Update pipeline diagram — show the test step as optional. Annotate it with `(--test)` or use dashed lines to indicate it's not part of the default flow.

- [x] 3.3 Simplify test failure handling — when tests fail in `--test` mode, present three options but trim the verbose explanations. "Fix and retry" stays. "Ship anyway" becomes: force `--draft`, add `tests-failing` label, done. "Abort" stays. Remove the multi-paragraph rationale for each option.

- [x] 3.4 Add inline spec health check to PR creation — during Step 5 (PR Creation), if `.writ/specs/` exists with an active spec, silently run checks 1-3 from verify-spec. Add "Spec Health" subsection to PR body template only if issues found. Update the PR body template and population table.

- [x] 3.5 Update ship overview — the overview says "assumes the code is ready (tests pass, review complete)." Remove the "tests pass" parenthetical since ship no longer verifies that by default. Align the overview with the new opt-in philosophy.

- [x] 3.6 Update "When to Use" table — add row for "Want test verification before PR" pointing to `/ship --test`.

## Notes

- **Philosophy alignment:** Ship's overview has always said "assumes the code is ready." Making tests opt-in finally makes the behavior match the words. Tests already ran in implement-story's Gate 4 — ship doesn't need to re-verify unless the merge introduced something.

- **Risk:** Users who relied on ship's implicit test run may be surprised. The `--test` flag is the escape hatch. Consider whether the overview should mention this shift explicitly.

- **Inline spec check scope:** Only checks 1-3 (story integrity, status consistency, completion integrity). Not checks 4-5 or 8. These three catch the most common drift (README out of sync with story files) without slowing down PR creation.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests do not run by default
- [x] `--test` flag re-enables test execution
- [x] Pipeline diagram shows tests as optional
- [x] PR body includes spec health only when issues found
