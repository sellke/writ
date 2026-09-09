# Writ Project Context

> Last Updated: 2026-09-09T00:26:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-09-08-phase11-stage3-spec-analysis` — Phase 11 Stage 3: Spec Analysis
- **Status:** In Progress
- **Story:** 3 of 3 — Eval Check + Precision Record on Labeled Fixtures (Completed ✅)
- **Progress:** 20/20 tasks complete (100%)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md, decisions.md present
- **Active spec:** .writ/specs/2026-09-08-phase11-stage3-spec-analysis/ — spec.md + spec-lite.md, user-stories/, sub-specs/
- **Knowledge:** .writ/knowledge/ (5 entries)
- **Docs:** .writ/docs/ (25 files)
- **Integrity:** ✅ all required present

## Open Issues

7 files under `.writ/issues/` — 1 goal, 5 improvements, 1 feature.

## Verification State

2026-09-08, Story 3 closeout:

- Precision: contradiction 1/0, gap 1/0, ambiguity 1/0, clean 1/0; overall 4/0
- `bash scripts/tests/test_eval_spec_analyze.sh` green
- `bash scripts/eval.sh --check=spec-analyze` Findings 0 (live spec unverifiable / no_findings)
- Typecheck: skipped, none configured
