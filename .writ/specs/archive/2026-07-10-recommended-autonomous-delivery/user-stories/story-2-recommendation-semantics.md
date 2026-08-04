# Story 2: Recommendation Semantics

> **Status:** Completed ✅ (2026-07-10)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user
**I want to** see a clearly labeled, evidence-backed recommendation for normal interactive decisions and have `--recommend` apply the same policy automatically
**So that** Writ can make routine choices transparently, pause at meaningful risk boundaries, and continue after required input without relying on option order or hidden reasoning

## Acceptance Criteria

- [x] Given a normal interactive decision with bounded options, when Writ presents the choice through AskQuestion, then exactly one evidence-backed option ends with `(Recommended)` unless the options are explicitly equivalent, and neither position nor affirmative wording determines the recommendation.
- [x] Given `--recommend` mode and sufficient repository, locked-artifact, provider-state, or project-convention evidence, when Writ evaluates bounded options, then it automatically selects the supported option, resolves low-risk reversible ambiguity toward the simplest viable choice, and emits a concise rationale identifying the evidence, material alternatives, and risk/reversibility without private chain-of-thought.
- [x] Given a decision involving safety, security, data integrity, compliance, unexpected cost, destructive or irreversible behavior before production approval, core-contract ambiguity, or subjective taste without usable evidence, when `--recommend` evaluates the decision, then it pauses with the applicable classification, missing evidence, bounded choices, and a safe next action.
- [x] Given an automatic or human-approved recommendation decision, when the choice is completed, then its decision, evidence, material alternatives, risk/reversibility, selection source, and resulting artifact or identifier are available for the tracked recommendation log and briefly shown in the active session.
- [x] Given recommendation mode pauses for a required human answer, when the user supplies that answer, then the workflow resumes automatically with recommendation mode still active and does not repeat the completed decision.

## Implementation Tasks

- [x] 2.1 Write `scripts/eval.sh` fixtures first for normal-mode labels, non-positional selection, evidence-based automatic choice, simpler reversible tie-breaking, each pause class, concise rationale output, and mode resumption after a required answer.
- [x] 2.2 Define the shared recommendation policy in `system-instructions.md`, preserving AskQuestion for bounded options and Plan Mode for open-ended discovery while specifying the exact `(Recommended)` label contract.
- [x] 2.3 Define evidence precedence, automatic-selection eligibility, equivalent-choice handling, and the prohibition on positional or affirmative defaults in `system-instructions.md`.
- [x] 2.4 Define the pause taxonomy, bounded blocker response, concise rationale record, active-session feedback, and automatic mode-resumption contract in `system-instructions.md`, explicitly excluding private chain-of-thought.
- [x] 2.5 Align `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md` with equivalent recommendation, pause, rationale, and resumption semantics without introducing provider-specific policy.
- [x] 2.6 Verify every acceptance criterion against the shared policy and adapter guidance, including the boundary between this story's decision-record contract and Story 3's durable state/log implementation.
- [x] 2.7 Run all recommendation eval fixtures and verify normal interactive behavior remains backward compatible apart from the required recommendation labels.

## Notes

- Story 1 must land first so this behavioral policy is built on the reconciled autonomy ceiling rather than conflicting governance.
- `system-instructions.md` is the authoritative shared-policy surface. Command files should supply phase-specific evidence and bounded options; they should not redefine recommendation semantics.
- AskQuestion remains the mechanism for bounded choices. Plan Mode remains the mechanism for discovery where the option space is not yet known.
- A recommendation is an assessment supported by observable evidence, not a UI default. Option order, affirmative phrasing, or inactivity are never evidence.
- The rationale is an audit summary: decision, evidence, material alternatives, risk/reversibility, selection source, and resulting artifact or identifier. It must not contain private chain-of-thought or transcript dumps.
- This story defines the rationale/logging contract. Story 3 implements the durable `recommendation-log.md`, execution state, propagation, and idempotent resume mechanics that consume it.
- Adapter drift is a material risk: platform-specific interaction APIs may differ, but their observable recommendation and pause behavior must remain equivalent.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [No defensible recommendation, Critical ambiguity] — `spec.md → ## Experience Design → ### Error Experience`
- **Shadow paths:** [Normal interactive bounded choice, Deliberate with evidence-backed automatic choices, Required human answer and automatic mode resumption] — `spec.md → ## Experience Design → ### Entry Points`; `spec.md → ## Experience Design → ### Happy Path`
- **Business rules:** [Normal interactive recommendations use `(Recommended)`, automatic choices require evidence rather than option order, equivalent choices favor simpler reversible options, required answers preserve recommendation mode, defined critical risks pause] — `spec.md → ## Detailed Requirements → ### R2 — Recommendation Policy`
- **Experience:** [Selected recommendations are shown and appended to the durable audit summary, recommendation entries record evidence and risk without hidden reasoning, blockers expose missing evidence and bounded choices] — `spec.md → ## Experience Design → ### Feedback and Audit Model`; `spec.md → ## Experience Design → ### Error Experience`; `spec.md → ## Implementation Approach → ### Shared Policy, Thin Command Integration`

---

## What Was Built

**Implementation Date:** 2026-07-10

### Files Created

[None created]

### Files Modified

- **`system-instructions.md` and `cursor/writ.mdc`**
  - Defined the canonical recommendation, evidence, pause, rationale, and same-session resumption policy.
- **`adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md`**
  - Mapped stable option identity and equivalent observable recommendation semantics to each platform.
- **`scripts/eval.sh`**
  - Added focused recommendation-policy fixtures and adapter parity assertions.

### Implementation Decisions

1. **Shared policy authority** — System instructions own recommendation semantics; adapters only map interaction mechanics.
2. **Domain-scoped evidence** — Governance, locked artifacts, current state, conventions, then simplicity/reversibility determine eligible choices.
3. **Explicit equivalence** — Genuinely equivalent options receive no recommendation label and disclose equivalence.
4. **Story boundary** — Resumption is same-session only; durable state and reconciliation remain Story 3.

### Test Results

**Verification:** Focused recommendation eval, full Tier 1 eval, shell syntax, policy parity, and diff validation passed.

- ✅ 27 focused recommendation assertions passed.
- ✅ All ten full eval checks passed.
- ✅ Story 3 persistence and command orchestration remained absent.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Low risk
- **Boundary Compliance:** Compliant

### Deviations from Spec

None
