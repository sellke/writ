# Shipped Docs Still Describe Retired Mechanisms

> **Type:** Improvement
> **Priority:** Low
> **Effort:** Small
> **Created:** 2026-10-20
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Phase 13's specs remove the friction-signal no-op lines and the internal links in shipped commands. Several shipped docs and command lines still describe retired mechanisms or name Writ ADRs that a user's project does not have.

## Current State

- `.writ/docs/model-tiers.md` lines ~101, ~134, and ~178 describe the `escalated` signal as "a no-op call until that spec ships". ADR-030 retired friction signals, so the spec will never ship.
- About 23 lines in 10 commands name a Writ ADR as a bare label without a link, such as `(ADR-013)` and `Design principle (ADR-001)`. `2026-10-20-shipped-command-hygiene` removes only links, by contract.
- `.writ/issues/improvements/2026-09-25-jev-typed-judgments-for-harness-gates.md` line ~35 cites `scripts/lean-decision.py` as an existing tool. `2026-10-20-harness-cuts` deletes it.
- pytest tests and several `eval-*.py` helpers pin command prose directly. The shipped-command-hygiene pin map covers only `eval.sh` pins.

## Expected Outcome

- `model-tiers.md` describes escalate-once without the retired signal.
- A decision on bare ADR labels in shipped commands: keep them as provenance, or replace each with the one-sentence rule it stands for.
- Prose pins outside `eval.sh` get the same keep/convert/remove review.

## Relevant Files

- `.writ/docs/model-tiers.md`
- `commands/*.md` (bare `ADR-0NN` labels)
- `scripts/tests/`, `scripts/eval-*.py` (prose pins)
- Origin: grounding notes in `.writ/specs/2026-10-20-harness-cuts/` and `.writ/specs/2026-10-20-shipped-command-hygiene/`
