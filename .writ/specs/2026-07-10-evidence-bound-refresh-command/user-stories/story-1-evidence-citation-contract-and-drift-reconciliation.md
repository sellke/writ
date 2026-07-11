# Story 1: Evidence-Citation Contract and Drift Reconciliation

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer refining a command from real use
**I want to** be required to cite transcript evidence for every proposed amendment, with a clear rejection path when I can't, and docs that describe what the command actually does
**So that** the learning loop is falsifiable and the audit trail is honest — improvements are justified, guesses are visibly rejected, and no doc claims a feature the command lacks

## Acceptance Criteria

- [x] Given a `/refresh-command` run proposes an amendment, when Phase 3 renders the proposal, then it includes a structured **Evidence** block (transcript ID/path + short observable signal + affected command section) alongside Title, Rationale, Confidence, and Diff.
- [x] Given a proposal cannot cite transcript evidence, when Phase 4 prepares to apply it, then the amendment is rejected before any file write and recorded in `.writ/refresh-log.md` under `**Rejected:**` with reason `no evidence`.
- [x] Given an amendment's evidence would include chain-of-thought or a verbatim private transcript body, when the citation is composed, then only a transcript ID/path and a short observable signal are stored — never the private body.
- [x] Given `commands/status.md`, `README.md`, and `.writ/docs/refresh-log-format.md` describe `/refresh-command`, when the drift is reconciled, then there is no reference to a nonexistent "Phase 2.2", a single canonical `.writ/refresh-log.md` path, and transcript phrasing that matches the human-driven cited-evidence behavior.
- [x] Given a run reviews a command and applies zero amendments, when Phase 4 logs the outcome, then the review is recorded as a valid no-op that is exempt from the evidence requirement.

## Implementation Tasks

- [x] 1.1 Write failing verification greps capturing the target state (they fail today): a `**Evidence:**` block in `commands/refresh-command.md` Phase 3; no `Phase 2.2` string in `commands/status.md`; a single `.writ/refresh-log.md` path with no `.writ/state/refresh-log.md`; accurate (non-"scans agent transcripts") phrasing in `README.md`.
- [x] 1.2 Rewrite `commands/refresh-command.md` Phase 2–3 to require the structured Evidence citation per proposal (transcript ID/path + short observable signal + affected line/section) and add the Prime Directive privacy guard forbidding chain-of-thought and verbatim private bodies.
- [x] 1.3 Update `commands/refresh-command.md` Phase 4 to run the rejection path for unevidenced proposals, record applied amendments with their evidence, and record rejected candidates under `**Rejected:**` with a reason token.
- [x] 1.4 Align `.writ/docs/refresh-log-format.md`: replace `**Source transcript:**` with the mandatory structured Evidence block, fix the stale "Phase 5 / Phase 6 Promotion Review" references, remove or mark-unimplemented the promotion/batch optional fields, fix the `**Target file:**` path convention, and document `LEARNING_CONTRACT_SINCE = 2026-07-11` grandfathering.
- [x] 1.5 Reconcile `commands/status.md`: remove the "command identification logic in Phase 2.2 of refresh-command.md" reference, replace `.writ/state/refresh-log.md` with `.writ/refresh-log.md`, and reword the transcript-count heuristic / drop the `--batch` suggestion so guidance matches the actual command.
- [x] 1.6 Reconcile `README.md`: change "scans agent transcripts" / "Scans agent transcripts" (lines ~58 and ~139) to accurate cited-evidence, human-driven phrasing.
- [x] 1.7 Run the verification greps from 1.1 and `bash scripts/eval.sh` to confirm drift is reconciled and no existing check regressed.

## Notes

- Direction of reconciliation is decided in the parent spec (D4): **restore** evidence citation into the command; **redefine docs to reality** for unimplemented `--batch`/promotion mechanics. Do not re-implement `--batch`/`--last`/promotion.
- The Evidence block's observable signal is a short factual quote of an event (correction, retry, override, error). It is never reasoning or a private body.
- Reviewed-with-no-amendments is a valid outcome and exempt from evidence — there is nothing to justify when nothing is applied.
- This story touches `commands/refresh-command.md`, which Story 3 also edits; keep changes structural and localized to Phases 2–4 so Story 3's gate wiring appends cleanly.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Drift greps clean; `bash scripts/eval.sh` clean
- [x] Docs and command describe identical behavior
- [x] Prime Directive privacy honored in every citation example

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Parse refresh-log entry`, `Missing transcript citation`, `Private-content guard`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Evidence citation`, `Drift reconciliation`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rules 1, 2, 3, 6, 7, 9]
- **Decisions:** [`technical-spec.md` → `### D1 — Evidence Is Mandatory and Structured`, `### D2 — Rejection Is a First-Class, Logged Outcome`, `### D3 — Privacy Guard`, `### D4 — Drift Reconciliation Direction`]
- **Experience:** [`spec.md` → `### Primary User Journey` → Steps 3, 5, 6, `spec.md` → `### State Catalog`]
