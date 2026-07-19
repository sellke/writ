# User Stories — Logical-Unit Revert (`/revert`)

> Spec: [`../spec.md`](../spec.md) · Origin: recommendation #2 from the Conductor analysis.

## Progress

| Story | Title | Status | Tasks | Priority | Depends on |
|-------|-------|--------|-------|----------|------------|
| 1 | [Record story commit SHA](./story-1-record-story-sha.md) | Not Started | 0/4 | High | — |
| 2 | [Commit resolver (`revert-resolve.py`)](./story-2-commit-resolver.md) | Not Started | 0/7 | High | Story 1 |
| 3 | [`/revert` command](./story-3-revert-command.md) | Not Started | 0/6 | High | Story 2 |
| 4 | [Artifact restoration + eval](./story-4-artifact-restoration-eval.md) | Not Started | 0/5 | Medium | Story 3 |

**Overall:** 0/22 tasks · 0%

## Dependency Graph

```
Story 1 (record SHA)
   └─▶ Story 2 (resolver + ghost-commit)
          └─▶ Story 3 (/revert command)
                 └─▶ Story 4 (artifact restoration + eval)
```

Linear chain — each story unlocks the next.

## Notes

- `scripts/revert-resolve.py` is the one piece of real testable code (≥80% coverage target). The rest is command markdown verified via `eval.sh` + manual dogfood on this repo.
- First cut = story + spec on the current branch. Phase-lane/quarantine reverts are deferred to `phase-state.py`'s existing machinery.
- Ghost-commit substitution always requires user confirmation — never auto-selected.
