# Story 3: Drop the generic Definition of Done

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** spec author and a developer running `/verify-spec`
**I want to** new stories to omit a generic Definition of Done, and `/verify-spec` to check only the Definition of Done a story has
**So that** generated stories carry less boilerplate, and legacy stories with a Definition of Done are still checked

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given the story template in `agents/user-story-generator.md`, when a story file is generated from it, then the file contains no `## Definition of Done` section `[AC-3.1]`
- [ ] Given the story-contents sentence in `commands/create-spec.md` Step 2.6, when it is read, then it names no definition of done `[AC-3.2]`
- [ ] Given a story with no `## Definition of Done` section, when `/verify-spec` runs Check 1d, then it reports no finding for that story `[AC-3.3]`
- [ ] Given a Completed story whose Definition of Done has unchecked items, when `/verify-spec` runs Check 3b, then it still reports the WARN; given a story with no Definition of Done, Check 3b reports nothing for it `[AC-3.4]`
- [ ] Given a change that grows `commands/create-spec.md` or `commands/verify-spec.md` in bytes, when the story is complete, then `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` has a dated entry for that file `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write tests in `scripts/tests/` that pin the new wording of `agents/user-story-generator.md`, `commands/create-spec.md` Step 2.6, and `commands/verify-spec.md` Checks 1d and 3b. Tests fail before the edits. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [ ] 3.2 Remove the `## Definition of Done` block from the Prompt Template in `agents/user-story-generator.md`. Leave the other template sections unchanged. `[AC-3.1]`
- [ ] 3.3 In `commands/create-spec.md` Step 2.6, drop the definition of done from the story-contents sentence. Leave the rest of the sentence and the criterion ID grammar paragraph unchanged. `[AC-3.2]`
- [ ] 3.4 In `commands/verify-spec.md`, remove Definition of Done from the Check 1d required sections. Change Check 3b so it runs only when the story has a Definition of Done section. `[AC-3.3, AC-3.4]`
- [ ] 3.5 Regenerate the platform copies with `python3 scripts/gen-platform-trees.py`, including `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**`. Do not hand-edit them. `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.6 Add a dated `KNOWN_OVER_BUDGET` entry in `scripts/tests/test_governor_enforcement.py` for each of `create-spec.md` and `verify-spec.md` that grows in bytes. Net-zero changes need no entry. `[AC-3.5]`
- [ ] 3.7 Run pytest alone under Python 3.9 and 3.14, then `bash scripts/eval.sh` and `python3 scripts/gen-platform-trees.py --check`. Confirm each criterion. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- This story keeps its own Definition of Done. Business Rule 5 applies to stories generated after this one ships.
- Cross-spec overlap: `2026-11-06-archived-dependencies-resolve` also edits `commands/verify-spec.md` (Check 3f) and its byte-budget ledger line. Whichever spec lands second rebases the ledger number.
- Stories 2, 3, and 4 all edit `agents/user-story-generator.md` and `commands/create-spec.md`. Apply them in order.
- Generated trees are outputs of `scripts/gen-platform-trees.py`. A hand edit is overwritten on the next run and fails `--check`.
- Legacy stories keep their Definition of Done. Do not edit them. `/revert` step 1 still unchecks Definition of Done items on those stories.
- Run pytest alone. `eval.sh`, the bash tests, and `git worktree` changes in the same checkout break `test_smoke_leaves_repo_unchanged` and the `app-verify` tests.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`/verify-spec` 1d, `/verify-spec` 3b] — from technical-spec.md → ## Error & Rescue Map
- **Business rules:** [Rule 5 (new stories have no Definition of Done; legacy stories untouched)] — from spec.md → ## 📋 Business Rules (Expanded)
- **Experience:** [State Catalog rows "Legacy story with DoD" and "New story with no DoD"] — from spec.md → ## 🎯 Experience Design → ### State Catalog
