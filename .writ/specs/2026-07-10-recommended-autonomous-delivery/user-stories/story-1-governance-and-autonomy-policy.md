# Story 1: Governance and Autonomy Policy

> **Status:** Completed ✅ (2026-07-10)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** replace the contract-level human gate with an explicit, observable, and resumable autonomy policy while reconciling existing governance
**So that** recommended delivery can proceed without contradictory instructions while retaining accountability at one immutable production approval boundary

## Acceptance Criteria

- [x] Given ADR-010 is accepted governance, when the superseding ADR is recorded, then it explicitly replaces the contract-level human gate and the prohibition on autonomous delivery, preserves the accountability objective through one explicit production approval for the exact reviewed PR head SHA, and retains opaque, unbounded unattended loops as a non-goal.
- [x] Given the active Phase 6 contract, lite spec, affected stories, and story index are governed by ADR-010, when they are reconciled, then they identify this spec as a prerequisite, distinguish Phase 6's normal multi-spec supervision from single-spec `--recommend` delivery, and contain no claim that every contract or User Challenge must be human-decided.
- [x] Given the product roadmap still defines the prior supervised ceiling, when its Phase 6 and parking-lot language is updated, then it reflects the superseding decision, preserves Phase 6's still-valid fresh-context, dependency, quarantine, health, knowledge, and Ralph-retirement scope, and does not imply that multi-spec `/implement-phase --recommend` is included.
- [x] Given `system-instructions.md` owns Writ's hard behavioral constraints, when the autonomy policy is added, then planning commands still stop after artifact creation by default, `--recommend` is the explicit narrow exception, automatic choices require observable evidence and durable audit summaries, interruptions are resumable, and critical ambiguity or hard blockers still pause safely.
- [x] Given all governance surfaces have been changed, when focused evals and contradiction searches run, then the new ADR, this locked spec, Phase 6 artifacts, roadmap, and `system-instructions.md` agree on the observable/resumable ceiling and one production approval boundary without weakening branch protection, authentication, or other platform policy.

## Implementation Tasks

- [x] 1.1 Write failing focused assertions in `scripts/eval.sh` for the superseding ADR linkage, this spec's prerequisite relationship to Phase 6, the `system-instructions.md` `--recommend` exception, the one-production-approval boundary, and the absence of superseded contract-level-gate language from active Phase 6 and roadmap surfaces.
- [x] 1.2 Create `.writ/decision-records/adr-013-recommended-autonomous-delivery.md` as an accepted decision that explicitly supersedes the conflicting portions of ADR-010, preserves its accountability rationale, defines the observable/session-started/resumable ceiling and immutable production gate, and rejects opaque unbounded execution.
- [x] 1.3 Reconcile `.writ/specs/2026-07-09-phase6-autonomy-ceiling/spec.md` and `spec-lite.md` so this spec is a prerequisite, normal Phase 6 supervision remains coherent, and contradictory contract-level and User Challenge requirements are replaced with the new evidence-based select-or-pause boundary.
- [x] 1.4 Update the affected Phase 6 story files and `user-stories/README.md`, especially Story 3's unconditional human-decision language and Story 7's autonomy-ceiling wording, without changing unrelated dependencies, task counts, or acceptance scope.
- [x] 1.5 Update `.writ/product/roadmap.md` so Phase 6 sequencing and autonomy language recognize the superseding ADR and this prerequisite while preserving the exclusion of multi-spec recommended execution and the still-valid Phase 6 deliverables.
- [x] 1.6 Update `system-instructions.md` with the hard governance contract: normal planning commands retain their terminal boundary; `--recommend` is the narrow explicit exception; autonomous progress must remain evidence-backed, observable, auditable, and resumable; and production, critical ambiguity, and hard platform blockers retain explicit pause rules.
- [x] 1.7 Verify every acceptance criterion, run `bash scripts/eval.sh`, inspect the complete governance diff, and perform targeted searches across active ADR, Phase 6, roadmap, and system-instruction surfaces to prove that no contradictory autonomy language remains.

