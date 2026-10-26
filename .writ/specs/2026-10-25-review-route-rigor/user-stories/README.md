# User Stories: Review-Route Rigor

> Spec: [`../spec.md`](../spec.md) · Technical spec: [`../sub-specs/technical-spec.md`](../sub-specs/technical-spec.md)

## Summary

| # | Story | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Upgrade switches](story-1-upgrade-switches.md) | Not Started | 6 | 0/6 (0%) | None |
| 2 | [Reviewer lead-judgment filters](story-2-reviewer-judgment-filters.md) | Not Started | 7 | 0/7 (0%) | Story 1 |
| 3 | [Blast radius at Gate 2.5](story-3-gate-2-5-blast-radius.md) | Not Started | 6 | 0/6 (0%) | Story 1, Story 2 |
| 4 | [Safety fact at Gate 3](story-4-gate-3-safety-fact.md) | Not Started | 7 | 0/7 (0%) | Story 1, Story 2, Story 3 |

**Total:** 4 stories, 26 tasks, 19 acceptance criteria. **Progress:** 0/26 tasks (0%).

## Dependencies

- **Story 1** adds `review-override.py switch`, which every later story calls.
- **Story 2** depends on Story 1 for the `reviewer-filters` switch.
- **Story 3** depends on Story 1 for the `safety-fact` switch. It follows Story 2 because both edit `commands/implement-story.md`.
- **Story 4** reads Story 3's blast-radius JSON and Story 1's switch. It follows Story 2 because both edit `agents/review-agent.md`, `.writ/manifest.yaml`, and Gate 3, and it extends the test file Story 2 creates.

The chain is serial on purpose: the stories are small, and three of them share files.

## Quick Links

- [Story 1: Upgrade switches](story-1-upgrade-switches.md)
- [Story 2: Reviewer lead-judgment filters](story-2-reviewer-judgment-filters.md)
- [Story 3: Blast radius at Gate 2.5](story-3-gate-2-5-blast-radius.md)
- [Story 4: Safety fact at Gate 3](story-4-gate-3-safety-fact.md)
