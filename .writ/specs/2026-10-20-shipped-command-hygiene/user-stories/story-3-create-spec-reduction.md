# Story 3: `create-spec.md` Reduction Pass

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** developer who runs `/create-spec`
**I want to** load a `create-spec.md` that keeps every step, gate, and rule but drops interview coaching, worked examples, and Writ's own history
**So that** the command says what to do without telling a current model how to hold a conversation, and its recorded overage falls instead of being repinned upward

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given the lean twin from `git show 617037b:commands/create-spec.lean.md` and `commands/create-spec.md` at Story 3 start, when `cut-log.md` is written, then every lean-twin change appears as a row marked adopted (class `coaching`) or declined (constraint, behavior, test-pinned text, or addition) with a one-line reason, and no reason cites bytes `[AC-3.1]`
- [x] Given the reduced file, when `bash scripts/eval.sh` and the bash tests run, then every Story 2 `keep` row and `command-structure` row that targets `create-spec.md` passes, `scripts/tests/test_jev_setup_hooks.sh` and `scripts/tests/test_spec_analyze_command_hooks.sh` pass, and `shipped-refs` still passes `[AC-3.2]`
- [x] Given `create-spec.md` before and after, when the frontmatter, the `#### Step` headings, the AskQuestion blocks, and the `scripts/*.py` invocations are compared, then the frontmatter (including the three `exit_criteria` lines) is byte-identical, every step number that remains keeps its number, every AskQuestion block and every script invocation is still present, and any removed heading is listed in `cut-log.md` `[AC-3.3]`
- [x] Given the reduced file, when its bytes are measured, then they are lower than at Story 3 start; `KNOWN_OVER_BUDGET["commands/create-spec.md"]` in `scripts/tests/test_governor_enforcement.py` equals the new overage exactly and is below both its value at Story 3 start and 29,304; and its dated comment names the coaching that was cut, not a byte goal `[AC-3.4]`
- [x] Given `git diff <start> -- commands/create-spec.md`, when a reviewer maps it against `cut-log.md`, then every hunk matches an adopted row, and `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` all pass with 0 findings `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write the failing guard first in `scripts/tests/test_governor_enforcement.py`: a test that fails while `KNOWN_OVER_BUDGET["commands/create-spec.md"]` is not below 29,304; run it and see it fail `[AC-3.4]`
- [x] 3.2 Re-measure the start state: record the commit, `wc -c commands/create-spec.md`, the recorded overage, the `#### Step` headings, the AskQuestion titles, and the `scripts/*.py` invocations; list every Story 2 `keep` and `command-structure` row that targets `create-spec.md` `[AC-3.2, AC-3.3]`
- [x] 3.3 Recover the lean twin, diff it against the current file, and write `cut-log.md` (format: technical-spec.md → Cut log format) from technical-spec.md → Candidate cuts from the lean twin, re-deciding each row against the post-dependency text and declining any cut that touches a Step 3.2 item `[AC-3.1]`
- [x] 3.4 Apply the adopted cuts in groups (discovery coaching, Phase 2 compression, Example Usage, history and internal labels), one commit per group, running `bash scripts/eval.sh` and the two Jev and spec-analyze bash tests after each `[AC-3.2, AC-3.3, AC-3.5]`
- [x] 3.5 Repin `KNOWN_OVER_BUDGET["commands/create-spec.md"]` to the exact new overage (`wc -c` minus 24,960) with a dated comment naming the coaching removed; confirm the guard from 3.1 now passes `[AC-3.4]`
- [x] 3.6 Verify the cut against its log: compare the Step 3.2 lists before and after, map every `git diff <start>` hunk to a `cut-log.md` row, and fill in the log's end bytes and overage `[AC-3.1, AC-3.3, AC-3.5]`
- [x] 3.7 Verify the suites: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-3.2, AC-3.5]`

## Notes

- **The lean twin is a candidate list, not evidence.** The flagged-harness-cuts null result ran `/implement-story`, never `/create-spec` (spec.md → Grounding Notes). Judge each cut by class.
- **Decline everything behavioral the twin dropped.** The Jev sub-steps in Step 2.6c, the item 3 exception clause, the `jev:` note in Step 2.9, and "any relevant phase/source metadata" in Step 2.4 stay. The twin's added "Production boundary" line is an addition; leave it out.
- **The twin's wording is not always safe to copy.** It rewrites the pinned iteration sentence in Step 2.6a ("— there is no second regeneration" → "; …"). Keep pinned sentences as they are unless Story 2 removed the pin.
- **Bytes are a drift signal (ADR-023).** Expect several KB of coaching to go. Do not cut a constraint to reach a number, and do not stop short of a coaching cut because the number already fell.
- **Dependencies changed this file first.** `2026-10-20-harness-cuts` removed the ADR-025 escalation line from Step 2.6a, `2026-10-20-platform-neutral-names` renamed `/design` in Step 1.5 and may have renamed tool names, and Story 1 removed the ADR-013 link. Work from the current file and the current recorded overage, not the snapshot.
- **Technical spec:** `sub-specs/technical-spec.md` → Current State → Create-spec size, and → Story 3: Create-Spec Reduction (candidate cut table, what the cuts must not touch, cut log format, repin).
- **Step numbers stay.** Other files and tests cite `Step 2.6a`, `2.6b`, `2.6c`. A removed step leaves a gap; do not renumber.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Cut `create-spec.md`, Repin]
- **Shadow paths:** []
- **Business rules:** [Cuts remove coaching only, Repin downward]
- **Experience:** [State Catalog]

---

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

1. **`.writ/specs/2026-10-20-shipped-command-hygiene/cut-log.md`** (126 lines)
   - Header: Start `37e097e`, 53,612 bytes, overage 28,652 · End 38,562 bytes, overage 13,602. A Start state section (29 step headings, 4 AskQuestion prompts, 7 script calls, 17 keep pins, 4 structural rows, other readers of the file). 54 Adopted rows (all `coaching`), 19 Declined rows, and a Hunk map tying each of the 22 hunks of `git diff 37e097e 5536b31 -- commands/create-spec.md` to adopted rows.

### Files Modified

- **`commands/create-spec.md`** (discovery, Phase 2, Example Usage)
  - Removed interview coaching (Topic Areas questions, pushback phrasing, transition phrases, Plan Mode benefits), rationale and duplicated framing, Writ history and internal labels, Step 2.1 Initialize Tracking, and the Example Usage dialogue. Step 1.2 and Step 2.1 are numbering gaps; nothing was renumbered.
  - Unchanged: frontmatter, the three AskQuestion blocks and the Jev prompt, all seven script calls, the `--recommend` section and matrix, the Completion section, the Step 2.6c Jev sub-steps and item 3 exception, the Step 2.9 `jev:` note, "any relevant phase/source metadata", and the pinned Step 2.6a iteration sentence.
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`; Story 3 section)
  - `KNOWN_OVER_BUDGET["commands/create-spec.md"]`: 28652 → 13602, with a dated comment naming the coaching cut.
  - `CreateSpecRepinTests`, `CreateSpecCutLogTests`, `CreateSpecBeforeAfterTests` (9 tests).

