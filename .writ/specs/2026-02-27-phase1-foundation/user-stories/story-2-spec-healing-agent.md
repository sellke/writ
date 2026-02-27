# Story 2: Spec-Healing Review Agent Extension

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** solo developer using Writ
**I want to** have the review agent automatically detect and classify spec drift during code review
**So that** deviations between spec and implementation are handled proportionally instead of the pipeline hard-failing or drift going unnoticed

## Acceptance Criteria

- [ ] **AC1:** Given the implementation has a Small deviation (e.g., different function name, minor API shape change, cosmetic implementation detail), when the review agent runs, then the deviation is classified as Small, a spec amendment is proposed in the review output, and the pipeline continues with PASS; the orchestrator logs the amendment to `drift-log.md`.
- [ ] **AC2:** Given the implementation has a Medium deviation (e.g., scope expansion, new dependency, approach variation affecting integration), when the review agent runs, then the deviation is classified as Medium, flagged with ⚠️ in the drift report, and the pipeline continues with PASS and a warning surfaced to the user.
- [ ] **AC3:** Given the implementation has a Large deviation (e.g., wrong approach, constraint violation, security model change, incompatible data model), when the review agent runs, then the deviation is classified as Large, the pipeline pauses, and the conflict is surfaced to the human with: what the spec said, what the implementation did, and why it matters.
- [ ] **AC4:** Given the severity of a deviation is ambiguous, when the review agent classifies it, then it defaults to Medium (flag) rather than Small or Large.
- [ ] **AC5:** Given the review agent runs with drift analysis enabled, when the review completes, then all existing duties (acceptance criteria verification, code quality, security, test coverage, integration) are still performed; drift analysis is additive and does not replace or skip any existing checklist items.

## Implementation Tasks

- [ ] 2.1 Write tests for drift classification — mock review agent inputs with Small/Medium/Large deviations, verify correct severity assignment, verify ambiguous cases default to Medium; verify pipeline behavior (continue vs pause) for each tier.
- [ ] 2.2 Add `spec_lite_content` to the review agent input parameters — document in `agents/review-agent.md` Input Requirements table; ensure the prompt template receives `{spec_lite_content}` for drift comparison.
- [ ] 2.3 Define explicit severity classification criteria in `agents/review-agent.md` — enumerate Small (cosmetic/naming, implementation details, behavior matches intent), Medium (scope additions, new dependencies, approach variations affecting integration), Large (architectural deviation, constraint breach, security model change, incompatible data model); include "when ambiguous → Medium" rule.
- [ ] 2.4 Add Drift Analysis section to the review agent prompt template — new checklist section after Integration Review: compare implementation vs spec, classify deviations per severity tiers, output structured drift report; for Small: propose spec amendment; for Medium: flag with warning; for Large: PAUSE and report (do not continue review).
- [ ] 2.5 Update `commands/implement-story.md` and `.cursor/commands/implement-story.md` — in Gate 3 (Review Agent), load `spec-lite.md` from the spec folder and pass its content to the review agent; document the new input parameter.
- [ ] 2.6 Add drift response handling to implement-story orchestration — when review output includes Small deviations with proposed amendments, append to `.writ/specs/[spec-folder]/drift-log.md`; when Large deviations are present, pause pipeline and surface conflict to user; when Medium deviations are present, include warning in summary.
- [ ] 2.7 Verify end-to-end: run implement-story on a story with intentional Small deviation (e.g., renamed function) → confirm auto-amend logged; run with Medium deviation → confirm flag + continue; run with Large deviation → confirm pause; run with ambiguous deviation → confirm default to Medium.

## Notes

**Technical considerations:**
- The review agent is read-only — it can detect and report drift but cannot modify files
- The spec amendment (for Small deviations) is a RECOMMENDATION in the review output — the implement-story orchestrator applies it by appending to `drift-log.md`
- The original spec is NEVER modified — drift-log serves as a living amendment record
- The implement-story command needs to be updated to pass `spec-lite.md` content to the review agent
- Severity classification criteria should be explicit and enumerated, not vague

**Risks:**
- Severity classification is inherently judgmental — ambiguous cases may be misclassified; defaulting to Medium mitigates under-classification

**Integration points:**
- `agents/review-agent.md` — prompt extension, input parameters
- `commands/implement-story.md` — Gate 3 context loading, drift response handling
- `.writ/specs/[spec-folder]/drift-log.md` — amendment record format

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated
