# Writ Project Context

> Last Updated: 2026-03-27T22:30:00Z

## Product Mission

Writ is an elegant development workflow for AI-assisted software development. It gives solo builders the engineering discipline of a great team — clear steps, firm boundaries, quality gates, and adaptive ceremony that right-sizes process to the work. Methodology-first, platform-agnostic, pure open-source.

## Active Spec

- **Spec:** 2026-03-27-context-engine — Context Engine
- **Status:** In Progress
- **Story:** 1 of 5 — Per-Story Context Hints (Completed ✅)
- **Progress:** 7/40 tasks complete (17.5%)

## Recent Drift

#### [DEV-002] Story tasks 1.4–1.5 test approach
- **Severity:** Small
- **Spec said:** "Write tests for hint generation logic" and "Test hint parsing in orchestrator"
- **Implementation did:** Documented validation strategy (golden file comparison, manual verification) in context-hint-format.md
- **Resolution:** Auto-amended — markdown system has no test harness, validation strategy is appropriate

#### [DEV-003] Validation checklist vs. dogfood format variety
- **Severity:** Small
- **Spec said:** Golden-file validation should check bracketed lists and exact names where applicable (context-hint-format.md validation checklist)
- **Implementation did:** Dogfood stories mix bracketed lines, extended `spec.md → ## Section` paths, and prose descriptions
- **Resolution:** Auto-amended — updated validation checklist to explicitly allow bracketed AND/OR extended format

#### [DEV-001] Orchestrator ACs vs phased delivery
- **Severity:** Medium
- **Spec said:** Story 1 establishes format and generation; Story 4 implements orchestrator parsing
- **Implementation did:** Format + generation complete; AC2-AC4 documented but not runtime-verifiable until Story 4
- **Resolution:** Flagged for review. Story 1 ACs should be reworded to separate format/generation concerns (Story 1) from orchestrator behavior (Story 4)
