# User Stories: Prompting Guide

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Write the Prompting Guide](story-1-write-the-guide.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Ship, Link, and Pin the Guide](story-2-ship-link-and-pin.md) | Completed ✅ | High | Story 1 | 6 | 6/6 |

**Total:** 2 stories, 13 tasks, 10 acceptance criteria.

## Dependencies

- **Story 1** has no dependency. It writes `.writ/docs/prompting-guide.md` and the five guide-file tests in `scripts/tests/test_prompting_guide.py`.
- **Story 2** needs Story 1: it links the guide from `README.md` § Quick Start and extends the same test file with the README and ship-set tests.
- At the spec level, `2026-10-22-front-door` depends on this spec, because its command cites the guide's path and headings.
