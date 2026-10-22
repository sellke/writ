# `/update-writ` Says a Kept File Is Asked About Only When Upstream Changes It

> **Type:** Improvement
> **Priority:** Low
> **Effort:** XS
> **Created:** 2026-10-21
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`commands/update-writ.md` Step 7 and Completion say a kept customized file "asks again when upstream changes" it. The UAT run of `2026-10-20-ci-and-update-integrity` (Scenario 28) recorded that a kept file is reported on every run. Make the text match what `update.sh` does.

## Current State

- Step 7: "A customized file the user kept keeps its previous baseline … The next update compares against that baseline, so it asks again when upstream changes the file."
- Completion repeats the sentence.
- The maintainer accepted Scenario 28 as Pass on 2026-10-21 and asked for this gap to be filed.

## Expected Outcome

- Run `update.sh` twice on a project with a kept customized file, once with no upstream change and once with one. Record what each run prints.
- Reword Step 7 and Completion to say exactly that.

## Relevant Files

- `commands/update-writ.md`: Step 7, Completion
- `scripts/update.sh`: the preserve path
- `.writ/specs/2026-10-20-ci-and-update-integrity/uat-plan.md`: Scenario 28 notes
