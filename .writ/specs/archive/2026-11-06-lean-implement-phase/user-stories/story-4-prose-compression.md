# Story 4: Compress implement-phase.md to 240 lines

> **Status:** Completed ✅ (2026-11-07)
> **Commit:** a3b04a510467223ccc334dcac497671049cc94b5
> **Priority:** Normal
> **Dependencies:** Story 3

## User Story

**As a** model reading `/implement-phase` at the start of a phase
**I want to** a command file that names each step and the script it calls, without re-explaining what the scripts enforce
**So that** the orchestrator spends its context on the phase, not on rationale

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4
> **Verified by:** AC-4.3 — `git diff b1feadc -- scripts/tests` changes one existing line (`KNOWN_OVER_BUDGET` implement-phase.md 10119 → 1465) and adds the new repro file; no existing assertion changed; recorded runs in `.writ/state/gate3-tests-story-4-prose-compression.txt` exit 0 (658 then 528 passed)
> **Verified by:** AC-4.4 — `.writ/docs/phase-execution-state-format.md` `## Why` has `### Why the phase branch is not under writ/phase/`, `### Why exhausting the iteration bound halts instead of quarantining`, `### Why one transient retry`, `### Why closure keeps the lane branch`; Gate 3 checked each against `scripts/phase-state.py`

