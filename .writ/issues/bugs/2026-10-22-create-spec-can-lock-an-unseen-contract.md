# `/create-spec` Can Ask to Lock a Contract It Never Showed

> **Type:** Bug
> **Priority:** High
> **Effort:** Small
> **Created:** 2026-10-22
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

In the 2026-10-22 UAT run of `2026-10-20-shipped-command-hygiene` Scenario 29 (Claude Code 2.1.308), `/create-spec` drafted the contract only in its thinking. It then showed the Contract Decision prompt ("How would you like to proceed with this contract?"). The user locked a contract they never saw. That breaks contract-first, the command's core rule.

## Current State

- The transcript has four assistant text blocks, none before the lock: "Contract locked…", "Story generators running…", "Jev skipped…", and the final review. The seven contract sections appear only in the written `spec.md`.
- Discovery ran as three `AskUserQuestion` calls. The run never entered Plan Mode.
- `commands/create-spec.md` still says "present the contract (still in Plan Mode)" (Step 1.3) and gives the Step 1.4 template. However, nothing requires the contract to be visible output before Step 1.4b, and nothing covers a run that skips Plan Mode.
- The Phase 13 cut (54,264 → 38,562 bytes; pre-cut text at `37e097e`) removed the Step 1.2 "Switch to Plan Mode for Discovery" section and the worked `--- PLAN MODE ---` example dialogue. One run does not prove the cut caused this, but it made the step less prominent.
- Separate platform limit: Step 1.4b lists five options. Claude Code's `AskUserQuestion` takes at most 4, plus an automatic "Other". The run dropped "I have more questions before deciding".

## Expected Outcome

- Step 1.4b states a precondition: the full contract (Step 1.4 template) is printed as a visible message to the user before the Contract Decision prompt, in Plan Mode or not. A prompt that refers to "this contract" when no contract was shown is a contract violation.
- Step 1.4b's options fit a 4-option cap. Either fold "more questions" into the free-text answer, or note in `adapters/claude-code.md` that "Other" covers it.
- Re-run hygiene Scenario 29 and confirm the contract appears before the prompt.

## Relevant Files

- `commands/create-spec.md`: Steps 1.3, 1.4, and 1.4b
- `adapters/claude-code.md`: the `AskQuestion` mapping
- `.writ/specs/2026-10-20-shipped-command-hygiene/uat-plan.md`: Scenario 29 notes
