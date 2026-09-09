# Story 3: Eval, Adapters, and Spawn-Cap Proof

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer implementing Phase 11 Stage 4b
**I want to** land `scripts/spawn-cap.py`, register an additive `eval.sh` `spawn-cap` check, rewrite adapter sentences that treat no-flag `/implement-story` as the full SDLC default, and record static spawn-cap proof plus a `{date} stage-4b:` decision-log line
**So that** “≤2 default spawns” is proven by a command-file scan (not a live Task count, eight-run, or yuss), `--full-pipeline` remains the hatch, nothing emits `GOAL.md`, and ADR-013 still forbids merge / PR / release

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given Python 3.9 stdlib and `python3 scripts/spawn-cap.py check --command commands/implement-story.md`, when the helper scans default-path spawn sites (`> **Agent:**` or an equivalent Task-spawn instruction in a Gate body that runs without `--full-pipeline`), then allowed stems are `coding-agent` and `evaluator-agent`; default ⊆ those stems and count ≤ 2 prints one `pass` verdict (exit 0); a third or disallowed default stem prints `fail` with `reason: over_cap` (exit 1); missing or unreadable `--command` prints `unverifiable` with `reason: missing_command` (exit 0); `--full-pipeline`-only Agent markers do not count; unknown subcommand or bad argv exits 2 on stderr; output is one verdict line, optional `reason:`, summary last; stdout never prints accept / reject / modify-spec; and the helper does not spawn live Tasks. `[AC-3.1]`
- [ ] Given `scripts/eval.sh` after this story, when `CHECKS` and the check function are read, then `spawn-cap` is listed near `goal-emit` and `check_spawn_cap()` mirrors `check_spec_analyze` / `check_goal_emit`: missing `scripts/spawn-cap.py` or helper usage exit 2 → `add_finding`; helper `pass` / `fail` / `unverifiable` → `add_note` only (do not count-block the suite on a documented `--full-pipeline` hatch); Stage 2b / 3 / 4a checks remain additive. `[AC-3.2]`
- [ ] Given `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, and `adapters/openclaw.md`, when sentences that imply no-flag `/implement-story` is the full SDLC / five-agent / six-gate default are rewritten, then that path is `--full-pipeline`; only those relitigating sentences change; no adapter gains a `/goal` section; and this story does not invent a high-stakes classifier. `[AC-3.3]`
- [ ] Given pytest fixtures in `scripts/tests/test_spawn_cap.py` for pass, `over_cap`, `missing_command`, and usage exit 2, plus `scripts/tests/test_eval_spawn_cap.sh` in the `test_eval_spec_analyze.sh` / `test_eval_review_override.sh` stub-helper shape, when `uv run --python 3.9 pytest scripts/tests/test_spawn_cap.py` and `bash scripts/tests/test_eval_spawn_cap.sh` run, then each fixture asserts the matching verdict, `reason:` when present, summary last, and exit 0 / 1 / 2, and the bash file asserts missing helper / exit 2 → finding and stub `pass` / `fail` / `unverifiable` → notes with check exit 0. `[AC-3.4]`
- [ ] Given Story 2’s default path already in `commands/implement-story.md`, when this story closes, then What Was Built records helper exists, default-path scan ≤ 2, `--full-pipeline` still names the six agents, and `bash scripts/eval.sh` exits 0; the closing commit appends `{date} stage-4b: {what changed}` to `.writ/decision-log.md` naming evaluator + default spawn + spawn-cap; spawn logic is not changed beyond an optional comment pointing at spawn-cap; no `GOAL.md` is emitted; no live Task count, eight-run, or yuss; and ADR-013 holds (nothing merges, opens a PR, or releases). `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write `scripts/tests/test_spawn_cap.py` (pytest, Python 3.9) with fixtures for pass (default ⊆ {coding-agent, evaluator-agent} and count ≤ 2), fail `over_cap` (third or disallowed default Agent marker; `--full-pipeline`-only markers excluded from the count), unverifiable `missing_command`, and usage exit 2; assert one verdict line, `reason:` when present, summary last, exit 0/1/2, and that accept / reject / modify-spec never appear `[AC-3.1, AC-3.4]`
- [ ] 3.2 Write `scripts/tests/test_eval_spawn_cap.sh` in the `scripts/tests/test_eval_spec_analyze.sh` / `scripts/tests/test_eval_review_override.sh` stub-helper shape: `spawn-cap` in `CHECKS`; `check_spawn_cap()` defined; missing helper → `add_finding`; usage exit 2 → `add_finding`; stub `pass` / `fail` / `unverifiable` → notes, check exit 0 `[AC-3.2, AC-3.4]`
- [ ] 3.3 Implement `scripts/spawn-cap.py` (stdlib, Python 3.9, argparse, `--repo` / `--project` house shape): `check --command PATH`; count default-path spawn sites only; do not count `--full-pipeline`-guarded markers; do not spawn live Tasks; unknown subcommand / bad argv → exit 2 `[AC-3.1]`
- [ ] 3.4 Add `spawn-cap` to `CHECKS=(...)` near `goal-emit` and implement `check_spawn_cap()` in `scripts/eval.sh` (mirror `check_spec_analyze` / `check_goal_emit`; additive only): missing helper / exit 2 → `add_finding`; other verdicts → `add_note` `[AC-3.2]`
- [ ] 3.5 Rewrite only adapter sentences in `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`, and `adapters/openclaw.md` that would relitigate the no-flag default (e.g. “Build it with the full SDLC pipeline”); that path is `--full-pipeline`; add no `/goal` section `[AC-3.3]`
- [ ] 3.6 Record spawn-cap proof in this story’s What Was Built (helper exists; default-path scan ≤ 2; `--full-pipeline` still names the six agents; `eval.sh` exits 0) and append `{date} stage-4b: {what changed}` to `.writ/decision-log.md` naming evaluator + default spawn + spawn-cap; optional comment in `commands/implement-story.md` pointing at spawn-cap only — do not change spawn logic `[AC-3.5]`
- [ ] 3.7 Verify acceptance criteria and tests: `uv run --python 3.9 pytest scripts/tests/test_spawn_cap.py` green; `bash scripts/tests/test_eval_spawn_cap.sh` green; `bash scripts/eval.sh --check=spawn-cap` and full `bash scripts/eval.sh` exit 0; adapters name `--full-pipeline` for the old full-SDLC implication; WWB + decision-log line; no emit, no live Task count, no eight-run / yuss `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Technical considerations.** Mirror `scripts/spec-analyze.py` / `scripts/goal-emit.py` for argparse, one verdict line, `reason:`, summary last, exit 0/1/2, and `--repo` / `--project`. Verdict table is technical-spec §3. Zero default Agent markers may be `fail` `over_cap` or a documented unverifiable — pick one in implementation and keep the fixtures honest. `install.sh` already copies `scripts/*.py`; do not edit it unless a dry-run proves otherwise.

**Decision log.** Prior stages append `{date} stage-N:` lines to `.writ/decision-log.md` (stage-2b, stage-4a). This story uses that same file. If the implementer cannot append there, state in Notes / WWB that Story 3 WWB carries the `stage-4b:` line.

**Proof, not a session.** ≤2 default spawns is a static command-file / agent-name scan. Do not count live Tasks. Do not run eight-run or yuss. Do not emit `GOAL.md`. Do not add a `/goal` section to any adapter.

**Eval hatch.** A live-repo `fail` `over_cap` or a documented `--full-pipeline` six-agent hatch must not count-block `eval.sh`. Missing helper / exit 2 is the finding.

**Integration.** Depends on Story 2’s default path and `--full-pipeline` hatch already being in `commands/implement-story.md`. This story does not change spawn logic beyond an optional pointer comment. Shared `eval.sh` with Stages 2b / 3 / 4a: append `spawn-cap`; do not rewrite those checks. ADR-013: nothing merges, opens a PR, or releases.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [spawn-cap.py, eval.sh] — `technical-spec.md` → `## 5. Error & Rescue Map` (command file missing → `missing_command`; third default Agent marker → `over_cap`; helper missing → `add_finding`)
- **Shadow paths:** [spawn-cap.py check, --full-pipeline] — `technical-spec.md` → `## 6. Shadow Paths`
- **Business rules:** [Spawn-cap proof is static (Rule 12), ADR-013 / no yuss / no eight-run / no emit (Rule 13), Decision log `{date} stage-4b:` (Rule 14)] — `spec.md` → `## 📋 Business Rules`
- **Experience:** [Moment of truth (default Task spawn count is 2), Error experience (missing spawn-cap helper / exit 2 is a finding)] — `spec.md` → `## 🎯 Experience Design`

Scope indexes: `spec.md` → `## Detailed Requirements` → `### Story 3`; `spec.md` → Success Criteria (last two bullets); `spec.md` → `## ⚠️ Technical Concerns` (adapters, static scan); `spec.md` → `## ⚠️ Cross-Spec Overlap` (`eval.sh` additive `CHECKS`); `technical-spec.md` → `## 3. Spawn-cap helper`; `technical-spec.md` → `## 4. Adapter wording`; Out of scope: emit, eight-run.
