# Story 3: Remove the ADR-025 No-Op Lines and Correct the /ship Description

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ user whose agent runs `/create-spec`, `/implement-story`, or `/ship`
**I want to** have the instructions to print `escalated(...)` lines nothing reads removed, and `/ship` described as opening a PR
**So that** agents stop doing work with no consumer, and nobody expects `/ship` to merge

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `commands/`, when `grep -rn "no-op until ADR-025" commands` and `grep -rn "The line has no sink today" commands` run, then both print nothing, `commands/create-spec.md` Step 2.6a has numbered items 1 to 3 only, and the Gate 0 anchor confirmation in `commands/implement-story.md` contains no `escalated(` emit `[AC-3.1]`
- [ ] Given the same two sections, when they are read and `scripts/eval.sh` `check_model_escalation` runs, then each section still re-runs a failing floor result once at `anchor` and carries its iteration sentence verbatim (spec.md Business Rule 5), and the check still requires both sentences and forbids `loop.max_iterations` in `create-spec.md`, with no `noop_prefix`, `missing_sink`, or `escalated(agent=` pin left `[AC-3.2]`
- [ ] Given `commands/ship.md`, when its frontmatter `description` and its `## Overview` section are read, then neither contains "merged PR", "branch to merged", or "gets it merged", both say `/ship` opens a pull request, and the `problem`, `outcome`, and `exit_criteria` frontmatter values are byte-identical to before `[AC-3.3]`
- [ ] Given `scripts/tests/test_governor_enforcement.py` after the edits, when it runs, then `commands/ship.md` is at most 28,990 bytes, and the `KNOWN_OVER_BUDGET` entries for `commands/create-spec.md` and `commands/implement-story.md` equal each file's new size minus 24,960, each lower than before and each with a dated comment `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write failing tests first: add a Story 3 class to `scripts/tests/test_harness_cuts.py` covering AC-3.1's two greps and AC-3.3's wording checks; in `scripts/tests/test_implement_story_default_path.py:228-230`, replace the three `assertIn` lines with `assertNotIn` for `(no-op until ADR-025 Story 1)`, `The line has no sink today`, and `escalated(agent=architecture-check-agent`, and keep the `PAIR_COUNTS_ONCE` assertion. Run them and record the failures `[AC-3.1, AC-3.2, AC-3.3]`
- [ ] 3.2 `commands/create-spec.md`: delete Step 2.6a item 4 (line 773). Leave items 1 to 3 and the "Escalation fires only on a *returned* file…" paragraph byte-identical `[AC-3.1, AC-3.2]`
- [ ] 3.3 `commands/implement-story.md` Gate 0 anchor confirmation (line 192): delete from "On the re-run emit" through "a `/retro --friction` consumer." Keep the sentence starting "Iteration accounting:" verbatim `[AC-3.1, AC-3.2]`
- [ ] 3.4 `scripts/eval.sh` `check_model_escalation`: delete the `noop_prefix` and `missing_sink` locals and the six `require_literal` pins that use them or the `escalated(agent=` literals. Keep the two iteration pins and the `loop.max_iterations` forbid. Rewrite the header comment to say the check pins the escalate-once accounting at both floor-tier sites `[AC-3.2]`
- [ ] 3.5 `commands/ship.md`: reword the `description` (line 3) and the Overview (lines 17, 19, 25) to say `/ship` takes a green branch to an open PR. Measure with `wc -c commands/ship.md`; it must not exceed 28,990 bytes `[AC-3.3, AC-3.4]`
- [ ] 3.6 `scripts/tests/test_governor_enforcement.py` `KNOWN_OVER_BUDGET`: set `commands/create-spec.md` and `commands/implement-story.md` to their measured overage, and `commands/ship.md` too if it shrank, each with one dated comment line in the ledger style `[AC-3.4]`
- [ ] 3.7 Verify: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox with 0 findings. No install or update runs are needed; if any are, use temp directories and never the Writ repo itself `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

- **Do not change escalate-once.** Only the emit and the sink sentences go. The re-run at anchor, "A passing story is never regenerated", the "returned file" rule, and both iteration sentences stay.
- **Where the dependency comes from.** Story 2 widens `test_harness_cuts.py`, which this story extends. The no-op greps over `commands/` also need Story 1, because two lean files carry the same line.
- **`ship.md` has no byte headroom.** It is 28,990 bytes, exactly 24,960 plus its recorded 4,030. "a merged PR" → "an open PR" saves one byte; keep every replacement the same length or shorter.
- **`/ship` still has a post-merge step.** Step 6 attaches audit notes after the PR merges on GitHub. The Overview may say so, but it must not say `/ship` merges.
- **Out of scope:** `.writ/docs/model-tiers.md:101,134,178` still describes the `escalated` signal; `claude-code/CLAUDE.md:20` still says "Branch to merged PR workflow". Both are reported to the orchestrator, not edited here.
- **Shared file with Story 4.** Story 4 edits `scripts/eval.sh` in `check_recommended_spec_implementation`. Touch only `check_model_escalation`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Remove the ADR-025 emit line, Reword ship.md]
- **Shadow paths:** [Guard grep]
- **Business rules:** [Rule 5 (escalate-once is unchanged), Rule 6 (byte budgets only go down), Rule 11 (every story leaves the tree green)]
- **Experience:** [State Catalog: Agent reads /create-spec Step 2.6a or /implement-story Gate 0, Agent or user reads /ship]
- **Technical:** technical-spec.md → ## Current State → ### ADR-025 and `/ship` inventory; ## Story 3 Design
