# Story 6: Error Mapping Enhancement in `/create-spec`

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer creating a feature specification
**I want to** have failure modes, shadow paths, and interaction edge cases documented during planning
**So that** critical error handling gaps are identified before code is written, not after

## Acceptance Criteria

- [x] Given I create a spec for a feature with API routes, when the technical sub-spec is generated, then it includes an Error & Rescue Map with all operations that can fail and their planned handling
- [x] Given an operation has no planned error handling, when the error map is generated, then it shows [UNPLANNED] as a visible gap marker that must be addressed
- [x] Given the spec involves critical data flows, when shadow paths are generated, then each flow documents planned behavior for happy, nil input, empty input, and upstream error paths
- [x] Given the spec involves user-facing interactive features, when edge cases are generated, then it includes planned handling for double-click, navigate-away, stale state, and back button scenarios
- [x] Given the error mapping tables are generated, when compared to `/review` output format, then they use identical table structures (shared format)

## Implementation Tasks

- [x] 6.1 Add the Error & Rescue Map section template to `commands/create-spec.md` in Step 2.8 (Technical Sub-Specs) — Operation | What Can Fail | Planned Handling | Test Strategy, with [UNPLANNED] marker logic
- [x] 6.2 Add the Shadow Paths section template — Flow | Happy Path | Nil Input | Empty Input | Upstream Error, with instructions for the AI to trace each critical data flow
- [x] 6.3 Add the Interaction Edge Cases section template — Edge Case | Planned Handling, covering the standard set (double-click, navigate-away, stale state, back button) plus feature-specific cases
- [x] 6.4 Add scope detection logic — instructions for determining when error mapping is required (API routes, auth, payments, file ops, external integrations) vs optional (pure UI, docs, config, refactors)
- [x] 6.5 Document the shared format principle — add a note that these tables match `/review`'s output format, enabling plan-vs-actual comparison during code review
- [x] 6.6 Verify changes compose cleanly with existing `/create-spec` flow and cross-spec consistency check (from Pipeline Quality Improvements spec)

## Notes

- The error mapping tables are a PLANNING tool, not an exhaustive analysis — they capture what the spec author knows at planning time
- [UNPLANNED] markers are the highest-value output: they force explicit decisions about error handling before coding begins
- Scope detection should be generous — when in doubt, include error mapping (it's cheap to plan, expensive to miss)
- This is the planning-phase counterpart to `/review`'s implementation-phase analysis: same format, different context

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/create-spec.md` updated with error mapping sections in Step 2.8
- [x] Scope detection logic documented
- [x] Table formats match `/review` command format (Story 3)
- [x] [UNPLANNED] marker logic is clear and actionable

## What Was Built

**Implemented:** 2026-03-15
**Files:** 0 created, 1 modified

**Key decisions made during implementation:**
- Error mapping sections added directly after the cross-reference integration paragraph in Step 2.8, maintaining the existing flow
- `[UNPLANNED]` markers must be resolved before implementation: either add a handling plan or explicitly mark `[OUT OF SCOPE — reason]`
- Shadow path cells describe what the *user sees*, not internal system behavior ("Error page with retry button" not "500 error")
- Shared format principle documented with explicit plan-vs-actual comparison explanation
- Scope detection errs on the side of inclusion — cheap to plan, expensive to miss

**Deviations from plan:** None
