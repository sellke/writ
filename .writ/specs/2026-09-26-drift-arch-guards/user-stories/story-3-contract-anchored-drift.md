# Story 3: Contract-Anchored Drift and Architecture-Class Severity

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer worried about architectural drift
**I want to** Gate 3 agents to judge drift against the locked `spec.md` contract and to pause on architecture-class deviations
**So that** a new dependency, a changed integration interface, or a changed approach stops for my decision instead of passing with a warning

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [x] Given `commands/implement-story.md` Gate 3 context routing, when either Gate 3 agent is spawned, then it receives `contract_content` (the `## Specification Contract` section of `spec.md` verbatim, empty string when absent) alongside `spec_lite_content` `[AC-3.1]`
- [x] Given `agents/evaluator-agent.md`, `agents/review-agent.md`, `claude-code/agents/writ-evaluator.md`, `claude-code/agents/writ-reviewer.md`, and the regenerated `codex/agents/{evaluator,review}-agent.toml`, when they are read, then each names `contract_content` as the drift reference that outranks `spec-lite.md` when they disagree `[AC-3.2]`
- [x] Given the drift rubrics in both agents and their peers, when a deviation adds a runtime dependency not named in the contract or spec-lite, changes an interface or data shape at an integration point another story or the contract names, or changes the architectural approach, then it is classified Large (PAUSE), and those cases no longer appear under Medium `[AC-3.3]`
- [x] Given `.writ/docs/drift-report-format.md` and `skills/drift-triage/SKILL.md`, when they are read, then the severity definitions carry the same three architecture-class Large cases, and the format doc's Medium example is not a new-dependency case; and `bash scripts/check-agent-parity.sh` reports no new warnings `[AC-3.4]`

## Implementation Tasks

- [x] 3.1 Write a failing wiring test (pytest) asserting `contract_content` in the Gate 3 context routing row and in both agents' input tables, and that the three architecture-class cases sit under Large, not Medium, in both agents, both Claude peers, the format doc, and the skill `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.2 Add `contract_content` to `commands/implement-story.md` Gate 3 context routing (evaluator and review rows) `[AC-3.1]`
- [x] 3.3 Edit `agents/evaluator-agent.md` and `agents/review-agent.md`: input row, prompt section "Locked Contract (drift reference)", and the severity rubric per technical-spec §3 `[AC-3.2, AC-3.3]`
- [x] 3.4 Mirror the change in `claude-code/agents/writ-evaluator.md` and `claude-code/agents/writ-reviewer.md`; regenerate the Codex TOMLs with `python3 scripts/gen-codex-agent-tomls.py` `[AC-3.2, AC-3.3]`
- [x] 3.5 Update `.writ/docs/drift-report-format.md` severity table and Medium example, and `skills/drift-triage/SKILL.md` Medium/Large definitions `[AC-3.4]`
- [x] 3.6 Verify: new wiring test, `uv run pytest`, bash suite, `bash scripts/check-agent-parity.sh`, `bash scripts/eval.sh` Findings 0 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

`drift-format.py` already enforces Large ⇒ PAUSE, so reclassifying the cases is enough to make them stop; no new field in `drift-log.md`. Keep "When severity is ambiguous → default to Medium" — the three cases are now named, not ambiguous. Story 3 edits the Gate 3 context-routing table in `implement-story.md`, which Story 2 does not touch; the governor re-pin from Story 2 must be recomputed if Story 3 lands after it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (6 Contract is the reference, 7 Architecture-class is Large)
- **Technical:** sub-specs/technical-spec.md → ## 3

---

## What Was Built

**Implementation Date:** 2026-09-26

### Files Modified

1. **`commands/implement-story.md`** — Gate 3 context-routing rows for the evaluator and review agents pass `contract_content` (the `## Specification Contract` section of `spec.md`, verbatim, `""` when absent). [AC-3.1]
2. **`agents/evaluator-agent.md`, `agents/review-agent.md`** — `contract_content` input row with the extraction rule; "Locked Contract (drift reference)" prompt section that outranks spec-lite; the three architecture-class cases (new runtime dependency, changed integration interface or data shape, changed architectural approach) moved from Medium to Large; "default to Medium" on ambiguity kept. [AC-3.2, AC-3.3]
3. **`claude-code/agents/writ-evaluator.md`, `claude-code/agents/writ-reviewer.md`** — Drift section and output block; writ-reviewer returns PASS/FAIL/PAUSE. [AC-3.2, AC-3.3]
4. **`codex/agents/evaluator-agent.toml`, `codex/agents/review-agent.toml`** — regenerated from the agent sources. [AC-3.2]
5. **`.writ/docs/drift-report-format.md`, `skills/drift-triage/SKILL.md`** — same three Large cases; the Medium example is now a scope expansion. [AC-3.4]
6. **`scripts/tests/test_drift_severity_wiring.py`** — 10 wiring tests. **Ratchets:** governor over-budget 9656 → 9763, lean SHA re-pinned, both with dated comments; `implement-story.lean.md` untouched. [AC-3.1, AC-3.2, AC-3.3, AC-3.4]

### Implementation Decisions

1. Spec-lite prompt section renamed to "Spec-Lite (for Drift Analysis)" (DEV-007).
2. writ-reviewer gains PAUSE so Large drift can stop on Claude Code (DEV-008).
3. Small tier limited to internal API shape changes (DEV-009).
4. Codex TOMLs generated via the generator functions; its CLI lacks an `evaluator-agent` entry (DEV-010).

### Test Results

- `uv run --python 3.9 pytest` (wiring, governor, lean, quality-gate wiring, evaluator contract): 135 passed, 1 failed pre-commit (`test_review_agent_not_in_story_edit_set` reads the uncommitted working tree). `check-agent-parity.sh`: OK. Skill lint: clean. Full suite and `eval.sh` run at spec end.
- boundary-map crossings: 5 `outside_boundary` (brace path and implicit test paths the map missed) → routed to review-agent. Review: PASS, Overall Drift Small; every crossing traced to a task or technical-spec §5.
- Minor follow-ups carried into Story 2: `implement-story.md` Gate 3 spawn sentences omit `contract_content`; Gate 3.5 still labels Medium "scope/integration impact".
