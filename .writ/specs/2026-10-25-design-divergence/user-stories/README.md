# User Stories: Design Divergence Skill and Usage-First Gate 0

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Extract the design-divergence Skill and Register It](story-1-extract-design-divergence-skill.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [/prototype Step 2.5 Loads the Skill](story-2-prototype-loads-skill.md) | Not Started | High | Story 1 | 6 | 0/6 |
| 3 | [Gate 0 Usage-First Divergence and the Gate 0 Divergence Switch](story-3-gate-0-usage-first-divergence.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 4 | [Divergence Trial Harness](story-4-divergence-trial-harness.md) | Not Started | Medium | None | 7 | 0/7 |
| 5 | [Trial Inputs, Generation, Blinding, and Rating Handoff](story-5-trial-inputs-run-and-handoff.md) | Not Started | Medium | Story 1, Story 4 | 7 | 0/7 |
| 6 | [Act on the Blind Verdict (Human-Gated)](story-6-act-on-blind-verdict.md) | Not Started | Medium | Story 2, Story 3, Story 5 | 7 | 0/7 |

**Total:** 6 stories, 41 tasks, 29 acceptance criteria.

## Dependencies

- **Story 1** has no dependency. It writes the skill and registers it.
- **Story 2** needs Story 1: `/prototype` loads the skill file Story 1 creates.
- **Story 3** needs Story 1 for the same reason. Stories 2 and 3 edit different command files and can run in parallel; both regenerate the trees, which write different output files.
- **Story 4** has no dependency and can run beside Stories 1–3.
- **Story 5** needs Story 1 (the axes arm follows the skill) and Story 4 (the harness).
- **Story 6** needs Stories 2, 3, and 5, and a human rating. `/implement-spec` stops at its task 6.1 until the rater has filled `rating-sheet.md` and run `rate`.
