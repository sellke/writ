# User Stories — Terminal Status For A Spec Closed By Decision

> Spec: [spec.md](../spec.md)
> Total stories: 4 · Total tasks: 27 · Complete: 27/27 (100%)

## Stories

| # | Story | Status | Priority | Tasks | Progress |
|---|---|---|---|---|---|
| 1 | [Enforced Status Vocabulary](story-1-enforced-status-vocabulary.md) | Completed ✅ | High | 7/7 | 100% |
| 2 | [The `close-spec` Subcommand](story-2-close-spec-subcommand.md) | Completed ✅ | High | 7/7 | 100% |
| 3 | [Contract Surfaces — Schema Doc and Commands](story-3-contract-surfaces.md) | Completed ✅ | High | 7/7 | 100% |
| 4 | [Close The Loop On The Live Phase 10b State](story-4-close-the-loop.md) | Completed ✅ | Medium | 6/6 | 100% |

## Dependencies

A **strict chain** — 1 → 2 → 3 → 4. No story may run concurrently with another.

```
Story 1 ──▶ Story 2 ──▶ Story 3 ──▶ Story 4
```

- **Story 1 — none.** Establishes the enforceable vocabulary. Must land first because
  Story 2 writes a status that Story 1's guard would otherwise reject.
- **Story 2 — Story 1.** Needs `SPEC_STATUSES` to admit `closed_unimplemented` and needs
  `TERMINAL_SPEC_STATUSES` for the cascade's skip rule.
- **Story 3 — Story 2.** Documents behavior that must already exist; its static eval
  assertions describe the finished reducer.
- **Story 4 — Story 3.** Runs the shipped subcommand against live data as the end-to-end
  proof.

The chain is not merely logical — it is the **file-ownership mechanism**. Stories 1, 2,
and 3 all write `scripts/eval-phase-closure.py`, and Stories 1 and 3 both write
`scripts/eval.sh`. Sequencing them is what keeps single-writer-per-file true.

## Incremental Green

`bash scripts/eval.sh --check=phase-closure` must report zero findings at the end of
**every** story, not only the last:

| After | The check contains |
|---|---|
| Story 1 | Vocabulary and enforcement scenarios |
| Story 2 | …plus `close-spec` scenarios |
| Story 3 | …plus static doc and command assertions |
| Story 4 | Unchanged — Story 4 adds no scenarios, it runs the real thing |

## Quick Links

- [spec.md](../spec.md) — full contract, business rules, file ownership
- [spec-lite.md](../spec-lite.md) — condensed agent context
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — reducer design, error
  map, shadow paths
- Source issue:
  [2026-08-12-phase-execution-closed-unimplemented-status.md](../../../issues/improvements/2026-08-12-phase-execution-closed-unimplemented-status.md)
