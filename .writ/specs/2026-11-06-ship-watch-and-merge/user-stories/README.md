# User Stories: Ship Watch and Merge

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Priority | Tasks | Progress |
|---|---|---|---|---|---|
| 1 | [The merge rule re-derives readiness](story-1-merge-rule-re-derives-readiness.md) | Completed ✅ | High | 7 | 7/7 |
| 2 | [`/ship` opens the PR without asking and records the ledger](story-2-ship-opens-without-asking.md) | Not Started | High | 7 | 0/7 |
| 3 | [A watch pass works a PR to merge-ready](story-3-watch-pass-to-merge-ready.md) | Not Started | High | 7 | 0/7 |
| 4 | [The watch merges on a green ledger](story-4-watch-merges-on-green-ledger.md) | Not Started | High | 6 | 0/6 |

**Total:** 4 stories, 27 tasks, 20 acceptance criteria.

## Dependencies

```
2026-11-06-pr-ready-and-ledger (spec) → 1 → 2 → 3 → 4
                                        └──────────→ 4
```

- **Story 1** changes `jev-judge.py`'s merge rule and the text that states it. Its real-script tests need the first spec's `pr-ready.py` and `verify-ledger.py`.
- **Story 2** rewrites `ship.md` Steps 1–5 and records the ledger. It follows Story 1 because both edit `.writ/docs/agent-cli-contract.md` (different Callers cells) and regenerate the platform trees.
- **Story 3** adds Step 7, the loop bound, and the adapter `re-enter` rows. It builds on Story 2's evidence file and Step 5.
- **Story 4** adds the merge step, which calls Story 1's merge rule, and changes the pinned frontmatter.

Stories 2, 3, and 4 all edit `commands/ship.md`, so they run in order on one branch. Each re-pins `KNOWN_OVER_BUDGET["commands/ship.md"]` and keeps the file above 24,960 bytes (technical-spec § Byte Budget).

## Not in any story

- The real-PR run (spec.md → Human UAT). `/create-uat-plan` hands it to a person.
- `.writ/product/mission-lite.md:35` ("merge and release always ask") and the roadmap's Phase 16 status. The orchestrator updates them at phase close.
