# User Stories — Phase 11 Stage 1: Repair and Baseline

> Spec: [`../spec.md`](../spec.md) · Origin: [Goal Card](../../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) (Stage 1 of 4) · Evidence: [assessment](../../../product/2026-09-05-goldilocks-assessment.md), [research](../../../research/2026-09-05-goldilocks-harness-research.md)

## Summary

| # | Story | Status | Priority | Deps | AC | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [Repair Dead Ends — Nineteen Verified Items and Three Blocking Regression Checks](story-1-repair-dead-ends.md) | Completed ✅ (2026-09-06) | High | — | 5 | 7 | 7/7 |
| 2 | [Validated Token Measurement — measure-invocation.py Counts With the Anthropic API](story-2-validated-token-measurement.md) | Completed ✅ (2026-09-06; real-key run pending) | High | 1 (ordering only) | 5 | 7 | 7/7 |
| 3 | [Story Selection — pipeline-baseline.py select Picks Four yuss.app Stories by Fixed Criteria](story-3-story-selection.md) | Complete (2026-09-06) | High | 1 (ordering only) | 5 | 7 | 7/7 |
| 4 | [Replay Runner — Isolated Checkout, Headless /implement-story, Metrics Per Run](story-4-replay-runner.md) | Completed ✅ (2026-09-06; smoke run 4.2 pending) | High | 3 | 5 | 7 | 7/7 |
| 5 | [Baseline Capture and Gate — Eight Fable 5.1 Runs, One Committed JSON, check_pipeline_baseline](story-5-baseline-capture-and-gate.md) | In Progress (5.5 — live capture via operator CLI) | High | 2, 4 | 5 | 7 | 4/7 |

**Total:** 5 stories · 25 acceptance criteria · 35 tasks · 32/35 complete (91%)

## Dependency Graph

```
Story 1 (repair) ─ commit first
Story 2 (tokens) ─────────────────────┐
Story 3 (select) ── Story 4 (run) ── Story 5 (capture + gate)
```

- **Story 1** has no code dependents, but Stories 2 and 3 land after its commit so the baseline measures the repaired corpus. Its five ACs together satisfy Goal Card DONE WHEN line 1.
- **Stories 2 and 3** are independent of each other and may run in parallel once Story 1 is committed.
- **Story 4** extends the script Story 3 creates and reads its `selection` block. Task 4.2 is a live smoke run that decides whether headless invocation works or the `ingest` fallback is used — an accepted outcome either way, recorded in What Was Built.
- **Story 5** needs Story 2's validated counts and Story 4's runner. Its AC-5.1 plus Story 2's AC-2.1 satisfy DONE WHEN line 2. It is the only story that spends real Fable 5.1 tokens at scale (eight full pipeline runs); Story 4 spends one.

## Prerequisites outside this repo

- `~/Projects/yuss` — clone of `github.com/sellke/yuss` (read-only; the runner writes only under `$TMPDIR`).
- A headless driver on `PATH` only for models that have one (this spec's Fable 5.1 file uses `claude`). No vendor API key is required in Writ; the operator's CLI or IDE login authenticates.
- Models without a headless driver (Grok, local/open-weight, a Cursor session) are captured with `pipeline-baseline.py ingest` after `/implement-story` in that host.
- `ANTHROPIC_API_KEY` is optional and only used by Story 2's `measure-invocation.py --tokenizer anthropic`.
