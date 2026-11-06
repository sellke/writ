# Story 5: Supervisor reads the story-gate record

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** `/implement-spec` or `/implement-phase` orchestrator that accepts or rejects a story's report
**I want to** the supervisor to reject a story without a valid story-gate record for its final code commit, and to read check verdicts from that record
**So that** a lane cannot skip a check and still pass (retro F6), and the supervisor stops re-running the three checkers when the record already holds their verdicts

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.5

- [ ] Given `agents/supervisor-agent.md`, when it is read, then it declares an optional input `story_gate_record`, and a missing post-review record, in any mode, yields a claim `story-gate record missing` marked false with `RERUN` `[AC-5.1]`
- [ ] Given a post-review record whose `head_sha` is not the story's final code commit or whose `dirty` is `true`, when the supervisor checks it, then it returns `RERUN` with a false claim that names the mismatch or the dirty flag `[AC-5.2]`
- [ ] Given a valid record, when a report claim about a check verdict disagrees with it, then the claim is `false`, and the supervisor reads `review-override.py`, `test-integrity.py`, and `drift-format.py` verdicts from the record instead of re-running them `[AC-5.3]`
- [ ] Given `commands/implement-spec.md`, when it is read, then Step 2.3 is absent, Step 2.3b remains, the Step 3.3 `.writ/context.md` regeneration bullet is absent, the Step 3.3 supervisor spawn passes the story-gate record path, and `postRun.contextRewritten` is still recorded `[AC-5.4]`
- [ ] Given the changed source files, when `python3 scripts/gen-platform-trees.py --check` runs, then every generated copy matches its source, and `KNOWN_OVER_BUDGET` holds a dated entry for each changed byte size the test covers `[AC-5.5]`

## Implementation Tasks

- [ ] 5.1 Write tests in `scripts/tests/test_supervisor_story_gate_record.py` that fail now. Pin key phrases, not whole paragraphs: the input name, the three `RERUN` rules, the record-verdict rule, and the `implement-spec.md` step changes `[AC-5.1, AC-5.2, AC-5.3, AC-5.4]`
- [ ] 5.2 Edit `agents/supervisor-agent.md` to add the optional `story_gate_record` input, the missing-record, head-SHA, and dirty-flag `RERUN` rules, the false-claim rule, and the rule that a valid record replaces re-running the three checkers `[AC-5.1, AC-5.2, AC-5.3]`
- [ ] 5.3 Edit `commands/implement-spec.md`: delete Step 2.3, keep Step 2.3b, delete the `.writ/context.md` regeneration bullet in Step 3.3, and pass the post-review record path in the supervisor spawn `[AC-5.4]`
- [ ] 5.4 Edit the `postRun.contextRewritten` description in `commands/implement-spec.md` so it says `implement-story` Step 4 sets it. Keep the `typecheck`, `testSuite`, and `at` fields unchanged `[AC-5.4]`
- [ ] 5.5 Run `python3 scripts/gen-platform-trees.py`. Add dated `KNOWN_OVER_BUDGET` entries in `scripts/tests/test_governor_enforcement.py` for each changed byte size the test covers `[AC-5.5]`
- [ ] 5.6 Verify acceptance criteria: map each criterion to a passing test in `scripts/tests/test_supervisor_story_gate_record.py` or `scripts/tests/test_governor_enforcement.py` `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`
- [ ] 5.7 Verify all tests pass: run the new test file and `test_governor_enforcement.py` under Python 3.9 and 3.14 with `uv run --isolated`, then run `gen-platform-trees.py --check` `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

## Notes

- **Source of the rules.** `technical-spec.md` → `## Supervisor change (Story 5)` and `## implement-spec.md cuts (Story 5)` define the behavior. Cite those sections; do not copy them into the agent file.
- **Record contract.** The record is `story-gate-v1` from Story 3, with `head_sha` and `dirty`. Story 3 owns the schema and path. Do not redefine them here.
- **Final code commit.** The technical spec defines it as the last commit in `base_commit..head_ref` that touches a non-Writ-artifact file. A commit after the post-review record makes the record stale (Business Rule 5).
- **`--quick`:** it writes a post-review record too (spec.md → State Catalog), so the supervisor needs no mode signal. Every mode needs the record.
- **Claim strings:** all three are in `technical-spec.md` → Supervisor change (missing, head mismatch, dirty tree). Pin them in Task 5.1.
- **`postRun` contract.** `exit-criteria.py` reads `preflight` and `postRun` for `implement-spec` c1–c4. Keep field names and types. Only the source of `contextRewritten` changes.
- **`KNOWN_OVER_BUDGET` scope.** The test keys entries by command stem (`Path(subject).stem`). Add entries only for files the test measures: `implement-spec.md`, and `supervisor-agent.md` only if the test reports it.
- **Generated copies.** Do not hand-edit `claude-code/agents/writ-supervisor.md`, `cursor/plugin/`, or `codex/`. Edit the sources, then regenerate.
- **File ownership.** This story edits `agents/supervisor-agent.md` and `commands/implement-spec.md` only, plus its tests and the budget entry. Story 3 owns `implement-story.md`. Story 4 owns the coding, evaluator, and review agents.
- **Python 3.9 floor.** Use stdlib only. The tests read Markdown and do not need the runner.
- **Targeted verification only.** The full pytest suite on both interpreters, the bash tests, and `scripts/eval.sh` run once at the end of the spec, not in this story. Run pytest alone. `eval.sh`, bash tests, `.writ/state/` writes, or `git worktree` changes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged`.

## Context for Agents

- **Business rules:** [Business Rule 5] — spec.md → ## Specification Contract → 📋 Business Rules
- **Error map rows:** [Supervisor read] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Coder commits again after post-review `pass`] — technical-spec.md → ## Interaction Edge Cases
- **Experience:** [No record at all, Code committed after the post-review record, `--quick`] — spec.md → ## 🎯 Experience Design → ### State Catalog
