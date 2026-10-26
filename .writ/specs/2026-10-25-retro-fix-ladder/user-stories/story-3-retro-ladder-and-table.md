# Story 3: /retro Fix Ladder, Proof, Rule Table, and Signal Retirement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** maintainer who runs `/retro` after an implementation run
**I want to** see each mistake fixed at the highest rung that works, proven by a check that fails on the real past mistake, and recorded in a rule-to-enforcer table
**So that** a rule that caused a mistake stops depending on an agent reading prose, and every retro file passes `scripts/retro-check.py`.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `commands/retro.md` § Step 5, when the `### Fix ladder` table is read top to bottom, then its first column reads `architecture`, `types`, `lint`, `test`, `docs` in that order, each row has a "what it is in /retro" cell and a route cell, and the step contains the Ladder grammar `<rung>: no (<reason>); ...; <rung>: yes` and the Proof grammar, which starts `mistake <ref>; check ` and ends `; result <fails|passes|pending>` `[AC-3.1]`
- [ ] Given `commands/retro.md` § Step 6 and § Step 8, when read, then Step 6 says an Apply on architecture, types, or lint runs the proof, and a check that does not fail restores the file, sets result `passes`, and records disposition `issue`, while a check that cannot run sets result `pending` and records disposition `issue`; and Step 8 names `## Transcripts`, `## Findings`, `**Disposition:**`, `## Rule table changes`, `.writ/retros/rule-enforcers.md`, and `python3 scripts/retro-check.py --retro <file>` `[AC-3.2]`
- [ ] Given `commands/retro.md` § Step 3 and § Step 4, when read, then the Step 3 signal is named `Writ command defect`, its counting rule says a user correction against a rule whose enforcer is `none` counts on its own as a Repeated mistake, and Step 4 reads `.writ/retros/rule-enforcers.md` before ranking and names `enforcer did not hold` beside `fix did not hold` `[AC-3.3]`
- [ ] Given the full text of `commands/retro.md`, when searched, then none of `signals.jsonl`, `signal.py`, `ADR-025`, `--friction`, or `Writ friction` appears, Step 7 still contains `read-only` and `mutates no knowledge file`, and the file is under 24,960 bytes `[AC-3.4]`
- [ ] Given the frontmatter of `commands/retro.md`, when read, then `description` equals the value recorded before the edit, `exit_criteria` keeps its three existing lines and adds one line containing `cites a proof run against a real past mistake` and one containing `retro-check.py --retro`, and `outcome` names the highest-rung fix and the rule table `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Read `scripts/tests/test_governor_mutation.py` first, then extend `scripts/tests/test_retro_fix_ladder.py` (created by Story 2) with pins that read `commands/retro.md` as text. Pin the five rungs in order inside the Fix ladder table, the Ladder and Proof grammar strings, the table path, `retro-check.py`, `Writ command defect`, the absence of the banned tokens, the `read-only` and `mutates no knowledge file` literals, and the byte ceiling. Name the AC IDs in test docstrings. Run the file and confirm the new pins fail on the current text `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.2 Edit the frontmatter `outcome` and `exit_criteria` of `commands/retro.md`, leaving `description` unchanged. Add the ladder principle line to Overview → Principles `[AC-3.5]`
- [ ] 3.3 Edit Steps 2 to 4 by section heading. In Step 2, delete the `signals.jsonl` sentence. In Step 3, rename the "Writ friction" row to "Writ command defect" and add the unenforced-rule counting sentence. In Step 4, add the rule-table read before ranking and the **enforcer did not hold** rule beside **fix did not hold** `[AC-3.3, AC-3.4]`
- [ ] 3.4 Edit Steps 5 and 6. In Step 5, replace the example with a finding that carries Rule, Rung, Ladder, Target, Change, Proof, and Route. Add the `### Fix ladder` table, the Ladder and Proof grammar paragraphs, and the note that a source or test edit routes `issue` with the proof as the done check. Keep "Never target source code or tests." In Step 6, add the proof run after an Apply and the restore-and-`issue` branch `[AC-3.1, AC-3.2]`
- [ ] 3.5 Edit Step 8, Error Handling, and Integration with Writ. Step 8 gets the `## Transcripts` and `## Findings` headings, `**Disposition:**` per finding, `## Rule table changes`, the table update (create with heading and header row when absent), and the `retro-check.py` run with one re-run on `fail`. Error Handling drops the ADR-025 clause and gains three rows. Integration drops the ADR-025 row and notes that a logged `execution failure` is a ladder candidate `[AC-3.2, AC-3.4]`
- [ ] 3.6 Run `python3 scripts/gen-platform-trees.py` to regenerate copies. Never hand-edit them. Run `python3 scripts/gen-platform-trees.py --check` and the new pins. Confirm they pass `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [ ] 3.7 Run `uv run --python 3.9 pytest`, the bash loop `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside any sandbox. Confirm no failures and no findings from `commands/retro.md` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Notes

