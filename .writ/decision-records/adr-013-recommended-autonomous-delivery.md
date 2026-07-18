# ADR-013: Recommended Autonomous Delivery

> Status: Accepted
> Date: 2026-07-10 (revised 2026-07-17)
> Deciders: Adam (product owner)
> Supersedes: Conflicting portions of [ADR-010](adr-010-supervised-autonomy-ceiling.md)
> Governs: `2026-07-10-recommended-autonomous-delivery`, `2026-07-17-recommend-redistribution`

## Context

ADR-010 correctly identified accountability as Writ's autonomy constraint, but implemented that objective as a contract-level human gate and a blanket prohibition on autonomous delivery. The recommended-delivery contract provides a narrower and more verifiable accountability mechanism: observable choices, resumable state, and a human-owned production boundary.

ADR-010 remains historical and retains useful rationale. This ADR supersedes only its contract-level human gate, blanket autonomy ceiling, and requirement that every User Challenge be human-decided.

## Decision

Writ may perform session-started, observable, and resumable autonomous work only when the invoked command explicitly supports `--recommend`. Normal planning commands still stop after producing their documented artifacts.

`--recommend` lives on exactly two commands:

- **`create-spec --recommend`** autonomously authors a locked, validated spec package from evidence — auto-adopting the contract lock, story decomposition, sub-spec set, and visual-reference default, and recording each material decision in `recommendation-log.md` — then **stops**. It never triggers implementation. It is invokable standalone and is the mode `implement-phase --recommend` passes down for missing specs.
- **`implement-phase --recommend`** is the sole end-to-end loop: it auto-authors missing specs (via `create-spec --recommend`), auto-accepts its decomposition and execution-plan confirmations, and runs `implement-spec` per spec through the existing isolated-lane flow. Its terminal scope is the honest completion report with manual UAT handoff.

`implement-spec`, `ship`, and `create-uat-plan` carry no `--recommend` flag. `implement-spec` is an explicit execute command with no confirmation gate: invoking it runs the plan.

Within recommended mode:

1. Automatic choices require observable evidence and a durable audit summary of the decision, evidence, material alternatives, risk, reversibility, and result. Audit summaries exclude private chain-of-thought, prompts, transcripts, and hidden scratch work.
2. Low-risk, reversible choices with defensible evidence may be selected automatically. Missing evidence, critical ambiguity, safety or contract risk, and hard platform blockers pause with a bounded question or actionable blocker.
3. Progress and external mutations are persisted and reconciled before retry so interruption remains safely resumable.
4. No `--recommend` command merges, opens PRs, or releases. Production remains a human decision.
5. Required checks, branch protection, required reviews, authentication, authorization, and provider policy are never bypassed.

The autonomous staging-through-production flow is deferred ("bigger loops later"). Its preserved design binds one explicit production approval to the exact reviewed PR head SHA — any head change invalidates the approval and requires refreshed checks, preview evidence, UAT, and approval. The staging machinery (`scripts/recommend-state.py` staging reducers and `.writ/docs/recommended-delivery-state-format.md`) is kept dormant as that design, not deleted; no current command reaches it, and the eval suite keeps it falsifiable until the work resumes.

Opaque, unbounded unattended loops remain a non-goal. Recommended execution is session-started and finite — bounded to one authored spec or one roadmap phase, with persisted state and a finite retry policy. Phase 6 continues to govern normal multi-spec `/implement-phase` execution with one routine plan confirmation, fresh contexts, explicit dependencies, quarantine, health reporting, and knowledge writeback.

## Consequences

**Positive:** Compartmentalized commands keep each responsibility legible — authoring is authoring, implementation is implementation — while the phase loop carries a roadmap phase to implemented specs without routine interruption, preserving accountability at the human production boundary.

**Negative:** The workflow has more state and reconciliation obligations, and the deferred staging design carries maintenance weight as dormant machinery until the bigger-loop work resumes.

**Compatibility:** ADR-010 remains unchanged as historical context. Active mission, roadmap, Phase 6, Ralph-retirement, system-instruction, and adapter surfaces must cite or conform to this superseding decision.

## Rejected Alternatives

- **Keep the contract-level human gate:** rejected because it blocks evidence-supported, reversible progress without strengthening production accountability.
- **Remove all human gates:** rejected because production remains the irreversible accountability boundary.
- **Restore Ralph-style unattended looping:** rejected because opaque, unbounded execution still outruns meaningful review.
- **Single-spec delivery through autonomous staging and production approval as the first cut (the original 2026-07-10 shape):** revised out on 2026-07-17. Carrying one spec through a production-approval boundary put autonomy at the wrong seam; redistributing `--recommend` to authoring and the phase loop keeps commands legible and defers the production flow until the bigger-loop design is proven.

## Revision History

- **2026-07-10:** Accepted — single-spec recommended delivery through a staging/production-approval boundary; `/implement-phase --recommend` excluded.
- **2026-07-17:** Revised — `--recommend` redistributed to `create-spec` (author and stop) and `implement-phase` (end-to-end phase loop); the staging-through-production flow deferred with its machinery kept dormant.
