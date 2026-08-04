# Writ Project Context

> Last Updated: 2026-08-04T21:27:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics to the platform underneath.

## Active Spec

- **Spec:** 2026-08-04-post-merge-archival-hook — Post-Merge Archival Hook
- **Status:** In Progress (2/4 stories complete)
- **Story:** 3 of 4 — Wire the Hook into /release Step 1.3c (Not Started, both dependencies now clear)
- **Progress:** 14/28 tasks complete (50%)

## Artifact Map

- **Product:** .writ/product/roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-08-04-post-merge-archival-hook/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (11 entries)
- **Docs:** .writ/docs/ (19 files)
- **Integrity:** ✅ all required present

## Recent Drift

Story 1 landed with zero drift (a real-repo dogfood run during Task 1.6 surfaced a README.md false-positive in the story-file matching signal, fixed within the same story rather than logged as a spec deviation). Story 2 landed with Overall Drift: Small (2 items, both auto-amended, no re-review needed — see `drift-log.md`): DEV-001 (`ArchiveOneResult` implemented as a plain dict with a `spec` key, matching `scan()`/`sweep()`'s existing convention, rather than the sub-spec's illustrative dataclass with `spec_name`), DEV-002 (the sub-spec's flagged `[UNPLANNED]` ledger-append-after-move atomicity question resolved as a new `archived_unlogged` status — accepted rare-risk, not rolled back).

## Open Issues

Open backlog: 1 file under `.writ/issues/` (features/).
