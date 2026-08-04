# User Stories Overview

> **Specification:** Phase 2a — Shipping & Review
> **Created:** 2026-03-15
> **Last Updated:** 2026-03-15
> **Status:** In Progress — 6/7 stories complete, dogfooding pending

## Stories Summary

| Story | Title | Status | Tasks | Progress | Dependencies |
|-------|-------|--------|-------|----------|--------------|
| 1 | [/ship — Core Workflow](./story-1-ship-core-workflow.md) | Completed ✅ | 7 | 7/7 | None |
| 2 | [/ship — PR Creation & Commit Intel](./story-2-ship-pr-creation.md) | Completed ✅ | 7 | 7/7 | Story 1 |
| 3 | [Standalone /review Command](./story-3-standalone-review.md) | Completed ✅ | 7 | 7/7 | None |
| 4 | [/retro — Git Analysis & Metrics](./story-4-retro-git-analysis.md) | Completed ✅ | 7 | 7/7 | None |
| 5 | [/retro — Output, Persistence & Trends](./story-5-retro-output-trends.md) | Completed ✅ | 7 | 7/7 | Story 4 |
| 6 | [Error Mapping in /create-spec](./story-6-error-mapping-create-spec.md) | Completed ✅ | 6 | 6/6 | None |
| 7 | [Integration Testing & Dogfooding](./story-7-integration-dogfooding.md) | In Progress 🔄 | 7 | 1/7 | All (1-6) |

**Total Progress:** 42/48 tasks (88%) — 6/7 stories complete, dogfooding pending

## Parallel Execution Batches

```
Batch 1 (parallel):  Story 1, Story 3, Story 4, Story 6
Batch 2 (parallel):  Story 2, Story 5
Batch 3 (sequential): Story 7
```

## Story Dependency Graph

```
Story 1: /ship core workflow ────┐
Story 2: /ship PR creation ──────┘(from 1)         ┐
Story 3: /review command ──────── (independent)     │
Story 4: /retro git analysis ────┐                  │
Story 5: /retro output & trends ─┘(from 4)         │
Story 6: Error mapping ────────── (independent)     │
                                                    │
Story 7: Integration & dogfooding ─────────────────┘(from all)
```

## Feature Mapping

| Feature | Stories |
|---------|---------|
| `/ship` command | Stories 1, 2 |
| `/review` command | Story 3 |
| `/retro` command | Stories 4, 5 |
| Error mapping in `/create-spec` | Story 6 |
| Validation | Story 7 |
