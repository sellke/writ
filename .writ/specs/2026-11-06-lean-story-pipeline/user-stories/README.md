# User Stories: Lean Story Pipeline

> Spec: [../spec.md](../spec.md) · Progress: 2/6 stories (33%)

| # | Story | Status | Tasks | AC | Dependencies |
|---|---|---|---|---|---|
| 1 | [Gate declarations and evidence](story-1-gate-evidence.md) | Completed ✅ | 6/6 | 5 | None |
| 2 | [Demote gates with no recorded catch](story-2-demote-unproven-gates.md) | Completed ✅ | 6/6 | 5 | Story 1 |
| 3 | [story-gate.py runner](story-3-story-gate-runner.md) | Not Started | 0/7 | 5 | Story 2 |
| 4 | [Targeted-test ownership](story-4-targeted-test-ownership.md) | Not Started | 0/7 | 4 | Story 3 |
| 5 | [Supervisor reads the story-gate record](story-5-supervisor-reads-record.md) | Not Started | 0/7 | 5 | Story 3 |
| 6 | [Before/after pipeline trial](story-6-lean-pipeline-trial.md) | Not Started | 0/7 | 5 | Story 4, Story 5 |

## Dependencies

- Story 1 records the evidence that every demotion in Story 2 cites.
- Story 3 builds the runner over the default gate set Story 2 leaves.
- Stories 4 and 5 both need the runner. They share no files, so `/implement-spec` runs them in one parallel batch.
- Story 6 trials the finished pipeline against the one before it.

Batches (`story-deps.py validate`): [1] → [2] → [3] → [4, 5] → [6].
