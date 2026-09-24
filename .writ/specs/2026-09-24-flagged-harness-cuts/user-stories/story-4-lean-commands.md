# Story 4: Lean command bodies

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** author lean sibling bodies for the four large commands behind `WRIT_HARNESS_LEAN`
**So that** flag-on runs load shorter command text without changing the default floor or dropping exit criteria, gates, or the production boundary

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given `WRIT_HARNESS_LEAN` is unset, when `scripts/measure-invocation.py` reports the invocation floor, then `commands/create-spec.md`, `commands/verify-spec.md`, `commands/implement-phase.md`, and `commands/implement-story.md` are byte-identical to before this story and no `*.lean.md` sibling bytes are counted in that floor. `[AC-4.1]`
- [ ] Given `WRIT_HARNESS_LEAN=1` and the four lean siblings exist, when `scripts/measure-invocation.py` reports the invocation floor, then it loads the lean bodies for create-spec, verify-spec, implement-phase, and implement-story. `[AC-4.2]`
- [ ] Given the lean siblings `commands/create-spec.lean.md`, `commands/verify-spec.lean.md`, `commands/implement-phase.lean.md`, and `commands/implement-story.lean.md`, when each is inspected, then none contains a line that asks the model to conserve tokens, be brief, or avoid waste, and each retains exit criteria, named gates, and the production boundary (no autonomous merge, PR, or release). `[AC-4.3]`
- [ ] Given lean bodies are authored, when the default command files are inspected, then neither text is embedded in the live `.md` command and the only lean command siblings this story creates are the four named files. `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write tests that assert the unset floor excludes lean command siblings and stays byte-stable on the four defaults, that `WRIT_HARNESS_LEAN=1` reports the lean bodies, and that embedding both texts in a live command fails the floor check. `[AC-4.1, AC-4.2, AC-4.4]`
- [ ] 4.2 Author `commands/create-spec.lean.md` (drop model-redundant and system-instructions restatement only; keep exit criteria, gates, production boundary). `[AC-4.3, AC-4.4]`
- [ ] 4.3 Author `commands/verify-spec.lean.md` under the same deletion class. `[AC-4.3, AC-4.4]`
- [ ] 4.4 Author `commands/implement-phase.lean.md` under the same deletion class. `[AC-4.3, AC-4.4]`
- [ ] 4.5 Author `commands/implement-story.lean.md` under the same deletion class. `[AC-4.3, AC-4.4]`
- [ ] 4.6 Verify acceptance criteria: unset floor excludes lean siblings and defaults are unchanged; flag-on reports lean bodies; no token-saving lines; gates and production boundary retained; run the new tests. `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- Depends on Story 1's loader substrate in `scripts/measure-invocation.py`; this story authors bodies only and does not re-teach flag parsing.
- Contract constraint: four rewrites stay one story — one task per lean file plus a floor-measurement check — not four specs.
- Allowed cuts: behavior the current default frontier already does (Opus 5.5, or GPT-6 Astra — both above the Fable 5.1 baseline model), and sentences that restate `system-instructions.md`. Forbidden cuts: exit criteria, named gates, production boundary. Do not justify a cut by what only a weaker model needed.
- Story 5 (keep-or-revert) is the only story that may change the default load path.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Load a lean sibling]
- **Shadow paths:** [Flag off assemble, Flag on assemble]
- **Business rules:** [No token-saving instruction, Deletion class, Siblings are not in the default floor]
- **Experience:** [Flag unset, Flag set, under budget]
