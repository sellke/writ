# User Stories — Phase 11 Stage 2a: Prune the Base

> Spec: [`../spec.md`](../spec.md) · Origin: [Goal Card](../../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) (Stage 2, first of two specs) · Evidence: [assessment](../../../product/2026-09-05-goldilocks-assessment.md) §2.1, §3, §5 Step 2

## Summary

| # | Story | Status | Priority | Deps | AC | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [Pruning Policy ADR and Ledger Tooling — ADR-026, prune-ledger.py, and the pruned-base eval check](story-1-pruning-policy-and-ledger.md) | Not Started | High | — | 5 | 7 | 0/7 |
| 2 | [Move Documentation Out — Five Base Sections Relocated to .writ/docs/ With Ledger Rows and a Measured Byte Count](story-2-move-documentation-out.md) | Not Started | High | 1 | 5 | 6 | 0/6 |
| 3 | [Cut Behavior Requests — Line-by-Line Classification to a 10,000-Byte Base, Batching Line to Adapters](story-3-cut-behavior-requests.md) | Not Started | High | 2 | 5 | 7 | 0/7 |
| 4 | [Gate Verification Markers and Provenance Check — gates: Frontmatter, verdict-provenance.py, and the verdict-provenance Eval Check](story-4-gate-verification-markers.md) | Not Started | High | — | 5 | 7 | 0/7 |
| 5 | [Baseline Re-run and Keep-or-Revert — Eight Fable 5.1 Runs on the Pruned Base, Compared Against Stage 1](story-5-baseline-rerun-keep-or-revert.md) | Not Started | High | 3, 4 | 4 | 6 | 0/6 |

**Total:** 5 stories · 24 acceptance criteria · 33 tasks · 0/33 complete (0%)

## Dependency Graph

```
Story 1 (ADR + ledger tooling) ── Story 2 (moves) ── Story 3 (cuts) ──┐
Story 4 (gate markers) ───────────────────────────────────────────────┴── Story 5 (re-run, keep-or-revert)
```

- **Batch 1 (parallel):** Stories 1 and 4 — Story 4 touches only `implement-story.md` frontmatter, `scripts/`, and `eval.sh`, none of which Story 1 edits except `eval.sh` (different functions, additive registration).
- **Story 2** needs Story 1's `prune-ledger.py check` green at every commit. **Story 3** needs Story 2's measured byte count (Business Rule 6).
- **Story 5** needs the pruned base (Story 3) and the gate markers (Story 4) in place before the eight runs, so the re-run measures the state that would ship. It is the only story that spends Fable 5.1 tokens at scale (about $190, 5.5 h, plus one retry pair worst case).
- **Revert range:** Stories 2 and 3. ADR-026, the ledger tooling, Story 4, and the re-run JSON survive a revert.

## Prerequisites outside this repo

- `~/Projects/yuss` — read-only clone at the same HEAD as Stage 1 (`7c2d043`); the runner writes only under the scratch `--tmp-root`.
- `claude` (headless driver) and `pnpm` on `PATH`; no vendor API key.
