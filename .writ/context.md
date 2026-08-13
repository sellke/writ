# Writ Project Context

> Last Updated: 2026-08-13T21:35:00+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-08-13-acceptance-criteria-traceability-ids — Per-Criterion Traceability IDs and an Orphan Check
- **Status:** In Progress (all 4 stories complete; one disclosed spec-contract exception open)
- **Story:** 4 of 4 complete — Story 2's AC-2.5 disclosed as an open, accepted exception (DEV-4)
- **Progress:** 28/28 tasks complete (100%); 16/17 acceptance criteria literally met

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-08-13-acceptance-criteria-traceability-ids/ — spec.md, spec-lite.md, user-stories/, sub-specs/
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (22 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-5] Task 3.6 reinterpreted as static assertions + worked examples (Story 3) — Small, accepted
- [DEV-4] AC-2.5's literal "exits 0" not satisfied by a live dogfood run (Story 2) — disclosed, still open. Wiring the checker into `/verify-spec` (Story 3) means `/verify-spec` on this spec folder now correctly reports Check 3 failing. Spec owner decision needed: amend AC-2.5's wording or record an accepted exception.
- [DEV-3] Task 4.1 reinterpreted as a golden-fixture test file (Story 4) — Small, accepted
- [DEV-2] `scripts/tests/test_governor_enforcement.py` byte-budget disclosure (Story 1) — Small, accepted
- [DEV-1] Step 2.6b addition to `create-spec.md` (Story 1) — Small, accepted

## Open Issues

5 files under `.writ/issues/` — unchanged this run; not investigated as part of this implementation.
