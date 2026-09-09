# `exit-criteria.py` implement-spec.c3 Rejects Stacks With No Typechecker

> **Type:** Improvement
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-09-07
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`commands/implement-spec.md` Step 4.1 says the typecheck is skipped "when the stack has none",
but `scripts/exit-criteria.py` (`implement-spec.c3`, near line 668) accepts only the literal
`postRun.typecheck == "pass"`. On this repo (Python scripts, no mypy/pyright configured in
`pyproject.toml`) an honest `postRun` can never satisfy c3, so a fully green spec run reports
`verdict: unmet` and the `✅ Specification Complete` banner is withheld.

## Evidence

2026-09-07, closing `2026-09-05-phase11-repair-and-baseline`: 1017 pytest passed, every bash
suite green, `eval.sh` Findings 0, `contextRewritten: true`, `typecheck: "skipped"` with a reason.
Checker output:

```
implement-spec.c3 unmet postRun recorded typecheck='skipped' testSuite='pass' contextRewritten=True
```

An ad-hoc `uv run --with mypy mypy scripts/*.py` finds 105 pre-existing errors in 17 files,
so writing `pass` would be false and `fail` would invent a gate the project never had.

## Proposed fix

Accept `typecheck: "skipped"` when `postRun.typecheckReason` is non-empty, and have the
evidence line say "typecheck skipped (reason)". Keep `fail` blocking. Alternatively, let
`/implement-spec` Step 4.1 write `typecheck: "pass"` with a `typecheckCommand: null` note —
but that hides the skip, which is worse than the current false negative.
