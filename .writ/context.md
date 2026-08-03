# Writ Project Context

> Last Updated: 2026-08-03T21:41:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics to the platform underneath.

## Active Spec

- **Spec:** 2026-08-03-deterministic-story-substrate — Deterministic Story Substrate
- **Status:** In Progress
- **Story:** 3 of 4 — Empirically Derived Context Budget and Real Measurement (Completed ✅). Story 4 (Prose Consolidation) next — depends on Story 3.
- **Progress:** 21/28 tasks complete (75%)

## Artifact Map

- **Product:** .writ/product/roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-08-03-deterministic-story-substrate/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (12 entries)
- **Docs:** .writ/docs/ (18 files)
- **Integrity:** ✅ all required present

## Recent Drift

Story 3 landed with Overall Drift: Small (2 items, both logged for traceability only, no spec amendment — see `drift-log.md`): DEV-003 (2× margin on the derived budget constant, compensating for a documented heading-mismatch undercount), DEV-004 (reused `CATEGORY_ORDER` for truncation relevance rather than a purpose-built ranking). Story 3's review agent also returned a procedural FAIL (missing `## What Was Built` section) that was overridden as a misapplication of the pipeline's own Gate 3.5 ordering — all 7 substantive review categories were independently verified clean. Story 2 landed with Overall Drift: Small (2 items, both auto-amended): DEV-001 (extended-reference backtick style vs. a stale doc example, deferred to Story 4), DEV-002 (corrected an inaccurate `>>` arrow claim in the story's own Notes). Story 2 also required one review-fail fix iteration for a Major path-traversal security finding, independently re-verified clean across 4 separate verification passes before landing. Story 1 landed with zero drift.

## Open Issues

Open backlog: 13 files under `.writ/issues/` (bugs/, features/, improvements/).
