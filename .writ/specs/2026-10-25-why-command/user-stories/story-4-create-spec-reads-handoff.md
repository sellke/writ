# Story 4: `/create-spec` Reads the `/why` Handoff

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** developer who ran `/why` before planning a change
**I want to** have `/create-spec` discovery pick up the Preserve / Change / Avoid / Risk list on its own
**So that** the contract keeps what the history says to keep, and discovery does not re-ask what `/why` already settled

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given `commands/create-spec.md` Phase 1, when its headings are read, then `#### Step 1.2: Read a `/why` Handoff` sits after Step 1.1 and before Step 1.3, and its section searches the conversation, a file the invocation names, and `.writ/research/*-why-*.md` records whose `Subject` or `Change` line shares a keyword with the feature idea, and says to skip the step when none is found `[AC-4.1]`
- [ ] Given that Step 1.2 section and `commands/why.md`, when the seam test compares them, then both contain the literal `## Preserve / Change / Avoid / Risk`, and Step 1.2 maps Preserve to Business Rules, Change to the Deliverable, Avoid to Scope Boundaries → Excluded, and Risk to Technical Concerns, keeping each item's tier and citing the record `[AC-4.2]`
- [ ] Given `scripts/tests/test_governor_enforcement.py`, when the full test suite runs, then `KNOWN_OVER_BUDGET["commands/create-spec.md"]` equals the file's measured overage, Step 1.2 added under 700 bytes, and a dated comment above the entry names this spec and the reason, matching the earlier entries' form `[AC-4.3]`
- [ ] Given dogfood fixture question 4, when `/why` answers it and `/create-spec` then runs Steps 1.1 and 1.2 in Plan Mode, then `/why` saved a record under `.writ/research/` whose last `##` section is the handoff, the draft contract carries its Preserve item into Business Rules and its Risk item into Technical Concerns with the record cited, and no file is written under `.writ/specs/` `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write the failing test first. Add `test_create_spec_reads_handoff` to `scripts/tests/test_why_command.py` per technical-spec.md → Tests, reading the heading literal from `commands/why.md` rather than repeating it. Run it and confirm it fails on the missing step `[AC-4.1, AC-4.2]`
- [ ] 4.2 Grep `scripts/` for pins on `Step 1.1` and `Step 1.3` in `commands/create-spec.md`. Then insert Step 1.2 with the text in technical-spec.md → `/create-spec` Step 1.2. Change no other step `[AC-4.1, AC-4.2]`
- [ ] 4.3 Measure the file with `wc -c commands/create-spec.md`. Re-pin `KNOWN_OVER_BUDGET["commands/create-spec.md"]` in `scripts/tests/test_governor_enforcement.py` to the new overage, with a dated comment in the form `# 2026-MM-DD (2026-10-25-why-command Story 4): 13654 -> <new>; Step 1.2 reads a /why handoff.` Stop if the step added 700 bytes or more and shorten it `[AC-4.3]`
- [ ] 4.4 Add the `commands/create-spec.md` heading row for ``Step 1.2: Read a `/why` Handoff`` to `ROWS` in `scripts/eval-command-structure.py` `[AC-4.1]`
- [ ] 4.5 Regenerate the plugin trees with `python3 scripts/gen-platform-trees.py` and confirm `--check` prints `pass` `[AC-4.1]`
- [ ] 4.6 Run dogfood fixture question 4. Follow `commands/why.md` to answer it and save the record. Then follow `commands/create-spec.md` Steps 1.1 and 1.2 only, in Plan Mode, for "add a fifth option to /writ's confirmation", and confirm the draft contract carries the Preserve and Risk items with the record cited. Write no spec files. Record the record path and the carried items in What Was Built `[AC-4.4]`
- [ ] 4.7 Verify. Run `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Confirm 0 failures and 0 findings `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- **Budget.** `commands/create-spec.md` is the tree's largest command and is pinned over budget. Every earlier growth re-pinned `KNOWN_OVER_BUDGET` with a dated disclosure. Do not trim other steps to offset; they are outside this story.
- **No new gate.** Step 1.2 adds no AskQuestion. Under `--recommend`, a carried section is evidence for the recommendation log like any other.
- **Modes.** `--from-issue` and `--from-prototype` replace Phase 1, so Step 1.2 does not run there. That is in scope boundaries as excluded; do not add it.
- **Fixture record.** Keep the saved record under `.writ/research/` as evidence. It is a real why record about Writ.
- **Parallel with Story 3.** Story 3 edits `commands/writ.md`, the prompting guide, and two existing test files. This story touches none of them.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Find handoff in create-spec, Save why record]
- **Shadow paths:** [Change follows, Happy path]
- **Business rules:** [Fixed handoff shape, The handoff maps into the contract, Saved record, Budgets, Generated files are regenerated]
- **Experience:** [Output Shape]
