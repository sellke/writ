# Writ Context

> Last Updated: 2026-08-13T04:05:00+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

None — both specs shipped in v0.31.0 are now archived under `.writ/specs/archive/`. No spec folder currently sits at the top level of `.writ/specs/`.

## Artifact Map

| Artifact | Path | Present |
|---|---|---|
| Product mission | `.writ/product/mission.md` | yes |
| Roadmap | `.writ/product/roadmap.md` | yes |
| Active spec | — | none |
| Knowledge ledger | `.writ/knowledge/` | yes (26 entries) |
| Decision records | `.writ/decision-records/` | yes |
| Docs | `.writ/docs/` | yes (21 files) |
| Issues | `.writ/issues/` | yes |

**Integrity:** ✅ all required present. Optional artifacts absent are reported, not fatal.

## Recent Drift

No open `drift-log.md` for either recently-shipped spec — all drift was recorded inline in per-story What Was Built sections. See `.writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/` and `.writ/specs/archive/2026-08-12-recalibrate-implement-loop/` for detail.

## Open Issues

4 files under `.writ/issues/` — unchanged this run; not investigated as part of this release.

## Release

**v0.31.0 tagged 2026-08-13.** Both `2026-08-12-machine-evaluable-exit-criteria` and `2026-08-12-recalibrate-implement-loop` shipped via PR #43 (merged `d269228`). The post-merge archival hook auto-archived `2026-08-12-recalibrate-implement-loop`; `2026-08-12-machine-evaluable-exit-criteria` was initially missed because `scripts/resolve-spec-reference.py`'s commit-message signal only matched a spec's full dated folder name, not its bare slug — the completing commit said "Completes Story 6 and the machine-evaluable-exit-criteria spec" (no date prefix), so it was invisible to the resolver. Root-caused, fixed with a regression test (`cd1c782`), and the missed spec archived by hand (`851f58f`). Both stale post-archival doc references (`commands/implement-phase.md`, `adapters/claude-code.md`) repointed to `.writ/specs/archive/...` (`b2a15b7`). Going forward, a normal single-spec-per-PR release will resolve and auto-archive correctly.
