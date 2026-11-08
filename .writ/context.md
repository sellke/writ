# Writ Project Context

> Last Updated: 2026-11-08T15:00:00Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** none active. Phase 16 (`2026-11-06-pr-ready-and-ledger`, `2026-11-06-ship-watch-and-merge`) is Complete and merged in PR #71 (`19f56e8`); unreleased (v0.46.0 is the latest release). One real-PR `/ship --watch` run is outstanding.
- **Not started:** `2026-11-06-archived-dependencies-resolve`. **In progress:** `2026-10-25-gate-upgrade-removal-measurement` (amendment requested).

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (v0.46.0 latest release, 2026-11-07)
- **Specs:** 6 under .writ/specs/; completed specs under .writ/specs/archive/
- **Knowledge:** .writ/knowledge/ (30 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-011 The first spec's contract tests follow the Callers cells — ship-watch-and-merge (Small)
- DEV-010 Step 6 names the landed SHA for a `--watch` merge, and the Gate 3 repro ships as its own test file — ship-watch-and-merge (Small)
- DEV-009 `test_harness_cuts.py`'s AC-3.3 frontmatter test is renamed and joined by a `--watch` merge-claim test — ship-watch-and-merge (Small)

## Open Issues

26 open issue files in .writ/issues/ (47 total; 21 closed with `## Resolution`, 1 Goal Card)
