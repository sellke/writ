# Story 1: /ship — Core Workflow

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer who just finished implementing a feature
**I want to** run a single command that merges main, runs tests, and prepares my branch for PR
**So that** I can ship code without the manual ceremony of merge → test → verify

## Acceptance Criteria

- [x] Given I run `/ship` on a feature branch, when the command starts, then it auto-detects my default branch, test runner, merge strategy, and PR tool without configuration
- [x] Given conventions are detected, when results are shown, then I can verify them and override if wrong before the workflow continues
- [x] Given my branch is behind the default branch, when `/ship` merges, then it fetches origin and merges cleanly or pauses on conflict with clear guidance
- [x] Given tests are detected and run, when they pass, then the workflow continues silently (no confirmation needed)
- [x] Given tests fail, when the failure is reported, then I'm offered "Fix and retry" / "Ship anyway (draft PR)" / "Abort"

## Implementation Tasks

- [x] 1.1 Create `commands/ship.md` with command header, purpose section, and pipeline overview diagram showing the full 5-step workflow (detect → merge → test → commit → PR)
- [x] 1.2 Implement Step 1: Convention Detection — write the detection chain for default branch, test runner, merge strategy, and PR tool with priority-ordered fallbacks and graceful ask-user fallback
- [x] 1.3 Implement Step 2: Merge & Rebase — fetch origin, merge default branch, handle conflict detection with pause and guidance
- [x] 1.4 Implement Step 3: Test Execution — auto-detect and run test command, stream output, handle pass/fail branching with the three-option menu on failure
- [x] 1.5 Write invocation table documenting `/ship`, `/ship --no-split`, `/ship --draft`, `/ship --dry-run` options
- [x] 1.6 Add suggestion to `commands/implement-story.md` at pipeline completion: "Your branch is ready — run `/ship` to merge, test, and open a PR"
- [x] 1.7 Verify the command file is complete, internally consistent, and follows existing Writ command patterns (check `commands/prototype.md` as reference)

## Notes

- Steps 4 (commit intelligence) and 5 (PR creation) are covered in Story 2
- Convention detection is the most fragile part — the detection chain must be priority-ordered with clear fallbacks
- `/ship` should be usable standalone (any branch) or as the natural next step after `/implement-story`
- Follow Design Principle 6: opinionated by default — "I recommend merge (not rebase) because it preserves commit history for bisection. Override with --rebase if you prefer."

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/ship.md` exists with Steps 1-3 fully specified
- [x] `commands/implement-story.md` updated with /ship suggestion
- [x] Command follows existing Writ patterns and Design Principle 6

## What Was Built

**Implemented:** 2026-03-15
**Files:** 1 created, 1 modified

**Key decisions made during implementation:**
- Convention detection chains are priority-ordered with detailed fallback logic (not just "ask user" but specific detection steps per convention)
- Opinionated defaults woven throughout: merge over rebase, fix-and-retry over ship-broken, commit-first over stash
- Uncommitted changes get caught with a recommendation (commit first) rather than silently proceeding
- Steps 4-5 left as clearly-marked stubs for Story 2, with the full pipeline diagram already in place

**Deviations from plan:** None
