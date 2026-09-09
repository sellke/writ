# User Stories — Phase 11 Stage 3: Spec Analysis

> Spec: [`../spec.md`](../spec.md) · Origin: [Goal Card](../../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) (Stage 3) · Evidence: [assessment](../../../product/2026-09-05-goldilocks-assessment.md) §5 Step 4, [research](../../../research/2026-09-05-goldilocks-harness-research.md) F5

## Summary

| # | Story | Status | Priority | Deps | AC | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [CLI + Schema — spec-analyze.py Structural Findings and Findings-JSON Check](story-1-spec-analyze-cli.md) | Completed ✅ | High | — | 5 | 7 | 7/7 |
| 2 | [Hooks — create-spec Step 2.6c and verify-spec Advisory Check](story-2-create-spec-and-verify-hooks.md) | Not Started | High | 1 | 5 | 6 | 0/6 |
| 3 | [Eval Check + Precision Record on Labeled Fixtures](story-3-eval-and-precision.md) | Not Started | High | 1, 2 | 5 | 7 | 0/7 |

**Total:** 3 stories · 15 acceptance criteria · 20 tasks · 7/20 complete (35%)

## Dependency Graph

```
Story 1 (CLI + schema) ──┬── Story 2 (create-spec 2.6c + verify-spec)
                         └── Story 3 (eval + precision)  [also depends on Story 2]
```

- **Batch 1:** Story 1.
- **Batch 2:** Story 2 (needs the CLI).
- **Batch 3:** Story 3 (needs CLI + hooks so the decision-log line can name both).

## Prerequisites outside this repo

None. Precision is scored on committed labeled fixtures. No yuss checkout. No Fable 5.1 eight-run.
