# Story 1: Refine migrate.md

> **Status:** Not Started
> **Priority:** P1
> **Dependencies:** None
> **Estimated effort:** Small

## User Story

As a Writ maintainer, I want the migrate command refined to A grade so that every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake.

## Acceptance Criteria

- Given the current migrate.md (371 lines), when the litmus test is applied, then every remaining line passes (teaches non-obvious / quality bar / prevents mistake)
- Given the refined file, when line count is measured, then it falls within 144–176 lines (~160 target)
- Given the refined file, when capabilities are compared to the original, then zero capabilities are lost
- Given the refined file, when cross-references are checked, then all paths are resolvable

## Implementation Tasks

- [ ] Task 1: Read current migrate.md and catalog every section with line ranges and litmus test verdict
- [ ] Task 2: Cut Phase 2 bash scripts — replace with principles about what to rename, what to verify, what order matters
- [ ] Task 3: Cut one-liner migration script and FAQ entries that restate spec behavior; keep FAQs that prevent real confusion
- [ ] Task 4: Compress install commands to what/where principles, not cp syntax
- [ ] Task 5: Verify what-changes/what-doesn't tables, modes table, integrity verification, and rollback are preserved
- [ ] Task 6: Run litmus test on every remaining section — flag any line that fails all three criteria

## Technical Notes

- The what-changes/what-doesn't tables are the command's contract — they tell the user exactly what will and won't be touched
- Integrity verification (count-before vs count-after) is genuinely non-obvious — most migration scripts skip this
- Rollback is only 3 lines but essential safety
- This is a one-time migration tool, not a recurring workflow — brevity matters even more since users run it once

## Definition of Done

- [ ] File passes litmus test with zero failures
- [ ] Line count within 144–176 range
- [ ] All capabilities from original preserved
- [ ] Voice and density match A-grade benchmarks (assess-spec.md, edit-spec.md)
