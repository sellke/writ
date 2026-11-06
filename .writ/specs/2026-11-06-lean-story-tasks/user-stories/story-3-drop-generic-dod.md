# Story 3: Drop the generic Definition of Done

> **Status:** Completed ✅ (2026-11-06)
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** spec author and a developer running `/verify-spec`
**I want to** new stories to omit a generic Definition of Done, and `/verify-spec` to check only the Definition of Done a story has
**So that** generated stories carry less boilerplate, and legacy stories with a Definition of Done are still checked

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given the story template in `agents/user-story-generator.md`, when a story file is generated from it, then the file contains no `## Definition of Done` section `[AC-3.1]`
- [x] Given the story-contents sentence in `commands/create-spec.md` Step 2.6, when it is read, then it names no definition of done `[AC-3.2]`
- [x] Given a story with no `## Definition of Done` section, when `/verify-spec` runs Check 1d, then it reports no finding for that story `[AC-3.3]`
- [x] Given a Completed story whose Definition of Done has unchecked items, when `/verify-spec` runs Check 3b, then it still reports the WARN; given a story with no Definition of Done, Check 3b reports nothing for it `[AC-3.4]`
- [x] Given a change that grows `commands/create-spec.md` or `commands/verify-spec.md` in bytes, when the story is complete, then `KNOWN_OVER_BUDGET` in `scripts/tests/test_governor_enforcement.py` has a dated entry for that file `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write tests in `scripts/tests/` that pin the new wording of `agents/user-story-generator.md`, `commands/create-spec.md` Step 2.6, and `commands/verify-spec.md` Checks 1d and 3b. Tests fail before the edits. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.2 Remove the `## Definition of Done` block from the Prompt Template in `agents/user-story-generator.md`. Leave the other template sections unchanged. `[AC-3.1]`
- [x] 3.3 In `commands/create-spec.md` Step 2.6, drop the definition of done from the story-contents sentence. Leave the rest of the sentence and the criterion ID grammar paragraph unchanged. `[AC-3.2]`
- [x] 3.4 In `commands/verify-spec.md`, remove Definition of Done from the Check 1d required sections. Change Check 3b so it runs only when the story has a Definition of Done section. `[AC-3.3, AC-3.4]`
- [x] 3.5 Regenerate the platform copies with `python3 scripts/gen-platform-trees.py`, including `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**`. Do not hand-edit them. `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.6 Add a dated `KNOWN_OVER_BUDGET` entry in `scripts/tests/test_governor_enforcement.py` for each of `create-spec.md` and `verify-spec.md` that grows in bytes. Net-zero changes need no entry. `[AC-3.5]`
- [x] 3.7 Run pytest alone under Python 3.9 and 3.14, then `bash scripts/eval.sh` and `python3 scripts/gen-platform-trees.py --check`. Confirm each criterion. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

- This story keeps its own Definition of Done. Business Rule 5 applies to stories generated after this one ships.
- Cross-spec overlap: `2026-11-06-archived-dependencies-resolve` also edits `commands/verify-spec.md` (Check 3f) and its byte-budget ledger line. Whichever spec lands second rebases the ledger number.
- Stories 2, 3, and 4 all edit `agents/user-story-generator.md` and `commands/create-spec.md`. Apply them in order.
- Generated trees are outputs of `scripts/gen-platform-trees.py`. A hand edit is overwritten on the next run and fails `--check`.
- Legacy stories keep their Definition of Done. Do not edit them. `/revert` step 1 still unchecks Definition of Done items on those stories.
- Run pytest alone. `eval.sh`, the bash tests, and `git worktree` changes in the same checkout break `test_smoke_leaves_repo_unchanged` and the `app-verify` tests.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`/verify-spec` 1d, `/verify-spec` 3b] — from technical-spec.md → ## Error & Rescue Map
- **Business rules:** [Rule 5 (new stories have no Definition of Done; legacy stories untouched)] — from spec.md → ## 📋 Business Rules (Expanded)
- **Experience:** [State Catalog rows "Legacy story with DoD" and "New story with no DoD"] — from spec.md → ## 🎯 Experience Design → ### State Catalog

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

None.

### Files Modified

- **`agents/user-story-generator.md`** (Prompt Template)
  - `## Definition of Done` block removed; Notes and Context for Agents unchanged
- **`commands/create-spec.md`** (Step 2.6, `--from-prototype` Step 3)
  - Story-contents sentence names no definition of done
  - `--from-prototype` Story 1 has its Implementation Tasks checked; no DoD mention
  - 39129 -> 39081 bytes
- **`commands/verify-spec.md`** (Checks 1d, 3b, Phase 5 report example)
  - 1d requires User Story, Acceptance Criteria, Implementation Tasks
  - 3b runs only on a Completed story that has a DoD; no DoD gives no finding; WARN-1 kept
  - Report example row 2 shows `—` for DoD; 35778 bytes, unchanged
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`)
  - create-spec.md entry 14169 -> 14121 with a dated line
- **`scripts/tests/test_harness_cuts.py`** (`NoGenericDefinitionOfDoneTest`)
  - 6 tests for AC-3.1..AC-3.5; Story 2's DoD guard test removed as planned
- **Generated copies** (`claude-code/agents/writ-story-gen.md`, `codex/agents/user-story-generator.toml`, `cursor/plugin/**`, `plugins/writ/**`; 8 files)
  - Regenerated with `scripts/gen-platform-trees.py`
- **`spec-lite.md`** — Small-drift auto-amendment (DEV-003, DEV-004)

### Implementation Decisions

1. **Remove the `--from-prototype` DoD mention instead of making it conditional** — a conditional would invite the generator to add one back.
2. **Shrink and re-pin the ledger** — `total_overage` is asserted exactly, so a smaller file needs a smaller entry.
3. **Leave `commands/revert.md` alone** — it unchecks DoD items only where they exist.

### Test Results

**Verification:** Automated

- ✅ Targeted (7 files): 478 passed, 1 skipped on Python 3.9 and 3.14
- ✅ Full suite: 4250 passed, 2 skipped on Python 3.9 and on 3.14
- ✅ `bash scripts/eval.sh`: exit 0
- ✅ `gen-platform-trees.py --check`: pass

**Coverage:** N/A (prose and test-only change)

### Review Outcome

**Result:** PASS with drift note

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** All changes in owned files; crossings are generated copies
- **Safety fact:** measured `tested` (claimed `tested`)

### Deviations from Spec

- **[DEV-003] `--from-prototype` Step 3 no longer names a Definition of Done** — Severity: Small
  - Spec said: create-spec Steps 2.4, 2.6, 2.6a, 2.8, Completion
  - Reality: `--from-prototype` Step 3 also edited
  - Resolution: auto-amended
  - Spec amendment: spec-lite.md → Files in Scope
- **[DEV-004] `/verify-spec` report example shows "—" for a story with no DoD** — Severity: Small
  - Spec said: verify-spec Checks 1d and 3b
  - Reality: Phase 5 report example cell changed, byte-neutral
  - Resolution: auto-amended
  - Spec amendment: spec-lite.md → Files in Scope

### Lessons Learned

1. **Legacy DoD items stay unchecked after `/implement-story`** — Step 4 checks tasks and AC only, so legacy stories with a DoD still draw WARN-1. Out of scope here.

### Next Story

**Story 4:** State each business rule once — also fix `.writ/docs/context-hint-format.md:18` and `:274`, which place Context for Agents "after the Definition of Done".
