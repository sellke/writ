# Story 4: Living Spec Auto-Amendment

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ pipeline operator
**I want** Small drift deviations to automatically update spec-lite.md with the proposed amendment
**So that** specs become progressively more accurate over time without manual intervention

## Acceptance Criteria

- [x] Given the review agent classifies a deviation as Small with a proposed spec amendment, when Gate 3.5 processes it, then the amendment is applied to `spec-lite.md` in addition to being logged in `drift-log.md`
- [x] Given a Medium or Large deviation is detected, when Gate 3.5 processes it, then `spec-lite.md` is NOT modified (existing behavior unchanged)
- [x] Given a Small deviation's amendment is applied to spec-lite.md, when the drift-log entry is written, then it includes `Spec-lite updated: Yes` as an additional field
- [x] Given multiple Small deviations in one story, when Gate 3.5 processes them, then all amendments are applied to spec-lite.md in a single read-modify-write cycle

## Implementation Tasks

- [x] 4.1 Read current `commands/implement-story.md` Gate 3.5 section — understand the existing Small deviation flow
- [x] 4.2 Add spec-lite.md update logic to the "On `Overall Drift: Small`" handling — read spec-lite.md, apply amendment text, write updated file
- [x] 4.3 Add the `Spec-lite updated: Yes` field to the drift-log entry format for Small deviations that trigger an update
- [x] 4.4 Handle the mixed-severity case — if a run has both Small and Medium deviations, the Small ones still get their spec-lite amendments applied (Medium ones don't)
- [x] 4.5 Verify the amendment application is safe — the proposed amendment text from the review agent is a plain text description of what to change, not a surgical diff. The orchestrator must interpret it and make the appropriate edit to spec-lite.md.

## Notes

- This builds directly on Phase 1's spec-healing infrastructure (Story 2: Spec-Healing Review Agent Extension, Story 3: Drift Report Format).
- The amendment text comes from the review agent's drift report: `**Spec amendment:** [proposed text]`. For Small deviations, this is typically something like "Update spec to reference `validateRegistrationData` instead of `validateUserInput`."
- The orchestrator needs to be smart about applying the amendment — it's a text description, not a regex. The simplest approach: find the relevant section in spec-lite.md and make the described substitution.
- Only touches `commands/implement-story.md` Gate 3.5 section.
- `spec.md` (the full spec) is never auto-modified — only `spec-lite.md` (the AI context summary).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/implement-story.md` Gate 3.5 auto-applies Small amendments to spec-lite.md
- [x] Drift-log entries for auto-amended deviations include `Spec-lite updated: Yes`
- [x] Medium and Large deviation handling is unchanged
