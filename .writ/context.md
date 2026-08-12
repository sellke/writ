# Writ Context

> Last Updated: 2026-08-12T12:11:17+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

**2026-08-12-refactor-dirty-tree-guard** — In Progress, 1/2 stories.
Story 1 (porcelain guard) shipped 2026-08-12 via the Scenario 20 harness probe.
Story 2 (executable checkpoint in `safe-refactor-loop`) is Not Started — 3 tasks.

## Artifact Map

| Artifact | Path | Present |
|---|---|---|
| Product mission | `.writ/product/mission.md` | yes |
| Roadmap | `.writ/product/roadmap.md` | yes |
| Active spec | `.writ/specs/2026-08-12-refactor-dirty-tree-guard/spec.md` | yes |
| Knowledge ledger | `.writ/knowledge/` | yes |
| Decision records | `.writ/decision-records/` | yes |
| Docs | `.writ/docs/` | yes |
| Issues | `.writ/issues/` | yes |

**Integrity:** all required artifacts resolve. Optional artifacts absent are reported, not fatal.

## Recent Drift

- **DEV-001 (Story 1, Small)** — dirty-tree guard implemented as a distinct numbered step (`Step 1.1b`) rather than prose inside Step 1.1; spec intent preserved and reachability made structural.
- **DEV-002 (Story 1, Small)** — `scripts/` leanness ratchet tripped by the eval.sh pins; non-blocking, left unsilenced for the baseline owner.
- **DEV-001 (Story 2, Low)** — this file was itself regenerated out of boundary during `/status` and asserted "No drift log for the active spec" while `drift-log.md` existed, and dropped a live follow-up. Corrected 2026-08-12.

**Open follow-up (Story 1):** `require_literal` pins proved the `/refactor` guard exists but not that it was *reachable*; a 9th pin on `proceed to Step 1.1b` closed it. Story 2 hit the same class twice more — see its What Was Built.

## Open Issues

3 total — 2 filed 2026-08-11 by Phase 10's own UAT (one now partly addressed by the active spec), 1 long-parked feature with a roadmap spec_ref.

## Release

v0.29.0 tagged 2026-08-12. Phase 10 closed PARTIALLY COMPLETE: determinism half shipped and enforced; progressive disclosure stopped after one conversion on measured evidence.
