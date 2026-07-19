# User Stories — Git-Notes Audit Channel

> Spec: [`../spec.md`](../spec.md) · Origin: recommendation #1 from the Conductor analysis.

## Progress

| Story | Title | Status | Tasks | Priority | Depends on |
|-------|-------|--------|-------|----------|------------|
| 1 | [Audit digest format + ADR-017](./story-1-audit-digest-format-adr.md) | Complete | 5/5 | High | — |
| 2 | [`/ship` integration — spec digest](./story-2-ship-integration.md) | Complete | 8/8 | High | Story 1 |
| 3 | [`/release` integration — version rollup](./story-3-release-integration.md) | Complete | 7/7 | Medium | Story 1 |
| 4 | [Sync config + opt-out + `/status` + eval](./story-4-sync-config-and-read-surface.md) | Complete | 5/5 | Medium | Story 1 |

**Overall:** 25/25 tasks · 100%

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
