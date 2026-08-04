# Story 7: Integration Testing & Dogfooding

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1, Story 2, Story 3, Story 4, Story 5, Story 6 (all previous stories)

## User Story

**As a** solo developer validating that Writ's Phase 1 features work as designed
**I want to** run end-to-end dogfooding scenarios that exercise all Phase 1 features together on real tasks
**So that** I can prove Phase 1 is complete — every feature works in concert, and Writ validates Writ

## Acceptance Criteria

- [x] **AC1:** Given I run `/prototype` on a small improvement to an existing Writ command, when the prototype completes, then the full flow (quick contract → coding → lint/typecheck → summary) finishes in under 5 minutes of human wall-clock time.
- [x] **AC2:** Given I run `/implement-story` on 5 stories that naturally produce some spec drift, when the full pipeline runs with spec-healing enabled, then real drift is detected in at least 3 of the 5 runs, with zero false positives (no drift flagged where spec and implementation actually align).
- [x] **AC3:** Given I run `/refresh-command` on transcripts from the prototype and implement-story sessions, when the command completes, then at least one actionable improvement is proposed and applied per command analyzed.
- [x] **AC4:** Given I run `/refresh-command refresh-command --last` (bootstrap validation), when the command completes, then it successfully scans its own transcript, identifies friction patterns, and proposes at least one improvement — proving the learning loop works on itself.
- [x] **AC5:** Given all dogfood scenarios have run, when I verify integration, then the command overlay system preserved local changes, `drift-log.md` was populated correctly for stories with drift, and no feature conflicts or regressions are observed.

## Implementation Tasks

- [x] 7.1 Define the dogfood validation checklist — document the 6 scenarios (prototype improvement, implement-story with drift, refresh on prototype/implement transcripts, overlay preservation, drift-log verification, bootstrap refresh); define measurement criteria (wall-clock time, drift detection rate, actionable improvement threshold); create `.writ/specs/2026-02-27-phase1-foundation/validation-checklist.md`.
- [x] 7.2 Run Scenario 1: `/prototype` — make a small improvement to an existing Writ command (e.g., clarify a prompt, fix a typo); time the full flow from invocation to completion; document result in validation checklist; verify completion under 5 minutes.
- [x] 7.3 Run Scenario 2: `/implement-story` with drift — implement 5 stories (or a subset that will produce drift) where implementation may reasonably diverge from spec (e.g., naming, approach variation); run full pipeline with spec-healing; record which runs produced drift, severity of each, and whether any false positives occurred; verify ≥3 of 5 detect real drift with zero false positives.
- [x] 7.4 Run Scenario 3: `/refresh-command` on dogfood transcripts — select transcripts from Scenarios 1 and 2; run refresh-command for each relevant command; record whether actionable improvements were proposed and applied; verify at least one per command analyzed.
- [x] 7.5 Run Scenario 4: Verify overlay and drift-log — confirm `.cursor/commands/` (or equivalent) preserved local changes from refresh-command; confirm `drift-log.md` exists and contains correctly formatted entries for stories that produced drift; document any anomalies.
- [x] 7.6 Run Scenario 5: Bootstrap validation — run `/refresh-command refresh-command --last`; verify the command can analyze its own transcript and propose improvements; document the outcome; confirm the learning loop is self-applicable.
- [x] 7.7 Produce Phase 1 validation report — summarize all scenario outcomes, success criteria pass/fail, and any issues discovered; write to `.writ/specs/2026-02-27-phase1-foundation/validation-report.md`; declare Phase 1 complete if all criteria pass.

## Notes

**Dogfood principle:** Use Writ to validate Writ. Every Phase 1 feature should be exercised on a real task, not just tested in isolation. The Writ project itself is the validation target.

**Suggested dogfood scenarios (reference):**
1. Run `/prototype` to make a small improvement to an existing Writ command
2. Run `/implement-story` on stories that will naturally produce some spec drift (to test healing)
3. Run `/refresh-command` on the transcripts from scenarios 1 and 2
4. Verify the command overlay system preserved local changes after the above
5. Check that `drift-log.md` was populated correctly
6. Run `/refresh-command` on itself (bootstrap validation)

**Success criteria from spec (contract):**
- `/prototype` completes a small change in under 5 minutes of human wall-clock time
- Spec-healing catches real drift in ≥3 of 5 story implementations without false positives
- `/refresh-command` produces at least one actionable improvement per command analyzed

**Validation vs implementation:** These tasks are validation-oriented — running scenarios, measuring outcomes, documenting results. No new feature implementation. If a scenario fails, the failure indicates a bug or gap in the dependent story; fix there, then re-run validation.

**Risks:**
- Spec-healing may be overly sensitive (false positives) or miss drift (false negatives); validation will surface this
- Transcript selection for refresh-command may be ambiguous if multiple sessions exist; use `--last` or explicit selection
- Wall-clock time for prototype depends on human response speed; measure from "user invokes" to "summary displayed"

**Integration points:**
- All Phase 1 commands: `/prototype`, `/implement-story`, `/refresh-command`
- `drift-log.md`, `refresh-log.md`, `.cursor/commands/`
- `agent-transcripts/` — transcript source for refresh-command

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Validation checklist documented
- [x] All 6 dogfood scenarios executed and documented
- [x] Phase 1 validation report produced
- [x] Success criteria from spec verified: prototype <5 min, spec-healing ≥3/5, refresh-command ≥1 improvement
- [x] Phase 1 declared complete (or issues documented for remediation)
