# `test-integrity.py authenticity` Flags Every Bash Test as `test_imports_no_source`

> **Type:** Improvement
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-09-03
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`python3 scripts/test-integrity.py authenticity --tests scripts/tests/<any>.sh` returns
`verdict: fail` with the blocking code `test_imports_no_source` for **every** bash test in
this repository — new or pre-existing — because its "whole-file module-specifier
extraction" has no notion of a shell script invoking a project script by path
(`bash "$REPO/scripts/lint-skill.sh"`). The finding's own claim ("cannot fail when the code
it claims to test changes") is empirically false for these files: mutation checks against
`scripts/tests/test_lint_model_tier.sh` (three behavioral mutations of `lint-skill.sh`)
were caught 3/3.

## Current State

- `scripts/test-integrity.py` `authenticity` treats `.sh` files as in-scope (`inspected.files: 1`,
  `out_of_scope: 0`) and then reports zero module specifiers — a `fail`, not an
  `unverifiable`.
- `.writ/docs/quality-signal-classification.md`'s stack support matrix does not list shell as a
  supported stack; by the doc's own rule an unsupported surface should classify as
  `unverifiable` with reason `unsupported_stack`, as the sibling `coverage` subcommand already
  does for the same file.
- `/implement-story` Gate 4 treats `test_imports_no_source` as blocking → BLOCKED escalation.
  On a bash-only story (Writ's own Stories 1, 2, 5 of `2026-09-03-model-delegation`) this
  fires by construction.

## Expected Outcome

- `authenticity` classifies test files whose language has no module-specifier concept
  (`.sh`, and any other unsupported suffix) as `out_of_scope` or `unverifiable`
  (`unsupported_stack`), never `fail`.
- Optionally: a shell-aware heuristic — a test that references a project path under
  `scripts/` via `bash`, `source`, or `$VAR` invocation counts as importing project source.
- A unit case in `scripts/tests/test_test_integrity.py` pinning the new classification.

## Relevant Files

- `scripts/test-integrity.py` — `authenticity` loop (~lines 620–676), `imports_project_source`
- `.writ/docs/quality-signal-classification.md` — stack support matrix and the unsupported-stack rule
- `commands/implement-story.md` Gate 4 — the consumer that turns this verdict into a block

## Origin

Surfaced during `/implement-spec 2026-09-03-model-delegation` Story 1 Gate 4. The story was
carried to Completed on the mutation evidence above with this issue filed as the durable
record — the orchestrator's judgment, recorded here rather than made quietly.
