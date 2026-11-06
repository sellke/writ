# User Stories: PR Ready and Verification Ledger

> Spec: [`../spec.md`](../spec.md) · Lite: [`../spec-lite.md`](../spec-lite.md) · Technical: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Priority | Tasks | Progress |
|---|---|---|---|---|---|
| 1 | [Verification ledger](story-1-verification-ledger.md) | Completed ✅ | High | 7 | 7/7 |
| 2 | [`pr-ready.py` snapshot and blocker classes](story-2-pr-ready-blocker-classes.md) | Not Started | High | 7 | 0/7 |
| 3 | [Ledger gate and machine output](story-3-ledger-gate-and-json.md) | Not Started | High | 6 | 0/6 |

**Total:** 3 stories, 20 tasks, 15 acceptance criteria.

## Dependencies

```
1 → 2 → 3
```

- **Story 1** builds `scripts/verify-ledger.py`, its mutation test, and its contract registration. Nothing depends on code outside it.
- **Story 2** builds `scripts/pr-ready.py` without the ledger gate. Its code needs nothing from Story 1, but it edits the same files: `.writ/docs/agent-cli-contract.md`, `scripts/tests/test_agent_cli_contract.py`, and `plugins/writ/scripts/`. So it runs after Story 1.
- **Story 3** loads `verify-ledger.py` from `pr-ready.py`, adds the `not_verified` gate and `--json`, and updates Story 2's clean-fixture tests in the same commit.

The sibling spec `2026-11-06-ship-watch-and-merge` depends on all three. It replaces the two Callers cells in `.writ/docs/agent-cli-contract.md` and edits nothing else this spec owns.

## Quick Links

- [Story 1: Verification ledger](story-1-verification-ledger.md)
- [Story 2: `pr-ready.py` snapshot and blocker classes](story-2-pr-ready-blocker-classes.md)
- [Story 3: Ledger gate and machine output](story-3-ledger-gate-and-json.md)
