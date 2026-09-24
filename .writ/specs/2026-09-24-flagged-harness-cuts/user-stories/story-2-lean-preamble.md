# Story 2: Lean preamble

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** author `commands/_preamble.lean.md` that drops Plan Mode and `--recommend` restatements of `system-instructions.md` while keeping User Challenge, autonomy gate classes, file organization, and artifact integrity
**so that** flag-on runs load a shorter preamble without touching the 95-line `check_length` cap on the default file, and without any token-saving instruction to the model

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given Story 1's lean-sibling load path, when `commands/_preamble.lean.md` is authored, then it omits the Plan Mode Integrity and Narrow Recommended-Delivery Exception restatements that duplicate `system-instructions.md`, and flag unset still loads `commands/_preamble.md` `[AC-2.1]`
- [ ] Given the lean preamble, when its standing sections are inspected, then User Challenge, Autonomy Gate Classes (production boundary and stakes triage inclusive), File Organization, and Artifact Integrity are present and enforceable `[AC-2.2]`
- [ ] Given both preamble files and the existing `check_length` rule, when line counts are measured, then `_preamble.lean.md` is shorter than `_preamble.md`, `_preamble.md` stays at or under 95 lines, and the 95-line cap is not raised `[AC-2.3]`
- [ ] Given the lean preamble text, when it is scanned for token-saving coaching, then no line tells the model to use fewer tokens, be brief, or avoid waste `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write tests that assert lean vs default line-count ordering, default ≤95 with unchanged `check_length`, absence of token-saving lines, and presence of the kept sections in the lean sibling `[AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Author `commands/_preamble.lean.md` from `commands/_preamble.md`, removing Plan Mode Integrity and Narrow Recommended-Delivery Exception restatements of `system-instructions.md` `[AC-2.1]`
- [ ] 2.3 Keep User Challenge, Autonomy Gate Classes (including production-boundary human gate and stakes triage), File Organization, and Artifact Integrity in the lean sibling `[AC-2.2]`
- [ ] 2.4 Leave `commands/_preamble.md` as the default measured by `check_length`; do not edit `scripts/eval.sh` or raise the 95-line cap `[AC-2.3]`
- [ ] 2.5 Confirm flag-off still resolves to `commands/_preamble.md` via Story 1's loader, with lean bytes excluded from the unset floor `[AC-2.1]`
- [ ] 2.6 Verify all acceptance criteria: lean shorter than default, default ≤95, kept sections present, no token-saving line, and the authored tests pass `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

**Technical considerations.** The cut target is restatement of Plan Mode and `--recommend` already carried by `system-instructions.md`, not a rewrite of User Challenge or autonomy gates. The lean sibling is a new file beside the default; embedding both texts in the live command fails the sibling-floor contract owned by Story 1. `check_length` continues to measure only `commands/_preamble.md`.

**Risks.** Over-cutting the Narrow Recommended-Delivery Exception could drop the production-boundary sentence if it is treated as pure restatement — keep the human-gate production boundary inside Autonomy Gate Classes even when the recommend exception section is removed. A lean file that grows past the default's length (or past 95 while still "lean") fails this story; do not "fix" that by raising the cap.

**Integration.** Depends on Story 1 for `WRIT_HARNESS_LEAN` sibling selection and default-floor exclusion. Story 5 may later flip the default load to this sibling; until then flag off must remain byte-identical on `_preamble.md`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Load a lean sibling]
- **Shadow paths:** [Flag on assemble]
- **Business rules:** [No token-saving instruction, Deletion class (Plan Mode / `--recommend` restatements may drop; User Challenge, production boundary, stakes triage stay), Preamble cap (default ≤95; lean shorter)]
- **Experience:** [Flag unset (default preamble unchanged), Flag set under budget (lean preamble loaded)]
