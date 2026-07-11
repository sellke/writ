# Evidence-Bound /refresh-command — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Complete
> **Progress:** 21/21 implementation tasks (100%)
> **Dependencies:** [] (independent — eval Tier 1 already exists)

## Story Summary

| # | Story | Priority | Dependencies | Status | Tasks |
|---|---|---|---|---|---:|
| 1 | [Evidence-Citation Contract and Drift Reconciliation](story-1-evidence-citation-contract-and-drift-reconciliation.md) | High | None | Completed ✅ | 7/7 |
| 2 | [Refresh-Evidence Eval Check](story-2-refresh-evidence-eval-check.md) | High | Story 1 | Completed ✅ | 7/7 |
| 3 | [Lightweight Tier 2 and Merge Gate](story-3-lightweight-tier2-and-merge-gate.md) | Medium | Stories 1, 2 | Completed ✅ | 7/7 |

## Dependency Plan

```text
Story 1  (evidence contract + drift)
   │
Story 2  (fixture-driven eval check)
   │
Story 3  (Tier 2 + merge gate + acceptance)
```

### Sequencing Rationale

- **Story 1** establishes the evidence contract in the command and aligns the docs first, so there is a single, coherent behavior for the eval check to validate. Reconciling drift up front prevents the check from encoding a description that contradicts the command.
- **Story 2** encodes that contract as a deterministic, fixture-driven eval check and registers it. It depends on Story 1 because its `require_literal` static assertions target the reconciled command and docs.
- **Story 3** builds the pre-merge gate and the bounded structural Tier 2 on top of a registered, passing check, then produces the two real acceptance entries the roadmap requires. It depends on Stories 1 and 2 because the gate invokes the registered check and asserts the reconciled command text.

Execution is sequential. Stories 2 and 3 share `scripts/eval.sh` and `scripts/eval-refresh-evidence.py`; Stories 1 and 3 share `commands/refresh-command.md`. Sequential single-writer ordering keeps every shared-file edit append-only and collision-free.

## Progress Rules

- Update each story's status `Not Started` → `In Progress` → `Completed ✅`.
- Count only top-level items under `## Implementation Tasks` (7 per story, 21 total).
- Do not mark Story 3 or the parent spec complete until both real acceptance entries exist in `.writ/refresh-log.md` (one merged-with-evidence, one rejected-for-lacking-evidence) and `bash scripts/eval.sh` plus `bash scripts/gen-skill.sh --check` are clean.
- Keep every `scripts/eval.sh` edit strictly append-only (one check function + one registry line) — a sibling Phase 7 spec appends later.
