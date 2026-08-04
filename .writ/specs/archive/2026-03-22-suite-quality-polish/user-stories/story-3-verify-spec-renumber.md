# Story 3: Renumber `/verify-spec` Checks

> **Status:** Completed ✅ (2026-03-22)
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** Writ user reading verify-spec output
**I want to** see sequential check numbers (1-7) without confusing gaps
**So that** the numbering makes sense and I can reference checks unambiguously

## Acceptance Criteria

- [x] Given the verify-spec command, when I read the check headings, then they are numbered sequentially 1-7 with no gaps
- [x] Given the verify-spec report output example, when I read the table, then it shows checks 1-7 (not 1-5, 8, 9)
- [x] Given the `/ship` command, when I search for verify-spec check references, then they reference the correct new numbers
- [x] Given the `/release` command, when I search for verify-spec check references, then they reference the correct new numbers

## Implementation Tasks

- [x] 3.1 In `commands/verify-spec.md`, renumber Check 8 → Check 6 and Check 9 → Check 7 in all section headings, body text, and references throughout the file
- [x] 3.2 Update the Phase 2 intro text ("Run checks 1–5, 8, and 9" → "Run checks 1–7")
- [x] 3.3 Update the Phase 3 report table and all output examples to show checks 1-7
- [x] 3.4 Update Phase 4 auto-fix references (Check 9 → Check 7)
- [x] 3.5 Update cross-references in `commands/ship.md` — search for "checks 1–3" or "1-3" (these reference verify-spec checks and should remain as "1-3" since those numbers didn't change)
- [x] 3.6 Update cross-references in `commands/release.md` — "checks 1–5 and 8" → "checks 1–6"
- [x] 3.7 Scan all other command files for references to verify-spec check numbers and update as needed

## Notes

- The old checks 6 and 7 were removed at some point but numbering was never cleaned up
- Checks 1-5 keep their numbers. Only 8→6 and 9→7 change.
- `/ship` references "checks 1-3" inline — those numbers didn't change, but verify the reference is still accurate
- `/release` references "checks 1-5 and 8" — the "8" needs to become "6"

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] No references to old check numbers remain in any command file
