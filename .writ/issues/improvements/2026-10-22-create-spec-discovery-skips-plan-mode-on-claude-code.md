# `/create-spec` Discovery Skips Plan Mode on Claude Code

> **Type:** Improvement
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-10-22
> **spec_ref:** .writ/specs/2026-10-22-generated-platform-trees/spec.md

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

## Resolution

2026-10-22, branch `writ/phase/14/2026-10-22-generated-platform-trees` (spec `2026-10-22-generated-platform-trees`, Story 1). Decision: the agent enters Plan Mode. On Claude Code it calls `EnterPlanMode`, presents the contract proposal as the plan, and after `ExitPlanMode` approval locks the contract with AskQuestion. On Cursor it asks the user to switch to Plan Mode and continues when they have. On Codex and OpenClaw there is no agent-side mode: it runs discovery as a read-only conversation and says so (Codex's `/plan` is user-side). On a platform with no toggle, it says so and proceeds read-only.

Each adapter's tool table ends with a `Plan Mode` row that carries that platform's mapping and the degradation sentence:

- `adapters/cursor.md`: used by create-spec, plan-product, new-command; "Ask the user to switch to Plan Mode; continue when they have."
- `adapters/claude-code.md`: "`EnterPlanMode`; present the contract proposal as the plan; after `ExitPlanMode` approval, lock with AskQuestion."
- `adapters/codex.md`: "No agent-side mode: run discovery as a read-only conversation and say so; Codex's `/plan` is user-side."
- `adapters/openclaw.md`: "No agent-side mode: run discovery as a read-only conversation and say so."

One sentence changed in each command that follows the ADR-001 pattern:

- `commands/create-spec.md` Step 1.3: "After the context scan, run discovery in Plan Mode, entered through the adapter's `Plan Mode` row; the user controls when to switch back."
- `commands/plan-product.md` Step 1.2: discovery runs in Plan Mode "through the adapter's `Plan Mode` row".
- `commands/new-command.md` Step 1.2: the switch to Plan Mode is "through the adapter's `Plan Mode` row".

`scripts/tests/test_gen_platform_trees.py` pins the four rows (`test_plan_mode_row`), the three sentences (`test_command_sentence`), and this section (`test_issue_resolution`).

Not done here: hygiene Scenario 29 was not re-run with a request that needs open-ended shaping. That is UAT for this spec.
