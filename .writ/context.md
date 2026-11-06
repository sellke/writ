# Writ Project Context

> Last Updated: 2026-11-06T18:55:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-06-lean-story-tasks — Lean Story Tasks (branch `spec/lean-story-tasks`)
- **Status:** Complete — all 5 stories done; integration suite green (4261 passed on Python 3.9 and 3.14, eval.sh exit 0); not yet shipped
- **Story:** 5 of 5 — Trial lean tasks on one archived spec (Completed ✅; verdict `lean-tasks: keep`)
- **Progress:** 32/32 tasks complete

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (Phases 14, 15, and 17 released in v0.44.0, 2026-11-06; ADR-033)
- **Active spec:** .writ/specs/2026-11-06-lean-story-tasks/ — spec.md + spec-lite.md, user-stories/, sub-specs/, recommendation-log.md, drift-log.md, trial-report.md
- **Knowledge:** .writ/knowledge/ (29 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-010 Reduced, hand-run pipeline instead of `/implement-story` in the trial — lean-story-tasks (Medium)
- DEV-009 arm-original seeded from the pre-implementation commit — lean-story-tasks (Small)
- DEV-008 context-hint-format.md drops the "after the Definition of Done" placement — lean-story-tasks (Small)

## Open Issues

26 open issue files in .writ/issues/ (45 total; 18 closed with `## Resolution`, 1 Goal Card)
