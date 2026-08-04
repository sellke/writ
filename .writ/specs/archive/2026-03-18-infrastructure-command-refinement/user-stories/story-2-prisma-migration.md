# Story 2: Refine prisma-migration.md

> **Status:** Not Started
> **Priority:** P1
> **Dependencies:** None
> **Estimated effort:** Medium

## User Story

As a Writ maintainer, I want the prisma-migration command refined to A grade so that every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake.

## Acceptance Criteria

- Given the current prisma-migration.md (667 lines), when the litmus test is applied, then every remaining line passes
- Given the refined file, when line count is measured, then it falls within 234–286 lines (~260 target)
- Given the refined file, when capabilities are compared to the original, then zero capabilities are lost
- Given the refined file, when cross-references are checked, then all paths are resolvable

## Implementation Tasks

- [ ] Task 1: Read current prisma-migration.md and catalog every section with line ranges and litmus test verdict
- [ ] Task 2: Cut dialog box mockups — replace with principles about when to warn and what information to include in warnings
- [ ] Task 3: Cut JSON todo block, Future Enhancements, Integration Notes, Best Practices naming section
- [ ] Task 4: Replace verbose bash examples with decision logic principles (when to run what, not the syntax)
- [ ] Task 5: Compress error scenarios from scripted dialogs to principle-based guidance (what to detect → what to recommend)
- [ ] Task 6: Verify setup detection heuristics, safety check matrix, dev/prod branching, and deployment options are preserved
- [ ] Task 7: Run litmus test on every remaining section — flag any line that fails all three criteria

## Technical Notes

- The 4-check safety framework is the command's organizing spine — compress presentation, not substance
- Setup detection (db push vs migrate, single vs dev/prod) is genuinely non-obvious — the AI wouldn't compose this unprompted
- Dev/prod separation guidance is high-value for developers on shared databases (like Neon)
- Deployment branching (now/later/checklist) with risk-level awareness is a quality bar the AI wouldn't set alone
- Error scenarios need principles not scripts: "when drift is detected, explain what caused it and offer three resolution paths"

## Definition of Done

- [ ] File passes litmus test with zero failures
- [ ] Line count within 234–286 range
- [ ] All capabilities from original preserved
- [ ] Voice and density match A-grade benchmarks
