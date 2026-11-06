# Writ Project Context

> Last Updated: 2026-11-06T19:09:27Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-06-ship-watch-and-merge — Ship Watch and Merge
- **Status:** In Progress — Phase 16 lane `writ/phase/16/2026-11-06-ship-watch-and-merge`
- **Story:** 3 of 4 complete (last: A watch pass works a PR to merge-ready)
- **Progress:** 21/27 tasks complete (78%)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-11-06-ship-watch-and-merge/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md, recommendation-log.md
- **Knowledge:** .writ/knowledge/ (29 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-007 The Gate 3 halt repro ships as its own test file, which `test-integrity.py` cannot attribute to `ship.md` — ship-watch-and-merge (Small)
- DEV-006 Step 7 is about twice the Story 3 byte estimate, and test fixtures learn the sixth loop command and `re-enter` — ship-watch-and-merge (Small)
- DEV-005 `gh api graphql --input` checked from gh's help text, not a live call — ship-watch-and-merge (Small)

## Open Issues

27 open issue files in .writ/issues/ (45 total; 18 closed with `## Resolution`)
