# User Stories: Claude Agent Generator

> Spec: [../spec.md](../spec.md)

| # | Story | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Generator and Overlay](story-1-generator-and-overlay.md) | Not Started | 7 | 0/7 | None |
| 2 | [Regenerate Claude Agents](story-2-regenerate-claude-agents.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [Parity Check, Eval Check, and Docs](story-3-parity-eval-and-docs.md) | Not Started | 7 | 0/7 | Story 1, Story 2 |

**Total:** 3 stories, 21 tasks, 15 acceptance criteria.

## Dependencies

- **Story 1** builds `scripts/gen-claude-agents.py` and its tests. It does not touch `claude-code/agents/`.
- **Story 2** runs the generator and commits the eight generated files. It needs Story 1's generator.
- **Story 3** wires content checks into `check-agent-parity.sh` and `eval.sh`. It needs the generator (Story 1) and a tree where `--check` already passes (Story 2), or `eval.sh` fails on the committed tree.

Execution is strictly sequential: 1 → 2 → 3.
