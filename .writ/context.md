# Writ Project Context

> Last Updated: 2026-09-25T16:33:10Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-25-jev-judgment-pilot` — Jev Judgment Pilot
- **Status:** In Progress (2/6 stories Completed ✅)
- **Story:** 2 of 6 — Client Transport and eval Check (Completed ✅)
- **Progress:** 13/40 tasks complete (32%)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present
- **Active spec:** .writ/specs/2026-09-25-jev-judgment-pilot/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (22 entries)
- **Docs:** .writ/docs/ (25 files)
- **Integrity:** ✅ all required present

## Recent Drift

- **DEV-009** Small — Retry schedule is 1 s then 2 s; `retry-after` capped at 30 s
- **DEV-010** Small — `judge()` takes `backend`, `environ`, `transport`, `sleep` and returns a `Judgment`
- **DEV-011** Small — New informational reason `thresholds_missing`

## Open Issues

8 files under `.writ/issues/`.
