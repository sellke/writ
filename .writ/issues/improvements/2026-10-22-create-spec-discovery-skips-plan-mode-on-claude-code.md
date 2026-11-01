# `/create-spec` Discovery Skips Plan Mode on Claude Code

> **Type:** Improvement
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-10-22
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

ADR-001 puts `/create-spec` discovery in Plan Mode as a conversation and keeps AskQuestion for bounded decisions. Neither of the two live hygiene Scenario 29 runs on 2026-10-22 (Claude Code 2.1.308) entered Plan Mode. Both ran discovery as `AskUserQuestion` forms. Open-ended shaping, the case ADR-001 was written for, has no conversational path in practice.

## Current State

- `commands/create-spec.md` Step 1.3 says "run discovery in Plan Mode; the user controls when to switch". The Phase 13 cut removed Step 1.2 ("Switch to Plan Mode for Discovery") and the worked `--- PLAN MODE ---` example (cut log row 17).
- Run 1 asked three single-question forms. Run 2 asked one form with three independent questions. Neither suggested Plan Mode, and neither offered free conversation beyond the forms' automatic "Other".
- On Claude Code, Plan Mode is entered by the user (shift+tab) or by the `EnterPlanMode` tool. The command does not say which, and `adapters/claude-code.md` does not map it for discovery.
- The maintainer decided on 2026-10-22 that independent bounded choices may share one prompt, so bundling is not the defect. The defect is that a form can be the whole discovery.

## Expected Outcome

- Decide how discovery reaches Plan Mode on each platform. Options: the agent calls `EnterPlanMode`, it asks the user to switch, or the adapter states that forms are the accepted substitute.
- Write that decision into `create-spec.md` Step 1.3 and the adapter's Plan Mode row. Check `plan-product.md` and `new-command.md`, which follow the same ADR-001 pattern.
- Re-run hygiene Scenario 29 with a request that needs open-ended shaping, not only bounded choices.

## Relevant Files

- `commands/create-spec.md`: Step 1.3
- `adapters/claude-code.md`: Plan Mode mapping
- `.writ/decision-records/adr-001-askquestion-vs-plan-mode.md`
- `.writ/specs/2026-10-20-shipped-command-hygiene/uat-plan.md`: Scenario 29 notes
