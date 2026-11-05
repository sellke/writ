# Writ Project Context

> Last Updated: 2026-11-05T15:16:43Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (when an agent stops and asks a person: on reasonable doubt, not on principle, per ADR-033). Users reach all three through one front door, `/writ`, that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-10-25-gate-upgrade-removal-measurement — Gate Upgrade Removal Measurement
- **Status:** In Progress — task 4.6 waits on the Repro First substitute baseline (drift-log DEV-013); the trial kept Gate 0 Divergence, Safety Fact, and Reviewer Filters and held Repro First
- **Story:** 4 of 4 — Act on the Labeled Trial (In Progress, 6/7 tasks)
- **Progress:** 27/28 tasks complete; the branch is `phase/15-code-level-rigor`, PR #64 (draft)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md (reconciled 2026-11-05; Phase 17 committed, ADR-033)
- **Active spec:** .writ/specs/2026-10-25-gate-upgrade-removal-measurement/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md, trial-report.md, rating-handoff.md
- **Knowledge:** .writ/knowledge/ (29 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-029 `slug_vendor` and `origin_vendor` kept for `trial-record` — evidence-gated-review (Small)
- DEV-028 A run-level stop after a failed prior check prints `fail` — evidence-gated-review (Small)
- DEV-027 Manifest entries carry the normalized `content`, and a row 4a brief reads it — evidence-gated-review (Small)

## Open Issues

24 open issue files in .writ/issues/ (42 total; 18 closed with `## Resolution`)
