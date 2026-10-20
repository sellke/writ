# Story 3: `create-spec.md` Reduction Pass

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** developer who runs `/create-spec`
**I want to** load a `create-spec.md` that keeps every step, gate, and rule but drops interview coaching, worked examples, and Writ's own history
**So that** the command says what to do without telling a current model how to hold a conversation, and its recorded overage falls instead of being repinned upward

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given the lean twin from `git show 617037b:commands/create-spec.lean.md` and `commands/create-spec.md` at Story 3 start, when `cut-log.md` is written, then every lean-twin change appears as a row marked adopted (class `coaching`) or declined (constraint, behavior, test-pinned text, or addition) with a one-line reason, and no reason cites bytes `[AC-3.1]`
- [ ] Given the reduced file, when `bash scripts/eval.sh` and the bash tests run, then every Story 2 `keep` row and `command-structure` row that targets `create-spec.md` passes, `scripts/tests/test_jev_setup_hooks.sh` and `scripts/tests/test_spec_analyze_command_hooks.sh` pass, and `shipped-refs` still passes `[AC-3.2]`
- [ ] Given `create-spec.md` before and after, when the frontmatter, the `#### Step` headings, the AskQuestion blocks, and the `scripts/*.py` invocations are compared, then the frontmatter (including the three `exit_criteria` lines) is byte-identical, every step number that remains keeps its number, every AskQuestion block and every script invocation is still present, and any removed heading is listed in `cut-log.md` `[AC-3.3]`
- [ ] Given the reduced file, when its bytes are measured, then they are lower than at Story 3 start; `KNOWN_OVER_BUDGET["commands/create-spec.md"]` in `scripts/tests/test_governor_enforcement.py` equals the new overage exactly and is below both its value at Story 3 start and 29,304; and its dated comment names the coaching that was cut, not a byte goal `[AC-3.4]`
- [ ] Given `git diff <start> -- commands/create-spec.md`, when a reviewer maps it against `cut-log.md`, then every hunk matches an adopted row, and `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` all pass with 0 findings `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write the failing guard first in `scripts/tests/test_governor_enforcement.py`: a test that fails while `KNOWN_OVER_BUDGET["commands/create-spec.md"]` is not below 29,304; run it and see it fail `[AC-3.4]`
- [ ] 3.2 Re-measure the start state: record the commit, `wc -c commands/create-spec.md`, the recorded overage, the `#### Step` headings, the AskQuestion titles, and the `scripts/*.py` invocations; list every Story 2 `keep` and `command-structure` row that targets `create-spec.md` `[AC-3.2, AC-3.3]`
- [ ] 3.3 Recover the lean twin, diff it against the current file, and write `cut-log.md` (format: technical-spec.md → Cut log format) from technical-spec.md → Candidate cuts from the lean twin, re-deciding each row against the post-dependency text and declining any cut that touches a Step 3.2 item `[AC-3.1]`
- [ ] 3.4 Apply the adopted cuts in groups (discovery coaching, Phase 2 compression, Example Usage, history and internal labels), one commit per group, running `bash scripts/eval.sh` and the two Jev and spec-analyze bash tests after each `[AC-3.2, AC-3.3, AC-3.5]`
- [ ] 3.5 Repin `KNOWN_OVER_BUDGET["commands/create-spec.md"]` to the exact new overage (`wc -c` minus 24,960) with a dated comment naming the coaching removed; confirm the guard from 3.1 now passes `[AC-3.4]`
- [ ] 3.6 Verify the cut against its log: compare the Step 3.2 lists before and after, map every `git diff <start>` hunk to a `cut-log.md` row, and fill in the log's end bytes and overage `[AC-3.1, AC-3.3, AC-3.5]`
- [ ] 3.7 Verify the suites: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-3.2, AC-3.5]`

## Notes

- **The lean twin is a candidate list, not evidence.** The flagged-harness-cuts null result ran `/implement-story`, never `/create-spec` (spec.md → Grounding Notes). Judge each cut by class.
- **Decline everything behavioral the twin dropped.** The Jev sub-steps in Step 2.6c, the item 3 exception clause, the `jev:` note in Step 2.9, and "any relevant phase/source metadata" in Step 2.4 stay. The twin's added "Production boundary" line is an addition; leave it out.
- **The twin's wording is not always safe to copy.** It rewrites the pinned iteration sentence in Step 2.6a ("— there is no second regeneration" → "; …"). Keep pinned sentences as they are unless Story 2 removed the pin.
- **Bytes are a drift signal (ADR-023).** Expect several KB of coaching to go. Do not cut a constraint to reach a number, and do not stop short of a coaching cut because the number already fell.
- **Dependencies changed this file first.** `2026-10-20-harness-cuts` removed the ADR-025 escalation line from Step 2.6a, `2026-10-20-platform-neutral-names` renamed `/design` in Step 1.5 and may have renamed tool names, and Story 1 removed the ADR-013 link. Work from the current file and the current recorded overage, not the snapshot.
- **Technical spec:** `sub-specs/technical-spec.md` → Current State → Create-spec size, and → Story 3: Create-Spec Reduction (candidate cut table, what the cuts must not touch, cut log format, repin).
- **Step numbers stay.** Other files and tests cite `Step 2.6a`, `2.6b`, `2.6c`. A removed step leaves a gap; do not renumber.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Cut `create-spec.md`, Repin]
- **Shadow paths:** []
- **Business rules:** [Cuts remove coaching only, Repin downward]
- **Experience:** [State Catalog]
