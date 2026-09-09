# User Stories — Phase 11 Stage 4a: Goal Emit

> Spec: [`../spec.md`](../spec.md) · Origin: [Goal Card](../../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) (Stage 4, emit only) · Evidence: [assessment](../../../product/2026-09-05-goldilocks-assessment.md) §5 Step 6, [claude-code adapter](../../../../adapters/claude-code.md) `/goal` Stop Hook

## Summary

| # | Story | Status | Priority | Deps | AC | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [CLI + Schema — goal-emit.py Emit and Check](story-1-emit-cli.md) | Completed ✅ | High | — | 5 | 7 | 7/7 |
| 2 | [Hooks — create-goal After Save and implement-phase Origin Emit](story-2-command-hooks.md) | Not Started | High | 1 | 5 | 6 | 0/6 |
| 3 | [Adapter + Eval + Gold Round-Trip](story-3-adapter-eval-roundtrip.md) | Not Started | High | 1, 2 | 5 | 7 | 0/7 |

**Total:** 3 stories · 15 acceptance criteria · 20 tasks · 7/20 complete (35%)

## Dependency Graph

```
Story 1 (CLI + schema) ──┬── Story 2 (create-goal + implement-phase hooks)
                         └── Story 3 (adapter + eval + gold)  [also depends on Story 2]
```

- **Batch 1:** Story 1.
- **Batch 2:** Story 2 (needs the CLI).
- **Batch 3:** Story 3 (needs CLI + hooks so the decision-log line can name both).

## Prerequisites outside this repo

None. Round-trip is scored on committed gold fixtures. No live Claude Code `/goal`. No yuss checkout. No Fable eight-run. Demote (≤2 subagents) is a later spec.
