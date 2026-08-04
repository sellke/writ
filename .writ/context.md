# Writ Project Context

> Last Updated: 2026-08-04T21:55:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics to the platform underneath.

## Active Spec

- **Spec:** 2026-08-04-post-merge-archival-hook — Post-Merge Archival Hook
- **Status:** In Progress (3/4 stories complete)
- **Story:** 4 of 4 — Dogfood and Verify (Not Started, dependency clear)
- **Progress:** 22/29 tasks complete (76%)

## Artifact Map

- **Product:** .writ/product/roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-08-04-post-merge-archival-hook/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (11 entries)
- **Docs:** .writ/docs/ (19 files)
- **Integrity:** ✅ all required present

## Recent Drift

Story 3 landed with Overall Drift: Small (1 item, auto-amended — see `drift-log.md`): DEV-003 (SHA-extraction mechanism swapped from `gh`'s built-in `--jq` to an external `jq` pipe, needed to capture four independent JSON fields in one `gh pr list` call; closed with a clarifying note on the external-`jq` dependency, consistent with an existing assumption elsewhere in `release.md`). Story 3's architecture check also returned CAUTION with 5 findings, all folded into the coding agent's task list before implementation (no duplicated eligibility checks, immediate-commit timing to avoid a dangling `git mv` on release cancellation, an additive `gh` JSON-field fix, an executable fixture test instead of a documented matrix, and a one-sentence Phase 2 sequencing note). Story 2 landed with Small drift (2 items, both auto-amended): dict-shaped result, and a new `archived_unlogged` status. Story 1 landed with zero drift.

## Open Issues

Open backlog: 1 file under `.writ/issues/` (features/).
