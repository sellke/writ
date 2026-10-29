# User Stories: Repro-First Bug Fixing

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Repro-Order Check Script](story-1-repro-order-check.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [The tdd-cycle Bug Path](story-2-tdd-cycle-bug-path.md) | Completed ✅ | High | Story 1 | 7 | 7/7 |
| 3 | [The Coding Agent's Repro Report](story-3-coding-agent-repro-report.md) | Completed ✅ | High | Story 2 | 6 | 6/6 |
| 4 | [Consumer Wiring and Ordered-Commit Integration](story-4-consumer-wiring-and-integration.md) | Completed ✅ | High | Story 3 | 7 | 7/7 |

**Total:** 4 stories, 27 tasks, 20 acceptance criteria. **Progress:** 27/27 tasks (100%).

## Dependencies

- **Story 1** has no dependency. It adds `scripts/repro-order.py check`, its tests, and its CLI contract row. Every later story names the script by path.
- **Story 2** needs Story 1: the skill's bug path tells the agent to run the script. It creates `scripts/tests/test_repro_first_wiring.py` and the `Repro First` config row.
- **Story 3** needs Story 2: the coding agent's Requirement 1 names the skill section, and the `### Repro` block reports the script's output.
- **Story 4** needs Story 3: the consumer lines trigger on the `### Repro` block's commits. It pins every Removal Inventory row.
- At the spec level, `2026-10-25-gate-upgrade-removal-measurement` uses this spec's `Repro First` switch and Removal Inventory.
