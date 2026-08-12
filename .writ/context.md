# Writ Context

> Last Updated: 2026-08-12T19:37:00+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

**None.** All 55 specs are archived under `.writ/specs/archive/` (see `LEDGER.md`). The most recent, `2026-08-12-refactor-dirty-tree-guard`, completed 2/2 stories and was archived 2026-08-12. Phase 10 closed PARTIALLY COMPLETE the same day; **no phase is currently committed** — next candidates live in the roadmap's *Beyond Phase 10* parking lot.

## Artifact Map

| Artifact | Path | Present |
|---|---|---|
| Product mission | `.writ/product/mission.md` | yes |
| Roadmap | `.writ/product/roadmap.md` | yes |
| Active spec | — (none in flight) | n/a |
| Knowledge ledger | `.writ/knowledge/` | yes |
| Decision records | `.writ/decision-records/` | yes |
| Docs | `.writ/docs/` | yes |
| Issues | `.writ/issues/` | yes |

**Integrity:** all required artifacts resolve. Optional artifacts absent are reported, not fatal.

## Recent Drift

From `2026-08-12-refactor-dirty-tree-guard` (now archived):

- **DEV-001 (Story 1, Small)** — dirty-tree guard implemented as a distinct numbered step (`Step 1.1b`) rather than prose inside Step 1.1; spec intent preserved and reachability made structural.
- **DEV-002 (Story 1, Small)** — `scripts/` leanness ratchet tripped by the eval.sh pins; non-blocking, left unsilenced for the baseline owner.
- **DEV-001 (Story 2, Low)** — this file was itself regenerated out of boundary during `/status` and asserted "No drift log for the active spec" while `drift-log.md` existed, and dropped a live follow-up. Corrected 2026-08-12.

**Closed follow-up (Story 1):** `require_literal` pins proved the `/refactor` guard exists but not that it was *reachable*; a 9th pin on `proceed to Step 1.1b` closed it. Story 2 hit the same class twice more — see its What Was Built.

## Open Issues

4 files — the two filed 2026-08-11/12 by Phase 10's own UAT both have shipped remedies (`/refactor` dirty-tree guard spec, complete; `phase-closure-status` spec, complete — carried a `spec_ref`) and await formal closure; plus `2026-08-11-restore-path-recording-for-destructive-commands` (improvement, open) and the long-parked business-process pipeline feature with a roadmap parking-lot entry.

## Release

v0.30.2 tagged 2026-08-12 (releases v0.29.0 → v0.30.2 all landed today). Phase 10 closed PARTIALLY COMPLETE: determinism half shipped and enforced; progressive disclosure stopped after one conversion on measured evidence; byte program withdrawn per ADR-023. Product docs reconciled to the closure via `/plan-product --reconcile` (2026-08-12).
