# Story 1: Cross-Cutting Cleanup

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ developer refining core commands
**I want to** remove redundant and non-functional sections from all 10 files
**So that** the subsequent per-file rewrites start from a clean baseline

## Acceptance Criteria

- [x] Given any command or agent file in scope, when searched for `SwitchMode`, then zero matches are found — replaced with natural guidance like "This discovery phase works best in Plan Mode"
- [x] Given plan-product.md, when the "Key Improvements Over Basic Product Planning" section (lines 527-561) is searched for, then it no longer exists
- [x] Given plan-product.md, when the "Tool Integration" section (lines 563-576) is searched for, then it no longer exists
- [x] Given plan-product.md, when the "Integration with Writ Ecosystem" section (lines 577-593) is searched for, then it no longer exists
- [x] Given plan-product.md, when the "Best Practices" section (lines 594-623) is searched for, then it no longer exists
- [x] Given create-spec.md, when the "Key Improvements Over Original" section (lines 657-683) is searched for, then it no longer exists
- [x] Given create-spec.md, when the "User Stories Best Practices" section (lines 580-613) is searched for, then it no longer exists

## Implementation Tasks

- [x] 1.1 Audit all 10 files for SwitchMode references and replace with natural mode guidance
- [x] 1.2 Remove "Key Improvements" sections from plan-product.md and create-spec.md
- [x] 1.3 Remove "Tool Integration" section from plan-product.md
- [x] 1.4 Remove "Integration with Writ Ecosystem" from plan-product.md (keep the table in implement-spec.md — it documents the orchestration contract)
- [x] 1.5 Remove "Best Practices" section from plan-product.md
- [x] 1.6 Remove "User Stories Best Practices" section from create-spec.md
- [x] 1.7 Verify no broken internal cross-references after removals

## Notes

- This is mechanical cleanup — no judgment calls about what to keep or cut within sections
- SwitchMode replacement text should be brief: "This phase works best in Plan Mode" or similar
- The implement-spec.md "Integration with Writ Ecosystem" table is an exception — it documents the orchestration contract between commands and should be kept
- Run this story first — all other stories depend on starting from the cleaned baseline

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] No broken cross-references between files
