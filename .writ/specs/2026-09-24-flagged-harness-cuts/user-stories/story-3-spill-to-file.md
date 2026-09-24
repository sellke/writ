# Story 3: Spill to file

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** spill over-budget story-context (and the lean What Was Built path) to a gitignored file under `.writ/state/` when `WRIT_HARNESS_LEAN=1`, instead of silently discarding the truncated body
**So that** flag-on baseline runs keep the full text on disk with path, size, and a short tail in the payload, while flag-off behavior and existing `enforce_budget` tests stay unchanged

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `WRIT_HARNESS_LEAN=1` and assembled story-context bytes strictly exceeding `FETCHED_CONTEXT_BUDGET_BYTES`, when `scripts/story-context.py` returns its payload, then the full pre-truncation text is written to `.writ/state/story-context-spill-<story-id>.md`, `truncated` is true, and the payload includes `spill.path`, `spill.bytes`, and a `fetched_context` tail of at most 500 bytes for the cut category `[AC-3.1]`
- [ ] Given `WRIT_HARNESS_LEAN` unset (or any non-`1` value treated as unset), when story-context exceeds the budget, then `enforce_budget` truncates as today, the payload has no `spill` field, no spill file is written under `.writ/state/`, and existing tests in `scripts/tests/test_story_context.py` still pass without the variable set `[AC-3.2]`
- [ ] Given `WRIT_HARNESS_LEAN=1`, over-budget context, and a non-writable `.writ/state/`, when assemble runs, then a warning names the error and states the spill was not written, the inline payload is the current truncated form, and no spill file appears `[AC-3.3]`
- [ ] Given the default `skills/dependency-context-loading/SKILL.md` truncate-by-priority wording for a “What Was Built” record over 1,000 lines, when this story lands, then that default skill text is unchanged; the lean `commands/implement-story.lean.md` path (named here, authored in Story 4) is the contract surface that points at spill instead of truncate `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write failing tests in `scripts/tests/test_story_context.py` for flag-on over-budget spill (path, bytes, ≤500-byte tail, `truncated`), flag-unset no-spill regression against current `enforce_budget` behavior, and read-only `.writ/state/` rescue `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.2 Gate spill on `WRIT_HARNESS_LEAN=1` inside `scripts/story-context.py` (alongside the Story 1 flag reader): when over budget, write `.writ/state/story-context-spill-<story-id>.md` with the pre-truncation text before applying the inline cut `[AC-3.1]`
- [ ] 3.3 Shape the over-budget payload so `truncated` stays true and `spill.path` / `spill.bytes` plus a ≤500-byte `fetched_context` tail are present only when a spill file was written `[AC-3.1]`
- [ ] 3.4 On spill write failure (non-writable `.writ/state/`), keep today’s truncated inline payload, append a warning that names the error and says the spill was not written, and omit `spill` `[AC-3.3]`
- [ ] 3.5 Confirm `skills/dependency-context-loading/SKILL.md` is byte-identical on the 1,000-line truncate rule, and record in Notes/What Was Built that `commands/implement-story.lean.md` (Story 4) is the lean surface that points at spill for oversized What Was Built records `[AC-3.4]`
- [ ] 3.6 Verify all acceptance criteria: flag-on spill tests green, `WRIT_HARNESS_LEAN` unset leaves `scripts/tests/test_story_context.py` green with no spill artifacts, read-only state-dir case warns without writing, default skill truncate wording untouched `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

**Technical considerations.** Spill is additive and flag-gated: unset continues through `enforce_budget` alone. The spill filename is `.writ/state/story-context-spill-<story-id>.md` so it stays gitignored with the rest of `.writ/state/`. `truncated` remains the signal that the inline body is incomplete whether or not a spill file exists. Tail length is a hard ceiling of 500 bytes, not a soft target.

**Risks.** A spill the agent never opens is a quality risk; this story does not prove agents read it — Story 5’s baseline catches that. Accidentally writing spill files when the flag is unset would break existing truncate tests and the byte-identical default contract from Story 1. A partial write that leaves an empty or truncated spill file while claiming success would lie about `spill.bytes`.

**Integration.** Depends on Story 1’s `WRIT_HARNESS_LEAN` reader semantics (treat non-`1` as unset with one warning). Story 4 authors `commands/implement-story.lean.md` and is where the What Was Built spill pointer lands in lean command prose; this story only freezes the default skill truncate wording and names that lean path as the contract surface. Story 5 exercises flag-on spill during the 8-run baseline.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Spill over-budget context]
- **Shadow paths:** [Flag off assemble, Flag on assemble]
- **Business rules:** [Spill, don’t truncate, only when the flag is on (rule 4)]
- **Experience:** [State catalog → Flag set, over budget; State catalog → Flag unset]
