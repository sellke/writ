# Writ Project Context

> Last Updated: 2026-11-08T12:00:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** none on `main`. Phase 16 (`2026-11-06-pr-ready-and-ledger`, `2026-11-06-ship-watch-and-merge`) is implemented on the unmerged branch `phase/16-verified-landing`; on `main` both read Not Started.
- **Also unmerged:** `claude/suspicious-nobel-c8a76d` — `story-context.py` resolves `Business Rule N` hints.
- **Not started:** `2026-11-06-archived-dependencies-resolve`. **In progress:** `2026-10-25-gate-upgrade-removal-measurement` (amendment requested).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (v0.46.0 latest release, 2026-11-07)
- **Specs:** 6 under .writ/specs/; completed specs under .writ/specs/archive/
- **Knowledge:** .writ/knowledge/ (30 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-010 ⚠️ A resume stop condition cut in round 1, restored in round 2 — lean-implement-phase (Medium)
- DEV-009 ⚠️ The 240-line target met mostly by removing blank lines — lean-implement-phase (Medium)
- DEV-008 Adapters describe the lane result file — lean-implement-phase (Small)

## Open Issues

25 open issue files in .writ/issues/ (46 total; 21 closed with `## Resolution`, 1 Goal Card)
