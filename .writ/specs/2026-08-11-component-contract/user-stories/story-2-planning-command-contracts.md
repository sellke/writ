# Story 2: Planning and Specification Command Contracts

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer or agent reading Writ's planning commands
**I want to** each of the ten planning and specification commands to declare its own problem, outcome, and exit criteria
**So that** the question "did `/create-spec` finish, or did it just stop?" has a declared answer in the file rather than an inference from prose

## Scope

Ten commands: `plan-product`, `create-spec`, `edit-spec`, `assess-spec`, `create-adr`, `create-uat-plan`, `research`, `design`, `knowledge`, `create-issue`.

Nine of the ten already carry a `## Completion` section — `create-adr`, `create-issue`, `create-spec`, `create-uat-plan`, `design`, `edit-spec`, `knowledge`, `plan-product`, `research`. Only `assess-spec` lacks one. For the nine, `exit_criteria` are derived **from** the existing section per Business Rule 7; `assess-spec`'s section belongs to Story 6.

## Acceptance Criteria

- [ ] Given all ten files carry `---` frontmatter with `name` and `description` and no `problem:`, when this story lands, then each carries `problem:`, `outcome:`, and `exit_criteria:` in the fixed key order, with 2–4 `exit_criteria` entries.
- [ ] Given Business Rule 3, when any `exit_criteria` entry is read, then it names at least one of: a file or directory path, a field value, a count or comparison, a process outcome, or a command-observable state — written as a present-tense assertion about post-run state.
- [ ] Given Business Rule 1, when any entry from any of the ten is pasted into a different one of the ten, then it reads as false or nonsensical there. `/create-spec` and `/edit-spec` are the hardest neighbours in this batch and must be checked explicitly against each other.
- [ ] Given Business Rule 2, when any entry is compared against its own file's `description:`, then it asserts something the description does not already say.
- [ ] Given Business Rule 7, when a file already has a `## Completion` section, then its `exit_criteria` are consistent with that section and do not contradict it; any contradiction found is resolved in favour of the file's actual behavior and recorded in the notes.
- [ ] Given Business Rule 4, when each file is diffed, then frontmatter grew by at most 7 lines, and `grep -c '^---$'` still returns exactly 2.
- [ ] Given Business Rules 9 and 10, when `git diff --name-only` is read, then it lists only these ten files — no `scripts/` changes, no `## Completion` sections added, no command body prose rewritten.

## Implementation Tasks

- [ ] 2.1 Read `.writ/docs/component-contract.md` (Story 1) and `commands/new-command.md`'s own frontmatter as the worked exemplar
- [ ] 2.2 For each of the ten, read the command's Overview, Command Process, and existing `## Completion` section (nine have one) and write down, in scratch, the concrete artifacts and state changes it produces — paths, status values, counts
- [ ] 2.3 Author `problem:` and `outcome:` for all ten as single sentences, then run the swap test across the batch, paying particular attention to the `create-spec` / `edit-spec` / `assess-spec` cluster and the `create-adr` / `knowledge` / `create-issue` cluster, which are the two places boilerplate is most likely to survive undetected
- [ ] 2.4 Author 2–4 `exit_criteria` per command, each naming an observable from Task 2.2's scratch list; reject any entry that would survive being pasted into a sibling
- [ ] 2.5 Run the restatement test on every entry against its own `description:`; rewrite any that merely rephrase it
- [ ] 2.6 Verify per file: ≤7 added frontmatter lines, `grep -c '^---$'` = 2, key order correct, `exit_criteria` is a block sequence of quoted strings
- [ ] 2.7 Run `bash scripts/eval.sh`; confirm no new findings and no `scripts/` changes; record any scoping defect surfaced during authoring in the Notes below without acting on it

## Notes

**Technical considerations:**

- This is the largest batch and the one with the most semantically adjacent commands. `/create-spec`, `/edit-spec`, and `/assess-spec` all operate on the same artifact; if their three `outcome:` lines could be shuffled without anyone noticing, the batch has failed regardless of what the checks say.
- `/design`, `/research`, and `/knowledge` produce artifacts at known paths — these are the easiest observables in the whole spec and should set the quality bar for the rest.
- `/plan-product` has a `--reconcile` mode with a materially different outcome from a fresh run. One `outcome:` line must cover both, or must name the dominant case honestly. Do not use a block scalar to fit both (BR5).
- `/create-issue` is explicitly a speed-over-completeness command. Its `exit_criteria` should reflect that — a criterion asserting thoroughness would contradict the command's own stated design.

**Risks / challenges:**

- `create-spec.md` is 865 lines. Reading it fully costs real context, and skimming it is exactly how a boilerplate `outcome:` gets written. Budget for the read.
- Nine of ten files already have a `## Completion` section, which makes it tempting to transcribe those sections into `exit_criteria`. Transcription is not derivation — the section is prose about the run, the criteria are assertions about post-run state. Related (BR7), not identical.
- Authoring ten files in one pass invites convergence: by file eight the phrasing template is set and the last three get filled in. Re-run the swap test at the end of the batch, not per file.

**Integration points:**

- Story 6 writes `assess-spec`'s `## Completion` section and will read the `exit_criteria` this story authors for it.
- `2026-08-11-governor-instrumentation` consumes these fields as its `structural` check target.
- Progressive disclosure (ADR-021) will later rewrite `create-spec.md` wholesale; keep this edit additive and surgical so that rewrite has minimal merge surface.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Swap test run across the full batch after the last file, not only per file
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] Any scoping defect surfaced is recorded, not acted on (BR10)

## Context for Agents

- **Business rules:** [BR1 swap test, BR2 restatement test, BR3 observable requirement, BR4 line budget, BR5 one-line fields, BR7 no contradiction with `## Completion`, BR9 no eval checks, BR10 no substance rewrite] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The contract schema; Command batching → Planning & specification] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Authoring 31 commands' worth of derived fields is the part most likely to degrade under time pressure] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: `exit_criteria` must be machine-checkable assertions, not restated descriptions] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Authoring `exit_criteria` — worked examples; Placement Rules; Line Budget Arithmetic] — from sub-specs/technical-spec.md
