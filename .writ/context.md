# Writ Project Context

> Last Updated: 2026-11-06T22:00:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-06-pr-ready-and-ledger — PR Ready and Verification Ledger
- **Status:** In Progress — Phase 16 lane `writ/phase/16/2026-11-06-pr-ready-and-ledger`
- **Story:** 3 of 3 — Ledger gate and machine output (Completed ✅)
- **Progress:** 20/20 tasks complete (100%)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-11-06-pr-ready-and-ledger/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md, recommendation-log.md
- **Knowledge:** .writ/knowledge/ (29 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-009 `evaluate` takes a `(pr, head)` gate that wraps `ledger_check`, and the loader checks the module and writes no bytecode — pr-ready-and-ledger (Small)
- DEV-008 A rejected snapshot value prints in a bounded form — pr-ready-and-ledger (Small)
- DEV-007 The contract test's AC-ID guard accepts a later spec's IDs, and two tests are appended — pr-ready-and-ledger (Small)

## Open Issues

25 open issue files in .writ/issues/ (43 total; 18 closed with `## Resolution`)
