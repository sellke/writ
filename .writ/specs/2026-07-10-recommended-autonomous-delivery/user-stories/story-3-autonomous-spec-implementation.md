# Story 3: Autonomous Spec-to-Implementation Orchestration

> **Status:** Completed ✅ (2026-07-10)
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ user
**I want to** start recommended delivery from spec creation or an existing locked spec and have Writ carry the mode through verified implementation
**So that** the complete spec package, recommendation history, and execution progress remain observable and resumable without routine intermediate gates

## Acceptance Criteria

- [x] Given `/create-spec --recommend` has produced a locked contract, when orchestration advances toward implementation, then the complete structurally valid spec package and tracked `recommendation-log.md` exist before `/implement-spec` receives the active recommendation mode.
- [x] Given a locked existing spec, when the user invokes `/implement-spec --recommend`, then Writ starts at implementation without regenerating or silently rewriting the contract and executes the story DAG through review, testing, documentation, and integration verification without routine intermediate gates.
- [x] Given recommended orchestration makes an automatic choice or completes a workflow transition, when the result is persisted, then the concise decision audit is appended to `{spec}/recommendation-log.md` and canonical resumable progress is stored in `.writ/state/recommend-execution-{id}.json` with the relevant artifact or completion identifier.
- [x] Given an interrupted run or contradictory saved state, when recommended orchestration resumes, then it reconciles persisted state with repository reality, skips already completed work, and either continues safely or stops on the mismatch without assuming success.
- [x] Given `--recommend` is absent or combined with an unsupported invocation, when `/create-spec` or `/implement-spec` starts, then existing interactive behavior remains compatible and invalid combinations fail with valid invocation guidance before mutation.

## Implementation Tasks

- [x] 3.1 Add `scripts/eval.sh` fixtures that cover create-to-implement mode propagation, direct existing-spec entry, complete-package preconditions, normal-mode compatibility, unsupported combinations, interruption resume, and contradictory-state blocking.
- [x] 3.2 Define and document the recommended execution-state and recommendation-log contracts, including stable execution and decision identifiers, story/gate progress, transition evidence, completion identifiers, and repository-reconciliation rules.
- [x] 3.3 Update `commands/create-spec.md` to parse `--recommend` once, create and structurally validate the complete spec package plus `recommendation-log.md`, initialize canonical execution state, and explicitly pass recommendation mode into implementation.
- [x] 3.4 Update `commands/implement-spec.md` to accept propagated or direct recommendation mode, preserve existing contracts, execute the story DAG through all verification gates, return a structured outcome to top-level orchestration, and retain normal behavior when the modifier is absent.
- [x] 3.5 Implement durable transition logging and resumable reconciliation across `commands/create-spec.md`, `commands/implement-spec.md`, and `.writ/state/recommend-execution-{id}.json`, ensuring retries do not repeat completed work and stale or contradictory state blocks safely.
- [x] 3.6 Verify every acceptance criterion against the eval fixtures and inspect generated spec packages, tracked audit entries, and ephemeral state for the required separation and identifiers.
- [x] 3.7 Verify all evals and repository validation checks pass and confirm existing non-`--recommend` create-spec and implement-spec flows remain unchanged.

## Notes

