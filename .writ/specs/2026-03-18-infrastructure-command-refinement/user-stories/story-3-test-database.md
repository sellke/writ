# Story 3: Refine test-database.md

> **Status:** Not Started
> **Priority:** P1
> **Dependencies:** None
> **Estimated effort:** Small

## User Story

As a Writ maintainer, I want the test-database command refined to A grade so that every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake.

## Acceptance Criteria

- Given the current test-database.md (422 lines), when the litmus test is applied, then every remaining line passes
- Given the refined file, when line count is measured, then it falls within 162–198 lines (~180 target)
- Given the refined file, when capabilities are compared to the original, then zero capabilities are lost
- Given the refined file, when cross-references are checked, then all paths are resolvable

## Implementation Tasks

- [ ] Task 1: Read current test-database.md and catalog every section with line ranges and litmus test verdict
- [ ] Task 2: Cut AI Implementation Prompt, JSON todo block, Future Enhancements, Tool Integration
- [ ] Task 3: Replace verbose status report templates with principles about what to report (layers, fixes, remaining issues, next steps)
- [ ] Task 4: Replace bash pseudocode with diagnostic principles (what to check at each layer, not how to type it)
- [ ] Task 5: Verify multi-layer model, safe/destructive classification, detection targets, and recovery guidance are preserved
- [ ] Task 6: Run litmus test on every remaining section — flag any line that fails all three criteria

## Technical Notes

- The three-layer model (Docker → Prisma → App) is the organizing spine — all diagnostics and reporting follow this structure
- Safe vs destructive classification is the highest-value insight: auto-starting containers is safe, resetting databases is destructive. This boundary prevents data loss.
- Detection targets (what to scan at each layer) encode domain knowledge about where database issues hide
- The reporting principles matter more than report formatting — what information helps the developer vs. what's noise
- Recovery guidance needs to be specific-error-to-specific-fix, not generic "check your database"

## Definition of Done

- [ ] File passes litmus test with zero failures
- [ ] Line count within 162–198 range
- [ ] All capabilities from original preserved
- [ ] Voice and density match A-grade benchmarks
