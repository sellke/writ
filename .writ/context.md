# Writ Project Context

> Last Updated: 2026-09-09T00:20:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-08-phase11-stage3-spec-analysis` — Phase 11 Stage 3 (Goal Card `.writ/issues/goals/2026-09-05-writ-contract-and-verifier-layer.md`)
- **Status:** In Progress — Story 1 Completed ✅
- **Story:** 1 of 3 — CLI + schema (Completed ✅)
- **Progress:** 7/20 tasks complete (35%)

`scripts/spec-analyze.py` lands. Command hooks and eval/precision are Stories 2–3.

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md, `2026-09-05-goldilocks-assessment.md` present
- **Active spec:** .writ/specs/2026-09-08-phase11-stage3-spec-analysis/ — spec.md + spec-lite.md, user-stories/, sub-specs/
- **Knowledge:** .writ/knowledge/ (21 entries)
- **Docs:** .writ/docs/ (25 files)
- **Integrity:** ✅ all required present

## Open Issues

7 files under `.writ/issues/` — 1 goal, 5 improvements, 1 feature.

## Verification State

2026-09-08, Story 1 closeout:

- `uv run --python 3.9 pytest scripts/tests/test_spec_analyze.py` — 14 passed
- Typecheck: skipped, none configured