- `commands/create-spec.md` remains contract-first: recommendation mode may remove routine choice gates, but implementation cannot begin until the full spec package exists and passes structural validation.
- `commands/implement-spec.md` remains the story-DAG orchestrator. Recommended mode changes continuation and outcome handling, not dependency ordering or the existing review, testing, documentation, and integration gates.
- Keep tracked audit history and ephemeral runtime data separate. `{spec}/recommendation-log.md` records concise decisions, evidence, material alternatives, risk/reversibility, selection source, and resulting identifiers; `.writ/state/recommend-execution-{id}.json` is canonical runtime state and must remain gitignored.
- Resume behavior must reconcile saved state with repository reality before acting. Contradictory or stale evidence is a blocker, not permission to infer success.
- This story depends on Story 2's recommendation and pause semantics. It hands a verified implementation outcome to Story 4; PR creation, CI/preview discovery, UAT, approval, merge, and release are outside this story.
- The narrow `--recommend` exception must not alter normal command behavior, store private chain-of-thought, or broaden into multi-spec `/implement-phase --recommend`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [No defensible recommendation, Critical ambiguity, Interrupted session] — from `spec.md → ## Experience Design → ### Error Experience`
- **Shadow paths:** [Create the complete spec package before implementation, Execute all stories through integration verification] — from `spec.md → ## Experience Design → ### Happy Path`
- **Business rules:** [Rule 2 (automatic choices require evidence), Rule 3 (equivalent choices favor simplicity and reversibility), Rule 4 (required answers preserve and resume recommendation mode), Rule 5 (critical risks and blockers still pause)] — from `spec.md → ## Specification Contract → ### Business Rules`; [R3 — Mode Propagation and Orchestration, R4 — Durable State and Recommendation Log] — from `spec.md → ## Detailed Requirements`
- **Experience:** [Entry Points (create-spec and implement-spec recommended entry behavior), Planning and Implementing states (package generation before story execution), Feedback and Audit Model (durable decision-entry fields), Blocked state (actionable blocker with safe resume path)] — from `spec.md → ## Experience Design → ### Entry Points`, `spec.md → ## Experience Design → ### State Catalog`, and `spec.md → ## Experience Design → ### Feedback and Audit Model`

---

## What Was Built

**Implementation Date:** 2026-07-10

### Files Created

1. **`scripts/recommend-state.py`**
   - Dependency-free validator and reducer for recommended execution state, package identity, audit integrity, ownership, reconciliation, and structured results.
2. **`scripts/eval-recommend-state-adversarial.py`**
   - Disposable-repository adversarial scenarios for state and reconciliation behavior.
3. **`.writ/docs/recommended-delivery-state-format.md`**
   - Canonical v1 runtime, package, result, audit, worktree, and amendment-chain contract.
4. **`recommendation-log.md`**
   - Tracked audit ledger for this specification.

### Files Modified

- **`commands/_preamble.md`, `commands/create-spec.md`, `commands/implement-spec.md`, and `commands/implement-story.md`**
  - Added explicit recommended branches, fail-before-mutation matrices, package validation, structured propagation/results, ownership handshake, and verified-implementation return boundary.
- **Cursor, Claude Code, and Codex adapters**
  - Added equivalent context transport, safe state replacement, ownership, and resume mappings.
- **`scripts/eval.sh`**
  - Added focused static and executable Story 3 validation.
- **Install, update, unlink, manifest, and catalog surfaces**
  - Distributed and tracked the helper and authoritative state contract.
- **Technical specification**
  - Synchronized unreleased v1 evidence and reconciliation fields.

### Implementation Decisions

1. **Executable source of truth** — A dependency-free helper enforces the documented state contract.
2. **Evidence-derived completion** — Saved completion markers are accepted only when package, result, nested state, plan, repository, ownership, and integration evidence agree.
3. **Immutable versus mutable identity** — Locked semantic package identity is separate from append-only recommendation logs and authorized spec-lite amendment chains.
4. **Fail-closed normalization** — Malformed state, CLI input, and nested results produce canonical blocked output.
5. **Verified-implementation ceiling** — Story 4/5 provider and production fields remain inert.

### Test Results

**Verification:** Focused, adversarial, full repository, installer lifecycle, syntax, catalog, diff, and lint checks passed.

- ✅ 162/162 focused Story 3 scenarios passed.
- ✅ 50/50 adversarial scenarios passed.
- ✅ 36/36 static assertions passed.
- ✅ All 11 full repository eval checks passed.
- ✅ 36/36 distribution lifecycle scenarios passed across Cursor, Claude Code, and Codex.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iterations in the successful rerun
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Compliant

### Deviations from Spec

None
