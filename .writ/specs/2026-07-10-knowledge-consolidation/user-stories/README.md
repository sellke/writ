# Phase 7: Knowledge Consolidation — User Stories

> **Spec:** [`../spec.md`](../spec.md)
> **Status:** Not Started
> **Progress:** 0/20 implementation tasks (0%)
> **Dependencies:** [] (independent — Phase 6 knowledge writeback provides the input)

## Story Summary

| # | Story | Priority | Dependencies | Status | Tasks |
|---|---|---|---|---|---:|
| 1 | [Consolidation Reducer](story-1-consolidation-reducer.md) | High | None | Not Started | 0/7 |
| 2 | [`/knowledge --consolidate` Command Mode](story-2-knowledge-consolidate-command.md) | High | Story 1 | Not Started | 0/7 |
| 3 | [Eval, `/retro` Hook, and Docs](story-3-eval-retro-hook-and-docs.md) | Medium | Stories 1, 2 | Not Started | 0/6 |

## Dependency Plan

```text
Story 1  (reducer: detection + proposal + lineage + dry-run)
   │
Story 2  (command mode: present proposals, approval gate, apply lineage)
   │
Story 3  (eval scenarios + retro hook + docs finalize)
```

### Sequencing Rationale

- **Story 1** builds the mechanical core — the reducer that reads the ledger, detects duplicates/contradictions/stale, proposes merges, and emits a reviewable diff. It writes failing fixtures first and owns `scripts/knowledge-consolidate.py`. Nothing else can be tested until detection and the dry-run/apply boundary exist.
- **Story 2** wraps the reducer in `/knowledge --consolidate`: it presents proposals, gates every write on human approval, applies approved merges with lineage, and documents the lineage schema in `.writ/knowledge/README.md`. It depends on Story 1's stable reducer contract.
- **Story 3** proves the whole loop with eval scenarios, registers the check in `eval.sh` (shared-additive append), adds the read-only `/retro` advisory hook, and finalizes docs. It depends on both prior stories because its scenarios exercise the reducer (Story 1) and its static assertions target the command and README (Story 2).

Execution is sequential. Stories 2 and 3 consume contracts established earlier, and the `eval.sh` registry edit in Story 3 must land after the sibling evidence-bound-refresh spec's append (or before — either order is safe as long as they are not simultaneous), which sequential phase execution guarantees.

## Progress Rules

- Update each story's status from `Not Started` → `In Progress` → `Completed ✅`.
- Count only top-level items under `## Implementation Tasks`.
- Do not mark Story 3 or the parent spec complete until a real-ledger consolidation pass has produced a reviewable PR diff — the roadmap's real-entry criterion. Fixture evidence satisfies mechanical acceptance only.
- Every dry-run scenario must assert zero file changes; non-destructive-by-default is a blocking property, not a nice-to-have.
