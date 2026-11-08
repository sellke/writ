# Shrink the interrogate-style review surface in favor of empirical and formal checks

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-11-03
> **spec_ref:** .writ/specs/archive/2026-11-04-evidence-gated-review/spec.md

## TL;DR

Audit every place Writ asks a model to argue with a change (pstack `interrogate`-style review), and replace or demote each one where a test, a reproduction, a script, or a type/contract check can establish the same fact.

## Current State

LLM-judgment review surfaces, mostly added or grown in Phase 15 with pstack `interrogate` as the named reference ([research F3](../../research/2026-10-19-writ-vs-pstack-research.md)):

- `agents/review-agent.md`, `agents/evaluator-agent.md`, `commands/review.md` (plus `claude-code/agents/writ-reviewer.md`, `writ-evaluator.md`): model-read review at Gate 3 and pre-landing.
- `skills/review-judgment-filters/SKILL.md`: three lead-judgment filters (all nits = fine; trace the call site; slow to dismiss security). These tune how a model weighs another model's findings.
- `scripts/review-panel.py` (ADR-028): opt-in cross-family panel, same prompt to several models, `block` votes.
- Safety Fact / evidence ladder (`skills/blast-radius/SKILL.md`, `scripts/review-override.py safety-fact`): five rungs `claimed`, `read`, `traced`, `tested`, `reproduced`. The review-agent route's floor is `traced`, a reading rung, not an executed one.
- No inventory says which review findings a deterministic check could have produced instead.

## Expected Outcome

- An inventory of each adversarial-review surface: what fact it tries to establish, how often it catches something the scripted gates missed, and its token/spawn cost.
- Per surface, one of: **replace** with an empirical or formal check (test, repro script, property test, typecheck, contract/AC-trace script), **demote** to fallback when no check exists, or **keep** with a stated reason.
- Evidence-ladder floor raised toward `tested` or `reproduced` wherever the stack can execute the claim; `traced` kept only where it cannot.
- Fewer reviewer instructions and spawns on the default path, with the exit-criteria pass rate on the Phase 11 baseline set at or above today's.

## Relevant Files

- `skills/review-judgment-filters/SKILL.md` - filters exist only to referee model-vs-model findings
- `scripts/review-panel.py` - cross-family adversarial panel
- `agents/review-agent.md` - Safety Fact section and `traced` floor

## Related Issues

- [2026-09-25-jev-typed-judgments-for-harness-gates](2026-09-25-jev-typed-judgments-for-harness-gates.md) - replaces other free-form LLM judgments with bounded typed ones
- [2026-09-26-architecture-rules-as-lint](../features/2026-09-26-architecture-rules-as-lint.md) - same move (prose review → mechanical check) for architecture

## Notes

- Sequence after `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/`. It is waiting on human labels and will issue keep/remove verdicts for `Reviewer Filters` and `Safety Fact`; reuse its findings data instead of re-measuring.
- Out of scope unless decided otherwise: discovery-time "challenge" prompts in `/plan-product` (Premise Challenge), `/create-spec`, `/new-command`, `/edit-spec`. They interrogate the user's idea, not code, and have no empirical substitute.
- Risk: some reviewer catches (design smell, missing case nobody wrote a test for) have no mechanical equivalent. The audit should name those and keep them, not cut by default.

## Resolution

2026-11-04, spec `2026-11-04-evidence-gated-review` (Complete, on `phase/15-code-level-rigor`, PR #64), recorded in [ADR-032](../../decision-records/adr-032-evidence-gated-review.md). The inventory is ADR-032 § Review-Surface Inventory: twelve surfaces, each with a keep, demote, replace, or remove verdict and its spawn and byte cost. Outcome: a Gate 3 or `/review` finding blocks only on executed evidence (`review-override.py evidence`); the review panel is removed; the Safety Fact floor rose from `traced` to `tested`; the reviewer filters stay, kept by the removal trial on one valid catch. Not done: surfaces that run before code exists (Gate 0, the discovery prompts) were kept by scope, as the Notes above expected.