- [x] Given Story 4 is complete, when `wc -l commands/implement-phase.md` runs, then it prints at most 240 `[AC-4.1]`
- [x] Given every `require_literal "$implement_phase"` line in `scripts/eval.sh`, when `eval.sh` runs, then each literal is still found and no check on `implement-phase.md` fails `[AC-4.2]`
- [x] Given the phase and exit-criteria tests, when they run after Story 4, then they pass with no assertion changed in this story `[AC-4.3]`
- [x] Given the rationale removed from `implement-phase.md` (halt versus quarantine, closure keeps the lane branch, phase-branch naming, retry bound), when `.writ/docs/phase-execution-state-format.md` is read, then each appears there under a "Why" subsection `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 List every pin on `implement-phase.md`: `grep -n 'require_literal "$implement_phase"' scripts/eval.sh` and `grep -rln implement-phase scripts/tests scripts/eval*.py`; record them in the story's Notes before editing `[AC-4.2, AC-4.3]`
- [x] 4.2 Move the rationale paragraphs from Steps 3.1, 3.2 and 3.3 into "Why" subsections of `.writ/docs/phase-execution-state-format.md` `[AC-4.4]`
- [x] 4.3 Replace Step 3.3 and the mid-run closure paragraph with an event → subcommand → effect table; reduce the Step 3.2 iteration bound and Step 3.1 phase-branch note to one line each `[AC-4.1, AC-4.2]`
- [x] 4.4 Merge the Initiative section, the inherited-answer rule and Step 4.3 into the one Question Policy section; cut Step 1.2b to the proposal shape, the Doubt Rule line, create-spec seeding and the close-spec line; shorten the Step 4.2 checker branches to one line each `[AC-4.1, AC-4.2]`
- [x] 4.5 Run `python3 scripts/gen-platform-trees.py`; replace the `commands/implement-phase.md` entry in `scripts/tests/test_governor_enforcement.py` with a dated entry for the smaller size `[AC-4.1, AC-4.3]`
- [x] 4.6 Verify acceptance criteria: `wc -l`, the phase and exit-criteria tests and `test_governor_enforcement.py` on Python 3.9, and `bash scripts/eval.sh --report=<scratch path>` (not while pytest runs) `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- **Business Rule 7:** this story moves and cuts text only. A test assertion edited here means behavior moved; flag it in review rather than editing it.
- **Pinned literals:** technical-spec.md → Pinned literals lists the strings known on 2026-11-06. Rebuild the list in task 4.1; Stories 1–3 may have changed it.
- **Compression targets:** technical-spec.md → Compression targets gives the per-section plan.
- **Unchanged (Business Rule 8):** verified-only merge, checker verdict governs, human criteria handed off, lane supervisor, quarantine and closure, terminal constraint. Each keeps at least one sentence in the command.
- **Pin list (task 4.1, rebuilt 2026-11-07 before editing; file 358 lines, 35079 bytes):**
  - `scripts/eval.sh` `require_literal "$implement_phase"` (lines 2213–3566): `Valid explicit \`Dependencies\` graph` · `inference remains advisory` · `stop before the confirmation gate` · `fresh subagent` · `writ/phase/{phase-id}/{spec-id}` · `phase-spec-result-v1` · `only a verified` · `User Challenge` · `ordinary failures use their normal` · `writ/quarantine/{spec-id}` · `one transient retry` · `skipped_blocked` · `does not guess or mutate git` · `evidence-bound` · `no qualifying candidate` · `production health` · `closed_not_implemented` · `Closed by decision` · `close-spec` · the c1–c4 criterion text (frontmatter). No `forbid_literal` on this file.
  - `scripts/eval.sh` `check_required_sections`: `## Overview`, `## Invocation`, `## Command Process`.
  - `scripts/eval-artifact-integrity.py`: `## Required Artifacts`.
  - `scripts/eval-command-structure.py` rows (`check_phase_lanes`): invocations `scripts/phase-state.py create-lane` and `scripts/phase-state.py validate-result`; `test_eval_command_structure.py` PhaseStateRowTests also needs `scripts/phase-state.py cmd_classify` in the frontmatter `calibrated_against`.
  - `scripts/eval-leanness.py` / `eval-loop-bounds.py` / `test_governor_mutation.py`: frontmatter `problem`, `outcome`, `exit_criteria`, `loop` (`max_iterations`, nested `spec_attempt`), and `## Completion`.
  - `test_exit_criteria.py`: c2 frontmatter line `  - "<c2 text>"`; slices `## Invocation`→`## Initiative` (`| \`/implement-phase --uat\` |`), `#### Step 3.2:`→`#### Step 3.2b:` (`when \`uatRequested\` is true, run \`/create-uat-plan {spec}\``), `#### Step 1.3:`→`### Phase 2:` (`**Phase state**` before `**Story statuses**`, the four terminal statuses in backticks, `` `uat-plan.md` never decides a skip ``, no `Existing \`uat-plan.md\``), `#### Step 4.2:`→`#### Step 4.3:` (`UAT: not requested`, `      /create-uat-plan 2026-07-07-`, `implement-phase.c2 — met — UAT not requested`), `#### Step 2.3:`→`### Phase 3:` (`UAT: not requested (pass --uat to generate plans per spec)`). So `## Initiative` and `#### Step 4.3:` headings must still exist.
  - `test_phase_state.py`: no `#### Step 1.4`, no `goal-emit.py`; `#### Step 4.1c:`→`#### Step 4.2:` health call in a fence with `--drift`, `--eval`, no `--verification`, and `never` in the step; `#### Step 3.2:`→`#### Step 3.2b:` has `(_lane-brief.md)`, `validate-result --input {result_path}`, a `**Supervise the result**`→`4. **` slice with `{result_path}` and no `report verbatim`, `result_missing`, `resume the same lane agent once`, `` `transient` ``, no `A truncated or dropped result`.
  - `test_product_check_direction.py`: `run /verify-spec --product`; in `#### Step 4.2`→`**The command never declares`, the line after `Phase status:` is `Product docs may lag what shipped — run /verify-spec --product.`, and `appears only when \`.writ/product/\` exists`.
  - `test_eval_shipped_refs.py`: the `](_lane-brief.md)` link (the generated plugin copy must carry `${CLAUDE_PLUGIN_ROOT}/commands/_lane-brief.md`).
  - `test_goal_emit_command_hooks.sh`: no `goal-emit.py`.
  - `test_governor_enforcement.py`: `KNOWN_OVER_BUDGET` must equal the over-budget set exactly.
  - External step references to keep: Step 2.1 (`implement-spec.md`), Step 3.2 (`_lane-brief.md`, `supervisor-agent.md`), Step 4.1 (`exit-criteria.py`, `exit-criteria-classification.md`).
