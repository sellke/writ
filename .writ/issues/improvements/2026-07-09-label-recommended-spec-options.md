# Add Recommended Autonomous Spec Workflows

> **Type:** Improvement
> **Priority:** High
> **Effort:** Medium
> **Created:** 2026-07-09
> **spec_ref:** .writ/specs/2026-07-10-recommended-autonomous-delivery/spec.md

## TL;DR

Add a `--recommend` modifier that automatically follows the model's evidence-based recommendations through `/create-spec` and `/implement-spec`, while retaining `(Recommended)` labels for interactive decisions.

## Current State

- The model may recommend a course of action while discussing a spec, but the corresponding decision option is not consistently identified as recommended.
- AskQuestion choices can therefore lose recommendation context established during Plan Mode.
- Users must infer which option best matches the model's assessment when several valid choices are presented.
- Every decision gate requires human input, even when the model has already established a clear, low-risk recommendation.
- There is no continuous mode for carrying recommended choices through planning, contract confirmation, and execution-plan confirmation.

## Expected Outcome

- `/create-spec --recommend` and `/implement-spec --recommend` proceed continuously by selecting the model's evidence-based recommendation at each Plan Mode or AskQuestion decision.
- In normal interactive mode, every option the model recommends ends with `(Recommended)`.
- The model records or briefly states each automatic choice and its rationale so autonomous progress remains auditable.
- The workflow pauses only when:
  - A critical unresolved question could materially affect safety, security, data integrity, cost, compliance, irreversible behavior, or the feature's core contract.
  - The decision is inherently subjective or a matter of taste and available evidence provides no defensible recommendation.
- Reversible, low-risk ambiguity does not cause a pause; the model chooses the simplest viable option and continues.
- When multiple options are materially equivalent, the model prefers the simpler or more reversible option instead of asking the user.
- Recommendations remain evidence-based and contextual; the modifier must not turn the first or affirmative option into an automatic default.
- After a required user answer, autonomous recommendation mode resumes without needing the modifier to be re-entered.

## Relevant Files

- `commands/create-spec.md` - Defines contract discovery and AskQuestion decision gates.
- `commands/implement-spec.md` - Defines spec selection and execution-plan confirmation choices.
- `system-instructions.md` - Defines shared interaction guidance for Plan Mode and AskQuestion.

## Related Issues

- [2026-04-08-plan-mode-implementation-boundary](2026-04-08-plan-mode-implementation-boundary.md) - Also concerns preserving intent across Plan Mode and command decision boundaries.

## Notes

- The modifier controls workflow autonomy; `(Recommended)` communicates recommendation state when choices are shown.
- “Without human intervention” applies to Writ's discretionary decision gates. It cannot bypass platform-enforced approvals, permissions, or mode-switch confirmations.
- Automatic choices should remain visible in the command's output or resulting artifacts to prevent silent contract drift.
