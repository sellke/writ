# User Stories — Machine-Evaluable Exit Criteria

> **Status:** In Progress — 5/6 stories (83%)

| # | Story | Status | Depends on | Files |
|---|---|---|---|---|
| 1 | Criterion classification | Completed ✅ | — | `.writ/docs/exit-criteria-classification.md` |
| 2 | Run-record extensions | Completed ✅ | — | `scripts/phase-state.py`, `commands/implement-phase.md`, `commands/implement-spec.md`, `.writ/docs/phase-execution-state-format.md` |
| 3 | The checker | Completed ✅ | 1, 2 | `scripts/exit-criteria.py`, `scripts/tests/test_exit_criteria.py` |
| 4 | Eval integration | Completed ✅ | 3 | `scripts/eval-exit-criteria.py`, `scripts/eval.sh` |
| 5 | Command wiring | Completed ✅ | 3 | `commands/implement-phase.md`, `commands/implement-spec.md` |
| 6 | Adapter wiring | Not Started | 5 | `adapters/claude-code.md` |

## Dependency graph

```
1 ─┐
   ├─→ 3 ─┬─→ 4
2 ─┘      └─→ 5 ─→ 6
```

Stories 1 and 2 are independent and can run as a parallel first batch — Story 1
writes only `.writ/docs/exit-criteria-classification.md`, Story 2 touches
everything else. Stories 4 and 5 are independent of each other once 3 lands.

## File ownership

The two command files are written by **Story 2** (run-record fields) and **Story
5** (checker invocation and report block). They are sequenced — 2 before 5 via the
3 → 5 edge — so there is no concurrent write. No other story touches them.

`scripts/eval.sh` is owned solely by Story 4 and is **append-only**: a new
`check_exit_criteria()` function and a new `CHECKS` entry. No existing check
function is modified.

## Cut order

If the spec is shortened, drop from the bottom: **6**, then **4**. Stories 1–3
deliver the checker and 5 delivers enforcement on all four platforms. Story 6 must
never ship alone — a Claude-Code-only mechanism is the outcome the spec exists to
avoid.
