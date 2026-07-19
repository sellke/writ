# User Stories — Git-Notes Audit Channel

> Spec: [`../spec.md`](../spec.md) · Origin: recommendation #1 from the Conductor analysis.

## Progress

| Story | Title | Status | Tasks | Priority | Depends on |
|-------|-------|--------|-------|----------|------------|
| 1 | [Audit digest format + ADR-017](./story-1-audit-digest-format-adr.md) | Not Started | 0/5 | High | — |
| 2 | [`/ship` integration — spec digest](./story-2-ship-integration.md) | Not Started | 0/8 | High | Story 1 |
| 3 | [`/release` integration — version rollup](./story-3-release-integration.md) | Not Started | 0/7 | Medium | Story 1 |
| 4 | [Sync config + opt-out + `/status` + eval](./story-4-sync-config-and-read-surface.md) | Not Started | 0/5 | Medium | Story 1 |

**Overall:** 0/25 tasks · 0%

## Dependency Graph

```
Story 1 (format + ADR)  ← foundation
   ├─▶ Story 2 (/ship digest)
   ├─▶ Story 3 (/release rollup)
   └─▶ Story 4 (sync + opt-out + /status + eval)
```

Story 1 defines the schema and rationale; Stories 2–4 are independent of each other and can run in parallel once Story 1 lands.

## Notes

- Methodology repo: deliverables are markdown/command/`install.sh` changes — verification is `scripts/eval.sh` + manual dogfood `/ship` on this repo, not code coverage.
- The load-bearing constraint is squash-survival: the digest attaches to the **landed** commit, never a pre-merge story commit.
