# Story 5: implement-spec.md Refinement (A- → A)

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** Writ user running /implement-spec
**I want** the pre-flight assessment expressed as principles rather than reimplemented assess-spec logic
**So that** the command stays focused on orchestration without creating maintenance coupling

## Acceptance Criteria

- [x] Given implement-spec.md, when pre-flight assessment (Step 2.3b) is reviewed, then it expresses thresholds as ~5 lines of principles, not 35 lines reimplementing assess-spec checks
- [x] Given implement-spec.md, when failure handling dialogs are reviewed, then they are compressed while preserving all user options
- [x] Given implement-spec.md, when the dependency graph, parallel batching, execution state, and resume support are reviewed, then they are unchanged
- [x] Given the complete file, when line count is checked, then it is approximately 250 lines (±15%)

## Implementation Tasks

- [x] 5.1 Read current implement-spec.md (post Story 1 cleanup) and identify pre-flight boundaries
- [x] 5.2 Rewrite pre-flight from 35 lines to ~5 lines of threshold principles
- [x] 5.3 Compress failure handling dialogs while preserving all user options
- [x] 5.4 Run litmus test on every remaining section
- [x] 5.5 Verify line count is in target range (~250 ±15%)

## Notes

- This is the most well-designed command already — minimal changes needed
- The pre-flight reimplements assess-spec checks 1, 2, 3, and 6 inline. Replace with: "Flag specs with >8 stories, >50 tasks, dependency depth >3, or any story with >7 tasks. Present above execution plan, offer full /assess-spec."
- The orchestration contract table ("Integration with Writ Ecosystem") should be kept — it documents the relationship between commands

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] File passes litmus test on every section
