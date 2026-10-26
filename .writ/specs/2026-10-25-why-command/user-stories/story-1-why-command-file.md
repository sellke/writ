# Story 1: The `/why` Command File

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer about to change code in a Writ project
**I want to** ask `/why` and get the reason from the ADRs, specs, drift logs, and audit notes, with a confidence tier on every claim
**So that** I keep the decisions their authors recorded, and I can tell a recorded reason from a guess

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `commands/why.md`, when its frontmatter is read, then it carries `name: why`, `description`, `problem`, `outcome`, `entry_level: high`, and exactly three `exit_criteria` entries, and the body has `## Overview`, `## Invocation`, `## Required Artifacts`, `## Confidence Tiers`, `## Command Process`, `## Integration with Writ`, `## Completion`, and `## References`, with `## Completion` immediately before `## References` `[AC-1.1]`
- [ ] Given `## Confidence Tiers`, when its first table is read, then the first column lists `Recorded`, `Stated`, `Corroborated`, `Inferred`, `Unknown` in that order, and the section states that code is not evidence of its own intent and that conflicting sources give the lower tier `[AC-1.2]`
- [ ] Given `## Command Process`, when its headings are read, then it has six `### Step N:` headings numbered 1 to 6; Step 2 names `refs/notes/writ`, `drift-log.md`, `What Was Built`, and `.writ/decision-records/`; Step 3 names `git log`; Step 4 reads MCP servers only when the strongest claim is below `Stated` and never prompts to connect or authorize one; and each step says what to do when its source is absent: a subject not found gets one natural-language question, and no `.writ/`, no git repository, or no connected MCP server is named in the answer and skipped `[AC-1.3]`
- [ ] Given Step 6 and the output templates in `commands/why.md`, when read, then the saved-record path is `.writ/research/<YYYY-MM-DD>-why-<slug>.md`, the record ends with `## Preserve / Change / Avoid / Risk` followed by `### Preserve`, `### Change`, `### Avoid`, `### Risk` in that order, and Step 6 runs only when a change follows `[AC-1.4]`
- [ ] Given dogfood fixture questions 1 to 3 in technical-spec.md → Dogfood Fixture, when `/why` answers each in this repository, then each answer's top tier is `Recorded` and cites the expected ledger source, and What Was Built records the three answer lines `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write the failing tests first. Create `scripts/tests/test_why_command.py` with `test_command_file`, `test_tiers`, `test_source_order`, `test_handoff_shape`, `test_budgets`, and `test_step_headings` as technical-spec.md → Tests describes. Use the Python 3.9 standard library and the section helpers in `scripts/tests/test_front_door.py`. Run them and confirm each fails on the missing file, not on an import or syntax error `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [ ] 1.2 Read `skills/plain-prose/SKILL.md`, then write `commands/why.md` frontmatter, `## Overview`, `## Invocation`, and `## Required Artifacts` from technical-spec.md → `commands/why.md` Skeleton. Copy the frontmatter strings exactly. Run `test_command_file` `[AC-1.1]`
- [ ] 1.3 Write `## Confidence Tiers`: the five-row table and the three rules beneath it. Run `test_tiers` `[AC-1.2]`
- [ ] 1.4 Write `## Command Process` Steps 1 to 5 from technical-spec.md → Step contents, with every degradation in technical-spec.md → Error & Rescue Map named in the step it belongs to. Run `test_source_order` and `test_step_headings` `[AC-1.3]`
- [ ] 1.5 Write Step 6 and the two output templates from technical-spec.md → Output Templates, then `## Integration with Writ`, `## Completion` with its Terminal constraint line, and `## References` linking `commands/_preamble.md` and `system-instructions.md`. Run `test_handoff_shape` and `test_budgets` `[AC-1.1, AC-1.4]`
- [ ] 1.6 Run dogfood fixture questions 1 to 3 against this repository by following `commands/why.md`. Record each answer line, top tier, and ledger source in What Was Built. If an answer misses its expected tier, fix the command file, not the fixture `[AC-1.5]`
- [ ] 1.7 Verify. Run the plain-prose scan from `skills/plain-prose/SKILL.md` step 1 on `commands/why.md`. Run `uv run --python 3.9 pytest scripts/tests/test_why_command.py`, then the full `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Expect `check_manifest` to report `commands/why.md` unregistered and `gen-platform-trees.py --check` to report the plugin trees stale until Story 2; every other check passes `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **No helper script, no subagents.** The command is prose plus read-only git calls. See spec.md → 📋 Business Rules (No subagents, Read-only).
- **Platform-neutral names.** Name MCP servers in plain prose, the way `commands/prototype.md` does. A backticked vendor tool name fails the vendor scan in `scripts/gen-platform-trees.py`.
- **Referenced paths.** Backticked `*.md` tokens must resolve or carry a placeholder (`<...>`, `*`, `YYYY`). `drift-log.md` resolves as a basename. Do not link Writ's own ADRs or dated research documents from the command; `scripts/eval-shipped-refs.py` fails on them.
- **Mirroring.** `/writ` Step 4 collects `### Step N` headings when a command has no `### Phase N` headings. Keep the six steps at `###`.
- **Known window.** Between this story and Story 2, `check_manifest` and the generated-tree check fail. Story 2 clears both.
- **Risks.** The command growing past 200 lines; tiers drifting from the table into ad hoc labels in the templates. `test_budgets` and `test_tiers` catch both.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Locate the subject, Find anchor commits, Read git notes, Read ledger files, Read git history, Read MCP server, Save why record]
- **Shadow paths:** [Happy path, Nil input, Empty input, Upstream error, No ledger, Stale ledger, Conflicting sources, Change follows]
- **Business rules:** [Ledger first, The anchor locates, Five tiers, Code is not evidence of its own intent, Null results are reported, Conflicts take the lower tier, MCP only when needed, Read-only, No subagents, A change follows, Fixed handoff shape, Saved record, Budgets, Entry level]
- **Experience:** [Entry Point, Happy Path, Moment of Truth, Feedback Model, Error Experience, State Catalog, Output Shape]
