# Story 7: Validation

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Stories 2, 3, 4, 5, 6

## User Story

**As a** Writ maintainer
**I want to** verify that all refinements preserved capability while eliminating waste
**So that** we can ship with confidence that nothing broke

## Acceptance Criteria

- [x] Given all 10 refined files, when line counts are tallied, then total is approximately 2,310 lines (±10%)
- [x] Given each file, when every section is tested against the litmus test (teaches non-obvious / sets quality bar / prevents mistake), then every section in every file passes
- [x] Given all command files, when scanned for references to other commands' sections, then no reference points to a section that was cut
- [x] Given all agent files, when scanned for references to command sections (e.g., "see Gate 3.5"), then all references resolve to existing content
- [x] Given the drift-log format reference in .writ/docs/drift-report-format.md, when compared against the simplified Gate 3.5 guidance, then they are consistent

## Implementation Tasks

- [x] 7.1 Run line count audit on all 10 files and compare against targets
- [x] 7.2 Perform litmus test on every section of every file — document any failures
- [x] 7.3 Scan for cross-reference breakage: search each file for references to other files' sections
- [x] 7.4 Verify drift-report-format.md consistency with simplified Gate 3.5
- [x] 7.5 Estimate context cost: for each agent, calculate approximate token count when prompt template is fully expanded with typical story content
- [x] 7.6 Create validation report summarizing results

## Notes

- The litmus test is the most important check. If a section doesn't teach something non-obvious, set a quality bar, or prevent a specific mistake, it should have been cut in an earlier story.
- Cross-reference breakage is the most likely failure mode — especially between implement-story.md (which references agent files) and the agents (which reference gate numbers and pipeline steps)
- Context cost estimation is informational, not a gate. The goal is awareness: "the review agent prompt fully expanded is approximately N tokens" — so future work can optimize if needed.
- The drift-report-format.md consistency check matters because Gate 3.5 was significantly simplified. If the format doc references procedures that no longer exist in the gate instructions, it creates confusion.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Validation report created at .writ/specs/2026-03-18-core-agrade-refinement/validation-report.md
- [x] No cross-reference breakage found (or issues fixed)
- [x] All 10 files confirmed A-grade
