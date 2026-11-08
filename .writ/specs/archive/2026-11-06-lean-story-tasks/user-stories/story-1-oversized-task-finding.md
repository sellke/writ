# Story 1: `oversized_task` finding in ac-trace

> **Status:** Completed ✅ (2026-11-06)
> **Commit:** 55eab7541727c6009444109e7c95ba2dd2e1d0e5
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** `/create-spec` orchestrator at Step 2.6a, or a developer running `ac-trace.py check`
**I want to** receive an informational `oversized_task` finding for each task over 50 words in a `Not Started` story
**So that** over-long tasks are regenerated before implementation starts (Business Rule 2)

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5
> **Verified by:** AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 — `scripts/tests/test_ac_trace.py::OversizedTaskTests` (10 tests), 75 passed on Python 3.9 and 3.14; that file is in the ac-trace citation scan's skip list

- [x] Given a `Not Started` story with one task of 51 words, when `ac-trace.py check` runs, then it reports one `oversized_task` finding with severity `informational` and detail `task 1.3 has 51 words (limit 50)`. `[AC-1.1]`
- [x] Given a `Not Started` story with one task of exactly 50 words, when `ac-trace.py check` runs, then it reports no `oversized_task` finding. `[AC-1.2]`
- [x] Given a story whose status is `In Progress`, `Completed ✅`, or absent, with a task over 50 words, when `ac-trace.py check` runs, then it reports no `oversized_task` finding. `[AC-1.3]`
- [x] Given a `Not Started` story with an over-long task, when `ac-trace.py check` runs, then the exit code matches the same run with that task at 50 words, and the schema is `ac-trace-check-v1`. `[AC-1.4]`
- [x] Given a `Not Started` story with an unnumbered 60-word task line at line L, when `ac-trace.py check` runs, then the detail reads `task at line L has 60 words (limit 50)`. `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write tests in `scripts/tests/test_ac_trace.py` for the `oversized_task` finding: over-limit, boundary, status scope, unnumbered line, exit code and schema. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.2 Emit an informational `oversized_task` finding from `scripts/ac-trace.py check` for each task line over 50 words in `Not Started` stories, with the fields the technical-spec.md `oversized_task` section defines. `[AC-1.1, AC-1.3]`
- [x] 1.3 Count words as Business Rule 2 defines, and format the detail text per the technical-spec.md `oversized_task` section, including the unnumbered-line form. `[AC-1.2, AC-1.5]`
- [x] 1.4 Add an `oversized_task` row to the Finding Codes table in `.writ/docs/acceptance-criteria-ids.md`, with severity informational and the Not Started scope. `[AC-1.3]`
- [x] 1.5 Verify each criterion against `test_ac_trace.py` output, and confirm no existing finding code or exit code changed. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.6 Run pytest under Python 3.9 and 3.14, then `bash scripts/eval.sh`; all must pass. Commands and the run-alone rule are in Notes. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Python floor:** 3.9 (`pyproject.toml`). Do not rely on 3.10+ stdlib behavior.
- **Commands:** `uv run --isolated --python 3.9 --with pytest pytest`, and the same with `--python 3.14`.
- **Run pytest alone.** `eval.sh`, the bash tests, writes under `.writ/state/`, or `git worktree` changes in the same checkout during pytest make `test_smoke_leaves_repo_unchanged` and the app-verify tests fail. For read-only eval runs, use `bash scripts/eval.sh --report=<scratch path>`.
- **Boundary:** 50 words gives no finding; 51 gives one. An empty task (checkbox and tag only) counts as 0 words.
- **Word counting:** strip the checkbox, the `N.M` number, and the trailing AC tag. Inline code counts as the words it contains.
- **Status scope:** only the exact status `Not Started`, after trimming. No Status line in the first 15 lines, or no `## Implementation Tasks` section, emits nothing.
- **Informational only:** the exit code and the `ac-trace-check-v1` schema do not change. Step 2.6a, not the script, treats the finding as a regeneration trigger.
- **Integration:** Story 2 (Step 2.6a) and Story 5 (trial) consume this finding.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Count task words, Read story status] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Happy: all tasks ≤50 words, Nil: story file has no tasks section, Empty: task line is only a checkbox and tag, Upstream: legacy spec under /verify-spec with long tasks and Completed ✅] — from technical-spec.md → Shadow Paths
- **Business rules:** [Rule 2 (50-word limit and task counting), Rule 2 scope (Not Started only)] — from spec.md → 📋 Business Rules (Expanded)
- **Experience:** [Feedback for a task over 50 words, first attempt (regenerate, no mention if retry passes)] — from spec.md → 🎯 Experience Design → State Catalog

---

## What Was Built

**Implementation Date:** 2026-11-06

### Files Created

None.

### Files Modified

- **`scripts/ac-trace.py`** (`SEVERITY`, task-word helpers, `check()`, module docstring)
  - New informational finding `oversized_task` for tasks over 50 words in `Not Started` stories
  - Detail `task N.M has W words (limit 50)`, or `task at line L has W words (limit 50)` for an unnumbered task; `id` is null
- **`scripts/tests/test_ac_trace.py`** (`OversizedTaskTests`, `write_story`)
  - 10 tests: boundary, statuses, no tasks section, empty task, inline code, missing tag, unnumbered line, line order, exit code and schema
  - `write_story` accepts `status=None` to omit the Status line
- **`.writ/docs/acceptance-criteria-ids.md`** (Finding Codes)
  - `oversized_task` row: informational, `Not Started` only
- **`plugins/writ/scripts/ac-trace.py`** (generated)
  - Regenerated with `scripts/gen-platform-trees.py`

### Implementation Decisions

1. **Number pattern is exactly `N.M` followed by whitespace** — `1.3. Foo` is treated as unnumbered and gets the line-number detail.
2. **Only the existing `TAG` pattern is stripped** — a malformed tag counts as words, matching the technical spec.

### Test Results

**Verification:** Automated

- ✅ `test_ac_trace.py`: 75 passed, 1 skipped (3.9 and 3.14)
- ✅ Full suite: 4236 passed, 2 skipped on Python 3.9 and on 3.14
- ✅ `bash scripts/eval.sh`: exit 0
- ✅ `gen-platform-trees.py --check`: pass

**Coverage:** N/A — `test-integrity.py coverage` unverifiable (no coverage report in this repo)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** All changes in owned files or the regenerated plugin copy; the Gate 0.5 map omitted `scripts/ac-trace.py`, which the tasks name
- **Safety fact:** measured `tested` (claimed `tested`)

### Deviations from Spec

None

### Lessons Learned

1. **Tests in `test_ac_trace.py` never count as AC citations** — the file is in `CITATION_SCAN_SKIP`, so stories tested there need a `Verified by:` line.

### Next Story

**Story 2:** Lean task rules in the story generator and Step 2.6a — make `oversized_task` a Step 2.6a failure.
