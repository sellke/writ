# Story 2: Lean task rules in the story generator and Step 2.6a

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** spec author running `/create-spec`, and the coding agent that later reads the stories
**I want to** get stories whose tasks name files and external contracts, stay under 50 words each, and fail generation when they do not
**So that** stories read in less space, a mechanical check catches long tasks, and the coding agent decides internal structure

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [x] Given the updated `agents/user-story-generator.md` task rules, when a story is generated, then each task names every file it creates or changes and any external contract it fixes, and no task prescribes internal function names, signatures, or step order `[AC-2.1]`
- [x] Given the updated task rules, when they are read, then they cap each task at 50 words, excluding the task number and AC tag, and direct gotchas and constraints to Notes `[AC-2.2]`
- [x] Given a generated story with a task over 50 words, when Step 2.6a runs, then the story counts as failing and is regenerated once at `anchor`, and a second failure lists its over-long task numbers and word counts in Step 2.9 `[AC-2.3]`
- [x] Given the changes are complete, when `python3 scripts/gen-platform-trees.py --check` runs, then it reports `pass`, and the byte change to `commands/create-spec.md` is zero or recorded in `KNOWN_OVER_BUDGET` `[AC-2.4]`

## Implementation Tasks

- [x] 2.1 Write tests in `scripts/tests/test_harness_cuts.py` that pin the new generator task rules and the Step 2.6a `oversized_task` clause. Run them and confirm they fail before the edits `[AC-2.2, AC-2.3]`
- [x] 2.2 Edit the Implementation Tasks rules and quality guideline in `agents/user-story-generator.md`: name files and external contracts only, a 50-word cap, gotchas in Notes. Cite Business Rules 1, 2, 3, and 6 by number `[AC-2.1, AC-2.2]`
- [x] 2.3 Edit Step 2.6a item 2 in `commands/create-spec.md` so any `oversized_task` finding fails its story. Item 3 regenerates once at `anchor`. Step 2.9 lists a second failure's task numbers and word counts `[AC-2.3]`
- [x] 2.4 Regenerate the platform copies with `python3 scripts/gen-platform-trees.py`, which rewrites `claude-code/agents/writ-story-gen.md` and the `cursor/plugin/` copies `[AC-2.4]`
- [x] 2.5 Keep `commands/create-spec.md` net-zero in bytes, or record its new overage in `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` with a dated comment `[AC-2.4]`
- [x] 2.6 Verify: run `uv run --isolated --python 3.9 --with pytest pytest`, then the 3.14 variant, each alone. Then run `bash scripts/eval.sh` and `python3 scripts/gen-platform-trees.py --check` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **Depends on Story 1.** `ac-trace.py check` must emit `oversized_task` before Step 2.6a can use it. This story cites that finding and does not implement it. Count words the way `technical-spec.md` → `## oversized_task finding` specifies.
- **Byte budget.** `commands/create-spec.md` is already over its command budget. `scripts/tests/test_governor_enforcement.py` fails if the overage grows past the recorded value, and it pins that entry to the exact overage. Target net-zero bytes.
- **Generated trees.** `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**` come from `scripts/gen-platform-trees.py`. Do not hand-edit them.
- **Run pytest alone.** `eval.sh` and the bash tests write under `.writ/state/`. Running them in the same checkout as pytest breaks `test_smoke_leaves_repo_unchanged` and the `app-verify` tests.
- **Python 3.9 floor.** Test code must run on Python 3.9 (`pyproject.toml`). Do not rely on 3.10+ stdlib behavior.
- **Keep the Definition of Done** in the generator template for this story. Story 3 removes it.
- **Step 2.6a item 3 is unchanged in shape.** One regeneration at `anchor`, no loop. A passing story is never regenerated.
- **Step 2.9 is outside the spec's Scope Boundaries list.** The Step 2.6a change needs its second-failure line, so this story edits it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Step 2.6a regenerate] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [Happy: all tasks ≤50 words] — technical-spec.md → ## Shadow Paths
- **Business rules:** [Business Rule 1, Business Rule 2, Business Rule 3, Business Rule 6] — spec.md → ## Specification Contract → Business Rules
- **Experience:** [State "A task over 50 words, first attempt", State "A task over 50 words after retry"] — spec.md → ## 🎯 Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Step 2.6a change; spec.md → ## Detailed Requirements

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

