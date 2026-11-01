# Gate 4.5 Fail Asked the User Instead of Recoding

> **Type:** Bug
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-10-31
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

In the Phase 12 UAT (behavioral-verification Scenario 26, agent run on 2026-10-31), a headless default `/implement-story` run on a scratch project got `app-verify: 1/1 fail — greet-page (exit 1)` at Gate 4.5. It did not go back to Gate 1. It stopped, asked the user, and offered skip and `DEGRADED` options. Its stated reason was that the failure existed before the story. `commands/implement-story.md` says Gate 4.5 never asks a question and that a `fail` goes to a Gate 1 recode.

## Current State

- The scenario breaks `/greet` and then runs Story 4, whose changed files map to the `greet-page` feature.
- Gate 4.5's text: "Gate 4.5 never asks a question; a script decides" and "`fail` → Gate 1 recode on the shared review-loop cap". It has no rule for a failure the story did not cause. The orchestrator made one up.
- The same run had already needed a human override for a separate false block. `test-integrity.py` flagged the Python end-to-end test as `test_imports_no_source` at Gate 3 and Gate 4. That is fixed in `db428bc`. The earlier override may have primed the run to ask again.
- One run, headless (`claude -p`, `--permission-mode acceptEdits`). Not yet reproduced interactively or with the `test-integrity` fix in place.

## Expected Outcome

- Re-run Scenario 26 on a tree with `db428bc`. If the orchestrator still asks, decide the rule for a pre-existing failure in a touched feature:
  - recode anyway, since the story touched the feature and owns its check; or
  - add an explicit pre-existing-failure branch that relays the line and records it, with no question.
- Whichever rule is chosen, state it in Gate 4.5 in one line, so an orchestrator has no gap to fill with a question.

## Relevant Files

- `commands/implement-story.md`: Gate 4.5
- `.writ/specs/archive/2026-10-01-behavioral-verification/uat-plan.md`: Scenario 26 notes
- Run transcripts from the UAT agent (not committed): `s26a`, `s26c` under the session scratchpad
