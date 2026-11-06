# Story 4: Targeted-test ownership

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** developer whose stories run through `/implement-story`
**I want to** the coding agent and Gate 3 reviewers to run only the story's targeted tests, with the full suite run once per spec
**So that** a story stops re-running the full gates in the coder, reviewer and lane (Phase 15 retro F21: 3.2 h of a 4.6 h lane)

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given `agents/coding-agent.md` self-verification, when it runs, then it runs only the story's targeted tests and no longer runs the full suite when the suite takes under 30 s `[AC-4.1]`
- [ ] Given `agents/evaluator-agent.md` and `agents/review-agent.md`, when they need test results, then they read `recorded_test_results` and run no full suite, except one ADR-032 evidence repro `[AC-4.2]`
- [ ] Given the Gate 4 prose in `commands/implement-story.md`, when read, then it states that the orchestrator's recorded run is targeted, the full suite runs once at `implement-spec` Step 4.1, and `/ship` runs it for a standalone story `[AC-4.3]`
- [ ] Given the source agents, when `scripts/gen-platform-trees.py` runs, then `claude-code/agents/`, `cursor/plugin/` and `codex/` carry the same wording, and `KNOWN_OVER_BUDGET` records each changed byte size with a date `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write tests in `scripts/tests/test_targeted_test_ownership.py` that fail now and pin the wording for the first three criteria and generated-copy parity for the fourth `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.2 Edit the self-verification step in `agents/coding-agent.md` to run only the story's targeted tests, and remove the full-suite-under-30-s rule `[AC-4.1]`
- [ ] 4.3 Edit the test instructions in `agents/evaluator-agent.md` and `agents/review-agent.md` to read `recorded_test_results`, with one ADR-032 evidence repro allowed and no suite run `[AC-4.2]`
- [ ] 4.4 Edit the Gate 4 prose in `commands/implement-story.md` to state that the recorded run is targeted and that the full suite runs once at `implement-spec` Step 4.1 or in `/ship` `[AC-4.3]`
- [ ] 4.5 Run `python3 scripts/gen-platform-trees.py`, then add dated `KNOWN_OVER_BUDGET` entries in `scripts/tests/test_governor_enforcement.py` for the changed byte sizes, then run `scripts/check-agent-parity.sh` `[AC-4.4]`
- [ ] 4.6 Verify acceptance criteria are met: each criterion maps to a passing test in `scripts/tests/test_targeted_test_ownership.py` `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [ ] 4.7 Verify all tests pass: run the new test file and `scripts/tests/test_governor_enforcement.py` under Python 3.9 and 3.14 with `uv run --isolated` `[AC-4.4]`

## Notes

- Python 3.9 is the floor. The new test file must use only 3.9 stdlib.
- Do not hand-edit `claude-code/agents/`, `cursor/plugin/` or `codex/`. Edit the source files in `agents/` and `commands/`, then regenerate.
- `commands/implement-story.md` is also edited by Story 3 (runner calls). Start this story from Story 3's commit, so the Gate 4 edit does not conflict with the runner prose.
- Do not touch `agents/supervisor-agent.md` or `commands/implement-spec.md`. Story 5 owns them. The `implement-spec` Step 4.1 reference in Gate 4 names an existing step; do not change that step here.
- Targeted verification covers only the new test file and `test_governor_enforcement.py`. The full pytest suite on both interpreters, the bash tests and `scripts/eval.sh` run once at the end of the spec, not in this story.
- Run pytest alone. `eval.sh`, bash tests, `.writ/state/` writes, or `git worktree` changes in the same checkout during pytest break `test_smoke_leaves_repo_unchanged`.
- Business Rule 6 allows one ADR-032 evidence repro by a reviewer. That repro is not a suite run, and the wording must say so, or a reviewer will read the rule as a ban on all test execution.
- Pin key phrases (for example `recorded_test_results`, `Step 4.1`, `/ship`) rather than whole paragraphs, so later prose edits do not break unrelated tests.
- The `KNOWN_OVER_BUDGET` entries are dated disclosures of byte changes. Record the new size, not a delta.

## Context for Agents

- **Business rules:** Business Rule 6 (targeted tests; reviewers read `recorded_test_results`). Cite by number only.
- **Experience:** spec.md → 🎯 Experience Design → User Journey, steps 3 and 6 (coder runs only targeted tests; Gate 3 reads `recorded_test_results` and does not run the full suite).
- **Error map rows:** []
- **Shadow paths:** []
