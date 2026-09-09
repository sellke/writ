# Story 1: Evaluator Agent — Fresh-Context Rubric File and Parity

> **Status:** Completed ✅
> **Commit:** cddc3e32ac4fdb56c157e55326e1358b424165be
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer implementing Phase 11 Stage 4b
**I want to** land `agents/evaluator-agent.md` plus Claude Code / Codex counterparts, the `check-agent-parity.sh` mapping, and a manifest `agents:` entry
**So that** Story 2 can spawn a read-only, fresh-context evaluator whose rubric is acceptance criteria plus test results, without rewriting `review-agent` or changing `/implement-story` spawn in this story

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `agents/review-agent.md` as the shape template, when `agents/evaluator-agent.md` is authored, then its Agent Configuration declares `subagent_type: generalPurpose`, `model_tier: anchor`, `readonly: true`, and `problem` / `outcome` / `exit_criteria`; the prompt rubric is the story’s acceptance criteria and recorded test results; residual architecture, security, and taste stay in scope; FAIL issues may carry an optional Suggested Fix that is never applied; and the prompt does not tell the coder how to rewrite functions or apply a patch. `[AC-1.1]`
- [x] Given the new agent stem `evaluator-agent`, when platform peers land, then `claude-code/agents/writ-evaluator.md` allows Read/Grep/Glob/Bash with Write/Edit disallowed and `permissionMode: plan`, `codex/agents/evaluator-agent.toml` sets `sandbox_mode = "read-only"`, `scripts/check-agent-parity.sh` `claude_counterpart()` maps `evaluator-agent` to `writ-evaluator.md`, and the stem is not added to `claude_exempt`. `[AC-1.2]`
- [x] Given the existing Cursor symlink `.cursor/agents` → `agents/`, when the manifest is updated, then `.writ/manifest.yaml` `agents:` lists `evaluator-agent` with `model_tier: anchor` and no extra Cursor agent file is created. `[AC-1.3]`
- [x] Given `scripts/tests/test_evaluator_agent_contract.py` (or equivalent), when `uv run --python 3.9 pytest` runs that file, then it asserts the markdown Agent Configuration and rubric/residual/no-patch language in `agents/evaluator-agent.md` and asserts `agents/review-agent.md` is not part of this story’s edited file set. `[AC-1.4]`
- [x] Given Story 1’s file set, when the diff is inspected, then `commands/implement-story.md`, `agents/review-agent.md`, `scripts/eval.sh`, and `scripts/review-override.py` are unchanged; no `--default` flag, emit CLI, eight-run, or spawn-site rewrite is introduced. `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_evaluator_agent_contract.py` asserting `model_tier: anchor`, `readonly: true`, problem/outcome/exit_criteria, AC + test-result rubric language, residual architecture/security/taste, no how-to-rewrite / apply-patch instruction, and that `review-agent.md` is not edited in this story `[AC-1.1, AC-1.4]`
- [x] 1.2 Author `agents/evaluator-agent.md` from the review-agent shape (Agent Configuration, Input Requirements, Prompt Template) with the evaluator rubric and residual; do not rewrite `agents/review-agent.md` `[AC-1.1]`
- [x] 1.3 Add `claude-code/agents/writ-evaluator.md` (Read/Grep/Glob/Bash; disallowed Write/Edit; `permissionMode: plan`) and `codex/agents/evaluator-agent.toml` (`sandbox_mode = "read-only"`) `[AC-1.2]`
- [x] 1.4 Add `evaluator-agent) echo "writ-evaluator.md"` to `scripts/check-agent-parity.sh` `claude_counterpart()`; do not add `claude_exempt` `[AC-1.2]`
- [x] 1.5 Add `evaluator-agent` with `model_tier: anchor` to `.writ/manifest.yaml` `agents:`; rely on the existing `.cursor/agents` symlink `[AC-1.3]`
- [x] 1.6 Confirm `commands/implement-story.md`, `agents/review-agent.md`, `scripts/eval.sh`, and `scripts/review-override.py` are byte-identical to the story start `[AC-1.5]`
- [x] 1.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_evaluator_agent_contract.py` green; parity mapping present; no extra Cursor file; no spawn, emit, eight-run, or `--default` work `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Technical considerations.** Copy the block structure from `agents/review-agent.md` (and peers `claude-code/agents/writ-reviewer.md`, `codex/agents/review-agent.toml`). Rubric and residual differ: AC + tests, not a general quality tour; residual is architecture / security / taste. Suggested Fix is report-only. Cursor needs no new file.

**Risks.** A missing `claude_counterpart` mapping makes `check-agent-parity.sh` warn (exit 0) on every run. Dual-purposing `review-agent.md` violates Business Rule 11. Putting spawn or `--full-pipeline` into this story leaks Story 2.

