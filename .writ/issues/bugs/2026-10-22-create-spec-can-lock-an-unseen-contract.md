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

## Resolution

2026-10-22, PR #62 (branch `claude/sweet-pike-a83e04`, commits `3fdbbbf`, `cae0ced`, `8a59b4b`); no spec, by maintainer decision. Step 1.4b of `commands/create-spec.md` now opens with a precondition: the full contract is printed as a visible message before the Contract Decision prompt, in Plan Mode or not. The `--from-prototype` and `--from-issue` paths print theirs too. The prompt has four options; "more questions" folds into "edit", where a free-text "Other" also goes, so `adapters/claude-code.md` needed no change. Step 1.3 opens with the discovery rule the maintainer chose: ask a question alone when its answer could change the next one; independent bounded choices may share one prompt. `eval-command-structure.py` pins both with its `lead` kind. Hygiene Scenario 29 was re-run on `3fdbbbf`: all seven sections printed before a 4-option prompt, and it is marked Pass. The remaining gap, discovery never entering Plan Mode on Claude Code, is `.writ/issues/improvements/2026-10-22-create-spec-discovery-skips-plan-mode-on-claude-code.md`.