None.

### Files Modified

- **`agents/user-story-generator.md`** (Rules for tasks, quality guideline, Notes "Include", exit criterion)
  - Tasks name every file they create or change and any external contract they fix; no internal function names, signatures, or step order
  - At most 50 words per task, not counting the task number and AC tag; Step 2.6a regenerates a longer one
  - Probed facts, gotchas, and environment constraints go in Notes
  - Definition of Done kept (Story 3 removes it)
- **`commands/create-spec.md`** (Step 2.6a items 1–2, iteration paragraph, Step 2.9)
  - Item 2: any `oversized_task` finding fails its story
  - Step 2.9: lists each story still failing and each `oversized_task` as `story=N task N.M words=W`
  - Offsets keep the file at 39129 bytes; `KNOWN_OVER_BUDGET` unchanged
- **`scripts/tests/test_harness_cuts.py`** (`LeanTaskRulesTest`, `Step26aOversizedTaskTest`)
  - 9 tests pinning the generator rules, the Step 2.6a clause, the Step 2.9 line, and the generated copies
- **Generated copies** (`claude-code/agents/writ-story-gen.md`, `codex/agents/user-story-generator.toml`, `cursor/plugin/agents/user-story-generator.md`, `cursor/plugin/commands/create-spec.md`, `plugins/writ/agents/user-story-generator.md`, `plugins/writ/agents/writ-story-gen.md`, `plugins/writ/commands/create-spec.md`)
  - Regenerated with `scripts/gen-platform-trees.py`
- **`spec-lite.md`** — Small-drift auto-amendment (DEV-001, DEV-002)

### Implementation Decisions

1. **State rule content, not rule numbers** — shipped prose cannot cite this spec's numbering (DEV-001).
2. **Offset by trimming text no consumer reads** — net-zero bytes instead of a ledger increase (DEV-002).

### Test Results

**Verification:** Automated

- ✅ Targeted (6 test files): 398 passed on Python 3.9 and 3.14
- ✅ Full suite: 4245 passed, 2 skipped on Python 3.9 and on 3.14
- ✅ `bash scripts/eval.sh`: exit 0
- ✅ `gen-platform-trees.py --check`: pass
- ⚠️ AC-2.1 is shown by pinned rule text only; generation behavior is checked by Story 5's trial

**Coverage:** N/A (prose and test-only change)

### Review Outcome

**Result:** PASS with drift note

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** All changes in owned files; codex and plugins copies are generator output
- **Safety fact:** measured `tested` (claimed `tested`)

### Deviations from Spec

- **[DEV-001] Generator states the rule content instead of citing Business Rules 1, 2, 3, 6 by number** — Severity: Small
  - Spec said: task 2.2 "Cite Business Rules 1, 2, 3, and 6 by number"
  - Reality: the shipped generator states the content
  - Resolution: auto-amended
  - Spec amendment: spec-lite.md → For Coding Agents → Implementation Approach
- **[DEV-002] Byte-offset trims in Step 2.6a item 1, the iteration paragraph, and Step 2.9** — Severity: Small
  - Spec said: net-zero bytes, no sentences named
  - Reality: three trims of text no consumer reads
  - Resolution: auto-amended
  - Spec amendment: spec-lite.md → For Coding Agents → Implementation Approach

### Lessons Learned

1. **Task 2.2's "cite by number" was itself over-prescriptive** — the kind of task wording this spec targets.

### Next Story

**Story 3:** Drop the generic Definition of Done — must delete or invert `test_ac_2_2_template_keeps_its_definition_of_done`.
