# Story 3: Adapter + Eval + Gold Round-Trip

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Writ maintainer who needs a machine check and a written gold match, not a live Claude Code session
**I want to** document invoke-as-copy in `adapters/claude-code.md`, register `goal-emit` in `scripts/eval.sh`, and commit `loop-yes` / `loop-no` gold fixtures
**So that** zero manual edits is proven by gold-file equality plus printed invoke equal to the adapter template, `eval.sh` stays additive, and we never run a live `/goal`, yuss, or eight-run

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given `adapters/claude-code.md` after this story, when the `/goal` Stop Hook section is read, then it states the human pastes the emitter’s printed invoke line unchanged; the existing three-way `/goal` template is not rewritten; Cursor, Codex, and OpenClaw adapters gain no `/goal` section `[AC-3.1]`
- [ ] Given `scripts/eval.sh` after this story, when `CHECKS` and function names are read, then `goal-emit` is listed in `CHECKS=(...)` and `check_goal_emit()` exists; a missing `scripts/goal-emit.py` or helper usage exit 2 causes `add_finding` (eval fails that check); Stage 3 `spec-analyze` and Stage 2b checks remain `[AC-3.2]`
- [ ] Given a present helper that prints `pass`, `fail`, or `unverifiable` with exit 0 or 1, when `bash scripts/eval.sh --check=goal-emit` runs, then those emit verdicts and reasons are relayed with `add_note` only — not count-blocking — and the check exits 0 when the helper is healthy `[AC-3.3]`
- [ ] Given `scripts/tests/fixtures/goal-emit/`, when the fixture tree is listed, then `loop-yes/` contains a card plus gold `GOAL.md`, `VERIFY.md`, and `invoke.txt`, and `loop-no/` contains a card only (expect `unverifiable` `loop_no`, no emit dir); fixture file bodies contain no `AC-n.m` tokens `[AC-3.4]`
- [ ] Given those gold files, when Story 1’s emitter is run against the `loop-yes` card, then emitted `GOAL.md`, `VERIFY.md`, and the printed invoke line are byte-equal to gold and the invoke diffs empty against the adapter template; Story 3 What Was Built records that equality; the closing commit appends `{date} stage-4a: naming emit + hooks + gold` to `.writ/decision-log.md`; no live Claude Code `/goal`, yuss checkout, or eight-run; nothing in this story demotes the five-agent pipeline `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_eval_goal_emit.sh` in the `scripts/tests/test_eval_spec_analyze.sh` stub-helper shape: `goal-emit` in `CHECKS`; `check_goal_emit()` defined; missing helper → `add_finding`; usage exit 2 → `add_finding`; stub `pass` / `fail` / `unverifiable` → report notes, check exit 0 `[AC-3.2, AC-3.3]`
- [ ] 3.2 Write gold-round-trip assertions (pytest under `scripts/tests/` or a focused bash file) that emit the `loop-yes` card into a temp dir, require equality with gold `GOAL.md` / `VERIFY.md` / `invoke.txt`, require printed invoke equal to the Claude Code adapter template, and assert `loop-no` is `unverifiable` `loop_no` with no `--out` dir `[AC-3.4, AC-3.5]`
- [ ] 3.3 Document in `adapters/claude-code.md` that the human pastes the emitter’s printed invoke line unchanged; leave the existing three-way `/goal` template as the source; do not add a `/goal` section to Cursor, Codex, or OpenClaw adapters `[AC-3.1]`
- [ ] 3.4 Add `goal-emit` to `CHECKS=(...)` and implement `check_goal_emit()` in `scripts/eval.sh` (additive only; do not revert `spec-analyze` or Stage 2b checks): missing helper / exit 2 → `add_finding`; emit `pass` / `fail` / `unverifiable` → `add_note` `[AC-3.2, AC-3.3]`
- [ ] 3.5 Author `scripts/tests/fixtures/goal-emit/loop-yes/` (card + gold `GOAL.md`, `VERIFY.md`, `invoke.txt`) and `loop-no/` (card only); keep fixture files free of `AC-n.m` tokens so `ac-trace` does not scan them as citations `[AC-3.4]`
- [ ] 3.6 Record gold equality in this story’s What Was Built and append `{date} stage-4a: naming emit + hooks + gold` to `.writ/decision-log.md` `[AC-3.5]`
- [ ] 3.7 Verify acceptance criteria and tests: adapter paste rule and unchanged three-way template, eval registration and note-vs-finding split, both fixture trees, WWB + decision-log, no live `/goal` / yuss / eight-run; `bash scripts/tests/test_eval_goal_emit.sh`, the gold assertions, and `bash scripts/eval.sh --check=goal-emit` (full `eval.sh` still exits 0) `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Technical considerations.** Story 1 owns `scripts/goal-emit.py` and the emit/check CLI. Story 2 owns `/create-goal` and `/implement-phase` hooks. This story only documents invoke-as-copy, adds an eval check, and commits gold. Shared `eval.sh` with prior stages: append `goal-emit`; do not rewrite `check_spec_analyze` or Stage 2b checks.

**Proof, not a session.** Live `/goal` cannot be proven in this repo’s eval. Gold-file equality plus printed invoke == adapter template is the proof. Do not register a hook and do not run a live Claude Code `/goal`.

**Fixture scan.** `scripts/tests/fixtures/` is test-shaped. Any `AC-n.m` token in those files becomes an `ac-trace` citation. Author stand-in card text without those tokens.

**Risks.** Treating emit `fail` like a format-check `fail` would make a live-repo `loop: no` or missing card count-blocking. Rewriting clauses (a)/(b)/(c) in the adapter would break Story 1 gold if the emitter copies that template.

**Integration.** Decision-log line must honestly name emit (Story 1) + hooks (Story 2) + gold (this story). Five-agent `/implement-story` spawn is out of scope.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** `technical-spec.md → ## 4. Error & Rescue Map`
- **Shadow paths:** `technical-spec.md → ## 5. Shadow Paths`
- **Business rules:** [Invoke is copy-paste, ADR-013 / no yuss / no eight-run / no live `/goal`, Decision log]
- **Experience:** `spec.md → ## 🎯 Experience Design`