- **Dependencies:** Story 1 ships `scripts/retro-check.py`, which Step 8 calls. Story 2 seeds `.writ/retros/rule-enforcers.md`. `check_referenced_paths` in `scripts/eval.sh` fails when `commands/retro.md` cites a `*.md` path that does not exist, so the seeded table must exist before task 3.5 runs.
- **Byte ceiling:** `COMMAND_BYTE_BUDGET` in `scripts/eval-leanness.py` is 24,960 bytes. The check is reported and does not block. `commands/retro.md` is 14,135 bytes today. The pin in task 3.1 enforces the ceiling for this story.
- **Padding test:** `scripts/tests/test_governor_mutation.py` pads `commands/retro.md` by 12,000 bytes and calls the clean file comfortably compliant. The file grows in this story. If that test's assertion fails at the new size, stop and report it. Do not change the padding in this story.
- **eval.sh pins that must keep passing:** `check_knowledge_consolidate` (`read-only` and `mutates no knowledge file` in Step 7), `check_referenced_paths` (the table path), and `check_shipped_refs` (no links to `.writ/research/` or `.writ/decision-records/`).
- **Generated copies:** `plugins/writ/commands/`, `cursor/plugin/commands/`, and `plugins/writ/scripts/` are generated. Edit only `commands/retro.md`.
- **Prose:** Every added line follows `skills/plain-prose/SKILL.md`.
- **Parallel work:** Story 4 edits `commands/refresh-command.md` and does not touch this file. No file overlap.
- **Eval:** `bash scripts/eval.sh` runs `git init` in a temp dir, so run it outside any sandbox.

## Context for Agents

- **Error map rows:** [`/retro` Step 6 proof run (check passes; check cannot run), `/retro` Step 8 table update, `/retro` Step 8 retro-check run (fails twice)] from technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Lint-rung ladder finding with a passing proof; no rule table yet] from technical-spec.md → ## Shadow Paths (`/retro` ladder finding row)
- **Business rules:** [1 rung vocabulary, 2 ladder signals, 3 ladder line shape, 4 rung meanings, 5 route by edit type, 6 proof line, 7 proof outcomes, 8 running a proof, 9 table format, 12 retro file headings] from spec.md → ## Business Rules (Expanded)
- **Experience:** [Proof fails to fail, Proof cannot run, retro-check prints fail, No table yet] from spec.md → ## Experience Design → ### State Catalog
- **Edge cases:** [Two findings name the same rule; table edited by hand] from technical-spec.md → ## Interaction Edge Cases
- **Current text to edit:** the friction remnants list in technical-spec.md → ## Current State, and the per-section edits in technical-spec.md → ## `commands/retro.md` changes (by section)
- **Pin scope:** technical-spec.md → ## Tests, row for `scripts/tests/test_retro_fix_ladder.py`
- **Retro-check output and reason codes:** technical-spec.md → ## `retro-check.py` (read only to confirm the Step 8 call and the `fail` branch)
