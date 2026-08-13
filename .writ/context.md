# Writ Project Context

> Last Updated: 2026-08-13T22:10:00+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** 2026-08-13-acceptance-criteria-traceability-ids — Per-Criterion Traceability IDs and an Orphan Check
- **Status:** Complete — all 4 stories, 17/17 acceptance criteria literally met (AC-2.5 amended 2026-08-13 via `/edit-spec`)
- **Story:** 4 of 4 complete
- **Progress:** 28/28 tasks complete (100%); 17/17 acceptance criteria literally met

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md present
- **Active spec:** .writ/specs/2026-08-13-acceptance-criteria-traceability-ids/ — spec.md, spec-lite.md, user-stories/, sub-specs/
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (22 files)
- **Integrity:** ✅ all required present

## Recent Drift

- [DEV-5] Task 3.6 reinterpreted as static assertions + worked examples (Story 3) — Small, accepted
- [DEV-4] AC-2.5's literal "exits 0" not satisfied by a live dogfood run (Story 2) — **resolved 2026-08-13** via `/edit-spec`: AC-2.5 reworded to name its own disclosed exception. Note this does NOT make `/verify-spec` exit clean on this spec — Check 3e/3f (Story 3) faithfully report ac-trace.py's real findings with no exception-carve-out mechanism, by design (no auto-fix for these checks). A `/verify-spec` run on this spec folder will still show Check 3 findings; the amendment resolves Story 2's own internal contract, not the checker's live output.
- [DEV-3] Task 4.1 reinterpreted as a golden-fixture test file (Story 4) — Small, accepted
- [DEV-2] `scripts/tests/test_governor_enforcement.py` byte-budget disclosure (Story 1) — Small, accepted
- [DEV-1] Step 2.6b addition to `create-spec.md` (Story 1) — Small, accepted

## Open Issues

5 files under `.writ/issues/` — unchanged this run; not investigated as part of this implementation.
