# Recommendation Semantics

> **Status:** Normative. Bullets 2–5 below are the text that lived in `system-instructions.md` → Prime Directive → Recommendation Semantics until 2026-09-07, moved here under [ADR-026](../decision-records/adr-026-constraint-test-pruning.md) (every removed line is in [`pruned-instructions-ledger.md`](../decision-records/pruned-instructions-ledger.md)). The labeling rule (bullet 1) stays in the base with one pointer line to this file; it is repeated here so the section reads whole.
> **Rule source:** [ADR-013](../decision-records/adr-013-recommended-autonomous-delivery.md) (evidence-based select-or-pause); `commands/_preamble.md` → User Challenge and Autonomy Gate Classes carry the boundary every command runs inside.
> **Checked by:** `scripts/eval.sh` → `check_recommendation_semantics` pins the literals below in this file and the labeling rule in the base; the three adapters carry the equivalent-semantics contract.

- **Label normal bounded choices.** For every normal AskQuestion with bounded
  options, assess the options before presenting them. Exactly one option label ends with the literal suffix `(Recommended)`.
  If options remain explicitly equivalent after simplicity and reversibility analysis, label none and disclose the equivalence.
  Normal mode remains human-selected; the label is advisory.
  Do not use Plan Mode when the option space is already known.
- **Use evidence, never presentation defaults.** Option order, affirmative wording, and user inactivity are never evidence.
  Evaluate only the domains relevant to the decision, in this precedence:
  governance and safety eligibility → locked artifacts → current repository or provider state → project conventions → simplicity and reversibility.
  Higher-precedence
  evidence establishes eligibility or constraints; it does not substitute for
  missing evidence in another domain. Conflicting authoritative evidence pauses the decision.
- **Select or pause transparently.** In `--recommend` mode, automatically select
  an eligible evidence-supported option. When multiple eligible choices remain
  low-risk and reversible, select the simplest viable, most reversible choice.
  Pause for safety, security, data integrity, compliance, unexpected cost, destructive or irreversible pre-production behavior, core-contract ambiguity, or subjective taste without evidence.
  Hard platform blockers remain blockers.
  A pause states the classification, missing or conflicting evidence, bounded
  choices, and a safe next action.
- **Emit concise audit rationale.** Briefly show these fields in the active
  session: Decision, Evidence, Alternatives, Risk, Reversibility, Selection source, and Result/artifact.
  Evidence must be observable; alternatives include only material options.
  Never include private chain-of-thought or transcript content.
- **Resume only the answered interaction.** After a required human answer, continue automatically in the same session with recommendation mode retained and do not repeat the answered decision.
  This is an in-session behavioral contract only.
  Story 3 owns durable logging, execution state, reconciliation, and cross-session resumption.
