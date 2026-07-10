# Story 3: Contract-Preserving User Challenges

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer supervising autonomous phase execution
**I want to** receive or audit a structured User Challenge when a decision would degrade roadmap scope, a locked specification contract, or exit criteria
**So that** consequential scope choices follow an evidence-based select-or-pause boundary without adding interruption or special framing to ordinary failures and already-answered decisions

## Acceptance Criteria

- [ ] Given a nested command encounters a choice that would weaken roadmap scope, the locked spec contract, or exit criteria, when it returns its structured result, then the result contains the trigger and all four required User Challenge parts; a defensible low-risk reversible choice may return an evidence-backed selection, while missing evidence, critical ambiguity, or material risk returns `status: challenge_required` with selectable options.
- [ ] Given `/implement-phase` receives a valid selected or `challenge_required` result, when it handles that result, then it presents or persists **What the roadmap/spec said**, **What Writ recommends**, **What context may be missing**, and **Cost if the recommendation is wrong**; it proceeds automatically only for the audited evidence-backed selection and otherwise uses one explicit `AskQuestion` before scope-changing action.
- [ ] Given the maintainer has not yet answered a valid User Challenge, when phase state is written or execution is resumed, then the unresolved challenge remains persisted and execution does not pass the challenged decision.
- [ ] Given the maintainer selects a challenge option, when `/implement-phase` records and applies the choice, then phase state preserves the challenge, selected option, and decision timestamp for resume and audit.
- [ ] Given an ordinary progress event, transient or terminal failure, malformed nested challenge, or decision already answered by repository artifacts, when the orchestrator classifies it, then it uses the existing progress, failure, or contract-error path and does not render User Challenge framing.

## Implementation Tasks

- [ ] 3.1 Write focused contract fixtures for qualifying scope/exit-criteria challenges, ordinary failures, already-answered decisions, malformed challenge payloads, unresolved resume, and resolved-decision persistence.
- [ ] 3.2 Define the four-part User Challenge trigger, payload, options, and decision contract in `commands/_preamble.md` and `.writ/docs/phase-execution-state-format.md`.
- [ ] 3.3 Update `commands/implement-spec.md` so nested execution applies the evidence-based select-or-pause rule, returning audited low-risk reversible selections or `challenge_required` for missing evidence, critical ambiguity, and material risk.
- [ ] 3.4 Update `commands/implement-phase.md` to validate returned challenges, present valid choices through `AskQuestion`, pause before scope-changing action, and route ordinary failures or malformed payloads to their normal handling.
- [ ] 3.5 Implement atomic persistence of unresolved and resolved challenges, including selected option and decision timestamp, so resume reconstructs the exact escalation state without asking an already-recorded decision again.
- [ ] 3.6 Verify all acceptance criteria with sandbox cases covering the qualifying path, non-qualifying failures, malformed payload rejection, interruption/resume, and audit state.
- [ ] 3.7 Run the repository's contract/eval checks and confirm all tests pass without changing the one-confirmation routine execution contract.

## Notes

- The challenge threshold is semantic and narrow: structured framing applies only when a proposed choice would weaken roadmap scope, a locked spec contract, or exit criteria. It must not become a generic wrapper for uncertainty, progress, retries, or failures.
- Story 2 supplies the fresh-subagent structured-result boundary. This story extends that boundary with `challenge_required`; it does not alter lane creation, merge, or quarantine mechanics.
- `/implement-phase` is the sole presenter and orchestration owner. Nested commands return an audited evidence-supported selection or the unresolved challenge so the parent can preserve one session and a durable audit trail.
- Challenge validation must reject omitted required fields as a contract error without misclassifying the malformed payload as either a User Challenge or an ordinary implementation failure.
- State updates must preserve unknown compatible fields and use the phase state's atomic-write behavior so interruption cannot leave a partially resolved decision.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Present User Challenge`]
- **Shadow paths:** []
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 6 (fresh subagents return structured results while the orchestrator owns escalation), `spec.md` → `### Detailed Requirements` → `R3 — User Challenge Escalation`]
- **Experience:** [`spec.md` → `### State Catalog` → `Scope degradation proposed`, `spec.md` → `### User Challenge Format`, `spec.md` → `### Interaction and Output Rules` → phase plan is the only routine confirmation, `technical-spec.md` → `### D5 — User Challenge Is a Structured Escalation`, `technical-spec.md` → `## Interaction Edge Cases` → `Scope challenge during retry`]
