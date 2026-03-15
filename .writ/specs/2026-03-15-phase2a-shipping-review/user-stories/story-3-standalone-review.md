# Story 3: Standalone `/review` Command

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer about to ship code
**I want to** run a deep review that identifies failure modes, shadow paths, and interaction edge cases
**So that** I catch production-breaking issues that the pipeline's standard review misses

## Acceptance Criteria

- [x] Given I run `/review` on a branch with data flow changes, when the review completes, then it produces an error & rescue map showing every method that can fail, how it's rescued, whether it's tested, and what the user sees
- [x] Given the review finds a method with no rescue, no test, and silent failure, when it reports findings, then it flags this as a CRITICAL gap in the failure modes registry
- [x] Given the diff includes user-facing features, when shadow path tracing runs, then it traces happy, nil input, empty input, and upstream error paths for each critical flow
- [x] Given the diff includes interactive UI, when interaction edge cases are checked, then it evaluates double-click, navigate-away, stale state, and back button scenarios
- [x] Given I run `/review` before `/ship`, when `/ship` creates the PR, then review findings are included in the PR's "Review Notes" section

## Implementation Tasks

- [x] 3.1 Create `commands/review.md` with command header, purpose section, and design philosophy explaining how it differs from the pipeline review agent (deeper, independent, judgment-focused)
- [x] 3.2 Implement the Error & Rescue Map technique — instructions for the AI to scan every method/function in the diff that can fail, producing the table with Method | What Fails | Exception Class | Rescued? | Test? | User Sees columns, with critical gap detection logic
- [x] 3.3 Implement Shadow Path Tracing — instructions to identify critical data flows and trace 4 paths (happy, nil, empty, upstream error) with a findings table
- [x] 3.4 Implement Interaction Edge Cases — checklist for user-facing features covering double-click, navigate-away, stale state, back button, and other common interaction failures
- [x] 3.5 Implement Failure Modes Registry — aggregated view of all findings from techniques 1-3, with ID, Category, Severity, Description, Status; plus mandatory ASCII architecture diagram for non-trivial flows
- [x] 3.6 Write invocation table and output format — document all flags (--diff, --file, --spec), structured markdown report format, and integration with `/ship` (review notes passthrough)
- [x] 3.7 Verify command is complete, follows Writ patterns, and embodies Design Principle 6 (opinionated — "The critical gap is X" not just "Here are findings")

## Notes

- `/review` is not a replacement for the pipeline review agent — it's a complementary deeper analysis
- The error & rescue map format is shared with the error mapping in `/create-spec` (Feature 4) — same table structure
- The AI should prioritize judgment over completeness — better to deeply analyze 3 critical paths than superficially scan 20
- Integration with `/ship` is output-based: `/review` writes a report, `/ship` reads it if present

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/review.md` exists with all 5 review techniques specified
- [x] Invocation options and output format documented
- [x] Command follows existing Writ patterns and Design Principle 6
- [x] Error & rescue map format matches the format used in error mapping story (Story 6)

## What Was Built

**Implemented:** 2026-03-15
**Files:** 1 created

**Key decisions made during implementation:**
- Diff scan (Step 2) is a separate step that builds a mental model before applying techniques — categorize files, identify trust boundaries, map external dependencies, note absences
- Critical gap detection uses a severity matrix derived from the rightmost table columns (Rescued × Test × User Sees) rather than subjective judgment
- Architecture diagrams annotated with failure mode registry IDs (FM-001, etc.) to create visual traceability
- Recommendation section explicitly leads with "The critical gap is X because Y" — judgment, not a neutral findings dump
- Review report saved to `.writ/state/review-[branch-name].md` for `/ship` integration (output-based coupling, no tight dependency)

**Deviations from plan:** None
