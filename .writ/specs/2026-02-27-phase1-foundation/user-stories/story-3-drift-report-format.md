# Story 3: Drift Report Format & drift-log.md

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2 (spec-healing review agent extension)

## User Story

**As a** solo developer using Writ
**I want to** have spec amendments accumulated in a structured drift-log file that is never overwritten
**So that** I can track how specs evolve during implementation without modifying the original spec, and review the amendment history across story runs

## Acceptance Criteria

- [ ] **AC1:** Given a spec folder exists and no drift-log.md has been created yet, when the first story run produces drift (any severity), then `drift-log.md` is created at `.writ/specs/[spec-folder]/drift-log.md` with the correct report format.
- [ ] **AC2:** Given drift-log.md already exists from a previous story run, when a subsequent story run produces drift, then the new drift report section is appended to the file; existing entries are never modified or overwritten.
- [ ] **AC3:** Given the review agent outputs drift analysis, when the implement-story orchestrator writes to drift-log.md, then each deviation follows the canonical format: severity, spec said, implementation did, reason, resolution, and spec amendment (when applicable); Small deviations include auto-amendment; Medium deviations include ⚠️ flag; Large deviations record the pause event and human decision.
- [ ] **AC4:** Given the implement-story pipeline completes Gate 3 (Review Agent) with drift output, when Small or Medium deviations are present, then the orchestrator parses the review output, formats the drift report section, and writes/appends it to drift-log.md before continuing; for Large deviations, the orchestrator records the pause event to drift-log.md after surfacing the conflict to the user.
- [ ] **AC5:** Given drift-log.md is written, when I read the file, then the original spec (spec.md, spec-lite.md) is unchanged; drift-log.md is the sole amendment record and serves as a living document of spec evolution.

## Implementation Tasks

- [ ] 3.1 Write tests for drift-log creation and appending — mock review agent output with structured drift report; verify file creation on first drift, append on subsequent drift; verify format compliance for each severity tier; verify original spec files are never modified.
- [ ] 3.2 Define the canonical drift report format in `.writ/docs/drift-report-format.md` — document the markdown structure (Story N header, Run date, Overall Drift, Deviations with DEV-001 style IDs); document severity-specific fields (Resolution, Spec amendment); document date format (e.g., ISO 8601 or YYYY-MM-DD).
- [ ] 3.3 Implement drift report parser — extract structured drift data from review agent output; handle the review agent's drift report section format; map severity to resolution (Auto-amended / Flagged for review / Pipeline paused); extract spec amendment text for Small deviations.
- [ ] 3.4 Implement drift-log writer in implement-story orchestration — after Gate 3 completes, parse drift analysis from review output; format the drift report section per canonical format; create drift-log.md if missing, else append; ensure atomic write (no partial writes on failure).
- [ ] 3.5 Add Large-deviation handling — when Large deviations are detected, pause pipeline, surface conflict to user; after user decision (amend spec / revert code / accept deviation), append the drift report entry to drift-log.md with the recorded resolution.
- [ ] 3.6 Update `commands/implement-story.md` and `.cursor/commands/implement-story.md` — document the drift-log write step in the pipeline flow; document the expected review agent drift output format for parsing; add reference to drift-report-format.md.
- [ ] 3.7 Verify end-to-end: run implement-story on a story with Small deviation → confirm drift-log.md created/appended with correct format; run with Medium deviation → confirm ⚠️ in entry; run with Large deviation → confirm pause, user decision, then entry written; run with no drift → confirm no drift-log write (or "None" entry if desired).

## Notes

**Technical considerations:**
- **File creation vs append:** Use append mode when file exists; create with header (optional: spec name, created date) on first write. Consider a minimal header for the first drift-log creation.
- **Date formatting:** Use consistent format (e.g., `YYYY-MM-DD` or ISO 8601) for Run date; align with existing Writ conventions in spec headers.
- **Parsing review agent output:** The review agent (Story 2) outputs a structured drift report section. Parser must be resilient to minor formatting variations; consider a regex or section-based extraction. Document the expected output format in the review agent prompt so parsing is reliable.
- **Atomic writes:** Append operations should be safe; for create, write to temp file then rename to avoid partial writes if interrupted.
- **DEV-001 style IDs:** Increment per deviation within a story run; reset or continue across story runs per design choice (recommend: global increment within spec folder for traceability).

**Risks:**
- Review agent output format may vary; tight coupling between review agent prompt and parser. Mitigate with explicit format documentation and validation in tests.
- Concurrent story runs (if ever supported) could cause append conflicts; Phase 1 assumes sequential execution.

**Integration points:**
- `commands/implement-story.md` — orchestration, post–Gate 3 drift handling
- `agents/review-agent.md` — drift output format (Story 2 defines; Story 3 consumes)
- `.writ/specs/[spec-folder]/drift-log.md` — output file
- `.writ/docs/drift-report-format.md` — format specification (new)

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Drift report format documented
- [ ] implement-story correctly creates/appends drift-log.md
- [ ] Original spec files never modified by drift handling
