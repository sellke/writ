# Phase 11 Stage 4b: Pipeline Demote

> **Status:** Not Started
> **Created:** 2026-09-09
> **Owner:** @unknown
> **Dependencies:** [2026-09-08-phase11-stage2b-mechanize-the-gates]
> **Extends:** [2026-09-08-phase11-stage2b-mechanize-the-gates](../2026-09-08-phase11-stage2b-mechanize-the-gates/spec.md)
> **Origin:** Promoted from Goal Card [`2026-09-05-writ-contract-and-verifier-layer.md`](../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — Stage 4 **demote only** (assessment §5 Step 5). Emit (Goal Card → `/goal`) is `2026-09-09-phase11-stage4-goal-emit` and is out of this spec. Evidence: [`2026-09-05-goldilocks-assessment.md`](../../product/2026-09-05-goldilocks-assessment.md) §5 Step 5; Goal Card DONE WHEN line 6 (spawn half); Stage 2b Story 1 What Was Built (FAIL-only review-override; do not rediscover).
> **Loop:** unit `story` · `max_iterations: 8` · `on_exhaustion: halt_reported` · stalled 3 turns: stop and report (carried from the Goal Card's STOP-CAPS)

## Specification Contract

**Deliverable:** Default `/implement-story` spawns exactly two Task subagents — `coding-agent` plus a new fresh-context `evaluator-agent` — and keeps the five-agent path behind `--full-pipeline`.

**Must Include:** A new `agents/evaluator-agent.md` whose rubric is the story’s acceptance criteria and test results (not “find problems”); existing Stage 2b scripts still run on the default path; `--full-pipeline` is the human opt-in; default auto-escalates to `--full-pipeline` only after the evaluator fails twice (recode, then fail again).

**Hardest Constraint:** Prove “≤2 default spawns” without an eight-run yuss re-run. A FAIL that means “could not tell” stays `unverifiable`. Do not invent a high-stakes classifier. Do not change Stage 2b’s FAIL-only `review-override.py` rule.

**Stories:**

1. **Evaluator agent** — `agents/evaluator-agent.md` plus Claude Code / Codex counterparts, manifest, and parity mapping. Rubric is AC + tests. Read-only. Does not rewrite `review-agent`. Does not change spawn yet.
2. **Default path + flags** — `commands/implement-story.md`: no-flag = coding-agent + evaluator + scripts; `--full-pipeline` / `--quick` / `--review-only` matrix; two-fail escalation; Gate 4 script fail recodes via coding-agent.
3. **Eval + adapters + proof** — `scripts/spawn-cap.py` + `eval.sh` check; adapter wording so “full SDLC” is no longer the no-flag implication; decision-log `{date} stage-4b:`; What Was Built records the spawn-cap proof.

**Success Criteria** (Goal Card DONE WHEN line 6, demote half only):

- Default path of `commands/implement-story.md` names at most two spawn sites (`coding-agent`, `evaluator-agent`).
- `agents/evaluator-agent.md` exists; `review-agent.md` is not rewritten.
- `--full-pipeline` / `--quick` / `--review-only` match the invocation matrix.
- `bash scripts/eval.sh` has a spawn-cap check and exits 0 at the end of every story.
- Story 3 What Was Built records the spawn-cap proof (static command scan). Nothing in this spec emits `GOAL.md`.

**Scope Boundaries:**

- **Included:** `evaluator-agent.md` + platform counterparts; `implement-story.md` default spawn + flag matrix + two-fail escalation; Gate 4 fail → coding-agent on default; adapter wording; `eval.sh` spawn-cap check; `stage-4b:` decision-log line.
- **Excluded:** Goal Card emit (4a); counterfactual patches; rewriting all agent prompts to 75% constraint; orchestrator background-await rewrite; eight-run / yuss / keep-or-revert; Stage 3 blocking; new gate numbers; pixel/DOM visual QA; live `/goal`; Codex goal-mode files; merge / PR / release.

---

## 🎯 Experience Design

**Entry point.** A maintainer runs `/implement-story` (no flag) on an active story.

**Happy path.** (1) Orchestrator runs Stage 2b scripts inline (arch-check, boundary-map, build-smoke, change-surface, review-override, drift-format, test-integrity, docs-check). (2) Spawns `coding-agent` in a worktree. (3) Spawns `evaluator-agent` in a fresh context against acceptance criteria and test results. (4) Story closes.

**Moment of truth.** A default run’s Task spawn count is 2. `--full-pipeline` still exists and still feels like today’s six-agent pipeline.

**Feedback model.** Evaluator reports what is wrong against the rubric. Suggested Fix is allowed in the report and is not applied. Scripts print `pass` / `fail` / `unverifiable` as they do now. Two-fail escalation is a one-line notice that this story continues as `--full-pipeline`.

**Error experience.** Evaluator FAIL → existing Gate 3 recode path (back to `coding-agent`). Second consecutive evaluator FAIL → continue as `--full-pipeline` for that story and say so. Script `unverifiable` continues; no `DEGRADED` on that basis alone. Gate 0 ABORT-class on default is script-`unverifiable` (no architecture-check spawn). Missing `evaluator-agent.md` or spawn-cap helper / exit 2 is a finding.

### State catalog

| State | What the user sees |
|---|---|
| Empty / first default run | Invocation table lists no-flag as 2-spawn; Pipeline table marks arch / testing / docs / visual as `--full-pipeline` only |
| Loading | Same inline scripts as today; two Task spawns |
| Populated | Evaluator PASS + scripts pass → story completion |
| Error | Evaluator FAIL → recode; second FAIL → `--full-pipeline` notice |
| Edge | `--quick` = coding-agent + scripts; `--review-only` = evaluator + scripts; ABORT-class = script unverifiable |

### Happy path flow

1. Load story + spec-lite + context (unchanged Step 2).
2. Run script gates that do not spawn (0, 0.5, 2, 2.5, 3 override, 3.5, 4, 5).
3. Spawn coding-agent (Gate 1).
4. Spawn evaluator-agent (Gate 3).
5. Complete the story (Step 4).

---

## 📋 Business Rules

1. **No-flag is the default.** `/implement-story` with no flag = coding-agent + evaluator + scripts. Do not add a `--default` flag.
2. **`--full-pipeline` is the hatch.** It keeps today’s six spawn sites: architecture-check, coding, review, testing, optional visual-qa, docs.
3. **`--quick` skips the evaluator.** Coding-agent + scripts only.
4. **`--review-only` skips coding.** Evaluator + scripts only.
5. **Two-fail auto-escalate only.** High-stakes is a documented reason to pass `--full-pipeline`, not a new story field and not an AskQuestion. After evaluator FAIL → recode → evaluator FAIL again, the rest of that story runs as `--full-pipeline`.
6. **No new gate numbers.** Evaluator replaces the Gate 3 *agent*; the heading stays Gate 3.
7. **FAIL-only override stands.** `review-override.py` is unchanged: script `fail` recodes; script `pass` / `unverifiable` does not wash an evaluator FAIL or PAUSE. Residual architecture / security / taste belong to `evaluator-agent` on the default path and to `review-agent` on `--full-pipeline`.
8. **Evaluator is read-only.** It reports what is wrong. It does not tell the coder how to fix. It does not apply a patch. Counterfactual apply is out of this spec.
9. **Default Gate 4 has no testing-agent.** `test-integrity.py` `fail` recodes via `coding-agent`. `--full-pipeline` keeps today’s testing-agent BLOCKED path.
10. **Gate 0 ABORT confirmation is `--full-pipeline` only.** Default cannot spawn architecture-check-agent to confirm ABORT. The script’s existing `unverifiable` on ABORT-class cases is the default verdict.
11. **`review-agent.md` is not rewritten.** New file only.
12. **Spawn-cap proof is static.** A command-file / agent-name scan (or a helper the command and `eval.sh` both call). Not a live Task count in CI. Not an eight-run.
13. **ADR-013 / no yuss / no eight-run / no emit.** Same honesty as Stages 2b, 3, and 4a.
14. **Decision log.** Each closing story appends `{date} stage-4b: {what changed}`.

---

## Detailed Requirements

### Story 1 — Evaluator agent

`agents/evaluator-agent.md` with an Agent Configuration block: `subagent_type: generalPurpose`, `model_tier: anchor` (judge), `readonly: true`, `problem` / `outcome` / `exit_criteria`. Rubric is the story’s acceptance criteria and the recorded test results, not a general “find problems” brief. Output: PASS / FAIL / PAUSE (PAUSE on Large drift, same as review-agent). FAIL issues carry Location, Severity, and an optional Suggested Fix that is never applied. Residual architecture, security, and taste are in scope. How-to-fix / rewrite-this-function instruction is out.

Platform counterparts so `check-agent-parity.sh` stays clean: `claude-code/agents/writ-evaluator.md` (Read/Grep/Glob/Bash; no Write/Edit), `codex/agents/evaluator-agent.toml` (`sandbox_mode = "read-only"`). Add the stem → `writ-evaluator.md` mapping in `scripts/check-agent-parity.sh`. Add a manifest `agents:` entry. Cursor consumes `agents/*.md` via the existing symlink — no extra Cursor file.

Do not edit `commands/implement-story.md`, `agents/review-agent.md`, `scripts/eval.sh`, or `scripts/review-override.py` in this story.

### Story 2 — Default path + flags

`commands/implement-story.md`:

- **Invocation table** gains `--full-pipeline`. No-flag row describes the 2-spawn default. `--quick` and `--review-only` match Business Rules 3–4. No `--default` flag.
- **Pipeline table** `Runs as` / `Skipped in` columns: architecture-check, testing, visual-qa, and docs spawn only on `--full-pipeline` (visual-qa still also skipped with no visual refs). Gate 3 `Runs as` is `evaluator-agent` on default and `review-agent` on `--full-pipeline`.
- **Spawn sites on the default path:** Gate 1 (`coding-agent`) and Gate 3 (`evaluator-agent`) only. Completeness and worktree-integration notes that list spawn gates name only those two on default.
- **Two-fail escalation:** a counter scoped to the current story. First evaluator FAIL → existing recode (Gate 1). Second consecutive evaluator FAIL → treat the remainder as `--full-pipeline` and print one notice. Do not AskQuestion.
- **Gate 3 body:** spawn `evaluator-agent` on default / `--quick` is skip / `--review-only` is evaluator-only. `--full-pipeline` still spawns `review-agent`. After the agent returns, run `review-override.py` exactly as Stage 2b wired it (FAIL-only). Substitute “evaluator” for “review-agent” in the residual sentence on the default path only.
- **Gate 4 body:** on default, do not spawn `testing-agent`. `test-integrity.py` `fail` uses BLOCKED escalation with agent `coding-agent`, restarting Gate 1 (not Gate 4). `--full-pipeline` keeps today’s testing-agent path.
- **Gate 0 / 4.5 / 5 bodies:** default runs the script only (Gate 0: `arch-check.py`; Gate 5: `docs-check.py`; Gate 4.5: skip). `--full-pipeline` keeps the agents. Gate 0 ADR-024 floor→anchor ABORT re-run is `--full-pipeline` only.

Do not rewrite `review-override.py`. Do not add `--default`.

### Story 3 — Eval + adapters + proof

`scripts/spawn-cap.py check --command commands/implement-story.md`: Python 3.9 stdlib; one verdict line; `reason:`; summary last; exit 0/1/2. `pass` when the default path names at most two spawn agent stems (`coding-agent`, `evaluator-agent`). `fail` `over_cap` when a third spawn site is named on the default path. `unverifiable` `missing_command` when the file is missing. Do not count `--full-pipeline`-only spawn sites. Do not spawn live Tasks.

`eval.sh` `CHECKS` includes `spawn-cap`. Missing helper / exit 2 → `add_finding`. `pass` / `fail` / `unverifiable` → `add_note` (do not count-block the suite on a documented `--full-pipeline` hatch). Pytest fixtures for pass / over_cap / missing_command / usage exit 2.

Adapters (`cursor.md`, `claude-code.md`, `codex.md`, `openclaw.md`): any sentence that implies no-flag `/implement-story` *is* the full SDLC / five-agent / six-gate pipeline is rewritten so that path is `--full-pipeline`. Do not add a `/goal` section. Do not invent a high-stakes classifier.

Story 3 What Was Built records: helper exists; default-path scan ≤2; `--full-pipeline` still names the six agents; `eval.sh` exits 0. Decision-log `stage-4b:` line names evaluator + default spawn + spawn-cap.

---

## Implementation Approach

Same helper family as `review-override.py` / `spec-analyze.py`: argparse, verdict line, `reason:`, summary last, exit 0/1/2. Additive `eval.sh` check. New agent file follows the existing Agent Configuration + platform-counterpart pattern (`review-agent` is the template; rubric and residual differ). `install.sh` already copies `scripts/*.py` and `agents/*.md`. No new gate numbers. No new command file.

## ⚠️ Technical Concerns

- Adapters and several command overview lines still describe no-flag `/implement-story` as the full SDLC pipeline. Those sentences have to move or they will relitigate the default.
- Gate 0’s ADR-024 floor→anchor ABORT path becomes `--full-pipeline` only. Default cannot spawn a third agent to confirm ABORT.
- Stage 2b / 3 / 4a headers still read `Not Started`. Do not “fix” them here.
- Spawn-cap proof must be a command-file / agent-name scan, not a live Task count in CI.
- `check-agent-parity.sh` warns (exit 0) on a missing counterpart — Story 1 must add the mapping or the warning becomes the new normal.

## 💡 Recommendations

- Keep `review-agent` as the `--full-pipeline` residual reviewer. Do not dual-purpose one file.
- Treat `--full-pipeline` as the compatibility hatch for the dogfooding study’s “gates caught real bugs” path, not as the thing we hope people still run by habit.
- Prompt-rewrite and background-await are later specs if they still matter after default spawn count drops.

## ⚠️ Cross-Spec Overlap

- `2026-09-08-phase11-stage2b-mechanize-the-gates` (Not Started header; stories landed) excluded five-agent demotion and told Stage 4 to change spawn. This spec takes that. Do not rewrite `review-override.py` or flip `gates:` provenance.
- `2026-09-09-phase11-stage4-goal-emit` (Not Started; Story 1 complete) owns emit and must not edit `implement-story.md`. Complementary; shared `eval.sh` is additive `CHECKS` only.
- `2026-09-08-phase11-stage3-spec-analysis` excluded Stage 4 demote. Complementary except additive `eval.sh`.