## Notes

- This story changes the governing contract before behavioral implementation. It should land first so later stories do not implement against two accepted but incompatible autonomy ceilings.
- Supersession should be surgical: ADR-010's accountability rationale and Ralph-era warning against opaque unbounded loops remain valuable; its contract-level human gate and blanket prohibition on autonomous delivery do not.
- Phase 6 remains a separate multi-spec orchestration effort. This story reconciles its governance but must not expand `--recommend` into `/implement-phase`, which the locked scope explicitly excludes.
- The select-or-pause taxonomy is established here only as a governance boundary. Story 2 owns the detailed recommendation labels, evidence rules, equivalence handling, and pause classifications.
- Durable audit summaries record decisions, evidence, alternatives, and risk—not private chain-of-thought. The production approval is valid only for the reviewed PR head SHA.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`spec.md → ## Experience Design → ### Error Experience → Critical ambiguity`, `spec.md → ## Experience Design → ### Error Experience → Interrupted session`, `spec.md → ## Experience Design → ### Error Experience → Merge conflict or branch protection`]
- **Shadow paths:** [`spec.md → ## Experience Design → ### Happy Path` — complete recommended delivery through one explicit approval, merge, and release; `spec.md → ## Implementation Approach → ### Explicit State Machine` — observable transitions with persisted evidence and safe retries]
- **Business rules:** [`spec.md → ## Detailed Requirements → ### R1 — Governance Supersession`, `spec.md → ## Specification Contract → ### Business Rules → Rule 5` — critical risks and ambiguity pause, `Rule 8` — production approval is explicit, `Rule 12` — platform protections are never bypassed]
- **Experience:** [`spec.md → ## Specification Contract → ### Experience Design → Human gate`, `spec.md → ## Experience Design → ### State Catalog → Deliberating, Awaiting approval, and Blocked`, `spec.md → ## Experience Design → ### Feedback and Audit Model`]

---

## What Was Built

**Implementation Date:** 2026-07-10

### Files Created

1. **`.writ/decision-records/adr-013-recommended-autonomous-delivery.md`**
   - Supersedes ADR-010's conflicting autonomy restrictions while preserving its accountability rationale.

### Files Modified

- **`scripts/eval.sh`**
  - Added focused governance assertions and active-surface contradiction checks.
- **Phase 6 spec, lite spec, Stories 3 and 7, and story index**
  - Established this spec as the prerequisite and replaced contradictory autonomy language.
- **`.writ/product/roadmap.md`, `.writ/product/mission.md`, and `.writ/product/mission-lite.md`**
  - Aligned product sequencing and autonomy boundaries with ADR-013.
- **`system-instructions.md` and `cursor/writ.mdc`**
  - Added the narrow, explicit `--recommend` exception and its evidence, audit, resume, and pause requirements.
- **`.writ/decision-records/adr-012-ralph-deprecation.md`**
  - Distinguished bounded recommended delivery from deprecated opaque loop execution.

### Implementation Decisions

1. **Surgical supersession** — ADR-010 remains historical; ADR-013 supersedes only its conflicting restrictions.
2. **Explicit command support** — The autonomy exception applies only when a command explicitly supports `--recommend`.
3. **Immutable production boundary** — One explicit approval is bound to the exact reviewed PR head SHA.
4. **Multi-spec exclusion** — `/implement-phase --recommend` remains out of scope.

### Test Results

**Verification:** Focused governance eval, full Tier 1 eval, shell syntax validation, diff checks, and targeted contradiction searches all passed.

- ✅ 31 focused governance assertions passed with zero findings.
- ✅ All nine full eval checks passed.
- ✅ No stale active-policy contradictions remained.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iterations
- **Drift:** None
- **Security:** Low risk
- **Boundary Compliance:** Compliant; architecture-required mission, ADR-012, and Cursor mirror surfaces were explicitly reconciled.

### Deviations from Spec

None
