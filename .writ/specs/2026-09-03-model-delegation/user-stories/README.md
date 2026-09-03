# User Stories — Model Delegation

> Spec: [`../spec.md`](../spec.md) · Decision: [ADR-024](../../../decision-records/adr-024-model-delegation.md) (+ Amendments A1–A3)

## Summary

| # | Story | Status | Priority | Deps | AC | Tasks | Progress |
|---|---|---|---|---|---|---|---|
| 1 | [The Contract — Anchor/Floor Vocabulary, Origin, Ceiling, and Lint Aliases](story-1-contract.md) | Completed ✅ (2026-09-03) | High | — | 5 | 6 | 6/6 |
| 2 | [Agents, Manifest, and Scaffolders — Rename Tiers, Retire "fast", Replace the Advisory Carrier](story-2-agents-manifest-scaffolders.md) | Completed ✅ (2026-09-03) | High | 1 | 5 | 7 | 7/7 |
| 3 | [Adapters and Platform Files — Verified Cursor Floor, Origin Sources, Resolution Tables](story-3-adapters-cursor-verification.md) | Completed ✅ (2026-09-03) | High | 1 | 5 | 7 | 7/7 |
| 4 | [Escalation — Floor Results Are Provisional at Two Sites](story-4-escalation.md) | Completed ✅ (2026-09-03) | High | 2, 3 | 5 | 6 | 6/6 |
| 5 | [Entry-Level Check — Every Command Declares What It Expects You Chose](story-5-entry-level.md) | Completed ✅ (2026-09-03) | Medium | 1 | 5 | 7 | 7/7 |

**Total:** 5 stories · 25 acceptance criteria · 33 tasks · 33/33 complete (100%)

## Dependency Graph

```
Story 1 (contract)
├── Story 2 (agents / manifest / scaffolders) ─┐
├── Story 3 (adapters / platform files)  ──────┴── Story 4 (escalation)
└── Story 5 (entry_level)
```

- **Story 1** writes the vocabulary every other story cites — land it first.
- **Stories 2, 3, 5** are independent of each other once Story 1 lands and may run in parallel.
- **Story 4** cites both the agent tiers (Story 2) and the platform-resolved anchor values (Story 3).
- Story 3's Cursor verification (task 3.2) runs before any adapter prose is edited; its `inherit` + `degraded` outcome is an accepted result, not a failure.

## Cross-cutting constraints

- `bash scripts/eval.sh` must end `Findings: 0` after every story.
- `system-instructions.md` § Model Tiers and `cursor/writ.mdc` stay byte-identical outside the mirror's appendix.
- `commands/_preamble.md` (95-line cap) receives nothing.
- `escalated`/`degraded` signal lines are written as documented no-ops until ADR-025's spec ships.
