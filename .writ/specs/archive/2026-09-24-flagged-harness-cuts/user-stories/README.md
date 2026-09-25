# Flagged harness cuts — stories

| Story | Status | Tasks | Depends on |
|---|---|---|---|
| [1 Flag substrate](story-1-flag-substrate.md) | Completed ✅ | 6 | None |
| [2 Lean preamble](story-2-lean-preamble.md) | Completed ✅ | 6 | Story 1 |
| [3 Spill to file](story-3-spill-to-file.md) | Completed ✅ | 6 | Story 1 |
| [4 Lean command bodies](story-4-lean-commands.md) | Completed ✅ | 6 | Story 1 |
| [5 Keep or revert](story-5-keep-or-revert.md) | Completed ✅ | 6 | Stories 2, 3, and 4 |

Stories 2, 3, and 4 can land in any order after Story 1. Story 5 is last: it is the only story that may change the default load path, and a recorded null completes it.

30 implementation tasks across 5 stories. Each story has 4 acceptance criteria.

Progress: 5/5 stories, 30/30 tasks (100%).
