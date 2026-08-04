# Story 7: Integration Testing & Dogfooding

> **Status:** In Progress 🔄 — Structural validation complete, dogfood scenarios pending
> **Priority:** High
> **Dependencies:** Story 1, Story 2, Story 3, Story 4, Story 5, Story 6 (all previous stories)

## User Story

**As a** Writ developer practicing what I preach
**I want to** validate all Phase 2a features on real Writ development work
**So that** I can confirm the shipping and review workflow works end-to-end before declaring Phase 2a complete

## Acceptance Criteria

- [ ] Given I run `/ship` on a real Writ branch, when the workflow completes, then conventions are detected, tests run, commits are split, and a PR is opened with structured body and labels
- [ ] Given I run `/review` on a real diff, when the review completes, then it produces an error & rescue map, shadow paths, and a failure modes registry with at least one finding
- [ ] Given I run `/retro` on the Writ repo, when the analysis completes, then it collects metrics, detects sessions, integrates Writ context, saves a JSON snapshot, and shows trend comparison if previous data exists
- [ ] Given I run `/review` then `/ship`, when the PR is created, then review findings appear in the PR's Review Notes section
- [ ] Given error mapping tables from `/create-spec` and `/review`, when compared, then they use identical table structures (shared format verified)

## Implementation Tasks

- [x] 7.1 Define the dogfood validation checklist — document the 6 scenarios with measurement criteria; create `.writ/specs/2026-03-15-phase2a-shipping-review/validation-checklist.md`
- [ ] 7.2 Run Scenario 1: `/ship` — ship a real Writ change using the new command; document convention detection results, test execution, commit splitting, and PR quality
- [ ] 7.3 Run Scenario 2: `/review` — review a real diff before shipping; document error & rescue map findings, shadow paths traced, and failure modes identified
- [ ] 7.4 Run Scenario 3: `/retro` — run retrospective on the current Writ development period; document metrics accuracy, session detection, Writ context integration, and JSON snapshot
- [ ] 7.5 Run Scenario 4: Error mapping — create a spec using `/create-spec` for a feature with data flows; verify technical sub-spec includes error mapping sections
- [ ] 7.6 Run Scenario 5: Integration — run `/review` → `/ship` end-to-end; verify review findings propagate to PR Review Notes; verify cross-command format consistency
- [ ] 7.7 Produce Phase 2a validation report — summarize all scenario outcomes, pass/fail, and any issues; write to `.writ/specs/2026-03-15-phase2a-shipping-review/validation-report.md`

## Notes

- This story MUST use real Writ development work, not synthetic examples
- If any scenario fails, document the failure, fix the underlying command, and re-run
- The validation report should be honest — partial passes are acceptable if issues are documented with remediation plans
- Phase 2a is not complete until this story passes

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Validation checklist created and documented
- [ ] All 6 dogfood scenarios executed and documented
- [ ] Phase 2a validation report produced
- [ ] Success criteria from spec verified
- [ ] Phase 2a declared complete (or issues documented for remediation)
