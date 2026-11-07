# Story 4: Targeted-test ownership

> **Status:** Completed ✅ (2026-11-07)
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** developer whose stories run through `/implement-story`
**I want to** the coding agent and Gate 3 reviewers to run only the story's targeted tests, with the full suite run once per spec
**So that** a story stops re-running the full gates in the coder, reviewer and lane (Phase 15 retro F21: 3.2 h of a 4.6 h lane)

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [x] Given `agents/coding-agent.md` self-verification, when it runs, then it runs only the story's targeted tests and no longer runs the full suite when the suite takes under 30 s `[AC-4.1]`
- [x] Given `agents/evaluator-agent.md` and `agents/review-agent.md`, when they need test results, then they read `recorded_test_results` and run no full suite, except one ADR-032 evidence repro `[AC-4.2]`
- [x] Given the Gate 4 prose in `commands/implement-story.md`, when read, then it states that the orchestrator's recorded run is targeted, the full suite runs once at `implement-spec` Step 4.1, and `/ship` runs it for a standalone story `[AC-4.3]`
- [x] Given the source agents, when `scripts/gen-platform-trees.py` runs, then `claude-code/agents/`, `cursor/plugin/` and `codex/` carry the same wording, and `KNOWN_OVER_BUDGET` records each changed byte size with a date `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 Write tests in `scripts/tests/test_targeted_test_ownership.py` that fail now and pin the wording for the first three criteria and generated-copy parity for the fourth `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.2 Edit the self-verification step in `agents/coding-agent.md` to run only the story's targeted tests, and remove the full-suite-under-30-s rule `[AC-4.1]`
- [x] 4.3 Edit the test instructions in `agents/evaluator-agent.md` and `agents/review-agent.md` to read `recorded_test_results`, with one ADR-032 evidence repro allowed and no suite run `[AC-4.2]`
- [x] 4.4 Edit the Gate 4 prose in `commands/implement-story.md` to state that the recorded run is targeted and that the full suite runs once at `implement-spec` Step 4.1 or in `/ship` `[AC-4.3]`
- [x] 4.5 Run `python3 scripts/gen-platform-trees.py`, then add dated `KNOWN_OVER_BUDGET` entries in `scripts/tests/test_governor_enforcement.py` for the changed byte sizes, then run `scripts/check-agent-parity.sh` `[AC-4.4]`
- [x] 4.6 Verify acceptance criteria are met: each criterion maps to a passing test in `scripts/tests/test_targeted_test_ownership.py` `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`
- [x] 4.7 Verify all tests pass: run the new test file and `scripts/tests/test_governor_enforcement.py` under Python 3.9 and 3.14 with `uv run --isolated` `[AC-4.4]`

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

---

## What Was Built

**Implementation Date:** 2026-11-07

### Files Created

1. **`scripts/tests/test_targeted_test_ownership.py`** — 15 tests pinning AC-4.1 to AC-4.4 (phrases, not paragraphs), including the `/ship --test` link to `commands/ship.md` and all 17 generated copies
2. **`scripts/tests/test_ship_suite_claim_repro.py`** — Gate 3 iteration 1 evidence repro (F1), committed unchanged

### Files Modified

- **`agents/coding-agent.md`** (Self-Verification step 1; recode step; `problem:` line) — targeted tests only; "Never run the full suite, however fast"; the full suite runs at `implement-spec` Step 4.1 or `/ship --test`
- **`agents/evaluator-agent.md`, `agents/review-agent.md`** (spawn prompt after `{recorded_test_results}`) — read recorded results, never run the full suite; write an `**Evidence:**` field per blocking finding; one repro run outside the repo or a re-run of a named test file is allowed
- **`commands/implement-story.md`** (Gate 3 `recorded_test_results` selection now includes importers of changed source files; Gate 4 default line) — 38542 → 38537 bytes
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET` 13582 → 13577, dated)
- **`scripts/tests/test_evidence_gate_wiring.py`** (`RECORDED_RUN_DEF` follows the Gate 3 definition)
- **`scripts/story-gate.py`, `scripts/tests/test_story_gate.py`** (maintainer-approved runner change, DEV-019: evidence-manifest repros left out of the authenticity input; manifest accepted only as `--prior` accepts it; shell filter on `check --tests`)
- **`.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`** (runner note)
- **17 generated copies** (`claude-code/agents/writ-{coder,evaluator,reviewer}.md`, `codex/agents/*.toml`, `cursor/plugin/{agents,commands}/*`, `plugins/writ/{agents,commands,scripts}/*`)

### Implementation Decisions

1. **Gate 3 owns the recorded-run selection** — Gate 4 only says the run is targeted; the selection is defined once.
2. **Agent repro limit vs evidence script** — the agent runs at most one repro itself; the evidence script still runs every `**Evidence:**` field the reviewer writes.

### Test Results

**Verification:** Automated

- ✅ Orchestrator's recorded run (Python 3.9): 590 passed across 13 files; `check-agent-parity.sh` and `test_jev_shadow_hooks.sh` pass
- ✅ Runner fix: `test_story_gate.py` 48 passed (3.9 and 3.14); 417 passed across the runner's targeted set
- ✅ `story-gate.py` post-review: pass, `gate3: PASS (row 5)`, head `9689250`, `dirty: false`
- ✅ `gen-platform-trees.py --check`: pass
- Full suite and `eval.sh`: run once at spec end

**Coverage:** N/A — no coverage report in this repo

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) (iteration 1 FAIL: F1, plain `/ship` runs no tests; confirmed by the runner, row 7)
- **Gate 3 route:** `review-agent` (cross-component; generated copies outside the map)
- **Drift:** Medium (DEV-018 Small; DEV-019 Medium, maintainer-approved runner change)
- **Security:** Clean
- **Boundary Compliance:** sources in owned files; generated copies, the repro, one wiring pin, and the runner change justified
- **Safety fact:** measured `tested` (claimed `tested`)
- **Runner change review:** targeted review FAIL (manifest acceptance looser than `--prior`), recoded in `9689250`, PASS

### Deviations from Spec

See `drift-log.md` Story 4: DEV-018 (Small), DEV-019 (Medium).

### Lessons Learned

1. **Spec facts about other commands need a check** — Business Rule 6 said plain `/ship` runs the suite; `ship.md` says it does not. The reviewer caught it by reading the command.
2. **The runner first ran on its own story's agents here** — Stories 4 onward run on the new two-call default path.

### Next Story

**Story 5:** the supervisor reads the `story-gate` record and checks its head SHA; `implement-spec` drops Step 2.3 and the per-story `context.md` regeneration. Open maintainer question: a standalone `/implement-story` + plain `/ship` never runs the full suite.