- **Test runs:** run pytest alone. Run `eval.sh` before or after pytest, not during. Full suites (3.9 and 3.14, bash, eval) run once at spec end.

## Context for Agents

- **Error map rows:** [Compression (Story 4)] — from technical-spec.md error map
- **Shadow paths:** []
- **Business rules:** [7, 8] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** []

## What Was Built

**Implementation Date:** 2026-11-07

### Files Created

- **`scripts/tests/test_story4_reconcile_stop_repro.py`** (Gate 3 evidence repro, committed unchanged: the `--resume` row keeps "continue only when they agree")

### Files Modified

- **`commands/implement-phase.md`** (358 → 236 lines; 35079 → 26425 bytes; non-blank lines 234 → 186; words 4904 → 3628)
  - Step 1.2b: proposal shape, Doubt Rule line, `/create-spec` seeding, `close-spec` line
  - Step 3.1 phase-branch note and Step 3.2 iteration bound: one line each (`record-halt`)
  - Step 3.3 and mid-run closure: Event → Subcommand → Effect table
  - Initiative, Question Policy, inherited-answer rule and old Step 4.3: one `## Initiative and Question Policy` section; Step 4.3 now holds the checker branches, one line each
  - Integration table and Completion shortened
- **`.writ/docs/phase-execution-state-format.md`** (new `## Why`: phase-branch naming, halt vs quarantine, one transient retry, closure keeps the lane branch, plus lane scope, checker verdict, closed-spec reporting)
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET` for `implement-phase.md` 10119 → 1465, dated)
- **`cursor/plugin/commands/implement-phase.md`, `plugins/writ/commands/implement-phase.md`** (generated)

### Implementation Decisions

1. **Headings kept as test anchors** — `## Initiative and Question Policy` keeps the `## Initiative` prefix and `#### Step 4.3:` survives as "Terminal Status", because existing test slices end at those headings and no assertion may change.
2. **All rationale in one `## Why` section** of the state-format doc, one subsection per mechanism.
3. **Overview says "never merges the phase branch"** — the loop merges lanes into the phase branch, so the old "never merges" could only mean the phase branch onward.

### Test Results

**Verification:** Automated

- ✅ Round 1 recorded run (Python 3.9): 658 passed across 15 files; goal-emit hook test PASS; coder's full `eval.sh`: 0 findings, 71 checks
- ✅ Round 2 recorded run: 528 passed across 10 files, including the repro; reviewer's full `eval.sh` on the round-2 tree: 0 findings; reviewer re-ran 6 more files: 131 passed
- ✅ `gen-platform-trees.py --check`: pass
- No existing test assertion changed: `git diff -- scripts/tests` is the `KNOWN_OVER_BUDGET` value plus the new repro

**Coverage:** N/A — `test-integrity.py coverage` unverifiable (no coverage report in this repo)

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (round 1 FAIL: F1 Major, the `--resume` stop "continues only if they agree" was cut; F2 Minor, the inherited-answer rule contradicted `_lane-brief.md`. Post-review's evidence gate overrode the FAIL to PASS (row 9, repro unconfirmed); the orchestrator recoded anyway because the reviewer showed the repro fails on round 1 and passes on the old file)
- **Gate 3 route:** `review-agent` (cross-component; 2 boundary crossings, both generated copies)
- **Drift:** Medium (DEV-009 ⚠️ blank lines; DEV-010 ⚠️ resolved in round 2)
- **Security:** Clean
- **Safety fact:** measured `tested` (claimed `tested`)
- **Real size of the cut:** −48 non-blank lines, −26% words, −24.7% bytes; 74 of the 122 lines removed are blank lines (DEV-009)

### Deviations from Spec

See `drift-log.md` Story 4: DEV-009, DEV-010 (Medium, logged).

### Lessons Learned

1. **A line-count target invites removing blank lines** — a byte or word target measures context cost; the spec's 240-line target was met with 74 blank lines doing most of the work.
2. **An evidence-gate override is not a verdict on the finding** — row 9 passed a real lost stop because the repro ran outside the repo; the reviewer's before/after run was the evidence.

### Next Story

None — last story in the spec.
