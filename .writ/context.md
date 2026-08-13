# Writ Context

> Last Updated: 2026-08-13T03:52:00+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-08-12-machine-evaluable-exit-criteria` — Machine-Evaluable Exit Criteria
- **Status:** All 6 stories complete; shipped in v0.31.0; not yet archived
- **Story:** 6 of 6 — Adapter Wiring (Completed ✅)
- **Progress:** 6/6 stories complete (100%)

## Artifact Map

| Artifact | Path | Present |
|---|---|---|
| Product mission | `.writ/product/mission.md` | yes |
| Roadmap | `.writ/product/roadmap.md` | yes |
| Active spec | `.writ/specs/2026-08-12-machine-evaluable-exit-criteria/` | yes — spec.md, spec-lite.md, sub-specs/, user-stories/ |
| Knowledge ledger | `.writ/knowledge/` | yes (26 entries) |
| Decision records | `.writ/decision-records/` | yes |
| Docs | `.writ/docs/` | yes (21 files) |
| Issues | `.writ/issues/` | yes |

**Integrity:** ✅ all required present. Optional artifacts absent are reported, not fatal.

## Recent Drift

No `drift-log.md` for `2026-08-12-machine-evaluable-exit-criteria` — all drift was inline, documentation-level corrections recorded in each story's What Was Built rather than a standalone log (Stories 1, 3, 6 — Small; Story 4's drift-detection gate independently verified twice). See the spec's own story files for detail.

## Open Issues

4 files under `.writ/issues/` — unchanged this run; not investigated as part of this release.

## Release

**v0.31.0 tagged 2026-08-13.** Both `2026-08-12-machine-evaluable-exit-criteria` and `2026-08-12-recalibrate-implement-loop` shipped via PR #43 (merged `d269228`). `/release`'s post-merge archival hook auto-archived `2026-08-12-recalibrate-implement-loop` (resolved unambiguously from commit bodies); `2026-08-12-machine-evaluable-exit-criteria` wasn't resolved by the same hook (its commits didn't carry an unambiguous spec-path reference the resolver could match) and remains un-archived — a known, disclosed limitation of the resolver's single-match behavior, not a defect requiring action here.
