# Story 4: Consumer Wiring and Ordered-Commit Integration

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** developer fixing a bug through `/prototype` or `/implement-story` **I want to** have both consumers reach the repro-first bug path and re-check the commit order after integration **So that** the failing repro lands before the fix in my checkout, and a broken order shows up in the run's report instead of passing quietly.

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given `commands/prototype.md` Step 3, when it is read, then principle 1 names the bug path in `skills/tdd-cycle/SKILL.md`, and a `**Bug path:**` line records the base from `git rev-parse HEAD`, re-runs `python3 scripts/repro-order.py check --repo . --base <that SHA>` after integration, puts the output and the failing-then-passing output in the Step 5 summary; the line fires only when the report's `### Repro` block names commits, so a `Repro: off` report never triggers it; Step 2.5 is byte-identical to its state before this story `[AC-4.1]`
- [ ] Given `commands/implement-story.md` Gate 1, when it is read, then a `**Bug path:**` line records the base, re-runs the check after integration, prints a `repro-order:` line in the Step 4 report, maps `fail` to `⚠️ DEGRADED` with its reason lines, lets `unverifiable` print and continue without DEGRADED, and fires only when the report's `### Repro` block names commits (a `Repro: off` report never triggers it); Gates 0, 2.5, and 3 and the `gates:` frontmatter (`gate1_coding: prose-only`) are unchanged `[AC-4.2]`
- [ ] Given `skills/subagent-worktree-integration/SKILL.md`, when step 3 ends, then an "Ordered commits" paragraph says to carry commits with `git cherry-pick` oldest first instead of copying files, and says that on a conflict the orchestrator runs `git cherry-pick --abort`, copies the files, and reports that the order was lost `[AC-4.3]`
- [ ] Given `scripts/tests/test_repro_first_wiring.py`, when any one Removal Inventory row's text or file is deleted from the repo, then at least one test in that module fails and names the row; every text row in `spec.md` → `## Removal Inventory` is pinned, and the generated-trees row is covered by `python3 scripts/gen-platform-trees.py --check` `[AC-4.4]`
- [ ] Given the finished change, when the gates run, then `python3 scripts/gen-platform-trees.py --check` passes, `uv run --python 3.9 pytest` passes, the bash test loop prints no `FAIL` line, and `bash scripts/eval.sh` reports zero findings `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Extend `scripts/tests/test_repro_first_wiring.py` with text checks for the two `**Bug path:**` lines, the fires-only-on-named-commits condition, the ordered-commits paragraph, and one pin per Removal Inventory row. Create the module if Story 2 has not. Run it and confirm the new checks fail before any command or skill edit `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.2 Edit `commands/prototype.md` Step 3: replace principle 1's line with the bug-path sentence, and add the `**Bug path:**` line after the integration paragraph. Do not edit Step 2.5 or the spawn text `[AC-4.1]`
- [ ] 4.3 Edit `commands/implement-story.md` Gate 1: add the `**Bug path:**` line after `**Report:**`. Leave the Gate 1 `**On STATUS: BLOCKED**` handling and the `gates:` frontmatter as they are `[AC-4.2]`
- [ ] 4.4 Add the "Ordered commits" paragraph at the end of step 3 in `skills/subagent-worktree-integration/SKILL.md`. Run `bash scripts/lint-skill.sh skills/subagent-worktree-integration/SKILL.md` `[AC-4.3]`
- [ ] 4.5 Run `python3 scripts/gen-platform-trees.py`, then `python3 scripts/gen-platform-trees.py --check`. Do not hand-edit `claude-code/`, `cursor/`, `codex/`, or plugin trees `[AC-4.5]`
- [ ] 4.6 Run `python3 scripts/verdict-provenance.py check --command commands/implement-story.md` and the wiring module. Confirm the Gate 1 line did not make a gate name both a script and prose-only, and that every Removal Inventory pin passes `[AC-4.2, AC-4.4]`
- [ ] 4.7 Verify: `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` outside any sandbox. Review `git diff` and confirm the only edits are `commands/prototype.md` Step 3, `commands/implement-story.md` Gate 1, the integration skill's step 3 paragraph, the wiring module, and generated trees `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Notes

- **Cherry-pick conflicts.** A worktree branched from a stale base can conflict on cherry-pick. The paragraph says to abort and copy files. The re-run check then fails `no_repro_commit`, so the loss shows in the report. Test a conflict case in the wiring checks by text only; the behavior itself belongs to the skill's instructions.
- **Sibling specs on the same files.** The design-divergence spec owns `/prototype` Step 2.5 and Gate 0. The Gate 2.5 and Gate 3 spec owns those sections of `/implement-story`. Both edit the same command files. Keep this story's diff to the lines named above, and rebase on any sibling commit that lands first.
- **DEGRADED stops the spec.** A post-integration `fail` marks the story `⚠️ DEGRADED`, and a DEGRADED story can stop `/implement-spec`. A false `fail` from `repro-order.py` therefore blocks a whole spec run. Run the check against a real bug-fix history before wiring it into the consumers.
- **Pins for earlier stories.** The wiring module pins Removal Inventory rows that Stories 2 and 3 create. Those rows must exist before task 4.6 can pass.
- **Generated trees.** Command and skill edits reach the platform trees only through `scripts/gen-platform-trees.py`. A hand edit in a generated tree fails `--check`.

## Context for Agents

- **Error map rows:** `technical-spec.md → ## Error & Rescue Map → Integration` (cherry-pick conflict; abort, copy, report `no_repro_commit`)
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path: repro then fix, check `pass`, orchestrator re-run `pass`)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 9 switch-off: neither consumer runs the check; Rule 10 enforcement differs by consumer; Rule 11 the path adds no spawn)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Check fails after integration; Merge commit in the range; Cherry-pick conflict at integration)
- **Consumer lines:** `technical-spec.md → ## Consumer Lines` (the three replacement or new lines for `/prototype` Step 3, `/implement-story` Gate 1, and the integration skill)
- **Removal Inventory:** `spec.md → ## Removal Inventory` (every row; the wiring module pins each)
- **Tests:** `technical-spec.md → ## Tests → ### scripts/tests/test_repro_first_wiring.py`
- **Verdict check:** `scripts/verdict-provenance.py` (`entry_both_sources`) and `agents/coding-agent.md` are out of scope for this story
