# Story 3: Implementation and Recovery Command Contracts

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer running Writ's execution pipeline
**I want to** each of the six implementation and recovery commands to declare its own problem, outcome, and exit criteria
**So that** the three nested execution commands stop being distinguishable only by prose, and each declares the scope it actually terminates on

## Scope

Six commands: `implement-phase`, `implement-spec`, `implement-story`, `prototype`, `refactor`, `revert`.

Only `implement-phase` carries a `## Completion` section today. The other five belong to Story 6.

## Acceptance Criteria

- [ ] Given all six files carry `---` frontmatter with `name` and `description` and no `problem:`, when this story lands, then each carries `problem:`, `outcome:`, and `exit_criteria:` in the fixed key order, with 2–4 `exit_criteria` entries.
- [ ] Given `implement-phase`, `implement-spec`, and `implement-story` are nested scopes of the same pipeline, when their fields are read side by side, then each names the **unit it terminates on** — a phase's exit criteria, a spec's story set, a single story's gate results — and no field from one is plausible in either of the other two.
- [ ] Given Business Rule 3, when any `exit_criteria` entry is read, then it names a file path, field value, count or comparison, process outcome, or command-observable state, as a present-tense assertion about post-run state.
- [ ] Given Business Rule 2, when any entry is compared against its own file's `description:`, then it asserts something the description does not already say.
- [ ] Given Business Rule 4, when each file is diffed, then frontmatter grew by at most 7 lines, and `grep -c '^---$'` still returns exactly 2.
- [ ] Given loop bounds are a separate Phase 10 feature, when the frontmatter is read, then no `loop:`, `max_iterations:`, or `on_exhaustion:` key appears — even though four of these six are loop-bearing commands and the temptation is direct.
- [ ] Given Business Rules 9 and 10, when `git diff --name-only` is read, then it lists only these six files — no `scripts/` changes, no `## Completion` sections added, no command body prose rewritten.

## Implementation Tasks

- [ ] 3.1 Read `.writ/docs/component-contract.md` (Story 1) and `commands/new-command.md`'s own frontmatter as the worked exemplar
- [ ] 3.2 For each of the six, identify the concrete terminal artifact and state change — for the three nested commands, write the three termination units down explicitly before authoring anything, since that distinction is the entire value of this batch
- [ ] 3.3 Author `problem:` and `outcome:` for all six as single sentences; swap-test the `implement-*` trio against each other first, then against `prototype`
- [ ] 3.4 Author 2–4 `exit_criteria` per command against real observables — story status values, phase-state entries under `.writ/state/`, git state for `revert`, test/lint results for `prototype` and `refactor`
- [ ] 3.5 Run the restatement test on every entry against its own `description:`
- [ ] 3.6 Verify per file: ≤7 added frontmatter lines, `grep -c '^---$'` = 2, key order correct, and no loop-bound keys present
- [ ] 3.7 Run `bash scripts/eval.sh`; confirm no new findings and no `scripts/` changes; record any scoping defect surfaced in the Notes without acting on it

## Notes

**Technical considerations:**

- The `implement-phase` → `implement-spec` → `implement-story` nesting is the hardest authoring problem in the spec. Each delegates to the next, so a lazily-written `outcome:` for any of the three reads as a fair description of all three. The distinguishing question is *what is true when this command returns that was not true when it was called* — a phase's exit criteria met, a spec's stories all Complete, one story's gates all PASS.
- `/refactor` promises behavior preservation and one revertable commit per concern. Both are observable: tests green before and after, one commit per concern in the log. These are strong criteria and should be used.
- `/revert` operates on git history and on `.writ/` artifacts. Its criteria should name both, since restoring one without the other is the failure this command exists to prevent.
- `/prototype` is explicitly the no-spec-files path. A criterion asserting that spec artifacts exist would contradict the command's own design; assert their *absence* if anything.
- `implement-phase` already has a `## Completion` section — derive from it (BR7), do not transcribe it.

**Risks / challenges:**

- `implement-story.md` is 961 lines, the largest file in the repo. It is also the file progressive disclosure (ADR-021) will rewrite first. Keep the edit to frontmatter only.
- Four of these six are the loop-bearing commands the Phase 10 loop-bounds feature targets. Adding `loop.max_iterations` here would be a scope violation that looks like helpfulness, and it would collide with that spec's own frontmatter edit.
- The `implement-*` trio is where a reviewer should spend their swap-test budget. If any two are interchangeable, the batch fails regardless of line counts.

**Integration points:**

- Story 6 writes `## Completion` for five of these six and will read the `exit_criteria` this story authors.
- The Phase 10 loop-bounds spec adds keys to the same frontmatter blocks in `implement-phase`, `implement-spec`, `implement-story`, and `refactor`. Fixed key order (spec.md → The contract schema) is what keeps that a clean append rather than a conflict.
- Progressive disclosure will rewrite `implement-story.md` wholesale later.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] The three nested `implement-*` commands verified as mutually non-interchangeable
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] No loop-bound keys introduced

## Context for Agents

- **Business rules:** [BR1 swap test, BR2 restatement test, BR3 observable requirement, BR4 line budget, BR5 one-line fields, BR7 no contradiction with `## Completion`, BR9 no eval checks, BR10 no substance rewrite] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The contract schema; Command batching → Implementation & recovery] — from spec.md → ## Detailed Requirements
- **Out of scope:** [Loop bounds are a separate Phase 10 feature with its own spec, even though they land in the same frontmatter block] — from spec.md → ## Out of Scope
- **Contract:** [Hardest constraint: each command's fields are derived from what it actually does] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Authoring `exit_criteria` — worked examples; Interaction Edge Cases → `implement-story.md` and `create-spec.md`] — from sub-specs/technical-spec.md
