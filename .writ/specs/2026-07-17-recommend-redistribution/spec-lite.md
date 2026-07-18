# Spec-Lite: Recommend Redistribution

> Source: spec.md
> Purpose: Condensed agent context

## What We're Building

Redistribute `--recommend` to exactly two commands — `create-spec --recommend`
(author + lock a spec from evidence, then stop) and `implement-phase --recommend`
(end-to-end phase loop that auto-authors missing specs and runs `implement-spec`
per spec). Remove it from `implement-spec`/`ship`/`create-uat-plan`. Defer the
autonomous staging → production-approval flow (keep its machinery dormant, not
deleted). Per ADR-013 as revised 2026-07-17.

## Key Constraints

- No `--recommend` command merges, opens PRs, or releases — production stays human.
- Deferred ≠ deleted: dormant staging machinery + ADR/locked-spec text preserved.
- The eval gate must be reconciled in the same change, not left lagging.

## Success Criteria

- Full `scripts/eval.sh` green (0 findings).
- `autonomy-governance` on the new literals; `recommended-spec-implementation` on the two-command model; `recommended-staging` redirected to dormant machinery.
- `_preamble.md` ≤ 80 lines. Product layer passes `/verify-spec --product`.

## State (2026-07-17)

**Complete.** All three stories done: command redistribution, policy/product
reconciliation, and eval-gate reconciliation. Full `scripts/eval.sh` green
(0 findings); `_preamble.md` at 79 lines.

## Files in Scope

`commands/{create-spec,implement-phase,implement-spec,ship,create-uat-plan}.md`,
`system-instructions.md`, `cursor/writ.mdc`, `commands/_preamble.md`,
`adapters/*.md`, `.writ/product/*`, `.writ/context.md`,
`.writ/decision-records/adr-013-*.md`, `scripts/eval.sh`.
