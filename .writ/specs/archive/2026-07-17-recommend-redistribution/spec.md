# Spec: Recommend Redistribution

> **Status:** Complete
> **Created:** 2026-07-17
> **Owner:** @adam
> **Type:** Product feature (ships to all Writ users)
> **Decision of record:** [ADR-013 (revised 2026-07-17)](../../decision-records/adr-013-recommended-autonomous-delivery.md)

## Contract Summary

Redistribute the `--recommend` capability after experience showed that a single
command carrying one spec all the way through a production-approval boundary was
the wrong first cut. `--recommend` now lives on **exactly two commands**:

- **`/create-spec --recommend`** — autonomously authors and locks a validated
  spec package from evidence, records each material decision in
  `recommendation-log.md`, then **stops**. Never implements.
- **`/implement-phase --recommend`** — the sole end-to-end loop: auto-authors
  missing specs (via `create-spec --recommend`), auto-accepts its decomposition
  and execution-plan confirmations, and runs `implement-spec` per spec through
  the existing isolated-lane flow. Terminal scope unchanged: honest completion
  report with manual UAT handoff.

`--recommend` is **removed** from `implement-spec`, `ship`, and `create-uat-plan`;
`implement-spec` is a plain execute command (no confirmation gate, no flag). The
autonomous **staging → production-approval** flow (original ADR-013 clause 4) is
**deferred** — not reached by any current command. Its staging machinery
(`scripts/recommend-state.py`, `.writ/docs/recommended-delivery-state-format.md`)
is kept **dormant**, not deleted.

**Hardest constraint:** both recommended flows end at their normal terminal scope
— **neither merges, opens PRs, nor releases.** Production stays a human decision.

## Why This, Why Now

The change was authored directly against `ADR-013` (amended in place) and the
command/adapter/policy surfaces, but landed **without a spec** and **without
updating the eval falsifiability gate** that guards the recommended-delivery
policy. `scripts/eval.sh` still asserts the pre-revision single-spec /
production-approval contract as literals and static assertions, so the suite
fails against the reconciled reality (109 findings at time of writing). This spec
gives the in-flight change a home and closes the eval debt so it is releasable.

## Scope Boundaries

**Included:**
- `create-spec`, `implement-phase`, `implement-spec`, `ship`, `create-uat-plan` — `--recommend` redistribution (already edited).
- `system-instructions.md`, `cursor/writ.mdc`, `commands/_preamble.md`, adapters — policy reconciliation (already edited).
- `.writ/product/{mission,mission-lite,roadmap}.md`, `.writ/context.md` — product-layer reconciliation (already edited).
- `.writ/decision-records/adr-013-*.md` — the 2026-07-17 revision (already landed).
- `scripts/eval.sh` — reconcile `autonomy-governance` (done), `recommended-spec-implementation`, and `recommended-staging` to the revision; keep dormant-machinery guards.

**Excluded:**
- **Building** the deferred staging → production flow (explicitly deferred — "bigger loops later").
- **Deleting** the dormant staging machinery (`scripts/recommend-state.py`, state-format doc) — preserved by ADR decision.
- Any new command file.

## Business Rules

- **Human production boundary is absolute.** No `--recommend` command merges,
  opens PRs, or releases.
- **Deferred ≠ deleted.** The staging machinery and its ADR/locked-delivery-spec
  descriptions are preserved as the future design; only *active* command/adapter
  surfaces drop the staging contract.
- **The eval gate must track the policy, not lag it.** Every policy surface the
  revision changed has a matching eval assertion reconciled in the same change.

## Success Criteria

1. `bash scripts/eval.sh` exits **0** with **0 findings** against the reconciled surfaces.
2. `autonomy-governance` asserts the revised policy's canonical literals on live surfaces and `forbid_literal`-guards the superseded wording there; the deferred production-approval design (reviewed-SHA binding) is preserved in ADR-013 + the locked delivery spec.
3. `recommended-spec-implementation` reflects the two-command model — no active-surface expectation of `implement-spec --recommend`.
4. `recommended-staging` either guards only the **dormant** machinery/design or is retired with a recorded rationale — it no longer demands staging orchestration on active `ship`/`create-uat-plan`/adapter surfaces.
5. `commands/_preamble.md` is within the 80-line limit.
6. Product layer passes `/verify-spec --product` (already ✅ as of 2026-07-17).

## Deliverables Checklist

- [x] `--recommend` redistributed across the five commands
- [x] Policy surfaces reconciled (`system-instructions.md`, `cursor/writ.mdc`, `_preamble.md`, adapters)
- [x] Product layer reconciled (mission, mission-lite, roadmap, context) + roadmap entry
- [x] ADR-013 revision recorded
- [x] `scripts/eval.sh` — `autonomy-governance` reconciled (4 literals repointed + 3 regression forbids), PASS
- [x] `scripts/eval.sh` — `recommended-spec-implementation` reconciled to the two-command model
- [x] `scripts/eval.sh` — `recommended-staging` redirected to the dormant machinery
- [x] `commands/_preamble.md` trimmed to ≤ 80 lines (79)
- [x] Full `bash scripts/eval.sh` green (0 findings)
