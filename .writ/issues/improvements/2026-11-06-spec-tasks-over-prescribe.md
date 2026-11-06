# Generated Story Tasks Over-Prescribe Implementation and Restate Rules

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-11-06
> **spec_ref:** .writ/specs/2026-11-06-lean-story-tasks/spec.md

## TL;DR

`/create-spec` stories write implementation tasks as pseudo-code in prose and repeat business rules across files. That costs context, invites drift, and adds little beyond what the acceptance criteria and Notes already pin down.

## Current State

- Sample: `.writ/specs/2026-11-06-pr-ready-and-ledger` is about 13,500 words for 3 stories. Story 1 is about 1,500 words for a script of a few hundred lines.
- The template caps tasks at 5–7 per story but sets no limit on task detail, so the generator packs detail into each task (80–120 words apiece in Story 1).
- Tasks fix internals a coding agent can work out itself: function signatures, the argparse formatter class, which helpers to copy, the order of checks inside a function.
- One business rule (Rule 8) appears in the `spec.md` contract, again in its expanded section, in `technical-spec.md`, and in the story's task text. Each copy has to be kept in sync, and the implementer has to resolve any mismatch between them.
- Every story carries the same generic Definition of Done ("Code reviewed", "Documentation updated").
- The archived specs' `drift-log.md` files suggest coding agents already depart from the tasks. That is not yet tied to over-prescription.
- What works and should stay: concrete, testable Given/When/Then acceptance criteria that cover hard edge cases, and Notes that record probed facts (git quirks, bytes vs text, the Python 3.9 floor).

## Expected Outcome

- Tasks prescribe files, external contracts (CLI shape, file format, exit and reason codes), and the order of tests and verification. Internal structure is left to the coding agent unless another story or spec depends on it (for example, `ledger_check()` used by ship-watch).
- The spec states each rule once, and other files link to it instead of restating it.
- The generic Definition of Done is dropped or replaced with checks specific to the story.
- Validation: regenerate one archived spec under the new rules, run `/implement-story` on both versions, and compare spec word count, drift-log entries, and review findings.

## Relevant Files

- `agents/user-story-generator.md` - defines story shape (3–5 ACs, 5–7 tasks); no limit on task detail
- `commands/create-spec.md` - story contents at line 526; quality gate at line 599
- `agents/coding-agent.md` - line 120 limits the agent to files the tasks list, which is why tasks must name files

## Notes

- Keep naming files in tasks: the file-creation rule in `coding-agent.md` and `implement-story.md` depends on it.
- Measure before rolling the change out: fewer words with more drift or more review findings would be a regression.
