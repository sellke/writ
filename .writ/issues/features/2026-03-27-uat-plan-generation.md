# UAT Plan Generation for Human QA

> **Type:** Feature
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-03-27
> **spec_ref:**

## TL;DR

Add a UAT plan step to the pipeline so humans have a structured checklist to manually validate features after implementation.

## Current State

- Automated testing exists via the testing-agent (coverage, regression, pass rate)
- `verify-spec` checks spec integrity and metadata — not runtime behavior
- No structured output for human QA exists in the pipeline
- After `/implement-spec` completes, there's no handoff artifact telling a human *what to click, check, or try*
- Human validation happens ad hoc (if at all) with no traceability

## Expected Outcome

- A UAT plan is generated as a markdown artifact after stories are implemented
- The plan contains human-readable test scenarios derived from acceptance criteria
- Each scenario includes: preconditions, steps, expected result, pass/fail checkbox
- Scenarios cover happy paths, edge cases, and regressions worth spot-checking
- The plan lives alongside the spec (e.g., `.writ/specs/{spec}/uat-plan.md`)
- Integration point: either as a new command (`/create-uat-plan`) or as an optional phase in `/implement-spec` or `/ship`

## Relevant Files

- `commands/verify-spec.md` - closest existing QA-adjacent command (metadata only, not runtime)
- `agents/testing-agent.md` - automated testing agent whose acceptance criteria could seed UAT scenarios
- `commands/ship.md` - release workflow where UAT sign-off could gate shipping

## Notes

- Key design decision: should this be a standalone command or an embedded phase? Standalone is more flexible; embedded ensures it's never skipped.
- The UAT plan should be *generated from* acceptance criteria in user stories, not written from scratch — Writ already captures the right inputs.
- Consider a sign-off mechanism: a human marks scenarios pass/fail, and `/ship` or `/release` can optionally check for UAT completion.
- This bridges the gap between "AI says it works" and "a human confirmed it works" — important for trust in AI-driven development.
