# ADR-013: Recommended Autonomous Delivery

> Status: Accepted
> Date: 2026-07-10
> Deciders: Adam (product owner)
> Supersedes: Conflicting portions of [ADR-010](adr-010-supervised-autonomy-ceiling.md)
> Governs: `2026-07-10-recommended-autonomous-delivery`

## Context

ADR-010 correctly identified accountability as Writ's autonomy constraint, but implemented that objective as a contract-level human gate and a blanket prohibition on autonomous delivery. The recommended-delivery contract provides a narrower and more verifiable accountability mechanism: observable choices, resumable state, reviewable preview evidence, and one immutable production boundary.

ADR-010 remains historical and retains useful rationale. This ADR supersedes only its contract-level human gate, blanket autonomy ceiling, and requirement that every User Challenge be human-decided.

## Decision

Writ may perform session-started, observable, and resumable autonomous delivery only when the invoked command explicitly supports `--recommend`. Normal planning commands still stop after producing their documented artifacts.

Within that narrow mode:

1. Automatic choices require observable evidence and a durable audit summary of the decision, evidence, material alternatives, risk, reversibility, and result. Audit summaries exclude private chain-of-thought, prompts, transcripts, and hidden scratch work.
2. Low-risk, reversible choices with defensible evidence may be selected automatically. Missing evidence, critical ambiguity, safety or contract risk, and hard platform blockers pause with a bounded question or actionable blocker.
3. Progress and external mutations are persisted and reconciled before retry so interruption remains safely resumable.
4. Exactly one explicit production approval authorizes protected merge and the recommended release for the exact reviewed PR head SHA. Any head change invalidates the approval and requires refreshed checks, preview evidence, UAT, and approval.
5. Required checks, branch protection, required reviews, authentication, authorization, and provider policy are never bypassed.

This decision applies to single-spec recommended delivery. Multi-spec `/implement-phase --recommend` remains excluded. Phase 6 continues to govern normal multi-spec `/implement-phase` execution with one routine plan confirmation, fresh contexts, explicit dependencies, quarantine, health reporting, and knowledge writeback.

Opaque, unbounded unattended loops remain a non-goal. Recommended delivery is bounded by one locked spec, one active session-started execution, persisted state, finite retry policy, and the immutable production approval boundary.

## Consequences

**Positive:** Writ can carry a reviewed contract to a release candidate without routine interruption while preserving accountability at an observable production boundary.

**Negative:** The workflow has more state and reconciliation obligations. Projects without required provider capabilities stop before production rather than degrading policy.

**Compatibility:** ADR-010 remains unchanged as historical context. Active mission, roadmap, Phase 6, Ralph-retirement, system-instruction, and adapter surfaces must cite or conform to this superseding decision.

## Rejected Alternatives

- **Keep the contract-level human gate:** rejected because it blocks evidence-supported, reversible progress without strengthening production accountability.
- **Remove all human gates:** rejected because production remains the irreversible accountability boundary.
- **Restore Ralph-style unattended looping:** rejected because opaque, unbounded execution still outruns meaningful review.
- **Enable multi-spec recommended delivery immediately:** rejected until single-spec staging, approval binding, and recovery are proven.
