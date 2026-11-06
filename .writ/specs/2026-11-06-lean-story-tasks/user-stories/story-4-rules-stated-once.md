# Story 4: State each business rule once

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** spec author
**I want to** cite spec Business Rule 4 by number from every spec and story document instead of copying it
**So that** the coding agent never has to choose between two versions of one rule (see `spec.md` → `## Evidence`, DEV-001)

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given the business-rules bullet in `commands/create-spec.md` Step 2.4, when Step 2.4 is read, then it adds detail per Business Rule number and does not restate contract rule text `[AC-4.1]`
- [ ] Given `commands/create-spec.md` Step 2.8, the business-rule hint in `agents/user-story-generator.md`, and `.writ/docs/context-hint-format.md`, when each is read, then each cites rules as `Business Rule N` and none restates rule text `[AC-4.2]`
- [ ] Given the generator's task rules, when a task cites a Business Rule, then the rules allow the task to cite the number and forbid paraphrasing the rule `[AC-4.3]`
- [ ] Given the edited `commands/create-spec.md`, when `scripts/tests/test_governor_enforcement.py` runs, then the file is net-zero bytes or a dated `KNOWN_OVER_BUDGET` entry covers its growth `[AC-4.4]`
- [ ] Given the finished change, when verification runs, then pytest passes on Python 3.9 and 3.14, `bash scripts/eval.sh` passes, and `python3 scripts/gen-platform-trees.py --check` reports no drift `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write tests in `scripts/tests/test_rule_citations.py` pinning rule-number citations in `commands/create-spec.md` Steps 2.4 and 2.8, `agents/user-story-generator.md`, and `.writ/docs/context-hint-format.md` `[AC-4.1, AC-4.2, AC-4.3]`
- [ ] 4.2 Update `commands/create-spec.md` Step 2.4 business-rules bullet and Step 2.8 to cite Business Rule numbers instead of restating rule text `[AC-4.1, AC-4.2]`
- [ ] 4.3 Update `agents/user-story-generator.md` task rules to forbid paraphrasing a Business Rule, and its Context for Agents business-rule hint to cite numbers `[AC-4.2, AC-4.3]`
- [ ] 4.4 Update `.writ/docs/context-hint-format.md` business-rule format and example to use `Business Rule N` citations `[AC-4.2]`
- [ ] 4.5 Add a dated `KNOWN_OVER_BUDGET` entry in `scripts/tests/test_governor_enforcement.py` if `commands/create-spec.md` grows; otherwise confirm net-zero bytes `[AC-4.4]`
- [ ] 4.6 Regenerate platform trees with `python3 scripts/gen-platform-trees.py` so `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**` match the edited sources `[AC-4.2, AC-4.3]`
- [ ] 4.7 Run pytest alone on Python 3.9 and 3.14, then `bash scripts/eval.sh` and `python3 scripts/gen-platform-trees.py --check`; confirm every criterion holds `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- Story 3 edits `commands/create-spec.md` and `agents/user-story-generator.md` too. Start from its result and expect conflicts in the same files.
- `commands/create-spec.md` is over its command byte budget. Any net growth needs a dated, disclosed `KNOWN_OVER_BUDGET` entry. Target net-zero.
- `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**` are generated. Edit the sources and regenerate. Do not hand-edit the trees.
- Run pytest alone in the checkout. `eval.sh`, bash tests, writes under `.writ/state/`, or `git worktree` changes during a pytest run break `test_smoke_leaves_repo_unchanged`.
- `scripts/tests/test_rule_citations.py` is new. `technical-spec.md` → `## Components` lists no test file for wording. Add a row there if the file stays.
- Component rows for this story: `technical-spec.md` → `## Components`, rows marked Story 4.
- The Story 5 trial is out of scope here.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** [Business Rule 4 (rules live once; cite by number), Business Rule 1 (tasks name files, no internal structure)] — from spec.md → `## 📋 Business Rules (Expanded)`
- **Experience:** []
