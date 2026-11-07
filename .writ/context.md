# Writ Project Context

> Last Updated: 2026-11-07T12:00:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-06-lean-story-pipeline — Lean Story Pipeline (branch `spec/lean-story-pipeline`, worktree `.claude/worktrees/lean-story-pipeline`)
- **Status:** In Progress — `/implement-spec` run started 2026-11-06T22:24:40Z
- **Story:** 5 of 6 — Supervisor reads the story-gate record (Completed ✅); next: Story 6, before/after trial
- **Progress:** 33/40 tasks complete

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (Phases 14, 15, and 17 released in v0.44.0, 2026-11-06; ADR-033)
- **Active spec:** .writ/specs/2026-11-06-lean-story-pipeline/ — spec.md + spec-lite.md, user-stories/, sub-specs/, recommendation-log.md, drift-log.md, gate-evidence.md
- **Knowledge:** .writ/knowledge/ (30 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-023 Shipped checker change: `test-integrity.py` credits Python doc-pin tests — lean-story-pipeline (Medium)
- DEV-021 Supervisor rules beyond the technical spec's four — lean-story-pipeline (Medium)
- DEV-020 Parallel batches run one after another in one working tree — lean-story-pipeline (Medium)

## Open Issues

27 open issue files in .writ/issues/ (45 total; 18 closed with `## Resolution`, 1 Goal Card)
