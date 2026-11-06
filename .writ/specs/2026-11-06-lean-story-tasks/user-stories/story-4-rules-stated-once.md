# Story 4: State each business rule once

> **Status:** Completed ✅ (2026-11-06)
> **Commit:** 66c4bebe665bb7f06c7c73f8c294d266c9096734
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** spec author
**I want to** cite spec Business Rule 4 by number from every spec and story document instead of copying it
**So that** the coding agent never has to choose between two versions of one rule (see `spec.md` → `## Evidence`, DEV-001)

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given the business-rules bullet in `commands/create-spec.md` Step 2.4, when Step 2.4 is read, then it adds detail per Business Rule number and does not restate contract rule text `[AC-4.1]`
- [x] Given `commands/create-spec.md` Step 2.8, the business-rule hint in `agents/user-story-generator.md`, and `.writ/docs/context-hint-format.md`, when each is read, then each cites rules as `Business Rule N` and none restates rule text `[AC-4.2]`
- [x] Given the generator's task rules, when a task cites a Business Rule, then the rules allow the task to cite the number and forbid paraphrasing the rule `[AC-4.3]`
- [x] Given the edited `commands/create-spec.md`, when `scripts/tests/test_governor_enforcement.py` runs, then the file is net-zero bytes or a dated `KNOWN_OVER_BUDGET` entry covers its growth `[AC-4.4]`
- [x] Given the finished change, when verification runs, then pytest passes on Python 3.9 and 3.14, `bash scripts/eval.sh` passes, and `python3 scripts/gen-platform-trees.py --check` reports no drift `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write tests in `scripts/tests/test_rule_citations.py` pinning rule-number citations in `commands/create-spec.md` Steps 2.4 and 2.8, `agents/user-story-generator.md`, and `.writ/docs/context-hint-format.md` `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.2 Update `commands/create-spec.md` Step 2.4 business-rules bullet and Step 2.8 to cite Business Rule numbers instead of restating rule text `[AC-4.1, AC-4.2]`
- [x] 4.3 Update `agents/user-story-generator.md` task rules to forbid paraphrasing a Business Rule, and its Context for Agents business-rule hint to cite numbers `[AC-4.2, AC-4.3]`
- [x] 4.4 Update `.writ/docs/context-hint-format.md` business-rule format and example to use `Business Rule N` citations `[AC-4.2]`
- [x] 4.5 Add a dated `KNOWN_OVER_BUDGET` entry in `scripts/tests/test_governor_enforcement.py` if `commands/create-spec.md` grows; otherwise confirm net-zero bytes `[AC-4.4]`
- [x] 4.6 Regenerate platform trees with `python3 scripts/gen-platform-trees.py` so `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**` match the edited sources `[AC-4.2, AC-4.3]`
- [x] 4.7 Run pytest alone on Python 3.9 and 3.14, then `bash scripts/eval.sh` and `python3 scripts/gen-platform-trees.py --check`; confirm every criterion holds `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- Story 3 edits `commands/create-spec.md` and `agents/user-story-generator.md` too. Start from its result and expect conflicts in the same files.
- `commands/create-spec.md` is over its command byte budget. Any net growth needs a dated, disclosed `KNOWN_OVER_BUDGET` entry. Target net-zero.
- `claude-code/agents/writ-story-gen.md` and `cursor/plugin/**` are generated. Edit the sources and regenerate. Do not hand-edit the trees.
- Run pytest alone in the checkout. `eval.sh`, bash tests, writes under `.writ/state/`, or `git worktree` changes during a pytest run break `test_smoke_leaves_repo_unchanged`.
- `scripts/tests/test_rule_citations.py` is new. `technical-spec.md` → `## Components` lists no test file for wording. Add a row there if the file stays.
- Component rows for this story: `technical-spec.md` → `## Components`, rows marked Story 4.
- The Story 5 trial is out of scope here.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** []
- **Business rules:** [Business Rule 4 (rules live once; cite by number), Business Rule 1 (tasks name files, no internal structure)] — from spec.md → `## 📋 Business Rules (Expanded)`
- **Experience:** []

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

1. **`scripts/tests/test_rule_citations.py`**
   - 11 tests pinning rule-number citations in create-spec Steps 1.4, 2.4, 2.8, the generator, and context-hint-format.md, plus the create-spec byte ledger

### Files Modified

- **`commands/create-spec.md`** (Steps 1.4, 2.4, 2.4b, 2.8)
  - Step 1.4 contract template numbers its Business Rules
  - Step 2.4 expanded rules add detail per `Business Rule N` and never restate
  - Step 2.8 sub-specs cite `Business Rule N`
  - Step 2.4b offset trims; 39081 bytes, unchanged
- **`agents/user-story-generator.md`** (task rules, quality guideline, Context for Agents hint)
  - A task may cite `Business Rule N` but never paraphrases it
  - Business-rule hints cite numbers from the spec's contract
- **`.writ/docs/context-hint-format.md`**
  - `Business Rule N` hint format, examples, validation rows; version 2.1
  - Context for Agents sits at the end of the story file
  - States that `story-context.py` does not resolve rule numbers yet
- **`scripts/tests/test_harness_cuts.py`** (Story 3 ledger test)
  - Accepts any dated ledger entry from the Story 3 start overage when a file's size changes; exact live-total assertion kept
- **Generated copies** (7 files) — regenerated with `scripts/gen-platform-trees.py`
- **`spec-lite.md`** — Small-drift auto-amendment (DEV-005..DEV-008)

### Implementation Decisions

1. **Number the contract template's rules** — the smallest change that makes `Business Rule N` resolvable in a generated spec (DEV-005).
2. **Generic dated-ledger regex** — later edits to `create-spec.md` or `verify-spec.md` need only a new ledger entry, not test edits (DEV-007).

### Test Results

**Verification:** Automated

- ✅ `test_rule_citations.py`: 11 passed on Python 3.9 and 3.14; red run 10 failed, 1 passed
- ✅ Targeted (7 files): 487 passed, 1 skipped on Python 3.9 and 3.14
- ✅ Ledger tolerance checks: +1 byte with a new dated entry passes for both commands; files restored
- ✅ Full suite: 4261 passed, 2 skipped on Python 3.9 and on 3.14
- ✅ `bash scripts/eval.sh`: exit 0
- ✅ `gen-platform-trees.py --check`: pass

**Coverage:** N/A (prose and test-only change)

### Review Outcome

**Result:** PASS with drift note

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** Owned files and regenerated copies, plus one authorized crossing into `test_harness_cuts.py`
- **Safety fact:** measured `tested` (claimed `tested`)

### Deviations from Spec

- **[DEV-005] Step 1.4 contract template numbers its Business Rules** — Severity: Small; auto-amended in spec-lite.md → Files in Scope
- **[DEV-006] Byte-offset trims in Step 2.4b** — Severity: Small; auto-amended in spec-lite.md → Files in Scope
- **[DEV-007] Story 3's ledger test accepts any later dated entry** — Severity: Small; auto-amended in spec-lite.md → Files in Scope
- **[DEV-008] context-hint-format.md drops the "after the Definition of Done" placement** — Severity: Small; auto-amended in spec-lite.md → Files in Scope

### Lessons Learned

1. **`story-context.py` does not resolve `Business Rule N`** — template-following specs resolved 0 bytes of business-rule context before and after; legacy specs with bold-name hints lose resolution if `/edit-spec` regenerates their stories. Follow-up: resolve rule numbers against the contract's numbered list.
2. **Ledger tests must not pin a later file size** — a test that encodes today's size breaks the next story that touches the file.

### Next Story

**Story 5:** Trial lean tasks on one archived spec.
