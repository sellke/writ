# Story 4: implement-story.md Refinement (B → A)

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user running /implement-story
**I want** the drift handling to be expressed as principles rather than procedures
**So that** the AI uses judgment instead of following a rigid script, while preserving the three-tier safety model

## Acceptance Criteria

- [x] Given implement-story.md, when the pipeline structure (gate model, change surface classification, quick mode, "What Was Built" record) is reviewed, then it is structurally preserved
- [x] Given implement-story.md Gate 3.5, when drift response is reviewed, then it expresses the three-tier model (Small/Medium/Large) as ~40 lines of principles, not 117 lines of procedures
- [x] Given Gate 3.5, when searched for atomic write procedure, DEV-ID continuation numbering, or exact drift-log markdown format, then none are found — replaced by one example and principles
- [x] Given Gate 3.5, when spec-lite auto-amendment is described, then it includes an explicit requirement to log all changes visibly in the pipeline summary
- [x] Given implement-story.md, when the commit section is reviewed, then it uses a principle ("descriptive message including story title, file counts, test results, drift status") not a prescriptive format
- [x] Given implement-story.md, when searched for "Deprecation Note", then it no longer exists
- [x] Given the complete file, when line count is checked, then it is approximately 320 lines (±15%)

## Implementation Tasks

- [x] 4.1 Read current implement-story.md (post Story 1 cleanup) and map Gate 3.5 boundaries
- [x] 4.2 Rewrite Gate 3.5 drift response: express Small/Medium/Large as principles with one drift-log example
- [x] 4.3 Add explicit spec-lite mutation visibility requirement: "Always include spec-lite changes in pipeline summary"
- [x] 4.4 Simplify commit section from prescriptive format to principle
- [x] 4.5 Remove deprecation note
- [x] 4.6 Run litmus test on every remaining section
- [x] 4.7 Verify line count is in target range (~320 ±15%)

## Notes

- Gate 3.5 rewrite is the highest-risk change in the entire spec. The drift severity model is genuinely valuable — the risk is in losing edge case coverage. Mitigations: keep the severity classification table from the review agent (that's where classification lives), keep one complete drift-log entry example, and keep the principle "overall drift = highest severity present."
- The spec-lite auto-mutation visibility requirement is NEW — it addresses a real corruption risk where the current version silently modifies spec-lite.md without logging what changed.
- Change surface classification (Gate 2.5) is smart and well-sized — don't touch it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] File passes litmus test on every section
