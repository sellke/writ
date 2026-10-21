# Writ Project Context

> Last Updated: 2026-10-21T15:01:26Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-10-20-shipped-command-hygiene — Shipped Command Hygiene
- **Status:** In Progress
- **Story:** 1 of 3 — Strip Internal References and Add `shipped-refs` (Completed ✅)
- **Progress:** 7/21 tasks complete (33%)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-10-20-shipped-command-hygiene/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (28 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-001 (Small) `shipped-refs` scans every `commands/*.md`, including any `*.lean.md` — shipped-command-hygiene Story 1
- DEV-002 (Small) No `commands/*.md` under `--root` is a run error, not a PASS — shipped-command-hygiene Story 1
- DEV-003 (Small) Story 1 repins `KNOWN_OVER_BUDGET` for five commands — shipped-command-hygiene Story 1

## Open Issues

19 open issue files in .writ/issues/ (30 total; 11 closed with `## Resolution`)
