# Story 3: The Front Door Routes Why Questions to `/why`

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** user who types `/writ "why is X like this?"`
**I want to** be routed to `/why`, and to `/research` only when the question is about something outside the project
**So that** project questions are answered from the project's own ledger, and the interim "when it ships" notes are gone

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `commands/writ.md` § Routing Rules, when its table is read, then it still has six data rows, and the fifth row's Signal cell reads "Asks why something in this project is the way it is, or how it works" and its Route cell contains `/why` and names `/research` for a question about something outside the project `[AC-3.1]`
- [ ] Given `commands/writ.md` § Step 2, when its "Why or how" bullet is read, then it routes `/why` and names `/research` for a question about a library, a standard, or a vendor, and the file no longer contains the text `when it ships` `[AC-3.2]`
- [ ] Given `.writ/docs/prompting-guide.md` § A why or how question, when its `Route:` line is read, then it names `/why` first and `/research` for questions outside the project, and the guide no longer contains `when it ships` `[AC-3.3]`
- [ ] Given the updated tests and regenerated trees, when `uv run --python 3.9 pytest`, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh` run, then `scripts/tests/test_front_door.py` and `scripts/tests/test_prompting_guide.py` pass with `/why` as the fifth route, `--check` prints `pass`, and eval reports 0 findings `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write the failing tests first. In `scripts/tests/test_front_door.py` set `ROUTES[4]` to `("/why", None)`, change the row-5 assertion to check `/research`, and add `test_why_route` per technical-spec.md → Tests. In `scripts/tests/test_prompting_guide.py` set the why-or-how recipe to `/why`, change its special-case assertion to `/research`, and assert the guide no longer contains `when it ships`. Run them and confirm they fail on the old route `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.2 Grep `scripts/` for a fragment of each sentence you will change in `commands/writ.md` and the guide. Update any other pin in the same change `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.3 Replace the fifth row of `commands/writ.md` § Routing Rules and its § Step 2 "Why or how" bullet with the text in technical-spec.md → `/writ` Route. Change no other row or step `[AC-3.1, AC-3.2]`
- [ ] 3.4 Replace the `Route:` line under `.writ/docs/prompting-guide.md` § A why or how question with the text in technical-spec.md → `/writ` Route. Leave the Weak and Strong lines unchanged `[AC-3.3]`
- [ ] 3.5 Regenerate the plugin trees with `python3 scripts/gen-platform-trees.py` and confirm `--check` prints `pass` `[AC-3.4]`
- [ ] 3.6 Verify. Run `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Confirm 0 failures and 0 findings, and that `git diff --stat` shows edits only to the files this story names plus the regenerated trees `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

- **Six rows.** `scripts/tests/test_front_door.py` pins the row count and the row order. The `/research` route moves into the fifth row's cell; no row is added.
- **Mirroring needs no change.** `/writ` Step 4 already collects `### Step N` headings, and `commands/why.md` has six.
- **The completed front-door spec stays as written.** Its routing fixture expected `/research` for question 5, which was correct when it ran. Do not edit `.writ/specs/2026-10-22-front-door/`.
- **Stale count in `commands/writ.md` frontmatter.** `problem:` says "Writ ships 32 commands". It is out of this story's scope; leave it.
- **Parallel with Story 4.** Story 4 edits `commands/create-spec.md` and `scripts/tests/test_why_command.py`. This story touches neither.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Happy path]
- **Business rules:** [Front-door route, Generated files are regenerated]
- **Experience:** [Entry Point]
