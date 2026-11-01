# UAT Plan Setup Helpers Can Commit Into the Writ Repo

> **Type:** Improvement
> **Priority:** High
> **Effort:** Small
> **Created:** 2026-10-21
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`/create-uat-plan` writes setup blocks with shell helpers such as `gc() { git -C "$SRC" … add -A && … commit; }`. If the path variable is empty, `git -C ""` acts on the current directory. When that directory is the project's own repo, the helper commits there. That happened on 2026-10-21: a UAT run put commit `a8aa8d8 "old release"` on the real `main`. It was caught and reset before any push.

## Current State

- Cause on 2026-10-21: five UAT agents ran in parallel and shared one scratchpad. One agent's `env.sh` overwrote another's. The second agent's setup then ran with `OLD` unset, from the repo as its working directory, and `git -C "$OLD" mv …` plus `gc "" "old release"` committed into the repo.
- The five Phase 13 plans were patched by hand the same day:
  - each setup block now runs `cd "$W"` right after creating the temp folder
  - each `gc` refuses a path outside `$W`
  - hygiene Scenario 29's seeding commit is guarded
- `commands/create-uat-plan.md` still generates unguarded helpers, so the next plan will have the same hazard.

## Expected Outcome

- `/create-uat-plan` generates setup blocks that:
  - `cd` into the temp folder they create
  - refuse any write (commit, `mv`, install, update) whose target is empty or outside that folder
  - never depend on files outside it, such as a shared scratchpad
- Optionally, a check over generated `uat-plan.md` files that flags a `git -C "$VAR" … commit` with no guard.

## Relevant Files

- `commands/create-uat-plan.md`: the setup-block guidance
- `.writ/specs/2026-10-20-*/uat-plan.md`: the patched examples
- `.writ/knowledge/lessons/`: the companion lesson on parallel agents and shared scratch space
