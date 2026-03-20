# Story 2 — Agent Iteration Caps

> Status: Completed ✅
> Priority: High
> Dependencies: None

## User Story

As a Writ user running the implement-story pipeline, I want coding and testing agents to have explicit self-fix iteration limits and a structured BLOCKED handoff, so that degenerate failure modes cannot spin forever and I get a clear repair decision when automation stalls.

## Acceptance Criteria

**Given** `agents/coding-agent.md` is the active coding agent instruction set, **when** an implementer reads the self-fix rules, **then** `MAX_SELF_FIX_ITERATIONS = 3` is stated explicitly and the agent is instructed to stop further self-fix attempts after reaching that cap.

**Given** `agents/testing-agent.md` is the active testing agent instruction set, **when** an implementer reads the self-fix rules, **then** `MAX_SELF_FIX_ITERATIONS = 3` is stated explicitly and the agent is instructed to stop further self-fix attempts after reaching that cap.

**Given** either agent has exhausted self-fix iterations without resolving the failure, **when** it terminates with a structured result, **then** it emits `STATUS: BLOCKED` and the output includes the agent name, number of attempts made, a specific failure description, and partial state (what was completed before the block).

**Given** `commands/implement-story.md` orchestrates coding and testing agents, **when** it receives a `STATUS: BLOCKED` result from either agent, **then** it escalates to the user with **AskQuestion** offering at least: retry, skip (with an explicit warning gate / marked warning path), and abort pipeline.

**Given** the BLOCKED contract is documented in the agent files, **when** comparing coding vs testing instructions, **then** both agents use the same `STATUS: BLOCKED` structured output shape so the orchestrator can parse and branch consistently.

## Implementation Tasks

- [x] 2.1 Write tests first: add or extend lightweight contract checks (e.g. scripted `rg`/assertions or existing spec-verification hooks) that fail until `MAX_SELF_FIX_ITERATIONS = 3`, the `STATUS: BLOCKED` schema, and orchestrator AskQuestion handling exist in the three target files; run and capture baseline failures before edits.

- [x] 2.2 Update `agents/coding-agent.md` — document `MAX_SELF_FIX_ITERATIONS = 3`, tie self-fix loops to the cap, and define the `STATUS: BLOCKED` output format with required fields (agent, attempts, failure context, partial state).

- [x] 2.3 Update `agents/testing-agent.md` — mirror the coding agent: same constant, same cap behavior, and the same `STATUS: BLOCKED` structured output contract.

- [x] 2.4 Update `commands/implement-story.md` — on `STATUS: BLOCKED`, present a user-facing repair decision via **AskQuestion**: retry, skip (warning gate / mark warning), and abort pipeline; ensure instructions reference parsing the BLOCKED payload fields.

- [x] 2.5 Cross-review the three markdown files for naming consistency, no contradictory iteration behavior, and that BLOCKED is only emitted after the cap (not for unrelated early exits).

- [x] 2.6 Verify all AC pass: run the contract checks from 2.1, manually walk through implement-story flow text for each AskQuestion branch, and confirm BLOCKED field list matches orchestrator expectations.

## Technical Notes

- Scope is **markdown instruction files only** — no runtime code; changes ship as product documentation consumed by Cursor/agents.
- **Partial state** should be concrete (e.g. files touched, tests run, last failing command or assertion) so the user can decide retry vs skip vs abort without re-deriving context.
- **Skip** must be framed as a gated choice with a visible warning (e.g. continuing leaves the story in a known-degraded state) so users do not accidentally bypass a hard block.
- Align with Writ interaction guidance: bounded repair decisions use **AskQuestion**; keep option labels unambiguous (`Retry`, `Skip with warning`, `Abort pipeline` or equivalent).
- This story closes the systemic gap where self-fix loops had no stated maximum, which risks unbounded agent churn in pathological cases.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed
