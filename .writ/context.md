# Writ Project Context

> Last Updated: 2026-11-07T23:30:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-06-lean-implement-phase — Lean Implement Phase (branch `spec/lean-implement-phase`, worktree `.claude/worktrees/lean-implement-phase`)
- **Status:** In Progress — 3/4 stories
- **Story:** 3 of 4 complete (UAT on request; health given sources; lane result file); next Story 4
- **Progress:** 18/24 tasks complete

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (v0.45.0 latest release; lean-story-pipeline merged in PR #68, unreleased)
- **Active spec:** .writ/specs/2026-11-06-lean-implement-phase/ — spec.md + spec-lite.md, user-stories/, sub-specs/, recommendation-log.md, drift-log.md
- **Knowledge:** .writ/knowledge/ (30 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-006 `validate-result` gains `result_missing` / `invalid_result` — lean-implement-phase (Small)
- DEV-005 Plugin generator treats every underscore file as a partial — lean-implement-phase (Small)
- DEV-004 ⚠️ Leanness `commands` metric counts invocable commands only — lean-implement-phase (Medium)

## Open Issues

28 open issue files in .writ/issues/ (46 total; 18 closed with `## Resolution`, 1 Goal Card)
