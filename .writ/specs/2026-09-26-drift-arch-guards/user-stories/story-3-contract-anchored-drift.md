# Story 3: Contract-Anchored Drift and Architecture-Class Severity

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer worried about architectural drift
**I want to** Gate 3 agents to judge drift against the locked `spec.md` contract and to pause on architecture-class deviations
**So that** a new dependency, a changed integration interface, or a changed approach stops for my decision instead of passing with a warning

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `commands/implement-story.md` Gate 3 context routing, when either Gate 3 agent is spawned, then it receives `contract_content` (the `## Specification Contract` section of `spec.md` verbatim, empty string when absent) alongside `spec_lite_content` `[AC-3.1]`
- [ ] Given `agents/evaluator-agent.md`, `agents/review-agent.md`, `claude-code/agents/writ-evaluator.md`, `claude-code/agents/writ-reviewer.md`, and the regenerated `codex/agents/{evaluator,review}-agent.toml`, when they are read, then each names `contract_content` as the drift reference that outranks `spec-lite.md` when they disagree `[AC-3.2]`
- [ ] Given the drift rubrics in both agents and their peers, when a deviation adds a runtime dependency not named in the contract or spec-lite, changes an interface or data shape at an integration point another story or the contract names, or changes the architectural approach, then it is classified Large (PAUSE), and those cases no longer appear under Medium `[AC-3.3]`
- [ ] Given `.writ/docs/drift-report-format.md` and `skills/drift-triage/SKILL.md`, when they are read, then the severity definitions carry the same three architecture-class Large cases, and the format doc's Medium example is not a new-dependency case; and `bash scripts/check-agent-parity.sh` reports no new warnings `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write a failing wiring test (pytest) asserting `contract_content` in the Gate 3 context routing row and in both agents' input tables, and that the three architecture-class cases sit under Large, not Medium, in both agents, both Claude peers, the format doc, and the skill `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.2 Add `contract_content` to `commands/implement-story.md` Gate 3 context routing (evaluator and review rows) `[AC-3.1]`
- [ ] 3.3 Edit `agents/evaluator-agent.md` and `agents/review-agent.md`: input row, prompt section "Locked Contract (drift reference)", and the severity rubric per technical-spec §3 `[AC-3.2, AC-3.3]`
- [ ] 3.4 Mirror the change in `claude-code/agents/writ-evaluator.md` and `claude-code/agents/writ-reviewer.md`; regenerate the Codex TOMLs with `python3 scripts/gen-codex-agent-tomls.py` `[AC-3.2, AC-3.3]`
- [ ] 3.5 Update `.writ/docs/drift-report-format.md` severity table and Medium example, and `skills/drift-triage/SKILL.md` Medium/Large definitions `[AC-3.4]`
- [ ] 3.6 Verify: new wiring test, `uv run pytest`, bash suite, `bash scripts/check-agent-parity.sh`, `bash scripts/eval.sh` Findings 0 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

`drift-format.py` already enforces Large ⇒ PAUSE, so reclassifying the cases is enough to make them stop; no new field in `drift-log.md`. Keep "When severity is ambiguous → default to Medium" — the three cases are now named, not ambiguous. Story 3 edits the Gate 3 context-routing table in `implement-story.md`, which Story 2 does not touch; the governor re-pin from Story 2 must be recomputed if Story 3 lands after it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (6 Contract is the reference, 7 Architecture-class is Large)
- **Technical:** sub-specs/technical-spec.md → ## 3
