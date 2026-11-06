# Story 1: `oversized_task` finding in ac-trace

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** `/create-spec` orchestrator at Step 2.6a, or a developer running `ac-trace.py check`
**I want to** receive an informational `oversized_task` finding for each task over 50 words in a `Not Started` story
**So that** over-long tasks are regenerated before implementation starts (Business Rule 2)

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given a `Not Started` story with one task of 51 words, when `ac-trace.py check` runs, then it reports one `oversized_task` finding with severity `informational` and detail `task 1.3 has 51 words (limit 50)`. `[AC-1.1]`
- [ ] Given a `Not Started` story with one task of exactly 50 words, when `ac-trace.py check` runs, then it reports no `oversized_task` finding. `[AC-1.2]`
- [ ] Given a story whose status is `In Progress`, `Completed ✅`, or absent, with a task over 50 words, when `ac-trace.py check` runs, then it reports no `oversized_task` finding. `[AC-1.3]`
- [ ] Given a `Not Started` story with an over-long task, when `ac-trace.py check` runs, then the exit code matches the same run with that task at 50 words, and the schema is `ac-trace-check-v1`. `[AC-1.4]`
- [ ] Given a `Not Started` story with an unnumbered 60-word task line at line L, when `ac-trace.py check` runs, then the detail reads `task at line L has 60 words (limit 50)`. `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write tests in `scripts/tests/test_ac_trace.py` for the `oversized_task` finding: over-limit, boundary, status scope, unnumbered line, exit code and schema. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Emit an informational `oversized_task` finding from `scripts/ac-trace.py check` for each task line over 50 words in `Not Started` stories, with the fields the technical-spec.md `oversized_task` section defines. `[AC-1.1, AC-1.3]`
- [ ] 1.3 Count words as Business Rule 2 defines, and format the detail text per the technical-spec.md `oversized_task` section, including the unnumbered-line form. `[AC-1.2, AC-1.5]`
- [ ] 1.4 Add an `oversized_task` row to the Finding Codes table in `.writ/docs/acceptance-criteria-ids.md`, with severity informational and the Not Started scope. `[AC-1.3]`
- [ ] 1.5 Verify each criterion against `test_ac_trace.py` output, and confirm no existing finding code or exit code changed. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.6 Run pytest under Python 3.9 and 3.14, then `bash scripts/eval.sh`; all must pass. Commands and the run-alone rule are in Notes. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Count task words, Read story status] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Happy: all tasks ≤50 words, Nil: story file has no tasks section, Empty: task line is only a checkbox and tag, Upstream: legacy spec under /verify-spec with long tasks and Completed ✅] — from technical-spec.md → Shadow Paths
- **Business rules:** [Rule 2 (50-word limit and task counting), Rule 2 scope (Not Started only)] — from spec.md → 📋 Business Rules (Expanded)
- **Experience:** [Feedback for a task over 50 words, first attempt (regenerate, no mention if retry passes)] — from spec.md → 🎯 Experience Design → State Catalog
