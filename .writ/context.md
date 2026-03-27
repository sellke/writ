# Writ Project Context

> Last Updated: 2026-03-27

## Product Mission

Writ is an elegant development workflow for AI-assisted software development. It gives solo builders the engineering discipline of a great team — clear steps, firm boundaries, quality gates, and adaptive ceremony that right-sizes process to the work. Methodology-first, platform-agnostic, pure open-source.

## Active Spec

- **Spec:** 2026-03-27-context-engine — Context Engine
- **Status:** Complete
- **Story:** 5 of 5 — all stories completed ✅
- **Progress:** 40/40 tasks complete (100%)

## Recent Drift

#### [DEV-007] Variable naming convention for agent-specific sections
- **Severity:** Small
- **Spec said:** `spec_lite_content["## For Coding Agents"]` array-access style
- **Implementation did:** Used `spec_lite_for_coding`, `spec_lite_for_review`, `spec_lite_for_testing`
- **Resolution:** Auto-amended — descriptive variable names clearer for markdown orchestrator

#### [DEV-006] Product files modified out of scope
- **Severity:** Small
- **Spec said:** Boundary map includes only `.writ/docs/what-was-built-format.md` and `commands/implement-story.md`
- **Implementation did:** Also modified `.writ/product/mission-lite.md`, `mission.md`, `roadmap.md` with Phase 3 documentation
- **Resolution:** Flagged for cleanup — product changes should be in separate commit

#### [DEV-005] Additional verification files created
- **Severity:** Small
- **Spec said:** Task 3.2 — Write tests for WWB generation
- **Implementation did:** Created 5 verification files (3 specified + 2 extra)
- **Resolution:** Auto-amended — positive scope expansion, improves validation thoroughness

## Open Issues

- 2 issues tracked in `.writ/issues/`
