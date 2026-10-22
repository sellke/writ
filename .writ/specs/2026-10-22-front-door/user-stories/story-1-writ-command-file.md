# Story 1: The `/writ` Command File

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** new user who has read the prompting guide, or a returning user who does not want to choose between `/prototype` and `/create-spec`
**I want to** type `/writ "<request>"` and get my request restated, routed to one fitting command, confirmed once, and run with its phases on the todo list
**So that** my work starts at the right level of ceremony without my knowing the command set

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `commands/writ.md` with the contracted frontmatter (`name`, `description`, `problem`, `outcome`, `entry_level: high`, four `exit_criteria`) and the sections Overview, Invocation, Required Artifacts, Command Process, Routing Rules, Completion, and References, when `test_command_file` runs, then it passes, the file is under 200 lines, and References links `commands/_preamble.md` and `system-instructions.md` `[AC-1.1]`
- [ ] Given a request that lacks a goal, a done check, or proof, when Step 1 restates it, then the restatement uses the labeled lines `Goal:`, `Problem:`, and `Done check:` (plus `Proof:` when the request names evidence), a missing part is named in the guide's terms and linked to `.writ/docs/prompting-guide.md` § What a request carries, a missing done check or proof does not block routing, a missing goal produces one natural-language question and no menu, and `test_guide_cited` passes `[AC-1.2]`
- [ ] Given the `## Routing Rules` table, when `test_routing_rules` runs, then its first table has six data rows whose Route cells, in order, are `/prototype`, `/prototype --no-diverge`, `/create-spec`, `/implement-phase <N>`, `/research`, and `/prototype` with the fork named, the fifth row mentions `/why`, and Step 2 sends a `/prototype --no-diverge` versus `/create-spec` conflict to `/create-spec` when any `/prototype` escalation signal fires `[AC-1.3]`
- [ ] Given a classified route, when Step 3 runs, then exactly one AskQuestion shows the restatement, a one-line reason, the proposed route labeled `(Recommended)`, every other route as an option, and `Not what I meant` last, and `test_confirmation_step` passes `[AC-1.4]`
- [ ] Given a confirmed route, when Steps 4 and 5 run, then each `### Phase N` heading of the routed command (or each `### Step N` heading when it has no phases) becomes one todo item, in order, before its first phase runs; a phase the chosen flags skip reads `skip: <reason>`; on a platform whose `todo_write` maps to a file, the checklist is printed and nothing is written; the routed command file is read and followed top to bottom with the restatement as its request; `/writ` creates no file under `.writ/`; and `test_mirroring_step` passes `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write the five failing tests in `scripts/tests/test_front_door.py` (command-file section): `test_command_file`, `test_routing_rules`, `test_confirmation_step`, `test_mirroring_step`, `test_guide_cited`, with assertions from technical-spec.md § Tests. Use Python 3.9 stdlib and read the markdown as text, as `scripts/tests/test_platform_neutral_names.py` does. Run `uv run --python 3.9 pytest scripts/tests/test_front_door.py` and confirm all five fail because `commands/writ.md` does not exist `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Write the `commands/writ.md` frontmatter from technical-spec.md § `commands/writ.md` Skeleton: `name: writ`, `description`, `problem`, `outcome`, `entry_level: high`, four `exit_criteria`. Add `## Overview`, `## Invocation` (`/writ "<request>"`, `/writ` with conversation context, `/writ @file`), and `## Required Artifacts` (none required; roadmap and prompting guide optional, with the degradation stated). Add `## References` linking `commands/_preamble.md` and `system-instructions.md`. Run `test_command_file` to green `[AC-1.1]`
- [ ] 1.3 Write `### Step 1: Restate` and `### Step 2: Classify`. Step 1 uses the labeled lines, the optional Proof line, and the missing-part wording from spec.md → ## Business Rules (Expanded) Rule 3. Step 2 applies the tie-break from Rule 2 and states the empirical-fork test: could a throwaway run answer this faster than asking? Run `test_guide_cited` to green `[AC-1.2]`
- [ ] 1.4 Write `## Routing Rules` with the six rows in the exact order and wording of technical-spec.md § Routing Rules table, Signal and Route columns both. Run `test_routing_rules` to green `[AC-1.3]`
- [ ] 1.5 Write `### Step 3: Confirm` with the AskQuestion block from technical-spec.md § Step 3 AskQuestion. Run `test_confirmation_step` to green `[AC-1.4]`
- [ ] 1.6 Write `### Step 4: Mirror the Route's Phases`, `### Step 5: Run the Route`, and `## Completion`. Run `test_mirroring_step` to green `[AC-1.5]`
- [ ] 1.7 Verify: `wc -l commands/writ.md` reports under 200; `uv run --python 3.9 pytest` and `uv run --python 3.9 pytest scripts/tests/test_front_door.py` pass; the bash test loop prints no `FAIL` line; `bash scripts/eval.sh`, run outside any sandbox, reports only the findings listed in Notes `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Thin command.** Target under 200 lines. A routed command's own steps inside `commands/writ.md` mean logic has leaked in. Cut it and keep the handoff.
- **One classifier.** The rule table is the only classification logic. Copy the rows from technical-spec.md § Routing Rules table; the wording is fixed.
- **Empirical-fork test.** "Could a throwaway run answer this faster than asking?" If yes, route to `/prototype` with the fork named as the thing to try, and the confirmation says so. Source: spec.md → ## Technical Concerns.
- **Confirmation versus `/prototype`.** ADR-001 assigns bounded choices to AskQuestion. `/prototype` keeps its single natural-language clarifying question for ambiguous input. `/writ` asks once about the route. Both hold. Source: spec.md → ## Technical Concerns.
- **Stale Claude Code row.** Until Story 2 changes the Claude Code `todo_write` row to `TodoWrite`, Step 4 takes the file-write branch and prints the checklist. This is expected. This story does not fix the row.
- **Expected eval findings.** `check_manifest` flags `commands/writ.md` as unregistered until Story 2. `check_referenced_paths` flags `.writ/docs/prompting-guide.md` until `2026-10-22-prompting-guide` lands. Record both in What Was Built. No other findings are acceptable.
- **Dependency gap.** The brief sets Dependencies to None. The guide path still has to resolve for `check_referenced_paths`, so this story's eval run is clean only after the prompting-guide spec lands. Consider setting Dependencies to `2026-10-22-prompting-guide`.
- **Missing routed command file.** Name the missing file and `/update-writ`. Do not improvise the workflow. Source: technical-spec.md → ## Shadow Paths, Upstream error.
- **Plugin namespace.** Under a Claude Code plugin the command reads `/writ:writ`. Accepted at discovery. The plugin spec documents it. No change here.
- **Symlinks.** `.claude/` and `.cursor/` point at `commands/`. Write `commands/writ.md` only. Do not run `install.sh` on this repo.
- **Technical references.** technical-spec.md → ## `commands/writ.md` Skeleton, ### Routing Rules table (exact rows, in order), ### Step 3 AskQuestion, ## Tests (`scripts/tests/test_front_door.py`). Reference by section heading, never by line number.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rules 1 rule table is the classifier, 2 tie-break, 3 restatement shape, 4 one confirmation, 5 phase mirroring, 6 handoff, 7 no artifacts, 11 entry level, 12 runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (goal, done check, and proof present; done check or proof missing; goal missing; roadmap phase or feature named; why or how question; fork; another route picked; Not what I meant; routed command has phases; route skips a phase; todo_write maps to a file; no request and no context), `spec.md → ## Experience Design → ### Interaction Patterns`
