# Story 5: Cross-Spec Consistency Check

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer creating a new spec
**I want** the contract proposal to warn me if another in-progress spec touches the same domain area
**So that** cross-spec conflicts are caught at planning time instead of at implementation time

## Acceptance Criteria

- [x] Given there are other non-complete specs in `.writ/specs/`, when `/create-spec` reaches Step 1.4 (Contract Proposal), then it scans other specs' `spec-lite.md` files for domain overlap
- [x] Given overlap is detected (e.g., two specs both mention modifying the User model), when the contract is presented, then a `⚠️ Cross-Spec Overlap` section is included with specific overlap details
- [x] Given no overlap is detected, when the contract is presented, then no overlap warning section appears (clean contract)
- [x] Given a spec has status "Complete" in its spec.md, when the cross-spec scan runs, then that spec is excluded from the overlap check

## Implementation Tasks

- [x] 5.1 Read current `commands/create-spec.md` Step 1.4 (Contract Proposal) to understand where the check should be inserted
- [x] 5.2 Add cross-spec scan logic before the contract is presented — list all spec folders, filter out Complete specs, read each spec-lite.md
- [x] 5.3 Define the overlap detection heuristic — keyword extraction from the new contract (models, routes, shared utilities, domain terms) compared against existing spec-lite.md content
- [x] 5.4 Add the `⚠️ Cross-Spec Overlap` section format to the contract template — show which spec overlaps, what domain area, and suggest sequencing or dependency declaration
- [x] 5.5 Verify the check is lightweight — reading spec-lite.md files (small files) and doing keyword matching should add negligible time to the contract step

## Notes

- This is a heuristic, not a guarantee. False positives are acceptable (user can dismiss). False negatives are possible for indirect overlap (e.g., two specs both affecting the same UI page via different models).
- The overlap check only reads `spec-lite.md` files — these are small, condensed files designed for AI context. No need to parse full specs or story files.
- Scoped to `create-spec.md` only. Adding this to `edit-spec.md` is follow-up work.
- Example overlap warning:
  ```
  ⚠️ Cross-Spec Overlap:
  - Spec "2026-03-01-auth-refactor" (In Progress) also modifies the User model (Story 2)
  - Consider sequencing these specs or declaring a dependency
  ```

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/create-spec.md` includes cross-spec scan before contract proposal
- [x] Overlap warning format is clear and actionable