**Integration.** No dependencies. Story 2 owns `/implement-story` spawn, flags, and FAIL-only `review-override.py` wiring (script stays unchanged). Story 3 owns `eval.sh` and spawn-cap. Do not edit `implement-story.md`, `review-agent.md`, `eval.sh`, or `review-override.py`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Spawn evaluator]
- **Shadow paths:** []
- **Business rules:** [Evaluator is read-only (reports what is wrong; no how-to-fix; no applied patch), `review-agent.md` is not rewritten]
- **Experience:** [No user-facing invoke yet (file exists for Story 2), Error experience (missing counterpart / missing `evaluator-agent.md` → parity warning / finding)]

---

## What Was Built

**Implementation Date:** 2026-09-09

### Files Created

1. **`agents/evaluator-agent.md`** (227 lines)
   - Read-only rubric agent. Agent Configuration uses the technical-spec `problem` / `outcome` / `exit_criteria` verbatim. Rubric is acceptance criteria plus recorded test results. Residual is architecture / security / taste. Output is `EVALUATION_RESULT` (PASS / FAIL / PAUSE). Suggested Fix is optional and never applied.

2. **`claude-code/agents/writ-evaluator.md`** (46 lines)
   - Claude peer: Read/Grep/Glob/Bash; Write/Edit disallowed; `permissionMode: plan`.

3. **`codex/agents/evaluator-agent.toml`** (40 lines)
   - Codex peer: `name = "evaluator-agent"`, `sandbox_mode = "read-only"`.

4. **`scripts/tests/test_evaluator_agent_contract.py`** (136 lines)
   - Ten unittest cases for config, rubric, residual, no-patch language, `EVALUATION_RESULT`, git-diff assertion that `review-agent.md` is not edited, and an authenticity pin that names `agents/evaluator-agent.md` as the unit under test.

### Files Modified

- **`scripts/check-agent-parity.sh`** (`claude_counterpart`)
  - Maps `evaluator-agent` → `writ-evaluator.md`. Not added to `claude_exempt`.
- **`.writ/manifest.yaml`** (`agents:`)
  - Alphabetical `evaluator-agent` entry with `model_tier: anchor`.
- **`SKILL.md`**
  - Regenerated via `bash scripts/gen-skill.sh` so CI `--check` stays green.
- **`scripts/tests/test_model_tier_migration.sh`**
  - Agent count 7 → 8; `evaluator-agent` / `anchor` added to the derivation lists.

`commands/implement-story.md`, `agents/review-agent.md`, `scripts/eval.sh`, and `scripts/review-override.py` left unchanged.

### Implementation Decisions

1. **Shape from review-agent, not its quality tour** — Headings and PASS/FAIL/PAUSE/drift stay; change-surface tables and “be actionable / rewrite this function” language do not.
2. **`EVALUATION_RESULT` not `REVIEW_RESULT`** — `review-override.py` does not parse agent output, so the new heading does not require a script edit.
3. **Catalog + model-tier counts in this story** — Gate 0 CAUTION: `gen-skill.sh --check` and `test_model_tier_migration.sh` would fail on an eighth agent if left to a later story.
4. **Authenticity pin** — Gate 4 `test-integrity.py authenticity` only extracts JS-style `from '…'` specifiers. The contract test reads markdown via `Path`; a comment pin `from "../../agents/evaluator-agent.md"` makes the checker resolve the real unit under test. User chose Retry on the BLOCKED escalation.

### Test Results

**Verification:** Automated
- ✅ `uv run --python 3.9 pytest scripts/tests/test_evaluator_agent_contract.py` — 10 passed
- ✅ `bash scripts/tests/test_model_tier_migration.sh` — 8 agents
- ✅ `bash scripts/check-agent-parity.sh` — parity OK
- ✅ `bash scripts/gen-skill.sh --check` — catalog current
- ✅ Regression `scripts/tests/test_gen_codex_agent_tomls.py` — 5 passed
- ✅ `test-integrity.py authenticity` — pass after the pin
- ⚠️ `test-integrity.py coverage` — unverifiable (`no_coverage_report`; no new production Python script)
- Mechanical: arch-check `pass` (rederived proceed; agent CAUTION injected); review-override `unverifiable` (`no_coverage_report` / `nothing_inspected`); drift-format `unverifiable` (`no_drift_signal`); docs-check `unverifiable` (`no_public_exports`); build-smoke `unverifiable` (`unsupported_stack`)

**Coverage:** N/A on production Python (markdown/TOML agents only). Optional measurement on the contract test file: 98%.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** All Story 1 changes in Owned paths. Protected files and adapters untouched.

### Deviations from Spec

None

### Next Story

**Story 2:** Default path and flags — no-flag `/implement-story` spawns `coding-agent` + `evaluator-agent`; `--full-pipeline` keeps the six-agent path.
