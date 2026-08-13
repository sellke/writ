# Writ Context

> Last Updated: 2026-08-12T20:00:00+00:00

## Product Mission

Writ is the thin, portable methodology layer on top of capable AI harnesses. It owns the durable contracts — specs, drift logs, decisions, knowledge, phase state — in plain markdown on git, and delegates mechanics (context management, subagents, browsing, retrieval) to the platform underneath. As harnesses absorb mechanics natively, Writ sheds them and concentrates on what compounds: the negotiated contract layer no harness provides.

## Active Spec

- **Spec:** `2026-08-12-machine-evaluable-exit-criteria` — Machine-Evaluable Exit Criteria
- **Status:** All 6 stories complete; not yet archived
- **Story:** 6 of 6 — Adapter Wiring (Completed ✅)
- **Progress:** 6/6 stories complete (100%)

## Artifact Map

| Artifact | Path | Present |
|---|---|---|
| Product mission | `.writ/product/mission.md` | yes |
| Roadmap | `.writ/product/roadmap.md` | yes |
| Active spec | `.writ/specs/2026-08-12-machine-evaluable-exit-criteria/` | yes — spec.md, spec-lite.md, sub-specs/, user-stories/ |
| Knowledge ledger | `.writ/knowledge/` | yes |
| Decision records | `.writ/decision-records/` | yes |
| Docs | `.writ/docs/` | yes |
| Issues | `.writ/issues/` | yes |

**Integrity:** all required artifacts resolve. Optional artifacts absent are reported, not fatal.

## Recent Drift

From `2026-08-12-machine-evaluable-exit-criteria` (active, no separate `drift-log.md` — Small drift recorded inline in each story's What Was Built rather than a standalone log, since every instance was a documentation-level correction, not an implementation deviation):

- **Story 1** — one imprecise closing sentence in the classification doc, corrected inline post-review; no contract deviation.
- **Story 3** — deliberate, disclosed id-format correction (dotted strings over `spec.md`'s stale positional-int worked example).
- **Story 4** — none; drift-detection binding independently verified twice (by coder and reviewer) by actually breaking and reverting a criterion string.
- **Story 6** — a citation slip (referenced "Step-3" where the actual step is 2.3), caught by review and corrected inline; the substantive claim held under the correct step number.

**Known, disclosed limitation (not drift, recorded in Story 3's What Was Built):** the archived `.writ/state/phase-execution-20260812-0200.json` (Phase 10, PARTIALLY COMPLETE) replays to `unmet` rather than the `impossible` that `spec.md`'s Success Criterion 2 names, because that file predates this spec's own instrumentation entirely — exposing a genuine tension between `spec.md`'s Business Rule 2 and Success Criterion 2 for pre-instrumentation archives, not an implementation defect. Flagged for the spec owner at `/verify-spec` or spec closure; unresolved by design (rewriting the criterion or the checker to force a match was explicitly rejected per Business Rule 5).

## Open Issues

4 files — the two filed 2026-08-11/12 by Phase 10's own UAT both have shipped remedies (`/refactor` dirty-tree guard spec, complete; `phase-closure-status` spec, complete — carried a `spec_ref`) and await formal closure; plus `2026-08-11-restore-path-recording-for-destructive-commands` (improvement, open) and the long-parked business-process pipeline feature with a roadmap parking-lot entry.

## Release

v0.30.3 tagged 2026-08-12. `2026-08-12-machine-evaluable-exit-criteria` is implemented and verified (full eval suite green, 71 unit tests passing) but not yet shipped/released — next steps are `/verify-spec` (recommended, to address the disclosed Success Criterion 2 gap) and `/ship`.
