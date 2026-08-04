# Story 2: /ship — PR Creation & Commit Intelligence

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1 (/ship core workflow)

## User Story

**As a** developer with a tested branch ready to ship
**I want to** have my commits organized into a bisectable history and a PR opened with a structured description
**So that** reviewers get clean context and the git history supports future debugging

## Acceptance Criteria

- [x] Given I run `/ship` on a branch with mixed changes (config + logic + tests), when commit splitting runs, then changes are organized into logical bisectable commits (infra → logic → tests)
- [x] Given a small single-file change, when commit splitting evaluates, then it skips splitting and ships the commit as-is
- [x] Given all tests pass and no medium/large drift exists, when PR is created, then it's marked "Ready for review" with a structured body including Summary, Changes, Spec Reference, Test Results, and Drift Report
- [x] Given test warnings or medium drift exist, when PR is created, then it's opened as a Draft PR with notes explaining why
- [x] Given the PR is created, when I check the labels, then they're auto-applied based on file types changed (infra, feature, fix, refactor, docs)

## Implementation Tasks

- [x] 2.1 Implement Step 4: Commit Intelligence — add the splitting heuristic to `commands/ship.md`: analyze diff by file type and change domain, group into logical commits, generate conventional commit messages with spec/story references
- [x] 2.2 Define the split/no-split decision logic: single-file bypass, <50 lines bypass, tight-coupling detection, and document the heuristic clearly for the AI agent
- [x] 2.3 Implement Step 5: PR Creation — structured body template (Summary, Changes, Spec Reference, Test Results, Drift Report, Review Notes), auto-label logic based on file types, draft/ready determination
- [x] 2.4 Add the completion output format showing branch, commits, PR URL, and labels
- [x] 2.5 Document the `--no-split` flag behavior (skip Step 4) and `--draft` flag behavior (force draft regardless of status)
- [x] 2.6 Add `--dry-run` mode that shows what would happen (planned commits, PR body preview) without executing
- [x] 2.7 Verify Steps 4 and 5 compose cleanly with Steps 1-3 from Story 1, and the complete command file is internally consistent

## Notes

- Commit splitting is "best effort" — the heuristic should err on the side of NOT splitting when unsure (broken intermediate states are worse than a fat commit)
- The PR body template should work even without Writ spec context (for projects not using the full pipeline)
- Auto-labeling should be additive (multiple labels if applicable), not exclusive
- Follow Design Principle 6: lead with recommendations — "I recommend splitting these into 3 commits because it makes bisection possible. Use --no-split to ship as a single commit."

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/ship.md` is complete with all 5 steps
- [x] Commit splitting heuristic is clear and documented
- [x] PR body template handles both Writ-pipeline and standalone usage
- [x] All flags documented: --no-split, --draft, --dry-run

## What Was Built

**Implemented:** 2026-03-15
**Files:** 0 created, 1 modified (commands/ship.md — added Steps 4-5)

**Key decisions made during implementation:**
- Commit splitting presents a plan before executing ("I recommend splitting into 3 commits because...") — user can see and override before any git commands run
- Each intermediate commit must build and pass tests — if splitting would create a broken state, the commits are merged. Safety over aesthetics.
- PR body template works both with and without Writ context (spec reference, drift report, review notes all have clear "not available" fallbacks)
- Auto-labeling is additive (multiple labels per PR) not exclusive — a feature + infra change gets both labels
- Draft/ready determination is codified in a truth table, not left to judgment: tests pass + no medium drift = Ready, anything else = Draft
- Dry-run output now covers all 5 steps with preview data

**Deviations from plan:** None
