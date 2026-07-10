# Story 5: Evidence-Bound Phase Knowledge

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 4

## User Story

**As a** Writ maintainer closing a roadmap phase
**I want to** record only durable, evidence-backed, non-duplicate cross-spec lessons and recurring drift patterns
**So that** phase knowledge remains trustworthy and useful without accumulating one-off observations or architectural decisions

## Acceptance Criteria

- [ ] Given phase-report and per-spec drift evidence at phase close, when Writ evaluates a candidate, then it qualifies only if it generalizes beyond one spec, names a supporting artifact or repeated drift pattern, is not substantively duplicated in the existing knowledge ledger, and remains below ADR blast radius.
- [ ] Given a qualifying candidate, when phase-close writeback runs, then Writ creates a conformant entry using the existing `.writ/knowledge/lessons/` schema and records the written entry in the phase report and phase execution state.
- [ ] Given a duplicate, one-off observation, weakly evidenced candidate, or ADR-scale decision, when Writ evaluates it, then no ledger entry is written and the phase report records the rejected candidate with a terse reason.
- [ ] Given no candidate or no candidate that satisfies every qualification rule, when the phase closes, then knowledge writeback is a valid no-op, no knowledge file is changed, and an empty candidate set produces no report section.
- [ ] Given an interrupted or resumed phase close, when knowledge writeback is reconciled against the ledger and phase state, then an already-recorded lesson is not written a second time.

## Implementation Tasks

- [ ] 5.1 Write focused fixtures and contract checks for qualifying lessons, duplicate detection, one-off and ADR-scale rejection, interrupted replay, and the no-candidate no-op.
- [ ] 5.2 Define the phase-close candidate, evidence citation, rejection reason, and written-entry state contract in `.writ/docs/phase-execution-state-format.md`.
- [ ] 5.3 Update `commands/implement-phase.md` to collect candidates from the phase report and per-spec drift logs, apply every qualification gate, and preserve no-op semantics.
- [ ] 5.4 Update `commands/knowledge.md` to deduplicate candidates substantively against `.writ/knowledge/` and emit only conformant `.writ/knowledge/lessons/` entries.
- [ ] 5.5 Integrate written and rejected candidate reporting with `knowledgeWritten` state so resume cannot duplicate a completed write.
- [ ] 5.6 Verify all acceptance criteria against qualifying, rejected, duplicate, resumed, and empty-input fixtures.
- [ ] 5.7 Verify all focused checks and repository evals pass without modifying the ledger for no-op cases.

## Notes

- Evidence must name a phase report, drift-log entry, failure record, or repeated observation; an unsupported summary is not sufficient.
- Substantive deduplication must compare meaning rather than filenames or exact text alone, while remaining conservative when equivalence is uncertain.
- Architectural decisions belong in ADRs and must not be downgraded into automatically written lessons.
- Story 4 supplies the terminal-failure, quarantine, and resume evidence that phase-close evaluation may consume.
- The main risk is noisy or repeated knowledge writeback; rejection and no-op behavior are first-class successful outcomes.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`Write knowledge`] — `technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** [`Knowledge writeback`] — `technical-spec.md` → `## Shadow Paths`
- **Business rules:** [`Rule 8 — Phase-close knowledge writeback creates only deduplicated, evidence-backed durable lessons or recurring drift patterns; no qualifying lesson means no write`] — `spec.md` → `### Business Rules`
- **Experience:** [`Primary User Journey step 7 — At phase close, record only qualifying durable knowledge`, `Interaction and Output Rules — output remains concise, terminal-oriented Markdown`] — `spec.md` → `## Experience Design`
