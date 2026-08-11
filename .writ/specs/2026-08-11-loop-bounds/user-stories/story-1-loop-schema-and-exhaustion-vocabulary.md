# Story 1: Loop Schema and Exhaustion Vocabulary

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer adding an iteration bound to a looping command
**I want** one declared schema for `loop:` and a closed three-value `on_exhaustion` vocabulary that maps onto `scripts/phase-state.py`'s existing verbs
**So that** every bound is written the same way, is machine-checkable, and cannot invent a second retry authority that contradicts the one already enforced in code

## Acceptance Criteria

- [ ] Given the ADR-020 frontmatter block, when the `loop:` key contract is documented, then it specifies `unit`, `max_iterations`, `on_exhaustion`, and `calibrated_against` as required at the top level of `loop:`, with `nested:` optional and capped at one level of depth.
- [ ] Given a command with more than one bounded loop, when its bounds are declared, then the primary loop occupies `loop.max_iterations` / `loop.on_exhaustion` directly — so the locked contract's literal path and the roadmap's success criterion both resolve — and additional loops occupy `nested:` entries carrying the same four keys.
- [ ] Given the `on_exhaustion` vocabulary, when it is defined, then it admits exactly three values — `quarantine`, `escalate`, `halt_reported` — and `retry` is explicitly named as illegal with the stated reason that retry is a pre-exhaustion state already governed by `scripts/phase-state.py`'s `attempts < 2` guard.
- [ ] Given `on_exhaustion: quarantine`, when its behavior is specified, then it invokes the existing `scripts/phase-state.py quarantine` subcommand and adds no new disposition path, no new state field, and no new branch-naming rule — and is declared legal only where a `phase-execution-*.json` record exists for the unit.
- [ ] Given any `on_exhaustion` value, when the loop exhausts, then the specified output includes the loop's `unit`, the declared bound, the count reached, the last completed unit, and a literal resume command — so no exhaustion path can terminate silently.
- [ ] Given `2026-08-11-component-contract` may land before or after this spec, when the schema is documented, then `loop:` is specified as append-only within the existing `---` block: it does not define, reorder, rename, or validate `problem:` / `outcome:` / `exit_criteria:`, and validates identically whether those keys are present or absent.

## Implementation Tasks

- [ ] 1.1 Read `scripts/phase-state.py` `cmd_classify`, `cmd_retry`, and `cmd_quarantine` in full and record, in the schema documentation, the exact composition rule: `attempts` starts at 0, `create-lane` sets it to 1, `retry` sets it to 2 and raises `retry_exhausted` at ≥2 — so the effective budget is two attempts, and `on_exhaustion` fires only after it is spent
- [ ] 1.2 Write the `loop:` key contract (types, required/optional, uniqueness of `unit` within a file, one-level `nested` cap, `max_iterations` as a positive integer literal — not a range, string, or expression) into `sub-specs/technical-spec.md`'s Schema section as the authoritative reference the other stories cite
- [ ] 1.3 Define the three `on_exhaustion` values with their behavior, their legality conditions, and their required output fields; state explicitly why `retry` and any "continue anyway" value are excluded
- [ ] 1.4 Record the `unit` vs. the roadmap's `loop.bound` naming reconciliation — `unit` names what is counted, `max_iterations` is the number — so the roadmap feature line and this schema are not read as two different designs
- [ ] 1.5 Write fixture frontmatter blocks covering every malformation Story 5 must reject: missing each required key, `on_exhaustion: retry`, an out-of-set `on_exhaustion`, non-integer `max_iterations`, duplicate `unit` across primary and nested, `nested` inside `nested`, `loop:` present but not a mapping
- [ ] 1.6 Verify acceptance criteria are met — in particular that the documented schema and the fixture set correspond one-for-one, so Story 5 has nothing to invent

## Notes

**Technical considerations:**

- The alternative shape — `loop:` as a bare list of loop declarations — was considered and rejected in the technical spec: it makes `loop.max_iterations` unaddressable, which breaks both the locked contract's wording and the roadmap success criterion *"All 5 loop-bearing commands declare `loop.max_iterations` + `on_exhaustion`"*. If implementation finds a reason to revisit, that is a spec amendment, not an implementation choice.
- `nested:` exists for exactly one command. Four of the five never use it and cost four frontmatter lines. Resist generalizing it into a nesting mechanism; the one-level cap is the guard.
- `quarantine` is legal only for `implement-phase`'s nested `spec_attempt` loop in this spec. Nothing in `implement-story`, `refactor`, or `verify-spec` has a `phase-execution-*.json` record to quarantine against, which is why all their exhaustion values are `escalate` or `halt_reported`.

**Risks / challenges:**

- The tempting mistake is adding a fourth value meaning "continue past the bound." That would make every bound advisory and delete the spec's reason to exist. If a loop genuinely needs to continue, its bound is wrong — raise the number with the run as evidence.
- The second tempting mistake is making `on_exhaustion: quarantine` do something slightly different from `phase-state.py quarantine` — a "soft quarantine," a quarantine without dependent blocking, a quarantine that skips the branch rename. Any of those is the parallel failure handling the locked contract forbids.

**Integration points:**

- Stories 2, 3, and 4 consume this schema verbatim and add no keys of their own.
- Story 5 mechanizes it; every rule stated here must be checkable, and any rule that cannot be checked should be reconsidered rather than shipped as unverifiable prose.
- `2026-08-11-component-contract` owns the surrounding block. This story must not touch its three fields.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 4 (`on_exhaustion` composes with `phase-state.py`'s existing retry rule and never widens it; `retry` is not a legal value — the primary rule this story implements), Rule 3 (named, resumable state, never a bare halt), Rule 6 (`loop:` is a reserved sibling key that restructures nothing)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The `loop:` frontmatter block — key shape, required vs. optional, why `nested:` exists; The `on_exhaustion` vocabulary — the three-value table with legality conditions] — from spec.md → ## Detailed Requirements
- **Error map rows:** [Parse `loop:` from frontmatter → blocking finding, never default-and-continue; `on_exhaustion: quarantine` invoked outside a phase → illegal by schema, `escalate` fallback at runtime; `loop:` and the ADR-020 keys land out of order → append-only, neither check assumes the other] — from sub-specs/technical-spec.md → Error & Rescue Map
- **Contract:** ["`on_exhaustion` maps onto `scripts/phase-state.py`'s existing `retry` / `quarantine` verbs rather than inventing parallel failure handling"; "`on_exhaustion` must always terminate with a reported, recoverable state — never a silent stop"] — from spec.md → ## Contract (Locked)
