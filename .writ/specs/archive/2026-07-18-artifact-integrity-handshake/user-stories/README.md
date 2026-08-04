# User Stories — Artifact Integrity + Handshake

> Spec: [`../spec.md`](../spec.md) · Origin: recommendation #3 from the Conductor analysis.

## Progress

| Story | Title | Status | Tasks | Priority | Depends on |
|-------|-------|--------|-------|----------|------------|
| 1 | [Artifact Integrity in `_preamble.md`](./story-1-preamble-integrity-rule.md) | Complete | 4/4 | High | — |
| 2 | [`context.md` Artifact Map schema](./story-2-context-artifact-map.md) | Complete | 4/4 | High | Story 1 |
| 3 | [Command declarations + eval](./story-3-command-declarations-eval.md) | Complete | 5/5 | Medium | Story 1, 2 |

**Overall:** 13/13 tasks · 100%

## Dependency Graph

```
Story 1 (preamble convention)
   ├─▶ Story 2 (context.md Artifact Map)
   └─▶ Story 3 (per-command declarations + eval)   [also depends on Story 2's Map]
```

## Notes

- The leanest of the three specs: pure markdown edits + one eval check, no new pointer file, no runtime code.
- Deliberate rejection of a `.writ/index.md` file — the Artifact Map rides in the already-regenerated `context.md`, and eval guards against reintroducing an index file.
- Verification: `scripts/eval.sh` (Findings: 0) including `artifact-integrity` (19/19 scenarios).
