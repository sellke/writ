# Writ Project Context

> Last Updated: 2026-11-07T17:25:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-06-lean-story-pipeline — Lean Story Pipeline (branch `spec/lean-story-pipeline`, worktree `.claude/worktrees/lean-story-pipeline`)
- **Status:** Complete — 6/6 stories; implement-spec checker verdict met; integration suite green after fix `bdff146`; not yet shipped
- **Story:** 6 of 6 complete; trial verdict `lean-pipeline: keep`
- **Progress:** 40/40 tasks complete

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (Phases 14, 15, and 17 released in v0.44.0, 2026-11-06; ADR-033)
- **Active spec:** .writ/specs/2026-11-06-lean-story-pipeline/ — spec.md + spec-lite.md, user-stories/, sub-specs/, recommendation-log.md, drift-log.md, gate-evidence.md, trial-report.md
- **Knowledge:** .writ/knowledge/ (30 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-025 The orchestrator ran the trial and wrote Story 6's files — lean-story-pipeline (Medium)
- DEV-024 Full-suite escaped-defect check replaced — lean-story-pipeline (Medium)
- DEV-023 Shipped checker change: `test-integrity.py` credits Python doc-pin tests — lean-story-pipeline (Medium)

## Open Issues

27 open issue files in .writ/issues/ (45 total; 18 closed with `## Resolution`, 1 Goal Card)