### Implementation Decisions

1. **Each lean-twin change judged by class** — the twin is a candidate list; 19 of its changes were declined (behavior, constraint, test-pinned text, additions, and pure rewordings).
2. **Cuts in four groups, one commit each** — discovery coaching (`27ffa38`), history and internal labels (`e52309e`), Phase 2 compression (`cb59701`), Example Usage (`ef91755`); each commit repinned and green.
3. **Before/after tests read the story's own commits** — invariants are checked between `git show 37e097e:` and `git show 5536b31:` and skip without full history, so later wording edits to the live file need no test change.
4. **Guard checks both bounds** — the recorded value must be below 29,304 and below the Story 3 start value 28,652 (DEV-009).

### Test Results

**Verification:** Automated, test-first (the guard failed at 28652 before any cut).
**Coverage:** N/A (no new source module; markdown and tests only).

- ✅ Orchestrator targeted runs: `test_governor_enforcement.py`, `test_harness_cuts.py`, `test_eval_command_structure.py` → 135 passed (iteration 1); `test_governor_enforcement.py`, `test_harness_cuts.py` → 100 passed (iteration 2). `test_jev_setup_hooks.sh` and `test_spec_analyze_command_hooks.sh` PASS.
- ✅ Full pytest (3.9): 2774 passed, 2 skipped (evaluator run on HEAD).
- ✅ Bash tests: 45/45.
- ✅ `bash scripts/eval.sh`: Findings 0, `shipped-refs` 5/5, `command-structure` 33/33; metrics show `commands/create-spec.md +13602`.
- ✅ `ac-trace.py check` on this spec: no findings.
- ✅ Evaluator mutations: a one-word edit plus dated repin and same-byte heading and description rewordings fail no test; drift between the story's commits is caught; missing history skips.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small (DEV-007, DEV-008, DEV-009)
- **Security:** Clean
- **Boundary Compliance:** Gate 2.5 found 0 crossings; `commands/create-spec.md` is named in technical-spec.md → Files in Scope for Story 3.
- gate3-route: evaluator-agent. review-panel: not convened (Gate 3 ran evaluator-agent without `--panel`). arch-lint: none — see .writ/docs/architecture-lint.md.
- Iteration 1 FAIL (Major, architecture): the new tests compared the live file and the live ledger entry against constants frozen at Story 3 start, so the next wording edit would fail them; and the cut had copied two twin edits that changed discovery actions ("ask clarifying questions", "dependencies"). Fixed in `5536b31` and `8a007d1`.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured. Gate 3 review-override: pass (no blocking helper finding). Gate 3.5 drift-format: pass. Gate 4 authenticity: pass. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Hunk audit: all 22 hunks coaching only; every explicit decline in the technical spec kept.

### Deviations from Spec

- **[DEV-007] Fifth declined class `wording` in the cut log** — Severity: Small
  - Spec said: four declined classes.
  - Reality: row 70 uses `wording` for pure twin rewordings.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md business rule added.
- **[DEV-008] The cut is larger than the technical spec's estimate** — Severity: Small
  - Spec said: roughly 8 to 12 KB, an expectation.
  - Reality: 53,612 → 38,562; no instruction lost per the hunk audit.
  - Resolution: Auto-amended
- **[DEV-009] The Task 3.1 guard also requires a value below the Story 3 start** — Severity: Small
  - Spec said: guard on 29,304.
  - Reality: guard on 29,304 and 28,652.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md Files in Scope S3 line updated.
