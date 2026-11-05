# Writ Project Context

> Last Updated: 2026-11-05T00:03:42Z

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns three things and delegates or deletes the rest: the contract (spec, acceptance and exit criteria, stakes), the verifier (scripts that re-derive verdicts about the code and the running app), and the boundary (what an agent may not do without a human). Users reach all three through one front door that restates, classifies, and routes each request.

## Active Spec

- **Spec:** 2026-11-04-evidence-gated-review — Evidence-Gated Review
- **Status:** Not Started (spec.md header); Stories 1, 2, 3, and 5 of 7 completed on branch `phase/15-code-level-rigor`
- **Story:** 5 of 7 — Evidence gating in `/review` (Completed ✅); next is Story 4 — Confirmed repros become regression tests (Not Started). Story 6 waits on Story 4.
- **Progress:** 27/48 tasks complete (56%)

## Artifact Map

- **Product:** roadmap.md, mission.md, mission-lite.md
- **Active spec:** .writ/specs/2026-11-04-evidence-gated-review/ — spec.md + spec-lite.md, user-stories/, sub-specs/, drift-log.md
- **Knowledge:** .writ/knowledge/ (29 entries)
- **Docs:** .writ/docs/ (30 files)
- **Integrity:** ✅ all required present

## Recent Drift

- DEV-018 A confirmed repro was not committed: the user's decision overtook it — evidence-gated-review (Medium)
- DEV-017 `/review` passes `--timeout 60` — evidence-gated-review (Small)
- DEV-016 `/review` always asks before the evidence run (`untrusted_branch`) — evidence-gated-review (Medium)

## Open Issues

25 open issue files in .writ/issues/ (41 total; 16 closed with `## Resolution`)
